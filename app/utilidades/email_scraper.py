# /home/pablo/app/utilidades/email_scraper.py
import email
import logging
import aiohttp
import environ
import asyncio
import re
from typing import Optional, List, Dict, Any, Tuple
from aioimaplib import aioimaplib
from datetime import datetime, timedelta
from email.utils import parseaddr
from urllib.parse import urlparse
import trafilatura
from bs4 import BeautifulSoup
from app.models import BusinessUnit, Vacante, DominioScraping
from app.utilidades.vacantes import VacanteManager
from asgiref.sync import sync_to_async
from app.chatbot.utils import clean_text
from app.chatbot.nlp import NLPProcessor
from app.chatbot.integrations.services import send_email
from app.utilidades.scraping import extract_field, validate_job_data, assign_business_unit, extract_skills
from django.utils import timezone

# Configuración de logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

# Global NLP Processor instance
NLP_PROCESSOR = NLPProcessor(language="es", mode="opportunity", analysis_depth="deep")

# Configuración de la cuenta IMAP
env = environ.Env()
environ.Env.read_env(env_file='/home/pablo/.env')
EMAIL_ACCOUNT = "pablo@huntred.com"
EMAIL_PASSWORD = env("EMAIL_HOST_PASSWORD")
IMAP_SERVER = env("EMAIL_HOST", default="mail.huntred.com")

# Variables de configuración
DAYS_TO_PROCESS = 10
DEFAULT_BATCH_SIZE = 10
SLEEP_TIME = 2

# Lista de remitentes válidos
VALID_SENDERS = [
    'jobs-noreply@linkedin.com', 'jobalerts-noreply@linkedin.com', 'jobs-listings@linkedin.com',
    'alerts@glassdoor.com', 'noreply@glassdoor.com', 'TalentCommunity@talent.honeywell.com',
    'santander@myworkday.com'
]

# Dominios permitidos para solicitudes HTTP
ALLOWED_DOMAINS = {
    "linkedin.com", "www.linkedin.com", "mx.linkedin.com", "*.linkedin.com",
    "glassdoor.com", "www.glassdoor.com", "*.glassdoor",
    "honeywell.com", "careers.honeywell.com", "*.honeywell.com",
    "myworkday.com", "santander.wd3.myworkdayjobs.com", "workday.com", "*.santander.com",
    "indeed.com", "*.indeed.com", "computrabajo.com", "*.computrabajo.com"
}

# Palabras clave para identificar correos de empleo
JOB_KEYWORDS = [
    'job', 'vacante', 'opportunity', 'empleo', 'position', 'opening', 'alert',
    'oportunidad', 'subdirector', 'director', 'trabajo', 'oferta laboral',
    'reclutamiento', 'contratación', 'convocatoria', 'anuncio laboral',
    'job offer', 'career', 'postulación', 'apply now', 'new jobs',
    'vacancy', 'hiring', 'recruitment', 'job listing', 'posición disponible'
]

