# Ubicación /home/amigro/app/integrations/whatsapp.py

import json
import httpx
import logging
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from asgiref.sync import sync_to_async
from django.views.decorators.csrf import csrf_exempt
from app.models import WhatsAppAPI, MetaAPI, BusinessUnit, ConfiguracionBU, Person, ChatState
from app.integrations.services import send_message, get_api_instance
from typing import Optional, List, Dict
import time

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

@csrf_exempt
async def verify_whatsapp_token(request):
    """ Maneja la verificación del token para el webhook de WhatsApp. """
    try:
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        phone_id = request.GET.get('phoneID')

        if not phone_id:
            logger.error("Falta el parámetro phoneID en la solicitud de verificación")
            return HttpResponse("Falta el parámetro phoneID", status=400)

        cache_key_whatsapp = f"whatsappapi:{phone_id}"
        whatsapp_api = cache.get(cache_key_whatsapp)

        if not whatsapp_api:
            whatsapp_api = await sync_to_async(
                WhatsAppAPI.objects.filter(phoneID=phone_id).select_related('business_unit').first
            )()
            if not whatsapp_api:
                logger.error(f"PhoneID no encontrado: {phone_id}")
                return HttpResponse('Configuración no encontrada', status=404)
            cache.set(cache_key_whatsapp, whatsapp_api, timeout=CACHE_TIMEOUT)

        business_unit = whatsapp_api.business_unit
        cache_key_meta = f"metaapi:{business_unit.id}"
        meta_api = cache.get(cache_key_meta)

        if not meta_api:
            meta_api = await sync_to_async(
                MetaAPI.objects.filter(business_unit=business_unit).first
            )()
            if not meta_api:
                logger.error(f"MetaAPI no encontrado para la unidad de negocio: {business_unit.name}")
                return HttpResponse('Configuración no encontrada', status=404)
            cache.set(cache_key_meta, meta_api, timeout=CACHE_TIMEOUT)

        if verify_token == meta_api.verify_token:
            logger.info(f"Token de verificación correcto para phoneID: {phone_id}")
            return HttpResponse(challenge)
        else:
            logger.warning(f"Token de verificación inválido: {verify_token}")
            return HttpResponse('Token de verificación inválido', status=403)

    except Exception as e:
        logger.exception(f"Error inesperado en verify_whatsapp_token: {str(e)}")
        return JsonResponse({"error": "Error inesperado en la verificación de token"}, status=500)

async def handle_incoming_message(payload):
    """
    Manejo de mensajes entrantes de WhatsApp con conexión al chatbot.
    """
    try:
        from app.chatbot import ChatBotHandler
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
                    phone_id = value.get('metadata', {}).get('phone_number_id')
                    if not phone_id:
                        logger.error("No se encontró 'phone_number_id' en el metadata")
                        continue

                    cache_key_whatsapp = f"whatsappapi:{phone_id}"
                    whatsapp_api = cache.get(cache_key_whatsapp)

                    if not whatsapp_api:
                        whatsapp_api = await sync_to_async(
                            WhatsAppAPI.objects.filter(phoneID=phone_id).select_related('business_unit').first
                        )()
                        if not whatsapp_api:
                            logger.error(f"No se encontró WhatsAppAPI para phoneID: {phone_id}")
                            continue
                        cache.set(cache_key_whatsapp, whatsapp_api, timeout=CACHE_TIMEOUT)

                    business_unit = whatsapp_api.business_unit

                    name = value.get('contacts', [{}])[0].get('profile', {}).get('name', 'Usuario')
                    raw_text = message.get('text', {}).get('body', '')

                    person, _ = await sync_to_async(Person.objects.get_or_create)(
                        phone=sender_id,
                        defaults={'name': name}
                    )

                    chat_state, _ = await sync_to_async(ChatState.objects.get_or_create)(
                        user_id=sender_id,
                        defaults={'platform': 'whatsapp', 'business_unit': business_unit}
                    )
                    # Asociar chat_state al usuario si no está ya asociado
                    if not hasattr(person, 'chat_state'):
                        person.chat_state = chat_state
                        await sync_to_async(person.save)()

                    await chatbot_handler.process_message(
                        platform='whatsapp',
                        user_id=sender_id,
                        text=raw_text,
                        business_unit=business_unit
                    )

        return JsonResponse({'status': 'success'}, status=200)

    except Exception as e:
        logger.error(f"Error procesando el mensaje: {e}", exc_info=True)
        return JsonResponse({'error': f"Error procesando el mensaje: {e}"}, status=500)

# Define handler functions for each message type
async def handle_text_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    text = message['text']['body']
    await chatbot_handler.process_message(
        platform='whatsapp',
        user_id=sender_id,
        text=text,
        business_unit=business_unit,
    )

async def handle_media_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    media_id = message.get('image', {}).get('id') or message.get('audio', {}).get('id')
    media_type = message['type']
    if media_id:
        await process_media_message('whatsapp', sender_id, media_id, media_type, business_unit)
    else:
        logger.warning(f"Media message received without 'id' for type {media_type}")

async def handle_location_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    location = message.get('location')
    if location:
        await process_location_message('whatsapp', sender_id, location, business_unit)
    else:
        logger.warning("Location message received without location data")

