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
"""
Sistema de monitoreo para la aplicación

Este módulo proporciona funcionalidad para monitorear el estado
de la aplicación, incluyendo colas, tareas, rendimiento y alertas.
"""

import logging
import psutil
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from celery import Celery
from django.core.cache import cache
from django.conf import settings
from app.tasks import with_retry
from celery import shared_task

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Monitor del sistema"""
    
    def __init__(self):
        """Inicializa el monitor"""
        self.celery = Celery('app')
        self.celery.config_from_object('django.conf:settings', namespace='CELERY')
        
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de las colas
        
        Returns:
            Dict con estadísticas de colas
        """
        try:
            inspector = self.celery.control.inspect()
            active = inspector.active() or {}
            reserved = inspector.reserved() or {}
            scheduled = inspector.scheduled() or {}
            
            return {
                'active': {q: len(tasks) for q, tasks in active.items()},
                'reserved': {q: len(tasks) for q, tasks in reserved.items()},
                'scheduled': {q: len(tasks) for q, tasks in scheduled.items()}
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de colas: {str(e)}")
            return {}
            
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema
        
        Returns:
            Dict con estadísticas del sistema
        """
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': psutil.getloadavg()
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del sistema: {str(e)}")
            return {}
            
    def get_task_stats(self, task_name: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de una tarea específica
        
        Args:
            task_name: Nombre de la tarea
            
        Returns:
            Dict con estadísticas de la tarea
        """
        try:
            inspector = self.celery.control.inspect()
            stats = inspector.stats() or {}
            
            task_stats = {}
            for worker, worker_stats in stats.items():
                if 'total' in worker_stats:
                    task_stats[worker] = worker_stats['total'].get(task_name, 0)
                    
            return task_stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de tarea: {str(e)}")
            return {}
            
    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Verifica condiciones de alerta
        
        Returns:
            Lista de alertas activas
        """
        alerts = []
        
        # Verificar uso de CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 80:
            alerts.append({
                'type': 'cpu_high',
                'message': f'Uso de CPU alto: {cpu_percent}%',
                'severity': 'warning'
            })
            
        # Verificar uso de memoria
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > 80:
            alerts.append({
                'type': 'memory_high',
                'message': f'Uso de memoria alto: {memory_percent}%',
                'severity': 'warning'
            })
            
        # Verificar colas
        queue_stats = self.get_queue_stats()
        for queue, tasks in queue_stats.get('active', {}).items():
            if tasks > 100:
                alerts.append({
                    'type': 'queue_size',
                    'message': f'Cola {queue} con {tasks} tareas activas',
                    'severity': 'info'
                })
                
        return alerts

@shared_task(bind=True, max_retries=3, queue='monitoring')
@with_retry
def monitor_system(self):
    """
    Tarea periódica para monitorear el sistema
    """
    try:
        monitor = SystemMonitor()
        
        # Obtener estadísticas
        queue_stats = monitor.get_queue_stats()
        system_stats = monitor.get_system_stats()
        alerts = monitor.check_alerts()
        
        # Guardar en caché
        cache.set('system_stats', {
            'timestamp': datetime.now().isoformat(),
            'queues': queue_stats,
            'system': system_stats,
            'alerts': alerts
        }, timeout=300)  # 5 minutos
        
        # Procesar alertas
        for alert in alerts:
            if alert['severity'] in ['warning', 'error']:
                logger.warning(f"Alerta del sistema: {alert['message']}")
                
    except Exception as e:
        logger.error(f"Error en monitoreo del sistema: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, queue='monitoring')
@with_retry
def monitor_tasks(self):
    """
    Tarea periódica para monitorear tareas específicas
    """
    try:
        monitor = SystemMonitor()
        
        # Monitorear tareas críticas
        critical_tasks = [
            'process_gamification_event',
            'update_user_level',
            'check_achievements',
            'process_rewards'
        ]
        
        task_stats = {}
        for task in critical_tasks:
            task_stats[task] = monitor.get_task_stats(task)
            
        # Guardar en caché
        cache.set('task_stats', {
            'timestamp': datetime.now().isoformat(),
            'tasks': task_stats
        }, timeout=300)  # 5 minutos
        
    except Exception as e:
        logger.error(f"Error en monitoreo de tareas: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, queue='monitoring')
@with_retry
def cleanup_monitoring_data(self):
    """
    Tarea periódica para limpiar datos antiguos de monitoreo
    """
    try:
        # Limpiar caché antigua
        cache.delete_pattern('monitoring:*')
        logger.info("Datos de monitoreo limpiados")
        
    except Exception as e:
        logger.error(f"Error limpiando datos de monitoreo: {str(e)}")
        raise self.retry(exc=e) 