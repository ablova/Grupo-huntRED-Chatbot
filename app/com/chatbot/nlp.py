# /home/pablo/app/com/chatbot/nlp.py
import os
import json
import logging
import asyncio
import pickle
import spacy
import numpy as np
from typing import Dict, List, Optional
from cachetools import TTLCache
from textblob import TextBlob
from langdetect import detect
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
try:
    import tensorflow as tf
    import tensorflow_hub as hub
    import tensorflow_text as text  # Required for SentencepieceOp
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    tf = None
    hub = None
    text = None
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

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

# Log TensorFlow import success
if TF_AVAILABLE:
    logger.info(f"TensorFlow {tf.__version__} y TensorFlow Hub importados correctamente.")

# Configuraciones desde settings.py
USE_EMBEDDINGS = TF_AVAILABLE and os.getenv('USE_EMBEDDINGS', 'true').lower() == 'true'
USE_ROBERTA = TRANSFORMERS_AVAILABLE and os.getenv('USE_ROBERTA', 'true').lower() == 'true'
MAX_SKILLS = int(os.getenv('MAX_SKILLS', 10000))
RAM_LIMIT = 8 * 1024 * 1024 * 1024  # 8 GB
EMBEDDINGS_CACHE = "/home/pablo/skills_data/embeddings_cache.pkl"
EMBEDDINGS_READY = os.path.exists(EMBEDDINGS_CACHE)

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
skill_embeddings_cache = None

# Modelos globales
nlp_spacy = None
use_model = None
roberta_model = None
roberta_tokenizer = None

def initialize_tensorflow():
    """Configura TensorFlow para evitar conflictos."""
    if not TF_AVAILABLE:
        logger.warning("TensorFlow no disponible, omitiendo inicialización.")
        return
    try:
        tf.config.set_soft_device_placement(True)
        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Disable GPU
        logger.info("TensorFlow configurado con soft placement y hilos mínimos (CPU-only).")
    except Exception as e:
        logger.error(f"Error inicializando TensorFlow: {str(e)}")

def load_spacy_model(language: str = "es"):
    """Carga el modelo spaCy de manera lazy."""
    global nlp_spacy
    if nlp_spacy is None:
        model_name = "es_core_news_md" if language == "es" else "en_core_web_md"
        try:
            nlp_spacy = spacy.load(model_name, disable=["ner", "parser"])
            logger.info(f"Modelo spaCy '{model_name}' cargado.")
        except Exception as e:
            logger.error(f"Error cargando spaCy: {str(e)}")
            nlp_spacy = None
    return nlp_spacy

def load_use_model():
    """Carga el modelo USE de manera lazy."""
    global use_model
    if use_model is None and USE_EMBEDDINGS and TF_AVAILABLE:
        try:
            model_path = "https://tfhub.dev/google/universal-sentence-encoder-multilingual/3"
            use_model = hub.load(model_path)
            logger.info("Modelo USE multilingüe cargado.")
        except Exception as e:
            logger.error(f"Error cargando USE: {str(e)}")
            use_model = None
    return use_model

def load_roberta_model():
    """Carga el modelo RoBERTa para análisis de sentimiento."""
    global roberta_model, roberta_tokenizer
    if USE_ROBERTA and TRANSFORMERS_AVAILABLE and roberta_model is None:
        try:
            model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            roberta_tokenizer = AutoTokenizer.from_pretrained(model_name)
            roberta_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            logger.info(f"Modelo RoBERTa '{model_name}' cargado para análisis de sentimiento.")
        except Exception as e:
            logger.error(f"Error cargando RoBERTa: {str(e)}")
            roberta_model = None
            roberta_tokenizer = None
    return roberta_model, roberta_tokenizer

def load_skill_embeddings(catalog_key: str) -> Dict[str, np.ndarray]:
    """Carga embeddings pre-generados desde caché."""
    global skill_embeddings_cache
    if skill_embeddings_cache is None and EMBEDDINGS_READY:
        try:
            with open(EMBEDDINGS_CACHE, "rb") as f:
                cached_data = pickle.load(f)
            if cached_data.get("version") == "1.0" and catalog_key in cached_data.get("catalogs", []):
                skill_embeddings_cache = cached_data.get("embeddings", {})
                logger.info(f"Embeddings pre-generados cargados para {catalog_key} desde {EMBEDDINGS_CACHE}")
            else:
                logger.warning(f"Caché de embeddings inválido o no contiene {catalog_key}")
                skill_embeddings_cache = {}
        except Exception as e:
            logger.error(f"Error cargando embeddings desde {EMBEDDINGS_CACHE}: {str(e)}")
            skill_embeddings_cache = {}
    return skill_embeddings_cache or {}

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calcula la similitud coseno entre dos vectores."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return np.dot(a, b) / (norm_a * norm_b)

