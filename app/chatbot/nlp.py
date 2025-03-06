# 📌 Ubicación en servidor: /home/pablo/app/chatbot/nlp.py
"""
nlp.py - Integración completa:
1) Parse RDF de ESCO y genera esco_from_rdf.json
2) ExternalSkillDataLoader y ESCOApiLoader para CSV/API
3) SkillDBMerger para fusionar bases en combined_skills.json
4) SkillExtractionPipeline (básica) y SkillExtractorManager (avanzada)
5) NLPProcessor con la misma interfaz, usando skillNer + heurísticas

Al final, en __main__, lo orquestamos:
- Parse RDF (opcional)
- run_all() para CSV,
- Merger,
- Pipeline para prueba.
- O la versión con SkillExtractorManager y NLPProcessor.

Algunas rutas y funciones son ejemplos; ajusta a tu estructura de proyecto.
"""

import os
import csv
import json
import logging
import asyncio
import spacy
import requests
import nltk
import unidecode
import threading
import shelve
import torch
import re
from nltk import word_tokenize, ngrams
from cachetools import cachedmethod, TTLCache
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from spacy.matcher import PhraseMatcher, Matcher
from skillNer.skill_extractor_class import SkillExtractor
from skillNer.general_params import SKILL_DB
from typing import Dict, Any, List, Optional, Set, Tuple
from cachetools import TTLCache, cachedmethod
from logging.handlers import RotatingFileHandler


from app.chatbot.extractors import ESCOExtractor, NICEExtractor, ONETExtractor, CareerOneStopExtractor, unify_data, parse_esco_rdf_to_json

# ============== CONFIGURACIÓN LOGGING ==============
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler("logs/nlp.log", maxBytes=5 * 1024 * 1024, backupCount=3),
        logging.StreamHandler()
    ]
)

CONFIG = {
    "OUTPUT_DIR": "/home/pablo/skills_data",
    "COMBINED_DB_PATH": os.path.join("OUTPUT_DIR", "combined_skills.json"),
    "CACHE_DB_PATH": "/home/pablo/cache/skill_cache.db"
}
# ============== CONFIGURACIÓN NLTK ==============
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# ============== PLACEHOLDERS Y DICCIONARIOS (para roles, business_units, etc.) ==============
# <<<--- EJEMPLOS: ajusta a tu realidad

BUSINESS_UNIT_SKILLS = {
    "huntRED®": {
        "Marketing": ["marketing digital", "seo", "sem", "branding"],
        "Ventas": ["negociación", "pipeline de ventas", "crm", "gestión de cuentas"],
    },
    "Amigro®": {
        "Operaciones": ["mantenimiento básico", "montacargas", "control de calidad"],
        "Logística": ["cadena de suministro", "almacén", "gestión de inventarios"],
    },
    # ...
}

def get_all_skills_for_unit(business_unit: str = "huntRED®") -> List[str]:
    """
    Dependiendo de la business_unit, retorna la lista de skills definidas en
    BUSINESS_UNIT_SKILLS o en tu base de datos real.
    """
    # <<<--- En tu caso real, podrías consultar una BD o un JSON más complejo
    # Por simplicidad, concateno las listas definidas en BUSINESS_UNIT_SKILLS[business_unit].
    if business_unit not in BUSINESS_UNIT_SKILLS:
        logger.warning(f"Business unit '{business_unit}' no encontrada en BUSINESS_UNIT_SKILLS.")
        return []
    skill_lists = BUSINESS_UNIT_SKILLS[business_unit].values()
    all_skills = []
    for sklist in skill_lists:
        all_skills.extend(sklist)
    return all_skills

def prioritize_interests(skills_list: List[str]) -> Dict[str, float]:
    """
    EJEMPLO: retorna un dict con cada skill y su 'peso' de 1.0.
    O podrías poner una lógica más compleja si lo deseas.
    """
    # <<<--- Esto es un placeholder
    return {skill: 1.0 for skill in skills_list}

