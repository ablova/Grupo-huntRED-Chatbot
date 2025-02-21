# /home/pablo/app/chatbot/integrations/whatsapp.py
import re
import json
import logging
import asyncio
import httpx
import time
from typing import Optional, List
from asgiref.sync import sync_to_async
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt # type: ignore

from app.chatbot.chatbot import ChatBotHandler
from app.models import Person, ChatState, BusinessUnit, WhatsAppAPI, Template
from app.chatbot.integrations.services import send_message

logger = logging.getLogger("app.chatbot.integrations.whatsapp")
# Semáforo para controlar la concurrencia en WhatsApp (se utiliza en el envío de mensajes)
whatsapp_semaphore = asyncio.Semaphore(10)
ENABLE_ADVANCED_PROCESSING = False  # Cambiar a True cuando se resuelvan los problemas
MAX_RETRIES = 3  # Número máximo de reintentos para envío
REQUEST_TIMEOUT = 10.0  # Tiempo de espera para las solicitudes HTTP

# ------------------------------------------------------------------------------
# Webhook Principal para WhatsApp
# ------------------------------------------------------------------------------


@csrf_exempt
async def whatsapp_webhook(request):
    """
    Webhook de WhatsApp para recibir mensajes entrantes.
    """
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode("utf-8"))
        logger.info(f"[whatsapp_webhook] Payload recibido: {json.dumps(payload, indent=2)}")

        if "entry" not in payload:
            logger.error("[whatsapp_webhook] Error: 'entry' no encontrado en el payload.")
            return JsonResponse({"status": "error", "message": "Formato de payload inválido"}, status=400)

        return JsonResponse({"status": "success"}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "JSON inválido"}, status=400)

    

# ------------------------------------------------------------------------------
# Procesamiento del Mensaje Entrante
# ------------------------------------------------------------------------------

@csrf_exempt
async def handle_incoming_message(request):
    """
    Procesa mensajes entrantes complejos de WhatsApp.
    Extrae la información necesaria, obtiene la configuración y estado del usuario,
    y delega el procesamiento al handler correspondiente según el tipo de mensaje.
    """
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

        # Obtener configuración de WhatsAppAPI y la Business Unit
        whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
            phoneID=phone_number_id, is_active=True
        ).select_related('business_unit').first())()

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

        # Determinar el tipo de mensaje y llamar al handler correspondiente
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
    """
    Construye la URL de WhatsApp basada en la versión de API y el phoneID.
    """
    api_version = whatsapp_api.v_api or "v21.0"
    return f"https://graph.facebook.com/{api_version}/{whatsapp_api.phoneID}/{endpoint}"

# ------------------------------------------------------------------------------
# Handlers de Tipos de Mensajes
# ------------------------------------------------------------------------------
async def handle_text_message(message, sender_id, business_unit):
    """
    Procesa mensajes de texto simples.
    """
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
    """
    Procesa mensajes interactivos (botones o listas) y extrae la selección.
    """
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
        response = f"Procesaste la opción: {selected_text}"

    await send_message('whatsapp', sender_id, response, business_unit)

async def handle_media_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    """
    Procesa mensajes de medios (imagen, audio, etc.).
    """
    media_id = message.get(message['type'], {}).get('id')
    if not media_id:
        logger.warning("Mensaje de medio recibido sin 'id'.")
        await send_message('whatsapp', sender_id, "No pude procesar el medio enviado.", business_unit)
        return

    whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
        business_unit=business_unit, is_active=True
    ).first())()
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
    """
    Procesa mensajes de ubicación y responde con la confirmación de las coordenadas.
    """
    location = message.get('location', {})
    latitude = location.get('latitude')
    longitude = location.get('longitude')
    if latitude and longitude:
        await send_message('whatsapp', sender_id,
                           f"Recibí tu ubicación: Latitud {latitude}, Longitud {longitude}", business_unit)
    else:
        logger.warning("Mensaje de ubicación recibido sin coordenadas completas.")
        await send_message('whatsapp', sender_id, "No pude procesar tu ubicación.", business_unit)

async def handle_unknown_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    """
    Maneja mensajes de tipos no soportados.
    """
    logger.warning(f"Tipo de mensaje no soportado: {message.get('type')}")
    await send_message('whatsapp', sender_id, "Tipo de mensaje no soportado. Por favor, envía texto.", business_unit)

