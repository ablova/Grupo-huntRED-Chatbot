# /home/amigro/app/tasks.py

import logging
import asyncio
import random
from celery import shared_task
from celery.schedules import crontab
from chatbot_django.celery import app
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async
from app.integrations.services import send_message, send_email
from app.chatbot import ChatBotHandler
from app.models import (
    Configuracion,
    ConfiguracionBU,
    Vacante,
    DominioScraping,
    Interview,
    Person,
    BusinessUnit,
    MilkyLeak,
    Application,  # Añade esta línea
)
from app.scraping import validar_url, extraer_detalles_sublink, run_scraper
from app.utils import haversine_distance  # Asegúrate de tener esta función en utils.py

logger = logging.getLogger('celery_tasks')

# Configuración de Celery Beat (asegúrate de que esta configuración esté en tu configuración de Celery)
app.conf.beat_schedule.update({
    'scheduled_scraping': {
        'task': 'app.tasks.ejecutar_scraping',
        'schedule': crontab(hour=3, minute=0),  # Por ejemplo, a las 3:00 AM
    },
    'send_daily_notification': {
        'task': 'app.tasks.send_daily_notification',
        'schedule': crontab(minute=0, hour='*'),  # Ejecuta cada hora
    },
    # Añade más tareas programadas si es necesario
})

# Tareas para enviar mensajes en diferentes plataformas

@shared_task(bind=True, max_retries=3)
def send_whatsapp_message(self, recipient, message):
    try:
        asyncio.run(send_message('whatsapp', recipient, message))
        logger.info(f"✅ Mensaje de WhatsApp enviado correctamente a {recipient}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a WhatsApp: {e}")
        self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def send_whatsapp_options(self, recipient, message, options):
    try:
        asyncio.run(send_message('whatsapp', recipient, message, options))
        logger.info(f"✅ Opciones enviadas a WhatsApp {recipient}")
    except Exception as e:
        logger.error(f"❌ Error enviando opciones a WhatsApp: {e}")
        self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def send_telegram_message(self, chat_id, message):
    try:
        asyncio.run(send_message('telegram', chat_id, message))
        logger.info(f"✅ Mensaje de Telegram enviado correctamente a {chat_id}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Telegram: {e}")
        self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def send_telegram_options(self, chat_id, message, options):
    try:
        asyncio.run(send_message('telegram', chat_id, message, options))
        logger.info(f"✅ Opciones enviadas a Telegram {chat_id}")
    except Exception as e:
        logger.error(f"❌ Error enviando opciones a Telegram: {e}")
        self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def send_messenger_message(self, recipient_id, message):
    try:
        asyncio.run(send_message('messenger', recipient_id, message))
        logger.info(f"✅ Mensaje de Messenger enviado correctamente a {recipient_id}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Messenger: {e}")
        self.retry(exc=e, countdown=60)

