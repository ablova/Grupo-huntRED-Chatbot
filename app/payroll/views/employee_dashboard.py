from django.views.generic import TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
import json

from app.payroll.models import Employee, PayrollRecord, AttendanceRecord, Benefit
from app.payroll.services.workplace_climate_service import WorkplaceClimateService
from app.payroll.services.ml_attendance_service import MLAttendanceService


class EmployeeDashboardView(LoginRequiredMixin, DetailView):
    """Dashboard personalizado para empleados con información completa."""
    model = Employee
    template_name = 'payroll/employee_dashboard.html'
    context_object_name = 'employee'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_object()
        
        # Datos básicos del empleado
        context.update({
            'payslip_history': self.get_payslip_history(employee),
            'attendance_summary': self.get_attendance_summary(employee),
            'benefits_overview': self.get_benefits_overview(employee),
            'requests_pending': self.get_pending_requests(employee),
            'notifications': self.get_notifications(employee),
            'performance_metrics': self.get_performance_metrics(employee),
            'upcoming_events': self.get_upcoming_events(employee),
            'quick_actions': self.get_quick_actions(employee)
        })
        
        return context
    
    def get_payslip_history(self, employee):
        """Obtiene historial de recibos de nómina."""
        return PayrollRecord.objects.filter(
            employee=employee
        ).order_by('-period_start')[:12]  # Últimos 12 meses
    
    def get_attendance_summary(self, employee):
        """Obtiene resumen de asistencia."""
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        attendance_records = AttendanceRecord.objects.filter(
            employee=employee,
            date__gte=month_start
        )
        
        total_days = (today - month_start).days + 1
        present_days = attendance_records.filter(status='present').count()
        absent_days = attendance_records.filter(status='absent').count()
        late_days = attendance_records.filter(status='late').count()
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'attendance_rate': (present_days / total_days * 100) if total_days > 0 else 0,
            'monthly_trend': self.get_attendance_trend(employee)
        }
    
    def get_attendance_trend(self, employee):
        """Obtiene tendencia de asistencia de los últimos 6 meses."""
        trend_data = []
        for i in range(6):
            month_date = timezone.now().date() - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            records = AttendanceRecord.objects.filter(
                employee=employee,
                date__gte=month_start,
                date__lte=month_end
            )
            
            total_days = records.count()
            present_days = records.filter(status='present').count()
            
            attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
            
            trend_data.append({
                'month': month_start.strftime('%B %Y'),
                'rate': round(attendance_rate, 1)
            })
        
        return list(reversed(trend_data))
    
    def get_benefits_overview(self, employee):
        """Obtiene resumen de beneficios."""
        benefits = Benefit.objects.filter(employee=employee, is_active=True)
        
        return {
            'total_benefits': benefits.count(),
            'benefits_list': benefits[:5],  # Top 5 beneficios
            'total_value': benefits.aggregate(Sum('monthly_value'))['monthly_value__sum'] or 0,
            'utilization_rate': self.calculate_benefits_utilization(employee)
        }
    
    def calculate_benefits_utilization(self, employee):
        """Calcula tasa de utilización de beneficios."""
        # Lógica simplificada - en producción sería más compleja
        return 85.5  # Porcentaje de utilización
    
    def get_pending_requests(self, employee):
        """Obtiene solicitudes pendientes del empleado."""
        # Aquí se integraría con el sistema de solicitudes
        return {
            'total_pending': 0,
            'requests': []
        }
    
    def get_notifications(self, employee):
        """Obtiene notificaciones relevantes para el empleado."""
        return {
            'unread_count': 0,
            'notifications': []
        }
    
    def get_performance_metrics(self, employee):
        """Obtiene métricas de rendimiento."""
        # Integración con sistema de evaluación de desempeño
        return {
            'current_rating': 4.2,
            'last_evaluation': '2024-01-15',
            'next_evaluation': '2024-07-15',
            'goals_completion': 75.0
        }
    
    def get_upcoming_events(self, employee):
        """Obtiene eventos próximos relevantes."""
        return {
            'holidays': [],
            'meetings': [],
            'deadlines': []
        }
    
    def get_quick_actions(self, employee):
        """Obtiene acciones rápidas disponibles."""
        return [
            {
                'name': 'Solicitar Recibo',
                'action': 'request_payslip',
                'icon': 'receipt',
                'url': f'/payroll/request-payslip/{employee.id}/'
            },
            {
                'name': 'Reportar Asistencia',
                'action': 'report_attendance',
                'icon': 'schedule',
                'url': f'/payroll/report-attendance/{employee.id}/'
            },
            {
                'name': 'Solicitar Beneficio',
                'action': 'request_benefit',
                'icon': 'card_giftcard',
                'url': f'/payroll/request-benefit/{employee.id}/'
            },
            {
                'name': 'Ver Historial',
                'action': 'view_history',
                'icon': 'history',
                'url': f'/payroll/history/{employee.id}/'
            }
        ]


