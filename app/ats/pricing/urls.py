# /home/pablo/app/com/pricing/urls.py
"""
URLs para el módulo de pricing de Grupo huntRED®.

Define las rutas para acceder a las vistas de gestión de propuestas,
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
    
    # Empresas y contactos
    path('companies/create/', views.CompanyCreateView.as_view(), name='company_create'),
    
    # Propuestas y generación de PDFs
    path('proposals/<int:pk>/', views.proposal_detail, name='proposal_detail'),
    
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
    
    # ============================================================================
    # URLS DE PAGOS, GATEWAYS Y FACTURACIÓN ELECTRÓNICA
    # ============================================================================
    
    # Dashboard de pagos
    path('payments/', views.payment_dashboard, name='payment_dashboard'),
    
    # Gateways de pago
    path('gateways/', views.gateway_list, name='gateway_list'),
    path('gateways/create/', views.gateway_create, name='gateway_create'),
    path('gateways/<int:gateway_id>/', views.gateway_detail, name='gateway_detail'),
    path('gateways/<int:gateway_id>/edit/', views.gateway_edit, name='gateway_edit'),
    
    # Cuentas bancarias
    path('bank-accounts/', views.bank_account_list, name='bank_account_list'),
    path('bank-accounts/create/', views.bank_account_create, name='bank_account_create'),
    
    # Transacciones de pago
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/<str:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    
    # Configuraciones PAC
    path('pac-configurations/', views.pac_configuration_list, name='pac_configuration_list'),
    path('pac-configurations/create/', views.pac_configuration_create, name='pac_configuration_create'),
    path('pac-configurations/<int:pac_id>/edit/', views.pac_configuration_edit, name='pac_configuration_edit'),
    
    # Procesamiento de pagos
    path('invoices/<int:invoice_id>/process-payment/', views.process_payment, name='process_payment'),
    
    # Webhooks
    path('webhooks/<int:gateway_id>/', views.webhook_handler, name='webhook_handler'),
    
    # Facturación electrónica
    path('electronic-billing/', views.electronic_billing_dashboard, name='electronic_billing_dashboard'),
    path('invoices/<int:invoice_id>/electronic-billing/', views.process_electronic_invoice, name='process_electronic_invoice'),
    
    # ============================================================================
    # URLS DE MODELOS MIGRADOS (EMPLEADORES, EMPLEADOS, OPORTUNIDADES)
    # ============================================================================
    
    # Empleadores
    path('empleadores/', views.empleador_list, name='empleador_list'),
    path('empleadores/create/', views.empleador_create, name='empleador_create'),
    path('empleadores/<int:empleador_id>/', views.empleador_detail, name='empleador_detail'),
    path('empleadores/<int:empleador_id>/edit/', views.empleador_edit, name='empleador_edit'),
    
    # Empleados
    path('empleados/', views.empleado_list, name='empleado_list'),
    path('empleados/create/', views.empleado_create, name='empleado_create'),
    path('empleados/<int:empleado_id>/', views.empleado_detail, name='empleado_detail'),
    path('empleados/<int:empleado_id>/edit/', views.empleado_edit, name='empleado_edit'),
    
    # Oportunidades
    path('oportunidades/', views.oportunidad_list, name='oportunidad_list'),
    path('oportunidades/create/', views.oportunidad_create, name='oportunidad_create'),
    path('oportunidades/<int:oportunidad_id>/', views.oportunidad_detail, name='oportunidad_detail'),
    path('oportunidades/<int:oportunidad_id>/edit/', views.oportunidad_edit, name='oportunidad_edit'),
    path('oportunidades/<int:oportunidad_id>/sync-wordpress/', views.sync_oportunidad_wordpress, name='sync_oportunidad_wordpress'),
    
    # Pagos recurrentes
    path('pagos-recurrentes/', views.pago_recurrente_list, name='pago_recurrente_list'),
    path('pagos-recurrentes/create/', views.pago_recurrente_create, name='pago_recurrente_create'),
    path('pagos-recurrentes/<int:pago_id>/', views.pago_recurrente_detail, name='pago_recurrente_detail'),
    path('pagos-recurrentes/<int:pago_id>/edit/', views.pago_recurrente_edit, name='pago_recurrente_edit'),
    
    # Sincronización WordPress
    path('wordpress/sync/', views.wordpress_sync_dashboard, name='wordpress_sync_dashboard'),
    path('wordpress/sync/all/', views.sync_all_wordpress, name='sync_all_wordpress'),
    path('wordpress/sync/pricing/', views.sync_pricing_wordpress, name='sync_pricing_wordpress'),
]
