import logging
import asyncio
from typing import Optional, Tuple, List
from asgiref.sync import sync_to_async
from app.models import (
    ChatState, Pregunta, Person, FlowModel, BusinessUnit
)
from app.vacantes import VacanteManager
from app.integrations.services import (
    send_message, send_whatsapp_decision_buttons, reset_chat_state, get_api_instance
)
from app.utils import analyze_text, clean_text
from django.core.cache import cache

logger = logging.getLogger(__name__)
CACHE_TIMEOUT = 600  # 10 minutes

class ChatBotHandler:
    async def process_message(self, platform: str, user_id: str, text: str, business_unit: BusinessUnit):
        """
        Procesa un mensaje entrante del usuario y gestiona el flujo de conversación.
        """
        logger.info(f"Processing message for {user_id} on {platform} for business unit {business_unit.name}")

        try:
            # Etapa 1: Preprocesamiento del Mensaje
            text = clean_text(text)
            analysis = analyze_text(text)
            intents = analysis.get("intents", [])
            entities = analysis.get("entities", {})
            if not isinstance(intents, list):
                logger.error(f"Invalid intents format: {intents}")
                intents = []
            cache_key = f"analysis_{user_id}"
            cache.set(cache_key, analysis, CACHE_TIMEOUT)
            logger.debug(f"Message analysis cached with key {cache_key}")

            # Etapa 2: Inicialización del Contexto de Conversación
            event = await self.get_or_create_event(user_id, platform, business_unit)
            if not event:
                logger.error(f"No se pudo crear el evento para el usuario {user_id}.")
                await send_message(platform, user_id, "Error al inicializar el contexto. Inténtalo más tarde.", business_unit)
                return
            user, created = await self.get_or_create_user(user_id, event, analysis)
            if not user:
                logger.error(f"No se pudo crear o recuperar el usuario {user_id}.")
                await send_message(platform, user_id, "Error al recuperar tu información. Inténtalo más tarde.", business_unit)
                return
            context = self.build_context(user)

            # Etapa 3: Manejo de Intents Conocidos
            if await self.handle_known_intents(intents, platform, user_id, event, business_unit):
                return

            # Etapa 4: Continuación del Flujo de Conversación
            current_question = event.current_question
            if not current_question:
                first_question = await self.get_first_question(event.flow_model)
                if first_question:
                    event.current_question = first_question
                    await event.asave()
                    await send_message(platform, user_id, first_question.content, business_unit)
                else:
                    logger.error("No first question found in the flow model")
                    await send_message(platform, user_id, "Lo siento, no se pudo iniciar la conversación en este momento.", business_unit)
                return

            # Etapa 5: Procesamiento de la Respuesta del Usuario
            response, options = await self.determine_next_question(event, text, analysis, context)

            # Etapa 6: Guardar estado y enviar respuesta
            await event.asave()
            await self.send_response(platform, user_id, response, business_unit, options)

            # Etapa 7: Manejo de Desviaciones en la Conversación
            if await self.detect_and_handle_deviation(event, text, analysis):
                return

            # Etapa 8: Verificación del Perfil del Usuario
            profile_check = await self.verify_user_profile(user)
            if profile_check:
                await send_message(platform, user_id, profile_check, business_unit)
                return

        except Exception as e:
            logger.error(f"Error processing message for {user_id}: {e}", exc_info=True)
            await send_message(platform, user_id, "Ha ocurrido un error. Por favor, inténtalo de nuevo más tarde.", business_unit)

    # -------------------------------------------
    # Métodos Auxiliares
    # -------------------------------------------

    async def get_or_create_event(self, user_id: str, platform: str, business_unit: BusinessUnit) -> Optional[ChatState]:
        try:
            chat_state, created = await sync_to_async(ChatState.objects.get_or_create)(
                user_id=user_id,
                defaults={
                    'platform': platform,
                    'business_unit': business_unit,
                    'current_question': None
                }
            )
            if created:
                logger.debug(f"ChatState creado para usuario {user_id}")
            else:
                logger.debug(f"ChatState obtenido para usuario {user_id}")
            return chat_state
        except Exception as e:
            logger.error(f"Error en get_or_create_event para usuario {user_id}: {e}", exc_info=True)
            raise

    async def get_or_create_user(self, user_id: str, event: ChatState, analysis: dict) -> Tuple[Person, bool]:
        try:
            entities = analysis.get('entities', {})
            name = entities.get('name') or event.platform or 'Usuario'

            user, created = await sync_to_async(Person.objects.get_or_create)(
                phone=user_id,
                defaults={'name': name}
            )
            if created:
                logger.debug(f"Persona creada: {user}")
            else:
                logger.debug(f"Persona obtenida: {user}")
            return user, created
        except Exception as e:
            logger.error(f"Error en get_or_create_user para usuario {user_id}: {e}", exc_info=True)
            raise

    def build_context(self, user: Person) -> dict:
        """
        Construye el contexto de la conversación basado en la información del usuario.
        """
        context = {
            'user_name': user.name,
            'user_phone': user.phone,
            # Agrega más campos según sea necesario
        }
        logger.debug(f"Contexto construido para usuario {user.phone}: {context}")
        return context

    async def handle_known_intents(
        self, intents: List[str], platform: str, user_id: str, event: ChatState, business_unit: BusinessUnit
    ) -> bool:
        for intent in intents:
            logger.debug(f"Intent detectado: {intent}")
            if intent == "saludo":
                greeting_message = f"Hola, buenos días. ¿Quieres conocer más acerca de {business_unit.name}?"
                quick_replies = [{"title": "Sí"}, {"title": "No"}]
                await send_whatsapp_decision_buttons(
                    user_id=user_id,
                    message=greeting_message,
                    buttons=quick_replies,
                    phone_id=business_unit.whatsapp_api.phoneID
                )
                logger.info(f"Intent 'saludo' manejado para usuario {user_id}")
                return True
            elif intent == 'despedida':
                await send_message(platform, user_id, "¡Hasta luego! Si necesitas más ayuda, no dudes en contactarnos.", business_unit)
                logger.info(f"Intent 'despedida' manejado para usuario {user_id}")
                await self.reset_chat_state(user_id)
                return True
            elif intent == 'iniciar_conversacion':
                event.current_question = None
                await event.asave()
                await send_message(platform, user_id, "¡Claro! Empecemos de nuevo. ¿En qué puedo ayudarte?", business_unit)
                logger.info(f"Intent 'iniciar_conversacion' manejado para usuario {user_id}")
                return True
            elif intent == 'menu':
                await self.handle_persistent_menu(event)
                logger.info(f"Intent 'menu' manejado para usuario {user_id}")
                return True
            elif intent == 'solicitar_ayuda_postulacion':
                ayuda_message = "Claro, puedo ayudarte con el proceso de postulación. ¿Qué necesitas saber específicamente?"
                await send_message(platform, user_id, ayuda_message, business_unit)
                logger.info(f"Intent 'solicitar_ayuda_postulacion' manejado para usuario {user_id}")
                return True
            elif intent == 'consultar_estatus':
                estatus_message = "Para consultar el estatus de tu aplicación, por favor proporciona tu número de aplicación o correo electrónico asociado."
                await send_message(platform, user_id, estatus_message, business_unit)
                logger.info(f"Intent 'consultar_estatus' manejado para usuario {user_id}")
                return True
            # Agrega más intents conocidos y sus manejadores aquí

        return False  # No se manejó ningún intent conocido

    async def handle_persistent_menu(self, event: ChatState):
        """
        Maneja el acceso al menú persistente.
        """
        business_unit = event.business_unit
        menu_message = f"Aquí tienes el menú principal de {business_unit.name}:"
        await send_message(event.platform, event.user_id, menu_message, business_unit)
        await send_menu(event.platform, event.user_id, business_unit)
        return

    async def determine_next_question(self, event: ChatState, user_message: str, analysis: dict, context: dict) -> Tuple[Optional[str], List]:
        current_question = event.current_question
        logger.info(f"Procesando la pregunta actual: {current_question.content}")

        try:
            # 1. Manejar acciones basadas en action_type
            if current_question.action_type:
                response, options = await self._handle_action_type(event, current_question, context)
                return response, options

            # 2. Manejar respuestas de botones
            if current_question.botones_pregunta.exists():
                response, options = await self._handle_button_response(event, current_question, user_message, context)
                return response, options

            # 3. Manejar diferentes input_type
            input_type_handlers = {
                'skills': self._handle_skills_input,
                'select_job': self._handle_select_job_input,
                'schedule_interview': self._handle_schedule_interview_input,
                'confirm_interview_slot': self._handle_confirm_interview_slot_input,
                'finalizar_perfil': self._handle_finalize_profile_input,
                'confirm_recap': self._handle_confirm_recap_input,
                # Agrega más input_types si es necesario
            }

            handler = input_type_handlers.get(current_question.input_type)
            if handler:
                response, options = await handler(event, current_question, user_message, context)
                return response, options

            # 4. Flujo estándar: avanzar a la siguiente pregunta
            next_question = await self.get_next_question(current_question, user_message)
            if next_question:
                event.current_question = next_question
                await event.asave()
                response = render_dynamic_content(next_question.content, context)
                return response, []
            else:
                return "No hay más preguntas en este flujo.", []

        except Exception as e:
            logger.error(f"Error determinando la siguiente pregunta: {e}", exc_info=True)
            return "Ha ocurrido un error al procesar tu respuesta. Por favor, inténtalo de nuevo más tarde.", []

    async def _handle_skills_input(self, event, current_question, user_message, context):
        user = await sync_to_async(Person.objects.get)(phone=event.user_id)
        user.skills = user_message
        await sync_to_async(user.save)()

        vacante_manager = VacanteManager(context)
        recommended_jobs = await sync_to_async(vacante_manager.match_person_with_jobs)(user)

        if recommended_jobs:
            response = "Aquí tienes algunas vacantes que podrían interesarte:\n"
            for idx, job in enumerate(recommended_jobs[:5]):
                response += f"{idx + 1}. {job['title']} en {job['company']}\n"
            response += "Por favor, ingresa el número de la vacante que te interesa."
            event.context = {'recommended_jobs': recommended_jobs}
            await event.asave()
            return response, []
        else:
            response = "Lo siento, no encontré vacantes que coincidan con tu perfil."
            return response, []

    async def _handle_select_job_input(self, event, current_question, user_message, context):
        try:
            job_index = int(user_message.strip()) - 1
        except ValueError:
            return "Por favor, ingresa un número válido.", []

        recommended_jobs = event.context.get('recommended_jobs')
        if recommended_jobs and 0 <= job_index < len(recommended_jobs):
            selected_job = recommended_jobs[job_index]
            event.context['selected_job'] = selected_job
            next_question = await self.get_question_by_option(event.flow_model, 'schedule_interview')
            if next_question:
                event.current_question = next_question
                await event.asave()
                return next_question.content, []
            else:
                logger.error("Pregunta 'schedule_interview' no encontrada.")
                return "No se pudo continuar con el proceso.", []
        else:
            return "Selección inválida.", []

    async def _handle_schedule_interview_input(self, event, current_question, user_message, context):
        selected_job = event.context.get('selected_job')
        if not selected_job:
            return "No se encontró la vacante seleccionada.", []

        vacante_manager = VacanteManager(context)
        available_slots = await sync_to_async(vacante_manager.get_available_slots)(selected_job)
        if available_slots:
            response = "Estos son los horarios disponibles para la entrevista:\n"
            for idx, slot in enumerate(available_slots):
                response += f"{idx + 1}. {slot}\n"
            response += "Por favor, selecciona el número del horario que prefieras."
            event.context['available_slots'] = available_slots
            await event.asave()
            return response, []
        else:
            return "No hay horarios disponibles.", []

    async def _handle_confirm_interview_slot_input(self, event, current_question, user_message, context):
        try:
            slot_index = int(user_message.strip()) - 1
        except ValueError:
            return "Por favor, ingresa un número válido.", []

        available_slots = event.context.get('available_slots')
        selected_job = event.context.get('selected_job')
        user = await sync_to_async(Person.objects.get)(phone=event.user_id)
        if available_slots and 0 <= slot_index < len(available_slots):
            selected_slot = available_slots[slot_index]
            vacante_manager = VacanteManager(context)
            success = await sync_to_async(vacante_manager.book_interview_slot)(selected_job, selected_slot, user)
            if success:
                response = f"Has reservado tu entrevista en el horario: {selected_slot}."
                await event.asave()
                return response, []
            else:
                return "No se pudo reservar el horario, por favor intenta nuevamente.", []
        else:
            return "Selección inválida. Por favor, intenta nuevamente.", []

    async def _handle_finalize_profile_input(self, event, current_question, user_message, context):
        user = await sync_to_async(Person.objects.get)(phone=event.user_id)
        recap_message = await self.recap_information(user)
        await send_message(event.platform, event.user_id, recap_message, event.business_unit)
        next_question = await self.get_question_by_option(event.flow_model, 'confirm_recap')
        if next_question:
            event.current_question = next_question
            await event.asave()
            return next_question.content, []
        else:
            logger.error("Pregunta 'confirm_recap' no encontrada.")
            return "No se pudo continuar con el proceso.", []

    async def _handle_confirm_recap_input(self, event, current_question, user_message, context):
        if user_message.strip().lower() in ['sí', 'si', 's']:
            response = "¡Perfecto! Continuemos."
            next_question = await self.get_question_by_option(event.flow_model, 'next_step')
            if next_question:
                event.current_question = next_question
                await event.asave()
                return response, []
            else:
                logger.error("Pregunta 'next_step' no encontrada.")
                return "No se pudo continuar con el proceso.", []
        else:
            await self.handle_correction_request(event, user_message)
            return None, []

    async def get_question_by_option(self, flow_model, option):
        question = await sync_to_async(Pregunta.objects.filter(flow_model=flow_model, option=option).first)()
        return question

    async def reset_chat_state(self, user_id: str):
        await reset_chat_state(user_id=user_id)
        logger.info(f"Chat state reset for user {user_id}")

    async def send_response(self, platform: str, user_id: str, response: str, business_unit: BusinessUnit, options: Optional[List] = None):
        """
        Envía una respuesta al usuario, incluyendo opciones si las hay.
        """
        logger.debug(f"Preparando para enviar respuesta al usuario {user_id}: {response} con opciones: {options}")

        # Enviar el mensaje
        await send_message(platform, user_id, response, business_unit, options=options)

        logger.info(f"Respuesta enviada al usuario {user_id}")

    async def detect_and_handle_deviation(self, event, text, analysis):
        # Define deviation thresholds and strategies
        # Placeholder para lógica de desviación
        # Implementa tu lógica específica aquí
        return False  # Asumiendo que no hay desviación por ahora

    async def verify_user_profile(self, user: Person) -> Optional[str]:
        required_fields = ['name', 'apellido_paterno', 'skills', 'ubicacion', 'email']
        missing_fields = [field for field in required_fields if not getattr(user, field, None)]
        if missing_fields:
            fields_str = ", ".join(missing_fields)
            return f"Para continuar, completa estos datos: {fields_str}."
        logger.debug(f"Perfil completo para usuario {user.phone}.")
        return None

    async def recap_information(self, user):
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

    async def handle_correction_request(self, event, user_response):
        correction_message = "Por favor, indica qué dato deseas corregir (e.g., 'nombre', 'email')."
        await self.send_response(event.platform, event.user_id, correction_message, event.business_unit)
        event.awaiting_correction = True
        await event.asave()

    async def update_user_information(self, user, user_input):
        field_mapping = {
            "nombre": "name",
            "apellido paterno": "apellido_paterno",
            "apellido materno": "apellido_materno",
            "nacionalidad": "nationality",
            "email": "email",
            "ubicación": "ubicacion",
            "experiencia laboral": "work_experience",
            "nivel salarial": "nivel_salarial",
        }
        try:
            field, new_value = user_input.split(':', 1)
            field = field_mapping.get(field.strip().lower())
            if field:
                setattr(user, field, new_value.strip())
                await sync_to_async(user.save)()
            else:
                logger.info(f"Campo no encontrado para actualizar: {user_input}")
        except ValueError:
            logger.warning(f"Entrada de usuario inválida para actualización: {user_input}")

    async def invite_known_person(self, referrer, name, apellido, phone_number):
        invitado, created = await sync_to_async(Person.objects.get_or_create)(
            phone=phone_number,
            defaults={'name': name, 'apellido_paterno': apellido},
        )

        await sync_to_async(Invitacion.objects.create)(referrer=referrer, invitado=invitado)

        if created:
            mensaje = (
                f"Hola {name}, has sido invitado por {referrer.name} a unirte a Amigro.org. "
                "¡Encuentra empleo en México de manera segura, gratuita e incluso podemos asesorarte en temas migrantes!"
            )
            await send_message("whatsapp", phone_number, mensaje, referrer.business_unit)

        return invitado

    async def get_first_question(self, flow_model: FlowModel) -> Optional[Pregunta]:
        first_question = await sync_to_async(flow_model.preguntas.order_by('order').first)()
        if first_question:
            logger.debug(f"Primera pregunta obtenida: {first_question.content}")
        else:
            logger.debug("No se encontró la primera pregunta en el FlowModel.")
        return first_question

    async def get_next_question(self, current_question: Pregunta, user_message: str) -> Optional[Pregunta]:
        response = user_message.strip().lower()
        if response in ['sí', 'si']:
            next_question = current_question.next_si
        else:
            next_question = current_question.next_no

        if next_question:
            logger.debug(f"Siguiente pregunta basada en la respuesta '{response}': {next_question.content}")
        else:
            logger.debug("No hay siguiente pregunta definida en el flujo.")
        return next_question

    async def _handle_action_type(
            self, event: ChatState, current_question: Pregunta, context: dict
        ) -> Tuple[str, List]:
        action = current_question.action_type
        logger.info(f"Handling action type '{action}' para pregunta {current_question.id}")

        if action == 'send_email':
            await self.send_profile_completion_email(event.user_id, context)
            response = "Te hemos enviado un correo electrónico con más información."
            return response, []
        elif action == 'start_process':
            response = "Estamos iniciando el proceso solicitado."
            return response, []
        else:
            logger.warning(f"Tipo de acción desconocida: {action}")
            response = "Ha ocurrido un error al procesar tu solicitud."
            return response, []

    async def send_profile_completion_email(self, user_id: str, context: dict):
        """
        Envía un correo electrónico para completar el perfil del usuario.
        """
        from app.integrations.services import send_email
        try:
            user = await sync_to_async(Person.objects.get)(phone=user_id)
            email = user.email
            if email:
                subject = "Completa tu perfil en Amigro.org"
                body = f"Hola {user.name},\n\nPor favor completa tu perfil en Amigro.org para continuar."
                await send_email(
                    business_unit_name=user.business_unit.name,
                    subject=subject,
                    to_email=email,
                    body=body
                )
                logger.info(f"Correo de completación de perfil enviado a {email}")
            else:
                logger.warning(f"Usuario {user_id} no tiene email registrado.")
        except Person.DoesNotExist:
            logger.error(f"No se encontró usuario con phone {user_id} para enviar correo de completación de perfil.")
        except Exception as e:
            logger.error(f"Error enviando correo de completación de perfil a {user_id}: {e}", exc_info=True)