"""
Servicio de notificaciones de caché de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class CacheNotificationService(BaseNotificationService):
    """Servicio de notificaciones de caché."""
    
    async def notify_cache_status(
        self,
        cache_name: str,
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de un caché.
        
        Args:
            cache_name: Nombre del caché
            status: Estado del caché
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.CACHE_STATUS.value,
            message="",
            context={
                "cache_name": cache_name,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_cache_health(
        self,
        cache_name: str,
        health_status: str,
        metrics: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la salud de un caché.
        
        Args:
            cache_name: Nombre del caché
            health_status: Estado de salud
            metrics: Métricas del caché
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.CACHE_HEALTH.value,
            message="",
            context={
                "cache_name": cache_name,
                "health_status": health_status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_cache_eviction(
        self,
        cache_name: str,
        eviction_type: str,
        eviction_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una evicción de caché.
        
        Args:
            cache_name: Nombre del caché
            eviction_type: Tipo de evicción
            eviction_details: Detalles de la evicción
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.CACHE_EVICTION.value,
            message="",
            context={
                "cache_name": cache_name,
                "eviction_type": eviction_type,
                "eviction_details": eviction_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_cache_invalidation(
        self,
        cache_name: str,
        invalidation_type: str,
        invalidation_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una invalidación de caché.
        
        Args:
            cache_name: Nombre del caché
            invalidation_type: Tipo de invalidación
            invalidation_details: Detalles de la invalidación
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.CACHE_INVALIDATION.value,
            message="",
            context={
                "cache_name": cache_name,
                "invalidation_type": invalidation_type,
                "invalidation_details": invalidation_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_cache_flush(
        self,
        cache_name: str,
        flush_type: str,
        flush_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un vaciado de caché.
        
        Args:
            cache_name: Nombre del caché
            flush_type: Tipo de vaciado
            flush_details: Detalles del vaciado
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.CACHE_FLUSH.value,
            message="",
            context={
                "cache_name": cache_name,
                "flush_type": flush_type,
                "flush_details": flush_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de caché
cache_notifier = CacheNotificationService(BusinessUnit.objects.first()) 