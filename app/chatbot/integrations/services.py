# /home/pablollh/app/chatbot/integrations/services.py

import logging
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.cache import cache
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from app.models import (
    WhatsAppAPI, TelegramAPI, InstagramAPI, MessengerAPI, MetaAPI, BusinessUnit, ConfiguracionBU,
    ChatState, Person, Vacante, Application, EnhancedNetworkGamificationProfile
)
from typing import Optional, List, Dict
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 600  # 10 minutos

platform_send_functions = {
    'telegram': 'send_telegram_message',
    'whatsapp': 'send_whatsapp_message',
    'messenger': 'send_messenger_message',
    'instagram': 'send_instagram_message',
}

async def send_message(
    platform: str,
    user_id: str,
    message: str,
    business_unit: BusinessUnit,
    options: Optional[List[dict]] = None
):
    """
    Envía un mensaje al usuario en la plataforma especificada, con opciones si las hay.
    Ajustado para que 'whatsapp' reciba (user_id, message, phone_id, buttons, business_unit).
    """
    from app.models import WhatsAppAPI  # Import puntual si lo requieres
    
    try:
        logger.info(f"[send_message] Platform: {platform}, User: {user_id}, BU: {business_unit.name}, Msg: {message[:30]}...")

        send_function_name = platform_send_functions.get(platform)
        if not send_function_name:
            logger.error(f"[send_message] Plataforma desconocida: {platform}")
            return

        # Obtener instancia del API
        api_instance = await get_api_instance(platform, business_unit)
        if not api_instance:
            logger.error(f"[send_message] No API configuration for {platform} / BU {business_unit.name}. Abort.")
            return

        # Importar dinámicamente la función de envío
        send_module = __import__(f'app.integrations.{platform}', fromlist=[send_function_name])
        send_function = getattr(send_module, send_function_name, None)

        if not send_function:
            logger.error(f"[send_message] No se encontró la función '{send_function_name}' en {platform}.py")
            return

        logger.debug(f"[send_message] Llamando a '{send_function_name}' con phone_id={getattr(api_instance, 'phoneID', None)}")

        # Llamada unificada, incluidas 'buttons' y 'phone_id'
        if platform == 'whatsapp':
            await send_function(
                user_id=user_id,
                message=message,
                phone_id=getattr(api_instance, 'phoneID', None), 
                buttons=options,  
                business_unit=business_unit
            )
        elif platform in ['telegram', 'messenger', 'instagram']:
            # Ejemplo de Telegram, Messenger, etc.
            await send_function(
                user_id=user_id,
                message=message,
                buttons=options,
                access_token=getattr(api_instance, 'page_access_token', None) or getattr(api_instance, 'api_key', None)
            )
        else:
            logger.error(f"[send_message] Plataforma no soportada: {platform}")

        if options:
            logger.debug(f"[send_message] Opciones incluidas: {options}")

    except Exception as e:
        logger.error(f"[send_message] Error enviando mensaje en {platform}: {e}", exc_info=True)

async def get_api_instance(platform: str, business_unit: BusinessUnit):
    """
    Obtiene la instancia de configuración de la API según la plataforma y unidad de negocio.
    """
    cache_key = f"api_instance:{platform}:{business_unit.id}"
    api_instance = cache.get(cache_key)

    if not api_instance:
        model_mapping = {
            'whatsapp': 'WhatsAppAPI',
            'telegram': 'TelegramAPI',
            'messenger': 'MessengerAPI',
            'instagram': 'InstagramAPI'
        }
        model_name = model_mapping.get(platform)
        if not model_name:
            logger.error(f"No model mapping found for platform: {platform}")
            return None

        model_class = getattr(__import__('app.models', fromlist=[model_name]), model_name)
        api_instance = await sync_to_async(model_class.objects.filter)(
            business_unit=business_unit, is_active=True
        ).select_related('business_unit').first()
        if not api_instance:
            logger.error(f"No API instance found for platform: {platform}, BU: {business_unit.name}")
            return None

        cache.set(cache_key, api_instance, CACHE_TIMEOUT)

    return api_instance

