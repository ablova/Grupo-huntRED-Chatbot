"""
AURA URLs
URLs para el sistema AURA de IA ética y responsable.
"""

from django.urls import path
from app.views.aura.dashboard import (
    AURADashboardView,
    aura_dashboard_data,
    aura_update_tier,
    aura_save_config,
    aura_reset_config,
    aura_analysis_details
)
from app.views.aura.api import (
    aura_analyze_comprehensive,
    aura_analyze_specific,
    aura_system_status,
    aura_performance_metrics,
    aura_audit_trail,
    aura_test_analysis
)

app_name = 'aura'

urlpatterns = [
    # Dashboard principal
    path('dashboard/', AURADashboardView.as_view(), name='dashboard'),
    
    # APIs del dashboard
    path('api/dashboard-data/', aura_dashboard_data, name='dashboard_data'),
    path('api/update-tier/', aura_update_tier, name='update_tier'),
    path('api/save-config/', aura_save_config, name='save_config'),
    path('api/reset-config/', aura_reset_config, name='reset_config'),
    path('api/analysis/<str:analysis_id>/', aura_analysis_details, name='analysis_details'),
    
    # APIs de análisis
    path('api/analyze/comprehensive/', aura_analyze_comprehensive, name='analyze_comprehensive'),
    path('api/analyze/specific/', aura_analyze_specific, name='analyze_specific'),
    path('api/system-status/', aura_system_status, name='system_status'),
    path('api/performance-metrics/', aura_performance_metrics, name='performance_metrics'),
    path('api/audit-trail/', aura_audit_trail, name='audit_trail'),
    path('api/test-analysis/', aura_test_analysis, name='test_analysis'),
]
