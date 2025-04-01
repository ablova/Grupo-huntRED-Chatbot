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

logger = logging.getLogger(__name__)

# Configuración de logging profesional
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

# Lista de remitentes válidos (ampliable)
VALID_SENDERS = [
    'jobs-noreply@linkedin.com', 'jobalerts-noreply@linkedin.com', 'jobs-listings@linkedin.com',
    'alerts@glassdoor.com', 'noreply@glassdoor.com', 'TalentCommunity@talent.honeywell.com',
    'santander@myworkday.com'
]

# Dominios permitidos para solicitudes HTTP (ampliable)
ALLOWED_DOMAINS = {
    "linkedin.com", "www.linkedin.com", "mx.linkedin.com", "*.linkedin.com",
    "glassdoor.com", "www.glassdoor.com", "*.glassdoor",
    "honeywell.com", "careers.honeywell.com", "*.honeywell.com",
    "myworkday.com", "santander.wd3.myworkdayjobs.com", "workday.com", "*.santander.com",
    "indeed.com", "*.indeed.com", "computrabajo.com", "*.computrabajo.com"  # Añadidos para más fuentes
}

# Palabras clave para identificar correos de empleo (ampliadas)
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
    # Conectar al servidor IMAP (asumimos que esta función ya existe y funciona)
    mail = await connect_to_email(email_account)
    if not mail:
        logger.error(f"No se pudo conectar al servidor IMAP para {email_account}")
        return {"emails_processed": 0, "total_vacancies": 0, "vacancies_created": 0, "errors": 1}

    stats = {"emails_processed": 0, "total_vacancies": 0, "vacancies_created": 0, "errors": 0}

    try:
        # Seleccionar la carpeta (ajusta esto si es necesario)
        await mail.select("INBOX.Jobs")  # Verifica si esta es la carpeta correcta

        # Filtro de fecha para buscar correos recientes
        date_filter = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        logger.debug(f"Buscando correos desde {date_filter}")
        resp, messages = await mail.search(None, f'SINCE {date_filter}')
        if resp != "OK":
            logger.error(f"Error en búsqueda de mensajes: {resp}")
            stats["errors"] += 1
            return stats

        email_ids = messages[0].split()  # Lista de IDs en bytes, ej: [b'1', b'2', ...]
        logger.info(f"Total de correos encontrados para {email_account}: {len(email_ids)}")
        if not email_ids:
            logger.warning("No se encontraron correos en el rango de fechas")
            return stats

        # Procesar un lote de correos
        batch_ids = email_ids[:batch_size]
        logger.info(f"Procesando lote de {len(batch_ids)} correos")

        tasks = []
        for email_id_bytes in batch_ids:
            email_id = email_id_bytes.decode()  # Convertir bytes a string
            try:
                resp, data = await mail.fetch(email_id, "(RFC822)")
                if resp == "OK" and data and isinstance(data[0], tuple) and len(data[0]) > 1:
                    message = email.message_from_bytes(data[0][1])
                    tasks.append(process_job_alert_email(mail, email_id, message, stats, enable_move))
                else:
                    logger.error(f"No se pudo obtener el contenido del correo {email_id}: {resp}")
                    stats["errors"] += 1
            except Exception as e:
                logger.error(f"Error al procesar el correo {email_id}: {e}")
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

def is_job_email(subject: str) -> bool:
    return any(pattern.search(subject) for pattern in JOB_SUBJECT_PATTERNS)

