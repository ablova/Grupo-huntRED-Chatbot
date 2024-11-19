# /home/amigro/app/integrations/whatsapp.py

import json
import httpx
import logging
from django.core.cache import cache
from asgiref.sync import sync_to_async
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from app.models import WhatsAppAPI, MetaAPI, BusinessUnit, Configuracion
from app.chatbot import ChatBotHandler

logger = logging.getLogger('whatsapp')
#Se crea un cache regenerativo para que no se hagan demasiadas llamadas al API
CACHE_TIMEOUT = 600  # 10 minutos
AMIGRO_VERIFY_TOKEN = "amigro_secret_token"

@csrf_exempt
async def whatsapp_webhook(request):
    """
    Webhook de WhatsApp para manejar mensajes entrantes y verificación de token.
    """
    try:
        logger.info(f"Solicitud entrante: {request.method}, Headers: {dict(request.headers)}")

        # Loggear el cuerpo de la solicitud
        try:
            body = await sync_to_async(request.body.decode)('utf-8')
            logger.debug(f"Cuerpo de la solicitud recibido: {body}")
        except Exception as e:
            logger.error(f"Error al leer el cuerpo de la solicitud: {str(e)}", exc_info=True)
            return JsonResponse({"error": f"Error al leer el cuerpo de la solicitud: {str(e)}"}, status=500)

        # Manejo del método GET para verificación de token
        if request.method == 'GET':
            return await verify_whatsapp_token(request)

        # Manejo del método POST para mensajes entrantes
        elif request.method == 'POST':
            try:
                payload = json.loads(body)
                logger.info(f"Payload recibido: {json.dumps(payload, indent=4)}")

                # Verificar y obtener el parámetro phoneID
                phone_id = payload.get('entry', [])[0].get('changes', [])[0].get('value', {}).get('metadata', {}).get('phone_number_id')
                if not phone_id:
                    logger.error("Falta el parámetro phoneID en el payload")
                    return JsonResponse({"error": "Falta el parámetro phoneID o phone_number_id como se extrae - value.metadata.phone_number_id."}, status=400)

                # Llamar a la función para manejar el mensaje entrante
                response = await handle_incoming_message(payload)
                logger.info(f"Respuesta generada: {response}")
                return response

            except json.JSONDecodeError as e:
                logger.error(f"Error al decodificar JSON: {str(e)}", exc_info=True)
                return JsonResponse({"error": "Error al decodificar el cuerpo de la solicitud"}, status=400)
            except Exception as e:
                logger.error(f"Error inesperado al manejar la solicitud POST: {str(e)}", exc_info=True)
                return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)

        # Manejar métodos no permitidos
        else:
            logger.warning(f"Método no permitido: {request.method}")
            return HttpResponse(status=405)

    except Exception as e:
        logger.error(f"Error crítico en el webhook de WhatsApp: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"Error crítico: {str(e)}"}, status=500)
    
@csrf_exempt
async def verify_whatsapp_token(request):
    try:
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        phone_id = request.GET.get('phoneID')

        if not phone_id:
            logger.error("Falta el parámetro phoneID en la solicitud de verificación")
            return HttpResponse("Falta el parámetro phoneID", status=400)

        # Obtener WhatsAppAPI desde la caché
        cache_key_whatsapp = f"whatsappapi:{phone_id}"
        whatsapp_api = cache.get(cache_key_whatsapp)

        if not whatsapp_api:
            whatsapp_api = await sync_to_async(
                lambda: WhatsAppAPI.objects.filter(phoneID=phone_id).select_related('business_unit').first()
            )()
            if not whatsapp_api:
                logger.error(f"PhoneID no encontrado: {phone_id}")
                return HttpResponse('Configuración no encontrada', status=404)

            # Guardar en caché
            cache.set(cache_key_whatsapp, whatsapp_api, timeout=CACHE_TIMEOUT)

        # Obtener MetaAPI usando la unidad de negocio
        business_unit = whatsapp_api.business_unit
        cache_key_meta = f"metaapi:{business_unit.id}"
        meta_api = cache.get(cache_key_meta)

        if not meta_api:
            meta_api = await sync_to_async(
                lambda: MetaAPI.objects.filter(business_unit=business_unit).first()
            )()
            if not meta_api:
                logger.error(f"MetaAPI no encontrado para la unidad de negocio: {business_unit.name}")
                return HttpResponse('Configuración no encontrada', status=404)

            # Guardar en caché
            cache.set(cache_key_meta, meta_api, timeout=CACHE_TIMEOUT)

        # Validar el token de verificación
        if verify_token == meta_api.verify_token:
            logger.info(f"Token de verificación correcto para phoneID: {phone_id}")
            return HttpResponse(challenge)
        else:
            logger.warning(f"Token de verificación inválido: {verify_token}")
            return HttpResponse('Token de verificación inválido', status=403)

    except Exception as e:
        logger.exception(f"Error inesperado en verify_whatsapp_token: {str(e)}")
        return JsonResponse({"error": "Error inesperado en la verificación de token"}, status=500)

@csrf_exempt
async def handle_incoming_message(request):
    """
    Manejo de mensajes entrantes de WhatsApp con conexión al chatbot.
    """
    try:
        # Obtener configuración global
        config = await sync_to_async(lambda: Configuracion.objects.first())()
        if not config:
            logger.error("Configuración global no encontrada")
            return JsonResponse({'error': 'Configuración no encontrada'}, status=500)

        test_phone_number = config.test_phone_number
        is_test_mode = config.is_test_mode
        default_platform = config.default_platform

        # Decodificar el cuerpo de la solicitud
        try:
            payload = request if isinstance(request, dict) else json.loads(request.body.decode('utf-8'))
            logger.info(f"Payload recibido: {json.dumps(payload, indent=4)}")
        except json.JSONDecodeError as e:
            logger.error("Error al decodificar JSON", exc_info=True)
            return JsonResponse({'error': 'Error al decodificar el JSON'}, status=400)

        # Procesar el payload
        if 'entry' not in payload:
            logger.error("El payload no contiene la clave 'entry'")
            return JsonResponse({'error': "El payload no contiene la clave 'entry'"}, status=400)

        for entry in payload.get('entry', []):
            if 'changes' not in entry:
                logger.warning("La entrada no contiene cambios (changes)")
                continue

            for change in entry.get('changes', []):
                value = change.get('value', {})
                messages = value.get('messages', [])
                if not messages:
                    logger.info("No se encontraron mensajes en el cambio")
                    continue

                for message in messages:
                    sender_id = message.get('from')
                    message_type = message.get('type', 'text')
                    logger.info(f"Mensaje recibido de {sender_id} con tipo {message_type}")

                    # Validar si es un mensaje de prueba
                    if is_test_mode and sender_id == test_phone_number:
                        logger.info("Modo de prueba activado. Mensaje recibido del número de prueba.")
                        await send_test_notification(sender_id)
                        continue

                    # Obtener el phone_id del payload
                    phone_id = value.get('metadata', {}).get('phone_number_id')

                    # Obtener WhatsAppAPI y unidad de negocio
                    whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(phoneID=phone_id).first)()
                    if not whatsapp_api:
                        logger.error(f"No se encontró WhatsAppAPI para phoneID: {phone_id}")
                        return JsonResponse({'error': 'WhatsAppAPI no encontrada'}, status=404)

                    business_unit = await sync_to_async(lambda: whatsapp_api.business_unit)()

                    # Instancia del chatbot
                    chatbot_handler = ChatBotHandler()

                    # Procesar según el tipo de mensaje
                    try:
                        if message_type == 'text':
                            message_text = message.get('text', {}).get('body', '')
                            logger.info(f"Mensaje de texto recibido: {message_text}")

                            # Llamar al chatbot para procesar el mensaje
                            await chatbot_handler.process_message(
                                platform='whatsapp',
                                user_id=sender_id,
                                text=message_text,
                                business_unit=business_unit
                            )
                            logger.info(f"Mensaje procesado por el chatbot para el usuario {sender_id}")

                        elif message_type == 'image':
                            image_id = message.get('image', {}).get('id')
                            if image_id:
                                await process_media_message('whatsapp', sender_id, image_id, 'image')
                            else:
                                logger.warning("Mensaje de imagen recibido sin 'id'")

                        elif message_type == 'audio':
                            audio_id = message.get('audio', {}).get('id')
                            if audio_id:
                                await process_media_message('whatsapp', sender_id, audio_id, 'audio')
                            else:
                                logger.warning("Mensaje de audio recibido sin 'id'")

                        elif message_type == 'location':
                            location = message.get('location')
                            if location:
                                await process_location_message('whatsapp', sender_id, location)
                            else:
                                logger.warning("Mensaje de ubicación recibido sin datos de ubicación")

                        else:
                            logger.warning(f"Tipo de mensaje no soportado: {message_type}")

                    except Exception as e:
                        logger.error(f"Error al procesar el mensaje de tipo {message_type}: {e}", exc_info=True)
                        return JsonResponse({'error': f"Error al procesar el mensaje: {e}"}, status=500)

        return JsonResponse({'status': 'success'}, status=200)

    except Exception as e:
        logger.error(f"Error inesperado al manejar la solicitud: {e}", exc_info=True)
        return JsonResponse({'error': f"Error inesperado: {e}"}, status=500)
