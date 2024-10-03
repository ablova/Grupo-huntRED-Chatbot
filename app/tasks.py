#/home/amigro/app/tasks.py

import requests
from chatbot_django.celery import shared_task
from app.integrations.services import WhatsAppService, MessengerService, TelegramService, send_options, WhatsAppAPI, MessengerAPI, TelegramAPI, InstagramAPI
from app.models import Person, Worker, WhatsAppAPI
from app.vacantes import match_person_with_jobs
import logging

# Inicializa el logger
logger = logging.getLogger('celery_tasks')

# Tarea para enviar mensajes de WhatsApp de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_whatsapp_message(self, recipient, message):  # Añadir 'self' como primer argumento
    try:
        whatsapp_api = WhatsAppAPI.objects.first()
        if whatsapp_api:
            api_token = whatsapp_api.api_token
            phone_id = whatsapp_api.phoneID
            version_api = whatsapp_api.v_api
            whatsapp_service = WhatsAppService(api_token=api_token, phone_id=phone_id, version_api=version_api)
            whatsapp_service.send_message(recipient, message)
            logger.info(f"Mensaje de WhatsApp enviado correctamente a {recipient}")
        else:
            logger.error("No se encontró configuración de API de WhatsApp.")
    except Exception as e:
        logger.error(f"Error enviando mensaje a WhatsApp: {e}")
        self.retry(exc=e, countdown=60)  # Reintenta después de 60 segundos

# Tarea para enviar botones de WhatsApp de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_whatsapp_options(self, recipient, message, options, api_token, phone_id, version_api):
    try:
        send_options('whatsapp', recipient, message)
        logger.info(f"Opciones enviadas a WhatsApp {recipient}")
    except Exception as e:
        logger.error(f"Error enviando opciones a WhatsApp: {e}")
        self.retry(exc=e, countdown=60)

# Tarea para enviar mensajes de Telegram de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_telegram_message(self, chat_id, message, bot_token):
    try:
        telegram_service = TelegramService(bot_token=bot_token)
        telegram_service.send_message(chat_id, message)
        logger.info(f"Mensaje de Telegram enviado correctamente a {chat_id}")
    except Exception as e:
        logger.error(f"Error enviando mensaje a Telegram: {e}")
        self.retry(exc=e, countdown=60)

# Tarea para enviar botones de Telegram de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_telegram_options(self, chat_id, message, options, bot_token):
    try:
        send_options('telegram', chat_id, message)
        logger.info(f"Opciones enviadas a Telegram {chat_id}")
    except Exception as e:
        logger.error(f"Error enviando opciones a Telegram: {e}")
        self.retry(exc=e, countdown=60)

# Tarea para enviar mensajes de Messenger de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_messenger_message(self, recipient_id, message, access_token):
    try:
        messenger_service = MessengerService(access_token=access_token)
        messenger_service.send_message(recipient_id, message)
        logger.info(f"Mensaje de Messenger enviado correctamente a {recipient_id}")
    except Exception as e:
        logger.error(f"Error enviando mensaje a Messenger: {e}")
        self.retry(exc=e, countdown=60)

# Actualizar recomendaciones de trabajo para una persona
@shared_task
def update_job_recommendations():
    try:
        for person in Person.objects.filter(int_work=True):
            matching_jobs = match_person_with_jobs(person)
            logger.info(f"Recomendaciones de trabajo actualizadas para {person.name}")
    except Exception as e:
        logger.error(f"Error actualizando recomendaciones de trabajo: {e}")

# Limpiar estados de chat antiguos
@shared_task
def clean_old_chat_states():
    try:
        # Agregar lógica para eliminar estados antiguos
        logger.info("Estados de chat antiguos limpiados correctamente.")
    except Exception as e:
        logger.error(f"Error limpiando estados de chat antiguos: {e}")