# Tarea para ejecutar el scraping programado
@shared_task(bind=True, max_retries=3)
def ejecutar_scraping(self):
    """
    Tarea principal para ejecutar scraping según el cronograma definido.
    """
    logger.info("🚀 Iniciando tarea de scraping programado.")

    async def run():
        # Obtener los dominios verificados
        schedules = await sync_to_async(list)(DominioScraping.objects.filter(verificado=True))
        for dominio in schedules:
            try:
                # Ejecutar el scraper
                vacantes = await run_scraper(dominio)
                if vacantes:
                    tasks = []
                    for vacante_data in vacantes:
                        # Actualizar o crear vacante en la base de datos
                        vacante, created = await sync_to_async(Vacante.objects.update_or_create)(
                            titulo=vacante_data["title"],
                            empresa=vacante_data.get("company", "Empresa desconocida"),
                            defaults={
                                'salario': vacante_data.get("salary"),
                                'tipo': vacante_data.get("job_type", "No especificado"),
                                'ubicacion': vacante_data.get("location", "No especificado"),
                                'descripcion': vacante_data["details"].get("description"),
                                'requisitos': vacante_data["details"].get("requirements"),
                                'beneficios': vacante_data["details"].get("benefits"),
                                'fecha_scraping': timezone.now(),
                            }
                        )
                        if created:
                            logger.info(f"🆕 Vacante creada: {vacante.titulo}")
                        else:
                            logger.info(f"🔄 Vacante actualizada: {vacante.titulo}")

                        # Procesar sublinks de la vacante de manera asíncrona
                        if "link" in vacante_data and vacante_data["link"]:
                            task = procesar_sublinks.delay(vacante.id, vacante_data["link"])
                            tasks.append(task)
                    
                    if tasks:
                        # Esperar a que todas las tareas de sublinks se completen
                        await asyncio.gather(*[asyncio.to_thread(task.get) for task in tasks])
                    
                    logger.info(f"✅ {len(vacantes)} vacantes procesadas para {dominio.dominio}")
                else:
                    logger.warning(f"⚠️ No se encontraron vacantes para {dominio.dominio}")
            except Exception as e:
                logger.error(f"❌ Error durante el scraping de {dominio.dominio}: {e}")
                self.retry(exc=e, countdown=60)

    try:
        asyncio.run(run())
    except Exception as e:
        logger.error(f"❌ Error ejecutando la tarea de scraping: {e}")
        self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def procesar_sublinks(self, vacante_id, sublink):
    """
    Procesa sublinks y extrae información detallada.
    """
    logger.info(f"🔍 Procesando sublink para vacante {vacante_id}: {sublink}")

    async def run():
        try:
            if not await validar_url(sublink):
                logger.warning(f"⚠️ El sublink {sublink} no es válido.")
                return

            detalles = await extraer_detalles_sublink(sublink)
            vacante = await sync_to_async(Vacante.objects.get)(pk=vacante_id)
            vacante.sublink = sublink
            vacante.descripcion = detalles.get("descripcion")
            vacante.requisitos = detalles.get("requisitos")
            vacante.beneficios = detalles.get("beneficios")
            await sync_to_async(vacante.save)()
            logger.info(f"📝 Detalles del sublink guardados para vacante {vacante_id}.")
        except Exception as e:
            logger.error(f"❌ Error procesando sublink {sublink}: {e}")
            self.retry(exc=e, countdown=60)

    try:
        asyncio.run(run())
    except Exception as e:
        logger.error(f"❌ Error ejecutando la tarea de procesar sublinks: {e}")
        self.retry(exc=e, countdown=60)

# Tarea para enviar reporte diario
@shared_task
def enviar_reporte_diario():
    """
    Envía un reporte diario detallado de scraping, incluyendo tasas de éxito y errores.
    """
    logger.info("📊 Generando reporte diario de scraping.")
    try:
        schedules = DominioScraping.objects.filter(verificado=True)
        mensaje = "<h2>📅 Reporte diario de scraping:</h2><ul>"

        for schedule in schedules:
            vacantes_creadas = Vacante.objects.filter(
                fecha_scraping__date=timezone.now().date(),
                empresa=schedule.empresa
            ).count()

            registros = RegistroScraping.objects.filter(
                dominio=schedule,
                fecha_inicio__date=timezone.now().date()
            )
            exitosos = registros.filter(estado="exitoso").count()
            fallidos = registros.filter(estado="fallido").count()
            tasa_exito = (exitosos / (exitosos + fallidos) * 100) if (exitosos + fallidos) > 0 else 0

            mensaje += (
                f"<li>📌 <strong>{schedule.empresa}</strong> en <em>{schedule.dominio}</em>: "
                f"{vacantes_creadas} vacantes creadas. "
                f"Tasa de éxito: {tasa_exito:.2f}%. "
                f"Errores: {fallidos}.</li>"
            )

        mensaje += "</ul><p>Este es un reporte automático generado por el sistema de scraping de Grupo huntRED®.</p>"

        # Enviar correo
        configuracion = Configuracion.objects.first()
        if configuracion and configuracion.test_email:
            asyncio.run(send_email(
                business_unit_name="Grupo huntRED®",
                subject="📈 Reporte Diario de Scraping",
                destinatario=configuracion.test_email,
                body=mensaje,
                html=True
            ))
            logger.info("✅ Reporte diario enviado por correo.")
        else:
            logger.warning("⚠️ No se encontró la configuración de correo para enviar el reporte diario.")
    except Exception as e:
        logger.error(f"❌ Error enviando el reporte diario: {e}")

