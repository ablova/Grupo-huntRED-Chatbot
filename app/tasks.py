# /home/amigro/app/tasks.py

import logging
import time
import random
from celery import shared_task
from app.integrations.services import send_message, send_options, send_menu, send_email
from app.chatbot import ChatBotHandler
from app.models import WhatsAppAPI, TelegramAPI, MessengerAPI, InstagramAPI, MilkyLeak, Interview, Worker, Person, Configuracion, ConfiguracionBU
from app.wordpress_integration import solicitud, consult
from app.integrations.whatsapp import send_whatsapp_message as send_whatsapp_msg
from django.shortcuts import get_object_or_404
from datetime import timedelta
from django.utils import timezone
from asgiref.sync import sync_to_async

logger = logging.getLogger('celery_tasks')


@shared_task(bind=True, max_retries=3)
async def send_whatsapp_message(self, recipient, message):
    try:
        await send_message('whatsapp', recipient, message)
        logger.info(f"Mensaje de WhatsApp enviado correctamente a {recipient}")
    except Exception as e:
        logger.error(f"Error enviando mensaje a WhatsApp: {e}")
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
async def send_whatsapp_options(self, recipient, message, options):
    try:
        await send_options('whatsapp', recipient, message, options)
        logger.info(f"Opciones enviadas a WhatsApp {recipient}")
    except Exception as e:
        logger.error(f"Error enviando opciones a WhatsApp: {e}")
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
async def send_telegram_message(self, chat_id, message):
    try:
        await send_message('telegram', chat_id, message)
        logger.info(f"Mensaje de Telegram enviado correctamente a {chat_id}")
    except Exception as e:
        logger.error(f"Error enviando mensaje a Telegram: {e}")
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
async def send_telegram_options(self, chat_id, message, options):
    try:
        await send_options('telegram', chat_id, message, options)
        logger.info(f"Opciones enviadas a Telegram {chat_id}")
    except Exception as e:
        logger.error(f"Error enviando opciones a Telegram: {e}")
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
async def send_messenger_message(self, recipient_id, message):
    try:
        await send_message('messenger', recipient_id, message)
        logger.info(f"Mensaje de Messenger enviado correctamente a {recipient_id}")
    except Exception as e:
        logger.error(f"Error enviando mensaje a Messenger: {e}")
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
async def update_job_recommendations():
    try:
        # Obtén las vacantes de WordPress y actualiza recomendaciones usando `consult`
        vacantes = consult(page=1, url="https://amigro.org/browse-jobs/")
        # Implementar la lógica para actualizar recomendaciones
        logger.info(f"Recomendaciones de trabajo actualizadas con {len(vacantes)} vacantes.")
    except Exception as e:
        logger.error(f"Error actualizando recomendaciones de trabajo: {e}")


@shared_task
async def clean_old_chat_states():
    try:
        # Implementar la lógica para limpiar estados antiguos
        logger.info("Estados de chat antiguos limpiados correctamente.")
    except Exception as e:
        logger.error(f"Error limpiando estados de chat antiguos: {e}")

#Se crean las acciones o tareas para entrevistas, recordatorio y todo lo que tenga que ver con ese paso del aplicativo
@shared_task(bind=True, max_retries=3)
async def send_interview_reminder(person_id, job_id, interview_date):
    """
    Enviar recordatorio 1 día antes de la entrevista.
    """
    person = await sync_to_async(Person.objects.get)(id=person_id)
    job = await sync_to_async(Worker.objects.get)(id=job_id)
    message = f"Hola {person.name}, te recordamos que tienes una entrevista para la posición {job.title} mañana a las {interview_date.strftime('%H:%M')}."
    
    await send_message('whatsapp', person.phone, message)
@shared_task(bind=True, max_retries=3)
def send_company_info(person_id, job_id):
    """
    Enviar información de la empresa 2 días antes de la entrevista.
    """
    person = Person.objects.get(id=person_id)
    job = Worker.objects.get(id=job_id)
    message = f"Hola {person.name}, te compartimos información sobre {job.company}, donde tendrás tu entrevista en 2 días. ¡Prepárate bien!"
    
    send_message('whatsapp', person.phone, message)

