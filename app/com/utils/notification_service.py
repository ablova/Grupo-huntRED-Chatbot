from typing import Dict, Optional, List
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from app.models import Notification, NotificationChannel, Person, Feedback
from app.com.utils import logger_utils
from app.com.utils.whatsapp import WhatsAppHandler
from app.com.utils.email import EmailHandler
import logging
import asyncio
import uuid
from datetime import timezone

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        """Inicializa el servicio de notificaciones."""
        self.logger = logger_utils.get_logger("notifications")
        self.whatsapp_handler = WhatsAppHandler()
        self.email_handler = EmailHandler()
        
    async def send_notification(self, recipient: Person, notification_type: str, content: str, metadata: Dict = None) -> Optional[Notification]:
        """
        Envía una notificación al destinatario.
        
        Args:
            recipient: Destinatario de la notificación
            notification_type: Tipo de notificación
            content: Contenido de la notificación
            metadata: Datos adicionales
            
        Returns:
            Notification: Objeto de notificación creado
        """
        try:
            # Crear notificación
            notification = await Notification.objects.acreate(
                recipient=recipient,
                notification_type=notification_type,
                content=content,
                metadata=metadata or {},
                status='PENDING'
            )
            
            # Verificar si el usuario tiene WhatsApp activado
            if recipient.whatsapp_enabled:
                success = await self._send_whatsapp_notification(notification)
                if success:
                    return notification
                    
            # Si WhatsApp falla o no está activado, enviar por correo
            await self._send_email_notification(notification)
            return notification
            
        except Exception as e:
            self.logger.error(f"Error enviando notificación: {str(e)}")
            return None
            
    async def _send_whatsapp_notification(self, notification: Notification) -> bool:
        """Envía la notificación por WhatsApp."""
        try:
            recipient = notification.recipient
            message = notification.content
            
            # Si es feedback, incluir ID
            if notification.notification_type == 'FEEDBACK' and notification.feedback:
                message += f"\nID del feedback: {notification.feedback.id}"
                
            success = await self.whatsapp_handler.send_message(recipient.phone, message)
            if success:
                notification.mark_as_sent()
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error enviando por WhatsApp: {str(e)}")
            return False
            
    async def _send_email_notification(self, notification: Notification) -> bool:
        """Envía la notificación por correo electrónico."""
        try:
            recipient = notification.recipient
            subject = f"Grupo huntRED® - {notification.notification_type}"
            
            # Renderizar template según el tipo de notificación
            template_name = f"notifications/{notification.notification_type.lower()}.html"
            context = {
                'content': notification.content,
                'metadata': notification.metadata,
                'recipient': recipient,
                'notification': notification
            }
            
            html_message = render_to_string(template_name, context)
            
            # Enviar correo
            await asyncio.to_thread(
                send_mail,
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [recipient.email],
                html_message=html_message
            )
            
            notification.mark_as_sent()
            return True
            
        except Exception as e:
            self.logger.error(f"Error enviando por correo: {str(e)}")
            return False
            
    async def get_unread_notifications(self, person: Person) -> List[Notification]:
        """Obtiene notificaciones no leídas para un usuario."""
        return await Notification.objects.filter(
            recipient=person,
            status__in=['SENT', 'DELIVERED']
        ).order_by('-created_at').all()
        
    async def mark_as_read(self, notification_id: int) -> bool:
        """Marca una notificación como leída."""
        try:
            notification = await Notification.objects.aget(id=notification_id)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
            
    async def skip_notification(self, notification_id: int) -> bool:
        """Omite una notificación."""
        try:
            notification = await Notification.objects.aget(id=notification_id)
            notification.skip_notification()
            return True
        except Notification.DoesNotExist:
            return False
            
    async def send_feedback_notification(self, interview: Entrevista) -> bool:
        """
        Envía notificación de feedback específico para entrevistas.
        
        Args:
            interview: Entrevista realizada
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            # Crear feedback
            feedback = await Feedback.objects.acreate(
                candidate=interview.candidato,
                interviewer=interview.tipo,
                feedback_type='INTERVIEW',
                status='PENDING'
            )
            
            # Preparar contenido
            content = f"Feedback solicitado para entrevista con {interview.candidato.nombre}\n"
            content += f"Vacante: {interview.vacante.titulo}\n"
            content += f"Fecha: {interview.fecha.strftime('%Y-%m-%d %H:%M')}\n"
            content += "\nPor favor, responda las siguientes preguntas:\n"
            content += "1. ¿El candidato/a le gustó? (Sí/No/Parcialmente)\n"
            content += "2. ¿Cumple con los requerimientos? (Sí/No/Parcialmente)\n"
            content += "3. ¿Qué requisitos faltan?\n"
            content += "4. Comentarios adicionales\n"
            
            # Enviar notificación
            return await self.send_notification(
                recipient=interview.tipo,
                notification_type='FEEDBACK',
                content=content,
                metadata={'interview_id': interview.id, 'feedback_id': feedback.id}
            )
            
        except Exception as e:
            self.logger.error(f"Error enviando notificación de feedback: {str(e)}")
            return False