# Tarea para limpieza semestral de vacantes
@shared_task
def limpieza_semestral_vacantes():
    """
    Limpia vacantes no actualizadas en más de 6 meses y registra detalles para auditoría.
    """
    logger.info("🧹 Iniciando limpieza semestral de vacantes.")
    try:
        hace_seis_meses = timezone.now() - timedelta(days=180)
        vacantes_a_eliminar = Vacante.objects.filter(fecha_scraping__lt=hace_seis_meses)
        vacantes_por_empresa = vacantes_a_eliminar.values('empresa').annotate(total=Count('id'))
        
        vacantes_eliminadas = vacantes_a_eliminar.count()
        vacantes_a_eliminar.delete()
        
        # Generar reporte de eliminación
        detalles = "\n".join([f"{v['empresa']}: {v['total']} vacantes eliminadas." for v in vacantes_por_empresa])
        logger.info(f"✅ Limpieza completada: {vacantes_eliminadas} vacantes eliminadas.")
        
        # Guardar registro en archivo
        with open(f"limpieza_vacantes_{timezone.now().date()}.log", "w") as log_file:
            log_file.write(f"Limpieza realizada el {timezone.now().date()}:\n{detalles}\n")
    except Exception as e:
        logger.error(f"❌ Error durante la limpieza semestral: {e}")

# Tarea para verificar dominios de scraping
@shared_task
def verificar_dominios_scraping():
    """
    Verifica periódicamente los dominios en la base de datos para validar su estado.
    """
    logger.info("🔄 Iniciando verificación de dominios de scraping.")
    dominios = DominioScraping.objects.all()
    for dominio in dominios:
        try:
            is_valid = asyncio.run(validar_url(dominio.dominio))
            dominio.verificado = is_valid
            dominio.mensaje_error = "" if is_valid else "Dominio no responde o es inválido."
            dominio.save()
            if is_valid:
                logger.info(f"✅ Dominio verificado exitosamente: {dominio.dominio}")
            else:
                logger.warning(f"⚠️ Dominio no válido: {dominio.dominio}")
        except Exception as e:
            logger.error(f"❌ Error verificando dominio {dominio.dominio}: {e}")

@shared_task
def ejecutar_scraping_inteligente():
    """
    Scraping inteligente que prioriza dominios con mayor éxito.
    """
    dominios = DominioScraping.objects.filter(activo=True).annotate(
        success_rate=Count('registroscraping', filter=models.Q(registroscraping__estado='exitoso'))
    ).order_by('-success_rate')

    asyncio.run(scrape_domains(dominios))
    
# Tarea para ejecutar una prueba de scraping
@shared_task
def ejecutar_prueba_scraping():
    """
    Ejecuta una prueba de scraping en un dominio específico para validación rápida.
    """
    logger.info("🧪 Ejecutando prueba de scraping.")
    try:
        configuracion = Configuracion.objects.first()
        dominio_prueba = DominioScraping.objects.filter(verificado=True).first()
        if not dominio_prueba:
            logger.warning("⚠️ No hay dominios verificados disponibles para la prueba.")
            return

        vacantes = asyncio.run(run_scraper(dominio_prueba))
        if vacantes:
            logger.info(f"✅ Prueba de scraping exitosa en {dominio_prueba.dominio}. Vacantes encontradas: {len(vacantes)}")
        else:
            logger.warning(f"⚠️ Prueba de scraping fallida en {dominio_prueba.dominio}. No se encontraron vacantes.")
    except Exception as e:
        logger.error(f"❌ Error ejecutando prueba de scraping: {e}")

