"""
Módulo de vistas para el módulo Publish.

Este módulo contiene todas las vistas relacionadas con:
- Insights estratégicos
- Notificaciones estratégicas
- Gestión de canales y bots
"""

from .strategic_insights_views import (
    strategic_insights_dashboard,
    StrategicInsightsAPIView,
    sector_movements_api,
    global_local_metrics_api,
    environmental_factors_api,
    periodic_insights_api,
    export_insights_report,
    insights_comparison_view,
    sector_opportunity_alert
)

from .strategic_notification_views import (
    strategic_notifications_dashboard,
    StrategicNotificationAPIView,
    StrategicNotificationStatsView,
    StrategicNotificationManagementView,
    notification_config_view,
    notification_logs_view
)

__all__ = [
    # Strategic Insights
    'strategic_insights_dashboard',
    'StrategicInsightsAPIView',
    'sector_movements_api',
    'global_local_metrics_api',
    'environmental_factors_api',
    'periodic_insights_api',
    'export_insights_report',
    'insights_comparison_view',
    'sector_opportunity_alert',
    
    # Strategic Notifications
    'strategic_notifications_dashboard',
    'StrategicNotificationAPIView',
    'StrategicNotificationStatsView',
    'StrategicNotificationManagementView',
    'notification_config_view',
    'notification_logs_view'
] 