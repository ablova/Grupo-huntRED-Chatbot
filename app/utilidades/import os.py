import os
import json
import logging
import asyncio
import spacy
import numpy as np
import tensorflow as tf
from transformers import pipeline, TFAutoModel, AutoTokenizer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from typing import Dict, List, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from functools import lru_cache
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from langdetect import detect
import time
import pandas as pd
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Constantes
CACHE_TIMEOUT = 600  # 10 minutos
MAX_BATCH_SIZE = 50  # Tamaño máximo del lote
RETRY_ATTEMPTS = 3  # Intentos de reintento

# Rutas de archivos
FILE_PATHS = {
    "relax_skills": "/home/pablo/skills_data/skill_db_relax_20.json",
    "esco_skills": "/home/pablo/skills_data/ESCO_occup_skills.json",
    "tabiya_skills": "/home/pablo/skills_data/tabiya/tabiya-esco-v1.1.1/csv/skills.csv",
    "opportunity_catalog": "/home/pablo/app/utilidades/catalogs/skills.json",
    "intents": "/home/pablo/chatbot_data/intents.json"
}

# Configuraciones
MODEL_CONFIG = {
    "MAX_SEQUENCE_LENGTH": 128,
    "SIMILARITY_THRESHOLD": 0.8,
    "CONFIDENCE_THRESHOLD": 0.7,
    "BATCH_SIZE": 32
}

# Inicialización lazy de dependencias
def initialize_nlp_dependencies():
    """Inicializa dependencias pesadas solo cuando se necesitan."""
    if not hasattr(initialize_nlp_dependencies, 'initialized'):
        import nltk
        nltk.download('vader_lexicon', quiet=True)
        initialize_nlp_dependencies.initialized = True

class RateLimitedTranslator:
    """Traductor con límites de velocidad."""
    def __init__(self, source='auto', target='en'):
        initialize_nlp_dependencies()
        self.translator = GoogleTranslator(source=source, target=target)
        self.semaphore = asyncio.Semaphore(5)  # 5 solicitudes por segundo
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._lock = asyncio.Lock()

    async def translate(self, text: str) -> str:
        if not text or len(text.strip()) < 1:
            return text
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(self.executor, self.translator.translate, text)
            except Exception as e:
                logger.error(f"Error en traducción: {e}")
                return text

    async def translate_batch(self, texts: List[str]) -> List[str]:
        if not texts:
            return []
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(self.executor, self.translator.translate_batch, texts)
            except Exception as e:
                logger.error(f"Error en traducción por lotes: {e}")
                return texts

class CacheManager:
    """Gestor de caché con Redis y memoria local."""
    def __init__(self):
        self._local_cache = {}
        self._lock = asyncio.Lock()

    async def get_or_set(self, key: str, getter_func, ttl: int = 3600):
        async with self._lock:
            if key in self._local_cache:
                value, expiry = self._local_cache[key]
                if time.time() < expiry:
                    return value
            value = await getter_func()
            self._local_cache[key] = (value, time.time() + ttl)
            return value

class ModelPool:
    """Pool de modelos NLP para optimizar carga."""
    def __init__(self, max_models=3):
        self.max_models = max_models
        self.models = {}
        self.last_used = {}
        self._lock = asyncio.Lock()

    async def get_model(self, model_type: str, language: str = "es"):
        async with self._lock:
            key = f"{model_type}_{language}"
            if key not in self.models:
                if len(self.models) >= self.max_models:
                    oldest = min(self.last_used.items(), key=lambda x: x[1])[0]
                    del self.models[oldest]
                    del self.last_used[oldest]
                try:
                    if model_type == "spacy":
                        self.models[key] = spacy.load("es_core_news_sm" if language == "es" else "en_core_web_sm")
                    elif model_type == "ner":
                        self.models[key] = pipeline("ner", model="dslim/bert-base-NER", framework="tf")
                    elif model_type == "intent":
                        self.models[key] = pipeline("text-classification", model="distilbert-base-multilingual-cased", framework="tf")
                    elif model_type == "encoder":
                        self.models[key] = (
                            TFAutoModel.from_pretrained("distilbert-base-multilingual-cased"),
                            AutoTokenizer.from_pretrained("distilbert-base-multilingual-cased")
                        )
                    logger.info(f"Modelo {key} cargado")
                except Exception as e:
                    logger.error(f"Error cargando modelo {key}: {e}")
                    return None
            self.last_used[key] = time.time()
            return self.models[key]

