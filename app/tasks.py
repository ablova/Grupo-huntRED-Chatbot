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
from django.db.models import Q
from django.utils import timezone
from asgiref.sync import sync_to_async
from app.chatbot.integrations.services import send_email, send_message
from app.chatbot.chatbot import ChatBotHandler
from app.chatbot.nlp import NLPProcessor
from app.chatbot.integrations.invitaciones import enviar_invitacion_completar_perfil
from app.utilidades.parser import CVParser, IMAPCVProcessor
from app.utilidades.email_scraper import EmailScraperV2
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

logger = logging.getLogger(__name__)


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
    from app.models import BusinessUnit
    from app.chatbot.integrations.services import send_message
    try:
        bu = BusinessUnit.objects.get(id=business_unit_id) if business_unit_id else BusinessUnit.objects.filter(name='amigro').first()
        asyncio.run(send_message('whatsapp', recipient, message, bu))
        logger.info(f"✅ Mensaje de WhatsApp enviado a {recipient}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a WhatsApp: {e}")
        self.retry(exc=e)


@shared_task(bind=True, max_retries=5, default_retry_delay=40, queue='notifications')
def send_telegram_message_task(self, chat_id, message, business_unit_id=None):
    from app.models import BusinessUnit
    from app.chatbot.integrations.services import send_message
    import asyncio
    try:
        business_unit = BusinessUnit.objects.get(id=business_unit_id) if business_unit_id else BusinessUnit.objects.filter(name='amigro').first()
        asyncio.run(send_message('telegram', chat_id, message, business_unit))
        logger.info(f"✅ Mensaje de Telegram enviado a {chat_id}")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Telegram: {e}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=5, default_retry_delay=40, queue='notifications')
def send_messenger_message_task(self, recipient_id, message, business_unit_id=None):
    from app.models import BusinessUnit
    from app.chatbot.integrations.services import send_message
    import asyncio
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
    from app.ml.ml_model import GrupohuntREDMLPipeline
    from app.ml.ml_opt import check_system_load, configure_tensorflow_based_on_load
    import pandas as pd
    try:
        if not check_system_load(threshold=70):
            logger.info("Carga del sistema alta. Reintentando en 10 minutos.")
            raise self.retry(countdown=600)
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
    from app.ml.ml_model import GrupohuntREDMLPipeline
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
    from app.models import DominioScraping, RegistroScraping
    import asyncio
    try:
        if dominio_id:
            dominio = DominioScraping.objects.get(pk=dominio_id)
            dominios = [dominio]
        else:
            dominios = DominioScraping.objects.filter(verificado=True)
        for dominio in dominios:
            logger.info(f"🚀 Iniciando scraping para {dominio.empresa} ({dominio.dominio})")
            try:
                vacantes = asyncio.run(run_scraper(dominio))
                RegistroScraping.objects.create(
                    dominio=dominio,
                    estado="exitoso",
                    fecha_inicio=timezone.now(),
                    fecha_fin=timezone.now(),
                    mensaje=f"Scraping completado. Vacantes encontradas: {len(vacantes)}"
                )
                logger.info(f"✅ Scraping completado para {dominio.empresa}: {len(vacantes)} vacantes")
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
def process_batch_task():
    from app.chatbot.nlp import process_recent_users_batch
    process_recent_users_batch()

# /home/pablo/app/utilidades/linkedin.py
import logging
import os
import csv
import time
import json
import random
import backoff
import requests
import itertools
from typing import Optional, List, Dict
from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from collections import defaultdict  # <--- Importado correctamente
from app.models import BusinessUnit, Person, ChatState, USER_AGENTS
from app.chatbot.nlp import NLPProcessor
from app.utilidades.loader import DIVISION_SKILLS, BUSINESS_UNITS, DIVISIONES
from spacy.matcher import PhraseMatcher
from spacy.lang.es import Spanish

logger = logging.getLogger(__name__)
os.environ["TRANSFORMERS_BACKEND"] = "tensorflow"




LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "781zbztzovea6a")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "WPL_AP1.MKozNnsrqofMSjN4.ua0UOQ==")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", None)
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

