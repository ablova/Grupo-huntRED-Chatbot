# /home/pablo/app/chatbot/chatbot.py
import logging
import asyncio
import re
from typing import Optional, List, Dict, Any, Tuple
from django.utils import timezone
from asgiref.sync import sync_to_async
from django.core.cache import cache

from app.models import (
    ChatState, Person, GptApi, Application, Invitacion, BusinessUnit, Vacante,
    WhatsAppAPI, EnhancedNetworkGamificationProfile, ConfiguracionBU
)
from app.chatbot.integrations.services import (
    send_email, send_message, send_options, send_menu, send_url, send_image, GamificationService
)
from app.chatbot.workflow.common import (
    generate_and_send_contract, iniciar_creacion_perfil, iniciar_perfil_conversacional,
    obtener_explicaciones_metodos
)
from app.chatbot.workflow.amigro import process_amigro_candidate
from app.chatbot.workflow.huntu import process_huntu_candidate
from app.chatbot.workflow.huntred import process_huntred_candidate
from app.chatbot.workflow.executive import process_executive_candidate
from app.chatbot.workflow.sexsi import iniciar_flujo_sexsi, confirmar_pago_sexsi
from app.utilidades.parser import CVParser
from app.chatbot.gpt import GPTHandler
from app.chatbot.intents_handler import detect_intents, handle_known_intents

logger = logging.getLogger(__name__)

# Configuración condicional
CACHE_ENABLED = True
GPT_ENABLED = True
ML_ENABLED = True
NLP_ENABLED = True

# Instancia global de NLPProcessor
if NLP_ENABLED:
    from app.chatbot.utils import analyze_text, is_spam_message, update_user_message_history, is_user_spamming
    from app.chatbot.nlp import NLPProcessor
    nlp_processor = NLPProcessor(language='es', mode='candidate', analysis_depth='quick')
    logger.info("✅ NLPProcessor inicializado globalmente")

CACHE_TIMEOUT = 600

