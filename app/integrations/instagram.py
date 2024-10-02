# /home/amigro/app/integrations/instagram.py

import logging
import json
import hashlib
import hmac
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from app.models import InstagramAPI, MetaAPI
from app.integrations.services import handle_message

logger = logging.getLogger('instagram')


@csrf_exempt
@require_http_methods(["GET", "POST"])
def instagram_webhook(request):
    """
    Maneja las solicitudes de webhook de Instagram.
    """
    if request.method == 'GET':
        return handle_verification(request)
    elif request.method == 'POST':
        return handle_incoming_message(request)
    else:
        logger.warning(f"Método no permitido: {request.method}")
        return HttpResponse(status=405)


def handle_verification(request):
    """
    Maneja la verificación del webhook de Instagram.
    """
    verify_token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')

    meta_api = MetaAPI.objects.first()
    expected_token = meta_api.verify_token if meta_api else 'amigro_secret_token'

    if verify_token == expected_token:
        logger.info("Webhook de Instagram verificado correctamente.")
        return HttpResponse(challenge)
    else:
        logger.error("Token de verificación inválido para Instagram.")
        return HttpResponse('Token de verificación inválido', status=403)


def handle_incoming_message(request):
    """
    Maneja los mensajes entrantes del webhook de Instagram.
    """
    x_hub_signature = request.headers.get('X-Hub-Signature-256')
    if not verify_request_signature(request.body, x_hub_signature):
        logger.warning("Firma de solicitud inválida para Instagram.")
        return HttpResponse(status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        logger.info(f"Payload recibido de Instagram: {payload}")

        for entry in payload.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                messages = value.get('messages', [])
                for message in messages:
                    sender_id = message['from']
                    message_text = message.get('text', {}).get('body', '')
                    logger.info(f"Mensaje recibido de {sender_id}: {message_text}")

                    # Procesar el mensaje usando services.py
                    handle_message(sender_id, message_text, 'instagram')

        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Error al manejar el webhook de Instagram: {e}", exc_info=True)
        return HttpResponse(status=500)


def verify_request_signature(payload, x_hub_signature):
    """
    Verifica la firma de la solicitud para asegurar que proviene de Instagram.
    """
    meta_api = MetaAPI.objects.first()
    app_secret = meta_api.app_secret if meta_api else None

    if not app_secret:
        logger.error("App Secret no configurado en MetaAPI.")
        return False

    if not x_hub_signature:
        logger.error("X-Hub-Signature-256 no proporcionado en la solicitud.")
        return False

    # Crear la firma esperada
    expected_signature = 'sha256=' + hmac.new(
        key=app_secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    # Comparar de forma segura
    if hmac.compare_digest(expected_signature, x_hub_signature):
        return True
    else:
        logger.error("La firma de la solicitud no coincide.")
        return False


def send_instagram_message(user_id, message_text, access_token):
    """
    Envía un mensaje de texto a un usuario de Instagram.
    """
    try:
        url = f"https://graph.facebook.com/v16.0/me/messages?access_token={access_token}"
        payload = {
            "recipient": {"id": user_id},
            "message": {"text": message_text}
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Mensaje enviado a usuario de Instagram {user_id}: {message_text}")
    except requests.RequestException as e:
        logger.error(f"Error enviando mensaje a Instagram: {e}")


def send_instagram_image(user_id, image_url, access_token):
    """
    Envía una imagen a un usuario de Instagram.
    """
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
        logger.info(f"Imagen enviada a usuario de Instagram {user_id}: {image_url}")
    except requests.RequestException as e:
        logger.error(f"Error enviando imagen a Instagram: {e}")


def send_instagram_quick_replies(user_id, message_text, quick_replies, access_token):
    """
    Envía un mensaje con respuestas rápidas (Quick Replies) a un usuario de Instagram.
    Nota: La API de Instagram puede tener limitaciones en comparación con Messenger.
    """
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
        logger.info(f"Quick Replies enviados a usuario de Instagram {user_id}: {message_text}")
    except requests.RequestException as e:
        logger.error(f"Error enviando Quick Replies a Instagram: {e}")


def send_instagram_buttons(user_id, message_text, buttons, access_token):
    """
    Envía botones interactivos a un usuario de Instagram.
    Nota: Asegúrate de que la API de Instagram soporte este tipo de mensajes.
    """
    try:
        url = f"https://graph.facebook.com/v16.0/me/messages?access_token={access_token}"
        payload = {
            "recipient": {"id": user_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": message_text,
                        "buttons": buttons
                    }
                }
            }
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Botones enviados a usuario de Instagram {user_id}: {message_text}")
    except requests.RequestException as e:
        logger.error(f"Error enviando botones a Instagram: {e}")
