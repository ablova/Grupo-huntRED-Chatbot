# /home/pablo/app/ml/analyzers/personality_analyzer.py
"""
Analizador de personalidad que integra datos de diversos assessments.

Este módulo proporciona funcionalidades para analizar la personalidad de los candidatos
basándose en diferentes modelos de evaluación, como el modelo de los Cinco Grandes,
ADN profesional, fit cultural y evaluación de talento.

El módulo se integra con el sistema de ML existente y utiliza caché para optimizar
el rendimiento de las evaluaciones frecuentes.
"""
import json
import logging
import hashlib
import asyncio
import time
from functools import lru_cache, wraps, partial
from typing import Dict, Any, Optional, List, Tuple, Union, TypedDict, Callable, TypeVar, cast, Type, TypeVar, Generic, Set, Iterable, Awaitable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

# Django
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Prefetch, Q
from django.conf import settings

# Local imports
from app.models import BusinessUnit, Person, Vacante, Skill  # Importaciones de modelos
from app.ml.ml_model import MatchmakingLearningSystem  # Sistema de ML

# Tipos genéricos para decoradores
F = TypeVar('F', bound=Callable[..., Any])

# Configuración de métricas (usando el patrón singleton)
class Metrics:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Metrics, cls).__new__(cls)
            cls._instance._init_metrics()
        return cls._instance
    
    def _init_metrics(self):
        # En un entorno real, aquí inicializaríamos las métricas con Prometheus o similar
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.error_count = 0
    
    def record_request(self):
        self.request_count += 1
    
    def record_cache_hit(self):
        self.cache_hits += 1
    
    def record_cache_miss(self):
        self.cache_misses += 1
    
    def record_error(self):
        self.error_count += 1

# Instancia global de métricas
metrics = Metrics()

# Decorador para medir tiempo de ejecución
def measure_time(func: F) -> F:
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = timezone.now()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.debug(f"{func.__name__} tomó {elapsed:.4f} segundos")
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = timezone.now()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.debug(f"{func.__name__} tomó {elapsed:.4f} segundos")
    
    return cast(F, async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper)

# Decorador para manejo de caché con tiempo de expiración
def cached(timeout: int = 300, key_prefix: str = ""):
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de caché única
            cache_key = f"{key_prefix}:{func.__module__}:{func.__name__}:{args}:{frozenset(kwargs.items())}"
            
            # Intentar obtener de caché
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                metrics.record_cache_hit()
                return cached_result
                
            metrics.record_cache_miss()
            result = func(*args, **kwargs)
            
            # Almacenar en caché
            cache.set(cache_key, result, timeout)
            return result
        return cast(F, wrapper)
    return decorator

# Modelos locales
from app.models import BusinessUnit

# Configuración de logging
logger = logging.getLogger(__name__)

# Constantes
DEFAULT_CACHE_TIMEOUT = 3600  # 1 hora en segundos
MAX_CACHE_ENTRIES = 1000  # Máximo número de entradas en caché

