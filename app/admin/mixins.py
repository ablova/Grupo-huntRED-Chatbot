# /home/pablo/app/admin/mixins.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.db.models import Q, Count
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from app.ats.admin.config import ADMIN_CONFIG, get_date_ranges
from django.urls import reverse
from typing import List, Dict, Any, Optional
from .config import AdminConfig

class AdminMixin:
    """Mixin base para todos los administradores"""
    
    def get_app_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de la aplicación"""
        app_label = self.model._meta.app_label
        return AdminConfig.get_app_config(app_label)
    
    def get_model_order(self) -> List[str]:
        """Obtiene el orden de los modelos"""
        app_label = self.model._meta.app_label
        return AdminConfig.get_model_order(app_label)

class ExportMixin:
    """Mixin para funcionalidad de exportación"""
    
    def get_export_actions(self) -> List[str]:
        """Retorna las acciones de exportación disponibles"""
        return ['export_as_csv', 'export_as_json', 'export_as_xlsx']
    
    def export_as_csv(self, request, queryset):
        """Exporta los registros seleccionados como CSV"""
        # Implementación de exportación CSV
        pass
    
    def export_as_json(self, request, queryset):
        """Exporta los registros seleccionados como JSON"""
        # Implementación de exportación JSON
        pass
    
    def export_as_xlsx(self, request, queryset):
        """Exporta los registros seleccionados como XLSX"""
        # Implementación de exportación XLSX
        pass

class FilterMixin:
    """Mixin para filtros personalizados"""
    
    def get_custom_filters(self) -> List[Any]:
        """Retorna los filtros personalizados"""
        return []
    
    def get_filter_horizontal(self) -> List[str]:
        """Retorna los campos para filtro horizontal"""
        return []
    
    def get_filter_vertical(self) -> List[str]:
        """Retorna los campos para filtro vertical"""
        return []

class ActionMixin:
    """Mixin para acciones personalizadas"""
    
    def get_custom_actions(self) -> List[str]:
        """Retorna las acciones personalizadas"""
        return []
    
    def get_action_choices(self) -> List[tuple]:
        """Retorna las opciones de acciones"""
        return []

class DisplayMixin:
    """Mixin para personalización de visualización"""
    
    def get_list_display(self) -> List[str]:
        """Retorna los campos a mostrar en la lista"""
        return ['__str__']
    
    def get_list_display_links(self) -> List[str]:
        """Retorna los campos que serán enlaces"""
        return ['__str__']
    
    def get_list_filter(self) -> List[str]:
        """Retorna los filtros de lista"""
        return []
    
    def get_search_fields(self) -> List[str]:
        """Retorna los campos de búsqueda"""
        return []

class PermissionMixin:
    """Mixin para permisos personalizados"""
    
    def has_add_permission(self, request) -> bool:
        """Verifica si el usuario puede agregar"""
        return super().has_add_permission(request)
    
    def has_change_permission(self, request, obj=None) -> bool:
        """Verifica si el usuario puede modificar"""
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None) -> bool:
        """Verifica si el usuario puede eliminar"""
        return super().has_delete_permission(request, obj)
    
    def has_view_permission(self, request, obj=None) -> bool:
        """Verifica si el usuario puede ver"""
        return super().has_view_permission(request, obj)

class AuditMixin:
    """Mixin para auditoría"""
    
    def get_audit_fields(self) -> List[str]:
        """Retorna los campos de auditoría"""
        return ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_readonly_fields(self) -> List[str]:
        """Retorna los campos de solo lectura"""
        return self.get_audit_fields()
    
    def save_model(self, request, obj, form, change):
        """Guarda el modelo con información de auditoría"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

class HistoryMixin:
    """Mixin para historial de cambios"""
    
    def get_history_fields(self) -> List[str]:
        """Retorna los campos a registrar en el historial"""
        return []
    
    def get_history_view(self, request, object_id):
        """Vista del historial de cambios"""
        pass

