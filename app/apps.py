# /home/pablo/app/apps.py
import os
import logging
from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class AppConfig(DjangoAppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        import app.signals

        # Solo bloquear ejecución en runserver, pero permitir en Celery
        if "runserver" in os.environ.get("DJANGO_RUN_MODE", ""):
            return

        self.register_startup_handlers()

    def _load_dynamic_settings(self, **kwargs):
        cache_key = 'dynamic_settings'
        settings_data = cache.get(cache_key)
        if not settings_data:
            try:
                self._load_settings_from_db()
                cache.set(cache_key, settings_data, timeout=3600)  # 1 hora
            except Exception as e:
                logger.error(f"Error loading dynamic settings: {e}")
                self._set_default_settings()

    def register_startup_handlers(self):
        """
        Registra manejadores de arranque para cargar configuraciones dinámicas
        y tareas periódicas después de aplicar migraciones.
        """
        from django.core.signals import request_started
        from django.db.models.signals import post_migrate

        if settings.DEBUG:
            # Cargar configuraciones dinámicas en la primera solicitud
            request_started.connect(self._load_dynamic_settings, weak=False)

        # Registrar periodic tasks después de las migraciones
        post_migrate.connect(self._setup_periodic_tasks, weak=False)

    def _load_dynamic_settings(self, **kwargs):
        """
        Carga configuraciones dinámicas desde la base de datos en la primera solicitud.
        """
        from django.core.signals import request_started
        request_started.disconnect(self._load_dynamic_settings)
        try:
            self._load_settings_from_db()
        except Exception as e:
            logger.error(f"Error loading dynamic settings: {e}")
            self._set_default_settings()

    def _load_settings_from_db(self):
        """
        Carga la configuración desde el modelo Configuracion.
        """
        from django.apps import apps
        Configuracion = apps.get_model('app', 'Configuracion')
        config = Configuracion.objects.first()
        if config:
            settings.SECRET_KEY = config.secret_key or settings.SECRET_KEY
            settings.DEBUG = config.debug_mode if config.debug_mode is not None else settings.DEBUG
            settings.SENTRY_DSN = config.sentry_dsn or settings.SENTRY_DSN
            logger.info("Dynamic settings loaded successfully")
        else:
            logger.warning("No configuration found in database. Using defaults")
            self._set_default_settings()

    def _set_default_settings(self):
        """
        Asigna valores predeterminados a las configuraciones.
        """
        DEFAULT_SETTINGS = {
            'SECRET_KEY': 'hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48',
            'DEBUG': False,
            'SENTRY_DSN': 'https://94c6575f877d16a00cc74bcaaab5ae79@o4508258791653376.ingest.us.sentry.io/4508258794471424',
        }
        for key, value in DEFAULT_SETTINGS.items():
            if not hasattr(settings, key) or getattr(settings, key) is None:
                setattr(settings, key, value)

    def _setup_periodic_tasks(self, **kwargs):
        """
        Configura las tareas periódicas llamando a la función de Celery.
        """
        try:
            from ai_huntred.celery import setup_periodic_tasks
            setup_periodic_tasks(None)
            logger.info("Periodic tasks registered successfully")
        except Exception as e:
            logger.error(f"Error registering periodic tasks: {e}")