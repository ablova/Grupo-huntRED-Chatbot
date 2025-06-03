from django.apps import AppConfig

class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.ats.analytics'
    
    def ready(self):
        import app.ats.analytics.signals
