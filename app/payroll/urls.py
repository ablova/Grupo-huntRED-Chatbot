"""
URLs del Sistema de Nómina huntRED®
"""
from django.urls import path, include
from django.contrib import admin

from . import views
from .services.whatsapp_service import WhatsAppWebhookView

app_name = 'payroll'

urlpatterns = [
    # ============================================================================
    # DASHBOARD Y VISTAS PRINCIPALES
    # ============================================================================
    
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    
    # ============================================================================
    # GESTIÓN DE EMPRESAS
    # ============================================================================
    
    # Lista de empresas
    path('companies/', views.company_list, name='company_list'),
    path('companies/create/', views.company_create, name='company_create'),
    path('companies/<uuid:company_id>/', views.company_detail, name='company_detail'),
    path('companies/<uuid:company_id>/edit/', views.company_edit, name='company_edit'),
    path('companies/<uuid:company_id>/delete/', views.company_delete, name='company_delete'),
    
    # ============================================================================
    # GESTIÓN DE EMPLEADOS
    # ============================================================================
    
    # Lista de empleados
    path('companies/<uuid:company_id>/employees/', views.employee_list, name='employee_list'),
    path('companies/<uuid:company_id>/employees/create/', views.employee_create, name='employee_create'),
    path('companies/<uuid:company_id>/employees/<uuid:employee_id>/', views.employee_detail, name='employee_detail'),
    path('companies/<uuid:company_id>/employees/<uuid:employee_id>/edit/', views.employee_edit, name='employee_edit'),
    path('companies/<uuid:company_id>/employees/<uuid:employee_id>/delete/', views.employee_delete, name='employee_delete'),
    
    # Carga masiva de empleados
    path('companies/<uuid:company_id>/employees/bulk-upload/', views.employee_bulk_upload, name='employee_bulk_upload'),
    path('companies/<uuid:company_id>/employees/bulk-upload/process/', views.employee_bulk_process, name='employee_bulk_process'),
    path('companies/<uuid:company_id>/employees/template/', views.employee_template_download, name='employee_template_download'),
    
    # ============================================================================
    # GESTIÓN DE NÓMINA
    # ============================================================================
    
    # Períodos de nómina
    path('companies/<uuid:company_id>/periods/', views.period_list, name='period_list'),
    path('companies/<uuid:company_id>/periods/create/', views.period_create, name='period_create'),
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/', views.period_detail, name='period_detail'),
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/edit/', views.period_edit, name='period_edit'),
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/delete/', views.period_delete, name='period_delete'),
    
    # Cálculo de nómina
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/calculate/', views.period_calculate, name='period_calculate'),
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/approve/', views.period_approve, name='period_approve'),
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/disburse/', views.period_disburse, name='period_disburse'),
    
    # Cálculos individuales
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/calculations/', views.calculation_list, name='calculation_list'),
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/calculations/<uuid:calculation_id>/', views.calculation_detail, name='calculation_detail'),
    
    # ============================================================================
    # CONTROL DE ASISTENCIA
    # ============================================================================
    
    # Registros de asistencia
    path('companies/<uuid:company_id>/attendance/', views.attendance_list, name='attendance_list'),
    path('companies/<uuid:company_id>/attendance/<uuid:employee_id>/', views.employee_attendance, name='employee_attendance'),
    path('companies/<uuid:company_id>/attendance/report/', views.attendance_report, name='attendance_report'),
    
    # ============================================================================
    # SOLICITUDES DE EMPLEADOS
    # ============================================================================
    
    # Solicitudes
    path('companies/<uuid:company_id>/requests/', views.request_list, name='request_list'),
    path('companies/<uuid:company_id>/requests/<uuid:request_id>/', views.request_detail, name='request_detail'),
    path('companies/<uuid:company_id>/requests/<uuid:request_id>/approve/', views.request_approve, name='request_approve'),
    path('companies/<uuid:company_id>/requests/<uuid:request_id>/reject/', views.request_reject, name='request_reject'),
    
    # ============================================================================
    # SERVICIOS PREMIUM
    # ============================================================================
    
    # Dispersión bancaria
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/disbursement/', views.disbursement_detail, name='disbursement_detail'),
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/disbursement/create/', views.disbursement_create, name='disbursement_create'),
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/disbursement/file/', views.disbursement_file, name='disbursement_file'),
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/disbursement/validate/', views.disbursement_validate, name='disbursement_validate'),
    
    # Timbrado fiscal
    path('companies/<uuid:company_id>/periods/<uuid:period_id>/tax-stamping/', views.tax_stamping, name='tax_stamping'),
    
    # Adelanto de nómina
    path('companies/<uuid:company_id>/employees/<uuid:employee_id>/advance/', views.salary_advance, name='salary_advance'),
    
    # ============================================================================
    # REPORTES Y ANALYTICS
    # ============================================================================
    
    # Reportes
    path('companies/<uuid:company_id>/reports/', views.reports_dashboard, name='reports_dashboard'),
    path('companies/<uuid:company_id>/reports/payroll/', views.payroll_report, name='payroll_report'),
    path('companies/<uuid:company_id>/reports/attendance/', views.attendance_report, name='attendance_report'),
    path('companies/<uuid:company_id>/reports/taxes/', views.taxes_report, name='taxes_report'),
    path('companies/<uuid:company_id>/reports/analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    
    # ============================================================================
    # CONFIGURACIÓN
    # ============================================================================
    
    # Configuración de empresa
    path('companies/<uuid:company_id>/settings/', views.company_settings, name='company_settings'),
    path('companies/<uuid:company_id>/settings/whatsapp/', views.whatsapp_settings, name='whatsapp_settings'),
    path('companies/<uuid:company_id>/settings/pricing/', views.pricing_settings, name='pricing_settings'),
    
    # ============================================================================
    # WEBHOOKS Y APIs
    # ============================================================================
    
    # Webhook de WhatsApp
    path('webhooks/whatsapp/<uuid:company_id>/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    
    # APIs REST
    path('api/', include('app.payroll.api.urls')),
    
    # ============================================================================
    # PRICING Y ANÁLISIS DE COSTOS
    # ============================================================================
    
    # Dashboard de pricing
    path('pricing/', include('app.payroll.urls.pricing_urls')),
    
    # ============================================================================
    # ADMIN
    # ============================================================================
    
    # Admin de Django
    path('admin/', admin.site.urls),
] 