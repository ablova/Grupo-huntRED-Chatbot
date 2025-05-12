# Ubicación del archivo: /home/pablo/app/config/admin_base.py
"""
Módulo base para configuraciones de administración de Django.

Este módulo contiene clases base y mixins reutilizables para las diferentes
configuraciones de administración en el sistema, siguiendo las reglas globales
de Grupo huntRED®.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Clases base para administración
class TokenMaskingMixin:
    """Mixin para enmascarar campos sensibles en el admin"""
    token_fields = []
    visible_prefix_length = 6
    visible_suffix_length = 4

    def get_masked_value(self, value):
        """Enmascarando valores sensibles manteniendo prefijo y sufijo visibles"""
        if not value:
            return "-"
        if len(value) <= (self.visible_prefix_length + self.visible_suffix_length):
            return "..." + value[-self.visible_suffix_length:]
        return f"{value[:self.visible_prefix_length]}...{value[-self.visible_suffix_length:]}"

    def get_list_display(self, request):
        """Sobreescribiendo list_display para incluir métodos de enmascaramiento"""
        list_display = super().get_list_display(request)
        if isinstance(list_display, tuple):
            list_display = list(list_display)
            
        for field in self.token_fields:
            if field in list_display:
                mask_method_name = f'get_masked_{field}'
                if not hasattr(self, mask_method_name):
                    setattr(self, mask_method_name, 
                           lambda obj, field=field: self.get_masked_value(getattr(obj, field)))
                    getattr(self, mask_method_name).short_description = field.replace('_', ' ').title()
                list_display[list_display.index(field)] = mask_method_name
                
        return list_display

class ReadOnlyAdminMixin:
    """Mixin para agregar comportamiento de solo lectura a un ModelAdmin"""
    
    def has_add_permission(self, request):
        """Deshabilitando permiso de añadir registros"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Deshabilitando permiso de modificar registros"""
        return False
        
    def has_delete_permission(self, request, obj=None):
        """Deshabilitando permiso de eliminar registros"""
        return False

class BaseModelAdmin(admin.ModelAdmin):
    """Clase base para todos los ModelAdmin con comportamiento común"""
    
    # Campos automáticos que normalmente son de solo lectura
    default_readonly_fields = ('created_at', 'updated_at', 'last_updated')
    
    def get_readonly_fields(self, request, obj=None):
        """Agregando campos automáticos a readonly_fields"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        for field in self.default_readonly_fields:
            if hasattr(self.model, field.replace('_', ' ')) or field in [f.name for f in self.model._meta.fields]:
                if field not in readonly_fields:
                    readonly_fields.append(field)
        return readonly_fields
    
    class Media:
        """Definiendo recursos estáticos comunes para todas las páginas de administrador"""
        css = {
            'all': ('css/admin.css',)
        }
        js = ('js/admin.js',)
