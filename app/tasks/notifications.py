"""
Módulo de tareas de notificaciones para Grupo huntRED.
Gestiona el envío de notificaciones a través de diferentes canales: 
WhatsApp, Telegram, Email, Push, etc.
"""

import logging
import requests
import aiohttp
import asyncio
from celery import shared_task
from django.conf import settings
from app.models import BusinessUnit
from app.ats.chatbot.integrations.services import send_email, send_message
from app.ats.tasks.base import with_retry

# Configuración de logging
logger = logging.getLogger(__name__)

# Función auxiliar para enviar notificaciones a ntfy.sh
def send_ntfy_notification(topic, message, image_url=None):
    """
    Envía una notificación a ntfy.sh si está habilitado, con soporte para imágenes.
    
    Args:
        topic: Tema de la notificación
        message: Mensaje a enviar
        image_url: URL opcional de una imagen para adjuntar
        
    Returns:
        bool: True si se envió correctamente, False si hubo error
    """
    if not settings.NTFY_ENABLED:
        logger.info("Notificaciones ntfy.sh desactivadas en settings.")
        return False

    url = f'https://ntfy.sh/{topic}'  # Cambia a tu servidor auto-hospedado si aplica
    headers = {}
    data = message.encode('utf-8')

    # Autenticación: Priorizar token API si existe, sino usar usuario/contraseña
    if settings.NTFY_API_TOKEN:
        headers['Authorization'] = f'Bearer {settings.NTFY_API_TOKEN}'
    elif settings.NTFY_USERNAME and settings.NTFY_PASSWORD:
        headers['Authorization'] = f'Basic {requests.auth._basic_auth_str(settings.NTFY_USERNAME, settings.NTFY_PASSWORD)}'

    # Añadir imagen si se proporciona
    if image_url:
        headers['Attach'] = image_url  # URL de la imagen

    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            logger.info(f"Notificación enviada a {topic}: {message}" + (f" con imagen {image_url}" if image_url else ""))
            return True
        else:
            logger.error(f"Error enviando notificación a ntfy.sh: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Excepción enviando notificación a ntfy.sh: {str(e)}")
        return False

def get_business_unit(business_unit_id=None, default_name="amigro"):
    """Obtiene un objeto BusinessUnit por su ID o un valor por defecto."""
    if business_unit_id:
        return BusinessUnit.objects.get(id=business_unit_id)
    return BusinessUnit.objects.get(name__iexact=default_name)

