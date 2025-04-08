# /home/pablo/app/chatbot/nlp.py
import os
import json
import time
import logging
import asyncio
import sys
import random
import weakref
import pandas as pd
import numpy as np
from functools import lru_cache
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text as text  # Necesario para registrar SentencepieceOp
import concurrent.futures
from django.core.cache import cache
from sklearn.metrics.pairwise import cosine_similarity
from geopy.distance import geodesic
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, List, Any, Optional
from app.chatbot.migration_check import skip_on_migrate

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.FileHandler('/home/pablo/logs/nlp.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Cargar el Universal Sentence Encoder multilingüe
# embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder-multilingual/3")

# Constantes
CACHE_TIMEOUT = 600
TRANSLATION_RATE_LIMIT = 5
TRANSLATION_DAILY_LIMIT = 200000
MAX_BATCH_SIZE = 50
RETRY_ATTEMPTS = 3

# Rutas de archivos
FILE_PATHS = {
    "relax_skills": "/home/pablo/skills_data/skill_db_relax_20.json",
    "esco_skills": "/home/pablo/skills_data/ESCO_occup_skills.json",
    "tabiya_skills": "/home/pablo/skills_data/tabiya/tabiya-esco-v1.1.1/csv/skills.csv",
    "opportunity_catalog": "/home/pablo/app/utilidades/catalogs/skills.json",
    "intents": "/home/pablo/chatbot_data/intents.json"
}

# Configuraciones
TRANSLATION_CONFIG = {'RATE_LIMIT': 5, 'DAILY_LIMIT': 200000, 'BATCH_SIZE': 50, 'TIMEOUT': 30, 'RETRY_ATTEMPTS': 3, 'BACKOFF_FACTOR': 2}
CACHE_CONFIG = {'EMBEDDINGS_TTL': 3600, 'CATALOG_TTL': 86400, 'TRANSLATION_TTL': 1800}
MODEL_CONFIG = {'MAX_SEQUENCE_LENGTH': 128, 'SIMILARITY_THRESHOLD': 0.8, 'CONFIDENCE_THRESHOLD': 0.7, 'BATCH_SIZE': 32}
# Catálogos globales
CANDIDATE_CATALOG = None
OPPORTUNITY_CATALOG = None
INTENTS_CATALOG = None

# Lazy-load solo para configuraciones pesadas
def initialize_nlp_dependencies():
    """Inicializa configuraciones pesadas solo cuando se necesitan"""
    if not hasattr(initialize_nlp_dependencies, 'initialized'):
        import nltk
        nltk.download('vader_lexicon', quiet=True)
        initialize_nlp_dependencies.initialized = True

class RateLimitedTranslator:
    def __init__(self, source='auto', target='en'):
        initialize_nlp_dependencies()  # Configuraciones pesadas
        from deep_translator import GoogleTranslator
        from concurrent.futures import ThreadPoolExecutor
        from asyncio import Semaphore
        self.translator = GoogleTranslator(source=source, target=target)
        self.request_semaphore = Semaphore(TRANSLATION_CONFIG['RATE_LIMIT'])
        self.daily_request_count = 0
        self.last_reset_time = time.time()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._lock = asyncio.Lock()
        self._error_count = 0
        self._last_error_time = 0
        self._backoff_time = 1
        self._translation_cache = {}  # Caché local para traducciones

    async def _handle_error(self, e: Exception):
        """Manejo inteligente de errores con backoff exponencial"""
        async with self._lock:
            current_time = time.time()
            if current_time - self._last_error_time > 60:
                self._error_count = 0
                self._backoff_time = 1
            
            self._error_count += 1
            self._last_error_time = current_time
            
            if self._error_count > RETRY_ATTEMPTS:
                self._backoff_time = min(self._backoff_time * 2, 60)
                await asyncio.sleep(self._backoff_time)
                self._error_count = 0
            
            logger.error(f"Error en traducción: {e}", exc_info=True)

    async def _check_and_reset_daily_limit(self):
        async with self._lock:
            current_time = time.time()
            if current_time - self.last_reset_time >= 86400:  # 24 horas
                self.daily_request_count = 0
                self.last_reset_time = current_time

    @retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def translate(self, text: str) -> str:
        if not text or len(text.strip()) < 1:
            logger.debug(f"Texto vacío o inválido para traducción: '{text}'")
            return text
        # Verificar caché primero
        cache_key = f"{text}_{self.translator.source}_{self.translator.target}"
        if cache_key in self._translation_cache:
            return self._translation_cache[cache_key]

        await self._check_and_reset_daily_limit()
        if self.daily_request_count >= TRANSLATION_CONFIG['DAILY_LIMIT']:
            logger.warning("Límite diario de traducciones alcanzado")
            return text

        async with self.request_semaphore:
            loop = asyncio.get_event_loop()
            try:
                logger.debug(f"Traduciendo texto: '{text}'")
                translated = await loop.run_in_executor(
                    self.executor,
                    lambda: self.translator.translate(text)
                )
                async with self._lock:
                    self.daily_request_count += 1
                logger.debug(f"Traducción completada: '{translated}'")
                return translated
            except Exception as e:
                await self._handle_error(e)
                return text

    @retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def translate_batch(self, texts: List[str]) -> List[str]:
        if not texts:
            logger.debug("Lista de textos vacía para traducción")
            return []

        await self._check_and_reset_daily_limit()
        remaining_slots = TRANSLATION_CONFIG['DAILY_LIMIT'] - self.daily_request_count
        if remaining_slots <= 0:
            logger.warning("Límite diario de traducciones alcanzado")
            return texts

        effective_batch = texts[:min(TRANSLATION_CONFIG['BATCH_SIZE'], remaining_slots)]
        async with self.request_semaphore:
            loop = asyncio.get_event_loop()
            try:
                logger.debug(f"Traduciendo lote de {len(effective_batch)} textos")
                translated = await loop.run_in_executor(
                    self.executor,
                    lambda: self.translator.translate_batch(effective_batch)
                )
                async with self._lock:
                    self.daily_request_count += len(effective_batch)
                logger.debug(f"Traducción de lote completada: {len(translated)} textos")
                return translated + texts[len(effective_batch):]
            except Exception as e:
                await self._handle_error(e)
                return texts

class AsyncTranslator:
    def __init__(self, source='auto', target='en'):
        self.rate_limited_translator = RateLimitedTranslator(source, target)

    async def translate(self, text: str) -> str:
        return await self.rate_limited_translator.translate(text)

    async def translate_batch(self, texts: List[str]) -> List[str]:
        return await self.rate_limited_translator.translate_batch(texts)

class CacheManager:
    def __init__(self):
        self.redis_client = cache
        self._local_cache = {}
        self._last_cleanup = time.time()
        self._lock = asyncio.Lock()

    async def get_or_set(self, key: str, getter_func, ttl: int = 3600):
        async with self._lock:
            if key in self._local_cache:
                value, expiry = self._local_cache[key]
                if time.time() < expiry:
                    return value

            value = self.redis_client.get(key)
            if value is not None:
                self._local_cache[key] = (value, time.time() + ttl)
                return value

            try:
                value = await getter_func()
                self.redis_client.set(key, value, timeout=ttl)
                self._local_cache[key] = (value, time.time() + ttl)
                return value
            except Exception as e:
                logger.error(f"Error al obtener o establecer en caché: {e}", exc_info=True)
                return None

    async def cleanup(self):
        async with self._lock:
            current_time = time.time()
            if current_time - self._last_cleanup > 3600:  # Limpiar cada hora
                self._local_cache = {k: v for k, v in self._local_cache.items() if current_time < v[1]}
                self._last_cleanup = current_time

class ModelPool:
    def __init__(self, max_models=3):
        self.max_models = max_models
        self.models = {}
        self.last_used = {}
        self._lock = asyncio.Lock()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    async def get_model(self, model_type: str):
        async with self._lock:
            if model_type not in self.models:
                if len(self.models) >= self.max_models:
                    oldest = min(self.last_used.items(), key=lambda x: x[1])[0]
                    del self.models[oldest]
                    del self.last_used[oldest]
                
                try:
                    loop = asyncio.get_event_loop()
                    if model_type == "ner":
                        # Cargar modelo NER de TensorFlow Hub
                        self.models[model_type] = await loop.run_in_executor(
                            self.executor, lambda: hub.load("https://tfhub.dev/google/bert_multi_cased_L-12_H-768_A-12/4")
                        )
                    elif model_type == "intent":
                        # Cargar clasificador personalizado con tf.keras
                        self.models[model_type] = await loop.run_in_executor(
                            self.executor, self._load_intent_model
                        )
                    # No necesitamos "encoder" porque USE ya lo reemplaza
                    logger.info(f"Modelo {model_type} cargado")
                except Exception as e:
                    logger.error(f"Error al cargar modelo {model_type}: {e}", exc_info=True)
                    return None

            self.last_used[model_type] = time.time()
            return self.models[model_type]

    def _load_intent_model(self):
        # Modelo ligero de clasificación con tf.keras
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(512,)),  # USE embeddings tienen 512 dimensiones
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(len(self._load_intents()), activation='softmax')  # Número de intenciones
        ])
        model.load_weights("path/to/intent_model_weights.h5")  # Cargar pesos preentrenados
        return model

