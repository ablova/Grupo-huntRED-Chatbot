# /home/pablo/app/ats/integrations/notifications/process/feedback_notifications.py
"""
Módulo de notificaciones específicas para el proceso de feedback.
Maneja todas las notificaciones relacionadas con la solicitud y recepción de feedback.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import Person, Vacante, BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import (
    NotificationType,
    NotificationSeverity
)

logger = logging.getLogger(__name__)

class FeedbackNotificationService(BaseNotificationService):
    """
    Servicio de notificaciones para el proceso de feedback.
    Extiende el servicio base con funcionalidad específica para feedback.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el servicio de notificaciones de feedback.
        
        Args:
            business_unit: Unidad de negocio requerida para las notificaciones
        """
        if not business_unit:
            raise ValueError("Se requiere especificar una unidad de negocio")
            
        super().__init__(business_unit)
        
    async def request_interview_feedback(
        self,
        person: Person,
        vacancy: Vacante,
        interview_date: datetime,
        interviewer: str,
        deadline: datetime,
        feedback_link: str = None
    ) -> bool:
        """
        Flujo innovador de feedback de dos niveles (rápido y completo), multicanal.
        - Siempre notifica a consultor y cliente.
        - Feedback rápido en canal (quick replies): 👍, 🤔, 👎.
        - Si la respuesta es negativa/neutral, pregunta "¿Qué le faltó?" (opciones rápidas + campo libre).
        - Opción de feedback completo (web o chat).
        - Agradecimiento visual al finalizar.
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'interview_date': interview_date.strftime('%d/%m/%Y %H:%M'),
                'interviewer': interviewer,
                'deadline': deadline.strftime('%d/%m/%Y %H:%M'),
                'business_unit': self.business_unit.name,
                'feedback_link': feedback_link or f'https://tusistema.com/feedback/{vacancy.id}/{person.id}',
                # Opciones rápidas para WhatsApp/Telegram
                'quick_replies': [
                    {'title': '👍 Cumple con el perfil', 'payload': 'positive'},
                    {'title': '🤔 Dudas', 'payload': 'neutral'},
                    {'title': '👎 No cumple', 'payload': 'negative'},
                ]
            }
            # Notificar al entrevistador (cliente)
            await self.send_notification(
                notification_type=NotificationType.FEEDBACK_REQUEST.value,
                message=self._get_feedback_request_template('interviewer'),
                context=context,
                channels=['email', 'telegram', 'whatsapp'],
                quick_replies=context['quick_replies']
            )
            # Notificar al consultor
            await self.send_notification(
                notification_type=NotificationType.FEEDBACK_REQUEST.value,
                message=self._get_feedback_request_template('consultant'),
                context=context,
                channels=['email', 'telegram', 'whatsapp'],
                quick_replies=context['quick_replies']
            )
            # Programar recordatorio automático si no responde en 24h
            # (Pseudocódigo, depende de tu sistema de tareas)
            # schedule_feedback_reminder(person, vacancy, interview_date, delay_hours=24)
            return True
        except Exception as e:
            logger.error(f"Error solicitando feedback de entrevista: {str(e)}", exc_info=True)
            return False

    def process_quick_reply_feedback(self, reply_payload, user_id, context):
        """
        Procesa la respuesta rápida del usuario en canal (WhatsApp/Telegram).
        Si la respuesta es negativa/neutral, pregunta automáticamente "¿Qué le faltó?" y ofrece escalamiento.
        Si es positiva, agradece y ofrece feedback completo.
        Si es muy negativa, ofrece:
          1. Reposición automática (Plan B GenIA)
          2. Hablar con consultor
          3. Escalamiento directo a Pablo (WhatsApp)
        """
        if reply_payload == 'positive':
            # Agradecer y ofrecer feedback completo
            self.send_followup_message(user_id, "¡Gracias por tu feedback! ¿Quieres dejar un feedback más completo? [Haz clic aquí]({feedback_link})".format(**context))
        elif reply_payload == 'negative':
            # Escalamiento doble: reposición, consultor, Pablo
            self.send_followup_message(
                user_id,
                "🤖 GenIA siempre tiene un Plan B. Ya estamos buscando una nueva alternativa para ti. ¿Qué prefieres hacer?",
                quick_replies=[
                    {'title': 'Ver alternativa (Plan B)', 'payload': 'ver_alternativa'},
                    {'title': 'Hablar con consultor', 'payload': 'consultor'},
                    {'title': 'Escalar a Pablo', 'payload': 'escalar_pablo'}
                ]
            )
            # El flujo continúa según la respuesta:
            # - ver_alternativa: buscar y ofrecer nuevo candidato
            # - consultor: notificar a consultor humano
            # - escalar_pablo: enviar WhatsApp a Pablo
        else:
            # Preguntar "¿Qué le faltó?" con opciones rápidas
            opciones = [
                {'title': 'Soft skills', 'payload': 'faltosoft'},
                {'title': 'Experiencia', 'payload': 'faltoexp'},
                {'title': 'Idiomas', 'payload': 'faltoidioma'},
                {'title': 'Otro', 'payload': 'faltootro'},
            ]
            self.send_followup_message(user_id, "¿Qué le faltó para ser el candidato ideal?", quick_replies=opciones)
            self.send_followup_message(user_id, "¿Quieres dejar un feedback más completo? [Haz clic aquí]({feedback_link})".format(**context))

    def handle_escalation(self, user_id, context, tipo):
        """
        Maneja el escalamiento según la opción elegida:
        - 'consultor': notifica a consultor humano y deja registro interno.
        - 'escalar_pablo': envía WhatsApp a Pablo con los datos del cliente y situación.
        """
        if tipo == 'consultor':
            # Notificación interna (puedes integrar con tu sistema de alertas/admin)
            self.send_internal_notification(
                f"[ESCALAMIENTO] Cliente {context.get('cliente_nombre', 'N/A')} ({context.get('cliente_contacto', 'N/A')}) solicita hablar con consultor. Vacante: {context.get('position', 'N/A')}. Motivo: Feedback negativo."
            )
            self.send_followup_message(user_id, "Un consultor humano te contactará a la brevedad. ¡Gracias por tu honestidad!")
        elif tipo == 'escalar_pablo':
            # Enviar WhatsApp a Pablo
            mensaje = (
                f"[ESCALAMIENTO DIRECTO]\n"
                f"Cliente: {context.get('cliente_nombre', 'N/A')}\n"
                f"Contacto: {context.get('cliente_contacto', 'N/A')}\n"
                f"Vacante: {context.get('position', 'N/A')}\n"
                f"Motivo: Feedback muy negativo sobre candidato.\n"
                f"Por favor, atiende personalmente."
            )
            self.send_whatsapp_to_pablo(mensaje)
            self.send_followup_message(user_id, "Pablo Lelo de Larrea te contactará personalmente para resolver tu situación. ¡Gracias por tu confianza!")

    def send_internal_notification(self, message):
        """
        Envía una notificación interna al equipo de consultores/admin.
        (Implementar integración real según tu sistema.)
        """
        pass

    def send_whatsapp_to_pablo(self, message):
        """
        Envía un WhatsApp directo a Pablo (555218490291) con el mensaje proporcionado.
        (Implementar integración real con API oficial de WhatsApp Business.)
        """
        pass

    def process_complete_feedback(self, user_id, context):
        """
        Flujo de feedback completo (web o chat):
        - ¿Cumple con los skills y requerimientos? (Sí/No)
        - ¿Qué le faltó para ser el candidato ideal? (Texto o selección)
        - ¿Recomendarías avanzar con este candidato? (Sí/No)
        - Comentarios adicionales (opcional)
        - Agradecimiento visual al finalizar.
        """
        # Ejemplo de lógica, debe integrarse con el sistema de formularios/chat
        self.send_followup_message(user_id, "¿Cumple con los skills y requerimientos?", quick_replies=[{'title': 'Sí', 'payload': 'si'}, {'title': 'No', 'payload': 'no'}])
        # ... continuar con el flujo ...
        self.send_followup_message(user_id, "¿Qué le faltó para ser el candidato ideal? (Puedes escribir o elegir)")
        self.send_followup_message(user_id, "¿Recomendarías avanzar con este candidato?", quick_replies=[{'title': 'Sí', 'payload': 'si'}, {'title': 'No', 'payload': 'no'}])
        self.send_followup_message(user_id, "¿Comentarios adicionales? (opcional)")
        self.send_followup_message(user_id, "¡Gracias por tu feedback! Ayudas a mejorar nuestro proceso. 🏆")

    def _get_feedback_request_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'interviewer': (
                "📝 *¡Ayúdanos a mejorar!*\n\n"
                "Por favor, deja tu feedback sobre el candidato entrevistado para {position} en {company}.\n\n"
                "*¿Cómo calificarías al candidato?*\n"
                "- 👍 Cumple con el perfil\n- 🤔 Dudas\n- 👎 No cumple\n\n"
                "[Dejar feedback detallado]({feedback_link})\n\n"
                "¡Gracias por tu colaboración!"
            ),
            'consultant': (
                "📝 *Solicitud de Feedback Enviada*\n\n"
                "Se ha solicitado feedback para el candidato {candidate_name} en la posición {position}."
            )
        }
        return templates.get(recipient_type, templates['interviewer'])
        
    async def notify_feedback_received(
        self,
        person: Person,
        vacancy: Vacante,
        feedback: Dict[str, Any],
        feedback_type: str = 'interview'
    ) -> bool:
        """
        Notifica sobre la recepción de feedback.
        
        Args:
            person: Candidato evaluado
            vacancy: Vacante relacionada
            feedback: Contenido del feedback
            feedback_type: Tipo de feedback
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'feedback_type': feedback_type,
                'evaluation': feedback.get('evaluation', ''),
                'strengths': feedback.get('strengths', []),
                'areas_for_improvement': feedback.get('areas_for_improvement', []),
                'recommendation': feedback.get('recommendation', ''),
                'business_unit': self.business_unit.name
            }
            
            # Notificar al consultor
            if vacancy.assigned_consultant:
                await self.send_notification(
                    notification_type=NotificationType.FEEDBACK_RECEIVED.value,
                    message=self._get_feedback_received_template('consultant'),
                    context=context,
                    channels=['email', 'telegram']
                )
            
            # Notificar al candidato si es apropiado
            if feedback_type == 'final' and feedback.get('share_with_candidate', False):
                await self.send_notification(
                    notification_type=NotificationType.FEEDBACK_RECEIVED.value,
                    message=self._get_feedback_received_template('candidate'),
                    context=context,
                    channels=['email']
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando recepción de feedback: {str(e)}", exc_info=True)
            return False
            
    async def send_feedback_reminder(
        self,
        person: Person,
        vacancy: Vacante,
        interviewer: str,
        deadline: datetime
    ) -> bool:
        """
        Envía un recordatorio para enviar feedback.
        
        Args:
            person: Candidato evaluado
            vacancy: Vacante relacionada
            interviewer: Nombre del entrevistador
            deadline: Fecha límite para enviar el feedback
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'interviewer': interviewer,
                'deadline': deadline.strftime('%d/%m/%Y %H:%M'),
                'business_unit': self.business_unit.name
            }
            
            await self.send_notification(
                notification_type=NotificationType.REMINDER.value,
                message=self._get_feedback_reminder_template(),
                context=context,
                channels=['email', 'telegram']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando recordatorio de feedback: {str(e)}", exc_info=True)
            return False
        
    def _get_feedback_received_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'consultant': (
                "📋 *Feedback Recibido*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📝 *Tipo:* {feedback_type}\n\n"
                "📊 *Evaluación:* {evaluation}\n"
                "✅ *Fortalezas:*\n{strengths}\n"
                "📈 *Áreas de mejora:*\n{areas_for_improvement}\n"
                "💡 *Recomendación:* {recommendation}"
            ),
            'candidate': (
                "📋 *Feedback de Evaluación*\n\n"
                "👋 *{candidate_name}*\n\n"
                "Hemos recibido el feedback de tu evaluación para {position} en {company}.\n\n"
                "📊 *Evaluación:* {evaluation}\n"
                "✅ *Fortalezas:*\n{strengths}\n"
                "📈 *Áreas de mejora:*\n{areas_for_improvement}\n"
                "💡 *Recomendación:* {recommendation}"
            )
        }
        return templates.get(recipient_type, templates['consultant'])
        
    def _get_feedback_reminder_template(self) -> str:
        """Obtiene la plantilla para recordatorio de feedback."""
        return (
            "⏰ *Recordatorio de Feedback*\n\n"
            "👤 *Candidato:* {candidate_name}\n"
            "💼 *Posición:* {position}\n"
            "🏢 *Empresa:* {company}\n"
            "👥 *Entrevistador:* {interviewer}\n"
            "⏰ *Fecha límite:* {deadline}\n\n"
            "Por favor, completa el formulario de feedback antes de la fecha límite."
        )

    def send_followup_message(self, user_id, message, quick_replies=None):
        """
        Envía un mensaje de seguimiento al usuario (por canal/chat).
        quick_replies: lista de opciones rápidas si aplica.
        (Este método debe integrarse con el sistema de mensajería/chatbot real.)
        """
        # Pseudocódigo: integrar con WhatsApp/Telegram/email
        pass
