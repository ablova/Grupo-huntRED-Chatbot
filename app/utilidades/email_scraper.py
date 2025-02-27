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
    soup = BeautifulSoup(html, "html.parser")
    job_listings = []

    # Limitar búsqueda a secciones comunes en correos de empleo
    job_containers = soup.select("a[href*='jobs'], a[href*='job-listing']")  # Ejemplo de selector CSS
    for job_section in job_containers:
        job_title = job_section.get_text(strip=True)
        job_link = job_section["href"]

        if "linkedin.com/jobs/view" in job_link and "linkedin" in sender:
            company_name = "LinkedIn"
        elif "glassdoor.com/job-listing" in job_link and "glassdoor" in sender:
            company_name = "Glassdoor"
        elif "santander.wd3.myworkdayjobs.com" in job_link and "santander" in sender:
            company_name = "Santander"
        elif "honeywell.com" in job_link and "honeywell" in sender:
            company_name = "Honeywell"
        else:
            continue

        job_listings.append({
            "job_title": job_title,
            "job_link": job_link,
            "company_name": company_name,
            "job_description": job_title,
            "business_unit": 4  # Se ajustará con assign_business_unit
        })

    return job_listings

def assign_business_unit(job_title, job_description=None, salary_range=None, required_experience=None, location=None):
    """
    Determina la unidad de negocio en función del título, descripción, salario, experiencia y ubicación de la vacante.
    Devuelve el ID de la BusinessUnit correspondiente o None si no se encuentra coincidencia clara.

    :param job_title: Título de la vacante (obligatorio).
    :param job_description: Descripción de la vacante (opcional).
    :param salary_range: Rango salarial ofrecido (opcional, tupla (min, max)).
    :param required_experience: Años de experiencia requeridos (opcional, entero).
    :param location: Ubicación del empleo (opcional, cadena de texto).
    :return: ID de la unidad de negocio o None.
    """
    # Normalizar entradas a minúsculas
    job_title_lower = job_title.lower()
    job_desc_lower = job_description.lower() if job_description else ""
    location_lower = location.lower() if location else ""

    # Definir palabras clave por unidad de negocio con pesos
    business_units_keywords = {
        'huntRED®': {
            'manager': 2, 'director': 3, 'leadership': 2,
            'senior manager': 4, 'operations manager': 3, 'project manager': 3, 'head of': 4,
            'gerente': 2, 'director de': 3, 'jefe de': 4  # Términos en español
        },
        'huntRED® Executive': {
            'strategic': 3, 'board': 4, 'global': 3, 'vp': 4, 'president': 4, 'cfo': 5, 'ceo': 5, 'coo': 5, 'executive': 4,
            'cto': 5, 'chief': 4, 'executive director': 5, 'senior vp': 5, 'vice president': 4,
            'estrategico': 3, 'global': 3, 'presidente': 4  # Términos en español
        },
        'huntu': {
            'trainee': 3, 'junior': 3, 'entry-level': 4, 'intern': 3, 'graduate': 3,
            'developer': 2, 'engineer': 2, 'senior developer': 3, 'lead developer': 3,
            'software engineer': 2, 'data analyst': 2, 'it specialist': 2, 'technical lead': 3,
            'architect': 3, 'analyst': 2, 'specialist': 2, 'consultant': 2, 'programador': 2,
            'ingeniero': 2, 'analista': 2  # Términos técnicos en español
        },
        'amigro': {
            'migration': 4, 'bilingual': 3, 'visa sponsorship': 4, 'temporary job': 3,
            'worker': 2, 'operator': 2, 'constructor': 2, 'laborer': 2, 'assistant': 2,
            'technician': 2, 'support': 2, 'seasonal': 2, 'entry-level': 2, 'no experience': 3,
            'trabajador': 2, 'operador': 2, 'asistente': 2, 'migración': 4  # Términos en español
        }
    }

    # Palabras clave de seniority
    seniority_keywords = {
        'junior': 1, 'entry-level': 1, 'mid-level': 2, 'senior': 3, 'lead': 3,
        'manager': 4, 'director': 5, 'vp': 5, 'executive': 5, 'chief': 5, 'jefe': 4
    }

    # Palabras clave por industria
    industry_keywords = {
        'tech': {'developer', 'engineer', 'software', 'data', 'it', 'architect', 'programador', 'ingeniero'},
        'management': {'manager', 'director', 'executive', 'leadership', 'gerente', 'jefe'},
        'operations': {'operator', 'worker', 'constructor', 'technician', 'trabajador', 'operador'},
        'strategy': {'strategic', 'global', 'board', 'president', 'estrategico'}
    }

    # Calcular seniority (se toma la puntuación máxima encontrada)
    seniority_score = 0
    for keyword, score in seniority_keywords.items():
        if keyword in job_title_lower:
            seniority_score = max(seniority_score, score)

    # Detectar industria dominante
    industry_scores = {ind: 0 for ind in industry_keywords}
    for ind, keywords in industry_keywords.items():
        for keyword in keywords:
            if keyword in job_title_lower or keyword in job_desc_lower:
                industry_scores[ind] += 1
    dominant_industry = max(industry_scores, key=industry_scores.get) if max(industry_scores.values()) > 0 else None

    # Calcular puntuaciones iniciales por unidad de negocio
    scores = {bu: 0 for bu in business_units_keywords}
    for bu, keywords in business_units_keywords.items():
        for keyword, weight in keywords.items():
            if keyword in job_title_lower or (job_description and keyword in job_desc_lower):
                scores[bu] += weight

    # Ajustes por seniority
    if seniority_score >= 4:
        scores['huntRED®'] += 3
        scores['huntRED® Executive'] += 2
    elif seniority_score >= 2:
        scores['huntu'] += 2
    else:
        scores['amigro'] += 2
        scores['huntu'] += 1

    # Ajustes por industria
    if dominant_industry == 'tech':
        scores['huntu'] += 3
    elif dominant_industry == 'management':
        scores['huntRED®'] += 3
    elif dominant_industry == 'operations':
        scores['amigro'] += 3
    elif dominant_industry == 'strategy':
        scores['huntRED® Executive'] += 3

    # Ajustes por descripción
    if job_description:
        if any(term in job_desc_lower for term in ['migration', 'visa', 'bilingual', 'temporary', 'migración']):
            scores['amigro'] += 4
        if any(term in job_desc_lower for term in ['strategic', 'global', 'executive', 'board', 'estrategico']):
            scores['huntRED® Executive'] += 3
        if any(term in job_desc_lower for term in ['development', 'coding', 'software', 'data', 'programación']):
            scores['huntu'] += 3
        if any(term in job_desc_lower for term in ['operations', 'management', 'leadership', 'gerencia']):
            scores['huntRED®'] += 3

    # Ajustes por rango salarial
    if salary_range:
        min_salary, max_salary = salary_range
        avg_salary = (min_salary + max_salary) / 2
        if avg_salary > 120000:
            scores['huntRED® Executive'] += 4
            scores['huntRED®'] += 2
        elif avg_salary > 70000:
            scores['huntRED®'] += 3
            scores['huntu'] += 2
        elif avg_salary > 30000:
            scores['huntu'] += 2
            scores['amigro'] += 1
        else:
            scores['amigro'] += 3

    # Ajustes por experiencia requerida
    if required_experience is not None:
        if required_experience >= 12:
            scores['huntRED® Executive'] += 3
            scores['huntRED®'] += 2
        elif required_experience >= 7:
            scores['huntRED®'] += 3
            scores['huntu'] += 2
        elif required_experience >= 3:
            scores['huntu'] += 2
        else:
            scores['amigro'] += 2
            scores['huntu'] += 1

    # Ajustes por ubicación
    if location:
        if any(term in location_lower for term in ['usa', 'europe', 'asia', 'mexico', 'latam']):
            scores['amigro'] += 2  # Áreas con potencial migratorio
        if any(term in location_lower for term in ['silicon valley', 'new york', 'london']):
            scores['huntRED® Executive'] += 2  # Áreas de alta dirección/tecnología
            scores['huntu'] += 1

    # Resolver la unidad de negocio con mayor puntuación
    max_score = max(scores.values())
    candidates = [bu for bu, score in scores.items() if score == max_score]

    if candidates:
        # En caso de empate, se usa un orden de prioridad y se considera la industria dominante
        priority_order = ['huntRED® Executive', 'huntRED®', 'huntu', 'amigro']
        if len(candidates) > 1 and dominant_industry:
            if dominant_industry == 'strategy' and 'huntRED® Executive' in candidates:
                chosen_bu = 'huntRED® Executive'
            elif dominant_industry == 'management' and 'huntRED®' in candidates:
                chosen_bu = 'huntRED®'
            elif dominant_industry == 'tech' and 'huntu' in candidates:
                chosen_bu = 'huntu'
            elif dominant_industry == 'operations' and 'amigro' in candidates:
                chosen_bu = 'amigro'
            else:
                # Si no se resuelve con la industria, se usa el orden de prioridad
                for bu in priority_order:
                    if bu in candidates:
                        chosen_bu = bu
                        break
        else:
            # Si solo hay un candidato, lo elegimos directamente
            chosen_bu = candidates[0]

        # CAMBIO: Mapear el nombre a su correspondiente ID en la base de datos.
        try:
            bu_obj = BusinessUnit.objects.get(name=chosen_bu)
            return bu_obj.id
        except BusinessUnit.DoesNotExist:
            return None
    return None  # Sin coincidencia clara

