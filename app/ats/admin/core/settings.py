from django.contrib import admin
from django.core.cache import cache
from django.utils.html import format_html
from app.ats.settings.models import SystemSetting, FeatureFlag, IntegrationConfig
from app.ats.models import SystemConfig, NotificationConfig, AIConfig

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    """Administración de Configuraciones del Sistema"""
    
    list_display = (
        'key',
        'value',
        'category',
        'is_active',
        'updated_at'
    )
    
    list_filter = (
        'category',
        'is_active',
        'updated_at'
    )
    
    search_fields = (
        'key',
        'value',
        'description'
    )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Limpiar caché al actualizar configuración
        cache.delete(f'system_setting_{obj.key}')

@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    """Administración de Feature Flags"""
    
    list_display = (
        'name',
        'is_enabled',
        'percentage',
        'created_at',
        'updated_at'
    )
    
    list_filter = (
        'is_enabled',
        'created_at',
        'updated_at'
    )
    
    search_fields = (
        'name',
        'description'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'description',
                'is_enabled'
            )
        }),
        ('Configuración', {
            'fields': (
                'percentage',
                'conditions',
                'expiry_date'
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
                'updated_by'
            )
        })
    )

@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    """Administración de Configuración del Sistema"""
    
    list_display = (
        'key',
        'value',
        'category',
        'is_active',
        'last_updated'
    )
    
    list_filter = (
        'category',
        'is_active',
        'last_updated'
    )
    
    search_fields = (
        'key',
        'value',
        'description'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'key',
                'value',
                'category',
                'is_active'
            )
        }),
        ('Detalles', {
            'fields': (
                'description',
                'data_type',
                'validation_rules'
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_by',
                'last_updated',
                'version'
            )
        })
    )

@admin.register(IntegrationConfig)
class IntegrationConfigAdmin(admin.ModelAdmin):
    """Administración de Configuración de Integraciones"""
    
    list_display = (
        'integration_name',
        'status',
        'api_version',
        'last_sync',
        'health_status'
    )
    
    list_filter = (
        'status',
        'api_version',
        'last_sync'
    )
    
    search_fields = (
        'integration_name',
        'api_key',
        'endpoints'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'integration_name',
                'status',
                'api_version'
            )
        }),
        ('Configuración API', {
            'fields': (
                'api_key',
                'api_secret',
                'endpoints'
            )
        }),
        ('Sincronización', {
            'fields': (
                'sync_frequency',
                'last_sync',
                'next_sync'
            )
        }),
        ('Monitoreo', {
            'fields': (
                'health_status',
                'error_rate',
                'response_time'
            )
        })
    )

@admin.register(NotificationConfig)
class NotificationConfigAdmin(admin.ModelAdmin):
    """Administración de Configuración de Notificaciones"""
    
    list_display = (
        'channel',
        'status',
        'rate_limit',
        'template_count',
        'last_used'
    )
    
    list_filter = (
        'channel',
        'status',
        'last_used'
    )
    
    search_fields = (
        'channel',
        'templates',
        'config'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'channel',
                'status',
                'priority'
            )
        }),
        ('Límites', {
            'fields': (
                'rate_limit',
                'daily_limit',
                'retry_policy'
            )
        }),
        ('Plantillas', {
            'fields': (
                'templates',
                'default_template',
                'variables'
            )
        }),
        ('Métricas', {
            'fields': (
                'success_rate',
                'delivery_time',
                'last_used'
            )
        })
    )

@admin.register(AIConfig)
class AIConfigAdmin(admin.ModelAdmin):
    """Administración de Configuración de IA"""
    
    list_display = (
        'model_name',
        'version',
        'status',
        'accuracy',
        'last_trained'
    )
    
    list_filter = (
        'model_name',
        'version',
        'status',
        'last_trained'
    )
    
    search_fields = (
        'model_name',
        'description',
        'parameters'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'model_name',
                'version',
                'status',
                'description'
            )
        }),
        ('Parámetros', {
            'fields': (
                'parameters',
                'thresholds',
                'constraints'
            )
        }),
        ('Rendimiento', {
            'fields': (
                'accuracy',
                'precision',
                'recall',
                'f1_score'
            )
        }),
        ('Entrenamiento', {
            'fields': (
                'training_data',
                'last_trained',
                'next_training'
            )
        }),
        ('Monitoreo', {
            'fields': (
                'drift_detection',
                'performance_metrics',
                'alerts'
            )
        })
    ) 