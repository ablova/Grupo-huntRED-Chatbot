"""
Configuración de la aplicación de nómina huntRED®
"""
from django.apps import AppConfig
from django.db.models.signals import post_migrate


class PayrollConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.payroll'
    verbose_name = 'Sistema de Nómina huntRED®'
    
    def ready(self):
        """Inicialización de la aplicación"""
        # Importar señales
        import app.payroll.signals
        
        # Registrar tareas de Celery
        from app.payroll.tasks import register_tasks
        register_tasks()
        
        # Configurar webhooks de WhatsApp
        from app.payroll.services.whatsapp_service import setup_webhooks
        setup_webhooks()
    
    def post_migrate(self, sender, **kwargs):
        """Configuración post-migración"""
        from app.payroll.models import create_default_data
        create_default_data() 