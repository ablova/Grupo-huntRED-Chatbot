"""
URLs para el sistema de Analytics Avanzados y Matching Automático.
"""

from django.urls import path
from app.views.dashboard.advanced_analytics_views import (
    # Dashboards principales
    advanced_analytics_dashboard,
    matching_automation_dashboard,
    cost_analytics_dashboard,
    whatsapp_integration_dashboard,
    
    # 🚀 Nuevos dashboards para sistema completo
    omnichannel_notifications_dashboard,
    conversational_ai_dashboard,
    notification_channels_dashboard,
    notification_templates_dashboard,
    
    # APIs
    api_advanced_matching,
    api_cost_analysis,
    api_whatsapp_send_message,
    api_export_cost_report,
    api_roi_analysis,
    api_matching_analytics,
    api_whatsapp_stats,
    
    # 🚀 Nuevas APIs para sistema completo
    api_send_omnichannel_notification,
    api_conversational_ai_metrics,
    api_channel_performance,
    api_notification_analytics,
)

app_name = 'advanced_analytics'

urlpatterns = [
    # ============================================================================
    # DASHBOARDS PRINCIPALES
    # ============================================================================
    path('dashboard/', advanced_analytics_dashboard, name='advanced_analytics_dashboard'),
    path('matching/', matching_automation_dashboard, name='matching_automation_dashboard'),
    path('costs/', cost_analytics_dashboard, name='cost_analytics_dashboard'),
    path('whatsapp/', whatsapp_integration_dashboard, name='whatsapp_integration_dashboard'),
    
    # ============================================================================
    # 🚀 DASHBOARDS SISTEMA COMPLETO DE NOTIFICACIONES Y CONVERSATIONAL AI
    # ============================================================================
    path('omnichannel/', omnichannel_notifications_dashboard, name='omnichannel_notifications_dashboard'),
    path('conversational-ai/', conversational_ai_dashboard, name='conversational_ai_dashboard'),
    path('channels/', notification_channels_dashboard, name='notification_channels_dashboard'),
    path('templates/', notification_templates_dashboard, name='notification_templates_dashboard'),
    
    # ============================================================================
    # APIs - MATCHING AUTOMÁTICO
    # ============================================================================
    path('api/matching/<int:candidate_id>/<int:position_id>/', 
         api_advanced_matching, name='api_advanced_matching'),
    path('api/matching/analytics/', 
         api_matching_analytics, name='api_matching_analytics'),
    
    # ============================================================================
    # APIs - ANALYTICS DE COSTOS
    # ============================================================================
    path('api/costs/', 
         api_cost_analysis, name='api_cost_analysis'),
    path('api/costs/<int:process_id>/', 
         api_cost_analysis, name='api_cost_analysis_process'),
    path('api/costs/export/<str:format>/', 
         api_export_cost_report, name='api_export_cost_report'),
    path('api/costs/roi/<int:process_id>/', 
         api_roi_analysis, name='api_roi_analysis'),
    
    # ============================================================================
    # APIs - WHATSAPP BUSINESS API
    # ============================================================================
    path('api/whatsapp/send/', 
         api_whatsapp_send_message, name='api_whatsapp_send_message'),
    path('api/whatsapp/stats/', 
         api_whatsapp_stats, name='api_whatsapp_stats'),
    
    # ============================================================================
    # 🚀 APIs - SISTEMA COMPLETO DE NOTIFICACIONES Y CONVERSATIONAL AI
    # ============================================================================
    path('api/omnichannel/send/', 
         api_send_omnichannel_notification, name='api_send_omnichannel_notification'),
    path('api/conversational-ai/metrics/', 
         api_conversational_ai_metrics, name='api_conversational_ai_metrics'),
    path('api/channels/performance/', 
         api_channel_performance, name='api_channel_performance'),
    path('api/notifications/analytics/', 
         api_notification_analytics, name='api_notification_analytics'),
] 