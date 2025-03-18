# /home/pablo/app/chatbot/nlp.py  - Archivo muy relevante para la obtención de skills homologados en el sistema
import time
import psutil
import os
import sys
import subprocess
import spacy
import json
import logging
from typing import Dict, List, Optional, Set, Union, Literal
from cachetools import cachedmethod, TTLCache
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from langdetect import detect
from threading import Lock
from datetime import datetime

# Importaciones condicionales
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelos disponibles por idioma y tamaño
MODEL_LANGUAGES = {
    "es": {"sm": "es_core_news_sm", "md": "es_core_news_md", "lg": "es_core_news_lg"},
    "en": {"sm": "en_core_web_sm", "md": "en_core_web_md", "lg": "en_core_web_lg"},
    "fr": {"sm": "fr_core_news_sm", "md": "fr_core_news_md", "lg": "fr_core_news_lg"},
    "default": {"sm": "xx_ent_wiki_sm", "md": "xx_ent_wiki_sm", "lg": "xx_ent_wiki_sm"}
}

# Ruta base para catálogos
CATALOG_BASE_PATH = "/home/pablo/skills_data"

# Lock para escritura segura
json_lock = Lock()

# Inicialización de VADER para análisis de sentimiento
nltk.download('vader_lexicon', quiet=True)
SIA = SentimentIntensityAnalyzer()

class CatalogManager:
    """Maneja la carga y actualización de catálogos de manera centralizada."""
    def __init__(self, base_path: str = CATALOG_BASE_PATH):
        self.base_path = base_path
        self.catalogs = {}

    def load_catalog(self, catalog_name: str) -> Dict:
        """Carga un catálogo desde archivo JSON."""
        path = os.path.join(self.base_path, f"{catalog_name}.json")
        if path in self.catalogs:
            return self.catalogs[path]
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.catalogs[path] = data
            logger.info(f"Catálogo cargado: {path}")
            return data
        except Exception as e:
            logger.error(f"Error cargando {path}: {e}")
            return {}

    def save_catalog(self, catalog_name: str, data: Dict) -> None:
        """Guarda un catálogo en archivo JSON."""
        path = os.path.join(self.base_path, f"{catalog_name}.json")
        with json_lock:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.catalogs[path] = data
                logger.info(f"Catálogo actualizado: {path}")
            except Exception as e:
                logger.error(f"Error guardando {path}: {e}")

    def get_all_skills(self, catalog_names: List[str]) -> Set[str]:
        """Obtiene todas las habilidades de una lista de catálogos."""
        skills = set()
        for name in catalog_names:
            catalog = self.load_catalog(name)
            if isinstance(catalog, dict):
                for division in catalog.values():
                    for role in division.values():
                        for category in ["Habilidades Técnicas", "Habilidades Blandas", "Certificaciones", "Herramientas"]:
                            skills.update(s.lower() for s in role.get(category, []))
        return skills

class ModelManager:
    """Gestiona modelos de spaCy y transformers con caché."""
    def __init__(self):
        self.spacy_cache = TTLCache(maxsize=10, ttl=21600)  # 6 horas
        self.transformer_cache = TTLCache(maxsize=5, ttl=21600)

    def get_spacy_model(self, lang: str, size: str = 'sm') -> spacy.language.Language:
        """Obtiene o carga un modelo spaCy."""
        key = f"{lang}_{size}"
        if key in self.spacy_cache:
            return self.spacy_cache[key]
        model_name = MODEL_LANGUAGES.get(lang, MODEL_LANGUAGES["default"]).get(size, "xx_ent_wiki_sm")
        try:
            model = spacy.load(model_name)
        except OSError:
            logger.info(f"Descargando modelo {model_name}...")
            subprocess.check_call([sys.executable, "-m", "spacy", "download", model_name])
            model = spacy.load(model_name)
        self.spacy_cache[key] = model
        return model

    def get_transformer_pipeline(self, task: str, model_path: str) -> Optional[pipeline]:
        """Obtiene un pipeline de transformers si está disponible."""
        if not TRANSFORMERS_AVAILABLE:
            return None
        key = f"{task}_{model_path}"
        if key in self.transformer_cache:
            return self.transformer_cache[key]
        try:
            pipe = pipeline(task, model=model_path)
            self.transformer_cache[key] = pipe
            return pipe
        except Exception as e:
            logger.error(f"Error cargando transformer {model_path}: {e}")
            return None

