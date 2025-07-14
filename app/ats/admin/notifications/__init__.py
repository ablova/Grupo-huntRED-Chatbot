from django.contrib import admin
from app.models import Notification, NotificationTemplate, NotificationChannel

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Administración de Notificaciones"""
    
    list_display = (
        'id',
        'notification_type',
        'status',
        'recipient',
        'channel',
        'created_at',
        'sent_at'
    )
    
    list_filter = (
        'notification_type',
        'status',
        'channel',
        'created_at',
        'sent_at'
    )
    
    search_fields = (
        'recipient__email',
        'recipient__nombre',
        'content',
        'notification_type'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'sent_at',
        'error_message'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'notification_type',
                'status',
                'recipient',
                'channel'
            )
        }),
        ('Contenido', {
            'fields': (
                'content',
                'template',
                'metadata'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
                'updated_at',
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
        'channel__channel',
        'is_active',
        'created_at'
    )
    
    search_fields = (
        'name',
        'content',
        'subject'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
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
        }),
        ('Temporal', {
            'fields': (
                'created_at',
                'updated_at'
            )
        })
    )

@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    """Administración de Canales de Notificación"""
    
    list_display = (
        'business_unit',
        'channel',
        'enabled',
        'is_active',
        'priority',
        'created_at'
    )
    
    list_filter = (
        'channel',
        'enabled',
        'is_active',
        'business_unit',
        'created_at'
    )
    
    search_fields = (
        'business_unit__name',
        'channel',
        'config'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'business_unit',
                'channel',
                'enabled',
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
        }),
        ('Temporal', {
            'fields': (
                'created_at',
                'updated_at'
            )
        })
    ) 