# Tareas relacionadas con entrevistas y notificaciones

@shared_task(bind=True, max_retries=3)
def verify_candidate_location(self, interview_id):
    """
    Verifica la ubicación del candidato para entrevistas presenciales.
    """
    async def run():
        interview = await sync_to_async(Interview.objects.get)(id=interview_id)

        # Verificar si la entrevista es presencial
        if interview.interview_type != 'presencial':
            logger.info(f"🖥️ Entrevista virtual detectada para ID: {interview_id}. No se realiza verificación de ubicación.")
            return

        job = interview.job

        if not interview.candidate_latitude or not interview.candidate_longitude:
            logger.warning(f"⚠️ No se pudo verificar la ubicación para la entrevista ID: {interview_id}. Falta la ubicación del candidato.")
            return

        try:
            candidate_lat = float(interview.candidate_latitude)
            candidate_lon = float(interview.candidate_longitude)
            job_lat = float(job.latitude)
            job_lon = float(job.longitude)

            # Calcular distancia entre el candidato y el lugar de la entrevista
            distance = haversine_distance(candidate_lat, candidate_lon, job_lat, job_lon)

            # Si la distancia es menor a 200 metros, se considera que está en el lugar correcto
            if distance <= 0.2:
                interview.location_verified = True
                message = f"✅ Gracias por llegar a tu entrevista presencial para la posición {job.title}. ¡Te deseamos mucho éxito!"
            else:
                interview.location_verified = False
                message = (
                    f"❌ No parece que te encuentres en el lugar acordado para la entrevista presencial de la posición {job.title}. "
                    "Por favor, verifica la dirección e intenta llegar a tiempo."
                )

            await sync_to_async(interview.save)()
            await asyncio.run(send_message('whatsapp', interview.person.phone, message))
            logger.info(f"📍 Verificación de ubicación realizada para entrevista ID: {interview_id}.")
        except Exception as e:
            logger.error(f"❌ Error verificando ubicación para entrevista ID: {interview_id}: {e}")
            self.retry(exc=e, countdown=60)

    try:
        asyncio.run(run())
    except Exception as e:
        logger.error(f"❌ Error ejecutando la tarea de verify_candidate_location: {e}")
        self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def send_confirmation_request_task(self, interview_id):
    """
    Envía un mensaje al candidato para que confirme su asistencia y solicite su ubicación si es presencial.
    """
    async def run():
        interview = await sync_to_async(Interview.objects.get)(id=interview_id)
        job = interview.job
        person = interview.person

        message = (
            f"👋 Hola {person.name}, ¿puedes confirmar si ya te encuentras en el lugar para la entrevista "
            f"de la posición {job.title}? Responde con 'Sí' para confirmar tu asistencia."
        )

        if interview.interview_type == 'presencial':
            message += (
                "\n\n📍 Además, por favor comparte tu ubicación actual para validar que estás en el lugar correcto. "
                "Esto nos ayudará a confirmar tu asistencia."
            )

        await asyncio.run(send_message('whatsapp', person.phone, message))
        logger.info(f"📩 Solicitud de confirmación enviada a {person.phone} para entrevista ID: {interview_id}")

    try:
        asyncio.run(run())
    except Exception as e:
        logger.error(f"❌ Error ejecutando la tarea de send_confirmation_request_task: {e}")
        self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def send_follow_up_messages(self, interview_id):
    """
    Envía mensajes adicionales para mantener el canal de comunicación abierto.
    """
    async def run():
        interview = await sync_to_async(Interview.objects.get)(id=interview_id)
        job = interview.job
        person = interview.person

        # Mensaje de seguimiento 1: Información sobre la empresa
        message_1 = (
            f"📄 Queremos asegurarnos de que estés listo para tu entrevista. Aquí tienes más información sobre {job.company}. "
            "Si tienes alguna duda, no dudes en responder este mensaje."
        )
        await asyncio.run(send_message('whatsapp', person.phone, message_1))

        # Mensaje de seguimiento 2: Recordatorio de la posición
        message_2 = (
            f"🔔 Te recordamos que estás aplicando para la posición de {job.title}. "
            "Estamos aquí para ayudarte si necesitas más información."
        )
        await asyncio.run(send_message('whatsapp', person.phone, message_2))
        logger.info(f"📬 Mensajes de seguimiento enviados a {person.phone} para entrevista ID: {interview_id}")

    try:
        asyncio.run(run())
    except Exception as e:
        logger.error(f"❌ Error ejecutando la tarea de send_follow_up_messages: {e}")
        self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def notify_interviewer_task(self, interview_id):
    """
    Tarea programada para notificar al entrevistador que el candidato ha confirmado su asistencia.
    """
    async def run():
        chatbot_handler = ChatBotHandler()
        interview = await sync_to_async(Interview.objects.get)(id=interview_id)
        await chatbot_handler.notify_interviewer(interview)
        logger.info(f"📢 Entrevistador notificado para entrevista ID: {interview_id}")

    try:
        asyncio.run(run())
    except Exception as e:
        logger.error(f"❌ Error ejecutando la tarea de notify_interviewer_task: {e}")
        self.retry(exc=e, countdown=60)

