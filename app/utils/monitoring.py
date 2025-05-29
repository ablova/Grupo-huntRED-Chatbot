"""
Módulo de monitoreo para métricas y rendimiento.

Proporciona utilidades para rastrear métricas de rendimiento, latencia
y estadísticas de uso de las APIs externas.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Dict, Optional, TypeVar, cast
from datetime import datetime

from prometheus_client import start_http_server, Counter, Histogram, Gauge
from django.conf import settings

logger = logging.getLogger(__name__)

# Tipo genérico para funciones
F = TypeVar('F', bound=Callable[..., Any])

# Métricas de LinkedIn
LINKEDIN_REQUESTS = Counter(
    'linkedin_requests_total',
    'Total de solicitudes a la API de LinkedIn',
    ['endpoint', 'status']
)

LINKEDIN_LATENCY = Histogram(
    'linkedin_request_latency_seconds',
    'Latencia de las solicitudes a LinkedIn',
    ['endpoint']
)

LINKEDIN_SCRAPE_DURATION = Histogram(
    'linkedin_scrape_duration_seconds',
    'Duración del scraping de perfiles de LinkedIn',
    ['status']
)

# Métricas de la aplicación
TASK_DURATION = Histogram(
    'task_duration_seconds',
    'Duración de las tareas en segundos',
    ['task_name', 'status']
)

TASKS_IN_PROGRESS = Gauge(
    'tasks_in_progress',
    'Número de tareas actualmente en progreso',
    ['task_name']
)

def monitor_task(task_name: str) -> Callable[[F], F]:
    """
    Decorador para monitorear tareas asíncronas.
    
    Args:
        task_name: Nombre de la tarea para las métricas
        
    Returns:
        Función decorada
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            TASKS_IN_PROGRESS.labels(task_name=task_name).inc()
            
            try:
                result = await func(*args, **kwargs)
                status = 'success'
                return result
            except Exception as e:
                status = 'error'
                logger.error(f"Error en tarea {task_name}: {str(e)}", exc_info=True)
                raise
            finally:
                duration = time.time() - start_time
                TASK_DURATION.labels(task_name=task_name, status=status).observe(duration)
                TASKS_IN_PROGRESS.labels(task_name=task_name).dec()
                
                logger.info(
                    f"Tarea {task_name} completada en {duration:.2f}s. "
                    f"Estado: {status}"
                )
        
        return cast(F, async_wrapper)
    
    return decorator


def monitor_linkedin_request(endpoint: str) -> Callable[[F], F]:
    """
    Decorador para monitorear solicitudes a la API de LinkedIn.
    
    Args:
        endpoint: Nombre del endpoint para las métricas
        
    Returns:
        Función decorada
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                status = 'success'
                return result
            except Exception as e:
                status = 'error'
                logger.error(f"Error en solicitud a {endpoint}: {str(e)}", exc_info=True)
                raise
            finally:
                duration = time.time() - start_time
                LINKEDIN_LATENCY.labels(endpoint=endpoint).observe(duration)
                LINKEDIN_REQUESTS.labels(endpoint=endpoint, status=status).inc()
                
                logger.debug(
                    f"Solicitud a {endpoint} completada en {duration:.2f}s. "
                    f"Estado: {status}"
                )
        
        return cast(F, wrapper)
    
    return decorator


def track_scrape_duration() -> Callable[[F], F]:
    """
    Decorador para rastrear la duración del scraping de perfiles.
    
    Returns:
        Función decorada
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                status = 'success' if result else 'empty'
                return result
            except Exception as e:
                status = 'error'
                logger.error(f"Error en scraping: {str(e)}", exc_info=True)
                raise
            finally:
                duration = time.time() - start_time
                LINKEDIN_SCRAPE_DURATION.labels(status=status).observe(duration)
                
                logger.info(
                    f"Scraping completado en {duration:.2f}s. "
                    f"Estado: {status}"
                )
        
        return cast(F, wrapper)
    
    return decorator


def start_metrics_server(port: int = 8000) -> None:
    """
    Inicia el servidor de métricas de Prometheus.
    
    Args:
        port: Puerto para el servidor de métricas
    """
    try:
        start_http_server(port)
        logger.info(f"Servidor de métricas iniciado en el puerto {port}")
    except Exception as e:
        logger.error(f"No se pudo iniciar el servidor de métricas: {str(e)}")


# Iniciar el servidor de métricas al importar el módulo
if getattr(settings, 'ENABLE_METRICS', False):
    start_metrics_server(port=getattr(settings, 'METRICS_PORT', 8000))
