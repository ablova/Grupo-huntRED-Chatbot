# app/ats/accounts/apps.py
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.ats.accounts'
    verbose_name = 'Gestión de Usuarios'

    def ready(self):
        # Importar señales para asegurar que se registren
        import app.ats.ats.accounts.signals  # noqa
