"""
Servicio de notificaciones de usuario de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType
from app.ats.utils.migration_handler import get_safe_notifier

logger = logging.getLogger('notifications')

class UserNotificationService(BaseNotificationService):
    """Servicio de notificaciones de usuario."""
    
    async def notify_user_activity(
        self,
        user_id: str,
        activity_type: str,
        activity_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una actividad de usuario.
        
        Args:
            user_id: ID del usuario
            activity_type: Tipo de actividad
            activity_details: Detalles de la actividad
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.USER_ACTIVITY.value,
            message="",
            context={
                "user_id": user_id,
                "activity_type": activity_type,
                "activity_details": activity_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_user_status(
        self,
        user_id: str,
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de un usuario.
        
        Args:
            user_id: ID del usuario
            status: Estado del usuario
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.USER_STATUS.value,
            message="",
            context={
                "user_id": user_id,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_user_preferences(
        self,
        user_id: str,
        preference_type: str,
        preference_changes: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre cambios en las preferencias de un usuario.
        
        Args:
            user_id: ID del usuario
            preference_type: Tipo de preferencia
            preference_changes: Cambios en las preferencias
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.USER_PREFERENCES.value,
            message="",
            context={
                "user_id": user_id,
                "preference_type": preference_type,
                "preference_changes": preference_changes,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_user_session(
        self,
        user_id: str,
        session_type: str,
        session_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una sesión de usuario.
        
        Args:
            user_id: ID del usuario
            session_type: Tipo de sesión
            session_details: Detalles de la sesión
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.USER_SESSION.value,
            message="",
            context={
                "user_id": user_id,
                "session_type": session_type,
                "session_details": session_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_user_interaction(
        self,
        user_id: str,
        interaction_type: str,
        interaction_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una interacción de usuario.
        
        Args:
            user_id: ID del usuario
            interaction_type: Tipo de interacción
            interaction_details: Detalles de la interacción
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.USER_INTERACTION.value,
            message="",
            context={
                "user_id": user_id,
                "interaction_type": interaction_type,
                "interaction_details": interaction_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de usuario
# Usa MigrationHandler para evitar consultas a la base de datos durante migraciones
def get_user_notifier():
    """Getter seguro que funciona durante migraciones."""
    try:
        from app.models import BusinessUnit
        bu = BusinessUnit.objects.first()
        return get_safe_notifier(UserNotificationService, bu)
    except Exception as e:
        logger.warning(f"Failed to get user notifier: {e}. Using dummy notifier.")
        from app.ats.utils.migration_handler import DummyNotificationService
        return DummyNotificationService()

# Variable global para compatibilidad
user_notifier = None

def _get_user_notifier_global():
    """Getter global que cachea la instancia."""
    global user_notifier
    if user_notifier is None:
        user_notifier = get_user_notifier()
    return user_notifier 