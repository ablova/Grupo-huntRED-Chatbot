# /home/pablo/app/ats/chatbot/integrations/telegram.py
#
# Módulo para manejar la integración con Telegram Bot API.
# Procesa mensajes entrantes, envía respuestas, y gestiona interacciones como botones.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.
# Incluye soporte para Mini-Apps y manejo de documentos multimedia (CV).

import json
import logging
import httpx
import asyncio
import time
import hmac
import hashlib
import os
from functools import partial
from django.conf import settings
from typing import Optional, Dict, Any, List, Tuple, Callable
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.cache import cache
from asgiref.sync import sync_to_async
from tenacity import retry, stop_after_attempt, wait_exponential
from app.models import Person, BusinessUnit, TelegramAPI
from app.ats.chatbot.components.rate_limiter import RateLimiter
from app.ats.chatbot.integrations.enhanced_document_processor import EnhancedDocumentProcessor as DocumentProcessor
from app.ats.chatbot.integrations.message_sender import (
    send_message, 
    send_options, 
    send_smart_options,
    send_image
)

logger = logging.getLogger('chatbot')

# Configuraciones globales
REQUEST_TIMEOUT = 10.0
MAX_RETRIES = 3
CACHE_TIMEOUT = 600

async def fetch_telegram_user_data(user_id: str, api_instance: TelegramAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Obtiene datos del usuario desde la API de Telegram."""
    try:
        if not isinstance(api_instance, TelegramAPI) or not api_instance.api_key:
            logger.error(f"api_instance no es válido: {type(api_instance)}")
            return {}

        url = f"https://api.telegram.org/bot{api_instance.api_key}/getChat"
        params = {"chat_id": user_id}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json().get('result', {})
                return {
                    'nombre': data.get('first_name', ''),
                    'apellido_paterno': data.get('last_name', ''),
                    'metadata': {
                        'username': data.get('username', ''),
                        'bio': data.get('bio', '')
                    },
                    'preferred_language': data.get('language_code', 'es')
                }
            else:
                logger.error(f"Error fetching Telegram user data: {response.text}")
                return {}
    except Exception as e:
        logger.error(f"Error en fetch_telegram_user_data: {str(e)}")
        return {}

class TelegramHandler:
    """Manejador de interacciones de Telegram para el chatbot."""

    def __init__(self, user_id: str, bot_name: str, business_unit: BusinessUnit):
        self.user_id = user_id
        self.bot_name = bot_name
        self.business_unit = business_unit
        self.user: Optional[Person] = None
        self._chat_manager = None  # Inicializado como None para carga perezosa
        self.intent_processor = None  # Inicializado como None para carga perezosa
        self.telegram_api: Optional[TelegramAPI] = None
        self.user_data: Dict[str, Any] = {}
        self.rate_limiter = RateLimiter()
        self.webapp_secret = getattr(settings, 'TELEGRAM_WEBAPP_SECRET', 'default_secret')
        self.base_url = getattr(settings, 'BASE_URL', 'https://grupohuntred.com')
    
    @property
    def chat_manager(self):
        """Carga perezosa de ChatStateManager para evitar importaciones circulares."""
        if self._chat_manager is None and self.user and self.business_unit:
            # Usamos la función de importación dinámica de services.py
            from app.ats.chatbot.integrations.services import get_telegram_handler
            _, fetch_user_data = get_telegram_handler()
            
            # Importamos ChatStateManager aquí para evitar importación circular
            from app.ats.chatbot.components.chat_state_manager import ChatStateManager
            
            self._chat_manager = ChatStateManager(
                user=self.user,
                business_unit=self.business_unit,
                channel='telegram'
            )
        return self._chat_manager

    async def initialize(self) -> bool:
        """Inicializa el manejador de Telegram."""
        try:
            # Obtener configuración de TelegramAPI
            cache_key = f"telegram_api:{self.bot_name}"
            self.telegram_api = cache.get(cache_key)
            if not self.telegram_api:
                self.telegram_api = await TelegramAPI.objects.filter(
                    bot_name=self.bot_name, is_active=True
                ).afirst()
                if self.telegram_api:
                    cache.set(cache_key, self.telegram_api, CACHE_TIMEOUT)
            if not self.telegram_api:
                raise ValueError(f"No se encontró TelegramAPI para bot_name: {self.bot_name}")

            # Obtener o crear usuario y extraer datos
            self.user = await self._get_or_create_user()
            self.user_data = await fetch_telegram_user_data(self.user_id, self.telegram_api)
            await self._update_user_profile()

            # Inicializar manejador de estados y procesador de intents
            self.chat_manager = ChatStateManager(self.user, self.business_unit)
            await self.chat_manager.initialize()
            self.intent_processor = IntentProcessor(self.user, self.business_unit)
            return True
        except Exception as e:
            logger.error(f"Error inicializando TelegramHandler: {str(e)}")
            raise

    async def handle_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un mensaje de Telegram y genera una respuesta."""
        try:
            # Extraer chat_id y texto
            chat_id, text = await self._extract_message_content(payload)
            if await self._is_spam_message(text):
                return {'response': "Por favor, no envíes mensajes repetidos o spam."}

            # Actualizar estado del chat
            await self.chat_manager.update_state('PROCESSING')

            # Procesar intent
            intent = await self.intent_processor.process(text)

            # Generar y enviar respuesta
            response = await self._generate_response(intent)
            await self._send_response(chat_id, response)

            # Actualizar estado del chat
            await self.chat_manager.update_state('IDLE')
            return response
        except Exception as e:
            logger.error(f"Error procesando mensaje en Telegram: {str(e)}")
            return {'response': "Lo siento, hubo un error procesando tu mensaje."}

    async def _get_or_create_user(self) -> Person:
        """Obtiene o crea un usuario en la base de datos."""
        user, created = await Person.objects.aget_or_create(
            telegram_user_id=self.user_id,
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

    async def _extract_message_content(self, payload: Dict[str, Any]) -> tuple[int, str]:
        """Extrae el chat_id y el contenido del mensaje."""
        if "callback_query" in payload:
            callback_query = payload["callback_query"]
            chat_id = int(callback_query["message"]["chat"]["id"])
            text = callback_query.get("data", "").strip()
            callback_query_id = callback_query.get("id", "")
            if callback_query_id:
                await self._confirm_callback(callback_query_id)
        else:
            message = payload.get("message", {})
            chat_id = int(message.get("chat", {}).get("id"))
            text = message.get("text", "").strip()
        return chat_id, text

    async def _confirm_callback(self, callback_query_id: str) -> bool:
        """Confirma la respuesta de un botón de Telegram."""
        url = f"https://api.telegram.org/bot{self.telegram_api.api_key}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"❌ Error confirmando callback: {str(e)}")
            return False

    async def _is_spam_message(self, message: str) -> bool:
        """Verifica si un mensaje es spam (implementación pendiente)."""
        return False

    async def _generate_response(self, intent: Dict):
        """
        Genera una respuesta basada en el intent detectado.
        
        Args:
            intent (Dict): Diccionario con la información del intent
            
        Returns:
            Dict: Respuesta formateada para el canal
        """
        response = {
            'text': intent.get('response', 'Lo siento, no puedo responder a eso en este momento.'),
            'options': intent.get('options', []),
            'type': 'text',
            'metadata': intent.get('metadata', {})
        }
        return response

    async def _send_response(self, chat_id: int, response: Dict[str, Any]) -> bool:
        """
        Envía la respuesta al usuario en Telegram.
        
        Args:
            chat_id (int): ID del chat de Telegram
            response (Dict): Respuesta a enviar
            
        Returns:
            bool: True si el mensaje se envió correctamente, False en caso contrario
        """
        try:
            if not response:
                logger.warning("Respuesta vacía, no se enviará ningún mensaje")
                return False
                
            if response.get('type') == 'text' and response.get('options'):
                # Usar el message_sender para enviar opciones
                await send_options(
                    platform='telegram',
                    user_id=str(chat_id),
                    message=response['text'],
                    options=response['options'],
                    business_unit=self.business_unit
                )
            else:
                # Envío de mensaje de texto simple
                await send_message(
                    platform='telegram',
                    user_id=str(chat_id),
                    message=response.get('text', 'Sin contenido'),
                    business_unit=self.business_unit
                )
                
            # Manejo de metadata adicional si es necesario
            if 'metadata' in response and response['metadata'].get('requires_follow_up'):
                asyncio.create_task(self._schedule_follow_up(chat_id, response['metadata']))
                
            return True
                
        except Exception as e:
            logger.error(f"Error al enviar respuesta a Telegram: {str(e)}", exc_info=True)
            # Intentar notificar al usuario del error
            try:
                await send_message(
                    platform='telegram',
                    user_id=str(chat_id),
                    message="Lo siento, ha ocurrido un error al procesar tu solicitud. Por favor, inténtalo de nuevo más tarde.",
                    business_unit=self.business_unit
                )
            except Exception as inner_e:
                logger.error(f"Error al notificar al usuario sobre el error: {str(inner_e)}", exc_info=True)
            return False

    async def _schedule_follow_up(self, chat_id: int, metadata: Dict[str, Any]) -> None:
        """
        Programa un seguimiento basado en los metadatos.
        
        Args:
            chat_id (int): ID del chat de Telegram
            metadata (Dict): Metadatos para el seguimiento
        """
        try:
            follow_up_time = metadata.get('follow_up_time', 3600)  # 1 hora por defecto
            follow_up_message = metadata.get('follow_up_message', '')
            
            if follow_up_message and follow_up_time > 0:
                await asyncio.sleep(follow_up_time)
                await send_message(
                    platform='telegram',
                    user_id=str(chat_id),
                    message=follow_up_message,
                    business_unit=self.business_unit
                )
        except Exception as e:
            logger.error(f"Error al programar seguimiento: {str(e)}", exc_info=True)

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def send_telegram_buttons(self, chat_id: int, message: str, buttons: List[Dict]) -> bool:
        """Envía un mensaje con inline keyboard."""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_api.api_key}/sendMessage"
            inline_keyboard = [
                [{"text": btn["title"], "callback_data": btn["payload"] or "no_data"}]
                for btn in buttons
            ]
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": inline_keyboard}
            }
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
            logger.info(f"✅ Inline keyboard enviado a {chat_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error enviando inline keyboard a Telegram: {str(e)}")
            return False
    
    async def send_vacancy_carousel(self, chat_id: int, vacancies: List[Dict]) -> bool:
        """Envía un carrusel de vacantes usando media groups y Mini-App."""
        try:
            # 1. Primero enviamos un álbum de fotos (pseudo-carrusel) con las primeras 3 vacantes
            if len(vacancies) > 0:
                media_group = []
                for i, vacancy in enumerate(vacancies[:3]):
                    # Definimos caption solo para la primera imagen para no sobrecargar
                    caption = "" if i > 0 else f"<b>Vacantes Recomendadas</b>\n\nHe encontrado {len(vacancies)} vacantes que podrían interesarte."
                    
                    media_group.append({
                        "type": "photo",
                        "media": vacancy.get('image_url', f"{self.base_url}/static/images/vacancy_default.jpg"),
                        "caption": caption,
                        "parse_mode": "HTML"
                    })
                
                # Enviar el grupo de fotos
                await self._send_media_group(chat_id, media_group)
                await asyncio.sleep(0.5)  # Pequeña pausa
            
            # 2. Enviamos mensaje con botones para las acciones principales
            # Incluimos botón para abrir la Mini-App con todas las vacantes
            webapp_token = self._generate_webapp_token(chat_id)
            webapp_url = f"{self.base_url}/telegram/mini_apps/vacancies/?token={webapp_token}"
            
            # Botones para acciones rápidas y acceso a la Mini-App
            message = "<b>🔍 Vacantes disponibles para ti</b>\n\nPuedes ver detalles y aplicar directamente:"
            keyboard = [
                # Primera fila: Mini-App para explorar todas las vacantes
                [{
                    "text": "Ver todas las vacantes 🔍",
                    "web_app": {"url": webapp_url}
                }]
            ]
            
            # Segunda fila: botones para las 2 primeras vacantes
            vacancy_buttons = []
            for i, vacancy in enumerate(vacancies[:2]):
                vacancy_buttons.append({
                    "text": f"Ver {vacancy['title'][:15]}...",
                    "callback_data": f"view_vacancy_{vacancy['id']}"
                })
            
            if vacancy_buttons:
                keyboard.append(vacancy_buttons)
            
            # Tercera fila: opciones adicionales
            keyboard.append([{
                "text": "Filtrar por ubicación",
                "callback_data": "filter_location"
            },{
                "text": "Subir mi CV",
                "callback_data": "upload_cv"
            }])
            
            # Enviar mensaje con el teclado inline
            await self._send_message_with_keyboard(chat_id, message, keyboard)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando carrusel de vacantes: {str(e)}", exc_info=True)
            return False
    
    async def _send_media_group(self, chat_id: int, media: List[Dict]) -> bool:
        """Envía un grupo de archivos multimedia (fotos, videos, etc)."""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_api.api_key}/sendMediaGroup"
            payload = {
                "chat_id": chat_id,
                "media": json.dumps(media)
            }
            
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
            
            logger.info(f"✅ Media group enviado a {chat_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error enviando media group: {str(e)}", exc_info=True)
            return False
    
    async def _send_message_with_keyboard(self, chat_id: int, message: str, keyboard: List[List[Dict]]) -> bool:
        """Envía un mensaje con teclado personalizado."""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_api.api_key}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": keyboard}
            }
            
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
            
            logger.info(f"✅ Mensaje con teclado enviado a {chat_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje con teclado: {str(e)}", exc_info=True)
            return False
    
    def _generate_webapp_token(self, chat_id: str) -> str:
        """Genera un token seguro para la Mini-App."""
        timestamp = int(time.time())
        token_data = f"{chat_id}:{timestamp}"
        
        # Generar firma HMAC
        signature = hmac.new(
            self.webapp_secret.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Token = datos + timestamp + firma
        return f"{token_data}:{signature}"
    
    async def handle_document(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un documento recibido (CV, etc.)."""
        try:
            chat_id = message.get("chat", {}).get("id")
            if not chat_id:
                return {"success": False, "error": "Chat ID no encontrado"}
            
            # Revisar si hay documento
            document = message.get("document")
            if not document:
                return {"success": False, "error": "No se encontró documento en el mensaje"}
            
            # Obtener detalles del documento
            file_id = document.get("file_id")
            mime_type = document.get("mime_type", "")
            filename = document.get("file_name", f"documento_{int(time.time())}")
            
            # Verificar si es un tipo de archivo soportado
            supported_types = [
                'application/pdf', 
                'application/msword', 
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            
            if mime_type not in supported_types:
                await self._send_response(chat_id, {
                    "response": "Lo siento, solo puedo procesar documentos PDF o Word (.doc/.docx). Por favor, envía tu CV en alguno de estos formatos."
                })
                return {"success": False, "error": "Tipo de documento no soportado"}
            
            # Descargar el documento
            file_data = await self._download_file(file_id)
            if not file_data:
                return {"success": False, "error": "No se pudo descargar el documento"}
            
            # Procesar documento
            processor = DocumentProcessor(self.user_id, self.business_unit.id)
            result = await processor.process_document(file_data, filename, mime_type)
            
            # Informar al usuario
            if result.get("success"):
                if result.get("processed") and result.get("cv_data"):
                    await self._send_cv_confirmation(chat_id, result["cv_data"])
                else:
                    await self._send_response(chat_id, {
                        "response": "Documento recibido correctamente. Gracias por compartirlo."
                    })
                    
            return result
        except Exception as e:
            logger.error(f"❌ Error procesando documento: {str(e)}", exc_info=True)
            if chat_id:
                await self._send_response(chat_id, {
                    "response": "Lo siento, ocurrió un error al procesar tu documento. Por favor, intenta nuevamente más tarde."
                })
            return {"success": False, "error": str(e)}
    
    async def _download_file(self, file_id: str) -> Optional[bytes]:
        """Descarga un archivo desde Telegram."""
        try:
            # Primero obtener la ruta del archivo
            url = f"https://api.telegram.org/bot{self.telegram_api.api_key}/getFile"
            params = {"file_id": file_id}
            
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                file_info = resp.json()
                
                if not file_info.get("ok") or "result" not in file_info:
                    return None
                    
                file_path = file_info["result"]["file_path"]
                
                # Ahora descargar el contenido del archivo
                download_url = f"https://api.telegram.org/file/bot{self.telegram_api.api_key}/{file_path}"
                resp = await client.get(download_url)
                resp.raise_for_status()
                
                return resp.content
        except Exception as e:
            logger.error(f"❌ Error descargando archivo: {str(e)}", exc_info=True)
            return None
    
    async def _send_cv_confirmation(self, chat_id: int, cv_data: Dict[str, Any]) -> bool:
        """Envía confirmación de recepción de CV con datos extraídos."""
        try:
            # Crear mensaje con datos extraídos
            message = (
                "<b>✅ CV Recibido Correctamente</b>\n\n"
                "He extraído la siguiente información:\n\n"
                f"👤 <b>Nombre:</b> {cv_data.get('nombre', 'No detectado')}\n"
                f"📧 <b>Email:</b> {cv_data.get('email', 'No detectado')}\n"
                f"📞 <b>Teléfono:</b> {cv_data.get('telefono', 'No detectado')}\n"
                f"🎓 <b>Nivel de estudios:</b> {cv_data.get('nivel_estudios', 'No detectado')}\n\n"
            )
            
            # Añadir habilidades detectadas
            if cv_data.get('skills'):
                message += "<b>Habilidades detectadas:</b>\n"
                for skill in cv_data.get('skills', [])[:5]:
                    message += f"• {skill}\n"
            else:
                message += "<i>No se detectaron habilidades específicas</i>\n"
            
            message += "\n¿Es correcta esta información?"
            
            # Botones para confirmar o corregir
            keyboard = [
                [
                    {"text": "✅ Sí, es correcta", "callback_data": "cv_data_confirm"},
                    {"text": "❌ No, actualizar", "callback_data": "cv_data_update"}
                ],
                [
                    {"text": "🔍 Ver vacantes compatibles", "callback_data": "find_matching_vacancies"}
                ]
            ]
            
            # Enviar el mensaje
            return await self._send_message_with_keyboard(chat_id, message, keyboard)
            
        except Exception as e:
            logger.error(f"❌ Error enviando confirmación de CV: {str(e)}", exc_info=True)
            return False

@csrf_exempt
async def telegram_webhook(request, bot_name: str):
    """Webhook para procesar mensajes entrantes de Telegram."""
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode("utf-8"))
        user_id = str(payload.get("message", {}).get("chat", {}).get("id", payload.get("callback_query", {}).get("from", {}).get("id")))
        business_unit = await sync_to_async(lambda: TelegramAPI.objects.filter(
            bot_name=bot_name, is_active=True
        ).first().business_unit)()

        handler = TelegramHandler(user_id, bot_name, business_unit)
        await handler.initialize()
        response = await handler.handle_message(payload)
        return JsonResponse({"status": "success", "response": response}, status=200)
    except Exception as e:
        logger.error(f"Error en telegram_webhook: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)