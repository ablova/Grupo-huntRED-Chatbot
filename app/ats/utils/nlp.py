# /home/pablo/app/com/utils/nlp.py
import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Optional, Any, Union, Tuple
import logging
import time
import functools
from django.core.cache import cache
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import asyncio
from cachetools import TTLCache

from app.models import Person, Vacante, BusinessUnit
from app.ats.utils.skills_utils import create_skill_processor
from app.ats.utils.skills.base.base_models import Skill, Competency

logger = logging.getLogger(__name__)

# Configuración de modelos
MODEL_CONFIG = {
    'es': {
        'quick': 'es_core_news_sm',
        'deep': 'es_core_news_md'
    },
    'en': {
        'quick': 'en_core_web_sm',
        'deep': 'en_core_web_md'
    }
}

# Configuración de caché
CACHE_SIZE = 1000
CACHE_TTL = 3600  # 1 hora
EMBEDDING_CACHE_TTL = 3600  # 1 hora
ANALYSIS_CACHE_TTL = 300    # 5 minutos

# Caché global para modelos de spaCy
SPACY_MODELS = {}

# Intenta importar psutil para monitoreo de recursos
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class NLPProcessor:
    """
    Procesador de lenguaje natural mejorado con soporte para múltiples modos y profundidades.
    
    Características principales:
    - Procesamiento rápido con spaCy para modo 'quick'
    - Análisis profundo con transformers para modo 'deep'
    - Caché de resultados para mejor rendimiento
    - Soporte multilingüe (es, en)
    - Procesamiento en paralelo para mejor rendimiento
    """
    
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
        self.cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)
        
        # Ajustar número de trabajadores según CPU disponible
        import os
        self.max_workers = min(os.cpu_count() or 4, 8)  # Máximo 8 workers
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        
        self._nlp = None
        self._sentiment_analyzer = None
        self._skill_patterns = None
        
    async def initialize(self):
        """Inicializa los recursos del procesador de forma asíncrona."""
        await self._load_models()
        await self._initialize_skill_patterns()
        
    async def _load_models(self):
        """Carga los modelos necesarios de forma asíncrona."""
        # Cargar modelo spaCy en segundo plano
        await asyncio.get_event_loop().run_in_executor(
            self.thread_pool,
            self._get_nlp
        )
        
        # Cargar otros modelos según sea necesario
        if self.analysis_depth == 'deep':
            await self._load_deep_models()
            
    def _get_nlp(self):
        """Obtiene el modelo spaCy, cargándolo si es necesario."""
        if self._nlp is None:
            model_key = f"{self.language}_{self.analysis_depth}"
            if model_key not in SPACY_MODELS:
                SPACY_MODELS[model_key] = spacy.load(MODEL_CONFIG[self.language][self.analysis_depth])
            self._nlp = SPACY_MODELS[model_key]
            
            # Agregar reglas para habilidades si no existen
            if 'skill_ruler' not in self._nlp.pipe_names:
                ruler = self._nlp.add_pipe("entity_ruler", before="ner")
                patterns = self._get_skill_patterns()
                ruler.add_patterns(patterns)
                
        return self._nlp
        
    def _get_skill_patterns(self) -> List[Dict]:
        """Obtiene patrones para reconocimiento de habilidades."""
        if self._skill_patterns is None:
            # Patrones básicos de habilidades técnicas
            self._skill_patterns = [
                {"label": "SKILL", "pattern": [{"LOWER": skill}]}
                for skill in [
                    "python", "java", "javascript", "typescript", "react", "angular",
                    "vue", "node", "django", "flask", "fastapi", "spring", "aws",
                    "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
                    "jenkins", "git", "sql", "nosql", "mongodb", "postgresql",
                    "mysql", "redis", "elasticsearch", "kafka", "rabbitmq"
                ]
            ]
            
            # Agregar patrones de habilidades específicas de la unidad de negocio
            if hasattr(self.business_unit, 'required_skills'):
                business_skills = self.business_unit.required_skills
                if isinstance(business_skills, list):
                    self._skill_patterns.extend([
                        {"label": "SKILL", "pattern": [{"LOWER": skill.lower()}]}
                        for skill in business_skills
                    ])
                    
        return self._skill_patterns
        
    async def _load_deep_models(self):
        """Carga modelos más pesados para análisis profundo."""
        if self.analysis_depth == 'deep':
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                
                logger.info("Cargando modelos profundos")
                
                # Usar modelo multilingüe para ambos idiomas
                model_name = 'xlm-roberta-base'
                
                # Cargar tokenizador y modelo
                self._tokenizer = AutoTokenizer.from_pretrained(model_name)
                self._model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    num_labels=3  # NEG, NEU, POS
                )
                
                # Inicializar pipeline para análisis de sentimiento
                self._sentiment_analyzer = {
                    'model': self._model,
                    'tokenizer': self._tokenizer
                }
                
                logger.info("Modelos profundos cargados exitosamente")
                
            except ImportError as e:
                logger.warning(f"No se pudieron cargar los modelos de transformadores: {str(e)}")
                self.analysis_depth = 'quick'
                
    async def _get_cache_key(self, prefix: str, *args) -> str:
        """Genera una clave de caché robusta."""
        timestamp = int(time.time() / 60)  # Redondear a minutos
        key_parts = [prefix, self.language, self.mode, self.analysis_depth, timestamp] + list(args)
        return '|'.join(str(part) for part in key_parts)
        
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analiza el sentimiento del texto con soporte para caché."""
        cache_key = await self._get_cache_key('sentiment', text)
        
        # Verificar caché
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        start_time = time.time()
        
        try:
            # Usar el modelo apropiado según la profundidad
            if self.analysis_depth == "deep" and self._sentiment_analyzer:
                result = await self._analyze_sentiment_deep(text)
            else:
                result = await self._analyze_sentiment_quick(text)
                
            # Agregar métricas
            result['execution_time'] = time.time() - start_time
            
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                result['resource_usage'] = {
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'cpu_percent': process.cpu_percent(interval=0.1)
                }
            
            # Almacenar en caché
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {str(e)}")
            return await self._analyze_sentiment_quick(text)
            
    async def _analyze_sentiment_deep(self, text: str) -> Dict[str, Any]:
        """Análisis de sentimiento profundo con modelo multilingüe."""
        try:
            # Tokenizar y truncar si es necesario
            inputs = self._sentiment_analyzer['tokenizer'](
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            
            # Obtener predicción
            outputs = self._sentiment_analyzer['model'](**inputs)
            scores = outputs.logits.softmax(dim=1)[0]
            
            # Obtener etiquetas del modelo
            labels = self._sentiment_analyzer['model'].config.id2label
            max_idx = scores.argmax().item()
            
            return {
                'sentiment': labels[max_idx].lower(),
                'score': float(scores[max_idx]),
                'scores': {labels[i]: float(scores[i]) for i in range(len(labels))}
            }
            
        except Exception as e:
            logger.error(f"Error en análisis profundo: {str(e)}")
            return await self._analyze_sentiment_quick(text)
            
    async def _analyze_sentiment_quick(self, text: str) -> Dict[str, Any]:
        """Análisis de sentimiento rápido con spaCy."""
        try:
            # Usar pysentimiento para español si está disponible
            if self.language == 'es':
                try:
                    from pysentimiento import create_analyzer
                    analyzer = create_analyzer(task="sentiment", lang="es")
                    result = analyzer.predict(text)
                    return {
                        'sentiment': result.output.lower(),
                        'score': result.probas[result.output]
                    }
                except ImportError:
                    pass
            
            # Fallback a análisis básico con spaCy
            doc = self._nlp(text)
            
            # Palabras clave para sentimiento
            positive_words = set(['excelente', 'bueno', 'satisfactorio', 'positivo', 'experto', 'experiencia'])
            negative_words = set(['pobre', 'malo', 'insatisfactorio', 'negativo', 'básico', 'limitado'])
            
            # Contar ocurrencias
            positive_count = sum(1 for token in doc if token.text.lower() in positive_words)
            negative_count = sum(1 for token in doc if token.text.lower() in negative_words)
            
            # Calcular score
            total_words = len(doc)
            if total_words > 0:
                score = (positive_count - negative_count) / total_words
            else:
                score = 0
                
            # Determinar sentimiento
            if score > 0.1:
                sentiment = 'positive'
            elif score < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
                
            return {
                'sentiment': sentiment,
                'score': score
            }
            
        except Exception as e:
            logger.error(f"Error en análisis rápido: {str(e)}")
            return {'sentiment': 'neutral', 'score': 0}
        
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
        cache_key = self._get_cache_key('analysis', text)
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
        doc = self._nlp(text)
        
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
            doc1 = self._nlp(text1)
            doc2 = self._nlp(text2)
            
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
