from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.db.models import Q, Count
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .config import ADMIN_CONFIG, get_date_ranges

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
