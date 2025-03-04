# Ubicación en servidor: /home/pablo/app/chatbot/nlp.py
import logging
import asyncio
import json
import threading
import re
from typing import Dict, List, Optional, Any, Set
from functools import lru_cache

import spacy
from spacy.matcher import PhraseMatcher
from spacy.language import Language
from cachetools import TTLCache

from skillNer.skill_extractor_class import SkillExtractor
from skillNer.general_params import SKILL_DB

# ✅ Configuración de Logging con rotación
logger = logging.getLogger(__name__)

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

loaded_models = {}  # Diccionario para almacenar modelos cargados
model_locks = {lang: threading.Lock() for lang in MODEL_LANGUAGES}  # Cerraduras para cada idioma

def load_nlp_model(language: str):
    import spacy
    model_name = MODEL_LANGUAGES.get(language, "es_core_news_md")
    if model_name in loaded_models:
        return loaded_models[model_name]
    with model_locks[language]:
        if model_name not in loaded_models:
            try:
                loaded_models[model_name] = spacy.load(model_name)
                logger.info(f"✅ Modelo NLP '{model_name}' cargado correctamente.")
            except Exception as e:
                logger.error(f"❌ Error cargando modelo '{model_name}': {e}")
                return None
    return loaded_models[model_name]

# ✅ Clase SafeLazySkillExtractor (tu versión integrada)
class SafeLazySkillExtractor:
    """
    Thread-safe Lazy Skill Extractor with improved initialization and error handling.
    
    Key Improvements:
    - Explicit initialization control
    - Comprehensive error handling
    - Configurable model loading
    - Minimal system impact
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(
        self, 
        model_name: str = "es_core_news_md", 
        custom_skills: Optional[List[str]] = None
    ):
        self.model_name = model_name
        self.custom_skills = custom_skills or []
        self._nlp = None
        self._skill_extractor = None
        self._phrase_matcher = None

    @classmethod
    def get_instance(
        cls, 
        model_name: str = "es_core_news_md", 
        custom_skills: Optional[List[str]] = None
    ):
        """
        Thread-safe method to get or create the skill extractor instance.
        
        Args:
            model_name (str): Name of the spaCy model to use
            custom_skills (List[str], optional): Additional skills to match
        
        Returns:
            SafeLazySkillExtractor: Skill extractor instance
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls(model_name, custom_skills)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Safely initialize the NLP model, skill extractor, and phrase matcher.
        
        This method is designed to minimize startup overhead and handle potential errors.
        """
        try:
            # Load spaCy model with error handling
            self._nlp = self._load_spacy_model()
            
            # Create phrase matcher with custom skills
            self._phrase_matcher = self._create_phrase_matcher()
            
            # Initialize skill extractor
            self._skill_extractor = SkillExtractor(
                self._nlp, 
                SKILL_DB, 
                self._phrase_matcher
            )
            
            logger.info(f"✅ Skill Extractor initialized with model {self.model_name}")
        
        except Exception as e:
            logger.error(f"❌ Failed to initialize Skill Extractor: {e}")
            self._nlp = None
            self._skill_extractor = None
            self._phrase_matcher = None

    def _load_spacy_model(self) -> Optional[Language]:
        """
        Load spaCy model with comprehensive error handling.
        
        Returns:
            Optional[Language]: Loaded spaCy language model
        """
        try:
            nlp = spacy.load(self.model_name)
            logger.info(f"🌐 Loaded spaCy model: {self.model_name}")
            return nlp
        except Exception as e:
            logger.critical(f"❌ Could not load spaCy model {self.model_name}: {e}")
            raise

    def _create_phrase_matcher(self) -> PhraseMatcher:
        """
        Create a custom phrase matcher with predefined and user-specified skills.
        
        Returns:
            PhraseMatcher: Configured phrase matcher
        """
        if not self._nlp:
            raise RuntimeError("SpaCy model not initialized")

        # Default skills with potential extension
        default_skills = [
            "Python", "machine learning", "data analysis", 
            "project management", "communication"
        ]
        all_skills = list(set(default_skills + self.custom_skills))

        phrase_matcher = PhraseMatcher(self._nlp.vocab, attr='LOWER')
        patterns = [self._nlp(skill) for skill in all_skills]
        phrase_matcher.add("SKILLS", patterns)
        
        logger.info(f"🔍 Phrase matcher created with {len(all_skills)} skills")
        return phrase_matcher

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """
        Extract skills from text with comprehensive error handling.
        
        Args:
            text (str): Input text to extract skills from
        
        Returns:
            Dict[str, List[str]]: Extracted skills
        """
        if not self._skill_extractor:
            logger.warning("Skill extractor not initialized")
            return {"skills": []}

        try:
            results = self._skill_extractor.annotate(text)
            
            # Safe extraction of skills
            skills = set()
            if results and "results" in results:
                skills = {
                    item.get("skill", "") 
                    for item in results.get("results", []) 
                    if isinstance(item, dict) and "skill" in item
                }
            
            logger.info(f"📊 Extracted {len(skills)} skills")
            return {"skills": list(skills)}
        
        except Exception as e:
            logger.error(f"❌ Error extracting skills: {e}")
            return {"skills": []}

    def add_custom_skills(self, skills: List[str]):
        """
        Dynamically add custom skills to the skill extractor.
        
        Args:
            skills (List[str]): New skills to add
        """
        with self._lock:
            self.custom_skills.extend(skills)
            # Reinitialize to incorporate new skills
            self._initialize()

# ✅ Configuración global para el extractor
SKILL_EXTRACTOR_CONFIG = {
    'default_model': 'es_core_news_md',
    'custom_skills': [
        'Python', 'machine learning', 'data analysis', 
        'project management', 'comunicación', 'liderazgo'
    ]
}

def get_skill_extractor(
    model_name: str = None, 
    custom_skills: Optional[List[str]] = None
) -> SafeLazySkillExtractor:
    """
    Factory function to get a skill extractor with optional configuration.
    
    Args:
        model_name (str, optional): Override default model
        custom_skills (List[str], optional): Additional custom skills
    
    Returns:
        SafeLazySkillExtractor: Configured skill extractor instance
    """
    model = model_name or SKILL_EXTRACTOR_CONFIG['default_model']
    skills = (custom_skills or []) + SKILL_EXTRACTOR_CONFIG['custom_skills']
    
    return SafeLazySkillExtractor.get_instance(
        model_name=model, 
        custom_skills=list(set(skills))
    )

# ✅ Clase NLPProcessor optimizada
class NLPProcessor:
    def __init__(self, language: str = "es"):
        self.language = language
        self._nlp = None
        self._matcher = None
        self._gpt_handler = None
        self._sentiment_analyzer = None
        self.gpt_cache = TTLCache(maxsize=1000, ttl=3600)

    def load_nlp(self):
        """Carga el modelo NLP bajo demanda."""
        if self._nlp is None:
            self._nlp = load_nlp_model(self.language)
        return self._nlp

    def load_matcher(self):
        """Carga el Matcher bajo demanda."""
        nlp = self.load_nlp()
        if nlp and self._matcher is None:
            from spacy.matcher import Matcher
            self._matcher = Matcher(nlp.vocab)
        return self._matcher

    async def load_gpt_handler(self):
        """Carga GPTHandler bajo demanda."""
        if self._gpt_handler is None:
            self._gpt_handler = await get_gpt_client()
        return self._gpt_handler

    def load_sentiment_analyzer(self):
        """Carga el analizador de sentimientos bajo demanda."""
        if self._sentiment_analyzer is None:
            self._sentiment_analyzer = RoBertASentimentAnalyzer()
        return self._sentiment_analyzer

    async def analyze(self, text: str) -> dict:
        """Análisis asíncrono de texto."""
        from app.chatbot.utils import clean_text, validate_term_in_catalog, get_all_divisions
        nlp = self.load_nlp()
        if not nlp:
            logger.error("No se ha cargado el modelo spaCy.")
            return {"intents": [], "entities": [], "sentiment": "neutral", "detected_divisions": []}

        cleaned_text = clean_text(text)
        intents = []
        # Verificar si el texto es el comando de reinicio
        if cleaned_text.strip().lower() == "/reset_chat_state":
            intents.append("reset_chat_state")
        doc = await asyncio.to_thread(nlp, cleaned_text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        matcher = self.load_matcher()
        if matcher:
            matches = await asyncio.to_thread(matcher, doc)
            intents = [nlp.vocab.strings[match_id] for match_id, _, _ in matches]

        sentiment_analyzer = self.load_sentiment_analyzer()
        sentiment = await asyncio.to_thread(sentiment_analyzer.analyze_sentiment, cleaned_text)

        all_divisions = get_all_divisions()
        detected_divisions = [term for term in entities if validate_term_in_catalog(term[0], all_divisions)]

        return {
            "entities": entities,
            "intents": intents,
            "sentiment": sentiment,
            "detected_divisions": detected_divisions
        }

    async def extract_skills(self, text: str, business_unit: str = "huntRED®") -> dict:
        """Extrae habilidades usando SafeLazySkillExtractor y maneja errores."""
        try:
            extractor = get_skill_extractor()  # Usamos la función factory
            skills_result = extractor.extract_skills(text)
            return skills_result
        except Exception as e:
            logger.error(f"Error extrayendo habilidades: {e}")
            return {"skills": []}

    def extract_interests_and_skills(self, text: str) -> dict:
        """Extrae intereses y habilidades usando SafeLazySkillExtractor."""
        try:
            extractor = get_skill_extractor()  # Usamos la función factory
            skills_result = extractor.extract_skills(text)
            return {"skills": skills_result["skills"]}
        except Exception as e:
            logger.error(f"Error en extract_interests_and_skills: {e}")
            return {"skills": []}

    def infer_gender(self, name: str) -> str:
        """Infiera género basado en heurísticas simples."""
        GENDER_DICT = {"jose": "M", "maria": "F", "andrea": "F", "juan": "M"}
        parts = name.lower().split()
        m_count = sum(1 for p in parts if p in GENDER_DICT and GENDER_DICT[p] == "M")
        f_count = sum(1 for p in parts if p in GENDER_DICT and GENDER_DICT[p] == "F")
        return "M" if m_count > f_count else "F" if f_count > m_count else "O"

    def extract_skills_and_roles(self, text: str, business_unit: str = "huntRED®") -> dict:
        """
        Extrae habilidades y sugiere roles usando SafeLazySkillExtractor.
        """
        try:
            extractor = get_skill_extractor()  # Usamos la función factory
            skills_result = extractor.extract_skills(text)
            skills = skills_result["skills"]
            # Aquí puedes agregar lógica para sugerir roles basado en las habilidades
            suggested_roles = []  # Implementa tu lógica aquí
            return {
                "skills": skills,
                "suggested_roles": suggested_roles
            }
        except Exception as e:
            logger.error(f"Error en extract_skills_and_roles: {e}")
            return {"skills": [], "suggested_roles": []}

class TabiyaJobClassifier:
    def __init__(self):
        from tabiya_livelihoods_classifier.inference.linker import EntityLinker
        self.linker = EntityLinker()

    def classify(self, text):
        return self.linker.link_text(text)

class RoBertASentimentAnalyzer:
    def __init__(self, model_name="cardiffnlp/twitter-roberta-base-sentiment-latest"):
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.torch = torch

    def analyze_sentiment(self, text):
        inputs = self.tokenizer(text, return_tensors="pt")
        with self.torch.no_grad():
            outputs = self.model(**inputs)
            predicted_class = self.torch.argmax(outputs.logits, dim=1).item()
        return ["negative", "neutral", "positive"][predicted_class]

# ✅ Pool de clientes para GPTHandler (Lazy Load)
GPT_CLIENT_POOL_SIZE = 5
gpt_client_pool = [None] * GPT_CLIENT_POOL_SIZE
gpt_client_locks = [asyncio.Lock() for _ in range(GPT_CLIENT_POOL_SIZE)]

async def get_gpt_client():
    """Devuelve un cliente GPT disponible del pool."""
    from app.chatbot.gpt import GPTHandler
    for i in range(GPT_CLIENT_POOL_SIZE):
        async with gpt_client_locks[i]:
            if gpt_client_pool[i] is None:
                gpt_client_pool[i] = GPTHandler()
                await gpt_client_pool[i].initialize()
            return gpt_client_pool[i]
    client = GPTHandler()
    await client.initialize()
    return client

# ✅ Ejemplo de uso (opcional, comentado)
# if __name__ == "__main__":
#     extractor = get_skill_extractor()
#     text = "I'm passionate about Python programming and machine learning projects"
#     skills = extractor.extract_skills(text)
#     print(skills)
#     extractor.add_custom_skills(['neural networks', 'AI'])