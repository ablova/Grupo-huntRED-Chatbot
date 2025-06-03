# app/client_portal/urls.py
from django.urls import path
from app.ats.ats.ats.client_portal import ats_views

app_name = 'client_portal'

urlpatterns = [
    path('', ats_views.client_dashboard, name='dashboard'),
    path('documents/', ats_views.client_documents, name='documents'),
    path('feedback/', ats_views.client_feedback, name='feedback'),
    path('assessments/', ats_views.client_assessments, name='assessments'),
    path('addons/request/<int:addon_id>/', ats_views.request_addon, name='request_addon'),
] 