# /home/pablo/app/com/onboarding/urls.py
"""
Configuración de URLs para el módulo de onboarding y feedback de clientes.
"""

from django.urls import path, include
from app.ats.onboarding import views
from app.ats.onboarding import client_feedback_views
from app.ats.onboarding import dashboard_views
from app.ats.onboarding import dashboard_api
from app.ats.onboarding import dashboard_share_urls

urlpatterns = [
    # URLs públicas para encuestas
    path('survey/', views.survey_view, name='onboarding_survey'),
    path('survey/submit/', views.survey_submit, name='onboarding_survey_submit'),
    path('survey/thanks/', views.survey_thanks, name='onboarding_survey_thanks'),
    
    # URLs con autenticación para gestión de procesos
    path('processes/', views.OnboardingView.as_view(), name='onboarding_processes'),
    path('processes/<int:onboarding_id>/', views.OnboardingView.as_view(), name='onboarding_process_detail'),
    
    # URLs para tareas
    path('tasks/', views.OnboardingTaskView.as_view(), name='onboarding_tasks'),
    path('tasks/<int:task_id>/', views.OnboardingTaskView.as_view(), name='onboarding_task_detail'),
    
    # URLs para reportes
    path('report/<int:onboarding_id>/', views.satisfaction_report, name='onboarding_satisfaction_report'),

    # URLs para feedback de clientes
    path('client-survey/', client_feedback_views.client_survey_view, name='client_survey'),
    path('client-survey/submit/', client_feedback_views.client_survey_submit, name='client_survey_submit'),
    path('client-survey/thanks/', client_feedback_views.client_survey_thanks, name='client_survey_thanks'),

    # URLs con autenticación para gestión de feedback de clientes
    path('client-feedback/', client_feedback_views.ClientFeedbackView.as_view(), name='client_feedback'),
    path('client-feedback/<int:feedback_id>/', client_feedback_views.ClientFeedbackView.as_view(), name='client_feedback_detail'),
    path('client-feedback/<int:feedback_id>/send/', client_feedback_views.SendClientFeedbackView.as_view(), name='send_client_feedback'),
    path('client-feedback/pending/', client_feedback_views.SendClientFeedbackView.as_view(), name='check_pending_feedback'),

    # URLs para reportes de feedback de clientes
    path('client-report/<int:business_unit_id>/', client_feedback_views.ClientFeedbackReportView.as_view(), name='client_satisfaction_report'),
    
    # Dashboard de clientes
    path('dashboard/client/', dashboard_views.ClientDashboardView.as_view(), name='client_dashboard'),
    path('dashboard/client/satisfaction/', dashboard_views.ClientSatisfactionDashboardView.as_view(), name='client_satisfaction_dashboard'),
    path('dashboard/client/onboarding/', dashboard_views.OnboardingMetricsDashboardView.as_view(), name='onboarding_metrics_dashboard'),
    path('dashboard/client/recommendations/', dashboard_views.RecommendationsDashboardView.as_view(), name='recommendations_dashboard'),
    
    # APIs para el dashboard
    path('api/dashboard/data/', dashboard_api.DashboardDataAPI.as_view(), name='dashboard_data_api'),
    
    # URLs para gestión y acceso a dashboards compartidos
    path('', include(dashboard_share_urls)),
]
