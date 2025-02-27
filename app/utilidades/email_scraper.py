# /home/pablo/app/utilidades/email_scraper.py
import imaplib
import email
import logging
import aiohttp
import environ
import asyncio
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parseaddr
from bs4 import BeautifulSoup
from app.models import ConfiguracionBU, Vacante, BusinessUnit
from app.utilidades.vacantes import VacanteManager
from asgiref.sync import sync_to_async
import time

# Configuración del logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configuración de la cuenta IMAP
EMAIL_ACCOUNT = "pablo@huntred.com"
env = environ.Env()
environ.Env.read_env(env_file='/home/pablo/.env')
EMAIL_PASSWORD = env("EMAIL_HOST_PASSWORD")
IMAP_SERVER = env("EMAIL_HOST", default="mail.huntred.com")
IMAP_FOLDER = "INBOX"

# Variables de configuración
DAYS_TO_PROCESS = 3  # Últimos días a procesar
BATCH_SIZE = 10      # Tamaño del lote para procesar correos
SLEEP_TIME = 2       # Tiempo de espera entre lotes (segundos)

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
    "myworkday.com", "santander.wd3.myworkdayjobs.com", "workday.com", "*.santander.com"
}

# Palabras clave para identificar correos de empleo
JOB_KEYWORDS = [
    'job', 'vacante', 'opportunity', 'empleo', 'position', 'opening', 'alert',
    'oportunidad', 'subdirector', 'director', 'trabajo', 'oferta laboral',
    'reclutamiento', 'contratación', 'convocatoria', 'anuncio laboral',
    'job offer', 'career', 'postulación', 'apply now', 'new jobs'
]

