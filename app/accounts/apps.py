from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.accounts'
    verbose_name = 'Gestión de Usuarios'

    def ready(self):
        # Importar señales para asegurar que se registren
        import app.accounts.signals  # noqa
