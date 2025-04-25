# Ubicación del archivo: /home/pablo/app/chatbot/nlp.py
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
import spacy
import asyncio
from collections import defaultdict
import psutil
import gc
import time
import sys
sys.path.append('/home/pablo')  # Temporal hasta configurar PYTHONPATH

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pablo/logs/nlp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('nlp')

# Intentar importar TensorFlow y TensorFlow Hub
try:
    import tensorflow as tf
    import tensorflow_hub as hub
    TF_AVAILABLE = True
    logger.info(f"TensorFlow {tf.__version__} y TensorFlow Hub importados correctamente.")
except ImportError as e:
    logger.error(f"Error importando TensorFlow o TensorFlow Hub: {e}")
    TF_AVAILABLE = False
    tf = None
    hub = None

# Configuraciones escalables
USE_EMBEDDINGS = True if TF_AVAILABLE else False
USE_SKILLNER = False
RAM_LIMIT = 8 * 1024 * 1024 * 1024  # 8 GB
EMBEDDINGS_READY = False

# Verificar caché de embeddings
EMBEDDINGS_CACHE = "/home/pablo/skills_data/embeddings_cache.pkl"
if os.path.exists(EMBEDDINGS_CACHE):
    EMBEDDINGS_READY = True
    logger.info("Embeddings cache encontrado.")

# Constantes
FILE_PATHS = {
    "candidate_quick": "/home/pablo/skills_data/skill_db_relax_20.json",
    "candidate_deep": "/home/pablo/skills_data/ESCO_occup_skills.json",
    "opportunity_quick": "/home/pablo/app/utilidades/catalogs/skills.json",
    "opportunity_deep": "/home/pablo/skills_data/ESCO_occup_skills.json",
}
LOCK_FILE = "/home/pablo/skills_data/nlp_init.lock"

# Cachés
translation_cache = TTLCache(maxsize=1000, ttl=3600)
embeddings_cache = TTLCache(maxsize=1000, ttl=3600)

# Modelos globales
nlp_spacy = None
use_model = None
skill_extractor = None

# Cargar extractors
try:
    from app.chatbot.extractors import ESCOExtractor, NICEExtractor, unify_data
except ImportError as e:
    logger.error(f"Error importando extractors: {e}")
    ESCOExtractor = None
    NICEExtractor = None
    unify_data = None

