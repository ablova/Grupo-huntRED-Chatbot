# /home/pablo/app/tasks.py
"""
Archivo de compatibilidad para tareas de Celery.
Este archivo importa todas las tareas desde los módulos específicos 
en app/tasks/ para mantener compatibilidad con el código existente.

NOTA: Este archivo será eliminado eventualmente. Todo el código nuevo debe
usar directamente los módulos específicos.
"""

import logging
import warnings

# Advertencia de deprecación
warnings.warn(
    "El archivo app/tasks.py está obsoleto. Usa los módulos específicos en app/tasks/",
    DeprecationWarning, stacklevel=2
)

# Importar todas las tareas desde los módulos específicos
from app.ats.tasks.base import with_retry, add
from app.ats.tasks.notifications import (
    send_ntfy_notification, send_linkedin_login_link,
    send_whatsapp_message_task, send_telegram_message_task, send_messenger_message_task
)
from app.ats.tasks.scraping import (
    ejecutar_scraping, retrain_ml_scraper, verificar_dominios_scraping,
    procesar_scraping_dominio, procesar_sublinks_task, execute_ml_and_scraping,
    execute_email_scraper, process_cv_emails_task
)
from app.ats.tasks.ml import (
    train_ml_task, ejecutar_ml, train_matchmaking_model_task,
    predict_top_candidates_task, sync_jobs_with_api
)
from app.ats.tasks.onboarding import (
    process_client_feedback_task, update_client_metrics_task,
    generate_client_feedback_reports_task, process_onboarding_ml_data_task,
    generate_employee_satisfaction_reports_task
)
from app.ats.tasks.reports import (
    generate_weekly_report_task, generate_scraping_efficiency_report_task,
    generate_conversion_funnel_report_task
)
# Configuración de logging
logger = logging.getLogger(__name__)

# Notificar la carga del archivo deprecado
logger.warning(
    "El archivo app/tasks.py está obsoleto. Se recomienda usar los módulos específicos en app/tasks/"
)

# Mantenemos get_business_unit por compatibilidad
from app.ats.tasks.utils import get_business_unit

# Definir __all__ para controlar qué se importa con 'from app.ats.tasks import *'
__all__ = [
    # Utilitarios
    'with_retry', 'add', 'get_business_unit',
    
    # Tareas de notificaciones
    'send_ntfy_notification', 'send_linkedin_login_link',
    'send_whatsapp_message_task', 'send_telegram_message_task', 'send_messenger_message_task',
    
    # Tareas de ML
    'train_ml_task', 'ejecutar_ml', 'train_matchmaking_model_task',
    'predict_top_candidates_task', 'sync_jobs_with_api',
    
    # Tareas de scraping
    'ejecutar_scraping', 'retrain_ml_scraper', 'verificar_dominios_scraping',
    'procesar_scraping_dominio', 'procesar_sublinks_task', 'execute_ml_and_scraping',
    'execute_email_scraper', 'process_cv_emails_task',
    
    # Tareas de onboarding
    'process_client_feedback_task', 'update_client_metrics_task',
    'generate_client_feedback_reports_task', 'process_onboarding_ml_data_task',
    'generate_employee_satisfaction_reports_task',
    
    # Tareas de reportes
    'generate_weekly_report_task', 'generate_scraping_efficiency_report_task',
    'generate_conversion_funnel_report_task'
]

# El decorador with_retry se ha movido a app.tasks.base

logger = logging.getLogger(__name__)


@shared_task
def add(x, y):
    return x + y

# =========================================================
# Tareas relacionadas con notificaciones
# =========================================================
# Función auxiliar para enviar notificaciones a ntfy.sh
def send_ntfy_notification(topic, message, image_url=None):
    """Envía una notificación a ntfy.sh si está habilitado, con soporte para imágenes."""
    if not settings.NTFY_ENABLED:
        logger.info("Notificaciones ntfy.sh desactivadas en settings.")
        return

    url = f'https://ntfy.sh/{topic}'  # Cambia a tu servidor auto-hospedado si aplica
    headers = {}
    data = message.encode('utf-8')

    # Autenticación: Priorizar token API si existe, sino usar usuario/contraseña
    if settings.NTFY_API_TOKEN:
        headers['Authorization'] = f'Bearer {settings.NTFY_API_TOKEN}'
    elif settings.NTFY_USERNAME and settings.NTFY_PASSWORD:
        headers['Authorization'] = f'Basic {requests.auth._basic_auth_str(settings.NTFY_USERNAME, settings.NTFY_PASSWORD)}'

    # Añadir imagen si se proporciona
    if image_url:
        headers['Attach'] = image_url  # URL de la imagen

    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            logger.info(f"Notificación enviada a {topic}: {message}" + (f" con imagen {image_url}" if image_url else ""))
        else:
            logger.error(f"Fallo al enviar notificación a {topic}: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error enviando notificación a {topic}: {str(e)}")

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='notifications')
@with_retry
def send_linkedin_login_link(self, recipient_email, business_unit_id=None):
    """Envía un enlace de inicio de sesión de LinkedIn y notifica a los administradores."""
    try:
        # Obtener la unidad de negocio (si aplica)
        business_unit = BusinessUnit.objects.get(id=business_unit_id) if business_unit_id else None
        bu_name = business_unit.name if business_unit else "Grupo huntRED®"

        # Obtener la URL de la imagen desde ConfiguracionBU
        image_url = None
        if business_unit:
            try:
                config_bu = business_unit.configuracionbu
                image_url = config_bu.logo_url if config_bu and config_bu.logo_url else "https://huntred.com/logo.png"
            except BusinessUnit.configuracionbu.RelatedObjectDoesNotExist:
                image_url = "https://huntred.com/logo.png"  # Valor por defecto si no hay ConfiguracionBU
        else:
            # Si no hay unidad de negocio, usar un logo por defecto
            image_url = "https://huntred.com/logo.png"

        # Contenido del correo
        subject = "Inicia sesión en LinkedIn con este enlace"
        body = (
            "Hemos enviado un enlace de inicio de sesión único a tu correo principal.\n\n"
            "Haz clic en el enlace para iniciar sesión en tu cuenta de LinkedIn al instante.\n\n"
            "¿Nuevo en LinkedIn? Únete ahora\n\n"
            "Al hacer clic en Continuar, aceptas el Acuerdo de usuario, la Política de privacidad "
            "y la Política de cookies de LinkedIn."
        )

        # Enviar el correo
        asyncio.run(send_email(
            business_unit_name=bu_name,
            subject=subject,
            destinatario=recipient_email,
            body=body
        ))
        logger.info(f"Correo con enlace enviado a {recipient_email} para {bu_name}")

        # Preparar mensaje de notificación
        timestamp = timezone.now().isoformat()
        notification_message = f"Enlace de inicio de sesión enviado a {recipient_email} a las {timestamp}"

        # Notificar al administrador de la unidad de negocio (si existe)
        if business_unit:
            bu_topic = business_unit.get_ntfy_topic()
            send_ntfy_notification(bu_topic, notification_message, image_url=image_url)

        # Notificar al administrador general
        config = Configuracion.objects.first()
        if config:
            general_topic = config.get_ntfy_topic()
            # Usar el logo por defecto para el administrador general si no se especifica otro
            send_ntfy_notification(general_topic, notification_message, image_url=image_url)

    except BusinessUnit.DoesNotExist:
        logger.error(f"Unidad de negocio con ID {business_unit_id} no encontrada.")
        self.retry(exc=Exception("Unidad de negocio no encontrada"))
    except Exception as e:
        logger.error(f"Error enviando enlace a {recipient_email}: {str(e)}")
        self.retry(exc=e)

def get_business_unit(business_unit_id=None, default_name="amigro"):
    if business_unit_id:
        return BusinessUnit.objects.filter(id=business_unit_id).first()
    return BusinessUnit.objects.filter(name=default_name).first()

@shared_task(bind=True, max_retries=5, default_retry_delay=40, queue='notifications')
@with_retry
def send_whatsapp_message_task(self, recipient, message, business_unit_id=None):
    from app.models import BusinessUnit
    from app.ats.chatbot.integrations.services import send_message
    try:
        bu = BusinessUnit.objects.get(id=business_unit_id) if business_unit_id else BusinessUnit.objects.filter(name='amigro').first()
        asyncio.run(send_message('whatsapp', recipient, message, bu))
        logger.info(f"✅ Mensaje de WhatsApp enviado a {recipient}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a WhatsApp: {e}")
        self.retry(exc=e)


