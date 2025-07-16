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
        # Importar señales (comentado para evitar error si no existe)
        # import app.payroll.signals
        
        # Registrar tareas de Celery (comentado para evitar error si no existe)
        # from app.payroll.tasks import register_tasks
        # register_tasks()
        
        # Configurar webhooks de WhatsApp usando el MessageService existente
        # from app.ats.integrations.services import MessageService
        # message_service = MessageService()
        # setup_webhooks()  # Comentado hasta implementar si es necesario
    
    def post_migrate(self, sender, **kwargs):
        """Configuración post-migración"""
        from app.payroll.models import create_default_data
        create_default_data() 