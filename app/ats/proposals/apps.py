from django.apps import AppConfig

class ProposalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.ats.proposals'
    
    def ready(self):
        import app.ats.proposals.signals
