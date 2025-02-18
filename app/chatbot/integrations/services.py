# /home/pablo/app/chatbot/integrations/services.py
import logging
import smtplib
import httpx
import asyncio
import ssl

from app.models import BusinessUnit, ConfiguracionBU
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
# Semáforo para controlar la concurrencia en WhatsApp (se usa en whatsapp.py)
whatsapp_semaphore = asyncio.Semaphore(10)

# Constantes globales
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0  # segundos
CACHE_TIMEOUT = 600     # 10 minutos

platform_send_functions = {
    'telegram': 'send_telegram_message',
    'whatsapp': 'send_whatsapp_message',
    'messenger': 'send_messenger_message',
    'instagram': 'send_instagram_message',
}

# Función helper para ejecutar consultas sincrónicas
async def execute_sync(query_lambda):
    return await sync_to_async(query_lambda)()

async def send_message(
    platform: str,
    user_id: str,
    message: str,
    business_unit: BusinessUnit,
    options: Optional[List[dict]] = None
):
    """
    Envía un mensaje al usuario en la plataforma especificada, delegando en la función
    específica de cada canal. Maneja WhatsApp, Telegram, Messenger e Instagram.
    """
    try:
        logger.info(f"[send_message] Plataforma: {platform}, User: {user_id}, BU: {business_unit.name}, Msg: {message[:30]}...")

        send_function_name = platform_send_functions.get(platform)
        if not send_function_name:
            logger.error(f"[send_message] Plataforma desconocida: {platform}")
            return

        # Obtener la instancia de API de forma asíncrona
        api_instance = await get_api_instance(platform, business_unit)
        if not api_instance:
            logger.error(f"[send_message] No se encontró configuración API para {platform} / BU {business_unit.name}. Abortando.")
            return

        # Importar dinámicamente la función de envío
        send_module = __import__(f'app.chatbot.integrations.{platform}', fromlist=[send_function_name])
        send_function = getattr(send_module, send_function_name, None)
        if not send_function:
            logger.error(f"[send_message] Función '{send_function_name}' no encontrada en {platform}.py")
            return

        logger.debug(f"[send_message] Llamando a '{send_function_name}' con phone_id={getattr(api_instance, 'phoneID', None)}")

        # 🟢 **Manejo especial para WhatsApp**
        if platform == 'whatsapp':
            from app.chatbot.integrations.whatsapp import send_whatsapp_message

            # Si los botones incluyen una URL, enviarla antes del mensaje principal
            url_buttons = [btn for btn in options if "url" in btn] if options else []
            if url_buttons:
                for btn in url_buttons:
                    url_msg = f"Aquí tienes más información: {btn['url']}"
                    await send_function(
                        user_id=user_id,
                        message=url_msg,
                        phone_id=getattr(api_instance, 'phoneID', None),
                        buttons=None,
                        business_unit=business_unit
                    )
                    await asyncio.sleep(0.5)  # Evitar bloqueos de WhatsApp

            # Enviar mensaje principal con botones (sin URL)
            valid_buttons = [btn for btn in options if "url" not in btn] if options else None
            await send_function(
                user_id=user_id,
                message=message,
                phone_id=getattr(api_instance, 'phoneID', None),
                buttons=valid_buttons,
                business_unit=business_unit
            )

        # 🟢 **Manejo especial para Telegram**
        elif platform == 'telegram':
            from app.chatbot.integrations.telegram import send_telegram_message
            await send_function(
                chat_id=user_id,
                message=message
            )  # Telegram no permite botones aquí, se deben enviar con send_options

        # 🟢 **Manejo especial para Messenger e Instagram**
        elif platform in ['messenger', 'instagram']:
            from app.chatbot.integrations.messenger import send_messenger_message, send_instagram_message
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

def fetch_api_instance(model_class, business_unit):
    return model_class.objects.filter(
        business_unit=business_unit,
        is_active=True
    ).select_related('business_unit').first()

async def get_api_instance(platform: str, business_unit: BusinessUnit):
    """
    Obtiene la instancia de configuración de la API según la plataforma y unidad de negocio.
    Se cachea el resultado para evitar consultas repetidas.
    """
    cache_key = f"api_instance:{platform}:{business_unit.id}"
    api_instance = cache.get(cache_key)

    if api_instance:
        logger.debug(f"[get_api_instance] Instancia obtenida desde cache: {cache_key}")
    else:
        logger.info(f"[get_api_instance] Cache vacía para {cache_key}, consultando DB.")

        model_mapping = {
            'whatsapp': 'WhatsAppAPI',
            'telegram': 'TelegramAPI',
            'messenger': 'MessengerAPI',
            'instagram': 'InstagramAPI'
        }
        model_name = model_mapping.get(platform)
        if not model_name:
            logger.error(f"[get_api_instance] No se encontró mapping para plataforma: {platform}")
            return None

        model_class = getattr(__import__('app.models', fromlist=[model_name]), model_name)
        api_instance = await execute_sync(lambda: fetch_api_instance(model_class, business_unit))

        if not api_instance:
            logger.error(f"[get_api_instance] No se encontró instancia API para {platform}, BU {business_unit.name}")
            return None

        cache.set(cache_key, api_instance, timeout=CACHE_TIMEOUT)
        logger.info(f"[get_api_instance] Instancia almacenada en cache: {cache_key}")

    return api_instance