def load_skills_catalog(mode: str, analysis_depth: str) -> Dict[str, List[Dict[str, str]]]:
    """Carga un catálogo de habilidades según el modo y nivel de procesamiento."""
    catalog = {"technical": [], "soft": [], "tools": [], "certifications": []}
    key = f"{mode}_{analysis_depth}"

    if key == "candidate_quick":
        try:
            with open(FILE_PATHS["candidate_quick"], "r") as f:
                data = json.load(f)
                type_mapping = {
                    "Hard Skill": "technical",
                    "Soft Skill": "soft",
                    "Tool": "tools",
                    "Certification": "certifications"
                }
                for skill_id, skill_data in data.items():
                    skill_type = skill_data.get("skill_type", "Hard Skill")
                    category = type_mapping.get(skill_type, "technical")
                    skill_cleaned = skill_data.get("skill_cleaned", skill_data.get("skill_name", "")).lower()
                    if skill_cleaned:
                        catalog[category].append({"original": skill_cleaned})
            total_skills = sum(len(v) for v in catalog.values())
            logger.info(f"Cargadas {total_skills} habilidades desde skill_db_relax_20.json (candidate_quick)")
            return catalog
        except Exception as e:
            logger.error(f"Error cargando skill_db_relax_20.json: {e}, usando catálogo vacío.")
            return catalog

    elif key == "candidate_deep":
        try:
            with open(FILE_PATHS["candidate_deep"], "r") as f:
                data = json.load(f)
                skill_count = 0
                for occupation, occ_data in data.items():
                    logger.debug(f"Ocupación: {occupation}, campos disponibles: {list(occ_data.keys())}")
                    for skill_field in ["hasEssentialSkill", "hasOptionalSkill"]:
                        for skill in occ_data.get(skill_field, []):
                            skill_name = skill.get("title", "").lower()
                            if skill_name:
                                catalog["technical"].append({"original": skill_name})
                                skill_count += 1
                                logger.debug(f"Habilidad encontrada: {skill_name}")
                    # Limitar para pruebas iniciales
                    if skill_count >= 10000:
                        break
                total_skills = sum(len(v) for v in catalog.values())
                logger.info(f"Cargadas {total_skills} habilidades desde ESCO_occup_skills.json (candidate_deep)")
                return catalog
        except Exception as e:
            logger.error(f"Error cargando ESCO_occup_skills.json: {e}, usando catálogo vacío.")
            return catalog

    elif key == "opportunity_quick":
        try:
            with open(FILE_PATHS["opportunity_quick"], "r") as f:
                data = json.load(f)
                for role_group, roles in data.items():
                    for role, categories in roles.items():
                        for category, skills in categories.items():
                            target_category = {
                                "Habilidades Técnicas": "technical",
                                "Habilidades Blandas": "soft",
                                "Herramientas": "tools",
                                "Certificaciones": "certifications"
                            }.get(category, "technical")
                            for skill in skills:
                                catalog[target_category].append({"original": skill.lower(), "role": role})
                total_skills = sum(len(v) for v in catalog.values())
                logger.info(f"Cargadas {total_skills} habilidades desde skills.json (opportunity_quick)")
                return catalog
        except Exception as e:
            logger.error(f"Error cargando skills.json: {e}, usando catálogo vacío.")
            return catalog

    elif key == "opportunity_deep":
        try:
            with open(FILE_PATHS["opportunity_deep"], "r") as f:
                data = json.load(f)
                skill_count = 0
                for occupation, occ_data in data.items():
                    role = occ_data.get("preferredLabel", {}).get("es", occupation).lower()
                    logger.debug(f"Ocupación: {occupation}, campos disponibles: {list(occ_data.keys())}")
                    for skill_field in ["hasEssentialSkill", "hasOptionalSkill"]:
                        for skill in occ_data.get(skill_field, []):
                            skill_name = skill.get("title", "").lower()
                            if skill_name:
                                catalog["technical"].append({"original": skill_name, "role": role})
                                skill_count += 1
                                logger.debug(f"Habilidad encontrada: {skill_name}")
                    # Limitar para pruebas iniciales
                    if skill_count >= 10000:
                        break
                total_skills = sum(len(v) for v in catalog.values())
                logger.info(f"Cargadas {total_skills} habilidades desde ESCO_occup_skills.json (opportunity_deep)")
                return catalog
        except Exception as e:
            logger.error(f"Error cargando ESCO_occup_skills.json: {e}, usando catálogo vacío.")
            return catalog

    return catalog

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
    if use_model is None and USE_EMBEDDINGS and TF_AVAILABLE:
        try:
            model_path = "/home/pablo/tfhub_cache/use_multilingual_4/use4"
            logger.debug(f"Intentando cargar modelo desde: {model_path}")
            tf.config.threading.set_intra_op_parallelism_threads(1)
            tf.config.threading.set_inter_op_parallelism_threads(1)
            use_model = hub.load(model_path)
            logger.info("Modelo USE v4 cargado con límite de CPU al 25%.")
        except Exception as e:
            logger.error(f"Error cargando USE desde {model_path}: {e}", exc_info=True)
            use_model = None
    else:
        logger.debug(f"Estado inicial: use_model={use_model}, USE_EMBEDDINGS={USE_EMBEDDINGS}, TF_AVAILABLE={TF_AVAILABLE}")
    return use_model

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return np.dot(a, b) / (norm_a * norm_b)

