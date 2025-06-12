from django.contrib import admin
from app.ats.integrations.notifications.models import Notification, NotificationTemplate, NotificationChannel

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Administración de Notificaciones"""
    
    list_display = (
        'id',
        'type',
        'status',
        'recipient',
        'created_at',
        'sent_at'
    )
    
    list_filter = (
        'type',
        'status',
        'created_at',
        'sent_at'
    )
    
    search_fields = (
        'recipient__email',
        'content',
        'type'
    )
    
    readonly_fields = (
        'created_at',
        'sent_at',
        'error_message'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'type',
                'status',
                'recipient'
            )
        }),
        ('Contenido', {
            'fields': (
                'content',
                'template'
            )
        }),
        ('Canal', {
            'fields': (
                'channel',
                'channel_data'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
                'sent_at'
            )
        }),
        ('Errores', {
            'fields': (
                'error_message',
                'retry_count'
            )
        })
    )

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Administración de Plantillas de Notificación"""
    
    list_display = (
        'name',
        'type',
        'channel',
        'is_active',
        'created_at'
    )
    
    list_filter = (
        'type',
        'channel',
        'is_active'
    )
    
    search_fields = (
        'name',
        'content'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'type',
                'channel',
                'is_active'
            )
        }),
        ('Contenido', {
            'fields': (
                'subject',
                'content',
                'variables'
            )
        })
    )

@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    """Administración de Canales de Notificación"""
    
    list_display = (
        'name',
        'type',
        'is_active',
        'priority'
    )
    
    list_filter = (
        'type',
        'is_active'
    )
    
    search_fields = (
        'name',
        'config'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'type',
                'is_active',
                'priority'
            )
        }),
        ('Configuración', {
            'fields': (
                'config',
                'rate_limit',
                'retry_policy'
            )
        })
    ) 