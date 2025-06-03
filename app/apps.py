# /home/pablo/app/apps.py
import logging
import sys
import os
from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings

logger = logging.getLogger(__name__)

class AppConfig(DjangoAppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # Evitar ejecución en comandos de gestión como migrate, makemigrations, etc.
        if any(arg in sys.argv for arg in ['migrate', 'makemigrations', 'collectstatic']):
            logger.info("Ejecución mínima durante comandos de migración")
            return

        # Importar signals centralizados
        try:
            from app.ats.signals import user_signals, model_signals, system_signals  # noqa
            logger.info("Signals centralizados cargados correctamente")
        except ImportError as e:
            logger.error(f"Error importing signals: {str(e)}")

        # Registrar handlers solo en entornos de ejecución
        if 'runserver' in sys.argv or 'gunicorn' in os.environ.get('SERVER_SOFTWARE', ''):
            try:
                self.register_startup_handlers()
            except Exception as e:
                logger.error(f"Error registering startup handlers: {str(e)}")

    def register_startup_handlers(self):
        from django.core.signals import request_started
        from django.db.models.signals import post_migrate
        
        if settings.DEBUG:
            request_started.connect(self._load_dynamic_settings, weak=False)
        post_migrate.connect(self._setup_periodic_tasks, weak=False)

    def _load_dynamic_settings(self, **kwargs):
        from django.core.signals import request_started
        request_started.disconnect(self._load_dynamic_settings)
        try:
            self._load_settings_from_db()
        except Exception as e:
            logger.error(f"Error loading dynamic settings: {e}")
            self._set_default_settings()

    def _load_settings_from_db(self):
        try:
            from app.models import Configuracion
            config = Configuracion.objects.first()
            if config:
                settings.SECRET_KEY = config.secret_key or settings.SECRET_KEY
                settings.DEBUG = config.debug_mode if config.debug_mode is not None else settings.DEBUG
                settings.SENTRY_DSN = config.sentry_dsn or settings.SENTRY_DSN
                logger.info("Dynamic settings loaded successfully")
            else:
                logger.warning("No configuration found in database. Using defaults")
                self._set_default_settings()
        except Exception as e:
            logger.error(f"Error loading settings from database: {e}")
            self._set_default_settings()

    def _set_default_settings(self):
        DEFAULT_SETTINGS = {
            'SECRET_KEY': settings.SECRET_KEY,
            'DEBUG': settings.DEBUG,
            'SENTRY_DSN': settings.SENTRY_DSN,
        }
        for key, value in DEFAULT_SETTINGS.items():
            if not hasattr(settings, key) or getattr(settings, key) is None:
                setattr(settings, key, value)
                logger.debug(f"Setting {key} set to default value")

    def _setup_periodic_tasks(self, **kwargs):
        try:
            from ai_huntred.celery import app
            from app.ats.tasks.scheduler import setup_periodic_tasks
            app.on_after_configure.connect(setup_periodic_tasks)
            logger.info("Periodic tasks registered successfully")
        except Exception as e:
            logger.error(f"Error registering periodic tasks: {e}")

# Inicialización
logger.info("AppConfig inicializado correctamente")