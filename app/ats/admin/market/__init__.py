from django.contrib import admin
from app.ats.market.models.trend import MarketTrend
from app.ats.market.models.benchmark import MarketBenchmark
from app.ats.market.models.analysis import MarketAnalysis

@admin.register(MarketTrend)
class MarketTrendAdmin(admin.ModelAdmin):
    """Administración de Tendencias de Mercado"""
    
    list_display = (
        'skill',
        'location',
        'business_unit',
        'demand_level',
        'demand_trend',
        'created_at'
    )
    
    list_filter = (
        'location',
        'business_unit',
        'created_at'
    )
    
    search_fields = (
        'skill__name',
        'location'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'skill',
                'location',
                'business_unit'
            )
        }),
        ('Datos', {
            'fields': (
                'trend_data',
                'predictions'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
                'updated_at'
            )
        })
    )

@admin.register(MarketBenchmark)
class MarketBenchmarkAdmin(admin.ModelAdmin):
    """Administración de Benchmarks de Mercado"""
    
    list_display = (
        'skill',
        'location',
        'business_unit',
        'mean_salary',
        'demand_level',
        'updated_at'
    )
    
    list_filter = (
        'location',
        'business_unit',
        'updated_at'
    )
    
    search_fields = (
        'skill__name',
        'location',
        'business_unit__name'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'skill',
                'location',
                'business_unit'
            )
        }),
        ('Datos', {
            'fields': (
                'salary_data',
                'market_metrics'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
                'updated_at'
            )
        })
    )

@admin.register(MarketAnalysis)
class MarketAnalysisAdmin(admin.ModelAdmin):
    """Administración de Análisis de Mercado"""
    
    list_display = (
        'skill',
        'benchmark',
        'analysis_type',
        'confidence_score',
        'created_at'
    )
    
    list_filter = (
        'analysis_type',
        'created_at'
    )
    
    search_fields = (
        'skill__name',
        'benchmark__skill__name',
        'benchmark__location'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'skill',
                'benchmark',
                'analysis_type'
            )
        }),
        ('Datos', {
            'fields': (
                'metrics',
                'results'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
                'updated_at'
            )
        })
    ) 