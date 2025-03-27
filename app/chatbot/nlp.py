import os
import json
import time
import logging
import spacy
import nltk
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor
from langdetect import detect
import numpy as np
import tensorflow as tf
from transformers import pipeline, TFAutoModel, AutoTokenizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Optional
import requests
from app.ml.ml_opt import configure_tensorflow_based_on_load
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from deep_translator import GoogleTranslator
from django.core.cache import cache
from tenacity import retry, stop_after_attempt, wait_exponential
import aiohttp
from asyncio import Semaphore
from app.chatbot.migration_check import skip_on_migrate
import sys

# Configurar TensorFlow según la carga del sistema
configure_tensorflow_based_on_load()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

nltk.download('vader_lexicon', quiet=True)

# Constantes
CACHE_TIMEOUT = 600  # 10 minutes
TRANSLATION_RATE_LIMIT = 5  # Requests per second
TRANSLATION_DAILY_LIMIT = 1000  # Daily translation limit
MAX_BATCH_SIZE = 50  # Maximum batch size for translations
# Catálogos globales
CANDIDATE_CATALOG = None
OPPORTUNITY_CATALOG = None
INTENTS_CATALOG = None

# Rutas de archivos
FILE_PATHS = {
    "relax_skills": "/home/pablo/skills_data/skill_db_relax_20.json",
    "esco_skills": "/home/pablo/skills_data/ESCO_occup_skills.json",
    "tabiya_skills": "/home/pablo/skills_data/tabiya/tabiya-esco-v1.1.1/csv/skills.csv",
    "opportunity_catalog": "/home/pablo/app/utilidades/catalogs/skills.json",
    "intents": "/home/pablo/chatbot_data/intents.json"
}

# 1. Configuración y constantes mejoradas
TRANSLATION_CONFIG = {
    'RATE_LIMIT': 5,  # Solicitudes por segundo
    'DAILY_LIMIT': 1000,  # Límite diario
    'BATCH_SIZE': 50,  # Tamaño máximo del lote
    'TIMEOUT': 30,  # Tiempo de espera para traducciones
    'RETRY_ATTEMPTS': 3,  # Intentos de reintento
    'BACKOFF_FACTOR': 2  # Factor de retroceso exponencial
}
CACHE_CONFIG = {
    'EMBEDDINGS_TTL': 3600,  # 1 hora para embeddings
    'CATALOG_TTL': 86400,    # 24 horas para catálogos
    'TRANSLATION_TTL': 1800  # 30 minutos para traducciones
}
MODEL_CONFIG = {
    'MAX_SEQUENCE_LENGTH': 128,
    'SIMILARITY_THRESHOLD': 0.8,
    'CONFIDENCE_THRESHOLD': 0.7,
    'BATCH_SIZE': 32
}
class RateLimitedTranslator:
    def __init__(self, source='auto', target='en', max_requests_per_second=TRANSLATION_RATE_LIMIT):
        """
        Rate-limited translator with intelligent backoff and retry mechanisms       
        Args:
            source (str): Source language code
            target (str): Target language code
            max_requests_per_second (int): Maximum translation requests per second
        """
        self.translator = GoogleTranslator(source=source, target=target)
        self.request_semaphore = asyncio.Semaphore(max_requests_per_second)
        self.daily_request_count = 0
        self.last_reset_time = time.time()
        self.error_backoff_time = 1  # Initial backoff time
        self.max_error_backoff_time = 60  # Maximum backoff time

    async def _check_and_reset_daily_limit(self):
        """Check and reset daily request count"""
        current_time = time.time()
        if current_time - self.last_reset_time >= 86400:  # 24 hours
            self.daily_request_count = 0
            self.last_reset_time = current_time

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def translate(self, text: str) -> str:
        """
        Translate a single text with rate limiting and error handling
        Args:
            text (str): Text to translate
        Returns:
            str: Translated text
        """
        await self._check_and_reset_daily_limit()
        
        if not text or len(text.strip()) < 1:
            return text

        if self.daily_request_count >= TRANSLATION_DAILY_LIMIT:
            logger.warning("Daily translation limit reached. Returning original text.")
            return text

        try:
            async with self.request_semaphore:
                # Random jitter to distribute requests
                await asyncio.sleep(random.uniform(0, 0.5))
                translated = await asyncio.to_thread(self.translator.translate, text)
                self.daily_request_count += 1
                self.error_backoff_time = 1  # Reset backoff time on success
                return translated
        
        except Exception as e:
            logger.warning(f"Translation error: {e}")
            # Implement exponential backoff
            await asyncio.sleep(self.error_backoff_time)
            self.error_backoff_time = min(self.error_backoff_time * 2, self.max_error_backoff_time)
            return text

    async def translate_batch(self, texts: List[str]) -> List[str]:
        """
        Translate a batch of texts with intelligent batching and rate limiting
        Args:
            texts (List[str]): List of texts to translate
        Returns:
            List[str]: Translated texts
        """
        if not texts:
            return []

        # Split into smaller batches to manage rate limits
        translated_texts = []
        for i in range(0, len(texts), MAX_BATCH_SIZE):
            batch = texts[i:i+MAX_BATCH_SIZE]
            batch_translations = await asyncio.gather(
                *[self.translate(text) for text in batch]
            )
            translated_texts.extend(batch_translations)

        return translated_texts

