# /home/pablo/app/com/feedback/apps.py
"""
Configuración de la aplicación de feedback para Grupo huntRED®.

Este módulo define la configuración de la aplicación Django para el sistema
integral de retroalimentación, asegurando que todas las señales y componentes
se inicialicen correctamente.
"""

from django.apps import AppConfig


class FeedbackConfig(AppConfig):
    """Configuración para la aplicación de feedback."""
    
    name = 'app.ats.feedback'
    verbose_name = 'Sistema de Retroalimentación'
    
    def ready(self):
        """
        Inicializa componentes del sistema de feedback cuando arranca Django.
        Conecta todas las señales necesarias.
        """
        # Importar señales para asegurar que se registren
        from app.ats.feedback import signals
        
        # Conectar las señales
        signals.connect_feedback_signals()