async def send_email(business_unit_name: str, subject: str, to_email: str, body: str, from_email: Optional[str] = None, domain_bu: str = "huntred.com"):
    """
    Envía un correo electrónico utilizando la configuración SMTP de la unidad de negocio.
    """
    server = None
    try:
        logger.info(f"[send_email] Iniciando envío de correo para BU: {business_unit_name}")
        config_bu = await sync_to_async(ConfiguracionBU.objects.select_related('business_unit').get)(
            business_unit__name=business_unit_name
        )
        smtp_host = config_bu.smtp_host or "mail.huntred.com"
        smtp_port = config_bu.smtp_port or 465
        smtp_username = config_bu.smtp_username or config_bu.correo_bu
        smtp_password = config_bu.smtp_password
        use_ssl = True
        from_email = from_email or smtp_username
        logger.info(f"[send_email] Configuración SMTP: {smtp_host}:{smtp_port}, Usuario: {smtp_username}")

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        logger.info("[send_email] Correo enviado exitosamente.")
        server.quit()
        return {"status": "success", "message": "Correo enviado correctamente."}

    except Exception as e:
        logger.error(f"[send_email] Error enviando correo: {e}", exc_info=True)
        if server:
            server.quit()
        return {"status": "error", "message": str(e)}

async def reset_chat_state(user_id: Optional[str] = None):
    """
    Resetea el estado del chatbot para un usuario específico o para todos los usuarios.
    """
    try:
        if user_id:
            chat_state = await sync_to_async(ChatState.objects.get)(user_id=user_id)
            await sync_to_async(chat_state.delete)()
            logger.info(f"[reset_chat_state] Estado de chat reseteado para {user_id}.")
        else:
            await sync_to_async(ChatState.objects.all().delete)()
            logger.info("[reset_chat_state] Estado de chat reseteado para todos los usuarios.")
    except ChatState.DoesNotExist:
        logger.warning(f"[reset_chat_state] No se encontró estado de chat para {user_id}.")
    except Exception as e:
        logger.error(f"[reset_chat_state] Error al resetear estado de chat: {e}", exc_info=True)

async def send_logo(platform, user_id, business_unit):
    """
    Envía el logo de la empresa al usuario.
    """
    try:
        configuracion = await sync_to_async(lambda: ConfiguracionBU.objects.filter(
            business_unit=business_unit
        ).select_related('business_unit').first())()
        image_url = configuracion.logo_url if configuracion else "https://huntred.com/logo.png"

        if platform in ['whatsapp', 'messenger']:
            await send_message(platform, user_id, 'Aquí tienes nuestro logo:', business_unit, options=[{'type': 'image', 'url': image_url}])
        else:
            logger.error(f"[send_logo] Envío de imagen no soportado para {platform}.")
    except Exception as e:
        logger.error(f"[send_logo] Error al enviar logo en {platform}: {e}", exc_info=True)

async def send_image(platform, user_id, message, image_url, business_unit):
    """
    Envía una imagen al usuario.
    """
    try:
        await send_message(platform, user_id, message, business_unit, options=[{'type': 'image', 'url': image_url}])
        logger.info(f"[send_image] Imagen enviada a {user_id} en {platform}.")
    except Exception as e:
        logger.error(f"[send_image] Error enviando imagen en {platform} a {user_id}: {e}", exc_info=True)

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
        logger.error(f"[render_dynamic_content] Error: Falta la variable {e}")
        return template_text

async def process_text_message(platform, sender_id, message_text, business_unit):
    """
    Procesa un mensaje de texto recibido.
    """
    from app.chatbot.chatbot import ChatBotHandler
    chatbot_handler = ChatBotHandler()
    try:
        await chatbot_handler.process_message(
            platform=platform,
            user_id=sender_id,
            text=message_text,
            business_unit=business_unit
        )
    except Exception as e:
        logger.error(f"[process_text_message] Error procesando mensaje: {e}", exc_info=True)

