from django.contrib import admin
from django.apps import apps
from .mixins import AdminMixin
from .config import AdminConfig

# Importar todos los módulos de administración
from .ats import *
from .notifications import *
from .chatbot import *
from .market import *
from .pricing import *
from .learning import *
from .analytics import *

class HuntREDAdminSite(admin.AdminSite):
    """Sitio de administración personalizado para HuntRED"""
    
    site_header = 'HuntRED Admin'
    site_title = 'HuntRED Administration'
    index_title = 'Administración de HuntRED'
    
    def get_app_list(self, request):
        """
        Retorna una lista ordenada de aplicaciones para el usuario.
        """
        app_list = super().get_app_list(request)
        
        # Ordenar aplicaciones según la configuración
        ordered_apps = AdminConfig.get_ordered_apps()
        app_dict = {app['app_label']: app for app in app_list}
        
        return [app_dict[app_label] for app_label in ordered_apps if app_label in app_dict]

# Instancia personalizada del sitio de administración
admin_site = HuntREDAdminSite(name='admin')

# Registrar modelos automáticamente si no están registrados manualmente
def auto_register_models():
    """Registra automáticamente los modelos que no tienen un admin personalizado"""
    for model in apps.get_models():
        if not model._meta.abstract and not model._meta.proxy:
            try:
                admin_site.register(model)
            except admin.sites.AlreadyRegistered:
                pass

# Ejecutar el registro automático
 