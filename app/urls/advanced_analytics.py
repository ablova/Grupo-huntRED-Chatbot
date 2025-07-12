"""
URLs para Analytics Avanzados y Matching Automático.
"""

from django.urls import path
from app.views.analytics import (
    advanced_analytics_dashboard,
    matching_analytics,
    performance_metrics,
    predictive_insights,
    automated_matching,
    analytics_api
)

urlpatterns = [
    # Dashboard principal de analytics
    path('', advanced_analytics_dashboard, name='advanced_analytics_dashboard'),
    
    # Analytics de matching
    path('matching/', matching_analytics, name='matching_analytics'),
    
    # Métricas de rendimiento
    path('performance/', performance_metrics, name='performance_metrics'),
    
    # Insights predictivos
    path('predictive/', predictive_insights, name='predictive_insights'),
    
    # Matching automático
    path('automated-matching/', automated_matching, name='automated_matching'),
    
    # API para analytics
    path('api/', analytics_api, name='analytics_api'),
] 