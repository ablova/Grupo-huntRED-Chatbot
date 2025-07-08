from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
import json

from app.payroll.models import (
    Employee, PayrollRecord, AttendanceRecord, Benefit, 
    Company, PayrollPeriod, PayrollCalculation
)
from app.payroll.serializers import (
    EmployeeSerializer, PayrollRecordSerializer, AttendanceRecordSerializer,
    BenefitSerializer, CompanySerializer, PayrollPeriodSerializer
)
from app.payroll.services.payroll_engine import PayrollEngine
from app.payroll.services.whatsapp_bot_service import WhatsAppBotService
from app.payroll.services.bank_disbursement_service import BankDisbursementService


class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de empleados."""
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtra empleados por empresa."""
        company_id = self.request.query_params.get('company_id')
        if company_id:
            return Employee.objects.filter(company_id=company_id)
        return Employee.objects.all()
    
    @action(detail=True, methods=['post'])
    def calculate_salary(self, request, pk=None):
        """Calcula salario de un empleado."""
        employee = self.get_object()
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        
        try:
            engine = PayrollEngine()
            calculation = engine.calculate_employee_salary(
                employee, period_start, period_end
            )
            return Response({
                'success': True,
                'calculation': PayrollRecordSerializer(calculation).data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def request_payslip(self, request, pk=None):
        """Solicita recibo de nómina."""
        employee = self.get_object()
        period = request.data.get('period')
        
        # Lógica para generar y enviar recibo
        try:
            # Aquí se integraría con el servicio de WhatsApp
            bot_service = WhatsAppBotService()
            bot_service.send_payslip_request(employee, period)
            
            return Response({
                'success': True,
                'message': 'Solicitud de recibo enviada'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PayrollViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de nómina."""
    queryset = PayrollRecord.objects.all()
    serializer_class = PayrollRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def calculate_period(self, request):
        """Calcula nómina para un período."""
        company_id = request.data.get('company_id')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        
        try:
            company = get_object_or_404(Company, id=company_id)
            engine = PayrollEngine()
            calculations = engine.calculate_company_payroll(
                company, period_start, period_end
            )
            
            return Response({
                'success': True,
                'calculations_count': len(calculations),
                'total_gross': sum(c.gross_salary for c in calculations),
                'total_net': sum(c.net_salary for c in calculations)
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def approve_period(self, request):
        """Aprueba nómina de un período."""
        period_id = request.data.get('period_id')
        
        try:
            period = get_object_or_404(PayrollPeriod, id=period_id)
            period.status = 'approved'
            period.approved_by = request.user
            period.approved_at = timezone.now()
            period.save()
            
            return Response({
                'success': True,
                'message': 'Nómina aprobada correctamente'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de asistencia."""
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def bulk_record(self, request):
        """Registra asistencia masiva."""
        records = request.data.get('records', [])
        
        try:
            created_records = []
            for record_data in records:
                record = AttendanceRecord.objects.create(**record_data)
                created_records.append(record)
            
            return Response({
                'success': True,
                'created_count': len(created_records)
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Obtiene resumen de asistencia."""
        company_id = request.query_params.get('company_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = self.get_queryset()
        if company_id:
            queryset = queryset.filter(employee__company_id=company_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        summary = queryset.aggregate(
            total_records=Count('id'),
            present_days=Count('id', filter=Q(status='present')),
            absent_days=Count('id', filter=Q(status='absent')),
            late_days=Count('id', filter=Q(status='late'))
        )
        
        attendance_rate = (summary['present_days'] / summary['total_records'] * 100) if summary['total_records'] > 0 else 0
        
        return Response({
            'summary': summary,
            'attendance_rate': round(attendance_rate, 2)
        })


class BenefitViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de beneficios."""
    queryset = Benefit.objects.all()
    serializer_class = BenefitSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activa un beneficio."""
        benefit = self.get_object()
        benefit.is_active = True
        benefit.save()
        
        return Response({
            'success': True,
            'message': 'Beneficio activado'
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Desactiva un beneficio."""
        benefit = self.get_object()
        benefit.is_active = False
        benefit.save()
        
        return Response({
            'success': True,
            'message': 'Beneficio desactivado'
        })


class ReportViewSet(viewsets.ViewSet):
    """ViewSet para reportes."""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def payroll_summary(self, request):
        """Reporte resumen de nómina."""
        company_id = request.query_params.get('company_id')
        period_start = request.query_params.get('period_start')
        period_end = request.query_params.get('period_end')
        
        queryset = PayrollRecord.objects.all()
        if company_id:
            queryset = queryset.filter(employee__company_id=company_id)
        if period_start:
            queryset = queryset.filter(period_start__gte=period_start)
        if period_end:
            queryset = queryset.filter(period_end__lte=period_end)
        
        summary = queryset.aggregate(
            total_employees=Count('employee', distinct=True),
            total_gross=Sum('gross_salary'),
            total_net=Sum('net_salary'),
            total_deductions=Sum('total_deductions'),
            total_bonuses=Sum('total_bonuses')
        )
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def attendance_report(self, request):
        """Reporte de asistencia."""
        company_id = request.query_params.get('company_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = AttendanceRecord.objects.all()
        if company_id:
            queryset = queryset.filter(employee__company_id=company_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Agrupar por empleado
        employee_attendance = {}
        for record in queryset:
            employee_id = record.employee.id
            if employee_id not in employee_attendance:
                employee_attendance[employee_id] = {
                    'employee_name': record.employee.full_name,
                    'present_days': 0,
                    'absent_days': 0,
                    'late_days': 0
                }
            
            if record.status == 'present':
                employee_attendance[employee_id]['present_days'] += 1
            elif record.status == 'absent':
                employee_attendance[employee_id]['absent_days'] += 1
            elif record.status == 'late':
                employee_attendance[employee_id]['late_days'] += 1
        
        return Response({
            'employee_attendance': list(employee_attendance.values()),
            'total_records': queryset.count()
        })


class WebhookViewSet(viewsets.ViewSet):
    """ViewSet para webhooks."""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def send_event(self, request):
        """Envía evento a webhooks registrados."""
        event_type = request.data.get('event_type')
        event_data = request.data.get('event_data')
        
        # Aquí se implementaría la lógica para enviar webhooks
        # a los endpoints registrados
        
        return Response({
            'success': True,
            'message': f'Evento {event_type} enviado'
        })


# APIs específicas
class EmployeeDashboardAPI(APIView):
    """API para dashboard de empleados."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, employee_id):
        """Obtiene datos del dashboard de un empleado."""
        employee = get_object_or_404(Employee, id=employee_id)
        
        # Obtener datos del dashboard
        dashboard_data = {
            'employee': EmployeeSerializer(employee).data,
            'attendance_summary': self.get_attendance_summary(employee),
            'payslip_summary': self.get_payslip_summary(employee),
            'benefits_summary': self.get_benefits_summary(employee)
        }
        
        return Response(dashboard_data)
    
    def get_attendance_summary(self, employee):
        """Obtiene resumen de asistencia."""
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        records = AttendanceRecord.objects.filter(
            employee=employee,
            date__gte=month_start
        )
        
        total_days = (today - month_start).days + 1
        present_days = records.filter(status='present').count()
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'attendance_rate': (present_days / total_days * 100) if total_days > 0 else 0
        }
    
    def get_payslip_summary(self, employee):
        """Obtiene resumen de nómina."""
        payslips = PayrollRecord.objects.filter(
            employee=employee
        ).order_by('-period_start')[:6]
        
        return {
            'recent_payslips': PayrollRecordSerializer(payslips, many=True).data,
            'total_count': PayrollRecord.objects.filter(employee=employee).count()
        }
    
    def get_benefits_summary(self, employee):
        """Obtiene resumen de beneficios."""
        benefits = Benefit.objects.filter(
            employee=employee,
            is_active=True
        )
        
        return {
            'active_benefits': BenefitSerializer(benefits, many=True).data,
            'total_value': benefits.aggregate(Sum('monthly_value'))['monthly_value__sum'] or 0
        }


class EmployeePayslipsAPI(APIView):
    """API para recibos de nómina de empleados."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, employee_id):
        """Obtiene historial de recibos."""
        employee = get_object_or_404(Employee, id=employee_id)
        payslips = PayrollRecord.objects.filter(
            employee=employee
        ).order_by('-period_start')
        
        return Response(PayrollRecordSerializer(payslips, many=True).data)


class EmployeeAttendanceAPI(APIView):
    """API para asistencia de empleados."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, employee_id):
        """Obtiene historial de asistencia."""
        employee = get_object_or_404(Employee, id=employee_id)
        attendance = AttendanceRecord.objects.filter(
            employee=employee
        ).order_by('-date')
        
        return Response(AttendanceRecordSerializer(attendance, many=True).data)
    
    def post(self, request, employee_id):
        """Registra asistencia."""
        employee = get_object_or_404(Employee, id=employee_id)
        
        serializer = AttendanceRecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=employee)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeBenefitsAPI(APIView):
    """API para beneficios de empleados."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, employee_id):
        """Obtiene beneficios del empleado."""
        employee = get_object_or_404(Employee, id=employee_id)
        benefits = Benefit.objects.filter(employee=employee)
        
        return Response(BenefitSerializer(benefits, many=True).data)


# APIs de nómina
class CalculatePayrollAPI(APIView):
    """API para cálculo de nómina."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, company_id):
        """Calcula nómina para una empresa."""
        company = get_object_or_404(Company, id=company_id)
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        
        try:
            engine = PayrollEngine()
            calculations = engine.calculate_company_payroll(
                company, period_start, period_end
            )
            
            return Response({
                'success': True,
                'calculations_count': len(calculations),
                'total_gross': sum(c.gross_salary for c in calculations),
                'total_net': sum(c.net_salary for c in calculations)
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ApprovePayrollAPI(APIView):
    """API para aprobar nómina."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, company_id):
        """Aprueba nómina de un período."""
        period_id = request.data.get('period_id')
        
        try:
            period = get_object_or_404(PayrollPeriod, id=period_id)
            period.status = 'approved'
            period.approved_by = request.user
            period.approved_at = timezone.now()
            period.save()
            
            return Response({
                'success': True,
                'message': 'Nómina aprobada correctamente'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class DisbursePayrollAPI(APIView):
    """API para dispersar nómina."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, company_id):
        """Dispersa nómina a empleados."""
        period_id = request.data.get('period_id')
        
        try:
            period = get_object_or_404(PayrollPeriod, id=period_id)
            disbursement_service = BankDisbursementService()
            
            result = disbursement_service.disburse_payroll(period)
            
            return Response({
                'success': True,
                'message': 'Nómina dispersada correctamente',
                'disbursed_amount': result.get('total_amount'),
                'transactions_count': result.get('transactions_count')
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# APIs de reportes
class PayrollReportAPI(APIView):
    """API para reportes de nómina."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, company_id):
        """Genera reporte de nómina."""
        company = get_object_or_404(Company, id=company_id)
        period_start = request.query_params.get('period_start')
        period_end = request.query_params.get('period_end')
        
        queryset = PayrollRecord.objects.filter(employee__company=company)
        if period_start:
            queryset = queryset.filter(period_start__gte=period_start)
        if period_end:
            queryset = queryset.filter(period_end__lte=period_end)
        
        summary = queryset.aggregate(
            total_employees=Count('employee', distinct=True),
            total_gross=Sum('gross_salary'),
            total_net=Sum('net_salary'),
            total_deductions=Sum('total_deductions'),
            total_bonuses=Sum('total_bonuses')
        )
        
        return Response(summary)


class AttendanceReportAPI(APIView):
    """API para reportes de asistencia."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, company_id):
        """Genera reporte de asistencia."""
        company = get_object_or_404(Company, id=company_id)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = AttendanceRecord.objects.filter(employee__company=company)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        summary = queryset.aggregate(
            total_records=Count('id'),
            present_days=Count('id', filter=Q(status='present')),
            absent_days=Count('id', filter=Q(status='absent')),
            late_days=Count('id', filter=Q(status='late'))
        )
        
        attendance_rate = (summary['present_days'] / summary['total_records'] * 100) if summary['total_records'] > 0 else 0
        
        return Response({
            'summary': summary,
            'attendance_rate': round(attendance_rate, 2)
        })


class AnalyticsAPI(APIView):
    """API para analytics."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, company_id):
        """Obtiene analytics de la empresa."""
        company = get_object_or_404(Company, id=company_id)
        
        # Analytics de nómina
        payroll_analytics = self.get_payroll_analytics(company)
        
        # Analytics de asistencia
        attendance_analytics = self.get_attendance_analytics(company)
        
        # Analytics de beneficios
        benefits_analytics = self.get_benefits_analytics(company)
        
        return Response({
            'payroll': payroll_analytics,
            'attendance': attendance_analytics,
            'benefits': benefits_analytics
        })
    
    def get_payroll_analytics(self, company):
        """Obtiene analytics de nómina."""
        # Últimos 12 meses
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)
        
        records = PayrollRecord.objects.filter(
            employee__company=company,
            period_start__gte=start_date
        )
        
        monthly_data = []
        for i in range(12):
            month_date = end_date - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_records = records.filter(
                period_start__gte=month_start,
                period_start__lte=month_end
            )
            
            monthly_data.append({
                'month': month_start.strftime('%B %Y'),
                'total_gross': month_records.aggregate(Sum('gross_salary'))['gross_salary__sum'] or 0,
                'total_net': month_records.aggregate(Sum('net_salary'))['net_salary__sum'] or 0,
                'employee_count': month_records.values('employee').distinct().count()
            })
        
        return {
            'monthly_trend': list(reversed(monthly_data)),
            'total_employees': records.values('employee').distinct().count(),
            'average_salary': records.aggregate(Avg('gross_salary'))['gross_salary__avg'] or 0
        }
    
    def get_attendance_analytics(self, company):
        """Obtiene analytics de asistencia."""
        # Últimos 30 días
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        records = AttendanceRecord.objects.filter(
            employee__company=company,
            date__gte=start_date
        )
        
        summary = records.aggregate(
            total_records=Count('id'),
            present_days=Count('id', filter=Q(status='present')),
            absent_days=Count('id', filter=Q(status='absent')),
            late_days=Count('id', filter=Q(status='late'))
        )
        
        attendance_rate = (summary['present_days'] / summary['total_records'] * 100) if summary['total_records'] > 0 else 0
        
        return {
            'summary': summary,
            'attendance_rate': round(attendance_rate, 2),
            'total_employees': records.values('employee').distinct().count()
        }
    
    def get_benefits_analytics(self, company):
        """Obtiene analytics de beneficios."""
        benefits = Benefit.objects.filter(
            employee__company=company,
            is_active=True
        )
        
        return {
            'total_benefits': benefits.count(),
            'total_value': benefits.aggregate(Sum('monthly_value'))['monthly_value__sum'] or 0,
            'average_per_employee': benefits.aggregate(Avg('monthly_value'))['monthly_value__avg'] or 0
        }


# APIs de webhooks
class WebhookEventsAPI(APIView):
    """API para eventos de webhooks."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Envía evento a webhooks."""
        event_type = request.data.get('event_type')
        event_data = request.data.get('event_data')
        
        # Implementar lógica de webhooks
        return Response({
            'success': True,
            'message': f'Evento {event_type} enviado'
        })


class WebhookSubscriptionsAPI(APIView):
    """API para suscripciones de webhooks."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtiene suscripciones de webhooks."""
        # Implementar lógica para obtener suscripciones
        return Response([])
    
    def post(self, request):
        """Crea suscripción de webhook."""
        # Implementar lógica para crear suscripción
        return Response({
            'success': True,
            'message': 'Suscripción creada'
        })


# APIs de integración
class WhatsAppIntegrationAPI(APIView):
    """API para integración con WhatsApp."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Envía mensaje por WhatsApp."""
        employee_id = request.data.get('employee_id')
        message = request.data.get('message')
        
        try:
            employee = get_object_or_404(Employee, id=employee_id)
            bot_service = WhatsAppBotService()
            bot_service.send_message(employee, message)
            
            return Response({
                'success': True,
                'message': 'Mensaje enviado'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BankingIntegrationAPI(APIView):
    """API para integración bancaria."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Realiza transferencia bancaria."""
        employee_id = request.data.get('employee_id')
        amount = request.data.get('amount')
        
        try:
            employee = get_object_or_404(Employee, id=employee_id)
            disbursement_service = BankDisbursementService()
            result = disbursement_service.transfer_to_employee(employee, amount)
            
            return Response({
                'success': True,
                'transaction_id': result.get('transaction_id'),
                'message': 'Transferencia realizada'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AuthoritiesIntegrationAPI(APIView):
    """API para integración con autoridades."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Envía reporte a autoridades."""
        report_type = request.data.get('report_type')
        report_data = request.data.get('report_data')
        
        # Implementar lógica de integración con autoridades
        return Response({
            'success': True,
            'message': f'Reporte {report_type} enviado'
        }) 