# Tarea para enviar notificaciones diarias (si es necesario)
@shared_task(bind=True, max_retries=3)
def send_daily_notification(self):
    """
    Envía notificaciones diarias de prueba.
    """
    async def run():
        try:
            configuracion = await sync_to_async(lambda: Configuracion.objects.first())()
            if not configuracion or not configuracion.is_test_mode:
                logger.info("🔒 Modo de pruebas desactivado o configuración faltante. No se envía notificación diaria.")
                return

            current_time = timezone.now().time()
            if configuracion.notification_hour and current_time.hour == configuracion.notification_hour.hour and current_time.minute == configuracion.notification_hour.minute:
                message = "📅 Buenos días, esta es tu notificación diaria de prueba."
                await send_message(configuracion.default_platform, configuracion.test_phone_number, message)
                logger.info("✅ Notificación diaria enviada.")
            else:
                logger.info("🕒 No es la hora configurada para enviar la notificación diaria.")
        except Exception as e:
            logger.error(f"❌ Error enviando la notificación diaria: {e}")

    try:
        asyncio.run(run())
    except Exception as e:
        logger.error(f"❌ Error ejecutando la tarea de send_daily_notification: {e}")
        self.retry(exc=e, countdown=60)



#________________________________________________________________________________________________
# Esto es para la aplicación de Milkyleak, independiente del chatbot de amigro, solo se utiliza el servidor.
# Tarea asíncrona para postear imágenes con un intervalo aleatorio
@shared_task(bind=True, max_retries=3)
def post_image_task(self, milky_leak_id, post_text=None):
    """
    Tarea asíncrona para postear imágenes con un intervalo aleatorio.
    """
    async def run():
        milky_leak_instance = await sync_to_async(get_object_or_404)(MilkyLeak, id=milky_leak_id)

        # Lógica para descargar y postear la imagen
        image_buffer = await sync_to_async(get_image)(milky_leak_instance)
        if image_buffer:
            message = post_text or "Publicación automática desde MilkyLeak"
            await sync_to_async(post_image)(milky_leak_instance, image_buffer, message)

        # Configurar el próximo intervalo de espera
        min_interval = milky_leak_instance.min_interval
        max_interval = milky_leak_instance.max_interval
        wait_time = random.uniform(min_interval, max_interval) * 60  # Convertir minutos a segundos

        # Reagendar la tarea
        post_image_task.apply_async((milky_leak_id,), countdown=wait_time)

    try:
        asyncio.run(run())
    except Exception as e:
        logger.error(f"❌ Error ejecutando la tarea de post_image_task: {e}")
        self.retry(exc=e, countdown=60)