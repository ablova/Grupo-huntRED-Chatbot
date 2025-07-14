from django.contrib import admin
from django.conf import settings
from app.ats.analytics.models import AnalyticsEvent, UserMetric, SystemMetric, Report

@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    """Administración de Eventos Analíticos"""
    
    list_display = (
        'event_type',
        'user',
        'timestamp',
        'event_data'
    )
    
    list_filter = (
        'event_type',
        'timestamp'
    )
    
    search_fields = (
        'user__email',
        'event_type',
        'event_data'
    )
    
    readonly_fields = (
        'timestamp',
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'event_type',
                'user',
                'event_data'
            )
        }),
        ('Temporal', {
            'fields': (
                'timestamp',
            )
        })
    )

@admin.register(UserMetric)
class UserMetricAdmin(admin.ModelAdmin):
    """Administración de Métricas de Usuario"""
    
    list_display = (
        'user',
        'metric_name',
        'metric_value',
        'timestamp'
    )
    
    list_filter = (
        'metric_name',
        'timestamp'
    )
    
    search_fields = (
        'user__email',
        'metric_name'
    )
    
    readonly_fields = (
        'timestamp',
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'user',
                'metric_name',
                'metric_value'
            )
        }),
        ('Temporal', {
            'fields': (
                'timestamp',
            )
        })
    )

@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    """Administración de Métricas del Sistema"""
    
    list_display = (
        'metric_name',
        'metric_value',
        'timestamp'
    )
    
    list_filter = (
        'timestamp',
    )
    
    search_fields = (
        'metric_name',
    )
    
    readonly_fields = (
        'timestamp',
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'metric_name',
                'metric_value'
            )
        }),
        ('Temporal', {
            'fields': (
                'timestamp',
            )
        })
    )

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Administración de Reportes"""
    
    list_display = (
        'title',
        'created_at'
    )
    
    list_filter = (
        'created_at'
    )
    
    search_fields = (
        'title',
        'content'
    )
    
    readonly_fields = (
        'created_at',
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'title',
                'content'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
            )
        })
    ) 