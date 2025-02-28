# Ubicación en servidor: /home/pablo/app/chatbot/nlp.py
import logging
import nltk
import torch
import spacy
import json
import re
import unidecode
import asyncio
import threading
import pandas as pd
from cachetools import TTLCache, cachedmethod
from langdetect import detect
from spacy.matcher import Matcher, PhraseMatcher
from nltk.corpus import stopwords
from skillNer.skill_extractor_class import SkillExtractor
from app.models import BusinessUnit, GptApi
from app.chatbot.utils import (
    get_all_skills_for_unit, get_positions_by_skills, 
    prioritize_interests, map_skill_to_database
)
from app.chatbot.gpt import GPTHandler
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from logging.handlers import RotatingFileHandler

# ✅ Configuración de Logging con rotación
logger = logging.getLogger(__name__)
logger.info("Inicio de la aplicación.")

# ✅ Descarga eficiente de NLTK
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download('stopwords', quiet=True)

# ✅ Modelos NLP con caché y Lazy Load
MODEL_LANGUAGES = {
    "es": "es_core_news_md",
    "en": "en_core_web_md",
    "fr": "fr_core_news_md",
    "it": "it_core_news_md",
    "de": "de_core_news_md",
    "ru": "ru_core_news_md",
    "pt": "pt_core_news_md"
}
loaded_models = {}
model_locks = {lang: threading.Lock() for lang in MODEL_LANGUAGES.keys()}  # Protección en multi-hilo

def load_nlp_model(language: str):
    """Carga modelos de NLP con caché y protección de concurrencia."""
    model_name = MODEL_LANGUAGES.get(language, "es_core_news_md")
    if model_name in loaded_models:
        return loaded_models[model_name]

    with model_locks[language]:  # Evita condiciones de carrera en multi-hilo
        if model_name not in loaded_models:
            try:
                loaded_models[model_name] = spacy.load(model_name)
                logger.info(f"✅ Modelo NLP '{model_name}' cargado correctamente.")
            except Exception as e:
                logger.error(f"❌ Error cargando modelo '{model_name}': {e}")
                return None
    return loaded_models[model_name]

# ✅ Lazy Load: SkillExtractor
class LazySkillExtractor:
    """Carga SkillExtractor solo cuando se necesita."""
    def __init__(self):
        self.instance = None
        self.lock = threading.Lock()

    def get(self):
        if self.instance is None:
            with self.lock:
                if self.instance is None:
                    try:
                        skill_db_path = "/home/pablo/skill_db_relax_20.json"
                        with open(skill_db_path, 'r', encoding='utf-8') as f:
                            skills_db = json.load(f)

                        nlp_model = load_nlp_model("es")
                        phrase_matcher = PhraseMatcher(nlp_model.vocab)
                        self.instance = SkillExtractor(nlp=nlp_model, skills_db=skills_db, phraseMatcher=phrase_matcher)
                        logger.info("✅ SkillExtractor inicializado correctamente.")
                    except Exception as e:
                        logger.error(f"❌ Error inicializando SkillExtractor: {e}", exc_info=True)
                        self.instance = None
        return self.instance

lazy_skill_extractor = LazySkillExtractor()

# ✅ Pool de clientes para GPTHandler (Lazy Load)
GPT_CLIENT_POOL_SIZE = 5
gpt_client_pool = [None] * GPT_CLIENT_POOL_SIZE
gpt_client_locks = [asyncio.Lock() for _ in range(GPT_CLIENT_POOL_SIZE)]

async def get_gpt_client():
    """Devuelve un cliente GPT disponible del pool."""
    for i in range(GPT_CLIENT_POOL_SIZE):
        async with gpt_client_locks[i]:
            if gpt_client_pool[i] is None:
                gpt_client_pool[i] = GPTHandler()
                await gpt_client_pool[i].initialize()
            return gpt_client_pool[i]
    return GPTHandler()  # Si todos están ocupados, crea uno nuevo.

