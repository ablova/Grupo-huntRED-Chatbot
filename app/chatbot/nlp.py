# 📌 Ubicación en servidor: /home/pablo/app/chatbot/nlp.py

import spacy
import json
import logging
from typing import List, Dict, Set, Optional
from transformers import pipeline
from spacy.matcher import PhraseMatcher
from cachetools import cachedmethod, TTLCache
# from tabiya_livelihoods_classifier.inference.linker import EntityLinker     NO FUNCIONA
logger = logging.getLogger(__name__)

# Diccionario de modelos por idioma
MODEL_LANGUAGES = {
    "es": "es_core_news_md",  # Español (LATAM y España)
    "en": "en_core_web_md",   # Inglés (migrantes y global)
    "pt": "pt_core_news_md",  # Portugués (Brasil y migrantes)
    "fr": "fr_core_news_md",  # Francés (Haití y migrantes)
    "nah": None,              # Náhuatl (sin modelo spaCy, usaremos multilingüe)
    "yua": None,              # Maya yucateco (sin modelo spaCy, usaremos multilingüe)
    "default": "xx_ent_wiki_sm"  # Modelo multilingüe básico de spaCy
}

# Modelos NER por idioma (Hugging Face)
NER_MODELS = {
    "es": "dccuchile/bert-base-spanish-wwm-cased",  # Español
    "en": "jjzha/jobbert_skill_extraction",         # Inglés
    "pt": "neuralmind/bert-base-portuguese-cased",  # Portugués
    "fr": "camembert-base",                         # Francés
    "default": "xlm-roberta-base"                   # Multilingüe (náhuatl, maya, etc.)
}

# Ruta al catálogo de habilidades
SKILLS_JSON_PATH = "/home/pablo/app/utilidades/catalogs/skills.json"

