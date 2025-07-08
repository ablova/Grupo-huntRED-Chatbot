from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet, basename='employee')
router.register(r'payroll', views.PayrollViewSet, basename='payroll')
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')
router.register(r'benefits', views.BenefitViewSet, basename='benefit')
router.register(r'reports', views.ReportViewSet, basename='report')
router.register(r'webhooks', views.WebhookViewSet, basename='webhook')

app_name = 'payroll_api'

urlpatterns = [
    # APIs RESTful principales
    path('v1/', include(router.urls)),
    
    # APIs específicas
    path('v1/employees/<uuid:employee_id>/dashboard/', views.EmployeeDashboardAPI.as_view(), name='employee_dashboard'),
    path('v1/employees/<uuid:employee_id>/payslips/', views.EmployeePayslipsAPI.as_view(), name='employee_payslips'),
    path('v1/employees/<uuid:employee_id>/attendance/', views.EmployeeAttendanceAPI.as_view(), name='employee_attendance'),
    path('v1/employees/<uuid:employee_id>/benefits/', views.EmployeeBenefitsAPI.as_view(), name='employee_benefits'),
    
    # APIs de nómina
    path('v1/companies/<uuid:company_id>/payroll/calculate/', views.CalculatePayrollAPI.as_view(), name='calculate_payroll'),
    path('v1/companies/<uuid:company_id>/payroll/approve/', views.ApprovePayrollAPI.as_view(), name='approve_payroll'),
    path('v1/companies/<uuid:company_id>/payroll/disburse/', views.DisbursePayrollAPI.as_view(), name='disburse_payroll'),
    
    # APIs de reportes
    path('v1/companies/<uuid:company_id>/reports/payroll/', views.PayrollReportAPI.as_view(), name='payroll_report'),
    path('v1/companies/<uuid:company_id>/reports/attendance/', views.AttendanceReportAPI.as_view(), name='attendance_report'),
    path('v1/companies/<uuid:company_id>/reports/analytics/', views.AnalyticsAPI.as_view(), name='analytics'),
    
    # APIs de webhooks
    path('v1/webhooks/events/', views.WebhookEventsAPI.as_view(), name='webhook_events'),
    path('v1/webhooks/subscriptions/', views.WebhookSubscriptionsAPI.as_view(), name='webhook_subscriptions'),
    
    # APIs de integración
    path('v1/integrations/whatsapp/', views.WhatsAppIntegrationAPI.as_view(), name='whatsapp_integration'),
    path('v1/integrations/banking/', views.BankingIntegrationAPI.as_view(), name='banking_integration'),
    path('v1/integrations/authorities/', views.AuthoritiesIntegrationAPI.as_view(), name='authorities_integration'),
] 