# /home/pablo/app/com/chatbot/chatbot.py
import logging
import asyncio
import re
import sys
from langdetect import detect
from typing import Optional, List, Dict, Any, Tuple
from django.utils import timezone
from asgiref.sync import sync_to_async
from django.core.cache import cache
import time

# Importaciones directas siguiendo estándares de Django - v2025.05.20
from app.com.chatbot.conversational_flow_manager import ConversationalFlowManager
from app.com.chatbot.intents_handler import IntentsHandler
from app.com.chatbot.components.context_manager import ContextManager
from app.com.chatbot.response_generator import ResponseGenerator
from app.com.chatbot.components.chat_state_manager import ChatStateManager
from app.com.chatbot.gpt import GPTHandler
from app.com.chatbot.components.channel_config import ChannelConfig
from app.com.chatbot.components.rate_limiter import RateLimiter
from app.com.chatbot.integrations.services import MessageService
from app.com.chatbot.service import GamificationService
from app.com.chatbot.integrations.document_processor import CVParser
from app.com.chatbot.nlp import NLPProcessor

from app.models import (
    ChatState, Person, GptApi, Application, Invitacion, BusinessUnit, ConfiguracionBU, Vacante,
    WhatsAppAPI, EnhancedNetworkGamificationProfile, ConfiguracionBU
)

# Workflow functions (loaded on demand)
from app.com.chatbot.workflow.common import (
    generate_and_send_contract, iniciar_creacion_perfil, iniciar_perfil_conversacional,
    obtener_explicaciones_metodos
)
from app.com.chatbot.workflow.amigro import process_amigro_candidate
from app.com.chatbot.workflow.huntu import process_huntu_candidate
from app.com.chatbot.workflow.huntred import process_huntred_candidate
from app.com.chatbot.workflow.huntred_executive import process_huntred_executive_candidate
from app.com.chatbot.workflow.sexsi import iniciar_flujo_sexsi, confirmar_pago_sexsi

# Importamos el gestor de workflows y clases relacionadas
from app.com.chatbot.workflow import (
    WorkflowManager, get_workflow_manager, create_workflow, handle_workflow_message,
    TalentAnalysisWorkflow, CulturalFitWorkflow
)

logger = logging.getLogger('chatbot')

# Configuración simplificada en el mismo archivo
CACHE_ENABLED = True
CACHE_TIMEOUT = 600  # 10 minutos 
GPT_ENABLED = True
ML_ENABLED = True
NLP_ENABLED = True

