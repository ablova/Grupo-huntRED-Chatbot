# /home/amigro/app/integrations/messenger.py
import logging
import json
import requests
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from app.models import MessengerAPI, MetaAPI
from app.integrations.services import send_message
from app.chatbot import ChatBotHandler
#from app.views import process_message

logger = logging.getLogger('messenger')

@csrf_exempt
def messenger_webhook(request):
    if request.method == 'GET':
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        meta_api = MetaAPI.objects.first()
        expected_token = meta_api.verify_token if meta_api else 'amigro_secret_token'

        if verify_token == expected_token:
            return HttpResponse(challenge)
        else:
            return HttpResponse('Token de verificación inválido', status=403)

    elif request.method == 'POST':  # <-- Indentación corregida aquí
        try:
            payload = json.loads(request.body.decode('utf-8'))
            logger.info(f"Payload recibido de Messenger: {payload}")

            # Procesar los mensajes recibidos
            for entry in payload.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    for message in messages:
                        sender_id = message['from']
                        message_text = message['text']['body']
                        logger.info(f"Mensaje recibido de {sender_id}: {message_text}")

                         # Proceso el mensaje con el ChatBotHandler
                        chatbot_handler = ChatBotHandler()
                        response_text, options = chatbot_handler.process_message('messenger', sender_id, message_text)

                        # Enviar la respuesta a Messenger
                        send_message('messenger', sender_id, response_text)
                        # Enviamos el mensaje para ser procesado en views.py y por chatbot.py
                        #response = process_message('messenger', sender_id, message_text, 'yes')

            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Error al manejar el webhook de Messenger: {e}", exc_info=True)
            return HttpResponse(status=500)
    else:
        return HttpResponse(status=405)


def send_messenger_message(user_id, message_text, access_token):
    try:
        url = f"https://graph.facebook.com/v16.0/me/messages?access_token={access_token}"
        payload = {
            "recipient": {"id": user_id},
            "message": {"text": message_text}
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Mensaje enviado a Messenger {user_id}: {message_text}")

    except requests.RequestException as e:
        logger.error(f"Error enviando mensaje a Messenger: {e}")
