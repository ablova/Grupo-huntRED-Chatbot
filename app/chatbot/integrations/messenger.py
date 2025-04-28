# /home/pablo/app/chatbot/integrations/messenger.py

import logging
import json
import httpx
import asyncio
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from asgiref.sync import sync_to_async
from app.models import MessengerAPI, MetaAPI, BusinessUnit, ChatState, Person
from app.chatbot.integrations.services import send_message
from app.chatbot.chatbot import ChatBotHandler
from typing import Optional, List, Dict

logger = logging.getLogger('chatbot')

REQUEST_TIMEOUT = 10.0  # segundos (si no está definido globalmente)
CACHE_TIMEOUT = 600  # 10 minutos

@csrf_exempt
async def messenger_webhook(request, page_id):
    """
    Webhook de Messenger para manejar mensajes entrantes y verificación de token.
    """
    if request.method == 'GET':
        return await verify_messenger_token(request, page_id)
    elif request.method == 'POST':
        try:
            body = request.body.decode('utf-8')
            payload = json.loads(body)
            logger.info(f"[messenger_webhook] Payload recibido: {json.dumps(payload, indent=2)}")
    
            # Obtener MessengerAPI basado en page_id
            messenger_api = await sync_to_async(
                MessengerAPI.objects.filter(page_id=page_id, is_active=True).select_related('meta_api').first
            )()

            if not messenger_api:
                logger.error(f"MessengerAPI no encontrado para page_id: {page_id}")
                return HttpResponse('Configuración no encontrada', status=404)

            # Procesar los mensajes recibidos
            for entry in payload.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    for message in messages:
                        sender_id = message.get('from')
                        message_text = message.get('message', {}).get('text', '').strip()
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
                        await send_messenger_response(sender_id, response_text, options, chat_state.business_unit, messenger_api)

            return HttpResponse(status=200)
        except json.JSONDecodeError as e:
            logger.error(f"[messenger_webhook] JSON inválido: {e}", exc_info=True)
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"[messenger_webhook] Error en webhook de Messenger: {e}", exc_info=True)
            return JsonResponse({"error": "Internal Server Error"}, status=500)
    else:
        logger.warning(f"[messenger_webhook] Método no permitido: {request.method}")
        return HttpResponse(status=405)

async def verify_messenger_token(request, page_id):
    """
    Verifica el token de Messenger durante la configuración del webhook.
    """
    verify_token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')

    if not verify_token or not challenge:
        logger.error("Faltan parámetros de verificación en la solicitud")
        return HttpResponse("Faltan parámetros de verificación", status=400)

    # Obtener MessengerAPI basado en page_id
    messenger_api = await sync_to_async(
        MessengerAPI.objects.filter(page_id=page_id, is_active=True).select_related('meta_api').first
    )()

    if not messenger_api:
        logger.error(f"MessengerAPI no encontrado para page_id: {page_id}")
        return HttpResponse('Configuración no encontrada', status=404)

    # Validar el token de verificación
    if verify_token == messenger_api.meta_api.verify_token:
        logger.info(f"Token de verificación correcto para page_id: {page_id}")
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

async def send_messenger_message(user_id: str, message: str, options: Optional[List[Dict]], business_unit: BusinessUnit, messenger_api: MessengerAPI):
    """
    Envía una respuesta a Messenger, incluyendo botones si están disponibles.
    """
    if options:
        await send_messenger_buttons(user_id, message, options, messenger_api.page_access_token)
    else:
        await send_message('messenger', user_id, message, business_unit)

async def send_messenger_buttons(user_id: str, message: str, quick_replies: List[Dict], access_token: str) -> bool:
    """
    Envía un mensaje con botones a través de Facebook Messenger usando respuestas rápidas.
    """
    url = "https://graph.facebook.com/v11.0/me/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "recipient": {"id": user_id},
        "message": {
            "text": message,
            "quick_replies": buttons
        }
    }
    max_retries = 3
    attempt = 0
    while attempt < max_retries:
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"[send_messenger_buttons] Mensaje enviado a Messenger para {user_id}. Respuesta: {response.text}")
                return
        except httpx.HTTPStatusError as e:
            logger.error(f"[send_messenger_buttons] Error HTTP en intento {attempt+1} para {user_id}: {e.response.text}", exc_info=True)
        except Exception as e:
            logger.error(f"[send_messenger_buttons] Error en intento {attempt+1} para {user_id}: {e}", exc_info=True)
        attempt += 1
        await asyncio.sleep(2 ** attempt)
    logger.error(f"[send_messenger_buttons] Falló el envío a {user_id} tras {attempt} intentos.")
    logger.info(f"✅ Botones enviados a {user_id} en Messenger")
    return True

async def send_messenger_image(user_id: str, image_url: str, caption: str, access_token: str):
    """Envía una imagen por Messenger."""
    url = "https://graph.facebook.com/v22.0/me/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "recipient": {"id": user_id},
        "message": {
            "attachment": {
                "type": "image",
                "payload": {"url": image_url, "is_reusable": True}
            },
            "text": caption
        }
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()

    logger.info(f"✅ Imagen enviada a {user_id} en Messenger.")
    
async def fetch_messenger_user_data(user_id: str, api_instance: MessengerAPI) -> Dict[str, Any]:
    """
    Fetch user data from Facebook Messenger (Graph API).
    """
    try:
        url = f"https://graph.facebook.com/v13.0/{user_id}"
        params = {
            "fields": "first_name,last_name,email,locale",
            "access_token": api_instance.page_access_token
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return {
                    'nombre': data.get('first_name', ''),
                    'apellido_paterno': data.get('last_name', ''),
                    'email': data.get('email', ''),
                    'preferred_language': data.get('locale', 'es_MX').replace('_', '_'),
                    'metadata': {}
                }
            else:
                logger.error(f"Error fetching Messenger user data: {response.text}")
                return {}
    except Exception as e:
        logger.error(f"Exception in fetch_messenger_user_data: {e}", exc_info=True)
        return {}