async def send_email(business_unit_name: str, subject: str, to_email: str, body: str, from_email: Optional[str] = None, domain_bu: str = "tudominio.com"):
    """
    Envía un correo electrónico utilizando la configuración SMTP de la unidad de negocio.
    """
    try:
        # Obtener configuración SMTP desde la caché
        cache_key = f"smtp_config:{business_unit_name}"
        config_bu = cache.get(cache_key)

        if not config_bu:
            config_bu = await sync_to_async(ConfiguracionBU.objects.select_related('business_unit').get)(
                business_unit__name=business_unit_name
            )
            cache.set(cache_key, config_bu, CACHE_TIMEOUT)

        smtp_host = config_bu.smtp_host
        smtp_port = config_bu.smtp_port
        smtp_username = config_bu.smtp_username
        smtp_password = config_bu.smtp_password
        use_tls = config_bu.smtp_use_tls
        use_ssl = config_bu.smtp_use_ssl

        # Crear el mensaje de correo
        msg = MIMEMultipart()
        msg['From'] = from_email or smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        # Conectar al servidor SMTP
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)

        if use_tls and not use_ssl:
            server.starttls()

        # Autenticarse y enviar el correo
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()

        logger.info(f"Correo enviado a {to_email} desde {msg['From']}")
        return {"status": "success", "message": "Correo enviado correctamente."}

    except ObjectDoesNotExist:
        logger.error(f"Configuración SMTP no encontrada para la unidad de negocio: {business_unit_name}")
        return {"status": "error", "message": "Configuración SMTP no encontrada para la Business Unit."}
    except Exception as e:
        logger.error(f"Error enviando correo electrónico: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

async def send_whatsapp_message(
    user_id: str, 
    message: str, 
    buttons: Optional[List[dict]] = None, 
    phone_id: Optional[str] = None, 
    business_unit: Optional[BusinessUnit] = None
):
    """
    Envía un mensaje directo a un usuario de WhatsApp, permitiendo botones y phone_id si se requiere.
    """
    try:
        if not phone_id and business_unit:
            # Si no se pasa phone_id y hay business_unit, busca la config
            whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter)(
                business_unit=business_unit, is_active=True
            ).select_related('business_unit').first()
            if not whatsapp_api:
                logger.error(f"[send_whatsapp_message] No se encontró WhatsAppAPI activo para {business_unit.name}")
                return
            phone_id = whatsapp_api.phoneID
            api_token = whatsapp_api.api_token
        else:
            # phone_id se pasa manual; obtener api_token
            if business_unit:
                whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter)(
                    business_unit=business_unit, is_active=True
                ).select_related('business_unit').first()
                api_token = whatsapp_api.api_token if whatsapp_api else None
            else:
                # Manejo minimal: phone_id y token están "hardcoded" o algo
                logger.warning("[send_whatsapp_message] No se pasó business_unit, asumiendo phone_id y token predefinidos.")
                api_token = phone_id  # <--- Ajustar según lógica real

        if not phone_id or not api_token:
            logger.error("[send_whatsapp_message] No se cuenta con phone_id o api_token válido.")
            return

        logger.debug(f"[send_whatsapp_message] user_id={user_id}, phone_id={phone_id}, tiene botones={bool(buttons)}")

        url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        # Construir payload base
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "text",
            "text": {
                "body": message
            }
        }

        # Si se proveen buttons, se cambia el 'type' a 'interactive'
        if buttons:
            logger.debug(f"[send_whatsapp_message] Convirtiendo a mensaje interactivo con {len(buttons)} botón(es).")
            formatted_buttons = []
            # Asumiendo que cada dict en 'buttons' es como {'title': '...', 'payload': '...'}
            for btn in buttons:
                formatted_buttons.append({
                    "type": "reply",
                    "reply": {
                        "id": btn.get('payload', 'btn_id'),
                        "title": btn.get('title', '')[:20]  # WhatsApp limita 20 chars
                    }
                })

            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": user_id,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {
                        "text": message
                    },
                    "action": {
                        "buttons": formatted_buttons
                    }
                }
            }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"[send_whatsapp_message] Mensaje enviado a {user_id}. Respuesta: {response.text[:200]}")

    except httpx.HTTPStatusError as e:
        logger.error(f"[send_whatsapp_message] Error HTTP al enviar mensaje a {user_id}: {e.response.text}", exc_info=True)
    except Exception as e:
        logger.error(f"[send_whatsapp_message] Error general al enviar mensaje a {user_id}: {e}", exc_info=True)

