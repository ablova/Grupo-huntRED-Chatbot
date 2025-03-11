# 📌 Ubicación en servidor: /home/pablo/app/chatbot/nlp.py
import spacy
import json
import logging
from typing import List, Dict, Optional, Set, Union, Literal
from spacy.matcher import PhraseMatcher, Matcher
from cachetools import cachedmethod, TTLCache
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from langdetect import detect, LangDetectException
import pandas as pd
import subprocess
import sys
import os
from threading import Lock

# Importaciones condicionales
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Modelos spaCy por idioma y tamaño
MODEL_LANGUAGES = {
    "es": {"sm": "es_core_news_sm", "md": "es_core_news_md", "lg": "es_core_news_lg"},
    "en": {"sm": "en_core_web_sm", "md": "en_core_web_md", "lg": "en_core_web_lg"},
    "fr": {"sm": "fr_core_news_sm", "md": "fr_core_news_md", "lg": "fr_core_news_lg"},
    "default": {"sm": "xx_ent_wiki_sm", "md": "xx_ent_wiki_sm", "lg": "xx_ent_wiki_sm"}
}

# Rutas a los catálogos
CATALOG_PATHS = {
    "es": {
        "skills": "/home/pablo/app/chatbot/catalogs/skills_es.json",
        "occupations": "/home/pablo/app/chatbot/catalogs/occupations_es.json",
        "skills_relax": "/home/pablo/skills_data/skill_db_relax_20.json"
    }
}

# Paths to CSV and JSON files
csv_paths = {
    "occupations_es": "/home/pablo/app/utilidades/catalogs/occupations_es.csv",
    "skills_es": "/home/pablo/app/utilidades/catalogs/skills_es.csv"
}
json_paths = {
    "occupations_es": "/home/pablo/app/utilidades/catalogs/occupations_es.json",
    "skills_es": "/home/pablo/app/utilidades/catalogs/skills_es.json"
}

# Lock para escritura segura en JSON
json_lock = Lock()

# Inicializar NLTK VADER
try:
    nltk.download('vader_lexicon', quiet=True)
    SIA = SentimentIntensityAnalyzer()
except Exception as e:
    logger.error(f"Error inicializando NLTK VADER: {e}")
    SIA = None

def load_catalog(path: str) -> Dict:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando {path}: {e}")
        return {}

def save_catalog(path: str, data: Dict) -> None:
    with json_lock:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Catálogo actualizado: {path}")
        except Exception as e:
            logger.error(f"Error guardando {path}: {e}")

def create_json_from_csv(csv_path, json_path):
    if os.path.exists(json_path):
        logger.info(f"JSON file {json_path} already exists.")
        return True
    if not os.path.exists(csv_path):
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write('{"division1": {"role1": {"Habilidades Técnicas": [], "Habilidades Blandas": []}}}')
        logger.info(f"Created empty JSON file: {json_path}")
        return True
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        df.to_json(json_path, orient='records', force_ascii=False)
        logger.info(f"Created {json_path} from {csv_path}")
        return True
    except Exception as e:
        logger.error(f"Error processing CSV {csv_path}: {e}")
        return False

# Crear los JSON si no existen
create_json_from_csv(csv_paths["occupations_es"], json_paths["occupations_es"])
create_json_from_csv(csv_paths["skills_es"], json_paths["skills_es"])

class ModelManager:
    def __init__(self):
        self.model_cache = TTLCache(maxsize=10, ttl=21600)  # Más espacio para diferentes tamaños

    def get_model(self, lang: str, size: str = 'sm') -> spacy.language.Language:
        cache_key = f"{lang}_{size}"
        if cache_key in self.model_cache:
            return self.model_cache[cache_key]
        model_name = MODEL_LANGUAGES.get(lang, MODEL_LANGUAGES["default"]).get(size, MODEL_LANGUAGES["default"]["sm"])
        try:
            model = spacy.load(model_name)
        except OSError:
            logger.info(f"Descargando modelo {model_name}...")
            subprocess.check_call([sys.executable, "-m", "spacy", "download", model_name])
            model = spacy.load(model_name)
        self.model_cache[cache_key] = model
        return model

