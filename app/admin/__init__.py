from django.contrib import admin
from app.admin.mixins import AdminMixin
from app.admin.config import AdminConfig
import app.ats.admin

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

# Configuración del admin
admin.site.site_header = AdminConfig.SITE_HEADER
admin.site.site_title = AdminConfig.SITE_TITLE
admin.site.index_title = AdminConfig.INDEX_TITLE
 