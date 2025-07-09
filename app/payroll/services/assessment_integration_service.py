"""
Servicio para integración de assessments en el sistema de nómina
Permite invitar, programar y dar seguimiento a los assessments requeridos
como NOM 35 para todos los empleados gestionados por la nómina.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from django.utils import timezone
from django.db.models import Q

from ..models import PayrollCompany, PayrollEmployee
from app.ats.chatbot.workflow.assessments.nom35.nom35_evaluation import NOM35EvaluationWorkflow
from app.ats.chatbot.workflow.assessments.nom35.models import AssessmentNOM35, AssessmentNOM35Result
from app.ats.chatbot.handlers.assessment_handlers import NOM35AssessmentHandler
from app.models import Person, BusinessUnit

logger = logging.getLogger(__name__)

class AssessmentIntegrationService:
    """
    Servicio para integrar assessments con el sistema de nómina,
    particularmente para la gestión de NOM 35 y otros assessments
    obligatorios o recomendados.
    """
    
    def __init__(self, company: PayrollCompany):
        """
        Inicializa el servicio con la empresa especificada
        
        Args:
            company: Instancia de PayrollCompany a la que pertenece el servicio
        """
        self.company = company
        self.business_unit = company.business_unit
        
    def check_nom35_requirements(self, employee: PayrollEmployee) -> Dict[str, Any]:
        """
        Verifica el estado de cumplimiento de NOM 35 para un empleado
        y determina si necesita realizarlo
        
        Args:
            employee: Empleado a verificar
            
        Returns:
            Diccionario con información sobre el estado de NOM 35 del empleado
        """
        person = employee.person
        
        # Buscar última evaluación NOM 35 completada
        try:
            last_assessment = AssessmentNOM35.objects.filter(
                person=person
            ).order_by('-date_taken').first()
        except Exception as e:
            logger.error(f"Error al buscar evaluación NOM 35 para {person}: {str(e)}")
            last_assessment = None
            
        # Determinar si necesita realizar la evaluación
        current_date = timezone.now()
        requires_assessment = False
        days_remaining = None
        last_date = None
        
        if not last_assessment:
            # Nunca ha realizado la evaluación
            requires_assessment = True
            urgency = "alta"
        else:
            # Verificar si ha pasado un año desde la última evaluación
            last_date = last_assessment.date_taken
            one_year_after = last_date + timedelta(days=365)
            
            if current_date >= one_year_after:
                requires_assessment = True
                urgency = "alta"
            else:
                # Calcular días restantes para que se cumpla un año
                days_remaining = (one_year_after - current_date).days
                
                if days_remaining <= 30:
                    urgency = "media"
                else:
                    urgency = "baja"
        
        return {
            "requires_assessment": requires_assessment,
            "last_assessment_date": last_date,
            "days_remaining": days_remaining,
            "urgency": urgency
        }
    
    def get_employees_requiring_nom35(self, days_threshold: int = 30) -> List[PayrollEmployee]:
        """
        Obtiene lista de empleados que necesitan realizar NOM 35
        
        Args:
            days_threshold: Umbral de días para considerar necesidad próxima
            
        Returns:
            Lista de empleados que necesitan NOM 35
        """
        all_employees = PayrollEmployee.objects.filter(company=self.company).select_related('person')
        requiring_assessment = []
        
        for employee in all_employees:
            status = self.check_nom35_requirements(employee)
            
            # Incluir si requiere assessment o está próximo
            if status["requires_assessment"] or (status["days_remaining"] is not None and status["days_remaining"] <= days_threshold):
                requiring_assessment.append({
                    "employee": employee,
                    "status": status
                })
        
        # Ordenar por urgencia y días restantes
        return sorted(requiring_assessment, 
                      key=lambda x: (0 if x["status"]["requires_assessment"] else 1, 
                                     x["status"]["days_remaining"] or 0))
    
    def schedule_nom35_assessment(self, employee: PayrollEmployee, 
                                scheduled_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Programa una evaluación NOM 35 para un empleado
        
        Args:
            employee: Empleado para programar la evaluación
            scheduled_date: Fecha programada (opcional, por defecto es ahora)
            
        Returns:
            Información sobre la evaluación programada
        """
        person = employee.person
        
        if not scheduled_date:
            scheduled_date = timezone.now()
            
        # Crear nueva evaluación programada
        try:
            assessment = AssessmentNOM35(
                person=person,
                business_unit=self.business_unit,
                responses={},
                score=0,
                risk_level="pendiente",
                scheduled_by_onboarding=False,
                scheduled_date=scheduled_date
            )
            assessment.save()
            
            logger.info(f"Evaluación NOM 35 programada para {person} en {scheduled_date}")
            return {
                "success": True,
                "assessment_id": assessment.id,
                "employee": employee,
                "scheduled_date": scheduled_date
            }
        except Exception as e:
            logger.error(f"Error al programar evaluación NOM 35: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_nom35_whatsapp_invitation(self, employee: PayrollEmployee) -> Dict[str, Any]:
        """
        Crea una invitación para completar NOM 35 por WhatsApp
        
        Args:
            employee: Empleado a invitar
            
        Returns:
            Mensaje para enviar por WhatsApp con la invitación
        """
        person = employee.person
        
        # Determinar el rol para la evaluación NOM 35
        is_leader = employee.role in ["supervisor", "manager", "director", "hr"]
        profile = "leader" if is_leader else "employee"
        
        # Crear mensaje de invitación
        message = f"""📋 *Evaluación NOM 35 Requerida*

Como parte del cumplimiento de la normativa laboral, necesitamos que completes la evaluación NOM 35.

Esta evaluación es obligatoria *una vez al año* y nos permite:
• Identificar factores de riesgo psicosocial
• Mejorar el ambiente laboral
• Cumplir con regulaciones oficiales

La evaluación toma aproximadamente 15-20 minutos.

¿Deseas comenzar ahora o programarla para después?
"""
        
        # Opciones de respuesta rápida
        quick_replies = [
            {"text": "✅ Comenzar ahora", "action": "start_nom35"},
            {"text": "⏰ Programar para después", "action": "schedule_nom35"},
            {"text": "❓ Más información", "action": "info_nom35"}
        ]
        
        return {
            "success": True,
            "message": message,
            "quick_replies": quick_replies,
            "profile": profile,
            "employee": employee
        }
    
    def start_nom35_assessment(self, employee: PayrollEmployee, phone_number: str) -> Dict[str, Any]:
        """
        Inicia una evaluación NOM 35 por WhatsApp
        
        Args:
            employee: Empleado para iniciar evaluación
            phone_number: Número de teléfono para el canal de WhatsApp
            
        Returns:
            Respuesta para iniciar la evaluación
        """
        # Programar el assessment
        schedule_result = self.schedule_nom35_assessment(employee)
        
        if not schedule_result["success"]:
            return {
                "success": False,
                "message": f"❌ Lo sentimos, no pudimos iniciar tu evaluación NOM 35. Por favor, intenta más tarde o contacta a RH."
            }
        
        # Determinar el perfil para el flujo (empleado o líder)
        is_leader = employee.role in ["supervisor", "manager", "director", "hr"]
        profile = "leader" if is_leader else "employee"
        
        # Crear el flujo de evaluación
        assessment_workflow = NOM35EvaluationWorkflow(profile=profile, channel="whatsapp")
        
        # Obtener la primera pregunta
        first_question = assessment_workflow.get_next_question()
        
        # Mensaje de introducción
        intro_message = f"""🚀 *Iniciando Evaluación NOM 35*

Responderás una serie de preguntas sobre tu experiencia laboral.
• Todas las respuestas son confidenciales
• Por favor responde con sinceridad
• Puedes pausar en cualquier momento enviando "pausa"

Primera pregunta:
"""
        
        question_message = f"{first_question['text']}"
        
        # Preparar opciones para WhatsApp
        options = []
        for option_value, option_text in first_question['options'].items():
            options.append({"text": f"{option_text}", "action": f"nom35_a_{option_value}"})
        
        # Guardar estado de la evaluación en progreso
        # (Esta lógica continuaría en el manejador de WhatsApp)
        
        return {
            "success": True,
            "message": f"{intro_message}\n\n{question_message}",
            "quick_replies": options,
            "metadata": {
                "assessment_id": schedule_result["assessment_id"],
                "workflow": "nom35",
                "profile": profile,
                "current_section": 0,
                "current_question": 0,
                "total_questions": assessment_workflow.total_questions
            }
        }
    
    def get_nom35_completion_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de cumplimiento de NOM 35 en la empresa
        
        Returns:
            Estadísticas de cumplimiento
        """
        # Total de empleados
        total_employees = PayrollEmployee.objects.filter(company=self.company).count()
        
        # Empleados con evaluación vigente
        one_year_ago = timezone.now() - timedelta(days=365)
        
        # Obtener IDs de personas asociadas a empleados de la empresa
        person_ids = PayrollEmployee.objects.filter(
            company=self.company
        ).values_list('person_id', flat=True)
        
        # Contar evaluaciones vigentes
        valid_assessments = AssessmentNOM35.objects.filter(
            person_id__in=person_ids,
            date_taken__gte=one_year_ago
        ).count()
        
        # Calcular porcentaje
        compliance_percentage = (valid_assessments / total_employees * 100) if total_employees > 0 else 0
        
        return {
            "total_employees": total_employees,
            "compliant_employees": valid_assessments,
            "compliance_percentage": round(compliance_percentage, 1),
            "pending_employees": total_employees - valid_assessments,
            "as_of_date": timezone.now().date()
        }
    
    def generate_nom35_compliance_report(self) -> Dict[str, Any]:
        """
        Genera un reporte detallado del estado de cumplimiento de NOM 35
        
        Returns:
            Reporte de cumplimiento
        """
        # Estadísticas generales
        stats = self.get_nom35_completion_statistics()
        
        # Lista de empleados que requieren la evaluación
        pending_employees = self.get_employees_requiring_nom35()
        
        # Formatear para el reporte
        report = {
            "company_name": self.company.name,
            "statistics": stats,
            "pending_employees": [
                {
                    "name": item["employee"].person.full_name,
                    "position": item["employee"].position,
                    "department": item["employee"].department,
                    "status": "Pendiente" if item["status"]["requires_assessment"] else f"Próximo ({item['status']['days_remaining']} días)",
                    "urgency": item["status"]["urgency"]
                }
                for item in pending_employees
            ]
        }
        
        return report
