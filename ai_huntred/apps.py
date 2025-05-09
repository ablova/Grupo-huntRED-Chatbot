# /home/pablo/ai_huntred/apps.py
#
# Configuración de la aplicación AI HuntRED.
# Inicializa los componentes y configuraciones necesarios.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

from django.apps import AppConfig

class AiHuntredConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_huntred'
    verbose_name = 'AI HuntRED'

    def ready(self):
        """
        Inicializa el módulo
        """
        # Importar señales
        import app.publish.signals
        
        # Configurar logger
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Registrar procesadores
        from app.publish.processors import register_processors
        register_processors()
        
        # Registrar integraciones
        from app.publish.integrations import register_integrations
        register_integrations()
