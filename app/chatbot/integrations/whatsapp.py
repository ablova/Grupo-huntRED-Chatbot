# /home/pablo/app/chatbot/integrations/whatsapp.py
#
# Módulo para manejar la integración con WhatsApp Business API.
# Procesa mensajes entrantes, envía respuestas, y gestiona interacciones como botones y listas.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.
import re
import json
import logging
import asyncio
import httpx
import time
from typing import Optional, Tuple, Dict, Any, List
from asgiref.sync import sync_to_async
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from tenacity import retry, stop_after_attempt, wait_exponential
from app.chatbot.chatbot import ChatBotHandler
from app.models import Person, ChatState, BusinessUnit, WhatsAppAPI, Template
from app.chatbot.integrations.services import send_message, RateLimiter  # Importamos RateLimit

# Configuración del logger para trazabilidad y depuración
logger = logging.getLogger('chatbot')

# Constantes globales
whatsapp_semaphore = asyncio.Semaphore(10)  # Limita la concurrencia para envíos
ENABLE_ADVANCED_PROCESSING = True  # Habilita el procesamiento avanzado con ChatBotHandler
MAX_RETRIES = 3  # Máximo de reintentos para solicitudes HTTP
REQUEST_TIMEOUT = 10.0  # Tiempo de espera para solicitudes HTTP (segundos)
# Instancia del RateLimiter (limita a 5 mensajes por segundo por usuario)
rate_limiter = RateLimit(rate=5, per=1)  # Ajusta rate y per según necesidades
# ------------------------------------------------------------------------------
# Webhook Principal para WhatsApp
# ------------------------------------------------------------------------------
@csrf_exempt
async def whatsapp_webhook(request):
    """
    Punto de entrada para el webhook de WhatsApp.
    Procesa solicitudes POST con payloads de mensajes entrantes.

    Args:
        request: Solicitud HTTP con el payload de WhatsApp.

    Returns:
        JsonResponse: Estado de la operación (éxito o error).
    """
    try:
        if request.method != "POST":
            logger.warning(f"Método no permitido: {request.method}")
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode("utf-8"))
        if "entry" not in payload:
            logger.error("[whatsapp_webhook] Error: 'entry' no encontrado en el payload")
            return JsonResponse({"status": "error", "message": "Formato de payload inválido"}, status=400)

        entry = payload.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        if not messages:
            logger.info("No hay mensajes para procesar, revisando statuses")
            statuses = value.get('statuses', [])
            for status in statuses:
                logger.info(f"Estado recibido: {status['status']} para mensaje {status['id']}")
            return JsonResponse({"status": "success", "message": "Estado procesado"}, status=200)

        message = messages[0]
        user_id = message.get('from')

        # Aplicar RateLimiter por user_id
        async with rate_limiter.acquire(user_id=user_id):
            await handle_incoming_message(payload)
            return JsonResponse({"status": "success"}, status=200)

    except json.JSONDecodeError:
        logger.error("[whatsapp_webhook] Error: JSON mal formado recibido")
        return JsonResponse({"status": "error", "message": "JSON inválido"}, status=400)
    except asyncio.TimeoutError:
        logger.error(f"❌ Rate limit excedido para user_id: {user_id}")
        return JsonResponse({"status": "error", "message": "Demasiadas solicitudes, intenta de nuevo más tarde"}, status=429)
    except Exception as e:
        logger.error(f"[whatsapp_webhook] Error inesperado: {e}", exc_info=True)
        return JsonResponse({"status": "error", "message": "Error interno"}, status=500)

