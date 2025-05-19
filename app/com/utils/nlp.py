# /home/pablo/app/com/utils/nlp.py
import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Optional, Any, Union
import logging
import time
import functools
from django.core.cache import cache
import re
from datetime import datetime

from app.models import Person, Vacante, BusinessUnit
from app.com.utils.skills import create_skill_processor
from app.com.utils.skills.base import Skill, Competency

logger = logging.getLogger(__name__)

# Intenta importar psutil para monitoreo de recursos (opcional)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    
# Caché global para modelos de spaCy para evitar carga repetida
SPACY_MODELS = {}

# Caché para embeddings y análisis
EMBEDDING_CACHE_TTL = 3600  # 1 hora
ANALYSIS_CACHE_TTL = 300    # 5 minutos

class NLPProcessor:
    """Procesador de lenguaje natural para análisis de texto."""
    
    def __init__(self, business_unit: BusinessUnit, language: str = "es", mode: str = "opportunity", analysis_depth: str = "deep"):
        """
        Inicializa el procesador de NLP híbrido (Spacy + Tabiya + SkillClassifier).
        
        Args:
            business_unit: Unidad de negocio para el análisis
            language: Idioma para el procesamiento ("es" o "en")
            mode: Modo de procesamiento ("opportunity" o "candidate")
            analysis_depth: Profundidad del análisis ("quick" o "deep")
        """
        self.business_unit = business_unit
        self.language = language
        self.mode = mode
        self.analysis_depth = analysis_depth
        
        # Validar parámetros
        if mode not in ["opportunity", "candidate"]:
            raise ValueError(f"Modo no válido: {mode}. Debe ser 'opportunity' o 'candidate'")
        if analysis_depth not in ["quick", "deep"]:
            raise ValueError(f"Profundidad no válida: {analysis_depth}. Debe ser 'quick' o 'deep'")
            
        # Inicializar procesadores
        self.spacy_model = self._load_spacy_model()
        self.skill_processor = create_skill_processor(
            business_unit.name,
            language=language,
            mode='executive' if business_unit.name == 'huntRED Executive' else 'technical'
        )
        
        # Inicializar vectorizador TF-IDF
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english' if language == 'en' else 'spanish'
        )
        
        # Inicializar modelos adicionales según el modo
        self._initialize_models()
        
    def _initialize_models(self):
        """Inicializa modelos adicionales para análisis profundo."""
        if self.mode == "opportunity":
            # Modelos específicos para análisis de ofertas
            self.job_classifier = JobClassifier()
            self.salary_estimator = SalaryEstimator()
            self.requirement_extractor = RequirementExtractor()
            self.benefit_extractor = BenefitExtractor()
            self.location_analyzer = LocationAnalyzer()
            self.remote_analyzer = RemoteWorkAnalyzer()
            self.contract_type_analyzer = ContractTypeAnalyzer()
        else:  # candidate
            # Modelos específicos para análisis de candidatos
            self.education_extractor = EducationExtractor()
            self.experience_analyzer = ExperienceAnalyzer()
            self.skill_matcher = SkillMatcher()
            self.cultural_fit_analyzer = CulturalFitAnalyzer()
            self.language_analyzer = LanguageAnalyzer()
            self.availability_analyzer = AvailabilityAnalyzer()
            self.relocation_analyzer = RelocationAnalyzer()
            
    def _load_spacy_model(self):
        """Carga el modelo de Spacy según el idioma y profundidad."""
        # Seleccionar modelo según profundidad
        if self.analysis_depth == "quick":
            model_name = "es_core_news_sm" if self.language == "es" else "en_core_web_sm"
        else:
            model_name = "es_core_news_md" if self.language == "es" else "en_core_web_md"
            
        # Verificar si ya está en caché global
        if model_name in SPACY_MODELS:
            logger.debug(f"Usando modelo {model_name} desde caché global")
            return SPACY_MODELS[model_name]
        
        # Monitorear recursos disponibles
        should_use_light_model = False
        if PSUTIL_AVAILABLE:
            mem = psutil.virtual_memory()
            if mem.available < 500 * 1024 * 1024:  # Menos de 500MB disponibles
                should_use_light_model = True
                logger.warning(f"Memoria baja ({mem.available/1024/1024:.1f}MB), usando modelo ligero")
                model_name = model_name.replace("_md", "_sm")
        
        # Cargar modelo con componentes selectivos
        disabled_components = ["ner"] if self.analysis_depth == "quick" else []
        model = spacy.load(model_name, disable=disabled_components)
        
        # Guardar en caché global
        SPACY_MODELS[model_name] = model
        logger.info(f"Modelo {model_name} cargado y almacenado en caché global")
        
        return model
        
    async def analyze(self, text: str) -> Dict:
        """
        Analiza un texto usando el procesador más apropiado según la profundidad y modo.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Dict con el análisis realizado
        """
        if not text or len(text.strip()) == 0:
            return self._get_empty_result()
            
        # Verificar caché
        cache_key = f"nlp:analysis:{self.business_unit.id}:{self.mode}:{self.analysis_depth}:{hash(text[:200])}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.debug(f"Resultado obtenido de caché para BU '{self.business_unit.name}'")
            cached_result["cached"] = True
            return cached_result
            
        # Medir tiempo de ejecución
        start_time = time.time()
        
        try:
            # Análisis base común para ambos modos
            base_analysis = await self._analyze_base(text)
            
            # Análisis específico según el modo
            if self.mode == "opportunity":
                specific_analysis = await self._analyze_opportunity(text)
            else:
                specific_analysis = await self._analyze_candidate(text)
                
            # Combinar resultados
            result = {**base_analysis, **specific_analysis}
            
            # Añadir metadatos
            result.update({
                "mode": self.mode,
                "analysis_depth": self.analysis_depth,
                "business_unit": self.business_unit.name,
                "execution_time": time.time() - start_time,
                "cached": False
            })
            
            # Guardar en caché
            cache.set(cache_key, result, ANALYSIS_CACHE_TTL)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis NLP: {str(e)}")
            return self._get_error_result(str(e), time.time() - start_time)
            
    def _get_empty_result(self) -> Dict:
        """Retorna un resultado vacío con la estructura correcta."""
        return {
            "entities": [],
            "sentiment": {},
            "keywords": [],
            "skills": [],
            "mode": self.mode,
            "analysis_depth": self.analysis_depth,
            "business_unit": self.business_unit.name,
            "cached": False
        }
        
    def _get_error_result(self, error: str, execution_time: float) -> Dict:
        """Retorna un resultado de error con la estructura correcta."""
        return {
            "entities": [],
            "sentiment": {},
            "keywords": [],
            "skills": [],
            "mode": self.mode,
            "analysis_depth": self.analysis_depth,
            "business_unit": self.business_unit.name,
            "execution_time": execution_time,
            "error": error,
            "cached": False
        }
        
    async def _analyze_base(self, text: str) -> Dict:
        """Realiza el análisis base común para todos los modos."""
        doc = self.spacy_model(text)
        
        return {
            "entities": self._extract_entities(doc),
            "sentiment": self._analyze_sentiment(doc),
            "keywords": self._extract_keywords(doc),
            "skills": self._extract_skills(doc)
        }
        
    async def _analyze_opportunity(self, text: str) -> Dict:
        """Realiza el análisis específico para ofertas de trabajo."""
        return {
            "requirements": await self.requirement_extractor.extract(text),
            "benefits": await self.benefit_extractor.extract(text),
            "salary_range": await self.salary_estimator.estimate(text),
            "job_category": await self.job_classifier.classify(text),
            "location": await self.location_analyzer.analyze(text),
            "remote_work": await self.remote_analyzer.analyze(text),
            "contract_type": await self.contract_type_analyzer.analyze(text)
        }
        
    async def _analyze_candidate(self, text: str) -> Dict:
        """Realiza el análisis específico para perfiles de candidatos."""
        return {
            "education": await self.education_extractor.extract(text),
            "experience": await self.experience_analyzer.analyze(text),
            "skill_match": await self.skill_matcher.match(text),
            "cultural_fit": await self.cultural_fit_analyzer.analyze(text),
            "languages": await self.language_analyzer.analyze(text),
            "availability": await self.availability_analyzer.analyze(text),
            "relocation": await self.relocation_analyzer.analyze(text)
        }
        
    def _extract_entities(self, doc) -> List[Dict]:
        """Extrae entidades nombradas del documento."""
        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "confidence": 0.9  # Simulación de confianza
            })
        return entities
        
    def _analyze_sentiment(self, doc) -> Dict:
        """Analiza el sentimiento del texto."""
        # Implementación básica de sentimiento
        positive_words = ["excelente", "bueno", "satisfactorio", "positivo"]
        negative_words = ["pobre", "malo", "insatisfactorio", "negativo"]
        
        words = [token.text.lower() for token in doc]
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        return {
            "score": (positive_count - negative_count) / len(words) if words else 0,
            "magnitude": abs(positive_count - negative_count)
        }
        
    def _extract_keywords(self, doc) -> List[str]:
        """Extrae palabras clave usando TF-IDF."""
        try:
            text = doc.text
            tfidf_matrix = self.vectorizer.fit_transform([text])
            feature_names = self.vectorizer.get_feature_names_out()
            
            keywords = []
            for i in tfidf_matrix.nonzero()[0]:
                keywords.append(feature_names[i])
            
            return keywords[:5]  # Top 5 keywords
            
        except Exception as e:
            logger.error(f"Error extrayendo keywords: {str(e)}")
            return []
            
    def _extract_skills(self, doc) -> List[Dict]:
        """Extrae habilidades del documento."""
        try:
            skills = []
            for token in doc:
                if token.pos_ == "NOUN" and token.text.lower() in [
                    "python", "java", "sql", "javascript", "react", "angular",
                    "vue", "node", "django", "flask", "fastapi", "spring",
                    "hibernate", "docker", "kubernetes", "jenkins", "gitlab"
                ]:
                    skills.append({
                        "name": token.text,
                        "confidence": 0.8,
                        "category": "technical"
                    })
            return skills
            
        except Exception as e:
            logger.error(f"Error extrayendo skills: {str(e)}")
            return []
            
    async def compare_texts(self, text1: str, text2: str) -> float:
        """
        Compara dos textos usando similitud del coseno.
        
        Args:
            text1: Primer texto
            text2: Segundo texto
            
        Returns:
            float: Puntaje de similitud (0-1)
        """
        if not text1 or not text2:
            return 0.0
            
        # Verificar caché
        cache_key = f"nlp:similarity:{self.business_unit.id}:{hash(text1[:100])}:{hash(text2[:100])}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
            
        try:
            # Usar versiones truncadas si son muy largas para ahorrar memoria
            if len(text1) > 5000 or len(text2) > 5000:
                text1 = text1[:5000]
                text2 = text2[:5000]
                logger.debug("Textos truncados para comparación (>5000 caracteres)")
                
            # Procesar textos
            doc1 = self.spacy_model(text1)
            doc2 = self.spacy_model(text2)
            
            # Calcular similitud
            similarity = doc1.similarity(doc2)
            
            # Guardar en caché
            cache.set(cache_key, similarity, EMBEDDING_CACHE_TTL)
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error en comparación de textos: {str(e)}")
            return 0.0

def create_nlp_processor(business_unit: BusinessUnit, **kwargs) -> NLPProcessor:
    """Factory para crear procesadores NLP."""
    return NLPProcessor(business_unit, **kwargs)