class NLPProcessor:
    """Procesador base de NLP para candidatos y oportunidades."""
    def __init__(self, language: str = 'es', mode: Literal['candidate', 'opportunity'] = 'opportunity', analysis_depth: Literal['quick', 'deep'] = 'quick'):
        self.language = language
        self.mode = mode
        self.analysis_depth = analysis_depth  # Usar analysis_depth directamente
        self.catalog_mgr = CatalogManager()
        self.model_mgr = ModelManager()
        self.nlp = self.model_mgr.get_spacy_model(language, 'sm' if analysis_depth == 'quick' else 'md')
        self.skills = self.catalog_mgr.get_all_skills(["skills", "occupations_es", "skills_relax", "skills_opportunities"])
        self.phrase_matcher = self._build_phrase_matcher()
        self.sentiment_analyzer = SIA if analysis_depth == 'quick' or not TRANSFORMERS_AVAILABLE else self.model_mgr.get_transformer_pipeline('sentiment-analysis', 'cardiffnlp/twitter-roberta-base-sentiment-latest')
        self.translator = GoogleTranslator(source='auto', target='es') if TRANSLATOR_AVAILABLE and analysis_depth == 'deep' else None

    def _build_phrase_matcher(self) -> spacy.matcher.PhraseMatcher:
        """Construye un PhraseMatcher para habilidades."""
        matcher = spacy.matcher.PhraseMatcher(self.nlp.vocab, attr='LOWER')
        patterns = [self.nlp.make_doc(skill) for skill in self.skills]
        matcher.add("SKILL", patterns)
        return matcher

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extrae habilidades del texto."""
        doc = self.nlp(text.lower())
        skills = {"technical": [], "soft": [], "certifications": [], "tools": []}
        matches = self.phrase_matcher(doc)
        for _, start, end in matches:
            skill = doc[start:end].text
            self._classify_skill(skill, skills)
        return skills

    def _classify_skill(self, skill: str, skills_dict: Dict[str, List[str]]) -> None:
        """Clasifica una habilidad en su categoría."""
        skill_lower = skill.lower()
        catalog = self.catalog_mgr.load_catalog("skills")
        for division in catalog.values():
            for role in division.values():
                for category, key in [("Habilidades Técnicas", "technical"), ("Habilidades Blandas", "soft"), ("Certificaciones", "certifications"), ("Herramientas", "tools")]:
                    if skill_lower in [s.lower() for s in role.get(category, [])]:
                        skills_dict[key].append(skill_lower)

    def analyze(self, text: str) -> Dict[str, any]:
        """Analiza el texto según el modo."""
        skills = self.extract_skills(text)
        sentiment = self.get_sentiment(text)
        result = {"skills": skills, "sentiment": sentiment["label"], "sentiment_score": sentiment["score"]}
        return result

    def get_sentiment(self, text: str) -> Dict[str, Union[str, float]]:
        """Obtiene el sentimiento del texto."""
        if not self.sentiment_analyzer:
            return {"label": "neutral", "score": 0.0}
        if self.analysis_depth == 'quick':
            scores = SIA.polarity_scores(text)
            compound = scores['compound']
            label = "positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral"
            return {"label": label, "score": abs(compound)}
        result = self.sentiment_analyzer(text[:512])[0]
        return {"label": result["label"], "score": result["score"]}

# Instancia global para compartir entre scripts
nlp_processor = NLPProcessor()

if __name__ == "__main__":
    # Ejemplo de uso
    sample_text = "Tengo experiencia en Python, liderazgo y gestión de proyectos."
    result = nlp_processor.analyze(sample_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))