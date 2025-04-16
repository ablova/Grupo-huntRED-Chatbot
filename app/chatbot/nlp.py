# /home/pablollh/app/chatbot/nlp.py
import os
import json
import logging
import asyncio
import spacy
import numpy as np
from typing import Dict, List, Optional
from cachetools import TTLCache
from textblob import TextBlob
from langdetect import detect
from deep_translator import GoogleTranslator
from filelock import FileLock
import tensorflow as tf
import tensorflow_hub as hub
from sklearn.metrics.pairwise import cosine_similarity
import psutil
import gc
import time

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pablo/logs/nlp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuraciones escalables
USE_EMBEDDINGS = False  # Activar embeddings solo si están listos y hay recursos
USE_SKILLNER = False    # Activar SkillNer solo si hay recursos suficientes
RAM_LIMIT = 8 * 1024 * 1024 * 1024  # 8 GB, umbral para embeddings
EMBEDDINGS_READY = False  # Indicador de si los embeddings están listos
# Configuraciones escalables
DISABLE_EXTRACTORS = True  # Deshabilitar extractors.py temporalmente

# Verificar si el caché de embeddings existe
EMBEDDINGS_CACHE = "/home/pablo/skills_data/embeddings_cache.pkl"
if os.path.exists(EMBEDDINGS_CACHE):
    EMBEDDINGS_READY = True
    logger.info("Embeddings cache encontrado. Modo 'deep' disponible si hay suficiente RAM.")

# Verificar recursos disponibles
AVAILABLE_RAM = psutil.virtual_memory().available
if AVAILABLE_RAM > RAM_LIMIT and EMBEDDINGS_READY:
    USE_EMBEDDINGS = True
    logger.info("Modo embeddings activado debido a suficiente RAM y embeddings listos.")

# Constantes
FILE_PATHS = {
    "relax_skills": "/home/pablo/skills_data/skill_db_relax_20.json",
    "esco_skills": "/home/pablo/skills_data/ESCO_occup_skills.json",
    "opportunity_catalog": "/home/pablollh/app/utilidades/catalogs/skills.json",
}
LOCK_FILE = "/home/pablo/skills_data/nlp_init.lock"

# Cachés
translation_cache = TTLCache(maxsize=1000, ttl=3600)
embeddings_cache = TTLCache(maxsize=1000, ttl=3600)

# Modelos globales
nlp_spacy = None
use_model = None
skill_extractor = None

# Cargar catálogo de habilidades desde extractors.py
from app.chatbot.extractors import ESCOExtractor, NICEExtractor, unify_data

# Cargar catálogo de habilidades con respaldo
def load_skills_catalog():
    """Carga un catálogo de habilidades, usando un respaldo local si DISABLE_EXTRACTORS es True."""
    if DISABLE_EXTRACTORS:
        try:
            with open("/home/pablo/skills_data/skill_db_relax_20.json", "r") as f:  #O puede ser /home/pablollh/app/utilidades/catalogs/skills.json
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando respaldo: {e}, usando catálogo vacío.")
            return {"technical": [], "soft": [], "tools": [], "certifications": []}
    else:
        try:
            from app.chatbot.extractors import ESCOExtractor, NICEExtractor, unify_data
            esco_ext = ESCOExtractor()
            nice_ext = NICEExtractor()
            esco_skills = esco_ext.get_skills(language="es", limit=100)
            nice_skills = nice_ext.get_skills(sheet_name="Skills")
            unified_skills = unify_data(esco_skills, nice_skills)
            catalog = {"technical": [], "soft": [], "tools": [], "certifications": []}
            for skill in unified_skills:
                skill_name = skill.get("name", "").lower()
                skill_type = skill.get("type", "skill")
                if skill_type == "skill":
                    catalog["technical"].append({"original": skill_name})
            logger.info(f"Cargadas {len(unified_skills)} habilidades en el catálogo.")
            return catalog
        except Exception as e:
            logger.error(f"Error cargando catálogo: {e}, usando catálogo vacío.")
            return {"technical": [], "soft": [], "tools": [], "certifications": []}

def load_spacy_model(language: str = "es"):
    global nlp_spacy
    if nlp_spacy is None:
        model_name = "es_core_news_md" if language == "es" else "en_core_web_md"
        try:
            nlp_spacy = spacy.load(model_name, disable=["ner", "parser"])
            logger.info(f"Modelo spaCy '{model_name}' cargado.")
        except Exception as e:
            logger.error(f"Error cargando spaCy: {e}")
    return nlp_spacy

def load_use_model():
    global use_model
    if use_model is None and USE_EMBEDDINGS:
        try:
            # Limitar uso de CPU
            tf.config.threading.set_intra_op_parallelism_threads(1)
            tf.config.threading.set_inter_op_parallelism_threads(1)
            use_model = hub.load("https://tfhub.dev/google/universal-sentence-encoder-multilingual/4")
            logger.info("Modelo USE v4 cargado con límite de CPU al 25%.")
        except Exception as e:
            logger.error(f"Error cargando USE: {e}")
    return use_model