async def fetch_job_details(url: str, retries=3) -> Dict:
    domain = urlparse(url).netloc.lower()
    if not any(allowed in domain for allowed in ALLOWED_DOMAINS):
        logger.warning(f"URL no permitida: {url}")
        return {}
    timeout = aiohttp.ClientTimeout(total=30)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        for attempt in range(retries):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        details = {
                            "title": extract_field(html, ["h1", "h2", "h3", "span.job-title", "a.job-title"]),
                            "description": extract_field(html, ["div.job-description", "section.job-description", "div[id*=description]"]),
                            "location": extract_field(html, ["span.location", "span.job-location", "div.companyLocation"]),
                            "salary_range": extract_field(html, ["span.salary", "div.salary-range"]),
                            "requirements": extract_requirements(html),
                            "company_info": extract_field(html, ["div.company-info", "span.company-name"]),
                            "employment_type": extract_field(html, ["span.employment-type", "div.employment-info"]),
                            "experience_level": extract_field(html, ["span.experience-level", "div.experience"]),
                            "posting_date": extract_field(html, ["span.posting-date", "time"]),
                            "benefits": extract_benefits(html),
                            "skills": await extract_skills(html),
                            "original_url": url
                        }
                        logger.debug(f"Detalles obtenidos de {url}: {details}")
                        return {k: v for k, v in details.items() if v}
            except Exception as e:
                logger.error(f"Error en intento {attempt + 1}/{retries} para {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2)
    return {}

def extract_requirements(html: str) -> Optional[List[str]]:
    soup = BeautifulSoup(html, "html.parser")
    req_selectors = [
        ("div", {"class_": ["requirements", "qualifications"]}),
        ("ul", {"class_": ["requirements-list", "qualifications-list"]}),
        ("div", {"id": lambda x: x and "requirements" in x.lower()})
    ]
    requirements = []
    for tag, attrs in req_selectors:
        elements = soup.find_all(tag, **attrs)
        for element in elements:
            if element.find_all('li'):
                requirements.extend([clean_text(li.text) for li in element.find_all('li')])
            else:
                requirements.append(clean_text(element.text))
    return requirements if requirements else None

def extract_benefits(html: str) -> Optional[List[str]]:
    soup = BeautifulSoup(html, "html.parser")
    benefits_selectors = [
        ("div", {"class_": ["benefits", "perks"]}),
        ("ul", {"class_": ["benefits-list", "perks-list"]})
    ]
    benefits = []
    for tag, attrs in benefits_selectors:
        elements = soup.find_all(tag, **attrs)
        for element in elements:
            if element.find_all('li'):
                benefits.extend([clean_text(li.text) for li in element.find_all('li')])
            else:
                benefits.append(clean_text(element.text))
    return benefits if benefits else None

async def extract_vacancies_from_html(html: str, sender: str, plain_text: str = None) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    job_listings = []
    excluded_texts = ["sign in", "ayuda", "darse de baja", "help", "unsubscribe", "feed", "profile", "premium"]
    excluded_domains = ["linkedin.com/help", "linkedin.com/comm/feed", "linkedin.com/comm/in/"]
    job_containers = soup.find_all("a", href=True)
    seen_urls = set()

    for link in job_containers:
        link_text = link.get_text(strip=True).lower()
        href = link["href"].lower()
        if any(excluded in link_text for excluded in excluded_texts) or any(domain in href for domain in excluded_domains):
            continue
        base_url = href.split("?")[0] if "?" in href else href
        if base_url in seen_urls:
            continue
        seen_urls.add(base_url)

        # Extraer cualquier enlace que parezca una oportunidad de empleo
        if "http" in href and any(keyword in link_text for keyword in JOB_KEYWORDS):
            job_title = link_text if link_text else "Unknown Job"
            job_link = href if href.startswith("http") else f"https://{sender.split('@')[1]}{href}"
            company_name = sender.split('@')[1].split('.')[0].capitalize() if '@' in sender else "Unknown Company"
            details = await fetch_job_details(job_link)
            job_listings.append({
                "job_title": details.get("title", job_title),
                "job_link": job_link,
                "company_name": details.get("company", company_name),
                "job_description": details.get("description", job_title),
                "location": details.get("location", "Unknown"),
                "business_unit": None
            })

    if not job_listings and plain_text:
        job_listings.extend(extract_from_plain_text(plain_text))

    logger.debug(f"Total de vacantes extraídas del HTML/texto: {len(job_listings)}")
    return job_listings

def extract_from_plain_text(plain_text: str) -> List[Dict]:
    job_listings = []
    lines = plain_text.split('\n')
    current_job = {}
    for line in lines:
        line = line.strip()
        if any(keyword in line.lower() for keyword in JOB_KEYWORDS):
            if current_job:
                job_listings.append(current_job)
            current_job = {"job_title": line}
        elif "http" in line and current_job:
            current_job["job_link"] = line
        elif current_job:
            current_job["job_description"] = current_job.get("job_description", "") + " " + line
    if current_job:
        job_listings.append(current_job)
    return job_listings

async def process_job_alert_email(mail, email_id: str, message, stats: Dict[str, int], enable_move: bool = False):
    try:
        sender = message["From"]
        subject = message["Subject"]
        if not sender or not subject:
            logger.warning(f"Correo {email_id} sin remitente o asunto")
            stats["errors"] += 1
            if enable_move:
                await mail.copy(email_id, FOLDER_CONFIG["error_folder"])
                await mail.store(email_id, "+FLAGS", "\\Deleted")
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
                if enable_move:
                    await mail.copy(email_id, FOLDER_CONFIG["error_folder"])
                    await mail.store(email_id, "+FLAGS", "\\Deleted")
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
        if enable_move:
            await mail.copy(email_id, FOLDER_CONFIG["error_folder"])
            await mail.store(email_id, "+FLAGS", "\\Deleted")
        try:
            bu = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
            admin_email = await sync_to_async(lambda: bu.admin_email)() if bu else None
            if bu and admin_email:
                await send_email(
                    business_unit_name=bu.name,
                    subject=f"Email Scraper Error: {email_id}",
                    to_email=admin_email,
                    body=f"Error processing email {email_id}: {str(e)}",
                    from_email="noreply@huntred.com"
                )
        except Exception as admin_e:
            logger.error(f"Error enviando correo de error: {admin_e}")

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
                "fecha_publicacion": job_data.get("posting_date", now()),
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