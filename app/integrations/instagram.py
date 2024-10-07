# /home/amigro/app/integrations/instagram.py

import logging
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from app.chatbot import ChatBotHandler

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def instagram_webhook(request):
    """
    Webhook para manejar mensajes entrantes desde Instagram.
    """
    try:
        data = request.body.decode('utf-8')
        # Aquí puedes procesar el mensaje de Instagram
        logger.info(f"Mensaje recibido desde Instagram: {data}")
        
        # Ejemplo de interacción con el chatbot
        chatbot_handler = ChatBotHandler()
        response, options = chatbot_handler.process_message('instagram', data['sender']['id'], data['message']['text'])

        return JsonResponse({'status': 'success', 'response': response}, status=200)
    except Exception as e:
        logger.error(f"Error en el webhook de Instagram: {e}")
        return JsonResponse({'status': 'error', 'message': 'Error interno del servidor'}, status=500)

async def send_instagram_message(recipient_id, message, access_token):
    """
    Envía un mensaje a un usuario de Instagram.
    """
    url = f"https://graph.facebook.com/v11.0/me/messages"
    params = {"access_token": access_token}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message},
    }
    response = requests.post(url, json=data, params=params)
    if response.status_code != 200:
        logger.error(f"Error enviando mensaje a Instagram: {response.text}")
    else:
        logger.info(f"Mensaje enviado correctamente a Instagram: {message}")
