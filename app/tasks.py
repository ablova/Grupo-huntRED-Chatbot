# /home/amigro/app/tasks.py

import logging
import asyncio
import random
from celery import shared_task, chain, group
from celery.schedules import crontab
from chatbot_django.celery import app
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from asgiref.sync import sync_to_async
from app.integrations.services import send_message, send_email
from app.chatbot import ChatBotHandler
from app.parser import CVParser, IMAPCVProcessor
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
from app.linkedin import (
    process_api_data,
    fetch_member_profile,
    process_csv,
    slow_scrape_from_csv,
    scrape_linkedin_profile
)
from app.scraping import validar_url, extraer_detalles_sublink, run_scraper
from app.utils import haversine_distance, sanitize_business_unit_name
from app.ml_model import GrupohuntREDMLPipeline
from celery.exceptions import MaxRetriesExceededError

logger = logging.getLogger('celery_tasks')

# =========================================================
# Configuración de Celery Beat (programación de tareas)
# =========================================================

app.conf.beat_schedule.update({
    'execute_ml_and_scraping_daily': {
        'task': 'app.tasks.execute_ml_and_scraping',
        'schedule': crontab(hour=11, minute=30),  # Primera ejecución a las 11:30 AM
    },
    'execute_ml_and_scraping_daily_late': {
        'task': 'app.tasks.execute_ml_and_scraping',
        'schedule': crontab(hour=12, minute=0),  # Segunda ejecución a las 12:00 PM
    },
    'send_daily_notification': {
        'task': 'app.tasks.send_daily_notification',
        'schedule': crontab(minute=0, hour='*'),  # Ejecuta cada hora (ejemplo)
    },
    'send_consolidated_reports': {
        'task': 'app.tasks.generate_and_send_reports',
        'schedule': crontab(hour=8, minute=0),  # Ejecuta a las 8:00 AM diariamente
    },
    'send_anniversary_reports': {
        'task': 'app.tasks.generate_and_send_anniversary_reports',
        'schedule': crontab(hour=9, minute=0),
    },
    'send_daily_report': {
        'task': 'app.tasks.enviar_reporte_diario',
        'schedule': crontab(hour=23, minute=59),
    },
    'database_cleanup_vacantes': {
        'task': 'app.tasks.limpieza_vacantes',
        'schedule': crontab(day_of_month='1', month_of_year='1,4,7,11', hour=0, minute=0),
    },
    'verify_scraping_domains_daily': {
        'task': 'app.tasks.verificar_dominios_scraping',
        'schedule': crontab(hour=2, minute=0),
    },
})

# Definición de colas específicas
app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'ml': {
        'exchange': 'ml',
        'routing_key': 'ml.#',
    },
    'scraping': {
        'exchange': 'scraping',
        'routing_key': 'scraping.#',
    },
    'notifications': {
        'exchange': 'notifications',
        'routing_key': 'notifications.#',
    },
}

# Rutas de las tareas a distintas colas
app.conf.task_routes = {
    'app.tasks.execute_ml_and_scraping': {'queue': 'ml'},
    'app.tasks.ejecutar_scraping': {'queue': 'scraping'},
    'app.tasks.send_whatsapp_message': {'queue': 'notifications'},
    'app.tasks.send_telegram_message': {'queue': 'notifications'},
    'app.tasks.send_messenger_message': {'queue': 'notifications'},
    # Añade otras tareas según sea necesario
}

# =========================================================
# Tareas relacionadas con notificaciones
# =========================================================

