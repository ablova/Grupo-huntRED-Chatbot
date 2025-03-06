# Ubicación en servidor: /home/pablo/app/chatbot/chatbot.py

import logging
import asyncio
import re  # AGREGADO para manejo de expresiones regulares en handle_status_email
from django.utils import timezone
from typing import Optional, List, Dict, Any, Tuple
from asgiref.sync import sync_to_async
from django.utils.timezone import now
from django.core.cache import cache

from app.models import (
    ChatState, Person, GptApi, Application, Invitacion, BusinessUnit, Vacante, WhatsAppAPI, EnhancedNetworkGamificationProfile, ConfiguracionBU
)
from app.chatbot.integrations.services import (
    send_email, send_message, send_options, send_menu, send_url, send_image, GamificationService
    )
# Importaciones de workflows
from app.chatbot.workflow.common import generate_and_send_contract
from app.chatbot.workflow.amigro import process_amigro_candidate
from app.chatbot.workflow.huntu import process_huntu_candidate
from app.chatbot.workflow.huntred import process_huntred_candidate
from app.chatbot.workflow.executive import process_executive_candidate
from app.chatbot.workflow.sexsi import iniciar_flujo_sexsi, confirmar_pago_sexsi

from app.utilidades.parser import CVParser

logger = logging.getLogger(__name__)

# Importaciones condicionales de NLP solo si está habilitado
NLP_ENABLED = False  # Cambia a True para habilitar NLP, False para desactivarlo
if NLP_ENABLED:
    from app.chatbot.utils import analyze_text, is_spam_message, update_user_message_history, is_user_spamming
    from app.chatbot.nlp import NLPProcessor

CACHE_TIMEOUT = 600  # 10 minutes

from app.chatbot.gpt import GPTHandler  # Asegúrese de que se importe correctamente

