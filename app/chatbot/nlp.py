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

# Importación condicional para análisis profundo
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Modelos spaCy por idioma
MODEL_LANGUAGES = {
    "es": "es_core_news_md",      # Español
    "en": "en_core_web_md",       # Inglés
    "fr": "fr_core_news_md",      # Francés
    "default": "xx_ent_wiki_sm"   # Multilingüe por defecto
}

# Rutas a los catálogos
CATALOG_PATHS = {
    "es": {
        "skills": "catalogs/skills_es.json",
        "occupations": "catalogs/occupations_es.json"
    },
    "en": {
        "skills": "catalogs/skills_en.json",
        "occupations": "catalogs/occupations_en.json"
    }
}

# Ruta al catálogo de habilidades
SKILLS_JSON_PATH = "/home/pablo/app/utilidades/catalogs/skills.json"

# Paths to CSV files
csv_paths = {
    "occupations_es": "/home/pablo/app/utilidades/catalogs/occupations_es.csv",
    "skills_es": "/home/pablo/app/utilidades/catalogs/skills_es.csv"
}

# Paths to JSON files
json_paths = {
    "occupations_es": "/home/pablo/app/utilidades/catalogs/occupations_es.json",
    "skills_es": "/home/pablo/app/utilidades/catalogs/skills_es.json"
}

def create_json_from_csv(csv_path, json_path):
    """Crea un archivo JSON a partir de un CSV si el JSON no existe."""
    import os
    
    # Check if the JSON already exists
    if os.path.exists(json_path):
        return True
        
    # Check if CSV exists
    if not os.path.exists(csv_path):
        logger.warning(f"CSV file {csv_path} does not exist.")
        
        # Create an empty JSON file if the directory exists
        json_dir = os.path.dirname(json_path)
        if not os.path.exists(json_dir):
            try:
                os.makedirs(json_dir)
                logger.info(f"Created directory: {json_dir}")
            except Exception as e:
                logger.error(f"Error creating directory {json_dir}: {e}")
                return False
        
        # Create an empty JSON file
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write('[]')  # Empty JSON array
            logger.info(f"Created empty JSON file: {json_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating empty JSON file {json_path}: {e}")
            return False
    
    # If CSV exists, convert it to JSON
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        df.to_json(json_path, orient='records', force_ascii=False)
        logger.info(f"Created {json_path} from {csv_path} with UTF-8")
        return True
    except UnicodeDecodeError:
        logger.info("Error with UTF-8, trying with ISO-8859-1...")
        try:
            df = pd.read_csv(csv_path, encoding='ISO-8859-1')
            df.to_json(json_path, orient='records', force_ascii=False)
            logger.info(f"Created {json_path} with ISO-8859-1")
            return True
        except Exception as e:
            logger.error(f"Error processing CSV with ISO-8859-1: {e}")
            return False
    except Exception as e:
        logger.error(f"Error processing CSV {csv_path}: {e}")
        return False

# Inicializar NLTK VADER para análisis de sentimientos (análisis rápido)
try:
    nltk.download('vader_lexicon', quiet=True)
    SIA = SentimentIntensityAnalyzer()
except Exception as e:
    logger.error(f"Error inicializando NLTK VADER: {e}")
    SIA = None

# Asegurar que los JSON existan
for csv_key, json_key in [("occupations_es", "occupations_es"), ("skills_es", "skills_es")]:
    success = create_json_from_csv(csv_paths[csv_key], json_paths[json_key])
    if not success:
        logger.warning(f"Could not create/find {json_key} data. Some functionality may be limited.")

