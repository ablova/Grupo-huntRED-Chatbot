"""
Ubicación en servidor: /home/pablollh/app/chatbot/integrations/whatsapp.py
Nombre del archivo: whatsapp.py
"""

import json
import logging
import httpx
from typing import Optional, List
from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

from app.chatbot.chatbot import ChatBotHandler
from app.models import Person, ChatState, BusinessUnit, WhatsAppAPI, Template
from app.chatbot.integrations.services import send_message

logger = logging.getLogger(__name__)

ENABLE_ADVANCED_PROCESSING = False  # Cambiar a True cuando se resuelvan los problemas

# ------------------------------------------------------------------------------
# Webhook Principal para WhatsApp
# ------------------------------------------------------------------------------
@csrf_exempt
async def whatsapp_webhook(request):
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode('utf-8'))
        logger.info(f"Payload recibido: {json.dumps(payload, indent=2)}")

        # Validar y procesar el payload
        entry = payload.get("entry", [])
        if not entry:
            return JsonResponse({"status": "error", "message": "Payload inválido: falta 'entry'"}, status=400)

        changes = entry[0].get("changes", [])
        for change in changes:
            messages = change.get("value", {}).get("messages", [])
            for message in messages:
                body = message.get("text", {}).get("body", "")
                if body:
                    logger.info(f"Mensaje recibido: {body}")
                    return JsonResponse({"status": "success", "message": f"Procesado: {body}"})

        return JsonResponse({"status": "error", "message": "No se encontraron mensajes"}, status=400)

    except Exception as e:
        logger.error(f"Error en el webhook: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# ------------------------------------------------------------------------------
# Procesamiento del Mensaje Entrante
# ------------------------------------------------------------------------------
async def handle_incoming_message(request):
    try:
        payload = json.loads(request.body)
        logger.info(f"Payload recibido: {json.dumps(payload, indent=4)}")

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

        if not phone_number_id:
            logger.error("phone_number_id no está presente en el payload.")
            return JsonResponse({'error': 'Missing phone_number_id'}, status=400)

        # Obtener configuración de WhatsAppAPI y unidad de negocio
        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(
            phoneID=phone_number_id, is_active=True
        ).select_related('business_unit').first)()

        if not whatsapp_api:
            logger.error(f"No se encontró WhatsAppAPI activo para phone_number_id: {phone_number_id}")
            return JsonResponse({'error': 'Invalid phone number ID'}, status=400)

        business_unit = whatsapp_api.business_unit
        chatbot = ChatBotHandler()

        # Estado del chat y perfil del usuario
        chat_state, _ = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=user_id,
            business_unit=business_unit,
            defaults={'platform': 'whatsapp'}
        )
        person, _ = await sync_to_async(Person.objects.get_or_create)(
            phone=user_id,
            defaults={'nombre': 'Nuevo Usuario'}
        )

        if chat_state.person != person:
            chat_state.person = person
            await sync_to_async(chat_state.save)()

        # Procesar el mensaje
        message_type = message.get('type', 'text')
        handlers = {
            'text': handle_text_message,
            'image': handle_media_message,
            'audio': handle_media_message,
            'location': handle_location_message,
            'interactive': handle_interactive_message
        }
        handler = handlers.get(message_type, handle_unknown_message)
        await handler(message, user_id, chatbot, business_unit, person, chat_state)

        return JsonResponse({'status': 'success'}, status=200)

    except Exception as e:
        logger.error(f"Error procesando el mensaje: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

# ------------------------------------------------------------------------------
# Utilidades para Construcción de Mensajes
# ------------------------------------------------------------------------------
def build_whatsapp_url(whatsapp_api: WhatsAppAPI, endpoint: str = "messages") -> str:
    api_version = whatsapp_api.v_api or "v21.0"
    return f"https://graph.facebook.com/{api_version}/{whatsapp_api.phoneID}/{endpoint}"

# ------------------------------------------------------------------------------
# Handlers de Tipos de Mensajes
# ------------------------------------------------------------------------------
async def handle_text_message(message, sender_id, business_unit):
    text = message['text']['body']
    logger.info(f"Texto recibido: {text} de {sender_id}")

    if ENABLE_ADVANCED_PROCESSING:
        logger.info("Procesamiento avanzado habilitado. Usando ChatBotHandler.")
        chatbot_handler = ChatBotHandler()
        response = await chatbot_handler.process_message(
            platform='whatsapp',
            user_id=sender_id,
            text=text,
            business_unit=business_unit
        )
    else:
        logger.info("Procesamiento avanzado deshabilitado. Solo captura básica.")
        response = f"Recibí tu mensaje: {text} @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    await send_whatsapp_message(user_id=sender_id, message=response, phone_id=business_unit.whatsapp_api.phoneID)

async def handle_interactive_message(message, sender_id, business_unit):
    interactive = message.get('interactive', {})
    interactive_type = interactive.get('type')
    logger.info(f"Procesando mensaje interactivo de tipo: {interactive_type}")

    if interactive_type == 'button_reply':
        selection = interactive.get('button_reply', {})
        selected_text = selection.get('title', 'Sin texto')
        logger.info(f"Botón seleccionado: {selected_text}")
    elif interactive_type == 'list_reply':
        selection = interactive.get('list_reply', {})
        selected_text = selection.get('title', 'Sin texto')
        logger.info(f"Lista seleccionada: {selected_text}")
    else:
        logger.warning(f"Tipo interactivo no soportado: {interactive_type}")
        await send_message('whatsapp', sender_id, "No puedo procesar este tipo de interacción.", business_unit)
        return

    if ENABLE_ADVANCED_PROCESSING:
        logger.info("Procesamiento avanzado habilitado para mensajes interactivos.")
        chatbot_handler = ChatBotHandler()
        response = await chatbot_handler.process_message(
            platform='whatsapp',
            user_id=sender_id,
            text=selected_text,
            business_unit=business_unit
        )
    else:
        logger.info("Procesamiento avanzado deshabilitado. Solo captura básica.")
        response = f"Seleccionaste: {selected_text}"

    await send_message('whatsapp', sender_id, response, business_unit)

async def handle_media_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    media_id = message.get(message['type'], {}).get('id')
    if not media_id:
        logger.warning("Mensaje de medio recibido sin 'id'.")
        await send_message('whatsapp', sender_id, "No pude procesar el medio enviado.", business_unit)
        return

    whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(
        business_unit=business_unit, is_active=True
    ).first)()
    if not whatsapp_api:
        logger.error("No se encontró configuración de WhatsAppAPI activa.")
        return

    media_url = await get_media_url(whatsapp_api, media_id)
    if not media_url:
        await send_message('whatsapp', sender_id, "No pude descargar el medio enviado.", business_unit)
        return

    logger.info(f"Media URL: {media_url}")
    await send_message('whatsapp', sender_id, "Medio recibido correctamente.", business_unit)