class EmployeeDashboardAPIView(LoginRequiredMixin, DetailView):
    """API para datos del dashboard de empleados."""
    model = Employee
    
    def get(self, request, *args, **kwargs):
        employee = self.get_object()
        data_type = request.GET.get('type', 'overview')
        
        if data_type == 'attendance':
            data = self.get_attendance_data(employee)
        elif data_type == 'payslip':
            data = self.get_payslip_data(employee)
        elif data_type == 'benefits':
            data = self.get_benefits_data(employee)
        elif data_type == 'performance':
            data = self.get_performance_data(employee)
        else:
            data = self.get_overview_data(employee)
        
        return JsonResponse(data)
    
    def get_overview_data(self, employee):
        """Datos generales del dashboard."""
        return {
            'employee_id': employee.id,
            'name': employee.full_name,
            'position': employee.position,
            'department': employee.department.name if employee.department else None,
            'hire_date': employee.hire_date.isoformat() if employee.hire_date else None,
            'status': employee.status
        }
    
    def get_attendance_data(self, employee):
        """Datos de asistencia para gráficos."""
        # Datos para gráfico de asistencia mensual
        attendance_data = []
        for i in range(12):
            month_date = timezone.now().date() - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            records = AttendanceRecord.objects.filter(
                employee=employee,
                date__gte=month_start,
                date__lte=month_end
            )
            
            total_days = records.count()
            present_days = records.filter(status='present').count()
            late_days = records.filter(status='late').count()
            absent_days = records.filter(status='absent').count()
            
            attendance_data.append({
                'month': month_start.strftime('%b %Y'),
                'present': present_days,
                'late': late_days,
                'absent': absent_days,
                'rate': (present_days / total_days * 100) if total_days > 0 else 0
            })
        
        return {
            'attendance_trend': list(reversed(attendance_data)),
            'current_month': self.get_current_month_attendance(employee)
        }
    
    def get_current_month_attendance(self, employee):
        """Asistencia del mes actual."""
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        records = AttendanceRecord.objects.filter(
            employee=employee,
            date__gte=month_start,
            date__lte=today
        )
        
        return {
            'total_days': records.count(),
            'present_days': records.filter(status='present').count(),
            'late_days': records.filter(status='late').count(),
            'absent_days': records.filter(status='absent').count(),
            'attendance_rate': self.calculate_attendance_rate(records)
        }
    
    def calculate_attendance_rate(self, records):
        """Calcula tasa de asistencia."""
        total = records.count()
        present = records.filter(status='present').count()
        return (present / total * 100) if total > 0 else 0
    
    def get_payslip_data(self, employee):
        """Datos de nómina para gráficos."""
        payslips = PayrollRecord.objects.filter(
            employee=employee
        ).order_by('-period_start')[:12]
        
        payslip_data = []
        for payslip in payslips:
            payslip_data.append({
                'period': payslip.period_start.strftime('%b %Y'),
                'gross_salary': float(payslip.gross_salary),
                'net_salary': float(payslip.net_salary),
                'deductions': float(payslip.total_deductions),
                'bonuses': float(payslip.total_bonuses)
            })
        
        return {
            'payslip_history': payslip_data,
            'salary_summary': self.get_salary_summary(payslips)
        }
    
    def get_salary_summary(self, payslips):
        """Resumen de salarios."""
        if not payslips:
            return {}
        
        return {
            'average_gross': payslips.aggregate(Avg('gross_salary'))['gross_salary__avg'],
            'average_net': payslips.aggregate(Avg('net_salary'))['net_salary__avg'],
            'total_deductions': payslips.aggregate(Sum('total_deductions'))['total_deductions__sum'],
            'total_bonuses': payslips.aggregate(Sum('total_bonuses'))['total_bonuses__sum']
        }
    
    def get_benefits_data(self, employee):
        """Datos de beneficios."""
        benefits = Benefit.objects.filter(employee=employee, is_active=True)
        
        benefits_data = []
        for benefit in benefits:
            benefits_data.append({
                'name': benefit.name,
                'type': benefit.benefit_type,
                'monthly_value': float(benefit.monthly_value),
                'utilization': benefit.utilization_rate if hasattr(benefit, 'utilization_rate') else 0
            })
        
        return {
            'benefits_list': benefits_data,
            'total_value': benefits.aggregate(Sum('monthly_value'))['monthly_value__sum'] or 0,
            'utilization_rate': self.calculate_overall_utilization(benefits)
        }
    
    def calculate_overall_utilization(self, benefits):
        """Calcula utilización general de beneficios."""
        if not benefits:
            return 0
        
        total_utilization = sum(
            getattr(benefit, 'utilization_rate', 0) for benefit in benefits
        )
        return total_utilization / benefits.count()
    
    def get_performance_data(self, employee):
        """Datos de rendimiento."""
        # Aquí se integraría con el sistema de evaluación
        return {
            'current_rating': 4.2,
            'rating_history': [
                {'period': 'Q1 2024', 'rating': 4.1},
                {'period': 'Q4 2023', 'rating': 4.3},
                {'period': 'Q3 2023', 'rating': 4.0}
            ],
            'goals': [
                {'name': 'Mejorar productividad', 'completion': 75},
                {'name': 'Desarrollo de habilidades', 'completion': 90},
                {'name': 'Colaboración en equipo', 'completion': 85}
            ]
        }


