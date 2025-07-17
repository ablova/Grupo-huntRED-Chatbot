from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    verbose_name = 'Autenticación huntRED®'
    
    def ready(self):
        """Inicializar la app de autenticación"""
        try:
            import authentication.signals  # noqa: F401
        except ImportError:
            pass