def schedule_reminders(person, job, interview_date, interview_type):
    """
    Programa las tareas de recordatorio para el candidato y notificación al entrevistador.
    """
    # 1 día antes
    send_interview_reminder.apply_async(
        (person.id, job.id, interview_date),
        eta=interview_date - timedelta(days=1)
    )
    
    # 2 días antes
    send_company_info.apply_async(
        (person.id, job.id),
        eta=interview_date - timedelta(days=2)
    )

    # Confirmación y solicitud de ubicación 30 minutos antes
    send_confirmation_request_task.apply_async(
        (person.id, job.id, interview_date),
        eta=interview_date - timedelta(minutes=30)
    )

    # Notificar al entrevistador si el candidato confirma
    notify_interviewer_task.apply_async(
        (interview_id,),
        eta=interview_date - timedelta(minutes=15)
    )

@shared_task
async def send_daily_notification():
    config = await sync_to_async(lambda: Configuracion.objects.first())()
    if not config.is_test_mode:
        return

    current_hour = datetime.now().strftime('%H:%M')
    if current_hour == config.notification_hour:
        message = "📅 Buenos días, esta es tu notificación diaria de prueba."
        await send_whatsapp_msg(config.test_phone_number, message, config.default_platform)
        logger.info("Notificación diaria enviada.")


@shared_task(bind=True, max_retries=3)
def alerta_nueva_empresa(company_data):
    # Enviar el WhatsApp a un número específico para notificar de una nueva empresa
    message = f"Se ha creado una nueva empresa: {company_data['company_name']} con datos de contacto: {company_data['job_whatsapp']}"
    send_whatsapp_notification('52518490291', message)  # Número destino

@shared_task
def scheduled_scraping():
    """
    Ejecuta el scraping para todas las unidades de negocio habilitadas y envía un reporte.
    """
    for bu in ConfiguracionBU.objects.all():
        if not bu.business_unit.scrapping_enabled:
            logger.info(f"Scraping deshabilitado para {bu.business_unit.name}.")
            continue

        destinatario = bu.correo_bu or f"hola@{bu.dominio_bu.split('//')[-1].split('/')[0]}"
        if not destinatario:
            logger.warning(f"No se encontró destinatario para {bu.business_unit.name}.")
            continue

        vacantes_por_dominio = {}

        for domain in bu.scraping_domains:
            vacantes = consult(page=1, url=domain, business_unit=bu.business_unit)
            if vacantes:
                logger.info(f"Scraping exitoso para {bu.business_unit.name}: {len(vacantes)} vacantes encontradas en {domain}.")
                vacantes_por_dominio[domain] = vacantes
            else:
                logger.warning(f"No se encontraron vacantes para {bu.business_unit.name} en {domain}.")

        if vacantes_por_dominio:
            enviar_reporte_vacantes(bu.business_unit.name, destinatario, vacantes_por_dominio)
        else:
            logger.info(f"No se encontraron vacantes para {bu.business_unit.name} en ninguno de los dominios configurados.")

def enviar_reporte_vacantes(business_unit_name, destinatario, vacantes_por_dominio):
    """
    Envía un reporte por correo con el listado de vacantes encontradas, agrupadas por dominio.
    """
    subject = f"Reporte de Vacantes Cargadas - {business_unit_name}"
    body = f"<h1>Reporte de Vacantes</h1><p>Se han encontrado un total de {sum(len(v) for v in vacantes_por_dominio.values())} vacantes para la unidad de negocio {business_unit_name}.</p>"

    # Añadir detalles agrupados por dominio
    for domain, vacantes in vacantes_por_dominio.items():
        body += f"<h2>Vacantes de {domain}</h2>"
        body += "<ul>"
        for vacante in vacantes:
            title = vacante.get('title', 'Sin título')
            company = vacante.get('company', 'Empresa desconocida')
            address = vacante.get('location', {}).get('address', 'Dirección no especificada')
            salary = vacante.get('salary', 'Salario no especificado')
            job_type = vacante.get('job_type', 'Tipo no especificado')

            body += (
                f"<li><strong>{title}</strong> en <em>{company}</em><br>"
                f"📍 Dirección: {address}<br>"
                f"💼 Tipo: {job_type}<br>"
                f"💲 Salario: {salary}</li><br>"
            )
        body += "</ul>"

    body += "<p>Este es un reporte automático generado por el sistema de scraping de Grupo huntRED®.</p>"

    send_email(business_unit_name, subject, destinatario, body)

