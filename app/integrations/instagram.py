# /home/amigro/app/integrations/instagram.py
import logging
import json
import httpx
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from asgiref.sync import sync_to_async
from app.models import InstagramAPI, MetaAPI, BusinessUnit, ChatState, Person
from app.integrations.services import send_message, get_api_instance
from app.chatbot import ChatBotHandler
from typing import Optional, List, Dict

logger = logging.getLogger('instagram')
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
            logger.info(f"Payload recibido de Instagram: {json.dumps(payload, indent=4)}")
    
            # Procesar los mensajes recibidos
            for entry in payload.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    for message in messages:
                        sender_id = message.get('from')
                        message_text = message.get('text', {}).get('body', '').strip()
                        if not message_text:
                            logger.warning(f"Mensaje vacío recibido de {sender_id}")
                            continue
                        logger.info(f"Mensaje recibido de {sender_id}: {message_text}")
    
                        # Obtener o crear el ChatState
                        chat_state = await get_or_create_chat_state(sender_id, 'instagram')
    
                        # Proceso el mensaje con el ChatBotHandler
                        chatbot_handler = ChatBotHandler()
                        response_text, options = await chatbot_handler.process_message('instagram', sender_id, message_text, chat_state.business_unit)
    
                        # Enviar la respuesta a Instagram
                        await send_instagram_response(sender_id, response_text, options, chat_state.business_unit)
    
            return HttpResponse(status=200)
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar JSON: {e}", exc_info=True)
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error al manejar el webhook de Instagram: {e}", exc_info=True)
            return JsonResponse({"error": "Internal Server Error"}, status=500)
    else:
        logger.warning(f"Método no permitido: {request.method}")
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

async def send_instagram_response(user_id: str, message: str, options: Optional[List[Dict]], business_unit: BusinessUnit):
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
    :param user_id: ID del usuario en Instagram.
    :param message: Mensaje de texto a enviar.
    :param buttons: Lista de botones [{'content_type': 'text', 'title': 'Boton 1', 'payload': 'boton_1'}].
    :param access_token: Token de acceso de la cuenta de Instagram.
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
            logger.debug(f"Enviando botones a Instagram para el usuario {user_id}")
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Botones enviados correctamente a Instagram. Respuesta: {response.text}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Error enviando botones a Instagram: {e.response.text}")
    except Exception as e:
        logger.error(f"Error enviando botones a Instagram: {e}", exc_info=True)