# /home/amigro/app/apps.py
import logging
from django.apps import AppConfig
from django.conf import settings
from django.db import connection
from django.core.signals import request_started


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        """
        Configura la señal para cargar configuraciones dinámicas después de que la aplicación esté completamente inicializada.
        """
        import app.signals
        if not settings.DEBUG:
            return

        # Conectar la señal para cargar configuraciones dinámicas
        request_started.connect(self.load_dynamic_settings_on_request)

    def load_dynamic_settings_on_request(self, **kwargs):
        """
        Carga configuraciones dinámicas cuando se recibe la primera solicitud.
        """
        # Desconecta el receptor para evitar múltiples ejecuciones
        request_started.disconnect(self.load_dynamic_settings_on_request)

        logger = logging.getLogger(__name__)
        try:
            from django.apps import apps
            Configuracion = apps.get_model('app', 'Configuracion')

            # Valores predeterminados
            default_settings = {
                'SECRET_KEY': 'hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48',
                'DEBUG': False,
                'SENTRY_DSN': 'https://94c6575f877d16a00cc74bcaaab5ae79@o4508258791653376.ingest.us.sentry.io/4508258794471424',
            }

            # Recuperar configuración desde la base de datos
            config = Configuracion.objects.first()
            if config:
                settings.SECRET_KEY = config.secret_key or default_settings['SECRET_KEY']
                settings.DEBUG = config.debug_mode if config.debug_mode is not None else default_settings['DEBUG']
                settings.SENTRY_DSN = config.sentry_dsn or default_settings['SENTRY_DSN']
                logger.info("Configuraciones dinámicas cargadas correctamente.")
            else:
                # Usar valores predeterminados si no hay configuración en la base de datos
                self._set_default_settings(default_settings)
                logger.warning("No se encontró ninguna configuración. Usando valores por defecto.")

        except Exception as e:
            logger.error(f"Error al cargar configuraciones dinámicas: {e}")
            # En caso de error, usar configuraciones predeterminadas
            self._set_default_settings({
                'SECRET_KEY': 'hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48',
                'DEBUG': False,
                'SENTRY_DSN': 'https://94c6575f877d16a00cc74bcaaab5ae79@o4508258791653376.ingest.us.sentry.io/4508258794471424',
            })

    def _set_default_settings(self, default_settings):
        """
        Asigna configuraciones predeterminadas al entorno.
        """
        settings.SECRET_KEY = default_settings['SECRET_KEY']
        settings.DEBUG = default_settings['DEBUG']
        settings.SENTRY_DSN = default_settings['SENTRY_DSN']