# /home/pablo/app/com/publish/urls.py
#
# Configuración de URLs para el módulo. Define endpoints, vistas y patrones de URL.

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.ats.publish.views import ChannelViewSet, BotViewSet, JobChannelViewSet
from app.ats.publish.views import strategic_insights_views, strategic_notification_views

router = DefaultRouter()
router.register(r'channels', ChannelViewSet)
router.register(r'bots', BotViewSet)
router.register(r'job-channels', JobChannelViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # URLs para Insights Estratégicos
    path('strategic-insights/', strategic_insights_views.strategic_insights_dashboard, name='strategic_insights_dashboard'),
    path('api/strategic-insights/<str:analysis_type>/', strategic_insights_views.StrategicInsightsAPIView.as_view(), name='strategic_insights_api'),

    # APIs específicas para insights estratégicos
    path('api/ats/publish/analyzers/sector-movements/', strategic_insights_views.sector_movements_api, name='sector_movements_api'),
    path('api/ats/publish/analyzers/global-local-metrics/', strategic_insights_views.global_local_metrics_api, name='global_local_metrics_api'),
    path('api/ats/publish/analyzers/environmental-factors/', strategic_insights_views.environmental_factors_api, name='environmental_factors_api'),
    path('api/ats/publish/analyzers/periodic-insights/', strategic_insights_views.periodic_insights_api, name='periodic_insights_api'),

    # Funcionalidades adicionales de insights
    path('api/strategic-insights/export-report/', strategic_insights_views.export_insights_report, name='export_insights_report'),
    path('api/strategic-insights/compare/', strategic_insights_views.insights_comparison_view, name='insights_comparison'),
    path('api/strategic-insights/sector-alerts/', strategic_insights_views.sector_opportunity_alert, name='sector_opportunity_alert'),
    
    # URLs para Notificaciones Estratégicas
    path('strategic-notifications/', strategic_notification_views.strategic_notifications_dashboard, name='strategic_notifications_dashboard'),
    path('api/strategic-notifications/', strategic_notification_views.StrategicNotificationAPIView.as_view(), name='strategic_notifications_api'),
    path('api/strategic-notifications/recent/', strategic_notification_views.StrategicNotificationAPIView.as_view(), name='strategic_notifications_recent'),
    path('api/strategic-notifications/send/', strategic_notification_views.StrategicNotificationAPIView.as_view(), name='strategic_notifications_send'),
    path('api/strategic-notifications/stats/', strategic_notification_views.StrategicNotificationStatsView.as_view(), name='strategic_notifications_stats'),
    path('api/strategic-notifications/manage/', strategic_notification_views.StrategicNotificationManagementView.as_view(), name='strategic_notifications_manage'),
    path('api/strategic-notifications/clear/', strategic_notification_views.StrategicNotificationManagementView.as_view(), name='strategic_notifications_clear'),
    path('api/strategic-notifications/config/', strategic_notification_views.notification_config_view, name='strategic_notifications_config'),
    path('api/strategic-notifications/logs/', strategic_notification_views.notification_logs_view, name='strategic_notifications_logs'),
]
