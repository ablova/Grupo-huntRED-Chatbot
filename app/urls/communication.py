"""
🎯 URLs para Optimización de Comunicación

Este módulo define las rutas para:
- Optimización de notificaciones
- Análisis de sentimientos
- Perfiles de comunicación
- Analytics de comunicación
- Testing de estrategias
"""

from django.urls import path
from app.views.communication_optimization_views import (
    optimize_notification_view,
    get_user_communication_profile,
    analyze_sentiment_view,
    get_communication_analytics,
    test_communication_strategies,
    get_communication_recommendations,
    CommunicationOptimizationDashboardView
)

app_name = 'communication'

urlpatterns = [
    # Optimización de notificaciones
    path('optimize/', optimize_notification_view, name='optimize_notification'),
    
    # Perfiles de comunicación
    path('profile/<int:user_id>/', get_user_communication_profile, name='user_profile'),
    
    # Análisis de sentimientos
    path('analyze-sentiment/', analyze_sentiment_view, name='analyze_sentiment'),
    
    # Analytics de comunicación
    path('analytics/', get_communication_analytics, name='analytics'),
    
    # Testing de estrategias
    path('test-strategies/', test_communication_strategies, name='test_strategies'),
    
    # Recomendaciones de comunicación
    path('recommendations/<int:user_id>/', get_communication_recommendations, name='recommendations'),
    
    # Dashboard de optimización
    path('dashboard/', CommunicationOptimizationDashboardView.as_view(), name='dashboard'),
] 