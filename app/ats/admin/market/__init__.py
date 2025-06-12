from django.contrib import admin
from app.ats.market.models.trend import MarketTrend
from app.ats.market.models.benchmark import MarketBenchmark
from app.ats.market.models.analysis import MarketAnalysis

@admin.register(MarketTrend)
class MarketTrendAdmin(admin.ModelAdmin):
    """Administración de Tendencias de Mercado"""
    
    list_display = (
        'skill',
        'demand_level',
        'growth_rate',
        'competition_level',
        'created_at'
    )
    
    list_filter = (
        'demand_level',
        'competition_level',
        'created_at'
    )
    
    search_fields = (
        'skill',
        'trends'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'skill',
                'demand_level',
                'growth_rate',
                'competition_level'
            )
        }),
        ('Tendencias', {
            'fields': (
                'trends',
                'insights'
            )
        }),
        ('Métricas', {
            'fields': (
                'confidence_score',
                'data_points'
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
        'salary_range',
        'updated_at'
    )
    
    list_filter = (
        'location',
        'business_unit',
        'updated_at'
    )
    
    search_fields = (
        'skill',
        'location',
        'business_unit__name'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'skill',
                'location',
                'business_unit'
            )
        }),
        ('Métricas', {
            'fields': (
                'salary_range',
                'market_metrics'
            )
        }),
        ('Análisis', {
            'fields': (
                'trends',
                'insights'
            )
        })
    )

@admin.register(MarketAnalysis)
class MarketAnalysisAdmin(admin.ModelAdmin):
    """Administración de Análisis de Mercado"""
    
    list_display = (
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
        'benchmark__skill',
        'benchmark__location'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'benchmark',
                'analysis_type',
                'confidence_score'
            )
        }),
        ('Resultados', {
            'fields': (
                'findings',
                'recommendations'
            )
        }),
        ('Métricas', {
            'fields': (
                'data_points',
                'accuracy_score'
            )
        })
    ) 