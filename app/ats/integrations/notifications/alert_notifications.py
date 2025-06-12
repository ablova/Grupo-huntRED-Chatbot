"""
Módulo para manejar notificaciones específicas de alertas.
Incluye notificaciones para diferentes tipos de alertas y unidades de negocio.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from .system_notifications import system_notifier

logger = logging.getLogger(__name__)

class AlertNotifier:
    """Clase para manejar notificaciones específicas de alertas."""
    
    async def notify_system_alert(self,
                                alert_name: str,
                                alert_type: str,
                                severity: str,
                                business_unit: str,
                                additional_details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Notifica sobre una alerta del sistema.
        
        Args:
            alert_name: Nombre de la alerta
            alert_type: Tipo de alerta
            severity: Severidad de la alerta
            business_unit: Unidad de negocio
            additional_details: Detalles adicionales
        """
        try:
            # Determinar emoji según severidad
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }.get(severity.lower(), "⚪")
            
            # Preparar mensaje de alerta del sistema
            message = (
                f"{severity_emoji} *Alerta del Sistema*\n\n"
                f"📝 *Alerta:* {alert_name}\n"
                f"📋 *Tipo:* {alert_type}\n"
                f"⚠️ *Severidad:* {severity}"
            )
            
            # Agregar detalles adicionales si existen
            if additional_details:
                message += "\n\n*Detalles Adicionales:*\n"
                for key, value in additional_details.items():
                    message += f"• {key}: {value}\n"
            
            return await system_notifier.send_notification(
                message=message,
                notification_type="warning",
                business_unit=business_unit,
                additional_data={
                    "tipo_alerta": alert_type,
                    "severidad": severity,
                    "fecha_alerta": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error en notify_system_alert: {str(e)}")
            return False
            
    async def notify_performance_alert(self,
                                     alert_name: str,
                                     metric_name: str,
                                     current_value: Any,
                                     threshold: Any,
                                     severity: str,
                                     business_unit: str,
                                     additional_details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Notifica sobre una alerta de rendimiento.
        
        Args:
            alert_name: Nombre de la alerta
            metric_name: Nombre de la métrica
            current_value: Valor actual
            threshold: Umbral
            severity: Severidad de la alerta
            business_unit: Unidad de negocio
            additional_details: Detalles adicionales
        """
        try:
            # Determinar emoji según severidad
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }.get(severity.lower(), "⚪")
            
            # Preparar mensaje de alerta de rendimiento
            message = (
                f"{severity_emoji} *Alerta de Rendimiento*\n\n"
                f"📝 *Alerta:* {alert_name}\n"
                f"📊 *Métrica:* {metric_name}\n"
                f"📈 *Valor Actual:* {current_value}\n"
                f"🎯 *Umbral:* {threshold}\n"
                f"⚠️ *Severidad:* {severity}"
            )
            
            # Agregar detalles adicionales si existen
            if additional_details:
                message += "\n\n*Detalles Adicionales:*\n"
                for key, value in additional_details.items():
                    message += f"• {key}: {value}\n"
            
            return await system_notifier.send_notification(
                message=message,
                notification_type="warning",
                business_unit=business_unit,
                additional_data={
                    "tipo_alerta": "performance",
                    "metrica": metric_name,
                    "valor_actual": current_value,
                    "umbral": threshold,
                    "severidad": severity,
                    "fecha_alerta": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error en notify_performance_alert: {str(e)}")
            return False
            
    async def notify_security_alert(self,
                                  alert_name: str,
                                  alert_type: str,
                                  severity: str,
                                  business_unit: str,
                                  additional_details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Notifica sobre una alerta de seguridad.
        
        Args:
            alert_name: Nombre de la alerta
            alert_type: Tipo de alerta
            severity: Severidad de la alerta
            business_unit: Unidad de negocio
            additional_details: Detalles adicionales
        """
        try:
            # Determinar emoji según severidad
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }.get(severity.lower(), "⚪")
            
            # Preparar mensaje de alerta de seguridad
            message = (
                f"{severity_emoji} *Alerta de Seguridad*\n\n"
                f"📝 *Alerta:* {alert_name}\n"
                f"📋 *Tipo:* {alert_type}\n"
                f"⚠️ *Severidad:* {severity}"
            )
            
            # Agregar detalles adicionales si existen
            if additional_details:
                message += "\n\n*Detalles Adicionales:*\n"
                for key, value in additional_details.items():
                    message += f"• {key}: {value}\n"
            
            return await system_notifier.send_notification(
                message=message,
                notification_type="warning",
                business_unit=business_unit,
                additional_data={
                    "tipo_alerta": alert_type,
                    "severidad": severity,
                    "fecha_alerta": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error en notify_security_alert: {str(e)}")
            return False
            
    async def notify_business_alert(self,
                                  alert_name: str,
                                  alert_type: str,
                                  severity: str,
                                  business_unit: str,
                                  company_name: str,
                                  additional_details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Notifica sobre una alerta de negocio.
        
        Args:
            alert_name: Nombre de la alerta
            alert_type: Tipo de alerta
            severity: Severidad de la alerta
            business_unit: Unidad de negocio
            company_name: Nombre de la empresa
            additional_details: Detalles adicionales
        """
        try:
            # Determinar emoji según severidad
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }.get(severity.lower(), "⚪")
            
            # Preparar mensaje de alerta de negocio
            message = (
                f"{severity_emoji} *Alerta de Negocio*\n\n"
                f"📝 *Alerta:* {alert_name}\n"
                f"📋 *Tipo:* {alert_type}\n"
                f"🏢 *Empresa:* {company_name}\n"
                f"⚠️ *Severidad:* {severity}"
            )
            
            # Agregar detalles adicionales si existen
            if additional_details:
                message += "\n\n*Detalles Adicionales:*\n"
                for key, value in additional_details.items():
                    message += f"• {key}: {value}\n"
            
            return await system_notifier.send_notification(
                message=message,
                notification_type="warning",
                business_unit=business_unit,
                additional_data={
                    "tipo_alerta": alert_type,
                    "empresa": company_name,
                    "severidad": severity,
                    "fecha_alerta": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error en notify_business_alert: {str(e)}")
            return False
            
    async def notify_alert_resolution(self,
                                    alert_name: str,
                                    alert_type: str,
                                    resolution: str,
                                    business_unit: str,
                                    additional_details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Notifica sobre la resolución de una alerta.
        
        Args:
            alert_name: Nombre de la alerta
            alert_type: Tipo de alerta
            resolution: Resolución de la alerta
            business_unit: Unidad de negocio
            additional_details: Detalles adicionales
        """
        try:
            # Preparar mensaje de resolución de alerta
            message = (
                f"✅ *Resolución de Alerta*\n\n"
                f"📝 *Alerta:* {alert_name}\n"
                f"📋 *Tipo:* {alert_type}\n"
                f"📋 *Resolución:* {resolution}"
            )
            
            # Agregar detalles adicionales si existen
            if additional_details:
                message += "\n\n*Detalles Adicionales:*\n"
                for key, value in additional_details.items():
                    message += f"• {key}: {value}\n"
            
            return await system_notifier.send_notification(
                message=message,
                notification_type="info",
                business_unit=business_unit,
                additional_data={
                    "tipo_alerta": alert_type,
                    "resolucion": resolution,
                    "fecha_resolucion": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error en notify_alert_resolution: {str(e)}")
            return False

# Instancia global del notificador de alertas
alert_notifier = AlertNotifier() 