def load_skills_catalog() -> Dict:
    """Carga el catálogo de habilidades desde skills.json."""
    try:
        with open(SKILLS_JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando skills.json: {e}")
        return {}

class BaseNLPProcessor:
    """Clase base para procesadores NLP que comparten funcionalidades comunes."""
    def __init__(self, language: str = 'es'):
        self.language = language
        self.skills_catalog = load_skills_catalog()
        self._load_nlp_model()
        self._load_ner_pipeline()
        self.sentiment_pipeline = pipeline('sentiment-analysis', 
                                         model='cardiffnlp/twitter-roberta-base-sentiment-latest')
        self.skill_cache = TTLCache(maxsize=5000, ttl=7200)  # Cache de 2 horas

    def _load_nlp_model(self):
        """Carga el modelo spaCy según el idioma."""
        model = MODEL_LANGUAGES.get(self.language, MODEL_LANGUAGES["default"])
        try:
            self.nlp = spacy.load(model) if model else spacy.load(MODEL_LANGUAGES["default"])
        except Exception as e:
            logger.warning(f"Modelo {model} no disponible para {self.language}: {e}. Usando modelo multilingüe.")
            self.nlp = spacy.load(MODEL_LANGUAGES["default"])

    def _load_ner_pipeline(self):
        """Carga el pipeline NER según el idioma."""
        ner_model = NER_MODELS.get(self.language, NER_MODELS["default"])
        try:
            self.ner_pipeline = pipeline('ner', model=ner_model, aggregation_strategy='simple')
        except Exception as e:
            logger.error(f"Error cargando NER para {self.language}: {e}. Usando xlm-roberta-base.")
            self.ner_pipeline = pipeline('ner', model=NER_MODELS["default"], aggregation_strategy='simple')

    def extract_entities(self, text: str) -> List[str]:
        """Extrae entidades nombradas del texto usando spaCy y NER especializado."""
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        doc = self.nlp(text.lower())
        entities = set()
        
        ner_results = self.ner_pipeline(text)
        for ent in ner_results:
            entities.add(ent['word'].replace('##', '').lower())
        
        for ent in doc.ents:
            entities.add(ent.text.lower())
        return list(entities)

    def get_sentiment(self, text: str) -> str:
        """Analiza el sentimiento del texto usando RoBERTa."""
        try:
            result = self.sentiment_pipeline(text[:512])  # Limite de 512 tokens
            return result[0]['label']
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {e}")
            return "neutral"

class CandidateNLPProcessor(BaseNLPProcessor):
    """Procesador NLP para analizar datos de candidatos."""
    def __init__(self, language: str = 'es'):
        super().__init__(language)
        self.matcher = self._build_matcher()
        try:
            self.linkedin_pipeline = pipeline('ner', model='algiraldohe/lm-ner-linkedin-skills-recognition')
        except Exception as e:
            logger.warning(f"Error cargando LinkedIn NER: {e}. Usando NER por defecto.")
            self.linkedin_pipeline = self.ner_pipeline
        
        if language == 'en':
            self.skillner_pipeline = pipeline('ner', model='ihk/skillner')
        else:
            self.skillner_pipeline = None

    def _build_matcher(self) -> PhraseMatcher:
        """Construye un matcher de spaCy con habilidades del catálogo."""
        matcher = PhraseMatcher(self.nlp.vocab, attr='LOWER')
        skills = set()
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    for category in ["Habilidades Técnicas", "Habilidades Blandas", "Certificaciones", "Herramientas"]:
                        skills.update(details.get(category, []))
        patterns = [self.nlp.make_doc(skill.lower()) for skill in skills]
        matcher.add("SKILL", patterns)
        return matcher

    @cachedmethod(lambda self: self.skill_cache)
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extrae habilidades del texto y las clasifica según el catálogo."""
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        doc = self.nlp(text.lower())
        skills = {"technical": [], "soft": [], "certifications": [], "tools": []}

        # 1. LinkedIn NER
        linkedin_results = self.linkedin_pipeline(text)
        for ent in linkedin_results:
            skill = ent['word'].replace('##', '').lower()
            self._classify_skill(skill, skills)

        # 2. NER especializado
        ner_results = self.ner_pipeline(text)
        for ent in ner_results:
            skill = ent['word'].replace('##', '').lower()
            self._classify_skill(skill, skills)

        # 3. SkillNER (solo inglés)
        if self.language == 'en' and self.skillner_pipeline:
            skillner_results = self.skillner_pipeline(text)
            for ent in skillner_results:
                skill = ent['word'].replace('##', '').lower()
                self._classify_skill(skill, skills)

        # 4. PhraseMatcher
        matches = self.matcher(doc)
        for _, start, end in matches:
            skill = doc[start:end].text.lower()
            self._classify_skill(skill, skills)

        return skills

    def _classify_skill(self, skill: str, skills_dict: Dict[str, List[str]]):
        """Clasifica una habilidad según el catálogo."""
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    if skill in [s.lower() for s in details.get("Habilidades Técnicas", [])]:
                        skills_dict["technical"].append(skill)
                    elif skill in [s.lower() for s in details.get("Habilidades Blandas", [])]:
                        skills_dict["soft"].append(skill)
                    elif skill in [s.lower() for s in details.get("Certificaciones", [])]:
                        skills_dict["certifications"].append(skill)
                    elif skill in [s.lower() for s in details.get("Herramientas", [])]:
                        skills_dict["tools"].append(skill)

    def analyze_candidate(self, text: str) -> Dict[str, any]:
        """Analiza el texto de un candidato."""
        skills_data = self.extract_skills(text)
        sentiment = self.get_sentiment(text)
        return {
            "skills": skills_data,
            "sentiment": sentiment
        }
    
    def _classify_skill(self, skill: str, skills_dict: Dict[str, List[str]]):
        """Clasifica habilidades para oportunidades, normalizando con ESCO si está disponible."""
        skill_lower = skill.lower()
        # Aquí podrías agregar un mapeo a nombres estandarizados de ESCO si los obtienes de Tabiya
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    if skill_lower in [s.lower() for s in details.get("Habilidades Técnicas", [])]:
                        skills_dict["technical"].append(skill_lower)
                    elif skill_lower in [s.lower() for s in details.get("Habilidades Blandas", [])]:
                        skills_dict["soft"].append(skill_lower)

class OpportunityNLPProcessor(BaseNLPProcessor):
    """Procesador NLP para analizar oportunidades laborales."""
    def __init__(self, language: str = 'es'):
        super().__init__(language)
        self.skill_extractor = None
        try:
            from transformers import pipeline
            self.skill_extractor = pipeline("ner", model="jjzha/escoxlmr_skill_extraction", tokenizer="jjzha/escoxlmr_skill_extraction")
        except Exception as e:
            logger.warning(f"No se pudo cargar escoxlmr_skill_extraction: {e}. Usando extracción básica.")
        if language == 'en':
            self.skillner_pipeline = pipeline('ner', model='ihk/skillner')
        else:
            self.skillner_pipeline = None

    def classify_job(self, text: str) -> Dict[str, any]:
        """Clasifica el tipo de empleo usando reglas básicas o modelo ESCO si disponible."""
        if self.skill_extractor:
            try:
                entities = self.skill_extractor(text)
                skills = [ent["word"] for ent in entities if ent["entity"] == "SKILL"]
                # Lógica simple para inferir ocupación (puedes mejorar esto)
                doc = self.nlp(text.lower())
                for ent in doc.ents:
                    if ent.label_ in ["ORG", "PERSON", "NORP"]:  # Ajustar según necesidad
                        continue
                    if "ingeniero" in ent.text.lower() or "engineer" in ent.text.lower():
                        return {"classification": "Software Engineer", "esco_code": "2512", "skills": skills}
                return {"classification": "unknown", "skills": skills}
            except Exception as e:
                logger.error(f"Error en clasificación con ESCO: {e}")
        return {"classification": "unknown"}

    def extract_opportunity_details(self, text: str) -> Dict[str, any]:
        """Extrae detalles clave de una oportunidad laboral."""
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        entities = self.extract_entities(text)
        details = {"skills": {"technical": [], "soft": []}, "location": None, "contract_type": None, "role": None}

        # Extracción de habilidades con SkillNER (solo inglés)
        if self.language == 'en' and self.skillner_pipeline:
            skillner_results = self.skillner_pipeline(text)
            for ent in skillner_results:
                skill = ent['word'].replace('##', '').lower()
                self._classify_skill(skill, details["skills"])

        # NER y entidades de spaCy
        for ent in entities:
            if ent in ["méxico", "são paulo", "brasil"]:  # Ejemplo, ampliar con opportunity_db
                details["location"] = ent
            elif ent in ["permanente", "temporal", "freelance"]:
                details["contract_type"] = ent
            else:
                self._classify_skill(ent, details["skills"])

        # Identificación del rol
        details["role"] = self._identify_role(text)
        return details

    def _classify_skill(self, skill: str, skills_dict: Dict[str, List[str]]):
        """Clasifica habilidades para oportunidades."""
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    if skill in [s.lower() for s in details.get("Habilidades Técnicas", [])]:
                        skills_dict["technical"].append(skill)
                    elif skill in [s.lower() for s in details.get("Habilidades Blandas", [])]:
                        skills_dict["soft"].append(skill)

    def _identify_role(self, text: str) -> Optional[str]:
        """Identifica el rol basado en el catálogo."""
        text_lower = text.lower()
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role in role_category.keys():
                    if role.lower() in text_lower:
                        return role
        return None


    def analyze_opportunity(self, text: str) -> Dict[str, any]:
        """Analiza una oportunidad laboral completa."""
        details = self.extract_opportunity_details(text)
        job_classification = self.classify_job(text)
        sentiment = self.get_sentiment(text)
        
        # Combinar habilidades extraídas del texto con las de ESCO
        esco_skills = job_classification.get("skills", [])
        for skill in esco_skills:
            skill_lower = skill.lower()
            if skill_lower not in [s.lower() for s in details["skills"]["technical"]]:
                self._classify_skill(skill_lower, details["skills"])
        
        return {
            "details": details,
            "job_classification": job_classification,
            "sentiment": sentiment
        }

    def _classify_skill(self, skill: str, skills_dict: Dict[str, List[str]]):
        """Clasifica habilidades para oportunidades, normalizando con ESCO si está disponible."""
        skill_lower = skill.lower()
        # Aquí podrías agregar un mapeo a nombres estandarizados de ESCO si los obtienes de Tabiya
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    if skill_lower in [s.lower() for s in details.get("Habilidades Técnicas", [])]:
                        skills_dict["technical"].append(skill_lower)
                    elif skill_lower in [s.lower() for s in details.get("Habilidades Blandas", [])]:
                        skills_dict["soft"].append(skill_lower)