# ✅ Lazy Load NLPProcessor
class NLPProcessor:
    """Procesador de NLP para análisis de texto, intenciones, sentimiento e intereses."""
    def __init__(self, language: str = "es"):
        self.language = language
        self._nlp = None  # Lazy Load
        self._matcher = None  # Lazy Load
        self._gpt_handler = None  # Lazy Load
        self._sentiment_analyzer = None  # Lazy Load
        self.gpt_cache = TTLCache(maxsize=1000, ttl=3600)  # Caché eficiente

    @property
    def nlp(self):
        """Carga el modelo NLP solo cuando se necesita."""
        if self._nlp is None:
            self._nlp = load_nlp_model(self.language)
        return self._nlp

    @property
    def matcher(self):
        """Carga el Matcher solo cuando se necesita."""
        if self._matcher is None:
            self._matcher = Matcher(self.nlp.vocab)
        return self._matcher

    @property
    def sentiment_analyzer(self):
        """Carga el analizador de sentimientos solo cuando se necesita."""
        if self._sentiment_analyzer is None:
            self._sentiment_analyzer = RoBertASentimentAnalyzer()
        return self._sentiment_analyzer

    async def initialize_gpt_handler(self):
        """Inicializa GPTHandler de manera diferida."""
        if self._gpt_handler is None:
            self._gpt_handler = await get_gpt_client()
            
    def set_language(self, language: str):
        """Permite cambiar dinámicamente el idioma del modelo NLP."""
        self.language = language
        self.nlp = load_nlp_model(language)
        self.matcher = Matcher(self.nlp.vocab) if self.nlp else None
        logger.info(f"🔄 Modelo NLP cambiado a: {language}")

    def define_intent_patterns(self) -> None:
        """Define patrones de intenciones con Matcher."""
        if not self.matcher:
            return
        # ... (patrones existentes sin cambios)
        logger.debug("Patrones de intenciones definidos: saludo, despedida, informacion_servicios, ayuda.")

    async def analyze(self, text: str) -> dict:
        """Análisis asíncrono de texto con RoBERTa para sentimiento."""
        from app.chatbot.utils import clean_text, validate_term_in_catalog, get_all_divisions

        if not self.nlp:
            logger.error("No se ha cargado el modelo spaCy, devolviendo análisis vacío.")
            return {"intents": [], "entities": [], "sentiment": "neutral", "detected_divisions": []}

        cleaned_text = clean_text(text)
        doc = await asyncio.to_thread(self.nlp, cleaned_text)  # Hacer SpaCy asíncrono
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        intents = []
        if self.matcher:
            matches = await asyncio.to_thread(self.matcher, doc)  # Hacer Matcher asíncrono
            intents = [self.nlp.vocab.strings[match_id] for match_id, _, _ in matches]
        
        # Usar RoBERTa para sentimiento en lugar de NLTK
        sentiment = await asyncio.to_thread(self.sentiment_analyzer.analyze_sentiment, cleaned_text)
        all_divisions = get_all_divisions()
        detected_divisions = [term for term in entities if validate_term_in_catalog(term[0], all_divisions)]

        logger.debug(f"Análisis: Intenciones={intents}, Entidades={entities}, Sentimiento={sentiment}")
        return {
            "entities": entities,
            "intents": intents,
            "sentiment": sentiment,  # Ahora solo RoBERTa
            "detected_divisions": detected_divisions
        }

    @cachedmethod(lambda self: self.gpt_cache)
    async def extract_skills(self, text: str, business_unit: str = "huntRED®") -> dict:
        """Extrae habilidades con caché, SkillNer y GPTHandler."""
        skills_from_skillner = set()
        skills_from_gpt = set()
        all_skills = get_all_skills_for_unit(business_unit)

        # ✅ Lazy Load SkillExtractor
        sn = lazy_skill_extractor.get()
        if sn:
            try:
                results = await asyncio.to_thread(sn.annotate, text)
                if "results" in results:
                    extracted_skills = {item["skill"] for item in results["results"]}
                    skills_from_skillner.update(extracted_skills)
            except Exception as e:
                logger.error(f"Error en SkillExtractor: {e}")

        # ✅ GPTHandler con Lazy Load
        await self.initialize_gpt_handler()
        gpt_prompt = f"Extrae habilidades del siguiente texto:\n\n{text}"
        try:
            response = await self._gpt_handler.generate_response(gpt_prompt)
        except Exception as e:
            logger.error(f"Error con GPTHandler: {e}")
            return {"skills": list(skills_from_skillner)}

        try:
            gpt_output = json.loads(response)
            skills_from_gpt = {map_skill_to_database(skill) for skill in gpt_output.get("skills", [])}
        except json.JSONDecodeError:
            logger.warning("Error al parsear respuesta de GPTHandler.")

        return {
            "skills": list(skills_from_skillner.union(skills_from_gpt))
        }
    
    def extract_interests_and_skills(self, text: str) -> dict:
        """
        Extrae intereses explícitos, habilidades y sugiere roles priorizando lo mencionado por el usuario.
        """
        text_normalized = unidecode.unidecode(text.lower())
        skills = set()
        priorities = {}

        # Cargar habilidades desde catálogos
        try:
            all_skills = get_all_skills_for_unit()
            logger.info(f"📌 Habilidades cargadas: {all_skills}")  
        except Exception as e:
            logger.error(f"Error obteniendo habilidades: {e}")
            all_skills = []

        # Coincidencias manuales
        for skill in all_skills:
            skill_normalized = unidecode.unidecode(skill.lower())
            if re.search(r'\b' + re.escape(skill_normalized) + r'\b', text_normalized):
                skills.add(skill)
                priorities[skill] = 2  # Mayor peso a lo mencionado directamente

        # Extraer habilidades con SkillExtractor
        if sn and nlp and nlp.vocab.vectors_length > 0:
            try:
                results = sn.annotate(text)
                if isinstance(results, dict) and "results" in results:
                    extracted_skills = {item["skill"] for item in results["results"] if isinstance(item, dict)}
                    skills.update(extracted_skills)
                    for skill in extracted_skills:
                        priorities[skill] = priorities.get(skill, 1)  # Menor peso a lo detectado automáticamente
                    logger.info(f"🧠 Habilidades extraídas por SkillExtractor: {extracted_skills}")
            except Exception as e:
                logger.error(f"❌ Error en SkillExtractor: {e}", exc_info=True)

        # Aplicar ponderación a intereses
        prioritized_interests = prioritize_interests(list(skills))  # Se pasa solo la lista de skills
        
        return {
            "skills": list(skills),
            "prioritized_skills": prioritized_interests
        }
    
    def infer_gender(self, name: str) -> str:
        """ Infiera género basado en heurísticas simples. """
        GENDER_DICT = {"jose": "M", "maria": "F", "andrea": "F", "juan": "M"}
        parts = name.lower().split()
        m_count = sum(1 for p in parts if p in GENDER_DICT and GENDER_DICT[p] == "M")
        f_count = sum(1 for p in parts if p in GENDER_DICT and GENDER_DICT[p] == "F")
        return "M" if m_count > f_count else "F" if f_count > m_count else "O"

    def extract_skills_and_roles(self, text: str, business_unit: str = "huntRED®") -> dict:
        """
        Extrae habilidades, identifica intereses explícitos y sugiere roles con prioridad en lo que el usuario menciona directamente.
        """
        text_normalized = unidecode.unidecode(text.lower())
        skills = set()
        priorities = {}  # Diccionario para ponderar lo que menciona el usuario

        # 1️⃣ Cargar habilidades desde catálogos
        try:
            all_skills = get_all_skills_for_unit(business_unit)
            logger.info(f"📌 Habilidades cargadas para {business_unit}: {all_skills}")  
        except Exception as e:
            logger.error(f"Error obteniendo habilidades para {business_unit}: {e}")
            all_skills = []

        # 2️⃣ Coincidencias manuales con prioridad
        for skill in all_skills:
            skill_normalized = unidecode.unidecode(skill.lower())
            if re.search(r'\b' + re.escape(skill_normalized) + r'\b', text_normalized):
                skills.add(skill)
                priorities[skill] = 2  # Mayor peso a lo mencionado directamente

        # 3️⃣ Extraer habilidades con SkillExtractor
        if sn and nlp and nlp.vocab.vectors_length > 0:
            try:
                results = sn.annotate(text)
                if isinstance(results, dict) and "results" in results:
                    extracted_skills = {item["skill"] for item in results["results"] if isinstance(item, dict)}
                    skills.update(extracted_skills)
                    for skill in extracted_skills:
                        priorities[skill] = priorities.get(skill, 1)  # Menor peso a lo detectado automáticamente
                    logger.info(f"🧠 Habilidades extraídas por SkillExtractor: {extracted_skills}")
            except Exception as e:
                logger.error(f"❌ Error en SkillExtractor: {e}", exc_info=True)

        # 4️⃣ Ponderar y asociar a roles
        skills, skill_weights = prioritize_skills(skills, priorities)
        suggested_roles = get_positions_by_skills(skills, skill_weights) if skills else []

        return {
            "skills": skills,
            "suggested_roles": suggested_roles
        }

    
class TabiyaJobClassifier:
    def __init__(self):
        from tabiya_livelihoods_classifier.inference.linker import EntityLinker
        self.linker = EntityLinker()

    def classify(self, text):
        return self.linker.link_text(text)

class RoBertASentimentAnalyzer:
    def __init__(self, model_name="cardiffnlp/twitter-roberta-base-sentiment-latest"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

    def analyze_sentiment(self, text):
        """Analiza el sentimiento del texto."""
        inputs = self.tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
            predicted_class = torch.argmax(outputs.logits, dim=1).item()
        return ["negative", "neutral", "positive"][predicted_class]


# Instancia global del procesador
nlp_processor = NLPProcessor()