"""
Servicio de notificaciones de base de datos de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class DatabaseNotificationService(BaseNotificationService):
    """Servicio de notificaciones de base de datos."""
    
    async def notify_database_status(
        self,
        database_name: str,
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de una base de datos.
        
        Args:
            database_name: Nombre de la base de datos
            status: Estado de la base de datos
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.DATABASE_STATUS.value,
            message="",
            context={
                "database_name": database_name,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_database_health(
        self,
        database_name: str,
        health_status: str,
        metrics: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la salud de una base de datos.
        
        Args:
            database_name: Nombre de la base de datos
            health_status: Estado de salud
            metrics: Métricas de la base de datos
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.DATABASE_HEALTH.value,
            message="",
            context={
                "database_name": database_name,
                "health_status": health_status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_database_backup(
        self,
        database_name: str,
        backup_type: str,
        backup_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un respaldo de base de datos.
        
        Args:
            database_name: Nombre de la base de datos
            backup_type: Tipo de respaldo
            backup_details: Detalles del respaldo
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.DATABASE_BACKUP.value,
            message="",
            context={
                "database_name": database_name,
                "backup_type": backup_type,
                "backup_details": backup_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_database_restore(
        self,
        database_name: str,
        restore_type: str,
        restore_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una restauración de base de datos.
        
        Args:
            database_name: Nombre de la base de datos
            restore_type: Tipo de restauración
            restore_details: Detalles de la restauración
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.DATABASE_RESTORE.value,
            message="",
            context={
                "database_name": database_name,
                "restore_type": restore_type,
                "restore_details": restore_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_database_migration(
        self,
        database_name: str,
        migration_type: str,
        migration_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una migración de base de datos.
        
        Args:
            database_name: Nombre de la base de datos
            migration_type: Tipo de migración
            migration_details: Detalles de la migración
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.DATABASE_MIGRATION.value,
            message="",
            context={
                "database_name": database_name,
                "migration_type": migration_type,
                "migration_details": migration_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de base de datos
database_notifier = DatabaseNotificationService(BusinessUnit.objects.first()) 