class ChatBotHandler:
    def __init__(self):
        self.gpt_handler = GPTHandler()
        self.workflow_mapping = {
            "amigro": process_amigro_candidate,
            "huntu": process_huntu_candidate,
            "huntred": process_huntred_candidate,
            "huntred executive": process_executive_candidate,
            "sexsi": iniciar_flujo_sexsi
        }
        self.initial_messages = {
            "default": [
                "Bienvenido a nuestra plataforma 🎉",
                "Al conversar, aceptas nuestros Términos de Servicio (TOS).",
                "¡Cuéntame, en qué puedo ayudarte hoy?"
            ],
            "amigro": [
                "Bienvenido a Amigro® 🌍 - amigro.org, somos una organización que facilitamos el acceso laboral a mexicanos regresando y migrantes de Latinoamérica ingresando a México, mediante Inteligencia Artificial Conversacional",
                "Por lo que platicaremos un poco de tu trayectoria profesional, tus intereses, tu situación migratoria, etc. Es importante ser lo más preciso posible, ya que con eso podremos identificar las mejores oportunidades para tí, tu familia, y en caso de venir en grupo, favorecerlo. *Por cierto Al iniciar, confirmas la aceptación de nuestros TOS."
            ]
        }
        try:
            self.nlp_processor = NLPProcessor(language='es', mode='candidate', analysis_depth='quick')
        except Exception as e:
            logger.error(f"Error inicializando NLPProcessor: {e}")
            self.nlp_processor = None

    async def process_message(self, platform: str, user_id: str, message: dict, business_unit: BusinessUnit):
        """Procesa mensajes entrantes con lógica optimizada y manejo completo de flujos conversacionales."""
        message_id = message.get("messages", [{}])[0].get("id")
        if CACHE_ENABLED:
            cache_key = f"processed_message:{message_id}"
            if cache.get(cache_key):
                logger.info(f"Mensaje {message_id} ya procesado, ignorando.")
                return
            cache.set(cache_key, True, timeout=CACHE_TIMEOUT)

        logger.debug(f"[process_message] Iniciando procesamiento para {user_id}, mensaje ID: {message_id}")
        try:
            # Extraer contenido del mensaje
            text, attachment = self._extract_message_content(message)
            logger.info(f"[process_message] 📩 Mensaje recibido de {user_id} en {platform} para BU: {business_unit.name}: {text or 'attachment'}")

            # Obtener o crear usuario y estado de chat
            user, chat_state = await self._get_or_create_user_and_chat_state(user_id, platform, business_unit)

            # Estado inicial: enviar mensajes de bienvenida
            if chat_state.state == "initial":
                await self.send_complete_initial_messages(platform, user_id, business_unit)
                chat_state.state = "waiting_for_tos"
                await sync_to_async(chat_state.save)()
                return

            # Verificación de aceptación de TOS
            if not user.tos_accepted:
                await self.handle_tos_acceptance(platform, user_id, text, chat_state, business_unit, user)
                if text in ["tos_accept", "sí", "si"]:
                    chat_state.state = "profile_in_progress"
                    await sync_to_async(chat_state.save)()
                    await self.start_profile_creation(platform, user_id, business_unit, chat_state, user)
                return

            # Detección de SPAM y muteo
            if NLP_ENABLED and is_spam_message(user_id, text):
                if is_user_spamming(user_id):
                    cache.set(f"muted:{user_id}", True, timeout=60)  # Mute por 1 minuto
                    await send_message(platform, user_id, "⚠️ Demasiados mensajes similares, espera un momento.", business_unit.name.lower())
                else:
                    await send_message(platform, user_id, "⚠️ Por favor, no envíes mensajes repetidos.", business_unit.name.lower())
                return
            if cache.get(f"muted:{user_id}"):
                await send_message(platform, user_id, "⚠️ Estás temporalmente silenciado. Espera un momento.", business_unit.name.lower())
                return

            # Manejo de adjuntos (CV u otros documentos)
            if attachment:
                file_type = attachment.get("type", "")
                if file_type not in ["pdf", "application/pdf", "doc", "docx", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                    await send_message(platform, user_id, "Formato no soportado. Usa PDF o Word.", business_unit.name.lower())
                    return
                response = await self.handle_cv_upload(user, attachment.get("url", ""))
                await send_message(platform, user_id, response, business_unit.name.lower())
                await self.store_bot_message(chat_state, response)
                await self.award_gamification_points(user, "cv_upload")
                return

            # Almacenar mensaje del usuario si existe
            if text:
                await self.store_user_message(chat_state, text)

            # Detección y manejo de intents conocidos
            detected_intents = detect_intents(text) if text else []
            if detected_intents and await handle_known_intents(detected_intents, platform, user_id, chat_state, business_unit, user, text):
                return

            # Manejo de estados conversacionales
            if chat_state.state == "profile_in_progress":
                from app.chatbot.workflow.common import manejar_respuesta_perfil
                if await manejar_respuesta_perfil(platform, user_id, text, business_unit, chat_state, user, self.gpt_handler):
                    if self.is_profile_complete(user, business_unit):
                        chat_state.state = "waiting_for_cv_confirmation"
                        recap = await self.recap_information(user)
                        await send_message(platform, user_id, recap, business_unit.name.lower())
                        await sync_to_async(chat_state.save)()
                    return

            if chat_state.state == "waiting_for_cv_confirmation":
                if text.lower() == "sí":
                    chat_state.state = "profile_complete"
                    user.profile_complete = True
                    await sync_to_async(user.save)()
                    await sync_to_async(chat_state.save)()
                    await self.award_gamification_points(user, "profile_completion")
                    await send_message(platform, user_id, "¡Perfecto! Tu perfil está completo. ¿En qué te ayudo ahora?", business_unit.name.lower())
                    await send_menu(platform, user_id, business_unit)
                    await self.notify_user_challenges(user)
                elif text.lower() == "no":
                    await send_message(platform, user_id, "¿Qué dato necesitas corregir?", business_unit.name.lower())
                    chat_state.state = "profile_in_progress"
                    await sync_to_async(chat_state.save)()
                return

            # Manejo de invitaciones de grupo
            if chat_state.context.get("awaiting_group_invitation"):
                await self.handle_group_invitation_input(platform, user_id, text, chat_state, business_unit, user)
                return

            # Manejo de selección de vacantes
            if text.startswith("job_") or text.startswith("apply_") or text.startswith("details_") or text.startswith("schedule_") or text.startswith("tips_") or text.startswith("book_slot_"):
                await self.handle_job_action(platform, user_id, text, chat_state, business_unit, user)
                return

            # Flujos específicos por unidad de negocio
            bu_key = business_unit.name.lower()
            if bu_key in self.workflow_mapping and user.profile_complete:
                workflow_func = self.workflow_mapping[bu_key]
                if bu_key == "sexsi":
                    response = workflow_func(user_id, user, business_unit, chat_state.context)
                    await send_message(platform, user_id, response, bu_key)
                    await self.store_bot_message(chat_state, response)
                else:
                    await sync_to_async(workflow_func)(user.id)
                return

            # Respuesta por defecto con análisis NLP
            if NLP_ENABLED and self.nlp_processor:
                analysis = await self.nlp_processor.analyze(text)
                entities = analysis.get("entities", [])
                sentiment = analysis.get("sentiment", {})
            else:
                entities = []
                sentiment = {}
            response = await self._generate_default_response(user, chat_state, text, entities, sentiment)
            await send_message(platform, user_id, response, business_unit.name.lower())
            await self.store_bot_message(chat_state, response)
            logger.info(f"[process_message] ✅ Mensaje procesado y enviado exitosamente para {user_id}")

        except Exception as e:
            logger.error(f"Error en process_message: {e}", exc_info=True)
            await send_message(platform, user_id, "Ups, algo salió mal. Te comparto el menú:", business_unit.name.lower())
            await send_menu(platform, user_id, business_unit)

    async def initialize_chat_state(platform: str, user_id: str, business_unit: BusinessUnit) -> ChatState:
        chat_state, _ = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=user_id, platform=platform, business_unit=business_unit, defaults={'state': 'initial', 'context': {}}
        )
        return chat_state

    async def get_or_create_user(self, user_id: str, platform: str) -> Tuple[Person, bool]:
        """Obtiene o crea un usuario basado en el user_id y la plataforma."""
        user, created = await sync_to_async(Person.objects.get_or_create)(
            phone=user_id,  # Usamos user_id como identificador único
            defaults={
                'nombre': f"Usuario_{user_id}",  # Nombre genérico por defecto
                'platform': platform,           # Guardamos la plataforma
            }
        )
        return user, created

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

    async def _get_or_create_user_and_chat_state(self, user_id: str, platform: str, business_unit: BusinessUnit) -> Tuple[Person, ChatState]:
        user, _ = await self.get_or_create_user(user_id, platform)
        chat_state, created = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=user_id,
            business_unit=business_unit,
            defaults={'platform': platform, 'state': 'initial', 'context': {}}
        )
        current_person = await sync_to_async(lambda: chat_state.person)()
        if current_person != user or chat_state.platform != platform:
            chat_state.person = user
            chat_state.platform = platform
            await sync_to_async(chat_state.save)()
        user.number_interaction += 1
        await sync_to_async(user.save)()
        return user, chat_state

    async def _generate_default_response(self, user: Person, chat_state: ChatState, text: str, entities: List, sentiment: Dict) -> str:
        if not GPT_ENABLED:
            return "No entendí tu mensaje. ¿En qué puedo ayudarte?"
        return await self.generate_dynamic_response(user, chat_state, text, entities, sentiment)

    async def send_complete_initial_messages(self, platform: str, user_id: str, business_unit: BusinessUnit):
        bu_key = business_unit.name.lower()
        messages = self.initial_messages.get(bu_key, self.initial_messages["default"])
        for msg in messages:
            await send_message(platform, user_id, msg, bu_key)
            await asyncio.sleep(1)
        tos_url = self.get_tos_url(business_unit)
        await send_message(platform, user_id, f"📜 Revisa nuestros Términos de Servicio: {tos_url}. Es necesario aceptarlos.", bu_key)
        tos_buttons = [
            {'title': 'Sí, continuar', 'payload': 'tos_accept'},
            {'title': 'No', 'payload': 'tos_reject'}
        ]
        await send_options(platform, user_id, "¿Aceptas nuestros Términos de Servicio?", tos_buttons, bu_key)

    async def generate_dynamic_response(self, user: Person, chat_state: ChatState, user_message: str, entities: List, sentiment: Dict) -> str:
        history = chat_state.conversation_history or []
        prompt = ""
        for msg in history[-5:]:
            prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
        prompt += f"Usuario: {user_message}\nAsistente:"
        gpt_api = await sync_to_async(GptApi.objects.first)()
        if not gpt_api or self.gpt_handler.gpt_api is None:
            await self.gpt_handler.initialize()
        return await self.gpt_handler.generate_response(prompt, chat_state.business_unit)

    async def start_profile_creation(self, platform: str, user_id: str, business_unit: BusinessUnit, chat_state: ChatState, person: Person):
        """Start profile creation process."""
        await iniciar_creacion_perfil(platform, user_id, business_unit, chat_state, person)

    def is_profile_complete(self, person: Person, business_unit: BusinessUnit) -> bool:
        """Check if the user's profile is complete."""
        required_fields = ['nombre', 'apellido_paterno', 'email', 'phone']
        if business_unit.name.lower() == "amigro":
            required_fields.extend(['nacionalidad', 'metadata'])
        elif business_unit.name.lower() == "huntu":
            required_fields.append('work_experience')
        missing_fields = [field for field in required_fields if not getattr(person, field, None) or (field == 'metadata' and 'migratory_status' not in person.metadata)]
        return not missing_fields

    async def handle_status_email(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        """Handle email status check."""
        email_pattern = r"[^@]+@[^@]+\.[^@]+"
        if re.match(email_pattern, text):
            applications = await sync_to_async(Application.objects.filter)(user__email=text)
            application = await sync_to_async(applications.first)()
            msg = f"El estatus de tu aplicación es: {application.status}." if application else "No encuentro una aplicación con ese correo."
            await send_message(platform, user_id, msg, business_unit.name.lower())
            await self.store_bot_message(event, msg)
            event.context['awaiting_status_email'] = False
            await sync_to_async(event.save)()
        else:
            msg = "Ese no parece un correo válido. Intenta nuevamente."
            await send_message(platform, user_id, msg, business_unit.name.lower())
            await self.store_bot_message(event, msg)

    async def handle_group_invitation_input(self, platform: str, user_id: str, text: str, chat_state: ChatState, business_unit: BusinessUnit, user: Person):
        """Handle group invitation input interactively with buttons."""
        bu_name = business_unit.name.lower()
        if not chat_state.context.get('awaiting_group_invitation'):
            await send_message(platform, user_id, "Por favor, dime el nombre de la persona que quieres invitar.", bu_name)
            chat_state.context['awaiting_group_invitation'] = True
            chat_state.state = "waiting_for_invitation_name"
            await sync_to_async(chat_state.save)()
            return
        if chat_state.state == "waiting_for_invitation_name":
            chat_state.context['invitation_name'] = text.capitalize()
            await send_message(platform, user_id, "Gracias, ahora dime el apellido.", bu_name)
            chat_state.state = "waiting_for_invitation_apellido"
            await sync_to_async(chat_state.save)()
            return
        elif chat_state.state == "waiting_for_invitation_apellido":
            chat_state.context['invitation_apellido'] = text.capitalize()
            await send_message(platform, user_id, "Perfecto, ahora dame el número de teléfono (ej. +521234567890).", bu_name)
            chat_state.state = "waiting_for_invitation_phone"
            await sync_to_async(chat_state.save)()
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
                await send_message(platform, user_id, resp, bu_name)
                await send_options(platform, user_id, "Selecciona una opción:", buttons, bu_name)
                chat_state.state = "waiting_for_invitation_confirmation"
                await sync_to_async(chat_state.save)()
            else:
                resp = "El número no parece válido. Usa el formato '+521234567890'. Intenta de nuevo."
                await send_message(platform, user_id, resp, bu_name)
                await self.store_bot_message(chat_state, resp)
            return
        elif chat_state.state == "waiting_for_invitation_confirmation":
            if text == "yes_invite_more":
                chat_state.context.pop('invitation_name', None)
                chat_state.context.pop('invitation_apellido', None)
                chat_state.context['awaiting_group_invitation'] = True
                await send_message(platform, user_id, "¡Genial! Dime el nombre de la siguiente persona.", bu_name)
                chat_state.state = "waiting_for_invitation_name"
                await sync_to_async(chat_state.save)()
            elif text == "no_invite_more":
                await send_message(platform, user_id, "¡Listo! No invitaré a nadie más. ¿En qué te ayudo ahora?", bu_name)
                await send_menu(platform, user_id, bu_name)
                chat_state.context.pop('awaiting_group_invitation', None)
                chat_state.context.pop('invitation_name', None)
                chat_state.context.pop('invitation_apellido', None)
                chat_state.state = "idle"
                await sync_to_async(chat_state.save)()
            else:
                await send_message(platform, user_id, "Por favor, selecciona 'Sí' o 'No'.", bu_name)
            return

    async def invite_known_person(self, referrer: Person, name: str, apellido: str, phone_number: str):
        """Invite a known person to the platform."""
        if not re.match(r"^\+\d{10,15}$", phone_number):
            raise ValueError("Número de teléfono inválido")
        invitado, created = await sync_to_async(Person.objects.get_or_create)(
            phone=phone_number, defaults={'nombre': name, 'apellido_paterno': apellido}
        )
        await sync_to_async(Invitacion.objects.create)(referrer=referrer, invitado=invitado)

    async def handle_job_selection(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        """Handle job selection from recommended jobs."""
        recommended_jobs = event.context.get('recommended_jobs', [])
        try:
            job_index = int(text.strip()) - 1
        except ValueError:
            resp = "Por favor, ingresa un número válido."
            await send_message(platform, user_id, resp, business_unit.name.lower())
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
            await send_message(platform, user_id, resp, business_unit.name, options=buttons)
            await self.store_bot_message(event, resp)
            event.context['selected_job'] = selected_job
            await sync_to_async(event.save)()
        else:
            resp = "Selección inválida."
            await send_message(platform, user_id, resp, business_unit.name.lower())
            await self.store_bot_message(event, resp)

    async def handle_job_action(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        """Handle actions related to job selection."""
        recommended_jobs = event.context.get('recommended_jobs', [])
        if text.startswith("apply_"):
            job_index = int(text.split('_')[1])
            if 0 <= job_index < len(recommended_jobs):
                job = recommended_jobs[job_index]
                await sync_to_async(Application.objects.create)(user=user, vacancy_id=job['id'], status='applied')
                resp = "¡Has aplicado a la vacante con éxito!"
                await send_message(platform, user_id, resp, business_unit.name.lower())
                await self.store_bot_message(event, resp)
                await self.award_gamification_points(user, "job_application")
            else:
                resp = "No encuentro esa vacante."
                await send_message(platform, user_id, resp, business_unit.name.lower())
                await self.store_bot_message(event, resp)
        elif text.startswith("details_"):
            job_index = int(text.split('_')[1])
            if 0 <= job_index < len(recommended_jobs):
                job = recommended_jobs[job_index]
                details = job.get('description', 'No hay descripción disponible.')
                resp = f"Detalles de la posición:\n{details}"
                await send_message(platform, user_id, resp, business_unit.name.lower())
                await self.store_bot_message(event, resp)
            else:
                resp = "No encuentro esa vacante."
                await send_message(platform, user_id, resp, business_unit.name.lower())
                await self.store_bot_message(event, resp)
        elif text.startswith("schedule_"):
            job_index = int(text.split('_')[1])
            if 0 <= job_index < len(recommended_jobs):
                selected_job = recommended_jobs[job_index]
                slots = await self.get_interview_slots(selected_job)
                if not slots:
                    resp = "No hay horarios disponibles por el momento."
                    await send_message(platform, user_id, resp, business_unit.name.lower())
                    await self.store_bot_message(event, resp)
                    return
                buttons = [{'title': slot['label'], 'payload': f"book_slot_{idx}"} for idx, slot in enumerate(slots)]
                event.context['available_slots'] = slots
                event.context['selected_job'] = selected_job
                await sync_to_async(event.save)()
                resp = "Elige un horario para la entrevista:"
                await send_message(platform, user_id, resp, business_unit.name, options=buttons)
                await self.store_bot_message(event, resp)
            else:
                resp = "No encuentro esa vacante."
                await send_message(platform, user_id, resp, business_unit.name.lower())
                await self.store_bot_message(event, resp)
        elif text.startswith("tips_"):
            job_index = int(text.split('_')[1])
            prompt = "Dame consejos para la entrevista en esta posición"
            response = await self.generate_dynamic_response(user, event, prompt, {}, {})
            if not response:
                response = "Prepárate, investiga la empresa, sé puntual y comunica tus logros con seguridad."
            await send_message(platform, user_id, response, business_unit.name.lower())
            await self.store_bot_message(event, response)
        elif text.startswith("book_slot_"):
            slot_index = int(text.split('_')[2])
            available_slots = event.context.get('available_slots', [])
            if 0 <= slot_index < len(available_slots):
                selected_slot = available_slots[slot_index]
                resp = f"Entrevista agendada para {selected_slot['label']} ¡Éxito!"
                await send_message(platform, user_id, resp, business_unit.name.lower())
                await self.store_bot_message(event, resp)
            else:
                resp = "No encuentro ese horario."
                await send_message(platform, user_id, resp, business_unit.name.lower())
                await self.store_bot_message(event, resp)

    async def get_interview_slots(self, job: Dict[str, Any]) -> List[Dict[str, str]]:
        """Return available interview slots."""
        return [
            {'label': 'Mañana 10:00 AM', 'datetime': '2024-12-10T10:00:00'},
            {'label': 'Mañana 11:00 AM', 'datetime': '2024-12-10T11:00:00'}
        ]

    async def handle_hiring_event(self, user: Person, business_unit: BusinessUnit, chat_state: ChatState):
        """Handle hiring event notification."""
        if business_unit.name.lower() == "amigro":
            from app.chatbot.workflow.amigro import notify_legal_on_hire
            await sync_to_async(notify_legal_on_hire.delay)(user.id)
        elif business_unit.name.lower() == "huntu":
            from app.chatbot.workflow.huntu import process_huntu_candidate
            await sync_to_async(process_huntu_candidate.delay)(user.id)
        elif business_unit.name.lower() == "huntred":
            from app.chatbot.workflow.huntred import process_huntred_candidate
            await sync_to_async(process_huntred_candidate.delay)(user.id)
        elif business_unit.name.lower() == "huntred executive":
            from app.chatbot.workflow.executive import process_executive_candidate
            await sync_to_async(process_executive_candidate.delay)(user.id)

        message = "Tu contratación ha sido registrada correctamente."
        await send_message(chat_state.platform, user.phone, message, business_unit.name)
        await self.store_bot_message(chat_state, message)
        logger.info(f"Contratación registrada para {user.full_name} en {business_unit.name}")

    async def handle_client_selection(self, client_id: int, candidate_id: int, business_unit: BusinessUnit):
        """Handle client selection and contract generation."""
        candidate = await sync_to_async(Person.objects.get)(id=candidate_id)
        process = await sync_to_async(Vacante.objects.filter(candidate=candidate).first)()
        if not process:
            return "El candidato no está en un proceso activo."
        file_path = generate_and_send_contract(candidate, process.client, process.job_position, business_unit)
        await send_message(
            platform="whatsapp",
            user_id=candidate.phone,
            message="Se ha generado tu Carta Propuesta. Por favor, revisa tu correo y firma el documento.",
            business_unit=business_unit.name
        )
        return f"Carta Propuesta enviada para {candidate.full_name} en {business_unit.name}"

    async def check_inactive_sessions(self, inactivity_threshold: int = 300):
        """Check inactive sessions and send reactivation message."""
        threshold_time = timezone.now() - timezone.timedelta(seconds=inactivity_threshold)
        inactive_sessions = await sync_to_async(
            lambda: list(ChatState.objects.filter(last_interaction_at__lt=threshold_time))
        )()
        for session in inactive_sessions:
            if not session.conversation_history or not any("¿Sigues ahí?" in m.get("content", "") for m in session.conversation_history):
                await send_message(session.platform, session.user_id, "¿Sigues ahí?", session.business_unit.name)
                await self.store_bot_message(session, "¿Sigues ahí?")
                logger.info(f"Mensaje de inactividad enviado a {session.user_id}")

    async def present_job_listings(
        self, platform: str, user_id: str, jobs: List[Dict[str, Any]], 
        business_unit: BusinessUnit, chat_state: ChatState, page: int = 0, 
        jobs_per_page: int = 3, filters: Dict[str, Any] = None
    ) -> None:
        """Present job listings with pagination and filters."""
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
        
        response = f"Aquí tienes algunas vacantes recomendadas (página {page + 1}):\n"
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

    async def send_profile_completion_email(self, user_id: str, context: dict):
        """Send profile completion email."""
        try:
            user = await sync_to_async(Person.objects.get)(phone=user_id)
            if not user.email:
                logger.warning(f"Usuario con phone {user_id} no tiene email registrado.")
                return
            business_unit = user.businessunit_set.first()
            configuracion_bu = await sync_to_async(ConfiguracionBU.objects.get)(business_unit=business_unit)
            dominio_bu = configuracion_bu.dominio_bu if configuracion_bu else "tu_dominio.com"
            subject = f"Completa tu perfil en {business_unit.name} ({dominio_bu})"
            body = f"Hola {user.nombre},\n\nPor favor completa tu perfil en {dominio_bu} para continuar."
            await send_email(business_unit_name=business_unit.name, subject=subject, to_email=user.email, body=body)
            logger.info(f"Correo de completación enviado a {user.email}")
        except (Person.DoesNotExist, ConfiguracionBU.DoesNotExist) as e:
            logger.error(f"Error enviando correo de perfil a {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error enviando correo de perfil a {user_id}: {e}", exc_info=True)

    async def recap_information(self, user: Person) -> str:
        """Generate a summary of user information."""
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
        """Handle CV upload."""
        person, created = await sync_to_async(Person.objects.get_or_create)(
            phone=user.phone, defaults={'nombre': user.nombre}
        )
        person.cv_file = uploaded_file
        person.cv_parsed = False
        await sync_to_async(person.save)()
        return "Tu CV ha sido recibido y será analizado."

    async def award_gamification_points(self, user: Person, activity_type: str):
        """Award gamification points to the user."""
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
        """Notify user about gamification update."""
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            message = f"¡Has ganado puntos por {activity_type}! Ahora tienes {profile.points} puntos."
            platform = user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp'
            business_unit = user.chat_state.business_unit if hasattr(user, 'chat_state') else user.businessunit_set.first()
            if platform and business_unit:
                await send_message(platform, user.phone, message, business_unit.name)
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            logger.warning(f"No se encontró perfil de gamificación para {user.nombre}")
        except Exception as e:
            logger.error(f"Error notificando gamificación a {user.nombre}: {e}", exc_info=True)

    async def generate_challenges(self, user: Person) -> List[str]:
        """Generate networking challenges for the user."""
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            return await sync_to_async(profile.generate_networking_challenges)()
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            return []

    async def notify_user_challenges(self, user: Person):
        """Notify user about new challenges."""
        challenges = await self.generate_challenges(user)
        if challenges:
            message = f"Tienes nuevos desafíos: {', '.join(challenges)}"
            platform = user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp'
            business_unit = user.chat_state.business_unit if hasattr(user, 'chat_state') else user.businessunit_set.first()
            if platform and business_unit:
                await send_message(platform, user.phone, message, business_unit.name)

    async def store_user_message(self, chat_state, text: str):
        """Almacena el mensaje del usuario en el historial de conversación."""
        if not chat_state.conversation_history:
            chat_state.conversation_history = []
        chat_state.conversation_history.append({
            "role": "user",
            "content": text,
            "timestamp": timezone.now().isoformat()
        })
        chat_state.last_interaction_at = timezone.now()
        await sync_to_async(chat_state.save)()

    async def store_bot_message(self, chat_state, text: str):
        """Almacena el mensaje del bot en el historial de conversación."""
        if not chat_state.conversation_history:
            chat_state.conversation_history = []
        chat_state.conversation_history.append({
            "role": "assistant",
            "content": text,
            "timestamp": timezone.now().isoformat()
        })
        chat_state.last_interaction_at = timezone.now()
        await sync_to_async(chat_state.save)()
                