def load_skills_catalog(mode: str, analysis_depth: str) -> Dict[str, List[Dict[str, str]]]:
    """Carga un catálogo de habilidades según el modo y nivel de procesamiento."""
    catalog = {"technical": [], "soft": [], "tools": [], "certifications": []}
    key = f"{mode}_{analysis_depth}"
    file_path = FILE_PATHS.get(key)

    if not file_path or not os.path.exists(file_path):
        logger.error(f"Archivo no encontrado: {file_path}. Usando catálogo vacío.")
        return catalog

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if key == "candidate_quick":
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
            elif key == "candidate_deep":
                skill_count = 0
                for _, occ_data in data.items():
                    for skill_field in ["hasEssentialSkill", "hasOptionalSkill"]:
                        for skill in occ_data.get(skill_field, []):
                            skill_name = skill.get("title", "").lower()
                            if skill_name:
                                if "certificación" in skill_name or "certificado" in skill_name:
                                    category = "certifications"
                                elif "herramienta" in skill_name or "tool" in skill_name:
                                    category = "tools"
                                elif "blanda" in skill_name or "soft" in skill_name:
                                    category = "soft"
                                else:
                                    category = "technical"
                                catalog[category].append({"original": skill_name})
                                skill_count += 1
                                if skill_count >= MAX_SKILLS:
                                    break
                    if skill_count >= MAX_SKILLS:
                        break
            elif key == "opportunity_quick":
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
            elif key == "opportunity_deep":
                skill_count = 0
                for _, occ_data in data.items():
                    role = occ_data.get("preferredLabel", {}).get("es", "").lower()
                    for skill_field in ["hasEssentialSkill", "hasOptionalSkill"]:
                        for skill in occ_data.get(skill_field, []):
                            skill_name = skill.get("title", "").lower()
                            if skill_name:
                                if "certificación" in skill_name or "certificado" in skill_name:
                                    category = "certifications"
                                elif "herramienta" in skill_name or "tool" in skill_name:
                                    category = "tools"
                                elif "blanda" in skill_name or "soft" in skill_name:
                                    category = "soft"
                                else:
                                    category = "technical"
                                catalog[category].append({"original": skill_name, "role": role})
                                skill_count += 1
                                if skill_count >= MAX_SKILLS:
                                    break
                    if skill_count >= MAX_SKILLS:
                        break
            total_skills = sum(len(v) for v in catalog.values())
            logger.info(f"Cargadas {total_skills} habilidades desde {file_path} ({key})")
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON en {file_path}: {str(e)}. Usando catálogo vacío.")
    except Exception as e:
        logger.error(f"Error cargando {file_path}: {str(e)}. Usando catálogo vacío.")
    return catalog