@shared_task(bind=True, max_retries=5, default_retry_delay=40, queue='notifications')
@with_retry
def send_telegram_message_task(self, chat_id, message, business_unit_id=None):
    from app.models import BusinessUnit
    from app.ats.chatbot.integrations.services import send_message
    try:
        business_unit = BusinessUnit.objects.get(id=business_unit_id) if business_unit_id else BusinessUnit.objects.filter(name='amigro').first()
        asyncio.run(send_message('telegram', chat_id, message, business_unit))
        logger.info(f"✅ Mensaje de Telegram enviado a {chat_id}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Telegram: {e}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=5, default_retry_delay=40, queue='notifications')
@with_retry
def send_messenger_message_task(self, recipient_id, message, business_unit_id=None):
    from app.models import BusinessUnit
    from app.ats.chatbot.integrations.services import send_message
    try:
        business_unit = BusinessUnit.objects.get(id=business_unit_id) if business_unit_id else BusinessUnit.objects.filter(name='amigro').first()
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
    from app.models import BusinessUnit
    from app.ml.core.models.base import GrupohuntREDMLPipeline
    from app.ml.core.optimizers.PerformanceOptimizer import TensorFlowConfigurator
    import pandas as pd
    try:
        if not TensorFlowConfigurator.check_system_load(threshold=70):
            logger.info("Carga del sistema alta. Reintentando en 10 minutos.")
            raise self.retry(countdown=600)
        TensorFlowConfigurator.configure_tensorflow_based_on_load()
        logger.info("🧠 Iniciando tarea de entrenamiento de Machine Learning.")
        if business_unit_id:
            business_units = BusinessUnit.objects.filter(id=business_unit_id)
        else:
            business_units = BusinessUnit.objects.all()
        for bu in business_units:
            logger.info(f"📊 Entrenando modelo para BU: {bu.name}")
            pipeline = GrupohuntREDMLPipeline(business_unit=bu.name)
            try:
                df = pd.read_csv('/home/pablo/app/model/training_data.csv')
                X_train, X_test, y_train, y_test = pipeline.preprocess_data(df)
                pipeline.build_model(input_dim=X_train.shape[1])
                pipeline.train_model(X_train, y_train, X_test, y_test)
                logger.info(f"✅ Modelo entrenado y guardado para {bu.name}")
            except Exception as e:
                logger.error(f"❌ Error entrenando modelo para BU {bu.name}: {e}")
                continue
        logger.info("🚀 Tarea de entrenamiento completada para todas las Business Units.")
    except Exception as e:
        logger.error(f"❌ Error en la tarea de entrenamiento de ML: {e}")
        self.retry(exc=e)
        
@shared_task(bind=True, max_retries=3, default_retry_delay=120, queue='ml')
def ejecutar_ml(self):
    """
    Tarea para entrenar y evaluar el modelo de Machine Learning para cada Business Unit.
    """
    from app.ml.core.models.base import GrupohuntREDMLPipeline
    from app.models import BusinessUnit
    import pandas as pd
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


@shared_task
def sync_jobs_with_api():
    logger.info(f"[{datetime.now().isoformat()}] Ejecutando tarea programada: sync_jobs_with_api")
    business_units = BusinessUnit.objects.prefetch_related('configuracionbu_set').all()
    for bu in business_units:
        try:
            configuracion = ConfiguracionBU.objects.get(business_unit=bu)
            api_url = configuracion.dominio_rest_api or f"https://{configuracion.dominio_bu}/wp-json/wp/v2/job-listings"
            headers = {
                "Authorization": f"Bearer {configuracion.jwt_token}",
                "Content-Type": "application/json"
            }
            with aiohttp.ClientSession() as session:
                response = async_to_sync(session.get)(api_url, headers=headers)
                if response.status != 200:
                    logger.error(f"Error al consultar API para {bu.name}: {response.status}")
                    continue
                api_jobs = response.json()
            local_jobs = Vacante.objects.filter(business_unit=bu)
            local_job_urls = {job.url_original: job for job in local_jobs if job.url_original}
            for api_job in api_jobs:
                job_url = api_job.get("link")
                if job_url in local_job_urls:
                    local_job = local_job_urls[job_url]
                    local_job.titulo = api_job["title"]["rendered"]
                    local_job.descripcion = api_job["content"]["rendered"]
                    local_job.save()
                    logger.info(f"Vacante actualizada para {bu.name}: {local_job.titulo}")
                else:
                    manager = VacanteManager({
                        "business_unit": bu,
                        "job_title": api_job["title"]["rendered"],
                        "job_description": api_job["content"]["rendered"],
                        "company_name": api_job.get("meta", {}).get("_company_name", "Unknown"),
                        "job_link": job_url
                    })
                    manager.initialize()
                    manager.create_job_listing()
                    logger.info(f"Vacante creada para {bu.name}: {api_job['title']['rendered']}")
        except Exception as e:
            logger.error(f"Error sincronizando vacantes para {bu.name}: {e}", exc_info=True)
            continue
    logger.info("Sincronización de vacantes completada para todas las unidades de negocio.")

# =========================================================
# Tareas relacionadas con el scraping programado
# =========================================================
@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def process_cv_emails_task(self, business_unit_id):
    try:
        # Retrieve the BusinessUnit instance
        business_unit = BusinessUnit.objects.get(id=business_unit_id)
        # Initialize the IMAPCVProcessor with the business unit
        processor = IMAPCVProcessor(business_unit)
        # Run the asynchronous process_emails() method using asyncio.run()
        asyncio.run(processor.process_emails())
        # Log success
        logger.info(f"✅ CV email processing completed for {business_unit.name}")
    except Exception as e:
        # Log the error and retry the task if it fails
        logger.error(f"❌ Error in CV email processing: {e}")
        self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def ejecutar_scraping(self, dominio_id=None):
    """
    Ejecuta el scraping para todos los dominios o un dominio específico.
    """
    async def run_scraping():
        ml_scraper = MLScraper()
        pipeline = ScrapingPipeline()
        metrics = ScrapingMetrics("web_scraper")

        if dominio_id:
            dominio = await sync_to_async(DominioScraping.objects.get)(pk=dominio_id)
            dominios = [dominio]
        else:
            dominios = await sync_to_async(list)(DominioScraping.objects.filter(verificado=True, activo=True))

        tasks = []
        for dominio in dominios:
            logger.info(f"🔍 Preparando scraping para {dominio.empresa} ({dominio.dominio})")
            registro = await sync_to_async(RegistroScraping.objects.create)(
                dominio=dominio, estado='parcial', fecha_inicio=timezone.now()
            )
            scraper = await get_scraper(dominio, ml_scraper)
            tasks.append(process_domain(scraper, dominio, registro, pipeline))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = 0
        failed = 0
        total_vacancies = 0
        feedback_tasks = []
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Error en un dominio: {str(result)}")
                failed += 1
            else:
                dominio, jobs = result
                successful += 1
                total_vacancies += len(jobs)
                # Preparar tareas de retroalimentación asíncronas
                for job in jobs:
                    async def log_feedback_for_job(job_url):
                        vacante = await sync_to_async(Vacante.objects.filter(url_original=job_url).first)()
                        if vacante:
                            await ml_scraper.log_feedback(
                                vacante_id=vacante.id,
                                success=True,
                                corrections={}
                            )
                    feedback_tasks.append(log_feedback_for_job(job["url_original"]))
                logger.info(f"✅ Completado para {dominio.empresa}: {len(jobs)} vacantes")

        # Ejecutar tareas de retroalimentación
        if feedback_tasks:
            await asyncio.gather(*feedback_tasks, return_exceptions=True)
            logger.info("✅ Retroalimentación registrada para todas las vacantes")

        return {
            "status": "success",
            "successful_domains": successful,
            "failed_domains": failed,
            "total_vacancies": total_vacancies
        }

    try:
        logger.info("🚀 Iniciando tarea de scraping para dominios")
        result = asyncio.run(run_scraping())
        logger.info(f"🏁 Scraping finalizado: {result['successful_domains']} dominios exitosos, {result['failed_domains']} fallidos, {result['total_vacancies']} vacantes")
        return result
    except Exception as e:
        logger.error(f"❌ Error general en ejecutar_scraping: {e}", exc_info=True)
        self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=120, queue='ml')
def retrain_ml_scraper(self):
    """
    Reentrena el modelo MLScraper con los datos acumulados.
    """
    try:
        ml_scraper = MLScraper()
        training_data = []
        with open(ml_scraper.training_data_path, "r") as f:
            for line in f:
                try:
                    training_data.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    logger.warning(f"Línea inválida en datos de entrenamiento: {line}")
                    continue
        
        if not training_data:
            logger.warning("No hay datos de entrenamiento disponibles")
            return {"status": "error", "message": "No training data"}

        ml_scraper.retrain(training_data)
        logger.info("✅ MLScraper reentrenado con éxito")
        return {"status": "success", "message": f"Reentrenado con {len(training_data)} ejemplos"}
    except Exception as e:
        logger.error(f"❌ Error reentrenando MLScraper: {e}")
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
        ml_scraper = MLScraper()
        results = asyncio.run(scrape_and_publish(dominios))
        
        # Registrar retroalimentación
        feedback_tasks = []
        for domain, jobs in results:
            if jobs:
                for job in jobs:
                    async def log_feedback_for_job(job_url):
                        vacante = await sync_to_async(Vacante.objects.filter(url_original=job_url).first)()
                        if vacante:
                            await ml_scraper.log_feedback(
                                vacante_id=vacante.id,
                                success=True,
                                corrections={}
                            )
                    feedback_tasks.append(log_feedback_for_job(job["url_original"]))
        
        if feedback_tasks:
            asyncio.run(asyncio.gather(*feedback_tasks, return_exceptions=True))
            logger.info("✅ Retroalimentación registrada para todas las vacantes")

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

        # 4. Reentrenar MLScraper
        logger.info("🧠 Reentrenando MLScraper...")
        retrain_ml_scraper.delay()

        logger.info("✨ Proceso de ML y scraping finalizado con éxito.")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"❌ Error en el proceso ML + scraping: {e}")
        self.retry(exc=e)

