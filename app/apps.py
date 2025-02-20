# /home/pablo/app/apps.py
from django.apps import AppConfig
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        """
        Initialization code that runs when the app is ready.
        Avoids database access during startup.
        """
        import app.signals  # Load signals

        # Only run on main process
        if os.environ.get('RUN_MAIN', None) != 'true':
            return

        # Register startup tasks
        self.register_startup_handlers()

    def register_startup_handlers(self):
        """
        Register handlers to run after Django is fully loaded
        """
        from django.core.signals import request_started
        from django.db.models.signals import post_migrate

        # Register the dynamic settings loader
        if settings.DEBUG:
            request_started.connect(self._load_dynamic_settings, weak=False)

        # Register periodic tasks after migrations
        post_migrate.connect(self._setup_periodic_tasks, weak=False)

    def _load_dynamic_settings(self, **kwargs):
        """
        Load dynamic settings on first request
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
        Load settings from database
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
        Set default settings values
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
        Setup periodic tasks after database is ready
        """
        try:
            from ai_huntred.celery import setup_periodic_tasks
            setup_periodic_tasks(None)
            logger.info("Periodic tasks registered successfully")
        except Exception as e:
            logger.error(f"Error registering periodic tasks: {e}")