# Tipos personalizados
@dataclass
class AnalysisResult:
    """Estructura de datos para los resultados del análisis."""
    traits: Dict[str, float] = field(default_factory=dict)
    dimensions: Dict[str, float] = field(default_factory=dict)
    insights: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: timezone.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a diccionario."""
        return asdict(self)

@dataclass
class AssessmentData:
    """Estructura de datos para la entrada de evaluación."""
    assessment_type: str
    responses: Dict[str, Union[str, int, float]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: timezone.now().isoformat())
    candidate_id: Optional[str] = None
    session_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AssessmentData':
        """Crea una instancia a partir de un diccionario."""
        return cls(**data)

class PersonalityAnalyzer:
    """
    Analizador de personalidad que integra datos de diversos assessments.
    
    Esta clase proporciona métodos para analizar la personalidad de los candidatos
    utilizando diferentes modelos de evaluación. Soporta múltiples tipos de evaluaciones
    y utiliza caché para optimizar el rendimiento.
    
    Atributos:
        ml_system: Instancia del sistema de aprendizaje automático para análisis avanzado
        cache_timeout: Tiempo de expiración de la caché en segundos (por defecto: 1 hora)
    """
    
    # Definición de rasgos de personalidad para diferentes modelos
    PERSONALITY_TRAITS = {
        'big_five': ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'],
        'professional_dna': ['strategic_thinking', 'emotional_intelligence', 'adaptability', 
                           'collaboration', 'innovation', 'resilience', 'results_orientation'],
        'leadership': ['vision', 'influence', 'motivation', 'decision_making', 'accountability'],
        'cultural_fit': ['adaptability', 'values_alignment', 'team_orientation', 'growth_mindset', 'work_ethic']
    }
    
    # Umbrales para análisis de fortalezas y debilidades
    STRENGTH_THRESHOLD = 0.7  # 70% o superior se considera fortaleza
    IMPROVEMENT_THRESHOLD = 0.4  # 40% o inferior se considera área de mejora
    
    def __init__(self, ml_system=None, cache_timeout: int = DEFAULT_CACHE_TIMEOUT, enable_async: bool = True):
        """
        Inicializa el analizador de personalidad con un sistema de ML opcional.
        
        Args:
            ml_system: Instancia del sistema de ML para análisis avanzado (opcional)
            cache_timeout: Tiempo de expiración de la caché en segundos (opcional)
            enable_async: Habilita el procesamiento asíncrono (por defecto: True)
        """
        self.ml_system = ml_system or MatchmakingLearningSystem()
        self.cache_timeout = cache_timeout
        self.cache_prefix = "personality_analyzer_"
        self.enable_async = enable_async
        self._init_cache()
    
    def _init_cache(self) -> None:
        """Inicializa la caché si es necesario."""
        # La caché de Django se inicializa automáticamente
        pass
        
    async def analyze_batch(self, candidate_data_list: List[Dict], 
                           business_unit: Optional[BusinessUnit] = None) -> List[AnalysisResult]:
        """
        Procesa múltiples evaluaciones en paralelo.
        
        Args:
            candidate_data_list: Lista de diccionarios con datos de candidatos
            business_unit: Unidad de negocio para la personalización (opcional)
                
        Returns:
            List[AnalysisResult]: Lista de resultados de análisis
        """
        if not self.enable_async:
            return [self.analyze(data, business_unit) for data in candidate_data_list]
            
        async def process_one(data):
            try:
                return await self.analyze(data, business_unit)
            except Exception as e:
                logger.error(f"Error procesando lote: {str(e)}")
                return None
                
        tasks = [process_one(data) for data in candidate_data_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if r is not None]  # Filtrar errores
        
    def _generate_cache_key(self, data: Dict[str, Any]) -> str:
        """
        Genera una clave de caché única para los datos de entrada.
        
        Args:
            data: Datos de entrada para el análisis
                
        Returns:
            str: Clave de caché generada
        """
        # Usar solo los campos relevantes para la clave de caché
        cache_data = {
            'assessment_type': data.get('assessment_type'),
            'responses_hash': self._hash_dict(data.get('responses', {})),
            'version': 'v2'  # Incrementar si cambia la estructura de caché
        }
        
        # Convertir a JSON y luego a hash MD5 para una clave consistente
        cache_str = json.dumps(cache_data, sort_keys=True)
        return f"{self.cache_prefix}{hashlib.md5(cache_str.encode('utf-8')).hexdigest()}"
    
    @staticmethod
    def _hash_dict(data: Dict) -> str:
        """Genera un hash estable para un diccionario."""
        def serialize(obj):
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in sorted(obj.items())}
            elif isinstance(obj, (list, tuple)):
                return [serialize(x) for x in obj]
            else:
                return str(obj)
                
        serialized = json.dumps(serialize(data), sort_keys=True)
        return hashlib.md5(serialized.encode('utf-8')).hexdigest()
    
    async def _get_cached_result_async(self, cache_key: str) -> Optional[AnalysisResult]:
        """
        Obtiene un resultado de la caché de forma asíncrona si está disponible.
        
        Args:
            cache_key: Clave de caché para buscar
                
        Returns:
            AnalysisResult or None: Resultado en caché o None si no existe
        """
        # Usar run_in_executor para operaciones bloqueantes
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cache.get, cache_key)
    
    async def _set_cached_result_async(self, cache_key: str, result: AnalysisResult, 
                                     timeout: int = None) -> None:
        """
        Almacena un resultado en la caché de forma asíncrona.
        
        Args:
            cache_key: Clave de caché
            result: Resultado a almacenar
            timeout: Tiempo de expiración en segundos (opcional, usa self.cache_timeout por defecto)
        """
        # Usar run_in_executor para operaciones bloqueantes
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: cache.set(cache_key, result, timeout=timeout or self.cache_timeout)
        )
    
    # Métodos síncronos para compatibilidad con código existente
    def _get_cached_result(self, cache_key: str) -> Optional[AnalysisResult]:
        """Versión síncrona para compatibilidad con código existente."""
        return cache.get(cache_key)
    
    def _set_cached_result(self, cache_key: str, result: AnalysisResult, 
                         timeout: int = None) -> None:
        """Versión síncrona para compatibilidad con código existente."""
        cache.set(cache_key, result, timeout=timeout or self.cache_timeout)
    
    def validate_assessment_data(self, data: AssessmentData) -> bool:
        """
        Valida los datos de evaluación de entrada.
        
        Args:
            data: Datos de evaluación a validar
                
        Returns:
            bool: True si los datos son válidos, False en caso contrario
        """
        required_fields = ['assessment_type', 'responses']
        return all(field in data for field in required_fields)
        
    @measure_time
    async def analyze(self, candidate_data: Dict[str, Any], 
                    business_unit: Optional[BusinessUnit] = None) -> AnalysisResult:
        """
        Analiza la personalidad del candidato basándose en los datos proporcionados.
        
        Args:
            candidate_data: Datos del candidato, incluyendo evaluaciones
            business_unit: Unidad de negocio para la personalización (opcional)
                
        Returns:
            AnalysisResult: Resultados del análisis de personalidad
                
        Raises:
            ValueError: Si los datos de entrada son inválidos
        """
        metrics.record_request()
        
        # Validación de entrada
        if not self.validate_assessment_data(candidate_data):
            metrics.record_error()
            raise ValueError("Datos de evaluación inválidos o incompletos")
        
        # Generar clave de caché y verificar caché
        cache_key = self._generate_cache_key(candidate_data)
        cached_result = await self._get_cached_result_async(cache_key)
        
        if cached_result is not None:
            metrics.record_cache_hit()
            logger.debug(f"Resultado encontrado en caché con clave: {cache_key}")
            return cached_result
            
        metrics.record_cache_miss()
        
        try:
            # Procesar los datos de evaluación
            result = await self._process_assessment_data_async(candidate_data, business_unit)
            
            # Almacenar en caché de forma asíncrona
            asyncio.create_task(self._set_cached_result_async(cache_key, result))
            
            return result
            
        except Exception as e:
            metrics.record_error()
            logger.error(f"Error al analizar la personalidad: {str(e)}", exc_info=True)
            # Devolver un análisis por defecto en caso de error
            return self._get_default_analysis(
                assessment_type=candidate_data.get('assessment_type', 'unknown'),
                error_message=str(e)
            )
        
    def _validate_input_data(self, data: Dict) -> None:
        """
        Valida los datos de entrada del análisis.
        
        Args:
            data: Datos del candidato a validar
            
        Raises:
            ValueError: Si los datos son inválidos o faltan campos requeridos
        """
        if not data or not isinstance(data, dict):
            raise ValueError("Los datos del candidato son inválidos o están vacíos")
            
        # Verificar campos requeridos
        required_fields = ['assessment_type', 'responses']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo requerido faltante: {field}")
        
        # Validar que las respuestas sean un diccionario no vacío
        if not isinstance(data.get('responses'), dict) or not data['responses']:
            raise ValueError("Las respuestas del assessment deben ser un diccionario no vacío")
        
        # Validar tipo de assessment
        valid_assessment_types = ['personality', 'professional_dna', 'cultural_fit', 'talent']
        if data.get('assessment_type') not in valid_assessment_types:
            logger.warning(f"Tipo de assessment no reconocido: {data.get('assessment_type')}")
    
    def _get_cache_key(self, data: Dict) -> str:
        """
        Genera una clave de caché única para los datos del candidato.
        
        Args:
            data: Datos del candidato
            
        Returns:
            str: Clave de caché única
        """
        # Usar solo los campos relevantes para la clave de caché
        cache_data = {
            'assessment_type': data.get('assessment_type'),
            'responses_hash': self._hash_dict(data.get('responses', {})),
            'version': 'v1'  # Versión del esquema de caché
        }
        
        # Convertir a JSON y luego a hash MD5 para una clave consistente
        cache_str = json.dumps(cache_data, sort_keys=True)
        return f"personality_analysis_{hashlib.md5(cache_str.encode('utf-8')).hexdigest()}"
    
    @staticmethod
    def _hash_dict(data: Dict) -> str:
        """
        Genera un hash único para un diccionario.
        
        Args:
            data: Diccionario a hashear
            
        Returns:
            str: Hash MD5 del diccionario serializado
        """
        return hashlib.md5(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()
    
    async def _process_assessment_data_async(self, data: AssessmentData, 
                                          business_unit: Optional[BusinessUnit] = None) -> AnalysisResult:
        """
        Procesa los datos de evaluación según el tipo de evaluación de forma asíncrona.
        
        Args:
            data: Datos de evaluación
            business_unit: Unidad de negocio (opcional)
                
        Returns:
            AnalysisResult: Resultados del análisis
                
        Raises:
            ValueError: Si el tipo de evaluación no es compatible
        """
        assessment_type = data.get('assessment_type', '').lower()
        
        # Usar procesamiento en paralelo para evaluaciones independientes
        if 'psychometric' in assessment_type:
            # Procesar componentes en paralelo si es posible
            tasks = [
                self._analyze_psychometric(data, business_unit),
                # Otras tareas que se puedan ejecutar en paralelo
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return self._combine_psychometric_results(results)
        handler = handlers.get(assessment_type, self._analyze_generic)
        
        # Ejecutar el análisis
        result = handler(data, business_unit)
        
        # Asegurar que el resultado tenga la estructura correcta
        if not isinstance(result, dict):
            logger.warning(f"El manejador para {assessment_type} no devolvió un diccionario")
            return self._get_default_analysis(assessment_type=assessment_type)
            
        return result
    
    def _analyze_personality(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> AnalysisResult:
        """
        Analiza datos de personalidad según el modelo de los Cinco Grandes.
        
        Este método implementa el análisis de personalidad basado en el modelo de los
        Cinco Grandes (Big Five), que evalúa cinco dimensiones principales de la personalidad:
        apertura a la experiencia, responsabilidad, extraversión, amabilidad y neuroticismo.
        
        Args:
            data: Datos del assessment de personalidad
            business_unit: Unidad de negocio para contextualizar recomendaciones
            
        Returns:
            AnalysisResult: Resultados del análisis de personalidad
        """
        try:
            # Extraer respuestas relevantes
            responses = data.get('responses', {})
            
            # Validar que hay suficientes respuestas
            if not responses:
                logger.warning("No se encontraron respuestas para el análisis de personalidad")
                return self._get_default_analysis(
                    assessment_type='personality',
                    error_message="No se encontraron respuestas para el análisis"
                )
            
            logger.debug(f"Analizando {len(responses)} respuestas de personalidad")
            
            # Calcular puntuaciones de rasgos
            traits = {}
            for trait in self.PERSONALITY_TRAITS['big_five']:
                trait_score = self._calculate_trait_score(trait, responses)
                traits[trait] = trait_score
                
            # Generar insights basados en puntuaciones
            strengths, improvements = self._identify_strengths_improvements(traits)
            recommended_roles = self._recommend_roles(traits, business_unit)
            
            # Crear resultado estructurado
            result: AnalysisResult = {
                'traits': traits,
                'insights': {
                    'strengths': strengths,
                    'areas_improvement': improvements,
                    'recommended_roles': recommended_roles,
                    'overall_score': sum(traits.values()) / len(traits) if traits else 0.0
                },
                'recommendations': self._generate_personality_recommendations(
                    traits, 
                    strengths, 
                    improvements,
                    business_unit
                )
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error en el análisis de personalidad: {str(e)}", exc_info=True)
            return self._get_default_analysis(
                assessment_type='personality',
                error_message=str(e)
            )
    
    def _analyze_professional_dna(self, data: Dict, business_unit: Any) -> Dict:
        """Analiza datos específicos de ADN profesional."""
        # Extraer respuestas relevantes
        responses = data.get('responses', {})
        
        # Calcular puntuaciones de dimensiones
        dimensions = {}
        for dimension in self.PERSONALITY_TRAITS['professional_dna']:
            dimension_score = self._calculate_dimension_score(dimension, responses)
            dimensions[dimension] = dimension_score
            
        # Generar insights basados en puntuaciones
        insights = self._generate_professional_dna_insights(dimensions)
        recommendations = self._generate_professional_dna_recommendations(dimensions, business_unit)
        
        return {
            'dimensions': dimensions,
            'insights': insights,
            'recommendations': recommendations
        }
    
    def _analyze_cultural_fit(self, data: Dict, business_unit: Any) -> Dict:
        """Analiza datos de fit cultural."""
        # Implementación básica que se puede expandir
        cultural_aspects = {}
        for aspect in self.PERSONALITY_TRAITS['cultural_fit']:
            cultural_aspects[aspect] = data.get(aspect, 0.5)
            
        return {
            'cultural_fit': cultural_aspects,
            'compatibility_score': sum(cultural_aspects.values()) / len(cultural_aspects),
            'recommendations': [
                'Evaluar alineación con valores de la empresa',
                'Considerar dinámicas de equipo en la entrevista'
            ]
        }
    
    def _analyze_talent(self, data: Dict, business_unit: Any) -> Dict:
        """Analiza datos de evaluación de talento."""
        # Implementación básica
        skill_levels = data.get('skill_levels', {})
        experience = data.get('experience', {})
        
        return {
            'skill_assessment': skill_levels,
            'experience_assessment': experience,
            'talent_score': 0.7,  # Placeholder, se implementaría algoritmo real
            'development_areas': ['Liderazgo técnico', 'Gestión de proyectos']
        }
    
    def _analyze_generic(self, data: Dict, business_unit: Any) -> Dict:
        """Analiza datos genéricos cuando no hay tipo específico."""
        # Fallback genérico
        return {
            'general_score': 0.7,
            'recommendations': [
                'Revisar historial profesional para evaluar trayectoria',
                'Considerar entrevista adicional para validar habilidades'
            ]
        }
        
    def _calculate_trait_score(self, trait: str, responses: Dict) -> float:
        """Calcula la puntuación para un rasgo basado en las respuestas."""
        # Implementación básica que se puede expandir
        trait_questions = [q for q in responses.keys() if trait in q.lower()]
        if not trait_questions:
            return 0.5  # Valor por defecto
            
        scores = [float(responses[q]) for q in trait_questions if responses[q]]
        return sum(scores) / len(scores) if scores else 0.5
        
    def _calculate_dimension_score(self, dimension: str, responses: Dict) -> float:
        """Calcula la puntuación para una dimensión de DNA profesional."""
        # Similar a trait_score pero adaptado a dimensiones profesionales
        dimension_questions = [q for q in responses.keys() if dimension.replace('_', ' ') in q.lower()]
        if not dimension_questions:
            return 50.0  # Valor por defecto (escala 0-100)
            
        scores = []
        for q in dimension_questions:
            if responses[q]:
                # Convertir respuestas a escala 0-100
                try:
                    val = float(responses[q])
                    # Asumiendo respuestas en escala 1-5
                    scores.append((val - 1) * 25)  # Convierte 1-5 a 0-100
                except (ValueError, TypeError):
                    continue
                    
        return sum(scores) / len(scores) if scores else 50.0
        
    def _identify_strengths_improvements(self, traits: Dict) -> Tuple[List[str], List[str]]:
        """Identifica fortalezas y áreas de mejora basadas en rasgos."""
        strengths = []
        improvements = []
        
        # Mapeo de rasgos a fortalezas (alto) y mejoras (bajo)
        trait_mapping = {
            'openness': ('Creatividad e innovación', 'Apertura a nuevas ideas'),
            'conscientiousness': ('Organización y responsabilidad', 'Planificación y disciplina'),
            'extraversion': ('Habilidades sociales y comunicativas', 'Asertividad en grupos'),
            'agreeableness': ('Trabajo en equipo y empatía', 'Colaboración y consenso'),
            'neuroticism': ('Estabilidad emocional', 'Manejo del estrés')
        }
        
        # Umbrales para considerar alto o bajo
        high_threshold = 0.7
        low_threshold = 0.3
        
        for trait, score in traits.items():
            if trait == 'neuroticism':
                # Para neuroticismo, bajo es bueno (estabilidad emocional)
                if score < low_threshold:
                    strengths.append(trait_mapping[trait][0])
                elif score > high_threshold:
                    improvements.append(trait_mapping[trait][1])
            else:
                # Para otros rasgos, alto es generalmente bueno
                if score > high_threshold:
                    strengths.append(trait_mapping[trait][0])
                elif score < low_threshold:
                    improvements.append(trait_mapping[trait][1])
                    
        return strengths, improvements
        
    def _recommend_roles(self, traits: Dict, business_unit: Any) -> List[str]:
        """Recomienda roles basados en perfil de personalidad y BU."""
        # Implementación básica que se puede expandir
        
        # Si no hay BU, dar recomendaciones genéricas
        if not business_unit:
            return ['Analista', 'Especialista', 'Coordinador']
            
        # Mapeo simplificado de rasgos dominantes a roles por BU
        bu_role_mapping = {
            'huntRED': {
                'openness': ['Consultor de Innovación', 'Estratega de Transformación'],
                'conscientiousness': ['Gerente de Proyectos', 'Director de Operaciones'],
                'extraversion': ['Director Comercial', 'Gerente de Relaciones Públicas'],
                'agreeableness': ['Gerente de Recursos Humanos', 'Director de Cultura Organizacional'],
                'low_neuroticism': ['Director General', 'Gerente de Crisis']
            },
            'huntU': {
                'openness': ['Desarrollador Creativo', 'Investigador'],
                'conscientiousness': ['Analista de Datos', 'Ingeniero de Calidad'],
                'extraversion': ['Ejecutivo de Ventas', 'Coordinador de Eventos'],
                'agreeableness': ['Especialista en Atención al Cliente', 'Coordinador de Equipo'],
                'low_neuroticism': ['Analista de Riesgos', 'Coordinador de Proyectos']
            },
            'Amigro': {
                'openness': ['Desarrollador de Soluciones', 'Especialista en Mejora Continua'],
                'conscientiousness': ['Supervisor de Operaciones', 'Administrador de Inventario'],
                'extraversion': ['Representante de Ventas', 'Ejecutivo de Servicio'],
                'agreeableness': ['Representante de Servicio al Cliente', 'Coordinador de Comunidad'],
                'low_neuroticism': ['Supervisor de Logística', 'Coordinador de Campo']
            }
        }
        
        # Determinar rasgo dominante (excluye neuroticismo)
        dominant_traits = []
        for trait, score in traits.items():
            if trait != 'neuroticism' and score > 0.65:
                dominant_traits.append(trait)
                
        if traits.get('neuroticism', 1.0) < 0.35:
            dominant_traits.append('low_neuroticism')
            
        # Si no hay rasgos dominantes, dar recomendación genérica para esa BU
        if not dominant_traits:
            return ['Posición analítica', 'Rol de especialista']
            
        # Obtener roles para los rasgos dominantes
        recommended_roles = []
        bu_name = getattr(business_unit, 'name', str(business_unit))
        bu_name = bu_name if bu_name in bu_role_mapping else 'huntRED'
        
        for trait in dominant_traits:
            if trait in bu_role_mapping[bu_name]:
                recommended_roles.extend(bu_role_mapping[bu_name][trait])
                
        return recommended_roles[:3]  # Limitar a 3 recomendaciones
        
    def _generate_professional_dna_insights(self, dimensions: Dict) -> Dict:
        """Genera insights basados en dimensiones de DNA profesional."""
        insights = {}
        
        # Definir interpretaciones para cada dimensión
        dimension_insights = {
            'strategic_thinking': 'Capacidad para pensar a largo plazo y alinear acciones con objetivos',
            'emotional_intelligence': 'Habilidad para reconocer y gestionar emociones propias y ajenas',
            'adaptability': 'Flexibilidad para ajustarse a cambios y nuevos entornos',
            'collaboration': 'Efectividad trabajando con otros para lograr objetivos comunes',
            'innovation': 'Capacidad para generar y aplicar ideas nuevas',
            'resilience': 'Fortaleza para recuperarse de dificultades y persistir',
            'results_orientation': 'Enfoque en lograr objetivos medibles y tangibles'
        }
        
        # Generar insight para cada dimensión
        for dimension, score in dimensions.items():
            base_insight = dimension_insights.get(dimension, '')
            if score > 75:
                level = "alto"
                impact = "una fortaleza significativa"
            elif score > 50:
                level = "moderado"
                impact = "un área con buen desarrollo"
            else:
                level = "en desarrollo"
                impact = "un área de oportunidad"
                
            insights[dimension] = f"{base_insight}. Tu nivel es {level}, lo que representa {impact}."
            
        return insights
        
    def _generate_professional_dna_recommendations(self, dimensions: Dict, business_unit: Any) -> List[str]:
        """Genera recomendaciones basadas en DNA profesional."""
        recommendations = []
        
        # Identificar dimensiones más bajas (áreas de oportunidad)
        low_dimensions = [d for d, score in dimensions.items() if score < 50]
        
        # Recomendaciones generales basadas en dimensiones bajas
        dimension_recommendations = {
            'strategic_thinking': 'Desarrollar habilidades de pensamiento a largo plazo y planificación',
            'emotional_intelligence': 'Practicar la autoconciencia y la empatía en interacciones profesionales',
            'adaptability': 'Exponerse a situaciones nuevas y diversas para aumentar flexibilidad',
            'collaboration': 'Participar en proyectos de equipo que requieran coordinación efectiva',
            'innovation': 'Dedicar tiempo a la generación de ideas y soluciones creativas',
            'resilience': 'Desarrollar técnicas de manejo del estrés y recuperación',
            'results_orientation': 'Establecer objetivos claros y medibles para tareas y proyectos'
        }
        
        # Añadir recomendaciones para dimensiones bajas
        for dimension in low_dimensions:
            if dimension in dimension_recommendations:
                recommendations.append(dimension_recommendations[dimension])
                
        # Añadir recomendaciones basadas en dimensiones altas (fortalezas)
        high_dimensions = [d for d, score in dimensions.items() if score > 75]
        if high_dimensions:
            high_dim = high_dimensions[0]  # Tomar la primera dimensión alta
            recommendations.append(f"Aprovechar tu alta {high_dim.replace('_', ' ')} en roles que requieran esta habilidad")
            
        # Añadir recomendación general si no hay muchas específicas
        if len(recommendations) < 2:
            recommendations.append("Buscar oportunidades de desarrollo integral en todas las dimensiones del ADN profesional")
            
        return recommendations
        
    def _enrich_with_ml_insights(self, result: Dict, candidate_data: Dict, business_unit: Any) -> Dict:
        """Enriquece los resultados con insights del sistema ML."""
        try:
            # Solo si tenemos suficiente información del candidato
            if 'personality_traits' in candidate_data or 'responses' in candidate_data:
                # Usar el sistema ML existente para obtener insights adicionales
                # Esto podría incluir predicciones basadas en modelos entrenados
                
                # Ejemplo de enriquecimiento:
                result['ml_insights'] = {
                    'market_alignment': 0.75,
                    'success_probability': 0.68,
                    'development_path': [
                        'Especializarse en habilidades técnicas core',
                        'Desarrollar competencias de liderazgo',
                        'Fortalecer habilidades de comunicación escrita'
                    ]
                }
                
                # Si el sistema ML tiene funcionalidad de matchmaking, usarla
                if hasattr(self.ml_system, 'calculate_personality_similarity'):
                    # Simulamos un objeto persona y vacante para la interfaz existente
                    # En una implementación real, construiríamos estos objetos adecuadamente
                    class MockObject:
                        def __init__(self, **kwargs):
                            for key, value in kwargs.items():
                                setattr(self, key, value)
                    
                    person = MockObject(personality_traits=result.get('traits', {}))
                    vacancy = MockObject(culture_fit={})
                    
                    # Calcular similitud usando el sistema existente
                    similarity = 0.5  # Valor por defecto
                    try:
                        similarity = self.ml_system.calculate_personality_similarity(person, vacancy)
                    except Exception as e:
                        logger.warning(f"Error calculating personality similarity: {str(e)}")
                        
                    result['personality_match'] = similarity
                
            return result
            
        except Exception as e:
            logger.error(f"Error enriqueciendo con ML insights: {str(e)}")
            return result
            
    def _generate_personality_recommendations(self, traits: Dict, strengths: List[str], 
                                         improvements: List[str], business_unit: Any) -> List[str]:
        """
        Genera recomendaciones personalizadas basadas en el perfil de personalidad.
        
        Args:
            traits: Diccionario con rasgos de personalidad y sus puntuaciones
            strengths: Lista de fortalezas identificadas
            improvements: Lista de áreas de mejora identificadas
            business_unit: Unidad de negocio para contextualizar recomendaciones
            
        Returns:
            List[str]: Lista de recomendaciones personalizadas
        """
        recommendations = []
        
        # Recomendaciones basadas en fortalezas
        if strengths:
            recommendations.append(
                f"Aprovecha tus fortalezas en {', '.join(strengths[:2])} "
                "para destacar en tu desarrollo profesional."
            )
        
        # Recomendaciones basadas en áreas de mejora
        if improvements:
            recommendations.append(
                f"Considera trabajar en {improvements[0]} para un desarrollo más equilibrado. "
                f"Puedes enfocarte en {improvements[1]} como siguiente paso."
            )
            
        # Recomendaciones específicas por rasgo
        for trait, score in traits.items():
            if score < 0.3:
                if trait == 'openness':
                    recommendations.append(
                        "Explora nuevas experiencias y perspectivas para desarrollar tu apertura."
                    )
            elif score > 0.7:
                if trait == 'conscientiousness':
                    recommendations.append(
                        "Tu alto nivel de responsabilidad es una fortaleza. "
                        "Considera roles que requieran planificación y organización detallada."
                    )
        
        # Asegurar un mínimo de recomendaciones
        if len(recommendations) < 3:
            recommendations.extend([
                "Participa en actividades de desarrollo profesional continuo.",
                "Busca retroalimentación regular para seguir mejorando."
            ])
            
        return recommendations[:5]  # Limitar a 5 recomendaciones
        
    async def _combine_psychometric_results(self, results: List[Dict]) -> AnalysisResult:
        """
        Combina resultados de múltiples evaluaciones psicométricas.
        
        Args:
            results: Lista de resultados de evaluaciones psicométricas
            
        Returns:
            AnalysisResult: Resultado combinado del análisis
        """
        combined = {
            'traits': {},
            'dimensions': {},
            'insights': {},
            'recommendations': [],
            'metadata': {}
        }
        
        # Contadores para promedios
        trait_counts = {}
        dimension_counts = {}
        
        # Combinar resultados
        for result in results:
            if not isinstance(result, dict):
                continue
                
            # Combinar rasgos
            for trait, score in result.get('traits', {}).items():
                combined['traits'][trait] = combined['traits'].get(trait, 0) + score
                trait_counts[trait] = trait_counts.get(trait, 0) + 1
                
            # Combinar dimensiones
            for dim, score in result.get('dimensions', {}).items():
                combined['dimensions'][dim] = combined['dimensions'].get(dim, 0) + score
                dimension_counts[dim] = dimension_counts.get(dim, 0) + 1
                
            # Combinar recomendaciones únicas
            for rec in result.get('recommendations', []):
                if rec not in combined['recommendations']:
                    combined['recommendations'].append(rec)
                    
        # Calcular promedios
        for trait in combined['traits']:
            if trait in trait_counts:
                combined['traits'][trait] /= trait_counts[trait]
                
        for dim in combined['dimensions']:
            if dim in dimension_counts:
                combined['dimensions'][dim] /= dimension_counts[dim]
                
        # Generar insights combinados
        combined['insights'] = self._generate_combined_insights(
            combined['traits'], 
            combined['dimensions']
        )
        
        return cast(AnalysisResult, combined)
        
    def _generate_combined_insights(self, traits: Dict, dimensions: Dict) -> Dict:
        """
        Genera insights combinados a partir de múltiples evaluaciones.
        
        Args:
            traits: Rasgos de personalidad combinados
            dimensions: Dimensiones profesionales combinadas
            
        Returns:
            Dict: Insights generados
        """
        insights = {
            'personality_summary': "",
            'professional_profile': "",
            'development_areas': []
        }
        
        # Resumen de personalidad
        if traits:
            top_trait = max(traits.items(), key=lambda x: x[1])[0] if traits else None
            insights['personality_summary'] = (
                f"Tu perfil de personalidad muestra un perfil equilibrado con una tendencia "
                f"hacia {top_trait.replace('_', ' ').title() if top_trait else 'varias áreas'}."
            )
            
        # Perfil profesional
        if dimensions:
            top_dim = max(dimensions.items(), key=lambda x: x[1])[0] if dimensions else None
            insights['professional_profile'] = (
                f"Tus fortalezas profesionales se alinean con {top_dim.replace('_', ' ').title() if top_dim else 'varias áreas'} "
                "lo que sugiere un buen ajuste para roles que valoren estas competencias."
            )
            
        # Áreas de desarrollo
        if traits and dimensions:
            low_trait = min(traits.items(), key=lambda x: x[1])[0] if traits else None
            low_dim = min(dimensions.items(), key=lambda x: x[1])[0] if dimensions else None
            
            if low_trait and traits[low_trait] < 0.4:
                insights['development_areas'].append(
                    f"Considera trabajar en {low_trait.replace('_', ' ')} para un perfil más equilibrado."
                )
                
            if low_dim and dimensions[low_dim] < 50:
                insights['development_areas'].append(
                    f"El desarrollo de {low_dim.replace('_', ' ')} podría mejorar tu perfil profesional."
                )
                
        return insights
    
    def _get_default_analysis(self, assessment_type: str = 'unknown', error_message: str = '') -> AnalysisResult:
        """
        Proporciona un análisis por defecto en caso de error.
        
        Args:
            assessment_type: Tipo de evaluación que falló
            error_message: Mensaje de error (opcional)
            
        Returns:
            AnalysisResult: Resultado de análisis por defecto
        """
        return AnalysisResult(
            traits={},
            dimensions={},
            insights={
                'error': f'No se pudo completar el análisis de {assessment_type}',
                'message': error_message or 'Error desconocido',
                'recommendation': 'Por favor, inténtalo de nuevo más tarde o contacta al soporte.'
            },
            recommendations=[
                'Verifica la calidad de los datos de entrada',
                'Revisa los logs del sistema para más detalles',
                'Si el problema persiste, contacta al equipo de soporte técnico'
            ],
            metadata={
                'status': 'error',
                'error_type': 'analysis_failed',
                'assessment_type': assessment_type,
                'retry_available': True,
                'timestamp': timezone.now().isoformat()
            }
        )