class BatchProcessor:
    def __init__(self, model_pool: ModelPool):
        self.model_pool = model_pool
        self.batch_size = MODEL_CONFIG['BATCH_SIZE']

    async def process_quick(self, preprocessed: Dict, catalog: Dict) -> Dict:
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        # Usar embeddings de USE para coincidencias rápidas
        text_emb = self._get_text_embedding(preprocessed["translated"])
        for category, skill_list in catalog.items():
            for skill_dict in skill_list:
                skill_emb = self._get_text_embedding(skill_dict["translated"])
                similarity = cosine_similarity([text_emb], [skill_emb])[0][0]
                if similarity > MODEL_CONFIG['SIMILARITY_THRESHOLD']:
                    skills[category].append(skill_dict)
        return skills

    async def process_deep(self, preprocessed: Dict, catalog: Dict) -> Dict:
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        ner_model = await self.model_pool.get_model("ner")
        
        if ner_model:
            try:
                # Procesar texto con modelo NER de TensorFlow Hub
                text_emb = self._get_text_embedding(preprocessed["translated"])
                # Aquí podrías integrar un pipeline NER personalizado con tf.keras si es necesario
                # Por simplicidad, usamos coincidencias de embeddings
                for category, skill_list in catalog.items():
                    for skill_dict in skill_list:
                        skill_emb = self._get_text_embedding(skill_dict["translated"])
                        similarity = cosine_similarity([text_emb], [skill_emb])[0][0]
                        if similarity > MODEL_CONFIG['SIMILARITY_THRESHOLD']:
                            skills[category].append(skill_dict)
            except Exception as e:
                logger.error(f"Error procesando NER: {e}", exc_info=True)

        return skills

    def _get_text_embedding(self, text: str) -> np.ndarray:
        return embed([text]).numpy()[0]

    def _classify_entity(self, entity_group: str) -> str:
        if entity_group in ["SKILL", "TECH"]:
            return "technical"
        if entity_group == "TOOL":
            return "tools"
        if entity_group == "CERT":
            return "certifications"
        return "soft"

    def _get_skill_embedding(self, skill: str, encoder, tokenizer) -> np.ndarray:
        try:
            inputs = tokenizer(skill, return_tensors="tf", padding=True, truncation=True, max_length=MODEL_CONFIG['MAX_SEQUENCE_LENGTH'])
            outputs = encoder(inputs["input_ids"], attention_mask=inputs["attention_mask"])
            return tf.reduce_mean(outputs.last_hidden_state, axis=1).numpy()[0]
        except Exception as e:
            logger.error(f"Error obteniendo embedding de habilidad: {e}", exc_info=True)
            return np.zeros(768)

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
        self._lock = asyncio.Lock()

    async def record_metric(self, name: str, value: float):
        async with self._lock:
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(value)
            if len(self.metrics[name]) > 1000:
                self.metrics[name] = self.metrics[name][-1000:]

    def get_average(self, name: str) -> float:
        return np.mean(self.metrics.get(name, [0]))

    def get_metrics_report(self) -> Dict:
        return {
            name: {
                "avg": np.mean(values),
                "min": np.min(values),
                "max": np.max(values),
                "count": len(values)
            }
            for name, values in self.metrics.items()
        }

