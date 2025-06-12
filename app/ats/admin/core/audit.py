from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.utils.html import format_html
from django.urls import reverse

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """Administración de Registros de Auditoría"""
    
    list_display = (
        'action_time',
        'user',
        'content_type',
        'object_repr',
        'action_flag',
        'change_message'
    )
    
    list_filter = (
        'action_flag',
        'content_type',
        'action_time'
    )
    
    search_fields = (
        'user__email',
        'object_repr',
        'change_message'
    )
    
    readonly_fields = (
        'action_time',
        'user',
        'content_type',
        'object_id',
        'object_repr',
        'action_flag',
        'change_message'
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def object_link(self, obj):
        """Genera un enlace al objeto modificado"""
        if obj.action_flag == 3:  # DELETE
            return obj.object_repr
        ct = obj.content_type
        try:
            url = reverse(
                f'admin:{ct.app_label}_{ct.model}_change',
                args=[obj.object_id]
            )
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.object_repr
            )
        except:
            return obj.object_repr
    
    object_link.short_description = 'Objeto'
    object_link.admin_order_field = 'object_repr' 