async def send_options(platform, user_id, message, buttons=None, business_unit: Optional[BusinessUnit] = None):
    """
    Envía opciones de respuesta al usuario.
    """
    try:
        if platform == 'whatsapp':
            from app.chatbot.integrations.whatsapp import send_whatsapp_decision_buttons
            # Asegúrate de construir cada botón con la clave 'reply' que incluya 'id' y 'title'
            formatted_buttons = []
            for button in buttons or []:
                formatted_buttons.append({
                    "type": "reply",
                    "reply": {
                        "id": button.get('payload', ''),
                        "title": button.get('title', '')
                    }
                })
            await send_whatsapp_decision_buttons(
                user_id=user_id,
                message=message,
                buttons=formatted_buttons,
                business_unit=business_unit
            )
        elif platform == 'telegram' and buttons:
            from app.chatbot.integrations.telegram import send_telegram_buttons  # ✅ Importamos la función correcta

            # ✅ Obtener la configuración de TelegramAPI
            api_instance = await sync_to_async(lambda: TelegramAPI.objects.filter(
                business_unit=business_unit, is_active=True
            ).first())()

            if not api_instance:
                logger.error(f"[send_options] No se encontró configuración activa de TelegramAPI para {business_unit.name}")
                return False, "No hay configuración de Telegram activa"

            # ✅ Convertir user_id en número si es necesario
            chat_id = int(user_id.split(":")[-1]) if ":" in user_id else int(user_id)

            # ✅ Validar botones antes de enviarlos
            telegram_buttons = [
                {"text": button.get('title', 'Opción'), "callback_data": button.get('payload', 'unknown_id')}
                for button in buttons if isinstance(button, dict) and button.get('payload') and button.get('title')
            ]

            if not telegram_buttons:
                logger.warning("[send_options] No hay botones válidos para enviar en Telegram")
                telegram_buttons = [{"text": "Continuar", "callback_data": "fallback_option"}]

            # ✅ Enviar mensaje con botones
            await send_telegram_buttons(
                chat_id=chat_id,
                message=message,
                buttons=telegram_buttons,
                access_token=api_instance.api_key  # ✅ Ahora api_instance está definido
            )
        elif platform == 'messenger' and buttons and business_unit:
            from app.chatbot.integrations.messenger import send_messenger_buttons
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
            from app.chatbot.integrations.instagram import send_instagram_buttons
            await send_instagram_buttons(
                user_id, message, buttons, business_unit.instagram_api.access_token
            )
        else:
            logger.error(f"[send_options] Plataforma desconocida o botones faltantes: {platform}")
    except Exception as e:
        logger.error(f"[send_options] Error enviando opciones a través de {platform}: {e}", exc_info=True)

async def notify_employer(worker, message):
    """
    Notifica al empleador que un evento ha ocurrido.
    """
    try:
        if worker.whatsapp:
            whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
                business_unit=worker.business_unit, is_active=True
            ).select_related('business_unit').first())()
            if whatsapp_api:
                from app.chatbot.integrations.whatsapp import send_whatsapp_message
                await send_whatsapp_message(
                    user_id=worker.whatsapp,
                    message=message,
                    phone_id=whatsapp_api.phoneID,
                    business_unit=whatsapp_api.business_unit
                )
                logger.info(f"[notify_employer] Notificación enviada al empleador {worker.name} vía WhatsApp.")
            else:
                logger.error("[notify_employer] No se encontró configuración de WhatsAppAPI.")
        else:
            logger.warning(f"[notify_employer] El empleador {worker.name} no tiene número de WhatsApp configurado.")
    except Exception as e:
        logger.error(f"[notify_employer] Error enviando notificación al empleador {worker.name}: {e}", exc_info=True)

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
            logger.info(f"[GamificationService] Otorgados {points} puntos a {user.nombre} por {activity_type}. Total: {profile.points}")
        except Exception as e:
            logger.error(f"[GamificationService] Error otorgando puntos a {user.nombre}: {e}", exc_info=True)

    async def notify_user_gamification_update(self, user: Person, activity_type: str):
        """
        Notifica al usuario sobre la actualización de puntos de gamificación.
        """
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            message = f"¡Has ganado puntos por {activity_type}! Ahora tienes {profile.points} puntos."
            platform = user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp'
            business_unit = user.chat_state.business_unit if hasattr(user, 'chat_state') else user.business_unit
            if platform and business_unit:
                await send_message(
                    platform=platform,
                    user_id=user.phone,
                    message=message,
                    business_unit=business_unit
                )
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            logger.warning(f"[GamificationService] No se encontró perfil de gamificación para {user.nombre}")
        except Exception as e:
            logger.error(f"[GamificationService] Error notificando gamificación a {user.nombre}: {e}", exc_info=True)

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
        if challenges:
            message = f"Tienes nuevos desafíos: {', '.join(challenges)}"
            await send_message(
                platform=user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp',
                user_id=user.phone,
                message=message,
                business_unit=user.chat_state.business_unit if hasattr(user, 'chat_state') else user.business_unit
            )
            
# Función helper para ejecutar consultas sincrónicas
async def execute_sync(query_lambda):
    return await sync_to_async(query_lambda)()
