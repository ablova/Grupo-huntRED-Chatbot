from django.apps import AppConfig


class SuccessionPlanningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.com.chatbot.workflow.assessments.succession_planning'
    verbose_name = 'Planeación de Sucesión'
    
    def ready(self):
        # Importar señales para que se registren
        try:
            from . import signals  # noqa F401
        except ImportError:
            pass
