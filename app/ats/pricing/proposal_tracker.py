# /home/pablo/app/com/pricing/proposal_tracker.py
"""
Sistema de seguimiento y retroalimentación de propuestas enviadas.

Este módulo permite:
1. Enviar encuestas automáticas a los 2-3 días de enviar una propuesta
2. Recolectar retroalimentación sobre por qué los clientes contratan o no
3. Ofrecer reuniones con el Managing Partner para acelerar conversiones
4. Generar indicadores para mejorar continuamente el servicio
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

from app.models import Proposal, TalentAnalysisRequest, Company, Contact, Opportunity
from app.ats.pricing.feedback_models import ProposalFeedback, MeetingRequest
from app.ats.chatbot.message_service import MessageService

logger = logging.getLogger(__name__)

class ProposalTracker:
    """
    Gestiona el seguimiento de propuestas enviadas y recolecta retroalimentación
    sobre por qué los clientes contratan o no los servicios.
    """
    
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.redis_prefix = "proposal_tracker:"
        self.message_service = MessageService()
        
        # Calendario.com API para Pablo (configurable desde settings)
        self.calendly_url = getattr(settings, "MANAGING_DIRECTOR_CALENDAR_URL", 
                                  "https://huntred.com/agenda-pllh/")
        
        # Preguntas predefinidas - simples para maximizar respuestas
        self.feedback_questions = [
            {
                "id": "interest_level",
                "question": "¿Cuál es su interés en nuestro servicio de Análisis de Talento 360°?",
                "options": [
                    "Interesado - Solicitaré el servicio", 
                    "Considerando - Evaluando opciones", 
                    "No por ahora - Podría considerar en el futuro",
                    "No interesado - No es relevante actualmente", 
                    "Elegí otro proveedor"
                ],
                "type": "radio"
            },
            {
                "id": "price_perception",
                "question": "¿Cómo percibe nuestros precios?",
                "options": ["1 - Muy accesible", "2", "3 - Justo", "4", "5 - Muy costoso"],
                "type": "scale"
            },
            {
                "id": "improvement",
                "question": "¿En qué podríamos mejorar nuestra propuesta?",
                "type": "text"
            },
            {
                "id": "meeting_request",
                "question": "¿Desea hablar directamente con nuestro Managing Director?",
                "description": "Reserve una reunión personal con Pablo Lelo de Larrea H. - Sr. Managing Partner Grupo huntRED® para discutir su estrategia de reclutamiento y resolver cualquier duda.",
                "button_text": "Agendar Reunión Estratégica",
                "type": "meeting_request"
            }
        ]
    
    def generate_feedback_token(self, proposal_id: int) -> str:
        """Genera un token único para identificar respuestas de retroalimentación."""
        token = secrets.token_urlsafe(32)
        # Guardar relación token-propuesta en Redis por 30 días
        token_key = f"{self.redis_prefix}token:{token}"
        self.redis.set(token_key, proposal_id, ex=60*60*24*30)  # 30 días
        return token
    
    async def schedule_feedback_request(self, proposal: 'Proposal', delay_days: int = 3):
        """
        Programa una solicitud de retroalimentación para ser enviada después de
        un número específico de días tras el envío de la propuesta.
        """
        # Solo para propuestas válidas con contactos
        if not proposal or not proposal.contact_email:
            logger.warning(f"No se puede programar seguimiento: propuesta {proposal.id} sin contacto")
            return False
        
        # Generar token único para esta solicitud
        token = self.generate_feedback_token(proposal.id)
        
        # Guardar programación en Redis
        schedule_key = f"{self.redis_prefix}scheduled:{proposal.id}"
        schedule_data = {
            "proposal_id": proposal.id,
            "token": token,
            "company_name": proposal.company_name,
            "contact_name": proposal.contact_name,
            "contact_email": proposal.contact_email,
            "send_after": (timezone.now() + timedelta(days=delay_days)).isoformat(),
            "status": "scheduled"
        }
        
        self.redis.set(schedule_key, json.dumps(schedule_data), ex=60*60*24*30)  # 30 días
        
        logger.info(f"Retroalimentación programada para propuesta {proposal.id} en {delay_days} días")
        return True
    
    async def send_feedback_requests(self):
        """
        Busca retroalimentaciones programadas que deban enviarse hoy y las envía.
        Esta función debería ejecutarse diariamente mediante una tarea programada.
        """
        now = timezone.now()
        pattern = f"{self.redis_prefix}scheduled:*"
        
        # Buscar todas las programaciones en Redis
        for key in self.redis.scan_iter(match=pattern):
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
                self.redis.set(key, json.dumps(data), ex=60*60*24*30)  # 30 días más
                logger.info(f"Enviada solicitud de retroalimentación para propuesta {data['proposal_id']}")
    
    async def _send_feedback_email(self, data: Dict) -> bool:
        """Envía email de solicitud de retroalimentación."""
        try:
            proposal_id = data["proposal_id"]
            token = data["token"]
            company_name = data["company_name"]
            contact_name = data["contact_name"]
            contact_email = data["contact_email"]
            
            # Generar URL única para retroalimentación
            feedback_url = f"{settings.SITE_URL}{reverse('pricing:proposal_feedback', args=[token])}"
            
            # Preparar email
            context = {
                "proposal_id": proposal_id,
                "token": token,
                "company_name": company_name, 
                "contact_name": contact_name,
                "feedback_url": feedback_url,
                "feedback_questions": self.feedback_questions,
                "managing_director_calendar": self.calendly_url
            }
            
            subject = f"Su opinión es importante para Grupo huntRED® - Propuesta de Talento 360°"
            html_message = render_to_string("emails/proposal_feedback_request.html", context)
            text_message = render_to_string("emails/proposal_feedback_request.txt", context)
            
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
            logger.error(f"Error al enviar solicitud de retroalimentación: {str(e)}")
            return False
    
    async def process_feedback(self, token: str, feedback_data: Dict) -> Optional[ProposalFeedback]:
        """
        Procesa la retroalimentación recibida de un cliente y la almacena 
        para análisis posterior.
        """
        # Validar token
        token_key = f"{self.redis_prefix}token:{token}"
        proposal_id = self.redis.get(token_key)
        
        if not proposal_id:
            logger.warning(f"Token inválido o expirado: {token}")
            return None
        
        try:
            proposal_id = int(proposal_id)
            proposal = Proposal.objects.get(id=proposal_id)
            
            # Crear registro de retroalimentación
            feedback = ProposalFeedback(
                proposal=proposal,
                opportunity=proposal.opportunity,
                token=token,
                contact_name=proposal.contact_name,
                contact_email=proposal.contact_email,
                company_name=proposal.company_name,
                response_type=feedback_data.get("interest_level"),
                rejection_reason=feedback_data.get("rejection_reason"),
                price_perception=feedback_data.get("price_perception"),
                improvement_suggestions=feedback_data.get("improvement"),
                meeting_requested=feedback_data.get("meeting_requested", False)
            )
            feedback.save()
            
            # Si se solicita reunión, crear solicitud
            if feedback.meeting_requested:
                self._create_meeting_request(feedback, feedback_data)
            
            # Actualizar propuesta con retroalimentación recibida
            proposal.feedback_received = True
            proposal.status = self._determine_proposal_status(feedback_data.get("interest_level"))
            proposal.save()
            
            logger.info(f"Retroalimentación procesada para propuesta {proposal_id}")
            return feedback
            
        except Exception as e:
            logger.error(f"Error al procesar retroalimentación: {str(e)}")
            return None
    
    def _determine_proposal_status(self, interest_level: str) -> str:
        """Determina el nuevo estado de la propuesta basado en el interés mostrado."""
        status_mapping = {
            "interested": "accepted", 
            "considering": "under_review",
            "not_now": "postponed",
            "not_interested": "rejected",
            "went_competitor": "lost"
        }
        return status_mapping.get(interest_level, "pending")
    
    def _create_meeting_request(self, feedback: ProposalFeedback, feedback_data: Dict) -> Optional[MeetingRequest]:
        """Crea una solicitud de reunión con el Managing Director."""
        try:
            # Crear solicitud de reunión
            meeting = MeetingRequest(
                contact_name=feedback.contact_name,
                contact_email=feedback.contact_email,
                company_name=feedback.company_name,
                proposal_feedback=feedback,
                meeting_type=feedback_data.get("meeting_type", "proposal_review"),
                notes=feedback_data.get("meeting_notes", "")
            )
            meeting.save()
            
            # Notificar al Managing Director sobre nueva solicitud
            self._notify_new_meeting_request(meeting)
            
            return meeting
            
        except Exception as e:
            logger.error(f"Error al crear solicitud de reunión: {str(e)}")
            return None
    
    def _notify_new_meeting_request(self, meeting: MeetingRequest):
        """Notifica al Managing Director sobre una nueva solicitud de reunión."""
        # Enviar email de notificación
        try:
            managing_director_email = getattr(settings, "MANAGING_DIRECTOR_EMAIL", 
                                           "pablo@huntred.com")
            
            subject = f"Nueva solicitud de reunión - {meeting.company_name}"
            message = (
                f"Hola Pablo,\n\n"
                f"Has recibido una nueva solicitud de reunión de {meeting.contact_name} "
                f"de {meeting.company_name}.\n\n"
                f"Email: {meeting.contact_email}\n"
                f"Razón: {meeting.get_meeting_type_display()}\n"
                f"Notas: {meeting.notes}\n\n"
                f"Por favor ingresa al panel para agendar esta reunión.\n\n"
                f"Saludos,\n"
                f"Sistema de Propuestas - Grupo huntRED®"
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[managing_director_email],
                fail_silently=False
            )
            
        except Exception as e:
            logger.error(f"Error al notificar sobre nueva solicitud de reunión: {str(e)}")
    
    async def generate_insights_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        Genera un informe de insights basado en la retroalimentación recibida 
        en un periodo específico.
        """
        feedbacks = ProposalFeedback.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        if not feedbacks.exists():
            return {"error": "No hay datos para el período seleccionado"}
        
        # Estadísticas básicas
        total = feedbacks.count()
        interested = feedbacks.filter(response_type__in=["interested", "considering"]).count()
        rejection_reasons = {}
        price_perception_avg = 0
        meeting_requests = feedbacks.filter(meeting_requested=True).count()
        
        # Analizar razones de rechazo
        for feedback in feedbacks:
            if feedback.rejection_reason:
                rejection_reasons[feedback.rejection_reason] = rejection_reasons.get(feedback.rejection_reason, 0) + 1
            if feedback.price_perception:
                price_perception_avg += feedback.price_perception
        
        if total > 0:
            price_perception_avg /= total
        
        # Recomendaciones basadas en datos
        recommendations = []
        if price_perception_avg > 4:
            recommendations.append("Los clientes perciben los precios como altos. Considerar revisar la estructura de precios o mejorar la comunicación de valor.")
        
        if rejection_reasons.get("clarity", 0) / total > 0.2:
            recommendations.append("Muchos clientes indican falta de claridad. Revisar cómo se presenta la información en las propuestas.")
        
        return {
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            },
            "total_feedbacks": total,
            "interest_rate": (interested / total) * 100 if total > 0 else 0,
            "rejection_reasons": rejection_reasons,
            "price_perception_avg": price_perception_avg,
            "meeting_requests": meeting_requests,
            "meeting_conversion_rate": (meeting_requests / total) * 100 if total > 0 else 0,
            "recommendations": recommendations
        }


# Función para inicializar el tracker
def get_proposal_tracker():
    """Obtiene una instancia del ProposalTracker."""
    return ProposalTracker()
