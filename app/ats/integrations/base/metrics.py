"""
Clase para manejar métricas de canales

Esta clase proporciona funcionalidad para registrar y obtener métricas
de rendimiento de los canales de integración.
"""

from typing import Dict, Any
from datetime import datetime
import time
from django.core.cache import cache
from django.conf import settings

class ChannelMetrics:
    """Clase para manejar métricas de canales"""
    
    def __init__(self, channel_name: str):
        """
        Inicializa el manejador de métricas
        
        Args:
            channel_name: Nombre del canal
        """
        self.channel_name = channel_name
        self.cache_prefix = f"channel_metrics_{channel_name}"
        self.metrics_ttl = getattr(settings, 'CHANNEL_METRICS_TTL', 3600)  # 1 hora por defecto
        
    def record_success(self, duration: float, message_size: int):
        """
        Registra una publicación exitosa
        
        Args:
            duration: Duración de la operación en segundos
            message_size: Tamaño del mensaje en bytes
        """
        metrics = self._get_metrics()
        
        # Actualizar contadores
        metrics['total_messages'] += 1
        metrics['successful_messages'] += 1
        metrics['total_duration'] += duration
        metrics['total_message_size'] += message_size
        
        # Actualizar promedios
        metrics['avg_duration'] = metrics['total_duration'] / metrics['successful_messages']
        metrics['avg_message_size'] = metrics['total_message_size'] / metrics['successful_messages']
        
        # Actualizar último éxito
        metrics['last_success'] = datetime.now().isoformat()
        
        self._save_metrics(metrics)
        
    def record_error(self, error_type: str, duration: float):
        """
        Registra un error en la publicación
        
        Args:
            error_type: Tipo de error
            duration: Duración de la operación en segundos
        """
        metrics = self._get_metrics()
        
        # Actualizar contadores
        metrics['total_messages'] += 1
        metrics['failed_messages'] += 1
        metrics['total_duration'] += duration
        
        # Actualizar errores por tipo
        if error_type not in metrics['errors_by_type']:
            metrics['errors_by_type'][error_type] = 0
        metrics['errors_by_type'][error_type] += 1
        
        # Actualizar último error
        metrics['last_error'] = {
            'type': error_type,
            'timestamp': datetime.now().isoformat()
        }
        
        self._save_metrics(metrics)
        
    def record_webhook_success(self, duration: float, payload_size: int):
        """
        Registra un webhook exitoso
        
        Args:
            duration: Duración de la operación en segundos
            payload_size: Tamaño del payload en bytes
        """
        metrics = self._get_metrics()
        
        # Actualizar contadores
        metrics['total_webhooks'] += 1
        metrics['successful_webhooks'] += 1
        metrics['total_webhook_duration'] += duration
        metrics['total_webhook_size'] += payload_size
        
        # Actualizar promedios
        metrics['avg_webhook_duration'] = metrics['total_webhook_duration'] / metrics['successful_webhooks']
        metrics['avg_webhook_size'] = metrics['total_webhook_size'] / metrics['successful_webhooks']
        
        # Actualizar último webhook exitoso
        metrics['last_webhook_success'] = datetime.now().isoformat()
        
        self._save_metrics(metrics)
        
    def record_webhook_error(self, error_type: str, duration: float):
        """
        Registra un error en el webhook
        
        Args:
            error_type: Tipo de error
            duration: Duración de la operación en segundos
        """
        metrics = self._get_metrics()
        
        # Actualizar contadores
        metrics['total_webhooks'] += 1
        metrics['failed_webhooks'] += 1
        metrics['total_webhook_duration'] += duration
        
        # Actualizar errores por tipo
        if error_type not in metrics['webhook_errors_by_type']:
            metrics['webhook_errors_by_type'][error_type] = 0
        metrics['webhook_errors_by_type'][error_type] += 1
        
        # Actualizar último error de webhook
        metrics['last_webhook_error'] = {
            'type': error_type,
            'timestamp': datetime.now().isoformat()
        }
        
        self._save_metrics(metrics)
        
    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene todas las métricas del canal
        
        Returns:
            Dict con las métricas del canal
        """
        metrics = self._get_metrics()
        
        # Calcular tasas de éxito/error
        if metrics['total_messages'] > 0:
            metrics['success_rate'] = (metrics['successful_messages'] / metrics['total_messages']) * 100
            metrics['error_rate'] = (metrics['failed_messages'] / metrics['total_messages']) * 100
        else:
            metrics['success_rate'] = 0
            metrics['error_rate'] = 0
            
        if metrics['total_webhooks'] > 0:
            metrics['webhook_success_rate'] = (metrics['successful_webhooks'] / metrics['total_webhooks']) * 100
            metrics['webhook_error_rate'] = (metrics['failed_webhooks'] / metrics['total_webhooks']) * 100
        else:
            metrics['webhook_success_rate'] = 0
            metrics['webhook_error_rate'] = 0
            
        return metrics
        
    def _get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene las métricas desde caché o inicializa nuevas
        
        Returns:
            Dict con las métricas
        """
        metrics = cache.get(self.cache_prefix)
        
        if not metrics:
            metrics = {
                'total_messages': 0,
                'successful_messages': 0,
                'failed_messages': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'total_message_size': 0,
                'avg_message_size': 0,
                'errors_by_type': {},
                'last_success': None,
                'last_error': None,
                'total_webhooks': 0,
                'successful_webhooks': 0,
                'failed_webhooks': 0,
                'total_webhook_duration': 0,
                'avg_webhook_duration': 0,
                'total_webhook_size': 0,
                'avg_webhook_size': 0,
                'webhook_errors_by_type': {},
                'last_webhook_success': None,
                'last_webhook_error': None
            }
            
        return metrics
        
    def _save_metrics(self, metrics: Dict[str, Any]):
        """
        Guarda las métricas en caché
        
        Args:
            metrics: Métricas a guardar
        """
        cache.set(self.cache_prefix, metrics, timeout=self.metrics_ttl)
        
    def reset_metrics(self):
        """Reinicia todas las métricas"""
        cache.delete(self.cache_prefix) 