model_manager = ModelManager()

class AdvancedModelManager:
    """Gestor de modelos avanzados (transformers) para modo profundo."""
    def __init__(self):
        self.sentiment_pipeline = None
        self.ner_pipelines = {}
        self.tokenizer_cache = TTLCache(maxsize=5, ttl=21600)
        self.model_cache = TTLCache(maxsize=5, ttl=21600)

    def get_sentiment_pipeline(self):
        if not TRANSFORMERS_AVAILABLE:
            return None
        if not self.sentiment_pipeline:
            self.sentiment_pipeline = pipeline('sentiment-analysis', model='cardiffnlp/twitter-roberta-base-sentiment-latest')
        return self.sentiment_pipeline

    def get_ner_pipeline(self, model_path: str):
        if not TRANSFORMERS_AVAILABLE:
            return None
        if model_path not in self.ner_pipelines:
            try:
                self.ner_pipelines[model_path] = pipeline("ner", model=model_path)
                logger.info(f"Cargado NER: {model_path}")
            except Exception as e:
                logger.error(f"Error cargando NER {model_path}: {e}")
                return None
        return self.ner_pipelines[model_path]

advanced_model_manager = AdvancedModelManager()

class BaseNLPProcessor:
    def __init__(self, language: str = 'es', mode: str = 'quick'):
        self.language = language
        self.mode = mode
        self.nlp = model_manager.get_model(language, 'sm' if mode == 'quick' else 'md')
        self.skills_catalog = load_catalog(CATALOG_PATHS["es"]["skills"])
        self.occupations_catalog = load_catalog(CATALOG_PATHS["es"]["occupations"])
        self.skills_relax_catalog = load_catalog(CATALOG_PATHS["es"]["skills_relax"])
        self.all_skills = self._get_all_skills()
        self.phrase_matcher = self._build_phrase_matcher()
        self.matcher = self._build_matcher() if mode == 'deep' else None
        self.skill_cache = TTLCache(maxsize=5000, ttl=3600 if mode == 'quick' else 7200)
        self.sentiment_analyzer = SIA if mode == 'quick' or not TRANSFORMERS_AVAILABLE else advanced_model_manager.get_sentiment_pipeline()
        if mode == 'deep' and TRANSLATOR_AVAILABLE:
            self.translator = GoogleTranslator(source='auto', target='es')
            self.translation_cache = TTLCache(maxsize=1000, ttl=3600)
        else:
            self.translator = None

    def _get_all_skills(self) -> Set[str]:
        skills = set()
        for catalog in [self.skills_catalog, self.skills_relax_catalog]:
            if isinstance(catalog, dict):
                for division in catalog.values():
                    for role_category in division.values():
                        for role, details in role_category.items():
                            if isinstance(details, dict):
                                for category in ["Habilidades Técnicas", "Habilidades Blandas", "Certificaciones", "Herramientas"]:
                                    skills.update([s.lower() for s in details.get(category, [])])
                            elif isinstance(details, list):
                                skills.update([s.lower() for s in details if isinstance(s, str)])
            elif isinstance(catalog, list):
                skills.update([s.lower() for s in catalog if isinstance(s, str)])
        logger.info(f"Total habilidades: {len(skills)} - Ejemplos: {list(skills)[:5]}")
        return skills

    def _build_phrase_matcher(self) -> PhraseMatcher:
        matcher = PhraseMatcher(self.nlp.vocab, attr='LOWER')
        patterns = [self.nlp.make_doc(skill) for skill in self.all_skills]
        matcher.add("SKILL", patterns)
        return matcher

    def _build_matcher(self) -> Matcher:
        matcher = Matcher(self.nlp.vocab)
        for skill in self.all_skills:
            pattern = [{"LOWER": {"IN": ["experiencia", "conocimiento", "uso", "habilidad", "requiere", "necesita"]}, "OP": "*"},
                       {"LOWER": skill}]
            matcher.add(f"SKILL_{skill}", [pattern])
        return matcher

    def get_sentiment(self, text: str) -> Dict[str, Union[str, float]]:
        if not self.sentiment_analyzer:
            return {"label": "neutral", "score": 0.0}
        if self.mode == 'quick':
            scores = SIA.polarity_scores(text)
            compound = scores['compound']
            label = "positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral"
            return {"label": label, "score": abs(compound)}
        try:
            result = self.sentiment_analyzer(text[:512])[0]
            return {"label": result["label"], "score": result["score"]}
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {e}")
            return {"label": "neutral", "score": 0.0}

    def extract_entities(self, text: str) -> List[str]:
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        doc = self.nlp(text.lower())
        return [ent.text.lower() for ent in doc.ents]

