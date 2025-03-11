# 📌 Ubicación en servidor: /home/pablo/app/chatbot/nlp.py

import spacy
import json
import logging
from typing import List, Dict, Optional
from spacy.matcher import PhraseMatcher, Matcher
from cachetools import cachedmethod, TTLCache
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

# Modelos spaCy por idioma
MODEL_LANGUAGES = {
    "es": "es_core_news_md",      # Español, ~50 MB
    "default": "xx_ent_wiki_sm"   # Multilingüe, ~10 MB
}

# Ruta al catálogo de habilidades
SKILLS_JSON_PATH = "/home/pablo/app/utilidades/catalogs/skills.json"

# Inicializar NLTK VADER
try:
    nltk.download('vader_lexicon', quiet=True)
    SIA = SentimentIntensityAnalyzer()
except Exception as e:
    logger.error(f"Error inicializando NLTK VADER: {e}")
    SIA = None

def load_skills_catalog() -> Dict:
    """Carga el catálogo de habilidades desde skills.json."""
    try:
        with open(SKILLS_JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando skills.json: {e}")
        return {}

class BaseNLPProcessor:
    """Clase base para procesadores NLP con spaCy y análisis de sentimientos en cascada."""
    def __init__(self, language: str = 'es'):
        self.language = language
        self.skills_catalog = load_skills_catalog()
        self._load_nlp_model()
        self.skill_cache = TTLCache(maxsize=5000, ttl=7200)
        self.sentiment_pipeline = None
        try:
            from transformers import pipeline
            self.sentiment_pipeline = pipeline('sentiment-analysis', 
                                              model='cardiffnlp/twitter-roberta-base-sentiment-latest')
            logger.info("RoBERTa sentiment pipeline cargado (~500 MB)")
        except Exception as e:
            logger.warning(f"No se pudo cargar RoBERTa: {e}. Usando NLTK VADER como primario.")

    def _load_nlp_model(self):
        """Carga el modelo spaCy según el idioma."""
        model = MODEL_LANGUAGES.get(self.language, MODEL_LANGUAGES["default"])
        try:
            self.nlp = spacy.load(model)
            logger.info(f"Modelo spaCy {model} cargado")
        except Exception as e:
            logger.warning(f"Modelo {model} no disponible: {e}")
            self.nlp = spacy.load(MODEL_LANGUAGES["default"])

    def extract_entities(self, text: str) -> List[str]:
        """Extrae entidades nombradas con spaCy."""
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        doc = self.nlp(text.lower())
        return [ent.text.lower() for ent in doc.ents]

    def get_sentiment(self, text: str) -> str:
        """
        Analiza el sentimiento en cascada:
        1. NLTK VADER (rápido, ligero).
        2. Si neutral o falla, RoBERTa (preciso, pesado).
        """
        if SIA:
            try:
                scores = SIA.polarity_scores(text)
                compound = scores['compound']
                if compound >= 0.05:
                    return "positive"
                elif compound <= -0.05:
                    return "negative"
                else:
                    logger.info("NLTK VADER dio neutral, intentando RoBERTa")
            except Exception as e:
                logger.error(f"Error con NLTK VADER: {e}")

        if self.sentiment_pipeline:
            try:
                result = self.sentiment_pipeline(text[:512])
                return result[0]['label']
            except Exception as e:
                logger.error(f"Error con RoBERTa sentiment: {e}")

        return "neutral"

class CandidateNLPProcessor(BaseNLPProcessor):
    """Procesador NLP para candidatos con máxima extracción de habilidades."""
    def __init__(self, language: str = 'es'):
        super().__init__(language)
        self.all_skills = self._get_all_skills()  # Primero inicializamos all_skills
        self.phrase_matcher = self._build_phrase_matcher()
        self.matcher = self._build_matcher()

    def _get_all_skills(self) -> set:
        """Extrae todas las habilidades del catálogo, manejando listas o diccionarios."""
        skills = set()
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    if isinstance(details, dict):  # Estructura como diccionario
                        for category in ["Habilidades Técnicas", "Habilidades Blandas", "Certificaciones", "Herramientas"]:
                            skills.update([s.lower() for s in details.get(category, [])])
                    elif isinstance(details, list):  # Estructura como lista
                        for item in details:
                            if isinstance(item, list):  # Lista anidada de habilidades
                                skills.update([s.lower() for s in item if isinstance(s, str)])
                            elif isinstance(item, str):  # Habilidad directa
                                skills.add(item.lower())
        return skills

    def _build_phrase_matcher(self) -> PhraseMatcher:
        """Construye un PhraseMatcher para coincidencias exactas."""
        matcher = PhraseMatcher(self.nlp.vocab, attr='LOWER')
        patterns = [self.nlp.make_doc(skill) for skill in self.all_skills]
        matcher.add("SKILL", patterns)
        return matcher

    def _build_matcher(self) -> Matcher:
        """Construye un Matcher para patrones flexibles."""
        matcher = Matcher(self.nlp.vocab)
        for skill in self.all_skills:
            pattern = [{"LOWER": {"IN": ["experiencia", "conocimiento", "uso", "habilidad"]}, "OP": "*"},
                       {"LOWER": skill}]
            matcher.add("FLEXIBLE_SKILL", [pattern])
        return matcher

    @cachedmethod(lambda self: self.skill_cache)
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Maximiza la extracción de habilidades."""
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        doc = self.nlp(text.lower())
        skills = {"technical": [], "soft": [], "certifications": [], "tools": []}

        matches = self.phrase_matcher(doc)
        for _, start, end in matches:
            skill = doc[start:end].text
            self._classify_skill(skill, skills)

        flex_matches = self.matcher(doc)
        for _, start, end in flex_matches:
            skill = doc[start:end].text.split()[-1]
            self._classify_skill(skill, skills)

        for token in doc:
            if token.text in self.all_skills:
                self._classify_skill(token.text, skills)

        return skills

    def _classify_skill(self, skill: str, skills_dict: Dict[str, List[str]]):
        """Clasifica una habilidad según skills.json, manejando listas o diccionarios."""
        # Si unit se proporciona, filtrar el catálogo por unidad antes de clasificar
        catalog = self.skills_catalog.get(unit, self.skills_catalog) if unit else self.skills_catalog
    
        skill_lower = skill.lower()
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    if isinstance(details, dict):
                        if skill_lower in [s.lower() for s in details.get("Habilidades Técnicas", [])]:
                            skills_dict["technical"].append(skill_lower)
                        elif skill_lower in [s.lower() for s in details.get("Habilidades Blandas", [])]:
                            skills_dict["soft"].append(skill_lower)
                        elif skill_lower in [s.lower() for s in details.get("Certificaciones", [])]:
                            skills_dict["certifications"].append(skill_lower)
                        elif skill_lower in [s.lower() for s in details.get("Herramientas", [])]:
                            skills_dict["tools"].append(skill_lower)
                    elif isinstance(details, list):
                        # Asumimos que las habilidades están en sublistas o como strings
                        for item in details:
                            if isinstance(item, list):
                                if skill_lower in [s.lower() for s in item if isinstance(s, str)]:
                                    # Clasificación simple: si está en la lista, asumimos técnica por defecto
                                    skills_dict["technical"].append(skill_lower)
                            elif isinstance(item, str) and skill_lower == item.lower():
                                skills_dict["technical"].append(skill_lower)
        # Eliminar duplicados
        skills_dict["technical"] = list(set(skills_dict["technical"]))
        skills_dict["soft"] = list(set(skills_dict["soft"]))
        skills_dict["certifications"] = list(set(skills_dict["certifications"]))
        skills_dict["tools"] = list(set(skills_dict["tools"]))

    def analyze_candidate(self, text: str) -> Dict[str, any]:
        """Analiza el texto de un candidato."""
        skills_data = self.extract_skills(text)
        sentiment = self.get_sentiment(text)
        return {"skills": skills_data, "sentiment": sentiment}

class OpportunityNLPProcessor(BaseNLPProcessor):
    """Procesador NLP para oportunidades laborales."""
    def __init__(self, language: str = 'es'):
        super().__init__(language)
        self.all_skills = self._get_all_skills()
        self.phrase_matcher = self._build_phrase_matcher()
        self.matcher = self._build_matcher()

    def _get_all_skills(self) -> set:
        """Extrae todas las habilidades del catálogo, manejando listas o diccionarios."""
        skills = set()
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    if isinstance(details, dict):
                        for category in ["Habilidades Técnicas", "Habilidades Blandas"]:
                            skills.update([s.lower() for s in details.get(category, [])])
                    elif isinstance(details, list):
                        for item in details:
                            if isinstance(item, list):
                                skills.update([s.lower() for s in item if isinstance(s, str)])
                            elif isinstance(item, str):
                                skills.add(item.lower())
        return skills

    def _build_phrase_matcher(self) -> PhraseMatcher:
        """Construye un PhraseMatcher para oportunidades."""
        matcher = PhraseMatcher(self.nlp.vocab, attr='LOWER')
        patterns = [self.nlp.make_doc(skill) for skill in self.all_skills]
        matcher.add("SKILL", patterns)
        return matcher

    def _build_matcher(self) -> Matcher:
        """Construye un Matcher para patrones flexibles."""
        matcher = Matcher(self.nlp.vocab)
        for skill in self.all_skills:
            pattern = [{"LOWER": {"IN": ["requiere", "necesita", "con", "en"]}, "OP": "*"},
                       {"LOWER": skill}]
            matcher.add("FLEXIBLE_SKILL", [pattern])
        return matcher

    def extract_opportunity_details(self, text: str) -> dict[str, any]:
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        doc = self.nlp(text.lower())
        details = {
            "skills": {"technical": [], "soft": [], "certifications": []},
            "location": None,
            "contract_type": None,
            "role": None
        }

        # Extraer habilidades con PhraseMatcher
        matches = self.phrase_matcher(doc)
        for match_id, start, end in matches:
            skill = doc[start:end].text
            self._classify_skill(skill, details["skills"])

        # Coincidencias flexibles
        flex_matches = self.matcher(doc)
        for match_id, start, end in flex_matches:
            skill = doc[start:end].text.split()[-1]
            self._classify_skill(skill, details["skills"])

        # Buscar tokens individuales en el catálogo
        for token in doc:
            if token.text in self.all_skills:
                self._classify_skill(token.text, details["skills"])

        # Extraer ubicación
        location_patterns = ["ubicación:", "location:", "lugar:", "ciudad:", "país:"]
        for sent in doc.sents:
            for pattern in location_patterns:
                if pattern in sent.text:
                    possible_location = sent.text.split(pattern)[1].strip().split('.')[0]
                    details["location"] = possible_location
                    break
            if details["location"]:
                break

        # Si no hay patrón, buscar entidades nombradas
        if not details["location"]:
            for ent in doc.ents:
                if ent.label_ in ["LOC", "GPE"]:
                    details["location"] = ent.text
                    break

        # Extraer tipo de contrato (opcional, si aparece en el texto)
        contract_keywords = ["contrato", "tipo de empleo"]
        contract_types = ["permanente", "temporal", "freelance", "full-time", "part-time"]
        for sent in doc.sents:
            for keyword in contract_keywords:
                if keyword in sent.text:
                    for ctype in contract_types:
                        if ctype in sent.text:
                            details["contract_type"] = ctype
                            break

        # Extraer rol (buscar patrones como "Se busca [rol]")
        for sent in doc.sents:
            if "se busca" in sent.text:
                possible_role = sent.text.replace("se busca", "").split("con")[0].strip()
                details["role"] = possible_role
                break

        return details
    def _classify_skill(self, skill: str, skills_dict: Dict[str, List[str]]):
        """Clasifica habilidades para oportunidades, manejando listas o diccionarios."""
        skill_lower = skill.lower()
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    if isinstance(details, dict):
                        if skill_lower in [s.lower() for s in details.get("Habilidades Técnicas", [])]:
                            skills_dict["technical"].append(skill_lower)
                        elif skill_lower in [s.lower() for s in details.get("Habilidades Blandas", [])]:
                            skills_dict["soft"].append(skill_lower)
                    elif isinstance(details, list):
                        for item in details:
                            if isinstance(item, list):
                                if skill_lower in [s.lower() for s in item if isinstance(s, str)]:
                                    skills_dict["technical"].append(skill_lower)
                            elif isinstance(item, str) and skill_lower == item.lower():
                                skills_dict["technical"].append(skill_lower)

    def _identify_role(self, text: str) -> Optional[str]:
        """Identifica el rol basado en el catálogo."""
        text_lower = text.lower()
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role in role_category.keys():
                    if role.lower() in text_lower:
                        return role
        return None

    def classify_job(self, text: str) -> Dict[str, any]:
        """Clasifica el tipo de empleo."""
        doc = self.nlp(text.lower())
        for ent in doc.ents:
            if "ingeniero" in ent.text.lower() or "engineer" in ent.text.lower():
                return {"classification": "Software Engineer"}
        return {"classification": "unknown"}

    def analyze_opportunity(self, text: str) -> Dict[str, any]:
        """Analiza una oportunidad laboral completa."""
        details = self.extract_opportunity_details(text)
        job_classification = self.classify_job(text)
        sentiment = self.get_sentiment(text)
        return {"details": details, "job_classification": job_classification, "sentiment": sentiment}

class NLPProcessor:
    """
    Clase genérica para compatibilidad con utils.py.
    Delega a CandidateNLPProcessor o OpportunityNLPProcessor según el contexto.
    """
    def __init__(self, language: str = 'es', mode: str = 'opportunity'):
        self.language = language
        self.mode = mode.lower()
        if self.mode == 'candidate':
            self.processor = CandidateNLPProcessor(language=self.language)
        else:
            self.processor = OpportunityNLPProcessor(language=self.language)

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extrae habilidades usando el procesador adecuado."""
        if self.mode == 'candidate':
            return self.processor.extract_skills(text)
        return self.processor.extract_opportunity_details(text)["skills"]

    def analyze(self, text: str) -> Dict[str, any]:
        """Analiza el texto según el modo."""
        if self.mode == 'candidate':
            return self.processor.analyze_candidate(text)
        return self.processor.analyze_opportunity(text)

    def get_sentiment(self, text: str) -> str:
        """Obtiene el sentimiento usando el procesador base."""
        return self.processor.get_sentiment(text)