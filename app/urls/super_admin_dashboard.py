"""
🚀 SUPER ADMIN DASHBOARD URLs - BRUCE ALMIGHTY MODE 🚀

URLs para el dashboard del Super Admin con control total del sistema.
"""

from django.urls import path
from app.views.dashboard.super_admin_views import (
    SuperAdminDashboardView, SuperAdminSystemOverviewView,
    SuperAdminConsultantAnalyticsView, SuperAdminClientAnalyticsView,
    SuperAdminCandidateAnalyticsView, SuperAdminProcessAnalyticsView,
    SuperAdminAuraAnalyticsView, SuperAdminGeniaAnalyticsView,
    SuperAdminDirectMessageView, SuperAdminAuraControlView,
    SuperAdminGeniaControlView, SuperAdminEmergencyActionsView,
    SuperAdminUserManagementView, SuperAdminSystemLogsView,
    SuperAdminFinancialDashboardView, SuperAdminFinancialDataView,
    SuperAdminProviderValidationView
)

urlpatterns = [
    # Dashboard principal
    path('super-admin/dashboard/', SuperAdminDashboardView.as_view(), name='super_admin_dashboard'),
    
    # Analytics del sistema
    path('super-admin/system-overview/', SuperAdminSystemOverviewView.as_view(), name='super_admin_system_overview'),
    path('super-admin/consultant-analytics/', SuperAdminConsultantAnalyticsView.as_view(), name='super_admin_consultant_analytics'),
    path('super-admin/client-analytics/', SuperAdminClientAnalyticsView.as_view(), name='super_admin_client_analytics'),
    path('super-admin/candidate-analytics/', SuperAdminCandidateAnalyticsView.as_view(), name='super_admin_candidate_analytics'),
    path('super-admin/process-analytics/', SuperAdminProcessAnalyticsView.as_view(), name='super_admin_process_analytics'),
    
    # Analytics de IA
    path('super-admin/aura-analytics/', SuperAdminAuraAnalyticsView.as_view(), name='super_admin_aura_analytics'),
    path('super-admin/genia-analytics/', SuperAdminGeniaAnalyticsView.as_view(), name='super_admin_genia_analytics'),
    
    # Dashboard Financiero y Pagos 🚀
    path('super-admin/financial-dashboard/', SuperAdminFinancialDashboardView.as_view(), name='super_admin_financial_dashboard'),
    path('super-admin/financial-data/', SuperAdminFinancialDataView.as_view(), name='super_admin_financial_data'),
    path('super-admin/provider-validation/', SuperAdminProviderValidationView.as_view(), name='super_admin_provider_validation'),
    
    # Control total del sistema (BRUCE ALMIGHTY MODE) 🚀
    path('super-admin/direct-message/', SuperAdminDirectMessageView.as_view(), name='super_admin_direct_message'),
    path('super-admin/aura-control/', SuperAdminAuraControlView.as_view(), name='super_admin_aura_control'),
    path('super-admin/genia-control/', SuperAdminGeniaControlView.as_view(), name='super_admin_genia_control'),
    path('super-admin/emergency-actions/', SuperAdminEmergencyActionsView.as_view(), name='super_admin_emergency_actions'),
    
    # Gestión de usuarios y logs
    path('super-admin/user-management/', SuperAdminUserManagementView.as_view(), name='super_admin_user_management'),
    path('super-admin/system-logs/', SuperAdminSystemLogsView.as_view(), name='super_admin_system_logs'),
] 