# ------------------------------------------------------------------------------
# Procesamiento del Mensaje Entrante
# ------------------------------------------------------------------------------
async def handle_incoming_message(payload: Dict[str, Any]):
    """
    Procesa mensajes entrantes de WhatsApp, incluyendo texto, interactivos, medios, y ubicaciones.
    Extrae datos del usuario del payload y los usa para crear/actualizar registros de Person.
    Pasa el payload a process_message para soportar fetch_whatsapp_user_data.

    Args:
        payload: Diccionario con el payload del webhook de WhatsApp.

    Returns:
        JsonResponse: Estado de la operación (éxito o error).
    """
    try:
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

        # Si no hay mensajes ni contactos, devolver error
        if not messages or not contacts:
            logger.warning("No se encontraron mensajes o contactos en el payload")
            return JsonResponse({'error': 'No messages or contacts found'}, status=400)

        # Extraer datos del mensaje y contacto
        message = messages[0]
        contact = contacts[0]
        user_id = contact.get('wa_id')
        
        # Determinar el texto del mensaje (texto directo o selección interactiva)
        text = message.get('text', {}).get('body', '').strip()
        if message.get('type') == 'interactive':
            interactive_content = message.get('interactive', {})
            if interactive_content.get('type') == 'button_reply':
                text = interactive_content.get('button_reply', {}).get('id', '')
            elif interactive_content.get('type') == 'list_reply':
                text = interactive_content.get('list_reply', {}).get('id', '')

        phone_number_id = value.get('metadata', {}).get('phone_number_id')
        logger.info(f"Procesando mensaje de {user_id}: {text}")

        # Validar phone_number_id
        if not phone_number_id:
            logger.error("phone_number_id no está presente en el payload")
            return JsonResponse({'error': 'Missing phone_number_id'}, status=400)

        # Obtener configuración de WhatsAppAPI
        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(phoneID=phone_number_id, is_active=True).first)()
        if not whatsapp_api:
            logger.error(f"No se encontró WhatsAppAPI activo para phone_number_id: {phone_number_id}")
            return JsonResponse({'error': 'Invalid phone number ID'}, status=400)

        business_unit = await sync_to_async(lambda: whatsapp_api.business_unit)()
        chatbot = ChatBotHandler()

        # Extraer datos del usuario desde el payload
        user_data = {
            'nombre': '',
            'apellido_paterno': '',
            'metadata': {},
            'preferred_language': 'es_MX'
        }
        if contacts:
            profile_name = contacts[0].get('profile', {}).get('name', '')
            if profile_name:
                user_data['nombre'] = profile_name.split(" ")[0] if profile_name else ""
                user_data['apellido_paterno'] = " ".join(profile_name.split(" ")[1:]) if len(profile_name.split(" ")) > 1 else ""

        # Crear o obtener chat_state
        chat_state, _ = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=user_id,
            business_unit=business_unit,
            defaults={'platform': 'whatsapp'}
        )
        logger.info(f"[handle_incoming_message] chat_state creado/obtenido: tipo={type(chat_state)}, valor={chat_state}")

        # Crear o obtener persona usando datos del payload
        person, created = await sync_to_async(Person.objects.get_or_create)(
            phone=user_id,
            defaults={
                'nombre': user_data['nombre'] or 'Nuevo Usuario',
                'apellido_paterno': user_data['apellido_paterno']
            }
        )
        if not created and user_data['nombre']:
            person.nombre = user_data['nombre']
            person.apellido_paterno = user_data['apellido_paterno']
            await sync_to_async(person.save)()

        logger.info(f"[handle_incoming_message] Antes de process_message: chat_state={type(chat_state)}, business_unit={type(business_unit)}")

        # Vincular person a chat_state si es necesario
        current_person = await sync_to_async(lambda: chat_state.person)()
        if current_person != person:
            chat_state.person = person
            await sync_to_async(chat_state.save)()

        # Determinar el tipo de mensaje y seleccionar el handler
        message_type = message.get('type', 'text')
        handlers = {
            'text': handle_text_message,
            'image': handle_media_message,
            'audio': handle_media_message,
            'location': handle_location_message,
            'interactive': handle_interactive_message
        }
        handler = handlers.get(message_type, handle_unknown_message)
        await handler(message, user_id, chatbot, business_unit, person, chat_state, payload)

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

    Args:
        whatsapp_api: Instancia de WhatsAppAPI con phoneID y v_api.
        endpoint: Endpoint de la API (por defecto, "messages").

    Returns:
        str: URL completa para la solicitud.
    """
    api_version = whatsapp_api.v_api or "v22.0"
    return f"https://graph.facebook.com/{api_version}/{whatsapp_api.phoneID}/{endpoint}"

# ------------------------------------------------------------------------------
# Handlers de Tipos de Mensajes
# ------------------------------------------------------------------------------
async def handle_text_message(message, sender_id, chatbot, business_unit, person, chat_state, payload):
    """
    Procesa mensajes de texto simples y los envía a ChatBotHandler.

    Args:
        message: Diccionario con el mensaje recibido.
        sender_id: ID del usuario (wa_id).
        chatbot: Instancia de ChatBotHandler.
        business_unit: Instancia de BusinessUnit.
        person: Instancia de Person.
        chat_state: Instancia de ChatState.
        payload: Payload completo del webhook.
    """
    text = message['text']['body']
    logger.info(f"Texto recibido: {text} de {sender_id}")

    message_dict = {
        "messages": [{"id": message.get('id', ''), "text": {"body": text}}],
        "chat": {"id": sender_id}
    }
    await chatbot.process_message(
        platform='whatsapp',
        user_id=sender_id,
        message=message_dict,
        business_unit=business_unit,
        payload=payload
    )

async def handle_interactive_message(message, sender_id, chatbot, business_unit, person, chat_state, payload):
    """
    Procesa mensajes interactivos (botones o listas) y extrae la selección.

    Args:
        message: Diccionario con el mensaje recibido.
        sender_id: ID del usuario (wa_id).
        chatbot: Instancia de ChatBotHandler.
        business_unit: Instancia de BusinessUnit.
        person: Instancia de Person.
        chat_state: Instancia de ChatState.
        payload: Payload completo del webhook.
    """
    interactive = message.get('interactive', {})
    interactive_type = interactive.get('type')
    logger.info(f"Mensaje interactivo recibido: {json.dumps(interactive, indent=2)}")
    
    if not interactive_type:
        logger.warning("El campo 'type' está ausente en el mensaje interactivo")
        await send_message('whatsapp', sender_id, "Error procesando tu selección.", business_unit.name.lower())
        return

    if interactive_type == 'button_reply':
        selection = interactive.get('button_reply', {})
        selected_id = selection.get('id', 'Sin ID')
        logger.info(f"Botón seleccionado: {selection.get('title', 'Sin texto')} (ID: {selected_id})")

        message_dict = {
            "messages": [{"id": message.get('id', ''), "text": {"body": selected_id}}],
            "chat": {"id": sender_id}
        }
        await chatbot.process_message(
            platform='whatsapp',
            user_id=sender_id,
            message=message_dict,
            business_unit=business_unit,
            payload=payload
        )
    elif interactive_type == 'list_reply':
        selection = interactive.get('list_reply', {})
        selected_id = selection.get('id', 'Sin ID')
        logger.info(f"Lista seleccionada: {selection.get('title', 'Sin texto')} (ID: {selected_id})")

        message_dict = {
            "messages": [{"id": message.get('id', ''), "text": {"body": selected_id}}],
            "chat": {"id": sender_id}
        }
        await chatbot.process_message(
            platform='whatsapp',
            user_id=sender_id,
            message=message_dict,
            business_unit=business_unit,
            payload=payload
        )
    else:
        logger.warning(f"Tipo interactivo no soportado: {interactive_type}")
        await send_message('whatsapp', sender_id, "Interacción no soportada.", business_unit.name.lower())

async def handle_media_message(message, sender_id, chatbot, business_unit, person, chat_state, payload):
    """
    Procesa mensajes de medios (imagen, audio, etc.).

    Args:
        message: Diccionario con el mensaje recibido.
        sender_id: ID del usuario (wa_id).
        chatbot: Instancia de ChatBotHandler.
        business_unit: Instancia de BusinessUnit.
        person: Instancia de Person.
        chat_state: Instancia de ChatState.
        payload: Payload completo del webhook.
    """
    media_id = message.get(message['type'], {}).get('id')
    if not media_id:
        logger.warning("Mensaje de medio recibido sin 'id'")
        await send_message('whatsapp', sender_id, "No pude procesar el medio enviado.", business_unit.name.lower())
        return

    whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(business_unit=business_unit, is_active=True).first)()
    if not whatsapp_api:
        logger.error("No se encontró configuración de WhatsAppAPI activa")
        return

    media_url = await get_media_url(whatsapp_api, media_id)
    if not media_url:
        await send_message('whatsapp', sender_id, "No pude descargar el medio enviado.", business_unit.name.lower())
        return

    logger.info(f"Media URL: {media_url}")
    await send_message('whatsapp', sender_id, "Medio recibido correctamente.", business_unit.name.lower())

async def handle_location_message(message, sender_id, chatbot, business_unit, person, chat_state, payload):
    """
    Procesa mensajes de ubicación y responde con la confirmación de las coordenadas.

    Args:
        message: Diccionario con el mensaje recibido.
        sender_id: ID del usuario (wa_id).
        chatbot: Instancia de ChatBotHandler.
        business_unit: Instancia de BusinessUnit.
        person: Instancia de Person.
        chat_state: Instancia de ChatState.
        payload: Payload completo del webhook.
    """
    location = message.get('location', {})
    latitude = location.get('latitude')
    longitude = location.get('longitude')
    if latitude and longitude:
        await send_message('whatsapp', sender_id,
                           f"Recibí tu ubicación: Latitud {latitude}, Longitud {longitude}", business_unit.name.lower())
    else:
        logger.warning("Mensaje de ubicación recibido sin coordenadas completas")
        await send_message('whatsapp', sender_id, "No pude procesar tu ubicación.", business_unit.name.lower())

async def handle_unknown_message(message, sender_id, chatbot, business_unit, person, chat_state, payload):
    """
    Maneja mensajes de tipos no soportados.

    Args:
        message: Diccionario con el mensaje recibido.
        sender_id: ID del usuario (wa_id).
        chatbot: Instancia de ChatBotHandler.
        business_unit: Instancia de BusinessUnit.
        person: Instancia de Person.
        chat_state: Instancia de ChatState.
        payload: Payload completo del webhook.
    """
    logger.warning(f"Tipo de mensaje no soportado: {message.get('type')}")
    await send_message('whatsapp', sender_id, "Tipo de mensaje no soportado. Por favor, envía texto.", business_unit.name.lower())

# ------------------------------------------------------------------------------
# Funciones para Envío de Mensajes
# ------------------------------------------------------------------------------
@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
async def send_whatsapp_message(
    user_id: str,
    message: str,
    buttons: Optional[List[dict]] = None,
    phone_id: Optional[str] = None,
    business_unit: Optional[BusinessUnit] = None
) -> bool:
    """
    Envía un mensaje de texto a un usuario en WhatsApp, con soporte para botones.

    Args:
        user_id: ID del usuario (wa_id).
        message: Texto del mensaje.
        buttons: Lista opcional de botones interactivos.
        phone_id: ID del número de teléfono de WhatsAppAPI.
        business_unit: Instancia de BusinessUnit para obtener la configuración.

    Returns:
        bool: True si el mensaje se envió correctamente, False en caso contrario.
    """
    try:
        # Validar parámetros de entrada
        if not user_id or not isinstance(user_id, str):
            logger.error("[send_whatsapp_message] user_id inválido")
            return False
        if not message or not isinstance(message, str):
            logger.error("[send_whatsapp_message] message inválido o vacío")
            return False

        # Obtener configuración de WhatsAppAPI
        whatsapp_api = None
        if business_unit:
            whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(business_unit=business_unit, is_active=True).first)()

        if whatsapp_api:
            phone_id = whatsapp_api.phoneID
            api_token = whatsapp_api.api_token
        else:
            logger.error("[send_whatsapp_message] Falta phone_id o api_token válido")
            return False

        if not phone_id or not api_token:
            logger.error("[send_whatsapp_message] phone_id o api_token no proporcionados")
            return False

        # Validar longitud del mensaje (límite de WhatsApp: 4096 caracteres)
        if len(message) > 4096:
            logger.warning(f"[send_whatsapp_message] Mensaje demasiado largo para {user_id}, truncando a 4093 caracteres")
            message = message[:4093] + "..."

        # Preparar URL y encabezados
        url = build_whatsapp_url(whatsapp_api)
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
            "text": {"body": message}
        }

        # Manejar botones
        if buttons:
            # Validar estructura de los botones
            valid_buttons = [
                btn for btn in buttons
                if isinstance(btn, dict) and btn.get('title') and btn.get('payload')
            ]
            if not valid_buttons:
                logger.warning(f"[send_whatsapp_message] No se encontraron botones válidos para {user_id}")
                payload["type"] = "text"  # Enviar como texto plano si no hay botones válidos
            else:
                # Nota: No truncamos botones aquí porque send_smart_options maneja listas grandes
                formatted_buttons = [
                    {
                        "type": "reply",
                        "reply": {
                            "id": btn.get('payload', f'btn_id_{i}'),
                            "title": btn.get('title', '')[:20]  # Límite de 20 caracteres por título
                        }
                    }
                    for i, btn in enumerate(valid_buttons)
                ]
                logger.debug(f"Botones formateados: {formatted_buttons}")
                payload["type"] = "interactive"
                payload["interactive"] = {
                    "type": "button",
                    "body": {"text": message},
                    "action": {"buttons": formatted_buttons}
                }

        # Enviar solicitud
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        logger.info(f"[send_whatsapp_message] Mensaje enviado a {user_id}")
        return True

    except httpx.HTTPStatusError as e:
        logger.error(f"[send_whatsapp_message] Error HTTP: {e.response.status_code} - {e.response.text}")
        return False
    except httpx.RequestException as e:
        logger.error(f"[send_whatsapp_message] Error de red: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"[send_whatsapp_message] Error inesperado: {str(e)}", exc_info=True)
        return False

@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
async def send_whatsapp_decision_buttons(user_id: str, message: str, buttons: List[Dict], business_unit: BusinessUnit) -> Tuple[bool, Optional[str]]:
    """
    Envía botones interactivos a WhatsApp, asegurando que los botones sean válidos.

    Args:
        user_id: ID del usuario (wa_id).
        message: Texto del mensaje.
        buttons: Lista de botones con estructura {'type': 'reply', 'reply': {'id': str, 'title': str}}.
        business_unit: Instancia de BusinessUnit.

    Returns:
        Tuple[bool, Optional[str]]: (Éxito, ID del mensaje o None).
    """
    try:
        # Validar botones
        valid_buttons = [
            btn for btn in buttons
            if isinstance(btn, dict) and btn.get('type') == 'reply'
            and 'reply' in btn and 'id' in btn['reply'] and 'title' in btn['reply']
        ]
        if not valid_buttons:
            logger.error(f"[send_whatsapp_decision_buttons] No se encontraron botones válidos: {buttons}")
            return False, None

        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(business_unit=business_unit, is_active=True).first)()
        if not whatsapp_api:
            logger.error(f"[send_whatsapp_decision_buttons] No se encontró WhatsAppAPI para {business_unit.name}")
            return False, None

        url = build_whatsapp_url(whatsapp_api)
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

        logger.debug(f"[send_whatsapp_decision_buttons] Enviando payload: {json.dumps(payload, indent=2)}")
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            msg_id = response.json().get("messages", [{}])[0].get("id", "")

        logger.info(f"[send_whatsapp_decision_buttons] Botones enviados correctamente. Message ID: {msg_id}")
        return True, msg_id

    except Exception as e:
        logger.error(f"[send_whatsapp_decision_buttons] Error: {e}", exc_info=True)
        return False, None

@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
async def send_whatsapp_list(user_id: str, message: str, sections: List[Dict], business_unit_name: str) -> bool:
    """
    Envía una lista interactiva a WhatsApp.

    Args:
        user_id: ID del usuario (wa_id).
        message: Texto del mensaje.
        sections: Lista de secciones con opciones (filas).
        business_unit_name: Nombre de la unidad de negocio.

    Returns:
        bool: True si la lista se envió correctamente, False en caso contrario.
    """
    try:
        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(business_unit__name__iexact=business_unit_name, is_active=True).first)()
        if not whatsapp_api:
            logger.error(f"[send_whatsapp_list] No se encontró WhatsAppAPI activo para {business_unit_name}")
            return False

        url = build_whatsapp_url(whatsapp_api)
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
                "header": {"type": "text", "text": "Menú Principal"},
                "body": {"text": message},
                "footer": {"text": "Selecciona una opción"},
                "action": {
                    "button": "Seleccionar",
                    "sections": sections
                }
            }
        }

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        logger.info(f"[send_whatsapp_list] Lista interactiva enviada a {user_id}")
        return True

    except Exception as e:
        logger.error(f"[send_whatsapp_list] Error enviando lista interactiva: {e}", exc_info=True)
        return False

@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
async def send_whatsapp_image(user_id: str, message: str, image_url: str, phone_id: str, business_unit: BusinessUnit):
    """
    Envía una imagen vía WhatsApp API.

    Args:
        user_id: ID del usuario (wa_id).
        message: Texto del mensaje (usado como caption).
        image_url: URL de la imagen.
        phone_id: ID del número de teléfono de WhatsAppAPI.
        business_unit: Instancia de BusinessUnit.

    Returns:
        bool: True si la imagen se envió correctamente, False en caso contrario.
    """
    try:
        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(phoneID=phone_id, business_unit=business_unit, is_active=True).first)()
        if not whatsapp_api:
            logger.error(f"[send_whatsapp_image] No se encontró WhatsAppAPI para phone_id: {phone_id}")
            return False

        url = build_whatsapp_url(whatsapp_api)
        headers = {
            "Authorization": f"Bearer {whatsapp_api.api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": message
            }
        }

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        logger.info(f"[send_whatsapp_image] Imagen enviada a {user_id}")
        return True

    except Exception as e:
        logger.error(f"[send_whatsapp_image] Error enviando imagen: {e}", exc_info=True)
        return False

# ------------------------------------------------------------------------------
# Obtención de Datos del Usuario
# ------------------------------------------------------------------------------
async def fetch_whatsapp_user_data(user_id: str, api_instance: WhatsAppAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Obtiene datos del usuario desde el payload del webhook de WhatsApp.
    Evita solicitudes HTTP innecesarias, usando datos disponibles en el payload.

    Args:
        user_id: ID del usuario (wa_id, e.g., '5215518490291').
        api_instance: Instancia de WhatsAppAPI con api_token.
        payload: Payload del webhook con información de contacto (opcional).

    Returns:
        Dict[str, Any]: Diccionario con datos del usuario (nombre, apellido_paterno, metadata, preferred_language).
    """
    try:
        # Validar api_instance
        if not isinstance(api_instance, WhatsAppAPI) or not hasattr(api_instance, 'api_token') or not api_instance.api_token:
            logger.error(f"[fetch_whatsapp_user_data] api_instance no es válido, recibido: {type(api_instance)}")
            return {
                'nombre': '',
                'apellido_paterno': '',
                'metadata': {},
                'preferred_language': 'es_MX'
            }

        # Validar payload
        if payload is None or not isinstance(payload, dict):
            logger.warning(f"[fetch_whatsapp_user_data] Payload inválido o ausente para user_id: {user_id}")
            return {
                'nombre': '',
                'apellido_paterno': '',
                'metadata': {},
                'preferred_language': 'es_MX'
            }

        # Extraer datos del payload si está disponible
        if "entry" not in payload:
            logger.warning(f"[fetch_whatsapp_user_data] Clave 'entry' no encontrada en el payload para user_id: {user_id}")
            return {
                'nombre': '',
                'apellido_paterno': '',
                'metadata': {},
                'preferred_language': 'es_MX'
            }

        contacts = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("contacts", [])
        if not contacts:
            logger.warning(f"[fetch_whatsapp_user_data] No se encontraron contactos en el payload para user_id: {user_id}")
            return {
                'nombre': '',
                'apellido_paterno': '',
                'metadata': {},
                'preferred_language': 'es_MX'
            }

        profile_name = contacts[0].get("profile", {}).get("name", "")
        nombre = profile_name.split(" ")[0] if profile_name else ""
        apellido = " ".join(profile_name.split(" ")[1:]) if len(profile_name.split(" ")) > 1 else ""
        return {
            'nombre': nombre,
            'apellido_paterno': apellido,
            'metadata': {},
            'preferred_language': 'es_MX'  # WhatsApp no proporciona el idioma
        }

    except Exception as e:
        logger.error(f"[fetch_whatsapp_user_data] Excepción: {e}", exc_info=True)
        return {
            'nombre': '',
            'apellido_paterno': '',
            'metadata': {},
            'preferred_language': 'es_MX'
        }
# ------------------------------------------------------------------------------
# Utilidades Adicionales
# ------------------------------------------------------------------------------
async def get_media_url(whatsapp_api: WhatsAppAPI, media_id: str) -> Optional[str]:
    """
    Obtiene la URL de un medio (imagen, audio, etc.) usando la API de WhatsApp.

    Args:
        whatsapp_api: Instancia de WhatsAppAPI con v_api y api_token.
        media_id: ID del medio.

    Returns:
        Optional[str]: URL del medio o None si falla.
    """
    try:
        url = f"https://graph.facebook.com/{whatsapp_api.v_api}/{media_id}"
        headers = {"Authorization": f"Bearer {whatsapp_api.api_token}"}
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("url")
    except Exception as e:
        logger.error(f"[get_media_url] Error obteniendo la URL del medio: {e}", exc_info=True)
        return None