def process_job_alert_email(mail, email_id, message):
    try:
        sender = message["From"]
        subject = message["Subject"]

        if not sender or not subject:
            return

        sender = sender.lower().strip()
        subject = subject.lower().strip()
        if sender not in VALID_SENDERS or not any(keyword in subject for keyword in ["job", "vacante", "alert"]):
            return  # No es un remitente o asunto válido

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
        mail.copy(email_id, FOLDER_CONFIG["error_folder"])
        mail.store(email_id, "+FLAGS", "\\Deleted")

def email_scraper():
    mail = connect_to_email()
    if not mail:
        return

    try:
        date_filter = (datetime.now() - timedelta(days=DAYS_TO_PROCESS)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE {date_filter})')
        if status != 'OK':
            logger.error("❌ Error en búsqueda de mensajes")
            return

        email_ids = messages[0].split()
        batch_size = 10  # Procesar en lotes de 50
        for i in range(0, len(email_ids), batch_size):
            batch_ids = email_ids[i:i + batch_size]
            for email_id in batch_ids:
                status, data = mail.fetch(email_id, "(RFC822)")
                if status != 'OK':
                    continue
                message = email.message_from_bytes(data[0][1])
                process_job_alert_email(mail, email_id, message)
            mail.expunge()  # Eliminar correos procesados después de cada lote
            time.sleep(2)  # Pausa de 1 segundo entre lotes
    except Exception as e:
        logger.error(f"❌ Error ejecutando email scraper: {e}")
    finally:
        mail.logout()