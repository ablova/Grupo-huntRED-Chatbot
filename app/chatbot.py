# Ubicación: /home/pablollh/app/chatbot.py
import logging
import asyncio
import re
from typing import Optional, List, Dict, Any, Tuple
from asgiref.sync import sync_to_async
from django.utils.timezone import now
from django.core.cache import cache

from app.models import (
    ChatState, Person, GptApi, Application, Invitacion, BusinessUnit, Vacante, WhatsAppAPI, EnhancedNetworkGamificationProfile
)
from app.integrations.services import (
    send_message, send_email, reset_chat_state
)
from app.vacantes import VacanteManager
from app.utils import analyze_text  # Encargado del NLP y patrones de intents
from app.parser import CVParser

logger = logging.getLogger(__name__)
CACHE_TIMEOUT = 600  # 10 minutes

async def get_whatsapp_config(phone_id):
    whatsapp_api = await sync_to_async(
        WhatsAppAPI.objects.filter(phoneID=phone_id, is_active=True).select_related('business_unit').first
    )()
    if not whatsapp_api:
        raise ValueError(f"No se encontró configuración para phoneID: {phone_id}")
    return whatsapp_api

class GPTHandler:
    def generate_response(self, prompt: str, api_key: str, model: str = "gpt-3.5-turbo") -> str:
        import openai
        openai.api_key = api_key
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generando respuesta con GPT: {e}", exc_info=True)
            return "Lo siento, no pude procesar tu solicitud."