# Configuración de carpetas IMAP
FOLDER_CONFIG = {
    "inbox": "INBOX",
    "jobs_folder": "INBOX.Jobs",
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

# Patrones para identificar correos de empleo
JOB_SUBJECT_PATTERNS = [
    re.compile(r'\bjob alert\b', re.IGNORECASE),
    re.compile(r'\bvacante\b', re.IGNORECASE),
    re.compile(r'\bopportunit(y|ies)\b', re.IGNORECASE),
    re.compile(r'\bempleo\b', re.IGNORECASE),
    re.compile(r'\boferta laboral\b', re.IGNORECASE),
    re.compile(r'\bhiring\b', re.IGNORECASE),
    re.compile(r'\brecruitment\b', re.IGNORECASE),
]

async def connect_to_email(email_account: str = EMAIL_ACCOUNT, retries: int = 3):
    logger.debug(f"Iniciando conexión IMAP a {IMAP_SERVER} con cuenta {email_account}")
    for attempt in range(retries):
        try:
            client = aioimaplib.IMAP4_SSL(IMAP_SERVER, 993)
            await client.wait_hello_from_server()
            await client.login(email_account, EMAIL_PASSWORD)
            await client.select(FOLDER_CONFIG["jobs_folder"])
            logger.info(f"Conectado al servidor IMAP: {IMAP_SERVER} con cuenta {email_account}")
            return client
        except Exception as e:
            logger.error(f"Intento {attempt + 1}/{retries} fallido para {email_account}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(5)
    logger.error(f"No se pudo conectar al servidor IMAP tras {retries} intentos para {email_account}")
    return None

async def email_scraper(email_account: str = "pablo@huntred.com", batch_size: int = 10, enable_move: bool = False):
    mail = await connect_to_email(email_account)
    if not mail:
        logger.error(f"No se pudo conectar al servidor IMAP para {email_account}")
        return {"emails_processed": 0, "total_vacancies": 0, "vacancies_created": 0, "errors": 1}

    stats = {"emails_processed": 0, "total_vacancies": 0, "vacancies_created": 0, "errors": 0}

    try:
        await mail.select("INBOX.Jobs")
        date_filter = (datetime.now() - timedelta(days=DAYS_TO_PROCESS)).strftime("%d-%b-%Y")
        logger.debug(f"Buscando correos desde {date_filter}")
        resp, messages = await mail.search(None, f'SINCE {date_filter}')
        if resp != "OK":
            logger.error(f"Error en búsqueda de mensajes: {resp}")
            stats["errors"] += 1
            return stats

        email_ids = messages[0].split()
        logger.info(f"Total de correos encontrados para {email_account}: {len(email_ids)}")
        if not email_ids:
            logger.warning("No se encontraron correos en el rango de fechas")
            return stats

        batch_ids = email_ids[:batch_size]
        logger.info(f"Procesando lote de {len(batch_ids)} correos")

        tasks = []
        for email_id_bytes in batch_ids:
            email_id = email_id_bytes.decode()
            message = await fetch_email(mail, email_id)
            if message:
                tasks.append(process_job_alert_email(mail, email_id, message, stats, enable_move))
            else:
                stats["errors"] += 1

        if tasks:
            await asyncio.gather(*tasks)
            logger.info(f"Lote procesado. Estadísticas: {stats}")
        else:
            logger.warning("No se encontraron correos procesables en el lote")

        return stats
    except Exception as e:
        logger.error(f"Error en email_scraper para {email_account}: {e}")
        stats["errors"] += 1
        return stats
    finally:
        await mail.logout()
        logger.info(f"Desconectado del servidor IMAP para {email_account}")

async def fetch_email(mail, email_id):
    resp, data = await mail.fetch(email_id, "(RFC822)")
    if resp == "OK":
        if data and isinstance(data[0], tuple) and len(data[0]) == 2:
            raw_email = data[0][1]
            if raw_email:
                message = email.message_from_bytes(raw_email)
                logger.info(f"Successfully fetched email {email_id}")
                return message
            else:
                logger.error(f"Empty email content for {email_id}")
        else:
            logger.error(f"Unexpected data format for email {email_id}: {data}")
    else:
        logger.error(f"Fetch failed for email {email_id}: {resp}")
    return None

def is_job_email(subject: str) -> bool:
    return any(pattern.search(subject) for pattern in JOB_SUBJECT_PATTERNS)

async def process_job_alert_email(mail, email_id: str, message, stats: Dict[str, int], enable_move: bool = False):
    try:
        sender = message["From"]
        subject = message["Subject"]
        if not sender or not subject:
            logger.warning(f"Correo {email_id} sin remitente o asunto")
            stats["errors"] += 1
            return

        sender_email = parseaddr(sender)[1].lower().strip()
        subject = subject.lower().strip()

        if sender_email in VALID_SENDERS or is_job_email(subject) or any(keyword in subject for keyword in JOB_KEYWORDS):
            logger.info(f"Procesando correo {email_id} de {sender_email}")
            stats["emails_processed"] += 1

            body = None
            plain_text = None
            if message.is_multipart():
                for part in message.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/html":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    elif content_type == "text/plain":
                        plain_text = part.get_payload(decode=True).decode("utf-8", errors="ignore")
            else:
                body = message.get_payload(decode=True).decode("utf-8", errors="ignore")

            if not body and not plain_text:
                logger.warning(f"Correo {email_id} sin contenido procesable")
                stats["errors"] += 1
                return

            job_listings = await extract_vacancies_from_html(body or "", sender_email, plain_text)
            logger.info(f"Encontradas {len(job_listings)} vacantes en el correo {email_id}")
            stats["total_vacancies"] += len(job_listings)

            tasks = []
            for job_data in job_listings:
                logger.debug(f"Procesando vacante: {job_data}")
                description = job_data.get("job_description", "")
                if description:
                    job_data["skills"] = extract_skills(description)

                business_unit_id = await assign_business_unit(job_data)
                if business_unit_id:
                    logger.info(f"Asignada BusinessUnit ID: {business_unit_id} para {job_data['job_title']}")
                    tasks.append(create_vacancy_from_email(job_data, business_unit_id))
                else:
                    logger.warning(f"No se asignó BusinessUnit para {job_data['job_title']}")
                    stats["errors"] += 1

            if tasks:
                results = await asyncio.gather(*tasks)
                stats["vacancies_created"] += sum(1 for r in results if r)
                stats["errors"] += sum(1 for r in results if not r)
                logger.info(f"Resultados de creación de vacantes: Creadas={stats['vacancies_created']}, Errores={stats['errors']}")
            else:
                logger.warning(f"No se crearon tareas para vacantes en {email_id}")

            if enable_move:
                await mail.copy(email_id, FOLDER_CONFIG["parsed_folder"])
                await mail.store(email_id, "+FLAGS", "\\Deleted")
    except Exception as e:
        logger.error(f"Error procesando correo {email_id}: {e}")
        stats["errors"] += 1

async def create_vacancy_from_email(job_data: Dict, business_unit_id: int) -> bool:
    try:
        bu = await sync_to_async(BusinessUnit.objects.get)(id=business_unit_id)
        vacante, created = await sync_to_async(Vacante.objects.get_or_create)(
            url_original=job_data["job_link"],
            defaults={
                "titulo": job_data["job_title"],
                "empresa": job_data["company_name"],
                "ubicacion": job_data["location"],
                "descripcion": job_data["job_description"],
                "business_unit": bu,
                "fecha_publicacion": job_data.get("posting_date", timezone.now()),
                "skills_required": job_data.get("skills", []),
                "contract_type": job_data.get("contract_type"),
                "job_type": job_data.get("employment_type"),
                "beneficios": ", ".join(job_data.get("benefits", [])) if job_data.get("benefits") else None,
                "salario": job_data.get("salary_range"),
                "sentiment": job_data.get("sentiment"),
                "job_classification": job_data.get("job_classification"),
            }
        )
        if created:
            logger.info(f"Vacante creada exitosamente: {vacante.titulo}")
            return True
        logger.info(f"Vacante ya existía: {vacante.titulo}")
        return False
    except Exception as e:
        logger.error(f"Error creando vacante: {e}")
        return False

# Ejemplo de ejecución
if __name__ == "__main__":
    asyncio.run(email_scraper())