"""
URLs para el sistema de dashboards de huntRED
"""

from django.urls import path
from app.views.dashboard import (
    consultant_views, client_views, super_admin_views
)

app_name = 'dashboard'

urlpatterns = [
    # ============================================================================
    # CONSULTOR DASHBOARD
    # ============================================================================
    
    # Dashboard principal del consultor
    path('consultant/', consultant_views.consultant_dashboard, name='consultant_dashboard'),
    
    # Analytics del consultor
    path('consultant/analytics/', consultant_views.consultant_analytics, name='consultant_analytics'),
    path('consultant/candidates/', consultant_views.candidate_management, name='consultant_candidates'),
    path('consultant/vacancies/', consultant_views.vacancy_management, name='consultant_vacancies'),
    path('consultant/interviews/', consultant_views.interview_management, name='consultant_interviews'),
    
    # AURA para consultores
    path('consultant/aura/', consultant_views.aura_analytics, name='consultant_aura'),
    path('consultant/aura/insights/', consultant_views.aura_insights, name='consultant_aura_insights'),
    path('consultant/aura/predictions/', consultant_views.aura_predictions, name='consultant_aura_predictions'),
    
    # APIs del consultor
    path('api/consultant/analytics/', consultant_views.analytics_api, name='consultant_analytics_api'),
    path('api/consultant/candidates/', consultant_views.candidates_api, name='consultant_candidates_api'),
    path('api/consultant/aura/', consultant_views.aura_api, name='consultant_aura_api'),
    
    # ============================================================================
    # CLIENT DASHBOARD
    # ============================================================================
    
    # Dashboard principal del cliente
    path('client/', client_views.client_dashboard, name='client_dashboard'),
    
    # Analytics del cliente
    path('client/analytics/', client_views.client_analytics, name='client_analytics'),
    path('client/vacancies/', client_views.client_vacancies, name='client_vacancies'),
    path('client/candidates/', client_views.client_candidates, name='client_candidates'),
    path('client/reports/', client_views.client_reports, name='client_reports'),
    
    # AURA para clientes (si está habilitado)
    path('client/aura/', client_views.client_aura_analytics, name='client_aura'),
    path('client/aura/insights/', client_views.client_aura_insights, name='client_aura_insights'),
    
    # APIs del cliente
    path('api/client/analytics/', client_views.client_analytics_api, name='client_analytics_api'),
    path('api/client/vacancies/', client_views.client_vacancies_api, name='client_vacancies_api'),
    path('api/client/aura/', client_views.client_aura_api, name='client_aura_api'),
    
    # ============================================================================
    # SUPER ADMIN DASHBOARD - BRUCE ALMIGHTY MODE 🚀
    # ============================================================================
    
    # Dashboard principal
    path('super-admin/', super_admin_views.super_admin_dashboard, name='super_admin_dashboard'),
    
    # Analytics principales
    path('super-admin/consultants/', super_admin_views.consultant_analytics, name='super_admin_consultants'),
    path('super-admin/clients/', super_admin_views.client_analytics, name='super_admin_clients'),
    path('super-admin/candidates/', super_admin_views.candidate_analytics, name='super_admin_candidates'),
    path('super-admin/processes/', super_admin_views.process_analytics, name='super_admin_processes'),
    
    # AURA y GenIA
    path('super-admin/aura/', super_admin_views.aura_analytics, name='super_admin_aura'),
    path('super-admin/genia/', super_admin_views.genia_analytics, name='super_admin_genia'),
    
    # NUEVAS FUNCIONALIDADES BRUCE ALMIGHTY MODE 🚀
    path('super-admin/business-units/', super_admin_views.business_unit_control, name='super_admin_business_units'),
    path('super-admin/proposals/', super_admin_views.proposals_analytics, name='super_admin_proposals'),
    path('super-admin/opportunities/', super_admin_views.opportunities_analytics, name='super_admin_opportunities'),
    path('super-admin/scraping/', super_admin_views.scraping_analytics, name='super_admin_scraping'),
    path('super-admin/gpt-jd/', super_admin_views.gpt_job_description_generator, name='super_admin_gpt_jd_generator'),
    path('super-admin/sexsi/', super_admin_views.sexsi_analytics, name='super_admin_sexsi'),
    path('super-admin/process-management/', super_admin_views.process_management, name='super_admin_process_management'),
    path('super-admin/salary-comparator/', super_admin_views.salary_comparator, name='super_admin_salary_comparator'),
    
    # Acciones Bruce Almighty Mode 🚀
    path('super-admin/move-candidate-state/', super_admin_views.move_candidate_state_view, name='super_admin_move_candidate_state'),
    path('super-admin/generate-jd/', super_admin_views.generate_jd_view, name='super_admin_generate_jd'),
    path('super-admin/control-scraping/', super_admin_views.control_scraping_view, name='super_admin_control_scraping'),
    path('super-admin/control-sexsi/', super_admin_views.control_sexsi_view, name='super_admin_control_sexsi'),
    path('super-admin/bulk-candidate-actions/', super_admin_views.bulk_candidate_actions_view, name='super_admin_bulk_actions'),
    
    # APIs del Super Admin
    path('api/super-admin/system-overview/', super_admin_views.system_overview_api, name='super_admin_system_overview_api'),
    path('api/super-admin/send-message/', super_admin_views.send_message_api, name='super_admin_send_message_api'),
    path('api/super-admin/control-aura/', super_admin_views.control_aura_api, name='super_admin_control_aura_api'),
    path('api/super-admin/control-genia/', super_admin_views.control_genia_api, name='super_admin_control_genia_api'),
    path('api/super-admin/emergency-actions/', super_admin_views.emergency_actions_api, name='super_admin_emergency_actions_api'),

    # Buscador Inteligente Avanzado
    path('super-admin/intelligent-search/', super_admin_views.intelligent_search_view, name='super_admin_intelligent_search'),
    path('super-admin/intelligent-search/api/', super_admin_views.intelligent_search_api, name='super_admin_intelligent_search_api'),

    # Dashboard Financiero Granular
    path('super-admin/financial-dashboard/', super_admin_views.financial_dashboard_view, name='super_admin_financial_dashboard'),
    path('super-admin/financial-dashboard/api/', super_admin_views.financial_dashboard_api, name='super_admin_financial_dashboard_api'),

    # Kanban Avanzado - BRUCE ALMIGHTY MODE
    path('super-admin/kanban/', super_admin_views.advanced_kanban_view, name='advanced_kanban'),
    path('super-admin/candidate/<int:candidate_id>/', super_admin_views.candidate_detail_view, name='candidate_detail'),
    path('super-admin/candidate/<int:candidate_id>/action/<str:action>/', super_admin_views.candidate_action_view, name='candidate_action'),
    path('super-admin/bulk-candidate-action/', super_admin_views.bulk_candidate_action_view, name='bulk_candidate_action'),
    
    # Visualizador de CV
    path('super-admin/candidate/<int:candidate_id>/cv/', super_admin_views.cv_viewer_view, name='cv_viewer'),
    
    # Reportes Avanzados
    path('super-admin/reports/', super_admin_views.advanced_reports_view, name='advanced_reports'),
    path('super-admin/reports/export/<str:report_type>/', super_admin_views.export_report_view, name='export_report'),
    path('super-admin/reports/schedule/', super_admin_views.schedule_report_view, name='schedule_report'),
] 