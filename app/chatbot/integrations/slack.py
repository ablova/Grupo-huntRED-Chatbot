import logging
import json
import httpx
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from app.models import SlackAPI, BusinessUnit
from app.chatbot.chatbot import ChatBotHandler

logger = logging.getLogger('chatbot')

async def send_slack_message(channel_id: str, message: str, bot_token: str) -> bool:
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

@csrf_exempt
async def slack_webhook(request):
    """Webhook de Slack para recibir eventos y procesar mensajes."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        event_type = payload.get("type")

        if event_type == "url_verification":
            return JsonResponse({"challenge": payload["challenge"]}, status=200)

        if event_type == "event_callback":
            event = payload["event"]
            if event["type"] == "message" and "bot_id" not in event:
                channel_id = event["channel"]
                text = event["text"]
                business_unit_id = request.headers.get("X-Business-Unit-ID")

                if not business_unit_id:
                    return JsonResponse({"status": "error", "message": "Business Unit ID no proporcionado"}, status=400)

                business_unit = await sync_to_async(BusinessUnit.objects.get)(id=business_unit_id)
                slack_api = await sync_to_async(SlackAPI.objects.get)(business_unit=business_unit, is_active=True)

                chatbot = ChatBotHandler()
                response_text = await chatbot.process_message(
                    platform="slack",
                    user_id=channel_id,
                    text=text,
                    business_unit=business_unit
                )

                await send_slack_message(
                    channel_id=channel_id,
                    message=response_text,
                    bot_token=slack_api.bot_token
                )
                return JsonResponse({"status": "success"}, status=200)

        return JsonResponse({"status": "ignored"}, status=200)
    except Exception as e:
        logger.error(f"❌ Error en webhook de Slack: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": "Error interno del servidor"}, status=500)
    
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