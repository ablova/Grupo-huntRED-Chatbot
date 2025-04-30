# /home/pablo/app/chatbot/integrations/instagram.py
import logging
import json
import httpx
import asyncio
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from asgiref.sync import sync_to_async
from app.models import InstagramAPI, MetaAPI, BusinessUnit, ChatState, Person
from app.chatbot.chatbot import ChatBotHandler
from typing import Optional, List, Dict, Any

logger = logging.getLogger('chatbot')


REQUEST_TIMEOUT = 10.0  # segundos
CACHE_TIMEOUT = 600  # 10 minutos

@csrf_exempt
async def instagram_webhook(request):
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
        
        payload = json.loads(request.body.decode("utf-8"))
        entry = payload.get("entry", [{}])[0]
        messaging = entry.get("messaging", [{}])[0]
        sender_id = messaging.get("sender", {}).get("id")
        message = messaging.get("message", {})
        
        instagram_api = await sync_to_async(InstagramAPI.objects.filter(is_active=True).first)()
        if not instagram_api:
            logger.error("No se encontró configuración de InstagramAPI activa")
            return JsonResponse({"status": "error", "message": "Configuración no encontrada"}, status=404)

        business_unit = await sync_to_async(lambda: instagram_api.business_unit)()
        chatbot = ChatBotHandler()

        text = message.get("text", "").strip()
        attachments = message.get("attachments", [])
        if attachments:
            attachment = attachments[0]
            if attachment["type"] == "file":
                message_dict = {
                    "messages": [{
                        "id": messaging.get("mid", ""),
                        "file_id": attachment["payload"]["url"],
                        "file_name": "document",
                        "mime_type": attachment.get("mime_type", "application/pdf")
                    }],
                    "chat": {"id": sender_id}
                }
                await chatbot.process_message(
                    platform="instagram",
                    user_id=sender_id,
                    message=message_dict,
                    business_unit=business_unit,
                    payload=payload
                )
                return JsonResponse({"status": "success"}, status=200)

        message_dict = {
            "messages": [{"id": messaging.get("mid", ""), "text": {"body": text}}],
            "chat": {"id": sender_id}
        }
        await chatbot.process_message(
            platform="instagram",
            user_id=sender_id,
            message=message_dict,
            business_unit=business_unit,
            payload=payload
        )
        return JsonResponse({"status": "success"}, status=200)
    except Exception as e:
        logger.error(f"Error en instagram_webhook: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
   
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

async def send_instagram_message(user_id, message, access_token):
    """Envía un mensaje a Instagram."""
    from app.chatbot.integrations.services import send_message  # 🔄 Import dentro de la función

    url = "https://graph.facebook.com/v22.0/me/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "recipient": {"id": user_id},
        "message": {"text": message}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()

    logger.info(f"✅ Mensaje enviado a {user_id} en Instagram.")

async def send_instagram_buttons(user_id: str, message: str, buttons: List[Dict], access_token: str) -> bool:
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
    logger.info(f"✅ Botones enviados a {user_id} en Instagram")
    return True

async def send_instagram_document(user_id: str, file_url: str, caption: str, api_instance: InstagramAPI) -> bool:
    try:
        url = f"https://graph.facebook.com/v22.0/me/messages"
        headers = {
            "Authorization": f"Bearer {api_instance.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "recipient": {"id": user_id},
            "message": {
                "attachment": {
                    "type": "file",
                    "payload": {"url": file_url}
                }
            }
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        logger.info(f"[send_instagram_document] Documento enviado a {user_id}")
        return True
    except Exception as e:
        logger.error(f"[send_instagram_document] Error: {e}")
        return False
 
async def fetch_instagram_user_data(user_id: str, api_instance: InstagramAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    try:
        if not isinstance(api_instance, InstagramAPI) or not hasattr(api_instance, 'access_token') or not api_instance.access_token:
            logger.error(f"api_instance no es válido, recibido: {type(api_instance)}")
            return {}
        url = f"https://graph.instagram.com/{user_id}"
        params = {
            "fields": "username,full_name",
            "access_token": api_instance.access_token
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                nombre = data.get('full_name', '').split(' ')[0]
                apellido = ' '.join(data.get('full_name', '').split(' ')[1:]) if len(data.get('full_name', '').split(' ')) > 1 else ''
                return {
                    'nombre': nombre,
                    'apellido_paterno': apellido,
                    'metadata': {'username': data.get('username', '')}
                }
            else:
                logger.error(f"Error fetching Instagram user data: {response.text}")
                return {}
    except Exception as e:
        logger.error(f"Exception in fetch_instagram_user_data: {e}", exc_info=True)
        return {}