async def process_media_message(platform, sender_id, media_id, media_type):
    """
    Procesa mensajes de medios (imágenes, audio, etc.) entrantes.
    """
    try:
        whatsapp_api = await WhatsAppAPI.objects.afirst()
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
            await handle_image_message(platform, sender_id, media_data)
        elif media_type == 'audio':
            await handle_audio_message(platform, sender_id, media_data)
        else:
            logger.warning(f"Tipo de medio no soportado: {media_type}")

    except Exception as e:
        logger.error(f"Error procesando mensaje de medios: {e}", exc_info=True)

async def get_media_url(media_id, api_token):
    """
    Obtiene la URL de descarga para un medio específico.
    """
    url = f"https://graph.facebook.com/v17.0/{media_id}"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    try:
        async with httpx.AsyncClient() as client:
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
        async with httpx.AsyncClient() as client:
            response = await client.get(media_url, headers=headers)
            response.raise_for_status()
            return response.content
    except httpx.HTTPStatusError as e:
        logger.error(f"Error descargando el medio: {e.response.text}", exc_info=True)
    except Exception as e:
        logger.error(f"Error general descargando el medio: {e}", exc_info=True)

    return None

async def handle_image_message(platform, sender_id, image_data):
    """
    Procesa una imagen recibida.
    """
    # Aquí puedes guardar la imagen, procesarla o extraer información
    # Por ejemplo, podrías guardar la imagen en el sistema de archivos o en una base de datos

    logger.info(f"Imagen recibida de {sender_id}. Procesando imagen...")

    # Ejemplo: Guardar la imagen en el sistema de archivos
    image_path = f"/path/to/save/images/{sender_id}_{int(time.time())}.jpg"
    with open(image_path, 'wb') as f:
        f.write(image_data)

    # Enviar una respuesta al usuario
    response_message = "Gracias por enviar la imagen. La hemos recibido correctamente."
    await send_message(platform, sender_id, response_message)

