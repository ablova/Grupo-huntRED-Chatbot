from django.apps import AppConfig

class ReferralsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.referrals'
    verbose_name = 'Programa de Referidos'

    def ready(self):
        try:
            import app.ats.referrals.signals  # noqa
        except ImportError:
            pass 