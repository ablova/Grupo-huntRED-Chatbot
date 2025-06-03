"""
Utilidades de caché para Grupo huntRED®.
Implementa funciones optimizadas para cacheo de consultas frecuentes
utilizando Redis, siguiendo las reglas globales de CPU efficiency.
"""

import logging
import json
import hashlib
import pickle
from typing import Any, Optional, Dict, Callable
from functools import wraps
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

def cache_result(prefix: str, timeout: int = 3600, use_pickle: bool = False):
    """
    Decorador para cachear resultados de funciones con Redis.
    Optimiza las consultas frecuentes siguiendo las reglas de CPU efficiency.
    
    Args:
        prefix: Prefijo para la clave de caché
        timeout: Tiempo de expiración en segundos
        use_pickle: Si se debe usar pickle para serializar objetos complejos
        
    Returns:
        Callable: Decorador para la función
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave única para la consulta
            key_parts = [prefix, func.__name__]
            
            # Añadir args y kwargs serializables a la clave
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
            
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}:{v}")
            
            # Generar clave única con hash
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Intentar obtener desde caché
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit para {func.__name__}: {cache_key}")
                if use_pickle:
                    try:
                        return pickle.loads(cached_result)
                    except Exception as e:
                        logger.error(f"Error deserializando caché: {str(e)}")
                        # Continuar para recalcular
                else:
                    return cached_result
            
            # Ejecutar función si no está en caché
            logger.debug(f"Cache miss para {func.__name__}: {cache_key}")
            result = func(*args, **kwargs)
            
            # Cachear resultado
            try:
                if use_pickle and not isinstance(result, (str, int, float, bool, dict, list)):
                    cache.set(cache_key, pickle.dumps(result), timeout)
                else:
                    cache.set(cache_key, result, timeout)
            except Exception as e:
                logger.error(f"Error cacheando resultado: {str(e)}")
            
            return result
        return wrapper
    return decorator


def invalidate_cache(prefix: str = None, keys: list = None):
    """
    Invalida claves de caché por prefijo o lista específica.
    
    Args:
        prefix: Prefijo de claves a invalidar
        keys: Lista específica de claves a invalidar
    """
    if prefix:
        # Usar clave de patrón para compatibilidad con Redis
        pattern = f"{prefix}*"
        try:
            # Si es Redis, usar scan_iter() para claves con patrón
            if hasattr(cache, '_cache') and hasattr(cache._cache, 'scan_iter'):
                keys_to_delete = list(cache._cache.scan_iter(match=pattern))
                if keys_to_delete:
                    cache._cache.delete(*keys_to_delete)
                    logger.info(f"Caché invalidado para patrón: {pattern}, {len(keys_to_delete)} claves")
            else:
                # Fallback para otros backends de caché
                logger.warning(f"Invalidación por patrón no soportada en este backend")
        except Exception as e:
            logger.error(f"Error invalidando caché por patrón: {str(e)}")
    
    if keys:
        for key in keys:
            try:
                cache.delete(key)
            except Exception as e:
                logger.error(f"Error invalidando clave {key}: {str(e)}")
        
        logger.info(f"Caché invalidado para {len(keys)} claves específicas")


def cached_dashboard_stats(business_unit_id=None, timeout=900):
    """
    Obtiene estadísticas de dashboard cacheadas.
    Wrapper optimizado para DashboardUtils.get_dashboard_stats().
    
    Args:
        business_unit_id: ID opcional de BU para filtrar
        timeout: Tiempo de caché en segundos (15 min default)
        
    Returns:
        dict: Estadísticas del dashboard
    """
    from app.ats.dashboard_utils import DashboardUtils
    
    # Generar clave de caché
    cache_key = f"dashboard:stats:{business_unit_id or 'all'}"
    
    # Intentar obtener desde caché
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.debug(f"Cache hit para dashboard_stats: {cache_key}")
        return cached_result
    
    # Calcular si no está en caché
    result = DashboardUtils.get_dashboard_stats(business_unit_id)
    
    # Cachear resultado
    try:
        # Añadir timestamp para saber cuándo fue cacheado
        result['cache_timestamp'] = timezone.now().isoformat()
        cache.set(cache_key, result, timeout)
    except Exception as e:
        logger.error(f"Error cacheando dashboard_stats: {str(e)}")
    
    return result
