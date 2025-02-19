# /home/pablo/app/chatbot/integrations/instagram.py
import logging
import json
import httpx
import asyncio
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from asgiref.sync import sync_to_async
from app.models import InstagramAPI, MetaAPI, BusinessUnit, ChatState, Person
from app.chatbot.integrations.services import MessageService, EmailService
from app.chatbot.chatbot import ChatBotHandler
from typing import Optional, List, Dict

logger = logging.getLogger("app.chatbot.integrations.instagram")

REQUEST_TIMEOUT = 10.0  # segundos
CACHE_TIMEOUT = 600  # 10 minutos

@csrf_exempt
async def instagram_webhook(request):
    """
    Webhook de Instagram para manejar mensajes entrantes y verificación de token.
    """
    if request.method == 'GET':
        return await verify_instagram_token(request)
    elif request.method == 'POST':
        try:
            body = request.body.decode('utf-8')
            payload = json.loads(body)
            logger.info(f"[instagram_webhook] Payload recibido: {json.dumps(payload, indent=2)}")
            # Procesamiento del payload
            for entry in payload.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    for message in messages:
                        sender_id = message.get('from')
                        message_text = message.get('text', {}).get('body', '').strip()
                        if not message_text:
                            logger.warning(f"[instagram_webhook] Mensaje vacío de {sender_id}")
                            continue
                        logger.info(f"[instagram_webhook] Mensaje de {sender_id}: {message_text}")
    
                        # Obtener o crear el ChatState
                        chat_state = await get_or_create_chat_state(sender_id, 'instagram')
    
                        # Proceso el mensaje con el ChatBotHandler
                        chatbot_handler = ChatBotHandler()
                        response_text, options = await chatbot_handler.process_message('instagram', sender_id, message_text, chat_state.business_unit)
    
                        # Enviar la respuesta a Instagram
                        await send_instagram_response(sender_id, response_text, options, chat_state.business_unit)
    
            return HttpResponse(status=200)
        except json.JSONDecodeError as e:
            logger.error(f"[instagram_webhook] Error al decodificar JSON: {e}", exc_info=True)
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"[instagram_webhook] Error en el webhook de Instagram: {e}", exc_info=True)
            return JsonResponse({"error": "Internal Server Error"}, status=500)
    else:
        logger.warning(f"[instagram_webhook] Método no permitido: {request.method}")
        return HttpResponse(status=405)

async def verify_instagram_token(request):
    """
    Verifica el token de Instagram durante la configuración del webhook.
    """
    verify_token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')
    phone_id = request.GET.get('phoneID')
    
    if not phone_id:
        logger.error("Falta el parámetro phoneID en la solicitud de verificación")
        return HttpResponse("Falta el parámetro phoneID", status=400)
    
    # Obtener InstagramAPI desde la caché
    cache_key_instagram = f"instagramapi:{phone_id}"
    instagram_api = cache.get(cache_key_instagram)
    
    if not instagram_api:
        instagram_api = await sync_to_async(
            InstagramAPI.objects.filter(phoneID=phone_id).select_related('business_unit').first
        )()
        if not instagram_api:
            logger.error(f"PhoneID no encontrado: {phone_id}")
            return HttpResponse('Configuración no encontrada', status=404)
        cache.set(cache_key_instagram, instagram_api, timeout=CACHE_TIMEOUT)
    
    # Obtener MetaAPI usando la unidad de negocio
    business_unit = instagram_api.business_unit
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

async def send_instagram_message(user_id: str, message: str, options: Optional[List[Dict]], business_unit: BusinessUnit):
    """
    Envía una respuesta a Instagram, incluyendo botones si están disponibles.
    """
    if options:
        await send_instagram_buttons(user_id, message, options, business_unit.instagram_api.access_token)
    else:
        await send_message('instagram', user_id, message, business_unit)

async def send_instagram_buttons(user_id, message, buttons, access_token):
    """
    Envía un mensaje con botones a través de Instagram usando respuestas rápidas.
    """
    url = f"https://graph.facebook.com/v11.0/me/messages"
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
                logger.info(f"[send_instagram_buttons] Botones enviados a Instagram para {user_id}. Respuesta: {response.text}")
                return
        except httpx.HTTPStatusError as e:
            logger.error(f"[send_instagram_buttons] Error HTTP en intento {attempt+1} para {user_id}: {e.response.text}", exc_info=True)
        except Exception as e:
            logger.error(f"[send_instagram_buttons] Error en intento {attempt+1} para {user_id}: {e}", exc_info=True)
        attempt += 1
        await asyncio.sleep(2 ** attempt)
    logger.error(f"[send_instagram_buttons] Falló el envío a {user_id} tras {attempt} intentos.")