MIN_DELAY = 8
MAX_DELAY = 18
# Ruta base de los catálogos
CATALOGS_BASE_PATH = "/home/pablo/app/utilidades/catalogs"

# =========================================================
# Clase para manejar habilidades y divisiones
# =========================================================

def extract_skills(text: str, unit: str) -> List[str]:
    nlp = NLPProcessor(language="es", mode="candidate", analysis_depth="deep")
    skills_dict = nlp.extract_skills(text)
    skills = list(set(skills_dict["technical"] + skills_dict["soft"] + skills_dict["certifications"] + skills_dict["tools"]))
    logger.info(f"Habilidades extraídas (deep) para {unit}: {skills}")
    return skills

class SkillsProcessor:
    def __init__(self, unit_name: str):
        self.unit_name = unit_name
        self.skills_data = self._load_unit_skills()

    def _load_unit_skills(self) -> Dict:
        """
        Carga el archivo skills.json para la unidad de negocio especificada.
        """
        skills_path = os.path.join(CATALOGS_BASE_PATH, self.unit_name, "skills.json")
        try:
            if os.path.exists(skills_path):
                with open(skills_path, 'r', encoding='utf-8') as file:
                    logger.info(f"Skills cargados para unidad: {self.unit_name}")
                    return json.load(file)
            else:
                logger.warning(f"Archivo de habilidades no encontrado para: {self.unit_name}")
                return {}
        except Exception as e:
            logger.error(f"Error cargando skills para {self.unit_name}: {e}")
            return {}

    def extract_skills(self, text: str) -> List[str]:
        """
        Extrae habilidades del texto utilizando el catálogo específico de la unidad.
        """
        try:
            words = text.lower().split()
            extracted_skills = set()

            for division, roles in self.skills_data.items():
                for role, attributes in roles.items():
                    tech_skills = attributes.get("Habilidades Técnicas", [])
                    soft_skills = attributes.get("Habilidades Blandas", [])
                    all_skills = tech_skills + soft_skills
                    for skill in all_skills:
                        if all(word in words for word in skill.lower().split()):
                            extracted_skills.add(skill)

            return list(extracted_skills)
        except Exception as e:
            logger.error(f"Error extrayendo habilidades: {e}")
            return []

    def associate_divisions(self, skills: List[str]) -> List[Dict[str, str]]:
        """
        Asocia divisiones basadas en habilidades extraídas y el catálogo de la unidad.
        """
        associations = []
        try:
            for skill in skills:
                for division, roles in self.skills_data.items():
                    for role, attributes in roles.items():
                        tech_skills = attributes.get("Habilidades Técnicas", [])
                        soft_skills = attributes.get("Habilidades Blandas", [])
                        all_skills = tech_skills + soft_skills
                        if skill in all_skills:
                            associations.append({"skill": skill, "division": division})
        except Exception as e:
            logger.error(f"Error asociando divisiones: {e}")
        return associations


# =========================================================
# Funciones de utilidad
# =========================================================

def normalize_name(name: str) -> str:
    return name.strip().title() if name else ''

def deduplicate_persons(
    first_name: str,
    last_name: str,
    email: Optional[str],
    company: Optional[str],
    position: Optional[str]
) -> Optional[Person]:
    query = Person.objects.all()
    if email:
        existing = query.filter(email__iexact=email).first()
        if existing:
            return existing

    filters = {'nombre__iexact': first_name}
    if last_name:
        filters['apellido_paterno__iexact'] = last_name

    possible_matches = query.filter(**filters)
    if company and company.strip():
        possible_matches = [p for p in possible_matches if p.metadata.get('last_company','').lower() == company.lower()]

    return possible_matches[0] if possible_matches else None

def normalize_and_save_person(first_name, last_name, email, linkedin_url, business_unit):
    """
    Normaliza los datos y guarda la información del usuario.
    """
    first_name = normalize_name(first_name)
    last_name = normalize_name(last_name)
    email = email.lower() if email else None

    person = save_person_record(first_name, last_name, linkedin_url, email, None, None, None, business_unit)
    if person:
        logger.info(f"Persona procesada: {person.nombre} ({person.email})")
    else:
        logger.warning(f"No se pudo procesar: {first_name} {last_name}")

