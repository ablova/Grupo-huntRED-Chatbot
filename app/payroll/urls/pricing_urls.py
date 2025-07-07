"""
URLs para el sistema de pricing de huntRED® Payroll
"""

from django.urls import path
from ..views.pricing_dashboard import (
    pricing_dashboard,
    pricing_comparison,
    profitability_analysis,
    calculate_pricing
)
from ..views.cross_sell_dashboard import (
    cross_sell_dashboard,
    company_cross_sell_analysis,
    cross_sell_opportunities_list,
    bundle_proposals,
    generate_cross_sell_proposal,
    cross_sell_analytics,
    cross_sell_recommendations
)

app_name = 'pricing'

urlpatterns = [
    # Dashboard principal de pricing
    path('dashboard/', pricing_dashboard, name='pricing_dashboard'),
    
    # Comparación con competidores
    path('comparison/', pricing_comparison, name='pricing_comparison'),
    
    # Análisis de rentabilidad
    path('profitability/', profitability_analysis, name='profitability_analysis'),
    
    # API para calculadora de precios
    path('calculate/', calculate_pricing, name='calculate_pricing'),
    
    # ============================================================================
    # VENTA CRUZADA
    # ============================================================================
    
    # Dashboard de venta cruzada
    path('cross-sell/', cross_sell_dashboard, name='cross_sell_dashboard'),
    
    # Análisis de venta cruzada por empresa
    path('cross-sell/company/<uuid:company_id>/', company_cross_sell_analysis, name='company_cross_sell_analysis'),
    
    # Lista de oportunidades
    path('cross-sell/opportunities/', cross_sell_opportunities_list, name='cross_sell_opportunities_list'),
    
    # Propuestas de bundles
    path('cross-sell/bundles/', bundle_proposals, name='bundle_proposals'),
    
    # Generar propuesta de venta cruzada
    path('cross-sell/proposal/<uuid:company_id>/', generate_cross_sell_proposal, name='generate_cross_sell_proposal'),
    
    # Analytics de venta cruzada
    path('cross-sell/analytics/', cross_sell_analytics, name='cross_sell_analytics'),
    
    # Recomendaciones de venta cruzada
    path('cross-sell/recommendations/', cross_sell_recommendations, name='cross_sell_recommendations'),
] 