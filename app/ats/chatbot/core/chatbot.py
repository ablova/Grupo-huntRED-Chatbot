# /home/pablo/app/ats/chatbot/core/chatbot.py
"""
Chatbot principal para Grupo huntRED®.
"""
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
from datetime import timedelta

# Importaciones de Django
from django.core.exceptions import ValidationError
from django.conf import settings

# Importaciones de modelos
from app.models import (
    ChatState, Person, GptApi, Application, Invitacion, 
    BusinessUnit, ConfiguracionBU, Vacante, WhatsAppAPI, 
    EnhancedNetworkGamificationProfile
)

# Importaciones de componentes
from app.ats.chatbot.flow.conversational_flow import ConversationalFlowManager
from app.ats.chatbot.core.intents_handler import IntentsHandler
from app.ats.chatbot.components.context_manager import ConversationContext as ContextManager
from app.ats.chatbot.components.response_generator import ResponseGenerator
from app.ats.chatbot.components.chat_state_manager import ChatStateManager
from app.ats.chatbot.components.channel_config import ChannelConfig
from app.ats.chatbot.components.rate_limiter import RateLimiter

# Importaciones de servicios
from app.ats.integrations.services import MessageService
# TODO: Implementar gamification_service
# from app.ats.integrations.services.gamification import gamification_service
from app.ats.integrations.services.document import CVParser

# Importaciones de NLP
from app.ats.chatbot.nlp.nlp import NLPProcessor

# Importaciones de middleware
from app.ats.chatbot.middleware.message_retry import MessageRetry

# Importaciones de workflow (cargadas bajo demanda)
from app.ats.chatbot.workflow.common.common import (
    generate_and_send_contract,
    iniciar_creacion_perfil,
    iniciar_perfil_conversacional,
    obtener_explicaciones_metodos
)

# Importaciones de business units
from app.ats.chatbot.workflow.business_units.huntred.huntred import process_huntred_candidate
from app.ats.chatbot.workflow.business_units.huntred_executive import process_huntred_executive_candidate
from app.ats.chatbot.workflow.business_units.huntu.huntu import process_huntu_candidate
from app.ats.chatbot.workflow.business_units.amigro.amigro import process_amigro_candidate
from app.ats.chatbot.workflow.business_units.sexsi.sexsi import (
    process_sexsi_payment,
    iniciar_flujo_sexsi,
    confirmar_pago_sexsi
)

from app.ats.chatbot.flow import FeedbackFlowManager
from app.ats.chatbot.components.intent_detector import IntentDetector
from app.ats.notifications.notification_manager import SkillFeedbackNotificationManager
from app.ats.onboarding.managers import OnboardingManager

logger = logging.getLogger('chatbot')

# Configuración
CACHE_ENABLED = True
CACHE_TIMEOUT = 600  # 10 minutos
GPT_ENABLED = True
ML_ENABLED = True
NLP_ENABLED = True

