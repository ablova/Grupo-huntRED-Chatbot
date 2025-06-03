""
Configuración de la aplicación de precios.
"""
from django.apps import AppConfig


class PricingConfig(AppConfig):
    """Configuración de la aplicación de precios."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.pricing'
    verbose_name = 'Gestión de Precios y Promociones'
    
    def ready(self):
        # Importar señales para conectar los manejadores
        import app.ats.pricing.signals