class BatchProcessor:
    """Procesador de lotes para análisis NLP."""
    def __init__(self, model_pool: ModelPool):
        self.model_pool = model_pool
        self.batch_size = MODEL_CONFIG['BATCH_SIZE']

    async def process_quick(self, preprocessed: Dict, catalog: Dict) -> Dict:
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        spacy_model = await self.model_pool.get_model("spacy", preprocessed["lang"])
        if spacy_model:
            try:
                doc = spacy_model(preprocessed["original"])
                for ent in doc.ents:
                    category = self._classify_entity(ent.label_)
                    skills[category].append({"original": ent.text, "translated": ent.text.lower(), "lang": preprocessed["lang"]})
            except Exception as e:
                logger.error(f"Error procesando con spaCy: {e}")
        for category, skill_list in catalog.items():
            for skill_dict in skill_list:
                if skill_dict["translated"] in preprocessed["translated"]:
                    skills[category].append(skill_dict)
        return skills

    async def process_deep(self, preprocessed: Dict, catalog: Dict) -> Dict:
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        ner_model = await self.model_pool.get_model("ner")
        encoder, tokenizer = await self.model_pool.get_model("encoder")
        
        if ner_model:
            try:
                ner_results = ner_model(preprocessed["translated"])
                for res in ner_results:
                    if res["score"] > MODEL_CONFIG['CONFIDENCE_THRESHOLD']:
                        category = self._classify_entity(res["entity_group"])
                        skills[category].append({"original": res["word"], "translated": res["word"].lower(), "lang": preprocessed["lang"]})
            except Exception as e:
                logger.error(f"Error procesando NER: {e}")

        if encoder and tokenizer:
            try:
                inputs = tokenizer(preprocessed["translated"], return_tensors="tf", padding=True, truncation=True, max_length=MODEL_CONFIG['MAX_SEQUENCE_LENGTH'])
                outputs = encoder(inputs["input_ids"], attention_mask=inputs["attention_mask"])
                text_emb = tf.reduce_mean(outputs.last_hidden_state, axis=1).numpy()[0]
                for category, skill_list in catalog.items():
                    for skill_dict in skill_list:
                        skill_emb = self._get_skill_embedding(skill_dict["translated"], encoder, tokenizer)
                        similarity = cosine_similarity([text_emb], [skill_emb])[0][0]
                        if similarity > MODEL_CONFIG['SIMILARITY_THRESHOLD']:
                            skills[category].append(skill_dict)
            except Exception as e:
                logger.error(f"Error procesando embeddings: {e}")

        return skills

    def _classify_entity(self, entity_group: str) -> str:
        if entity_group in ["SKILL", "TECH"]:
            return "technical"
        elif entity_group == "TOOL":
            return "tools"
        elif entity_group == "CERT":
            return "certifications"
        return "soft"

    def _get_skill_embedding(self, skill: str, encoder, tokenizer) -> np.ndarray:
        try:
            inputs = tokenizer(skill, return_tensors="tf", padding=True, truncation=True, max_length=MODEL_CONFIG['MAX_SEQUENCE_LENGTH'])
            outputs = encoder(inputs["input_ids"], attention_mask=inputs["attention_mask"])
            return tf.reduce_mean(outputs.last_hidden_state, axis=1).numpy()[0]
        except Exception as e:
            logger.error(f"Error obteniendo embedding: {e}")
            return np.zeros(768)