class EmployeeQuickActionView(LoginRequiredMixin, DetailView):
    """Vista para acciones rápidas de empleados."""
    model = Employee
    
    def post(self, request, *args, **kwargs):
        employee = self.get_object()
        action = request.POST.get('action')
        
        if action == 'request_payslip':
            return self.handle_payslip_request(employee, request)
        elif action == 'report_attendance':
            return self.handle_attendance_report(employee, request)
        elif action == 'request_benefit':
            return self.handle_benefit_request(employee, request)
        else:
            return JsonResponse({'error': 'Acción no válida'}, status=400)
    
    def handle_payslip_request(self, employee, request):
        """Maneja solicitud de recibo de nómina."""
        period = request.POST.get('period')
        
        # Lógica para generar y enviar recibo
        # En producción, esto generaría un PDF y lo enviaría por email/WhatsApp
        
        return JsonResponse({
            'success': True,
            'message': f'Recibo solicitado para {period}',
            'estimated_delivery': '24 horas'
        })
    
    def handle_attendance_report(self, employee, request):
        """Maneja reporte de asistencia."""
        date = request.POST.get('date')
        status = request.POST.get('status')
        location = request.POST.get('location')
        
        # Crear registro de asistencia
        AttendanceRecord.objects.create(
            employee=employee,
            date=date,
            status=status,
            location=location,
            reported_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Asistencia reportada correctamente'
        })
    
    def handle_benefit_request(self, employee, request):
        """Maneja solicitud de beneficio."""
        benefit_type = request.POST.get('benefit_type')
        description = request.POST.get('description')
        
        # Crear solicitud de beneficio
        # En producción, esto crearía una solicitud en el sistema
        
        return JsonResponse({
            'success': True,
            'message': 'Solicitud de beneficio enviada',
            'request_id': 'REQ-2024-001'
        }) 