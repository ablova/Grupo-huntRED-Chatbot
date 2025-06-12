# /home/pablo/ai_huntred/apps.py
#
# Configuración de la aplicación AI HuntRED.
# Inicializa los componentes y configuraciones necesarios.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

import logging
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

class AiHuntredConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_huntred'
    verbose_name = 'Grupo huntRED AI'

    def ready(self):
        """
        Inicializa el módulo con manejo de errores y configuración robusta
        """
        try:
            # Importar señales
            import app.ats.publish.signals
            
            # Configurar logger
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Registrar procesadores
            from app.ats.publish.processors import register_processors
            register_processors()
            
            # Registrar integraciones
            from app.ats.publish.integrations import register_integrations
            register_integrations()

            # Configurar Celery
            from ai_huntred.celery_app import app as celery_app
            celery_app.autodiscover_tasks(['app.ats.tasks'])

            logger.info("AI HuntRED initialized successfully")
            
        except ImportError as e:
            logger.error(f"Error importing required modules: {e}")
            raise ImproperlyConfigured(f"Required module not found: {e}")
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            raise ImproperlyConfigured(f"Initialization failed: {e}")