def save_person_record(
    first_name, last_name, linkedin_url, email, birthday, company, position, business_unit, skills=None, phone=None
):
    """
    Crea o actualiza un registro en la base de datos.
    """
    with transaction.atomic():
        existing = deduplicate_persons(first_name, last_name, email, company, position)
        if existing:
            # Actualizar datos existentes
            updated = False
            if linkedin_url and 'linkedin_url' not in existing.metadata:
                existing.metadata['linkedin_url'] = linkedin_url
                updated = True
            if skills:
                normalized_skills = normalize_skills(skills, business_unit, None, position)
                existing.metadata['skills'] = list(set(existing.metadata.get('skills', []) + normalized_skills))
                divisions = associate_divisions(normalized_skills)
                existing.metadata['divisions'] = list(set(existing.metadata.get('divisions', []) + divisions))
                updated = True
            if updated:
                existing.save()
            return existing
        else:
            # Crear nuevo registro
            person = Person(
                ref_num=f"LI-{int(time.time())}-{random.randint(100, 999)}",
                nombre=first_name,
                apellido_paterno=last_name,
                email=email,
                phone=phone,
                metadata={
                    'linkedin_url': linkedin_url,
                    'last_company': company,
                    'last_position': position,
                    'skills': normalize_skills(skills, business_unit, None, position) if skills else [],
                    'divisions': associate_divisions(normalize_skills(skills, business_unit, None, position)) if skills else []
                }
            )
            person.save()
            return person
     
def normalize_skills(raw_skills, business_unit=None, division=None, position=None):
    """
    Normaliza habilidades utilizando el catálogo en skills.json.
    """
    normalized = []
    for skill in raw_skills:
        for unit, unit_data in DIVISION_SKILLS.items():
            if business_unit and unit != business_unit:
                continue
            for div, div_data in unit_data.items():
                if division and div != division:
                    continue
                for pos, pos_data in div_data.items():
                    if position and pos != position:
                        continue
                    if skill.lower() in map(str.lower, pos_data.get("Habilidades Técnicas", [])):
                        normalized.append(skill)
    return list(set(normalized))

def normalize_candidate_key(person):
    return (
        person.nombre.strip().lower() if person.nombre else "",
        person.apellido_paterno.strip().lower() if person.apellido_paterno else "",
        person.email.strip().lower() if person.email else "",
        person.phone.strip() if person.phone else ""
    )

def deduplicate_candidates():
    """
    Agrupa candidatos según nombre, apellido, email y teléfono;
    conserva el de ID menor y elimina los duplicados.
    """
    all_candidates = Person.objects.all().order_by('nombre', 'apellido_paterno', 'email', 'phone', 'id')
    duplicates = []
    for key, group in itertools.groupby(all_candidates, key=normalize_candidate_key):
        group_list = list(group)
        if len(group_list) > 1:
            to_keep = min(group_list, key=lambda p: p.id)
            for candidate in group_list:
                if candidate.id != to_keep.id:
                    duplicates.append(candidate.id)
                    candidate.delete()
    return duplicates

def merge_candidate_data(existing: Person, new_data: Dict) -> Person:
    """
    Fusiona los datos del candidato 'new_data' en el registro 'existing'.
    Para cada campo, si en el registro existente no hay información o está vacía,
    se actualiza con la información de new_data.
    """
    # Por ejemplo, para campos básicos:
    if not existing.nombre and new_data.get('nombre'):
        existing.nombre = new_data['nombre']
    if not existing.apellido_paterno and new_data.get('apellido_paterno'):
        existing.apellido_paterno = new_data['apellido_paterno']
    if not existing.email and new_data.get('email'):
        existing.email = new_data['email']
    if not existing.phone and new_data.get('phone'):
        existing.phone = new_data['phone']
    
    # Para metadata, se puede fusionar de forma similar:
    metadata = existing.metadata or {}
    new_metadata = new_data.get('metadata', {})
    for key, value in new_metadata.items():
        if key not in metadata or not metadata[key]:
            metadata[key] = value
        # Si ambos tienen datos, podrías definir reglas específicas (por ejemplo, unir listas, etc.)
        elif isinstance(metadata[key], list) and isinstance(value, list):
            # Unir sin duplicados
            metadata[key] = list(set(metadata[key] + value))
    existing.metadata = metadata

    return existing