# ------------------------------------------------------------------------------
# Función para obtener la URL del medio
# ------------------------------------------------------------------------------
async def get_media_url(whatsapp_api: WhatsAppAPI, media_id: str) -> Optional[str]:
    """
    Obtiene la URL del medio usando la API de WhatsApp.
    """
    try:
        url = f"https://graph.facebook.com/{whatsapp_api.v_api}/{media_id}"
        headers = {"Authorization": f"Bearer {whatsapp_api.api_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("url")
    except Exception as e:
        logger.error(f"Error obteniendo la URL del medio: {e}", exc_info=True)
        return None

# ------------------------------------------------------------------------------
# Envío de Mensajes a WhatsApp
# ------------------------------------------------------------------------------
async def send_whatsapp_message(
    user_id: str, 
    message: str, 
    buttons: Optional[List[dict]] = None, 
    phone_id: Optional[str] = None, 
    business_unit: Optional[BusinessUnit] = None
):
    try:
        whatsapp_api = None
        if business_unit:
            whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
                business_unit=business_unit, is_active=True
            ).select_related('business_unit').first())()

        if whatsapp_api:
            phone_id = whatsapp_api.phoneID
            api_token = whatsapp_api.api_token
        else:
            api_token = None

        if not phone_id or not api_token:
            logger.error("[send_whatsapp_message] ❌ Falta phone_id o api_token válido.")
            return False

        url = f"https://graph.facebook.com/v22.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "text",
            "text": {"body": message}
        }

        if buttons:
            formatted_buttons = [
                {
                    "type": "reply",
                    "reply": {
                        "id": btn.get('payload', 'btn_id'),
                        "title": btn.get('title', '')[:20]
                    }
                }
                for btn in buttons
            ]
            payload["type"] = "interactive"
            payload["interactive"] = {
                "type": "button",
                "body": {"text": message},
                "action": {"buttons": formatted_buttons}
            }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        logger.info(f"[send_whatsapp_message] ✅ Mensaje enviado a {user_id}.")
        return True

    except Exception as e:
        logger.error(f"[send_whatsapp_message] ❌ Error inesperado: {e}", exc_info=True)
        return False
  
async def send_whatsapp_image(user_id, message, image_url, phone_id, business_unit):
    """Envía una imagen vía WhatsApp API."""
    logger.info(f"📷 Enviando imagen a {user_id} en WhatsApp.")
    url = f"https://graph.facebook.com/v22.0/{phone_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": user_id,
        "type": "image",
        "image": {
            "link": image_url
        }
    }

    headers = {
        "Authorization": f"Bearer {business_unit.whatsapp_api.api_key}",  # Corregido
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()

    logger.info(f"✅ Imagen enviada a {user_id} en WhatsApp.")
 
async def send_whatsapp_list(user_id, message, sections, business_unit_name):
    """
    Envía una lista interactiva a WhatsApp.
    """
    try:
        whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
            business_unit__name=business_unit_name, is_active=True
        ).first())()

        if not whatsapp_api:
            logger.error(f"[send_whatsapp_list] ❌ No se encontró WhatsAppAPI activo para {business_unit_name}")
            return False

        url = f"https://graph.facebook.com/{whatsapp_api.v_api}/{whatsapp_api.phoneID}/messages"
        headers = {
            "Authorization": f"Bearer {whatsapp_api.api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": message},
                "action": {
                    "button": "Seleccionar",
                    "sections": sections
                }
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        logger.info(f"✅ Lista interactiva enviada a {user_id} en WhatsApp.")
        return True

    except Exception as e:
        logger.error(f"[send_whatsapp_list] ❌ Error enviando lista interactiva: {e}", exc_info=True)
        return False
    import json

async def send_whatsapp_decision_buttons(user_id, message, buttons, business_unit):
    """
    Envía botones interactivos a WhatsApp asegurando que los botones válidos no sean eliminados.
    """
    try:
        logger.debug(f"[send_whatsapp_decision_buttons] Procesando botones: {buttons}")

        # 🔹 Filtrar solo botones de tipo 'payload' (evitando eliminar botones válidos)
        valid_buttons = [btn for btn in buttons if "payload" in btn]

        if not valid_buttons:
            logger.warning("⚠️ No hay botones válidos tras filtrar. Verifica la estructura de los botones.")
            return False, None  # No enviamos nada si no hay botones

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": message},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": btn["payload"], "title": btn["title"]}}
                        for btn in valid_buttons
                    ]
                }
            }
        }

        logger.info(f"[send_whatsapp_decision_buttons] 📤 Enviando payload: {payload}")
        
        response = await send_whatsapp_request(payload, business_unit)  # Ajusta esta función según tu código
        msg_id = response.get("messages", [{}])[0].get("id", "")

        if msg_id:
            logger.info(f"✅ Botones enviados correctamente. Message ID: {msg_id}")
            return True, msg_id
        else:
            logger.error("❌ Error enviando botones interactivos a WhatsApp.")
            return False, None
    except Exception as e:
        logger.error(f"❌ Error en send_whatsapp_decision_buttons: {e}", exc_info=True)
        return False, None