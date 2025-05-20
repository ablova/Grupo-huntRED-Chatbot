# /home/pablo/app/com/chatbot/integrations/whatsapp.py
#
# Módulo para manejar la integración con WhatsApp Business API.
# Procesa mensajes entrantes, envía respuestas, y gestiona interacciones como botones y listas.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.
# Incluye soporte para carruseles de vacantes y manejo de documentos (CV).

import json
import logging
import asyncio
import httpx
import time
import os
from typing import Optional, Dict, Any, List
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.conf import settings
from asgiref.sync import sync_to_async
from tenacity import retry, stop_after_attempt, wait_exponential
from app.models import Person, BusinessUnit, WhatsAppAPI, ChatState
# Importaciones directas siguiendo estándares de Django
from app.com.chatbot.chat_state_manager import ChatStateManager
from app.com.chatbot.intents_handler import IntentProcessor
from app.com.chatbot.integrations.document_processor import DocumentProcessor

logger = logging.getLogger('chatbot')

# Configuraciones globales
REQUEST_TIMEOUT = 10.0
MAX_RETRIES = 3
CACHE_TIMEOUT = 600  # 10 minutos
whatsapp_semaphore = asyncio.Semaphore(10)

class WhatsAppHandler:
    """Handler for WhatsApp channel interactions with rate limiting and error handling."""
    def __init__(self, user_id: str, phone_number_id: str, business_unit: BusinessUnit):
        self.user_id = user_id
        self.phone_number_id = phone_number_id
        self.business_unit = business_unit
        self.user: Optional[Person] = None
        self.chat_manager = ChatStateManager()
        self.intent_processor = IntentProcessor()
        self.whatsapp_api: Optional[WhatsAppAPI] = None
        self.user_data: Dict[str, Any] = {}
        self.api_base_url = settings.WHATSAPP_API_URL
        self.api_token = settings.WHATSAPP_API_TOKEN
        
        # Importación a nivel de método para evitar dependencias circulares
        from app.com.chatbot.rate_limiter import RateLimiter
        self.rate_limiter = RateLimiter(requests_per_minute=settings.WHATSAPP_RATE_LIMIT)
        self.session = None
        logger.info("WhatsAppHandler initialized")

    async def initialize(self):
        """Initialize the aiohttp session for WhatsApp API calls."""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            })
            logger.info("WhatsAppHandler session initialized")
        return self.session

    async def fetch_whatsapp_user_data(self, user_id: str, api_instance: WhatsAppAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Obtiene datos del usuario desde el payload de WhatsApp."""
        try:
            if not isinstance(api_instance, WhatsAppAPI) or not api_instance.api_token:
                logger.error(f"api_instance no es válido: {type(api_instance)}")
                return {'nombre': '', 'apellido_paterno': '', 'metadata': {}, 'preferred_language': 'es_MX'}

            if not payload or 'entry' not in payload:
                logger.warning(f"Payload inválido para user_id: {user_id}")
                return {'nombre': '', 'apellido_paterno': '', 'metadata': {}, 'preferred_language': 'es_MX'}

            contacts = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("contacts", [])
            if not contacts:
                return {'nombre': '', 'apellido_paterno': '', 'metadata': {}, 'preferred_language': 'es_MX'}

            profile_name = contacts[0].get("profile", {}).get("name", "")
            nombre = profile_name.split(" ")[0] if profile_name else ""
            apellido = " ".join(profile_name.split(" ")[1:]) if len(profile_name.split(" ")) > 1 else ""
            return {
                'nombre': nombre,
                'apellido_paterno': apellido,
                'metadata': {'wa_id': user_id},
                'preferred_language': 'es_MX'
            }
        except Exception as e:
            logger.error(f"Error en fetch_whatsapp_user_data: {str(e)}")
            return {'nombre': '', 'apellido_paterno': '', 'metadata': {}, 'preferred_language': 'es_MX'}

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un mensaje de WhatsApp y genera una respuesta."""
        try:
            async with whatsapp_semaphore:
                # Extraer texto o contenido interactivo
                text = await self._extract_message_content(message)
                if await self._is_spam_message(text):
                    return {'response': "Por favor, no envíes mensajes repetidos o spam."}

                # Actualizar estado del chat
                await self.chat_manager.update_state('PROCESSING')

                # Procesar intent
                intent = await self.intent_processor.process(text)

                # Generar y enviar respuesta
                response = await self._generate_response(intent)
                if intent.get('smart_options'):
                    await self.send_whatsapp_buttons(
                        message.get('from', self.user_id),
                        response.get('response', ''),
                        intent['smart_options']
                    )
                elif intent.get('template_messages') and 'list' in intent['template_messages'][0].get('template_type', '').lower():
                    await self.send_whatsapp_list(
                        message.get('from', self.user_id),
                        response.get('response', ''),
                        intent['template_messages'][0].get('options', [])
                    )
                else:
                    await self._send_response(message.get('from', self.user_id), response)

                # Actualizar estado del chat
                await self.chat_manager.update_state('IDLE')
                return response
        except Exception as e:
            logger.error(f"Error procesando mensaje en WhatsApp: {str(e)}")
            return {'response': "Lo siento, hubo un error procesando tu mensaje."}

    async def _get_or_create_user(self) -> Person:
        """Obtiene o crea un usuario en la base de datos."""
        user, created = await Person.objects.aget_or_create(
            phone=self.user_id,
            defaults={'business_unit': self.business_unit, 'nombre': 'Nuevo Usuario'}
        )
        return user

    async def _update_user_profile(self) -> None:
        """Actualiza el perfil del usuario con datos extraídos."""
        if self.user_data.get('nombre') and not self.user.nombre:
            self.user.nombre = self.user_data['nombre']
        if self.user_data.get('apellido_paterno') and not self.user.apellido_paterno:
            self.user.apellido_paterno = self.user_data['apellido_paterno']
        if self.user_data.get('metadata'):
            self.user.metadata.update(self.user_data['metadata'])
        if self.user_data.get('preferred_language'):
            self.user.metadata['preferred_language'] = self.user_data['preferred_language']
        await self.user.asave()

    async def _extract_message_content(self, message: Dict[str, Any]) -> str:
        """Extrae el contenido del mensaje (texto o interactivo)."""
        text = message.get('text', {}).get('body', '').strip()
        if message.get('type') == 'interactive':
            interactive = message.get('interactive', {})
            if interactive.get('type') == 'button_reply':
                text = interactive.get('button_reply', {}).get('id', '')
            elif interactive.get('type') == 'list_reply':
                text = interactive.get('list_reply', {}).get('id', '')
        return text

    async def _is_spam_message(self, message: str) -> bool:
        """Verifica si un mensaje es spam (implementación pendiente)."""
        return False

    async def _generate_response(self, intent: Dict) -> Dict[str, Any]:
        """Genera una respuesta basada en el intent detectado."""
        return intent  # IntentProcessor ya devuelve response, smart_options, etc.

    async def _send_response(self, recipient_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message via WhatsApp with rate limiting."""
        try:
            await self.rate_limiter.acquire()
            await self.initialize()
            payload = {
                "to": recipient_id,
                "type": "text",
                "text": {
                    "body": response.get('response', '')
                }
            }
            async with self.session.post(f"{self.api_base_url}/messages", json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"WhatsApp message sent to {recipient_id}")
                    return result
                else:
                    error_text = await resp.text()
                    logger.error(f"Failed to send WhatsApp message to {recipient_id}: {resp.status} - {error_text}")
                    return {"error": f"HTTP {resp.status}", "details": error_text}
        except Exception as e:
            logger.error(f"Error sending WhatsApp message to {recipient_id}: {str(e)}", exc_info=True)
            return {"error": str(e)}
        finally:
            await self.rate_limiter.release()

    async def send_whatsapp_buttons(self, user_id: str, message: str, buttons: List[Dict]) -> bool:
        """Envía un mensaje con botones interactivos (máximo 3)."""
        try:
            await self.rate_limiter.acquire()
            await self.initialize()
            formatted_buttons = [
                {"type": "reply", "reply": {"id": btn["payload"], "title": btn["title"][:20]}}
                for btn in buttons[:3]
            ]
            payload = {
                "to": user_id,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": message},
                    "action": {"buttons": formatted_buttons}
                }
            }
            async with self.session.post(f"{self.api_base_url}/messages", json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"WhatsApp buttons sent to {user_id}")
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f"Failed to send WhatsApp buttons to {user_id}: {resp.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp buttons to {user_id}: {str(e)}", exc_info=True)
            return False
        finally:
            await self.rate_limiter.release()

    async def send_whatsapp_list(self, user_id: str, message: str, options: List[Dict]) -> bool:
        """Envía una lista interactiva (hasta 10 opciones)."""
        try:
            await self.rate_limiter.acquire()
            await self.initialize()
            sections = [{
                "title": "Opciones",
                "rows": [
                    {"id": opt["payload"], "title": opt["title"][:24]}
                    for opt in options[:10]
                ]
            }]
            payload = {
                "to": user_id,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "header": {"type": "text", "text": "Menú Principal"},
                    "body": {"text": message},
                    "footer": {"text": "Selecciona una opción"},
                    "action": {
                        "button": "Seleccionar",
                        "sections": sections
                    }
                }
            }
            async with self.session.post(f"{self.api_base_url}/messages", json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"WhatsApp list sent to {user_id}")
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f"Failed to send WhatsApp list to {user_id}: {resp.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp list to {user_id}: {str(e)}", exc_info=True)
            return False
        finally:
            await self.rate_limiter.release()
            
    async def send_vacancy_carousel(self, user_id: str, vacancies: List[Dict]) -> bool:
        """
        Envía un conjunto de vacantes en formato visual atractivo.
        Simula un carrusel con mensajes secuenciales enriquecidos.
        """
        try:
            await self.initialize()
            success_count = 0
            
            # Mensaje introductorio
            intro_text = "*Vacantes que coinciden con tu perfil* 📋\n\nRevisa las siguientes oportunidades:\n"
            await self.send_text_message(user_id, intro_text)
            await asyncio.sleep(0.5)  # Breve pausa para separar mensajes
            
            # Limitamos a 5 vacantes para evitar spam
            for vacancy in vacancies[:5]:  
                await self.rate_limiter.acquire()
                
                # Preparamos los botones para cada vacante
                buttons = [
                    {"title": "Ver Detalles", "payload": f"view_vacancy_{vacancy['id']}"},
                    {"title": "Postularme", "payload": f"apply_vacancy_{vacancy['id']}"},
                    {"title": "Guardar", "payload": f"save_vacancy_{vacancy['id']}"}
                ]
                
                # Formateamos el mensaje de la vacante
                vacancy_message = (
                    f"*{vacancy['title']}*\n\n"
                    f"🏢 *Empresa:* {vacancy.get('company', 'Confidencial')}\n"
                    f"📍 *Ubicación:* {vacancy.get('location', 'No especificada')}\n"
                    f"💰 *Salario:* {vacancy.get('salary_range', 'A convenir')}\n\n"
                    f"{vacancy.get('short_description', '')[:150]}..."
                )
                
                # Enviamos mensaje con botones
                sent = await self.send_whatsapp_buttons(user_id, vacancy_message, buttons)
                if sent:
                    success_count += 1
                    await asyncio.sleep(0.8)  # Pausa para simular efecto carrusel
                await self.rate_limiter.release()
            
            # Mensaje final con CTA si enviamos al menos una vacante
            if success_count > 0:
                more_options = [
                    {"title": "Ver Más Vacantes", "payload": "more_vacancies"},
                    {"title": "Filtrar Resultados", "payload": "filter_vacancies"},
                    {"title": "Actualizar CV", "payload": "update_cv"}
                ]
                await self.send_whatsapp_buttons(
                    user_id, 
                    "¿Qué te gustaría hacer ahora?", 
                    more_options
                )
            
            return success_count > 0
        except Exception as e:
            logger.error(f"Error enviando carrusel de vacantes: {str(e)}", exc_info=True)
            return False
    
    async def send_text_message(self, user_id: str, message: str) -> bool:
        """
        Envía un mensaje de texto simple a un usuario de WhatsApp.
        """
        try:
            await self.rate_limiter.acquire()
            await self.initialize()
            
            payload = {
                "to": user_id,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            async with self.session.post(f"{self.api_base_url}/messages", json=payload) as resp:
                if resp.status == 200:
                    logger.info(f"Text message sent to {user_id}")
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f"Failed to send text message to {user_id}: {resp.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending text message: {str(e)}", exc_info=True)
            return False
        finally:
            await self.rate_limiter.release()
    
    async def handle_document(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un documento adjunto recibido vía WhatsApp (CV u otros).
        """
        try:
            document = message.get('document', {})
            if not document:
                return {"success": False, "error": "No document found in message"}
                
            document_id = document.get('id')
            mime_type = document.get('mime_type', '')
            filename = document.get('filename', f"doc_{int(time.time())}.pdf")
            
            # Verificamos si el documento es un tipo soportado
            supported_types = [
                'application/pdf', 
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            
            if mime_type not in supported_types:
                await self.send_text_message(
                    self.user_id,
                    "Lo siento, solo puedo procesar documentos en formato PDF o Word (.docx/.doc). Por favor, envía tu archivo en alguno de estos formatos."
                )
                return {"success": False, "error": "Unsupported document type"}
            
            # Descargamos el documento
            file_data = await self._download_media(document_id)
            if not file_data:
                return {"success": False, "error": "Failed to download document"}
            
            # Procesamos el documento usando el DocumentProcessor
            processor = DocumentProcessor(self.user_id, self.business_unit.id if self.business_unit else None)
            result = await processor.process_document(file_data, filename, mime_type)
            
            # Si es un CV procesado correctamente, enviamos feedback al usuario
            if result.get("success") and result.get("processed") and result.get("cv_data"):
                await self._send_cv_confirmation(result["cv_data"])
                
            return result
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            await self.send_text_message(
                self.user_id,
                "Lo siento, ocurrió un error al procesar tu documento. Por favor, intenta nuevamente más tarde."
            )
            return {"success": False, "error": str(e)}
    
    async def _download_media(self, media_id: str) -> Optional[bytes]:
        """
        Descarga un archivo multimedia desde la API de WhatsApp.
        """
        try:
            # Primero obtenemos la URL del medio
            media_url = await self._get_media_url(media_id)
            if not media_url:
                return None
                
            # Descargamos el contenido del archivo
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.api_token}"}
                response = await client.get(media_url, headers=headers)
                
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"Error downloading media: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error downloading media: {str(e)}", exc_info=True)
            return None
    
    async def _get_media_url(self, media_id: str) -> Optional[str]:
        """
        Obtiene la URL para descargar un archivo multimedia.
        """
        try:
            await self.initialize()
            async with self.session.get(f"{self.api_base_url}/{media_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('url')
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get media URL: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"Error getting media URL: {str(e)}", exc_info=True)
            return None
    
    async def _send_cv_confirmation(self, cv_data: Dict[str, Any]) -> bool:
        """
        Envía confirmación de recepción de CV con datos extraídos.
        """
        try:
            # Lista de habilidades detectadas
            skills_text = "\n"
            if cv_data.get('skills'):
                for skill in cv_data.get('skills', [])[:5]:
                    skills_text += f"• {skill}\n"
            else:
                skills_text = "No se detectaron habilidades específicas\n"
            
            # Mensaje de confirmación
            message = (
                f"✅ *CV Recibido Correctamente*\n\n"
                f"He extraído la siguiente información de tu documento:\n\n"
                f"👤 *Nombre:* {cv_data.get('nombre', 'No detectado')}\n"
                f"📧 *Email:* {cv_data.get('email', 'No detectado')}\n"
                f"📞 *Teléfono:* {cv_data.get('telefono', 'No detectado')}\n"
                f"🎓 *Nivel de estudios:* {cv_data.get('nivel_estudios', 'No detectado')}\n\n"
                f"*Habilidades detectadas:*{skills_text}\n"
                f"¿Es correcta esta información?"
            )
            
            # Botones de confirmación
            buttons = [
                {"title": "✅ Sí, es correcta", "payload": "cv_data_confirm"},
                {"title": "❌ No, actualizar", "payload": "cv_data_update"}
            ]
            
            # Enviar mensaje con opciones
            return await self.send_whatsapp_buttons(self.user_id, message, buttons)
            
        except Exception as e:
            logger.error(f"Error sending CV confirmation: {str(e)}", exc_info=True)
            return False

@csrf_exempt
async def whatsapp_webhook(request):
    """Webhook para procesar mensajes entrantes de WhatsApp."""
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode("utf-8"))
        entry = payload.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        if not messages:
            return JsonResponse({"status": "success", "message": "No messages to process"}, status=200)

        message = messages[0]
        user_id = message.get('from')
        phone_number_id = value.get('metadata', {}).get('phone_number_id')
        business_unit = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
            phoneID=phone_number_id, is_active=True
        ).first().business_unit)()

        handler = WhatsAppHandler(user_id, phone_number_id, business_unit)
        await handler.initialize()
        response = await handler.handle_message(message)
        return JsonResponse({"status": "success", "response": response}, status=200)
    except Exception as e:
        logger.error(f"Error en whatsapp_webhook: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)