# /home/pablo/app/com/feedback/ongoing_tracker.py
"""
Sistema de seguimiento y retroalimentación para servicios en curso.

Este módulo permite:
1. Enviar encuestas automáticas en momentos clave durante la prestación del servicio
2. Recolectar retroalimentación sobre la experiencia del cliente mientras el servicio está activo
3. Identificar áreas problemáticas que requieren atención inmediata
4. Realizar ajustes en tiempo real para asegurar la satisfacción del cliente
"""
from typing import Dict, List, Optional, Union
import asyncio
from datetime import datetime, timedelta
import json
import logging
import secrets
import uuid

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
import redis
import requests

from app.models import Opportunity, Contract, Company, Contact
from app.ats.feedback.feedback_models import ServiceFeedback, OngoingServiceFeedback, ServiceImprovementSuggestion

logger = logging.getLogger(__name__)

class OngoingServiceTracker:
    """
    Gestiona el seguimiento y retroalimentación de servicios activos.
    
    Envía encuestas automáticas en momentos clave durante la prestación del servicio
    y recolecta retroalimentación para realizar ajustes en tiempo real.
    """
    
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.redis_prefix = "ongoing_service_tracker:"
        
        # Calendario.com API para Pablo (configurable desde settings)
        self.calendly_url = getattr(settings, "MANAGING_DIRECTOR_CALENDAR_URL", 
                                  "https://huntred.com/agenda-pllh/")
        
        # Preguntas predefinidas - enfocadas en experiencia durante el servicio
        self.ongoing_questions = [
            {
                "id": "progress_satisfaction",
                "question": "¿Qué tan satisfecho está con el progreso del servicio hasta ahora?",
                "options": ["5 - Muy satisfecho", "4 - Satisfecho", "3 - Neutral", "2 - Insatisfecho", "1 - Muy insatisfecho"],
                "type": "scale"
            },
            {
                "id": "communication_rating",
                "question": "¿Cómo calificaría la comunicación con nuestro equipo?",
                "options": ["5 - Excelente", "4 - Buena", "3 - Aceptable", "2 - Deficiente", "1 - Muy deficiente"],
                "type": "scale"
            },
            {
                "id": "consultant_rating",
                "question": "¿Cómo evaluaría el desempeño de nuestro consultor?",
                "options": ["5 - Excelente", "4 - Bueno", "3 - Aceptable", "2 - Deficiente", "1 - Muy deficiente"],
                "type": "scale"
            },
            {
                "id": "urgent_issues",
                "question": "¿Hay algún problema urgente que necesitemos resolver?",
                "type": "text"
            },
            {
                "id": "improvement_suggestions",
                "question": "¿Qué podríamos mejorar para hacer este servicio más valioso para usted?",
                "type": "text"
            },
            {
                "id": "new_services",
                "question": "¿Qué otros servicios le gustaría que Grupo huntRED® ofreciera?",
                "type": "text"
            },
            {
                "id": "meeting_request",
                "question": "¿Desea hablar directamente con nuestro Managing Director?",
                "description": "Reserve una reunión personal con Pablo Lelo de Larrea H. - Sr. Managing Partner Grupo huntRED® para discutir cualquier aspecto del servicio o resolver problemas específicos.",
                "button_text": "Agendar Reunión",
                "type": "meeting_request"
            }
        ]
    
    def generate_feedback_token(self, opportunity_id: int, milestone: int = 1) -> str:
        """Genera un token único para identificar respuestas de retroalimentación."""
        token = secrets.token_urlsafe(32)
        # Guardar relación token-oportunidad en Redis por 60 días
        token_key = f"{self.redis_prefix}token:{token}"
        token_data = {
            "opportunity_id": opportunity_id,
            "milestone": milestone
        }
        self.redis.set(token_key, json.dumps(token_data), ex=60*60*24*60)  # 60 días
        return token
    
    async def schedule_feedback_request(self, opportunity_id: int, milestone: int = 1, 
                                      delay_days: int = 7, contact_email: str = None,
                                      progress_percentage: int = None):
        """
        Programa una solicitud de retroalimentación para un momento específico
        durante la prestación del servicio.
        """
        try:
            # Obtener datos de la oportunidad
            opportunity = Opportunity.objects.get(id=opportunity_id)
            
            # Verificar si hay contrato activo
            if not hasattr(opportunity, 'service_contract') or not opportunity.service_contract.is_active:
                logger.warning(f"No se puede programar seguimiento: Oportunidad {opportunity_id} sin contrato activo")
                return False
            
            # Obtener información de contacto
            company = opportunity.company
            contact_email = contact_email or opportunity.contact.email if opportunity.contact else None
            
            if not contact_email:
                logger.warning(f"No se puede programar seguimiento: Oportunidad {opportunity_id} sin email de contacto")
                return False
            
            # Generar token único para esta solicitud
            token = self.generate_feedback_token(opportunity_id, milestone)
            
            # Determinar el progreso si no se proporciona
            if progress_percentage is None:
                # Lógica para inferir progreso basado en hitos y fechas
                contract = opportunity.service_contract
                start_date = contract.start_date
                end_date = contract.end_date or (start_date + timedelta(days=90))  # Valor por defecto
                total_days = (end_date - start_date).days
                days_elapsed = (timezone.now().date() - start_date).days
                
                if total_days > 0:
                    progress_percentage = min(int((days_elapsed / total_days) * 100), 99)
                else:
                    progress_percentage = 50  # Valor por defecto
            
            # Guardar programación en Redis
            schedule_key = f"{self.redis_prefix}scheduled:{opportunity_id}:{milestone}"
            schedule_data = {
                "opportunity_id": opportunity_id,
                "token": token,
                "milestone": milestone,
                "company_name": company.name,
                "contact_email": contact_email,
                "service_type": opportunity.service_type,
                "progress_percentage": progress_percentage,
                "send_after": (timezone.now() + timedelta(days=delay_days)).isoformat(),
                "status": "scheduled"
            }
            
            self.redis.set(schedule_key, json.dumps(schedule_data), ex=60*60*24*60)  # 60 días
            
            logger.info(f"Retroalimentación programada para servicio en curso ID:{opportunity_id}, Hito:{milestone}")
            return True
            
        except Opportunity.DoesNotExist:
            logger.error(f"No se encontró la oportunidad con ID {opportunity_id}")
            return False
        except Exception as e:
            logger.error(f"Error al programar retroalimentación de servicio en curso: {str(e)}")
            return False
    
    async def send_feedback_requests(self):
        """
        Busca retroalimentaciones programadas que deban enviarse hoy y las envía.
        Esta función debería ejecutarse diariamente mediante una tarea programada.
        """
        now = timezone.now()
        pattern = f"{self.redis_prefix}scheduled:*"
        
        # Buscar todas las programaciones en Redis
        for key in self.redis.scan_iter(match=pattern):
            try:
                data = json.loads(self.redis.get(key))
                
                # Verificar si ya es hora de enviar
                send_after = datetime.fromisoformat(data["send_after"])
                if now < send_after or data["status"] != "scheduled":
                    continue
                
                # Enviar solicitud de retroalimentación
                success = await self._send_feedback_email(data)
                
                # Actualizar estado
                if success:
                    data["status"] = "sent"
                    data["sent_at"] = now.isoformat()
                    self.redis.set(key, json.dumps(data), ex=60*60*24*60)  # 60 días más
                    logger.info(f"Enviada solicitud de retroalimentación de servicio en curso para oportunidad {data['opportunity_id']}, hito {data['milestone']}")
            except Exception as e:
                logger.error(f"Error procesando clave de Redis {key}: {str(e)}")
    
    async def _send_feedback_email(self, data: Dict) -> bool:
        """Envía email de solicitud de retroalimentación para servicio en curso."""
        try:
            opportunity_id = data["opportunity_id"]
            token = data["token"]
            milestone = data["milestone"]
            company_name = data["company_name"]
            contact_email = data["contact_email"]
            progress_percentage = data.get("progress_percentage", 50)
            
            # Personalizar el asunto según el hito/progreso
            if progress_percentage < 25:
                subject_prefix = "Primeras impresiones"
            elif progress_percentage < 50:
                subject_prefix = "Evaluación intermedia"
            elif progress_percentage < 75:
                subject_prefix = "Avance significativo"
            else:
                subject_prefix = "Etapa final"
            
            # Generar URL única para retroalimentación
            feedback_url = f"{settings.SITE_URL}{reverse('feedback:ongoing_feedback', args=[token])}"
            
            # Preparar email
            context = {
                "opportunity_id": opportunity_id,
                "token": token,
                "milestone": milestone,
                "company_name": company_name,
                "progress_percentage": progress_percentage,
                "feedback_url": feedback_url,
                "feedback_questions": self.ongoing_questions,
                "managing_director_calendar": self.calendly_url
            }
            
            subject = f"{subject_prefix} - Su opinión sobre el servicio de Grupo huntRED®"
            html_message = render_to_string("emails/ongoing_feedback_request.html", context)
            text_message = render_to_string("emails/ongoing_feedback_request.txt", context)
            
            # Enviar email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contact_email],
                html_message=html_message,
                fail_silently=False
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar solicitud de retroalimentación de servicio en curso: {str(e)}")
            return False
    
    async def process_feedback(self, token: str, feedback_data: Dict) -> Optional[ServiceFeedback]:
        """
        Procesa la retroalimentación recibida sobre un servicio en curso
        y la almacena para análisis.
        """
        # Validar token
        token_key = f"{self.redis_prefix}token:{token}"
        token_data_json = self.redis.get(token_key)
        
        if not token_data_json:
            logger.warning(f"Token inválido o expirado: {token}")
            return None
        
        try:
            token_data = json.loads(token_data_json)
            opportunity_id = token_data.get("opportunity_id")
            milestone = token_data.get("milestone", 1)
            
            opportunity = Opportunity.objects.get(id=opportunity_id)
            
            # Determinar si ya existe un feedback para esta oportunidad y etapa
            try:
                existing_feedback = ServiceFeedback.objects.get(
                    opportunity=opportunity,
                    stage='ongoing',
                    token=token
                )
                # Actualizar existente
                base_feedback = existing_feedback
                base_feedback.rating = feedback_data.get("rating")
                base_feedback.comments = feedback_data.get("comments")
                base_feedback.suggested_services = feedback_data.get("new_services")
                base_feedback.meeting_requested = feedback_data.get("meeting_requested", False)
                base_feedback.save()
                
                # Actualizar la parte específica
                ongoing_feedback = base_feedback.ongoing_feedback
                
            except ServiceFeedback.DoesNotExist:
                # Crear nuevo feedback base
                base_feedback = ServiceFeedback(
                    opportunity=opportunity,
                    company=opportunity.company,
                    stage='ongoing',
                    service_type=opportunity.service_type,
                    token=token,
                    contact_name=opportunity.contact.name if opportunity.contact else "Cliente",
                    contact_email=opportunity.contact.email if opportunity.contact else "",
                    company_name=opportunity.company.name,
                    rating=feedback_data.get("rating"),
                    comments=feedback_data.get("comments"),
                    suggested_services=feedback_data.get("new_services"),
                    meeting_requested=feedback_data.get("meeting_requested", False)
                )
                base_feedback.save()
                
                # Crear la parte específica
                ongoing_feedback = OngoingServiceFeedback(
                    base_feedback=base_feedback,
                    milestone_number=milestone
                )
            
            # Actualizar datos específicos de servicio en curso
            ongoing_feedback.progress_satisfaction = feedback_data.get("progress_satisfaction")
            ongoing_feedback.communication_rating = feedback_data.get("communication_rating")
            ongoing_feedback.consultant_rating = feedback_data.get("consultant_rating")
            ongoing_feedback.urgent_issues = feedback_data.get("urgent_issues")
            ongoing_feedback.improvement_suggestions = feedback_data.get("improvement_suggestions")
            ongoing_feedback.service_progress = feedback_data.get("progress_percentage", 50)
            ongoing_feedback.save()
            
            # Si hay problemas urgentes, enviar notificación inmediata
            urgent_issues = feedback_data.get("urgent_issues")
            if urgent_issues and len(urgent_issues.strip()) > 10:
                self._notify_urgent_issue(base_feedback, urgent_issues)
            
            # Si se solicitó una reunión, crear la solicitud
            if base_feedback.meeting_requested:
                self._create_meeting_request(base_feedback, feedback_data)
            
            # Si hay sugerencias de nuevos servicios, registrarlas
            new_services = feedback_data.get("new_services")
            if new_services and len(new_services.strip()) > 10:
                self._register_service_suggestion(base_feedback, new_services)
            
            logger.info(f"Procesada retroalimentación de servicio en curso para oportunidad {opportunity_id}, hito {milestone}")
            return base_feedback
            
        except Exception as e:
            logger.error(f"Error al procesar retroalimentación de servicio en curso: {str(e)}")
            return None
    
    def _notify_urgent_issue(self, feedback: ServiceFeedback, urgent_issues: str):
        """Notifica a los responsables sobre problemas urgentes reportados."""
        try:
            # Determinar a quién notificar
            project_manager_email = None
            if hasattr(feedback.opportunity, 'assigned_to') and feedback.opportunity.assigned_to:
                project_manager_email = feedback.opportunity.assigned_to.email
            
            # Si no hay PM asignado, enviar al Managing Director
            if not project_manager_email:
                project_manager_email = getattr(settings, "MANAGING_DIRECTOR_EMAIL", "pablo@huntred.com")
            
            # Enviar notificación
            subject = f"⚠️ URGENTE: Problema reportado por {feedback.company_name}"
            message = (
                f"Se ha reportado un problema urgente en el servicio para {feedback.company_name}.\n\n"
                f"Detalles del problema:\n{urgent_issues}\n\n"
                f"Contacto del cliente: {feedback.contact_name} ({feedback.contact_email})\n"
                f"Servicio: {feedback.get_service_type_display()}\n\n"
                f"Por favor contacte al cliente lo antes posible para resolver este problema.\n\n"
                f"Puede ver todos los detalles de esta retroalimentación en el panel de administración."
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[project_manager_email],
                fail_silently=False
            )
            
            logger.info(f"Notificación de problema urgente enviada para feedback {feedback.id}")
            
        except Exception as e:
            logger.error(f"Error al enviar notificación de problema urgente: {str(e)}")
    
    def _create_meeting_request(self, feedback: ServiceFeedback, feedback_data: Dict):
        """Crea una solicitud de reunión con el Managing Director."""
        # Esta función se implementó anteriormente en el sistema de feedback de propuestas
        pass
    
    def _register_service_suggestion(self, feedback: ServiceFeedback, suggestion_text: str):
        """Registra una sugerencia de nuevo servicio para análisis posterior."""
        try:
            # Crear registro de sugerencia
            suggestion = ServiceImprovementSuggestion(
                feedback=feedback,
                suggestion_type='new_service',
                title=f"Sugerencia de nuevo servicio - {feedback.company_name}",
                description=suggestion_text,
                status='new'
            )
            suggestion.save()
            
            logger.info(f"Registrada sugerencia de nuevo servicio desde feedback {feedback.id}")
            
        except Exception as e:
            logger.error(f"Error al registrar sugerencia de nuevo servicio: {str(e)}")
    
    async def trigger_milestone_feedback(self, opportunity_id: int, milestone: int, 
                                       delay_days: int = 1, progress_percentage: int = None):
        """
        Dispara una solicitud de retroalimentación para un hito específico del servicio.
        
        Esta función puede ser llamada manualmente o por eventos del sistema
        cuando se alcanza un hito importante en la prestación del servicio.
        """
        return await self.schedule_feedback_request(
            opportunity_id=opportunity_id,
            milestone=milestone,
            delay_days=delay_days,
            progress_percentage=progress_percentage
        )
    
    async def generate_insights_report(self, start_date: datetime, end_date: datetime, 
                                     service_type: str = None) -> Dict:
        """
        Genera un informe de insights basado en la retroalimentación de servicios en curso
        en un periodo específico.
        """
        # Filtrar feedback
        query = ServiceFeedback.objects.filter(
            stage='ongoing',
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        if service_type:
            query = query.filter(service_type=service_type)
        
        feedbacks = query.select_related('ongoing_feedback')
        
        if not feedbacks.exists():
            return {"error": "No hay datos para el período seleccionado"}
        
        # Estadísticas básicas
        total = feedbacks.count()
        
        # Promedios de calificaciones
        avg_ratings = {
            "general": 0,
            "progress": 0,
            "communication": 0,
            "consultant": 0
        }
        
        urgent_issues_count = 0
        urgent_issues_list = []
        
        for feedback in feedbacks:
            if feedback.rating:
                avg_ratings["general"] += feedback.rating
            
            ongoing = getattr(feedback, 'ongoing_feedback', None)
            if ongoing:
                if ongoing.progress_satisfaction:
                    avg_ratings["progress"] += ongoing.progress_satisfaction
                if ongoing.communication_rating:
                    avg_ratings["communication"] += ongoing.communication_rating
                if ongoing.consultant_rating:
                    avg_ratings["consultant"] += ongoing.consultant_rating
                
                if ongoing.urgent_issues and len(ongoing.urgent_issues.strip()) > 0:
                    urgent_issues_count += 1
                    urgent_issues_list.append({
                        "company": feedback.company_name,
                        "issue": ongoing.urgent_issues[:100] + "..." if len(ongoing.urgent_issues) > 100 else ongoing.urgent_issues
                    })
        
        # Calcular promedios
        for key in avg_ratings:
            avg_ratings[key] = round(avg_ratings[key] / total, 1) if total > 0 else 0
        
        # Recomendaciones basadas en datos
        recommendations = []
        if avg_ratings["communication"] < 3.5:
            recommendations.append("La comunicación durante los servicios está por debajo del estándar esperado. Revisar protocolos de comunicación con clientes.")
        
        if urgent_issues_count / total > 0.15:
            recommendations.append("Hay un número significativo de problemas urgentes reportados. Implementar revisión preventiva de servicios en curso.")
        
        return {
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            },
            "total_feedbacks": total,
            "average_ratings": avg_ratings,
            "urgent_issues": {
                "count": urgent_issues_count,
                "percentage": (urgent_issues_count / total) * 100 if total > 0 else 0,
                "examples": urgent_issues_list[:5]  # Limitar a 5 ejemplos
            },
            "recommendations": recommendations
        }


# Función para inicializar el tracker
def get_ongoing_service_tracker():
    """Obtiene una instancia del OngoingServiceTracker."""
    return OngoingServiceTracker()