class CandidateProcessor(BaseNLPProcessor):
    def __init__(self, language: str = 'es', mode: str = 'quick'):
        super().__init__(language, mode)
        if mode == 'deep' and TRANSFORMERS_AVAILABLE:
            self.linkedin_ner = advanced_model_manager.get_ner_pipeline("/home/pablo/skills_data/algiraldohe_lm-ner-linkedin-skills-recognition")
            self.ihk_ner = advanced_model_manager.get_ner_pipeline("/home/pablo/skills_data/ihk_skillner")
        else:
            self.linkedin_ner = None
            self.ihk_ner = None

    @cachedmethod(lambda self: self.skill_cache)
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        doc = self.nlp(text.lower())
        skills = {"technical": [], "soft": [], "certifications": [], "tools": []}

        # Modo rápido: solo PhraseMatcher
        matches = self.phrase_matcher(doc)
        for _, start, end in matches:
            skill = doc[start:end].text
            self._classify_skill(skill, skills)

        # Modo profundo: Matcher + NER
        if self.mode == 'deep':
            if self.matcher:
                flex_matches = self.matcher(doc)
                for _, start, end in flex_matches:
                    skill = doc[start:end].text.split()[-1]
                    self._classify_skill(skill, skills)

            if self.linkedin_ner:
                entities = self.linkedin_ner(text)
                for entity in entities:
                    if entity["entity"].startswith("SKILL"):
                        self._classify_skill(entity["word"], skills)
            if self.ihk_ner:
                entities = self.ihk_ner(text)
                for entity in entities:
                    if entity["entity"].startswith("SKILL"):
                        self._classify_skill(entity["word"], skills)

            if self.translator and detect(text) != 'es':
                translated = self.translator.translate(text)
                trans_doc = self.nlp(translated.lower())
                trans_matches = self.phrase_matcher(trans_doc)
                for _, start, end in trans_matches:
                    skill = trans_doc[start:end].text
                    self._classify_skill(skill, skills)

            self._update_catalogs(skills)

        return {k: list(set(v)) for k, v in skills.items()}

    def _classify_skill(self, skill: str, skills_dict: Dict[str, List[str]]):
        skill_lower = skill.lower()
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    if isinstance(details, dict):
                        for category, key in [("Habilidades Técnicas", "technical"), ("Habilidades Blandas", "soft"),
                                             ("Certificaciones", "certifications"), ("Herramientas", "tools")]:
                            if skill_lower in [s.lower() for s in details.get(category, [])]:
                                skills_dict[key].append(skill_lower)

    def _update_catalogs(self, skills: Dict[str, List[str]]):
        skills_catalog = load_catalog(CATALOG_PATHS["es"]["skills"])
        if "division1" not in skills_catalog:
            skills_catalog["division1"] = {"role1": {"Habilidades Técnicas": [], "Habilidades Blandas": [], "Certificaciones": [], "Herramientas": []}}
        for category, key in [("Habilidades Técnicas", "technical"), ("Habilidades Blandas", "soft"), ("Certificaciones", "certifications"), ("Herramientas", "tools")]:
            current = skills_catalog["division1"]["role1"][category]
            for skill in skills[key]:
                if skill not in [s.lower() for s in current]:
                    current.append(skill.capitalize())
        save_catalog(CATALOG_PATHS["es"]["skills"], skills_catalog)

    def analyze_candidate(self, text: str) -> Dict[str, any]:
        skills = self.extract_skills(text)
        sentiment = self.get_sentiment(text)
        result = {"skills": skills, "sentiment": sentiment["label"], "sentiment_score": sentiment["score"]}
        if self.mode == 'deep':
            result["entities"] = self.extract_entities(text)
            result["experience_level"] = self._detect_experience_level(text)
        return result

    def _detect_experience_level(self, text: str) -> Dict[str, str]:
        levels = {}
        doc = self.nlp(text.lower())
        for sent in doc.sents:
            for skill in self.all_skills:
                if skill in sent.text:
                    if any(w in sent.text for w in ["experto", "avanzado", "senior"]):
                        levels[skill] = "advanced"
                    elif any(w in sent.text for w in ["básico", "principiante", "junior"]):
                        levels[skill] = "basic"
                    else:
                        levels[skill] = "intermediate"
        return levels