@shared_task(bind=True, max_retries=3)
def send_linkedin_login_link(self, recipient_email, business_unit_id=None):
    """
    Envía un enlace de inicio de sesión de LinkedIn y notifica a los administradores.
    
    Args:
        recipient_email: Email del destinatario
        business_unit_id: ID opcional de la unidad de negocio
        
    Returns:
        dict: Resultado de la operación
    """
    try:
        # Obtener la unidad de negocio
        business_unit = get_business_unit(business_unit_id)
        
        # Enviar email con enlace de inicio de sesión
        subject = f"[{business_unit.name.upper()}] - Solicitud de inicio de sesión LinkedIn"
        from_email = settings.DEFAULT_FROM_EMAIL
        login_link = "https://www.linkedin.com/login"
        
        # Crear contenido HTML para el email
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #0A66C2; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
                .button {{ background-color: #0A66C2; color: white; padding: 10px 20px; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Inicio de Sesión LinkedIn Requerido</h2>
                </div>
                <div class="content">
                    <p>Hola,</p>
                    <p>Se requiere que inicies sesión en LinkedIn para continuar con el proceso.</p>
                    <p style="text-align: center;">
                        <a href="{login_link}" class="button">Iniciar Sesión en LinkedIn</a>
                    </p>
                    <p>Si tienes problemas para iniciar sesión, contacta a soporte.</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} {business_unit.name.capitalize()}. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Enviar email
        send_email(recipient_email, subject, html_content, from_email)
        
        # Notificar a administradores
        admin_emails = settings.ADMIN_EMAILS
        if admin_emails:
            admin_subject = f"LinkedIn Login Solicitado - {recipient_email}"
            admin_content = f"Se ha enviado un enlace de inicio de sesión LinkedIn a {recipient_email} desde {business_unit.name}."
            
            for admin_email in admin_emails:
                send_email(admin_email, admin_subject, admin_content, from_email)
        
        # Enviar notificación interna
        send_ntfy_notification("linkedin_login", f"Login solicitado: {recipient_email}")
        
        return {
            "status": "success",
            "message": f"Enlace de inicio de sesión enviado a {recipient_email}"
        }
        
    except Exception as e:
        logger.error(f"Error enviando enlace de LinkedIn: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=2 ** self.request.retries * 60)
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }

@shared_task(bind=True, max_retries=3)
def send_whatsapp_message_task(self, recipient, message, business_unit_id=None):
    """
    Envía un mensaje de WhatsApp a un destinatario.
    
    Args:
        recipient: Número de teléfono del destinatario
        message: Mensaje a enviar
        business_unit_id: ID opcional de la unidad de negocio
        
    Returns:
        dict: Resultado de la operación
    """
    try:
        business_unit = get_business_unit(business_unit_id)
        result = send_message(recipient, message, "whatsapp", business_unit)
        logger.info(f"Mensaje WhatsApp enviado a {recipient}")
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error enviando mensaje WhatsApp: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task(bind=True, max_retries=3)
def send_telegram_message_task(self, chat_id, message, business_unit_id=None):
    """
    Envía un mensaje de Telegram a un chat específico.
    
    Args:
        chat_id: ID del chat de Telegram
        message: Mensaje a enviar
        business_unit_id: ID opcional de la unidad de negocio
        
    Returns:
        dict: Resultado de la operación
    """
    try:
        business_unit = get_business_unit(business_unit_id)
        result = send_message(chat_id, message, "telegram", business_unit)
        logger.info(f"Mensaje Telegram enviado a {chat_id}")
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error enviando mensaje Telegram: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task(bind=True, max_retries=3)
def send_messenger_message_task(self, recipient_id, message, business_unit_id=None):
    """
    Envía un mensaje de Facebook Messenger a un destinatario.
    
    Args:
        recipient_id: ID del destinatario en Messenger
        message: Mensaje a enviar
        business_unit_id: ID opcional de la unidad de negocio
        
    Returns:
        dict: Resultado de la operación
    """
    try:
        business_unit = get_business_unit(business_unit_id)
        result = send_message(recipient_id, message, "messenger", business_unit)
        logger.info(f"Mensaje Messenger enviado a {recipient_id}")
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error enviando mensaje Messenger: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task(bind=True, max_retries=3)
def send_notification(self, channel, recipient, message, attachments=None, business_unit_id=None):
    """
    Envía una notificación a través del canal especificado.
    
    Args:
        channel: Canal de notificación (whatsapp, telegram, email, etc.)
        recipient: Destinatario (número, email, etc.)
        message: Contenido del mensaje
        attachments: Archivos adjuntos (opcional)
        business_unit_id: ID de la unidad de negocio (opcional)
    
    Returns:
        dict: Resultado de la operación
    """
    try:
        # Seleccionar la tarea correspondiente según el canal
        if channel == 'whatsapp':
            return send_whatsapp_message_task(recipient, message, business_unit_id)
        elif channel == 'telegram':
            return send_telegram_message_task(recipient, message, business_unit_id)
        elif channel == 'messenger':
            return send_messenger_message_task(recipient, message, business_unit_id)
        elif channel == 'email':
            # Implementar envío de email
            pass
        else:
            return {"status": "error", "message": f"Canal no soportado: {channel}"}
    except Exception as e:
        logger.error(f"Error enviando notificación por {channel}: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task(bind=True)
def aggregate_notifications(self, recipient_id, business_unit_id=None):
    """
    Agrega notificaciones pendientes y las envía en un solo mensaje.
    
    Args:
        recipient_id: ID del destinatario
        business_unit_id: ID de la unidad de negocio (opcional)
    
    Returns:
        dict: Resultado de la operación
    """
    # Implementar lógica de agregación
    pass
