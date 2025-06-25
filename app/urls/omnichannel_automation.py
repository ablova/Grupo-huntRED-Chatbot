"""
URLs para el sistema de Automatización Omnicanal.
"""

from django.urls import path
from app.views.dashboard.omnichannel_automation_views import (
    omnichannel_automation_dashboard,
    predictive_engagement_dashboard,
    intelligent_workflows_dashboard,
    automation_optimization_dashboard,
    api_start_workflow,
    api_advance_workflow,
    api_predict_engagement,
    api_get_user_engagement_profile,
    api_get_engagement_insights,
    api_optimize_notification,
    api_get_workflow_status,
    api_retrain_models,
    api_apply_optimization
)

app_name = 'omnichannel_automation'

urlpatterns = [
    # Dashboards principales
    path('dashboard/', omnichannel_automation_dashboard, name='omnichannel_automation_dashboard'),
    path('predictive-engagement/', predictive_engagement_dashboard, name='predictive_engagement_dashboard'),
    path('intelligent-workflows/', intelligent_workflows_dashboard, name='intelligent_workflows_dashboard'),
    path('automation-optimization/', automation_optimization_dashboard, name='automation_optimization_dashboard'),
    
    # APIs para workflows
    path('api/workflows/start/', api_start_workflow, name='api_start_workflow'),
    path('api/workflows/advance/', api_advance_workflow, name='api_advance_workflow'),
    path('api/workflows/status/', api_get_workflow_status, name='api_get_workflow_status'),
    
    # APIs para engagement predictivo
    path('api/engagement/predict/', api_predict_engagement, name='api_predict_engagement'),
    path('api/engagement/profile/', api_get_user_engagement_profile, name='api_get_user_engagement_profile'),
    path('api/engagement/insights/', api_get_engagement_insights, name='api_get_engagement_insights'),
    path('api/engagement/optimize/', api_optimize_notification, name='api_optimize_notification'),
    
    # APIs para optimización
    path('api/optimization/retrain/', api_retrain_models, name='api_retrain_models'),
    path('api/optimization/apply/', api_apply_optimization, name='api_apply_optimization'),
] 