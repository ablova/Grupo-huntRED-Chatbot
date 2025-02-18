# /home/pablo/app/chatbot/integrations/whatsapp.py
import json
import logging
import asyncio
import httpx
from typing import Optional, List
from asgiref.sync import sync_to_async
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app.chatbot.chatbot import ChatBotHandler
from app.models import Person, ChatState, BusinessUnit, WhatsAppAPI, Template
from app.chatbot.integrations.services import send_message

logger = logging.getLogger(__name__)
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
    Webhook principal que recibe mensajes de WhatsApp.
    Valida el método y el payload, y retorna una respuesta adecuada.
    """
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode('utf-8'))
        logger.info(f"Payload recibido: {json.dumps(payload, indent=2)}")

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
        logger.error(f"Error en el webhook: {e}", exc_info=True)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

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
        if not phone_id and business_unit:
            whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
                business_unit=business_unit, is_active=True
            ).select_related('business_unit').first())()
            if not whatsapp_api:
                logger.error(f"[send_whatsapp_message] No se encontró WhatsAppAPI activo para {business_unit.name}")
                return
            phone_id = whatsapp_api.phoneID
            api_token = whatsapp_api.api_token
            version_api = whatsapp_api.v_api  # Usamos la versión definida en la instancia
        else:
            if business_unit:
                whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
                    business_unit=business_unit, is_active=True
                ).select_related('business_unit').first())()
                api_token = whatsapp_api.api_token if whatsapp_api else None
            else:
                logger.warning("[send_whatsapp_message] No se pasó business_unit; se asume phone_id y token predefinidos.")
                api_token = phone_id  # Ajustar según la lógica real

        if not phone_id or not api_token:
            logger.error("[send_whatsapp_message] Falta phone_id o api_token válido.")
            return

        logger.debug(f"[send_whatsapp_message] Enviando mensaje a {user_id} con phone_id={phone_id} y botones: {bool(buttons)}")

        url = f"https://graph.facebook.com/{whatsapp_api.v_api}/{whatsapp_api.phoneID}/messages"
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
            logger.debug(f"[send_whatsapp_message] Convirtiendo mensaje a interactivo con {len(buttons)} botón(es).")
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
                    "body": {"text": message},
                    "action": {"buttons": formatted_buttons}
                }
            }

        attempt = 0
        while attempt < MAX_RETRIES:
            try:
                async with whatsapp_semaphore:
                    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                        response = await client.post(url, headers=headers, json=payload)
                        response.raise_for_status()
                        logger.info(f"[send_whatsapp_message] Mensaje enviado a {user_id}. Respuesta: {response.text[:200]}")
                        return
            except httpx.HTTPStatusError as e:
                logger.error(f"[send_whatsapp_message] Error HTTP en intento {attempt+1} para {user_id}: {e.response.text}", exc_info=True)
            except Exception as e:
                logger.error(f"[send_whatsapp_message] Error general en intento {attempt+1} para {user_id}: {e}", exc_info=True)
            attempt += 1
            await asyncio.sleep(2 ** attempt)
        logger.error(f"[send_whatsapp_message] Falló el envío a {user_id} tras {attempt} intentos.")
    except Exception as e:
        logger.error(f"[send_whatsapp_message] Error inesperado: {e}", exc_info=True)

async def send_whatsapp_decision_buttons(user_id, message, buttons, business_unit):
    try:
        # Obtener configuración de WhatsApp API
        whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
            business_unit=business_unit, is_active=True
        ).select_related('business_unit').first())()
        
        if not whatsapp_api:
            logger.error(f"[send_whatsapp_decision_buttons] No se encontró configuración activa para {business_unit.name}")
            return False, "No hay configuración de WhatsApp activa"

        url = f"https://graph.facebook.com/{whatsapp_api.v_api}/{whatsapp_api.phoneID}/messages"
        headers = {
            "Authorization": f"Bearer {whatsapp_api.api_token}",
            "Content-Type": "application/json"
        }

        # Validar que tengamos al menos 1 botón y máximo 3 (límite de WhatsApp)
        if not buttons or not isinstance(buttons, list) or len(buttons) > 3:
            logger.error(f"[send_whatsapp_decision_buttons] Botones inválidos: debe ser una lista de 1-3 elementos")
            return False, "Formato de botones inválido"

        # Procesar botones con validación completa
        formatted_buttons = []
        for button in buttons:
            if not isinstance(button, dict):
                continue
                
            payload = str(button.get('payload', '')) if button.get('payload') is not None else ''
            title = str(button.get('title', 'Opción'))
            
            # Validaciones según especificaciones de WhatsApp
            if not payload or len(payload) > 256:
                logger.warning(f"[send_whatsapp_decision_buttons] Payload inválido: {payload}")
                continue
                
            if not title or len(title) > 20:
                title = title[:20]  # Truncar si excede
                
            formatted_buttons.append({
                "type": "reply",
                "reply": {
                    "id": payload,
                    "title": title
                }
            })
        
        if not formatted_buttons:
            logger.error("[send_whatsapp_decision_buttons] No hay botones válidos para enviar")
            return False, "No hay botones válidos"
        
        # Validar longitud del mensaje (límite de WhatsApp: 1024 caracteres)
        if len(message) > 1024:
            message = message[:1021] + "..."
            
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": message},
                "action": {"buttons": formatted_buttons}
            }
        }

        # Timeout para evitar bloqueos
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response_data = response.json()
            
            if response.status_code == 200:
                message_id = response_data.get('messages', [{}])[0].get('id', 'unknown')
                logger.info(f"[send_whatsapp_decision_buttons] Botones enviados a {user_id}. Message ID: {message_id}")
                return True, message_id
            else:
                error_msg = response_data.get('error', {}).get('message', 'Error desconocido')
                logger.error(f"[send_whatsapp_decision_buttons] Error de API: {error_msg}")
                return False, error_msg

    except ValueError as e:
        logger.error(f"[send_whatsapp_decision_buttons] Error de validación: {str(e)}")
        return False, f"Error de validación: {str(e)}"
    except httpx.HTTPStatusError as e:
        error_msg = e.response.text if hasattr(e, 'response') else str(e)
        logger.error(f"[send_whatsapp_decision_buttons] Error HTTP: {error_msg}", exc_info=True)
        return False, f"Error HTTP: {error_msg}"
    except httpx.RequestError as e:
        logger.error(f"[send_whatsapp_decision_buttons] Error de conexión: {str(e)}", exc_info=True)
        return False, f"Error de conexión: {str(e)}"
    except Exception as e:
        logger.error(f"[send_whatsapp_decision_buttons] Error inesperado: {str(e)}", exc_info=True)
        return False, f"Error inesperado: {str(e)}"