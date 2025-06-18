# app/ats/integrations/notifications/process_notifications.py   
"""
Servicio de notificaciones de procesos de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit, Vacante as Process
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

# ---------------------------------------------------------------------------
# Backward-compatibility: mantener el nombre `ProcessNotificationManager` que
# algunos módulos (p.ej. `app.ats.tasks`) esperan encontrar en este paquete.
# Reexportamos la clase real desde `process.manager` sin instanciarla.
# ---------------------------------------------------------------------------
from app.ats.integrations.notifications.process.manager import (
    ProcessNotificationManager as _ProcessNotificationManager,
)
# Alias público
ProcessNotificationManager = _ProcessNotificationManager

logger = logging.getLogger('notifications')

class ProcessNotificationService(BaseNotificationService):
    """Servicio de notificaciones de procesos."""
    
    async def notify_process_start(
        self,
        process: Process,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el inicio de un proceso.
        
        Args:
            process: Objeto Process
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PROCESS_START.value,
            message="",
            context={
                "process_name": process.name,
                "process_type": process.process_type,
                "start_date": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_process_completion(
        self,
        process: Process,
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la finalización de un proceso.
        
        Args:
            process: Objeto Process
            status: Estado del proceso
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PROCESS_COMPLETION.value,
            message="",
            context={
                "process_name": process.name,
                "process_type": process.process_type,
                "status": status,
                "completion_date": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_process_error(
        self,
        process: Process,
        error_message: str,
        error_type: str,
        stack_trace: Optional[str] = None,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un error en un proceso.
        
        Args:
            process: Objeto Process
            error_message: Mensaje de error
            error_type: Tipo de error
            stack_trace: Traza del error
            additional_details: Detalles adicionales
        """
        context = {
            "process_name": process.name,
            "process_type": process.process_type,
            "error_type": error_type,
            "error_message": error_message
        }
        
        if stack_trace:
            context["stack_trace"] = stack_trace
        
        return await self.send_notification(
            notification_type=NotificationType.PROCESS_ERROR.value,
            message="",
            context=context,
            additional_data=additional_details
        )
    
    async def notify_process_warning(
        self,
        process: Process,
        warning_message: str,
        warning_type: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una advertencia en un proceso.
        
        Args:
            process: Objeto Process
            warning_message: Mensaje de advertencia
            warning_type: Tipo de advertencia
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PROCESS_WARNING.value,
            message="",
            context={
                "process_name": process.name,
                "process_type": process.process_type,
                "warning_type": warning_type,
                "warning_message": warning_message
            },
            additional_data=additional_details
        )
    
    async def notify_process_progress(
        self,
        process: Process,
        progress: float,
        stage: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el progreso de un proceso.
        
        Args:
            process: Objeto Process
            progress: Progreso (0-100)
            stage: Etapa actual
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PROCESS_PROGRESS.value,
            message="",
            context={
                "process_name": process.name,
                "process_type": process.process_type,
                "progress": progress,
                "stage": stage
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de procesos.
# Para evitar errores durante comandos de migración (la tabla aún no existe),
# atrapamos excepciones de base de datos y diferimos la creación.
from django.db.utils import OperationalError, ProgrammingError

try:
    process_notifier = ProcessNotificationService(BusinessUnit.objects.first())
except (OperationalError, ProgrammingError):
    # La base de datos todavía no está lista; se inicializará en tiempo de ejecución.
    process_notifier = None 