class ChatBotHandler:
    def __init__(self):
        self.gpt_handler = GPTHandler()

    async def process_message(self, platform: str, user_id: str, text: str, business_unit: BusinessUnit):
        """
        Procesa el mensaje entrante para un usuario en una plataforma específica dentro de una unidad de negocio.
        """
        try:
            chat_state, _ = await sync_to_async(ChatState.objects.get_or_create)(
                user_id=user_id,
                defaults={'platform': platform, 'business_unit': business_unit}
            )
            logger.info(f"Processing message for {user_id} on {platform} for BU {business_unit.name}")
            text = text.strip()

            # Obtener o crear el ChatState y User
            event = await self.get_or_create_event(user_id, platform, business_unit)
            user, _ = await self.get_or_create_user(user_id, event, {})

            # Almacenar mensaje del usuario en el historial
            await self.store_user_message(event, text)

            analysis = analyze_text(text)  # { "intents": [...], "entities": [...], "sentiment": {...} }
            if not analysis or not isinstance(analysis, dict):
                raise ValueError(f"Invalid analysis result: {analysis}")
            intents = analysis.get("intents", [])
            entities = analysis.get("entities", {})
            sentiment = analysis.get("sentiment", {})

            # Si se espera email para consultar estatus
            if event.context.get('awaiting_status_email'):
                await self.handle_status_email(platform, user_id, text, event, business_unit, user)
                return

            # Si se espera info de grupo para invitar
            if event.context.get('awaiting_group_invitation'):
                await self.handle_group_invitation_input(platform, user_id, text, event, business_unit, user)
                return

            # Manejo de intents conocidos
            if await self.handle_known_intents(intents, platform, user_id, event, business_unit, user):
                return

            # Verificar si el usuario seleccionó una vacante anteriormente
            if event.context.get('recommended_jobs') and text.isdigit():
                await self.handle_job_selection(platform, user_id, text, event, business_unit, user)
                return

            # Verificar acciones sobre vacantes (apply_x, details_x, schedule_x, tips_x, book_slot_x)
            if text.startswith("apply_") or text.startswith("details_") or text.startswith("schedule_") or text.startswith("tips_") or text.startswith("book_slot_"):
                await self.handle_job_action(platform, user_id, text, event, business_unit, user)
                return

            # Sin intent ni acción conocida -> GPT fallback
            response = await self.generate_dynamic_response(user, event, text, entities, sentiment)
            await send_message(platform, user_id, response, business_unit)
            await self.store_bot_message(event, response)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await send_message(platform, user_id, "Ha ocurrido un error. Inténtalo más tarde.", business_unit)

    async def get_or_create_event(self, user_id: str, platform: str, business_unit: BusinessUnit) -> ChatState:
        chat_state, created = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=user_id,
            defaults={'platform': platform, 'business_unit': business_unit}
        )
        return chat_state

    async def get_or_create_user(self, user_id: str, event: ChatState, analysis: dict) -> Tuple[Person, bool]:
        user, created = await sync_to_async(Person.objects.get_or_create)(
            phone=user_id,
            defaults={
                'nombre': 'Usuario',
                'number_interaction': 0,  # Inicializa el contador si el usuario es nuevo.
                }
        )
        # Incrementar interacciones si ya existe
        if not created:
            user.number_interaction += 1
            await sync_to_async(user.save)()
        return user, created

    async def handle_known_intents(self, intents: List[str], platform: str, user_id: str, event: ChatState, business_unit: BusinessUnit, user: Person) -> bool:
        for intent in intents:
            logger.debug(f"Intent detectado: {intent}")

            if intent == "saludo":
                return await self.handle_greeting(platform, user_id, event, business_unit, user)

            elif intent == "despedida":
                response = "¡Hasta luego! Si necesitas más ayuda, contáctame de nuevo."
                await send_message(platform, user_id, response, business_unit)
                await self.store_bot_message(event, response)
                await reset_chat_state(user_id)
                return True

            elif intent == "iniciar_conversacion":
                event.context = {}
                await event.asave()
                response = "¡Claro! Empecemos de nuevo. ¿En qué puedo ayudarte?"
                await send_message(platform, user_id, response, business_unit)
                await self.store_bot_message(event, response)
                return True

            elif intent == "menu":
                menu_options = [
                    {'title': 'Ver Vacantes', 'payload': 'ver_vacantes'},
                    {'title': 'Actualizar Perfil', 'payload': 'actualizar_perfil'},
                    {'title': 'Ayuda Postulación', 'payload': 'ayuda_postulacion'},
                    {'title': 'Consultar Estatus', 'payload': 'consultar_estatus'}
                ]
                await send_message(platform, user_id, "Aquí tienes el menú principal:", business_unit, options=menu_options)
                await self.store_bot_message(event, "Aquí tienes el menú principal:")
                return True

            elif intent == "solicitar_ayuda_postulacion":
                response = "Puedo guiarte en el proceso de postulación. ¿Qué necesitas saber?"
                await send_message(platform, user_id, response, business_unit)
                await self.store_bot_message(event, response)
                return True

            elif intent == "consultar_estatus":
                response = "Por favor, proporciona tu correo electrónico asociado a la aplicación."
                await send_message(platform, user_id, response, business_unit)
                await self.store_bot_message(event, response)
                event.context['awaiting_status_email'] = True
                await event.asave()
                return True

            elif intent in ["travel_in_group", "travel_with_family"]:
                response = (
                    "Entiendo, ¿te gustaría invitar a tus acompañantes para que también obtengan oportunidades laborales? "
                    "Envíame su nombre completo y teléfono en el formato: 'Nombre Apellido +52XXXXXXXXXX'."
                )
                await send_message(platform, user_id, response, business_unit)
                await self.store_bot_message(event, response)
                event.context['awaiting_group_invitation'] = True
                await event.asave()
                return True

            elif intent == "ver_vacantes":
                recommended_jobs = await sync_to_async(VacanteManager.match_person_with_jobs)(user)
                if recommended_jobs:
                    event.context['recommended_jobs'] = recommended_jobs
                    await event.asave()
                    await self.present_job_listings(platform, user_id, recommended_jobs, business_unit, event)
                else:
                    resp = "No encontré vacantes para tu perfil por ahora."
                    await send_message(platform, user_id, resp, business_unit)
                    await self.store_bot_message(event, resp)
                return True
            elif intent == "agradecimiento":
                response = "¡De nada! ¿En qué más puedo ayudarte?"
                await send_message(platform, user_id, response, business_unit)
                await self.store_bot_message(event, response)
                return True
            elif intent == "busqueda_impacto":
                response = "Entiendo que buscas un trabajo con impacto social. Puedo mostrarte vacantes que destaquen proyectos con propósito. ¿Deseas verlas?"
                await send_message(platform, user_id, response, business_unit)
                await self.store_bot_message(event, response)
                return True
            elif intent == "solicitar_informacion_empresa":
                response = "¿Sobre qué empresa necesitas información? Puedo contarte sobre sus valores, cultura o posiciones disponibles."
                await send_message(platform, user_id, response, business_unit)
                await self.store_bot_message(event, response)
                return True
            elif intent == "solicitar_tips_entrevista":
                # Puedes integrar GPT para dar consejos o tener una respuesta fija
                response = "Para entrevistas: investiga la empresa, se puntual, muestra logros cuantificables y prepara ejemplos de situaciones pasadas."
                await send_message(platform, user_id, response, business_unit)
                await self.store_bot_message(event, response)
                return True
            elif intent == "consultar_sueldo_mercado":
                response = "¿Para qué posición o nivel buscas el rango salarial de mercado? Puedo darte una estimación."
                await send_message(platform, user_id, response, business_unit)
                await self.store_bot_message(event, response)
                return True
            elif intent == "actualizar_perfil":
                response = "Claro, ¿qué dato de tu perfil deseas actualizar? Ejemplo: nombre, email, experiencia, o expectativas salariales."
                await send_message(platform, user_id, response, business_unit)
                await self.store_bot_message(event, response)
                return True
            elif intent == "notificaciones":
                response = (
                    "Puedo enviarte notificaciones automáticas sobre cambios en tus procesos. "
                    "¿Quieres activarlas? Responde 'sí' para confirmar."
                )
                await send_message(platform, user_id, response, business_unit)
                await self.store_bot_message(event, response)
                return True

        return False


    async def handle_tyc_acceptance(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit) -> bool:
        configuracion_bu = await sync_to_async(ConfiguracionBU.objects.filter(business_unit=business_unit).first)()
        email = configuracion_bu.correo_bu if configuracion_bu else "hola@amigro.org"

        if text.lower() in ['sí', 'si', 'aceptar_tyc']:
            response = (
                "¡Gracias por aceptar los Términos y Condiciones! Ahora podemos continuar. 😊 "
                "Cuéntame más sobre lo que buscas en un empleo para ayudarte mejor. Y platícame de ti,"
                "para que logra conocer que tipo de oportunidad puede serte atractiva y relevante. "
                "Entre más me platiques/escribas, mejor puedo conocer tus habilidades, intereses, etc."
            )
            await send_message(platform, user_id, response, business_unit)
            await self.store_bot_message(event, response)
            event.context['awaiting_tyc_acceptance'] = False
            await event.asave()
            return True

        elif text.lower() in ['no', 'rechazar_tyc']:
            response = (
                f"Para utilizar nuestra plataforma, es necesario aceptar los Términos y Condiciones. "
                f"Si tienes dudas, por favor contáctanos en {email}."
            )
            await send_message(platform, user_id, response, business_unit)
            await self.store_bot_message(event, response)
            return True

        return False

    async def handle_greeting(self, platform: str, user_id: str, event: ChatState, business_unit: BusinessUnit, user: Person) -> bool:
        configuracion_bu = await sync_to_async(ConfiguracionBU.objects.filter(business_unit=business_unit).first)()
        tos_link = f"{configuracion_bu.dominio_bu}/tos" if configuracion_bu and configuracion_bu.dominio_bu else "https://amigro.org/tos"
        logo_url = configuracion_bu.logo_url if configuracion_bu and configuracion_bu.logo_url else "https://amigro.org/logo.png"

        # Primer mensaje: Saludo
        response = (
            f"¡Hola {user.name}! Somos {business_unit.name}, una plataforma diseñada para ayudarte a encontrar "
            f"el empleo ideal basado en tu experiencia, momento tanto profesional como personal e intereses. "
            f"¡Cuéntame un poco más sobre ti!, que para eso me han creado! 😊"
        )
        await send_message(platform, user_id, response, business_unit)
        await self.store_bot_message(event, response)

        # Pausa
        await asyncio.sleep(2)

        # Segundo mensaje: Información sobre la unidad de negocio y Términos
        business_info = business_unit.description or (
            "Nos especializamos en conectar talentos como tú con oportunidades laborales ideales."
        )
        tos_message = (
            f"En {business_unit.name}, {business_info}.\n\n"
            f"Para continuar, necesitamos que aceptes nuestros Términos y Condiciones. "
            f"Puedes leerlos aquí: {tos_link}"
        )
        await send_message(platform, user_id, tos_message, business_unit)
        await self.store_bot_message(event, tos_message)

        # Pausa
        await asyncio.sleep(2)

        # Enviar logo
        await send_image(platform, user_id, "Este es nuestro logo oficial:", logo_url, business_unit)

        # Pausa
        await asyncio.sleep(2)

        # Tercer mensaje: Quick Reply
        quick_reply_message = "¿Aceptas nuestros Términos y Condiciones? Esto es necesario para continuar usando la plataforma."
        quick_reply_buttons = [
            {'title': 'Sí', 'payload': 'aceptar_tyc'},
            {'title': 'No', 'payload': 'rechazar_tyc'}
        ]
        await send_message(platform, user_id, quick_reply_message, business_unit, options=quick_reply_buttons)
        await self.store_bot_message(event, quick_reply_message)

        # Actualizar contexto
        event.context['awaiting_tyc_acceptance'] = True
        await event.asave()

        return True
    
    async def handle_status_email(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        email_pattern = r"[^@]+@[^@]+\.[^@]+"
        if re.match(email_pattern, text):
            applications = await sync_to_async(Application.objects.filter)(user__email=text)
            application = await sync_to_async(applications.first)()
            if application:
                msg = f"El estatus de tu aplicación es: {application.status}."
            else:
                msg = "No encuentro una aplicación con ese correo."
            await send_message(platform, user_id, msg, business_unit)
            await self.store_bot_message(event, msg)
            event.context['awaiting_status_email'] = False
            await event.asave()
        else:
            msg = "Ese no parece un correo válido. Intenta nuevamente."
            await send_message(platform, user_id, msg, business_unit)
            await self.store_bot_message(event, msg)

    async def update_candidate_status_from_tracker(self, updates: List[Dict[str, Any]]):
        """
        Actualiza el estatus de los candidatos basado en actualizaciones externas (JobTracker).
        """
        for update in updates:
            try:
                # Asumimos que las actualizaciones incluyen `user_id` y `new_status`
                user = await sync_to_async(Person.objects.get)(phone=update['user_id'])
                application = await sync_to_async(Application.objects.get)(
                    user=user,
                    vacancy_id=update['vacancy_id']
                )
                application.status = update['new_status']
                await sync_to_async(application.save)()

                # Notificar al candidato
                business_unit = application.vacancy.business_unit
                message = f"Tu estatus para la vacante '{application.vacancy.titulo}' ha cambiado a: {update['new_status']}."
                await send_message('whatsapp', user.phone, message, business_unit)
            except Exception as e:
                logger.error(f"Error actualizando estatus de candidato: {e}")

    async def handle_group_invitation_input(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        parts = text.split()
        if len(parts) >= 3:
            phone_number = parts[-1]
            name = parts[0]
            apellido = parts[1]
            await self.invite_known_person(user, name, apellido, phone_number)

            resp = f"He invitado a {name} {apellido}. ¿Deseas invitar a alguien más? Responde 'sí' o 'no'."
            await send_message(platform, user_id, resp, business_unit)
            await self.store_bot_message(event, resp)

            # Si el usuario responde luego 'no', en el próximo mensaje deberíamos manejarlo en el process_message.
            # Por simplicidad, lo revisamos en intent. Si dice no se desactiva.
            # Manejo simplificado: el usuario tendrá que decir 'no' en un próximo mensaje -> Intent "negacion".
        else:
            resp = "Formato no válido. Envía: 'Nombre Apellido +521234567890'"
            await send_message(platform, user_id, resp, business_unit)
            await self.store_bot_message(event, resp)

    async def invite_known_person(self, referrer: Person, name: str, apellido: str, phone_number: str):
        invitado, created = await sync_to_async(Person.objects.get_or_create)(
            phone=phone_number,
            defaults={'name': name, 'apellido_paterno': apellido}
        )
        await sync_to_async(Invitacion.objects.create)(referrer=referrer, invitado=invitado)
        # Podríamos enviar un mensaje al invitado vía WhatsApp si se deseara, con send_message.

    async def handle_job_selection(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        recommended_jobs = event.context.get('recommended_jobs', [])
        try:
            job_index = int(text.strip()) - 1
        except ValueError:
            resp = "Por favor, ingresa un número válido."
            await send_message(platform, user_id, resp, business_unit)
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
            await send_message(platform, user_id, resp, business_unit, options=buttons)
            await self.store_bot_message(event, resp)
            event.context['selected_job'] = selected_job
            await event.asave()
        else:
            resp = "Selección inválida."
            await send_message(platform, user_id, resp, business_unit)
            await self.store_bot_message(event, resp)

    async def handle_job_action(self, platform: str, user_id: str, text: str, event: ChatState, business_unit: BusinessUnit, user: Person):
        recommended_jobs = event.context.get('recommended_jobs', [])

        if text.startswith("apply_"):
            job_index = int(text.split('_')[1])
            if 0 <= job_index < len(recommended_jobs):
                job = recommended_jobs[job_index]
                await sync_to_async(Application.objects.create)(user=user, vacancy_id=job['id'], status='applied')
                resp = "¡Has aplicado a la vacante con éxito!"
                await send_message(platform, user_id, resp, business_unit)
                await self.store_bot_message(event, resp)
            else:
                resp = "No encuentro esa vacante."
                await send_message(platform, user_id, resp, business_unit)
                await self.store_bot_message(event, resp)

        elif text.startswith("details_"):
            job_index = int(text.split('_')[1])
            if 0 <= job_index < len(recommended_jobs):
                job = recommended_jobs[job_index]
                details = job.get('description', 'No hay descripción disponible.')
                resp = f"Detalles de la posición:\n{details}"
                await send_message(platform, user_id, resp, business_unit)
                await self.store_bot_message(event, resp)
            else:
                resp = "No encuentro esa vacante."
                await send_message(platform, user_id, resp, business_unit)
                await self.store_bot_message(event, resp)

        elif text.startswith("schedule_"):
            job_index = int(text.split('_')[1])
            if 0 <= job_index < len(recommended_jobs):
                selected_job = recommended_jobs[job_index]
                slots = await self.get_interview_slots(selected_job)
                if not slots:
                    resp = "No hay horarios disponibles por el momento."
                    await send_message(platform, user_id, resp, business_unit)
                    await self.store_bot_message(event, resp)
                    return
                buttons = [{'title': slot['label'], 'payload': f"book_slot_{idx}"} for idx, slot in enumerate(slots)]
                event.context['available_slots'] = slots
                event.context['selected_job'] = selected_job
                await event.asave()
                resp = "Elige un horario para la entrevista:"
                await send_message(platform, user_id, resp, business_unit, options=buttons)
                await self.store_bot_message(event, resp)
            else:
                resp = "No encuentro esa vacante."
                await send_message(platform, user_id, resp, business_unit)
                await self.store_bot_message(event, resp)

        elif text.startswith("tips_"):
            job_index = int(text.split('_')[1])
            # GPT para tips
            prompt = "Dame consejos para la entrevista en esta posición"
            response = await self.generate_dynamic_response(user, event, prompt, {}, {})
            if not response:
                response = "Prepárate, investiga la empresa, sé puntual y comunica tus logros con seguridad."
            await send_message(platform, user_id, response, business_unit)
            await self.store_bot_message(event, response)

        elif text.startswith("book_slot_"):
            slot_index = int(text.split('_')[2])
            available_slots = event.context.get('available_slots', [])
            if 0 <= slot_index < len(available_slots):
                selected_slot = available_slots[slot_index]
                resp = f"Entrevista agendada para {selected_slot['label']} ¡Éxito!"
                await send_message(platform, user_id, resp, business_unit)
                await self.store_bot_message(event, resp)
            else:
                resp = "No encuentro ese horario."
                await send_message(platform, user_id, resp, business_unit)
                await self.store_bot_message(event, resp)

    async def get_interview_slots(self, job: Dict[str, Any]) -> List[Dict[str, str]]:
        # Slots simulados
        return [
            {'label': 'Mañana 10:00 AM', 'datetime': '2024-12-10T10:00:00'},
            {'label': 'Mañana 11:00 AM', 'datetime': '2024-12-10T11:00:00'}
        ]

    async def generate_dynamic_response(self, user: Person, event: ChatState, user_message: str, entities, sentiment) -> str:
        """
        Genera una respuesta dinámica usando GPT. El prompt puede ser personalizado con el historial.
        """
        history = await self.get_conversation_history(event)
        prompt = self.build_gpt_prompt(history, user_message, user, entities, sentiment)

        gpt_api = await sync_to_async(GptApi.objects.first)()
        if not gpt_api:
            logger.warning("No se encontró configuración GptApi, no se puede usar GPT.")
            return "Lo siento, no tengo suficiente información para responder."
        
        gpt_response = self.gpt_handler.generate_response(prompt, gpt_api.api_token, gpt_api.model or "gpt-3.5-turbo")
        return gpt_response

    def build_gpt_prompt(self, history, user_message, user: Person, entities, sentiment):
        """
        Construye el prompt para GPT incorporando historial y contexto.
        """
        roles_text = ""
        for msg in history[-5:]:  # Últimos 5 mensajes
            if msg["role"] == "user":
                roles_text += f"Usuario: {msg['content']}\n"
            else:
                roles_text += f"Asistente: {msg['content']}\n"

        roles_text += f"Usuario: {user_message}\nAsistente:"
        return roles_text

    async def get_conversation_history(self, event: ChatState):
        history = event.metadata.get('history', [])
        return history

    async def store_user_message(self, event: ChatState, message: str):
        history = event.metadata.get('history', [])
        history.append({"role": "user", "content": message, "timestamp": now().isoformat()})
        event.metadata['history'] = history
        await sync_to_async(event.save)()

    async def store_bot_message(self, event: ChatState, message: str):
        history = event.metadata.get('history', [])
        history.append({"role": "assistant", "content": message, "timestamp": now().isoformat()})
        event.metadata['history'] = history
        await sync_to_async(event.save)()

    async def present_job_listings(self, platform: str, user_id: str, jobs: List[Dict[str, Any]], business_unit: BusinessUnit, event: ChatState):
        """
        Muestra las vacantes recomendadas al usuario.
        """
        response = "Aquí tienes algunas vacantes recomendadas:\n"
        for idx, job in enumerate(jobs[:5]):
            response += f"{idx+1}. {job['title']} en {job['company']}\n"
        response += "Responde con el número de la vacante que te interesa."
        await send_message(platform, user_id, response, business_unit)
        await self.store_bot_message(event, response)

    async def send_profile_completion_email(self, user_id: str, context: dict):
        """
        Envía un correo electrónico para completar el perfil del usuario, 
        integrando el nombre y dominio de la BusinessUnit activa.
        """
        try:
            # Obtener el usuario de manera asíncrona
            user = await sync_to_async(Person.objects.get)(phone=user_id)
            email = user.email
            if email:
                business_unit = user.business_unit
                try:
                    # Obtener la configuración de la BusinessUnit
                    configuracion_bu = await sync_to_async(ConfiguracionBU.objects.get)(business_unit=business_unit)
                    dominio_bu = configuracion_bu.dominio_bu
                except ObjectDoesNotExist:
                    logger.error(f"No se encontró ConfiguracionBU para la unidad de negocio {business_unit.name}.")
                    dominio_bu = "tu_dominio.com"  # Valor por defecto o maneja según tu lógica

                # Construir el asunto y cuerpo del correo
                subject = f"Completa tu perfil en {business_unit.name} ({dominio_bu})"
                body = (
                    f"Hola {user.name},\n\n"
                    f"Por favor completa tu perfil en {dominio_bu} para continuar."
                )

                # Enviar el correo electrónico
                await send_email(
                    business_unit_name=business_unit.name,
                    subject=subject,
                    to_email=email,
                    body=body
                )
                logger.info(f"Correo de completación de perfil enviado a {email}")
            else:
                logger.warning(f"Usuario con phone {user_id} no tiene email registrado.")
        except Person.DoesNotExist:
            logger.error(f"No se encontró usuario con phone {user_id} para enviar correo.")
        except Exception as e:
            logger.error(f"Error enviando correo de completación de perfil a {user_id}: {e}", exc_info=True)
    
    async def recap_information(self, user: Person):
        recap_message = (
            f"Recapitulación de tu información:\n"
            f"Nombre: {user.name}\n"
            f"Apellido Paterno: {user.apellido_paterno}\n"
            f"Apellido Materno: {user.apellido_materno}\n"
            f"Fecha de Nacimiento: {user.fecha_nacimiento}\n"
            f"Sexo: {user.sexo}\n"
            f"Nacionalidad: {user.nationality}\n"
            f"Permiso de Trabajo: {user.permiso_trabajo}\n"
            f"CURP: {user.curp}\n"
            f"Ubicación: {user.ubicacion}\n"
            f"Experiencia Laboral: {user.work_experience}\n"
            f"Nivel Salarial Esperado: {user.nivel_salarial}\n\n"
            "¿Es correcta esta información? Responde 'Sí' o 'No'."
        )
        return recap_message
    
    def handle_cv_upload(user, uploaded_file):
        person, created = Person.objects.get_or_create(name=user.name)
        person.cv_file = uploaded_file
        person.cv_parsed = False  # Se marca como no analizado
        person.save()
        return "Tu CV ha sido recibido y será analizado."
    

    # Network Gamification - Word of Mouth
    def award_gamification_points(self, user, activity_type):
        """Otorga puntos de gamificación al usuario."""
        try:
            profile = EnhancedNetworkGamificationProfile.objects.get(user=user)
            profile.award_points(activity_type)
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            print(f"No gamification profile found for user {user.id}")

    def handle_user_interaction(self, user, message):
        # Manejar interacciones del usuario
        if "complete_profile" in message:
            self.award_gamification_points(user, 'profile_update')