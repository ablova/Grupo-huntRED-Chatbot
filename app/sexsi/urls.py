# /home/pablo/app/sexsi/urls.py
#
# Configuración de URLs para el módulo. Define endpoints, vistas y patrones de URL.

"""
URL configuration for the SEXSI app.
"""
from django.urls import path
from app.ats.sexsi import views

app_name = 'sexsi'

urlpatterns = [
    # Rutas para acuerdos
    path('agreement/create/', views.create_agreement, name='create_agreement'),
    path('agreement/<int:pk>/', views.agreement_detail, name='agreement_detail'),
    path('agreement/<int:pk>/edit/', views.agreement_edit, name='agreement_edit'),
    path('agreement/<int:pk>/sign/', views.sign_agreement, name='agreement_sign'),
    path('agreement/<int:pk>/cancel/', views.cancel_agreement, name='agreement_cancel'),
    
    # Rutas para preferencias
    path('preference/select/', views.PreferenceSelectionView.as_view(), name='preference_select'),
    path('preference/<int:agreement_id>/update/', views.PreferenceUpdateView.as_view(), name='preference_update'),
    
    # Rutas para notificaciones
    path('notifications/mark-as-read/<int:pk>/', views.mark_notification_as_read, name='notification_mark_as_read'),
    path('notifications/delete/<int:pk>/', views.delete_notification, name='notification_delete'),
    
    # Ruta para el chatbot
    path('chatbot/', views.chatbot_view, name='chatbot'),
    
    # Rutas para documentos
    path('document/<str:document_type>/<str:token>/', views.document_view, name='document_view'),
    path('document/<str:document_type>/<str:token>/sign/', views.sign_document, name='sign_document'),
    
    # Rutas para firmas internas
    path('internal-signature/create/', views.create_internal_signature, name='create_internal_signature'),
    path('internal-signature/list/', views.internal_signature_list, name='internal_signature_list'),
    path('internal-signature/<int:pk>/', views.internal_signature_detail, name='internal_signature_detail'),
    path('internal-signature/<int:pk>/sign/<str:signer>/<str:token>/', views.internal_signature_sign, name='internal_signature_sign'),
    path('internal-signature/<int:pk>/cancel/', views.internal_signature_cancel, name='internal_signature_cancel'),
]
