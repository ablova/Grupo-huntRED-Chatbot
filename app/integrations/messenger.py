# /home/amigro/app/integrations/messenger.py

import logging
import json
import hashlib
import hmac
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from app.models import MessengerAPI, MetaAPI
from app.integrations.services import handle_message, send_options

logger = logging.getLogger('messenger')

@csrf_exempt
def messenger_webhook(request):
    if request.method == 'GET':
        # Verificación del webhook
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        meta_api = MetaAPI.objects.first()
        expected_token = meta_api.verify_token if meta_api else 'amigro_secret_token'

        if verify_token == expected_token:
            return HttpResponse(challenge)
        else:
            return HttpResponse('Token de verificación inválido', status=403)
    elif request.method == 'POST':
        # Verificar la firma de la solicitud
        x_hub_signature = request.headers.get('X-Hub-Signature')
        if not verify_request_signature(request.body, x_hub_signature):
            logger.warning("X-Hub-Signature inválida")
            return HttpResponse(status=403)
        # Manejar eventos entrantes del webhook
        try:
            payload = json.loads(request.body.decode('utf-8'))
            logger.info(f"Payload recibido de Messenger: {payload}")
            for entry in payload.get('entry', []):
                messaging_events = entry.get('messaging', [])
                for event in messaging_events:
                    sender_id = event['sender']['id']
                    if 'message' in event:
                        message_text = event['message'].get('text', '')
                        logger.info(f"Mensaje recibido de {sender_id}: {message_text}")
                        handle_message(sender_id, message_text, 'messenger')
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Error al manejar el webhook de Messenger: {e}", exc_info=True)
            return HttpResponse(status=500)
    else:
        logger.warning(f"Método no permitido: {request.method}")
        return HttpResponse(status=405)

def verify_request_signature(payload, x_hub_signature):
    meta_api = MetaAPI.objects.first()
    app_secret = meta_api.app_secret if meta_api else None
    if not app_secret:
        logger.error("App Secret no configurado")
        return False
    if not x_hub_signature:
        logger.error("X-Hub-Signature no proporcionado")
        return False
    expected_signature = 'sha1=' + hmac.new(
        key=app_secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha1
    ).hexdigest()
    return hmac.compare_digest(expected_signature, x_hub_signature)

def send_messenger_message(user_id, message_text, access_token):
    try:
        url = f"https://graph.facebook.com/v16.0/me/messages?access_token={access_token}"
        payload = {
            "recipient": {"id": user_id},
            "message": {"text": message_text}
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Mensaje enviado a usuario de Messenger {user_id}: {message_text}")
    except requests.RequestException as e:
        logger.error(f"Error enviando mensaje a Messenger: {e}")

def send_messenger_image(user_id, image_url, access_token):
    try:
        url = f"https://graph.facebook.com/v16.0/me/messages?access_token={access_token}"
        payload = {
            "recipient": {"id": user_id},
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {
                        "url": image_url,
                        "is_reusable": True
                    }
                }
            }
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Imagen enviada a usuario de Messenger {user_id}: {image_url}")
    except requests.RequestException as e:
        logger.error(f"Error enviando imagen a Messenger: {e}")

def send_messenger_quick_replies(user_id, message_text, quick_replies, access_token):
    try:
        url = f"https://graph.facebook.com/v16.0/me/messages?access_token={access_token}"
        payload = {
            "recipient": {"id": user_id},
            "message": {
                "text": message_text,
                "quick_replies": quick_replies
            }
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Mensaje con quick replies enviado a usuario de Messenger {user_id}: {message_text}")
    except requests.RequestException as e:
        logger.error(f"Error enviando quick replies a Messenger: {e}")
