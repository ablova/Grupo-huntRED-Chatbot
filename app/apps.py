# /home/amigro/app/apps.py

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # Conectar señal post_migrate
        post_migrate.connect(load_dynamic_settings, sender=self)

def load_dynamic_settings(sender, **kwargs):
    if getattr(settings, 'TESTING', False):
        return  # Ignorar durante las pruebas

    from app.models import Configuracion
    try:
        config = Configuracion.objects.first()
        if not config:
            raise ImproperlyConfigured("No se encontraron configuraciones en la base de datos.")

        # Establecer configuraciones dinámicas
        settings.SECRET_KEY = config.secret_key
        settings.DEBUG = config.debug_mode
        settings.SENTRY_DSN = config.sentry_dsn

    except ImproperlyConfigured as e:
        raise  # Re-raise the exception to avoid silent failures
    except Exception as e:
        raise ImproperlyConfigured(f"Error al cargar configuraciones desde la base de datos: {e}")