async def send_whatsapp_decision_buttons(user_id, message, buttons, business_unit):
    """
    Envía botones interactivos a través de WhatsApp usando la configuración asociada a la unidad de negocio.
    """
    from app.models import WhatsAppAPI

    try:
        # Obtener la configuración de WhatsAppAPI vinculada a la unidad de negocio
        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter)(
            business_unit=business_unit, is_active=True
        ).select_related('business_unit').first()
        
        if not whatsapp_api:
            raise ValueError(f"No se encontró configuración activa de WhatsAppAPI para la unidad de negocio: {business_unit.name}")

        url = f"https://graph.facebook.com/v17.0/{whatsapp_api.phoneID}/messages"
        headers = {
            "Authorization": f"Bearer {whatsapp_api.api_token}",
            "Content-Type": "application/json"
        }

        # Formatear botones para WhatsApp
        formatted_buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": button['payload'],
                    "title": button['title'][:20]  # WhatsApp limita a 20 caracteres
                }
            }
            for button in buttons
        ]

        # Construir el payload de la solicitud
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": message  # El mensaje que acompaña los botones
                },
                "action": {
                    "buttons": formatted_buttons
                }
            }
        }

        # Enviar la solicitud
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Botones enviados correctamente a WhatsApp. Respuesta: {response.text}")

    except ValueError as e:
        logger.error(f"Error en configuración: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Error al enviar botones a WhatsApp: {e.response.text}", exc_info=True)
    except Exception as e:
        logger.error(f"Error general al enviar botones a WhatsApp: {e}", exc_info=True)

async def reset_chat_state(user_id: Optional[str] = None):
    """
    Resetea el estado del chatbot para un usuario específico o para todos los usuarios.
    """
    try:
        if user_id:
            chat_state = await sync_to_async(ChatState.objects.get)(user_id=user_id)
            await sync_to_async(chat_state.delete)()
            logger.info(f"Chatbot state reset for user {user_id}.")
        else:
            await sync_to_async(ChatState.objects.all().delete)()
            logger.info("Chatbot state reset for all users.")
    except ChatState.DoesNotExist:
        logger.warning(f"No chatbot state found for user {user_id}.")
    except Exception as e:
        logger.error(f"Error resetting chatbot state: {e}", exc_info=True)

async def send_logo(platform, user_id, business_unit):
    """
    Envía el logo de la empresa al usuario.
    """
    try:
        configuracion = await sync_to_async(ConfiguracionBU.objects.filter)(business_unit=business_unit).select_related('business_unit').first()
        image_url = configuracion.logo_url if configuracion else "https://huntred.com/logo.png"

        if platform == 'whatsapp':
            await send_message(platform, user_id, 'Aquí tienes nuestro logo:', business_unit, options=[{'type': 'image', 'url': image_url}])
        elif platform == 'messenger':
            await send_message(platform, user_id, 'Aquí tienes nuestro logo:', business_unit, options=[{'type': 'image', 'url': image_url}])
        else:
            logger.error(f"Image sending not supported for platform {platform}")

    except Exception as e:
        logger.error(f"Error sending image on {platform}: {e}", exc_info=True)

async def send_image(platform, user_id, message, image_url, business_unit):
    """
    Envía una imagen al usuario.
    """
    try:
        await send_message(platform, user_id, message, business_unit, options=[{'type': 'image', 'url': image_url}])
        logger.info(f"Imagen enviada a {user_id} en {platform}")
    except Exception as e:
        logger.error(f"Error enviando imagen en {platform} a {user_id}: {e}", exc_info=True)

async def send_menu(platform, user_id, business_unit):
    """
    Envía el menú principal al usuario.
    """
    menu_message = """
El Menú Principal de huntred.com
1 - Bienvenida
2 - Registro
3 - Ver Oportunidades
4 - Actualizar Perfil
5 - Invitar Amigos
6 - Términos y Condiciones
7 - Contacto
8 - Solicitar Ayuda
"""
    await send_message(platform, user_id, menu_message, business_unit)

def render_dynamic_content(template_text, context):
    """
    Renders dynamic content in a message template using variables from the context.
    """
    try:
        content = template_text.format(**context)
        return content
    except KeyError as e:
        logger.error(f"Error rendering dynamic content: Missing variable {e}")
        return template_text  # Return the original text in case of error

async def process_text_message(platform, sender_id, message_text, business_unit):
    """
    Procesa un mensaje de texto recibido.
    """
    from app.chatbot import ChatBotHandler
    chatbot_handler = ChatBotHandler()

    try:
        await chatbot_handler.process_message(
            platform=platform,
            user_id=sender_id,
            text=message_text,
            business_unit=business_unit
        )
    except Exception as e:
        logger.error(f"Error processing text message: {e}", exc_info=True)