# =========================================================
# Tareas de Notificaciones
# =========================================================

# =========================================================
# Tareas de Onboarding y Satisfacción
# =========================================================

@shared_task(bind=True, max_retries=3)
def send_satisfaction_survey_task(self, onboarding_id, period):
    """
    Envía una encuesta de satisfacción a un candidato para un período específico.
    
    Args:
        onboarding_id (int): ID del proceso de onboarding
        period (int): Período de días desde contratación (3, 7, 15, 30, 60, 90, 180, 365)
    """
    from app.models import OnboardingProcess
    from app.ats.onboarding.onboarding_controller import OnboardingController
    from app.ats.integrations.notifications.process.onboarding_notifications import OnboardingNotificationService
    
    try:
        # Obtener proceso de onboarding
        process = OnboardingProcess.objects.get(id=onboarding_id)
        
        # Verificar si ya se ha enviado para este período
        if str(period) in process.survey_responses:
            logger.info(f"Encuesta para período {period} ya fue respondida en proceso {onboarding_id}")
            return f"Encuesta ya respondida para período {period}"
        
        # Generar enlace seguro
        survey_url = asyncio.run(OnboardingController.generate_secure_survey_link(onboarding_id, period))
        if not survey_url:
            raise ValueError(f"No se pudo generar el enlace para la encuesta ID: {onboarding_id}, período: {period}")
        
        # Preparar mensaje
        person = process.person
        vacancy = process.vacancy
        company_name = vacancy.empresa.name if hasattr(vacancy, 'empresa') and vacancy.empresa else "la empresa"
        
        message = f"👋 Hola {person.first_name},\n\n"
        message += f"Han pasado {period} días desde tu incorporación a {company_name} y nos gustaría conocer tu experiencia.\n\n"
        message += f"📝 Por favor, completa esta breve encuesta de satisfacción: {survey_url}\n\n"
        message += "Tu opinión es muy importante para nosotros.\n\n"
        
        # Enviar notificación usando el servicio específico
        notification_service = OnboardingNotificationService()
        result = asyncio.run(notification_service.notify_satisfaction_survey(
            onboarding_id=onboarding_id,
            period=period
        ))
        
        if not result.get('success'):
            raise ValueError(f"Error enviando notificación: {result.get('error')}")
        
        return f"Encuesta enviada correctamente para período {period}"
        
    except Exception as e:
        logger.error(f"Error enviando encuesta de satisfacción: {str(e)}")
        if self.request.retries < self.max_retries:
            countdown = 5 * 60 * (5 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        return f"Error: {str(e)}"

@shared_task(bind=True)
def check_satisfaction_surveys_task(self):
    """
    Revisa los procesos de onboarding activos y programa encuestas de satisfacción
    según los períodos definidos (3, 7, 15, 30, 60, 90, 180, 365 días).
    """
    from app.models import OnboardingProcess, SATISFACTION_PERIODS
    from django.db.models import Q
    
    try:
        today = timezone.now().date()
        count = 0
        
        # Obtener procesos activos
        active_processes = OnboardingProcess.objects.filter(
            Q(status='IN_PROGRESS') | Q(status='COMPLETED')
        )
        
        for process in active_processes:
            hire_date = process.hire_date.date()
            surveys_status = process.get_surveys_status()
            
            for period in SATISFACTION_PERIODS:
                target_date = hire_date + timedelta(days=period)
                
                # Si hoy es el día para enviar y no se ha enviado
                if today == target_date and surveys_status.get(period, {}).get('status') == 'SCHEDULED':
                    # Programar tarea para enviar encuesta
                    send_satisfaction_survey_task.delay(process.id, period)
                    count += 1
                    logger.info(f"Programada encuesta para onboarding {process.id}, período {period}")
        
        return f"Programadas {count} encuestas de satisfacción"
    
    except Exception as e:
        logger.error(f"Error verificando encuestas de satisfacción: {str(e)}")
        return f"Error: {str(e)}"

@shared_task(bind=True)
def generate_client_satisfaction_reports_task(self):
    """
    Genera reportes mensuales de satisfacción para clientes con procesos de onboarding activos.
    """
    from app.models import OnboardingProcess, BusinessUnit
    from app.ats.onboarding.onboarding_controller import OnboardingController
    
    try:
        # Obtener todas las Business Units activas
        business_units = BusinessUnit.objects.filter(is_active=True)
        reports_generated = 0
        
        for bu in business_units:
            # Obtener procesos activos de la BU
            active_processes = OnboardingProcess.objects.filter(
                vacancy__business_unit=bu,
                status__in=['IN_PROGRESS', 'COMPLETED']
            )
            
            if not active_processes.exists():
                continue
            
            # Generar reporte para cada proceso
            for process in active_processes:
                report = asyncio.run(OnboardingController.generate_satisfaction_report(process.id))
                
                if report.get('success'):
                    reports_generated += 1
                    logger.info(f"Generado reporte para onboarding {process.id} en BU {bu.name}")
        
        return f"Generados {reports_generated} reportes de satisfacción de clientes"
        
    except Exception as e:
        logger.error(f"Error generando reportes de satisfacción de clientes: {str(e)}")
        return f"Error: {str(e)}"

@shared_task(bind=True)
def process_onboarding_ml_data_task(self):
    """
    Procesa datos de onboarding para actualizar modelos predictivos de satisfacción y retención.
    """
    from app.ml.onboarding_processor import OnboardingMLProcessor
    from app.models import OnboardingProcess
    
    try:
        # Obtener todos los procesos de onboarding
        processes = OnboardingProcess.objects.all()
        
        # Procesar datos para ML
        ml_processor = OnboardingMLProcessor()
        results = asyncio.run(ml_processor.process_onboarding_data(processes))
        
        return f"Procesados {len(processes)} procesos de onboarding para ML"
        
    except Exception as e:
        logger.error(f"Error procesando datos de onboarding para ML: {str(e)}")
        return f"Error: {str(e)}"

# =========================================================
# Tareas de Notificaciones de Ofertas
# =========================================================

@shared_task(bind=True, max_retries=3)
def send_offer_notification_task(self, offer_id, notification_type):
    """
    Envía notificaciones relacionadas con ofertas.
    
    Args:
        offer_id (int): ID de la oferta
        notification_type (str): Tipo de notificación ('created', 'accepted', 'declined')
    """
    from app.models import Offer
    from app.ats.integrations.notifications.process.offer_notifications import OfferNotificationService
    
    try:
        offer = Offer.objects.get(id=offer_id)
        notification_service = OfferNotificationService(offer.business_unit)
        
        if notification_type == 'created':
            result = asyncio.run(notification_service.notify_offer_made(
                person=offer.candidate,
                vacancy=offer.vacancy,
                offer_details=offer.details,
                deadline=offer.expiration_date
            ))
        elif notification_type == 'accepted':
            result = asyncio.run(notification_service.notify_offer_accepted(
                person=offer.candidate,
                vacancy=offer.vacancy,
                acceptance_date=timezone.now()
            ))
        elif notification_type == 'declined':
            result = asyncio.run(notification_service.notify_offer_declined(
                person=offer.candidate,
                vacancy=offer.vacancy,
                reason=offer.decline_reason
            ))
        else:
            raise ValueError(f"Tipo de notificación no válido: {notification_type}")
            
        if not result:
            raise ValueError("Error enviando notificación de oferta")
            
        return f"Notificación de oferta enviada correctamente: {notification_type}"
        
    except Exception as e:
        logger.error(f"Error enviando notificación de oferta: {str(e)}")
        if self.request.retries < self.max_retries:
            countdown = 5 * 60 * (5 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        return f"Error: {str(e)}"

# =========================================================
# Tareas de Notificaciones de Entrevistas
# =========================================================

@shared_task(bind=True, max_retries=3)
def send_interview_notification_task(self, interview_id, notification_type):
    """
    Envía notificaciones relacionadas con entrevistas.
    
    Args:
        interview_id (int): ID de la entrevista
        notification_type (str): Tipo de notificación ('scheduled', 'reminder', 'cancelled', 'location_update', 'delay')
    """
    from app.models import Interview
    from app.ats.integrations.notifications.process.interview_notifications import InterviewNotificationService
    
    try:
        interview = Interview.objects.get(id=interview_id)
        notification_service = InterviewNotificationService(interview.business_unit)
        
        if notification_type == 'scheduled':
            result = asyncio.run(notification_service.notify_interview_scheduled(
                interview=interview,
                candidate=interview.candidate,
                consultant=interview.consultant
            ))
        elif notification_type == 'reminder':
            result = asyncio.run(notification_service.notify_interview_reminder(
                interview=interview,
                candidate=interview.candidate,
                consultant=interview.consultant
            ))
        elif notification_type == 'cancelled':
            result = asyncio.run(notification_service.notify_interview_cancelled(
                interview=interview,
                candidate=interview.candidate,
                consultant=interview.consultant,
                reason=interview.cancellation_reason
            ))
        elif notification_type == 'location_update':
            result = asyncio.run(notification_service.notify_candidate_location_update(
                person=interview.candidate,
                vacancy=interview.vacancy,
                interview_date=interview.interview_date,
                location=interview.current_location,
                status=interview.location_status,
                estimated_arrival=interview.estimated_arrival
            ))
        elif notification_type == 'delay':
            result = asyncio.run(notification_service.notify_interview_delay(
                person=interview.candidate,
                vacancy=interview.vacancy,
                interview_date=interview.interview_date,
                delay_minutes=interview.delay_minutes,
                reason=interview.delay_reason
            ))
        else:
            raise ValueError(f"Tipo de notificación no válido: {notification_type}")
            
        if not result:
            raise ValueError("Error enviando notificación de entrevista")
            
        return f"Notificación de entrevista enviada correctamente: {notification_type}"
        
    except Exception as e:
        logger.error(f"Error enviando notificación de entrevista: {str(e)}")
        if self.request.retries < self.max_retries:
            countdown = 5 * 60 * (5 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        return f"Error: {str(e)}"

@shared_task(bind=True)
async def track_candidate_location_task(self, interview_id):
    """
    Rastrea la ubicación del candidato antes de la entrevista.
    
    Args:
        interview_id (int): ID de la entrevista
    """
    from app.models import Interview
    from app.ats.integrations.notifications.process.interview_notifications import InterviewNotificationService
    from app.ats.utils.location_tracker import LocationTracker
    
    try:
        interview = Interview.objects.get(id=interview_id)
        location_tracker = LocationTracker()
        notification_service = InterviewNotificationService(interview.business_unit)
        
        # Obtener ubicación actual
        current_location = await location_tracker.get_current_location(interview.candidate)
        
        # Calcular distancia y tiempo estimado
        distance = await location_tracker.calculate_distance(
            current_location,
            interview.location
        )
        
        # Determinar estado
        if distance < 1:  # Menos de 1 km
            status = 'cerca'
        elif distance < 5:  # Menos de 5 km
            status = 'en_traslado'
        else:
            status = 'llegando_tarde'
            
        # Calcular tiempo estimado de llegada
        estimated_arrival = await location_tracker.estimate_arrival_time(
            current_location,
            interview.location,
            interview.interview_date
        )
        
        # Actualizar estado en la entrevista
        interview.current_location = current_location
        interview.location_status = status
        interview.estimated_arrival = estimated_arrival
        await interview.asave()
        
        # Enviar notificación
        result = await notification_service.notify_candidate_location_update(
            person=interview.candidate,
            vacancy=interview.vacancy,
            interview_date=interview.interview_date,
            location=current_location,
            status=status,
            estimated_arrival=estimated_arrival
        )
        
        if not result:
            raise ValueError("Error enviando notificación de ubicación")
            
        return f"Ubicación del candidato actualizada: {status}"
        
    except Exception as e:
        logger.error(f"Error rastreando ubicación del candidato: {str(e)}")
        return f"Error: {str(e)}"

@shared_task(bind=True)
async def check_interview_delays_task(self):
    """
    Verifica retrasos en entrevistas programadas.
    """
    from app.models import Interview
    from app.ats.integrations.notifications.process.interview_notifications import InterviewNotificationService
    from django.utils import timezone
    
    try:
        now = timezone.now()
        upcoming_interviews = await Interview.objects.filter(
            interview_date__gt=now,
            interview_date__lte=now + timezone.timedelta(hours=1),
            status='scheduled'
        ).aiterator()
        
        async for interview in upcoming_interviews:
            # Verificar si el candidato está en camino
            if interview.location_status == 'en_traslado':
                # Calcular tiempo estimado de llegada
                estimated_arrival = interview.estimated_arrival
                if estimated_arrival and estimated_arrival > interview.interview_date:
                    # Calcular minutos de retraso
                    delay_minutes = int((estimated_arrival - interview.interview_date).total_seconds() / 60)
                    
                    # Actualizar estado
                    interview.delay_minutes = delay_minutes
                    interview.delay_reason = "Tráfico o distancia"
                    await interview.asave()
                    
                    # Enviar notificación
                    notification_service = InterviewNotificationService(interview.business_unit)
                    result = await notification_service.notify_interview_delay(
                        person=interview.candidate,
                        vacancy=interview.vacancy,
                        interview_date=interview.interview_date,
                        delay_minutes=delay_minutes,
                        reason=interview.delay_reason
                    )
                    
                    if not result:
                        logger.error(f"Error notificando retraso para entrevista {interview.id}")
        
        return "Verificación de retrasos completada"
        
    except Exception as e:
        logger.error(f"Error verificando retrasos: {str(e)}")
        return f"Error: {str(e)}"

# =========================================================
# Tareas de Notificaciones de Propuestas
# =========================================================

@shared_task(bind=True, max_retries=3)
def send_proposal_notification_task(self, proposal_id):
    """
    Envía notificaciones relacionadas con propuestas.
    
    Args:
        proposal_id (int): ID de la propuesta
    """
    from app.models import Proposal
    from app.ats.integrations.notifications.process.proposal_notifications import ProposalNotificationService
    
    try:
        proposal = Proposal.objects.get(id=proposal_id)
        notification_service = ProposalNotificationService(proposal.business_unit)
        
        result = asyncio.run(notification_service.notify_proposal_created(
            proposal=proposal,
            client=proposal.client,
            consultant=proposal.consultant
        ))
            
        if not result:
            raise ValueError("Error enviando notificación de propuesta")
            
        return "Notificación de propuesta enviada correctamente"
        
    except Exception as e:
        logger.error(f"Error enviando notificación de propuesta: {str(e)}")
        if self.request.retries < self.max_retries:
            countdown = 5 * 60 * (5 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        return f"Error: {str(e)}"

# =========================================================
# Tareas para obtención de oportunidades, scraping, 
# =========================================================

@shared_task(name="tasks.execute_email_scraper")
def execute_email_scraper(dominio_id=None, batch_size=10):
    """
    Ejecuta la extracción de vacantes desde correos electrónicos, opcionalmente para un dominio específico.
    
    Args:
        dominio_id (int, optional): ID del dominio específico para filtrar correos (si aplica).
        batch_size (int): Número de correos a procesar por lote.
    
    Returns:
        dict: Resultado de la ejecución con estadísticas.
    """
    try:
        # Obtener credenciales desde el entorno
        EMAIL_ACCOUNT = os.environ.get("EMAIL_ACCOUNT", "pablo@huntred.com")
        EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "Natalia&Patricio1113!")

        # Instanciar el scraper
        scraper = EmailScraperV2(EMAIL_ACCOUNT, EMAIL_PASSWORD)

        if dominio_id:
            dominio = DominioScraping.objects.get(id=dominio_id)
            logger.info(f"🚀 Ejecutando email scraper para {dominio.dominio} con batch_size={batch_size}...")
            # Nota: Actualmente EmailScraperV2 no filtra por dominio_id, pero lo dejamos preparado
        else:
            logger.info(f"🚀 Ejecutando email scraper para todos los correos con batch_size={batch_size}...")

        # Ejecutar el scraper de manera asíncrona
        asyncio.run(scraper.process_all_emails(batch_size=batch_size))

        # Retornar estadísticas
        result = {
            "status": "success",
            "correos_procesados": scraper.stats["correos_procesados"],
            "correos_exitosos": scraper.stats["correos_exitosos"],
            "correos_error": scraper.stats["correos_error"],
            "vacantes_extraidas": scraper.stats["vacantes_extraidas"],
            "vacantes_guardadas": scraper.stats["vacantes_guardadas"]
        }
        logger.info(f"✅ Email scraper ejecutado: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Error en email_scraper: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

# =========================================================
# Tareas de mantenimiento
# =========================================================

@shared_task(bind=True, max_retries=3, queue='maintenance')
@with_retry
def cleanup_old_logs(self, days: int = 30):
    """
    Limpia logs antiguos
    
    Args:
        days: Días a mantener
    """
    try:
        from app.ats.utils.logging import cleanup_old_log_files
        cleanup_old_log_files(days)
        logger.info(f"Logs más antiguos de {days} días limpiados")
    except Exception as e:
        logger.error(f"Error limpiando logs: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, queue='maintenance')
@with_retry
def cleanup_temp_files(self):
    """
    Limpia archivos temporales
    """
    try:
        import os
        import glob
        from django.conf import settings
        
        # Limpiar archivos temporales
        temp_dir = getattr(settings, 'TEMP_DIR', '/tmp')
        pattern = os.path.join(temp_dir, 'huntred_*')
        
        for file in glob.glob(pattern):
            try:
                if os.path.isfile(file):
                    os.remove(file)
            except Exception as e:
                logger.error(f"Error eliminando archivo temporal {file}: {str(e)}")
                
        logger.info("Archivos temporales limpiados")
    except Exception as e:
        logger.error(f"Error limpiando archivos temporales: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, queue='maintenance')
@with_retry
def cleanup_old_cache(self):
    """
    Limpia caché antigua
    """
    try:
        from django.core.cache import cache
        from django.conf import settings
        
        # Obtener todas las claves de caché
        keys = cache.keys('*')
        
        # Eliminar claves antiguas
        for key in keys:
            try:
                if not key.startswith(('system_stats', 'task_stats')):
                    cache.delete(key)
            except Exception as e:
                logger.error(f"Error eliminando clave de caché {key}: {str(e)}")
                
        logger.info("Caché antigua limpiada")
    except Exception as e:
        logger.error(f"Error limpiando caché: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, queue='maintenance')
@with_retry
def cleanup_old_data(self):
    """
    Limpia datos antiguos de la base de datos
    """
    try:
        from app.models import (
            GamificationEvent, UserBadge, UserChallenge,
            ChatState, Notification
        )
        from django.utils import timezone
        from datetime import timedelta
        
        # Fecha límite
        limit_date = timezone.now() - timedelta(days=90)
        
        # Limpiar eventos de gamificación antiguos
        GamificationEvent.objects.filter(created_at__lt=limit_date).delete()
        
        # Limpiar estados de chat antiguos
        ChatState.objects.filter(updated_at__lt=limit_date).delete()
        
        # Limpiar notificaciones antiguas
        Notification.objects.filter(created_at__lt=limit_date).delete()
        
        logger.info("Datos antiguos limpiados")
    except Exception as e:
        logger.error(f"Error limpiando datos antiguos: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, queue='maintenance')
@with_retry
def run_maintenance_tasks(self):
    """
    Ejecuta todas las tareas de mantenimiento
    """
    try:
        # Programar tareas de mantenimiento
        cleanup_old_logs.delay(days=30)
        cleanup_temp_files.delay()
        cleanup_old_cache.delay()
        cleanup_old_data.delay()
        
        logger.info("Tareas de mantenimiento programadas")
    except Exception as e:
        logger.error(f"Error programando tareas de mantenimiento: {str(e)}")
        raise self.retry(exc=e)

# Tareas del módulo ATS
@shared_task(
    name='ats.process_message',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def process_message(self, conversation_id: int, content: str, channel: str) -> bool:
    """
    Procesa un mensaje recibido a través de cualquier canal.
    
    Args:
        conversation_id: ID de la conversación
        content: Contenido del mensaje
        channel: Canal de comunicación
        
    Returns:
        bool: True si el procesamiento fue exitoso
    """
    try:
        # Verificar configuración del canal
        channel_config = ATS_CONFIG['COMMUNICATION']['CHANNELS'].get(channel)
        if not channel_config or not channel_config['enabled']:
            logger.warning(f"Canal {channel} no configurado o deshabilitado")
            return False
        
        # Obtener conversación
        conversation = Conversation.objects.get(id=conversation_id)
        
        # Crear mensaje
        message = ChatMessage.objects.create(
            conversation=conversation,
            content=content,
            direction='in',
            status='received',
            channel=channel
        )
        
        # Actualizar estado de la conversación
        conversation.last_message = content
        conversation.last_message_at = message.created_at
        conversation.save()
        
        # Registrar métrica
        Metric.objects.create(
            name=f'messages_received_{channel}',
            value=1,
            metadata={
                'conversation_id': conversation_id,
                'channel': channel
            }
        )
        
        logger.info(f"Mensaje procesado exitosamente para conversación {conversation_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")
        self.retry(exc=e)

@shared_task(
    name='ats.send_notification',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_notification(
    self,
    recipient_id: int,
    notification_type: str,
    channel: str,
    content: str,
    metadata: dict = None
) -> bool:
    """
    Envía una notificación a través del canal especificado.
    
    Args:
        recipient_id: ID del destinatario
        notification_type: Tipo de notificación
        channel: Canal de comunicación
        content: Contenido de la notificación
        metadata: Metadatos adicionales
        
    Returns:
        bool: True si el envío fue exitoso
    """
    try:
        # Verificar configuración del canal
        channel_config = ATS_CONFIG['COMMUNICATION']['CHANNELS'].get(channel)
        if not channel_config or not channel_config['enabled']:
            logger.warning(f"Canal {channel} no configurado o deshabilitado")
            return False
        
        # Crear notificación
        notification = Notification.objects.create(
            recipient_id=recipient_id,
            type=notification_type,
            channel=channel,
            content=content,
            metadata=metadata or {},
            status='pending'
        )
        
        # Intentar envío
        success = True  # Aquí iría la lógica de envío real
        if success:
            notification.status = 'sent'
        else:
            notification.status = 'failed'
        notification.save()
        
        # Registrar métrica
        Metric.objects.create(
            name=f'notifications_{notification.status}',
            value=1,
            metadata={
                'type': notification_type,
                'channel': channel
            }
        )
        
        logger.info(f"Notificación {notification.id} procesada con estado: {notification.status}")
        return success
        
    except Exception as e:
        logger.error(f"Error enviando notificación: {str(e)}")
        self.retry(exc=e)

@shared_task(
    name='ats.update_workflow_state',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def update_workflow_state(
    self,
    conversation_id: int,
    new_state: str,
    workflow_type: str = 'candidate'
) -> bool:
    """
    Actualiza el estado del flujo de trabajo.
    
    Args:
        conversation_id: ID de la conversación
        new_state: Nuevo estado
        workflow_type: Tipo de flujo de trabajo ('candidate' o 'client')
        
    Returns:
        bool: True si la actualización fue exitosa
    """
    try:
        # Obtener configuración del flujo
        workflow_config = ATS_CONFIG['WORKFLOW'].get(workflow_type)
        if not workflow_config:
            logger.error(f"Tipo de flujo de trabajo no válido: {workflow_type}")
            return False
        
        # Validar estado
        if new_state not in workflow_config['states']:
            logger.error(f"Estado no válido para {workflow_type}: {new_state}")
            return False
        
        # Obtener estado actual
        current_state = WorkflowState.objects.filter(
            conversation_id=conversation_id
        ).order_by('-timestamp').first()
        
        # Validar transición
        if current_state:
            valid_transitions = workflow_config['transitions'].get(current_state.state, [])
            if new_state not in valid_transitions:
                logger.warning(
                    f"Transición no válida: {current_state.state} -> {new_state}"
                )
                return False
        
        # Crear nuevo estado
        WorkflowState.objects.create(
            conversation_id=conversation_id,
            state=new_state,
            workflow_type=workflow_type
        )
        
        # Registrar métrica
        Metric.objects.create(
            name='workflow_transitions',
            value=1,
            metadata={
                'workflow_type': workflow_type,
                'from_state': current_state.state if current_state else None,
                'to_state': new_state
            }
        )
        
        logger.info(
            f"Estado de flujo actualizado a {new_state} para conversación {conversation_id}"
        )
        return True
        
    except Exception as e:
        logger.error(f"Error actualizando estado de flujo: {str(e)}")
        self.retry(exc=e)

# Tareas de Analytics
@shared_task
def generate_conversion_report():
    """
    Genera el reporte de conversión de oportunidades.
    """
    analytics = AnalyticsEngine()
    report = analytics.generate_opportunity_conversion_report()
    
    # Almacenar en cache
    cache.set('conversion_report', json.dumps(report), timeout=3600)
    return report

@shared_task
def generate_industry_trends():
    """
    Genera las tendencias por industria.
    """
    analytics = AnalyticsEngine()
    report = analytics.generate_industry_trends()
    
    # Almacenar en cache
    cache.set('industry_trends', json.dumps(report), timeout=3600)
    return report

@shared_task
def generate_location_heatmap():
    """
    Genera el heatmap de ubicaciones.
    """
    analytics = AnalyticsEngine()
    report = analytics.generate_location_heatmap()
    
    # Almacenar en cache
    cache.set('location_heatmap', json.dumps(report), timeout=3600)
    return report

@shared_task
def predict_conversion(opportunity_data):
    """
    Predice la probabilidad de conversión de una oportunidad.
    
    Args:
        opportunity_data: Datos de la oportunidad
        
    Returns:
        dict: Resultado de la predicción
    """
    analytics = AnalyticsEngine()
    opportunity = Opportunity(**opportunity_data)
    probability = analytics.predict_conversion_probability(opportunity)
    
    return {
        'probability': probability,
        'recommendation': analytics._get_recommendation(probability)
    }

# Tareas de Onboarding
@shared_task(bind=True, max_retries=3)
def send_client_feedback_survey_task(self, feedback_id):
    """
    Envía una encuesta de satisfacción a un cliente.
    
    Args:
        feedback_id (int): ID del feedback a enviar
    """
    try:
        # Enviar encuesta
        result = asyncio.run(ClientFeedbackController.send_feedback_survey(feedback_id))
        
        if not result.get('success'):
            raise ValueError(f"Error enviando encuesta: {result.get('error')}")
        
        return f"Encuesta enviada correctamente: {feedback_id}"
        
    except Exception as e:
        logger.error(f"Error enviando encuesta a cliente: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)  # Reintentar en 5 minutos

@shared_task(bind=True)
def check_pending_client_feedback_task(self):
    """
    Verifica encuestas pendientes de envío según las programaciones.
    """
    try:
        # Verificar encuestas pendientes
        result = asyncio.run(ClientFeedbackController.check_pending_feedback())
        
        if not result.get('success'):
            raise ValueError(f"Error verificando encuestas pendientes: {result.get('error')}")
        
        # Programar envío de encuestas pendientes
        count = 0
        for feedback in result.get('pending_feedback', []):
            feedback_id = feedback.get('feedback_id')
            if feedback_id:
                send_client_feedback_survey_task.delay(feedback_id)
                count += 1
                logger.info(f"Programado envío de encuesta {feedback_id} a cliente {feedback.get('empresa_name')}")
        
        return f"Programado envío de {count} encuestas pendientes"
        
    except Exception as e:
        logger.error(f"Error verificando encuestas pendientes para clientes: {str(e)}")
        return f"Error: {str(e)}"

@shared_task(bind=True)
def generate_client_feedback_reports_task(self):
    """
    Genera reportes mensuales de satisfacción de clientes por Business Unit.
    """
    from app.models import BusinessUnit
    import os
    from django.conf import settings
    
    try:
        # Obtener todas las Business Units activas
        business_units = BusinessUnit.objects.filter(is_active=True)
        reports_generated = 0
        
        for bu in business_units:
            # Verificar si hay encuestas para esta BU
            feedback_count = ClientFeedback.objects.filter(
                business_unit=bu,
                status='COMPLETED'
            ).count()
            
            if feedback_count == 0:
                continue
            
            # Generar reporte para la BU
            report_data = asyncio.run(
                ClientFeedbackController.generate_bu_satisfaction_report(bu.id)
            )
            
            # Crear directorio si no existe
            reports_dir = os.path.join(settings.MEDIA_ROOT, 'client_feedback_reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            # Guardar reporte en formato HTML
            current_month = timezone.now().strftime('%B_%Y').lower()
            report_filename = f"{bu.code.lower()}_client_satisfaction_{current_month}.html"
            report_path = os.path.join(reports_dir, report_filename)
            
            # Renderizar HTML
            from django.template.loader import render_to_string
            context = {
                'report': report_data,
                'year': datetime.now().year,
                'logo_url': f"{settings.STATIC_URL}images/logo.png"
            }
            html_content = render_to_string('onboarding/client_satisfaction_report.html', context)
            
            # Guardar reporte
            with open(report_path, 'w') as f:
                f.write(html_content)
            
            reports_generated += 1
            logger.info(f"Generado reporte de satisfacción de clientes para BU {bu.name}: {report_path}")
        
        return f"Generados {reports_generated} reportes de satisfacción de clientes"
        
    except Exception as e:
        logger.error(f"Error generando reportes de satisfacción de clientes: {str(e)}")
        return f"Error: {str(e)}"

@shared_task(bind=True)
def analyze_client_feedback_trends_task(self):
    """
    Analiza tendencias en el feedback de clientes e identifica patrones.
    """
    from app.models import BusinessUnit
    from app.ml.onboarding_processor import OnboardingMLProcessor
    
    try:
        # Procesar datos de feedback para ML
        ml_processor = OnboardingMLProcessor()
        results = asyncio.run(ml_processor.analyze_client_feedback_trends())
        
        return f"Análisis de tendencias de feedback completado: {results}"
        
    except Exception as e:
        logger.error(f"Error analizando tendencias de feedback: {str(e)}")
        return f"Error: {str(e)}"

# Tareas de Proposals
@shared_task
def send_proposal_email(proposal_id):
    """
    Envía un correo electrónico con la propuesta adjunta.
    
    Args:
        proposal_id: ID de la propuesta
    """
    proposal = Proposal.objects.get(id=proposal_id)
    
    # Construir el mensaje
    subject = f"Propuesta de Servicios - {proposal.company.name}"
    message = f"Estimado(a) {proposal.company.name},\n\nAdjunto encontrará nuestra propuesta de servicios para las oportunidades identificadas.\n\nAtentamente,\nEl equipo de Grupo huntRED®"
    
    # Crear el email
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[proposal.company.email],
        cc=[settings.DEFAULT_FROM_EMAIL]
    )
    
    # Adjuntar el PDF de la propuesta
    pdf_path = os.path.join(settings.MEDIA_ROOT, 'proposals', f"proposal_{proposal_id}.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            email.attach(f"proposal_{proposal_id}.pdf", f.read(), 'application/pdf')
    
    # Enviar el email
    email.send()
    
    # Notificar al equipo
    notification_handler = NotificationHandler()
    message = f"Propuesta enviada a {proposal.company.name}"
    notification_handler.send_notification(
        recipient='pablo@huntred.com',
        message=message,
        subject='Propuesta Enviada'
    )

@shared_task
def generate_monthly_report():
    """
    Genera un reporte mensual de propuestas.
    """
    from datetime import datetime, timedelta
    from django.db.models import Count, Sum
    
    # Obtener fecha de inicio del mes
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Obtener estadísticas
    proposals = Proposal.objects.filter(
        created_at__gte=start_of_month
    ).aggregate(
        total_count=Count('id'),
        total_value=Sum('pricing_total')
    )
    
    # Notificar al equipo
    notification_handler = NotificationHandler()
    message = f"Reporte Mensual de Propuestas:\n\nTotal de Propuestas: {proposals['total_count']}\nValor Total: ${proposals['total_value']:.2f}"
    notification_handler.send_notification(
        recipient='pablo@huntred.com',
        message=message,
        subject='Reporte Mensual de Propuestas'
    )

# Tareas de Pagos
@shared_task
def sincronizar_opportunidad_task(opportunidad_id: int) -> Dict[str, Any]:
    """
    Tarea Celery para sincronizar una oportunidad con WordPress.
    
    Args:
        oportunidad_id: ID de la oportunidad a sincronizar
        
    Returns:
        Dict con el resultado de la sincronización
    """
    try:
        # Inicializar sincronizador
        sync = WordPressSync()
        sync.initialize()
        
        # Registrar inicio de sincronización
        log = SincronizacionLog.objects.create(
            oportunidad_id=oportunidad_id,
            estado='in_progress'
        )
        
        # Realizar sincronización
        result = sync.sincronizar_oportunidad(opportunidad_id)
        
        # Actualizar log de sincronización
        log.estado = 'completed'
        log.resultado = result
        log.save()
        
        return result
        
    except Exception as e:
        # Registrar error
        error = SincronizacionError.objects.create(
            oportunidad_id=oportunidad_id,
            mensaje=str(e),
            intento=log.intentos + 1
        )
        
        # Actualizar log de sincronización
        log.estado = 'failed'
        log.error = error
        log.save()
        raise

@shared_task
def sincronizar_empresa_task(empresa_id: int) -> Dict[str, Any]:
    """
    Tarea Celery para sincronizar una empresa con WordPress.
    
    Args:
        empresa_id: ID de la empresa a sincronizar
        
    Returns:
        Dict con el resultado de la sincronización
    """
    try:
        # Inicializar sincronizador
        sync = WordPressSync()
        sync.initialize()
        
        # Obtener empresa
        empresa = Empleador.objects.get(id=empresa_id)
        
        # Realizar sincronización
        success, result = sync.sincronizar_empresa(empresa)
        
        # Registrar resultado
        if success:
            log = SincronizacionLog.objects.create(
                oportunidad_id=None,
                estado='completed',
                detalle={'empresa_id': empresa_id, 'resultado': result}
            )
        else:
            error = SincronizacionError.objects.create(
                oportunidad_id=None,
                mensaje=f"Error sincronizando empresa {empresa_id}: {result.get('error', 'Desconocido')}",
                intento=1
            )
            log = SincronizacionLog.objects.create(
                oportunidad_id=None,
                estado='failed',
                error=error
            )
        
        return {'success': success, 'result': result}
        
    except Exception as e:
        error = SincronizacionError.objects.create(
            oportunidad_id=None,
            mensaje=f"Error sincronizando empresa {empresa_id}: {str(e)}",
            intento=1
        )
        log = SincronizacionLog.objects.create(
            oportunidad_id=None,
            estado='failed',
            error=error
        )
        raise

@shared_task
def sincronizar_candidato_task(candidato_id: int) -> Dict[str, Any]:
    """
    Tarea Celery para sincronizar un candidato con WordPress.
    
    Args:
        candidato_id: ID del candidato a sincronizar
        
    Returns:
        Dict con el resultado de la sincronización
    """
    try:
        # Inicializar sincronizador
        sync = WordPressSync()
        sync.initialize()
        
        # Obtener candidato
        candidato = Candidato.objects.get(id=candidato_id)
        
        # Realizar sincronización
        success, result = sync.sincronizar_candidato(candidato)
        
        # Registrar resultado
        if success:
            log = SincronizacionLog.objects.create(
                oportunidad_id=None,
                estado='completed',
                detalle={'candidato_id': candidato_id, 'resultado': result}
            )
        else:
            error = SincronizacionError.objects.create(
                oportunidad_id=None,
                mensaje=f"Error sincronizando candidato {candidato_id}: {result.get('error', 'Desconocido')}",
                intento=1
            )
            log = SincronizacionLog.objects.create(
                oportunidad_id=None,
                estado='failed',
                error=error
            )
        
        return {'success': success, 'result': result}
        
    except Exception as e:
        error = SincronizacionError.objects.create(
            oportunidad_id=None,
            mensaje=f"Error sincronizando candidato {candidato_id}: {str(e)}",
            intento=1
        )
        log = SincronizacionLog.objects.create(
            oportunidad_id=None,
            estado='failed',
            error=error
        )
        raise

@shared_task
def sincronizar_pricing_task(business_unit: str) -> Dict[str, Any]:
    """
    Tarea Celery para sincronizar la configuración de pricing para una Business Unit específica.
    
    Args:
        business_unit: Nombre de la Business Unit (huntRED, huntU, Amigro)
        
    Returns:
        Dict con estadísticas de la sincronización
    """
    try:
        # Inicializar sincronizador para la Business Unit específica
        sync = WordPressSync(business_unit)
        sync.initialize()
        
        # Obtener configuraciones de pricing
        pricing_config = {
            'baselines': PricingBaseline.objects.filter(bu=business_unit),
            'addons': Addons.objects.filter(bu=business_unit),
            'coupons': Coupons.objects.filter(bu=business_unit),
            'milestones': PaymentMilestones.objects.filter(bu=business_unit)
        }
        
        # Sincronizar cada tipo de configuración
        stats = {
            'baselines': sync.sincronizar_baselines(pricing_config['baselines']),
            'addons': sync.sincronizar_addons(pricing_config['addons']),
            'coupons': sync.sincronizar_coupons(pricing_config['coupons']),
            'milestones': sync.sincronizar_milestones(pricing_config['milestones'])
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error sincronizando pricing: {str(e)}")
        return {"status": "error", "message": str(e)}

# =========================================================
# Tareas de unidades de negocio
# =========================================================

@shared_task
def process_huntu_candidate(person_id: int):
    """
    Procesa un candidato de Huntu, generando contratos.
    
    Args:
        person_id: ID de la persona.
    """
    try:
        person = Person.objects.get(id=person_id)
        application = Application.objects.filter(user=person).first()
        if not application or not application.vacancy:
            return "Candidato sin vacante asignada."

        contract_path = generate_contract_pdf(person, None, application.vacancy.titulo, person.business_unit)
        request_digital_signature(
            user=person,
            document_path=contract_path,
            document_name=f"Carta Propuesta - {application.vacancy.titulo}.pdf"
        )
        return f"Contrato generado y enviado a {person.nombre}"
    except Person.DoesNotExist:
        logger.error(f"Candidato {person_id} no encontrado.")
        return "Candidato no encontrado."
    except Exception as e:
        logger.error(f"Error procesando candidato {person_id}: {e}", exc_info=True)
        return f"Error: {str(e)}"

@shared_task
def process_amigro_candidate(person_id: int):
    """
    Procesa un candidato de Amigro, generando contratos.
    
    Args:
        person_id: ID de la persona.
    """
    try:
        person = Person.objects.get(id=person_id)
        application = Application.objects.filter(user=person).first()
        if not application or not application.vacancy:
            return "Candidato sin vacante asignada."

        contract_path = generate_contract_pdf(person, None, application.vacancy.titulo, person.business_unit)
        request_digital_signature(
            user=person,
            document_path=contract_path,
            document_name=f"Carta Propuesta - {application.vacancy.titulo}.pdf"
        )
        return f"Contrato generado y enviado a {person.nombre}"
    except Person.DoesNotExist:
        logger.error(f"Candidato {person_id} no encontrado.")
        return "Candidato no encontrado."
    except Exception as e:
        logger.error(f"Error procesando candidato {person_id}: {e}", exc_info=True)
        return f"Error: {str(e)}"

# Tareas de Notificaciones
@shared_task
def process_notification_queue(limit=50):
    """
    Procesa la cola de notificaciones pendientes.
    
    Args:
        limit: Número máximo de notificaciones a procesar
    """
    try:
        # Obtener notificaciones pendientes
        notifications = Notification.objects.filter(
            status='pending'
        ).order_by('created_at')[:limit]
        
        for notification in notifications:
            try:
                # Procesar notificación
                notification_handler = NotificationHandler()
                notification_handler.send_notification(
                    recipient=notification.recipient,
                    message=notification.message,
                    subject=notification.subject
                )
                
                # Actualizar estado
                notification.status = 'sent'
                notification.sent_at = timezone.now()
                notification.save()
                
            except Exception as e:
                logger.error(f"Error procesando notificación {notification.id}: {str(e)}")
                notification.status = 'failed'
                notification.error = str(e)
                notification.save()
                
    except Exception as e:
        logger.error(f"Error procesando cola de notificaciones: {str(e)}")

@shared_task
def send_scheduled_notification(notification_id):
    """
    Envía una notificación programada.
    
    Args:
        notification_id: ID de la notificación
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        
        # Verificar si es hora de enviar
        if notification.scheduled_at <= timezone.now():
            notification_handler = NotificationHandler()
            notification_handler.send_notification(
                recipient=notification.recipient,
                message=notification.message,
                subject=notification.subject
            )
            
            # Actualizar estado
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
    except Notification.DoesNotExist:
        logger.error(f"Notificación {notification_id} no encontrada")
    except Exception as e:
        logger.error(f"Error enviando notificación programada {notification_id}: {str(e)}")

@shared_task
def send_daily_status_reports():
    """
    Envía reportes diarios de estado.
    """
    try:
        # Obtener estadísticas
        stats = {
            'notifications': {
                'pending': Notification.objects.filter(status='pending').count(),
                'sent': Notification.objects.filter(status='sent').count(),
                'failed': Notification.objects.filter(status='failed').count()
            },
            'opportunities': {
                'active': Opportunity.objects.filter(status='active').count(),
                'completed': Opportunity.objects.filter(status='completed').count(),
                'cancelled': Opportunity.objects.filter(status='cancelled').count()
            },
            'candidates': {
                'active': Candidate.objects.filter(status='active').count(),
                'hired': Candidate.objects.filter(status='hired').count(),
                'rejected': Candidate.objects.filter(status='rejected').count()
            }
        }
        
        # Enviar reporte
        notification_handler = NotificationHandler()
        message = f"Reporte Diario de Estado:\n\nNotificaciones:\n- Pendientes: {stats['notifications']['pending']}\n- Enviadas: {stats['notifications']['sent']}\n- Fallidas: {stats['notifications']['failed']}\n\nOportunidades:\n- Activas: {stats['opportunities']['active']}\n- Completadas: {stats['opportunities']['completed']}\n- Canceladas: {stats['opportunities']['cancelled']}\n\nCandidatos:\n- Activos: {stats['candidates']['active']}\n- Contratados: {stats['candidates']['hired']}\n- Rechazados: {stats['candidates']['rejected']}"
        
        notification_handler.send_notification(
            recipient='pablo@huntred.com',
            message=message,
            subject='Reporte Diario de Estado'
        )
        
    except Exception as e:
        logger.error(f"Error enviando reporte diario: {str(e)}")

@shared_task
def send_payment_reminders():
    """
    Envía recordatorios de pago.
    """
    try:
        # Obtener pagos pendientes
        pending_payments = Payment.objects.filter(
            status='pending',
            due_date__lte=timezone.now() + timedelta(days=7)
        )
        
        for payment in pending_payments:
            try:
                # Enviar recordatorio
                notification_handler = NotificationHandler()
                message = f"Recordatorio de Pago:\n\nMonto: ${payment.amount}\nFecha de vencimiento: {payment.due_date.strftime('%d/%m/%Y')}\n\nPor favor, realice el pago lo antes posible."
                
                notification_handler.send_notification(
                    recipient=payment.company.email,
                    message=message,
                    subject='Recordatorio de Pago'
                )
                
                # Actualizar estado
                payment.reminder_sent = True
                payment.save()
                
            except Exception as e:
                logger.error(f"Error enviando recordatorio de pago {payment.id}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error procesando recordatorios de pago: {str(e)}")

@shared_task
def clean_old_notifications(days=90):
    """
    Limpia notificaciones antiguas.
    
    Args:
        days: Número de días a mantener en el historial
    """
    try:
        # Calcular fecha límite
        limit_date = timezone.now() - timedelta(days=days)
        
        # Eliminar notificaciones antiguas
        Notification.objects.filter(
            created_at__lt=limit_date,
            status__in=['sent', 'failed']
        ).delete()
        
    except Exception as e:
        logger.error(f"Error limpiando notificaciones antiguas: {str(e)}")

# Tareas de Mantenimiento
#// ... existing code ...

from app.ats.integrations.channels.linkedin.channel import LinkedInChannel
from datetime import datetime, timedelta
import re
from typing import Optional
import time
import random

def parse_linkedin_activity(activity_str: str) -> Optional[datetime]:
    """
    Parsea la cadena de actividad de LinkedIn a un objeto datetime.
    
    Args:
        activity_str: Cadena de actividad (ej: "Activo hace 2 meses")
        
    Returns:
        datetime o None si no se puede parsear
    """
    if not activity_str:
        return None
        
    # Patrones comunes de actividad
    patterns = {
        r'hace (\d+) hora': lambda x: timedelta(hours=int(x)),
        r'hace (\d+) día': lambda x: timedelta(days=int(x)),
        r'hace (\d+) semana': lambda x: timedelta(weeks=int(x)),
        r'hace (\d+) mes': lambda x: timedelta(days=int(x)*30),
        r'hace (\d+) año': lambda x: timedelta(days=int(x)*365)
    }
    
    for pattern, delta_func in patterns.items():
        match = re.search(pattern, activity_str.lower())
        if match:
            return datetime.now() - delta_func(match.group(1))
            
    return None

@shared_task
def send_linkedin_invitations():
    """
    Envía invitaciones de LinkedIn según la programación configurada.
    """
    from app.models import (
        LinkedInProfile, LinkedInMessageTemplate, 
        LinkedInInvitationSchedule, Application
    )
    from app.ats.integrations.ai.insights import generate_personalized_message
    from django.utils import timezone
    from datetime import timedelta
    import pytz
    
    # Obtener la hora actual en la zona horaria del servidor
    current_time = timezone.localtime(timezone.now()).time()
    
    # Obtener programaciones activas para la hora actual
    schedules = LinkedInInvitationSchedule.objects.filter(
        is_active=True,
        time_window_start__lte=current_time,
        time_window_end__gte=current_time
    ).order_by('priority')
    
    if not schedules.exists():
        logger.info("No hay programaciones activas para la hora actual")
        return
        
    # Obtener template de mensaje
    template = LinkedInMessageTemplate.objects.filter(is_active=True).first()
    if not template:
        logger.error("No hay template de mensaje activo para LinkedIn")
        return
        
    # Inicializar canal de LinkedIn
    channel = LinkedInChannel(cookies_path='linkedin_cookies.json')
    
    try:
        for schedule in schedules:
            # Verificar si se pueden enviar invitaciones hoy
            if not schedule.can_send_today():
                logger.info(
                    f"Programación {schedule.name} no puede enviar invitaciones hoy "
                    f"(límites alcanzados o día no permitido)"
                )
                continue
                
            logger.info(f"Procesando programación: {schedule.name}")
            
            # Obtener perfiles según el tipo de objetivo
            if schedule.target_type == 'ACTIVE_CANDIDATES':
                # Obtener perfiles de candidatos en procesos activos
                active_applications = Application.objects.filter(
                    status__in=['INTERVIEW', 'OFFER', 'NEGOTIATION']
                ).values_list('candidate__linkedin_profile', flat=True)
                
                profiles = LinkedInProfile.objects.filter(
                    id__in=active_applications,
                    is_connected=False
                )
            else:
                # Obtener perfiles generales inactivos
                profiles = LinkedInProfile.objects.filter(
                    is_connected=False,
                    last_invitation_sent__isnull=True
                )
                
            # Obtener información de perfiles
            profiles_with_info = []
            for profile in profiles[:schedule.max_invitations]:
                info = channel.get_profile_info(profile.profile_url)
                if info:
                    profiles_with_info.append((profile, info))
                    
            # Enviar invitaciones
            invitations_sent = 0
            for profile, info in profiles_with_info:
                # Verificar límites diarios y semanales
                if not schedule.can_send_today():
                    logger.info(
                        f"Límites alcanzados para la programación {schedule.name}. "
                        f"Enviadas {invitations_sent} invitaciones."
                    )
                    break
                    
                # Generar mensaje personalizado
                message = generate_personalized_message(info, template.template)
                
                success = channel.send_connection_request(
                    profile_url=profile.profile_url,
                    message=message
                )
                
                if success:
                    profile.last_invitation_sent = timezone.now()
                    profile.save()
                    invitations_sent += 1
                    
                    # Registrar el mensaje enviado
                    logger.info(
                        f"Mensaje enviado a {profile.name} "
                        f"(Programación: {schedule.name}):\n{message}"
                    )
                    
                # Esperar el delay configurado
                time.sleep(schedule.delay_between_invitations)
                
            logger.info(
                f"Programación {schedule.name} completada. "
                f"Enviadas {invitations_sent} invitaciones."
            )
                
    except Exception as e:
        logger.error(f"Error en tarea de invitaciones LinkedIn: {str(e)}")
        
    finally:
        channel.close()

from celery import shared_task
from celery.schedules import crontab
from app.celery import app
from app.tasks.linkedin import send_linkedin_invitations, cleanup_linkedin_invitations

# Configuración de tareas periódicas
app.conf.beat_schedule = {
    'send-linkedin-invitations': {
        'task': 'app.tasks.linkedin.send_linkedin_invitations',
        'schedule': crontab(hour='9,12,15,18', minute='0'),  # 4 veces al día
    },
    'cleanup-linkedin-invitations': {
        'task': 'app.tasks.linkedin.cleanup_linkedin_invitations',
        'schedule': crontab(hour=0, minute=0),  # Diario a medianoche
    },
    'enrich-linkedin-profiles': {
        'task': 'app.tasks.linkedin.enrich_linkedin_profiles',
        'schedule': crontab(hour='*/8'),  # Cada 8 horas
    },
    'process-linkedin-updates': {
        'task': 'app.tasks.linkedin.process_linkedin_updates',
        'schedule': crontab(hour='*/12'),  # Cada 12 horas
    },
    'cleanup-linkedin-data': {
        'task': 'app.tasks.linkedin.cleanup_linkedin_data',
        'schedule': crontab(hour=1, minute=0),  # Diario a la 1 AM
    },
}

# =========================================================
# Tareas de Seguimiento de Entrevistas
# =========================================================

from app.ats.services.interview_tracking_service import InterviewTrackingService

@shared_task
async def track_candidate_location_task(interview_id: int) -> None:
    """
    Tarea para actualizar la ubicación del candidato.
    
    Args:
        interview_id: ID de la entrevista
    """
    try:
        interview = await Interview.objects.aget(id=interview_id)
        tracking_service = InterviewTrackingService(interview.business_unit)
        await tracking_service.update_location(interview_id)
    except Exception as e:
        logger.error(f"Error en track_candidate_location_task: {str(e)}")

@shared_task
async def start_interview_tracking_task(interview_id: int) -> None:
    """
    Tarea para iniciar el tracking de una entrevista.
    
    Args:
        interview_id: ID de la entrevista
    """
    try:
        interview = await Interview.objects.aget(id=interview_id)
        tracking_service = InterviewTrackingService(interview.business_unit)
        await tracking_service.start_tracking(interview_id)
    except Exception as e:
        logger.error(f"Error en start_interview_tracking_task: {str(e)}")

@shared_task
async def stop_interview_tracking_task(interview_id: int) -> None:
    """
    Tarea para detener el tracking de una entrevista.
    
    Args:
        interview_id: ID de la entrevista
    """
    try:
        interview = await Interview.objects.aget(id=interview_id)
        tracking_service = InterviewTrackingService(interview.business_unit)
        await tracking_service.stop_tracking(interview_id)
    except Exception as e:
        logger.error(f"Error en stop_interview_tracking_task: {str(e)}")

@shared_task
async def schedule_interview_tracking_task(interview_id: int) -> None:
    """
    Tarea para programar el tracking de una entrevista.
    
    Args:
        interview_id: ID de la entrevista
    """
    try:
        interview = await Interview.objects.aget(id=interview_id)
        
        # Programar inicio del tracking 1 hora antes
        start_time = interview.interview_date - timedelta(hours=1)
        start_interview_tracking_task.apply_async(
            args=[interview_id],
            eta=start_time
        )
        
        # Programar fin del tracking al finalizar la entrevista
        end_time = interview.interview_date + timedelta(hours=1)  # Asumiendo 1 hora de duración
        stop_interview_tracking_task.apply_async(
            args=[interview_id],
            eta=end_time
        )
        
    except Exception as e:
        logger.error(f"Error en schedule_interview_tracking_task: {str(e)}")