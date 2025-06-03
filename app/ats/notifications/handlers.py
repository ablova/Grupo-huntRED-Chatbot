"""
Manejadores de notificaciones para diferentes canales.

Implementa las clases necesarias para gestionar el envío de notificaciones
a través de diferentes canales como correo electrónico, WhatsApp, SMS, etc.
"""

import uuid
import logging
import asyncio
from typing import Dict, Optional, List, Any, Union
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string

from app.models import Person, BusinessUnit, Vacante, User, Notification, NotificationStatus, NotificationType, NotificationChannel, ChatState
from app.ats.chatbot.integrations.services import send_message_async, send_whatsapp

logger = logging.getLogger('notifications')

class NotificationHandler:
    """Clase base para todos los manejadores de notificaciones."""
    
    def __init__(self, business_unit: Optional[BusinessUnit] = None):
        self.business_unit = business_unit
    
    async def send(self, notification: Notification) -> bool:
        """
        Método abstracto para enviar una notificación.
        Debe ser implementado por las clases hijas.
        """
        raise NotImplementedError("Este método debe ser implementado por las clases hijas")
    
    def generate_verification_code(self) -> str:
        """
        Genera un código de verificación único para la notificación.
        """
        return str(uuid.uuid4())[:8].upper()
    
    def update_notification_status(self, notification: Notification, status: str, error: Optional[str] = None) -> None:
        """
        Actualiza el estado de una notificación.
        """
        notification.status = status
        notification.delivery_attempts += 1
        notification.last_delivery_attempt = timezone.now()
        
        if status == NotificationStatus.SENT:
            notification.mark_as_sent()
        elif status == NotificationStatus.DELIVERED:
            notification.mark_as_delivered()
        elif status == NotificationStatus.FAILED:
            notification.mark_as_failed(error)
        
        notification.save()
        logger.info(f"Notification {notification.id} updated to status: {status}")

class EmailNotificationHandler(NotificationHandler):
    """Manejador para enviar notificaciones por correo electrónico."""
    
    async def send(self, notification: Notification) -> bool:
        """
        Envía una notificación por correo electrónico.
        """
        try:
            recipient_email = notification.recipient.email
            
            if not recipient_email:
                self.update_notification_status(
                    notification, 
                    NotificationStatus.FAILED, 
                    "El destinatario no tiene un correo electrónico registrado"
                )
                return False
            
            # Configuramos los datos del correo
            subject = notification.title
            from_email = f"{notification.business_unit.name} <{settings.DEFAULT_FROM_EMAIL}>"
            html_content = notification.content
            
            # Si hay un código de verificación, lo incluimos en el contenido
            if notification.verification_code:
                html_content = f"{html_content}\n\nCódigo de verificación: {notification.verification_code}"
            
            # Enviamos el correo
            send_mail(
                subject=subject,
                message="",  # El contenido texto plano
                from_email=from_email,
                recipient_list=[recipient_email],
                html_message=html_content,
                fail_silently=False
            )
            
            self.update_notification_status(notification, NotificationStatus.SENT)
            return True
            
        except Exception as e:
            error_msg = f"Error al enviar notificación por correo: {str(e)}"
            logger.error(error_msg)
            self.update_notification_status(notification, NotificationStatus.FAILED, error_msg)
            return False

