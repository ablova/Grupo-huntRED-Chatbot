# Ubicación /home/pablo/app/utilidades/email_scraper.py

import imaplib
import email
import logging
import aiohttp
from datetime import datetime, timedelta
import environ
from email.header import decode_header
from bs4 import BeautifulSoup
from app.models import ConfiguracionBU, Vacante, BusinessUnit
from app.utilidades.vacantes import VacanteManager

# Configuración del logger
logger = logging.getLogger(__name__)

# Configuración de la cuenta IMAP (Se obtiene de la BD)
EMAIL_ACCOUNT = "pablo@huntred.com"
env = environ.Env()
environ.Env.read_env(env_file='/home/pablo/.env')  # Cambia la ruta aquí
EMAIL_PASSWORD = env("EMAIL_HOST_PASSWORD")
IMAP_SERVER = env("EMAIL_HOST", default="mail.huntred.com")
IMAP_FOLDER = "INBOX"
DAYS_TO_PROCESS = 15  # Últimos 3 días

# Lista de remitentes válidos
VALID_SENDERS = [
    'jobs-noreply@linkedin.com', 'jobalerts-noreply@linkedin.com', 'jobs-listings@linkedin.com', 'alerts@glassdoor.com',
    'noreply@glassdoor.com', 'TalentCommunity@talent.honeywell.com', 'santander@myworkday.com'
]

FOLDER_CONFIG = {
    "inbox": "INBOX",
    "jobs_folder": "INBOX.Jobs",  # Reemplaza por la ruta correcta
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

def connect_to_email():
    """ Conecta a la cuenta IMAP usando credenciales de la BD. """
    global EMAIL_ACCOUNT, EMAIL_PASSWORD

    try:
        config = ConfiguracionBU.objects.filter(business_unit__name="huntRED®").first()
        if config:
            EMAIL_ACCOUNT = config.email_account
            EMAIL_PASSWORD = config.email_password

        if not EMAIL_ACCOUNT or not EMAIL_PASSWORD:
            logger.error("⚠️ No se encontraron credenciales de email en la BD.")
            return None

        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select(FOLDER_CONFIG["jobs_folder"])
        return mail

    except Exception as e:
        logger.error(f"❌ Error conectando al servidor IMAP: {e}")
        return None

def extract_vacancies_from_html(html, sender):
    """Extrae vacantes de un correo HTML basado en el remitente."""
    soup = BeautifulSoup(html, "html.parser")
    job_listings = []

    for job_section in soup.find_all("a", href=True):
        job_title = job_section.get_text(strip=True)
        job_link = job_section["href"]

        # Determinar la empresa remitente y validar las URLs de vacantes
        if "linkedin.com/jobs/view" in job_link and "linkedin" in sender:
            company_name = "LinkedIn"
        elif "glassdoor.com/job-listing" in job_link and "glassdoor" in sender:
            company_name = "Glassdoor"
        elif "santander.wd3.myworkdayjobs.com" in job_link and "santander" in sender:
            company_name = "Santander"
        elif "honeywell.com" in job_link and "honeywell" in sender:
            company_name = "Honeywell"
        else:
            continue  # No es una URL válida

        job_listings.append({
            "job_title": job_title,
            "job_link": job_link,
            "company_name": company_name,
            "job_description": job_title,
            "business_unit": 4  # Se puede mejorar con lógica más avanzada
        })

    return job_listings

def assign_business_unit(job_title):
    """ Determina la unidad de negocio en función del título de la vacante. """
    analysis_points = {
        'huntRED®': ['leadership', 'executive', 'manager', 'director', 'ceo', 'coo'],
        'huntRED® Executive': ['strategic', 'board', 'global', 'vp', 'president', 'cfo'],
        'huntu': ['trainee', 'junior', 'entry-level', 'intern', 'graduate'],
        'amigro': ['migration', 'bilingual', 'visa sponsorship', 'temporary job']
    }

    job_title_lower = job_title.lower()
    for business_unit, keywords in analysis_points.items():
        if any(keyword in job_title_lower for keyword in keywords):
            return business_unit

    return None  # No se encontró una coincidencia clara

def process_job_alert_email(mail, email_id, message):
    """ Procesa alertas de empleo y extrae vacantes. """
    try:
        sender = message["From"]
        subject = message["Subject"]

        if not sender or not subject:
            return

        sender = sender.lower().strip()
        if sender not in VALID_SENDERS:
            return  # No es un remitente válido

        # Extraer contenido del correo
        body = None
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            body = message.get_payload(decode=True).decode("utf-8", errors="ignore")

        if not body:
            logger.warning(f"⚠️ Correo {email_id} sin contenido HTML procesable.")
            return

        # Extraer vacantes con la nueva función
        job_listings = extract_vacancies_from_html(body, sender)

        if not job_listings:
            logger.warning(f"⚠️ No se detectaron vacantes en el correo {email_id}")
            return

        # Crear vacantes en el sistema
        for job_data in job_listings:
            business_unit_name = assign_business_unit(job_data["job_title"])
            if business_unit_name:
                job_data["business_unit"] = BusinessUnit.objects.get(name=business_unit_name).id

            vacante_manager = VacanteManager(job_data)
            vacante_manager.create_job_listing()

        # Mover el correo a la carpeta Parsed después de procesarlo
        mail.copy(email_id, FOLDER_CONFIG["parsed_folder"])
        mail.store(email_id, "+FLAGS", "\\Deleted")

    except Exception as e:
        logger.error(f"❌ Error procesando alerta de empleo {email_id}: {e}")

def email_scraper():
    """ Ejecuta la extracción de correos y procesa vacantes de empleo. """
    mail = connect_to_email()
    if not mail:
        return

    try:
        # Obtener la fecha límite para procesar (últimos 3 días)
        date_filter = (datetime.now() - timedelta(days=DAYS_TO_PROCESS)).strftime("%d-%b-%Y")

        status, messages = mail.search(None, f'(SINCE {date_filter})')
        if status != 'OK':
            logger.error("❌ Error en búsqueda de mensajes")
            return

        email_ids = messages[0].split()
        for email_id in email_ids:
            status, data = mail.fetch(email_id, "(RFC822)")
            if status != 'OK':
                continue

            message = email.message_from_bytes(data[0][1])
            process_job_alert_email(mail, email_id, message)

        # Eliminar correos procesados
        mail.expunge()
    except Exception as e:
        logger.error(f"❌ Error ejecutando email scraper: {e}")
    finally:
        mail.logout()