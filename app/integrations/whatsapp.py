# /home/amigro/app/integrations/whatsapp.py

import logging
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from app.chatbot import ChatBotHandler

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_webhook(request):
    """
    Webhook para manejar mensajes entrantes desde WhatsApp.
    """
    try:
        data = request.body.decode('utf-8')
        # Aquí puedes procesar el mensaje de WhatsApp
        logger.info(f"Mensaje recibido desde WhatsApp: {data}")
        
        # Ejemplo de interacción con el chatbot
        chatbot_handler = ChatBotHandler()
        response, options = chatbot_handler.process_message('whatsapp', data['From'], data['Body'])

        return JsonResponse({'status': 'success', 'response': response}, status=200)
    except Exception as e:
        logger.error(f"Error en el webhook de WhatsApp: {e}")
        return JsonResponse({'status': 'error', 'message': 'Error interno del servidor'}, status=500)

async def send_whatsapp_message(recipient, message, api_token, phone_id, version_api):
    """
    Envía un mensaje a un usuario de WhatsApp utilizando la API.
    """
    url = f"https://graph.facebook.com/{version_api}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "text": {
            "body": message
        }
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200:
        logger.error(f"Error enviando mensaje a WhatsApp: {response.text}")
    else:
        logger.info(f"Mensaje enviado correctamente a WhatsApp: {message}")



async def invite_known_person(referrer, name, apellido, phone_number):
    """
    Función para invitar a un conocido por WhatsApp y crear un pre-registro del invitado.
    
    :param referrer: Usuario que realizó la invitación.
    :param name: Nombre del invitado.
    :param apellido: Apellido del invitado.
    :param phone_number: Número de contacto del invitado.
    """
    # Crear pre-registro del invitado
    invitado, created = await Person.objects.aget_or_create(phone=phone_number, defaults={
        'name': name,
        'apellido': apellido
    })
    
    # Crear el registro de la invitación
    await Invitacion.objects.acreate(referrer=referrer, invitado=invitado)

    # Enviar mensaje de invitación por WhatsApp
    if created:
        mensaje = f"Hola {name}, has sido invitado por {referrer.name} a unirte a Amigro.org. ¡Únete a nuestra comunidad!"
        await send_whatsapp_message(phone_number, mensaje)

    return invitado
