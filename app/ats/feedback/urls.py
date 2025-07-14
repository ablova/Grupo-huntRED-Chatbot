# /home/pablo/app/com/feedback/urls.py
"""
URLs para el sistema integrado de retroalimentación de Grupo huntRED®.

Define las rutas para acceder a las vistas del sistema de retroalimentación,
incluyendo formularios de feedback, panel de administración, y gestión de recordatorios.
"""

from django.urls import path
from app.ats.feedback import views
from app.ats.feedback import process_views

app_name = 'feedback'

urlpatterns = [
    # Panel principal
    path('', views.feedback_dashboard, name='dashboard'),
    
    # Formularios públicos para clientes
    path('proposal/<str:token>/', views.proposal_feedback, name='proposal_feedback'),
    path('ongoing/<str:token>/', views.ongoing_feedback, name='ongoing_feedback'),
    path('completion/<str:token>/', views.completion_feedback, name='completion_feedback'),
    path('skills/<str:token>/', views.skill_feedback, name='skill_feedback'),
    
    # Vistas administrativas generales
    # path('list/', views.FeedbackListView.as_view(), name='feedback_list'),
    # path('detail/<int:pk>/', views.FeedbackDetailView.as_view(), name='feedback_detail'),
    path('suggestions/', views.suggestions_list, name='suggestions_list'),
    path('suggestions/<int:suggestion_id>/update/', views.update_suggestion_status, name='update_suggestion'),
    path('testimonials/', views.testimonials_list, name='testimonials_list'),
    path('export/', views.export_insights, name='export_insights'),
    
    # Vistas para procesos específicos
    path('process/<int:opportunity_id>/', process_views.process_feedback_summary, name='process_summary'),
    path('process/<int:opportunity_id>/request/', process_views.send_feedback_request, name='request_process_feedback'),
    path('process/<int:opportunity_id>/reminder/', process_views.send_reminder, name='send_process_reminder'),
    
    # Gestión de recordatorios
    path('reminders/', process_views.pending_reminders_dashboard, name='pending_reminders'),
    path('reminders/bulk/', process_views.bulk_send_reminders, name='bulk_send_reminders'),
    path('reminders/mark-responded/', process_views.manually_mark_responded, name='mark_responded'),
    
    # Redirecciones para compatibilidad
    path('dashboard/', views.redirect_to_feedback_dashboard, name='old_dashboard'),
    
    # APIs
    path('api/insights/', views.api_feedback_stats, name='api_insights'),
    path('api/webhook/', views.webhook_feedback, name='webhook'),
]