def load_catalog(path: str) -> Dict:
    """Carga un catálogo desde un archivo JSON."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando {path}: {e}")
        return {}

class ModelManager:
    """Gestor de modelos spaCy con caché y descarga bajo demanda."""
    def __init__(self):
        # Caché con límite de 5 modelos y tiempo de vida de 6 horas
        self.model_cache = TTLCache(maxsize=5, ttl=21600)

    def get_model(self, lang: str, size: str = 'md') -> spacy.language.Language:
        """
        Obtiene el modelo spaCy para el idioma, descargándolo si es necesario.
        
        Args:
            lang: Código de idioma ('es', 'en', etc.)
            size: Tamaño del modelo ('sm', 'md', 'lg') - solo usado para análisis profundo
        """
        cache_key = f"{lang}_{size}"
        if cache_key in self.model_cache:
            return self.model_cache[cache_key]
        
        model_name = MODEL_LANGUAGES.get(lang, MODEL_LANGUAGES["default"])
        # Si se pide un modelo pequeño y estamos usando modelo mediano, usamos el pequeño para quick mode
        if size == 'sm' and 'md' in model_name:
            model_name = model_name.replace('md', 'sm')
        
        try:
            model = spacy.load(model_name)
            logger.info(f"Modelo {model_name} cargado desde el sistema.")
        except OSError:
            logger.info(f"Modelo {model_name} no encontrado. Descargando...")
            subprocess.check_call([sys.executable, "-m", "spacy", "download", model_name])
            model = spacy.load(model_name)
            logger.info(f"Modelo {model_name} descargado y cargado.")
        
        self.model_cache[cache_key] = model
        return model

# Instancia global del gestor de modelos
model_manager = ModelManager()

class BaseNLPProcessor:
    """Clase base para procesadores NLP con interfaz común."""
    def __init__(self, language: str = 'es', mode: str = 'quick'):
        """
        Inicializa el procesador NLP base.
        
        Args:
            language: Código de idioma ('es', 'en', etc.)
            mode: Modo de análisis ('quick' o 'deep')
        """
        self.language = language
        self.mode = mode
        self.skills_catalog = load_catalog(CATALOG_PATHS.get(language, CATALOG_PATHS["es"])["skills"])
        self.occupations_catalog = load_catalog(CATALOG_PATHS.get(language, CATALOG_PATHS["es"])["occupations"])
        
        # Elegir el tamaño del modelo según el modo
        model_size = 'sm' if mode == 'quick' else 'md'
        self.nlp = model_manager.get_model(language, model_size)
        
        # Caché optimizada según el modo
        cache_ttl = 3600 if mode == 'quick' else 7200  # 1h en modo rápido, 2h en modo profundo
        self.skill_cache = TTLCache(maxsize=5000, ttl=cache_ttl)
        
        # Inicializar analizador de sentimiento según el modo
        self.sentiment_analyzer = self._init_sentiment_analyzer()
    
    def _init_sentiment_analyzer(self):
        """Inicializa el analizador de sentimiento apropiado según el modo."""
        if self.mode == 'quick' or not self._is_transformers_available():
            return SIA
        
        # Solo carga transformers en modo profundo
        try:
            from transformers import pipeline
            return pipeline('sentiment-analysis', 
                           model='cardiffnlp/twitter-roberta-base-sentiment-latest')
        except Exception as e:
            logger.warning(f"No se pudo cargar transformers: {e}. Usando NLTK VADER.")
            return SIA
    
    def _is_transformers_available(self):
        """Verifica si transformers está disponible."""
        try:
            import transformers
            return True
        except ImportError:
            return False
    
    def get_sentiment(self, text: str) -> str:
        """Analiza el sentimiento según el modo configurado."""
        if self.mode == 'quick' or not hasattr(self.sentiment_analyzer, '__call__'):
            # Análisis rápido con VADER
            if SIA:
                try:
                    scores = SIA.polarity_scores(text)
                    compound = scores['compound']
                    if compound >= 0.05:
                        return "positive"
                    elif compound <= -0.05:
                        return "negative"
                except Exception as e:
                    logger.error(f"Error con NLTK VADER: {e}")
            return "neutral"
        
        # Análisis profundo con transformers
        try:
            result = self.sentiment_analyzer(text[:512])
            return result[0]['label']
        except Exception as e:
            logger.error(f"Error con sentiment pipeline: {e}")
            return "neutral"

    def extract_entities(self, text: str) -> List[str]:
        """Extrae entidades nombradas con spaCy."""
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        doc = self.nlp(text.lower())
        return [ent.text.lower() for ent in doc.ents]

class CandidateProcessor(BaseNLPProcessor):
    """Procesador NLP para candidatos con máxima extracción de habilidades."""
    def __init__(self, language: str = 'es', mode: str = 'quick'):
        super().__init__(language, mode)
        self.all_skills = self._get_all_skills()
        self.phrase_matcher = self._build_phrase_matcher()
        
        # Solo construir matcher complejo en modo deep
        if self.mode == 'deep':
            self.matcher = self._build_matcher()
        else:
            self.matcher = None
            
        # Solo inicializar traductor en modo deep si está disponible
        if self.mode == 'deep' and TRANSLATOR_AVAILABLE:
            from deep_translator import GoogleTranslator
            self.translator = GoogleTranslator(source='auto', target='es')
            self.translation_cache = TTLCache(maxsize=1000, ttl=3600)
        else:
            self.translator = None

    def _get_all_skills(self) -> set:
        """Extrae todas las habilidades del catálogo."""
        skills = set()
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    if isinstance(details, dict):
                        for category in ["Habilidades Técnicas", "Habilidades Blandas", "Certificaciones", "Herramientas"]:
                            skills.update([s.lower() for s in details.get(category, [])])
                    elif isinstance(details, list):
                        for item in details:
                            if isinstance(item, list):
                                skills.update([s.lower() for s in item if isinstance(s, str)])
                            elif isinstance(item, str):
                                skills.add(item.lower())
        return skills

    def _build_phrase_matcher(self) -> PhraseMatcher:
        """Construye un PhraseMatcher para coincidencias exactas."""
        matcher = PhraseMatcher(self.nlp.vocab, attr='LOWER')
        patterns = [self.nlp.make_doc(skill) for skill in self.all_skills]
        matcher.add("SKILL", patterns)
        return matcher

    def _build_matcher(self) -> Matcher:
        """Construye un Matcher para patrones flexibles - solo modo deep."""
        matcher = Matcher(self.nlp.vocab)
        for skill in self.all_skills:
            pattern = [{"LOWER": {"IN": ["experiencia", "conocimiento", "uso", "habilidad"]}, "OP": "*"},
                      {"LOWER": skill}]
            matcher.add("FLEXIBLE_SKILL", [pattern])
        return matcher

    @cachedmethod(lambda self: self.skill_cache)
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extrae habilidades con diferente nivel de profundidad según el modo."""
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        doc = self.nlp(text.lower())
        skills = {"technical": [], "soft": [], "certifications": [], "tools": []}

        # Coincidencias básicas con PhraseMatcher - funciona en ambos modos
        matches = self.phrase_matcher(doc)
        for _, start, end in matches:
            skill = doc[start:end].text
            self._classify_skill(skill, skills)

        # Análisis más profundo solo en modo 'deep'
        if self.mode == 'deep':
            # Coincidencias flexibles con Matcher
            flex_matches = self.matcher(doc)
            for _, start, end in flex_matches:
                skill = doc[start:end].text.split()[-1]
                self._classify_skill(skill, skills)

            # Búsqueda por tokens individuales
            for token in doc:
                if token.text in self.all_skills:
                    self._classify_skill(token.text, skills)
                    
            # Traducción para textos no españoles (si está disponible)
            if self.translator and self.language != 'es':
                try:
                    translated_text = self.translator.translate(text)
                    # Analizar traducción para detectar más habilidades
                    trans_doc = self.nlp(translated_text.lower())
                    trans_matches = self.phrase_matcher(trans_doc)
                    for _, start, end in trans_matches:
                        skill = trans_doc[start:end].text
                        self._classify_skill(skill, skills)
                except Exception as e:
                    logger.error(f"Error en traducción: {e}")

        return skills

    def _classify_skill(self, skill: str, skills_dict: Dict[str, List[str]], unit: str = None):
        """Clasifica una habilidad según el catálogo."""
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
                        for item in details:
                            if isinstance(item, list):
                                if skill_lower in [s.lower() for s in item if isinstance(s, str)]:
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
        
        # En modo profundo, añadir más análisis
        if self.mode == 'deep':
            return {
                "skills": skills_data, 
                "sentiment": sentiment,
                "entities": self.extract_entities(text)
            }
        
        # En modo rápido, solo lo básico
        return {"skills": skills_data, "sentiment": sentiment}