class NLPProcessor:
    def __init__(self, mode: str = "candidate", language: str = "es", analysis_depth: str = "quick"):
        self.mode = mode
        self.language = language
        self.requested_depth = analysis_depth
        self.nlp = load_spacy_model(language)
        self.skills_catalog = load_skills_catalog(mode, analysis_depth)
        self.skill_sets = {
            category: set(skill["original"].lower() for skill in skills_list if isinstance(skill, dict) and skill.get("original"))
            for category, skills_list in self.skills_catalog.items()
        }
        self.effective_depth = analysis_depth
        if analysis_depth == "deep" and not (USE_EMBEDDINGS and TF_AVAILABLE):
            logger.info("Modo 'deep' solicitado pero embeddings no disponibles. Usando 'quick'.")
            self.effective_depth = "quick"
            self.skills_catalog = load_skills_catalog(mode, "quick")
            self.skill_sets = {
                category: set(skill["original"].lower() for skill in skills_list if isinstance(skill, dict) and skill.get("original"))
                for category, skills_list in self.skills_catalog.items()
            }
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
        if self.effective_depth != "deep" or not USE_EMBEDDINGS:
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
        elif self.effective_depth == "deep":
            return await self._extract_skills_deep(text)
        return {"technical": [], "soft": [], "tools": [], "certifications": []}

    def _extract_skills_quick(self, text: str) -> Dict[str, List[Dict[str, any]]]:
        doc = self.nlp(text.lower())
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        for token in doc:
            skill_name = token.text
            for category, skill_set in self.skill_sets.items():
                if skill_name in skill_set:
                    skills[category].append({"original": skill_name, "role": self.skills_catalog[category][0].get("role", "") if self.mode == "opportunity" else ""})
        return skills

    async def _extract_skills_deep(self, text: str) -> Dict[str, List[Dict[str, any]]]:
        preprocessed = await self.preprocess(text)
        text_emb = self.get_text_embedding(preprocessed["translated"])
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        for category, skills_list in self.skills_catalog.items():
            for skill in skills_list:
                skill_name = skill.get("original", "")
                if skill_name:
                    skill_emb = self.get_text_embedding(skill_name)
                    similarity = cosine_similarity(text_emb, skill_emb)
                    if similarity > 0.8:
                        skills[category].append({"original": skill_name, "role": skill.get("role", "") if self.mode == "opportunity" else ""})
        return skills

    def analyze_sentiment(self, text: str) -> str:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        return "positive" if polarity > 0.05 else "negative" if polarity < -0.05 else "neutral"

    def infer_opportunities(self, skills: Dict[str, List[Dict[str, any]]]) -> List[Dict[str, any]]:
        if self.mode != "opportunity":
            return []
        opportunities = []
        role_skills_count = {}
        for category, skill_list in skills.items():
            for skill in skill_list:
                role = skill.get("role", "")
                if role:
                    role_skills_count[role] = role_skills_count.get(role, 0) + 1
        for role, count in role_skills_count.items():
            if count >= 3:
                opportunities.append({"role": role, "confidence": count / max(role_skills_count.values(), 1)})
        return sorted(opportunities, key=lambda x: x["confidence"], reverse=True)

    async def analyze(self, text: str) -> Dict:
        start_time = time.time()
        preprocessed = await self.preprocess(text)
        skills = await self.extract_skills(text)
        sentiment = self.analyze_sentiment(preprocessed["translated"])
        opportunities = self.infer_opportunities(skills) if self.mode == "opportunity" else []
        execution_time = time.time() - start_time
        result = {
            "skills": skills,
            "sentiment": sentiment,
            "metadata": {
                "execution_time": execution_time,
                "original_text": preprocessed["original"],
                "translated_text": preprocessed["translated"],
                "detected_language": preprocessed["lang"],
                "analysis_depth": self.effective_depth
            }
        }
        if opportunities:
            result["opportunities"] = opportunities
        return result

if __name__ == "__main__":
    async def test_nlp():
        for mode in ["candidate", "opportunity"]:
            for depth in ["quick", "deep"]:
                print(f"\nProbando modo: {mode}, profundidad: {depth}")
                nlp = NLPProcessor(mode=mode, analysis_depth=depth)
                text = "Tengo experiencia en Python, liderazgo, y gestión de proyectos."
                result = await nlp.analyze(text)
                print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(test_nlp())