class ChatBotHandler:
    def __init__(self):
        self.gpt_handler = GPTHandler()
        # Diccionario que mapea las unidades de negocio a su workflow respectivo.
        self.workflow_mapping = {
            "amigro": process_amigro_candidate,
            "huntu": process_huntu_candidate,
            "huntred": process_huntred_candidate,
            "huntred executive": process_executive_candidate,
            "sexsi": iniciar_flujo_sexsi
        }
        # Diccionario para configuración de mensajes de bienvenida inicial.
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
            # Se pueden agregar mensajes específicos para otras unidades si se requiere.
        }

    def get_tos_url(self, business_unit: BusinessUnit) -> str:
        """Obtiene la URL de TOS según la unidad de negocio."""
        tos_urls = {
            "huntred": "https://huntred.com/tos",
            "huntred executive": "https://huntred.com/executive/tos",
            "huntu": "https://huntu.mx/tos",
            "amigro": "https://amigro.org/tos",
            "sexsi": "https://sexsi.org/tos"
        }
        return tos_urls.get(business_unit.name.lower(), "https://huntred.com/tos")

    @staticmethod
    async def handle_welcome_message(user_id: str, platform: str, business_unit: BusinessUnit) -> str:
        """Envía el mensaje de bienvenida, logo y menú."""
        try:
            logger.info(f"[handle_welcome_message] Enviando bienvenida a {user_id} en {platform} para BU: {business_unit.name}")

            welcome_messages = {
                "huntred": "Bienvenido a huntRED® 🚀\nSomos expertos en encontrar el mejor talento para empresas líderes.",
                "huntred executive": "Bienvenido a huntRED® Executive 🌟\nNos especializamos en colocación de altos ejecutivos.",
                "huntu": "Bienvenido a huntU® 🏆\nConectamos talento joven con oportunidades de alto impacto.",
                "amigro": "Bienvenido a Amigro® 🌍\nFacilitamos el acceso laboral a mexicanos regresando y migrantes de Latinoamérica ingresando a México.",
                "sexsi": "Bienvenido a SEXSI 🔐\nAquí puedes gestionar acuerdos de consentimiento seguros y firmarlos digitalmente."
            }
            logo_urls = {
                "huntred": "/home/pablo/app/media/huntred.png",
                "huntred executive": "/home/pablo/app/media/executive.png",
                "huntu": "/home/pablo/app/media/huntu.png",
                "amigro": "/home/pablo/app/media/amigro.png",
                "sexsi": "/home/pablo/app/media/sexsi.png",
            }

            welcome_msg = welcome_messages.get(business_unit.name.lower(), "Bienvenido a nuestra plataforma 🎉")
            logo_url = logo_urls.get(business_unit.name.lower(), "/home/pablo/app/media/Grupo_huntRED.png")

            user = await sync_to_async(Person.objects.filter(phone=user_id).first)()
            if user and user.number_interaction > 0:
                welcome_msg += f" ¡Qué bueno verte de nuevo, {user.nombre}!"

            # Envío de mensajes con manejo de errores por separado
            try:
                await send_message(platform, user_id, welcome_msg, business_unit.name)
            except Exception as e:
                logger.error(f"❌ Error enviando mensaje de bienvenida: {e}")

            await asyncio.sleep(1)  # Pequeño delay antes de enviar la imagen

            try:
                await send_image(platform, user_id, "Aquí tienes nuestro logo 📌", logo_url, business_unit.name)
            except Exception as e:
                logger.error(f"❌ Error enviando imagen de bienvenida: {e}")

            await asyncio.sleep(1)

            try:
                await send_menu(platform, user_id, business_unit.name)
            except Exception as e:
                logger.error(f"❌ Error enviando menú: {e}")

            return "Mensaje de bienvenida enviado correctamente."

        except Exception as e:
            logger.error(f"[handle_welcome_message] ❌ Error enviando bienvenida a {user_id}: {e}", exc_info=True)
            return "Error enviando mensaje de bienvenida."

    async def send_complete_initial_messages(self, platform: str, user_id: str, business_unit: BusinessUnit):
        """Envía el flujo inicial: saludo, intro, TOS URL, y prompt interactivo."""
        try:
            logger.info(f"[send_complete_initial_messages] Iniciando flujo inicial para {user_id} en {platform}, BU: {business_unit.name}")
            welcome_result = await self.handle_welcome_message(user_id, platform, business_unit)
            logger.info(f"[send_complete_initial_messages] {welcome_result}")
            await asyncio.sleep(1)

            bu_key = business_unit.name.lower()
            messages = self.initial_messages.get(bu_key, self.initial_messages["default"])
            for msg in messages:
                await send_message(platform, user_id, msg, business_unit.name.lower())
                await asyncio.sleep(1)

            tos_url = self.get_tos_url(business_unit)
            url_message = f"📜 Puedes revisar nuestros Términos de Servicio aquí: {tos_url}"
            await send_message(platform, user_id, url_message, business_unit.name)
            await asyncio.sleep(1)

            tos_prompt = "¿Aceptas nuestros Términos de Servicio (TOS)?"
            tos_buttons = [
                {'title': 'Sí', 'payload': 'tos_accept'},
                {'title': 'No', 'payload': 'tos_reject'}
            ]
            await send_options(platform, user_id, tos_prompt, tos_buttons, business_unit.name)
            logger.info(f"[send_complete_initial_messages] Flujo inicial completado para {user_id} en {business_unit.name}")
        except Exception as e:
            logger.error(f"[send_complete_initial_messages] Error en flujo inicial para {user_id}: {e}", exc_info=True)

    async def handle_tos_acceptance(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        """Procesa la respuesta del usuario para los TOS."""
        tos_url = self.get_tos_url(business_unit)
        tos_buttons = [
            {'title': 'Sí', 'payload': 'tos_accept'},
            {'title': 'No', 'payload': 'tos_reject'},
            {'title': 'Ver TOS', 'url': tos_url}
        ]
        normalized = text.strip().lower()
        if normalized in ['tos_accept', 'sí', 'si']:
            user.tos_accepted = True
            await sync_to_async(user.save)()
            confirmation_msg = "Gracias por aceptar nuestros TOS. Aquí tienes el menú principal:"
            await send_message(platform, user_id, confirmation_msg, business_unit.name.lower())
            await send_menu(platform, user_id, business_unit.name.lower())  # Pasar business_unit.name
            await self.store_bot_message(event, confirmation_msg)
            await self.award_gamification_points(user, "tos_accepted")
            logger.info(f"TOS aceptados para {user.phone}")
        elif normalized in ['tos_reject', 'no']:
            rejection_msg = "No se puede continuar sin aceptar los TOS. Responde 'Sí' o 'Salir'."
            await send_message(platform, user_id, rejection_msg, business_unit.name.lower())
            await self.store_bot_message(event, rejection_msg)
            event.context['tos_attempts'] = event.context.get('tos_attempts', 0) + 1
            if event.context['tos_attempts'] >= 3:
                await send_message(platform, user_id, "Sesión terminada por falta de aceptación.", business_unit.name.lower())
                await self.store_bot_message(event, "Sesión terminada por falta de aceptación.")
                return
            await sync_to_async(event.save)()
        else:
            # Enviar URL como mensaje separado
            await send_message(platform, user_id, f"📜 Revisa nuestros Términos de Servicio: {tos_url}", business_unit.name.lower())
            await asyncio.sleep(1)  # Pequeña pausa para evitar spam
            prompt = "Por favor, selecciona una opción:"
            await send_options(platform, user_id, prompt, tos_buttons, business_unit.name.lower())
   
    async def process_message(self, platform: str, user_id: str, text: str, business_unit: BusinessUnit):
        """Procesa el mensaje entrante y responde según la intención del usuario."""
        try:
            logger.info(f"[process_message] 📩 Mensaje recibido de {user_id} en {platform} para BU: {business_unit.name}")

            # Obtener o crear ChatState de forma asíncrona
            chat_state, _ = await sync_to_async(ChatState.objects.get_or_create)(
                user_id=user_id, business_unit=business_unit, defaults={'platform': platform}
            )
            user, _ = await self.get_or_create_user(user_id, platform)

            # Usar sync_to_async para acceder a relaciones síncronas
            chat_state_person = await sync_to_async(lambda: chat_state.person)()
            if chat_state_person != user:
                chat_state.person = user
                await sync_to_async(chat_state.save)()
            # Verificación de spam solo si NLP está habilitado
            if NLP_ENABLED:
                if is_spam_message(user_id, text):
                    logger.warning(f"[SPAM DETECTADO] ⛔ Mensaje repetido de {user_id}: {text}")
                    await send_message(platform, user_id, "⚠️ No envíes mensajes repetidos, por favor.", business_unit.name.lower())
                    return
            else:
                logger.info(f"[NLP DESACTIVADO] Omitiendo verificación de spam para {user_id}")

            if cache.get(f"muted:{user_id}"):
                logger.warning(f"[MUTEADO] ⛔ Usuario {user_id} aún en cooldown.")
                return

            if not user.tos_accepted:
                await self.handle_tos_acceptance(platform, user_id, text, chat_state, business_unit, user)
                return

            await self.store_user_message(chat_state, text)
            
            from app.chatbot.intents_handler import handle_known_intents
            if NLP_ENABLED:
                analysis = analyze_text(text)
                intents = analysis.get("intents", [])
                if await handle_known_intents(intents, platform, user_id, chat_state, business_unit, user):
                    return
            else:
                # Respuesta predeterminada cuando NLP está desactivado
                intents = []
                analysis = {"entities": [], "sentiment": {}}
            
            # Usar predicción y mensaje personalizado con GPTHandler
            from app.ml.ml_model import MatchmakingLearningSystem
            ml_system = MatchmakingLearningSystem(business_unit=business_unit.name)
            top_candidates = await ml_system.predict_top_candidates(vacancy=None)
            if user in [c[0] for c in top_candidates]:
                gpt_handler = GPTHandler()
                if not gpt_handler.client:
                    await gpt_handler.initialize()
                vacancy = await sync_to_async(Vacante.objects.filter)(activa=True, business_unit=business_unit).first()
                if vacancy:
                    candidate_skills = " ".join(user.skills.split(',') if user.skills else [])
                    job_skills = " ".join(vacancy.skills_required if vacancy.skills_required else [])
                    prompt = (
                        f"Context: Candidato con habilidades: {candidate_skills}. Vacante requiere: {job_skills}. "
                        f"Genera un mensaje personalizado invitando al candidato a aplicar, usando un tono profesional y motivador."
                    )
                    personalized_msg = await gpt_handler.generate_response(prompt, business_unit)
                    await send_message(platform, user_id, personalized_msg, business_unit.name.lower())
                    await self.store_bot_message(chat_state, personalized_msg)
                    if skills_data["sentiment"] == "negative":
                        await send_message(platform, user_id, "¿Hay algo en lo que pueda ayudarte para mejorar tu experiencia?", business_unit.name.lower())
                    return

            bu_key = business_unit.name.lower()
            if bu_key in self.workflow_mapping:
                workflow_func = self.workflow_mapping[bu_key]
                if bu_key == "sexsi":
                    response = workflow_func(user_id, user, business_unit, chat_state.context)
                    await send_message(platform, user_id, response, business_unit.name.lower())
                    await self.store_bot_message(chat_state, response)
                    return
                else:
                    await sync_to_async(workflow_func)(user.id)  # Synchronous execution for reliability

            if chat_state.context.get('awaiting_status_email'):
                await self.handle_status_email(platform, user_id, text, chat_state, business_unit, user)
                return

            if chat_state.context.get('awaiting_group_invitation'):
                await self.handle_group_invitation_input(platform, user_id, text, chat_state, business_unit, user)
                return

            if text.lower() in ["confirmar contratación", "he sido contratado", "contratado"]:
                await self.handle_hiring_event(user, business_unit, chat_state)
                return

            if chat_state.context.get('recommended_jobs') and text.isdigit():
                await self.handle_job_selection(platform, user_id, text, chat_state, business_unit, user)
                return

            if any(text.startswith(prefix) for prefix in ["apply_", "details_", "schedule_", "tips_", "book_slot_"]):
                await self.handle_job_action(platform, user_id, text, chat_state, business_unit, user)
                return

            entities = analysis.get("entities", [])
            sentiment = analysis.get("sentiment", {})
            response = await self.generate_dynamic_response(user, chat_state, text, entities, sentiment)
            await send_message(platform, user_id, response, business_unit.name.lower())
            await self.store_bot_message(chat_state, response)

        except ChatState.DoesNotExist:
            logger.error(f"No ChatState for {user_id} in {business_unit.name}")
            await send_message(platform, user_id, "No se encontró tu estado de chat. Reiniciando...", business_unit.name.lower())
        except ValueError as ve:
            logger.error(f"ValueError processing message: {ve}")
            await send_message(platform, user_id, "Entrada inválida. Intenta de nuevo.", business_unit.name.lower())
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            await send_message(platform, user_id, "Error interno. Intenta más tarde.", business_unit.name.lower())
        logger.info(f"[process_message] Procesamiento completado para {user_id} con respuesta enviada")
    
    async def get_or_create_event(self, user_id: str, platform: str, business_unit: BusinessUnit) -> ChatState:
        chat_state, created = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=user_id, business_unit=business_unit, defaults={'platform': platform}
        )
        return chat_state

    async def get_or_create_user(self, user_id: str, platform: str) -> Tuple[Person, bool]:
        """Obtiene o crea un usuario y actualiza el contador de interacciones."""
        user, created = await sync_to_async(Person.objects.get_or_create)(
            phone=user_id, defaults={'nombre': 'Nuevo Usuario', 'number_interaction': 0}
        )
        if not created:
            user.number_interaction += 1
            await sync_to_async(user.save)()
        return user, created

    async def handle_status_email(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
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

    async def handle_group_invitation_input(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        parts = text.split()
        if len(parts) >= 3:
            phone_number = parts[-1]
            name = parts[0]
            apellido = parts[1]
            await self.invite_known_person(user, name, apellido, phone_number)
            resp = f"He invitado a {name} {apellido}. ¿Deseas invitar a alguien más? Responde 'sí' o 'no'."
            await send_message(platform, user_id, resp, business_unit.name.lower())
            await self.store_bot_message(event, resp)
        else:
            resp = "Formato no válido. Envía: 'Nombre Apellido +521234567890'"
            await send_message(platform, user_id, resp, business_unit.name.lower())
            await self.store_bot_message(event, resp)

    async def invite_known_person(self, referrer: Person, name: str, apellido: str, phone_number: str):
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
        return [
            {'label': 'Mañana 10:00 AM', 'datetime': '2024-12-10T10:00:00'},
            {'label': 'Mañana 11:00 AM', 'datetime': '2024-12-10T11:00:00'}
        ]

    async def generate_dynamic_response(self, user: Person, event: ChatState, user_message: str, entities, sentiment) -> str:
        """Genera una respuesta dinámica usando GPT."""
        history = await self.get_conversation_history(event)
        prompt = self.build_gpt_prompt(history, user_message, user, entities, sentiment)
        gpt_api = await sync_to_async(GptApi.objects.first)()
        if not gpt_api:
            logger.warning("No se encontró configuración GptApi.")
            return "Lo siento, no tengo suficiente información para responder."
        if self.gpt_handler.gpt_api is None:
            await self.gpt_handler.initialize()
        return await self.gpt_handler.generate_response(prompt)

    async def handle_hiring_event(self, user: Person, business_unit: BusinessUnit, chat_state: ChatState):
        """Maneja la notificación de contratación dependiendo de la unidad de negocio."""
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

    def build_gpt_prompt(self, history, user_message, user: Person, entities, sentiment):
        roles_text = ""
        for msg in history[-5:]:
            if msg["role"] == "user":
                roles_text += f"Usuario: {msg['content']}\n"
            else:
                roles_text += f"Asistente: {msg['content']}\n"
        roles_text += f"Usuario: {user_message}\nAsistente:"
        return roles_text

    async def get_conversation_history(self, event: ChatState):
        return event.conversation_history or []

    async def store_user_message(self, event: ChatState, text: str):
        """Almacena el mensaje del usuario en el historial."""
        try:
            history = event.conversation_history or []
            history.append({'timestamp': timezone.now().isoformat(), 'role': 'user', 'content': text})
            event.conversation_history = history
            event.last_interaction_at = timezone.now()
            await sync_to_async(event.save)()
            logger.debug(f"Historial actualizado para {event.user_id}: {history}")
        except Exception as e:
            logger.error(f"Error almacenando mensaje del usuario: {e}", exc_info=True)

    async def store_bot_message(self, event: ChatState, message: str):
        """Almacena el mensaje del bot en el historial."""
        try:
            history = event.conversation_history or []
            history.append({'timestamp': timezone.now().isoformat(), 'role': 'assistant', 'content': message})
            event.conversation_history = history
            await sync_to_async(event.save)()
            logger.info(f"Bot respondió a {event.user_id}: {message}")
        except Exception as e:
            logger.error(f"Error almacenando mensaje del bot: {e}", exc_info=True)

    async def check_inactive_sessions(self, inactivity_threshold: int = 300):
        """Revisa sesiones inactivas y envía mensaje de reactivación."""
        threshold_time = timezone.now() - timezone.timedelta(seconds=inactivity_threshold)
        inactive_sessions = await sync_to_async(
            lambda: list(ChatState.objects.filter(last_interaction_at__lt=threshold_time))
        )()
        for session in inactive_sessions:
            if not session.conversation_history or not any("¿Sigues ahí?" in m.get("content", "") for m in session.conversation_history):
                await send_message(session.platform, session.user_id, "¿Sigues ahí?", session.business_unit.name)
                await self.store_bot_message(session, "¿Sigues ahí?")
                logger.info(f"Mensaje de inactividad enviado a {session.user_id}")

    async def present_job_listings(self, platform: str, user_id: str, jobs: List[Dict[str, Any]], business_unit: BusinessUnit, event: ChatState):
        response = "Aquí tienes algunas vacantes recomendadas:\n"
        for idx, job in enumerate(jobs[:5]):
            response += f"{idx+1}. {job['title']} en {job['company']}\n"
        response += "Responde con el número de la vacante que te interesa."
        await send_message(platform, user_id, response, business_unit.name.lower())
        await self.store_bot_message(event, response)

    async def send_profile_completion_email(self, user_id: str, context: dict):
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
                await send_message(platform, user.phone, message, business_unit.name)
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
                await send_message(platform, user.phone, message, business_unit.name)