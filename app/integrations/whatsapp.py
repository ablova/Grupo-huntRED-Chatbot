# /home/amigro/app/integrations/whatsapp.py
import logging
import json
import hashlib
import hmac
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from app.models import WhatsAppAPI, MetaAPI
from app.chatbot import ChatBotHandler
from app.integrations.services import send_message
from app.views import process_message  # Aseguramos que este importe funcione bien

logger = logging.getLogger('whatsapp')

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'GET':
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        meta_api = MetaAPI.objects.first()
        expected_token = meta_api.verify_token if meta_api else 'amigro_secret_token'

        if verify_token == expected_token:
            return HttpResponse(challenge)
        else:
            return HttpResponse('Token de verificación inválido', status=403)

    # Recepción de mensajes
    elif request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
            logger.info(f"Payload recibido de WhatsApp: {payload}")

            # Procesar los mensajes recibidos
            for entry in payload.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    for message in messages:
                        sender_id = message['from']
                        message_text = message['text']['body']
                        logger.info(f"Mensaje recibido de {sender_id}: {message_text}")

                        #Proceso el mensaje con el ChatbotHandler
                        chatbot_handler = ChatBotHandler()
                        response_text, options = chatbot_handler.process_message('whatsapp', sender_id, message_text)
                        #Enviar el mensaje de respuesta a Whatsapp
                        send_message('whatsapp', sender_id, response_text)
                        # Enviar el mensaje para ser procesado en views.py y por el chatbot
                        #response = process_message('whatsapp', sender_id, message_text, 'yes')

            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Error al manejar el webhook de WhatsApp: {e}", exc_info=True)
            return HttpResponse(status=500)
    else:
        return HttpResponse(status=405)

def send_whatsapp_message(to_number, message_text, access_token, phone_number_id, v_api):
    """
    Función para enviar mensajes a través de la API de WhatsApp.
    """
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

async def invite_known_person(referrer, name, apellido, phone_number):
    """
    Invita a un conocido por WhatsApp y crea un pre-registro del invitado.

    :param referrer: Usuario que realizó la invitación.
    :param name: Nombre del invitado.
    :param apellido: Apellido del invitado.
    :param phone_number: Número de contacto del invitado.
    """
    try:
        # Crear pre-registro del invitado
        invitado, created = await Person.objects.aupdate_or_create(
            telefono=phone_number,
            defaults={
                'nombre': name,
                'apellido_paterno': apellido
            }
        )

        # Crear el registro de la invitación
        await Invitacion.objects.acreate(referrer=referrer, invitado=invitado)

        # Enviar mensaje de invitación por WhatsApp
        if created:
            mensaje = f"Hola {name}, has sido invitado por {referrer.nombre} a unirte a Amigro.org. ¡Únete a nuestra comunidad!"
            await send_whatsapp_message(phone_number, mensaje, referrer.api_token, referrer.phoneID, referrer.v_api)

        return invitado
    except Exception as e:
        logger.error(f"Error al invitar a {name} por WhatsApp: {e}")

async def registro_amigro(recipient, access_token, phone_id, version_api, form_data):
    """
    Envía un mensaje de registro personalizado a un nuevo usuario con los datos capturados.
    """
    try:
        url = f"https://graph.facebook.com/{version_api}/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Se puede agregar lógica para personalizar el mensaje según los datos recibidos
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": "registro_amigro",
                "language": {"code": "es_MX"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": form_data.get("nombre", "Usuario")},
                            {"type": "text", "text": form_data.get("apellido_paterno", "")}
                        ]
                    }
                ]
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        logger.info(f"Plantilla de registro enviada correctamente a {recipient}")

    except Exception as e:
        logger.error(f"Error enviando plantilla de registro: {e}")
