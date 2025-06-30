"""
URLs para el Sistema Administrativo Avanzado de Publicación.
"""
from django.urls import path
from app.ats.publish.views import admin_views

app_name = 'publish_admin'

urlpatterns = [
    # Dashboard principal
    path('dashboard/', admin_views.campaign_dashboard, name='dashboard'),
    
    # Workflow de aprobación
    path('approvals/', admin_views.approval_workflow, name='approval_workflow'),
    path('approvals/<int:approval_id>/review/', admin_views.review_campaign, name='review_campaign'),
    
    # Métricas
    path('metrics/', admin_views.campaign_metrics, name='campaign_metrics'),
    path('metrics/<int:campaign_id>/', admin_views.campaign_metrics, name='campaign_metrics_detail'),
    
    # Auditoría
    path('audit/', admin_views.audit_log, name='audit_log'),
    path('audit/<int:log_id>/', admin_views.audit_log_detail, name='audit_log_detail'),
    
    # APIs
    path('api/stats/', admin_views.api_campaign_stats, name='api_campaign_stats'),
    path('api/metrics/chart/', admin_views.api_metrics_chart, name='api_metrics_chart'),
    path('api/metrics/update/', admin_views.api_update_metrics, name='api_update_metrics'),
] 