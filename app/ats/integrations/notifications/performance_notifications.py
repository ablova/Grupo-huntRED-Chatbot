"""
Servicio de notificaciones de rendimiento de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class PerformanceNotificationService(BaseNotificationService):
    """Servicio de notificaciones de rendimiento."""
    
    async def notify_performance_alert(
        self,
        alert_name: str,
        metric_name: str,
        current_value: Any,
        threshold: Any,
        severity: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una alerta de rendimiento.
        
        Args:
            alert_name: Nombre de la alerta
            metric_name: Nombre de la métrica
            current_value: Valor actual
            threshold: Umbral
            severity: Severidad de la alerta
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PERFORMANCE_ALERT.value,
            message="",
            context={
                "alert_name": alert_name,
                "metric_name": metric_name,
                "current_value": current_value,
                "threshold": threshold,
                "severity": severity,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_performance_metrics(
        self,
        metrics: Dict[str, Any],
        period: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre métricas de rendimiento.
        
        Args:
            metrics: Diccionario de métricas
            period: Período de las métricas
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PERFORMANCE_METRICS.value,
            message="",
            context={
                "metrics": metrics,
                "period": period,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_performance_degradation(
        self,
        component: str,
        metric_name: str,
        current_value: Any,
        previous_value: Any,
        threshold: Any,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre degradación de rendimiento.
        
        Args:
            component: Componente afectado
            metric_name: Nombre de la métrica
            current_value: Valor actual
            previous_value: Valor anterior
            threshold: Umbral
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PERFORMANCE_DEGRADATION.value,
            message="",
            context={
                "component": component,
                "metric_name": metric_name,
                "current_value": current_value,
                "previous_value": previous_value,
                "threshold": threshold,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_performance_recovery(
        self,
        component: str,
        metric_name: str,
        current_value: Any,
        previous_value: Any,
        threshold: Any,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre recuperación de rendimiento.
        
        Args:
            component: Componente recuperado
            metric_name: Nombre de la métrica
            current_value: Valor actual
            previous_value: Valor anterior
            threshold: Umbral
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PERFORMANCE_RECOVERY.value,
            message="",
            context={
                "component": component,
                "metric_name": metric_name,
                "current_value": current_value,
                "previous_value": previous_value,
                "threshold": threshold,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_performance_optimization(
        self,
        component: str,
        optimization_type: str,
        improvement: float,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre optimización de rendimiento.
        
        Args:
            component: Componente optimizado
            optimization_type: Tipo de optimización
            improvement: Mejora en porcentaje
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PERFORMANCE_OPTIMIZATION.value,
            message="",
            context={
                "component": component,
                "optimization_type": optimization_type,
                "improvement": improvement,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de rendimiento
performance_notifier = PerformanceNotificationService(BusinessUnit.objects.first()) 