async def handle_audio_message(platform, sender_id, audio_data):
    """
    Procesa un archivo de audio recibido.
    """
    # Aquí puedes guardar el audio, procesarlo o extraer información
    # Por ejemplo, podrías transcribir el audio o guardarlo para análisis posterior

    logger.info(f"Audio recibido de {sender_id}. Procesando audio...")

    # Ejemplo: Guardar el audio en el sistema de archivos
    audio_path = f"/path/to/save/audio/{sender_id}_{int(time.time())}.ogg"
    with open(audio_path, 'wb') as f:
        f.write(audio_data)

    # Enviar una respuesta al usuario
    response_message = "Gracias por enviar el audio. Lo hemos recibido correctamente."
    await send_message(platform, sender_id, response_message)

async def process_location_message(platform, sender_id, location):
    """
    Procesa una ubicación recibida.
    """
    latitude = location.get('latitude')
    longitude = location.get('longitude')
    logger.info(f"Ubicación recibida de {sender_id}: Latitud {latitude}, Longitud {longitude}")

    # Aquí puedes usar la ubicación para proporcionar información relevante
    # Por ejemplo, mostrar vacantes cercanas al usuario

    # Enviar una respuesta al usuario
    response_message = f"Hemos recibido tu ubicación: Latitud {latitude}, Longitud {longitude}."
    await send_message(platform, sender_id, response_message)

