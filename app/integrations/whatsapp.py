# /home/amigro/app/integrations/whatsapp.py

import logging
import json
import hashlib
import hmac
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from app.models import WhatsAppAPI, MetaAPI
from app.integrations.services import handle_message, send_options

logger = logging.getLogger('whatsapp')

@csrf_exempt
def whatsapp_webhook(request, token):
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
        x_hub_signature = request.headers.get('X-Hub-Signature-256')
        if not verify_request_signature(request.body, x_hub_signature):
            logger.warning("X-Hub-Signature-256 inválida")
            return HttpResponse(status=403)
        # Manejar eventos entrantes del webhook
        try:
            payload = json.loads(request.body.decode('utf-8'))
            logger.info(f"Payload recibido de WhatsApp: {payload}")
            for entry in payload.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    for message in messages:
                        sender_id = message['from']
                        message_text = message['text']['body']
                        logger.info(f"Mensaje recibido de {sender_id}: {message_text}")
                        handle_message(sender_id, message_text, 'whatsapp')
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Error al manejar el webhook de WhatsApp: {e}", exc_info=True)
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
        logger.error("X-Hub-Signature-256 no proporcionado")
        return False
    expected_signature = 'sha256=' + hmac.new(
        key=app_secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, x_hub_signature)

def send_whatsapp_message(to_number, message_text, access_token, phone_number_id, v_api):
    try:
        url = f"https://graph.facebook.com/{v_api}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message_text}
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Mensaje enviado a usuario de WhatsApp {to_number}: {message_text}")
    except requests.RequestException as e:
        logger.error(f"Error enviando mensaje a WhatsApp: {e}")

def send_whatsapp_buttons(to_number, message_text, buttons, access_token, phone_number_id, v_api):
    try:
        url = f"https://graph.facebook.com/{v_api}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": message_text
                },
                "action": {
                    "buttons": buttons
                }
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Botones enviados a usuario de WhatsApp {to_number}")
    except requests.RequestException as e:
        logger.error(f"Error enviando botones a WhatsApp: {e}")