def procesar_cumpleaños(fecha_str):
    """
    Recibe un string de cumpleaños que incluye el año y retorna una fecha con el año predeterminado (por ejemplo, el año actual),
    manteniendo el día y el mes.
    Ejemplo: '1985-06-15' -> '2025-06-15' (siendo 2025 el año actual o el que desees)
    """
    try:
        # Parseamos la fecha original (asumiendo el formato 'YYYY-MM-DD')
        fecha_original = datetime.strptime(fecha_str, '%Y-%m-%d')
        # Asignamos el año deseado, por ejemplo, el año actual:
        año_predeterminado = datetime.now().year
        # Reconstruimos la fecha con el nuevo año
        fecha_nueva = fecha_original.replace(year=año_predeterminado)
        return fecha_nueva
    except Exception as e:
        # Si ocurre un error, se puede loguear y retornar None
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error procesando cumpleaños {fecha_str}: {e}")
        return None
# =========================================================
# Manejo de CSV
# =========================================================
def process_csv(csv_path: str, business_unit: BusinessUnit):
    count = 0
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            count += 1
            fn = normalize_name(row.get('First Name', ''))
            ln = normalize_name(row.get('Last Name', ''))
            linkedin_url = row.get('URL', '').strip() or None
            email = row.get('Email Address', '').strip() or None
            phone_number = row.get('Phone', '').strip() or None

            candidate_data = {
                'nombre': fn,
                'apellido_paterno': ln,
                'linkedin_url': linkedin_url,
                'email': email,
                'phone': phone_number,
                'metadata': {}
            }

            try:
                candidate = deduplicate_persons(fn, ln, email, None, None)
                if candidate:
                    candidate = merge_candidate_data(candidate, candidate_data)
                    candidate.number_interaction += 1
                    candidate.save()
                    logger.info(f"Actualizado candidato: {candidate.nombre} (ID {candidate.id})")
                else:
                    candidate = Person.objects.create(
                        ref_num=f"LI-{int(time.time())}-{random.randint(100, 999)}",
                        **candidate_data
                    )
                    candidate.number_interaction = 1
                    candidate.save()
                    logger.info(f"Creado nuevo candidato: {candidate.nombre} (ID {candidate.id})")

                # Si existe linkedin_url y se quiere enriquecer, realizar scraping:
                if linkedin_url:
                    scraped_data = scrape_linkedin_profile(linkedin_url, business_unit.name.lower())
                    if scraped_data:
                        update_person_from_scrape(candidate, scraped_data)
                        logger.info(f"Enriquecido candidato {candidate.nombre} con datos de LinkedIn")
            except Exception as e:
                logger.error(f"Error procesando registro: {fn} {ln} ({email}): {e}", exc_info=True)

            if count % 100 == 0:
                logger.info(f"Avance: Se han procesado {count} registros.")
    logger.info(f"Proceso CSV completado. Total registros: {count}")

def update_phone_number(person: Person, new_phone: str):
    """
    Actualiza el número de celular para un candidato y su ChatState.
    """
    if new_phone and new_phone != person.chatstate_set.first().phone_number:
        chat_state = person.chatstate_set.first()
        if chat_state:
            chat_state.phone_number = new_phone
            chat_state.save()
        logger.info(f"Celular actualizado para {person}: {new_phone}")
    else:
        logger.warning(f"No se encontró un número nuevo válido para {person}")

def find_placeholders():
    placeholders = ChatState.objects.filter(phone_number__startswith="placeholder-")
    for chat_state in placeholders:
        logger.info(f"Placeholder encontrado: {chat_state.phone_number} para {chat_state.person}")
    return placeholders
# =========================================================
# Manejo API LinkedIn (Futuro)
# =========================================================

