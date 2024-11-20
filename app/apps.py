# /home/amigro/app/apps.py

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
import logging


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

#    def ready(self):
#        """
#        Método llamado cuando la aplicación está lista.
#        """
#        self.safe_load_dynamic_settings()

    def safe_load_dynamic_settings(self):
        """
        Intenta cargar configuraciones dinámicas de manera segura,
        asegurándose de que las tablas de la base de datos existen.
        """
        if not self._is_table_ready('app_configuracion'):
            # Tabla 'app_configuracion' no está lista, omitir carga dinámica.
            return

        try:
            self.load_dynamic_settings()
        except Exception as e:
            # Manejar cualquier error durante la carga de configuraciones dinámicas
            logger = logging.getLogger(__name__)
            logger.warning(f"Error al cargar configuraciones dinámicas: {e}")

    def _is_table_ready(self, table_name):
        """
        Verifica si una tabla específica existe en la base de datos.
        """
        try:
            return table_name in connection.introspection.table_names()
        except Exception as e:
            # Capturar y registrar cualquier error al verificar las tablas
            logger = logging.getLogger(__name__)
            logger.warning(f"No se pudo verificar si la tabla '{table_name}' está lista: {e}")
            return False

    def load_dynamic_settings(self):
        """
        Carga configuraciones dinámicas desde la tabla `app_configuracion`.
        """
        from django.apps import apps
        Configuracion = apps.get_model('app', 'Configuracion')

        # Recuperar configuración desde la base de datos
        config = Configuracion.objects.first()
        if config:
            settings.SECRET_KEY = config.secret_key
            settings.DEBUG = config.debug_mode
            settings.SENTRY_DSN = config.sentry_dsn