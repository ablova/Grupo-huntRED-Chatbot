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
from app.ats.tasks.base import with_retry
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