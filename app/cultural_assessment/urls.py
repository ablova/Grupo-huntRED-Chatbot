"""
URLs para el Sistema de Análisis Cultural de Grupo huntRED®.

Define las rutas para acceder a las evaluaciones culturales,
reportes y APIs relacionadas con el análisis cultural.
"""

from django.urls import path
from app.cultural_assessment import views

# Prefijo: /cultural-assessment/
urlpatterns = [
    # Acceso público para participantes
    path('<str:token>/', views.assessment_view, name='cultural_assessment'),
    path('<str:token>/complete/', views.assessment_complete_view, name='cultural_assessment_complete'),
    
    # Reportes (accesibles con token)
    path('reports/<str:token>/', views.report_view, name='cultural_report'),
    
    # APIs para AJAX y Chatbot
    path('api/dimension/<int:dimension_id>/response/', views.api_save_dimension_response, name='api_save_dimension_response'),
    path('api/assessment/<int:assessment_id>/status/', views.api_assessment_status, name='api_assessment_status'),
    
    # Dashboard administrativo
    path('dashboard/', views.dashboard_view, name='cultural_dashboard'),
    path('dashboard/organization/<int:organization_id>/', views.organization_dashboard_view, name='cultural_org_dashboard'),
]
