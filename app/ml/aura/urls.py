"""
AURA URLs - URLs para el sistema AURA.
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
from app.ml.aura.dashboard import views as dashboard_views

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

    # Dashboards organizacionales avanzados
    path('dashboard/attrition/', dashboard_views.attrition_dashboard_view, name='attrition_dashboard'),
    path('dashboard/skills/', dashboard_views.skills_dashboard_view, name='skills_dashboard'),

    # Dashboards individuales (usuario)
    path('dashboard/user/attrition/', dashboard_views.user_attrition_dashboard_view, name='user_attrition_dashboard'),
    path('dashboard/user/skills/', dashboard_views.user_skills_dashboard_view, name='user_skills_dashboard'),

    # Dashboards innovadores y diferenciales
    path('dashboard/talent-copilot/', dashboard_views.talent_copilot_view, name='talent_copilot'),
    path('dashboard/whatif-simulator/', dashboard_views.whatif_simulator_view, name='whatif_simulator'),
    path('dashboard/opportunities-risks/', dashboard_views.opportunities_risks_panel_view, name='opportunities_risks_panel'),
    path('dashboard/storytelling/', dashboard_views.storytelling_report_view, name='storytelling_report'),
    path('dashboard/gamification/', dashboard_views.gamification_panel_view, name='gamification_panel'),
    path('dashboard/cv-generator/', dashboard_views.cv_generator_view, name='cv_generator'),
    path('dashboard/dei-interactive/', dashboard_views.interactive_dei_panel_view, name='interactive_dei_panel'),
    path('dashboard/api-webhooks/', dashboard_views.api_webhooks_panel_view, name='api_webhooks_panel'),
    path('dashboard/innovation/', dashboard_views.innovation_panel_view, name='innovation_panel'),
    path('dashboard/social-impact/', dashboard_views.social_impact_panel_view, name='social_impact_panel'),
    path('dashboard/cockpit/', dashboard_views.cockpit_dashboard_view, name='cockpit_dashboard'),
]
