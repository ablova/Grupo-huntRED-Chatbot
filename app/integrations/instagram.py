# /home/amigro/app/integrations/instagram.py
import logging
import json
import httpx
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from app.models import InstagramAPI, MetaAPI
from app.integrations.services import send_message

logger = logging.getLogger('instagram')

@csrf_exempt
def instagram_webhook(request):
    if request.method == 'GET':
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        meta_api = MetaAPI.objects.first()
        expected_token = meta_api.verify_token if meta_api else 'amigro_secret_token'

        if verify_token == expected_token:
            return HttpResponse(challenge)
        else:
            return HttpResponse('Token de verificación inválido', status=403)

    elif request.method == 'POST':
        payload = json.loads(request.body.decode('utf-8'))
        logger.info(f"Payload recibido de Instagram: {payload}")

        try:
            for entry in payload.get('entry', []):
                for change in entry.get('changes', []):
                    messages = change.get('value', {}).get('messages', [])
                    for message in messages:
                        sender_id = message['from']
                        message_text = message.get('text', {}).get('body', '')
                        handle_message(sender_id, message_text, 'instagram')
            return HttpResponse(status=200)

        except Exception as e:
            logger.error(f"Error al manejar el webhook de Instagram: {e}", exc_info=True)
            return HttpResponse(status=500)

    return HttpResponse(status=405)

async def send_instagram_message(user_id, message, access_token):
    url = f"https://graph.facebook.com/v14.0/me/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "instagram",
        "recipient": {
            "id": user_id
        },
        "message": {
            "text": message
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Mensaje enviado a Instagram {user_id} correctamente.")
            return response.json()
    except Exception as e:
        logger.error(f"Error enviando mensaje en Instagram: {e}", exc_info=True)
        raise e
    
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
           response.raise_for_status()  # Verifica si hubo algún error
           logger.info(f"Botones enviados correctamente a Instagram. Respuesta: {response.text}")

   except httpx.HTTPStatusError as e:
       logger.error(f"Error enviando botones a Instagram: {e}")