def get_linkedin_headers():
    if ACCESS_TOKEN:
        return {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
    return {}

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def fetch_member_profile(member_id: str):
    if not ACCESS_TOKEN:
        logger.warning("Sin ACCESS_TOKEN, no se puede usar API LinkedIn.")
        return None
    url = f"{LINKEDIN_API_BASE}/someMemberEndpoint/{member_id}"
    headers = get_linkedin_headers()
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        logger.error(f"Error {resp.status_code} API LinkedIn: {resp.text}")
        return None

def process_api_data(business_unit: BusinessUnit, member_ids: List[str]):
    for mid in member_ids:
        data = fetch_member_profile(mid)
        if not data:
            continue
        first_name = data.get('firstName','')
        last_name = data.get('lastName','')
        email = data.get('emailAddress',None)
        # Suponiendo posiciones
        company = None
        position = None

        linkedin_url = data.get('profileUrl',None)
        birthday = None
        p = save_person_record(
            normalize_name(first_name),
            normalize_name(last_name),
            linkedin_url,
            email,
            birthday,
            company,
            position,
            business_unit
        )
        logger.info(f"Persona procesada desde API: {p.nombre} {p.apellido_paterno}")

# =========================================================
# Scraping Manual (Sin API)
# =========================================================

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=10, base=30)
def fetch_url(url):
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    time.sleep(random.uniform(15, 30))  # Pausa entre requests
    return r.text

async def slow_scrape_from_csv(csv_path: str, business_unit: BusinessUnit):
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            linkedin_url = row.get('URL', '').strip()
            fn = normalize_name(row.get('First Name', ''))
            ln = normalize_name(row.get('Last Name', ''))
            email = row.get('Email Address', '').strip() or None
            birthday = row.get('Cumpleaños', '').strip() or None
            company = row.get('Company', '').strip() or None
            position = row.get('Position', '').strip() or None

            existing_person = Person.objects.filter(
                nombre__iexact=fn,
                apellido_paterno__iexact=ln,
                linkedin_url=linkedin_url
            ).first()

            if existing_person and existing_person.metadata.get('scraped', False):
                logger.info(f"Perfil ya procesado: {fn} {ln}")
                continue

            if linkedin_url:
                try:
                    scraped_data = await scrape_linkedin_profile(linkedin_url, business_unit.name.lower())
                    if scraped_data:
                        person = save_person_record(
                            fn, ln, linkedin_url, email, birthday, company, position, business_unit
                        )
                        updated = False
                        if 'contact_info' in scraped_data:
                            contact_info = scraped_data['contact_info']
                            if contact_info.get('email') and not person.email:
                                person.email = contact_info['email']
                                updated = True
                                logger.info(f"📧 Email actualizado: {person.email}")
                            if contact_info.get('phone'):
                                person.metadata['phone'] = contact_info['phone']
                                updated = True
                                logger.info(f"📱 Celular actualizado: {contact_info['phone']}")
                        person.metadata['scraped'] = True
                        person.save()
                        if updated:
                            logger.info(f"✅ Perfil enriquecido y actualizado: {person.nombre} {person.apellido_paterno}")
                        else:
                            logger.info(f"Perfil enriquecido sin actualizaciones: {person.nombre} {person.apellido_paterno}")
                    else:
                        logger.warning(f"⚠️ No se encontraron datos para {fn} {ln} con URL {linkedin_url}")
                except Exception as e:
                    logger.error(f"❌ Error scrapeando {linkedin_url}: {e}")
            else:
                person = save_person_record(fn, ln, None, email, birthday, company, position, business_unit)
                logger.info(f"✅ Perfil básico guardado: {fn} {ln} ({email})")