# Configuración de carpetas IMAP
FOLDER_CONFIG = {
    "inbox": "INBOX",
    "jobs_folder": "INBOX.Jobs",
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

# Constantes para assign_business_unit
BUSINESS_UNITS_KEYWORDS = {
    'huntRED®': {
        'manager': 2, 'director': 3, 'leadership': 2,
        'senior manager': 4, 'operations manager': 3, 'project manager': 3, 'head of': 4,
        'gerente': 2, 'director de': 3, 'jefe de': 4
    },
    'huntRED® Executive': {
        'strategic': 3, 'board': 4, 'global': 3, 'vp': 4, 'president': 4, 'cfo': 5, 'ceo': 5, 'coo': 5, 'executive': 4,
        'cto': 5, 'chief': 4, 'executive director': 5, 'senior vp': 5, 'vice president': 4,
        'estrategico': 3, 'global': 3, 'presidente': 4
    },
    'huntu': {
        'trainee': 3, 'junior': 3, 'entry-level': 4, 'intern': 3, 'graduate': 3,
        'developer': 2, 'engineer': 2, 'senior developer': 3, 'lead developer': 3,
        'software engineer': 2, 'data analyst': 2, 'it specialist': 2, 'technical lead': 3,
        'architect': 3, 'analyst': 2, 'specialist': 2, 'consultant': 2, 'programador': 2,
        'ingeniero': 2, 'analista': 2
    },
    'amigro': {
        'migration': 4, 'bilingual': 3, 'visa sponsorship': 4, 'temporary job': 3,
        'worker': 2, 'operator': 2, 'constructor': 2, 'laborer': 2, 'assistant': 2,
        'technician': 2, 'support': 2, 'seasonal': 2, 'entry-level': 2, 'no experience': 3,
        'trabajador': 2, 'operador': 2, 'asistente': 2, 'migración': 4
    }
}

SENIORITY_KEYWORDS = {
    'junior': 1, 'entry-level': 1, 'mid-level': 2, 'senior': 3, 'lead': 3,
    'manager': 4, 'director': 5, 'vp': 5, 'executive': 5, 'chief': 5, 'jefe': 4
}

INDUSTRY_KEYWORDS = {
    'tech': {'developer', 'engineer', 'software', 'data', 'it', 'architect', 'programador', 'ingeniero'},
    'management': {'manager', 'director', 'executive', 'leadership', 'gerente', 'jefe'},
    'operations': {'operator', 'worker', 'constructor', 'technician', 'trabajador', 'operador'},
    'strategy': {'strategic', 'global', 'board', 'president', 'estrategico'}
}

@sync_to_async
def connect_to_email():
    """Conecta a la cuenta IMAP usando credenciales de la BD."""
    global EMAIL_ACCOUNT, EMAIL_PASSWORD
    try:
        # Aquí asumimos que tienes una tabla ConfiguracionBU para obtener credenciales
        config = ConfiguracionBU.objects.filter(business_unit__name="huntRED®").first()
        if config:
            EMAIL_ACCOUNT = config.email_account
            EMAIL_PASSWORD = config.email_password
        if not EMAIL_ACCOUNT or not EMAIL_PASSWORD:
            print("⚠️ No se encontraron credenciales de email en la BD.")
            return None
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")  # Ajusta el nombre de la carpeta si es diferente
        mail.select(FOLDER_CONFIG["jobs_folder"])
        print(f"✅ Conectado al servidor IMAP: {IMAP_SERVER}")
        return mail
    except Exception as e:
        print(f"❌ Error conectando al servidor IMAP: {e}")
        return None

async def fetch_job_details(url: str, retries=3) -> dict:
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    if domain not in ALLOWED_DOMAINS:
        logger.warning(f"🚫 Solicitud bloqueada a dominio no permitido: {domain}")
        return {}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for attempt in range(retries):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        title = soup.find("h1") or soup.find("title")
                        description = soup.find("div", class_=["job-description", "description", "content"])
                        location = soup.find(lambda tag: tag.name in ["span", "div"] and "location" in tag.get("class", []) or "location" in tag.text.lower())
                        details = {
                            "title": title.text.strip() if title else "Unknown",
                            "description": description.text.strip() if description else "No description",
                            "location": location.text.strip() if location else "Unknown"
                        }
                        logger.info(f"✅ Detalles obtenidos de {url}")
                        return details
                    else:
                        logger.warning(f"Intento {attempt + 1}/{retries} falló para {url}. Estado: {response.status}")
            except Exception as e:
                logger.error(f"Intento {attempt + 1}/{retries} falló para {url}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(SLEEP_TIME)
    logger.error(f"❌ Fallaron todos los intentos para {url}")
    return {}

def extract_vacancies_from_html(html: str, sender: str, plain_text: str = None) -> list:
    """Extrae vacantes desde HTML o texto plano."""
    soup = BeautifulSoup(html, "html.parser")
    job_listings = []

    # Extracción estructurada desde HTML
    job_containers = soup.find_all("a", href=True)
    for link in job_containers:
        link_text = link.get_text(strip=True).lower()
        href = link["href"].lower()
        if any(keyword in link_text or keyword in href for keyword in JOB_KEYWORDS):
            job_title = link_text or "Unknown Job"
            job_link = href if href.startswith("http") else f"https://{sender.split('@')[1]}{href}"
            company_name = sender.split('@')[1].split('.')[0].capitalize()

            logger.info(f"🔍 Encontrado enlace de vacante: {job_link}")
            print(f"🔍 Encontrado enlace de vacante: {job_link}")
            details = asyncio.run(fetch_job_details(job_link))
            job_listings.append({
                "job_title": details.get("title", job_title),
                "job_link": job_link,
                "company_name": company_name,
                "job_description": details.get("description", job_title),
                "location": details.get("location", "Unknown"),
                "business_unit": None
            })

    # Fallback a texto plano si no se encontraron enlaces en HTML
    if not job_listings and plain_text:
        lines = plain_text.split('\n')
        current_job = {}
        for line in lines:
            line = line.strip().lower()
            if any(keyword in line for keyword in JOB_KEYWORDS) and not current_job.get("job_title"):
                current_job["job_title"] = line.title()
                current_job["company_name"] = sender.split('@')[1].split('.')[0].capitalize()
            elif "apply now" in line and current_job.get("job_title"):
                apply_link = soup.find("a", string=lambda text: text and "apply now" in text.lower())
                current_job["job_link"] = apply_link["href"] if apply_link else ""
                if current_job["job_link"]:
                    details = asyncio.run(fetch_job_details(current_job["job_link"]))
                    current_job.update({
                        "job_title": details.get("title", current_job["job_title"]),
                        "job_description": details.get("description", current_job["job_title"]),
                        "location": details.get("location", "Unknown")
                    })
                job_listings.append(current_job)
                current_job = {}
            elif current_job.get("job_title") and not current_job.get("location"):
                current_job["location"] = line if line else "Unknown"
            elif current_job.get("job_title"):
                current_job["job_description"] = current_job.get("job_description", "") + " " + line

    return job_listings

async def assign_business_unit(job_title, job_description=None, salary_range=None, required_experience=None, location=None):
    """Determina la unidad de negocio para una vacante."""
    job_title_lower = job_title.lower()
    job_desc_lower = job_description.lower() if job_description else ""
    location_lower = location.lower() if location else ""

    seniority_score = 0
    for keyword, score in SENIORITY_KEYWORDS.items():
        if keyword in job_title_lower:
            seniority_score = max(seniority_score, score)

    industry_scores = {ind: 0 for ind in INDUSTRY_KEYWORDS}
    for ind, keywords in INDUSTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in job_title_lower or keyword in job_desc_lower:
                industry_scores[ind] += 1
    dominant_industry = max(industry_scores, key=industry_scores.get) if max(industry_scores.values()) > 0 else None

    scores = {bu: 0 for bu in BUSINESS_UNITS_KEYWORDS}
    for bu, keywords in BUSINESS_UNITS_KEYWORDS.items():
        for keyword, weight in keywords.items():
            if keyword in job_title_lower or (job_description and keyword in job_desc_lower):
                scores[bu] += weight

    if seniority_score >= 4:
        scores['huntRED®'] += 3
        scores['huntRED® Executive'] += 2
    elif seniority_score >= 2:
        scores['huntu'] += 2
    else:
        scores['amigro'] += 2
        scores['huntu'] += 1

    if dominant_industry == 'tech':
        scores['huntu'] += 3
    elif dominant_industry == 'management':
        scores['huntRED®'] += 3
    elif dominant_industry == 'operations':
        scores['amigro'] += 3
    elif dominant_industry == 'strategy':
        scores['huntRED® Executive'] += 3

    if job_description:
        if any(term in job_desc_lower for term in ['migration', 'visa', 'bilingual', 'temporary', 'migración']):
            scores['amigro'] += 4
        if any(term in job_desc_lower for term in ['strategic', 'global', 'executive', 'board', 'estrategico']):
            scores['huntRED® Executive'] += 3
        if any(term in job_desc_lower for term in ['development', 'coding', 'software', 'data', 'programación']):
            scores['huntu'] += 3
        if any(term in job_desc_lower for term in ['operations', 'management', 'leadership', 'gerencia']):
            scores['huntRED®'] += 3

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

    if location:
        if any(term in location_lower for term in ['usa', 'europe', 'asia', 'mexico', 'latam']):
            scores['amigro'] += 2
        if any(term in location_lower for term in ['silicon valley', 'new york', 'london']):
            scores['huntRED® Executive'] += 2
            scores['huntu'] += 1

    max_score = max(scores.values())
    candidates = [bu for bu, score in scores.items() if score == max_score]

    if candidates:
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
                for bu in priority_order:
                    if bu in candidates:
                        chosen_bu = bu
                        break
        else:
            chosen_bu = candidates[0]

        try:
            bu_obj = await sync_to_async(BusinessUnit.objects.get)(name=chosen_bu)
            logger.info(f"✅ Unidad de negocio asignada: {chosen_bu} (ID: {bu_obj.id}) para '{job_title}'")
            print(f"✅ Unidad de negocio asignada: {chosen_bu} (ID: {bu_obj.id}) para '{job_title}'")
            return bu_obj.id
        except BusinessUnit.DoesNotExist:
            logger.warning(f"⚠️ Unidad de negocio '{chosen_bu}' no encontrada en BD para '{job_title}'")
            print(f"⚠️ Unidad de negocio '{chosen_bu}' no encontrada en BD para '{job_title}'")

    logger.warning(f"⚠️ Sin coincidencia de unidad de negocio para '{job_title}', usando huntRED® por defecto")
    print(f"⚠️ Sin coincidencia de unidad de negocio para '{job_title}', usando huntRED® por defecto")
    try:
        default_bu = await sync_to_async(BusinessUnit.objects.get)(id=1)
        logger.info(f"🔧 Asignada huntRED® por defecto (ID: {default_bu.id}) para '{job_title}'")
        print(f"🔧 Asignada huntRED® por defecto (ID: {default_bu.id}) para '{job_title}'")
        return default_bu.id
    except BusinessUnit.DoesNotExist:
        logger.error(f"❌ Unidad de negocio por defecto 'huntRED®' no encontrada en BD")
        print(f"❌ Unidad de negocio por defecto 'huntRED®' no encontrada en BD")
        return None

async def process_job_alert_email(mail, email_id, message, stats):
    try:
        sender = message["From"]
        subject = message["Subject"]

        if not sender or not subject:
            logger.warning(f"⚠️ Correo {email_id} sin remitente o asunto, saltando")
            print(f"⚠️ Correo {email_id} sin remitente o asunto, saltando")
            stats["errors"] += 1
            return

        sender = sender.lower().strip()
        subject = subject.lower().strip()
        _, sender_email = parseaddr(sender)
        sender_email = sender_email.lower().strip()

        if sender_email in VALID_SENDERS or any(keyword in subject for keyword in JOB_KEYWORDS):
            logger.info(f"📧 Procesando correo {email_id} de {sender_email} con asunto '{subject}'")
            print(f"📧 Procesando correo {email_id} de {sender_email} con asunto '{subject}'")
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
                logger.warning(f"⚠️ Correo {email_id} sin contenido procesable")
                print(f"⚠️ Correo {email_id} sin contenido procesable")
                stats["errors"] += 1
                return

            job_listings = extract_vacancies_from_html(body or "", sender_email, plain_text)
            logger.info(f"📑 Vacantes encontradas en correo {email_id}: {len(job_listings)}")
            print(f"📑 Vacantes encontradas en correo {email_id}: {len(job_listings)}")
            stats["total_vacancies"] += len(job_listings)

            if not job_listings:
                logger.warning(f"⚠️ No se detectaron vacantes en el correo {email_id}")
                print(f"⚠️ No se detectaron vacantes en el correo {email_id}")
                return

            for job_data in job_listings:
                business_unit_id = await assign_business_unit(job_data["job_title"], job_data["job_description"])
                if business_unit_id:
                    job_data["business_unit"] = business_unit_id
                else:
                    logger.warning(f"⚠️ No se asignó unidad de negocio para '{job_data['job_title']}'")
                    print(f"⚠️ No se asignó unidad de negocio para '{job_data['job_title']}'")
                    stats["errors"] += 1
                    continue

                vacante_manager = VacanteManager(job_data)
                try:
                    result = await vacante_manager.create_job_listing()
                    logger.info(f"✅ Vacante '{job_data['job_title']}' creada con éxito. Resultado: {result}")
                    print(f"✅ Vacante '{job_data['job_title']}' creada con éxito. Resultado: {result}")
                    stats["vacancies_created"] += 1
                except Exception as e:
                    logger.error(f"❌ Error al crear vacante '{job_data['job_title']}': {e}")
                    print(f"❌ Error al crear vacante '{job_data['job_title']}': {e}")
                    stats["errors"] += 1

            mail.copy(email_id, FOLDER_CONFIG["parsed_folder"])
            mail.store(email_id, "+FLAGS", "\\Deleted")
            logger.info(f"📩 Correo {email_id} movido a {FOLDER_CONFIG['parsed_folder']}")
            print(f"📩 Correo {email_id} movido a {FOLDER_CONFIG['parsed_folder']}")
        else:
            logger.info(f"📧 Correo {email_id} de {sender_email} con asunto '{subject}' no coincide con criterios, saltando")
            print(f"📧 Correo {email_id} de {sender_email} con asunto '{subject}' no coincide con criterios, saltando")
    except Exception as e:
        logger.error(f"❌ Error procesando correo {email_id}: {e}")
        print(f"❌ Error procesando correo {email_id}: {e}")
        mail.copy(email_id, FOLDER_CONFIG["error_folder"])
        mail.store(email_id, "+FLAGS", "\\Deleted")
        stats["errors"] += 1

async def email_scraper():
    mail = await connect_to_email()
    if not mail:
        return

    stats = {
        "emails_processed": 0,
        "total_vacancies": 0,
        "vacancies_created": 0,
        "errors": 0
    }

    try:
        date_filter = (datetime.now() - timedelta(days=DAYS_TO_PROCESS)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE {date_filter})')
        if status != 'OK':
            print(f"❌ Error en búsqueda de mensajes para fecha {date_filter}")
            return

        email_ids = messages[0].split()
        print(f"📬 Total de correos a procesar: {len(email_ids)}")

        for i in range(0, len(email_ids), BATCH_SIZE):
            batch_ids = email_ids[i:i + BATCH_SIZE]
            print(f"📤 Procesando lote de {len(batch_ids)} correos (índices {i} a {i + len(batch_ids) - 1})")

            for email_id in batch_ids:
                status, data = mail.fetch(email_id, "(RFC822)")
                if status != 'OK':
                    print(f"⚠️ No se pudo obtener correo {email_id}")
                    stats["errors"] += 1
                    continue
                message = email.message_from_bytes(data[0][1])
                await process_job_alert_email(mail, email_id, message, stats)

            mail.expunge()
            print(f"🗑️ Correos eliminados del inbox después del lote")
            await asyncio.sleep(SLEEP_TIME)

        print(f"📊 Estadísticas finales: Correos procesados: {stats['emails_processed']}, "
              f"Vacantes encontradas: {stats['total_vacancies']}, Vacantes creadas: {stats['vacancies_created']}, "
              f"Errores: {stats['errors']}")

    except Exception as e:
        print(f"❌ Error ejecutando email_scraper: {e}")
    finally:
        mail.logout()
        print("🔌 Desconectado del servidor IMAP")

if __name__ == "__main__":
    asyncio.run(email_scraper())