class ValidationMixin:
    """Mixin para validación personalizada"""
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Retorna las reglas de validación"""
        return {}
    
    def validate_model(self, obj) -> bool:
        """Valida el modelo"""
        return True

class CacheMixin:
    """Mixin para cache"""
    
    def get_cache_key(self, obj) -> str:
        """Retorna la clave de cache para el objeto"""
        return f"{self.model._meta.model_name}:{obj.pk}"
    
    def get_cache_ttl(self) -> int:
        """Retorna el tiempo de vida del cache"""
        return 300  # 5 minutos
    
    def invalidate_cache(self, obj):
        """Invalida el cache del objeto"""
        pass

class EnhancedAdminMixin(admin.ModelAdmin):
    """Mixin que agrega mejoras de performance y UX al admin"""
    
    def get_list_display(self, request):
        """Obtiene los campos a mostrar en la lista"""
        config = ADMIN_CONFIG.get(self.model.__name__)
        if config:
            return config.get('list_display', super().get_list_display(request))
        return super().get_list_display(request)
    
    def get_list_filter(self, request):
        """Obtiene los filtros disponibles"""
        config = ADMIN_CONFIG.get(self.model.__name__)
        if config:
            return config.get('list_filter', super().get_list_filter(request))
        return super().get_list_filter(request)
    
    def get_search_fields(self, request):
        """Obtiene los campos de búsqueda"""
        config = ADMIN_CONFIG.get(self.model.__name__)
        if config:
            return config.get('search_fields', super().get_search_fields(request))
        return super().get_search_fields(request)
    
    def get_queryset(self, request):
        """Optimiza las consultas usando select_related y prefetch_related"""
        qs = super().get_queryset(request)
        config = ADMIN_CONFIG.get(self.model.__name__)
        if config and config.get('list_select_related'):
            qs = qs.select_related(*config['list_select_related'])
        return qs
    
    def get_date_hierarchy(self, request):
        """Obtiene la jerarquía de fechas"""
        config = ADMIN_CONFIG.get(self.model.__name__)
        return config.get('date_hierarchy')
    
    class Media:
        css = {
            'all': ('css/admin-enhancements.css',)
        }
        js = ('js/admin-enhancements.js',)

class DateRangeFilter(admin.SimpleListFilter):
    """Filtro por rango de fechas"""
    title = _('Fecha')
    parameter_name = 'date_range'
    
    def lookups(self, request, model_admin):
        """Devuelve las opciones disponibles"""
        return [
            ('today', _('Hoy')),
            ('this_week', _('Esta semana')),
            ('this_month', _('Este mes')),
            ('last_month', _('Mes pasado'))
        ]
    
    def queryset(self, request, queryset):
        """Aplica el filtro al queryset"""
        if self.value():
            date_ranges = get_date_ranges()
            start_date, end_date = date_ranges[self.value()]
            return queryset.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )
        return queryset

class StatusFilter(admin.SimpleListFilter):
    """Filtro por estado personalizado"""
    title = _('Estado')
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        """Devuelve las opciones disponibles"""
        return [
            ('active', _('Activo')),
            ('inactive', _('Inactivo')),
            ('pending', _('Pendiente')),
            ('completed', _('Completado'))
        ]
    
    def queryset(self, request, queryset):
        """Aplica el filtro al queryset"""
        if self.value():
            return queryset.filter(status=self.value())
        return queryset

class BulkActionsMixin(admin.ModelAdmin):
    """Mixin para acciones en bulk"""
    
    def get_actions(self, request):
        """Agrega acciones en bulk"""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def bulk_change_status(self, request, queryset):
        """Cambia el estado de múltiples registros"""
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        new_status = request.POST.get('new_status')
        if new_status:
            queryset.filter(id__in=selected).update(status=new_status)
            self.message_user(request, f"Estado actualizado para {len(selected)} registros")
    bulk_change_status.short_description = _('Cambiar estado seleccionado')
    
    def bulk_export(self, request, queryset):
        """Exporta múltiples registros"""
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        # Implementar lógica de exportación
        self.message_user(request, f"Exportando {len(selected)} registros")
    bulk_export.short_description = _('Exportar seleccionados')
