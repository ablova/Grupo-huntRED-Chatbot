# /home/amigro/app/tasks.py

import os
import django
from celery import Celery
import requests
from celery import shared_task
from app.integrations.services import send_options, send_message, WhatsAppAPI, MessengerAPI, TelegramAPI, InstagramAPI
from app.models import Person, Worker, WhatsAppAPI
from app.vacantes import match_person_with_jobs
import logging
#Esto es para la aplicación de Milkyleak, independiente del chatbot de amigro, solo se utiliza el servidor.


# Inicializa el logger
logger = logging.getLogger('celery_tasks')

# Tarea para enviar mensajes de WhatsApp de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_whatsapp_message(self, recipient, message):
    try:
        whatsapp_api = WhatsAppAPI.objects.first()
        if whatsapp_api:
            send_message('whatsapp', recipient, message)
            logger.info(f"Mensaje de WhatsApp enviado correctamente a {recipient}")
        else:
            logger.error("No se encontró configuración de API de WhatsApp.")
    except Exception as e:
        logger.error(f"Error enviando mensaje a WhatsApp: {e}")
        self.retry(exc=e, countdown=60)  # Reintenta después de 60 segundos

# Tarea para enviar botones de WhatsApp de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_whatsapp_options(self, recipient, message, options):
    try:
        send_options('whatsapp', recipient, message, options)
        logger.info(f"Opciones enviadas a WhatsApp {recipient}")
    except Exception as e:
        logger.error(f"Error enviando opciones a WhatsApp: {e}")
        self.retry(exc=e, countdown=60)

# Tarea para enviar mensajes de Telegram de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_telegram_message(self, chat_id, message):
    try:
        send_message('telegram', chat_id, message)
        logger.info(f"Mensaje de Telegram enviado correctamente a {chat_id}")
    except Exception as e:
        logger.error(f"Error enviando mensaje a Telegram: {e}")
        self.retry(exc=e, countdown=60)

# Tarea para enviar botones de Telegram de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_telegram_options(self, chat_id, message, options):
    try:
        send_options('telegram', chat_id, message, options)
        logger.info(f"Opciones enviadas a Telegram {chat_id}")
    except Exception as e:
        logger.error(f"Error enviando opciones a Telegram: {e}")
        self.retry(exc=e, countdown=60)

# Tarea para enviar mensajes de Messenger de manera asíncrona
@shared_task(bind=True, max_retries=3)
def send_messenger_message(self, recipient_id, message):
    try:
        send_message('messenger', recipient_id, message)
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


#________________________________________________________________________________________________
#Esto es para la aplicación de Milkyleak, independiente del chatbot de amigro, solo se utiliza el servidor.
from celery import shared_task
import time
import random
from django.shortcuts import get_object_or_404
from .models import MilkyLeak
from .milkyleak import get_image_from_mega, post_image

# Tarea asíncrona para postear imágenes con un intervalo aleatorio
@shared_task
def post_image_task(milky_leak_id):
    # Obtener la configuración de MilkyLeak usando el ID
    milky_leak_instance = get_object_or_404(MilkyLeak, id=milky_leak_id)
    
    # Descargar la imagen desde Mega.nz
    image_path = get_image_from_mega(milky_leak_instance)
    
    if image_path:
        message = "Publicación automática desde MilkyLeak"
        # Postear la imagen en Twitter
        post_image(milky_leak_instance, image_path, message)
    
    # Obtener los valores de min_interval y max_interval desde el modelo
    min_interval = milky_leak_instance.min_interval
    max_interval = milky_leak_instance.max_interval
    
    # Generar un intervalo de espera aleatorio entre min_interval y max_interval
    wait_time = random.uniform(min_interval, max_interval) * 60  # Convertir minutos a segundos
    print(f"Esperando {wait_time / 60:.2f} minutos antes de la siguiente publicación.")
    
    # Hacer una pausa antes de reprogramar la tarea
    time.sleep(wait_time)
    
    # Volver a ejecutar la tarea después del intervalo
    post_image_task.apply_async((milky_leak_id,))
