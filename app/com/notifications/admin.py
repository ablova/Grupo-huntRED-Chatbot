"""
Configuración de administración para el sistema de notificaciones.

Registra los modelos del sistema de notificaciones en el panel de administración de Django.
"""

from django.contrib import admin
from .models import Notification, NotificationPreference

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Administración para el modelo de notificaciones."""
    list_display = ('id', 'title', 'notification_type', 'recipient', 'status', 'created_at')
    list_filter = ('notification_type', 'status', 'business_unit', 'is_verified')
    search_fields = ('title', 'content', 'recipient__nombre', 'recipient__email')
    readonly_fields = ('created_at', 'delivered_at', 'read_at')
    date_hierarchy = 'created_at'
    raw_id_fields = ('recipient', 'sender', 'vacante')
    
    fieldsets = (
        ('Información básica', {
            'fields': ('title', 'content', 'notification_type', 'business_unit')
        }),
        ('Destinatario y relaciones', {
            'fields': ('recipient', 'sender', 'vacante')
        }),
        ('Estado y seguimiento', {
            'fields': ('status', 'created_at', 'scheduled_for', 'delivered_at', 'read_at', 'error_message')
        }),
        ('Verificación', {
            'fields': ('verification_code', 'is_verified')
        }),
        ('Canales', {
            'fields': ('email_data', 'whatsapp_data', 'sms_data', 'telegram_data', 'app_data', 'slack_data'),
            'classes': ('collapse',)
        }),
    )

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Administración para el modelo de preferencias de notificación."""
    list_display = ('user', 'notification_type', 'business_unit', 'email_enabled', 'whatsapp_enabled', 'app_enabled')
    list_filter = ('notification_type', 'business_unit', 'email_enabled', 'whatsapp_enabled', 'app_enabled')
    search_fields = ('user__username', 'user__email')
    
    fieldsets = (
        ('Usuario y contexto', {
            'fields': ('user', 'notification_type', 'business_unit')
        }),
        ('Canales habilitados', {
            'fields': ('email_enabled', 'whatsapp_enabled', 'sms_enabled', 'telegram_enabled', 'app_enabled', 'slack_enabled')
        }),
    )