class OpportunityProcessor(BaseNLPProcessor):
    """Procesador NLP para oportunidades laborales."""
    def __init__(self, language: str = 'es', mode: str = 'quick'):
        super().__init__(language, mode)
        self.all_skills = self._get_all_skills()
        self.phrase_matcher = self._build_phrase_matcher()
        
        # Solo construir matcher complejo en modo deep
        if self.mode == 'deep':
            self.matcher = self._build_matcher()
        else:
            self.matcher = None

    def _get_all_skills(self) -> set:
        """Extrae todas las habilidades del catálogo."""
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
        """Construye un Matcher para patrones flexibles - solo modo deep."""
        matcher = Matcher(self.nlp.vocab)
        for skill in self.all_skills:
            pattern = [{"LOWER": {"IN": ["requiere", "necesita", "con", "en"]}, "OP": "*"},
                      {"LOWER": skill}]
            matcher.add("FLEXIBLE_SKILL", [pattern])
        return matcher

    def extract_opportunity_details(self, text: str) -> dict[str, any]:
        """Extrae detalles de oportunidad con diferente nivel de profundidad según el modo."""
        from app.chatbot.utils import clean_text
        text = clean_text(text)
        doc = self.nlp(text.lower())
        details = {
            "skills": {"technical": [], "soft": [], "certifications": []},
            "location": None,
            "role": None
        }
        
        # También extraer tipo de contrato en modo profundo
        if self.mode == 'deep':
            details["contract_type"] = None

        # Extraer habilidades con PhraseMatcher - común en ambos modos
        matches = self.phrase_matcher(doc)
        for _, start, end in matches:
            skill = doc[start:end].text
            self._classify_skill(skill, details["skills"])

        # Análisis más profundo solo en modo 'deep'
        if self.mode == 'deep' and self.matcher:
            # Coincidencias flexibles
            flex_matches = self.matcher(doc)
            for _, start, end in flex_matches:
                skill = doc[start:end].text.split()[-1]
                self._classify_skill(skill, details["skills"])

            # Análisis por tokens
            for token in doc:
                if token.text in self.all_skills:
                    self._classify_skill(token.text, details["skills"])

        # Extraer ubicación - siempre
        for ent in doc.ents:
            if ent.label_ in ["LOC", "GPE"]:
                details["location"] = ent.text
                break
                
        # Extraer rol - siempre pero con diferentes métodos según el modo
        if self.mode == 'quick':
            # Método simple para encontrar rol
            role = self._identify_role(text)
            if role:
                details["role"] = role
        else:
            # Método más avanzado en modo profundo
            for sent in doc.sents:
                if "se busca" in sent.text:
                    possible_role = sent.text.replace("se busca", "").split("con")[0].strip()
                    details["role"] = possible_role
                    break
                elif "vacante" in sent.text:
                    possible_role = sent.text.split("vacante")[1].split("para")[0].strip()
                    details["role"] = possible_role
                    break
            
            # Extraer tipo de contrato - solo en modo profundo
            contract_keywords = ["contrato", "tipo de empleo"]
            contract_types = ["permanente", "temporal", "freelance", "full-time", "part-time"]
            for sent in doc.sents:
                for keyword in contract_keywords:
                    if keyword in sent.text:
                        for ctype in contract_types:
                            if ctype in sent.text:
                                details["contract_type"] = ctype
                                break

        # Normalizar resultados
        details["skills"] = {k: list(set(v)) for k, v in details["skills"].items()}
        return details
    
    def _classify_skill(self, skill: str, skills_dict: Dict[str, List[str]]):
        """Clasifica habilidades para oportunidades."""
        skill_lower = skill.lower()
        for division in self.skills_catalog.values():
            for role_category in division.values():
                for role, details in role_category.items():
                    if isinstance(details, dict):
                        if skill_lower in [s.lower() for s in details.get("Habilidades Técnicas", [])]:
                            skills_dict["technical"].append(skill_lower)
                        elif skill_lower in [s.lower() for s in details.get("Habilidades Blandas", [])]:
                            skills_dict["soft"].append(skill_lower)
                        elif "Certificaciones" in skills_dict and skill_lower in [s.lower() for s in details.get("Certificaciones", [])]:
                            skills_dict["certifications"].append(skill_lower)
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

    def analyze_opportunity(self, text: str) -> Dict[str, any]:
        """Analiza una oportunidad laboral completa."""
        details = self.extract_opportunity_details(text)
        sentiment = self.get_sentiment(text)
        
        # En modo deep, añadir clasificación de trabajo
        if self.mode == 'deep':
            doc = self.nlp(text.lower())
            job_classification = "unknown"
            for ent in doc.ents:
                if "ingeniero" in ent.text.lower() or "engineer" in ent.text.lower():
                    job_classification = "Software Engineer"
                    break
                
            return {
                "details": details, 
                "sentiment": sentiment,
                "job_classification": job_classification,
                "entities": self.extract_entities(text)
            }
        
        # En modo rápido, solo lo básico
        return {"details": details, "sentiment": sentiment}

