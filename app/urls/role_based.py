"""
URLs específicas por rol con control de acceso y funcionalidades limitadas.
"""

from django.urls import path
from app.views.dashboard.role_based_views import (
    # Consultores Senior
    consultant_dashboard,
    consultant_kanban,
    consultant_cv_viewer,
    consultant_reports,
    
    # Clientes
    client_dashboard,
    client_kanban,
    client_cv_viewer,
    client_reports,
    
    # Super Admin
    super_admin_redirect,
    
    # APIs Consultores Senior
    consultant_api_kanban_data,
    consultant_api_cv_data,
    consultant_api_reports_data,
    
    # APIs Clientes
    client_api_kanban_data,
    client_api_cv_data,
    client_api_add_note,
    client_api_cv_download,
    
    # Redirecciones inteligentes
    role_based_dashboard_redirect,
    role_based_kanban_redirect,
    role_based_reports_redirect,
)

app_name = 'role_based'

urlpatterns = [
    # ============================================================================
    # REDIRECCIONES INTELIGENTES
    # ============================================================================
    path('dashboard/', role_based_dashboard_redirect, name='dashboard_redirect'),
    path('kanban/', role_based_kanban_redirect, name='kanban_redirect'),
    path('reports/', role_based_reports_redirect, name='reports_redirect'),
    
    # ============================================================================
    # CONSULTORES SENIOR
    # ============================================================================
    path('consultant/dashboard/', consultant_dashboard, name='consultant_dashboard'),
    path('consultant/kanban/', consultant_kanban, name='consultant_kanban'),
    path('consultant/cv/<int:candidate_id>/', consultant_cv_viewer, name='consultant_cv_viewer'),
    path('consultant/reports/', consultant_reports, name='consultant_reports'),
    
    # APIs Consultores Senior
    path('consultant/api/kanban/', consultant_api_kanban_data, name='consultant_api_kanban'),
    path('consultant/api/cv/<int:candidate_id>/', consultant_api_cv_data, name='consultant_api_cv'),
    path('consultant/api/reports/', consultant_api_reports_data, name='consultant_api_reports'),
    
    # ============================================================================
    # CLIENTES
    # ============================================================================
    path('client/dashboard/', client_dashboard, name='client_dashboard'),
    path('client/kanban/', client_kanban, name='client_kanban'),
    path('client/cv/<int:candidate_id>/', client_cv_viewer, name='client_cv_viewer'),
    path('client/reports/', client_reports, name='client_reports'),
    
    # APIs Clientes
    path('client/api/kanban/', client_api_kanban_data, name='client_api_kanban'),
    path('client/api/cv/<int:candidate_id>/', client_api_cv_data, name='client_api_cv'),
    path('client/api/note/<int:candidate_id>/', client_api_add_note, name='client_api_note'),
    path('client/api/cv/<int:candidate_id>/download/', client_api_cv_download, name='client_api_cv_download'),
    
    # ============================================================================
    # SUPER ADMIN (REDIRECCIÓN)
    # ============================================================================
    path('super-admin/', super_admin_redirect, name='super_admin_redirect'),
] 