def safe_extract(func):
    """
    Decorador para manejar excepciones en funciones de extracción.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en {func.__name__}: {e}", exc_info=True)
            return None if 'return' not in kwargs else kwargs['return']
    return wrapper

def extract_profile_image(soup):
    try:
        image_tag = soup.find('img', class_='profile-background-image__image')
        return image_tag['src'] if image_tag else None
    except Exception as e:
        logger.error(f"Error extrayendo imagen del perfil: {e}")
        return None

@safe_extract
def extract_contact_link(soup):
    link = soup.find('a', id='top-card-text-details-contact-info')
    if link and link.get('href'):
        return link.get('href')
    return None

@safe_extract
def extract_contact_info(soup):
    contact_info = {}
    sections = soup.find_all('section', class_='pv-contact-info__contact-type')
    for sec in sections:
        header = sec.find('h3', class_='pv-contact-info__header')
        if not header:
            continue
        title = header.get_text(strip=True).lower()
        val_div = sec.find('div', class_='WOncHgTtCymFjecLBiiRjdtcyPWIdpyxk')
        if not val_div:
            continue
        value = val_div.get_text(strip=True)
        if 'email' in title:
            mail_link = val_div.find('a', href=True)
            if mail_link and mail_link['href'].startswith('mailto:'):
                value = mail_link['href'].replace('mailto:', '')
            contact_info['email'] = value
        elif 'teléfono' in title or 'phone' in title:
            contact_info['phone'] = value
        elif 'cumpleaños' in title or 'birthday' in title:
            contact_info['birthday'] = value
        elif 'perfil' in title or 'profile' in title:
            a_profile = val_div.find('a', href=True)
            if a_profile:
                contact_info['profile_link'] = a_profile['href']
    return contact_info

@safe_extract
def extract_name(soup):
    h1 = soup.find('h1', class_='inline t-24 v-align-middle break-words')
    return h1.get_text(strip=True) if h1 else None

@safe_extract
def extract_headline(soup):
    hd = soup.find('div', class_='text-body-medium break-words')
    return hd.get_text(strip=True) if hd else None

@safe_extract
def extract_location(soup):
    loc = soup.find('span', class_='text-body-small inline t-black--light break-words')
    return loc.get_text(strip=True) if loc else None

@safe_extract
def extract_experience(soup):
    exp_section = soup.find('section', id='experience')
    if not exp_section:
        return []
    experiences = []
    lis = exp_section.select('ul li.artdeco-list__item')
    for li in lis:
        role_div = li.find('div', class_='t-bold')
        comp_span = li.find('span', class_='t-14 t-normal')
        dates_span = li.find('span', class_='t-14 t-normal t-black--light')
        role = role_div.get_text(strip=True) if role_div else None
        company = comp_span.get_text(strip=True) if comp_span else None
        dates = dates_span.get_text(strip=True) if dates_span else None
        if role or company:
            experiences.append({'role': role, 'company': company, 'dates': dates})
    return experiences

@safe_extract
def extract_education(soup):
    edu_section = soup.find('section', id='education')
    if not edu_section:
        return []
    education_list = []
    lis = edu_section.select('ul li.artdeco-list__item')
    for li in lis:
        school_div = li.find('div', class_='t-bold')
        degree_span = li.find('span', class_='t-14 t-normal')
        dates_span = li.find('span', class_='t-14 t-normal t-black--light')
        school = school_div.get_text(strip=True) if school_div else None
        degree = degree_span.get_text(strip=True) if degree_span else None
        dates = dates_span.get_text(strip=True) if dates_span else None
        education_list.append({'school': school, 'degree': degree, 'dates': dates})
    return education_list

@safe_extract
def extract_languages(soup):
    lang_section = soup.find('section', id='languages')
    if not lang_section:
        return []
    language_list = []
    lis = lang_section.select('ul li.artdeco-list__item')
    for li in lis:
        lang_div = li.find('div', class_='t-bold')
        level_span = li.find('span', class_='t-14 t-normal t-black--light')
        lname = lang_div.get_text(strip=True) if lang_div else None
        level = level_span.get_text(strip=True) if level_span else None
        if lname:
            language_list.append({'language': lname, 'level': level})
    return language_list


def associate_divisions(skills: List[str], unit: str) -> List[Dict[str, str]]:
    processor = SkillsProcessor(unit)
    return processor.associate_divisions(skills)

from playwright.async_api import async_playwright

async def scrape_linkedin_profile(link_url: str, unit: str) -> Dict:
    try:
        async with async_playwright() as p:
            # Seleccionar un USER_AGENT aleatorio
            user_agent = random.choice(USER_AGENTS)
            
            # Lanzar el navegador con configuraciones robustas
            browser = await p.chromium.launch(headless=True)  # Cambia a False para depurar visualmente
            context = await browser.new_context(
                user_agent=user_agent,
                viewport={"width": 1280, "height": 720},
                locale="es-ES"  # Simula un navegador en español
            )
            
            # Ruta para almacenar cookies autenticadas
            cookies_file = "/home/pablo/skills_data/linkedin_cookies.json"
            
            # Verificar si hay cookies guardadas y válidas
            if os.path.exists(cookies_file):
                await context.storage_state(path=cookies_file)
                logger.info(f"Cargando cookies desde {cookies_file}")
            else:
                logger.warning("No se encontraron cookies guardadas. Intentando login manual.")
                page = await context.new_page()
                await page.goto("https://www.linkedin.com/login")
                await page.fill("#username", "pablo@huntred.com")  # Reemplaza con tu email
                await page.fill("#password", "Natalia&Patricio1113!")  # Reemplaza con tu contraseña
                await page.click("button[type=submit]")
                await page.wait_for_load_state("networkidle", timeout=60000)
                await context.storage_state(path=cookies_file)  # Guardar cookies tras login
                logger.info(f"Cookies guardadas en {cookies_file}")
                await page.close()

            # Abrir la página del perfil
            page = await context.new_page()
            logger.info(f"Intentando acceder a {link_url}")
            await page.goto(link_url, timeout=60000)  # Timeout aumentado a 60 segundos
            
            # Esperar a que la página cargue completamente
            await page.wait_for_load_state("networkidle", timeout=60000)
            
            # Verificar si requiere login (título de la página de login)
            if "Log In or Sign Up" in await page.title():
                logger.error(f"Autenticación fallida para {link_url}. Actualiza las credenciales o cookies.")
                await browser.close()
                return {}

            # Obtener el contenido HTML
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            
            # Extraer datos
            data = {
                "headline": extract_headline(soup),
                "location": extract_location(soup),
                "experience": extract_experience(soup),
                "education": extract_education(soup),
                "skills": extract_skills(soup.get_text(), unit),  # Esto usa NLPProcessor
                "languages": extract_languages(soup),
                "contact_info": extract_contact_info(soup),
            }
            
            # Normalizar habilidades y asociar divisiones
            data["skills"] = normalize_skills(data["skills"], unit)
            data["divisions"] = associate_divisions(data["skills"], unit)
            
            # Log de éxito
            logger.info(f"Scrapeado exitosamente {link_url}")
            
            # Cerrar el navegador
            await browser.close()
            
            # Pausa aleatoria para evitar bloqueos
            await asyncio.sleep(random.uniform(10, 20))
            
            return data
            
    except Exception as e:
        logger.error(f"Error scrapeando {link_url}: {str(e)}", exc_info=True)
        return {}
    
@backoff.on_exception(backoff.expo, Exception, max_tries=5, jitter=backoff.full_jitter)
async def fetch_page(page, url):
    await page.goto(url)

def update_person_from_scrape(person: Person, scraped_data: dict):
    """
    Actualiza los datos de un perfil con la información scrapeada solo si hay datos válidos.
    """
    if not scraped_data or not any(scraped_data.values()):
        logger.warning(f"No se encontraron datos válidos para actualizar {person.nombre}")
        return
    
    updated = False
    if scraped_data.get("headline"):
        person.metadata["headline"] = scraped_data["headline"]
        updated = True
    if scraped_data.get("experience"):
        person.metadata["experience"] = scraped_data["experience"]
        updated = True
    if scraped_data.get("education"):
        person.metadata["education"] = scraped_data["education"]
        updated = True
    if scraped_data.get("skills"):
        extracted_skills = extract_skills(" ".join(scraped_data["skills"]))
        person.metadata["skills"] = list(set(person.metadata.get("skills", []) + extracted_skills))
        updated = True
    if scraped_data.get("languages"):
        person.metadata["languages"] = scraped_data["languages"]
        updated = True
    if scraped_data.get("contact_info"):
        contact_info = scraped_data["contact_info"]
        if "email" in contact_info and not person.email:
            person.email = contact_info["email"]
            updated = True
        if "phone" in contact_info and not person.phone:
            person.phone = contact_info["phone"]
            updated = True

    person.metadata["linkedin_last_updated"] = timezone.now().isoformat()
    if updated:
        person.save()
        logger.info(f"Perfil actualizado: {person.nombre} {person.apellido_paterno}")
    else:
        logger.info(f"No se actualizó {person.nombre}: sin datos nuevos")

def construct_linkedin_url(first_name: str, last_name: str) -> str:
    """
    Construye una posible URL de LinkedIn a partir del nombre y apellido.
    """
    base_url = "https://www.linkedin.com/in/"
    name_slug = f"{first_name.lower()}-{last_name.lower()}".replace(" ", "-")
    return f"{base_url}{name_slug}"

async def process_linkedin_updates():
    persons = Person.objects.all()
    processed_count = 0
    constructed_count = 0
    errors_count = 0

    for person in persons:
        linkedin_url = person.linkedin_url
        if not linkedin_url:
            linkedin_url = construct_linkedin_url(person.nombre, person.apellido_paterno)
            person.linkedin_url = linkedin_url
            person.save()
            constructed_count += 1
            logger.info(f"🌐 URL construida para {person.nombre}: {linkedin_url}")

        try:
            logger.info(f"Procesando: {person.nombre} ({linkedin_url})")
            scraped_data = await scrape_linkedin_profile(linkedin_url, "amigro")  # Default unit
            update_person_from_scrape(person, scraped_data)
            processed_count += 1
            logger.info(f"✅ Actualizado: {person.nombre}")
        except Exception as e:
            logger.error(f"❌ Error procesando {person.nombre} ({linkedin_url}): {e}")
            errors_count += 1

    logger.info(f"Resumen: Procesados: {processed_count}, URLs construidas: {constructed_count}, Errores: {errors_count}")


@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def process_linkedin_updates_task(self):
    try:
        asyncio.run(process_linkedin_updates())
        logger.info("✅ LinkedIn updates completed")
    except Exception as e:
        logger.error(f"❌ Error in LinkedIn updates: {e}")
        self.retry(exc=e)

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

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue='scraping')
def slow_scrape_from_csv_task(self, csv_path: str, business_unit_id: int):
    try:
        business_unit = BusinessUnit.objects.get(id=business_unit_id)
        asyncio.run(slow_scrape_from_csv(csv_path, business_unit))
        logger.info(f"✅ Slow scrape completed for {csv_path}")
    except Exception as e:
        logger.error(f"❌ Error in slow scrape: {e}")
        self.retry(exc=e)

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
    logger.info(f"Scrapeando perfil: {profile_url}")
    data = asyncio.run(scrape_linkedin_profile(profile_url, "amigro"))  # Default unit, adjust as needed
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
def execute_email_scraper(dominio_id=None, batch_size=10):
    """
    Ejecuta la extracción de vacantes desde correos electrónicos, opcionalmente para un dominio específico.
    
    Args:
        dominio_id (int, optional): ID del dominio específico para filtrar correos (si aplica).
        batch_size (int): Número de correos a procesar por lote.
    
    Returns:
        str: Resultado de la ejecución.
    """
    try:
        # Obtener credenciales desde el entorno
        EMAIL_ACCOUNT = env("EMAIL_ACCOUNT", default="pablo@huntred.com")
        EMAIL_PASSWORD = env("EMAIL_PASSWORD", default="Natalia&Patricio1113!")

        # Instanciar el scraper
        scraper = EmailScraperV2(EMAIL_ACCOUNT, EMAIL_PASSWORD)

        if dominio_id:
            dominio = DominioScraping.objects.get(id=dominio_id)
            logger.info(f"🚀 Ejecutando email scraper para {dominio.dominio} con batch_size={batch_size}...")
            # Nota: Actualmente EmailScraperV2 no filtra por dominio_id, pero lo dejamos preparado
        else:
            logger.info(f"🚀 Ejecutando email scraper para todos los correos con batch_size={batch_size}...")

        # Ejecutar el scraper de manera asíncrona
        asyncio.run(scraper.run(batch_size=batch_size))

        # Obtener el número de correos procesados desde los logs sería ideal, pero como no devolvemos un contador directamente,
        # asumimos éxito si no hay excepciones
        return f"✅ Email scraper ejecutado con éxito para {batch_size} correos"

    except Exception as e:
        logger.error(f"❌ Error en email_scraper: {e}", exc_info=True)
        return f"❌ Error en ejecución: {e}"