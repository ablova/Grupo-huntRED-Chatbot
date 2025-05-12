# /home/pablo/app/com/chatbot/integrations/slack.py
#
# Módulo para manejar la integración con Slack API.
# Procesa mensajes entrantes, envía respuestas, y gestiona interacciones como botones y archivos.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

import logging
import json
import httpx
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from app.models import SlackAPI, BusinessUnit
from app.com.chatbot.chatbot import ChatBotHandler
from app.com.chatbot.channel_config import RateLimiter

logger = logging.getLogger('chatbot')

 
@csrf_exempt
async def slack_webhook(request):
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
        
        payload = json.loads(request.body.decode("utf-8"))
        event = payload.get("event", {})
        user_id = event.get("user")
        channel = event.get("channel")
        text = event.get("text", "").strip()
        files = event.get("files", [])

        slack_api = await sync_to_async(SlackAPI.objects.filter(is_active=True).first)()
        if not slack_api:
            logger.error("No se encontró configuración de SlackAPI activa")
            return JsonResponse({"status": "error", "message": "Configuración no encontrada"}, status=404)

        business_unit = await sync_to_async(lambda: slack_api.business_unit)()
        chatbot = ChatBotHandler()

        if files:
            file = files[0]
            message_dict = {
                "messages": [{
                    "id": event.get("ts", ""),
                    "file_id": file["url_private"],
                    "file_name": file["name"],
                    "mime_type": file["mimetype"]
                }],
                "chat": {"id": channel}
            }
            await chatbot.process_message(
                platform="slack",
                user_id=user_id,
                message=message_dict,
                business_unit=business_unit,
                payload=payload
            )
            return JsonResponse({"status": "success"}, status=200)

        message_dict = {
            "messages": [{"id": event.get("ts", ""), "text": {"body": text}}],
            "chat": {"id": channel}
        }
        await chatbot.process_message(
            platform="slack",
            user_id=user_id,
            message=message_dict,
            business_unit=business_unit,
            payload=payload
        )
        return JsonResponse({"status": "success"}, status=200)
    except Exception as e:
        logger.error(f"Error en slack_webhook: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

async def send_slack_message(channel_id: str, message: str, bot_token: str) -> bool:
    """Envía un mensaje de texto a un canal de Slack con rate limiting."""
    rate_limiter = RateLimiter()
    await rate_limiter.wait_for_limit('slack')
    """Envía un mensaje de texto a un canal de Slack."""
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": channel_id,
        "text": message
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        logger.info(f"✅ Mensaje enviado a {channel_id} en Slack: {message}")
        return True
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Error HTTP {e.response.status_code}: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Slack: {e}", exc_info=True)
        return False

async def send_slack_message_with_buttons(channel_id: str, message: str, buttons: List[Dict], bot_token: str) -> bool:
    """Envía un mensaje con botones a Slack con rate limiting."""
    rate_limiter = RateLimiter()
    await rate_limiter.wait_for_limit('slack')
    """Envía un mensaje con botones a Slack."""
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json"
    }
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": btn["text"]["text"] if isinstance(btn.get("text"), dict) else btn["text"]
                    },
                    "value": btn["value"]
                } for btn in buttons
            ]
        }
    ]
    payload = {
        "channel": channel_id,
        "blocks": blocks
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        logger.info(f"✅ Mensaje con botones enviado a {channel_id} en Slack")
        return True
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Error HTTP {e.response.status_code}: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje con botones a Slack: {e}", exc_info=True)
        return False

async def send_slack_document(channel_id: str, file_url: str, caption: str, bot_token: str) -> bool:
    """Envía un documento a Slack con rate limiting."""
    rate_limiter = RateLimiter()
    await rate_limiter.wait_for_limit('slack')
    try:
        url = "https://slack.com/api/files.upload"
        headers = {"Authorization": f"Bearer {bot_token}"}
        payload = {
            "channels": channel_id,
            "content": caption,
            "file": file_url,
            "filename": "document"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, data=payload)
            response.raise_for_status()
        logger.info(f"[send_slack_document] Documento enviado a {channel_id}")
        return True
    except Exception as e:
        logger.error(f"[send_slack_document] Error: {e}")
        return False
 
async def fetch_slack_user_data(user_id: str, api_instance: SlackAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    try:
        if not isinstance(api_instance, SlackAPI) or not hasattr(api_instance, 'bot_token') or not api_instance.bot_token:
            logger.error(f"api_instance no es válido, recibido: {type(api_instance)}")
            return {}
        url = "https://slack.com/api/users.info"
        headers = {"Authorization": f"Bearer {api_instance.bot_token}"}
        params = {"user": user_id}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json().get("user", {})
                nombre = data.get("real_name", "").split(" ")[0]
                apellido = " ".join(data.get("real_name", "").split(" ")[1:]) if len(data.get("real_name", "").split(" ")) > 1 else ""
                return {
                    'nombre': nombre,
                    'apellido_paterno': apellido,
                    'metadata': {
                        'username': data.get("name", ""),
                        'email': data.get("profile", {}).get("email", "")
                    }
                }
            else:
                logger.error(f"Error fetching Slack user data: {response.text}")
                return {}
    except Exception as e:
        logger.error(f"Exception in fetch_slack_user_data: {e}", exc_info=True)
        return {}