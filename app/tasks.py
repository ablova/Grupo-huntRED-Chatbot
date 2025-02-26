# /home/pablo/app/tasks.py

import logging
import asyncio
import random
from celery import shared_task, chain, group
from celery.schedules import crontab
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
from celery.exceptions import MaxRetriesExceededError
import celery
app = celery.current_app
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async
from app.chatbot.integrations.services import send_email, send_message
from app.chatbot.chatbot import ChatBotHandler
from app.chatbot.integrations.invitaciones import enviar_invitacion_completar_perfil
from app.utilidades.parser import CVParser, IMAPCVProcessor
from app.utilidades.email_scraper import email_scraper
from app.models import (
    Configuracion, ConfiguracionBU,
    Vacante, Person, BusinessUnit,
    DominioScraping, RegistroScraping,
    Interview, Application,
)
from app.utilidades.linkedin import (
    process_api_data,
    fetch_member_profile,
    process_csv,
    slow_scrape_from_csv,
    scrape_linkedin_profile,
    deduplicate_candidates,
)
from app.chatbot.workflow.amigro import (
    generate_candidate_summary_task,
    send_migration_docs_task,
    follow_up_migration_task
)
from app.utilidades.scraping import (
    validar_url, ScrapingPipeline, scrape_and_publish, process_domain
)
from app.chatbot.utils import haversine_distance, sanitize_business_unit_name
from app.ml.ml_model import GrupohuntREDMLPipeline, MatchmakingLearningSystem
from app.ml.ml_opt import check_system_load, configure_tensorflow_based_on_load
from app.utilidades.catalogs import DIVISIONES
import json, os

logger = logging.getLogger("app.tasks")

@shared_task
def add(x, y):
    return x + y

# =========================================================
# Tareas relacionadas con notificaciones
# =========================================================
def get_business_unit(business_unit_id=None, default_name="amigro"):
    if business_unit_id:
        return BusinessUnit.objects.filter(id=business_unit_id).first()
    return BusinessUnit.objects.filter(name=default_name).first()

@shared_task(bind=True, max_retries=5, default_retry_delay=40, queue='notifications')
def send_whatsapp_message_task(self, recipient, message, business_unit_id=None):
    try:
        bu = BusinessUnit.objects.get(id=business_unit_id) if business_unit_id else BusinessUnit.objects.filter(name='amigro').first()
        asyncio.run(send_message('whatsapp', recipient, message, bu))
        logger.info(f"✅ Mensaje de WhatsApp enviado a {recipient}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a WhatsApp: {e}")
        self.retry(exc=e)


