"""
Configuración de la aplicación de precios.
"""
from django.apps import AppConfig


class PricingConfig(AppConfig):
    """Configuración de la aplicación de precios."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.ats.pricing'
    verbose_name = 'Gestión de Precios y Promociones'
    
    def ready(self):
        # Las señales se importan de forma lazy para evitar importaciones circulares
        pass