class WhatsAppNotificationHandler(NotificationHandler):
    """Manejador para enviar notificaciones por WhatsApp."""
    
    async def send(self, notification: Notification) -> bool:
        """
        Envía una notificación por WhatsApp.
        """
        try:
            recipient_phone = notification.recipient.telefono
            
            if not recipient_phone:
                self.update_notification_status(
                    notification, 
                    NotificationStatus.FAILED, 
                    "El destinatario no tiene un número de teléfono registrado"
                )
                return False
            
            # Generamos un identificador único para esta notificación de servicio
            notification_id = f"NOTIF_{notification.id}_{int(timezone.now().timestamp())}"
            
            # Prefijo para indicar que es un mensaje de servicio (no interactivo)
            service_prefix = "📢 *MENSAJE INFORMATIVO* 📢\n"
            
            # Configuramos el mensaje principal
            message = f"{service_prefix}*{notification.title}*\n\n{notification.content}"
            
            # Si hay un código de verificación, lo incluimos en el mensaje
            if notification.verification_code:
                message = f"{message}\n\nCódigo de verificación: *{notification.verification_code}*"
                
            # Añadimos un pie de mensaje indicando que es informativo
            footer = "\n\n---\n_Este es un mensaje informativo. No es necesario responder. Si necesita ayuda, envíe un mensaje nuevo o contacte a su consultor asignado._\n\n_ID: {notification_id}_"
            message = f"{message}{footer}"
            
            # Enviamos el mensaje
            business_unit_name = notification.business_unit.name.lower() if notification.business_unit else None
            
            # Registramos esta notificación en el sistema de ChatState para crear un tiempo de gracia
            try:
                # Buscamos si ya existe un ChatState para este usuario
                chat_state = ChatState.objects.filter(user_id=recipient_phone, channel='whatsapp').first()
                
                # Si existe, registramos el ID de la notificación y establecemos un tiempo de gracia
                if chat_state:
                    # Guardamos el estado actual para poder restaurarlo después del tiempo de gracia
                    previous_state = chat_state.state
                    
                    # Creamos o actualizamos los metadatos con información sobre esta notificación
                    metadata = chat_state.metadata or {}
                    metadata.update({
                        'service_notification': {
                            'id': notification_id,
                            'sent_at': timezone.now().isoformat(),
                            'grace_period_seconds': 300,  # 5 minutos de tiempo de gracia
                            'previous_state': previous_state
                        }
                    })
                    
                    # Actualizamos el ChatState con un estado especial y los metadatos
                    chat_state.metadata = metadata
                    chat_state.state = 'service_notification'  # Estado especial para notificaciones
                    chat_state.save(update_fields=['metadata', 'state'])
                    
                    logger.info(f"ChatState actualizado con estado de notificación para {recipient_phone}")
            except Exception as e:
                # Si hay un error, lo registramos pero continuamos con el envío del mensaje
                logger.error(f"Error al registrar notificación en ChatState: {e}")
            
            # Usamos la función asíncrona de la integración existente
            result = await send_message_async(
                platform="whatsapp",
                user_id=recipient_phone,
                message=message,
                business_unit_name=business_unit_name
            )
            
            if result.get('success', False):
                self.update_notification_status(notification, NotificationStatus.SENT)
                return True
            else:
                error_msg = result.get('error', 'Error desconocido al enviar WhatsApp')
                self.update_notification_status(notification, NotificationStatus.FAILED, error_msg)
                return False
            
        except Exception as e:
            error_msg = f"Error al enviar notificación por WhatsApp: {str(e)}"
            logger.error(error_msg)
            self.update_notification_status(notification, NotificationStatus.FAILED, error_msg)
            return False

class SMSNotificationHandler(NotificationHandler):
    """Manejador para enviar notificaciones por SMS."""
    
    async def send(self, notification: Notification) -> bool:
        """
        Envía una notificación por SMS.
        """
        # Implementación similar a WhatsApp, usando el servicio SMS correspondiente
        # Esta es una implementación básica que puede expandirse según las necesidades
        logger.info(f"SMS notification would be sent to {notification.recipient}")
        return True

class TelegramNotificationHandler(NotificationHandler):
    """Manejador para enviar notificaciones por Telegram."""
    
    async def send(self, notification: Notification) -> bool:
        """
        Envía una notificación por Telegram.
        """
        # Implementación usando la API de Telegram
        logger.info(f"Telegram notification would be sent to {notification.recipient}")
        return True

class AppNotificationHandler(NotificationHandler):
    """Manejador para enviar notificaciones dentro de la aplicación web."""
    
    async def send(self, notification: Notification) -> bool:
        """
        Registra una notificación para ser mostrada en la aplicación web.
        """
        # Las notificaciones en app simplemente se marcan como enviadas
        # ya que se mostrarán cuando el usuario acceda a la aplicación
        notification.app_data = {
            'displayed': False,
            'priority': 'normal',
            'icon': self._get_icon_for_notification_type(notification.notification_type)
        }
        notification.save()
        
        self.update_notification_status(notification, NotificationStatus.SENT)
        logger.info(f"App notification registered for {notification.recipient}")
        return True
    
    def _get_icon_for_notification_type(self, notification_type: str) -> str:
        """
        Devuelve el icono adecuado para cada tipo de notificación.
        """
        icons = {
            NotificationType.PROCESO_CREADO: 'fa-plus-circle',
            NotificationType.FEEDBACK_REQUERIDO: 'fa-comment-dots',
            NotificationType.CONFIRMACION_ENTREVISTA: 'fa-calendar-check',
            NotificationType.FELICITACION_CONTRATACION: 'fa-trophy',
            NotificationType.FIRMA_CONTRATO: 'fa-file-signature',
            NotificationType.EMISION_PROPUESTA: 'fa-file-invoice-dollar',
            NotificationType.RECORDATORIO_PAGO: 'fa-money-bill-wave',
            # Añadir más iconos según sea necesario
        }
        return icons.get(notification_type, 'fa-bell')

class SlackNotificationHandler(NotificationHandler):
    """Manejador para enviar notificaciones por Slack."""
    
    async def send(self, notification: Notification) -> bool:
        """
        Envía una notificación por Slack.
        """
        # Implementación usando la API de Slack
        logger.info(f"Slack notification would be sent to {notification.recipient}")
        return True