async def handle_location_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    location = message.get('location', {})
    latitude = location.get('latitude')
    longitude = location.get('longitude')
    if latitude and longitude:
        await send_message('whatsapp', sender_id, f"Recibí tu ubicación: Latitud {latitude}, Longitud {longitude}", business_unit)
    else:
        logger.warning("Mensaje de ubicación recibido sin coordenadas completas.")
        await send_message('whatsapp', sender_id, "No pude procesar tu ubicación.", business_unit)

async def handle_unknown_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    logger.warning(f"Tipo de mensaje no soportado: {message.get('type')}")
    await send_message('whatsapp', sender_id, "Tipo de mensaje no soportado. Por favor, envía texto.", business_unit)

# ------------------------------------------------------------------------------
# Envío de Mensajes
# ------------------------------------------------------------------------------
"""
Ubicación en servidor: /home/pablollh/app/chatbot/integrations/whatsapp.py
Nombre del archivo: whatsapp.py
"""

import json
import logging
import httpx
from typing import Optional, List
from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

from app.chatbot.chatbot import ChatBotHandler
from app.models import Person, ChatState, BusinessUnit, WhatsAppAPI
from app.chatbot.integrations.services import send_message

logger = logging.getLogger(__name__)

ENABLE_ADVANCED_PROCESSING = False  # Cambiar a True cuando se resuelvan los problemas