def get_positions_by_skills(skills: Set[str], skill_weights: Dict[str, float]) -> List[str]:
    """
    Dada una lista de skills, sugiere roles o puestos. Placeholder.
    Podrías tener un mapeo 'role -> skills requeridas', y hacer un matchscore.
    """
    # <<<--- Placeholder: si detecta 'marketing digital', sugiero "Especialista en Mkt"
    suggestions = []
    if "marketing digital" in skills or "seo" in skills:
        suggestions.append("Especialista en Marketing Digital")
    if "negociación" in skills or "crm" in skills:
        suggestions.append("Ejecutivo de Ventas")
    if "mantenimiento básico" in skills:
        suggestions.append("Técnico de Operaciones")
    # ...
    return suggestions

# ============== MERGE DB =================
class SkillDBMerger:
    """
    Fusiona archivos <xxx>_skills.json en un solo combined_skills.json
    """
    def __init__(self, input_dir: str = "OUTPUT_DIR", output_file: str = "combined_skills.json"):
        self.input_dir = input_dir
        self.output_file = output_file
    
    def merge(self):
        combined_db = {}
        for filename in os.listdir(self.input_dir):
            if filename.endswith("_skills.json"):
                path = os.path.join(self.input_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        logger.info(f"Cargando {len(data)} skills desde {path}")
                        
                        for skill_id, skill_obj in data.items():
                            if skill_id not in combined_db:
                                combined_db[skill_id] = skill_obj
                            else:
                                # Combinar low_surface_forms
                                existing = combined_db[skill_id]
                                ex_lows = set(existing.get("low_surface_forms", []))
                                new_lows = set(skill_obj.get("low_surface_forms", []))
                                combined_lows = ex_lows.union(new_lows)
                                existing["low_surface_forms"] = list(combined_lows)
                except Exception as e:
                    logger.error(f"No se pudo combinar {filename}: {e}", exc_info=True)
        
        out_path = os.path.join(self.input_dir, self.output_file)
        with open(out_path, "w", encoding="utf-8") as out:
            json.dump(combined_db, out, indent=2, ensure_ascii=False)
        logger.info(f"Fusión completa. {len(combined_db)} skills totales -> {out_path}.")

# ============== EJEMPLO Pipeline (SkillExtractionPipeline) ==============
class SkillExtractionPipeline:
    """
    Pipeline básico para extracción de habilidades usando skillNer con PhraseMatcher.
    Se alimenta de un archivo combined_skills.json y un modelo de spaCy.
    """
    def __init__(self,
                 combined_db_path: str = os.path.join("OUTPUT_DIR", "combined_skills.json"),
                 language_model: str = "es_core_news_md"):
        # Asegurar que la ruta use OUTPUT_DIR correctamente
        self.combined_db_path = combined_db_path

        # Cargar la base de datos de habilidades
        if not os.path.exists(self.combined_db_path):
            logger.warning(f"⚠️ {self.combined_db_path} no existe. Usando SKILL_DB interno.")
            self.skill_db = SKILL_DB
        else:
            try:
                with open(self.combined_db_path, "r", encoding="utf-8") as f:
                    self.skill_db = json.load(f)
                if not isinstance(self.skill_db, dict):
                    raise ValueError("El archivo JSON no contiene un diccionario válido.")
                logger.info(f"✅ {len(self.skill_db)} habilidades cargadas desde {self.combined_db_path}.")
            except Exception as e:
                logger.error(f"❌ Error cargando {self.combined_db_path}: {e}. Usando SKILL_DB.")
                self.skill_db = SKILL_DB

        # Cargar el modelo spaCy
        self.nlp = None
        try:
            self.nlp = spacy.load(language_model)
            logger.info(f"✅ Modelo spaCy '{language_model}' cargado.")
        except Exception as e:
            logger.error(f"❌ No se pudo cargar {language_model}: {e}. Intentando fallback.")
            try:
                self.nlp = spacy.load("es_core_news_sm")
                logger.info("✅ Modelo fallback 'es_core_news_sm' cargado.")
            except Exception as e:
                logger.error(f"❌ No se pudo cargar el modelo fallback: {e}.")

        # Inicializar SkillExtractor solo si hay un modelo spaCy válido
        self.skill_extractor = None
        if self.nlp:
            try:
                self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
                self.skill_extractor = SkillExtractor(
                    nlp=self.nlp,
                    skills_db=self.skill_db,
                    phraseMatcher=self.phrase_matcher
                )
                logger.info("✅ SkillExtractor (skillNer) inicializado con éxito (pipeline básico).")
            except Exception as e:
                logger.error(f"❌ Error inicializando SkillExtractor: {e}", exc_info=True)
        else:
            logger.error("❌ No se puede inicializar SkillExtractor sin un modelo spaCy.")

    def extract_skills(self, text: str) -> List[str]:
        if not self.skill_extractor:
            logger.warning("SkillExtractor no disponible.")
            return []
        
        doc = self.nlp(text)
        res = self.skill_extractor.annotate(doc)
        detected = set()
        if "results" in res:
            for match_type in ["full_matches", "ngram_scored"]:
                if match_type in res["results"]:
                    for info in res["results"][match_type]:
                        val = info.get("doc_node_value","").strip().lower()
                        if val:
                            detected.add(val)
        return list(detected)

    def debug_extract(self, text: str):
        skills = self.extract_skills(text)
        logger.info(f"{text} -> {skills}")

# ============== AVANZADO: SkillExtractorManager + heurísticas ==============
class SkillExtractorManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, language: str = "es"):
        self.language = language
        self.skill_cache = shelve.open(CONFIG["CACHE_DB_PATH"], 'c')
        self._nlp = load_nlp_model(language)
        if not self._nlp:
            logger.error("❌ No se pudo cargar el modelo NLP. SkillExtractorManager no iniciado.")
            self._skill_extractor = None
            return
        self._skill_db = load_skill_dbs()
        logger.info(f"🔎 skill_db combinada contiene {len(self._skill_db)} ítems")
        self._common_terms = load_common_terms()
        self._phrase_matcher = PhraseMatcher(self._nlp.vocab, attr="LOWER")
        self._matcher = Matcher(self._nlp.vocab)
        try:
            self._skill_extractor = SkillExtractor(
                nlp=self._nlp, 
                skills_db=self._skill_db, 
                phraseMatcher=self._phrase_matcher
            )
            logger.info("✅ SkillExtractor de skillNer inicializado correctamente.")
        except Exception as e:
            logger.error(f"❌ Error inicializando SkillExtractor: {e}", exc_info=True)
            self._skill_extractor = None
        self._prepare_spacy_patterns()
        self._ner_pipeline = None

    def _prepare_spacy_patterns(self):
        for category, terms in self._common_terms.items():
            for term in terms:
                if " " not in term:
                    self._matcher.add(category, [[{"LOWER": term}]])
                else:
                    pattern = [{"LOWER": w} for w in term.split()]
                    self._matcher.add(category, [pattern])

    @property
    def ner_pipeline(self):
        if self._ner_pipeline is None:
            try:
                from transformers import pipeline
                self._ner_pipeline = pipeline("ner", model="Babelscape/wikineural-multilingual-ner")
                logger.info("✅ Pipeline NER de transformers inicializado.")
            except Exception as e:
                logger.error(f"❌ Error inicializando pipeline NER: {e}")
                return None
        return self._ner_pipeline

    @classmethod
    def get_instance(cls, language: str = "es"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(language)
        return cls._instance

    @classmethod
    def get(cls, language: str = "es"):
        return cls.get_instance(language)

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        if not self._skill_extractor or not self._nlp:
            logger.warning("⚠️ SkillExtractor o modelo NLP no inicializados correctamente.")
            return {"skills": []}
        try:
            text = text.strip()
            skills = set()
            cache_key = f"{self.language}:{text}"
            if cache_key in self.skill_cache:
                return {"skills": self.skill_cache[cache_key]}
            skills.update(self._extract_with_skillner(text))
            skills.update(self._extract_with_spacy_matcher(text))
            skills.update(self._extract_with_ngrams(text))
            if len(skills) < 2 and self.ner_pipeline:
                skills.update(self._extract_with_transformers(text))
            skills.update(self._extract_with_heuristics(text))
            result = list(skills)
            self.skill_cache[cache_key] = result
            logger.info(f"📊 Total de habilidades extraídas: {result}")
            return {"skills": result}

        except Exception as e:
            logger.error(f"❌ Error extrayendo habilidades: {e}", exc_info=True)
            return {"skills": []}
        
    def _extract_with_skillner(self, text: str) -> Set[str]:
        """Extrae habilidades usando skillNer."""
        skills = set()
        
        if not self._skill_extractor:
            return skills
            
        try:
            # Procesamos el documento con spaCy
            doc = self._nlp(text)
            
            # Aplicamos skillNer
            annotations = self._skill_extractor.annotate(doc)
            
            # Procesamos las anotaciones según su formato
            if isinstance(annotations, dict):
                # Si tenemos resultados directos
                if "results" in annotations:
                    results = annotations["results"]
                    for match_type in ["full_matches", "ngram_scored"]:
                        if match_type in results:
                            match_data = results[match_type]
                            # Si es un diccionario indexado (antigua versión)
                            if isinstance(match_data, dict):
                                for skill_info in match_data.values():
                                    if isinstance(skill_info, dict) and "doc_node_value" in skill_info:
                                        skill_name = skill_info["doc_node_value"].strip().lower()
                                        if skill_name:
                                            skills.add(skill_name)
                            # Si es una lista (nueva versión)
                            elif isinstance(match_data, list):
                                for skill_info in match_data:
                                    if isinstance(skill_info, dict) and "doc_node_value" in skill_info:
                                        skill_name = skill_info["doc_node_value"].strip().lower()
                                        if skill_name:
                                            skills.add(skill_name)
            
            logger.info(f"🔍 skillNer encontró: {skills}")
        except Exception as e:
            logger.error(f"❌ Error en _extract_with_skillner: {e}", exc_info=True)
        
        return skills

    def _extract_with_spacy_matcher(self, text: str) -> Set[str]:
        """Extrae habilidades usando patrones personalizados con Matcher de spaCy."""
        skills = set()
        
        if not self._nlp or not self._matcher:
            return skills
        
        try:
            doc = self._nlp(text)
            matches = self._matcher(doc)
            
            for match_id, start, end in matches:
                # Obtener el nombre de la categoría (programación, framework, etc.)
                category = self._nlp.vocab.strings[match_id]
                # Obtener el texto coincidente
                span = doc[start:end]
                skill_name = span.text.lower()
                skills.add(skill_name)
            
            logger.info(f"🔍 spaCy Matcher encontró: {skills}")
        except Exception as e:
            logger.error(f"❌ Error en _extract_with_spacy_matcher: {e}")
        
        return skills

    def _extract_with_ngrams(self, text: str) -> Set[str]:
        """Detecta posibles habilidades utilizando análisis de n-gramas."""
        skills = set()
        
        try:
            # Normalizar texto
            text_lower = text.lower()
            text_normalized = unidecode.unidecode(text_lower)
            
            # Tokenizar y generar n-gramas (1, 2 y 3 palabras)
            tokens = word_tokenize(text_normalized)
            candidates = []
            
            # Unigrams
            candidates.extend(tokens)
            
            # Bigrams
            if len(tokens) >= 2:
                bigrams_list = list(ngrams(tokens, 2))
                bigrams_text = [' '.join(bg) for bg in bigrams_list]
                candidates.extend(bigrams_text)
            
            # Trigrams
            if len(tokens) >= 3:
                trigrams_list = list(ngrams(tokens, 3))
                trigrams_text = [' '.join(tg) for tg in trigrams_list]
                candidates.extend(trigrams_text)
            
            # Verificar candidatos contra bases de habilidades
            for candidate in candidates:
                # 1. Verificar en el skill_db
                if candidate in self._skill_db:
                    skills.add(candidate)
                    continue
                    
                # 2. Verificar en términos comunes
                for category, terms in self._common_terms.items():
                    if candidate in terms:
                        skills.add(candidate)
                        break
            
            logger.info(f"🔍 Análisis de n-gramas encontró: {skills}")
        except Exception as e:
            logger.error(f"❌ Error en _extract_with_ngrams: {e}")
        
        return skills

    def _extract_with_transformers(self, text: str) -> Set[str]:
        """Extrae posibles habilidades usando un modelo de NER basado en transformers."""
        skills = set()
        
        if not self.ner_pipeline:
            return skills
        
        try:
            # Obtener entidades reconocidas
            ner_results = self.ner_pipeline(text)
            
            # Filtrar por categorías relevantes (ORG, TECH, PRODUCT)
            potential_skills = []
            for item in ner_results:
                if item['entity'] in ['B-ORG', 'I-ORG', 'B-PRODUCT', 'I-PRODUCT']:
                    potential_skills.append(item['word'].lower().replace('##', ''))
            
            # Reconstruir palabras fragmentadas por tokenización
            i = 0
            current_skill = ""
            while i < len(potential_skills):
                if potential_skills[i].startswith('##'):
                    current_skill += potential_skills[i].replace('##', '')
                else:
                    if current_skill:
                        skills.add(current_skill)
                    current_skill = potential_skills[i]
                i += 1
            
            if current_skill:
                skills.add(current_skill)
            
            # Verificar contra diccionarios para evitar falsos positivos
            filtered_skills = set()
            for skill in skills:
                # Verificar en el skill_db o en términos comunes
                if skill in self._skill_db:
                    filtered_skills.add(skill)
                    continue
                
                for terms in self._common_terms.values():
                    if skill in terms:
                        filtered_skills.add(skill)
                        break
            
            logger.info(f"🔍 NER con transformers encontró: {filtered_skills}")
            return filtered_skills
        except Exception as e:
            logger.error(f"❌ Error en _extract_with_transformers: {e}")
        
        return skills

    def _extract_with_heuristics(self, text: str) -> Set[str]:
        """Aplica reglas heurísticas específicas para encontrar habilidades."""
        skills = set()
        
        try:
            text_lower = text.lower()
            text_normalized = unidecode.unidecode(text_lower)
            
            # Patrones para habilidades técnicas específicas
            tech_patterns = {
                r'\b(?:program|code|develop)\s+(?:in|with)?\s+([a-z\+\#]+)': 'programming_languages',
                r'\bexperien(?:ce|cia)\s+(?:with|en|con)?\s+([a-z\+\#\.]+)': 'general',
                r'\bconoc(?:er|imiento)\s+(?:de|en)?\s+([a-z\+\#\.]+)': 'general',
                r'\b(?:expert|experiencia|conocimientos)\s+(?:in|on|en|de)?\s+([a-z\+\#\.]+)': 'general',
                r'\bhabil(?:idad|idades)\s+(?:en|con|de)?\s+([a-z\+\#\.]+)': 'general',
                r'\b(?:using|utilizando|con)\s+([a-z\+\#\.]+)': 'tools',
                r'\b(?:database|bd|bbdd|base de datos)\s+([a-z\+\#\.]+)': 'databases',
                r'\b(?:framework|librería|biblioteca|library)\s+([a-z\+\#\.]+)': 'frameworks'
            }
            
            # Buscar coincidencias con los patrones
            for pattern, category in tech_patterns.items():
                matches = re.finditer(pattern, text_normalized)
                for match in matches:
                    potential_skill = match.group(1).strip()
                    
                    # Verificar si es una habilidad válida (en diccionarios o términos comunes)
                    if potential_skill in self._skill_db:
                        skills.add(potential_skill)
                        continue
                    
                    # Verificar en términos comunes por categoría
                    if category in self._common_terms and potential_skill in self._common_terms[category]:
                        skills.add(potential_skill)
                    elif category == 'general':
                        # Para la categoría general, buscar en todas las categorías
                        for terms in self._common_terms.values():
                            if potential_skill in terms:
                                skills.add(potential_skill)
                                break
            
            # Detectar versiones de lenguajes (Python 3.9, Java 11, etc.)
            version_pattern = r'\b(python|java|php|javascript|typescript|c\+\+|c\#)\s+(\d+(?:\.\d+)?)+'
            for match in re.finditer(version_pattern, text_normalized):
                lang = match.group(1)
                version = match.group(2)
                skills.add(f"{lang} {version}")
                skills.add(lang)  # También agregar el lenguaje sin versión
            
            # Buscar acrónimos conocidos (NLP, ML, AI, etc.)
            acronyms = {
                "nlp": "natural language processing",
                "ml": "machine learning",
                "ai": "artificial intelligence",
                "dl": "deep learning",
                "cv": "computer vision",
                "api": "api development",
                "oop": "object oriented programming",
                "ci/cd": "continuous integration",
                "aws": "amazon web services",
                "gcp": "google cloud platform",
                "ui/ux": "user interface design"
            }
            
            # Buscar acrónimos en el texto
            for acronym, full_term in acronyms.items():
                pattern = r'\b' + re.escape(acronym) + r'\b'
                if re.search(pattern, text_lower):
                    skills.add(acronym)
                    skills.add(full_term)
            
            logger.info(f"🔍 Análisis heurístico encontró: {skills}")
        except Exception as e:
            logger.error(f"❌ Error en _extract_with_heuristics: {e}")
        
        return skills

    def fallback_skill_detection(self, text: str) -> Set[str]:
        """
        Método fallback mejorado para cuando otros métodos fallan o no devuelven resultados.
        Utiliza las mismas categorías cargadas en común para mantener coherencia.
        """
        skills = set()
        
        # Usar los términos ya cargados
        fallback_lists = self._common_terms
        
        # Buscar coincidencias en el texto
        text_lower = text.lower()
        for category, terms in fallback_lists.items():
            for term in terms:
                if term in text_lower:
                    skills.add(term)
        
        # Buscar versiones específicas
        version_pattern = r'\b(python|java|javascript|react)\s+(\d+(?:\.\d+)?)\b'
        for match in re.finditer(version_pattern, text_lower):
            skills.add(f"{match.group(1)} {match.group(2)}")
        
        logger.info(f"📌 Fallback encontró: {skills}")
        return skills
    
    def __del__(self):
        if hasattr(self, 'skill_cache'):
            self.skill_cache.close()
# ✅ Lazy Load NLPProcessor
class NLPProcessor:
    def __init__(self, language: str = "es"):
        self.language = language
        self._nlp = None
        self._matcher = None
        self._gpt_handler = None
        self._sentiment_analyzer = None
        self.gpt_cache = TTLCache(maxsize=1000, ttl=3600)

    @property
    def nlp(self):
        if self._nlp is None:
            self._nlp = load_nlp_model(self.language)
        return self._nlp

    @property
    def matcher(self):
        if self._matcher is None:
            self._matcher = Matcher(self.nlp.vocab)
        return self._matcher

    @property
    def sentiment_analyzer(self):
        if self._sentiment_analyzer is None:
            self._sentiment_analyzer = RoBertASentimentAnalyzer()
        return self._sentiment_analyzer

    async def initialize_gpt_handler(self):
        if self._gpt_handler is None:
            self._gpt_handler = await get_gpt_client()

    def set_language(self, language: str):
        self.language = language
        self.nlp = load_nlp_model(language)
        self.matcher = Matcher(self.nlp.vocab) if self.nlp else None
        logger.info(f"🔄 Modelo NLP cambiado a: {language}")

    def define_intent_patterns(self) -> None:
        pass  # Ejemplo sin cambios

    async def analyze(self, text: str) -> dict:
        if not self.nlp:
            logger.error("No se ha cargado el modelo spaCy, devolviendo análisis vacío.")
            return {"intents": [], "entities": [], "sentiment": "neutral", "detected_divisions": []}
        from app.chatbot.utils import clean_text
        cleaned_text = clean_text(text)
        doc = await asyncio.to_thread(self.nlp, cleaned_text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        matches = await asyncio.to_thread(self.matcher, doc)
        intents = [self.nlp.vocab.strings[m[0]] for m in matches]
        sentiment = await asyncio.to_thread(self.sentiment_analyzer.analyze_sentiment, cleaned_text)
        # ...
        return {
            "entities": entities,
            "intents": intents,
            "sentiment": sentiment,
            "detected_divisions": []
        }

    @cachedmethod(lambda self: self.gpt_cache)
    async def extract_skills(self, text: str, business_unit: str = "huntRED®") -> dict:
        extractor = SkillExtractorManager.get_instance(self.language)
        if not extractor:
            logger.warning("⚠️ SkillExtractor no está inicializado")
            return {"skills": []}
        try:
            from app.chatbot.utils import clean_text
            cleaned_text = clean_text(text)
            skills_result = extractor.extract_skills(cleaned_text)
            logger.info(f"📊 Habilidades extraídas: {skills_result['skills']}")
            return skills_result
        except Exception as e:
            logger.error(f"❌ Error extrayendo habilidades: {e}", exc_info=True)
            return {"skills": []}

    def extract_interests_and_skills(self, text: str) -> dict:
        text_normalized = unidecode.unidecode(text.lower())
        skills = set()
        priorities = {}
        all_skills = get_all_skills_for_unit()

        for skill in all_skills:
            skill_normalized = unidecode.unidecode(skill.lower())
            if re.search(r'\b' + re.escape(skill_normalized) + r'\b', text_normalized):
                skills.add(skill)
                priorities[skill] = 2

        if self._nlp:
            doc = self.nlp(text)
            # ...
        prioritized_interests = prioritize_interests(list(skills))
        return {"skills": list(skills), "prioritized_skills": prioritized_interests}

    def infer_gender(self, name: str) -> str:
        GENDER_DICT = {"jose": "M", "maria": "F", "andrea": "F", "juan": "M"}
        parts = name.lower().split()
        m_count = sum(1 for p in parts if p in GENDER_DICT and GENDER_DICT[p] == "M")
        f_count = sum(1 for p in parts if p in GENDER_DICT and GENDER_DICT[p] == "F")
        return "M" if m_count > f_count else "F" if f_count > m_count else "O"

    def extract_skills_and_roles(self, text: str, business_unit: str = "huntRED®") -> dict:
        text_normalized = unidecode.unidecode(text.lower())
        skills = set()
        priorities = {}
        try:
            all_skills = get_all_skills_for_unit(business_unit)
        except Exception as e:
            logger.error(f"Error obteniendo habilidades para {business_unit}: {e}")
            all_skills = []

        for skill in all_skills:
            skill_normalized = unidecode.unidecode(skill.lower())
            if re.search(r'\b' + re.escape(skill_normalized) + r'\b', text_normalized):
                skills.add(skill)
                priorities[skill] = 2

        extractor = SkillExtractorManager.get_instance(self.language)
        if extractor:
            try:
                skill_results = extractor.extract_skills(text)
                extracted_skills = set(skill_results.get("skills", []))
                skills.update(extracted_skills)
                for skill in extracted_skills:
                    priorities[skill] = priorities.get(skill, 1)
                logger.info(f"🧠 Habilidades extraídas por SkillExtractorManager: {extracted_skills}")
            except Exception as e:
                logger.error(f"❌ Error en SkillExtractorManager: {e}", exc_info=True)

        skills_list = list(skills)
        weighted_skills = prioritize_interests(skills_list) if skills_list else {}
        suggested_roles = get_positions_by_skills(skills, weighted_skills) if skills else []
        return {
            "skills": skills_list,
            "suggested_roles": suggested_roles
        }

# ============== GPT CLIENT POOL / Tabiya y Robert  ==============
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
nlp_processor = NLPProcessor(language="es")

# ============== EJEMPLO MAIN ==============
if __name__ == "__main__":
    # 1) (Opcional) Parse RDF local de ESCO
    parse_esco_rdf_to_json("esco.ttl", "esco_from_rdf.json")
    
    # 2) Extraer data desde las CLASES DE EXTRACTORS (APIs, XLS, CSV, etc.)
    # Ejemplo: instanciamos cada una según necesitemos
    esco_ext = ESCOExtractor()
    onet_ext = ONETExtractor()
    nice_ext = NICEExtractor()
    career_ext = CareerOneStopExtractor()

    # Recogemos datos de ESCO (API) en español
    esco_skills_data = esco_ext.get_skills(language="es", limit=5)
    esco_occ_data = esco_ext.get_occupations(language="es", limit=5)

    # O from NICE XLSX
    nice_data = nice_ext.get_skills(sheet_name="Skills")
    
    # ... y así con O*NET o CareerOneStop
    onet_data = onet_ext.get_occupations(api_key="...", count=5)
    career_data = career_ext.get_careers(api_user_id="...", api_key="...", keyword="cybersecurity", limit=5)

    # 3) Unificamos los datos en un solo formato (unify_data)
    #    Por ahora, ejemplo con ESCO + NICE
    unified = unify_data(esco_skills_data, esco_occ_data, nice_data)
    logger.info(f"Datos unificados: {len(unified)}")

    # 4) (Opcional) Guardar estos datos en un .json (similar a "esco_skills.json"), 
    #    o prepara un "merger" para combinarlos con otras fuentes
    #    -> En caso de que quieras que generen un archivo tipo "ESCO_API_skills.json", etc.

    # EJEMPLO rápido: guardamos un 'esco_api_skills.json' con lo que unificamos
    with open(os.path.join(CONFIG["OUTPUT_DIR"], "esco_api_skills.json"), "w", encoding="utf-8") as out:
        json.dump({f"gen_{i}": item for i, item in enumerate(unified)}, out, indent=2, ensure_ascii=False)

    # 5) Fusionamos con el resto de bases para tener un combined_skills.json
    merger = SkillDBMerger(CONFIG["OUTPUT_DIR"], "combined_skills.json")
    merger.merge()

    # 6) Probar pipeline básico
    pipeline = SkillExtractionPipeline(combined_db_path=CONFIG["COMBINED_DB_PATH"])
    texts = [
        "Busco un desarrollador con experiencia en Python, Django y machine learning.",
        "Me interesa contratar a alguien con habilidades en Java, React y gestión de proyectos."
    ]
    for txt in texts:
        print(f"[Pipeline Básico] {txt} -> {pipeline.extract_skills(txt)}")

    # 7) Probar extractor avanzado
    advanced_extractor = SkillExtractorManager.get_instance("es")
    for txt in texts:
        print(f"[Avanzado] {txt} -> {advanced_extractor.extract_skills(txt)['skills']}")

    # 8) Probar NLPProcessor
    nlp_proc = NLPProcessor(language="es")
    async def test_nlp():
        for txt in texts:
            res = await nlp_proc.extract_skills(txt)
            print(f"[NLPProcessor] {txt} -> {res['skills']}")
    asyncio.run(test_nlp())