@shared_task(bind=True, max_retries=5, default_retry_delay=40, queue='notifications')
def send_telegram_message_task(self, chat_id, message, business_unit_id=None):
    try:
        business_unit = get_business_unit(business_unit_id)
        asyncio.run(send_message('telegram', chat_id, message, business_unit))
        logger.info(f"✅ Mensaje de Telegram enviado a {chat_id}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Telegram: {e}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=5, default_retry_delay=40, queue='notifications')
def send_messenger_message_task(self, recipient_id, message, business_unit_id=None):
    try:
        business_unit = get_business_unit(business_unit_id)
        asyncio.run(send_message('messenger', recipient_id, message, business_unit))
        logger.info(f"✅ Mensaje de Messenger enviado a {recipient_id}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Messenger: {e}")
        self.retry(exc=e)


# =========================================================
# Tareas relacionadas con el ML (Machine Learning)
# =========================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=120, queue='ml')
def train_ml_task(self, business_unit_id=None):
    """
    Tarea para entrenar el modelo de ML para una Business Unit específica o todas.
    """
    try:
        # Verificar la carga del sistema
        if not check_system_load(threshold=70):
            logger.info("Carga del sistema alta. Reintentando en 10 minutos.")
            raise self.retry(countdown=600)  # Reintentar en 30 minutos

        # Configurar TensorFlow según la carga
        configure_tensorflow_based_on_load()

        logger.info("🧠 Iniciando tarea de entrenamiento de Machine Learning.")
        if business_unit_id:
            business_units = BusinessUnit.objects.filter(id=business_unit_id)
        else:
            business_units = BusinessUnit.objects.all()

        for bu in business_units:
            logger.info(f"📊 Entrenando modelo para BU: {bu.name}")
            pipeline = GrupohuntREDMLPipeline(business_unit=bu.name)
            try:
                # 1) Cargar CSV con pandas, ya que 'pipeline.load_data()' no existe
                df = pd.read_csv('/home/pablo/app/model/training_data.csv')
                # 2) Preprocesar
                X_train, X_test, y_train, y_test = pipeline.preprocess_data(df)
                # 3) build_model con el input_dim necesario
                pipeline.build_model(input_dim=X_train.shape[1])
                # 4) Entrenar (dentro de train_model se guarda el .h5)
                pipeline.train_model(X_train, y_train, X_test, y_test)
                # No existe 'save_model', porque el guardado ocurre dentro de train_model().
                # Si realmente quisieras otro guardado manual, podrías crear un nuevo método:
                #
                # pipeline.save_model()   <-- no existe, deberías implementarlo o quitar la llamada.
                # Pero por ahora se te guarda automáticamente en train_model().
                logger.info(f"✅ Modelo entrenado y guardado para {bu.name}")
            except Exception as e:
                logger.error(f"❌ Error entrenando modelo para BU {bu.name}: {e}")
                continue
        logger.info("🚀 Tarea de entrenamiento completada para todas las Business Units.")
    except Retry:
        raise  # Permitir que Celery maneje el reintento
    except Exception as e:
        logger.error(f"❌ Error en la tarea de entrenamiento de ML: {e}")
        self.retry(exc=e)
        
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
            # 1) Cargar CSV con pandas, ya que 'pipeline.load_data()' no existe
            df = pd.read_csv('/home/pablo/app/model/training_data.csv')
            # 2) Preprocesar
            X_train, X_test, y_train, y_test = pipeline.preprocess_data(df)
            # 3) build_model con el input_dim necesario
            pipeline.build_model(input_dim=X_train.shape[1])
            # 4) Entrenar (dentro de train_model se guarda el .h5)
            pipeline.train_model(X_train, y_train, X_test, y_test)
            # No existe 'save_model', porque el guardado ocurre dentro de train_model().
            # Si realmente quisieras otro guardado manual, podrías crear un nuevo método:
            #
            # pipeline.save_model()   <-- no existe, deberías implementarlo o quitar la llamada.
            # Pero por ahora se te guarda automáticamente en train_model().
            logger.info(f"✅ Modelo ML entrenado para {bu.name}")
    except Exception as e:
        logger.error(f"❌ Error en tarea ML: {e}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=300, queue='ml')
def train_matchmaking_model_task(self, business_unit_id=None):
    """
    Entrena el modelo de matchmaking para una Business Unit específica.
    """
    try:
        if business_unit_id:
            bu = BusinessUnit.objects.get(id=business_unit_id)
        else:
            logger.info("No se proporcionó una Business Unit específica, seleccionando la primera.")
            bu = BusinessUnit.objects.first()  # Seleccionar la primera como predeterminada

        if not bu:
            logger.error("No se encontró una Business Unit para entrenar el modelo.")
            return

        pipeline = GrupohuntREDMLPipeline(bu.name)
        # Si quieres leer un CSV arbitrario
        df = pd.read_csv('/home/pablo/app/model/training_data.csv') 
        # Y luego:
        X_train, X_test, y_train, y_test = pipeline.preprocess_data(df)
        pipeline.build_model(input_dim=X_train.shape[1])  
        pipeline.train_model(X_train, y_train, X_test, y_test)
        # No existe 'save_model', porque el guardado ocurre dentro de train_model().
        # Si realmente quisieras otro guardado manual, podrías crear un nuevo método:
        #
        # pipeline.save_model()   <-- no existe, deberías implementarlo o quitar la llamada.
        #
        # Pero por ahora se te guarda automáticamente en train_model().
        logger.info(f"✅ Modelo matchmaking entrenado para BU: {bu.name}")
    except BusinessUnit.DoesNotExist:
        logger.error(f"BU con ID {business_unit_id} no encontrada.")
    except Exception as e:
        logger.error(f"❌ Error entrenando matchmaking para BU {business_unit_id}: {e}")
        self.retry(exc=e)

@shared_task
def predict_top_candidates_task(vacancy_id, top_n=10):
    vacancy = Vacante.objects.get(id=vacancy_id)
    ml_system = MatchmakingLearningSystem(vacancy.business_unit)
    return ml_system.predict_top_candidates(vacancy, top_n)
# =========================================================
# Tareas relacionadas con el scraping programado
# =========================================================
@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def ejecutar_scraping(self, dominio_id=None):
    """
    Ejecuta el scraping para un dominio específico o todos los dominios verificados.
    
    Args:
        dominio_id (int, optional): ID del dominio a scrapear. Si no se proporciona, 
                                  se ejecutará para todos los dominios verificados.
    """
    try:
        if dominio_id:
            # Ejecutar para un dominio específico
            dominio = DominioScraping.objects.get(pk=dominio_id)
            dominios = [dominio]
        else:
            # Ejecutar para todos los dominios verificados
            dominios = DominioScraping.objects.filter(verificado=True)

        for dominio in dominios:
            logger.info(f"🚀 Iniciando scraping para {dominio.empresa} ({dominio.dominio})")
            
            try:
                # Ejecutar el scraping y obtener las vacantes
                vacantes = asyncio.run(run_scraper(dominio))
                
                # Registrar el resultado del scraping
                RegistroScraping.objects.create(
                    dominio=dominio,
                    estado="exitoso",
                    fecha_inicio=timezone.now(),
                    fecha_fin=timezone.now(),
                    mensaje=f"Scraping completado. Vacantes encontradas: {len(vacantes)}"
                )
                
                logger.info(f"✅ Scraping completado para {dominio.empresa}: {len(vacantes)} vacantes")
                
                # Mostrar las primeras 5 vacantes extraídas (para debugging)
                for vacante in vacantes[:5]:
                    logger.info(f"   - {vacante.get('title', 'Sin título')}")
                    
            except Exception as e:
                logger.error(f"❌ Error en scraping para {dominio.empresa}: {str(e)}")
                RegistroScraping.objects.create(
                    dominio=dominio,
                    estado="fallido",
                    fecha_inicio=timezone.now(),
                    fecha_fin=timezone.now(),
                    mensaje=f"Error: {str(e)}"
                )
                continue

    except DominioScraping.DoesNotExist:
        logger.error(f"Dominio con ID {dominio_id} no encontrado.")
        self.retry(exc=Exception("Dominio no encontrado."))
    except Exception as e:
        logger.error(f"Error al ejecutar scraping: {str(e)}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def verificar_dominios_scraping(self):
    """
    Verifica que los dominios de scraping sean accesibles.
    """
    logger.info("🔄 Verificando dominios de scraping.")
    dominios = DominioScraping.objects.all()

    for dominio in dominios:
        try:
            is_valid = asyncio.run(validar_url(dominio.dominio))
            dominio.verificado = is_valid
            dominio.ultimo_chequeo = timezone.now()
            dominio.mensaje_error = "" if is_valid else "El dominio no responde correctamente"
            dominio.save()

            RegistroScraping.objects.create(
                dominio=dominio,
                estado="exitoso" if is_valid else "fallido",
                fecha_inicio=timezone.now(),
                fecha_fin=timezone.now(),
                mensaje=f"Verificación {'exitosa' if is_valid else 'fallida'}"
            )

            if is_valid:
                logger.info(f"✅ Dominio verificado correctamente: {dominio.dominio}")
            else:
                logger.warning(f"⚠️ Dominio no responde: {dominio.dominio}")

        except Exception as e:
            logger.error(f"❌ Error al verificar dominio {dominio.dominio}: {str(e)}")
            self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def procesar_scraping_dominio(self, dominio_id):
    """
    Ejecuta el scraping para un dominio específico.
    """
    try:
        dominio = DominioScraping.objects.get(id=dominio_id)
        registro = RegistroScraping.objects.create(dominio=dominio, estado='pendiente')

        scraper = asyncio.run(process_domain(dominio, registro))

        registro.estado = "exitoso" if scraper else "fallido"
        registro.save()

        logger.info(f"✅ Scraping completado para {dominio.dominio}")

    except DominioScraping.DoesNotExist:
        logger.error(f"❌ Dominio no encontrado: ID {dominio_id}")
        self.retry(exc=Exception("Dominio no encontrado."))
    except Exception as e:
        logger.error(f"❌ Error en scraping de dominio {dominio_id}: {e}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def procesar_sublinks_task(self, vacante_id, sublink):
    """
    Procesa sublinks de una vacante específica.
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
    """
    Ejecuta el proceso de Machine Learning y scraping en cadena.
    """
    logger.info("🚀 Iniciando proceso de ML y scraping.")

    try:
        # 1. Ejecutar modelo ML inicial
        logger.info("🧠 Entrenando modelo ML inicial...")
        business_units = BusinessUnit.objects.all()
        for bu in business_units:
            try:
                pipeline = GrupohuntREDMLPipeline(bu.name)
                pipeline.load_model()
                pipeline.predict_pending()
                logger.info(f"✅ ML inicial completado para {bu.name}")
            except Exception as e:
                logger.error(f"❌ Error en ML inicial para {bu.name}: {str(e)}")
                continue

        # 2. Ejecutar scraping
        logger.info("🔍 Iniciando proceso de scraping...")
        dominios = DominioScraping.objects.filter(activo=True)
        asyncio.run(scrape_and_publish(dominios))

        # 3. Ejecutar modelo ML final
        logger.info("🧠 Entrenando modelo ML final...")
        for bu in business_units:
            try:
                pipeline = GrupohuntREDMLPipeline(bu.name)
                pipeline.load_model()
                pipeline.predict_pending()
                logger.info(f"✅ ML final completado para {bu.name}")
            except Exception as e:
                logger.error(f"❌ Error en ML final para {bu.name}: {str(e)}")
                continue

        logger.info("✨ Proceso de ML y scraping finalizado con éxito.")

    except Exception as e:
        logger.error(f"❌ Error en el proceso ML + scraping: {str(e)}")
        self.retry(exc=e)

# =========================================================
# Tareas de Notificaciones
# =========================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='notifications')
def send_notification_task(self, platform, recipient, message):
    try:
        asyncio.run(send_message(platform, recipient, message))
        logger.info(f"✅ Notificación enviada a {recipient} en {platform}.")
    except Exception as e:
        logger.error(f"❌ Error enviando notificación: {e}")
        self.retry(exc=e)

def trigger_amigro_workflows(candidate_id):
    """ Ejecuta los flujos de trabajo al agendar un candidato con un cliente. """
    generate_candidate_summary_task.delay(candidate_id)
    send_migration_docs_task.delay(candidate_id)
    
    # Programar seguimiento en 5 días
    follow_up_migration_task.apply_async(args=[candidate_id], countdown=5 * 86400)

    return f"Flujos de trabajo iniciados para el candidato {candidate_id}"

# =========================================================
# Tareas para manejo de datos LinkedIn (API/Csv/Scraping)
# =========================================================

@shared_task
def process_linkedin_api_data_task(member_ids: list):
    """
    Procesa datos desde la API oficial de LinkedIn.
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
def process_linkedin_csv_task(csv_path: str = "/home/pablo/connections.csv"):
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
    Tarea que scrapea un perfil de LinkedIn.
    """
    logger.info(f"Scrapeando perfil: {profile_url}")
    data = scrape_linkedin_profile(profile_url)
    logger.info(f"Datos obtenidos: {data}")
    return data

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def process_csv_and_scrape_task(self, csv_path: str = "/home/pablo/connections.csv"):
    """
    Procesa el archivo CSV y ejecuta scraping de los perfiles.
    Al finalizar, se ejecuta la función de deduplicación para eliminar candidatos duplicados.
    """
    try:
        bu = BusinessUnit.objects.filter(name='huntRED').first()
        if not bu:
            raise Exception("No se encontró la BU huntRED.")

        logger.info("🚀 Iniciando procesamiento del CSV.")
        process_csv(csv_path, bu)  # Procesa el CSV utilizando update_or_create

        # Opcional: Ejecutar deduplicación luego de procesar el CSV
        duplicates = deduplicate_candidates()
        logger.info(f"🧹 Deduplicación completada. Total duplicados eliminados: {len(duplicates)}")

        logger.info("🔍 Iniciando scraping de perfiles.")
        scrape_linkedin_profile()  # Suponiendo que esta función se encarga de scraping de perfiles pendientes

        logger.info("✅ Proceso completo de CSV y scraping finalizado.")
    except Exception as e:
        logger.error(f"❌ Error en el flujo combinado: {e}")
        self.retry(exc=e)
        
@shared_task(bind=True, max_retries=3, default_retry_delay=300, queue='notifications')
def enviar_invitaciones_completar_perfil(self, fields=None):
    """
    Envía invitaciones a candidatos con perfiles incompletos, filtrando por campos específicos.
    
    Args:
        fields (list, optional): Lista de campos a considerar como incompletos (e.g., ['phone', 'email']).
                                 Por defecto, solo 'phone'.
    """
    if fields is None:
        fields = ['phone']
    try:
        query = Q()
        for field in fields:
            query |= Q(**{f"{field}__isnull": True})
        candidatos = Person.objects.filter(query)
        if not candidatos.exists():
            logger.info("No se encontraron candidatos con perfiles incompletos para invitar.")
            return "No candidates to invite."
        
        business_unit = BusinessUnit.objects.first()
        if not business_unit:
            logger.error("No se encontró ninguna BusinessUnit.")
            return "No BusinessUnit found."
        
        invitaciones_enviadas = 0
        for candidate in candidatos:
            enviar_invitacion_completar_perfil(candidate, business_unit)
            invitaciones_enviadas += 1
        
        logger.info(f"Invitaciones enviadas: {invitaciones_enviadas}")
        return f"Invitaciones enviadas: {invitaciones_enviadas}"
    except Exception as e:
        logger.error(f"Error en el task enviar_invitaciones_completar_perfil: {e}", exc_info=True)
        self.retry(exc=e)
# =========================================================
# Tareas para reportes, limpieza y otros
# =========================================================

@shared_task
def send_final_candidate_report(business_unit_id, candidates_ids, recipient_email):
    """
    Genera y envía el reporte final de candidatos con análisis.
    
    :param business_unit_id: ID de la unidad de negocio.
    :param candidates_ids: Lista de IDs de candidatos a incluir en el reporte.
    :param recipient_email: Correo electrónico del destinatario.
    """
    try:
        # Obtener la unidad de negocio
        business_unit = BusinessUnit.objects.get(id=business_unit_id)
        
        # Ruta al logo de la división
        division_logo_path = os.path.join(settings.MEDIA_ROOT, business_unit.logo_path)
        
        # Obtener los candidatos
        candidates = Person.objects.filter(id__in=candidates_ids)
        
        # Generar el reporte principal (asumiendo que ya tienes una función para esto)
        main_report_path = os.path.join(settings.MEDIA_ROOT, f"report_{business_unit.name}.pdf")
        generate_main_candidate_report(candidates, main_report_path)  # Implementa esta función según tu lógica
    
        # Preparar los datos de análisis
        analysis_data = {
            "Análisis de Personalidad": "Alta capacidad de liderazgo, orientado a resultados.",
            "Análisis de Skills": ", ".join(sn.extract_skills(" ".join([p.metadata.get('skills', []) for p in candidates]).replace(',', ' '))),
            "Análisis Salarial": "Rango salarial estimado entre $50,000 - $70,000 USD.",
            # Añade más secciones según necesidad
        }
        
        # Generar la página de análisis
        analysis_pdf_path = os.path.join(settings.MEDIA_ROOT, f"analysis_{business_unit.name}.pdf")
        generate_analysis_page(division_logo_path, analysis_data, analysis_pdf_path)
        
        # Fusionar los PDFs
        final_report_path = os.path.join(settings.MEDIA_ROOT, f"final_report_{business_unit.name}.pdf")
        merge_pdfs(main_report_path, analysis_pdf_path, final_report_path)
        
        # Enviar el correo electrónico con el reporte adjunto
        email = EmailMessage(
            subject=f"Reporte Final de Candidatos - {business_unit.name}",
            body="Adjunto encontrarás el reporte final de candidatos con análisis.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.attach_file(final_report_path)
        email.send()
        
        logger.info(f"Reporte final enviado a {recipient_email}")
        
        # Opcional: Eliminar los archivos temporales
        os.remove(main_report_path)
        os.remove(analysis_pdf_path)
        os.remove(final_report_path)
        
    except Exception as e:
        logger.error(f"Error al enviar el reporte final: {e}")

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='notifications')
def generate_and_send_reports(self):
    """
    Genera y envía reportes consolidados.
    """
    logger.info("📊 Generando reportes consolidados.")
    today = timezone.now().date()

    try:
        configuracion = Configuracion.objects.first()
        if not configuracion:
            logger.warning("⚠️ Sin configuración general.")
            return

        business_units = BusinessUnit.objects.all()
        for bu in business_units:
            try:
                nuevas_posiciones = bu.vacantes.filter(fecha_publicacion__date=today)
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
        logger.error(f"Error reportes consolidados: {e}")
        self.retry(exc=e)

def generate_scraping_report(nuevas_posiciones):
    """
    Genera un reporte de nuevas vacantes.
    """
    report = f"Reporte Nuevas Posiciones - {timezone.now().date()}\n\n"
    for v in nuevas_posiciones:
        report += f"{v.titulo} - {v.descripcion[:50]}...\n"
    return report

def generate_birthday_report(birthday_persons):
    """
    Genera un reporte de cumpleaños.
    """
    report = f"Reporte Cumpleaños - {timezone.now().date()}\n\n"
    for p in birthday_persons:
        report += f"{p.nombre} {p.apellido_paterno}, Tel: {p.phone}\n"
    return report

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

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def scrape_single_profile_task(self, profile_url: str):
    """
    Tarea que toma una URL de perfil LinkedIn y obtiene datos.
    """
    logger.info(f"Scrapeando perfil: {profile_url}")
    data = scrape_linkedin_profile(profile_url)
    logger.info(f"Datos obtenidos: {data}")
    return data

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def scrape_single_profile_task(self, profile_url: str):
    """
    Tarea que toma una URL de perfil LinkedIn y obtiene datos.
    """
    logger.info(f"Scrapeando perfil: {profile_url}")
    data = scrape_linkedin_profile(profile_url)
    logger.info(f"Datos obtenidos: {data}")
    return data

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_emails_and_parse_cvs(self):
    """
    Revisa los correos y procesa los CVs adjuntos.
    """
    try:
        # Aquí iría la lógica para conectarse a la bandeja de entrada y revisar los correos
        # Por ejemplo, usando IMAP para obtener los correos
        # ...

        # Supongamos que tienes una lista de archivos de CVs adjuntos
        cv_files = []  # Aquí deberías obtener los archivos de CVs de los correos

        for cv_file in cv_files:
            # Procesar cada CV
            parser = CVParser(business_unit)  # Asegúrate de pasar la unidad de negocio correcta
            analysis_result = parser.parse_cv(cv_file)
            if analysis_result:  # Validar que el resultado no esté vacío
                person = Person.objects.create(**analysis_result)
                logger.info(f"CV procesado y candidato añadido: {person.name}")
            else:
                logger.warning(f"No se pudo procesar el CV: {cv_file}")

    except Exception as e:
        logger.error(f"Error al procesar correos y CVs: {e}")
        self.retry(exc=e)

@shared_task
def send_signature_reminders():
    """Envía recordatorios de firma a los candidatos y clientes cada 24 horas"""
    pending_signatures = Person.objects.filter(signature_status="pending")

    for person in pending_signatures:
        send_message("whatsapp", person.phone, "⚠️ Tienes un documento pendiente de firma. Revísalo y firma lo antes posible.", person.business_unit)

    return f"Recordatorios enviados a {pending_signatures.count()} personas."

# =========================================================
# Tareas para obtención de oportunidades, scraping, 
# =========================================================
@shared_task(name="tasks.execute_email_scraper")
def execute_email_scraper():
    """ Ejecuta la extracción de vacantes desde correos electrónicos """
    try:
        logger.info("🚀 Ejecutando email scraper desde Celery...")
        email_scraper()
        return "✅ Email scraper ejecutado con éxito."
    except Exception as e:
        logger.error(f"❌ Error en email_scraper: {e}")
        return f"❌ Error en ejecución: {e}"