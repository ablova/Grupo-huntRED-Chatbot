"""
Servicio de notificaciones de métricas de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class MetricsNotificationService(BaseNotificationService):
    """Servicio de notificaciones de métricas."""
    
    async def notify_metrics(
        self,
        metric_name: str,
        value: Any,
        period: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una métrica.
        
        Args:
            metric_name: Nombre de la métrica
            value: Valor de la métrica
            period: Período de la métrica
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.METRICS.value,
            message="",
            context={
                "metric_name": metric_name,
                "value": value,
                "period": period,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_metrics_batch(
        self,
        metrics: Dict[str, Any],
        period: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un lote de métricas.
        
        Args:
            metrics: Diccionario de métricas
            period: Período de las métricas
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.METRICS_BATCH.value,
            message="",
            context={
                "metrics": metrics,
                "period": period,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_metrics_alert(
        self,
        metric_name: str,
        current_value: Any,
        threshold: Any,
        severity: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una alerta de métrica.
        
        Args:
            metric_name: Nombre de la métrica
            current_value: Valor actual
            threshold: Umbral
            severity: Severidad de la alerta
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.METRICS_ALERT.value,
            message="",
            context={
                "metric_name": metric_name,
                "current_value": current_value,
                "threshold": threshold,
                "severity": severity,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_metrics_trend(
        self,
        metric_name: str,
        current_value: Any,
        previous_value: Any,
        trend: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una tendencia de métrica.
        
        Args:
            metric_name: Nombre de la métrica
            current_value: Valor actual
            previous_value: Valor anterior
            trend: Tendencia (up, down, stable)
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.METRICS_TREND.value,
            message="",
            context={
                "metric_name": metric_name,
                "current_value": current_value,
                "previous_value": previous_value,
                "trend": trend,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_metrics_report(
        self,
        report_name: str,
        metrics: Dict[str, Any],
        period: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un reporte de métricas.
        
        Args:
            report_name: Nombre del reporte
            metrics: Diccionario de métricas
            period: Período del reporte
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.METRICS_REPORT.value,
            message="",
            context={
                "report_name": report_name,
                "metrics": metrics,
                "period": period,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de métricas
metrics_notifier = MetricsNotificationService(BusinessUnit.objects.first()) 