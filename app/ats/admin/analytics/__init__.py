from django.contrib import admin
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
        'name',
        'value',
        'value_type',
        'timestamp'
    )
    
    list_filter = (
        'value_type',
        'timestamp'
    )
    
    search_fields = (
        'name',
        'category'
    )
    
    readonly_fields = (
        'timestamp',
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'value',
                'value_type',
                'category'
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
        'report_type',
        'created_at'
    )
    
    list_filter = (
        'report_type',
        'created_at'
    )
    
    search_fields = (
        'title',
        'description'
    )
    
    readonly_fields = (
        'created_at',
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'title',
                'description',
                'report_type',
                'data'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
            )
        })
    ) 