# /home/pablo/app/chatbot/integrations/whatsapp.py
import re
import json
import logging
import asyncio
import httpx
import time
from typing import Optional, List, Dict
from asgiref.sync import sync_to_async
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt # type: ignore

from app.chatbot.chatbot import ChatBotHandler
from app.models import Person, ChatState, BusinessUnit, WhatsAppAPI, Template
from app.chatbot.integrations.services import send_message

logger = logging.getLogger(__name__)

# Semáforo para controlar la concurrencia en WhatsApp (se utiliza en el envío de mensajes)
whatsapp_semaphore = asyncio.Semaphore(10)
ENABLE_ADVANCED_PROCESSING = True  # Cambiar a True cuando se resuelvan los problemas
MAX_RETRIES = 3  # Número máximo de reintentos para envío
REQUEST_TIMEOUT = 10.0  # Tiempo de espera para las solicitudes HTTP

# ------------------------------------------------------------------------------
# Webhook Principal para WhatsApp
# ------------------------------------------------------------------------------
@csrf_exempt
async def whatsapp_webhook(request):
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode("utf-8"))
        # Eliminar logging aquí para evitar duplicados
        if "entry" not in payload:
            logger.error("[whatsapp_webhook] Error: 'entry' no encontrado en el payload.")
            return JsonResponse({"status": "error", "message": "Formato de payload inválido"}, status=400)

        await handle_incoming_message(request)
        return JsonResponse({"status": "success"}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "JSON inválido"}, status=400)
    except Exception as e:
        logger.error(f"[whatsapp_webhook] Error inesperado: {e}", exc_info=True)
        return JsonResponse({"status": "error", "message": "Error interno"}, status=500)
    
# ------------------------------------------------------------------------------
# Procesamiento del Mensaje Entrante
# ------------------------------------------------------------------------------
@csrf_exempt
async def handle_incoming_message(request):
    try:
        payload = json.loads(request.body)
        logger.info(f"[handle_incoming_message] Payload recibido de {payload.get('entry', [{}])[0].get('id', 'unknown')}: {json.dumps(payload, indent=2)}")#Antes 4 espero que me deje menos detalle pero menos consumo de logs

        entry = payload.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        contacts = value.get('contacts', [])
        statuses = value.get('statuses', [])

        # Si solo hay statuses, registrar y salir
        if statuses and not messages:
            for status in statuses:
                logger.info(f"Estado recibido: {status['status']} para mensaje {status['id']} al destinatario {status['recipient_id']}")
            return JsonResponse({'status': 'success', 'message': 'Estado procesado'}, status=200)

        # Si no hay mensajes ni contactos, devolver error solo si no hay statuses
        if not messages or not contacts:
            logger.warning("No se encontraron mensajes o contactos en el payload, y no hay statuses para procesar.")
            return JsonResponse({'error': 'No messages or contacts found'}, status=400)

        # Procesar mensaje entrante
        message = messages[0]
        contact = contacts[0]
        user_id = contact.get('wa_id')
        
        text = message.get('text', {}).get('body', '').strip()
        if message.get('type') == 'interactive':
            interactive_content = message.get('interactive', {})
            if interactive_content.get('type') == 'button_reply':
                text = interactive_content.get('button_reply', {}).get('id', '')
            elif interactive_content.get('type') == 'list_reply':
                text = interactive_content.get('list_reply', {}).get('id', '')

        phone_number_id = value.get('metadata', {}).get('phone_number_id')
        logger.info(f"Procesando mensaje de {user_id}: {text}")

        if not phone_number_id:
            logger.error("phone_number_id no está presente en el payload.")
            return JsonResponse({'error': 'Missing phone_number_id'}, status=400)

        whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
            phoneID=phone_number_id, is_active=True
        ).select_related('business_unit').first())()

        if not whatsapp_api:
            logger.error(f"No se encontró WhatsAppAPI activo para phone_number_id: {phone_number_id}")
            return JsonResponse({'error': 'Invalid phone number ID'}, status=400)

        business_unit = whatsapp_api.business_unit
        chatbot = ChatBotHandler()

        chat_state, _ = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=user_id, business_unit=business_unit, defaults={'platform': 'whatsapp'}
        )
        person, _ = await sync_to_async(Person.objects.get_or_create)(
            phone=user_id, defaults={'nombre': 'Nuevo Usuario'}
        )

        current_person = await sync_to_async(lambda: chat_state.person)()
        if current_person != person:
            chat_state.person = person
            await sync_to_async(chat_state.save)()

        message_type = message.get('type', 'text')
        handlers = {
            'text': handle_text_message, 'image': handle_media_message, 'audio': handle_media_message, 'location': handle_location_message, 'interactive': handle_interactive_message}
        handler = handlers.get(message_type, handle_unknown_message)
        await handler(message, user_id, chatbot, business_unit, person, chat_state)

        return JsonResponse({'status': 'success'}, status=200)
    except Exception as e:
        logger.error(f"Error procesando el mensaje para {user_id}: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

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
async def handle_text_message(message, sender_id, chatbot, business_unit, person, chat_state):
    """
    Procesa mensajes de texto simples.
    """
    from app.chatbot.chatbot import ChatBotHandler
    text = message['text']['body']
    logger.info(f"Texto recibido: {text} de {sender_id}")

    if ENABLE_ADVANCED_PROCESSING:
        logger.info("Procesamiento avanzado habilitado. Usando ChatBotHandler.")
        await chatbot.process_message(
            platform='whatsapp',
            user_id=sender_id,
            message=message,  # Pasa el diccionario completo
            business_unit=business_unit
        )
        logger.info(f"Procesamiento completado para {sender_id} con mensaje: {text}")
    else:
        logger.info("Procesamiento avanzado deshabilitado. Solo captura básica.")
        response = f"Recibí tu mensaje: {text} @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        await send_whatsapp_message(
            user_id=sender_id,
            message=response,
            phone_id=business_unit.whatsapp_api.phoneID,
            business_unit=business_unit
        )


