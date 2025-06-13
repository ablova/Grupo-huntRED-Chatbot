# /home/pablo/app/com/pricing/urls.py
"""
URLs para el módulo de pricing de Grupo huntRED®.

Define las rutas para acceder a las vistas de gestión de propuestas, promociones,
generación rápida de propuestas de Talento 360° para maximizar tracción, y
sistema de retroalimentación para comprender por qué los clientes contratan o no.
"""

from django.urls import path
from app.ats.pricing import views
from app.ats.pricing import feedback_views

app_name = 'pricing'

urlpatterns = [
    # Dashboard principal
    path('', views.pricing_dashboard, name='dashboard'),
    
    # Análisis de Talento 360°
    path('talent360/', views.Talent360RequestListView.as_view(), name='talent360_request_list'),
    path('talent360/create/', views.Talent360RequestCreateView.as_view(), name='talent360_request_create'),
    path('talent360/<int:pk>/', views.talent360_request_detail, name='talent360_request_detail'),
    path('talent360/<int:pk>/proposal/', views.generate_talent360_proposal, name='generate_talent360_proposal'),
    path('talent360/bulk/', views.bulk_talent360_requests, name='bulk_talent360_requests'),
    
    # Empresas y contactos
    path('companies/create/', views.CompanyCreateView.as_view(), name='company_create'),
    path('companies/', views.company_list, name='company_list'),
    path('contacts/create/', views.contact_create, name='contact_create'),
    path('contacts/by-company/<int:company_id>/', views.get_contacts_by_company, name='contacts_by_company'),
    
    # Promociones y descuentos
    path('promotions/', views.promotion_list, name='promotion_list'),
    path('promotions/create/', views.promotion_create, name='promotion_create'),
    path('promotions/<int:pk>/edit/', views.promotion_edit, name='promotion_edit'),
    path('promotions/<int:pk>/toggle/', views.promotion_toggle, name='promotion_toggle'),
    
    # Propuestas y generación de PDFs
    path('proposals/', views.proposal_list, name='proposal_list'),
    path('proposals/<int:pk>/', views.proposal_detail, name='proposal_detail'),
    path('proposals/<int:pk>/download/', views.download_proposal, name='download_proposal'),
    
    # API para integración con otras aplicaciones
    path('api/validate-promotion/', views.validate_promotion_code, name='validate_promotion_code'),
    path('api/calculate-pricing/', views.calculate_talent360_pricing, name='calculate_talent360_pricing'),
    
    # Sistema de retroalimentación de propuestas
    path('feedback/<str:token>/', feedback_views.proposal_feedback, name='proposal_feedback'),
    path('feedback/stats/', feedback_views.feedback_dashboard, name='feedback_dashboard'),
    path('feedback/list/', feedback_views.FeedbackListView.as_view(), name='feedback_list'),
    path('feedback/<int:pk>/detail/', feedback_views.FeedbackDetailView.as_view(), name='feedback_detail'),
    path('feedback/<int:feedback_id>/schedule-meeting/', feedback_views.schedule_meeting, name='schedule_meeting'),
    path('meetings/', feedback_views.meeting_requests_list, name='meeting_requests_list'),
    path('meetings/<int:meeting_id>/mark-completed/', feedback_views.mark_meeting_completed, name='mark_meeting_completed'),
    
    # API para retroalimentación
    path('api/feedback-stats/', feedback_views.get_feedback_stats_json, name='feedback_stats_json'),
    path('api/webhook/feedback/', feedback_views.webhook_feedback, name='webhook_feedback'),
]