async def send_whatsapp_message(user_id, message, phone_id, image_url=None):
    """
    Envía un mensaje a través de WhatsApp usando la configuración de WhatsAppAPI.
    """
    whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(phoneID=phone_id).first)()
    if not whatsapp_api:
        logger.error(f"No se encontró configuración para phoneID: {phone_id}")
        return

    token = whatsapp_api.api_token  # Corregido: Usar el api_token de WhatsAppAPI
    api_version = whatsapp_api.v_api

    url = f"https://graph.facebook.com/{api_version}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": user_id,
        "type": "image" if image_url else "text",
        "image": {"link": image_url} if image_url else None,
        "text": {"body": message} if not image_url else None
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Mensaje enviado a {user_id}: {message}")
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Error enviando mensaje a {user_id}: {e.response.text}")
        raise e
    
async def send_whatsapp_decision_buttons(user_id, message, buttons, phone_id):
    """
    Envía botones interactivos de decisión (Sí/No) a través de WhatsApp usando MetaAPI.
    """
    # Obtener configuración de MetaAPI usando el phoneID
    whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(phoneID=phone_id).first)()
    if not meta_api:
        logger.error(f"No se encontró configuración para phoneID: {phone_id}")
        return

    api_token = whatsapp_api.api_token
    version_api = meta_api.version_api

    url = f"https://graph.facebook.com/{version_api}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # Validación de botones para asegurarse de que sean sólo "Sí" y "No"
    if not isinstance(buttons, list) or len(buttons) != 2:
        raise ValueError("Se deben proporcionar exactamente 2 botones: Sí y No.")

    # Formatear los botones para WhatsApp
    formatted_buttons = []
    for idx, button in enumerate(buttons):
        formatted_button = {
            "type": "reply",
            "reply": {
                "id": f"btn_{idx}",  # ID único para cada botón
                "title": button['title'][:20]  # Límite de 20 caracteres
            }
        }
        formatted_buttons.append(formatted_button)

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

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Botones de Sí/No enviados a {user_id} correctamente.")
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Error enviando botones de decisión (Sí/No): {e.response.text}", exc_info=True)
        raise e
    except Exception as e:
        logger.error(f"Error general enviando botones de decisión (Sí/No): {e}", exc_info=True)
        raise e

async def invite_known_person(referrer, name, apellido, phone_number):
    """
    Invita a una persona conocida vía WhatsApp y crea un pre-registro.
    """
    try:
        invitado, created = await sync_to_async(lambda: Person.objects.update_or_create(
            telefono=phone_number, defaults={'nombre': name, 'apellido_paterno': apellido}))()

        await sync_to_async(Invitacion.objects.create)(referrer=referrer, invitado=invitado)

        if created:
            mensaje = f"Hola {name}, has sido invitado por {referrer.nombre} a unirte a Amigro.org. ¡Únete a nuestra comunidad!"
            await send_whatsapp_message(phone_number, mensaje, referrer.api_token, referrer.phoneID, referrer.v_api)

        return invitado

    except Exception as e:
        logger.error(f"Error al invitar a {name}: {e}")
        raise

async def registro_amigro(recipient, access_token, phone_id, version_api, form_data):
    """
    Envía una plantilla de mensaje de registro personalizado a un nuevo usuario en WhatsApp.

    :param recipient: Número de teléfono del destinatario en formato internacional.
    :param access_token: Token de acceso para la API de WhatsApp.
    :param phone_id: ID del teléfono configurado para el envío de mensajes.
    :param version_api: Versión de la API de WhatsApp.
    :param form_data: Diccionario con datos del usuario para personalizar la plantilla.
    """
    try:
        url = f"https://graph.facebook.com/{version_api}/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": "registro_amigro",
                "language": {"code": "es_MX"},
                "components": [
                    {
                        "type": "header",
                        "parameters": [{"type": "image", "image": {"link": "https://amigro.org/registro2.png"}}]
                    },
                    {"type": "body", "parameters": []},
                    {
                        "type": "button",
                        "sub_type": "FLOW",
                        "index": "0",
                        "parameters": [{"type": "text", "text": "https://amigro.org"}]
                    }
                ]
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        logger.info(f"Plantilla de registro enviada correctamente a {recipient}")
        return response.json()

    except Exception as e:
        logger.error(f"Error enviando plantilla de registro a {recipient}: {e}", exc_info=True)
        raise e

