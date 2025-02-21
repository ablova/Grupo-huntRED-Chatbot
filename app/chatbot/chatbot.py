# Ubicación en servidor: /home/pablo/app/chatbot/chatbot.py

import logging
import asyncio
import re  # AGREGADO para manejo de expresiones regulares en handle_status_email
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
from app.chatbot.utils import analyze_text  # Encargado del NLP y patrones de intents

# Importaciones de workflows
from app.chatbot.workflow.common import generate_and_send_contract
from app.chatbot.workflow.amigro import process_amigro_candidate
from app.chatbot.workflow.huntu import process_huntu_candidate
from app.chatbot.workflow.huntred import process_huntred_candidate
from app.chatbot.workflow.executive import process_executive_candidate
from app.chatbot.workflow.sexsi import iniciar_flujo_sexsi, confirmar_pago_sexsi

from app.utilidades.parser import CVParser

logger = logging.getLogger("app.chatbot")
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
    async def handle_welcome_message(user_id, platform, business_unit: BusinessUnit):
        """
        Envía el mensaje de bienvenida, logo y menú.
        """
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

            # Enviar mensaje de bienvenida
            await send_message(platform, user_id, welcome_msg, business_unit.name)
            await send_image(platform, user_id, "Aquí tienes nuestro logo 📌", logo_url, business_unit.name)
            await send_menu(platform, user_id, business_unit.name)

            return "Mensaje de bienvenida enviado correctamente."

        except Exception as e:
            logger.error(f"[handle_welcome_message] Error enviando bienvenida a {user_id}: {e}", exc_info=True)
            return "Error enviando mensaje de bienvenida."
        
    async def send_complete_initial_messages(self, platform: str, user_id: str, business_unit: BusinessUnit):
        """
        Envía el flujo inicial:
        1. Saludo, imagen y menú (handle_welcome_message)
        2. Mensajes introductorios
        3. Prompt interactivo para aceptación de TOS
        """
        try:
            logger.info(f"[send_complete_initial_messages] Iniciando flujo inicial  para {user_id} en {platform}, BU: {business_unit.name}")
            
            # Paso 1: Enviar bienvenida
            welcome_result = await ChatBotHandler.handle_welcome_message(user_id, platform, business_unit)
            logger.info(f"[send_complete_initial_messages] {welcome_result}")
            await asyncio.sleep(1)

            # Paso 2: Enviar mensajes de introducción
            bu_key = business_unit.name.lower()
            messages = self.initial_messages.get(bu_key, self.initial_messages["default"])
            for msg in messages:
                await send_message(platform, user_id, msg, business_unit.name.lower())
                await asyncio.sleep(1)

            # Paso 3: Enviar prompt interactivo para aceptación de TOS
            tos_prompt = "¿Aceptas nuestros Términos de Servicio (TOS)?"
            tos_url = self.get_tos_url(business_unit)
            tos_buttons = [
                {'title': 'Sí', 'payload': 'tos_accept'},
                {'title': 'No', 'payload': 'tos_reject'},
                {'title': 'Ver TOS', 'url': tos_url}
            ]
            logger.info(f"[handle_tos_acceptance] Botones enviados: {tos_buttons}")
            await send_options(platform, user_id, tos_prompt, tos_buttons, business_unit.name)
            logger.info(f"[send_complete_initial_messages] Flujo inicial completado para {user_id} en {business_unit.name}")

        except Exception as e:
            logger.error(f"[send_complete_initial_messages] Error en flujo inicial para {user_id}: {e}", exc_info=True)

    async def handle_tos_acceptance(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        """
        Procesa la respuesta del usuario para los TOS.
        Si la respuesta es afirmativa, actualiza el estado y muestra el menú;
        si es negativa, envía mensaje de rechazo;
        en otro caso, reenvía el prompt interactivo usando get_tos_url.
        """
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
            await send_menu(platform, user_id, business_unit.name.lower())
            await self.store_bot_message(event, confirmation_msg)
            logger.info(f"TOS aceptados para {user.phone}")
        elif normalized in ['tos_reject', 'no']:
            rejection_msg = "No se puede continuar sin aceptar los TOS. Por favor, responde 'Sí' para aceptarlos."
            await send_message(platform, user_id, rejection_msg, business_unit.name.lower())
            await self.store_bot_message(event, rejection_msg)
        else:
            # Reenviar prompt interactivo para aclarar la aceptación
            prompt = "Por favor, selecciona una opción:"
            await send_options(platform, user_id, prompt, tos_buttons, business_unit.name.lower())

async def process_message(self, platform: str, user_id: str, text: str, business_unit: BusinessUnit):
    """
    Procesa el mensaje entrante y dirige la respuesta según el contexto e intención.

    Args:
        platform (str): Plataforma donde se ejecuta (WhatsApp, Telegram, Messenger, Instagram).
        user_id (str): Identificador del usuario.
        text (str): Mensaje recibido.
        business_unit (BusinessUnit): Objeto BusinessUnit correspondiente.

    Returns:
        None
    """
    try:
        logger.info(f"[process_message] Procesando mensaje de {user_id} en {platform} para BU: {business_unit.name}")

        chat_state = await sync_to_async(lambda: ChatState.objects.get(user_id=user_id, business_unit=business_unit))()
        user = chat_state.person

        # Si es el primer mensaje, iniciar flujo inicial
        if not chat_state.conversation_history:
            await self.send_complete_initial_messages(platform, user_id, business_unit)
            return

        # Verificar aceptación de TOS
        if not user.tos_accepted:
            await self.handle_tos_acceptance(platform, user_id, text, chat_state, business_unit, user)
            return
        
        # Guardar el mensaje del usuario antes del procesamiento
        await self.store_user_message(chat_state, text)

        # Procesar el mensaje según la unidad de negocio mediante el diccionario de workflows.
        bu_key = business_unit.name.lower()
        if bu_key in self.workflow_mapping:
            workflow_func = self.workflow_mapping[bu_key]

            if bu_key == "sexsi":
                response = workflow_func(user_id, user, business_unit, chat_state.context)
                await send_message(platform, user_id, response, business_unit.name.lower())
                await self.store_bot_message(chat_state, response)
            else:
                workflow_func.delay(user.id)  # No necesita sync_to_async

        # Analizar el texto con NLP
        analysis = analyze_text(text)  # { "intents": [...], "entities": [...], "sentiment": {...} }
        if not analysis or not isinstance(analysis, dict):
            raise ValueError(f"Invalid analysis result: {analysis}")

        intents = analysis.get("intents", [])
        entities = analysis.get("entities", [])
        sentiment = analysis.get("sentiment", {})

        # Manejo de intents conocidos (se ejecuta después de NLP)
        from app.chatbot.intents_handler import handle_known_intents
        if await handle_known_intents(intents, platform, user_id, chat_state, business_unit, user):
            return  # Si un intent fue manejado, no seguimos procesando

        # Manejar contextos especiales
        if chat_state.context.get('awaiting_status_email'):
            await self.handle_status_email(platform, user_id, text, chat_state, business_unit, user)
            return

        if chat_state.context.get('awaiting_group_invitation'):
            await self.handle_group_invitation_input(platform, user_id, text, chat_state, business_unit, user)
            return

        # Si el usuario confirma su contratación, activar el flujo de contratación
        if text.lower() in ["confirmar contratación", "he sido contratado", "contratado"]:
            await self.handle_hiring_event(user, business_unit)
            return

        # Manejar selección de vacante
        if chat_state.context.get('recommended_jobs') and text.isdigit():
            await self.handle_job_selection(platform, user_id, text, chat_state, business_unit, user)
            return

        # Manejar acciones sobre vacantes
        if any(text.startswith(prefix) for prefix in ["apply_", "details_", "schedule_", "tips_", "book_slot_"]):
            await self.handle_job_action(platform, user_id, text, chat_state, business_unit, user)
            return

        # Respuesta de fallback usando GPT
        response = await self.generate_dynamic_response(user, chat_state, text, entities, sentiment)
        await send_message(platform, user_id, response, business_unit.name.lower())
        await self.store_bot_message(chat_state, response)

    except ChatState.DoesNotExist:
        logger.error(f"[process_message] No se encontró ChatState para {user_id} y BU: {business_unit.name}")
        await send_message(platform, user_id, "No se encontró tu estado de chat. Por favor, reinicia la conversación.", business_unit.name.lower())
    except Exception as e:
        logger.error(f"[process_message] Error procesando mensaje: {e}", exc_info=True)
        await send_message(platform, user_id, "Ha ocurrido un error. Inténtalo más tarde.", business_unit.name.lower())

    async def get_or_create_event(self, user_id: str, platform: str, business_unit: BusinessUnit) -> ChatState:
        chat_state, created = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=user_id,
            business_unit=business_unit,
            defaults={'platform': platform}
        )
        return chat_state

    async def get_or_create_user(self, user_id: str, event: ChatState, analysis: dict) -> Tuple[Person, bool]:
        """
        Obtiene o crea un usuario y actualiza el contador de interacciones.
        """
        user, created = await sync_to_async(Person.objects.get_or_create)(
            phone=user_id,
            defaults={
                'nombre': 'Usuario',
                'number_interaction': 0,
            }
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
            if application:
                msg = f"El estatus de tu aplicación es: {application.status}."
            else:
                msg = "No encuentro una aplicación con ese correo."
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
            phone=phone_number,
            defaults={'nombre': name, 'apellido_paterno': apellido}
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
        # Slots simulados; se puede integrar con sistema de agendamiento real.
        return [
            {'label': 'Mañana 10:00 AM', 'datetime': '2024-12-10T10:00:00'},
            {'label': 'Mañana 11:00 AM', 'datetime': '2024-12-10T11:00:00'}
        ]

    async def generate_dynamic_response(self, user: Person, event: ChatState, user_message: str, entities, sentiment) -> str:
        """
        Genera una respuesta dinámica usando GPT. El prompt se construye a partir del historial y contexto.
        """
        history = await self.get_conversation_history(event)
        prompt = self.build_gpt_prompt(history, user_message, user, entities, sentiment)

        gpt_api = await sync_to_async(GptApi.objects.first)()
        if not gpt_api:
            logger.warning("No se encontró configuración GptApi, no se puede usar GPT.")
            return "Lo siento, no tengo suficiente información para responder."

        if self.gpt_handler.gpt_api is None:
            await self.gpt_handler.initialize()

        gpt_response = await self.gpt_handler.generate_response(prompt)
        return gpt_response

    async def handle_hiring_event(self, user: Person, business_unit: BusinessUnit):
        """
        Maneja la notificación de contratación dependiendo de la unidad de negocio.
        """
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

        await send_message(
            platform="whatsapp",
            user_id=user.phone,
            message="Tu contratación ha sido registrada correctamente.",
            business_unit=business_unit.name
        )

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
        return event.conversation_history

    async def store_user_message(self, event, text: str):
        """
        Almacena el mensaje del usuario en el historial y actualiza la última interacción.
        """
        try:
            history = event.conversation_history or []
            history.append({
                'timestamp': now().isoformat(),
                'role': 'user',
                'content': text
            })
            event.conversation_history = history
            event.last_interaction_at = now()  # Actualización de actividad
            await sync_to_async(event.save)()
            logger.debug(f"Historial actualizado para {event.user_id}: {history}")
        except Exception as e:
            logger.error(f"Error almacenando mensaje del usuario: {e}", exc_info=True)

    async def store_bot_message(self, event, message: str):
        """
        Almacena el mensaje del bot en el historial.
        """
        try:
            history = event.conversation_history or []
            history.append({
                'timestamp': now().isoformat(),
                'role': 'assistant',
                'content': message
            })
            event.conversation_history = history
            await sync_to_async(event.save)()
        except Exception as e:
            logger.error(f"Error almacenando mensaje del bot: {e}", exc_info=True)

    async def check_inactive_sessions(self, inactivity_threshold: int = 300):
        """
        Revisa los ChatState inactivos (por defecto 300 segundos = 5 minutos)
        y envía un mensaje de reactivación.
        """
        threshold_time = now() - timezone.timedelta(seconds=inactivity_threshold)
        inactive_sessions = await sync_to_async(
            lambda: ChatState.objects.filter(last_interaction_at__lt=threshold_time)
        )()
        for session in inactive_sessions:
            # Verificamos que no se haya enviado ya el mensaje de inactividad
            if not session.conversation_history or \
            (session.conversation_history and not any("¿Sigues ahí?" in m.get("content", "") for m in session.conversation_history)):
                await send_message("whatsapp", session.user_id, "¿Sigues ahí?", session.business_unit.name)
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
            email = user.email
            if email:
                business_unit = user.businessunit_set.first()
                try:
                    configuracion_bu = await sync_to_async(ConfiguracionBU.objects.get)(business_unit=business_unit)
                    dominio_bu = configuracion_bu.dominio_bu
                except ConfiguracionBU.DoesNotExist:
                    logger.error(f"No se encontró ConfiguracionBU para {business_unit.name}.")
                    dominio_bu = "tu_dominio.com"
                subject = f"Completa tu perfil en {business_unit.name} ({dominio_bu})"
                body = f"Hola {user.nombre},\n\nPor favor completa tu perfil en {dominio_bu} para continuar."
                await send_email(business_unit_name=business_unit.name, subject=subject, to_email=email, body=body)
                logger.info(f"Correo de completación enviado a {email}")
            else:
                logger.warning(f"Usuario con phone {user_id} no tiene email registrado.")
        except Person.DoesNotExist:
            logger.error(f"No se encontró usuario con phone {user_id} para enviar correo.")
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
    
    async def handle_cv_upload(self, user, uploaded_file) -> str:
        person, created = await sync_to_async(Person.objects.get_or_create)(
            phone=user.phone, defaults={'nombre': user.nombre}
        )
        person.cv_file = uploaded_file
        person.cv_parsed = False
        await sync_to_async(person.save)()
        return "Tu CV ha sido recibido y será analizado."

    def award_gamification_points(self, user, activity_type):
        try:
            profile = EnhancedNetworkGamificationProfile.objects.get(user=user)
            profile.award_points(activity_type)
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            logger.error(f"No se encontró perfil de gamificación para el usuario {user.id}")

    async def notify_user_gamification_update(self, user: Person, activity_type: str):
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            message = f"¡Has ganado puntos por {activity_type}! Ahora tienes {profile.points} puntos."
            platform = user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp'
            business_unit = user.chat_state.business_unit if hasattr(user, 'chat_state') else user.business_unit
            if platform and business_unit:
                await send_message(platform, user.phone, message, business_unit)
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            logger.warning(f"No se encontró perfil de gamificación para {user.nombre}")
        except Exception as e:
            logger.error(f"Error notificando gamificación a {user.nombre}: {e}", exc_info=True)

    async def generate_challenges(self, user: Person) -> List[str]:
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            return profile.generate_networking_challenges()
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            return []

    async def notify_user_challenges(self, user: Person):
        challenges = await self.generate_challenges(user)
        if challenges:
            message = f"Tienes nuevos desafíos: {', '.join(challenges)}"
            await send_message(
                platform=user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp',
                user_id=user.phone,
                message=message,
                business_unit=user.chat_state.business_unit if hasattr(user, 'chat_state') else user.business_unit
            )
# Fin de ChatBotHandler