class ChatBotHandler:
    def __init__(self):
        # Importación a nivel de método para evitar dependencias circulares
        from app.ats.chatbot.core.gpt import GPTHandler
        self.gpt_handler = GPTHandler()
        
        # ✅ Workflow mapping optimizado - la mayoría sin GPT
        self.workflow_mapping = {
            "amigro": process_amigro_candidate,
            "huntu": process_huntu_candidate,
            "huntred": process_huntred_candidate,
            "huntred executive": process_huntred_executive_candidate,
            "sexsi": iniciar_flujo_sexsi,
            "talent_analysis": self.start_talent_analysis_workflow,
            "cultural_fit": self.start_cultural_fit_workflow
        }
        
        # ✅ Respuestas predefinidas por BU - sin costo de GPT
        self.initial_messages = {
            "default": [
                "Bienvenido a nuestra plataforma 🎉",
                "Al conversar, aceptas nuestros Términos de Servicio (TOS).",
                "¡Cuéntame, en qué puedo ayudarte hoy?"
            ],
            "amigro": [
                "Bienvenido a Amigro - amigro.org, somos una organización que facilitamos el acceso laboral a mexicanos regresando y migrantes de Latinoamérica ingresando a México, mediante Inteligencia Artificial Conversacional",
                "Por lo que platicaremos un poco de tu trayectoria profesional, tus intereses, tu situación migratoria, etc. Es importante ser lo más preciso posible, ya que con eso podremos identificar las mejores oportunidades para tí, tu familia, y en caso de venir en grupo, favorecerlo. *Por cierto Al iniciar, confirmas la aceptación de nuestros TOS."
            ],
            "huntred": [
                "¡Bienvenido a huntRED®! 🎯",
                "Somos especialistas en reclutamiento de middle y top management.",
                "Te ayudaré a encontrar las mejores oportunidades para tu carrera profesional.",
                "Al continuar, aceptas nuestros Términos de Servicio."
            ],
            "huntu": [
                "¡Bienvenido a huntU®! 🚀",
                "Somos expertos en conectar talento joven con grandes oportunidades.",
                "Te guiaré en tu proceso de reclutamiento paso a paso.",
                "Al continuar, aceptas nuestros Términos de Servicio."
            ],
            "huntred_executive": [
                "¡Bienvenido a huntRED® Executive! 👔",
                "Especialistas en reclutamiento para C-level y board.",
                "Te acompañaré en tu proceso de selección ejecutiva.",
                "Al continuar, aceptas nuestros Términos de Servicio."
            ],
            "sexsi": [
                "¡Bienvenido a SEXSI®! 💼",
                "Plataforma especializada en contratos íntimos.",
                "Te ayudaré a gestionar tus contratos de manera segura.",
                "Al continuar, aceptas nuestros Términos de Servicio."
            ]
        }
        
        # ✅ Respuestas de error predefinidas - sin GPT
        self.error_responses = {
            "timeout": "La solicitud está tomando más tiempo de lo esperado. Por favor, inténtalo de nuevo.",
            "invalid": "No entiendo tu solicitud. ¿Podrías reformularla?",
            "error": "Lo siento, ha ocurrido un error. Por favor, inténtalo de nuevo.",
            "quota_exceeded": "Estamos experimentando alta demanda. Por favor, inténtalo en unos minutos.",
            "maintenance": "El sistema está en mantenimiento. Por favor, inténtalo más tarde."
        }
        
        # ✅ Estados de conversación predefinidos
        self.conversation_states = {
            "initial": "Bienvenida y presentación",
            "profile_creation": "Creación de perfil profesional",
            "job_selection": "Selección de oportunidades laborales",
            "interview_scheduling": "Agendamiento de entrevistas",
            "offer_management": "Gestión de ofertas y contratos",
            "feedback": "Recopilación de feedback",
            "onboarding": "Proceso de onboarding"
        }
        
        # Inicializar componentes del nuevo sistema modular
        self.conversational_flow = ConversationalFlowManager()
        self.intents_manager = IntentsHandler()
        self.context_manager = ContextManager()
        self.response_generator = ResponseGenerator()
        self.state_manager = ChatStateManager()
        self.message_service = MessageService()
        # TODO: Implementar gamification_service
        # from app.ats.integrations.services.gamification import gamification_service
        # self.gamification_service = gamification_service
        self.gamification_service = None
        self.cv_parser = CVParser()
        
        # Inicializar el gestor de workflows
        # Importación a nivel de método para evitar dependencias circulares
        from app.ats.chatbot.workflow import WorkflowManager
        self.workflow_manager = WorkflowManager()
        self.active_workflows = {}
        
        try:
            self.nlp_processor = NLPProcessor(language='es', mode='candidate', analysis_depth='quick')
        except Exception as e:
            logger.error(f"Error inicializando NLPProcessor: {e}")
            self.nlp_processor = None if NLP_ENABLED else None

        self.feedback_manager = FeedbackFlowManager()
        self.intent_detector = IntentDetector()
        self.onboarding_manager = OnboardingManager()

    def get_business_unit_key(self, business_unit) -> str:
        """Obtiene una clave segura para el business unit."""
        try:
            if hasattr(business_unit, 'name'):
                return str(business_unit.name).lower().replace('®', '').strip()
        except Exception as e:
            logger.error(f"Error obteniendo business unit key: {e}")
        return 'default'

    @MessageRetry.with_retry()
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
        
        try:
            # ✅ Obtener o crear usuario y estado del chat
            user, chat_state = await self._get_or_create_user_and_chat_state(user_id, platform, business_unit, payload)
            
            # ✅ Extraer contenido del mensaje
            text, entities = self._extract_message_content(message)
            
            # ✅ Detectar intent usando sistema local (sin GPT)
            intent = await self._detect_intent_local(text, business_unit)
            
            # ✅ Procesar según el intent detectado
            if intent in self.workflow_mapping:
                # Usar workflow específico sin GPT
                response = await self.workflow_mapping[intent](platform, user_id, text, chat_state, business_unit, user)
            else:
                # ✅ Generar respuesta usando sistema local
                response = await self._generate_response_local(user, chat_state, text, intent, business_unit)
            
            # ✅ Enviar respuesta
            await self.send_message(platform, user_id, response, business_unit)
            
            return {'success': True, 'response': response}
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            error_response = self.error_responses.get("error", "Error inesperado")
            await self.send_message(platform, user_id, error_response, business_unit)
            return {'success': False, 'error': str(e)}

    async def _detect_intent_local(self, text: str, business_unit: BusinessUnit) -> str:
        """✅ Detecta intent usando sistema local sin GPT"""
        text_lower = text.lower()
        
        # Patrones específicos por BU
        if business_unit.name.lower() == "amigro":
            if any(word in text_lower for word in ["hola", "buenos días", "buenas"]):
                return "greeting"
            elif any(word in text_lower for word in ["perfil", "información", "datos"]):
                return "profile_creation"
            elif any(word in text_lower for word in ["trabajo", "empleo", "oportunidad"]):
                return "job_search"
            elif any(word in text_lower for word in ["migrante", "migración", "visa"]):
                return "migration_info"
        
        elif business_unit.name.lower() == "huntred":
            if any(word in text_lower for word in ["hola", "buenos días", "buenas"]):
                return "greeting"
            elif any(word in text_lower for word in ["perfil", "cv", "experiencia"]):
                return "profile_creation"
            elif any(word in text_lower for word in ["oportunidad", "vacante", "puesto"]):
                return "job_search"
            elif any(word in text_lower for word in ["entrevista", "cita", "agendar"]):
                return "interview_scheduling"
        
        # Patrones generales
        if any(word in text_lower for word in ["hola", "buenos días", "buenas", "hi", "hello"]):
            return "greeting"
        elif any(word in text_lower for word in ["ayuda", "help", "soporte"]):
            return "help"
        elif any(word in text_lower for word in ["perfil", "información", "datos"]):
            return "profile_creation"
        elif any(word in text_lower for word in ["trabajo", "empleo", "oportunidad", "vacante"]):
            return "job_search"
        elif any(word in text_lower for word in ["entrevista", "cita", "agendar"]):
            return "interview_scheduling"
        elif any(word in text_lower for word in ["oferta", "contrato", "salario"]):
            return "offer_management"
        elif any(word in text_lower for word in ["feedback", "opinión", "sugerencia"]):
            return "feedback"
        
        return "unknown"

    async def _generate_response_local(self, user: Person, chat_state: ChatState, text: str, intent: str, business_unit: BusinessUnit) -> str:
        """✅ Genera respuesta usando sistema local sin GPT"""
        
        # Respuestas específicas por intent y BU
        if intent == "greeting":
            bu_key = self.get_business_unit_key(business_unit)
            if bu_key in self.initial_messages:
                return self.initial_messages[bu_key][0]
            return self.initial_messages["default"][0]
        
        elif intent == "help":
            return "Te ayudo con:\n• Crear tu perfil profesional\n• Buscar oportunidades laborales\n• Agendar entrevistas\n• Gestionar ofertas\n\n¿En qué puedo ayudarte?"
        
        elif intent == "profile_creation":
            return "Perfecto, vamos a crear tu perfil profesional. Te haré algunas preguntas para conocer mejor tu experiencia y objetivos. ¿Estás listo para comenzar?"
        
        elif intent == "job_search":
            return "Excelente, te ayudo a encontrar las mejores oportunidades. ¿En qué área te gustaría trabajar? ¿Tienes alguna preferencia de ubicación o salario?"
        
        elif intent == "interview_scheduling":
            return "Perfecto, te ayudo a agendar tu entrevista. ¿Qué día y hora te funciona mejor? Tenemos disponibilidad en diferentes horarios."
        
        elif intent == "offer_management":
            return "Te ayudo con la gestión de ofertas. ¿Ya recibiste una oferta o necesitas información sobre el proceso?"
        
        elif intent == "feedback":
            return "Me encantaría escuchar tu feedback. ¿Cómo ha sido tu experiencia con nosotros? ¿Hay algo que podamos mejorar?"
        
        # Respuesta por defecto
        return "Entiendo tu mensaje. Te ayudo a encontrar la mejor manera de asistirte. ¿Podrías ser más específico sobre lo que necesitas?"

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
            from app.ats.utils.parser import parse_document
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
        from app.ats.integrations.services import MessageService
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
            from app.ats.chatbot.workflow.amigro import notify_legal_on_hire
            await sync_to_async(notify_legal_on_hire.delay)(user.id)
        elif self.get_business_unit_key(business_unit) == "huntu":
            from app.ats.chatbot.workflow.huntu import process_huntu_candidate
            await sync_to_async(process_huntu_candidate.delay)(user.id)
        elif self.get_business_unit_key(business_unit) == "huntred":
            from app.ats.chatbot.workflow.huntred import process_huntred_candidate
            await sync_to_async(process_huntred_candidate.delay)(user.id)
        elif self.get_business_unit_key(business_unit) == "huntred executive":
            from app.ats.chatbot.workflow.huntred_executive import process_huntred_executive_candidate
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

    async def award_gamification_points(self, user: Person, activity_type: str, points: int = None, metadata: dict = None):
        """
        Otorga puntos de gamificación a un usuario por una actividad específica.
        
        Args:
            user: Usuario al que se le otorgan los puntos
            activity_type: Tipo de actividad (puede ser string o ActivityType)
            points: Cantidad de puntos a otorgar (opcional, se usará el valor por defecto si no se especifica)
            metadata: Metadatos adicionales para la actividad
        """
        try:
            from app.ats.integrations.services.gamification import ActivityType
            
            # Mapeo de tipos de actividad antiguos a los nuevos
            activity_mapping = {
                'job_application': ActivityType.JOB_APPLICATION,
                'profile_completion': ActivityType.PROFILE_COMPLETED,
                'test_completion': ActivityType.TEST_COMPLETED,
                'referral': ActivityType.REFERRAL_MADE,
                'connection': ActivityType.CONNECTION_MADE,
                'post_created': ActivityType.POST_CREATED,
                'comment_added': ActivityType.COMMENT_ADDED,
                'like_received': ActivityType.LIKE_RECEIVED
            }
            
            # Convertir a ActivityType si es necesario
            activity = activity_mapping.get(activity_type, activity_type)
            
            # Registrar la actividad
            result = await gamification_service.record_activity(
                user=user,
                activity_type=activity,
                xp_amount=points,
                metadata=metadata or {}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error en award_gamification_points para {user.id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def notify_user_gamification_update(self, user: Person, activity_type: str):
        """
        Notifica al usuario sobre actualizaciones de gamificación.
        Esta función ahora es manejada internamente por el servicio de gamificación.
        """
        pass  # Las notificaciones ahora se manejan en el servicio

    async def generate_challenges(self, user: Person) -> List[Dict]:
        """
        Genera desafíos personalizados para el usuario.
        
        Returns:
            Lista de diccionarios con información de los desafíos
        """
        from app.ats.integrations.services.gamification import gamification_service
        
        try:
            # Obtener desafíos del servicio de gamificación
            challenges = await gamification_service.generate_challenges(user)
            return challenges or []
        except Exception as e:
            logger.error(f"Error generando desafíos para {user.id}: {e}", exc_info=True)
            return []

    async def notify_user_challenges(self, user: Person):
        """
        Notifica al usuario sobre nuevos desafíos disponibles.
        """
        try:
            challenges = await self.generate_challenges(user)
            if challenges:
                # Formatear mensaje con los desafíos
                challenge_list = "\n".join([f"- {c.get('title', 'Nuevo desafío')}" for c in challenges])
                message = f"🎯 *Tienes nuevos desafíos disponibles:*\n\n{challenge_list}"
                
                # Obtener plataforma y business unit
                platform = user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp'
                business_unit = user.chat_state.business_unit if hasattr(user, 'chat_state') else user.businessunit_set.first()
                
                if platform and business_unit:
                    await send_message(platform, user.phone, message, self.get_business_unit_key(business_unit))
        except Exception as e:
            logger.error(f"Error notificando desafíos a {user.id}: {e}", exc_info=True)
    
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
        
    async def _handle_feedback_intent(self, person: Person, intent: str, message: str) -> Dict[str, Any]:
        """
        Maneja los intents relacionados con feedback.
        """
        try:
            if intent == 'feedback_request':
                # Extraer información del mensaje
                vacante_id = self._extract_vacante_id(message)
                candidate_id = self._extract_candidate_id(message)
                
                if not vacante_id or not candidate_id:
                    return {
                        'success': False,
                        'error': 'No se pudo identificar la vacante o el candidato'
                    }
                
                vacante = await Vacante.objects.aget(id=vacante_id)
                candidate = await Person.objects.aget(id=candidate_id)
                
                return await self.feedback_manager.handle_feedback_request(
                    person=person,
                    vacante=vacante,
                    candidate=candidate
                )
                
            elif intent == 'feedback_complete':
                # Extraer información del mensaje
                vacante_id = self._extract_vacante_id(message)
                candidate_id = self._extract_candidate_id(message)
                feedback_data = self._extract_feedback_data(message)
                
                if not vacante_id or not candidate_id or not feedback_data:
                    return {
                        'success': False,
                        'error': 'Faltan datos necesarios para completar el feedback'
                    }
                
                vacante = await Vacante.objects.aget(id=vacante_id)
                candidate = await Person.objects.aget(id=candidate_id)
                
                return await self.feedback_manager.handle_feedback_completion(
                    person=person,
                    vacante=vacante,
                    candidate=candidate,
                    feedback_data=feedback_data
                )
            
            return {
                'success': False,
                'error': 'Intent de feedback no reconocido'
            }
            
        except Exception as e:
            logger.error(f"Error handling feedback intent: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_onboarding_intent(self, person: Person, intent: str, message: str) -> Dict[str, Any]:
        """
        Maneja los intents relacionados con onboarding.
        """
        try:
            if intent == 'onboarding_start':
                return await self.onboarding_manager.start_onboarding(person)
            elif intent == 'onboarding_check_status':
                return await self.onboarding_manager.check_status(person)
            elif intent == 'onboarding_complete_step':
                step = self._extract_onboarding_step(message)
                return await self.onboarding_manager.complete_step(person, step)
            
            return {
                'success': False,
                'error': 'Intent de onboarding no reconocido'
            }
            
        except Exception as e:
            logger.error(f"Error handling onboarding intent: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_vacante_intent(self, person: Person, intent: str, message: str) -> Dict[str, Any]:
        """
        Maneja los intents relacionados con vacantes.
        """
        try:
            if intent == 'vacante_cierre_proximo':
                vacante_id = self._extract_vacante_id(message)
                if not vacante_id:
                    return {
                        'success': False,
                        'error': 'No se pudo identificar la vacante'
                    }
                
                vacante = await Vacante.objects.aget(id=vacante_id)
                return await self._handle_vacante_cierre(vacante)
            
            return {
                'success': False,
                'error': 'Intent de vacante no reconocido'
            }
            
        except Exception as e:
            logger.error(f"Error handling vacante intent: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_post_contratacion_intent(self, person: Person, intent: str, message: str) -> Dict[str, Any]:
        """
        Maneja los intents relacionados con el seguimiento post-contratación.
        """
        try:
            if intent == 'post_contratacion_feedback_candidato':
                return await self._handle_candidato_feedback(person)
            elif intent == 'post_contratacion_feedback_cliente':
                return await self._handle_cliente_feedback(person)
            elif intent == 'post_contratacion_check_in':
                return await self._handle_check_in(person)
            
            return {
                'success': False,
                'error': 'Intent de post-contratación no reconocido'
            }
            
        except Exception as e:
            logger.error(f"Error handling post-contratación intent: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_vacante_cierre(self, vacante: Vacante) -> Dict[str, Any]:
        """
        Maneja el proceso de cierre de una vacante.
        """
        try:
            # Notificar a todos los stakeholders
            notifications = []
            
            # Notificar al responsable del proceso
            if vacante.responsible:
                notifications.append(
                    await self.notification_manager.notify_vacante_cierre(
                        recipient=vacante.responsible,
                        vacante=vacante
                    )
                )
            
            # Notificar al contacto del cliente
            if vacante.empresa and vacante.empresa.contacto_principal:
                notifications.append(
                    await self.notification_manager.notify_vacante_cierre_cliente(
                        recipient=vacante.empresa.contacto_principal,
                        vacante=vacante
                    )
                )
            
            # Notificar a los candidatos en proceso
            for candidato in await vacante.candidatos_en_proceso.all():
                notifications.append(
                    await self.notification_manager.notify_vacante_cierre_candidato(
                        recipient=candidato,
                        vacante=vacante
                    )
                )
            
            return {
                'success': True,
                'notifications_sent': len(notifications)
            }
            
        except Exception as e:
            logger.error(f"Error handling vacante cierre: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_candidato_feedback(self, person: Person) -> Dict[str, Any]:
        """
        Maneja el feedback post-contratación del candidato.
        """
        try:
            # Obtener el proceso de onboarding asociado
            onboarding = await self.onboarding_manager.get_onboarding_for_person(person)
            
            if not onboarding:
                return {
                    'success': False,
                    'error': 'No se encontró un proceso de onboarding'
                }
            
            # Enviar encuesta de feedback
            return await self.onboarding_manager.send_feedback_survey(
                person=person,
                survey_type='candidato',
                onboarding=onboarding
            )
            
        except Exception as e:
            logger.error(f"Error handling candidato feedback: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_cliente_feedback(self, person: Person) -> Dict[str, Any]:
        """
        Maneja el feedback post-contratación del cliente.
        """
        try:
            # Obtener la empresa asociada
            empresa = await person.empresa_set.first()
            
            if not empresa:
                return {
                    'success': False,
                    'error': 'No se encontró una empresa asociada'
                }
            
            # Enviar encuesta de feedback
            return await self.onboarding_manager.send_feedback_survey(
                person=person,
                survey_type='cliente',
                empresa=empresa
            )
            
        except Exception as e:
            logger.error(f"Error handling cliente feedback: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_check_in(self, person: Person) -> Dict[str, Any]:
        """
        Maneja el check-in post-contratación.
        """
        try:
            # Obtener el proceso de onboarding asociado
            onboarding = await self.onboarding_manager.get_onboarding_for_person(person)
            
            if not onboarding:
                return {
                    'success': False,
                    'error': 'No se encontró un proceso de onboarding'
                }
            
            # Realizar check-in
            return await self.onboarding_manager.perform_check_in(
                person=person,
                onboarding=onboarding
            )
            
        except Exception as e:
            logger.error(f"Error handling check-in: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_vacante_id(self, message: str) -> Optional[int]:
        """
        Extrae el ID de la vacante del mensaje.
        """
        # Implementar lógica de extracción
        return None
    
    def _extract_candidate_id(self, message: str) -> Optional[int]:
        """
        Extrae el ID del candidato del mensaje.
        """
        # Implementar lógica de extracción
        return None
    
    def _extract_feedback_data(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Extrae los datos del feedback del mensaje.
        """
        # Implementar lógica de extracción
        return None
    
    def _extract_onboarding_step(self, message: str) -> Optional[str]:
        """
        Extrae el paso de onboarding del mensaje.
        """
        # Implementar lógica de extracción
        return None
        