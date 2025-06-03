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
from app.ml.core.models.base import MatchmakingLearningSystem  # Sistema de ML
from app.ml.analyzers.base_analyzer import BaseAnalyzer

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

class PersonalityAnalyzer(BaseAnalyzer):
    """
    Analizador de personalidad basado en el modelo TIPI y otros factores.
    """
    
    def __init__(self):
        super().__init__()
        self.model = MatchmakingLearningSystem()
        
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza los datos de personalidad y retorna un perfil.
        
        Args:
            data: Diccionario con los datos de personalidad
            
        Returns:
            Dict con el perfil de personalidad
        """
        try:
            # Extraer características de personalidad
            personality_traits = self._extract_traits(data)
            
            # Calcular compatibilidad
            compatibility = self._calculate_compatibility(personality_traits)
            
            # Generar recomendaciones
            recommendations = self._generate_recommendations(personality_traits)
            
            return {
                'traits': personality_traits,
                'compatibility': compatibility,
                'recommendations': recommendations,
                'score': self._calculate_score(personality_traits)
            }
            
        except Exception as e:
            logger.error(f"Error analizando personalidad: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }
            
    def _extract_traits(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extrae los rasgos de personalidad de los datos.
        """
        traits = {}
        
        # Extraer puntuaciones TIPI
        tipi_scores = data.get('tipi_scores', {})
        for trait, score in tipi_scores.items():
            traits[f'tipi_{trait}'] = float(score)
            
        # Extraer otros rasgos
        other_traits = data.get('other_traits', {})
        traits.update(other_traits)
        
        return traits
        
    def _calculate_compatibility(self, traits: Dict[str, float]) -> Dict[str, float]:
        """
        Calcula la compatibilidad con diferentes perfiles.
        """
        try:
            return self.model.predict_compatibility(traits)
        except Exception as e:
            logger.error(f"Error calculando compatibilidad: {str(e)}")
            return {}
            
    def _generate_recommendations(self, traits: Dict[str, float]) -> List[str]:
        """
        Genera recomendaciones basadas en el perfil.
        """
        try:
            return self.model.generate_recommendations(traits)
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return []
            
    def _calculate_score(self, traits: Dict[str, float]) -> float:
        """
        Calcula un score general del perfil.
        """
        try:
            return self.model.calculate_score(traits)
        except Exception as e:
            logger.error(f"Error calculando score: {str(e)}")
            return 0.0
