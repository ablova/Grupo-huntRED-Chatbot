from django.contrib import admin
from app.ats.analytics.models import AnalyticsEvent, UserMetric, SystemMetric, Report

@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    """Administración de Eventos Analíticos"""
    
    list_display = (
        'event_type',
        'user',
        'timestamp',
        'source',
        'value'
    )
    
    list_filter = (
        'event_type',
        'source',
        'timestamp'
    )
    
    search_fields = (
        'user__email',
        'event_type',
        'metadata'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'event_type',
                'user',
                'timestamp',
                'source'
            )
        }),
        ('Datos', {
            'fields': (
                'value',
                'metadata',
                'context'
            )
        })
    )

@admin.register(UserMetric)
class UserMetricAdmin(admin.ModelAdmin):
    """Administración de Métricas de Usuario"""
    
    list_display = (
        'user',
        'metric_type',
        'value',
        'period',
        'updated_at'
    )
    
    list_filter = (
        'metric_type',
        'period',
        'updated_at'
    )
    
    search_fields = (
        'user__email',
        'metric_type'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'user',
                'metric_type',
                'value',
                'period'
            )
        }),
        ('Tendencias', {
            'fields': (
                'trend',
                'comparison',
                'target'
            )
        }),
        ('Análisis', {
            'fields': (
                'insights',
                'recommendations'
            )
        })
    )

@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    """Administración de Métricas del Sistema"""
    
    list_display = (
        'metric_type',
        'value',
        'period',
        'updated_at'
    )
    
    list_filter = (
        'metric_type',
        'period',
        'updated_at'
    )
    
    search_fields = (
        'metric_type',
        'description'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'metric_type',
                'value',
                'period',
                'description'
            )
        }),
        ('Tendencias', {
            'fields': (
                'trend',
                'comparison',
                'target'
            )
        }),
        ('Análisis', {
            'fields': (
                'insights',
                'recommendations',
                'alerts'
            )
        })
    )

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Administración de Reportes"""
    
    list_display = (
        'name',
        'type',
        'period',
        'created_at',
        'status'
    )
    
    list_filter = (
        'type',
        'period',
        'status',
        'created_at'
    )
    
    search_fields = (
        'name',
        'description',
        'content'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'type',
                'period',
                'status'
            )
        }),
        ('Contenido', {
            'fields': (
                'content',
                'metrics',
                'visualizations'
            )
        }),
        ('Distribución', {
            'fields': (
                'recipients',
                'schedule',
                'format'
            )
        })
    ) 