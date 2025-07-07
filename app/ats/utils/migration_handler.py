"""
Migration Handler para detectar contexto de migración y evitar ciclos de dependencia.
Resuelve el problema del huevo y la gallina en migraciones de Django.
"""
import sys
import logging
from typing import Optional, Any
from django.db import connection
from django.db.utils import OperationalError
from django.conf import settings

logger = logging.getLogger(__name__)

class MigrationHandler:
    """
    Handler para detectar contexto de migración y proporcionar servicios seguros.
    """
    
    _migration_mode = None
    
    @classmethod
    def is_migration_mode(cls) -> bool:
        """
        Detecta si estamos en modo migración.
        
        Returns:
            bool: True si estamos en proceso de migración
        """
        if cls._migration_mode is not None:
            return cls._migration_mode
            
        # Estrategia 1: Detectar comando migrate
        if 'migrate' in sys.argv:
            cls._migration_mode = True
            logger.info("Migration mode detected: migrate command")
            return True
        
        # Estrategia 2: Verificar si la base de datos está lista
        try:
            connection.ensure_connection()
            # Intentar una consulta simple para verificar que las tablas existen
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            cls._migration_mode = False
            return False
        except (OperationalError, Exception) as e:
            cls._migration_mode = True
            logger.info(f"Migration mode detected: database not ready - {e}")
            return True
    
    @classmethod
    def get_safe_notifier(cls, notifier_class, *args, **kwargs):
        """
        Obtiene un notificador seguro que funciona en modo migración.
        
        Args:
            notifier_class: Clase del notificador a instanciar
            *args, **kwargs: Argumentos para el notificador
            
        Returns:
            notifier_class o DummyNotificationService
        """
        if cls.is_migration_mode():
            logger.debug(f"Using dummy notifier for {notifier_class.__name__} in migration mode")
            return DummyNotificationService()
        
        try:
            return notifier_class(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Failed to create {notifier_class.__name__}: {e}. Using dummy notifier.")
            return DummyNotificationService()

class DummyNotificationService:
    """
    Servicio de notificación dummy que no hace nada.
    Se usa durante migraciones para evitar errores de base de datos.
    """
    
    def __init__(self, *args, **kwargs):
        self.name = "DummyNotificationService"
    
    def __getattr__(self, name):
        """Intercepta cualquier método y devuelve una función dummy."""
        def dummy_method(*args, **kwargs):
            logger.debug(f"Dummy notification service called: {name}")
            return {"success": True, "dummy": True}
        return dummy_method
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Función de conveniencia para uso global
def is_migration_mode() -> bool:
    """Función global para detectar modo migración."""
    return MigrationHandler.is_migration_mode()

def get_safe_notifier(notifier_class, *args, **kwargs):
    """Función global para obtener notificador seguro."""
    return MigrationHandler.get_safe_notifier(notifier_class, *args, **kwargs) 