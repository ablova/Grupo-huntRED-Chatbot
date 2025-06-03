"""
Servicio centralizado de notificaciones para Grupo huntRED®.
Este módulo implementa un sistema unificado de notificaciones para todos 
los componentes del sistema, siguiendo las reglas globales.
"""

import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.db import models
from django.core.mail import send_mail
from django.template.loader import render_to_string
from asgiref.sync import sync_to_async
from app.ats.utils.logging_manager import LoggingManager, log_function_call, log_async_function_call
from app.ats.utils.rbac import RBAC

logger = LoggingManager.get_logger('notifications')

class NotificationChannel:
    """Canales de notificación disponibles en el sistema."""
    EMAIL = 'email'
    SMS = 'sms'
    WHATSAPP = 'whatsapp'
    TELEGRAM = 'telegram'
    PUSH = 'push'
    INTERNAL = 'internal'
    ALL = 'all'

class NotificationPriority:
    """Niveles de prioridad para notificaciones."""
    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'
    URGENT = 'urgent'

class NotificationService:
    """
    Servicio centralizado para envío de notificaciones en todas las unidades de negocio.
    Implementa una API unificada para diferentes canales de comunicación.
    """
    
    # Mapeo de BusinessUnit a configuraciones específicas
    BU_CONFIGS = {
        'huntRED': {
            'default_channel': NotificationChannel.EMAIL,
            'channels': [NotificationChannel.EMAIL, NotificationChannel.INTERNAL, NotificationChannel.WHATSAPP],
            'email_template_prefix': 'notifications/huntred'
        },
        'huntU': {
            'default_channel': NotificationChannel.EMAIL,
            'channels': [NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.WHATSAPP],
            'email_template_prefix': 'notifications/huntu'
        },
        'Amigro': {
            'default_channel': NotificationChannel.WHATSAPP,
            'channels': [NotificationChannel.WHATSAPP, NotificationChannel.SMS, NotificationChannel.EMAIL],
            'email_template_prefix': 'notifications/amigro'
        },
        'SEXSI': {
            'default_channel': NotificationChannel.EMAIL,
            'channels': [NotificationChannel.EMAIL, NotificationChannel.INTERNAL],
            'email_template_prefix': 'notifications/sexsi'
        },
        'MilkyLeak': {
            'default_channel': NotificationChannel.PUSH,
            'channels': [NotificationChannel.PUSH, NotificationChannel.EMAIL],
            'email_template_prefix': 'notifications/milkyleak'
        }
    }
    
    # Configuración por defecto para cualquier BU no especificada
    DEFAULT_CONFIG = {
        'default_channel': NotificationChannel.EMAIL,
        'channels': [NotificationChannel.EMAIL, NotificationChannel.INTERNAL],
        'email_template_prefix': 'notifications/default'
    }
    
    @classmethod
    def get_bu_config(cls, bu_name=None):
        """
        Obtiene la configuración específica para una BU.
        
        Args:
            bu_name: Nombre de la Business Unit
            
        Returns:
            dict: Configuración para la BU
        """
        if bu_name and bu_name in cls.BU_CONFIGS:
            return cls.BU_CONFIGS[bu_name]
        return cls.DEFAULT_CONFIG
    
    @classmethod
    @log_function_call(module='notifications')
    def send_notification(cls, 
                         recipient: Union[str, Dict, models.Model],
                         subject: str,
                         message: str,
                         channel: str = None,
                         template: str = None,
                         context: Dict = None,
                         priority: str = NotificationPriority.NORMAL,
                         bu_name: str = None,
                         sender: Union[str, Dict, models.Model] = None,
                         metadata: Dict = None) -> Dict:
        """
        Envía una notificación a través del canal especificado.
        
        Args:
            recipient: Destinatario (email, ID, objeto Person, etc.)
            subject: Asunto de la notificación
            message: Mensaje principal
            channel: Canal de envío (email, sms, whatsapp, etc.)
            template: Plantilla específica para renderizar
            context: Contexto para renderizado de plantilla
            priority: Prioridad de la notificación
            bu_name: Nombre de la BU (para seleccionar configuración)
            sender: Remitente de la notificación
            metadata: Metadatos adicionales
            
        Returns:
            Dict: Resultado del envío
        """
        # Obtener configuración de BU
        bu_config = cls.get_bu_config(bu_name)
        
        # Determinar canal si no se especificó
        if not channel:
            channel = bu_config['default_channel']
        
        # Normalizar recipient
        recipient_info = cls._normalize_recipient(recipient)
        
        # Normalizar sender
        sender_info = cls._normalize_sender(sender)
        
        # Consolidar contexto
        full_context = context or {}
        full_context.update({
            'subject': subject,
            'message': message,
            'recipient': recipient_info,
            'sender': sender_info,
            'bu_name': bu_name,
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        })
        
        # Registrar intento de notificación
        notification_id = cls._log_notification_attempt(
            recipient=recipient_info,
            subject=subject,
            channel=channel,
            priority=priority,
            bu_name=bu_name,
            metadata=metadata or {}
        )
        
        # Enviar por el canal apropiado
        result = {
            'success': False,
            'notification_id': notification_id,
            'channel': channel,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if channel == NotificationChannel.EMAIL:
                result = cls._send_email(
                    recipient_info,
                    subject,
                    message,
                    template,
                    full_context,
                    bu_name
                )
            elif channel == NotificationChannel.SMS:
                result = cls._send_sms(
                    recipient_info,
                    message,
                    full_context
                )
            elif channel == NotificationChannel.WHATSAPP:
                result = cls._send_whatsapp(
                    recipient_info,
                    message,
                    full_context
                )
            elif channel == NotificationChannel.INTERNAL:
                result = cls._send_internal(
                    recipient_info,
                    subject,
                    message,
                    full_context
                )
            elif channel == NotificationChannel.PUSH:
                result = cls._send_push(
                    recipient_info,
                    subject,
                    message,
                    full_context
                )
            elif channel == NotificationChannel.ALL:
                # Enviar por todos los canales disponibles
                results = []
                for ch in bu_config['channels']:
                    res = cls.send_notification(
                        recipient=recipient,
                        subject=subject,
                        message=message,
                        channel=ch,
                        template=template,
                        context=context,
                        priority=priority,
                        bu_name=bu_name,
                        sender=sender,
                        metadata=metadata
                    )
                    results.append(res)
                
                # Combinar resultados
                success = any(r['success'] for r in results)
                result = {
                    'success': success,
                    'notification_id': notification_id,
                    'channel': NotificationChannel.ALL,
                    'results': results,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                result['error'] = f"Canal no soportado: {channel}"
                logger.warning(f"Notification sent through unsupported channel: {channel}")
            
            # Actualizar registro de notificación
            cls._update_notification_status(
                notification_id,
                result.get('success', False),
                result.get('error')
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error sending notification: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Actualizar registro con error
            cls._update_notification_status(
                notification_id,
                False,
                error_msg
            )
            
            result['success'] = False
            result['error'] = error_msg
            return result
    
    @classmethod
    @log_async_function_call(module='notifications')
    async def send_notification_async(cls, 
                                    recipient: Union[str, Dict, models.Model],
                                    subject: str,
                                    message: str,
                                    channel: str = None,
                                    template: str = None,
                                    context: Dict = None,
                                    priority: str = NotificationPriority.NORMAL,
                                    bu_name: str = None,
                                    sender: Union[str, Dict, models.Model] = None,
                                    metadata: Dict = None) -> Dict:
        """
        Versión asincrónica de send_notification.
        Todos los parámetros son idénticos a send_notification.
        """
        # Usar una función auxiliar sincrónica y convertirla a asíncrona
        send_func = sync_to_async(cls.send_notification)
        return await send_func(
            recipient=recipient,
            subject=subject,
            message=message,
            channel=channel,
            template=template,
            context=context,
            priority=priority,
            bu_name=bu_name,
            sender=sender,
            metadata=metadata
        )
    
    @classmethod
    @log_function_call(module='notifications')
    def send_bulk_notification(cls,
                              recipients: List[Union[str, Dict, models.Model]],
                              subject: str,
                              message: str,
                              channel: str = None,
                              template: str = None,
                              context: Dict = None,
                              priority: str = NotificationPriority.NORMAL,
                              bu_name: str = None,
                              sender: Union[str, Dict, models.Model] = None,
                              metadata: Dict = None) -> Dict:
        """
        Envía notificaciones masivas a múltiples destinatarios.
        
        Args:
            recipients: Lista de destinatarios
            (resto de parámetros igual a send_notification)
            
        Returns:
            Dict: Resultado del envío masivo
        """
        if not recipients:
            return {
                'success': False,
                'error': 'No recipients specified',
                'timestamp': datetime.now().isoformat()
            }
        
        # Utilizar Celery para procesamiento en segundo plano
        try:
            from app.ats.tasks.notifications import send_bulk_notifications_task
            
            # Normalizar destinatarios para serialización
            normalized_recipients = []
            for recipient in recipients:
                if isinstance(recipient, models.Model):
                    # Si es una instancia de modelo, guardar ID y tipo
                    normalized_recipients.append({
                        'type': recipient.__class__.__name__,
                        'id': recipient.id,
                        'str': str(recipient)
                    })
                else:
                    normalized_recipients.append(recipient)
            
            # Lanzar tarea en segundo plano
            task = send_bulk_notifications_task.delay(
                recipients=normalized_recipients,
                subject=subject,
                message=message,
                channel=channel,
                template=template,
                context=context,
                priority=priority,
                bu_name=bu_name,
                sender=cls._normalize_sender(sender),
                metadata=metadata
            )
            
            return {
                'success': True,
                'task_id': task.id,
                'recipients_count': len(recipients),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error scheduling bulk notifications: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
    
    # Métodos para canales específicos
    
    @classmethod
    def _send_email(cls, recipient, subject, message, template, context, bu_name):
        """Envía notificación por email."""
        # Determinar email del destinatario
        to_email = cls._get_recipient_email(recipient)
        if not to_email:
            return {'success': False, 'error': 'No email address for recipient'}
        
        # Determinar plantilla apropiada
        bu_config = cls.get_bu_config(bu_name)
        template_prefix = bu_config['email_template_prefix']
        
        if template:
            template_name = template
        else:
            template_name = f"{template_prefix}/notification.html"
        
        # Renderizar contenido HTML
        try:
            html_message = render_to_string(template_name, context)
        except Exception as e:
            logger.error(f"Error rendering email template {template_name}: {str(e)}")
            # Fallback a mensaje de texto plano
            html_message = message
        
        # Enviar email
        try:
            from_email = settings.DEFAULT_FROM_EMAIL
            send_mail(
                subject=subject,
                message=message,  # Versión texto plano
                from_email=from_email,
                recipient_list=[to_email],
                html_message=html_message
            )
            
            return {
                'success': True,
                'channel': NotificationChannel.EMAIL,
                'recipient_email': to_email
            }
            
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'channel': NotificationChannel.EMAIL
            }
    
    @classmethod
    def _send_sms(cls, recipient, message, context):
        """Envía notificación por SMS."""
        # Determinar número de teléfono del destinatario
        phone = cls._get_recipient_phone(recipient)
        if not phone:
            return {'success': False, 'error': 'No phone number for recipient'}
        
        # Implementar integración con proveedor SMS
        # En este ejemplo, usamos un mock
        try:
            logger.info(f"SMS notification would be sent to {phone}: {message[:50]}...")
            
            # Aquí iría la integración real con un servicio como Twilio, SNS, etc.
            # Por ejemplo, con Twilio:
            """
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            sms = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone
            )
            sms_id = sms.sid
            """
            sms_id = f"mock-sms-{int(datetime.now().timestamp())}"
            
            return {
                'success': True,
                'channel': NotificationChannel.SMS,
                'recipient_phone': phone,
                'sms_id': sms_id
            }
            
        except Exception as e:
            error_msg = f"Error sending SMS: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'channel': NotificationChannel.SMS
            }
    
    @classmethod
    def _send_whatsapp(cls, recipient, message, context):
        """Envía notificación por WhatsApp."""
        # Determinar número de teléfono del destinatario
        phone = cls._get_recipient_phone(recipient)
        if not phone:
            return {'success': False, 'error': 'No phone number for recipient'}
        
        # Implementar integración con WhatsApp API
        try:
            logger.info(f"WhatsApp notification would be sent to {phone}: {message[:50]}...")
            
            # Aquí iría la integración real con WhatsApp Business API
            # Por ejemplo:
            """
            import requests
            response = requests.post(
                f"{settings.WHATSAPP_API_URL}/messages",
                headers={
                    "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "to": phone,
                    "type": "text",
                    "text": {
                        "body": message
                    }
                }
            )
            response.raise_for_status()
            whatsapp_id = response.json().get("messages", [{}])[0].get("id")
            """
            whatsapp_id = f"mock-wa-{int(datetime.now().timestamp())}"
            
            return {
                'success': True,
                'channel': NotificationChannel.WHATSAPP,
                'recipient_phone': phone,
                'whatsapp_id': whatsapp_id
            }
            
        except Exception as e:
            error_msg = f"Error sending WhatsApp message: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'channel': NotificationChannel.WHATSAPP
            }
    
    @classmethod
    def _send_internal(cls, recipient, subject, message, context):
        """Envía notificación interna en el sistema."""
        # Determinar ID de usuario del destinatario
        user_id = cls._get_recipient_user_id(recipient)
        if not user_id:
            return {'success': False, 'error': 'No user ID for recipient'}
        
        # Crear notificación interna en la base de datos
        try:
            from app.models import InternalNotification
            
            notification = InternalNotification.objects.create(
                user_id=user_id,
                title=subject,
                message=message,
                data=json.dumps(context, default=str),
                is_read=False
            )
            
            return {
                'success': True,
                'channel': NotificationChannel.INTERNAL,
                'notification_db_id': notification.id
            }
            
        except Exception as e:
            error_msg = f"Error creating internal notification: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'channel': NotificationChannel.INTERNAL
            }
    
    @classmethod
    def _send_push(cls, recipient, subject, message, context):
        """Envía notificación push."""
        # Determinar token de dispositivo del destinatario
        device_token = cls._get_recipient_device_token(recipient)
        if not device_token:
            return {'success': False, 'error': 'No device token for recipient'}
        
        # Implementar integración con servicio de notificaciones push
        try:
            logger.info(f"Push notification would be sent to token {device_token[:10]}...: {subject}")
            
            # Aquí iría la integración real con FCM, APNS, etc.
            # Por ejemplo, con Firebase Cloud Messaging:
            """
            from firebase_admin import messaging
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=subject,
                    body=message,
                ),
                data=context,
                token=device_token,
            )
            
            response = messaging.send(message)
            """
            push_id = f"mock-push-{int(datetime.now().timestamp())}"
            
            return {
                'success': True,
                'channel': NotificationChannel.PUSH,
                'push_id': push_id
            }
            
        except Exception as e:
            error_msg = f"Error sending push notification: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'channel': NotificationChannel.PUSH
            }
    
    # Métodos auxiliares
    
    @classmethod
    def _normalize_recipient(cls, recipient):
        """Normaliza el destinatario a un formato estándar."""
        if not recipient:
            return {}
            
        if isinstance(recipient, str):
            # Verificar si es email o teléfono
            if '@' in recipient:
                return {'email': recipient}
            else:
                return {'phone': recipient}
                
        if isinstance(recipient, dict):
            return recipient
            
        if isinstance(recipient, models.Model):
            # Extraer información relevante del modelo
            result = {'id': recipient.id, 'model': recipient.__class__.__name__}
            
            # Intentar obtener campos comunes
            for field in ['email', 'phone', 'name', 'user_id', 'device_token']:
                if hasattr(recipient, field):
                    result[field] = getattr(recipient, field)
            
            return result
            
        # Último recurso
        return {'raw': str(recipient)}
    
    @classmethod
    def _normalize_sender(cls, sender):
        """Normaliza el remitente a un formato estándar."""
        if not sender:
            return {
                'name': settings.DEFAULT_NOTIFICATION_SENDER_NAME,
                'email': settings.DEFAULT_FROM_EMAIL
            }
            
        if isinstance(sender, str):
            if '@' in sender:
                return {'email': sender}
            return {'name': sender}
                
        if isinstance(sender, dict):
            return sender
            
        if isinstance(sender, models.Model):
            # Extraer información relevante del modelo
            result = {'id': sender.id, 'model': sender.__class__.__name__}
            
            # Intentar obtener campos comunes
            for field in ['email', 'name', 'user_id']:
                if hasattr(sender, field):
                    result[field] = getattr(sender, field)
            
            return result
            
        # Último recurso
        return {'raw': str(sender)}
    
    @classmethod
    def _get_recipient_email(cls, recipient):
        """Extrae el email del destinatario normalizado."""
        if isinstance(recipient, dict):
            # Probar diferentes campos donde podría estar el email
            if 'email' in recipient:
                return recipient['email']
            
            # Si tenemos un Person o User, intentar obtener de la base de datos
            if 'model' in recipient and 'id' in recipient:
                model_name = recipient['model']
                obj_id = recipient['id']
                
                try:
                    from django.apps import apps
                    Model = apps.get_model('app', model_name)
                    obj = Model.objects.get(id=obj_id)
                    
                    if hasattr(obj, 'email'):
                        return obj.email
                    
                    if hasattr(obj, 'user') and hasattr(obj.user, 'email'):
                        return obj.user.email
                except Exception:
                    pass
        
        return None
    
    @classmethod
    def _get_recipient_phone(cls, recipient):
        """Extrae el teléfono del destinatario normalizado."""
        if isinstance(recipient, dict):
            # Probar diferentes campos donde podría estar el teléfono
            for field in ['phone', 'telefono', 'phone_number', 'mobile']:
                if field in recipient:
                    return recipient[field]
            
            # Si tenemos un Person o User, intentar obtener de la base de datos
            if 'model' in recipient and 'id' in recipient:
                model_name = recipient['model']
                obj_id = recipient['id']
                
                try:
                    from django.apps import apps
                    Model = apps.get_model('app', model_name)
                    obj = Model.objects.get(id=obj_id)
                    
                    for field in ['phone', 'telefono', 'phone_number', 'mobile']:
                        if hasattr(obj, field):
                            return getattr(obj, field)
                except Exception:
                    pass
        
        return None
    
    @classmethod
    def _get_recipient_user_id(cls, recipient):
        """Extrae el ID de usuario del destinatario normalizado."""
        if isinstance(recipient, dict):
            # Probar diferentes campos donde podría estar el ID
            if 'user_id' in recipient:
                return recipient['user_id']
            
            if 'id' in recipient:
                return recipient['id']
        
        return None
    
    @classmethod
    def _get_recipient_device_token(cls, recipient):
        """Extrae el token de dispositivo del destinatario normalizado."""
        if isinstance(recipient, dict):
            # Probar diferentes campos donde podría estar el token
            for field in ['device_token', 'push_token', 'fcm_token']:
                if field in recipient:
                    return recipient[field]
            
            # Si tenemos un Person o User, intentar obtener de la base de datos
            if 'model' in recipient and 'id' in recipient:
                model_name = recipient['model']
                obj_id = recipient['id']
                
                try:
                    from django.apps import apps
                    Model = apps.get_model('app', model_name)
                    obj = Model.objects.get(id=obj_id)
                    
                    for field in ['device_token', 'push_token', 'fcm_token']:
                        if hasattr(obj, field):
                            return getattr(obj, field)
                            
                    # Buscar en device tokens relacionados
                    if hasattr(obj, 'device_tokens'):
                        tokens = obj.device_tokens.filter(is_active=True).values_list('token', flat=True)
                        if tokens:
                            return tokens[0]
                except Exception:
                    pass
        
        return None
    
    @classmethod
    def _log_notification_attempt(cls, recipient, subject, channel, priority, bu_name, metadata):
        """Registra un intento de notificación en la base de datos."""
        try:
            from app.models import NotificationLog
            
            # Extraer información del destinatario
            recipient_id = None
            recipient_type = None
            recipient_identifier = None
            
            if isinstance(recipient, dict):
                recipient_id = recipient.get('id')
                recipient_type = recipient.get('model')
                
                # Determinar identificador (email o teléfono)
                recipient_identifier = (
                    recipient.get('email') or 
                    recipient.get('phone') or 
                    str(recipient_id)
                )
            
            # Crear registro
            log = NotificationLog.objects.create(
                recipient_id=recipient_id,
                recipient_type=recipient_type,
                recipient_identifier=recipient_identifier,
                subject=subject,
                channel=channel,
                priority=priority,
                bu_name=bu_name,
                status='pending',
                metadata=json.dumps(metadata, default=str)
            )
            
            return log.id
            
        except Exception as e:
            logger.error(f"Error logging notification attempt: {str(e)}")
            return None
    
    @classmethod
    def _update_notification_status(cls, notification_id, success, error=None):
        """Actualiza el estado de una notificación en la base de datos."""
        if not notification_id:
            return False
            
        try:
            from app.models import NotificationLog
            
            log = NotificationLog.objects.get(id=notification_id)
            log.status = 'delivered' if success else 'failed'
            
            if error:
                log.error_message = error
                
            log.delivered_at = datetime.now() if success else None
            log.save(update_fields=['status', 'error_message', 'delivered_at'])
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating notification status: {str(e)}")
            return False