async def send_options(platform, user_id, message, buttons=None, business_unit: Optional[BusinessUnit] = None):
    """
    Envía opciones de respuesta al usuario.
    """
    try:
        if platform == 'whatsapp' and buttons and business_unit:
            formatted_buttons = [{"title": button['title']} for button in buttons]
            await send_whatsapp_decision_buttons(
                user_id=user_id,
                message=message,
                buttons=formatted_buttons,
                business_unit=business_unit
            )
        elif platform == 'telegram' and buttons:
            from app.integrations.telegram import send_telegram_buttons
            telegram_buttons = [
                [{"text": button['title'], "callback_data": button['payload']}]
                for button in buttons
            ]
            await send_telegram_buttons(
                user_id, message, telegram_buttons, business_unit.telegram_api.api_key
            )
        elif platform == 'messenger' and buttons and business_unit:
            from app.integrations.messenger import send_messenger_buttons
            quick_reply_options = [
                {'content_type': 'text', 'title': button['title'], 'payload': button['payload']}
                for button in buttons
            ]
            await send_messenger_buttons(
                user_id,
                message,
                quick_reply_options,
                business_unit.messenger_api.page_access_token,
            )
        elif platform == 'instagram' and buttons and business_unit:
            from app.integrations.instagram import send_instagram_buttons
            await send_instagram_buttons(
                user_id, message, buttons, business_unit.instagram_api.access_token
            )
        else:
            logger.error(f"Plataforma desconocida o botones faltantes: {platform}")

    except Exception as e:
        logger.error(f"Error enviando opciones a través de {platform}: {e}", exc_info=True)

async def notify_employer(worker, message):
    """
    Notifica al empleador que un evento ha ocurrido.
    """
    try:
        if worker.whatsapp:
            whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter)(
                phoneID=worker.whatsapp, is_active=True
            ).select_related('business_unit').first()
            if whatsapp_api:
                await send_whatsapp_message(
                    user_id=worker.whatsapp,
                    message=message,
                    phone_id=whatsapp_api.phoneID,
                    business_unit=whatsapp_api.business_unit
                )
                logger.info(f"Notificación enviada al empleador {worker.name} vía WhatsApp.")
            else:
                logger.error("No se encontró configuración de WhatsAppAPI.")
        else:
            logger.warning(f"El empleador {worker.name} no tiene número de WhatsApp configurado.")
    except Exception as e:
        logger.error(f"Error enviando notificación al empleador {worker.name}: {e}", exc_info=True)

class GamificationService:
    def __init__(self):
        pass

    async def award_points(self, user: Person, activity_type: str, points: int = 10):
        """
        Otorga puntos al usuario basado en el tipo de actividad.
        """
        try:
            profile, created = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get_or_create)(
                user=user,
                defaults={'points': 0, 'level': 1}
            )
            profile.award_points(activity_type, points)
            await sync_to_async(profile.save)()
            logger.info(f"Otorgados {points} puntos a {user.nombre} por {activity_type}. Total puntos: {profile.points}")
        except Exception as e:
            logger.error(f"Error otorgando puntos a {user.nombre}: {e}", exc_info=True)

    async def notify_user_gamification_update(self, user: Person, activity_type: str):
        """
        Notifica al usuario sobre la actualización de puntos de gamificación.
        """
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            message = f"¡Has ganado puntos por {activity_type}! Ahora tienes {profile.points} puntos."
            # Determinar la plataforma del usuario para enviar la notificación
            platform = user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp'  # Asumiendo WhatsApp por defecto
            business_unit = user.chat_state.business_unit if hasattr(user, 'chat_state') else user.business_unit

            if platform and business_unit:
                await send_message(
                    platform=platform,
                    user_id=user.phone,
                    message=message,
                    business_unit=business_unit
                )
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            logger.warning(f"No perfil de gamificación encontrado para {user.nombre}")
        except Exception as e:
            logger.error(f"Error notificando actualización de gamificación a {user.nombre}: {e}", exc_info=True)

    async def generate_challenges(self, user: Person):
        """Genera desafíos personalizados para el usuario."""
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            return profile.generate_networking_challenges()
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            return []

    async def notify_user_challenges(self, user: Person):
        """Notifica al usuario sobre nuevos desafíos."""
        challenges = await self.generate_challenges(user)
        # Enviar desafíos al usuario a través del canal activo
        if challenges:
            message = f"Tienes nuevos desafíos: {', '.join(challenges)}"
            await send_message(
                platform=user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp',
                user_id=user.phone,
                message=message,
                business_unit=user.chat_state.business_unit if hasattr(user, 'chat_state') else user.business_unit
            )