# /home/pablo/app/chatbot/integrations/whatsapp.py

async def handle_interactive_message(message, sender_id, chatbot, business_unit, person, chat_state):
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
        selected_id = selection.get('id', 'Sin ID')
        selected_text = selection.get('title', 'Sin texto')
        logger.info(f"Botón seleccionado: {selected_text} (ID: {selected_id})")

        # Construir un mensaje en el formato esperado por ChatBotHandler
        message_for_chatbot = {
            "text": {
                "body": selected_id  # Usamos el ID del botón como el texto procesable
            }
        }

        # Enviar el mensaje estructurado al chatbot
        await chatbot.process_message(
            platform='whatsapp',
            user_id=sender_id,
            message=message_for_chatbot,  # Pasamos un diccionario en lugar de solo el string
            business_unit=business_unit
        )
    elif interactive_type == 'list_reply':
        selection = interactive.get('list_reply', {})
        selected_id = selection.get('id', 'Sin ID')
        selected_text = selection.get('title', 'Sin texto')
        logger.info(f"Lista seleccionada: {selected_text} (ID: {selected_id})")

        # Similar para listas, si aplica
        message_for_chatbot = {
            "text": {
                "body": selected_id
            }
        }
        await chatbot.process_message(
            platform='whatsapp',
            user_id=sender_id,
            message=message_for_chatbot,
            business_unit=business_unit
        )
    else:
        logger.warning(f"Tipo interactivo no soportado: {interactive_type}")
        await send_message('whatsapp', sender_id, "Interacción no soportada.", business_unit)
        return


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
from tenacity import retry, stop_after_attempt
@retry(stop=stop_after_attempt(3))
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
            logger.debug(f"Botones formateados: {formatted_buttons}")
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
                "header": {"type": "text", "text": "Menú Principal"},  # Campo obligatorio
                "body": {"text": message},
                "footer": {"text": "Selecciona una opción"},  # Campo recomendado
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

async def send_whatsapp_decision_buttons(user_id: str, message: str, buttons: List[Dict], business_unit: BusinessUnit) -> bool:
    from app.chatbot.integrations.services import MessageService
    service = MessageService(business_unit)
    api_instance = await service.get_api_instance("whatsapp")
    if not api_instance:
        return False
    """
    Envía botones interactivos a WhatsApp asegurando que los botones válidos no sean eliminados.
    """
    try:
        logger.debug(f"[send_whatsapp_decision_buttons] Procesando botones: {buttons}")

        # Filtrar botones válidos (solo tipo 'reply' con 'id' y 'title')
        valid_buttons = [
            btn for btn in buttons 
            if isinstance(btn, dict) and 'type' in btn and btn['type'] == 'reply' 
            and 'reply' in btn and 'id' in btn['reply'] and 'title' in btn['reply']
        ]

        if not valid_buttons:
            logger.error("❌ No se encontraron botones válidos. Verifica la estructura: {buttons}")
            return False, None

        whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
            business_unit=business_unit, is_active=True
        ).first())()

        if not whatsapp_api:
            logger.error(f"[send_whatsapp_decision_buttons] ❌ No se encontró WhatsAppAPI para {business_unit.name}")
            return False, None

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
                "type": "button",
                "body": {"text": message},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": btn["reply"]["id"], "title": btn["reply"]["title"]}}
                        for btn in valid_buttons
                    ]
                }
            }
        }

        logger.info(f"[send_whatsapp_decision_buttons] 📤 Enviando payload: {json.dumps(payload, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            msg_id = response.json().get("messages", [{}])[0].get("id", "")

        if msg_id:
            logger.info(f"✅ Botones enviados correctamente. Message ID: {msg_id}")
            return True, msg_id
        else:
            logger.error("❌ Respuesta de WhatsApp no contiene message ID.")
            return False, None
    except Exception as e:
        logger.error(f"❌ Error en send_whatsapp_decision_buttons: {e}", exc_info=True)
        return False, None