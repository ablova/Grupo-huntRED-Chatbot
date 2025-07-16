"""
Servicio de Feedback para huntRED® Payroll
Extiende el sistema de feedback existente de ATS
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.mail import send_mail
from django.template.loader import render_to_string

from app.payroll.models import (
    PayrollEmployee, PayrollFeedback, PerformanceEvaluation,
    EmployeeShift, ShiftChangeRequest
)
from app.payroll.services.unified_whatsapp_service import UnifiedWhatsAppService
from app.payroll.services.notification_service import NotificationService

# Importar sistema de feedback existente
from app.ats.feedback.feedback_models import ServiceFeedback, OngoingServiceFeedback

logger = logging.getLogger(__name__)


class PayrollFeedbackService:
    """
    Servicio de feedback específico para nómina
    Extiende el sistema de feedback existente
    """
    
    def __init__(self, company):
        self.company = company
        self.whatsapp_service = UnifiedWhatsAppService(company)
        self.notification_service = NotificationService(company)
    
    def create_feedback(self, employee: PayrollEmployee, feedback_data: Dict[str, Any]) -> PayrollFeedback:
        """
        Crea un nuevo feedback de nómina
        
        Args:
            employee: Empleado
            feedback_data: Datos del feedback
            
        Returns:
            PayrollFeedback: Feedback creado
        """
        try:
            feedback = PayrollFeedback.objects.create(
                employee=employee,
                feedback_type=feedback_data['feedback_type'],
                priority=feedback_data.get('priority', 'medium'),
                subject=feedback_data['subject'],
                message=feedback_data['message'],
                send_to_supervisor=feedback_data.get('send_to_supervisor', True),
                send_to_hr=feedback_data.get('send_to_hr', False),
                is_anonymous=feedback_data.get('is_anonymous', False),
                created_via=feedback_data.get('created_via', 'whatsapp')
            )
            
            # Notificar a destinatarios
            self._notify_feedback_recipients(feedback)
            
            # Crear feedback en sistema ATS si es necesario
            if feedback.send_to_hr:
                self._create_ats_feedback(feedback)
            
            logger.info(f"Feedback creado para {employee.get_full_name()}: {feedback.subject}")
            return feedback
            
        except Exception as e:
            logger.error(f"Error creando feedback: {str(e)}")
            raise
    
    def respond_to_feedback(self, feedback: PayrollFeedback, responder, response_data: Dict[str, Any]) -> bool:
        """
        Responde a un feedback
        
        Args:
            feedback: Feedback a responder
            responder: Usuario que responde
            response_data: Datos de la respuesta
            
        Returns:
            bool: True si se respondió exitosamente
        """
        try:
            feedback.response_message = response_data['message']
            feedback.responded_by = responder
            feedback.response_date = timezone.now()
            
            if response_data.get('is_resolved', False):
                feedback.is_resolved = True
                feedback.resolution_notes = response_data.get('resolution_notes', '')
            
            feedback.save()
            
            # Notificar al empleado
            self._notify_feedback_response(feedback)
            
            logger.info(f"Feedback respondido para {feedback.employee.get_full_name()}")
            return True
            
        except Exception as e:
            logger.error(f"Error respondiendo feedback: {str(e)}")
            return False
    
    def get_employee_feedback_history(self, employee: PayrollEmployee, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene historial de feedback de un empleado
        
        Args:
            employee: Empleado
            limit: Límite de resultados
            
        Returns:
            Lista con historial de feedback
        """
        try:
            feedbacks = PayrollFeedback.objects.filter(
                employee=employee
            ).order_by('-created_at')[:limit]
            
            history = []
            for feedback in feedbacks:
                history.append({
                    'feedback_id': feedback.id,
                    'feedback_type': feedback.get_feedback_type_display(),
                    'subject': feedback.subject,
                    'message': feedback.message,
                    'priority': feedback.get_priority_display(),
                    'is_resolved': feedback.is_resolved,
                    'created_at': feedback.created_at.strftime('%Y-%m-%d %H:%M'),
                    'response_message': feedback.response_message,
                    'response_date': feedback.response_date.strftime('%Y-%m-%d %H:%M') if feedback.response_date else None,
                    'responded_by': feedback.responded_by.get_full_name() if feedback.responded_by else None
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de feedback: {str(e)}")
            return []
    
    def get_company_feedback_analytics(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Obtiene analytics de feedback de la empresa
        
        Args:
            period_days: Días a analizar
            
        Returns:
            Dict con analytics
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=period_days)
            
            # Obtener feedbacks del período
            feedbacks = PayrollFeedback.objects.filter(
                employee__company=self.company,
                created_at__date__range=[start_date, end_date]
            )
            
            # Estadísticas por tipo
            type_stats = feedbacks.values('feedback_type').annotate(
                count=Count('id'),
                resolved_count=Count('id', filter=Q(is_resolved=True)),
                avg_response_time=Avg('response_date' - 'created_at')
            )
            
            # Estadísticas por prioridad
            priority_stats = feedbacks.values('priority').annotate(
                count=Count('id')
            )
            
            # Análisis de resolución
            resolution_stats = {
                'total': feedbacks.count(),
                'resolved': feedbacks.filter(is_resolved=True).count(),
                'pending': feedbacks.filter(is_resolved=False).count(),
                'resolution_rate': 0
            }
            
            if resolution_stats['total'] > 0:
                resolution_stats['resolution_rate'] = (
                    resolution_stats['resolved'] / resolution_stats['total'] * 100
                )
            
            # Análisis por departamento
            department_stats = feedbacks.values('employee__department').annotate(
                count=Count('id'),
                resolved_count=Count('id', filter=Q(is_resolved=True))
            )
            
            # Tendencias temporales
            daily_stats = feedbacks.extra(
                select={'day': 'date(created_at)'}
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')
            
            return {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'days': period_days
                },
                'type_statistics': list(type_stats),
                'priority_statistics': list(priority_stats),
                'resolution_statistics': resolution_stats,
                'department_statistics': list(department_stats),
                'daily_trends': list(daily_stats),
                'total_employees': self.company.employees.filter(is_active=True).count()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de feedback: {str(e)}")
            return {'error': str(e)}
    
    def send_feedback_reminder(self, employee: PayrollEmployee, feedback_type: str = None) -> bool:
        """
        Envía recordatorio de feedback
        
        Args:
            employee: Empleado
            feedback_type: Tipo de feedback específico (opcional)
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            message = "📝 *Recordatorio de Feedback*\n\n"
            message += "Tu opinión es importante para nosotros. "
            message += "¿Tienes algún comentario o sugerencia sobre:\n\n"
            
            if feedback_type:
                message += f"• {self._get_feedback_type_description(feedback_type)}\n"
            else:
                message += "• Horarios y turnos\n"
                message += "• Ambiente laboral\n"
                message += "• Procesos de nómina\n"
                message += "• Beneficios\n"
                message += "• Cualquier otro aspecto\n\n"
            
            message += "Envía tu feedback respondiendo a este mensaje o usa el comando:\n"
            message += "`feedback [tipo] [mensaje]`\n\n"
            message += "Ejemplo: `feedback horarios Necesito ajustar mi horario`"
            
            if employee.whatsapp_number:
                return self.whatsapp_service.send_message(
                    'whatsapp',
                    employee.whatsapp_number,
                    message
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error enviando recordatorio de feedback: {str(e)}")
            return False
    
    def process_whatsapp_feedback(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Procesa feedback recibido vía WhatsApp
        
        Args:
            phone_number: Número de teléfono
            message: Mensaje recibido
            
        Returns:
            Dict con resultado del procesamiento
        """
        try:
            # Buscar empleado por número de WhatsApp
            employee = PayrollEmployee.objects.filter(
                company=self.company,
                whatsapp_number=phone_number
            ).first()
            
            if not employee:
                return {
                    'success': False,
                    'error': 'Empleado no encontrado'
                }
            
            # Parsear mensaje
            parsed_feedback = self._parse_whatsapp_feedback(message)
            
            if not parsed_feedback:
                return {
                    'success': False,
                    'error': 'Formato de mensaje no válido'
                }
            
            # Crear feedback
            feedback = self.create_feedback(employee, {
                'feedback_type': parsed_feedback['type'],
                'subject': parsed_feedback['subject'],
                'message': parsed_feedback['message'],
                'priority': parsed_feedback.get('priority', 'medium'),
                'created_via': 'whatsapp'
            })
            
            # Enviar confirmación
            confirmation_message = f"✅ *Feedback Recibido*\n\n"
            confirmation_message += f"*Tipo:* {feedback.get_feedback_type_display()}\n"
            confirmation_message += f"*Asunto:* {feedback.subject}\n\n"
            confirmation_message += "Gracias por tu feedback. Te responderemos pronto."
            
            self.whatsapp_service.send_message(
                'whatsapp',
                phone_number,
                confirmation_message
            )
            
            return {
                'success': True,
                'feedback_id': feedback.id,
                'message': 'Feedback procesado exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error procesando feedback de WhatsApp: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _notify_feedback_recipients(self, feedback: PayrollFeedback):
        """Notifica a los destinatarios del feedback"""
        try:
            # Notificar a supervisor
            if feedback.send_to_supervisor and feedback.employee.supervisor:
                supervisor_message = f"📝 *Nuevo Feedback de Empleado*\n\n"
                supervisor_message += f"*Empleado:* {feedback.employee.get_full_name()}\n"
                supervisor_message += f"*Tipo:* {feedback.get_feedback_type_display()}\n"
                supervisor_message += f"*Prioridad:* {feedback.get_priority_display()}\n"
                supervisor_message += f"*Asunto:* {feedback.subject}\n\n"
                supervisor_message += f"*Mensaje:*\n{feedback.message}\n\n"
                supervisor_message += "Revisa en el sistema para responder."
                
                # Aquí enviarías la notificación al supervisor
                # self.notification_service.send_notification_to_user(
                #     feedback.employee.supervisor,
                #     'payroll_feedback',
                #     supervisor_message
                # )
            
            # Notificar a RRHH
            if feedback.send_to_hr:
                hr_message = f"📝 *Feedback Requiere Atención de RRHH*\n\n"
                hr_message += f"*Empleado:* {feedback.employee.get_full_name()}\n"
                hr_message += f"*Departamento:* {feedback.employee.department}\n"
                hr_message += f"*Tipo:* {feedback.get_feedback_type_display()}\n"
                hr_message += f"*Prioridad:* {feedback.get_priority_display()}\n"
                hr_message += f"*Asunto:* {feedback.subject}\n\n"
                hr_message += f"*Mensaje:*\n{feedback.message}"
                
                # Aquí enviarías la notificación a RRHH
                # self.notification_service.send_notification_to_hr(
                #     'payroll_feedback_hr',
                #     hr_message
                # )
                
        except Exception as e:
            logger.error(f"Error notificando destinatarios: {str(e)}")
    
    def _notify_feedback_response(self, feedback: PayrollFeedback):
        """Notifica respuesta al feedback"""
        try:
            if not feedback.employee.whatsapp_number:
                return
            
            message = f"📝 *Respuesta a tu Feedback*\n\n"
            message += f"*Asunto:* {feedback.subject}\n"
            message += f"*Respondido por:* {feedback.responded_by.get_full_name()}\n"
            message += f"*Fecha:* {feedback.response_date.strftime('%d/%m/%Y %H:%M')}\n\n"
            message += f"*Respuesta:*\n{feedback.response_message}\n\n"
            
            if feedback.is_resolved:
                message += "✅ *Este feedback ha sido marcado como resuelto*"
            else:
                message += "🔄 *Este feedback está siendo procesado*"
            
            self.whatsapp_service.send_message(
                'whatsapp',
                feedback.employee.whatsapp_number,
                message
            )
            
        except Exception as e:
            logger.error(f"Error notificando respuesta: {str(e)}")
    
    def _create_ats_feedback(self, payroll_feedback: PayrollFeedback):
        """Crea feedback en el sistema ATS"""
        try:
            # Mapear tipos de feedback
            feedback_type_mapping = {
                'schedule': 'workplace',
                'supervisor': 'management',
                'hr': 'hr_process',
                'payroll': 'compensation',
                'benefits': 'benefits',
                'workplace': 'workplace',
                'general': 'general'
            }
            
            ats_feedback_type = feedback_type_mapping.get(
                payroll_feedback.feedback_type, 'general'
            )
            
            # Crear feedback en ATS
            ats_feedback = ServiceFeedback.objects.create(
                stage='ongoing',
                service_type=ats_feedback_type,
                token=f"payroll_{payroll_feedback.id}",
                contact_name=payroll_feedback.employee.get_full_name(),
                contact_email=payroll_feedback.employee.email,
                contact_phone=payroll_feedback.employee.phone,
                company_name=payroll_feedback.employee.company.name,
                comments=payroll_feedback.message,
                rating=None  # No aplica para feedback de empleados
            )
            
            # Crear feedback en curso
            OngoingServiceFeedback.objects.create(
                base_feedback=ats_feedback,
                urgent_issues=payroll_feedback.message if payroll_feedback.priority in ['high', 'urgent'] else '',
                improvement_suggestions=payroll_feedback.message
            )
            
            logger.info(f"Feedback ATS creado para {payroll_feedback.employee.get_full_name()}")
            
        except Exception as e:
            logger.error(f"Error creando feedback ATS: {str(e)}")
    
    def _parse_whatsapp_feedback(self, message: str) -> Optional[Dict[str, Any]]:
        """Parsea mensaje de WhatsApp para extraer feedback"""
        try:
            # Comando: feedback [tipo] [mensaje]
            if message.lower().startswith('feedback'):
                parts = message.split(' ', 2)
                if len(parts) >= 3:
                    feedback_type = parts[1].lower()
                    feedback_message = parts[2]
                    
                    # Mapear tipos
                    type_mapping = {
                        'horarios': 'schedule',
                        'turnos': 'schedule',
                        'supervisor': 'supervisor',
                        'rrhh': 'hr',
                        'nomina': 'payroll',
                        'beneficios': 'benefits',
                        'ambiente': 'workplace',
                        'general': 'general'
                    }
                    
                    mapped_type = type_mapping.get(feedback_type, 'general')
                    
                    return {
                        'type': mapped_type,
                        'subject': f"Feedback vía WhatsApp - {feedback_type.title()}",
                        'message': feedback_message,
                        'priority': 'medium'
                    }
            
            # Mensaje libre - intentar detectar tipo
            message_lower = message.lower()
            
            if any(word in message_lower for word in ['horario', 'turno', 'hora']):
                feedback_type = 'schedule'
            elif any(word in message_lower for word in ['supervisor', 'jefe', 'manager']):
                feedback_type = 'supervisor'
            elif any(word in message_lower for word in ['nomina', 'pago', 'salario']):
                feedback_type = 'payroll'
            elif any(word in message_lower for word in ['beneficio', 'prestacion']):
                feedback_type = 'benefits'
            elif any(word in message_lower for word in ['ambiente', 'clima', 'trabajo']):
                feedback_type = 'workplace'
            else:
                feedback_type = 'general'
            
            return {
                'type': feedback_type,
                'subject': f"Feedback vía WhatsApp - {feedback_type.title()}",
                'message': message,
                'priority': 'medium'
            }
            
        except Exception as e:
            logger.error(f"Error parseando feedback de WhatsApp: {str(e)}")
            return None
    
    def _get_feedback_type_description(self, feedback_type: str) -> str:
        """Obtiene descripción de tipo de feedback"""
        descriptions = {
            'schedule': 'Horarios y turnos de trabajo',
            'supervisor': 'Relación con tu supervisor',
            'hr': 'Procesos de Recursos Humanos',
            'payroll': 'Nómina y pagos',
            'benefits': 'Beneficios y prestaciones',
            'workplace': 'Ambiente laboral',
            'general': 'Cualquier otro aspecto'
        }
        return descriptions.get(feedback_type, 'Aspectos generales') 