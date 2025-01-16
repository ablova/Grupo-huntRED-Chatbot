# /home/pablollh/app/chatbot/integrations/whatsapp.py

import requests
import logging
import httpx
from typing import Optional, List
from asgiref.sync import sync_to_async
from urllib.parse import quote
from app.chatbot.utils import validate_message_format
from app.chatbot.services import generate_auto_response
from app.chatbot.gpt import GPTHandler
from app.chatbot.nlp import process_text
from app.chatbot.webhook_views import handle_webhook_event
from app.chatbot.webhook_urls import WHATSAPP_WEBHOOK_URL

logger = logging.getLogger(__name__)

# Configuración base
def build_whatsapp_url(phone_id: str, api_version: str = "v21.0", endpoint: str = "messages") -> str:
    """
    Construye la URL base para la API de WhatsApp con la versión configurada.
    """
    return f"https://graph.facebook.com/{api_version}/{phone_id}/{endpoint}"

def check_api_status(phone_id: str, token: str) -> bool:
    """
    Verifica el estado de la API de WhatsApp.
    """
    try:
        url = build_whatsapp_url(phone_id, endpoint="")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            logger.info("La API de WhatsApp está operativa.")
            return True
        logger.error(f"Error al verificar API: {response.status_code} - {response.json()}")
        return False
    except Exception as e:
        logger.error(f"Excepción al verificar API: {str(e)}")
        return False

def get_business_unit_from_phone(phone_id: str) -> Optional["WhatsAppAPI"]:
    """
    Busca el Business Unit asociado a un phoneID.
    """
    try:
        whatsapp_api = WhatsAppAPI.objects.filter(phoneID=phone_id, is_active=True).first()
        if whatsapp_api:
            return whatsapp_api.business_unit
        logger.warning(f"No se encontró un Business Unit para phoneID={phone_id}. Usando predeterminado.")
        return WhatsAppAPI.objects.filter(business_unit_id=4, is_active=True).first()  # Amigro por defecto
    except Exception as e:
        logger.error(f"Error al obtener el Business Unit: {str(e)}")
        return None

def generate_whatsapp_link(phone_number: str, text: str = "Deja que te ayudemos a encontrar el trabajo de tus sueños") -> str:
    """
    Genera un enlace de WhatsApp para invitar a los usuarios a iniciar una conversación.
    """
    base_url = "https://wa.me"
    encoded_text = quote(text)
    return f"{base_url}/{phone_number}?text={encoded_text}"

async def send_whatsapp_message(
    user_id: str,
    message: str,
    buttons: Optional[List[dict]] = None,
    phone_id: Optional[str] = None,
    business_unit=None
):
    """
    Envía un mensaje directo a un usuario de WhatsApp, soportando botones y configuraciones dinámicas.
    """
    try:
        # Obtener configuración
        whatsapp_api = None
        if business_unit:
            whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(
                phoneID=phone_id or None,
                business_unit=business_unit,
                is_active=True
            ).select_related('business_unit').first)()
        if not whatsapp_api and phone_id:
            whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(
                phoneID=phone_id,
                is_active=True
            ).select_related('business_unit').first)()

        if not whatsapp_api:
            logger.error("No se encontró una configuración activa de WhatsAppAPI.")
            return

        phone_id = whatsapp_api.phoneID
        api_token = whatsapp_api.api_token
        api_version = whatsapp_api.v_api or "v21.0"

        if not check_api_status(phone_id, api_token):
            logger.warning("La API de WhatsApp no está disponible actualmente.")
            return

        # Construir URL
        url = build_whatsapp_url(phone_id, api_version)

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        # Construcción del payload
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "text",
            "text": {
                "body": message
            }
        }

        # Convertir a interactivo si hay botones
        if buttons:
            payload["type"] = "interactive"
            payload["interactive"] = {
                "type": "button",
                "body": {"text": message},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": btn["payload"], "title": btn["title"][:20]}}
                        for btn in buttons
                    ]
                }
            }

        # Enviar mensaje
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Mensaje enviado exitosamente: {response.text}")
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"Error HTTP al enviar mensaje: {e.response.text}")
    except Exception as e:
        logger.error(f"Error general: {str(e)}")

# Webhook handler
def handle_whatsapp_webhook(event):
    """
    Procesa eventos del webhook de WhatsApp.
    """
    try:
        logger.debug(f"Evento recibido: {event}")
        # Lógica para procesar mensajes entrantes
        user_message = process_text(event.get("message"))
        gpt_response = GPTHandler.generate_response(user_message)
        generate_auto_response(event.get("user_id"), gpt_response)

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        return {"status": "error", "message": str(e)}