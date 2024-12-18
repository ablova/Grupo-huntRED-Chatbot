# /home/pablollh/app/integrations/messenger.py

import logging
import json
import httpx
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from asgiref.sync import sync_to_async
from app.models import MessengerAPI, MetaAPI, BusinessUnit, ChatState, Person
from app.integrations.services import send_message, get_api_instance
from app.chatbot import ChatBotHandler
from typing import Optional, List, Dict

logger = logging.getLogger('messenger')
CACHE_TIMEOUT = 600  # 10 minutos

@csrf_exempt
async def messenger_webhook(request):
    """
    Webhook de Messenger para manejar mensajes entrantes y verificación de token.
    """
    if request.method == 'GET':
        return await verify_messenger_token(request)
    elif request.method == 'POST':
        try:
            body = request.body.decode('utf-8')
            payload = json.loads(body)
            logger.info(f"Payload recibido de Messenger: {json.dumps(payload, indent=4)}")
    
            # Procesar los mensajes recibidos
            for entry in payload.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    for message in messages:
                        sender_id = message['from']
                        message_text = message.get('message', {}).get('text', {}).get('body', '').strip()
                        if not message_text:
                            logger.warning(f"Mensaje vacío recibido de {sender_id}")
                            continue
                        logger.info(f"Mensaje recibido de {sender_id}: {message_text}")
    
                        # Obtener o crear el ChatState
                        chat_state = await get_or_create_chat_state(sender_id, 'messenger')
    
                        # Proceso el mensaje con el ChatBotHandler
                        chatbot_handler = ChatBotHandler()
                        response_text, options = await chatbot_handler.process_message('messenger', sender_id, message_text, chat_state.business_unit)
    
                        # Enviar la respuesta a Messenger
                        await send_messenger_response(sender_id, response_text, options, chat_state.business_unit)
    
            return HttpResponse(status=200)
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar JSON: {e}", exc_info=True)
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error al manejar el webhook de Messenger: {e}", exc_info=True)
            return JsonResponse({"error": "Internal Server Error"}, status=500)
    else:
        logger.warning(f"Método no permitido: {request.method}")
        return HttpResponse(status=405)

async def verify_messenger_token(request):
    """
    Verifica el token de Messenger durante la configuración del webhook.
    """
    verify_token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')
    phone_id = request.GET.get('phoneID')
    
    if not phone_id:
        logger.error("Falta el parámetro phoneID en la solicitud de verificación")
        return HttpResponse("Falta el parámetro phoneID", status=400)
    
    # Obtener MessengerAPI desde la caché
    cache_key_messenger = f"messengerapi:{phone_id}"
    messenger_api = cache.get(cache_key_messenger)
    
    if not messenger_api:
        messenger_api = await sync_to_async(
            MessengerAPI.objects.filter(phoneID=phone_id).select_related('business_unit').first
        )()
        if not messenger_api:
            logger.error(f"PhoneID no encontrado: {phone_id}")
            return HttpResponse('Configuración no encontrada', status=404)
        cache.set(cache_key_messenger, messenger_api, timeout=CACHE_TIMEOUT)
    
    # Obtener MetaAPI usando la unidad de negocio
    business_unit = messenger_api.business_unit
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
    
    # Validar el token de verificación
    if verify_token == meta_api.verify_token:
        logger.info(f"Token de verificación correcto para phoneID: {phone_id}")
        return HttpResponse(challenge)
    else:
        logger.warning(f"Token de verificación inválido: {verify_token}")
        return HttpResponse('Token de verificación inválido', status=403)

async def get_or_create_chat_state(user_id: str, platform: str) -> ChatState:
    """
    Obtiene o crea el estado de chat para un usuario específico.
    """
    try:
        chat_state, created = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=user_id,
            defaults={'platform': platform, 'current_question': None}
        )
        if created:
            logger.debug(f"ChatState creado para usuario {user_id}")
        else:
            logger.debug(f"ChatState obtenido para usuario {user_id}")
        return chat_state
    except Exception as e:
        logger.error(f"Error obteniendo o creando ChatState para {user_id}: {e}", exc_info=True)
        raise

async def send_messenger_response(user_id: str, message: str, options: Optional[List[Dict]], business_unit: BusinessUnit):
    """
    Envía una respuesta a Messenger, incluyendo botones si están disponibles.
    """
    if options:
        await send_messenger_buttons(user_id, message, options, business_unit.messenger_api.access_token)
    else:
        await send_message('messenger', user_id, message, business_unit)

async def send_messenger_buttons(user_id, message, buttons, access_token):
    """
    Envía un mensaje con botones a través de Facebook Messenger usando respuestas rápidas.
    :param user_id: ID del usuario en Messenger.
    :param message: Mensaje de texto a enviar.
    :param buttons: Lista de botones [{'content_type': 'text', 'title': 'Boton 1', 'payload': 'boton_1'}].
    :param access_token: Token de acceso de la página de Facebook.
    """
    url = f"https://graph.facebook.com/v11.0/me/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Construcción del payload para enviar el mensaje con botones
    payload = {
        "recipient": {"id": user_id},
        "message": {
            "text": message,
            "quick_replies": buttons
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Enviando botones a Messenger para el usuario {user_id}")
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Verifica si hubo algún error
            logger.info(f"Botones enviados correctamente a Messenger. Respuesta: {response.text}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Error enviando botones a Messenger: {e.response.text}")
    except Exception as e:
        logger.error(f"Error enviando botones a Messenger: {e}", exc_info=True)