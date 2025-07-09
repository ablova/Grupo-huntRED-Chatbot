"""
Servicio de recordatorios automáticos para evaluaciones y requisitos de nómina
Permite programar, gestionar y optimizar recordatorios automáticos para evaluaciones NOM 35
y otros requisitos con plazos específicos.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from django.utils import timezone
from django.db.models import Q, F, Count, Case, When, Value, IntegerField
from django.db import transaction

from ..models import PayrollCompany, PayrollEmployee
from app.ats.chatbot.workflow.assessments.nom35.models import AssessmentNOM35
from app.models import Person, BusinessUnit
from .assessment_integration_service import AssessmentIntegrationService
from .unified_whatsapp_service import UnifiedWhatsAppService

logger = logging.getLogger(__name__)

class AssessmentReminderService:
    """
    Servicio para gestionar recordatorios automáticos de assessments
    y optimizar la tasa de respuesta mediante recordatorios inteligentes.
    """
    
    def __init__(self, company: PayrollCompany):
        """
        Inicializa el servicio con la empresa especificada
        
        Args:
            company: Instancia de PayrollCompany a la que pertenece el servicio
        """
        self.company = company
        self.business_unit = company.business_unit
        self.assessment_service = AssessmentIntegrationService(company)
        self.whatsapp_service = UnifiedWhatsAppService(company)
        
    def schedule_assessment_reminders(self) -> Dict[str, Any]:
        """
        Programa recordatorios automáticos para empleados que necesitan completar assessments
        
        Returns:
            Información sobre recordatorios programados
        """
        # Obtener empleados que requieren assessments
        employees_needing_nom35 = self.assessment_service.get_employees_requiring_nom35(days_threshold=45)
        
        reminders_scheduled = []
        
        for item in employees_needing_nom35:
            employee = item["employee"]
            status = item["status"]
            
            # Determinar el mejor momento para el recordatorio basado en análisis de comportamiento
            reminder_date = self._calculate_optimal_reminder_date(employee, status)
            
            if reminder_date:
                # Registrar el recordatorio en la base de datos (implementación simulada)
                reminder_record = {
                    "employee_id": employee.id,
                    "assessment_type": "NOM35",
                    "scheduled_date": reminder_date,
                    "urgency": status["urgency"],
                    "days_remaining": status["days_remaining"]
                }
                
                reminders_scheduled.append(reminder_record)
                
                logger.info(f"Recordatorio programado para {employee.person.full_name}: NOM 35 - {reminder_date}")
                
        return {
            "reminders_scheduled": len(reminders_scheduled),
            "reminders": reminders_scheduled
        }
    
    def _calculate_optimal_reminder_date(self, employee: PayrollEmployee, status: Dict[str, Any]) -> Optional[datetime]:
        """
        Calcula la fecha óptima para enviar un recordatorio basado en análisis de comportamiento
        
        Args:
            employee: Empleado para programar recordatorio
            status: Estado actual de cumplimiento
            
        Returns:
            Fecha óptima para el recordatorio, o None si no se debe programar
        """
        now = timezone.now()
        
        # Si la urgencia es alta, programar recordatorio inmediato
        if status["urgency"] == "alta":
            return now
        
        # Si urgencia media, programar para la próxima semana
        if status["urgency"] == "media":
            # Analizar día de la semana más efectivo (simulado, en una implementación real usaríamos ML)
            day_offset = 2  # Por defecto, en 2 días
            return now + timedelta(days=day_offset)
        
        # Si urgencia baja, programar recordatorio un mes antes del vencimiento
        if status["days_remaining"] and status["days_remaining"] > 30:
            target_date = now + timedelta(days=status["days_remaining"] - 30)
            return target_date
            
        return None
    
    def send_pending_reminders(self) -> Dict[str, Any]:
        """
        Envía recordatorios pendientes programados para hoy
        
        Returns:
            Resultado de los recordatorios enviados
        """
        # Simulación de recordatorios pendientes
        # En implementación real, se obtendrían de la base de datos
        
        now = timezone.now()
        
        # Obtener empleados con recordatorios pendientes para hoy
        employees_needing_nom35 = self.assessment_service.get_employees_requiring_nom35()
        employees_for_reminder = []
        
        # Filtrar solo empleados que deberían recibir recordatorio hoy
        # (en implementación real, esto sería una consulta a la tabla de recordatorios)
        for item in employees_needing_nom35:
            employee = item["employee"]
            status = item["status"]
            
            # Simulamos un criterio simple para determinar si se envía hoy
            if status["urgency"] == "alta" or (status["days_remaining"] and status["days_remaining"] <= 7):
                employees_for_reminder.append(item)
        
        # Enviar recordatorios
        reminders_sent = []
        
        with transaction.atomic():
            for item in employees_for_reminder:
                employee = item["employee"]
                
                try:
                    # Generar mensaje de recordatorio personalizado
                    reminder_message = self._generate_reminder_message(employee, item["status"])
                    
                    # En una implementación real, aquí enviaríamos el mensaje por WhatsApp
                    # self.whatsapp_service.send_message_to_employee(employee, reminder_message["message"], reminder_message["options"])
                    
                    # Registrar el recordatorio enviado
                    reminder_sent = {
                        "employee_id": employee.id,
                        "employee_name": employee.person.full_name,
                        "assessment_type": "NOM35",
                        "sent_date": now,
                        "status": "sent"
                    }
                    
                    reminders_sent.append(reminder_sent)
                    
                    logger.info(f"Recordatorio enviado a {employee.person.full_name}: NOM 35")
                    
                except Exception as e:
                    logger.error(f"Error al enviar recordatorio a {employee.person.full_name}: {str(e)}")
                    
        return {
            "reminders_sent": len(reminders_sent),
            "reminders": reminders_sent
        }
    
    def _generate_reminder_message(self, employee: PayrollEmployee, status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un mensaje de recordatorio personalizado basado en el perfil del empleado
        
        Args:
            employee: Empleado para generar recordatorio
            status: Estado actual de cumplimiento
            
        Returns:
            Mensaje y opciones para el recordatorio
        """
        # Determinar nivel de personalización
        is_first_reminder = True  # En implementación real, verificaríamos si es el primer recordatorio
        
        # Opciones de respuesta rápida
        options = [
            {"text": "✅ Comenzar ahora", "action": "start_nom35"},
            {"text": "⏰ Programar para después", "action": "schedule_nom35"},
            {"text": "❓ Más información", "action": "info_nom35"}
        ]
        
        # Mensaje con diferentes niveles de urgencia
        if status["urgency"] == "alta":
            if not status["last_assessment_date"]:
                # Nunca ha completado la evaluación
                message = f"""⚠️ *Recordatorio: Evaluación NOM 35 pendiente*

Hola {employee.person.first_name},

Aún no has completado la evaluación NOM 35 requerida por normativa laboral. 
Esta evaluación es obligatoria y nos ayuda a asegurar un ambiente de trabajo saludable.

¿Te gustaría comenzar ahora? Solo tomará unos minutos.
"""
            else:
                # Ha pasado más de un año
                last_date = status["last_assessment_date"].strftime("%d/%m/%Y")
                message = f"""⚠️ *Recordatorio: Actualización NOM 35 requerida*

Hola {employee.person.first_name},

Tu última evaluación NOM 35 se realizó el {last_date} y necesita ser actualizada.
La normativa requiere completar esta evaluación anualmente.

¿Te gustaría actualizarla ahora?
"""
        else:
            # Recordatorio preventivo
            days = status["days_remaining"]
            message = f"""📋 *Recordatorio: NOM 35 próxima a vencer*

Hola {employee.person.first_name},

Tu evaluación NOM 35 vencerá en {days} días. Para mantenernos al día con la normativa laboral, te recomendamos completarla antes del vencimiento.

¿Deseas programarla ahora?
"""
        
        return {
            "message": message,
            "options": options
        }
    
    def get_compliance_analytics(self) -> Dict[str, Any]:
        """
        Genera analíticas avanzadas sobre el cumplimiento de evaluaciones
        
        Returns:
            Analíticas detalladas sobre tasas de completitud
        """
        # Estadísticas generales
        stats = self.assessment_service.get_nom35_completion_statistics()
        
        # En implementación real, aquí haríamos análisis más avanzados:
        # - Tendencias de completitud
        # - Efectividad de recordatorios
        # - Tiempo promedio de respuesta
        # - Perfiles de empleados con mejor/peor tasa de completitud
        
        # Simulamos datos adicionales para el dashboard
        completion_by_department = {
            "RH": 95.0,
            "Ventas": 78.5,
            "Operaciones": 82.3,
            "Administración": 91.2,
            "TI": 88.7
        }
        
        response_time_distribution = {
            "mismo_día": 35,
            "1_3_días": 25,
            "4_7_días": 20,
            "más_de_7_días": 20
        }
        
        return {
            "general_stats": stats,
            "completion_by_department": completion_by_department,
            "response_time_distribution": response_time_distribution,
            "as_of_date": timezone.now().date()
        }
