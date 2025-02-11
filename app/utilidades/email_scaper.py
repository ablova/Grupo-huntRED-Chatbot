# Ubicación /home/pablollh/app/utilidades/email_scaper.py
import imaplib
import email
import logging
from datetime import datetime, timedelta
from email.header import decode_header
from bs4 import BeautifulSoup
from app.models import ConfiguracionBU, Vacante
from app.utilidades.vacantes import VacanteManager

# Configuración del logger
logger = logging.getLogger(__name__)

# Configuración de la cuenta específica para scraping
EMAIL_ACCOUNT = "pablo@huntred.com"
EMAIL_PASSWORD = "tu_password_aqui"  # ⚠️ Debe gestionarse de forma segura
IMAP_SERVER = "imap.huntred.com"
IMAP_FOLDER = "INBOX"

# Solo procesar correos de los últimos 3 días
DAYS_TO_PROCESS = 3

def connect_to_email():
    """ Conecta a la cuenta de IMAP para extraer correos. """
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select(IMAP_FOLDER)
        return mail
    except Exception as e:
        logger.error(f"Error conectando al servidor IMAP: {e}")
        return None

def process_job_alert_email(mail, email_id, message):
    """ Procesa alertas de empleo de LinkedIn, Glassdoor y otros. """
    try:
        sender = message["From"]
        subject = message["Subject"]

        if not sender or not subject:
            return

        # Filtrar remitentes y sujetos relevantes
        valid_senders = [
            'jobs-noreply@linkedin.com', 'jobalerts-noreply@linkedin.com',
            'jobs-listings@linkedin.com', 'alerts@glassdoor.com',
            'noreply@glassdoor.com', 'TalentCommunity@talent.honeywell.com',
            'santander@myworkday.com'
        ]

        if sender.lower() not in valid_senders:
            return

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
            logger.warning(f"Correo {email_id} sin contenido HTML procesable.")
            return

        # Parsear el HTML para extraer vacantes
        soup = BeautifulSoup(body, "html.parser")
        job_listings = []

        for job_section in soup.find_all("a", href=True):
            job_title = job_section.get_text(strip=True)
            job_link = job_section["href"]

            if "linkedin.com/jobs/view" in job_link or "glassdoor.com/job-listing" in job_link:
                job_listings.append({
                    "job_title": job_title,
                    "job_link": job_link,
                    "company_name": "LinkedIn/Glassdoor Alert",
                    "job_description": f"Vacante detectada: {job_title}",
                    "business_unit": 4  # Ajustar según la unidad de negocio
                })

        if not job_listings:
            logger.warning(f"No se detectaron vacantes en el correo {email_id}")
            return

        # Crear vacantes en el sistema
        for job_data in job_listings:
            vacante_manager = VacanteManager(job_data)
            vacante_manager.create_job_listing()

        # Mover y eliminar el correo procesado
        mail.store(email_id, "+FLAGS", "\\Deleted")

    except Exception as e:
        logger.error(f"Error procesando alerta de empleo {email_id}: {e}")

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
            logger.error("Error en búsqueda de mensajes")
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
        logger.error(f"Error ejecutando email scraper: {e}")
    finally:
        mail.logout()