class AsyncTranslator:
    def __init__(self, source='auto', target='en'):
        """
        Asynchronous translator wrapper with fallback mechanisms
        Args:
            source (str): Source language code
            target (str): Target language code
        """
        self.rate_limited_translator = RateLimitedTranslator(source, target)
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def translate(self, text: str) -> str:
        """
        Translate a single text
        Args:
            text (str): Text to translate
        Returns:
            str: Translated text
        """
        if not text or len(text.strip()) < 1:
            return text
        
        return await self.rate_limited_translator.translate(text)

    async def translate_batch(self, texts: List[str]) -> List[str]:
        """
        Translate multiple texts
        Args:
            texts (List[str]): List of texts to translate        
        Returns:
            List[str]: Translated texts
        """
        return await self.rate_limited_translator.translate_batch(texts)


class NLPProcessor:
    @skip_on_migrate
    def __init__(self, mode: str = "candidate", analysis_depth: str = "quick", language: str = "es"):
        if 'migrate' in sys.argv:
            return
        self.mode = mode
        self.depth = analysis_depth
        self.language = language
        self.last_used = time.time()

        try:
            self.nlp_spacy = spacy.load("es_core_news_sm" if language == "es" else "en_core_web_sm")
        except Exception as e:
            logger.error(f"Error al cargar modelo spaCy: {e}")
            self.nlp_spacy = None

        self._encoder = None
        self._encoder_tokenizer = None
        self._ner = None
        self._translator = AsyncTranslator()
        self._translator_fallback = None
        self._sentiment_analyzer = None
        self._intent_classifier = None
        self.api_key = os.getenv("GROK_API_KEY")

        self.CATALOG_FILES = {
            "relax_skills": {"path": FILE_PATHS["relax_skills"], "type": "json", "process": self._process_relax_skills},
            "esco_skills": {"path": FILE_PATHS["esco_skills"], "type": "json", "process": self._process_esco_skills},
            "tabiya_skills": {"path": FILE_PATHS["tabiya_skills"], "type": "csv", "process": self._process_csv_skills}
        }
        global CANDIDATE_CATALOG, OPPORTUNITY_CATALOG, INTENTS_CATALOG
        if CANDIDATE_CATALOG is None:
            CANDIDATE_CATALOG = asyncio.run(self._load_catalog_async("candidate"))
        if OPPORTUNITY_CATALOG is None:
            OPPORTUNITY_CATALOG = asyncio.run(self._load_opportunity_catalog())
        if INTENTS_CATALOG is None:
            INTENTS_CATALOG = self._load_intents()

        self.candidate_catalog = CANDIDATE_CATALOG
        self.opportunity_catalog = OPPORTUNITY_CATALOG
        self.intents = INTENTS_CATALOG

        self._cache_embeddings = {}
        self.cache_manager = CacheManager()
        self.model_pool = ModelPool()
        self.batch_processor = BatchProcessor(self.model_pool)

    def _check_and_free_models(self, timeout=600):
        if time.time() - self.last_used > timeout:
            self._encoder = None
            self._ner = None
            self._translator_fallback = None
            self._sentiment_analyzer = None
            self._intent_classifier = None
            logger.info("Modelos liberados por inactividad")
        self.last_used = time.time()

    def _load_encoder(self):
        if self._encoder is None:
            self._encoder = TFAutoModel.from_pretrained("distilbert-base-multilingual-cased", from_pt=True)
            self._encoder_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-multilingual-cased")
            logger.info("Modelo encoder y tokenizer cargados con from_pt=True")
        return self._encoder, self._encoder_tokenizer

    def _load_ner(self):
        if self._ner is None:
            self._ner = pipeline("ner", model="dslim/bert-base-NER", framework="tf", aggregation_strategy="simple")
            logger.info("Modelo NER cargado")
        return self._ner

    def _load_translator_fallback(self):
        if self._translator_fallback is None:
            self._translator_fallback = pipeline("translation", model="facebook/m2m100_418M", framework="tf", src_lang="es", tgt_lang="en")
            logger.info("Modelo de traducción local cargado: facebook/m2m100_418M")
        return self._translator_fallback

    def _load_sentiment_analyzer(self):
        if self._sentiment_analyzer is None:
            self._sentiment_analyzer = SentimentIntensityAnalyzer()
            logger.info("Analizador de sentimientos cargado")
        return self._sentiment_analyzer

    def _load_intent_classifier(self):
        if self._intent_classifier is None:
            self._intent_classifier = pipeline("text-classification", model="distilbert-base-multilingual-cased", framework="tf")
            logger.info("Clasificador de intenciones cargado")
        return self._intent_classifier

    async def _load_catalog_async(self, catalog_type: str) -> Dict[str, List[Dict[str, str]]]:
        cache_key = f"catalog_{catalog_type}"
        cached_catalog = cache.get(cache_key)
        if cached_catalog is not None:
            logger.info(f"Catálogo de {catalog_type} cargado desde caché")
            return cached_catalog

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
        
        cache.set(cache_key, catalog, timeout=CACHE_TIMEOUT)
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
            if skill_type == "Certification":
                catalog["certifications"].append(skill_dict)
            elif skill_type == "Hard Skill":
                catalog["technical"].append(skill_dict)
            elif skill_type == "Soft Skill":
                catalog["soft"].append(skill_dict)
            else:
                catalog["tools"].append(skill_dict)

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

    async def _process_opportunities(self, data: List[Dict], catalog: Dict) -> None:
        for entry in data:
            if isinstance(entry, dict) and "title" in entry:
                for category, skills in entry.get("skills", {}).items():
                    if skills:
                        translated_skills = await self._translator.translate_batch(skills)
                        for skill, translated in zip(skills, translated_skills):
                            if isinstance(translated, str):
                                lang = detect(skill)
                                catalog[category].append({"original": skill, "translated": translated.lower(), "lang": lang})
                            else:
                                logger.warning(f"Traducción fallida para {skill}: {translated}")
                                catalog[category].append({"original": skill, "translated": skill.lower(), "lang": detect(skill)})
            else:
                logger.debug(f"Entrada inválida en skills_opportunities.json: {entry}")

    async def _load_opportunity_catalog(self) -> List[Dict]:
        cache_key = "opportunity_catalog"
        cached_catalog = cache.get(cache_key)
        if cached_catalog is not None:
            logger.info(f"✅ Catálogo de oportunidades cargado desde caché")
            return cached_catalog

        logger.debug(f"[nlp] Cargando opportunity_catalog desde {FILE_PATHS['opportunity_catalog']}")
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
            cache.set(cache_key, opportunities, timeout=None)
            return opportunities
        except Exception as e:
            logger.error(f"Error al cargar {opp_path}: {e}. Usando catálogo vacío.")
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
            cache.set(cache_key, intents_data, timeout=None)
            return intents_data
        except Exception as e:
            logger.error(f"Error al cargar intents: {e}. Usando intents vacíos.")
            return {}

    async def preprocess(self, text: str) -> Dict[str, str]:
        if not text or len(text.strip()) < 3:
            return {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}
        lang = detect(text)
        translated = await self._translator.translate(text) if lang != "en" else text
        return {"original": text.lower(), "translated": translated.lower(), "lang": lang}

    async def preprocess_batch(self, texts: List[str]) -> List[Dict[str, str]]:
        langs = [detect(text) if text and len(text.strip()) >= 3 else "unknown" for text in texts]
        to_translate = [text for text, lang in zip(texts, langs) if lang != "en"]
        translated_texts = await self._translator.translate_batch(to_translate) if to_translate else []
        translated_iter = iter(translated_texts)
        return [
            {"original": text.lower(), "translated": next(translated_iter) if lang != "en" else text.lower(), "lang": lang}
            if text and len(text.strip()) >= 3 else {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}
            for text, lang in zip(texts, langs)
        ]

    async def extract_skills(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        cache_key = f"skills_{hash(text)}"
        return await self.cache_manager.get_or_set(
            cache_key,
            lambda: self._extract_skills_impl(text),
            CACHE_CONFIG['EMBEDDINGS_TTL']
        )

    async def _extract_skills_impl(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        # Implementación optimizada con procesamiento por lotes
        preprocessed = await self.preprocess(text)
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        
        if self.depth == "quick":
            skills = await self.batch_processor.process_quick(preprocessed)
        elif self.depth == "deep":
            skills = await self.batch_processor.process_deep(preprocessed)
        
        return self._deduplicate_skills(skills)

    def _classify_skill(self, skill_dict: Dict[str, str], catalog: Dict) -> None:
        skill_lower = skill_dict["translated"]
        if "cert" in skill_lower or "certificación" in skill_lower:
            catalog["certifications"].append(skill_dict)
        elif "tool" in skill_lower or "herramienta" in skill_lower:
            catalog["tools"].append(skill_dict)
        elif "soft" in skill_lower or "blanda" in skill_lower:
            catalog["soft"].append(skill_dict)
        else:
            catalog["technical"].append(skill_dict)

    def _classify_entity(self, entity_group: str) -> str:
        if entity_group in ["SKILL", "TECH"]:
            return "technical"
        if entity_group == "TOOL":
            return "tools"
        if entity_group == "CERT":
            return "certifications"
        return "soft"

    def get_text_embedding(self, text: str) -> np.ndarray:
        cache_key = f"embedding_{text}"
        cached_embedding = cache.get(cache_key)
        if cached_embedding is not None:
            return cached_embedding

        encoder, tokenizer = self._load_encoder()
        inputs = tokenizer(text, return_tensors="tf", padding=True, truncation=True, max_length=128)
        outputs = encoder(inputs["input_ids"], attention_mask=inputs["attention_mask"])
        embedding = tf.reduce_mean(outputs.last_hidden_state, axis=1).numpy()[0]
        cache.set(cache_key, embedding, timeout=3600)
        return embedding

    def get_skill_embedding(self, skill: str) -> np.ndarray:
        cache_key = f"skill_embedding_{skill}"
        cached_embedding = cache.get(cache_key)
        if cached_embedding is not None:
            return cached_embedding

        embedding = self.get_text_embedding(skill)
        cache.set(cache_key, embedding, timeout=3600)
        return embedding

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        sentiment_analyzer = self._load_sentiment_analyzer()
        sentiment = sentiment_analyzer.polarity_scores(text)
        return {
            "compound": sentiment["compound"],
            "label": "positive" if sentiment["compound"] > 0.05 else "negative" if sentiment["compound"] < -0.05 else "neutral"
        }

    def classify_intent(self, text: str) -> Dict[str, float]:
        intent_classifier = self._load_intent_classifier()
        preprocessed = asyncio.run(self.preprocess(text))
        intent_result = intent_classifier(preprocessed["translated"])[0]
        return {"intent": intent_result["label"], "confidence": intent_result["score"]}

    def match_opportunities(self, candidate_skills: Dict[str, List[Dict[str, str]]]) -> List[Dict]:
        if self.mode != "candidate":
            logger.warning("match_opportunities solo está disponible en modo 'candidate'")
            return []
        matches = []
        candidate_emb = np.mean([self.get_skill_embedding(s["translated"]) for s in sum(candidate_skills.values(), [])] or [np.zeros(768)], axis=0)
        for opp in self.opportunity_catalog:
            opp_skills = sum(opp["required_skills"].values(), [])
            opp_emb = np.mean([self.get_skill_embedding(s["translated"]) for s in opp_skills] or [np.zeros(768)], axis=0)
            score = cosine_similarity([candidate_emb], [opp_emb])[0][0]
            matches.append({"opportunity": opp["title"], "match_score": score})
        return sorted(matches, key=lambda x: x["match_score"], reverse=True)[:5]

    def get_suggested_skills(self, business_unit: str, category: str = "general") -> List[str]:
        if not self.opportunity_catalog:
            logger.warning("Catálogo de oportunidades vacío. No se pueden sugerir habilidades.")
            return []

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

    async def analyze(self, text: str) -> Dict:
        start_time = time.time()
        preprocessed = await self.preprocess(text)
        skills = await self.extract_skills(text)
        sentiment = self.analyze_sentiment(preprocessed["translated"])
        result = {
            "skills": skills["skills"],
            "sentiment": sentiment["label"],
            "sentiment_score": abs(sentiment["compound"]),
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
            result["required_skills"] = skills

        if self.depth == "quick":
            result["intent"] = self.classify_intent(text)

        return result

# 2. Pool de conexiones para solicitudes HTTP
class AsyncHTTPClient:
    def __init__(self, max_connections=100):
        self._session = None
        self._semaphore = asyncio.Semaphore(max_connections)
    
    async def get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(limit=100)
            )
        return self._session

# 3. Gestor de caché mejorado
class CacheManager:
    def __init__(self):
        self.redis_client = cache
        self._local_cache = {}
        self._last_cleanup = time.time()
    
    async def get_or_set(self, key: str, getter_func, ttl: int = 3600):
        # Intentar obtener de caché local primero
        if key in self._local_cache:
            value, expiry = self._local_cache[key]
            if time.time() < expiry:
                return value
        
        # Intentar obtener de Redis
        value = self.redis_client.get(key)
        if value is not None:
            self._local_cache[key] = (value, time.time() + ttl)
            return value
        
        # Obtener valor y almacenar en ambas cachés
        value = await getter_func()
        self.redis_client.set(key, value, timeout=ttl)
        self._local_cache[key] = (value, time.time() + ttl)
        return value

# 4. Optimización del RateLimitedTranslator
class RateLimitedTranslator:
    def __init__(self, config=TRANSLATION_CONFIG):
        self.config = config
        self.request_semaphore = asyncio.Semaphore(config['RATE_LIMIT'])
        self.daily_requests = 0
        self.last_reset = time.time()
        self.cache_manager = CacheManager()
        self.http_client = AsyncHTTPClient()
        self._translation_queue = asyncio.Queue()
        self._worker_task = None

    async def start_worker(self):
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._process_queue())

    async def _process_queue(self):
        while True:
            batch = []
            try:
                while len(batch) < self.config['BATCH_SIZE']:
                    try:
                        text = await asyncio.wait_for(
                            self._translation_queue.get(), 
                            timeout=0.1
                        )
                        batch.append(text)
                    except asyncio.TimeoutError:
                        break
                
                if batch:
                    translated = await self._translate_batch(batch)
                    for future in translated:
                        future.set_result(translated)
                
            except Exception as e:
                logger.error(f"Error en el procesamiento de la cola: {e}")
                await asyncio.sleep(1)

# 5. Optimización del NLPProcessor
class NLPProcessor:
    def __init__(self, mode: str = "candidate", analysis_depth: str = "quick", language: str = "es"):
        # ... código existente ...
        self.cache_manager = CacheManager()
        self.model_pool = ModelPool()
        self.batch_processor = BatchProcessor(self.model_pool)

    async def extract_skills(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        cache_key = f"skills_{hash(text)}"
        return await self.cache_manager.get_or_set(
            cache_key,
            lambda: self._extract_skills_impl(text),
            CACHE_CONFIG['EMBEDDINGS_TTL']
        )

    async def _extract_skills_impl(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        # Implementación optimizada con procesamiento por lotes
        preprocessed = await self.preprocess(text)
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        
        if self.depth == "quick":
            skills = await self.batch_processor.process_quick(preprocessed)
        elif self.depth == "deep":
            skills = await self.batch_processor.process_deep(preprocessed)
        
        return self._deduplicate_skills(skills)

# 6. Pool de modelos para mejor gestión de memoria
class ModelPool:
    def __init__(self, max_models=3):
        self.max_models = max_models
        self.models = {}
        self.last_used = {}
        self._lock = asyncio.Lock()

    async def get_model(self, model_type: str):
        async with self._lock:
            if model_type not in self.models:
                if len(self.models) >= self.max_models:
                    # Liberar el modelo menos usado
                    oldest = min(self.last_used.items(), key=lambda x: x[1])[0]
                    del self.models[oldest]
                    del self.last_used[oldest]
                
                self.models[model_type] = self._load_model(model_type)
            
            self.last_used[model_type] = time.time()
            return self.models[model_type]

# 7. Procesador por lotes para mejor rendimiento
class BatchProcessor:
    def __init__(self, model_pool: ModelPool):
        self.model_pool = model_pool
        self.batch_size = MODEL_CONFIG['BATCH_SIZE']

    async def process_quick(self, preprocessed: Dict) -> Dict:
        model = await self.model_pool.get_model('quick')
        return await self._process_batch(preprocessed, model)

    async def process_deep(self, preprocessed: Dict) -> Dict:
        model = await self.model_pool.get_model('deep')
        return await self._process_batch(preprocessed, model)

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