async def handle_interactive_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    interactive = message.get('interactive', {})
    interactive_type = interactive.get('type')
    interactive_handlers = {
        'button_reply': handle_button_reply,
        'list_reply': handle_list_reply,
        # Add more interactive types and their handlers here
    }
    handler = interactive_handlers.get(interactive_type, handle_unknown_interactive)
    await handler(message, sender_id, chatbot_handler, business_unit, person, chat_state)

async def handle_button_reply(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    button_reply = message['interactive']['button_reply']
    payload = button_reply.get('payload') or button_reply.get('id')  # Adjust according to your payload structure
    logger.info(f"Button reply received: {payload}")
    await chatbot_handler.process_message(
        platform='whatsapp',
        user_id=sender_id,
        text=payload,  # Assuming payload corresponds to user response
        business_unit=business_unit
    )

async def handle_list_reply(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    list_reply = message['interactive']['list_reply']
    payload = list_reply.get('payload') or list_reply.get('id')  # Adjust according to your payload structure
    logger.info(f"List reply received: {payload}")
    await chatbot_handler.process_message(
        platform='whatsapp',
        user_id=sender_id,
        text=payload,  # Assuming payload corresponds to user response
        business_unit=business_unit
    )

async def handle_unknown_interactive(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    interactive_type = message.get('interactive', {}).get('type')
    logger.warning(f"Unsupported interactive type: {interactive_type}")
    await send_message('whatsapp', sender_id, "No entendí tu selección. Por favor, intenta nuevamente.", business_unit)

async def handle_unknown_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    message_type = message.get('type', 'unknown')
    logger.warning(f"Unsupported message type: {message_type}")
    await send_message('whatsapp', sender_id, "Tipo de mensaje no soportado.", business_unit)

async def process_media_message(platform, sender_id, media_id, media_type, business_unit):
    """
    Procesa mensajes de medios (imágenes, audio, etc.) entrantes.
    """
    try:
        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(business_unit=business_unit).first)()
        if not whatsapp_api:
            logger.error("No se encontró configuración de WhatsAppAPI.")
            return

        # Obtener la URL de descarga del medio
        media_url = await get_media_url(media_id, whatsapp_api.api_token)
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

async def get_media_url(media_id, api_token):
    """
    Obtiene la URL de descarga para un medio específico.
    """
    url = f"https://graph.facebook.com/{api_version}/{media_id}"
    headers = {
        "Authorization": f"Bearer {api_token}"
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

async def download_media(media_url, api_token):
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

async def handle_image_message(platform, sender_id, image_data, business_unit):
    """
    Procesa una imagen recibida.
    """
    logger.info(f"Imagen recibida de {sender_id}. Procesando imagen...")

    # Guardar la imagen en el sistema de archivos
    image_path = f"/home/amigro/app/static/images/{sender_id}_{int(time.time())}.jpg"
    try:
        with open(image_path, 'wb') as f:
            f.write(image_data)
        logger.info(f"Imagen guardada en {image_path}")
        await send_message(platform, sender_id, "Gracias por enviar la imagen. La hemos recibido correctamente.", business_unit)
    except Exception as e:
        logger.error(f"Error guardando la imagen: {e}", exc_info=True)
        await send_message(platform, sender_id, "Hubo un problema al procesar la imagen. Por favor, intenta nuevamente.", business_unit)

async def handle_audio_message(platform, sender_id, audio_data, business_unit):
    """
    Procesa un archivo de audio recibido.
    """
    logger.info(f"Audio recibido de {sender_id}. Procesando audio...")

    # Guardar el audio en el sistema de archivos
    audio_path = f"/path/to/save/audio/{sender_id}_{int(time.time())}.ogg"
    try:
        with open(audio_path, 'wb') as f:
            f.write(audio_data)
        logger.info(f"Audio guardado en {audio_path}")
        await send_message(platform, sender_id, "Gracias por enviar el audio. Lo hemos recibido correctamente.", business_unit)
    except Exception as e:
        logger.error(f"Error guardando el audio: {e}", exc_info=True)
        await send_message(platform, sender_id, "Hubo un problema al procesar el audio. Por favor, intenta nuevamente.", business_unit)

async def send_whatsapp_buttons(user_id, message, buttons, phone_id):
    """
    Envía botones interactivos a través de WhatsApp.
    """
    from app.integrations.whatsapp import send_whatsapp_decision_buttons

    try:
        await send_whatsapp_decision_buttons(
            user_id=user_id,
            message=message,
            buttons=buttons,
            phone_id=phone_id
        )
    except Exception as e:
        logger.error(f"Error enviando botones de WhatsApp: {e}", exc_info=True)

async def send_whatsapp_decision_buttons(user_id, message, buttons, business_unit):
    """
    Envía botones interactivos a través de WhatsApp usando la configuración asociada a la unidad de negocio.
    """
    from app.models import WhatsAppAPI

    try:
        # Obtener la configuración de WhatsAppAPI vinculada a la unidad de negocio
        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(
            business_unit=business_unit,
            is_active=True
        ).first)()

        if not whatsapp_api:
            raise ValueError(f"No se encontró configuración activa de WhatsAppAPI para la unidad de negocio: {business_unit.name}")

        url = f"https://graph.facebook.com/{whatsapp_api.v_api}/{whatsapp_api.phoneID}/messages"
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
                    "text": message
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

