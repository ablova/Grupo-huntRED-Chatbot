# /home/pablo/app/com/feedback/reminder_system.py
"""
Sistema de recordatorios y seguimiento de solicitudes de feedback pendientes.

Este módulo permite:
1. Rastrear solicitudes de feedback no respondidas
2. Enviar recordatorios automáticos por múltiples canales (email, WhatsApp, etc.)
3. Escalar las solicitudes pendientes a supervisores y stakeholders clave
4. Generar reportes de tasas de respuesta y efectividad de los recordatorios
"""
from typing import Dict, List, Optional, Union, Any
import asyncio
from datetime import datetime, timedelta
import json
import logging
import secrets
from enum import Enum

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
import redis
import requests

from app.models import Opportunity, Proposal, Company, Contact, Person, User, BusinessUnit
from app.ats.chatbot.message_service import MessageService
from app.ats.feedback.feedback_models import ServiceFeedback

logger = logging.getLogger(__name__)

class ReminderChannel(Enum):
    """Canales disponibles para enviar recordatorios."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    SLACK = "slack"
    TELEGRAM = "telegram"
    CALL = "call"

class ReminderStatus(Enum):
    """Estados posibles de un recordatorio."""
    SCHEDULED = "scheduled"
    SENT = "sent"
    RESPONDED = "responded"
    FAILED = "failed"
    CANCELLED = "cancelled"

class FeedbackReminderSystem:
    """
    Sistema para gestionar recordatorios de encuestas de retroalimentación pendientes.
    
    Se encarga de rastrear las solicitudes enviadas, detectar cuáles no han sido
    respondidas, y enviar recordatorios automáticos por diversos canales.
    """
    
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.redis_prefix = "feedback_reminder:"
        self.message_service = MessageService()
        
        # Configuraciones por defecto
        self.reminder_intervals = [3, 7, 14]  # Días después del envío inicial para recordatorios
        self.default_channels = [ReminderChannel.EMAIL]  # Canales por defecto
        self.escalation_threshold = 14  # Días sin respuesta antes de escalar
        
        # Prioridad de escalación (a qué roles notificar según el tiempo sin respuesta)
        self.escalation_priority = [
            {"days": 14, "roles": ["project_manager"]},
            {"days": 21, "roles": ["project_manager", "account_manager"]},
            {"days": 30, "roles": ["project_manager", "account_manager", "business_unit_director"]},
        ]
    
    async def register_feedback_request(self, token: str, opportunity_id: Optional[int] = None, 
                                      proposal_id: Optional[int] = None, stage: str = "proposal",
                                      contact_email: str = None, company_id: Optional[int] = None,
                                      business_unit_id: Optional[int] = None, priority: str = "normal"):
        """
        Registra una solicitud de feedback enviada para su seguimiento.
        
        Args:
            token: Token único que identifica la solicitud de feedback
            opportunity_id: ID de la oportunidad relacionada (opcional)
            proposal_id: ID de la propuesta relacionada (opcional)
            stage: Etapa del feedback ('proposal', 'ongoing', 'completed')
            contact_email: Email del contacto principal
            company_id: ID de la empresa
            business_unit_id: ID de la unidad de negocio
            priority: Prioridad del seguimiento ('low', 'normal', 'high', 'critical')
        """
        try:
            # Crear registro en Redis para seguimiento
            request_key = f"{self.redis_prefix}request:{token}"
            
            # Obtener datos adicionales si están disponibles
            contact_name = ""
            company_name = ""
            business_unit_name = ""
            responsible_email = ""
            
            if company_id:
                try:
                    company = Company.objects.get(id=company_id)
                    company_name = company.name
                except:
                    pass
            
            if business_unit_id:
                try:
                    bu = BusinessUnit.objects.get(id=business_unit_id)
                    business_unit_name = bu.name
                except:
                    pass
            
            # Buscar responsable según la oportunidad o propuesta
            if opportunity_id:
                try:
                    opportunity = Opportunity.objects.get(id=opportunity_id)
                    if opportunity.assigned_to:
                        responsible_email = opportunity.assigned_to.email
                    
                    # Si no tenemos company_id, intentar obtenerlo de la oportunidad
                    if not company_name and opportunity.company:
                        company_name = opportunity.company.name
                        
                    # Si no tenemos contact_email, intentar obtenerlo de la oportunidad
                    if not contact_email and opportunity.contact:
                        contact_email = opportunity.contact.email
                        contact_name = opportunity.contact.name
                        
                    # Si no tenemos business_unit, intentar obtenerlo de la oportunidad
                    if not business_unit_name and opportunity.business_unit:
                        business_unit_name = opportunity.business_unit.name
                except:
                    pass
                    
            elif proposal_id:
                try:
                    proposal = Proposal.objects.get(id=proposal_id)
                    if proposal.created_by:
                        responsible_email = proposal.created_by.email
                    
                    # Usar datos de la propuesta
                    if not company_name:
                        company_name = proposal.company_name
                    if not contact_email:
                        contact_email = proposal.contact_email
                    if not contact_name:
                        contact_name = proposal.contact_name
                except:
                    pass
            
            # Datos del registro
            now = timezone.now()
            request_data = {
                "token": token,
                "opportunity_id": opportunity_id,
                "proposal_id": proposal_id,
                "stage": stage,
                "contact_email": contact_email,
                "contact_name": contact_name,
                "company_name": company_name,
                "company_id": company_id,
                "business_unit": business_unit_name,
                "business_unit_id": business_unit_id,
                "responsible_email": responsible_email,
                "priority": priority,
                "created_at": now.isoformat(),
                "sent_at": now.isoformat(),
                "status": ReminderStatus.SENT.value,
                "reminders_sent": 0,
                "reminders_history": [],
                "responded": False,
                "responded_at": None,
                "last_checked": now.isoformat()
            }
            
            # Guardar en Redis (90 días)
            self.redis.set(request_key, json.dumps(request_data), ex=60*60*24*90)
            
            # Programar recordatorios automáticos
            for interval in self.reminder_intervals:
                await self.schedule_reminder(token, interval)
            
            logger.info(f"Solicitud de feedback registrada para seguimiento: {token}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error al registrar solicitud de feedback: {str(e)}")
            return False
    
    async def schedule_reminder(self, token: str, days_delay: int, 
                              channels: List[ReminderChannel] = None):
        """
        Programa un recordatorio para una solicitud de feedback pendiente.
        
        Args:
            token: Token único que identifica la solicitud de feedback
            days_delay: Días a esperar desde el envío inicial
            channels: Canales a utilizar para el recordatorio
        """
        try:
            # Obtener datos de la solicitud
            request_key = f"{self.redis_prefix}request:{token}"
            request_data_json = self.redis.get(request_key)
            
            if not request_data_json:
                logger.warning(f"No se encontró la solicitud de feedback: {token}")
                return False
            
            request_data = json.loads(request_data_json)
            
            # Verificar si ya se respondió
            if request_data.get("responded", False):
                logger.info(f"No se programa recordatorio: la solicitud {token} ya fue respondida")
                return False
            
            # Calcular fecha de envío
            sent_at = datetime.fromisoformat(request_data["sent_at"])
            reminder_date = sent_at + timedelta(days=days_delay)
            
            # Usar canales por defecto si no se especifican
            if not channels:
                channels = self.default_channels
            
            # Crear registro del recordatorio
            reminder_id = secrets.token_urlsafe(16)
            reminder_key = f"{self.redis_prefix}reminder:{reminder_id}"
            
            reminder_data = {
                "id": reminder_id,
                "token": token,
                "scheduled_for": reminder_date.isoformat(),
                "channels": [channel.value for channel in channels],
                "status": ReminderStatus.SCHEDULED.value,
                "attempt": request_data.get("reminders_sent", 0) + 1,
                "created_at": timezone.now().isoformat()
            }
            
            # Guardar en Redis (30 días)
            self.redis.set(reminder_key, json.dumps(reminder_data), ex=60*60*24*30)
            
            logger.info(f"Recordatorio programado para {reminder_date.isoformat()} - solicitud: {token}")
            
            return reminder_id
            
        except Exception as e:
            logger.error(f"Error al programar recordatorio: {str(e)}")
            return False
    
    async def process_pending_reminders(self):
        """
        Procesa todos los recordatorios pendientes que deben enviarse hoy.
        
        Esta función debe ejecutarse diariamente mediante una tarea programada.
        """
        now = timezone.now()
        pattern = f"{self.redis_prefix}reminder:*"
        
        # Buscar todos los recordatorios en Redis
        for key in self.redis.scan_iter(match=pattern):
            try:
                reminder_data = json.loads(self.redis.get(key))
                
                # Verificar si ya es hora de enviar
                scheduled_for = datetime.fromisoformat(reminder_data["scheduled_for"])
                if now < scheduled_for or reminder_data["status"] != ReminderStatus.SCHEDULED.value:
                    continue
                
                # Verificar si la solicitud original sigue pendiente
                token = reminder_data["token"]
                request_key = f"{self.redis_prefix}request:{token}"
                request_data_json = self.redis.get(request_key)
                
                if not request_data_json:
                    logger.warning(f"No se encontró la solicitud original para el recordatorio: {key}")
                    continue
                
                request_data = json.loads(request_data_json)
                
                # Si ya se respondió, actualizar estado del recordatorio y continuar
                if request_data.get("responded", False):
                    reminder_data["status"] = ReminderStatus.CANCELLED.value
                    reminder_data["cancelled_reason"] = "ya_respondido"
                    self.redis.set(key, json.dumps(reminder_data), ex=60*60*24*30)
                    continue
                
                # Enviar recordatorio por todos los canales configurados
                success = False
                for channel_str in reminder_data["channels"]:
                    channel = ReminderChannel(channel_str)
                    
                    if channel == ReminderChannel.EMAIL:
                        email_sent = await self._send_email_reminder(token, request_data, reminder_data)
                        success = success or email_sent
                    
                    elif channel == ReminderChannel.WHATSAPP:
                        whatsapp_sent = await self._send_whatsapp_reminder(token, request_data, reminder_data)
                        success = success or whatsapp_sent
                
                # Actualizar estado del recordatorio
                if success:
                    reminder_data["status"] = ReminderStatus.SENT.value
                    reminder_data["sent_at"] = now.isoformat()
                else:
                    reminder_data["status"] = ReminderStatus.FAILED.value
                
                self.redis.set(key, json.dumps(reminder_data), ex=60*60*24*30)
                
                # Actualizar la solicitud original
                if success:
                    request_data["reminders_sent"] = request_data.get("reminders_sent", 0) + 1
                    request_data["reminders_history"].append({
                        "reminder_id": reminder_data["id"],
                        "sent_at": now.isoformat(),
                        "attempt": reminder_data["attempt"]
                    })
                    self.redis.set(request_key, json.dumps(request_data), ex=60*60*24*90)
                    
                    # Programar próximo recordatorio si es necesario
                    days_without_response = (now - datetime.fromisoformat(request_data["sent_at"])).days
                    
                    # Verificar si hay que escalar
                    await self._check_escalation(token, days_without_response, request_data)
                    
                    logger.info(f"Recordatorio enviado correctamente: {key}")
                else:
                    logger.error(f"Error al enviar recordatorio: {key}")
                
            except Exception as e:
                logger.error(f"Error procesando recordatorio {key}: {str(e)}")
    
    async def check_pending_responses(self):
        """
        Verifica si hay nuevas respuestas para solicitudes pendientes.
        
        Esta función debe ejecutarse diariamente mediante una tarea programada.
        """
        pattern = f"{self.redis_prefix}request:*"
        
        # Buscar todas las solicitudes en Redis
        for key in self.redis.scan_iter(match=pattern):
            try:
                request_data = json.loads(self.redis.get(key))
                
                # Si ya se respondió, continuar
                if request_data.get("responded", False):
                    continue
                
                # Verificar si hay respuesta en la base de datos
                token = request_data["token"]
                
                if ServiceFeedback.objects.filter(token=token).exists():
                    # Actualizar estado
                    now = timezone.now()
                    request_data["responded"] = True
                    request_data["responded_at"] = now.isoformat()
                    request_data["status"] = ReminderStatus.RESPONDED.value
                    self.redis.set(key, json.dumps(request_data), ex=60*60*24*90)
                    
                    logger.info(f"Detectada respuesta para solicitud: {token}")
                    
                    # Enviar agradecimiento
                    await self._send_response_acknowledgment(token, request_data)
                else:
                    # Actualizar última verificación
                    request_data["last_checked"] = timezone.now().isoformat()
                    self.redis.set(key, json.dumps(request_data), ex=60*60*24*90)
                
            except Exception as e:
                logger.error(f"Error verificando respuestas pendientes para {key}: {str(e)}")
    
    async def _send_email_reminder(self, token: str, request_data: Dict, reminder_data: Dict) -> bool:
        """Envía un recordatorio por email."""
        try:
            contact_email = request_data.get("contact_email")
            if not contact_email:
                logger.warning(f"No se puede enviar recordatorio email: falta email de contacto para {token}")
                return False
            
            stage = request_data.get("stage", "proposal")
            company_name = request_data.get("company_name", "su empresa")
            contact_name = request_data.get("contact_name", "Estimado cliente")
            attempt = reminder_data.get("attempt", 1)
            
            # Personalizar asunto según el intento
            if attempt == 1:
                subject_prefix = "Recordatorio"
            elif attempt == 2:
                subject_prefix = "Segundo recordatorio"
            else:
                subject_prefix = "Recordatorio importante"
            
            # Determinar tipo de feedback según la etapa
            if stage == "proposal":
                feedback_type = "propuesta"
                feedback_url = f"{settings.SITE_URL}{reverse('feedback:proposal_feedback', args=[token])}"
            elif stage == "ongoing":
                feedback_type = "servicio en curso"
                feedback_url = f"{settings.SITE_URL}{reverse('feedback:ongoing_feedback', args=[token])}"
            else:  # completed
                feedback_type = "servicio concluido"
                feedback_url = f"{settings.SITE_URL}{reverse('feedback:completion_feedback', args=[token])}"
            
            # Preparar contexto
            context = {
                "token": token,
                "company_name": company_name,
                "contact_name": contact_name,
                "feedback_type": feedback_type,
                "feedback_url": feedback_url,
                "attempt": attempt,
                "minutes_to_complete": 3,  # Tiempo estimado para completar
                "is_final_reminder": attempt >= 3
            }
            
            # Renderizar templates
            subject = f"{subject_prefix} - Su opinión sobre nuestra {feedback_type} es importante"
            html_message = render_to_string("emails/feedback_reminder.html", context)
            text_message = render_to_string("emails/feedback_reminder.txt", context)
            
            # Enviar email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contact_email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Recordatorio email enviado a {contact_email} para {token}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar recordatorio por email: {str(e)}")
            return False
    
    async def _send_whatsapp_reminder(self, token: str, request_data: Dict, reminder_data: Dict) -> bool:
        """Envía un recordatorio por WhatsApp."""
        try:
            # Verificar si hay números de teléfono en los datos de contacto
            # Esta función requiere integración con el MessageService
            
            # Por ahora, registrar que intentamos enviar WhatsApp
            logger.info(f"Intento de envío de recordatorio WhatsApp para {token}")
            
            # Implementación real requiere integración con app.ats.chatbot.message_service
            return False
            
        except Exception as e:
            logger.error(f"Error al enviar recordatorio por WhatsApp: {str(e)}")
            return False
    
    async def _send_response_acknowledgment(self, token: str, request_data: Dict) -> bool:
        """Envía un agradecimiento por haber completado la retroalimentación."""
        try:
            contact_email = request_data.get("contact_email")
            if not contact_email:
                return False
            
            # Obtener la retroalimentación
            feedback = ServiceFeedback.objects.get(token=token)
            
            # Personalizar según la etapa
            if feedback.stage == "proposal":
                feedback_type = "nuestra propuesta"
            elif feedback.stage == "ongoing":
                feedback_type = "nuestro servicio en curso"
            else:  # completed
                feedback_type = "el servicio que le brindamos"
            
            # Preparar email
            subject = f"Gracias por su retroalimentación - Grupo huntRED®"
            message = (
                f"Estimado/a {feedback.contact_name},\n\n"
                f"Queremos agradecerle sinceramente por tomarse el tiempo de compartir su experiencia con {feedback_type}.\n\n"
                f"Sus comentarios son extremadamente valiosos para nosotros y nos ayudan a mejorar constantemente nuestros servicios.\n\n"
                f"Si tiene cualquier consulta adicional, no dude en contactarnos.\n\n"
                f"Atentamente,\n\n"
                f"Equipo de Grupo huntRED®"
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contact_email],
                fail_silently=False
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar agradecimiento: {str(e)}")
            return False
    
    async def _check_escalation(self, token: str, days_without_response: int, request_data: Dict):
        """
        Verifica si la solicitud pendiente debe escalarse según su antigüedad.
        
        Si una solicitud lleva demasiado tiempo sin respuesta, se notifica a roles
        con mayor jerarquía para que intervengan.
        """
        try:
            # Verificar si hay que escalar según los umbrales configurados
            roles_to_notify = []
            
            for escalation in self.escalation_priority:
                if days_without_response >= escalation["days"]:
                    roles_to_notify = escalation["roles"]
            
            if not roles_to_notify:
                return False
            
            # Obtener emails para notificar según roles
            emails_to_notify = await self._get_escalation_emails(request_data, roles_to_notify)
            
            if not emails_to_notify:
                return False
            
            # Enviar notificación de escalación
            await self._send_escalation_notification(token, request_data, days_without_response, emails_to_notify)
            
            return True
            
        except Exception as e:
            logger.error(f"Error al verificar escalación: {str(e)}")
            return False
    
    async def _get_escalation_emails(self, request_data: Dict, roles: List[str]) -> List[str]:
        """Obtiene los emails de las personas a notificar según roles."""
        emails = []
        
        # Siempre incluir al responsable directo si está disponible
        responsible_email = request_data.get("responsible_email")
        if responsible_email and responsible_email not in emails:
            emails.append(responsible_email)
        
        # Obtener emails según Business Unit
        business_unit_id = request_data.get("business_unit_id")
        if business_unit_id:
            try:
                # Implementación depende de la estructura organizacional
                # Ejemplo simplificado
                if "business_unit_director" in roles:
                    try:
                        # Lógica para obtener email del director de BU
                        pass
                    except:
                        pass
            except:
                pass
        
        # Añadir escalación a Managing Director en casos críticos
        if "managing_director" in roles:
            md_email = getattr(settings, "MANAGING_DIRECTOR_EMAIL", "pablo@huntred.com")
            if md_email and md_email not in emails:
                emails.append(md_email)
        
        return emails
    
    async def _send_escalation_notification(self, token: str, request_data: Dict, 
                                          days_without_response: int, emails: List[str]) -> bool:
        """Envía notificación de escalación a los responsables."""
        try:
            if not emails:
                return False
            
            company_name = request_data.get("company_name", "un cliente")
            stage = request_data.get("stage", "proposal")
            
            # Determinar tipo de feedback
            if stage == "proposal":
                feedback_type = "propuesta"
            elif stage == "ongoing":
                feedback_type = "servicio en curso"
            else:  # completed
                feedback_type = "servicio concluido"
            
            # Preparar email
            subject = f"ESCALACIÓN: Retroalimentación pendiente de {company_name} ({days_without_response} días)"
            message = (
                f"Notificación de Escalación - Sistema de Retroalimentación\n\n"
                f"La solicitud de retroalimentación para {company_name} sobre {feedback_type} lleva {days_without_response} días sin respuesta.\n\n"
                f"Detalles:\n"
                f"- Empresa: {company_name}\n"
                f"- Contacto: {request_data.get('contact_name', 'No disponible')} ({request_data.get('contact_email', 'No disponible')})\n"
                f"- Tipo de feedback: {feedback_type}\n"
                f"- Enviado originalmente: {request_data.get('sent_at', 'Desconocido')}\n"
                f"- Recordatorios enviados: {request_data.get('reminders_sent', 0)}\n\n"
                f"Se recomienda realizar seguimiento personal con el cliente para obtener su retroalimentación.\n\n"
                f"Puede acceder a más detalles en el panel de administración.\n\n"
                f"Este es un mensaje automático del Sistema de Retroalimentación de Grupo huntRED®."
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=emails,
                fail_silently=False
            )
            
            logger.info(f"Notificación de escalación enviada para {token} a {', '.join(emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar notificación de escalación: {str(e)}")
            return False
    
    async def get_pending_requests_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas sobre solicitudes pendientes."""
        stats = {
            "total_pending": 0,
            "by_stage": {},
            "by_business_unit": {},
            "critical": 0,  # Pendientes por más de 30 días
            "high": 0,      # Pendientes entre 14-30 días
            "normal": 0,    # Pendientes entre 7-14 días
            "low": 0        # Pendientes menos de 7 días
        }
        
        now = timezone.now()
        pattern = f"{self.redis_prefix}request:*"
        
        # Buscar todas las solicitudes pendientes
        for key in self.redis.scan_iter(match=pattern):
            try:
                request_data = json.loads(self.redis.get(key))
                
                # Si ya se respondió, continuar
                if request_data.get("responded", False):
                    continue
                
                # Actualizar contador total
                stats["total_pending"] += 1
                
                # Clasificar por etapa
                stage = request_data.get("stage", "proposal")
                stats["by_stage"][stage] = stats["by_stage"].get(stage, 0) + 1
                
                # Clasificar por unidad de negocio
                bu = request_data.get("business_unit", "No asignada")
                stats["by_business_unit"][bu] = stats["by_business_unit"].get(bu, 0) + 1
                
                # Clasificar por antigüedad
                sent_at = datetime.fromisoformat(request_data["sent_at"])
                days_pending = (now - sent_at).days
                
                if days_pending > 30:
                    stats["critical"] += 1
                elif days_pending > 14:
                    stats["high"] += 1
                elif days_pending > 7:
                    stats["normal"] += 1
                else:
                    stats["low"] += 1
                
            except Exception as e:
                logger.error(f"Error al procesar estadísticas de {key}: {str(e)}")
        
        return stats

# Función para inicializar el sistema de recordatorios
def get_reminder_system():
    """Obtiene una instancia del FeedbackReminderSystem."""
    return FeedbackReminderSystem()