class NLPProcessor:
    """
    Clase principal que mantiene compatibilidad con código existente.
    Permite elegir entre modo rápido y profundo.
    """
    def __init__(self, language: str = 'es', mode: str = 'opportunity', analysis_depth: str = 'quick'):
        """
        Inicializa el procesador NLP.
        
        Args:
            language: Código de idioma ('es', 'en', etc.)
            mode: Tipo de análisis ('candidate' o 'opportunity')
            analysis_depth: Profundidad de análisis ('quick' o 'deep')
        """
        self.language = language
        self.mode = mode.lower()
        self.analysis_depth = analysis_depth.lower()
        
        # Validar y corregir parámetros
        if self.analysis_depth not in ['quick', 'deep']:
            logger.warning(f"Modo de análisis '{self.analysis_depth}' no válido. Usando 'quick'.")
            self.analysis_depth = 'quick'
            
        if self.mode == 'candidate':
            self.processor = CandidateProcessor(language=self.language, mode=self.analysis_depth)
        else:
            self.processor = OpportunityProcessor(language=self.language, mode=self.analysis_depth)
            
        logger.info(f"NLPProcessor inicializado: modo={self.mode}, profundidad={self.analysis_depth}, idioma={self.language}")

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
        
    def set_analysis_depth(self, depth: Literal['quick', 'deep']):
        """
        Cambia la profundidad de análisis dinámicamente.
        Útil para cambiar entre modos sin crear una nueva instancia.
        """
        if depth not in ['quick', 'deep']:
            logger.warning(f"Modo de análisis '{depth}' no válido. No se cambió el modo.")
            return
            
        if depth != self.analysis_depth:
            self.analysis_depth = depth
            # Reinicializar el procesador con la nueva profundidad
            if self.mode == 'candidate':
                self.processor = CandidateProcessor(language=self.language, mode=self.analysis_depth)
            else:
                self.processor = OpportunityProcessor(language=self.language, mode=self.analysis_depth)
            logger.info(f"Profundidad de análisis cambiada a: {depth}")

# Ejemplo de uso
if __name__ == "__main__":
    # Procesador rápido para chatbot
    nlp_quick = NLPProcessor(language='es', mode='candidate', analysis_depth='quick')
    text_candidate = "Tengo experiencia en Python y trabajo en equipo."
    result_quick = nlp_quick.analyze(text_candidate)
    print("Análisis rápido:", result_quick)
    
    # Procesador profundo para batch
    nlp_deep = NLPProcessor(language='es', mode='candidate', analysis_depth='deep')
    result_deep = nlp_deep.analyze(text_candidate)
    print("Análisis profundo:", result_deep)
    
    # Cambiar dinámicamente
    nlp_quick.set_analysis_depth('deep')
    result_changed = nlp_quick.analyze(text_candidate)
    print("Después de cambio a modo profundo:", result_changed)