@shared_task(bind=True, max_retries=5, default_retry_delay=40, queue='notifications')
def send_whatsapp_message_task(self, recipient, message):
    try:
        asyncio.run(send_message('whatsapp', recipient, message))
        logger.info(f"✅ Mensaje de WhatsApp enviado a {recipient}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a WhatsApp: {e}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=5, default_retry_delay=40, queue='notifications')
def send_telegram_message_task(self, chat_id, message):
    try:
        asyncio.run(send_message('telegram', chat_id, message))
        logger.info(f"✅ Mensaje de Telegram enviado a {chat_id}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Telegram: {e}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=5, default_retry_delay=40, queue='notifications')
def send_messenger_message_task(self, recipient_id, message):
    try:
        asyncio.run(send_message('messenger', recipient_id, message))
        logger.info(f"✅ Mensaje de Messenger enviado a {recipient_id}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Messenger: {e}")
        self.retry(exc=e)

# =========================================================
# Tareas relacionadas con el ML (Machine Learning)
# =========================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=120, queue='ml')
def ejecutar_ml(self):
    """
    Tarea para entrenar y evaluar el modelo de Machine Learning para cada Business Unit.
    """
    logger.info("🧠 Iniciando tarea de ML.")
    try:
        business_units = BusinessUnit.objects.all()
        for bu in business_units:
            logger.info(f"📊 Entrenando modelo para BU: {bu.name}")
            pipeline = GrupohuntREDMLPipeline(bu.name)
            data = pipeline.load_data('/home/amigro/app/model/training_data.csv')
            X_train, X_test, y_train, y_test = pipeline.preprocess_data(data)
            
            pipeline.build_model()
            pipeline.train(X_train, y_train, X_test, y_test)
            pipeline.save_model()
            
            logger.info(f"✅ Modelo ML entrenado para {bu.name}")
    except Exception as e:
        logger.error(f"❌ Error en tarea ML: {e}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=300, queue='ml')
def train_matchmaking_model_task(self, business_unit_id):
    """
    Entrena el modelo de matchmaking para una Business Unit específica.
    """
    try:
        bu = BusinessUnit.objects.get(id=business_unit_id)
        pipeline = GrupohuntREDMLPipeline(bu.name)
        data = pipeline.load_data('/home/amigro/app/model/training_data.csv')
        X_train, X_test, y_train, y_test = pipeline.preprocess_data(data)
        pipeline.build_model()
        pipeline.train(X_train, y_train, X_test, y_test)
        pipeline.save_model()
        logger.info(f"✅ Modelo matchmaking entrenado para BU: {bu.name}")
    except BusinessUnit.DoesNotExist:
        logger.error(f"BU con ID {business_unit_id} no encontrada.")
    except Exception as e:
        logger.error(f"❌ Error entrenando matchmaking para BU {business_unit_id}: {e}")
        self.retry(exc=e)

# =========================================================
# Tareas relacionadas con el scraping programado
# =========================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def ejecutar_scraping(self):
    """
    Ejecuta scraping programado (ej. diario).
    """
    logger.info("🚀 Iniciando tarea scraping programado.")
    async def run():
        schedules = await sync_to_async(list)(DominioScraping.objects.filter(verificado=True))
        for dominio in schedules:
            try:
                vacantes = await run_scraper(dominio)
                if vacantes:
                    tasks = []
                    for vac_data in vacantes:
                        vacante, created = await sync_to_async(Vacante.objects.update_or_create)(
                            titulo=vac_data["title"],
                            empresa=vac_data.get("company", "Empresa desconocida"),
                            defaults={
                                'salario': vac_data.get("salary"),
                                'tipo': vac_data.get("job_type", "No especificado"),
                                'ubicacion': vac_data.get("location", "No especificado"),
                                'descripcion': vac_data["details"].get("description"),
                                'requisitos': vac_data["details"].get("requirements"),
                                'beneficios': vac_data["details"].get("benefits"),
                                'fecha_scraping': timezone.now(),
                            }
                        )
                        msg = "creada" if created else "actualizada"
                        logger.info(f"🔄 Vacante {msg}: {vacante.titulo}")

                        # Procesar sublinks asíncronamente
                        if "link" in vac_data and vac_data["link"]:
                            task = procesar_sublinks_task.delay(vacante.id, vac_data["link"])
                            tasks.append(task)

                    if tasks:
                        await asyncio.gather(*[asyncio.to_thread(t.get) for t in tasks])
                    logger.info(f"✅ {len(vacantes)} vacantes procesadas para {dominio.dominio}")
                else:
                    logger.warning(f"⚠️ No vacantes para {dominio.dominio}")
            except Exception as e:
                logger.error(f"❌ Error en scraping de {dominio.dominio}: {e}")
                self.retry(exc=e)

    try:
        asyncio.run(run())
    except Exception as e:
        logger.error(f"❌ Error ejecutando tarea scraping: {e}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def procesar_sublinks_task(self, vacante_id, sublink):
    """
    Procesa sublinks de una vacante.
    """
    logger.info(f"🔍 Procesando sublink {sublink} para vacante {vacante_id}")
    async def run():
        try:
            if not await validar_url(sublink):
                logger.warning(f"⚠️ URL inválida {sublink}")
                return
            detalles = await extraer_detalles_sublink(sublink)
            vacante = await sync_to_async(Vacante.objects.get)(pk=vacante_id)
            vacante.sublink = sublink
            vacante.descripcion = detalles.get("descripcion")
            vacante.requisitos = detalles.get("requisitos")
            vacante.beneficios = detalles.get("beneficios")
            await sync_to_async(vacante.save)()
            logger.info(f"📝 Sublink procesado para vacante {vacante_id}.")
        except Exception as e:
            logger.error(f"❌ Error sublink {sublink}: {e}")
            self.retry(exc=e)

    try:
        asyncio.run(run())
    except Exception as e:
        logger.error(f"❌ Error en tarea procesar_sublinks: {e}")
        self.retry(exc=e)

# Cadena ML -> Scraping -> ML
@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='ml')
def execute_ml_and_scraping(self):
    try:
        workflow = chain(
            ejecutar_ml.s(),
            ejecutar_scraping.s(),
            ejecutar_ml.s()
        )
        workflow.apply_async()
        logger.info("🚀 Workflow ML+Scraping iniciado.")
    except Exception as e:
        logger.error(f"❌ Error en workflow ML+Scraping: {e}")
        self.retry(exc=e)

# =========================================================
# Tareas para manejo de datos LinkedIn (API/Csv/Scraping)
# =========================================================

@shared_task
def process_linkedin_api_data_task(member_ids: list):
    """
    Tarea para procesar datos desde la API oficial de LinkedIn (cuando esté disponible).
    """
    bu = BusinessUnit.objects.filter(name='huntRED').first()
    if not bu:
        logger.error("No se encontró la BU huntRED.")
        return

    if not member_ids:
        logger.warning("No member_ids, nada que hacer.")
        return

    logger.info(f"Iniciando API LinkedIn para {len(member_ids)} miembros.")
    process_api_data(bu, member_ids)
    logger.info("Datos vía API LinkedIn completado.")

@shared_task
def process_linkedin_csv_task(csv_path: str):
    """
    Procesa el CSV de conexiones de LinkedIn.
    """
    bu = BusinessUnit.objects.filter(name='huntRED').first()
    if not bu:
        logger.error("No se encontró BU huntRED.")
        return
    logger.info(f"Procesando CSV {csv_path}")
    process_csv(csv_path, bu)
    logger.info("Procesamiento CSV completado.")

@shared_task
def slow_scrape_profiles_task(csv_path: str):
    """
    Scraping lento desde el CSV (a perfiles de LinkedIn).
    """
    bu = BusinessUnit.objects.filter(name='huntRED').first()
    if not bu:
        logger.error("No se encontró BU huntRED.")
        return
    
    logger.info(f"Iniciando scraping lento {csv_path}")
    slow_scrape_from_csv(csv_path, bu)
    logger.info("Scraping lento completado.")

@shared_task
def scrape_single_profile_task(profile_url: str):
    """
    Tarea que toma una URL de perfil LinkedIn y obtiene datos.
    """
    logger.info(f"Scrapeando perfil: {profile_url}")
    data = scrape_linkedin_profile(profile_url)
    logger.info(f"Datos obtenidos: {data}")
    return data

# =========================================================
# Tareas para reportes, limpieza y otros
# =========================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='notifications')
def enviar_reporte_diario(self):
    """
    Envía un reporte diario del scraping.
    """
    logger.info("📊 Generando reporte diario scraping.")
    try:
        schedules = DominioScraping.objects.filter(verificado=True)
        mensaje = "<h2>📅 Reporte diario:</h2><ul>"
        from app.models import RegistroScraping  # Import local

        for sch in schedules:
            vacantes_creadas = Vacante.objects.filter(
                fecha_scraping__date=timezone.now().date(),
                empresa=sch.empresa
            ).count()

            registros = RegistroScraping.objects.filter(
                dominio=sch,
                fecha_inicio__date=timezone.now().date()
            )
            exitosos = registros.filter(estado="exitoso").count()
            fallidos = registros.filter(estado="fallido").count()
            total = exitosos + fallidos
            tasa_exito = (exitosos / total * 100) if total > 0 else 0
            mensaje += (
                f"<li><strong>{sch.empresa}</strong> ({sch.dominio}): "
                f"{vacantes_creadas} vacantes. Éxito: {tasa_exito:.2f}%. Errores: {fallidos}</li>"
            )
        mensaje += "</ul>"

        configuracion = Configuracion.objects.first()
        if configuracion and configuracion.test_email:
            asyncio.run(send_email(
                business_unit_name="Grupo huntRED®",
                subject="📈 Reporte Diario Scraping",
                destinatario=configuracion.test_email,
                body=mensaje,
                html=True
            ))
            logger.info("✅ Reporte diario enviado por correo.")
        else:
            logger.warning("⚠️ Sin configuracion de correo para reporte diario.")
    except Exception as e:
        logger.error(f"❌ Error reporte diario: {e}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=120, queue='scraping')
def limpieza_vacantes(self):
    """
    Limpieza periódica de vacantes antiguas.
    """
    logger.info("🧹 Limpieza semestral vacantes.")
    from django.db import models
    try:
        hace_seis_meses = timezone.now() - timedelta(days=180)
        vacantes_a_eliminar = Vacante.objects.filter(fecha_scraping__lt=hace_seis_meses)
        vacantes_por_empresa = vacantes_a_eliminar.values('empresa').annotate(total=models.Count('id'))

        count_eliminadas = vacantes_a_eliminar.count()
        vacantes_a_eliminar.delete()
        detalles = "\n".join([f"{v['empresa']}: {v['total']} eliminadas." for v in vacantes_por_empresa])
        logger.info(f"✅ Limpieza completada: {count_eliminadas} vacantes.")
        
        with open(f"limpieza_vacantes_{timezone.now().date()}.log", "w") as log_file:
            log_file.write(f"Limpieza {timezone.now().date()}:\n{detalles}\n")
    except Exception as e:
        logger.error(f"❌ Error limpieza vacantes: {e}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def verificar_dominios_scraping(self):
    """
    Verifica dominios de scraping.
    """
    logger.info("🔄 Verificación dominios scraping.")
    dominios = DominioScraping.objects.all()
    for d in dominios:
        try:
            is_valid = asyncio.run(validar_url(d.dominio))
            d.verificado = is_valid
            d.mensaje_error = "" if is_valid else "Dominio no responde."
            d.save()
            if is_valid:
                logger.info(f"✅ Dominio ok: {d.dominio}")
            else:
                logger.warning(f"⚠️ Dominio no válido: {d.dominio}")
        except Exception as e:
            logger.error(f"❌ Error verificación dominio {d.dominio}: {e}")
            self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='notifications')
def generate_and_send_reports(self):
    """
    Generar y enviar reportes consolidados (ejemplo).
    """
    logger.info("📊 Reportes consolidados.")
    today = timezone.now().date()

    try:
        configuracion = Configuracion.objects.first()
        if not configuracion:
            logger.warning("⚠️ Sin configuración general.")
            return

        business_units = BusinessUnit.objects.all()
        for bu in business_units:
            try:
                nuevas_posiciones = bu.vacantes.filter(created_at__date=today)
                birthday_persons = Person.objects.filter(
                    fecha_nacimiento__month=today.month,
                    fecha_nacimiento__day=today.day,
                    interactions__timestamp__date=today
                ).distinct()

                scraping_report = generate_scraping_report(nuevas_posiciones)
                birthday_report = generate_birthday_report(birthday_persons)

                admin_phone = bu.admin_phone if bu.admin_phone else configuracion.test_phone_number
                admin_email = bu.admin_email if bu.admin_email else configuracion.test_email

                # Mensaje WA
                admin_whatsapp_message = (
                    f"📋 Reporte {today.strftime('%d/%m/%Y')}\n\n"
                    f"Nuevas Posiciones: {nuevas_posiciones.count()} en {bu.name}\n"
                    f"Cumpleaños: {birthday_persons.count()} en {bu.name}\n"
                    "Ver detalles en tu correo."
                )
                send_whatsapp_message_task.delay(
                    recipient=admin_phone,
                    message=admin_whatsapp_message
                )

                # Email
                try:
                    configuracion_bu = ConfiguracionBU.objects.get(business_unit=bu)
                    domain_bu = configuracion_bu.dominio_bu
                except ConfiguracionBU.DoesNotExist:
                    logger.error(f"Sin ConfigBU para {bu.name}")
                    domain_bu = "tudominio.com"

                email_subject = f"📋 Reporte Consolidado {today.strftime('%d/%m/%Y')}"
                email_text = (
                    f"Hola Admin {bu.name},\n\n"
                    f"Nuevas Posiciones: {nuevas_posiciones.count()}\n"
                    f"Cumpleaños: {birthday_persons.count()}\n\n"
                    "Detalles en dashboard."
                )

                send_email_task.delay(
                    user_id=bu.name,
                    email_type='consolidated_report',
                    dynamic_content=email_text
                )
                logger.info(f"✅ Correo reporte {bu.name} a {admin_email}")

                # Gamificación por cumpleaños
                for person in birthday_persons:
                    gamification_profile = person.enhancednetworkgamificationprofile
                    gamification_profile.award_points('birthday_greeting')
                    logger.info(f"🏅 Gamificación a {person.nombre}")

            except Exception as bu_error:
                logger.error(f"❌ Error procesando BU {bu.name}: {bu_error}")
                self.retry(exc=bu_error, countdown=60)
    except Exception as e:
        logger.error(f"❌ Error reportes consolidados: {e}")
        self.retry(exc=e)

def generate_scraping_report(nuevas_posiciones):
    report = f"Reporte Nuevas Posiciones - {timezone.now().date()}\n\n"
    for v in nuevas_posiciones:
        report += f"{v.titulo} - {v.descripcion[:50]}...\n"
    return report

def generate_birthday_report(birthday_persons):
    report = f"Reporte Cumpleaños - {timezone.now().date()}\n\n"
    for p in birthday_persons:
        report += f"{p.nombre} {p.apellido_paterno}, Tel: {p.phone}\n"
    return report