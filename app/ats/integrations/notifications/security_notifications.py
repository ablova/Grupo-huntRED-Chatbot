"""
Servicio de notificaciones de seguridad de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class SecurityNotificationService(BaseNotificationService):
    """Servicio de notificaciones de seguridad."""
    
    async def notify_security_alert(
        self,
        alert_name: str,
        alert_type: str,
        severity: str,
        affected_systems: List[str],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una alerta de seguridad.
        
        Args:
            alert_name: Nombre de la alerta
            alert_type: Tipo de alerta
            severity: Severidad de la alerta
            affected_systems: Sistemas afectados
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SECURITY_ALERT.value,
            message="",
            context={
                "alert_name": alert_name,
                "alert_type": alert_type,
                "severity": severity,
                "affected_systems": affected_systems,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_security_breach(
        self,
        breach_type: str,
        affected_systems: List[str],
        severity: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una violación de seguridad.
        
        Args:
            breach_type: Tipo de violación
            affected_systems: Sistemas afectados
            severity: Severidad de la violación
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SECURITY_BREACH.value,
            message="",
            context={
                "breach_type": breach_type,
                "affected_systems": affected_systems,
                "severity": severity,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_security_incident(
        self,
        incident_name: str,
        incident_type: str,
        severity: str,
        affected_systems: List[str],
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un incidente de seguridad.
        
        Args:
            incident_name: Nombre del incidente
            incident_type: Tipo de incidente
            severity: Severidad del incidente
            affected_systems: Sistemas afectados
            status: Estado del incidente
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SECURITY_INCIDENT.value,
            message="",
            context={
                "incident_name": incident_name,
                "incident_type": incident_type,
                "severity": severity,
                "affected_systems": affected_systems,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_security_vulnerability(
        self,
        vulnerability_name: str,
        vulnerability_type: str,
        severity: str,
        affected_systems: List[str],
        cve_id: Optional[str] = None,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una vulnerabilidad de seguridad.
        
        Args:
            vulnerability_name: Nombre de la vulnerabilidad
            vulnerability_type: Tipo de vulnerabilidad
            severity: Severidad de la vulnerabilidad
            affected_systems: Sistemas afectados
            cve_id: ID de CVE (opcional)
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SECURITY_VULNERABILITY.value,
            message="",
            context={
                "vulnerability_name": vulnerability_name,
                "vulnerability_type": vulnerability_type,
                "severity": severity,
                "affected_systems": affected_systems,
                "cve_id": cve_id,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_security_patch(
        self,
        patch_name: str,
        patch_type: str,
        affected_systems: List[str],
        patch_version: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un parche de seguridad.
        
        Args:
            patch_name: Nombre del parche
            patch_type: Tipo de parche
            affected_systems: Sistemas afectados
            patch_version: Versión del parche
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SECURITY_PATCH.value,
            message="",
            context={
                "patch_name": patch_name,
                "patch_type": patch_type,
                "affected_systems": affected_systems,
                "patch_version": patch_version,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_security_scan(
        self,
        scan_name: str,
        scan_type: str,
        scan_results: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un escaneo de seguridad.
        
        Args:
            scan_name: Nombre del escaneo
            scan_type: Tipo de escaneo
            scan_results: Resultados del escaneo
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SECURITY_SCAN.value,
            message="",
            context={
                "scan_name": scan_name,
                "scan_type": scan_type,
                "scan_results": scan_results,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de seguridad
security_notifier = SecurityNotificationService(BusinessUnit.objects.first()) 