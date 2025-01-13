# Ubicación /home/pablollh/app/chatbot/integrations/whatsapp.py

import json
import httpx
import logging
from typing import Optional, List
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from asgiref.sync import sync_to_async
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from app.models import WhatsAppAPI, MetaAPI, BusinessUnit, Person, ChatState
from app.chatbot.integrations.services import send_message

logger = logging.getLogger('whatsapp')
CACHE_TIMEOUT = 600  # 10 minutos

@csrf_exempt
async def whatsapp_webhook(request):
    """
    Webhook de WhatsApp para manejar mensajes entrantes y verificación de token.
    """
    try:
        logger.info(f"Solicitud entrante: {request.method}, Headers: {dict(request.headers)}")

        if request.method == 'GET':
            return await verify_whatsapp_token(request)

        elif request.method == 'POST':
            try:
                body = request.body.decode('utf-8')
                payload = json.loads(body)
                logger.info(f"Payload recibido: {json.dumps(payload, indent=4)}")

                response = await handle_incoming_message(payload)
                logger.info(f"Respuesta generada: {response}")
                return response

            except json.JSONDecodeError as e:
                logger.error(f"Error al decodificar JSON: {str(e)}", exc_info=True)
                return JsonResponse({"error": "Error al decodificar el cuerpo de la solicitud"}, status=400)
            except Exception as e:
                logger.error(f"Error inesperado al manejar la solicitud POST: {str(e)}", exc_info=True)
                return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)

        else:
            logger.warning(f"Método no permitido: {request.method}")
            return HttpResponse(status=405)

    except Exception as e:
        logger.error(f"Error crítico en el webhook de WhatsApp: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"Error crítico: {str(e)}"}, status=500)

async def verify_whatsapp_token(request):
    """ Maneja la verificación del token para el webhook de WhatsApp. """
    try:
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if not verify_token:
            logger.error("Falta el parámetro hub.verify_token en la solicitud de verificación")
            return HttpResponse("Falta el parámetro hub.verify_token", status=400)

        # Buscar MetaAPI basado en verify_token (ya que ahora es común para todas las BUs)
        cache_key_meta = f"metaapi:verify_token:{verify_token}"
        meta_api = cache.get(cache_key_meta)

        if not meta_api:
            meta_api = await sync_to_async(
                MetaAPI.objects.filter(verify_token=verify_token).select_related('business_unit').first
            )()
            if not meta_api:
                logger.error(f"Verify token no encontrado: {verify_token}")
                return HttpResponse('Configuración no encontrada', status=404)
            cache.set(cache_key_meta, meta_api, timeout=CACHE_TIMEOUT)

        logger.info(f"Token de verificación correcto para webhook")
        return HttpResponse(challenge)

    except Exception as e:
        logger.exception(f"Error inesperado en verify_whatsapp_token: {str(e)}")
        return JsonResponse({"error": "Error inesperado en la verificación de token"}, status=500)

async def handle_incoming_message(payload):
    """
    Maneja los mensajes entrantes de WhatsApp con conexión al chatbot.
    """
    try:
        from app.chatbot import ChatBotHandler  # Asegúrate de tener esta importación correcta
        chatbot_handler = ChatBotHandler()

        if 'entry' not in payload:
            logger.error("El payload no contiene la clave 'entry'")
            return JsonResponse({'error': "El payload no contiene la clave 'entry'"}, status=400)

        for entry in payload.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                messages = value.get('messages', [])
                if not messages:
                    logger.info("No se encontraron mensajes en el cambio")
                    continue

                for message in messages:
                    sender_id = message.get('from')
                    phone_number_id = value.get('metadata', {}).get('phone_number_id')
                    if not phone_number_id:
                        logger.error("No se encontró 'phone_number_id' en el metadata")
                        continue

                    # Obtener WhatsAppAPI basado en phone_number_id (usando 'phoneID' según tu modelo)
                    cache_key_whatsapp = f"whatsappapi:phoneID:{phone_number_id}"
                    whatsapp_apis = cache.get(cache_key_whatsapp)

                    if not whatsapp_apis:
                        # Obtener el QuerySet de forma asíncrona
                        whatsapp_apis_qs = await sync_to_async(
                            WhatsAppAPI.objects.filter(phoneID=phone_number_id, is_active=True).select_related('business_unit').all
                        )()
                        # Convertir el QuerySet a una lista de forma asíncrona
                        whatsapp_apis = await sync_to_async(list)(whatsapp_apis_qs)

                        if not whatsapp_apis:
                            logger.error(f"No se encontró WhatsAppAPI para phoneID: {phone_number_id}")
                            continue

                        # Cachear la lista de APIs
                        cache.set(cache_key_whatsapp, whatsapp_apis, timeout=CACHE_TIMEOUT)

                    if not isinstance(whatsapp_apis, list):
                        whatsapp_apis = await sync_to_async(list)(whatsapp_apis)

                    for whatsapp_api in whatsapp_apis:
                        business_unit = whatsapp_api.business_unit

                        # Extraer información del contacto
                        contacts = value.get('contacts', [])
                        if contacts:
                            contact = contacts[0]
                            name = contact.get('profile', {}).get('name', 'Usuario')
                        else:
                            name = 'Usuario'

                        raw_text = message.get('text', {}).get('body', '') if message.get('type') == 'text' else ''

                        # Obtener o crear el usuario Person
                        person, created = await sync_to_async(Person.objects.get_or_create)(
                            phone=sender_id,
                            defaults={
                                'nombre': name.split()[0] if name else 'Nombre',
                                'apellido_paterno': ' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
                            }
                        )

                        # Obtener o crear el ChatState
                        chat_state, created = await sync_to_async(ChatState.objects.get_or_create)(
                            user_id=sender_id,
                            defaults={'platform': 'whatsapp', 'business_unit': business_unit}
                        )

                        # Asociar chat_state al usuario si no está ya asociado
                        if not hasattr(person, 'chat_state') or person.chat_state != chat_state:
                            person.chat_state = chat_state
                            await sync_to_async(person.save)()

                        # Determinar tipo de mensaje
                        message_type = message.get('type', 'unknown')
                        message_handlers = {
                            'text': handle_text_message,
                            'image': handle_media_message,
                            'audio': handle_media_message,
                            'location': handle_location_message,
                            'interactive': handle_interactive_message,
                            # Agrega más tipos si es necesario
                        }

                        handler = message_handlers.get(message_type, handle_unknown_message)
                        await handler(message, sender_id, chatbot_handler, business_unit, person, chat_state)

        return JsonResponse({'status': 'success'}, status=200)

    except Exception as e:
        logger.error(f"Error procesando el mensaje: {e}", exc_info=True)
        return JsonResponse({'error': f"Error procesando el mensaje: {e}"}, status=500)

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
    url = f"https://graph.facebook.com/{api_version}/{media_id}"
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

    image_path = f"/home/pablollh/app/static/images/{sender_id}_{int(timezone.now().timestamp())}.jpg"
    try:
        async with await sync_to_async(open)(image_path, 'wb') as f:
            await sync_to_async(f.write)(image_data)
        logger.info(f"Imagen guardada en {image_path}")

        await send_message(platform, sender_id, "Gracias por enviar la imagen. La hemos recibido correctamente.", business_unit)
    except Exception as e:
        logger.error(f"Error guardando la imagen: {e}", exc_info=True)
        await send_message(platform, sender_id, "Hubo un problema al procesar la imagen. Por favor, intenta nuevamente.", business_unit)

async def handle_audio_message(platform, sender_id, audio_data: bytes, business_unit):
    """
    Procesa un archivo de audio recibido: se guarda y se notifica confirmación al usuario.
    """
    logger.info(f"Audio recibido de {sender_id}. Procesando audio...")

    audio_path = f"/home/pablollh/app/static/audio/{sender_id}_{int(timezone.now().timestamp())}.ogg"
    try:
        async with await sync_to_async(open)(audio_path, 'wb') as f:
            await sync_to_async(f.write)(audio_data)
        logger.info(f"Audio guardado en {audio_path}")

        await send_message(platform, sender_id, "Gracias por enviar el audio. Lo hemos recibido correctamente.", business_unit)
    except Exception as e:
        logger.error(f"Error guardando el audio: {e}", exc_info=True)
        await send_message(platform, sender_id, "Hubo un problema al procesar el audio. Por favor, intenta nuevamente.", business_unit)

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
            from app.models import WhatsAppAPI
            whatsapp_api = await sync_to_async(
                WhatsAppAPI.objects.filter(phoneID=phone_id, is_active=True).select_related('business_unit').first()
            )()
            if not whatsapp_api:
                logger.error(f"[send_whatsapp_message] No se encontró WhatsAppAPI activo para {business_unit.name}")
                return
            phone_id = whatsapp_api.phoneID
            api_token = whatsapp_api.api_token
        else:
            from app.models import WhatsAppAPI
            if business_unit:
                whatsapp_api = await sync_to_async(
                    WhatsAppAPI.objects.filter(phoneID=phone_id, is_active=True).select_related('business_unit').first()
                )()
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
        await send_whatsapp_decision_buttons(user_id=user_id, message=message, buttons=buttons, phone_id=phone_id)
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