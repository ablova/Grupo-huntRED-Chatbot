"""
Configuración de la aplicación de Análisis Cultural para Grupo huntRED®.
"""

from django.apps import AppConfig


class CulturalAssessmentConfig(AppConfig):
    """Configuración para el módulo de Análisis Cultural"""
    name = 'app.cultural_assessment'
    verbose_name = 'Análisis Cultural'
    
    def ready(self):
        """
        Importa las señales cuando la aplicación está lista.
        Garantiza que las señales se registren correctamente.
        """
        try:
            import app.ats.cultural_assessment.signals  # noqa
        except ImportError:
            pass
