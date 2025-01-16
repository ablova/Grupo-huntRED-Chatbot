# Ubicación: /home/pablollh/app/chatbot/integrations/whatsapp.py
import json
import logging
import time
from typing import Optional, List

import httpx
import asyncio
from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app.chatbot.chatbot import ChatBotHandler
from app.models import Person, ChatState, BusinessUnit, WhatsAppAPI

from app.chatbot.integrations.services import send_message

logger = logging.getLogger(__name__)

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'POST':
        try:
            logger.info(f"Solicitud entrante: {request.method}, Headers: {request.headers}")
            response = await handle_incoming_message(request)
            return response
        except Exception as e:
            logger.error(f"Error inesperado al manejar la solicitud POST: {e}", exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
    else:
        # Manejar la verificación del webhook (GET request)
        verify_token = "amigro_secret_token"  # Reemplaza con tu token de verificación
        challenge = request.GET.get('hub.challenge')
        token = request.GET.get('hub.verify_token')

        if token == verify_token:
            logger.info(f"Verificación exitosa del webhook. Retornando challenge: {challenge}")
            return JsonResponse({'hub.challenge': challenge}, status=200)
        else:
            logger.warning("Token de verificación inválido.")
            return JsonResponse({'error': 'Invalid verification token'}, status=403)

async def handle_incoming_message(request):
    try:
        payload = json.loads(request.body)
        logger.info(f"Payload recibido: {json.dumps(payload, indent=4)}")
        
        # Extraer información del payload
        entry = payload.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        contacts = value.get('contacts', [])
        
        if not messages or not contacts:
            logger.warning("No se encontraron mensajes o contactos en el payload.")
            return JsonResponse({'error': 'No messages found'}, status=400)
        
        message = messages[0]
        contact = contacts[0]
        
        user_id = contact.get('wa_id')
        text = message.get('text', {}).get('body', '').strip()
        phone_number_id = value.get('metadata', {}).get('phone_number_id')
        
        logger.info(f"Procesando mensaje de {user_id}: {text}")
        logger.debug(f"phone_number_id: {phone_number_id}")
        
        if not phone_number_id:
            logger.error("phone_number_id no está presente en el payload.")
            return JsonResponse({'error': 'Missing phone_number_id'}, status=400)
        
        # Obtener WhatsAppAPI basado en phone_number_id
        whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
            phoneID=phone_number_id,
            is_active=True
        ).select_related('business_unit').first())()
        
        if not whatsapp_api:
            logger.error(f"No se encontró WhatsAppAPI activo para phone_number_id: {phone_number_id}")
            return JsonResponse({'error': 'Invalid phone number ID'}, status=400)
        
        business_unit = whatsapp_api.business_unit
        logger.debug(f"business_unit: {business_unit.name if business_unit else 'None'}")
        
        # Instanciar el manejador del chatbot
        chatbot = ChatBotHandler()
        
        # Obtener o crear ChatState con user_id y business_unit
        chat_state, created = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=user_id,
            business_unit=business_unit,
            defaults={'platform': 'whatsapp'}
        )
        
        # Obtener o crear Persona usando sync_to_async
        person = await sync_to_async(Person.objects.filter(phone=user_id).first)()
        if not person:
            logger.info(f"No se encontró persona con phone {user_id}. Creando nueva persona.")
            person = await sync_to_async(Person.objects.create)(
                phone=user_id,
                nombre='Nuevo Usuario'
            )
        
        # Verificar y asociar persona al estado del chat
        if chat_state.person != person:
            logger.info(f"Actualizando persona asociada al estado del chat para {user_id}.")
            chat_state.person = person
            await sync_to_async(chat_state.save)()
    
        # Procesar el mensaje
        try:
            await chatbot.process_message('whatsapp', user_id, text, business_unit)
        except Exception as e:
            logger.error(f"Error procesando el mensaje en ChatBotHandler: {e}", exc_info=True)
            return JsonResponse({'error': 'Processing error'}, status=500)
        
        return JsonResponse({'status': 'success'}, status=200)
    
    except Exception as e:
        logger.error(f"Error procesando el mensaje: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)
# ------------------------------------------------------------------------------
# Funciones auxiliares y de construcción de URL
# ------------------------------------------------------------------------------
def build_whatsapp_url(whatsapp_api: WhatsAppAPI, endpoint: str = "messages") -> str:
    """
    Construye la URL base para la API de WhatsApp con la versión configurada.
    """
    api_version = whatsapp_api.v_api or "v21.0"
    return f"https://graph.facebook.com/{api_version}/{whatsapp_api.phoneID}/{endpoint}"

# ------------------------------------------------------------------------------
# Handlers de mensajes
# ------------------------------------------------------------------------------
async def handle_text_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    """Maneja mensajes de texto."""
    text = message['text']['body']
    logger.debug(f"Mensaje de texto recibido: {text}")
    await chatbot_handler.process_message(
        platform='whatsapp',
        user_id=sender_id,
        text=text,
        business_unit=business_unit,
    )

async def handle_media_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    """Maneja mensajes de medios (imágenes, audio, etc.)."""
    media_id = None
    media_type = message['type']
    if media_type == 'image':
        media_id = message.get('image', {}).get('id')
    elif media_type == 'audio':
        media_id = message.get('audio', {}).get('id')

    if media_id:
        await process_media_message('whatsapp', sender_id, media_id, media_type, business_unit)
    else:
        logger.warning(f"Mensaje de tipo {media_type} recibido sin 'id' de medio.")
        await send_message('whatsapp', sender_id, "No pude procesar el medio enviado.", business_unit)

async def handle_location_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    """Maneja mensajes de ubicación."""
    location = message.get('location')
    if location:
        latitude = location.get('latitude')
        longitude = location.get('longitude')
        if latitude and longitude:
            # Se procesa la ubicación
            await send_message('whatsapp', sender_id, f"Recibí tu ubicación: Latitud {latitude}, Longitud {longitude}", business_unit)
        else:
            logger.warning("Mensaje de ubicación recibido sin datos completos.")
            await send_message('whatsapp', sender_id, "No pude procesar tu ubicación.", business_unit)
    else:
        logger.warning("Mensaje de ubicación recibido sin datos.")
        await send_message('whatsapp', sender_id, "No pude encontrar la información de tu ubicación.", business_unit)

async def handle_interactive_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    """Maneja mensajes interactivos como botones y listas."""
    interactive = message.get('interactive', {})
    interactive_type = interactive.get('type')
    interactive_handlers = {
        'button_reply': handle_button_reply,
        'list_reply': handle_list_reply,
        # Agrega más tipos interactivos si es necesario
    }
    handler = interactive_handlers.get(interactive_type, handle_unknown_interactive)
    await handler(message, sender_id, chatbot_handler, business_unit, person, chat_state)

async def handle_button_reply(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    """Maneja respuestas de botones."""
    button_reply = message['interactive'].get('button_reply', {})
    payload = button_reply.get('payload') or button_reply.get('id')
    if payload:
        logger.info(f"Respuesta de botón recibida: {payload}")
        await chatbot_handler.process_message(
            platform='whatsapp',
            user_id=sender_id,
            text=payload,
            business_unit=business_unit
        )
    else:
        logger.warning("Respuesta de botón recibida sin payload.")
        await send_message('whatsapp', sender_id, "No pude entender tu selección. Por favor, intenta nuevamente.", business_unit)

async def handle_list_reply(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    """Maneja respuestas de listas."""
    list_reply = message['interactive'].get('list_reply', {})
    payload = list_reply.get('payload') or list_reply.get('id')
    if payload:
        logger.info(f"Respuesta de lista recibida: {payload}")
        await chatbot_handler.process_message(
            platform='whatsapp',
            user_id=sender_id,
            text=payload,
            business_unit=business_unit
        )
    else:
        logger.warning("Respuesta de lista recibida sin payload.")
        await send_message('whatsapp', sender_id, "No pude entender tu selección. Por favor, intenta nuevamente.", business_unit)

async def handle_unknown_interactive(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    """Maneja tipos de mensajes interactivos no soportados."""
    interactive_type = message.get('interactive', {}).get('type')
    logger.warning(f"Tipo interactivo no soportado: {interactive_type}")
    await send_message('whatsapp', sender_id, "No entendí tu selección. Por favor, intenta nuevamente.", business_unit)

async def handle_unknown_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    """Maneja tipos de mensajes desconocidos."""
    message_type = message.get('type', 'unknown')
    logger.warning(f"Tipo de mensaje no soportado: {message_type}")
    await send_message('whatsapp', sender_id, "Tipo de mensaje no soportado.", business_unit)

# ------------------------------------------------------------------------------
# Procesamiento de media
# ------------------------------------------------------------------------------
async def process_media_message(platform, sender_id, media_id, media_type, business_unit):
    """
    Procesa mensajes de medios (imágenes, audio, etc.) entrantes: 
    obtiene la URL, descarga el contenido y lo maneja según sea imagen o audio.
    """
    try:
        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(
            business_unit=business_unit,
            is_active=True
        ).first)()
        if not whatsapp_api:
            logger.error("No se encontró configuración de WhatsAppAPI.")
            return

        # Obtener la URL de descarga del medio
        media_url = await get_media_url(whatsapp_api, media_id)
        if not media_url:
            logger.error(f"No se pudo obtener la URL del medio {media_id}")
            return

        # Descargar el archivo
        media_data = await download_media(media_url, whatsapp_api.api_token)
        if not media_data:
            logger.error(f"No se pudo descargar el medio {media_url}")
            return

        # Procesar el archivo según el tipo
        if media_type == 'image':
            await handle_image_message(platform, sender_id, media_data, business_unit)
        elif media_type == 'audio':
            await handle_audio_message(platform, sender_id, media_data, business_unit)
        else:
            logger.warning(f"Tipo de medio no soportado: {media_type}")

    except Exception as e:
        logger.error(f"Error procesando mensaje de medios: {e}", exc_info=True)

async def get_media_url(whatsapp_api: WhatsAppAPI, media_id: str) -> Optional[str]:
    """
    Obtiene la URL de descarga para un medio específico (imagen/audio/etc.),
    usando la versión de API definida en whatsapp_api.
    """
    api_version = whatsapp_api.v_api or "v21.0"
    url = f"https://graph.facebook.com/{api_version}/{whatsapp_api.phoneID}/{media_id}"
    headers = {
        "Authorization": f"Bearer {whatsapp_api.api_token}"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get('url')
    except httpx.HTTPStatusError as e:
        logger.error(f"Error obteniendo la URL del medio: {e.response.text}", exc_info=True)
    except Exception as e:
        logger.error(f"Error general obteniendo la URL del medio: {e}", exc_info=True)

    return None

async def download_media(media_url: str, api_token: str) -> Optional[bytes]:
    """
    Descarga el contenido de un medio desde la URL proporcionada.
    """
    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(media_url, headers=headers)
            response.raise_for_status()
            return response.content
    except httpx.HTTPStatusError as e:
        logger.error(f"Error descargando el medio: {e.response.text}", exc_info=True)
    except Exception as e:
        logger.error(f"Error general descargando el medio: {e}", exc_info=True)

    return None

async def handle_image_message(platform, sender_id, image_data: bytes, business_unit):
    """
    Procesa una imagen recibida: se guarda en el sistema de archivos y se envía confirmación al usuario.
    """
    logger.info(f"Imagen recibida de {sender_id}. Procesando imagen...")

    image_path = f"/home/pablollh/app/static/images/{sender_id}_{int(time.time())}.jpg"
    try:
        async with await sync_to_async(open)(image_path, 'wb') as f:
            await sync_to_async(f.write)(image_data)
        logger.info(f"Imagen guardada en {image_path}")

        await send_message('whatsapp', sender_id, "Gracias por enviar la imagen. La hemos recibido correctamente.", business_unit)
    except Exception as e:
        logger.error(f"Error guardando la imagen: {e}", exc_info=True)
        await send_message('whatsapp', sender_id, "Hubo un problema al procesar la imagen. Por favor, intenta nuevamente.", business_unit)

async def handle_audio_message(platform, sender_id, audio_data: bytes, business_unit):
    """
    Procesa un archivo de audio recibido: se guarda y se notifica confirmación al usuario.
    """
    logger.info(f"Audio recibido de {sender_id}. Procesando audio...")

    audio_path = f"/home/pablollh/app/static/audio/{sender_id}_{int(time.time())}.ogg"
    try:
        async with await sync_to_async(open)(audio_path, 'wb') as f:
            await sync_to_async(f.write)(audio_data)
        logger.info(f"Audio guardado en {audio_path}")

        await send_message('whatsapp', sender_id, "Gracias por enviar el audio. Lo hemos recibido correctamente.", business_unit)
    except Exception as e:
        logger.error(f"Error guardando el audio: {e}", exc_info=True)
        await send_message('whatsapp', sender_id, "Hubo un problema al procesar el audio. Por favor, intenta nuevamente.", business_unit)

# ------------------------------------------------------------------------------
# Ejemplo de función para enviar mensajes (similar a la de services.py)
# ------------------------------------------------------------------------------
async def send_whatsapp_message(
    user_id: str,
    message: str,
    buttons: Optional[List[dict]] = None,
    phone_id: Optional[str] = None,
    business_unit=None
):
    """
    Envía un mensaje directo a un usuario de WhatsApp, permitiendo botones y phone_id si se requiere.
    """
    try:
        if not phone_id and business_unit:
            whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(
                business_unit=business_unit,
                is_active=True
            ).select_related('business_unit').first)()
            if not whatsapp_api:
                logger.error(f"[send_whatsapp_message] No se encontró WhatsAppAPI activo para {business_unit.name}")
                return
            phone_id = whatsapp_api.phoneID
            api_token = whatsapp_api.api_token
        else:
            if business_unit:
                whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(
                    phoneID=phone_id,
                    is_active=True
                ).select_related('business_unit').first)()
                api_token = whatsapp_api.api_token if whatsapp_api else None
            else:
                logger.warning("[send_whatsapp_message] No se pasó business_unit, asumiendo phone_id y token predefinidos.")
                api_token = phone_id

        if not phone_id or not api_token:
            logger.error("[send_whatsapp_message] No se cuenta con phone_id o api_token válido.")
            return

        logger.debug(f"[send_whatsapp_message] user_id={user_id}, phone_id={phone_id}, tiene botones={bool(buttons)}")

        # Construcción de la URL con la función unificada:
        url = build_whatsapp_url(whatsapp_api, "messages")

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        # Payload base
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "text",
            "text": {
                "body": message
            }
        }

        # Si se proveen buttons, se convierte a interactivo
        if buttons:
            logger.debug(f"[send_whatsapp_message] Convirtiendo a mensaje interactivo con {len(buttons)} botón(es).")
            formatted_buttons = []
            for btn in buttons:
                formatted_buttons.append({
                    "type": "reply",
                    "reply": {
                        "id": btn.get('payload', 'btn_id'),
                        "title": btn.get('title', '')[:20]
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

async def send_whatsapp_buttons(user_id, message, buttons, phone_id):
    """Envía botones interactivos a través de WhatsApp."""
    from app.integrations.whatsapp import send_whatsapp_decision_buttons

    try:
        await send_whatsapp_decision_buttons(user_id=user_id, message=message, buttons=buttons, business_unit=phone_id)
    except Exception as e:
        logger.error(f"Error enviando botones de WhatsApp: {e}", exc_info=True)

async def send_whatsapp_decision_buttons(user_id, message, buttons, business_unit):
    """
    Envía botones interactivos a través de WhatsApp usando la configuración asociada a la unidad de negocio.
    """
    from app.models import WhatsAppAPI

    try:
        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(
            business_unit=business_unit,
            is_active=True
        ).first)()
        if not whatsapp_api:
            raise ValueError(f"No se encontró configuración activa de WhatsAppAPI para la unidad de negocio: {business_unit.name}")

        url = build_whatsapp_url(whatsapp_api, "messages")
        headers = {
            "Authorization": f"Bearer {whatsapp_api.api_token}",
            "Content-Type": "application/json"
        }

        formatted_buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": button['payload'],
                    "title": button['title'][:20]
                }
            }
            for button in buttons
        ]

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
            logger.info(f"Botones enviados correctamente a WhatsApp. Respuesta: {response.text}")

    except ValueError as e:
        logger.error(f"Error en configuración: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Error al enviar botones a WhatsApp: {e.response.text}", exc_info=True)
    except Exception as e:
        logger.error(f"Error general al enviar botones a WhatsApp: {e}", exc_info=True)