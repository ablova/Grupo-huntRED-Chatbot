# /home/pablo/app/utils/system_optimization.py
"""
Utilidades para optimización del sistema Grupo huntRED®.
Este módulo centraliza herramientas para mejorar rendimiento, seguridad y
coherencia en todos los componentes del sistema.
"""

import logging
import asyncio
import time
import inspect
import functools
import redis
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, TypeVar, Generic
from django.conf import settings
from django.core.cache import cache
from django.db.models import Model, QuerySet
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

# Tipos para anotaciones
T = TypeVar('T')
ModelType = TypeVar('ModelType', bound=Model)
FuncType = TypeVar('FuncType', bound=Callable)


class PerformanceTracker:
    """
    Clase para monitorear y optimizar rendimiento en todos los componentes.
    Implementa métricas, caché y medición de tiempos.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Implementación Singleton para tener una instancia global."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.metrics = {}
            cls._instance.slow_operations = []
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        """Inicializa recursos necesarios para el tracker."""
        self.start_time = time.time()
        self.operation_count = 0
        
        # Inicializar conexión a Redis para métricas persistentes
        try:
            self.redis_client = redis.Redis.from_url(
                settings.REDIS_URL, 
                decode_responses=True
            )
            logger.info("PerformanceTracker: Redis connection established")
        except Exception as e:
            self.redis_client = None
            logger.warning(f"PerformanceTracker: Could not connect to Redis: {str(e)}")
    
    def track_operation(self, operation_type: str, duration: float, details: Dict = None):
        """
        Registra una operación para métricas de rendimiento.
        
        Args:
            operation_type: Tipo de operación (db_query, api_call, etc.)
            duration: Duración en segundos
            details: Detalles adicionales sobre la operación
        """
        self.operation_count += 1
        
        if operation_type not in self.metrics:
            self.metrics[operation_type] = {
                'count': 0,
                'total_time': 0,
                'min_time': float('inf'),
                'max_time': 0
            }
        
        self.metrics[operation_type]['count'] += 1
        self.metrics[operation_type]['total_time'] += duration
        self.metrics[operation_type]['min_time'] = min(self.metrics[operation_type]['min_time'], duration)
        self.metrics[operation_type]['max_time'] = max(self.metrics[operation_type]['max_time'], duration)
        
        # Registrar operaciones lentas para análisis
        threshold = 0.5  # 500ms
        if duration > threshold:
            self.slow_operations.append({
                'type': operation_type,
                'duration': duration,
                'timestamp': time.time(),
                'details': details or {}
            })
            
            # Limitar lista de operaciones lentas
            if len(self.slow_operations) > 1000:
                self.slow_operations = self.slow_operations[-1000:]
        
        # Persistir datos en Redis para análisis a largo plazo
        if self.redis_client:
            try:
                key = f"performance:{operation_type}:{int(time.time())}"
                self.redis_client.hmset(key, {
                    'duration': duration,
                    'details': str(details or {})
                })
                self.redis_client.expire(key, 86400 * 7)  # 7 días
            except Exception as e:
                logger.error(f"Error persisting metrics to Redis: {str(e)}")
    
    def get_metrics_report(self) -> Dict:
        """
        Genera un reporte de métricas de rendimiento.
        
        Returns:
            Dict: Reporte de métricas
        """
        runtime = time.time() - self.start_time
        
        report = {
            'runtime': runtime,
            'operation_count': self.operation_count,
            'operations_per_second': self.operation_count / runtime if runtime > 0 else 0,
            'metrics_by_type': {},
            'slow_operations_count': len(self.slow_operations)
        }
        
        for op_type, data in self.metrics.items():
            if data['count'] > 0:
                avg_time = data['total_time'] / data['count']
            else:
                avg_time = 0
                
            report['metrics_by_type'][op_type] = {
                'count': data['count'],
                'total_time': data['total_time'],
                'avg_time': avg_time,
                'min_time': data['min_time'] if data['min_time'] != float('inf') else 0,
                'max_time': data['max_time']
            }
            
        return report
    
    def reset_metrics(self):
        """Reinicia las métricas acumuladas."""
        self.metrics = {}
        self.slow_operations = []
        self.start_time = time.time()
        self.operation_count = 0


# Decoradores para optimización de rendimiento en todo el sistema

def performance_tracked(operation_type: str = None):
    """
    Decorador para rastrear el rendimiento de cualquier función o método.
    Se puede aplicar en cualquier componente del sistema.
    
    Args:
        operation_type: Tipo de operación para categorización
    """
    def decorator(func: FuncType) -> FuncType:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if operation_type is None:
                op_type = f"{func.__module__}.{func.__name__}"
            else:
                op_type = operation_type
                
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Registrar operación
            tracker = PerformanceTracker()
            tracker.track_operation(
                op_type, 
                duration, 
                {'args': str(args), 'kwargs': str(kwargs)}
            )
            
            return result
            
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if operation_type is None:
                op_type = f"{func.__module__}.{func.__name__}"
            else:
                op_type = operation_type
                
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Registrar operación
            tracker = PerformanceTracker()
            tracker.track_operation(
                op_type, 
                duration, 
                {'args': str(args), 'kwargs': str(kwargs)}
            )
            
            return result
        
        # Determinar si la función es asíncrona
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
        
    return decorator


def cached_result(timeout: int = 300, key_prefix: str = None):
    """
    Decorador para cachear resultados de funciones en todo el sistema.
    
    Args:
        timeout: Tiempo de expiración en segundos
        key_prefix: Prefijo personalizado para la clave de caché
    """
    def decorator(func: FuncType) -> FuncType:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generar clave de caché
            if key_prefix:
                prefix = key_prefix
            else:
                prefix = f"{func.__module__}.{func.__name__}"
            
            # Crear clave única basada en argumentos
            key_parts = [prefix]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            
            cache_key = ":".join(key_parts)
            
            # Intentar obtener de caché
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Calcular resultado
            result = func(*args, **kwargs)
            
            # Guardar en caché
            cache.set(cache_key, result, timeout)
            
            return result
            
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generar clave de caché
            if key_prefix:
                prefix = key_prefix
            else:
                prefix = f"{func.__module__}.{func.__name__}"
            
            # Crear clave única basada en argumentos
            key_parts = [prefix]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            
            cache_key = ":".join(key_parts)
            
            # Intentar obtener de caché
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Calcular resultado
            result = await func(*args, **kwargs)
            
            # Guardar en caché
            cache.set(cache_key, result, timeout)
            
            return result
        
        # Determinar si la función es asíncrona
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
        
    return decorator


def optimized_db_query(select_related: List[str] = None, prefetch_related: List[str] = None):
    """
    Decorador para optimizar consultas a base de datos en todo el sistema.
    Automáticamente aplica select_related y prefetch_related según necesidad.
    
    Args:
        select_related: Campos para select_related
        prefetch_related: Campos para prefetch_related
    """
    def decorator(func: FuncType) -> FuncType:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Si el resultado es un QuerySet, aplicar optimizaciones
            if isinstance(result, QuerySet):
                if select_related:
                    result = result.select_related(*select_related)
                if prefetch_related:
                    result = result.prefetch_related(*prefetch_related)
            
            return result
        return wrapper
    return decorator


# Utilidades para consistencia en todo el sistema

def apply_business_unit_filter(queryset: QuerySet, user, bu_param: str = None) -> QuerySet:
    """
    Aplica filtro por Business Unit de forma consistente en todo el sistema.
    
    Args:
        queryset: QuerySet a filtrar
        user: Usuario actual
        bu_param: Parámetro de BU opcional
        
    Returns:
        QuerySet filtrado
    """
    from app.ats.utils.rbac import RBAC
    
    # Si hay un parámetro BU explícito, intentar usarlo
    if bu_param:
        # Verificar permiso con RBAC
        if RBAC.has_permission(user, f"view_bu_{bu_param}"):
            return queryset.filter(bu_id=bu_param)
    
    # Si el usuario es superadmin, no filtrar
    if user.is_superuser:
        return queryset
    
    # Obtener BUs permitidas para el usuario
    if hasattr(user, 'profile') and hasattr(user.profile, 'business_units'):
        allowed_bus = user.profile.business_units.values_list('id', flat=True)
        return queryset.filter(bu_id__in=allowed_bus)
    
    # Si no tiene perfil o BUs asignadas, no mostrar nada
    return queryset.none()


def standardize_response(data: Any = None, errors: List = None, 
                        status: str = "success", meta: Dict = None) -> Dict:
    """
    Estandariza respuestas de API en todo el sistema.
    
    Args:
        data: Datos principales de respuesta
        errors: Lista de errores si existen
        status: Estado de la operación
        meta: Metadatos adicionales
        
    Returns:
        Respuesta estandarizada
    """
    response = {
        "status": status,
        "timestamp": time.time()
    }
    
    if data is not None:
        response["data"] = data
        
    if errors:
        response["errors"] = errors
        response["status"] = "error"
        
    if meta:
        response["meta"] = meta
        
    return response


# Entrypoint para la optimización del sistema
def optimize_system():
    """
    Aplica optimizaciones a nivel sistema.
    Esta función puede ser llamada durante el inicio de la aplicación.
    """
    # Inicializar tracker de rendimiento
    tracker = PerformanceTracker()
    logger.info("System-wide performance tracking initialized")
    
    # Configurar caché para modelos frecuentes (estratégico)
    common_models = ["BusinessUnit", "Person", "Vacante", "Pago"]
    
    for model_name in common_models:
        cache_key = f"model_count:{model_name}"
        if not cache.get(cache_key):
            try:
                from django.apps import apps
                model = apps.get_model('app', model_name)
                count = model.objects.count()
                cache.set(cache_key, count, 3600)
            except Exception as e:
                logger.error(f"Error caching model count for {model_name}: {str(e)}")
    
    logger.info("System optimization complete")
    return True