class NLPProcessor:
    """Procesador NLP principal para el sistema de reclutamiento."""
    def __init__(self, mode: str = "candidate", analysis_depth: str = "quick", language: str = "es"):
        initialize_nlp_dependencies()
        self.mode = mode
        self.depth = analysis_depth
        self.language = language
        self.translator = RateLimitedTranslator()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.cache_manager = CacheManager()
        self.model_pool = ModelPool()
        self.batch_processor = BatchProcessor(self.model_pool)
        self.catalogs = {}
        logger.info(f"NLPProcessor inicializado: modo={mode}, profundidad={analysis_depth}, idioma={language}")

    async def _load_catalog(self, path: str, file_type: str) -> Dict:
        """Carga un catálogo desde archivo."""
        cache_key = f"catalog_{path}"
        async def load():
            if not os.path.exists(path):
                logger.warning(f"Archivo no encontrado: {path}")
                return {}
            try:
                if file_type == "json":
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                elif file_type == "csv":
                    return pd.read_csv(path).to_dict(orient="records")
                return {}
            except Exception as e:
                logger.error(f"Error cargando {path}: {e}")
                return {}
        return await self.cache_manager.get_or_set(cache_key, load, CACHE_TIMEOUT)

    async def _ensure_catalogs_loaded(self):
        """Carga todos los catálogos necesarios."""
        if not self.catalogs.get("candidate"):
            self.catalogs["candidate"] = {
                "technical": [], "soft": [], "tools": [], "certifications": []
            }
            for key, path in FILE_PATHS.items():
                if key in ["opportunity_catalog", "intents"]:
                    continue
                data = await self._load_catalog(path, "json" if key.endswith("json") else "csv")
                self._process_catalog(data, self.catalogs["candidate"])
        if not self.catalogs.get("opportunity") and self.mode == "opportunity":
            data = await self._load_catalog(FILE_PATHS["opportunity_catalog"], "json")
            self.catalogs["opportunity"] = self._process_opportunity_catalog(data)
        if not self.catalogs.get("intents") and self.depth == "quick":
            data = await self._load_catalog(FILE_PATHS["intents"], "json")
            self.catalogs["intents"] = data.get("intents", {})

    def _process_catalog(self, data: Any, catalog: Dict):
        """Procesa datos de catálogos y los normaliza."""
        if isinstance(data, dict):
            for skill_dict in data.values():
                skill = skill_dict.get("skill_name", "")
                skill_type = skill_dict.get("skill_type", "technical")
                if skill:
                    catalog[skill_type].append({"original": skill, "translated": skill.lower(), "lang": "es"})
        elif isinstance(data, list):
            for row in data:
                skill = row.get("PREFERREDLABEL", "")
                if skill:
                    catalog["technical"].append({"original": skill, "translated": skill.lower(), "lang": "es"})

    def _process_opportunity_catalog(self, data: Dict) -> List[Dict]:
        """Procesa el catálogo de oportunidades."""
        opportunities = []
        if isinstance(data, dict):
            for bu, roles in data.items():
                for role, skills in roles.items():
                    skill_dict = {
                        "technical": [{"original": s, "translated": s.lower(), "lang": "es"} for s in skills.get("Habilidades Técnicas", [])],
                        "soft": [{"original": s, "translated": s.lower(), "lang": "es"} for s in skills.get("Habilidades Blandas", [])],
                        "tools": [{"original": s, "translated": s.lower(), "lang": "es"} for s in skills.get("Herramientas", [])],
                        "certifications": [{"original": s, "translated": s.lower(), "lang": "es"} for s in skills.get("Certificaciones", [])]
                    }
                    opportunities.append({"title": f"{role} en {bu}", "required_skills": skill_dict})
        return opportunities

    async def preprocess(self, text: str) -> Dict[str, str]:
        """Preprocesa texto para análisis."""
        if not text or len(text.strip()) < 3:
            return {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}
        lang = detect(text)
        translated = await self.translator.translate(text) if lang != "en" else text
        return {"original": text.lower(), "translated": translated.lower(), "lang": lang}

    async def extract_skills(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """Extrae habilidades del texto."""
        await self._ensure_catalogs_loaded()
        preprocessed = await self.preprocess(text)
        catalog = self.catalogs.get(self.mode, {})
        skills = await (self.batch_processor.process_quick(preprocessed, catalog) if self.depth == "quick" else 
                        self.batch_processor.process_deep(preprocessed, catalog))
        return self._deduplicate_skills(skills)

    def _deduplicate_skills(self, skills: Dict) -> Dict:
        """Elimina habilidades duplicadas."""
        for category in skills:
            seen = set()
            skills[category] = [s for s in skills[category] if not (s["translated"] in seen or seen.add(s["translated"]))]
        return {"skills": skills}

    async def analyze(self, text: str) -> Dict:
        """Analiza texto completo."""
        start_time = time.time()
        preprocessed = await self.preprocess(text)
        skills = await self.extract_skills(text)
        sentiment = self.analyze_sentiment(preprocessed["translated"])
        intent = await self.classify_intent(text) if self.depth == "quick" else {"intent": "unknown", "confidence": 0.0}

        result = {
            "skills": skills["skills"],
            "sentiment": sentiment["label"],
            "sentiment_score": sentiment["compound"],
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
            result["opportunities"] = await self.match_opportunities(skills["skills"])
        return result

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analiza el sentimiento del texto."""
        try:
            scores = self.sentiment_analyzer.polarity_scores(text)
            return {
                "compound": scores["compound"],
                "label": "positive" if scores["compound"] > 0.05 else "negative" if scores["compound"] < -0.05 else "neutral"
            }
        except Exception as e:
            logger.error(f"Error analizando sentimiento: {e}")
            return {"compound": 0.0, "label": "neutral"}

    @retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def classify_intent(self, text: str) -> Dict[str, float]:
        """Clasifica la intención del texto."""
        intent_classifier = await self.model_pool.get_model("intent")
        if intent_classifier:
            preprocessed = await self.preprocess(text)
            result = intent_classifier(preprocessed["translated"])[0]
            confidence = result["score"]
            intent = result["label"] if confidence > MODEL_CONFIG['CONFIDENCE_THRESHOLD'] else "unknown"
            return {"intent": intent, "confidence": confidence}
        return {"intent": "unknown", "confidence": 0.0}

    async def match_opportunities(self, candidate_skills: Dict[str, List[Dict[str, str]]]) -> List[Dict]:
        """Empareja habilidades del candidato con oportunidades."""
        if self.mode != "candidate":
            return []
        await self._ensure_catalogs_loaded()
        matches = []
        candidate_emb = np.mean([self.get_text_embedding(s["translated"]) for s in sum(candidate_skills.values(), [])] or [np.zeros(768)], axis=0)
        for opp in self.catalogs.get("opportunity", []):
            opp_skills = sum(opp["required_skills"].values(), [])
            opp_emb = np.mean([self.get_text_embedding(s["translated"]) for s in opp_skills] or [np.zeros(768)], axis=0)
            score = cosine_similarity([candidate_emb], [opp_emb])[0][0]
            matches.append({"opportunity": opp["title"], "match_score": float(score)})
        return sorted(matches, key=lambda x: x["match_score"], reverse=True)[:5]

    @lru_cache(maxsize=1000)
    def get_text_embedding(self, text: str) -> np.ndarray:
        """Obtiene embeddings de texto."""
        encoder, tokenizer = asyncio.run(self.model_pool.get_model("encoder"))
        if encoder and tokenizer:
            inputs = tokenizer(text, return_tensors="tf", padding=True, truncation=True, max_length=MODEL_CONFIG['MAX_SEQUENCE_LENGTH'])
            outputs = encoder(inputs["input_ids"], attention_mask=inputs["attention_mask"])
            return tf.reduce_mean(outputs.last_hidden_state, axis=1).numpy()[0]
        return np.zeros(768)

    async def analyze_opportunity(self, description: str) -> Dict:
        """Analiza una descripción de oportunidad."""
        analysis = await self.analyze(description)
        return {
            "details": {
                "skills": analysis["skills"],
                "location": "Unknown",  # Placeholder, ajustar según necesidad
                "contract_type": None  # Placeholder, ajustar según necesidad
            },
            "sentiment": analysis["sentiment"],
            "job_classification": "Unknown"  # Placeholder, ajustar según necesidad
        }

if __name__ == "__main__":
    nlp = NLPProcessor(mode="candidate", analysis_depth="quick")
    text = "Tengo experiencia en Python y trabajo en equipo."
    result = asyncio.run(nlp.analyze(text))
    print(json.dumps(result, indent=2, ensure_ascii=False))