# ------------------------------------------------------------------------------
# Webhook Principal para WhatsApp
# ------------------------------------------------------------------------------
@csrf_exempt
async def whatsapp_webhook(request):
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode('utf-8'))
        logger.info(f"Payload recibido: {json.dumps(payload, indent=2)}")

        # Validar y procesar el payload
        entry = payload.get("entry", [])
        if not entry:
            return JsonResponse({"status": "error", "message": "Payload inválido: falta 'entry'"}, status=400)

        changes = entry[0].get("changes", [])
        for change in changes:
            messages = change.get("value", {}).get("messages", [])
            for message in messages:
                body = message.get("text", {}).get("body", "")
                if body:
                    logger.info(f"Mensaje recibido: {body}")
                    return JsonResponse({"status": "success", "message": f"Procesado: {body}"})

        return JsonResponse({"status": "error", "message": "No se encontraron mensajes"}, status=400)

    except Exception as e:
        logger.error(f"Error en el webhook: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# ------------------------------------------------------------------------------
# Handlers de Tipos de Mensajes
# ------------------------------------------------------------------------------
async def handle_text_message(message, sender_id, business_unit):
    text = message['text']['body']
    logger.info(f"Texto recibido: {text} de {sender_id}")

    if ENABLE_ADVANCED_PROCESSING:
        logger.info("Procesamiento avanzado habilitado. Usando ChatBotHandler.")
        chatbot_handler = ChatBotHandler()
        response = await chatbot_handler.process_message(
            platform='whatsapp',
            user_id=sender_id,
            text=text,
            business_unit=business_unit
        )
    else:
        logger.info("Procesamiento avanzado deshabilitado. Solo captura básica.")
        response = f"Recibí tu mensaje: {text} @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    await send_whatsapp_message(user_id=sender_id, message=response, phone_id=business_unit.whatsapp_api.phoneID)

async def handle_interactive_message(message, sender_id, business_unit):
    interactive = message.get('interactive', {})
    interactive_type = interactive.get('type')

    logger.info(f"Mensaje interactivo recibido: {json.dumps(interactive, indent=2)}")
    
    if not interactive_type:
        logger.warning("El campo 'type' está ausente en el mensaje interactivo.")
        await send_message('whatsapp', sender_id, "Error procesando tu selección.", business_unit)
        return

    if interactive_type == 'button_reply':
        selection = interactive.get('button_reply', {})
        selected_text = selection.get('title', 'Sin texto')
        logger.info(f"Botón seleccionado: {selected_text}")
    elif interactive_type == 'list_reply':
        selection = interactive.get('list_reply', {})
        selected_text = selection.get('title', 'Sin texto')
        logger.info(f"Lista seleccionada: {selected_text}")
    else:
        logger.warning(f"Tipo interactivo no soportado: {interactive_type}")
        await send_message('whatsapp', sender_id, "Interacción no soportada.", business_unit)
        return

    response = f"Procesaste la opción: {selected_text}"
    await send_message('whatsapp', sender_id, response, business_unit)


# ------------------------------------------------------------------------------
# Envío de Mensajes
# ------------------------------------------------------------------------------
async def send_whatsapp_message(user_id: str, message: str, buttons: Optional[List[dict]] = None, phone_id: Optional[str] = None):
    try:
        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(phoneID=phone_id, is_active=True).first)()
        if not whatsapp_api:
            logger.error("No se encontró configuración de WhatsAppAPI activa.")
            return

        url = f"https://graph.facebook.com/{whatsapp_api.v_api}/{whatsapp_api.phoneID}/messages"
        headers = {
            "Authorization": f"Bearer {whatsapp_api.api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": user_id,
            "type": "text",
            "text": {"body": message}
        }

        if buttons:
            payload["type"] = "interactive"
            payload["interactive"] = {
                "type": "button",
                "body": {"text": message},
                "action": {"buttons": buttons}
            }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Mensaje enviado a {user_id}: {response.json()}")

    except Exception as e:
        logger.error(f"Error enviando mensaje a {user_id}: {e}", exc_info=True)