class NLPProcessor:
    def __init__(self, mode: str = "candidate", language: str = "es", analysis_depth: str = "quick"):
        """Inicializa el procesador NLP."""
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
        initialize_tensorflow()
        if USE_ROBERTA:
            load_roberta_model()
        if self.effective_depth == "deep":
            self.skill_embeddings = load_skill_embeddings(f"{mode}_{analysis_depth}")

    async def preprocess(self, text: str) -> Dict[str, str]:
        """Preprocesa el texto, incluyendo traducción si es necesario."""
        if self.effective_depth == "quick" or not TRANSLATOR_AVAILABLE:
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
            logger.warning(f"Error en preprocesamiento: {str(e)}")
            return {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}

    def get_text_embedding(self, text: str) -> np.ndarray:
        """Genera un embedding para el texto usando USE."""
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
            logger.warning(f"Error generando embedding: {str(e)}")
            return np.zeros(512)

    async def extract_skills(self, text: str) -> Dict[str, List[Dict[str, any]]]:
        """Extrae habilidades del texto."""
        if self.effective_depth == "quick":
            return self._extract_skills_quick(text)
        elif self.effective_depth == "deep":
            return await self._extract_skills_deep(text)
        return {"technical": [], "soft": [], "tools": [], "certifications": []}

    def _extract_skills_quick(self, text: str) -> Dict[str, List[Dict[str, any]]]:
        """Extrae habilidades en modo quick usando spaCy."""
        if not self.nlp:
            logger.error("Modelo spaCy no disponible, devolviendo habilidades vacías.")
            return {"technical": [], "soft": [], "tools": [], "certifications": []}
        doc = self.nlp(text.lower())
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        # Single-token matching
        for token in doc:
            skill_name = token.text
            for category, skill_set in self.skill_sets.items():
                if skill_name in skill_set:
                    skills[category].append({"original": skill_name, "role": self.skills_catalog[category][0].get("role", "") if self.mode == "opportunity" else ""})
        # Multi-token phrase matching
        for span in doc.noun_chunks:
            skill_name = span.text.lower()
            for category, skill_set in self.skill_sets.items():
                if skill_name in skill_set:
                    skills[category].append({"original": skill_name, "role": self.skills_catalog[category][0].get("role", "") if self.mode == "opportunity" else ""})
        return skills

    async def _extract_skills_deep(self, text: str) -> Dict[str, List[Dict[str, any]]]:
        """Extrae habilidades en modo deep usando embeddings."""
        preprocessed = await self.preprocess(text)
        text_emb = self.get_text_embedding(preprocessed["translated"])
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        
        if self.skill_embeddings:
            # Use pre-generated embeddings
            for category, skills_list in self.skills_catalog.items():
                for skill in skills_list[:MAX_SKILLS]:
                    skill_name = skill.get("original", "").lower()
                    if skill_name in self.skill_embeddings:
                        skill_emb = self.skill_embeddings[skill_name]
                        similarity = cosine_similarity(text_emb, skill_emb)
                        if similarity > 0.8:
                            skills[category].append({"original": skill_name, "role": skill.get("role", "") if self.mode == "opportunity" else ""})
        else:
            # Fallback to on-the-fly generation
            for category, skills_list in self.skills_catalog.items():
                for skill in skills_list[:MAX_SKILLS]:
                    skill_name = skill.get("original", "")
                    if skill_name:
                        skill_emb = self.get_text_embedding(skill_name)
                        similarity = cosine_similarity(text_emb, skill_emb)
                        if similarity > 0.8:
                            skills[category].append({"original": skill_name, "role": skill.get("role", "") if self.mode == "opportunity" else ""})
        return skills

    def analyze_sentiment(self, text: str) -> str:
        """Analiza el sentimiento del texto usando RoBERTa o TextBlob."""
        if USE_ROBERTA and roberta_model and roberta_tokenizer:
            try:
                inputs = roberta_tokenizer(text[:512], return_tensors="pt", truncation=True)
                with torch.no_grad():
                    outputs = roberta_model(**inputs)
                predicted_class = outputs.logits.argmax().item()
                return ["negative", "neutral", "positive"][predicted_class]
            except Exception as e:
                logger.error(f"Error en análisis de sentimiento con RoBERTa: {str(e)}")
                # Fallback a TextBlob
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            return "positive" if polarity > 0.05 else "negative" if polarity < -0.05 else "neutral"
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento con TextBlob: {str(e)}")
            return "neutral"

    def infer_opportunities(self, skills: Dict[str, List[Dict[str, any]]]) -> List[Dict[str, any]]:
        """Infiere oportunidades basadas en habilidades."""
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
        """Analiza el texto y devuelve habilidades, sentimiento y oportunidades."""
        start_time = time.time()
        try:
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
            logger.info(f"Análisis completado en {execution_time:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Error en análisis: {str(e)}")
            execution_time = time.time() - start_time
            return {
                "skills": {"technical": [], "soft": [], "tools": [], "certifications": []},
                "sentiment": "neutral",
                "metadata": {
                    "execution_time": execution_time,
                    "original_text": text.lower(),
                    "translated_text": text.lower(),
                    "detected_language": "unknown",
                    "analysis_depth": self.effective_depth
                }
            }

if __name__ == "__main__":
    async def test_nlp():
        for mode in ["candidate", "opportunity"]:
            for depth in ["quick", "deep"]:
                logger.info(f"\nProbando modo: {mode}, profundidad: {depth}")
                nlp = NLPProcessor(mode=mode, analysis_depth=depth)
                text = "Tengo experiencia en Python, liderazgo, y gestión de proyectos."
                result = await nlp.analyze(text)
                logger.info(f"[nlp.py] Análisis para '{text}': {json.dumps(result, indent=2, ensure_ascii=False)}")

    asyncio.run(test_nlp())