@shared_task(bind=True, max_retries=3)
async def verify_candidate_location(self, interview_id):
    interview = await sync_to_async(Interview.objects.get)(id=interview_id)

    # Verificar si la entrevista es presencial
    if interview.interview_type != 'presencial':
        logger.info(f"Entrevista virtual detectada para ID: {interview_id}. No se realiza verificación de ubicación.")
        return

    job = interview.job

    if not interview.candidate_latitude or not interview.candidate_longitude:
        logger.warning(f"No se pudo verificar la ubicación para la entrevista ID: {interview_id}. Falta la ubicación del candidato.")
        return

    candidate_lat = float(interview.candidate_latitude)
    candidate_lon = float(interview.candidate_longitude)
    job_lat = float(job.latitude)
    job_lon = float(job.longitude)

    # Calcular distancia entre el candidato y el lugar de la entrevista
    distance = haversine_distance(candidate_lat, candidate_lon, job_lat, job_lon)

    # Si la distancia es menor a 200 metros, se considera que está en el lugar correcto
    if distance <= 0.2:
        interview.location_verified = True
        message = f"Gracias por llegar a tu entrevista presencial para la posición {job.title}. ¡Te deseamos mucho éxito!"
    else:
        interview.location_verified = False
        message = (
            f"No parece que te encuentres en el lugar acordado para la entrevista presencial de la posición {job.title}. "
            "Por favor, verifica la dirección e intenta llegar a tiempo."
        )

    await sync_to_async(interview.save)()
    await send_message('whatsapp', interview.person.phone, message)

@shared_task(bind=True, max_retries=3)
async def send_confirmation_request(self, interview_id):
    """
    Envía un mensaje al candidato para que confirme su asistencia y solicite su ubicación si es presencial.
    """
    interview = await sync_to_async(Interview.objects.get)(id=interview_id)
    job = interview.job
    person = interview.person

    message = (
        f"Hola {person.name}, ¿puedes confirmar si ya te encuentras en el lugar para la entrevista "
        f"de la posición {job.title}? Responde con 'Sí' para confirmar tu asistencia."
    )

    if interview.interview_type == 'presencial':
        message += (
            "\n\nAdemás, por favor comparte tu ubicación actual para validar que estás en el lugar correcto. "
            "Esto nos ayudará a confirmar tu asistencia."
        )

    await send_message('whatsapp', person.phone, message)

@shared_task(bind=True, max_retries=3)
async def send_follow_up_messages(self, interview_id):
    """
    Envía mensajes adicionales para mantener el canal de comunicación abierto.
    """
    interview = await sync_to_async(Interview.objects.get)(id=interview_id)
    job = interview.job
    person = interview.person

    # Mensaje de seguimiento 1: Información sobre la empresa
    message_1 = (
        f"Queremos asegurarnos de que estés listo para tu entrevista. Aquí tienes más información sobre {job.company}. "
        "Si tienes alguna duda, no dudes en responder este mensaje."
    )
    await send_message('whatsapp', person.phone, message_1)

    # Mensaje de seguimiento 2: Recordatorio de la posición
    message_2 = (
        f"Te recordamos que estás aplicando para la posición de {job.title}. "
        "Estamos aquí para ayudarte si necesitas más información."
    )
    await send_message('whatsapp', person.phone, message_2)

@shared_task(bind=True, max_retries=3)
async def notify_interviewer_task(self, interview_id):
    """
    Tarea programada para notificar al entrevistador que el candidato ha confirmado su asistencia.
    """
    chatbot_handler = ChatBotHandler()
    interview = await sync_to_async(Interview.objects.get)(id=interview_id)
    await chatbot_handler.notify_interviewer(interview)
#________________________________________________________________________________________________
# Esto es para la aplicación de Milkyleak, independiente del chatbot de amigro, solo se utiliza el servidor.
# Tarea asíncrona para postear imágenes con un intervalo aleatorio
@shared_task(bind=True, max_retries=3)
def post_image_task(self, milky_leak_id, post_text=None):
    """
    Tarea asíncrona para postear imágenes con un intervalo aleatorio.
    """
    milky_leak_instance = get_object_or_404(MilkyLeak, id=milky_leak_id)

    # Lógica para descargar y postear la imagen
    image_buffer = get_image(milky_leak_instance)
    if image_buffer:
        message = post_text or "Publicación automática desde MilkyLeak"
        post_image(milky_leak_instance, image_buffer, message)

    # Configurar el próximo intervalo de espera
    min_interval = milky_leak_instance.min_interval
    max_interval = milky_leak_instance.max_interval
    wait_time = random.uniform(min_interval, max_interval) * 60  # Convertir minutos a segundos

    # Reagendar la tarea
    post_image_task.apply_async((milky_leak_id,), countdown=wait_time)
