import logging
from .models import ChatState, Pregunta, Person, FlowModel, Invitacion
from app.vacantes import match_person_with_jobs, get_available_slots, book_interview_slot, solicitud
from app.integrations.services import send_message, send_options, send_menu

# Inicializa el logger
logger = logging.getLogger(__name__)

class ChatBotHandler:
    def __init__(self):
        self.flow_model = None

    async def process_message(self, platform, user_id, text):
        """
        Procesa el mensaje del usuario y gestiona la conversación según el flujo de preguntas.
        """
        if not self.flow_model:
            self.flow_model = await FlowModel.objects.afirst()

        event = await self.get_or_create_event(user_id, platform)
        analysis = analyze_text(text)

        if not event.current_question:
            event.current_question = await self.flow_model.preguntas.afirst()  # Cambiado a 'preguntas'

        response, options = await self.process_user_response(event, text, analysis)

        await event.asave()
        await self.send_response(platform, user_id, response, options)

        return response, options

    async def get_or_create_event(self, user_id, platform):
        """
        Crea o recupera el estado del chat del usuario.
        """
        event, created = await ChatState.objects.aget_or_create(user_id=user_id)
        if created:
            event.flow_model = self.flow_model
            event.platform = platform
            await event.asave()
        else:
            if event.platform != platform:
                event.platform = platform
                await event.asave()
        return event

    async def process_user_response(self, event, user_message, analysis):
        """
        Procesa la respuesta del usuario y determina la siguiente pregunta en base a condiciones.
        """
        intents = analysis.get('intents', [])
        entities = analysis.get('entities', [])

        logger.info(f"Intenciones detectadas: {intents}")
        logger.info(f"Entidades detectadas: {entities}")

        # Menú Persistente
        if user_message.lower() in ['menu', 'inicio', 'volver', 'menu principal']:
            return await handle_persistent_menu(event)

        if 'saludo' in intents:
            response = "¡Hola! ¿En qué puedo ayudarte hoy?"
            return response, []

        elif 'despedida' in intents:
            response = "¡Hasta luego!"
            event.current_question = None
            return response, []

        elif 'buscar_vacante' in intents:
            response = "Claro, puedo ayudarte a buscar vacantes. ¿En qué área estás interesado?"
            event.current_question = await Pregunta.objects.aget(option='buscar_vacante')
            return response, []

        elif 'postular_vacante' in intents:
            response = "Para postularte a una vacante, necesito algunos datos. ¿Puedes proporcionarme tu nombre y habilidades?"
            event.current_question = await Pregunta.objects.aget(option='solicitar_datos')
            return response, []

        return await self.determine_next_question(event, user_message, analysis)

    async def determine_next_question(self, event, user_message, analysis):
        """
        Determina la siguiente pregunta en el flujo basado en la intención y entidades extraídas del mensaje.
        """
        # Si no hay una pregunta actual, asignar la primera pregunta del flujo
        if not event.current_question:
            event.current_question = await self.flow_model.preguntas.afirst()
            if not event.current_question:
                return "Lo siento, no se encontró una pregunta inicial en el flujo.", []

        # Obtener o crear un usuario asociado con el evento
        user, _ = await Person.objects.aget_or_create(number_interaction=event.user_id)

        # Verificar si la pregunta actual requiere habilidades
        if event.current_question.input_type == 'skills':
            user.skills = user_message
            await user.asave()

            recommended_jobs = match_person_with_jobs(user)
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
                event.current_question = await Pregunta.objects.aget(option='schedule_interview')
                return event.current_question.content, []
            else:
                return "Selección inválida.", []

        # Procesar agendado de entrevista
        elif event.current_question.input_type == 'schedule_interview':
            selected_job = event.context.get('selected_job')
            if not selected_job:
                return "No se encontró la vacante seleccionada.", []

            available_slots = get_available_slots(selected_job)
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
                if book_interview_slot(event.context['selected_job'], slot_index, user):
                    response = f"Has reservado tu entrevista en el horario: {selected_slot}."
                    return response, []
                else:
                    return "No se pudo reservar el slot, por favor intenta nuevamente.", []
            else:
                return "Selección inválida.", []

        # Guardar el estado del evento
        await event.asave()
        next_question = await Pregunta.objects.filter(id__gt=event.current_question.id).first()
        if next_question:
            event.current_question = next_question
            return next_question.content, []
        else:
            event.current_question = None
            return "No hay más preguntas.", []

    async def send_response(self, platform, user_id, response, options=None):
        """
        Envía la respuesta generada al usuario, con opciones si están disponibles.
        """
        await send_message(platform, user_id, response)

        if options:
            await send_options(platform, user_id, options)

    async def recap_information(self, user):
        """
        Función para hacer un recap de la información proporcionada por el usuario y permitirle hacer ajustes.
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
            f"Nivel Salarial Esperado: {user.nivel_salarial}"
        )
        return recap_message

    async def invite_known_person(self, referrer, name, apellido, phone_number):
        """
        Función para invitar a un conocido por WhatsApp y crear un pre-registro del invitado.
        """
        invitado, created = await Person.objects.aget_or_create(phone=phone_number, defaults={
            'name': name,
            'apellido_paterno': apellido
        })

        await Invitacion.objects.acreate(referrer=referrer, invitado=invitado)

        if created:
            mensaje = f"Hola {name}, has sido invitado por {referrer.name} a unirte a Amigro.org. ¡Únete a nuestra comunidad!"
            await send_message("whatsapp", phone_number, mensaje)

        return invitado
