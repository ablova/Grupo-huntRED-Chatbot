"""
Servicio de Gestión de Turnos y Horarios para huntRED® Payroll
Integrado con WhatsApp y sistema de notificaciones
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.mail import send_mail
from django.template.loader import render_to_string

from app.payroll.models import (
    PayrollEmployee, EmployeeShift, ShiftChangeRequest, 
    AttendanceRecord, PayrollFeedback
)
from app.payroll.services.unified_whatsapp_service import UnifiedWhatsAppService
from app.payroll.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ShiftManagementService:
    """
    Servicio para gestión integral de turnos y horarios
    """
    
    def __init__(self, company):
        self.company = company
        self.whatsapp_service = UnifiedWhatsAppService(company)
        self.notification_service = NotificationService(company)
    
    def create_shift(self, employee: PayrollEmployee, shift_data: Dict[str, Any]) -> EmployeeShift:
        """
        Crea un nuevo turno para un empleado
        
        Args:
            employee: Empleado
            shift_data: Datos del turno
            
        Returns:
            EmployeeShift: Turno creado
        """
        try:
            shift = EmployeeShift.objects.create(
                employee=employee,
                shift_name=shift_data['shift_name'],
                shift_type=shift_data['shift_type'],
                start_time=shift_data['start_time'],
                end_time=shift_data['end_time'],
                break_start=shift_data.get('break_start'),
                break_end=shift_data.get('break_end'),
                work_days=shift_data.get('work_days', [0,1,2,3,4]),  # L-V por defecto
                location=shift_data.get('location', {}),
                is_location_variable=shift_data.get('is_location_variable', False),
                hours_per_day=shift_data.get('hours_per_day', 8.0),
                overtime_threshold=shift_data.get('overtime_threshold', 8.0),
                effective_date=shift_data.get('effective_date', date.today()),
                notes=shift_data.get('notes', '')
            )
            
            # Notificar al empleado
            self._notify_shift_assignment(employee, shift)
            
            logger.info(f"Turno creado para {employee.get_full_name()}: {shift.shift_name}")
            return shift
            
        except Exception as e:
            logger.error(f"Error creando turno: {str(e)}")
            raise
    
    def update_shift(self, shift_id, data):
        """Actualiza un turno desde la API drag & drop"""
        try:
            shift = EmployeeShift.objects.get(id=shift_id)
            for key, value in data.items():
                setattr(shift, key, value)
            shift.save()
            return shift
        except EmployeeShift.DoesNotExist:
            return None
    
    def get_employee_schedule(self, employee: PayrollEmployee, week_start: date = None) -> Dict[str, Any]:
        """
        Obtiene el horario semanal de un empleado
        
        Args:
            employee: Empleado
            week_start: Inicio de la semana (opcional)
            
        Returns:
            Dict con el horario semanal
        """
        if not week_start:
            week_start = date.today() - timedelta(days=date.today().weekday())
        
        # Obtener turno actual
        current_shift = EmployeeShift.objects.filter(
            employee=employee,
            effective_date__lte=week_start,
            end_date__isnull=True,
            status='active'
        ).first()
        
        if not current_shift:
            return {
                'error': 'No hay turno activo asignado',
                'week_start': week_start,
                'schedule': {}
            }
        
        # Generar horario semanal
        schedule = current_shift.get_weekly_schedule(week_start)
        
        # Agregar información de asistencia real
        attendance_data = self._get_attendance_data(employee, week_start)
        
        return {
            'employee_name': employee.get_full_name(),
            'shift_name': current_shift.shift_name,
            'shift_type': current_shift.get_shift_type_display(),
            'week_start': week_start,
            'schedule': schedule,
            'attendance': attendance_data,
            'location': current_shift.location,
            'is_location_variable': current_shift.is_location_variable
        }
    
    def request_shift_change(self, employee: PayrollEmployee, request_data: Dict[str, Any]) -> ShiftChangeRequest:
        """
        Solicita un cambio de turno
        
        Args:
            employee: Empleado
            request_data: Datos de la solicitud
            
        Returns:
            ShiftChangeRequest: Solicitud creada
        """
        try:
            # Obtener turno solicitado
            requested_shift = EmployeeShift.objects.get(id=request_data['requested_shift_id'])
            
            request = ShiftChangeRequest.objects.create(
                employee=employee,
                request_type=request_data['request_type'],
                start_date=request_data['start_date'],
                end_date=request_data['end_date'],
                requested_shift=requested_shift,
                reason=request_data['reason'],
                emergency_details=request_data.get('emergency_details', '')
            )
            
            # Notificar a supervisor y RRHH
            self._notify_shift_change_request(request)
            
            logger.info(f"Solicitud de cambio de turno creada para {employee.get_full_name()}")
            return request
            
        except Exception as e:
            logger.error(f"Error creando solicitud de cambio: {str(e)}")
            raise
    
    def approve_shift_change(self, request: ShiftChangeRequest, approver, notes: str = '') -> bool:
        """
        Aprueba una solicitud de cambio de turno
        
        Args:
            request: Solicitud a aprobar
            approver: Usuario que aprueba
            notes: Notas de aprobación
            
        Returns:
            bool: True si se aprobó exitosamente
        """
        try:
            request.status = 'approved'
            request.approved_by = approver
            request.approval_date = timezone.now()
            request.approval_notes = notes
            request.save()
            
            # Crear turno temporal si es necesario
            if request.request_type in ['temporary', 'emergency']:
                self._create_temporary_shift(request)
            
            # Notificar al empleado
            self._notify_shift_change_approval(request)
            
            logger.info(f"Solicitud de cambio de turno aprobada para {request.employee.get_full_name()}")
            return True
            
        except Exception as e:
            logger.error(f"Error aprobando solicitud: {str(e)}")
            return False
    
    def get_shift_analytics(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Obtiene analytics de turnos
        
        Args:
            period_days: Días a analizar
            
        Returns:
            Dict con analytics
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=period_days)
            
            # Estadísticas por tipo de turno
            shift_stats = EmployeeShift.objects.filter(
                employee__company=self.company,
                effective_date__range=[start_date, end_date]
            ).values('shift_type').annotate(
                count=Count('id'),
                avg_hours=Avg('hours_per_day')
            )
            
            # Solicitudes de cambio
            change_requests = ShiftChangeRequest.objects.filter(
                employee__company=self.company,
                created_at__date__range=[start_date, end_date]
            )
            
            request_stats = change_requests.values('request_type', 'status').annotate(
                count=Count('id')
            )
            
            # Análisis de asistencia por turno
            attendance_by_shift = AttendanceRecord.objects.filter(
                employee__company=self.company,
                date__range=[start_date, end_date]
            ).select_related('employee__shifts').values(
                'employee__shifts__shift_type'
            ).annotate(
                avg_hours=Avg('hours_worked'),
                attendance_rate=Count('id', filter=Q(status='present')) * 100.0 / Count('id')
            )
            
            return {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'days': period_days
                },
                'shift_statistics': list(shift_stats),
                'change_request_statistics': list(request_stats),
                'attendance_by_shift': list(attendance_by_shift),
                'total_employees': self.company.employees.filter(is_active=True).count(),
                'employees_with_shifts': EmployeeShift.objects.filter(
                    employee__company=self.company,
                    status='active'
                ).values('employee').distinct().count()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics: {str(e)}")
            return {'error': str(e)}
    
    def send_weekly_schedule_notification(self, employee: PayrollEmployee) -> bool:
        """
        Envía notificación con horario semanal
        
        Args:
            employee: Empleado
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            schedule = self.get_employee_schedule(employee)
            
            if 'error' in schedule:
                return False
            
            # Formatear mensaje para WhatsApp
            message = self._format_weekly_schedule_message(schedule)
            
            # Enviar vía WhatsApp
            if employee.whatsapp_number:
                return self.whatsapp_service.send_message(
                    'whatsapp',
                    employee.whatsapp_number,
                    message
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error enviando horario semanal: {str(e)}")
            return False
    
    def _notify_shift_assignment(self, employee: PayrollEmployee, shift: EmployeeShift):
        """Notifica asignación de turno"""
        try:
            message = f"🕐 *Nuevo Turno Asignado*\n\n"
            message += f"*Turno:* {shift.shift_name}\n"
            message += f"*Horario:* {shift.start_time.strftime('%H:%M')} - {shift.end_time.strftime('%H:%M')}\n"
            message += f"*Días:* {', '.join([self._get_day_name(d) for d in shift.work_days])}\n"
            message += f"*Efectivo desde:* {shift.effective_date.strftime('%d/%m/%Y')}\n\n"
            
            if shift.location:
                message += f"📍 *Ubicación:* {shift.location.get('name', 'No especificada')}\n"
            
            if employee.whatsapp_number:
                self.whatsapp_service.send_message(
                    'whatsapp',
                    employee.whatsapp_number,
                    message
                )
                
        except Exception as e:
            logger.error(f"Error notificando asignación de turno: {str(e)}")
    
    def _notify_shift_changes(self, employee: PayrollEmployee, shift: EmployeeShift, old_data: Dict):
        """Notifica cambios en turno"""
        try:
            message = f"⚠️ *Cambios en tu Turno*\n\n"
            message += f"*Turno:* {shift.shift_name}\n\n"
            
            if old_data['old_start_time'] != shift.start_time:
                message += f"🕐 *Horario anterior:* {old_data['old_start_time'].strftime('%H:%M')} - {old_data['old_end_time'].strftime('%H:%M')}\n"
                message += f"🕐 *Nuevo horario:* {shift.start_time.strftime('%H:%M')} - {shift.end_time.strftime('%H:%M')}\n\n"
            
            message += f"Los cambios son efectivos desde: {shift.effective_date.strftime('%d/%m/%Y')}"
            
            if employee.whatsapp_number:
                self.whatsapp_service.send_message(
                    'whatsapp',
                    employee.whatsapp_number,
                    message
                )
                
        except Exception as e:
            logger.error(f"Error notificando cambios de turno: {str(e)}")
    
    def _notify_shift_change_request(self, request: ShiftChangeRequest):
        """Notifica solicitud de cambio de turno"""
        try:
            # Notificar a supervisor
            if request.employee.supervisor:
                supervisor_message = f"📋 *Nueva Solicitud de Cambio de Turno*\n\n"
                supervisor_message += f"*Empleado:* {request.employee.get_full_name()}\n"
                supervisor_message += f"*Tipo:* {request.get_request_type_display()}\n"
                supervisor_message += f"*Período:* {request.start_date.strftime('%d/%m/%Y')} - {request.end_date.strftime('%d/%m/%Y')}\n"
                supervisor_message += f"*Motivo:* {request.reason}\n\n"
                supervisor_message += "Revisa en el sistema para aprobar o rechazar."
                
                # Aquí enviarías la notificación al supervisor
                # self.notification_service.send_notification_to_user(
                #     request.employee.supervisor,
                #     'shift_change_request',
                #     supervisor_message
                # )
                
        except Exception as e:
            logger.error(f"Error notificando solicitud de cambio: {str(e)}")
    
    def _notify_shift_change_approval(self, request: ShiftChangeRequest):
        """Notifica aprobación de cambio de turno"""
        try:
            message = f"✅ *Solicitud de Cambio Aprobada*\n\n"
            message += f"*Tipo:* {request.get_request_type_display()}\n"
            message += f"*Período:* {request.start_date.strftime('%d/%m/%Y')} - {request.end_date.strftime('%d/%m/%Y')}\n"
            message += f"*Turno:* {request.requested_shift.shift_name}\n"
            
            if request.approval_notes:
                message += f"*Notas:* {request.approval_notes}\n"
            
            if request.employee.whatsapp_number:
                self.whatsapp_service.send_message(
                    'whatsapp',
                    request.employee.whatsapp_number,
                    message
                )
                
        except Exception as e:
            logger.error(f"Error notificando aprobación: {str(e)}")
    
    def _get_attendance_data(self, employee: PayrollEmployee, week_start: date) -> Dict[str, Any]:
        """Obtiene datos de asistencia para la semana"""
        week_end = week_start + timedelta(days=6)
        
        attendance_records = AttendanceRecord.objects.filter(
            employee=employee,
            date__range=[week_start, week_end]
        ).order_by('date')
        
        attendance_data = {}
        for record in attendance_records:
            attendance_data[record.date.strftime('%Y-%m-%d')] = {
                'status': record.status,
                'check_in': record.check_in_time.strftime('%H:%M') if record.check_in_time else None,
                'check_out': record.check_out_time.strftime('%H:%M') if record.check_out_time else None,
                'hours_worked': float(record.hours_worked) if record.hours_worked else 0
            }
        
        return attendance_data
    
    def _format_weekly_schedule_message(self, schedule: Dict[str, Any]) -> str:
        """Formatea horario semanal para WhatsApp"""
        message = f"📅 *Tu Horario Semanal*\n\n"
        message += f"*Empleado:* {schedule['employee_name']}\n"
        message += f"*Turno:* {schedule['shift_name']}\n"
        message += f"*Semana del:* {schedule['week_start'].strftime('%d/%m/%Y')}\n\n"
        
        days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        for day_name, day_data in schedule['schedule'].items():
            if day_data:
                message += f"*{days[day_name.weekday()]} {day_name.strftime('%d/%m')}*\n"
                message += f"🕐 {day_data['start_time'].strftime('%H:%M')} - {day_data['end_time'].strftime('%H:%M')}\n"
                
                if day_data.get('break_start') and day_data.get('break_end'):
                    message += f"☕ Descanso: {day_data['break_start'].strftime('%H:%M')} - {day_data['break_end'].strftime('%H:%M')}\n"
                
                if day_data.get('location', {}).get('name'):
                    message += f"📍 {day_data['location']['name']}\n"
                
                message += "\n"
        
        if schedule.get('is_location_variable'):
            message += "⚠️ *Ubicación variable - consulta con tu supervisor*\n"
        
        return message
    
    def _get_day_name(self, day_number: int) -> str:
        """Convierte número de día a nombre"""
        days = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        return days[day_number] if 0 <= day_number < 7 else 'Desconocido'
    
    def _create_temporary_shift(self, request: ShiftChangeRequest):
        """Crea turno temporal para solicitudes aprobadas"""
        try:
            # Crear turno temporal basado en el turno solicitado
            temp_shift = EmployeeShift.objects.create(
                employee=request.employee,
                shift_name=f"Temporal - {request.requested_shift.shift_name}",
                shift_type=request.requested_shift.shift_type,
                start_time=request.requested_shift.start_time,
                end_time=request.requested_shift.end_time,
                break_start=request.requested_shift.break_start,
                break_end=request.requested_shift.break_end,
                work_days=request.requested_shift.work_days,
                location=request.requested_shift.location,
                hours_per_day=request.requested_shift.hours_per_day,
                overtime_threshold=request.requested_shift.overtime_threshold,
                effective_date=request.start_date,
                end_date=request.end_date,
                status='temporary',
                notes=f"Turno temporal por solicitud #{request.id}"
            )
            
            logger.info(f"Turno temporal creado para {request.employee.get_full_name()}")
            
        except Exception as e:
            logger.error(f"Error creando turno temporal: {str(e)}") 