class NLPProcessor:
    @skip_on_migrate
    def __init__(self, mode: str = "candidate", analysis_depth: str = "quick", language: str = "es"):
        if 'migrate' in sys.argv:
            self.mode = mode
            self.depth = analysis_depth
            self.language = language
            return
        self.semaphore = asyncio.Semaphore(5)  # Limitar a 5 tareas concurrentes
        self.mode = mode
        self.depth = analysis_depth
        self.language = language
        self.last_used = time.time()
        self._translator = AsyncTranslator()
        self.candidate_catalog = None
        self.opportunity_catalog = None
        self.intents = None
        self.cache_manager = CacheManager()
        self.performance_monitor = PerformanceMonitor()
        logger.info(f"NLPProcessor inicializado: modo={mode}, profundidad={analysis_depth}, idioma={language}")

        initialize_nlp_dependencies()  # Inicializar dependencias solo aquí

        self.mode = mode
        self.depth = analysis_depth
        self.language = language
        self.last_used = time.time()

        self._translator = AsyncTranslator()
        self._sentiment_analyzer = None
        self.api_key = os.getenv("GROK_API_KEY", "default_key")

        self.CATALOG_FILES = {
            "relax_skills": {"path": FILE_PATHS["relax_skills"], "type": "json", "process": self._process_relax_skills},
            "esco_skills": {"path": FILE_PATHS["esco_skills"], "type": "json", "process": self._process_esco_skills},
            "tabiya_skills": {"path": FILE_PATHS["tabiya_skills"], "type": "csv", "process": self._process_csv_skills}
        }

        self.candidate_catalog = None
        self.opportunity_catalog = None
        self.intents = None

        self.cache_manager = CacheManager()
        self.model_pool = ModelPool()
        self.batch_processor = BatchProcessor(self.model_pool)
        self._cache_embeddings = {}
        self.performance_monitor = PerformanceMonitor()
        logger.info(f"NLPProcessor inicializado: modo={mode}, profundidad={analysis_depth}, idioma={language}")

    async def initialize_gpt(self):
        if not self.gpt_handler:
            self.gpt_handler = GPTHandler()
            await self.gpt_handler.initialize()

    async def analyze_with_gpt(self, text: str, prompt: str) -> str:
        await self.initialize_gpt()
        response = await self.gpt_handler.generate_response(prompt + text)
        return response

    async def _ensure_catalogs_loaded(self):
        if self.candidate_catalog is None:
            self.candidate_catalog = await self._load_catalog_async("candidate") or {"technical": [], "soft": [], "tools": [], "certifications": []}
        if self.opportunity_catalog is None:
            self.opportunity_catalog = await self._load_opportunity_catalog() or []
        if self.intents is None:
            self.intents = self._load_intents() or {"default": ["No se pudieron cargar las intenciones"]}

    def _check_and_free_models(self, timeout=600):
        if time.time() - self.last_used > timeout:
            self._sentiment_analyzer = None
            self.model_pool.models.clear()
            self.model_pool.last_used.clear()
            logger.info("Modelos liberados por inactividad")
        self.last_used = time.time()

    def _load_sentiment_analyzer(self):
        if self._sentiment_analyzer is None:
            try:
                self._sentiment_analyzer = SentimentIntensityAnalyzer()
                logger.info("Analizador de sentimientos cargado")
            except Exception as e:
                logger.error(f"Error al cargar analizador de sentimientos: {e}", exc_info=True)
        return self._sentiment_analyzer

    async def _load_catalog_async(self, catalog_type: str) -> Dict[str, List[Dict[str, str]]]:
        cache_key = f"catalog_{catalog_type}"
        return await self.cache_manager.get_or_set(
            cache_key,
            lambda: self._load_catalog_impl(catalog_type),
            CACHE_CONFIG['CATALOG_TTL']
        )

    async def _load_catalog_impl(self, catalog_type: str) -> Dict[str, List[Dict[str, str]]]:
        catalog = {"technical": [], "soft": [], "tools": [], "certifications": []}
        for file_key, file_info in self.CATALOG_FILES.items():
            path = file_info["path"]
            if path in [FILE_PATHS["opportunity_catalog"], FILE_PATHS["intents"]]:
                logger.debug(f"Omitiendo archivo excluido: {path}")
                continue
            if not os.path.exists(path):
                logger.warning(f"Archivo no encontrado: {path}. Omitiendo.")
                continue
            try:
                if file_info["type"] == "json":
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                elif file_info["type"] == "csv":
                    data = pd.read_csv(path)
                else:
                    logger.error(f"Tipo de archivo no soportado para {path}: {file_info['type']}")
                    continue
                await file_info["process"](data, catalog)
                logger.info(f"Catálogo cargado exitosamente desde {path}")
            except Exception as e:
                logger.error(f"Error al cargar {path}: {e}", exc_info=True)
                continue
        return catalog

    async def _process_relax_skills(self, data: Dict, catalog: Dict) -> None:
        skill_names = [skill_info.get("skill_name") for skill_info in data.values() if skill_info.get("skill_name")]
        skill_types = [skill_info.get("skill_type") for skill_info in data.values() if skill_info.get("skill_name")]
        if not skill_names:
            logger.debug("No hay habilidades válidas en skill_db_relax_20.json")
            return
        langs = [detect(skill) for skill in skill_names]
        to_translate = [skill for skill, lang in zip(skill_names, langs) if lang != "en"]
        translated_skills = await self._translator.translate_batch(to_translate) if to_translate else []
        translated_iter = iter(translated_skills)
        for skill_name, skill_type, lang in zip(skill_names, skill_types, langs):
            if not skill_type:
                logger.debug(f"Entrada inválida en skill_db_relax_20.json: {skill_name}")
                continue
            translated = next(translated_iter) if lang != "en" else skill_name
            skill_dict = {"original": skill_name, "translated": translated.lower(), "lang": lang}
            self._classify_skill(skill_dict, catalog)

    async def _process_esco_skills(self, data: Dict, catalog: Dict) -> None:
        for occupation, info in data.items():
            description = info.get("description", "")
            if not description:
                logger.debug(f"No se encontró descripción para la ocupación {occupation}")
                continue
            logger.debug(f"Omitiendo ocupación {occupation}: no se procesan habilidades directas")

    async def _process_csv_skills(self, data: pd.DataFrame, catalog: Dict) -> None:
        skills = data["PREFERREDLABEL"].dropna().tolist()
        if not skills:
            logger.debug("No hay habilidades válidas en skills.csv")
            return
        translated_skills = await self._translator.translate_batch(skills)
        for skill, translated in zip(skills, translated_skills):
            if isinstance(translated, str):
                self._classify_skill({"original": skill, "translated": translated.lower(), "lang": "en"}, catalog)
            else:
                logger.warning(f"Traducción fallida para {skill}: {translated}")
                self._classify_skill({"original": skill, "translated": skill.lower(), "lang": "en"}, catalog)

    async def _load_opportunity_catalog(self) -> List[Dict]:
        cache_key = "opportunity_catalog"
        return await self.cache_manager.get_or_set(
            cache_key,
            self._load_opportunity_catalog_impl,
            CACHE_CONFIG['CATALOG_TTL']
        )

    async def _load_opportunity_catalog_impl(self) -> List[Dict]:
        opp_path = FILE_PATHS["opportunity_catalog"]
        if not os.path.exists(opp_path):
            logger.error(f"Archivo no encontrado: {opp_path}. Usando catálogo vacío.")
            return []
        try:
            with open(opp_path, "r", encoding="utf-8") as f:
                opp_data = json.load(f)
            opportunities = []
            if isinstance(opp_data, dict):
                for business_unit, roles in opp_data.items():
                    for role, skills in roles.items():
                        skill_dict = {
                            "technical": [{"original": s, "translated": s.lower(), "lang": "es"} for s in skills.get("Habilidades Técnicas", [])],
                            "soft": [{"original": s, "translated": s.lower(), "lang": "es"} for s in skills.get("Habilidades Blandas", [])],
                            "certifications": [{"original": s, "translated": s.lower(), "lang": "es"} for s in skills.get("Certificaciones", [])],
                            "tools": [{"original": s, "translated": s.lower(), "lang": "es"} for s in skills.get("Herramientas", [])]
                        }
                        opportunities.append({
                            "title": f"{role} en {business_unit}",
                            "required_skills": skill_dict
                        })
            elif isinstance(opp_data, list):
                opportunities = opp_data
            else:
                logger.error(f"Formato no soportado en {opp_path}. Usando catálogo vacío.")
                return []
            for opp in opportunities:
                for category in opp["required_skills"]:
                    skills = opp["required_skills"][category]
                    if skills:
                        originals = [s["original"] for s in skills]
                        translated = await self._translator.translate_batch(originals)
                        for skill, trans in zip(skills, translated):
                            if isinstance(trans, str):
                                skill["translated"] = trans.lower()
                            else:
                                logger.warning(f"Traducción fallida para {skill['original']}: {trans}")
                                skill["translated"] = skill["original"].lower()
            logger.info(f"Catálogo de oportunidades cargado con {len(opportunities)} oportunidades")
            return opportunities
        except Exception as e:
            logger.error(f"Error al cargar {opp_path}: {e}", exc_info=True)
            return []

    def _load_intents(self) -> Dict[str, List[str]]:
        cache_key = "intents_catalog"
        cached_catalog = cache.get(cache_key)
        if cached_catalog is not None:
            logger.info("Catálogo de intents cargado desde caché")
            return cached_catalog
        try:
            from app.chatbot.intents_handler import INTENTS
            intents_data = {intent: data["patterns"] for intent, data in INTENTS.items()}
            logger.info("Intents cargados desde intents_handler.py")
            cache.set(cache_key, intents_data, timeout=CACHE_CONFIG['CATALOG_TTL'])
            return intents_data
        except Exception as e:
            logger.error(f"Error al cargar intents: {e}", exc_info=True)
            return {"default": ["No se pudieron cargar las intenciones"]}

    async def preprocess(self, text: str) -> Dict[str, str]:
        if not text or len(text.strip()) < 3:
            return {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}
        try:
            lang = detect(text)
            translated = await self._translator.translate(text) if lang != "en" else text
            return {"original": text.lower(), "translated": translated.lower(), "lang": lang}
        except Exception as e:
            logger.error(f"Error en preprocess: {e}", exc_info=True)
            return {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}

    async def preprocess_batch(self, texts: List[str]) -> List[Dict[str, str]]:
        try:
            langs = [detect(text) if text and len(text.strip()) >= 3 else "unknown" for text in texts]
            to_translate = [text for text, lang in zip(texts, langs) if lang != "en"]
            translated_texts = await self._translator.translate_batch(to_translate) if to_translate else []
            translated_iter = iter(translated_texts)
            return [
                {"original": text.lower(), "translated": next(translated_iter) if lang != "en" else text.lower(), "lang": lang}
                if text and len(text.strip()) >= 3 else {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}
                for text, lang in zip(texts, langs)
            ]
        except Exception as e:
            logger.error(f"Error en preprocess_batch: {e}", exc_info=True)
            return [{"original": text.lower(), "translated": text.lower(), "lang": "unknown"} for text in texts]

    async def extract_skills(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        cache_key = f"skills_{hash(text)}"
        await self._ensure_catalogs_loaded()
        return await self.cache_manager.get_or_set(
            cache_key,
            lambda: self._extract_skills_impl(text),
            CACHE_CONFIG['EMBEDDINGS_TTL']
        )
    
    async def _extract_skills_impl(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        preprocessed = await self.preprocess(text)
        catalog = self.candidate_catalog if self.mode == "candidate" else self.opportunity_catalog
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        text_emb = self.get_text_embedding(preprocessed["translated"])
        for category, skill_list in catalog.items():
            for skill_dict in skill_list:
                skill_emb = self.get_skill_embedding(skill_dict["translated"])
                similarity = cosine_similarity([text_emb], [skill_emb])[0][0]
                if similarity > MODEL_CONFIG['SIMILARITY_THRESHOLD']:
                    skills[category].append(skill_dict)
        return {"skills": skills}

    def _deduplicate_skills(self, skills: Dict[str, List[Dict[str, str]]]) -> Dict[str, List[Dict[str, str]]]:
        for category in skills:
            unique_skills = []
            embeddings = [self.get_skill_embedding(s["translated"]) for s in skills[category]]
            for i, emb in enumerate(embeddings):
                is_unique = True
                for j in range(i):
                    if cosine_similarity([emb], [embeddings[j]])[0][0] > 0.9:
                        is_unique = False
                        break
                if is_unique:
                    unique_skills.append(skills[category][i])
            skills[category] = unique_skills
        return {"skills": skills}

    def _classify_skill(self, skill_dict: Dict[str, str], catalog: Dict) -> None:
        try:
            skill_lower = skill_dict["translated"]
            if "cert" in skill_lower or "certificación" in skill_lower:
                catalog["certifications"].append(skill_dict)
            elif "tool" in skill_lower or "herramienta" in skill_lower:
                catalog["tools"].append(skill_dict)
            elif "soft" in skill_lower or "blanda" in skill_lower:
                catalog["soft"].append(skill_dict)
            else:
                catalog["technical"].append(skill_dict)
        except Exception as e:
            logger.error(f"Error clasificando habilidad: {e}", exc_info=True)

    def get_text_embedding(self, text: str) -> np.ndarray:
        cache_key = f"embedding_{text}"
        cached_embedding = cache.get(cache_key)
        if cached_embedding is not None:
            return cached_embedding
        try:
            embedding = embed([text]).numpy()[0]
            cache.set(cache_key, embedding, timeout=CACHE_CONFIG['EMBEDDINGS_TTL'])
            return embedding
        except Exception as e:
            logger.error(f"Error obteniendo embedding de texto: {e}", exc_info=True)
            return np.zeros(512)  # USE devuelve embeddings de 512 dimensiones

    def get_skill_embedding(self, skill: str) -> np.ndarray:
        return self.get_text_embedding(skill)

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        sentiment_analyzer = self._load_sentiment_analyzer()
        if sentiment_analyzer:
            try:
                sentiment = sentiment_analyzer.polarity_scores(text)
                return {
                    "compound": sentiment["compound"],
                    "label": "positive" if sentiment["compound"] > 0.05 else "negative" if sentiment["compound"] < -0.05 else "neutral"
                }
            except Exception as e:
                logger.error(f"Error analizando sentimiento: {e}", exc_info=True)
        return {"compound": 0.0, "label": "neutral"}

    async def classify_intent(self, text: str) -> Dict[str, float]:
        try:
            intent_classifier = asyncio.run(self.model_pool.get_model("intent"))
            if intent_classifier:
                preprocessed = asyncio.run(self.preprocess(text))
                intent_result = intent_classifier(preprocessed["translated"])[0]
                confidence = intent_result["score"]
                intent = intent_result["label"] if confidence > MODEL_CONFIG['CONFIDENCE_THRESHOLD'] else "unknown"
                logger.debug(f"Intención clasificada: {intent} con confianza {confidence}")
                return {"intent": intent, "confidence": confidence}
        except Exception as e:
            logger.error(f"Error clasificando intención: {e}", exc_info=True)
        return {"intent": "unknown", "confidence": 0.0}

    def match_opportunities(self, candidate_skills: Dict[str, List[Dict[str, str]]]) -> List[Dict]:
        if self.mode != "candidate":
            return []
        asyncio.run(self._ensure_catalogs_loaded())
        try:
            matches = []
            candidate_emb = np.mean([self.get_skill_embedding(s["translated"]) for s in sum(candidate_skills.values(), [])] or [np.zeros(512)], axis=0)
            for opp in self.opportunity_catalog:
                opp_skills = sum(opp["required_skills"].values(), [])
                opp_emb = np.mean([self.get_skill_embedding(s["translated"]) for s in opp_skills] or [np.zeros(512)], axis=0)
                score = cosine_similarity([candidate_emb], [opp_emb])[0][0]
                matches.append({"opportunity": opp["title"], "match_score": float(score)})
            return sorted(matches, key=lambda x: x["match_score"], reverse=True)[:5]
        except Exception as e:
            logger.error(f"Error emparejando oportunidades: {e}", exc_info=True)
            return []

    def get_suggested_skills(self, business_unit: str, category: str = "general") -> List[str]:
        asyncio.run(self._ensure_catalogs_loaded())  # Asegurarse de que los catálogos estén cargados
        if not self.opportunity_catalog:
            logger.warning("Catálogo de oportunidades vacío. No se pueden sugerir habilidades.")
            return []
        try:
            relevant_opps = [opp for opp in self.opportunity_catalog if business_unit.lower() in opp["title"].lower()]
            if not relevant_opps:
                logger.warning(f"No se encontraron oportunidades para {business_unit}. Usando catálogo general.")
                relevant_opps = self.opportunity_catalog
            suggested = set()
            for opp in relevant_opps:
                if category == "general":
                    for cat_skills in opp["required_skills"].values():
                        for skill in cat_skills:
                            suggested.add(skill["original"])
                else:
                    for skill in opp["required_skills"].get(category, []):
                        suggested.add(skill["original"])
            return list(suggested)
        except Exception as e:
            logger.error(f"Error obteniendo habilidades sugeridas: {e}", exc_info=True)
            return []

    async def analyze(self, text: str) -> Dict:
        start_time = time.time()
        try:
            preprocessed = await self.preprocess(text)
            skills = await self.extract_skills(text)
            sentiment = self.analyze_sentiment(preprocessed["translated"])
            intent = self.classify_intent(text) if self.depth == "quick" else {"intent": "unknown", "confidence": 0.0}

            result = {
                "skills": skills["skills"],
                "sentiment": sentiment["label"],
                "sentiment_score": abs(sentiment["compound"]),
                "intent": intent["intent"],
                "intent_confidence": intent["confidence"],
                "metadata": {
                    "execution_time": time.time() - start_time,
                    "original_text": preprocessed["original"],
                    "translated_text": preprocessed["translated"],
                    "detected_language": preprocessed["lang"]
                }
            }

            if self.mode == "candidate":
                result["opportunities"] = self.match_opportunities(skills["skills"])
            elif self.mode == "opportunity":
                result["required_skills"] = skills["skills"]
            elif self.depth == "deep":
                summary = await self.analyze_with_gpt(text, "Resume el siguiente texto en una frase: ")
                result["summary"] = summary

            logger.info(f"Análisis completado para texto: {text[:50]}... en {result['metadata']['execution_time']:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Error en análisis: {e}", exc_info=True)
            return {
                "skills": {"technical": [], "soft": [], "tools": [], "certifications": []},
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "intent": "unknown",
                "intent_confidence": 0.0,
                "metadata": {
                    "execution_time": time.time() - start_time,
                    "original_text": text.lower(),
                    "translated_text": text.lower(),
                    "detected_language": "unknown"
                }
            }
        

if __name__ == "__main__":
    nlp = NLPProcessor(mode="candidate", analysis_depth="quick")
    examples = {
        "candidate_quick": "Tengo experiencia en Python y trabajo en equipo.",
        "candidate_deep": "Soy un desarrollador con certificación AWS y habilidades en Java.",
        "opportunity_quick": "Buscamos un ingeniero con experiencia en SQL y comunicación."
    }
    for mode, text in examples.items():
        print(f"\nAnalizando en modo '{mode}':")
        nlp.depth = "quick" if "quick" in mode else "deep"
        result = asyncio.run(nlp.analyze(text))
        print(json.dumps(result, indent=2, ensure_ascii=False)) 