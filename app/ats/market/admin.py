from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
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
        'created_at',
        'trends'
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
    
    def trends(self, obj):
        """Muestra tendencias"""
        return ', '.join(obj.trends[:3]) + '...' if len(obj.trends) > 3 else ', '.join(obj.trends)

@admin.register(MarketBenchmark)
class MarketBenchmarkAdmin(admin.ModelAdmin):
    """Administración de Benchmarks de Mercado"""
    
    list_display = (
        'skill',
        'location',
        'business_unit',
        'salary_range',
        'market_metrics',
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
    
    def salary_range(self, obj):
        """Formatea rango salarial"""
        return f"${obj.salary_range['min']:,.2f} - ${obj.salary_range['max']:,.2f}"
    
    def market_metrics(self, obj):
        """Muestra métricas de mercado"""
        return format_html(
            '<a href="{}?benchmark__id__exact={}">Ver Métricas</a>',
            reverse('admin:market_marketanalysis_changelist'),
            obj.id
        )

@admin.register(MarketAnalysis)
class MarketAnalysisAdmin(admin.ModelAdmin):
    """Administración de Análisis de Mercado"""
    
    list_display = (
        'benchmark',
        'analysis_type',
        'confidence_score',
        'created_at',
        'actions'
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
    
    def actions(self, obj):
        """Acciones disponibles"""
        return format_html(
            '<a href="{}" class="button">Ver</a> '
            '<a href="{}" class="button">Exportar</a>',
            reverse('admin:market_marketanalysis_change', args=[obj.id]),
            reverse('admin:market_marketanalysis_export', args=[obj.id])
        ) 