class OpportunityProcessor(BaseNLPProcessor):
    def __init__(self, language: str = 'es', mode: str = 'quick'):
        super().__init__(language, mode)
        if mode == 'deep' and TRANSFORMERS_AVAILABLE:
            self.linkedin_ner = advanced_model_manager.get_ner_pipeline("/home/pablo/skills_data/algiraldohe_lm-ner-linkedin-skills-recognition")
            self.ihk_ner = advanced_model_manager.get_ner_pipeline("/home/pablo/skills_data/ihk_skillner")
        else:
            self.linkedin_ner = None
            self.ihk_ner = None

    def extract_opportunity_details(self, text: str) -> Dict[str, any]:
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        doc = self.nlp(text.lower())
        details = {"skills": {"technical": [], "soft": [], "certifications": []}, "location": None, "role": None, "contract_type": None}

        matches = self.phrase_matcher(doc)
        for _, start, end in matches:
            skill = doc[start:end].text
            self._classify_skill(skill, details["skills"])

        if self.mode == 'deep':
            if self.matcher:
                flex_matches = self.matcher(doc)
                for _, start, end in flex_matches:
                    skill = doc[start:end].text.split()[-1]
                    self._classify_skill(skill, details["skills"])
            if self.linkedin_ner:
                entities = self.linkedin_ner(text)
                for entity in entities:
                    if entity["entity"].startswith("SKILL"):
                        self._classify_skill(entity["word"], details["skills"])
            if self.ihk_ner:
                entities = self.ihk_ner(text)
                for entity in entities:
                    if entity["entity"].startswith("SKILL"):
                        self._classify_skill(entity["word"], details["skills"])
            self._update_catalogs(details["skills"])

        for ent in doc.ents:
            if ent.label_ in ["LOC", "GPE"]:
                details["location"] = ent.text
                break
        details["role"] = self._identify_role(text)
        if self.mode == 'deep':
            details["contract_type"] = self._detect_contract_type(text)

        details["skills"] = {k: list(set(v)) for k, v in details["skills"].items()}
        return details

    def _classify_skill(self, skill: str, skills_dict: Dict[str, List[str]]):
        skill_lower = skill.lower()
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    if isinstance(details, dict):
                        for category, key in [("Habilidades Técnicas", "technical"), ("Habilidades Blandas", "soft"), ("Certificaciones", "certifications")]:
                            if skill_lower in [s.lower() for s in details.get(category, [])]:
                                skills_dict[key].append(skill_lower)

    def _update_catalogs(self, skills: Dict[str, List[str]]):
        skills_catalog = load_catalog(CATALOG_PATHS["es"]["skills"])
        if "division1" not in skills_catalog:
            skills_catalog["division1"] = {"role1": {"Habilidades Técnicas": [], "Habilidades Blandas": [], "Certificaciones": []}}
        for category, key in [("Habilidades Técnicas", "technical"), ("Habilidades Blandas", "soft"), ("Certificaciones", "certifications")]:
            current = skills_catalog["division1"]["role1"][category]
            for skill in skills[key]:
                if skill not in [s.lower() for s in current]:
                    current.append(skill.capitalize())
        save_catalog(CATALOG_PATHS["es"]["skills"], skills_catalog)

    def _identify_role(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role in role_category.keys():
                    if role.lower() in text_lower:
                        return role
        return None

    def _detect_contract_type(self, text: str) -> Optional[str]:
        contract_types = ["permanente", "temporal", "freelance", "full-time", "part-time"]
        for sent in self.nlp(text.lower()).sents:
            for ctype in contract_types:
                if ctype in sent.text:
                    return ctype
        return None

    def analyze_opportunity(self, text: str) -> Dict[str, any]:
        details = self.extract_opportunity_details(text)
        sentiment = self.get_sentiment(text)
        result = {"details": details, "sentiment": sentiment["label"], "sentiment_score": sentiment["score"]}
        if self.mode == 'deep':
            result["entities"] = self.extract_entities(text)
        return result

class NLPProcessor:
    def __init__(self, language: str = 'es', mode: str = 'opportunity', analysis_depth: str = 'quick'):
        self.language = language
        self.mode = mode.lower()
        self.analysis_depth = analysis_depth.lower()
        if self.analysis_depth not in ['quick', 'deep']:
            logger.warning(f"Profundidad '{self.analysis_depth}' no válida. Usando 'quick'.")
            self.analysis_depth = 'quick'
        if self.mode == 'candidate':
            self.processor = CandidateProcessor(language=self.language, mode=self.analysis_depth)
        else:
            self.processor = OpportunityProcessor(language=self.language, mode=self.analysis_depth)
        logger.info(f"NLPProcessor: mode={self.mode}, depth={self.analysis_depth}, lang={self.language}")

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        if self.mode == 'candidate':
            return self.processor.extract_skills(text)
        return self.processor.extract_opportunity_details(text)["skills"]

    def analyze(self, text: str) -> Dict[str, any]:
        if self.mode == 'candidate':
            return self.processor.analyze_candidate(text)
        return self.processor.analyze_opportunity(text)

    def set_analysis_depth(self, depth: Literal['quick', 'deep']):
        if depth not in ['quick', 'deep']:
            logger.warning(f"Profundidad '{depth}' no válida.")
            return
        if depth != self.analysis_depth:
            self.analysis_depth = depth
            if self.mode == 'candidate':
                self.processor = CandidateProcessor(language=self.language, mode=self.analysis_depth)
            else:
                self.processor = OpportunityProcessor(language=self.language, mode=self.analysis_depth)
            logger.info(f"Profundidad cambiada a: {depth}")

def process_recent_users_batch():
    from app.models import Person
    from django.utils import timezone
    from datetime import timedelta
    recent_threshold = timezone.now() - timedelta(days=7)
    recent_users = Person.objects.filter(created_at__gte=recent_threshold)
    nlp_deep = NLPProcessor(language="es", mode="candidate", analysis_depth="deep")
    for user in recent_users:
        text = " ".join([user.metadata.get("headline", ""), user.metadata.get("experience", "")])
        if text:
            result = nlp_deep.analyze(text)
            user.metadata["skills"] = result["skills"]
            user.metadata["sentiment"] = result["sentiment"]
            user.save()
            logger.info(f"Usuario procesado: {user.nombre} - {result}")

if __name__ == "__main__":
    nlp_quick = NLPProcessor(language='es', mode='candidate', analysis_depth='quick')
    nlp_deep = NLPProcessor(language='es', mode='candidate', analysis_depth='deep')
    text = "Tengo experiencia avanzada en Python y liderazgo en equipos."
    print("Quick:", nlp_quick.analyze(text))
    print("Deep:", nlp_deep.analyze(text))