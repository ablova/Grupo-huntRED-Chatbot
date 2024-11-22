# /home/amigro/app/chatbot.py
import logging
import asyncio
from typing import Optional, Tuple, List, Dict, Any
from asgiref.sync import sync_to_async
from app.models import (
    ChatState,
    Pregunta,
    Person,
    FlowModel,
    Invitacion,
    MetaAPI,
    WhatsAppAPI,
    TelegramAPI,
    MessengerAPI,
    InstagramAPI,
    Interview
)
from app.vacantes import VacanteManager
from app.integrations.services import (
    send_message,
    send_options,
    send_menu,
    render_dynamic_content,
    send_logo,
    send_email
)

from app.nlp_utils import analyze_text

# Inicializa el logger
logger = logging.getLogger(__name__)

class ChatBotHandler:
    async def process_message(self, platform, user_id, text, business_unit):
        """
        Procesa el mensaje del usuario y gestiona la conversación.

        :param platform: Plataforma de mensajería (e.g., 'whatsapp').
        :param user_id: ID del usuario.
        :param text: Mensaje de texto recibido.
        :param business_unit: Unidad de negocio asociada.
        :return: Respuesta generada y opciones.
        """
        logger.info(
            f"Procesando mensaje para {user_id} en {platform} para la unidad de negocio {business_unit}"
        )

        # Obtener configuración dinámica para la plataforma utilizando MetaAPI
        meta_api = await MetaAPI.objects.filter(business_unit=business_unit).afirst()
        if not meta_api:
            logger.error(f"No se encontró configuración de MetaAPI para {platform} y unidad de negocio {business_unit}.")
            return

        # Instanciar la API según la plataforma
        if platform == 'whatsapp':
            whatsapp_api = await WhatsAppAPI.objects.filter(business_unit=business_unit).afirst()
            if not whatsapp_api:
                logger.error(f"No se encontró configuración de WhatsAppAPI para la unidad de negocio {business_unit}.")
                return
            phone_id = whatsapp_api.phoneID
            api_instance, _ = await WhatsAppAPI.objects.aget_or_create(
                business_unit=business_unit, phoneID=phone_id
            )
        elif platform == 'telegram':
            api_instance, _ = await TelegramAPI.objects.aget_or_create(
                business_unit=business_unit
            )
        elif platform == 'messenger':
            api_instance, _ = await MessengerAPI.objects.aget_or_create(
                business_unit=business_unit
            )
        elif platform == 'instagram':
            api_instance, _ = await InstagramAPI.objects.aget_or_create(
                business_unit=business_unit
            )
        else:
            raise ValueError(f"Plataforma no soportada: {platform}")

        # Asignar el flujo asociado a la instancia de API
        flow_model = await sync_to_async(lambda: api_instance.associated_flow)()

        # Obtener o crear el estado de chat (evento) para el usuario
        event = await self.get_or_create_event(user_id, platform, flow_model)

        # Realizar el análisis de intención en el mensaje
        analysis = analyze_text(text)
        intents = analysis.get("intents", [])
        logger.info(f"Análisis del mensaje completado para el texto '{text}': {analysis}")

        # Procesar intenciones conocidas
        if "menu" in intents:
            logger.info(f"El usuario {user_id} solicitó el menú principal.")
            await send_menu(platform, user_id)
            return

        if "reiniciar" in intents:
            logger.info(f"El usuario {user_id} solicitó reiniciar la conversación.")
            await reset_chat_state(user_id)
            await send_message(platform, user_id, "Se ha reiniciado tu conversación. ¿Cómo puedo ayudarte?")
            return

        if "recapitulación" in intents or "recap" in intents:
            logger.info(f"El usuario {user_id} solicitó recapitulación.")
            recap = await self.recap_information(event.user_id)
            if recap:
                await self.send_response(platform, user_id, recap)
            return

        # Obtener o crear el usuario y preparar el contexto
        user, _ = await Person.objects.aget_or_create(number_interaction=event.user_id)
        context = {
            'name': user.name or '',
            'apellido_paterno': user.apellido_paterno or '',
            'apellido_materno': user.apellido_materno or '',
            'sexo': user.sexo or '',
            'email': user.email or '',
            'phone': user.phone or '',
            'nacionalidad': user.nationality or '',
            'fecha_nacimiento': user.fecha_nacimiento or '',
        }

        # Verificar si el perfil del usuario está completo
        profile_check = await self.verify_user_profile(user)
        if profile_check:
            return await self.send_response(platform, user_id, profile_check)

        # Confirmar la información antes de proceder con vacantes
        recap = await self.recap_information(user)
        if recap:
            return await self.send_response(platform, user_id, recap)

        # Obtener la pregunta actual y continuar el flujo
        current_question = event.current_question

        if not current_question:
            # Si no hay pregunta actual, asignar la primera pregunta del flujo
            event.current_question = await flow_model.preguntas.afirst()
            logger.info(f"Conversación iniciada con la primera pregunta: {event.current_question}")

        # Procesar el mensaje del usuario y generar respuesta y opciones
        response, options = await self.process_user_message(event, text, analysis, context)
        logger.info(f"Respuesta generada: {response}, con opciones: {options}")

        # Guardar el estado actualizado del chat
        await event.asave()
        logger.info(f"Estado del chat guardado para el usuario {user_id}")

        # Enviar la respuesta al usuario
        await self.send_response(platform, user_id, response, options)

        return response, options

    async def get_or_create_event(self, user_id, platform, flow_model):
        """
        Obtiene o crea un estado de chat (evento) para el usuario.

        :param user_id: ID del usuario.
        :param platform: Plataforma de mensajería.
        :param flow_model: Modelo de flujo asociado.
        :return: Instancia de ChatState.
        """
        event, created = await ChatState.objects.aget_or_create(user_id=user_id)
        if created:
            event.flow_model = flow_model
            event.platform = platform
            await event.asave()
        else:
            if event.platform != platform:
                event.platform = platform
                await event.asave()
        return event

    async def verify_user_profile(self, user):
        """
        Verifica si el perfil del usuario tiene toda la información necesaria para continuar.

        :param user: Instancia de Person.
        :return: Mensaje de solicitud de datos faltantes o None si está completo.
        """
        required_fields = ['name', 'apellido_paterno', 'skills', 'ubicacion', 'email']
        missing_fields = [field for field in required_fields if not getattr(user, field)]
        if missing_fields:
            fields_str = ", ".join(missing_fields)
            return f"Para continuar, completa estos datos: {fields_str}"
        return None  # Todo está completo

    async def recap_information(self, user):
        """
        Proporciona un resumen de la información del usuario y le permite hacer ajustes.

        :param user: Instancia de Person.
        :return: Mensaje de recapitulación.
        """
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
        """
        Permite que el usuario corrija su información tras la recapitulación.

        :param event: Instancia de ChatState.
        :param user_response: Respuesta del usuario.
        """
        correction_message = "Por favor, indica qué dato deseas corregir (e.g., 'nombre', 'email')."
        await self.send_response(event.platform, event.user_id, correction_message)
        event.awaiting_correction = True
        await event.asave()

    async def update_user_information(self, user, user_input):
        """
        Actualiza la información del usuario basada en la entrada de corrección.

        :param user: Instancia de Person.
        :param user_input: Entrada del usuario para actualizar datos.
        """
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
                await user.asave()
            else:
                logger.info(f"Campo no encontrado para actualizar: {user_input}")
        except ValueError:
            logger.warning(f"Entrada de usuario inválida para actualización: {user_input}")

    async def send_response(self, platform, user_id, response, options=None):
        """
        Envía la respuesta generada al usuario, con opciones si están disponibles.

        :param platform: Plataforma de mensajería.
        :param user_id: ID del usuario.
        :param response: Mensaje de respuesta.
        :param options: Opciones adicionales.
        """
        await send_message(platform, user_id, response)
        if options:
            await send_options(platform, user_id, response, options)
        return response, options or []

    async def handle_standard_flow(self, event, user_message, analysis):
        """
        Continúa el flujo estándar del chatbot cuando no hay botones o condiciones específicas.
        """
        # Si no hay una pregunta actual, asignar la primera pregunta del flujo
        if not event.current_question:
            event.current_question = await sync_to_async(self.flow_model.preguntas.first)()
            if not event.current_question:
                return "Lo siento, no se encontró una pregunta inicial en el flujo.", []

        # Obtener o crear un usuario asociado con el evento
        user, _ = await Person.objects.aget_or_create(number_interaction=event.user_id)
        
        # Inicializar VacanteManager
        vacante_manager = VacanteManager(event.context)  # Pasa el contexto del evento, si es necesario

        # Verificar si la pregunta actual requiere habilidades
        if event.current_question.input_type == 'skills':
            user.skills = user_message
            await sync_to_async(user.save)()

            recommended_jobs = await sync_to_async(vacante_manager.match_person_with_jobs)(user)
            if recommended_jobs:
                response = "Aquí tienes algunas vacantes que podrían interesarte:\n"
                for idx, (job, score) in enumerate(recommended_jobs[:5]):
                    response += f"{idx + 1}. {job['title']} en {job['company']}\n"
                response += "Por favor, ingresa el número de la vacante que te interesa."
                event.context = {'recommended_jobs': recommended_jobs}
                return response, []
            else:
                response = "Lo siento, no encontré vacantes que coincidan con tu perfil."
                return response, []

        # Manejo de selección de vacante
        elif event.current_question.input_type == 'select_job':
            try:
                job_index = int(user_message) - 1
            except ValueError:
                return "Por favor, ingresa un número válido.", []

            recommended_jobs = event.context.get('recommended_jobs')
            if recommended_jobs and 0 <= job_index < len(recommended_jobs):
                selected_job = recommended_jobs[job_index]
                event.context['selected_job'] = selected_job
                event.current_question = await sync_to_async(Pregunta.objects.get)(option='schedule_interview')
                return event.current_question.content, []
            else:
                return "Selección inválida.", []

        # Procesar agendado de entrevista
        elif event.current_question.input_type == 'schedule_interview':
            selected_job = event.context.get('selected_job')
            if not selected_job:
                return "No se encontró la vacante seleccionada.", []

            available_slots = await sync_to_async(vacante_manager.get_available_slots)(selected_job)
            if available_slots:
                response = "Estos son los horarios disponibles para la entrevista:\n"
                for idx, slot in enumerate(available_slots):
                    response += f"{idx + 1}. {slot}\n"
                response += "Por favor, selecciona el número del horario que prefieras."
                event.context['available_slots'] = available_slots
                return response, []
            else:
                return "No hay horarios disponibles.", []

        # Reserva de entrevista
        elif event.current_question.input_type == 'confirm_interview_slot':
            try:
                slot_index = int(user_message) - 1
            except ValueError:
                return "Por favor, ingresa un número válido.", []

            available_slots = event.context.get('available_slots')
            if available_slots and 0 <= slot_index < len(available_slots):
                selected_slot = available_slots[slot_index]
                if await sync_to_async(vacante_manager.book_interview_slot)(selected_job, slot_index, user):
                    response = f"Has reservado tu entrevista en el horario: {selected_slot}."
                    return response, []
                else:
                    return "No se pudo reservar el slot, por favor intenta nuevamente.", []
            else:
                return "Selección inválida. Por favor, intenta nuevamente.", []

        # Si no hay más preguntas, finalizar el flujo
        await sync_to_async(event.save)()
        next_question = await sync_to_async(Pregunta.objects.filter(id__gt=event.current_question.id).first)()
        if next_question:
            event.current_question = next_question
            return next_question.content, []
        else:
            event.current_question = None
            response = "No hay más preguntas. Aquí tienes el menú principal:"
            await send_menu(event.platform, event.user_id)
            return response, []

    async def handle_persistent_menu(self, event):
        """
        Envía el menú persistente en cualquier momento de la conversación.
        """
        user = await sync_to_async(Person.objects.get)(number_interaction=event.user_id)
        context = {
            'name': user.name or ''
        }
        response = f"Aquí tienes el menú principal, {context['name']}:"
        await send_menu(event.platform, event.user_id)
        return response, []

    async def invite_known_person(self, referrer, name, apellido, phone_number):
        """
        Invita a una persona conocida vía WhatsApp y crea un pre-registro.

        :param referrer: Usuario que refiere.
        :param name: Nombre del invitado.
        :param apellido: Apellido del invitado.
        :param phone_number: Número de teléfono del invitado.
        :return: Instancia de Person creada o existente.
        """
        invitado, created = await Person.objects.aget_or_create(
            phone=phone_number,
            defaults={'name': name, 'apellido_paterno': apellido},
        )

        await Invitacion.objects.acreate(referrer=referrer, invitado=invitado)

        if created:
            mensaje = (
                f"Hola {name}, has sido invitado por {referrer.name} a unirte a Amigro.org. "
                "¡Encuentra empleo en México de manera segura, gratuita e incluso podemos asesorarte en temas migrantes!"
            )
            await send_message("whatsapp", phone_number, mensaje)

        return invitado

    async def determine_next_question(
        self, event, user_message: str, analysis: dict, context: dict
    ) -> Tuple[Optional[str], List]:
        """
        Determina la siguiente pregunta en el flujo basado en la respuesta del usuario y las entidades extraídas.

        :param event: Instancia de ChatState.
        :param user_message: Mensaje del usuario.
        :param analysis: Análisis de NLP del mensaje.
        :param context: Contexto de la conversación.
        :return: Siguiente mensaje y opciones.
        """
        current_question = event.current_question
        logger.info(f"Procesando la pregunta actual: {current_question}")

        # Manejar diferentes tipos de preguntas y acciones
        if current_question.action_type:
            response, options = await self._handle_action_type(
                event, current_question, context
            )
            return response, options

        if current_question.botones_pregunta.exists():
            response, options = await self._handle_button_response(
                event, current_question, user_message, context
            )
            return response, options

        # Flujo estándar: avanzar a la siguiente pregunta
        next_question = current_question.next_si
        if next_question:
            event.current_question = next_question
            await event.asave()
            response = render_dynamic_content(next_question.content, context)
            return response, []
        else:
            return "No hay más preguntas en este flujo.", []

    async def verify_user_profile(self, user):
        """
        Verifica si el perfil del usuario tiene toda la información necesaria para continuar.
        """
        required_fields = ['name', 'apellido_paterno', 'skills', 'ubicacion', 'email']
        missing_fields = [field for field in required_fields if not getattr(user, field)]
        if missing_fields:
            fields_str = ", ".join(missing_fields)
            return f"Para continuar, completa estos datos: {fields_str}"
        return None  # Todo está completo

    async def process_user_message(self, event, text, analysis, context):
        """
        Procesa el mensaje del usuario y determina la respuesta.

        :param event: Instancia de ChatState.
        :param text: Mensaje del usuario.
        :param analysis: Resultado del análisis NLP.
        :param context: Contexto de la conversación.
        :return: Respuesta y opciones.
        """
        # Aquí se implementa la lógica para procesar el mensaje del usuario.
        # Este es un ejemplo simplificado.
        current_question = event.current_question

        if not current_question:
            return "No hay una pregunta actual en el flujo.", []

        # Determinar la siguiente pregunta o acción
        response, options = await self.determine_next_question(
            event, text, analysis, context
        )
        return response, options

    async def _handle_action_type(
        self, event, current_question, context
    ) -> Tuple[Optional[str], List]:
        """
        Maneja acciones específicas definidas en la pregunta actual.

        :param event: Instancia de ChatState.
        :param current_question: Pregunta actual.
        :param context: Contexto de la conversación.
        :return: Respuesta y opciones.
        """
        action_handlers = {
            'enviar_whatsapp_plantilla': self._handle_whatsapp_template,
            'enviar_url': self._handle_url,
            'enviar_imagen': self._handle_image,
            'enviar_logo': self._handle_logo,
            'decision_si_no': self._handle_yes_no_decision,
        }
        handler = action_handlers.get(current_question.action_type)
        if handler:
            return await handler(event, current_question, context)
        else:
            return "Error: Acción no soportada.", []

    async def _get_next_main_question(self, event, current_question):
        return await sync_to_async(lambda: current_question.next_si)()

    async def _handle_whatsapp_template(
        self, event, current_question, context
    ) -> Tuple[str, List]:
        await send_message(
            event.platform, event.user_id, f"Enviando template: {current_question.option}"
        )
        return await self._advance_to_next_question(event, current_question, context)

    async def _handle_url(
        self, event, current_question, context
    ) -> Tuple[str, List]:
        await send_message(event.platform, event.user_id, "Aquí tienes el enlace:")
        await send_message(event.platform, event.user_id, current_question.content)
        return await self._advance_to_next_question(event, current_question, context)

    async def _handle_image(
        self, event, current_question, context
    ) -> Tuple[str, List]:
        await send_message(event.platform, event.user_id, "Aquí tienes la imagen:")
        await send_image(event.platform, event.user_id, current_question.content)
        return await self._advance_to_next_question(event, current_question, context)

    async def _handle_logo(
        self, event, current_question, context
    ) -> Tuple[str, List]:
        await send_logo(event.platform, event.user_id)
        return await self._advance_to_next_question(event, current_question, context)

    async def _handle_yes_no_decision(
        self, event, current_question, context
    ) -> Tuple[None, List]:
        from app.integrations.whatsapp import send_whatsapp_decision_buttons

        decision_buttons = [{"title": "Sí"}, {"title": "No"}]
        whatsapp_api = await WhatsAppAPI.objects.afirst()
        await send_whatsapp_decision_buttons(
            event.user_id,
            current_question.content,
            decision_buttons,
            whatsapp_api.api_token,
            whatsapp_api.phoneID,
            whatsapp_api.v_api,
        )
        return None, []

    async def _handle_no_response_required(self, event, current_question, context) -> Tuple[Optional[str], List]:
        await self.send_response(event.platform, event.user_id, current_question.content)
        await asyncio.sleep(3)
        next_question = await sync_to_async(lambda: current_question.next_si)()
        return render_dynamic_content(next_question.content, context), [] if next_question else ("No hay más preguntas en este flujo.", [])

    async def _handle_multi_select(self, event, current_question, user_message: str, context) -> Tuple[Optional[str], List]:
        selected_options = [option.strip().lower() for option in user_message.split(',')]
        valid_options = []
        for option in selected_options:
            selected_button = await sync_to_async(
                lambda: current_question.botones_pregunta.filter(name__iexact=option).first()
            )()
            if selected_button:
                valid_options.append(selected_button.name)
            else:
                return "Opción no válida. Selecciona una opción válida.", []

        return await self._advance_to_next_question(event, current_question, context)

    async def _handle_button_response(
        self, event, current_question, user_message: str, context
    ) -> Tuple[Optional[str], List]:
        user_response = user_message.lower().strip()

        if user_response in ['sí', 'si', 'yes']:
            next_question = current_question.next_si
        elif user_response == 'no':
            next_question = current_question.next_no
        else:
            return "Por favor responde con 'Sí' o 'No'.", []

        if next_question:
            event.current_question = next_question
            await event.asave()
            response = render_dynamic_content(next_question.content, context)
            return response, []
        else:
            return "No hay más preguntas en este flujo.", []

    async def _advance_to_next_question(
        self, event, current_question, context
    ) -> Tuple[str, List]:
        next_question = current_question.next_si
        if next_question:
            event.current_question = next_question
            await event.asave()
            response = render_dynamic_content(next_question.content, context)
            return response, []
        else:
            return "No hay más preguntas en este flujo.", []

    async def handle_new_job_position(self, event):
        """
        Procesa la creación de una nueva posición laboral y envía la confirmación al usuario.

        :param event: Instancia de ChatState.
        """
        job_data = event.data  # Aquí recibimos los datos de la vacante recogidos en el flujo

        # Llamar a la función para procesar la vacante y crearla en WordPress
        result = await procesar_vacante(job_data)

        # Verificar el resultado y notificar al usuario
        if result["status"] == "success":
            await send_message(
                event.platform,
                event.user_id,
                "La vacante ha sido creada exitosamente en nuestro sistema.",
            )
        else:
            await send_message(
                event.platform,
                event.user_id,
                "Hubo un problema al crear la vacante. Por favor, inténtalo de nuevo.",
            )
            
    async def request_candidate_location(self, event, interview):
        """
        Solicita al candidato que comparta su ubicación antes de la entrevista, solo si es presencial.
        """
        if interview.interview_type != 'presencial':
            logger.info(f"No se solicita ubicación porque la entrevista es virtual para ID: {interview.id}")
            return

        message = (
            "Hola, para confirmar tu asistencia a la entrevista presencial, por favor comparte tu ubicación actual. "
            "Esto nos ayudará a verificar que estás en el lugar acordado."
        )
        await send_message(event.platform, event.user_id, message)

    async def handle_candidate_confirmation(self, platform, user_id, user_message):
        """
        Procesa la confirmación del candidato y guarda la información de ubicación si es presencial.
        Notifica al entrevistador sobre la confirmación del candidato.
        """
        person = await sync_to_async(Person.objects.get)(number_interaction=user_id)
        interview = await sync_to_async(Interview.objects.filter)(person=person).first()

        if not interview or interview.candidate_confirmed:
            return

        if user_message.lower() in ['sí', 'si', 'yes']:
            interview.candidate_confirmed = True
            message = "¡Gracias por confirmar tu asistencia!"

            # Si es presencial, solicitar ubicación
            if interview.interview_type == 'presencial' and not interview.candidate_latitude:
                message += "\nPor favor, comparte tu ubicación actual para validar que estás en el lugar correcto."
            else:
                message += "\nTe deseamos mucho éxito en tu entrevista."

            await send_message(platform, user_id, message)
            await sync_to_async(interview.save)()

            # Notificar al entrevistador
            await self.notify_interviewer(interview)
        else:
            await send_message(platform, user_id, "Por favor, confirma tu asistencia respondiendo con 'Sí'.")

    async def notify_interviewer(self, interview):
        """
        Notifica al entrevistador que el candidato ha confirmado su asistencia.
        """
        job = interview.job
        interviewer_phone = job.whatsapp or interview.person.phone  # WhatsApp del entrevistador
        interviewer_email = job.email or interview.person.email     # Email del entrevistador

        message = (
            f"El candidato {interview.person.name} ha confirmado su asistencia a la entrevista para la posición {job.title}.\n"
            f"Fecha de la entrevista: {interview.interview_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Tipo de entrevista: {'Presencial' if interview.interview_type == 'presencial' else 'Virtual'}"
        )
        try:
            # Enviar notificación por WhatsApp
            if interviewer_phone:
                await send_message('whatsapp', interviewer_phone, message)
                logger.info(f"Notificación enviada al entrevistador vía WhatsApp: {interviewer_phone}")

            # Enviar notificación por correo electrónico
            if interviewer_email:
                subject = f"Confirmación de asistencia para {job.title}"
                send_email(
                    business_unit_name=job.business_unit.name,
                    subject=subject,
                    recipient=interviewer_email,
                    body=message
                )
                logger.info(f"Notificación enviada al entrevistador vía email: {interviewer_email}")

        except Exception as e:
            logger.error(f"Error enviando notificación al entrevistador: {e}")