from django.apps import AppConfig

class MLCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml.core'
    verbose_name = 'ML Core'
    
    def ready(self):
        # Initialize ML models when Django starts
        from .factory import MLFactory
        MLFactory.initialize()