async def nueva_posicion_amigro(recipient, access_token, phone_id, version_api, form_data):
    """
    Envía una plantilla de mensaje para notificar al usuario de una nueva oportunidad laboral.

    :param recipient: Número de teléfono del destinatario en formato internacional.
    :param access_token: Token de acceso para la API de WhatsApp.
    :param phone_id: ID del teléfono configurado para el envío de mensajes.
    :param version_api: Versión de la API de WhatsApp.
    :param form_data: Diccionario con datos de la vacante para personalizar la plantilla.
    """
    try:
        url = f"https://graph.facebook.com/{version_api}/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": "nueva_posicion_amigro",
                "language": {"code": "es_MX"},
                "components": [
                    {
                        "type": "header",
                        "parameters": [{"type": "image", "image": {"link": "https://amigro.org/registro.png"}}]
                    },
                    {"type": "body", "parameters": [{"type": "text", "text": "Hola, bienvenido a Amigro!"}]},
                    {
                        "type": "button",
                        "sub_type": "FLOW",
                        "index": "0",
                        "parameters": [{"type": "text", "text": "https://amigro.org"}]
                    }
                ]
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        logger.info(f"Plantilla de nueva posición enviada correctamente a {recipient}")
        return response.json()

    except Exception as e:
        logger.error(f"Error enviando plantilla de nueva posición a {recipient}: {e}", exc_info=True)
        raise e

def dividir_botones(botones, n):
    """
    Divide la lista de botones en grupos de tamaño `n`, útil para cuando una plataforma tiene límite en el número de botones.

    :param botones: Lista de botones para dividir.
    :param n: Tamaño del grupo de botones.
    :return: Generador que produce grupos de botones.
    """
    for i in range(0, len(botones), n):
        yield botones[i:i + n]

async def send_pregunta_with_buttons(user_id, pregunta, phone_id):
    """
    Envía una pregunta con botones de respuesta en WhatsApp.

    :param user_id: ID del usuario destinatario.
    :param pregunta: Objeto Pregunta con el contenido y los botones a enviar.
    :param phone_id: ID del teléfono de WhatsApp para obtener la configuración.
    """
    from app.integrations.whatsapp import send_whatsapp_buttons

    if pregunta.botones_pregunta.exists():
        botones = pregunta.botones_pregunta.all()
        whatsapp_api = await WhatsAppAPI.objects.afirst(phoneID__exact=phone_id)

        if not meta_api:
            logger.error(f"No se encontró configuración para phoneID: {phone_id}")
            return

        message = pregunta.content
        tasks = []

        # Dividir los botones en grupos de tres para WhatsApp
        for tercia in dividir_botones(list(botones), 3):
            buttons = [{"title": boton.name} for boton in tercia]
            logger.info(f"Enviando botones: {[boton['title'] for boton in buttons]} a {user_id}")
            tasks.append(send_whatsapp_buttons(
                user_id,
                message,
                buttons,
                meta_api.api_token,
                meta_api.phoneID,
                meta_api.version_api
            ))

        await asyncio.gather(*tasks)
    else:
        logger.warning(f"La pregunta {pregunta.id} no tiene botones asignados.")
    
async def send_test_notification(user_id):
    """
    Envía una notificación de prueba al número configurado.
    """
    from app.integrations.whatsapp import send_whatsapp_message
    config = await sync_to_async(lambda: Configuracion.objects.first())()
    message = "🔔 Notificación de prueba recibida. El sistema está operativo."
    
    await send_whatsapp_message(
        user_id,
        message,
        config.default_platform
    )
    logger.info(f"Notificación de prueba enviada a {user_id}.")