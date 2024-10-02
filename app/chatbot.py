# /home/amigro/app/chatbot.py

import logging
import random
from .models import (
    Person,
    Worker,
    Pregunta,
    GptApi,
    Chat,
    FlowModel,
    ChatState,
    Condicion,
    TelegramAPI,
    WhatsAppAPI,
    MessengerAPI,
)
from app.integrations.services import send_options
from app.integrations.telegram import send_telegram_message
from app.integrations.messenger import send_messenger_message
from app.integrations.whatsapp import send_whatsapp_message
from .gpt import gpt_message
from celery import shared_task
import asyncio
from .nlp_utils import analyze_text  # Importamos la función mejorada
from .vacantes import (
    match_person_with_jobs,
    get_available_slots,
    book_interview_slot,
)
from .google_calendar import create_calendar_event

# Inicializa el logger
logging.basicConfig(filename="logger.log", level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatBotHandler:
    def __init__(self):
        self.gpt_api = GptApi.objects.first()
        self.flow_model = None

    async def process_message(self, platform, user_id, text):
        """
        Procesa el mensaje del usuario y gestiona la conversación según el flujo de preguntas.
        """
        # Asegurarse de que el flow_model está inicializado
        if not self.flow_model:
            self.flow_model = await FlowModel.objects.afirst()

        event = await self.get_or_create_event(user_id, platform)
        analysis = analyze_text(text)  # Utilizamos la función mejorada

        if not event.current_question:
            event.current_question = await self.flow_model.pregunta_set.afirst()

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
            # Actualizar la plataforma si es diferente
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

        # Manejo de intenciones específicas
        if 'saludo' in intents:
            response = "¡Hola! ¿En qué puedo ayudarte hoy?"
            return response, []

        elif 'despedida' in intents:
            response = "¡Hasta luego! Si necesitas algo más, no dudes en contactarme."
            event.current_question = None  # Finalizar la conversación
            return response, []

        elif 'buscar_vacante' in intents:
            response = "Claro, puedo ayudarte a buscar vacantes. ¿En qué área estás interesado?"
            event.current_question = await Pregunta.objects.aget(option='solicitar_skills')
            return response, []

        elif 'postular_vacante' in intents:
            response = "Para postularte a una vacante, necesito algunos datos. ¿Puedes proporcionarme tu nombre y habilidades?"
            event.current_question = await Pregunta.objects.aget(option='solicitar_datos')
            return response, []

        else:
            # Si no se detecta ninguna intención conocida, continuar con el flujo normal
            return await self.determine_next_question(event, user_message, analysis)

    async def determine_next_question(self, event, user_message, analysis):
        """
        Determina la siguiente pregunta en el flujo basado en la intención y entidades extraídas del mensaje.
        """
        # Asegurarse de que event.current_question está definido
        if not event.current_question:
            event.current_question = await self.flow_model.pregunta_set.afirst()

        # Obtener el usuario
        user, _ = await Person.objects.aget_or_create(number_interaction=event.user_id)

        # Manejo de diferentes tipos de input
        if event.current_question.input_type == 'skills':
            # Guardar las habilidades del usuario
            user.skills = user_message
            await user.asave()

            # Obtener vacantes recomendadas
            recommended_jobs = match_person_with_jobs(user)

            if recommended_jobs:
                response = "Aquí tienes algunas vacantes que podrían interesarte:\n"
                for idx, (job, score) in enumerate(recommended_jobs[:5]):  # Mostrar top 5
                    response += f"{idx + 1}. {job.name} en {job.company}\n"
                response += "Por favor, ingresa el número de la vacante que te interesa para agendar una entrevista."
                event.context = {'recommended_jobs': recommended_jobs}
                # Mantener la misma pregunta o avanzar según tu lógica
                return response, []
            else:
                response = "Lo siento, no encontré vacantes que coincidan con tu perfil en este momento."
                event.current_question = None  # Finalizar conversación o pasar a otra pregunta
                return response, []

        elif event.current_question.input_type == 'select_job':
            try:
                job_index = int(user_message) - 1
            except ValueError:
                return "Por favor, ingresa un número válido.", []

            recommended_jobs = event.context.get('recommended_jobs')
            if recommended_jobs and 0 <= job_index < len(recommended_jobs):
                selected_job, _ = recommended_jobs[job_index]
                event.context['selected_job'] = selected_job
                event.current_question = await Pregunta.objects.aget(option='schedule_interview')
                return event.current_question.content, self.get_options(event.current_question)
            else:
                return "Selección inválida. Por favor, ingresa el número de la vacante que te interesa.", []

        elif event.current_question.input_type == 'schedule_interview':
            if user_message.lower() in ['sí', 'si']:
                selected_job = event.context.get('selected_job')
                available_slots = get_available_slots(selected_job)
                if available_slots:
                    response = "Estos son los horarios disponibles para la entrevista:\n"
                    for idx, slot in enumerate(available_slots):
                        response += f"{idx + 1}. {slot['date']} a las {slot['time']}\n"
                    response += "Por favor, selecciona el número del horario que prefieras."
                    event.context['available_slots'] = available_slots
                    event.current_question = await Pregunta.objects.aget(option='select_slot')
                    return response, []
                else:
                    event.current_question = None  # No hay más preguntas
                    return "Lo siento, no hay horarios disponibles para esta vacante en este momento.", []
            else:
                event.current_question = None  # Finalizar conversación
                return "Entiendo. Si necesitas algo más, no dudes en pedírmelo.", []

        elif event.current_question.input_type == 'select_slot':
            try:
                slot_index = int(user_message) - 1
            except ValueError:
                return "Por favor, ingresa un número válido.", []

            available_slots = event.context.get('available_slots')
            selected_job = event.context.get('selected_job')

            if available_slots and 0 <= slot_index < len(available_slots):
                success = book_interview_slot(selected_job, slot_index, user)
                if success:
                    slot = available_slots[slot_index]
                    # Crear evento en Google Calendar
                    event_link = create_calendar_event(slot, user, selected_job)
                    event.current_question = None  # Finalizar conversación
                    return (
                        f"¡Listo! Tu entrevista ha sido programada para el {slot['date']} a las {slot['time']}. "
                        f"Puedes ver los detalles aquí: {event_link}",
                        [],
                    )
                else:
                    return "Lo siento, ese horario ya no está disponible. Por favor, elige otro.", []
            else:
                return "Selección inválida. Por favor, elige un número de la lista.", []

        # Si no se cumplen las condiciones anteriores, avanzar al siguiente nodo en el flujo
        # Primero, verificar si hay subpreguntas sin responder
        if event.current_question.sub_pregunta.exists():
            # Obtener la siguiente subpregunta que no haya sido respondida
            last_sub_pregunta_id = event.context.get('last_sub_pregunta_id')
            sub_pregunta = event.current_question.sub_pregunta.filter(
                id__gt=last_sub_pregunta_id or 0
            ).first()
            if sub_pregunta:
                event.context['last_sub_pregunta_id'] = sub_pregunta.id
                await event.asave()
                event.current_question = sub_pregunta
                return sub_pregunta.content, self.get_options(sub_pregunta)

        # Si la pregunta actual no requiere respuesta, avanzar automáticamente
        if not event.current_question.requires_response:
            # Obtener la siguiente pregunta en el flujo
            next_question = self.get_next_question_in_flow(event.current_question, user_message)
            if next_question:
                event.current_question = next_question
                return next_question.content, self.get_options(next_question)
            else:
                event.current_question = None  # No hay más preguntas
                return None, []

        # Manejo normal de la conversación
        next_question = self.get_next_question_in_flow(event.current_question, user_message)
        if next_question:
            event.current_question = next_question
            return next_question.content, self.get_options(next_question)
        else:
            event.current_question = None
            return None, []

    def get_next_question_in_flow(self, current_question, user_message):
        """
        Obtiene la siguiente pregunta en el flujo de conversación.
        """
        next_question_id = current_question.decision.get(user_message.lower())
        if next_question_id:
            return Pregunta.objects.get(id=next_question_id)
        else:
            # Si no hay una decisión basada en la respuesta, obtener la siguiente pregunta secuencialmente
            next_question = Pregunta.objects.filter(id__gt=current_question.id).order_by('id').first()
            return next_question

    def get_options(self, question):
        """
        Retorna las opciones disponibles para una pregunta.
        """
        return question.options.split(',') if question.options else []

    async def generate_gpt_response(self, message):
        """
        Genera una respuesta utilizando la API de GPT.
        """
        try:
            response = gpt_message(
                api_token=self.gpt_api.api_token,
                text=message,
                model=self.gpt_api.model,
            )
            return response['choices'][0]['message']['content'], []
        except Exception as e:
            logger.error(f"Error llamando a GPT: {e}", exc_info=True)
            return "Lo siento, ocurrió un error al procesar tu solicitud.", []

    async def send_response(self, platform, user_id, response, options):
        """
        Envía la respuesta al usuario en la plataforma correspondiente.
        """
        if platform == 'telegram':
            telegram_api = TelegramAPI.objects.first()
            if telegram_api:
                await send_telegram_message(
                    user_id,
                    response,
                    telegram_api.api_key
                )
            else:
                logger.error("No se encontró configuración de API de Telegram")
        elif platform == 'whatsapp':
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                await send_whatsapp_message(
                    user_id,
                    response,
                    whatsapp_api.api_token,
                    whatsapp_api.phoneID,
                    whatsapp_api.v_api
                )
            else:
                logger.error("No se encontró configuración de API de WhatsApp")
        elif platform == 'messenger':
            messenger_api = MessengerAPI.objects.first()
            if messenger_api:
                await send_messenger_message(
                    user_id,
                    response,
                    messenger_api.page_access_token
                )
            else:
                logger.error("No se encontró configuración de API de Messenger")
        else:
            logger.error(f"Plataforma desconocida: {platform}")

    # Función para manejar preguntas del chatbot (si es necesaria)
    def handle_user_message(self, platform, user_id, message):
        # Lógica para determinar si se envían opciones
        if some_condition:  # Aquí iría la lógica para verificar cuándo enviar opciones
            send_options(platform, user_id, "Por favor selecciona una opción:")
        else:
            # Lógica normal de respuesta del chatbot
            pass