def load_skillner():
    global skill_extractor
    if skill_extractor is None and USE_SKILLNER:
        try:
            from skillNer.skill_extractor_class import SkillExtractor
            from skillNer.general_params import SKILL_DB
            nlp = load_spacy_model()
            if nlp:
                skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher(nlp.vocab, attr="LOWER"))
                logger.info("SkillNer cargado.")
        except Exception as e:
            logger.error(f"Error cargando SkillNer: {e}")
    return skill_extractor

class NLPProcessor:
    def __init__(self, mode: str = "candidate", language: str = "es", analysis_depth: str = "quick"):
        self.mode = mode
        self.language = language
        self.requested_depth = analysis_depth  # Guardamos la profundidad solicitada
        self.nlp = load_spacy_model(language)
        self.skills_catalog = load_skills_catalog()  # Cargar catálogo al inicializar
        
        # Determinar el modo efectivo basado en recursos y embeddings
        self.effective_depth = "quick"
        if analysis_depth == "deep" and USE_EMBEDDINGS:
            self.effective_depth = "deep"
            load_use_model()
            load_skillner()
        elif analysis_depth == "deep":
            logger.info("Modo 'deep' solicitado pero no disponible. Usando 'quick'.")
        
        logger.info(f"Modo efectivo: {self.effective_depth}")

    async def preprocess(self, text: str) -> Dict[str, str]:
        if self.effective_depth == "quick":
            return {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}
        cache_key = f"preprocess_{text}"
        if cache_key in translation_cache:
            return translation_cache[cache_key]
        try:
            lang = detect(text)
            if lang != "en":
                translator = GoogleTranslator(source='auto', target='en')
                translated = translator.translate(text)
            else:
                translated = text
            result = {"original": text.lower(), "translated": translated.lower(), "lang": lang}
            translation_cache[cache_key] = result
            return result
        except Exception as e:
            logger.warning(f"Error en preprocesamiento: {e}")
            return {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}

    def get_text_embedding(self, text: str) -> np.ndarray:
        if self.effective_depth == "quick" or not USE_EMBEDDINGS:
            return np.zeros(512)
        cache_key = f"embedding_{text}"
        if cache_key in embeddings_cache:
            return embeddings_cache[cache_key]
        try:
            model = load_use_model()
            if model:
                embedding = model([text]).numpy()[0]
                embeddings_cache[cache_key] = embedding
                return embedding
            return np.zeros(512)
        except Exception as e:
            logger.warning(f"Error generando embedding: {e}")
            return np.zeros(512)

    async def extract_skills(self, text: str) -> Dict[str, List[Dict[str, any]]]:
        if self.effective_depth == "quick":
            return self._extract_skills_quick(text)
        elif USE_SKILLNER and skill_extractor:
            return self._extract_skills_skillner(text)
        elif USE_EMBEDDINGS:
            return await self._extract_skills_embeddings(text)
        return {"technical": [], "soft": [], "tools": [], "certifications": []}

    def _extract_skills_quick(self, text: str) -> Dict[str, List[Dict[str, any]]]:
        doc = self.nlp(text.lower())
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        for token in doc:
            skill_name = token.text
            for category, skills_list in self.skills_catalog.items():
                if any(skill["original"] == skill_name for skill in skills_list):
                    skills[category].append({"original": skill_name})
        return skills

    async def _extract_skills_embeddings(self, text: str) -> Dict[str, List[Dict[str, any]]]:
        preprocessed = await self.preprocess(text)
        text_emb = self.get_text_embedding(preprocessed["translated"])
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        
        for category, skills_list in self.skills_catalog.items():
            for skill in skills_list:
                skill_emb = self.get_text_embedding(skill["original"])
                similarity = cosine_similarity([text_emb], [skill_emb])[0][0]
                if similarity > 0.8:
                    skills[category].append(skill)
        return skills

    def _extract_skills_skillner(self, text: str) -> Dict[str, List[Dict[str, any]]]:
        if skill_extractor:
            doc = self.nlp(text)
            res = skill_extractor.annotate(doc)
            skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
            for match_type in ["full_matches", "ngram_scored"]:
                for match in res.get("results", {}).get(match_type, []):
                    skill_name = match.get("doc_node_value", "").lower()
                    if skill_name:
                        skills["technical"].append({"original": skill_name})  # Clasificación básica
            return skills
        return {"technical": [], "soft": [], "tools": [], "certifications": []}

    def analyze_sentiment(self, text: str) -> str:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        return "positive" if polarity > 0.05 else "negative" if polarity < -0.05 else "neutral"

    async def analyze(self, text: str) -> Dict:
        start_time = time.time()
        preprocessed = await self.preprocess(text)
        skills = await self.extract_skills(text)
        sentiment = self.analyze_sentiment(preprocessed["translated"])
        execution_time = time.time() - start_time
        return {
            "skills": skills,
            "sentiment": sentiment,
            "metadata": {
                "execution_time": execution_time,
                "original_text": preprocessed["original"],
                "translated_text": preprocessed["translated"],
                "detected_language": preprocessed["lang"],
                "analysis_depth": self.effective_depth  # Indicar el modo efectivo usado
            }
        }

if __name__ == "__main__":
    nlp = NLPProcessor(analysis_depth="deep")  # Solicita 'deep', pero usará 'quick' si no hay recursos
    text = "Tengo experiencia en Python y liderazgo."
    result = asyncio.run(nlp.analyze(text))
    print(json.dumps(result, indent=2, ensure_ascii=False))