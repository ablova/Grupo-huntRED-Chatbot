from django.apps import AppConfig

class PublishConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.ats.publish'
    verbose_name = 'Publicación y Campañas Digitales'

    def ready(self):
        """
        Inicializa el módulo
        """
        # Importar señales
        import app.ats.publish.signals
