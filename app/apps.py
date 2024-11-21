from django.apps import AppConfig
from django.conf import settings
from django.db import connection
import logging
from django.db.utils import OperationalError
from django.core.management import execute_from_command_line


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        """
        Método llamado cuando la aplicación está lista.
        """
        try:
            if settings.DEBUG:
                logger = logging.getLogger(__name__)
                logger.info("El entorno está en modo DEBUG.")
            # Evitar cargar configuraciones si las migraciones están pendientes
            if self._has_pending_migrations():
                logger = logging.getLogger(__name__)
                logger.info("Existen migraciones pendientes. Omitiendo carga de configuraciones dinámicas.")
                return
            self.safe_load_dynamic_settings()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Error al preparar la app: {e}")

    def safe_load_dynamic_settings(self):
        """
        Intenta cargar configuraciones dinámicas de manera segura,
        asegurándose de que las tablas de la base de datos existen.
        """
        required_table = 'app_configuracion'

        if not self._is_table_ready(required_table):
            logger = logging.getLogger(__name__)
            logger.info(f"La tabla {required_table} no está lista. Omitiendo carga de configuraciones dinámicas.")
            return

        try:
            self.load_dynamic_settings()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error al cargar configuraciones dinámicas: {e}")

    def _is_table_ready(self, table_name):
        """
        Verifica si una tabla específica existe en la base de datos.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
                return cursor.fetchone() is not None
        except OperationalError:
            return False
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error al verificar la existencia de la tabla '{table_name}': {e}")
            return False

    def _has_pending_migrations(self):
        """
        Verifica si hay migraciones pendientes.
        """
        try:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            return executor.migration_plan(executor.loader.graph.leaf_nodes())
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error al verificar migraciones pendientes: {e}")
            return True

    def load_dynamic_settings(self):
        """
        Carga configuraciones dinámicas desde la tabla `app_configuracion`.
        """
        from django.apps import apps
        Configuracion = apps.get_model('app', 'Configuracion')

        # Recuperar configuración desde la base de datos
        config = Configuracion.objects.first()
        if config:
            # Asignar valores dinámicos a las configuraciones globales
            settings.SECRET_KEY = config.secret_key
            settings.DEBUG = config.debug_mode
            settings.SENTRY_DSN = config.sentry_dsn
            logger = logging.getLogger(__name__)
            logger.info("Configuraciones dinámicas cargadas correctamente.")
        else:
            logger = logging.getLogger(__name__)
            logger.warning("No se encontró ninguna configuración en la tabla 'app_configuracion'.")