from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class IntegrationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.ats.integrations'
    verbose_name = _('Integraciones')

    def ready(self):
        """
        Se ejecuta cuando la aplicación está lista
        """
        try:
            # Importar señales
            from . import signals
        except ImportError:
            pass 