class ChatBotHandler:
    def __init__(self):
        self.gpt_handler = GPTHandler()
        self.workflow_mapping = {
            "amigro": process_amigro_candidate,
            "huntu": process_huntu_candidate,
            "huntred": process_huntred_candidate,
            "huntred executive": process_huntred_executive_candidate,
            "sexsi": iniciar_flujo_sexsi,
            # Nuevos workflows gestionados por el WorkflowManager
            "talent_analysis": self.start_talent_analysis_workflow,
            "cultural_fit": self.start_cultural_fit_workflow
        }
        self.initial_messages = {
            "default": [
                "Bienvenido a nuestra plataforma 🎉",
                "Al conversar, aceptas nuestros Términos de Servicio (TOS).",
                "¡Cuéntame, en qué puedo ayudarte hoy?"
            ],
            "amigro": [
                "Bienvenido a Amigro - amigro.org, somos una organización que facilitamos el acceso laboral a mexicanos regresando y migrantes de Latinoamérica ingresando a México, mediante Inteligencia Artificial Conversacional",
                "Por lo que platicaremos un poco de tu trayectoria profesional, tus intereses, tu situación migratoria, etc. Es importante ser lo más preciso posible, ya que con eso podremos identificar las mejores oportunidades para tí, tu familia, y en caso de venir en grupo, favorecerlo. *Por cierto Al iniciar, confirmas la aceptación de nuestros TOS."
            ]
        }
        
        # Inicializar componentes del nuevo sistema modular
        self.conversational_flow = ConversationalFlowManager()
        self.intents_manager = IntentsHandler()
        self.context_manager = ContextManager()
        self.response_generator = ResponseGenerator()
        self.state_manager = ChatStateManager()
        self.message_service = MessageService()
        self.gamification_service = GamificationService()
        self.cv_parser = CVParser()
        
        # Inicializar el gestor de workflows
        # Importación a nivel de método para evitar dependencias circulares
        from app.com.chatbot.workflow import WorkflowManager
        self.workflow_manager = WorkflowManager()
        self.active_workflows = {}
        
        try:
            self.nlp_processor = NLPProcessor(language='es', mode='candidate', analysis_depth='quick')
        except Exception as e:
            logger.error(f"Error inicializando NLPProcessor: {e}")
            self.nlp_processor = None if NLP_ENABLED else None

    def get_business_unit_key(self, business_unit) -> str:
        """Obtiene una clave segura para el business unit."""
        try:
            if hasattr(business_unit, 'name'):
                return str(business_unit.name).lower().replace('®', '').strip()
        except Exception as e:
            logger.error(f"Error obteniendo business unit key: {e}")
        return 'default'

    @MessageRetry.with_retry(platform)
    async def send_message(self, platform: str, user_id: str, message: dict, business_unit: BusinessUnit, payload: Dict[str, Any] = None):
        """Envía un mensaje a través del canal especificado con retry."""
        logger.info(f"[send_message] Enviando mensaje a {user_id} en {platform}: {message}")
        
        try:
            await send_message(platform, user_id, message, business_unit.name)
            chatbot_metrics.track_message(platform, 'sent', success=True)
            return True
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            chatbot_metrics.track_message(platform, 'sent', success=False)
            return False

    async def process_message(self, platform: str, user_id: str, message: dict, business_unit: BusinessUnit, payload: Dict[str, Any] = None):
        logger.info(f"[process_message] Recibido mensaje de {user_id} en {platform} para {business_unit.name}: {message}")
        
        # Registrar actividad del usuario
        chatbot_metrics.track_user_activity(platform, user_id)
        
        # Inicializar gestor de flujo conversacional
        flow_manager = ConversationalFlowManager(business_unit)
        
        try:
            # Procesar el mensaje usando el nuevo flujo
            result = await flow_manager.process_message(
                platform=platform,
                user_id=user_id,
                message=message,
                business_unit=business_unit
            )
            
            if result['success']:
                # Enviar respuesta usando el servicio de mensajes
                await self.message_service.send_message(
                    platform,
                    user_id,
                    result['response']['text']
                )
                
                # Si hay opciones, enviarlas
                if result['response'].get('options'):
                    await self.message_service.send_options(
                        platform,
                        user_id,
                        result['response']['text'],
                        result['response']['options']
                    )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
        
        # Validar business_unit
        if not isinstance(business_unit, BusinessUnit):
            logger.error(f"[process_message] business_unit no es un BusinessUnit, es {type(business_unit)}")
            await self.send_message(platform, user_id, "Ups, algo salió mal. Contacta a soporte.", "default")
            return False

        # Inicializar chat_state
        user, chat_state, _ = await self._get_or_create_user_and_chat_state(user_id, platform, business_unit, payload)
        if chat_state is None:
            logger.error(f"Failed to initialize chat_state for user_id: {user_id}")
            await send_message(platform, user_id, "Error: No se pudo inicializar el estado del chat.", self.get_business_unit_key(business_unit))
            return False

        # Validar mensaje según las restricciones del canal
        if not MessageRetry.validate_message(platform, message):
            logger.warning(f"Mensaje inválido para el canal {platform}")
            await send_message(platform, user_id, "El mensaje no cumple con las restricciones del canal.", self.get_business_unit_key(business_unit))
            return False

        # Validar chat_state
        if not isinstance(chat_state, ChatState):
            logger.error(f"[process_message] chat_state no es un ChatState, es {type(chat_state)}")
            await send_message(platform, user_id, "Ups, algo salió mal. Contacta a soporte.", self.get_business_unit_key(business_unit))
            return False

        # Registrar métrica de mensaje recibido
        chatbot_metrics.track_message(platform, 'received')

        # Validar chat_state.person
        if not hasattr(chat_state, 'person') or chat_state.person is None:
            logger.error(f"[process_message] chat_state.person no está asignado para user_id: {user_id}")
            await send_message(platform, user_id, "No se encontró tu perfil. Por favor, inicia de nuevo.", business_unit.name.lower())
            return False

        try:
            logger.info(f"Procesando mensaje de {user_id} en {platform} para {business_unit.name}")
            
            # 1. Verificación de mensaje duplicado
            message_id = message.get("messages", [{}])[0].get("id")
            if CACHE_ENABLED and message_id:
                cache_key = f"processed_message:{message_id}"
                if cache.get(cache_key):
                    logger.info(f"Mensaje {message_id} ya procesado, ignorando.")
                    return

            # 2. Extraer contenido y detectar idioma/ubicación
            text, attachment = self._extract_message_content(message)
            bu_key = self.get_business_unit_key(business_unit)
            logger.info(f"[process_message] 📩 Mensaje recibido de {user_id} en {platform} para BU: {bu_key}: {text or 'attachment'}")

            if not text and not attachment:
                logger.warning(f"[process_message] Mensaje vacío recibido de user_id: {user_id}, platform: {platform}")
                await send_message(platform, user_id, "Por favor, envía un mensaje válido o un archivo.", bu_key)
                return

            language = detect(text) if text and len(text) > 5 and any(c.isalpha() for c in text) else "es"
            logger.info(f"Idioma detectado: {language}")
            
            # 3. Obtener usuario y estado
            user, chat_state, _ = await self._get_or_create_user_and_chat_state(user_id, platform, business_unit, payload)
            chat_state.context["language"] = language
            await sync_to_async(chat_state.save)()
            logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")

            from app.com.chatbot.utils import analyze_text, is_spam_message, update_user_message_history, is_user_spamming
            # 4. Verificar SPAM y silenciado
            if NLP_ENABLED and text and is_spam_message(user_id, text):
                if is_user_spamming(user_id):
                    cache.set(f"muted:{user_id}", True, timeout=60)
                    await send_message(platform, user_id, "⚠️ Demasiados mensajes similares, espera un momento.", bu_key)
                    return
                await send_message(platform, user_id, "⚠️ Por favor, no envíes mensajes repetidos.", bu_key)
                return

            # 5. Handle document uploads
            if attachment or (message.get("messages", [{}])[0].get("file_id")):
                file_id = attachment.get("file_id") if attachment else message["messages"][0].get("file_id")
                file_name = attachment.get("file_name") if attachment else message["messages"][0].get("file_name")
                mime_type = attachment.get("mime_type") if attachment else message["messages"][0].get("mime_type")
                response = await self.handle_document_upload(user, file_id, file_name, mime_type, platform, bu_key)
                await send_message(platform, user_id, response, bu_key)
                await self.store_bot_message(chat_state, response)
                return response

            # 6. Handle waiting_for_cv state
            if chat_state.state == "waiting_for_cv" and text:
                if text.lower() in ["sí", "si"]:
                    chat_state.state = "profile_in_progress"
                    await sync_to_async(chat_state.save)()
                    await send_message(platform, user_id, "¡Gracias por confirmar! Continuemos con tu perfil.", bu_key)
                    await self.start_profile_creation(platform, user_id, business_unit, chat_state, user)
                elif text.lower() == "no":
                    chat_state.state = "waiting_for_cv"
                    await sync_to_async(chat_state.save)()
                    await send_message(platform, user_id, "Por favor, envía un CV correcto (PDF o Word).", bu_key)
                else:
                    await send_message(platform, user_id, "Por favor, envía tu CV como archivo adjunto (PDF o Word) o confirma los datos con 'sí' o 'no'.", bu_key)
                return

            # 7. Detectar y manejar intents
            if text:
                intents = await detect_intents(text)
                logger.info(f"[detect_intents] Intents detectados para '{text}': {intents}")
                if intents:
                    intent = intents[0]
                    # Crear procesador de intents
                    intent_processor = IntentProcessor(user, business_unit)
                    response = await intent_processor.process_intent(intent, text)
                    return response
                    
                # Verificamos si hay un workflow activo para este usuario
                # En ese caso, delegamos el manejo del mensaje al workflow correspondiente
                if chat_state.state in ["TALENT_ANALYSIS_WORKFLOW", "CULTURAL_FIT_WORKFLOW"] and \
                   'active_workflow' in chat_state.context:
                    
                    # Delegamos el mensaje al gestor de workflows
                    workflow_handled = await self.handle_workflow_message(
                        platform, user_id, text, chat_state, business_unit, user
                    )
                    
                    if workflow_handled:
                        # El mensaje fue manejado por un workflow, no continuamos con el procesamiento normal
                        return
                
                # Detectamos si el usuario quiere iniciar un análisis cultural o de talento
                if re.search(r'(analisis\s+cultural|cultural\s+fit|compatibilidad\s+cultural)', text.lower()):
                    # El usuario quiere iniciar un análisis cultural
                    await self.start_cultural_fit_workflow(platform, user_id, business_unit, chat_state, user)
                    return
                elif re.search(r'(analisis\s+de\s+talento|talent\s+analysis|analisis\s+360|360\s+grados)', text.lower()):
                    # El usuario quiere iniciar un análisis de talento
                    await self.start_talent_analysis_workflow(platform, user_id, business_unit, chat_state, user)
                    return
                
                # Fallback a NLP con manejo robusto
                if NLP_ENABLED and self.nlp_processor:
                    try:
                        analysis = await self.nlp_processor.analyze(text)
                        response = await self._generate_default_response(
                            user, chat_state, text, 
                            analysis.get("entities", []), 
                            analysis.get("sentiment", {})
                        )
                        await send_message(platform, user_id, response, bu_key)
                        return response
                    except Exception as nlp_error:
                        logger.error(f"Error en análisis NLP: {nlp_error}")
                        response = f"No entendí bien, pero parece que dijiste '{text}'. ¿En qué más puedo ayudarte?"
                        await send_message(platform, user_id, response, bu_key)
                        return response

                # 8. Estado inicial y TOS
                if chat_state.state == "initial":
                    await self.send_complete_initial_messages(platform, user_id, business_unit)
                    chat_state.state = "waiting_for_tos"
                    await sync_to_async(chat_state.save)()
                    logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")
                    return

                # 7. Verificación de aceptación de TOS
                if not user.tos_accepted:
                    await self.handle_tos_acceptance(platform, user_id, text, chat_state, business_unit, user)
                    if text.lower() in ["sí", "si"]:
                        chat_state.state = "profile_in_progress"
                        await sync_to_async(chat_state.save)()
                        logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")
                        await self.start_profile_creation(platform, user_id, business_unit, chat_state, user)
                    return

                # 9. Almacenar mensaje del usuario
                if text:
                    await self.store_user_message(chat_state, text)

                # 10. Procesar adjuntos si existen
                if attachment:
                    url = attachment.get("url")
                    if not url or not isinstance(url, str) or not url.strip():
                        logger.warning(f"[process_message] Adjunto sin URL válida para user_id: {user_id}, platform: {platform}")
                        await send_message(platform, user_id, "No se pudo procesar el adjunto. Asegúrate de enviar un archivo válido.", bu_key)
                        return
                    response = await self.handle_cv_upload(user, url)
                    await send_message(platform, user_id, response, bu_key)
                    await self.store_bot_message(chat_state, response)
                    return

                # 11. Procesamiento específico por estado (incluye captura de sueldo)
                if chat_state.state == "profile_in_progress":
                    if await manejar_respuesta_perfil(platform, user_id, text, business_unit, chat_state, user, self.gpt_handler):
                        # Preguntar por sueldo actual después de experiencia
                        if "experience" in chat_state.context and "current_salary" not in chat_state.context:
                            response = "¿Cuál es tu sueldo actual? Si está en MXN, puedo darte una comparativa con otras monedas si quieres."
                            await send_message(platform, user_id, response, bu_key)
                            chat_state.context["awaiting_salary"] = True
                            await sync_to_async(chat_state.save)()
                            logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")
                        elif chat_state.context.get("awaiting_salary") and text:
                            salary = text.strip()
                            chat_state.context["current_salary"] = salary
                            chat_state.context["awaiting_salary"] = False
                            if "mxn" in salary.lower():
                                response = f"Guardé tu sueldo: {salary}. ¿Te gustaría una comparativa con otras monedas o el mercado laboral?"
                            else:
                                response = f"Guardé tu sueldo: {salary}. ¿En qué más puedo ayudarte?"
                            await send_message(platform, user_id, response, bu_key)
                            await sync_to_async(chat_state.save)()
                            logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")
                        return

                # 12. Análisis NLP y respuesta por defecto
                if NLP_ENABLED and self.nlp_processor and text:
                    analysis = await self.nlp_processor.analyze(text)
                    response = await self._generate_default_response(
                        user, chat_state, text, 
                        analysis.get("entities", []), 
                        analysis.get("sentiment", {})
                    )
                    await send_message(platform, user_id, response, bu_key)
                    await self.store_bot_message(chat_state, response)

                # Análisis NLP adicional si es requerido
                if chat_state.context.get('requires_nlp', False) and NLP_ENABLED and self.nlp_processor:
                    analysis = await self.nlp_processor.analyze(text)
                    # Aquí puedes usar el análisis si es necesario, aunque actualmente no hace nada

        except NameError as ne:
            logger.error(f"Error de definición en process_message: {ne}", exc_info=True)
            await send_message(platform, user_id, "Ups, algo salió mal con la configuración. Intenta de nuevo.", bu_key)
            await send_menu(platform, user_id, business_unit)
        except Exception as e:
            logger.error(f"Error en process_message: {e}", exc_info=True)
            await send_message(platform, user_id, "Ups, algo salió mal. Te comparto el menú:", bu_key)
            await send_menu(platform, user_id, business_unit)

    async def handle_document_upload(self, user: Person, file_id: str, file_name: str, mime_type: str, platform: str, bu_key: str) -> str:
        valid_mime_types = [
            "application/pdf", "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        if mime_type not in valid_mime_types:
            return f"No puedo procesar archivos de tipo {mime_type}. Usa PDF o Word."
        
        try:
            file_url = await self._get_file_url(platform, file_id, bu_key)
            if not file_url:
                return "No pude obtener el archivo. Intenta de nuevo."
            
            # Parse document
            from app.com.utils.parser import parse_document
            parsed_data = await sync_to_async(parse_document)(file_url, 'pdf' if mime_type == "application/pdf" else 'doc')
            
            # Update user profile
            saved_attributes = []
            user.cv_parsed = True
            saved_attributes.append(f"cv_parsed: True")
            user.cv_url = file_url
            saved_attributes.append(f"cv_url: {file_url}")
            user.cv_parsed_data = parsed_data
            saved_attributes.append(f"cv_parsed_data: {parsed_data}")

            if 'name' in parsed_data and not user.nombre:
                user.nombre = parsed_data['name']
                saved_attributes.append(f"nombre: {parsed_data['name']}")
            if 'email' in parsed_data and not user.email:
                user.email = parsed_data['email']
                saved_attributes.append(f"email: {parsed_data['email']}")
            if 'phone' in parsed_data and not user.phone:
                user.phone = parsed_data['phone']
                saved_attributes.append(f"phone: {parsed_data['phone']}")
            if 'skills' in parsed_data:
                user.skills = ', '.join(parsed_data['skills']) if isinstance(parsed_data['skills'], list) else parsed_data['skills']
                saved_attributes.append(f"skills: {user.skills}")

            await sync_to_async(user.save)()
            logger.info(f"[handle_document_upload] Atributos guardados para {user.id}: {', '.join(saved_attributes)}")

            return (
                "✅ ¡He procesado tu CV correctamente!\n\n"
                "Datos extraídos:\n"
                f"👤 Nombre: {parsed_data.get('name', 'No detectado')}\n"
                f"📧 Email: {parsed_data.get('email', 'No detectado')}\n"
                f"📱 Teléfono: {parsed_data.get('phone', 'No detectado')}\n"
                f"🛠 Habilidades: {', '.join(parsed_data.get('skills', [])) or 'No detectadas'}\n\n"
                "¿Están correctos estos datos? Responde 'sí' para confirmar o 'no' para corregir."
            )
        except Exception as e:
            logger.error(f"Error procesando documento: {str(e)}")
            return "❌ Hubo un problema al procesar tu documento. Intenta de nuevo."

    async def _get_file_url(self, platform: str, file_id: str, bu_key: str) -> str:
        if platform == "telegram":
            telegram_api = await self.get_api_instance("telegram")
            url = f"https://api.telegram.org/bot{telegram_api.api_key}/getFile?file_id={file_id}"
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.get(url)
                response.raise_for_status()
                file_path = response.json().get("result", {}).get("file_path")
                return f"https://api.telegram.org/file/bot{telegram_api.api_key}/{file_path}" if file_path else None
        elif platform == "whatsapp":
            whatsapp_api = await self.get_api_instance("whatsapp")
            return await get_media_url(whatsapp_api, file_id)
        # Add handlers for Messenger, Slack, Instagram
        return None
    
    async def initialize_chat_state(self, platform: str, user_id: str, business_unit: BusinessUnit) -> ChatState:
        chat_state, _ = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=user_id, platform=platform, business_unit=business_unit, defaults={'state': 'initial', 'context': {}}
        )
        return chat_state

    def _extract_message_content(self, message: dict) -> Tuple[str, Optional[dict]]:
        text = ""
        attachment = None
        if isinstance(message, dict) and "text" in message and "body" in message["text"]:
            text = message["text"]["body"].strip().lower()
        elif message.get("messages") and "text" in message["messages"][0] and "body" in message["messages"][0]["text"]:
            text = message["messages"][0]["text"]["body"].strip().lower()
        elif "attachment" in message:
            attachment = message["attachment"]
        return text, attachment

    async def get_or_create_user(self, user_id: str, platform: str, business_unit: BusinessUnit, payload: Dict[str, Any] = None):
        from app.com.chatbot.integrations.services import MessageService
        message_service = MessageService(business_unit)
        user_data = await message_service.fetch_user_data(platform, user_id, payload)

        phone = user_id if platform == "whatsapp" else f"{platform}:{user_id}"

        defaults = {
            "nombre": user_data.get("nombre", ""),
            "apellido_paterno": user_data.get("apellido_paterno", ""),
            "metadata": user_data.get("metadata", {})
        }

        user, created = await sync_to_async(Person.objects.get_or_create)(
            phone=phone,
            defaults=defaults
        )

        if not created and user_data:
            user.nombre = defaults["nombre"]
            user.apellido_paterno = defaults["apellido_paterno"]
            user.metadata = defaults["metadata"]
            await sync_to_async(user.save)()

        return user, created
    
    async def _get_or_create_user_and_chat_state(self, user_id: str, platform: str, business_unit: BusinessUnit, payload: Dict[str, Any] = None):
        user, created = await self.get_or_create_user(user_id, platform, business_unit, payload)
        
        chat_state, chat_created = await sync_to_async(ChatState.objects.select_related('person', 'business_unit').get_or_create)(
            user_id=user_id,
            business_unit=business_unit,
            defaults={"platform": platform, "person": user}
        )
        
        return user, chat_state, created or chat_created

    async def _generate_default_response(self, user: Person, chat_state: ChatState, text: str, entities: List, sentiment: Dict) -> str:
        if not GPT_ENABLED:
            return "No entendí tu mensaje. ¿En qué puedo ayudarte?"
        return await self.generate_dynamic_response(user, chat_state, text, entities, sentiment)

    async def send_complete_initial_messages(self, platform: str, user_id: str, business_unit: BusinessUnit):
        bu_key = self.get_business_unit_key(business_unit)
        messages = self.initial_messages.get(bu_key, self.initial_messages["default"])
        for msg in messages:
            await send_message(platform, user_id, msg, bu_key)
            await asyncio.sleep(1)
        tos_url = get_tos_url(business_unit)  # Usamos la función de intents_handler
        await send_message(platform, user_id, f"📜 Revisa nuestros Términos de Servicio: {tos_url}. Es necesario aceptarlos.", bu_key)
        tos_buttons = [
            {'title': 'Sí, continuar', 'payload': 'tos_accept'},
            {'title': 'No', 'payload': 'tos_reject'}
        ]
        await send_options(platform, user_id, "¿Aceptas nuestros Términos de Servicio?", tos_buttons, bu_key)

    async def generate_dynamic_response(self, user: Person, chat_state: ChatState, user_message: str, entities: List, sentiment: Dict) -> str:
        if not GPT_ENABLED or not self.gpt_handler:
            logger.error(f"GPT Desabilitado, no se pudo procesar mensaje.")
            return "No entendí tu mensaje. ¿En qué puedo ayudarte?"
        history = chat_state.conversation_history or []
        prompt = ""
        for msg in history[-5:]:
            prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
        prompt += f"Usuario: {user_message}\nAsistente:"
        try:
            return await self.gpt_handler.generate_response(prompt, chat_state.business_unit)
        except Exception as e:
            logger.error(f"Error generando respuesta GPT: {e}")
            return "No entendí tu mensaje. ¿En qué más puedo ayudarte?"

    async def start_profile_creation(self, platform: str, user_id: str, business_unit: BusinessUnit, chat_state: ChatState, person: Person):
        await iniciar_creacion_perfil(platform, user_id, business_unit, chat_state, person)

    def is_profile_complete(self, person: Person, business_unit: BusinessUnit) -> bool:
        required_fields = ['nombre', 'apellido_paterno', 'email', 'phone']
        if self.get_business_unit_key(business_unit) == "amigro":
            required_fields.extend(['nacionalidad', 'metadata'])
        elif self.get_business_unit_key(business_unit) == "huntu":
            required_fields.append('work_experience')
        missing_fields = [field for field in required_fields if not getattr(person, field, None) or (field == 'metadata' and 'migratory_status' not in person.metadata)]
        return not missing_fields

    async def handle_status_email(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        email_pattern = r"[^@]+@[^@]+\.[^@]+"
        if re.match(email_pattern, text):
            applications = await sync_to_async(Application.objects.filter)(user__email=text)
            application = await sync_to_async(applications.first)()
            msg = f"El estatus de tu aplicación es: {application.status}." if application else "No encuentro una aplicación con ese correo."
            await send_message(platform, user_id, msg, self.get_business_unit_key(business_unit))
            await self.store_bot_message(event, msg)
            event.context['awaiting_status_email'] = False
            await sync_to_async(event.save)()
        else:
            msg = "Ese no parece un correo válido. Intenta nuevamente."
            await send_message(platform, user_id, msg, self.get_business_unit_key(business_unit))
            await self.store_bot_message(event, msg)

    async def handle_group_invitation_input(self, platform: str, user_id: str, text: str, chat_state: ChatState, business_unit: BusinessUnit, user: Person):
        bu_key = self.get_business_unit_key(business_unit)
        if not chat_state.context.get('awaiting_group_invitation'):
            await send_message(platform, user_id, "Por favor, dime el nombre de la persona que quieres invitar.", bu_key)
            chat_state.context['awaiting_group_invitation'] = True
            chat_state.state = "waiting_for_invitation_name"
            await sync_to_async(chat_state.save)()
            logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")
            return
        if chat_state.state == "waiting_for_invitation_name":
            chat_state.context['invitation_name'] = text.capitalize()
            await send_message(platform, user_id, "Gracias, ahora dime el apellido.", bu_key)
            chat_state.state = "waiting_for_invitation_apellido"
            await sync_to_async(chat_state.save)()
            logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")
            return
        elif chat_state.state == "waiting_for_invitation_apellido":
            chat_state.context['invitation_apellido'] = text.capitalize()
            await send_message(platform, user_id, "Perfecto, ahora dame el número de teléfono (ej. +521234567890).", bu_key)
            chat_state.state = "waiting_for_invitation_phone"
            await sync_to_async(chat_state.save)()
            logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")
            return
        elif chat_state.state == "waiting_for_invitation_phone":
            phone_pattern = r"^\+\d{10,15}$"
            if re.match(phone_pattern, text):
                name = chat_state.context.get('invitation_name')
                apellido = chat_state.context.get('invitation_apellido')
                phone_number = text
                await self.invite_known_person(user, name, apellido, phone_number)
                resp = f"He invitado a {name} {apellido}. ¿Deseas invitar a alguien más?"
                buttons = [
                    {"title": "Sí", "payload": "yes_invite_more"},
                    {"title": "No", "payload": "no_invite_more"}
                ]
                await send_message(platform, user_id, resp, bu_key)
                await send_options(platform, user_id, "Selecciona una opción:", buttons, bu_key)
                chat_state.state = "waiting_for_invitation_confirmation"
                await sync_to_async(chat_state.save)()
                logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")
            else:
                resp = "El número no parece válido. Usa el formato '+521234567890'. Intenta de nuevo."
                await send_message(platform, user_id, resp, bu_key)
                await self.store_bot_message(chat_state, resp)
            return
        elif chat_state.state == "waiting_for_invitation_confirmation":
            if text == "yes_invite_more":
                chat_state.context.pop('invitation_name', None)
                chat_state.context.pop('invitation_apellido', None)
                chat_state.context['awaiting_group_invitation'] = True
                await send_message(platform, user_id, "¡Genial! Dime el nombre de la siguiente persona.", bu_key)
                chat_state.state = "waiting_for_invitation_name"
                await sync_to_async(chat_state.save)()
                logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")
            elif text == "no_invite_more":
                await send_message(platform, user_id, "¡Listo! No invitaré a nadie más. ¿En qué te ayudo ahora?", bu_key)
                await send_menu(platform, user_id, business_unit)
                chat_state.context.pop('awaiting_group_invitation', None)
                chat_state.context.pop('invitation_name', None)
                chat_state.context.pop('invitation_apellido', None)
                chat_state.state = "idle"
                await sync_to_async(chat_state.save)()
                logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")
            else:
                await send_message(platform, user_id, "Por favor, selecciona 'Sí' o 'No'.", bu_key)
            return

    async def invite_known_person(self, referrer: Person, name: str, apellido: str, phone_number: str):
        if not re.match(r"^\+\d{10,15}$", phone_number):
            raise ValueError("Número de teléfono inválido")
        invitado, created = await sync_to_async(Person.objects.get_or_create)(
            phone=phone_number, defaults={'nombre': name, 'apellido_paterno': apellido}
        )
        await sync_to_async(Invitacion.objects.create)(referrer=referrer, invitado=invitado)

    async def handle_job_selection(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        recommended_jobs = event.context.get('recommended_jobs', [])
        try:
            job_index = int(text.strip()) - 1
        except ValueError:
            resp = "Por favor, ingresa un número válido."
            await send_message(platform, user_id, resp, self.get_business_unit_key(business_unit))
            await self.store_bot_message(event, resp)
            return

        if 0 <= job_index < len(recommended_jobs):
            selected_job = recommended_jobs[job_index]
            buttons = [
                {'title': 'Aplicar', 'payload': f"apply_{job_index}"},
                {'title': 'Ver Detalles', 'payload': f"details_{job_index}"},
                {'title': 'Agendar Entrevista', 'payload': f"schedule_{job_index}"},
                {'title': 'Tips Entrevista', 'payload': f"tips_{job_index}"}
            ]
            resp = f"Has seleccionado: {selected_job['title']}. ¿Qué deseas hacer?"
            await send_message(platform, user_id, resp, self.get_business_unit_key(business_unit), options=buttons)
            await self.store_bot_message(event, resp)
            event.context['selected_job'] = selected_job
            await sync_to_async(event.save)()
        else:
            resp = "Selección inválida."
            await send_message(platform, user_id, resp, self.get_business_unit_key(business_unit))
            await self.store_bot_message(event, resp)

    async def handle_job_action(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        recommended_jobs = event.context.get('recommended_jobs', [])
        if text.startswith("apply_"):
            job_index = int(text.split('_')[1])
            if 0 <= job_index < len(recommended_jobs):
                job = recommended_jobs[job_index]
                await sync_to_async(Application.objects.create)(user=user, vacancy_id=job['id'], status='applied')
                resp = "¡Has aplicado a la vacante con éxito!"
                await send_message(platform, user_id, resp, self.get_business_unit_key(business_unit))
                await self.store_bot_message(event, resp)
                await self.award_gamification_points(user, "job_application")
            else:
                resp = "No encuentro esa vacante."
                await send_message(platform, user_id, resp, self.get_business_unit_key(business_unit))
                await self.store_bot_message(event, resp)
        elif text.startswith("details_"):
            job_index = int(text.split('_')[1])
            if 0 <= job_index < len(recommended_jobs):
                job = recommended_jobs[job_index]
                details = job.get('description', 'No hay descripción disponible.')
                resp = f"Detalles de la posición:\n{details}"
                await send_message(platform, user_id, resp, self.get_business_unit_key(business_unit))
                await self.store_bot_message(event, resp)
            else:
                resp = "No encuentro esa vacante."
                await send_message(platform, user_id, resp, self.get_business_unit_key(business_unit))
                await self.store_bot_message(event, resp)
        elif text.startswith("schedule_"):
            job_index = int(text.split('_')[1])
            if 0 <= job_index < len(recommended_jobs):
                selected_job = recommended_jobs[job_index]
                slots = await self.get_interview_slots(selected_job)
                if not slots:
                    resp = "No hay horarios disponibles por el momento."
                    await send_message(platform, user_id, resp, self.get_business_unit_key(business_unit))
                    await self.store_bot_message(event, resp)
                    return
                buttons = [{'title': slot['label'], 'payload': f"book_slot_{idx}"} for idx, slot in enumerate(slots)]
                event.context['available_slots'] = slots
                event.context['selected_job'] = selected_job
                await sync_to_async(event.save)()
                resp = "Elige un horario para la entrevista:"
                await send_message(platform, user_id, resp, self.get_business_unit_key(business_unit), options=buttons)
                await self.store_bot_message(event, resp)
            else:
                resp = "No encuentro esa vacante."
                await send_message(platform, user_id, resp, self.get_business_unit_key(business_unit))
                await self.store_bot_message(event, resp)
        elif text.startswith("tips_"):
            job_index = int(text.split('_')[1])
            prompt = "Dame consejos para la entrevista en esta posición"
            response = await self.generate_dynamic_response(user, event, prompt, {}, {})
            if not response:
                response = "Prepárate, investiga la empresa, sé puntual y comunica tus logros con seguridad."
            await send_message(platform, user_id, response, self.get_business_unit_key(business_unit))
            await self.store_bot_message(event, response)
        elif text.startswith("book_slot_"):
            slot_index = int(text.split('_')[2])
            available_slots = event.context.get('available_slots', [])
            if 0 <= slot_index < len(available_slots):
                selected_slot = available_slots[slot_index]
                resp = f"Entrevista agendada para {selected_slot['label']} ¡Éxito!"
                await send_message(platform, user_id, resp, self.get_business_unit_key(business_unit))
                await self.store_bot_message(event, resp)
            else:
                resp = "No encuentro ese horario."
                await send_message(platform, user_id, resp, self.get_business_unit_key(business_unit))
                await self.store_bot_message(event, resp)

    async def get_interview_slots(self, job: Dict[str, Any]) -> List[Dict[str, str]]:
        return [
            {'label': 'Mañana 10:00 AM', 'datetime': '2024-12-10T10:00:00'},
            {'label': 'Mañana 11:00 AM', 'datetime': '2024-12-10T11:00:00'}
        ]

    async def handle_hiring_event(self, user: Person, business_unit: BusinessUnit, chat_state: ChatState):
        if self.get_business_unit_key(business_unit) == "amigro":
            from app.com.chatbot.workflow.amigro import notify_legal_on_hire
            await sync_to_async(notify_legal_on_hire.delay)(user.id)
        elif self.get_business_unit_key(business_unit) == "huntu":
            from app.com.chatbot.workflow.huntu import process_huntu_candidate
            await sync_to_async(process_huntu_candidate.delay)(user.id)
        elif self.get_business_unit_key(business_unit) == "huntred":
            from app.com.chatbot.workflow.huntred import process_huntred_candidate
            await sync_to_async(process_huntred_candidate.delay)(user.id)
        elif self.get_business_unit_key(business_unit) == "huntred executive":
            from app.com.chatbot.workflow.huntred_executive import process_huntred_executive_candidate
            await sync_to_async(process_huntred_executive_candidate.delay)(user.id)

        message = "Tu contratación ha sido registrada correctamente."
        await send_message(chat_state.platform, user.phone, message, self.get_business_unit_key(business_unit))
        await self.store_bot_message(chat_state, message)
        logger.info(f"Contratación registrada para {user.full_name} en {self.get_business_unit_key(business_unit)}")

    async def handle_client_selection(self, client_id: int, candidate_id: int, business_unit: BusinessUnit):
        candidate = await sync_to_async(Person.objects.get)(id=candidate_id)
        process = await sync_to_async(Vacante.objects.filter(candidate=candidate).first)()
        if not process:
            return "El candidato no está en un proceso activo."
        file_path = generate_and_send_contract(candidate, process.client, process.job_position, business_unit)
        await send_message(
            platform="whatsapp",
            user_id=candidate.phone,
            message="Se ha generado tu Carta Propuesta. Por favor, revisa tu correo y firma el documento.",
            business_unit=self.get_business_unit_key(business_unit)
        )
        return f"Carta Propuesta enviada para {candidate.full_name} en {self.get_business_unit_key(business_unit)}"

    async def check_inactive_sessions(self, inactivity_threshold: int = 300):
        threshold_time = timezone.now() - timezone.timedelta(seconds=inactivity_threshold)
        inactive_sessions = await sync_to_async(
            lambda: list(ChatState.objects.filter(last_interaction_at__lt=threshold_time))
        )()
        for session in inactive_sessions:
            if not session.conversation_history or not any("¿Sigues ahí?" in m.get("content", "") for m in session.conversation_history):
                await send_message(session.platform, session.user_id, "¿Sigues ahí?", self.get_business_unit_key(session.business_unit))
                await self.store_bot_message(session, "¿Sigues ahí?")
                logger.info(f"Mensaje de inactividad enviado a {session.user_id}")

    async def present_job_listings(platform: str, user_id: str, jobs: List[Dict[str, Any]], 
                               business_unit: BusinessUnit, chat_state: ChatState, page: int = 0, 
                               jobs_per_page: int = 3, filters: Dict[str, Any] = None) -> None:
        try:
            async with asyncio.timeout(10):  # Timeout de 10 segundos
                filters = filters or {}
                filtered_jobs = jobs
                if 'location' in filters:
                    filtered_jobs = [job for job in filtered_jobs if filters['location'].lower() in job.get('location', '').lower()]
                if 'min_salary' in filters:
                    filtered_jobs = [job for job in filtered_jobs if float(job.get('salary', 0)) >= filters['min_salary']]
                
                if not filtered_jobs:
                    await send_message(platform, user_id, "No encontré vacantes que coincidan con tus filtros.", business_unit.name.lower())
                    return
                
                total_jobs = len(filtered_jobs)
                start_idx = page * jobs_per_page
                end_idx = min(start_idx + jobs_per_page, total_jobs)
                
                response = f"Encontré {total_jobs} vacantes. Aquí tienes algunas (página {page + 1} de {total_jobs // jobs_per_page + 1}):\n"
                job_options = []
                for idx, job in enumerate(filtered_jobs[start_idx:end_idx], start=start_idx + 1):
                    salary = f"${job.get('salary', 'N/A')}" if job.get('salary') else "N/A"
                    location = job.get('location', 'No especificada')
                    response += f"{idx}. {job['title']} en {job.get('company', 'N/A')} ({location}, Salario: {salary})\n"
                    job_options.append({"title": f"Vacante {idx}", "payload": f"job_{idx}"})
                
                navigation_options = []
                if start_idx > 0:
                    navigation_options.append({"title": "⬅️ Anterior", "payload": f"jobs_page_{page - 1}"})
                if end_idx < total_jobs:
                    navigation_options.append({"title": "➡️ Siguiente", "payload": f"jobs_page_{page + 1}"})
                
                all_options = job_options + navigation_options
                await send_message(platform, user_id, response, business_unit.name.lower(), options=all_options if all_options else None)
                chat_state.context['current_jobs_page'] = page
                await sync_to_async(chat_state.save)()
                logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout al presentar vacantes para user_id={user_id}")
            await send_message(platform, user_id, "Lo siento, tardé demasiado en mostrar las vacantes. Intenta de nuevo.", business_unit.name.lower())

    async def send_profile_completion_email(self, user_id: str, context: dict):
        try:
            user = await sync_to_async(Person.objects.get)(phone=user_id)
            if not user.email:
                logger.warning(f"Usuario con phone {user_id} no tiene email registrado.")
                return
            business_unit = user.businessunit_set.first()
            configuracion_bu = await sync_to_async(ConfiguracionBU.objects.get)(business_unit=business_unit)
            dominio_bu = configuracion_bu.dominio_bu if configuracion_bu else "tu_dominio.com"
            subject = f"Completa tu perfil en {self.get_business_unit_key(business_unit)} ({dominio_bu})"
            body = f"Hola {user.nombre},\n\nPor favor completa tu perfil en {dominio_bu} para continuar."
            await send_email(business_unit_name=self.get_business_unit_key(business_unit), subject=subject, to_email=user.email, body=body)
            logger.info(f"Correo de completación enviado a {user.email}")
        except (Person.DoesNotExist, ConfiguracionBU.DoesNotExist) as e:
            logger.error(f"Error enviando correo de perfil a {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error enviando correo de perfil a {user_id}: {e}", exc_info=True)

    async def recap_information(self, user: Person) -> str:
        info_fields = {
            "Nombre": user.nombre,
            "Apellido Paterno": user.apellido_paterno,
            "Apellido Materno": user.apellido_materno,
            "Fecha de Nacimiento": user.fecha_nacimiento,
            "Sexo": user.sexo,
            "Nacionalidad": user.nacionalidad,
            "Permiso de Trabajo": user.metadata.get('migratory_status', {}).get('permiso_trabajo'),
            "CURP": user.metadata.get('curp'),
            "Ubicación": user.metadata.get('ubicacion'),
            "Experiencia Laboral": user.work_experience,
            "Nivel Salarial Esperado": user.salary_data.get('expected_salary')
        }
        recap_lines = ["Recapitulación de tu información:"]
        faltante = []
        for etiqueta, valor in info_fields.items():
            if valor:
                recap_lines.append(f"{etiqueta}: {valor}")
            else:
                faltante.append(etiqueta)
        if faltante:
            recap_lines.append("\nInformación faltante: " + ", ".join(faltante))
        else:
            recap_lines.append("\nToda la información está completa.")
        recap_lines.append("\n¿Es correcta esta información? Responde 'Sí' o 'No'.")
        return "\n".join(recap_lines)

    async def handle_cv_upload(self, user: Person, uploaded_file) -> str:
        person, created = await sync_to_async(Person.objects.get_or_create)(
            phone=user.phone, defaults={'nombre': user.nombre}
        )
        person.cv_file = uploaded_file
        person.cv_parsed = False
        await sync_to_async(person.save)()
        return "Tu CV ha sido recibido y será analizado."

    async def award_gamification_points(self, user: Person, activity_type: str):
        try:
            profile, created = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get_or_create)(
                user=user, defaults={'points': 0, 'level': 1}
            )
            await sync_to_async(profile.award_points)(activity_type)
            await sync_to_async(profile.save)()
            await self.notify_user_gamification_update(user, activity_type)
        except Exception as e:
            logger.error(f"Error otorgando puntos de gamificación a {user.id}: {e}", exc_info=True)

    async def notify_user_gamification_update(self, user: Person, activity_type: str):
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            message = f"¡Has ganado puntos por {activity_type}! Ahora tienes {profile.points} puntos."
            platform = user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp'
            business_unit = user.chat_state.business_unit if hasattr(user, 'chat_state') else user.businessunit_set.first()
            if platform and business_unit:
                await send_message(platform, user.phone, message, self.get_business_unit_key(business_unit))
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            logger.warning(f"No se encontró perfil de gamificación para {user.nombre}")
        except Exception as e:
            logger.error(f"Error notificando gamificación a {user.nombre}: {e}", exc_info=True)

    async def generate_challenges(self, user: Person) -> List[str]:
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            return await sync_to_async(profile.generate_networking_challenges)()
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            return []

    async def notify_user_challenges(self, user: Person):
        challenges = await self.generate_challenges(user)
        if challenges:
            message = f"Tienes nuevos desafíos: {', '.join(challenges)}"
            platform = user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp'
            business_unit = user.chat_state.business_unit if hasattr(user, 'chat_state') else user.businessunit_set.first()
            if platform and business_unit:
                await send_message(platform, user.phone, message, self.get_business_unit_key(business_unit))
    
    # Métodos para gestión de workflows
    async def start_talent_analysis_workflow(self, platform: str, user_id: str, business_unit: BusinessUnit, chat_state: ChatState, person: Person, **kwargs):
        """
        Inicia un nuevo workflow de análisis de talento para el usuario.
        
        Args:
            platform: Plataforma desde la que se inicia el workflow
            user_id: ID del usuario
            business_unit: Unidad de negocio
            chat_state: Estado actual del chat
            person: Persona asociada
            **kwargs: Argumentos adicionales para el workflow
        
        Returns:
            str: Mensaje inicial del workflow
        """
        try:
            # Creamos el contexto para el workflow
            workflow_context = {
                'user_id': user_id,
                'person_id': person.id,
                'business_unit': self.get_business_unit_key(business_unit),
                'chat_id': chat_state.id,
                'platform': platform,
                'created_at': timezone.now().isoformat()
            }
            
            # Añadimos argumentos adicionales al contexto
            workflow_context.update(kwargs)
            
            # Creamos una instancia del workflow
            workflow = await create_workflow('talent_analysis', **workflow_context)
            
            if not workflow:
                logger.error(f"No se pudo crear el workflow de análisis de talento para {user_id}")
                return "Lo siento, ha ocurrido un error al iniciar el análisis de talento. Por favor, inténtalo de nuevo más tarde."
                
            # Generamos un ID único para esta sesión de workflow
            session_id = f"talent_{user_id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Almacenamos la referencia al workflow activo
            self.active_workflows[session_id] = {
                'workflow': workflow,
                'user_id': user_id,
                'type': 'talent_analysis',
                'start_time': timezone.now(),
                'last_activity': timezone.now()
            }
            
            # Actualizamos el estado del chat
            chat_state.state = "TALENT_ANALYSIS_WORKFLOW"
            chat_state.context['active_workflow'] = session_id
            chat_state.context['workflow_type'] = 'talent_analysis'
            await sync_to_async(chat_state.save)()
            
            # Inicializamos el workflow y obtenemos el mensaje inicial
            initial_message = await workflow.initialize(workflow_context)
            
            # Enviamos el mensaje inicial
            await self.send_message(platform, user_id, {'text': initial_message}, business_unit)
            
            return initial_message
            
        except Exception as e:
            logger.error(f"Error iniciando workflow de análisis de talento: {e}", exc_info=True)
            return "Lo siento, ha ocurrido un error al iniciar el análisis de talento. Por favor, inténtalo de nuevo más tarde."
    
    async def start_cultural_fit_workflow(self, platform: str, user_id: str, business_unit: BusinessUnit, chat_state: ChatState, person: Person, **kwargs):
        """
        Inicia un nuevo workflow de compatibilidad cultural para el usuario.
        
        Args:
            platform: Plataforma desde la que se inicia el workflow
            user_id: ID del usuario
            business_unit: Unidad de negocio
            chat_state: Estado actual del chat
            person: Persona asociada
            **kwargs: Argumentos adicionales para el workflow
            
        Returns:
            str: Mensaje inicial del workflow
        """
        try:
            # Creamos el contexto para el workflow
            workflow_context = {
                'user_id': user_id,
                'person_id': person.id,
                'business_unit': self.get_business_unit_key(business_unit),
                'chat_id': chat_state.id,
                'platform': platform,
                'domain': kwargs.get('domain', 'general'),
                'created_at': timezone.now().isoformat()
            }
            
            # Si hay una empresa objetivo, la añadimos al contexto
            if 'target_company_id' in kwargs:
                workflow_context['target_entity_type'] = 'COMPANY'
                workflow_context['target_entity_id'] = kwargs['target_company_id']
                
            # Creamos una instancia del workflow
            workflow = await create_workflow('cultural_fit', **workflow_context)
            
            if not workflow:
                logger.error(f"No se pudo crear el workflow de compatibilidad cultural para {user_id}")
                return "Lo siento, ha ocurrido un error al iniciar el análisis de compatibilidad cultural. Por favor, inténtalo de nuevo más tarde."
                
            # Generamos un ID único para esta sesión de workflow
            session_id = f"cultural_{user_id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Almacenamos la referencia al workflow activo
            self.active_workflows[session_id] = {
                'workflow': workflow,
                'user_id': user_id,
                'type': 'cultural_fit',
                'start_time': timezone.now(),
                'last_activity': timezone.now()
            }
            
            # Actualizamos el estado del chat
            chat_state.state = "CULTURAL_FIT_WORKFLOW"
            chat_state.context['active_workflow'] = session_id
            chat_state.context['workflow_type'] = 'cultural_fit'
            await sync_to_async(chat_state.save)()
            
            # Inicializamos el workflow y obtenemos el mensaje inicial
            initial_message = await workflow.initialize(workflow_context)
            
            # Enviamos el mensaje inicial
            await self.send_message(platform, user_id, {'text': initial_message}, business_unit)
            
            return initial_message
            
        except Exception as e:
            logger.error(f"Error iniciando workflow de compatibilidad cultural: {e}", exc_info=True)
            return "Lo siento, ha ocurrido un error al iniciar el análisis de compatibilidad cultural. Por favor, inténtalo de nuevo más tarde."
    
    async def handle_workflow_message(self, platform: str, user_id: str, message_text: str, chat_state: ChatState, business_unit: BusinessUnit, person: Person):
        """
        Maneja un mensaje dentro de un workflow activo.
        
        Args:
            platform: Plataforma desde la que llega el mensaje
            user_id: ID del usuario
            message_text: Texto del mensaje
            chat_state: Estado actual del chat
            business_unit: Unidad de negocio
            person: Persona asociada
            
        Returns:
            bool: True si el mensaje fue manejado por un workflow, False en caso contrario
        """
        # Verificamos si hay un workflow activo
        session_id = chat_state.context.get('active_workflow')
        
        if not session_id or session_id not in self.active_workflows:
            return False
            
        workflow_info = self.active_workflows[session_id]
        workflow_info['last_activity'] = timezone.now()
        
        try:
            # Procesamos el mensaje con el workflow
            response = await handle_workflow_message(session_id, message_text)
            
            if response:
                # Enviamos la respuesta al usuario
                await self.send_message(platform, user_id, {'text': response}, business_unit)
                
                # Verificamos si el workflow ha finalizado
                workflow = workflow_info.get('workflow')
                if workflow and await workflow.is_completed():
                    # Limpiamos el workflow
                    self.active_workflows.pop(session_id, None)
                    
                    # Actualizamos el estado del chat
                    chat_state.state = "CONVERSACIONAL"  # Volvemos al estado normal
                    chat_state.context.pop('active_workflow', None)
                    await sync_to_async(chat_state.save)()
                    
                    # Notificamos que se ha completado el workflow
                    logger.info(f"Workflow {workflow_info['type']} completado para {user_id}")
                    
                    # Gamificación por completar el workflow
                    await self.award_gamification_points(person, f"completar_{workflow_info['type']}")
                
                return True
        except Exception as e:
            logger.error(f"Error procesando mensaje en workflow: {e}", exc_info=True)
            
            # Enviamos un mensaje de error y abortamos el workflow
            await self.send_message(
                platform, 
                user_id, 
                {'text': "Lo siento, ha ocurrido un error procesando tu mensaje. Por favor, intenta de nuevo más tarde."}, 
                business_unit
            )
            
            # Limpiamos el workflow
            self.active_workflows.pop(session_id, None)
            
            # Actualizamos el estado del chat
            chat_state.state = "CONVERSACIONAL"  # Volvemos al estado normal
            chat_state.context.pop('active_workflow', None)
            await sync_to_async(chat_state.save)()
            
            return True
            
        return False

    async def store_user_message(self, chat_state, text: str):
        """Almacena el mensaje del usuario usando el ContextManager."""
        await self.context_manager.update_context({
            'last_message': text,
            'timestamp': timezone.now(),
            'role': 'user'
        })

    async def store_bot_message(self, chat_state, text: str):
        """Almacena el mensaje del bot usando el ContextManager."""
        await self.context_manager.update_context({
            'last_bot_message': text,
            'timestamp': timezone.now(),
            'role': 'assistant'
        })

    async def handle_tos_acceptance(self, platform: str, user_id: str, text: str, chat_state: ChatState, business_unit: BusinessUnit, user: Person):
        """Maneja la aceptación de los TOS usando el nuevo sistema modular."""
        bu_key = self.get_business_unit_key(business_unit)
        
        # Actualizar contexto usando ContextManager
        await self.context_manager.update_context({
            'tos_attempts': chat_state.context.get('tos_attempts', 0),
            'last_tos_response': text
        })
        
        # Determinar siguiente estado usando StateManager
        next_state = await self.state_manager.determine_next_state(text)
        
        # Generar respuesta usando ResponseGenerator
        response = await self.response_generator.generate_response(
            intent='tos_acceptance',
            state=next_state
        )
        
        # Enviar mensaje usando MessageService
        await self.message_service.send_message(
            platform,
            user_id,
            response['text']
        )
        
        # Actualizar estado usando StateManager
        await self.state_manager.update_state(chat_state, next_state)
        
        logger.info(f"[process_message] Usuario: {user.id}, Estado del chat: {chat_state.state}")
        