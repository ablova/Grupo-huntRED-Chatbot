# /home/pablo/app/utilidades/email_scraper.py
import email
import logging
import aiohttp
import environ
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from aioimaplib import aioimaplib
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parseaddr
from urllib.parse import urlparse
import trafilatura
from app.models import BusinessUnit, Vacante, ConfiguracionBU, WeightingModel
from app.utilidades.vacantes import VacanteManager
from asgiref.sync import sync_to_async
from app.chatbot.utils import clean_text  # Imported explicitly
from app.utilidades.scraping import validate_job_data, JobListing
from app.chatbot.nlp import NLPProcessor
from app.chatbot.integrations.services import send_email

logger = logging.getLogger(__name__)

# Global NLP Processor instance
NLP_PROCESSOR = NLPProcessor(language="es", mode="opportunity", analysis_depth="deep")

# Configuración de la cuenta IMAP
EMAIL_ACCOUNT = "pablo@huntred.com"
env = environ.Env()
environ.Env.read_env(env_file='/home/pablo/.env')
EMAIL_PASSWORD = env("EMAIL_HOST_PASSWORD")
IMAP_SERVER = env("EMAIL_HOST", default="mail.huntred.com")

# Variables de configuración
DAYS_TO_PROCESS = 10  # Últimos días a procesar
BATCH_SIZE = 10       # Tamaño del lote para procesar correos
SLEEP_TIME = 2        # Tiempo de espera entre lotes (segundos)

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
        'manager': 2, 'director': 3, 'leadership': 2, 'senior manager': 4, 'operations manager': 3,
        'project manager': 3, 'head of': 4, 'gerente': 2, 'director de': 3, 'jefe de': 4
    },
    'huntRED® Executive': {
        'strategic': 3, 'board': 4, 'global': 3, 'vp': 4, 'president': 4, 'cfo': 5, 'ceo': 5, 'coo': 5,
        'executive': 4, 'cto': 5, 'chief': 4, 'executive director': 5, 'senior vp': 5, 'vice president': 4,
        'estrategico': 3, 'global': 3, 'presidente': 4
    },
    'huntu': {
        'trainee': 3, 'junior': 3, 'entry-level': 4, 'intern': 3, 'graduate': 3, 'developer': 2, 'engineer': 2,
        'senior developer': 3, 'lead developer': 3, 'software engineer': 2, 'data analyst': 2, 'it specialist': 2,
        'technical lead': 3, 'architect': 3, 'analyst': 2, 'specialist': 2, 'consultant': 2, 'programador': 2,
        'ingeniero': 2, 'analista': 2
    },
    'amigro': {
        'migration': 4, 'bilingual': 3, 'visa sponsorship': 4, 'temporary job': 3, 'worker': 2, 'operator': 2,
        'constructor': 2, 'laborer': 2, 'assistant': 2, 'technician': 2, 'support': 2, 'seasonal': 2,
        'entry-level': 2, 'no experience': 3, 'trabajador': 2, 'operador': 2, 'asistente': 2, 'migración': 4
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

async def connect_to_email():
    """Conecta a la cuenta IMAP usando credenciales de la BD."""
    try:
        config = await sync_to_async(ConfiguracionBU.objects.filter)(business_unit__name="huntRED®").first()
        if not config:
            logger.error("⚠️ No ConfiguracionBU found for huntRED®")
            return None
        username = config.smtp_username or EMAIL_ACCOUNT
        password = config.smtp_password or EMAIL_PASSWORD
        if not username or not password:
            logger.error("⚠️ No email credentials found in DB")
            return None
        client = aioimaplib.IMAP4_SSL(IMAP_SERVER, 993)
        await client.wait_hello_from_server()
        await client.login(username, password)
        await client.select(FOLDER_CONFIG["jobs_folder"])
        logger.info(f"✅ Conectado al servidor IMAP: {IMAP_SERVER}")
        return client
    except Exception as e:
        logger.error(f"❌ Error conectando al servidor IMAP: {e}")
        return None

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
        resp, messages = await mail.search(f'SINCE {date_filter}')
        if resp != "OK":
            logger.error(f"❌ Error en búsqueda de mensajes para fecha {date_filter}")
            return

        email_ids = messages[0].split()
        logger.info(f"📬 Total de correos a procesar: {len(email_ids)}")

        for i in range(0, len(email_ids), BATCH_SIZE):
            batch_ids = email_ids[i:i + BATCH_SIZE]
            logger.info(f"📤 Procesando lote de {len(batch_ids)} correos (índices {i} a {i + len(batch_ids) - 1})")

            for email_id in batch_ids:
                resp, data = await mail.fetch(email_id, "(RFC822)")
                if resp != "OK":
                    logger.error(f"⚠️ No se pudo obtener correo {email_id}")
                    stats["errors"] += 1
                    continue
                message = email.message_from_bytes(data[0][1])
                await process_job_alert_email(mail, email_id, message, stats)
                await asyncio.sleep(SLEEP_TIME)

        await mail.expunge()
        logger.info("🗑️ Correos eliminados del inbox después de procesar todos los lotes")

        logger.info(f"📊 Estadísticas finales: Correos procesados: {stats['emails_processed']}, "
                   f"Vacantes encontradas: {stats['total_vacancies']}, Vacantes creadas: {stats['vacancies_created']}, "
                   f"Errores: {stats['errors']}")

    except Exception as e:
        logger.error(f"❌ Error ejecutando email_scraper: {e}")
    finally:
        await mail.logout()
        logger.info("🔌 Desconectado del servidor IMAP")


async def fetch_job_details(url: str, retries=3) -> dict:
    domain = urlparse(url).netloc.lower()
    if not any(allowed in domain for allowed in ALLOWED_DOMAINS):
        logger.warning(f"URL no permitida: {url}")
        return {}
    """Obtiene detalles completos de la vacante desde la URL."""
    timeout = aiohttp.ClientTimeout(total=30)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        for attempt in range(retries):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        text = trafilatura.extract(html)
                        details = {
                            "title": extract_title(soup),
                            "description": extract_description(soup),
                            "location": extract_location(soup),
                            "salary_range": extract_salary(soup),
                            "requirements": extract_requirements(soup),
                            "company_info": extract_company_info(soup),
                            "employment_type": extract_employment_type(soup),
                            "experience_level": extract_experience_level(soup),
                            "posting_date": extract_posting_date(soup),
                            "benefits": extract_benefits(soup),
                            "skills": await extract_skills(soup),  # Updated to use global NLP_PROCESSOR
                            "original_url": url
                        }
                        logger.info(f"✅ Detalles completos obtenidos de {url}")
                        return {k: v for k, v in details.items() if v}
            except Exception as e:
                logger.error(f"❌ Error en intento {attempt + 1}/{retries} para {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2)
    return {}

def extract_title(soup):
    """Extrae el título del puesto con mayor precisión."""
    title_candidates = [
        soup.find("h1"),
        soup.find("h1", class_=lambda x: x and any(word in x.lower() for word in ['job', 'title', 'position'])),
        soup.find(class_=lambda x: x and any(word in x.lower() for word in ['job-title', 'position-title']))
    ]
    for candidate in title_candidates:
        if candidate and candidate.text.strip():
            return clean_text(candidate.text)
    return None

def extract_description(soup):
    """Extrae la descripción completa del puesto."""
    description_selectors = [
        ("div", {"class_": ["job-description", "description", "details"]}),
        ("section", {"class_": ["job-description", "description"]}),
        ("div", {"id": lambda x: x and "description" in x.lower()})
    ]
    for tag, attrs in description_selectors:
        element = soup.find(tag, **attrs)
        if element:
            return clean_text(element.text)
    return None

def extract_location(soup):
    """Extrae la ubicación del puesto."""
    location_selectors = [
        ("span", {"class_": ["location", "job-location", "posting-location"]}),
        ("div", {"class_": ["location", "job-location"]}),
        ("meta", {"property": "jobLocation"}),
        ("div", {"data-automation-id": "location"})
    ]
    for tag, attrs in location_selectors:
        element = soup.find(tag, **attrs)
        if element:
            return clean_text(element.text)
    return None

def extract_salary(soup):
    """Extrae el rango salarial si está disponible."""
    salary_selectors = [
        ("span", {"class_": ["salary", "compensation"]}),
        ("div", {"class_": ["salary-range", "compensation-info"]}),
        ("div", {"data-automation-id": "salary"})
    ]
    for tag, attrs in salary_selectors:
        element = soup.find(tag, **attrs)
        if element:
            return clean_text(element.text)
    return None

def extract_requirements(soup):
    """Extrae requisitos del puesto."""
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

def extract_company_info(soup):
    """Extrae información de la empresa."""
    company_selectors = [
        ("div", {"class_": ["company-info", "employer-info"]}),
        ("span", {"class_": ["company-name", "employer"]}),
        ("div", {"data-automation-id": "company"})
    ]
    for tag, attrs in company_selectors:
        element = soup.find(tag, **attrs)
        if element:
            return clean_text(element.text)
    return None

def extract_employment_type(soup):
    """Extrae el tipo de empleo."""
    type_selectors = [
        ("span", {"class_": ["employment-type", "job-type"]}),
        ("div", {"class_": ["employment-info", "job-type"]}),
        ("div", {"data-automation-id": "employmentType"})
    ]
    for tag, attrs in type_selectors:
        element = soup.find(tag, **attrs)
        if element:
            return clean_text(element.text)
    return None

def extract_experience_level(soup):
    """Extrae el nivel de experiencia requerido."""
    exp_selectors = [
        ("span", {"class_": ["experience-level", "seniority"]}),
        ("div", {"class_": ["experience", "seniority-level"]})
    ]
    for tag, attrs in exp_selectors:
        element = soup.find(tag, **attrs)
        if element:
            return clean_text(element.text)
    return None

def extract_posting_date(soup):
    """Extrae la fecha de publicación."""
    date_selectors = [
        ("span", {"class_": ["posting-date", "job-date"]}),
        ("time", {}),
        ("meta", {"property": "datePosted"})
    ]
    for tag, attrs in date_selectors:
        element = soup.find(tag, **attrs)
        if element:
            return clean_text(element.get("datetime", element.text))
    return None

def extract_benefits(soup):
    """Extrae los beneficios ofrecidos."""
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

async def extract_skills(soup) -> List[str]:
    """Extrae habilidades del texto usando el NLPProcessor global."""
    description = extract_description(soup)
    if not description:
        return []
    try:
        skills_dict = NLP_PROCESSOR.extract_skills(description)
        skills = list(set(skills_dict["technical"] + skills_dict["soft"] + 
                         skills_dict["certifications"] + skills_dict["tools"]))
        return skills
    except Exception as e:
        logger.error(f"Error extrayendo habilidades: {e}")
        return []

async def extract_vacancies_from_html(html: str, sender: str, plain_text: str = None) -> list:
    """Extrae vacantes desde HTML o texto plano de manera asíncrona."""
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

        if "linkedin.com" in sender and "/jobs/view/" in href:
            job_title = link_text if link_text and not any(excluded in link_text for excluded in excluded_texts) else "Unknown Job"
            job_link = href if href.startswith("http") else f"https://{sender.split('@')[1]}{href}"
            company_name = sender.split('@')[1].split('.')[0].capitalize()
            details = await fetch_job_details(job_link)
            job_listings.append({
                "job_title": details.get("title", job_title),
                "job_link": job_link,
                "company_name": company_name,
                "job_description": details.get("description", job_title),
                "location": details.get("location", "Unknown"),
                "business_unit": None
            })
        elif "glassdoor.com" in sender and "joblistingid" in href:
            job_title = link_text if link_text and not any(excluded in link_text for excluded in excluded_texts) else "Unknown Job"
            job_link = href if href.startswith("http") else f"https://{sender.split('@')[1]}{href}"
            company_name = sender.split('@')[1].split('.')[0].capitalize()
            details = await fetch_job_details(job_link)
            job_listings.append({
                "job_title": details.get("title", job_title),
                "job_link": job_link,
                "company_name": company_name,
                "job_description": details.get("description", job_title),
                "location": details.get("location", "Unknown"),
                "business_unit": None
            })

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
                    details = await fetch_job_details(current_job["job_link"])
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
    """Determina la unidad de negocio para una vacante con pesos dinámicos."""
    job_title_lower = job_title.lower()
    job_desc_lower = job_description.lower() if job_description else ""
    location_lower = location.lower() if location else ""

    # Fetch all business units and their weights
    bu_candidates = await sync_to_async(list)(BusinessUnit.objects.all())
    scores = {bu.name: 0 for bu in bu_candidates}

    # Seniority scoring
    seniority_score = 0
    for keyword, score in SENIORITY_KEYWORDS.items():
        if keyword in job_title_lower:
            seniority_score = max(seniority_score, score)

    # Industry scoring
    industry_scores = {ind: 0 for ind in INDUSTRY_KEYWORDS}
    for ind, keywords in INDUSTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in job_title_lower or keyword in job_desc_lower:
                industry_scores[ind] += 1
    dominant_industry = max(industry_scores, key=industry_scores.get) if max(industry_scores.values()) > 0 else None

    # Dynamic scoring with weights
    for bu in bu_candidates:
        weighting = WeightingModel(bu)
        weights = weighting.get_weights("operativo")  # Adjust level dynamically if needed

        # Keyword scoring with weights
        for keyword, weight in BUSINESS_UNITS_KEYWORDS.get(bu.name, {}).items():
            if keyword in job_title_lower or (job_description and keyword in job_desc_lower):
                scores[bu.name] += weight * weights["hard_skills"]

        # Seniority adjustments
        if seniority_score >= 5:  # Roles muy senior (ejecutivos)
            if bu.name == 'huntRED® Executive':
                scores[bu.name] += 4 * weights["personalidad"]
            elif bu.name == 'huntRED®':
                scores[bu.name] += 2 * weights["soft_skills"]
        elif seniority_score >= 3:  # Roles de nivel medio a senior (gestión)
            if bu.name == 'huntRED®':
                scores[bu.name] += 3 * weights["soft_skills"]
            elif bu.name == 'huntu':
                scores[bu.name] += 1 * weights["hard_skills"]
        elif seniority_score >= 1:  # Roles junior a intermedios (técnicos)
            if bu.name == 'huntu':
                scores[bu.name] += 2 * weights["hard_skills"]
            elif bu.name == 'amigro':
                scores[bu.name] += 1 * weights["ubicacion"]
        else:  # Roles de nivel inicial o operativos
            if bu.name == 'amigro':
                scores[bu.name] += 3 * weights["ubicacion"]

        # Industry adjustments
        if dominant_industry:
            if dominant_industry == 'tech':
                if bu.name == 'huntu':
                    scores[bu.name] += 3 * weights["hard_skills"] * industry_scores['tech']
                elif bu.name == 'huntRED®':  # Para roles de gestión técnica
                    scores[bu.name] += 1 * weights["soft_skills"] * industry_scores['tech']
            elif dominant_industry == 'management':
                if bu.name == 'huntRED®':
                    scores[bu.name] += 3 * weights["soft_skills"] * industry_scores['management']
                elif bu.name == 'huntRED® Executive':
                    scores[bu.name] += 2 * weights["personalidad"] * industry_scores['management']
            elif dominant_industry == 'operations':
                if bu.name == 'amigro':
                    scores[bu.name] += 3 * weights["ubicacion"] * industry_scores['operations']
            elif dominant_industry == 'strategy':
                if bu.name == 'huntRED® Executive':
                    scores[bu.name] += 3 * weights["personalidad"] * industry_scores['strategy']
                elif bu.name == 'huntRED®':
                    scores[bu.name] += 1 * weights["soft_skills"] * industry_scores['strategy']

        # Description-based adjustments
        if job_description:
            if any(term in job_desc_lower for term in ['migration', 'visa', 'bilingual', 'temporary', 'migración']):
                if bu.name == 'amigro':
                    scores[bu.name] += 4 * weights["ubicacion"]
            if any(term in job_desc_lower for term in ['strategic', 'global', 'executive', 'board', 'estrategico']):
                if bu.name == 'huntRED® Executive':
                    scores[bu.name] += 3 * weights["personalidad"]
            if any(term in job_desc_lower for term in ['development', 'coding', 'software', 'data', 'programación']):
                if bu.name == 'huntu':
                    scores[bu.name] += 3 * weights["hard_skills"]
            if any(term in job_desc_lower for term in ['operations', 'management', 'leadership', 'gerencia']):
                if bu.name == 'huntRED®':
                    scores[bu.name] += 3 * weights["soft_skills"]

        # Salary range adjustments
        if salary_range:
            try:
                if isinstance(salary_range, str):
                    salary_range = salary_range.replace(',', '').replace('$', '').replace('k', '000')
                    if '-' in salary_range:
                        min_salary, max_salary = map(float, salary_range.split('-'))
                    elif salary_range.isdigit():
                        min_salary = max_salary = float(salary_range)
                    else:
                        min_salary = max_salary = 0
                else:
                    min_salary, max_salary = salary_range
                avg_salary = (min_salary + max_salary) / 2
                if avg_salary > 160000:
                    if bu.name == 'huntRED® Executive':
                        scores[bu.name] += 4 * weights["personalidad"]
                    elif bu.name == 'huntRED®':
                        scores[bu.name] += 2 * weights["soft_skills"]
                elif avg_salary > 70000:
                    if bu.name == 'huntRED®':
                        scores[bu.name] += 3 * weights["soft_skills"]
                    elif bu.name == 'huntu':
                        scores[bu.name] += 2 * weights["hard_skills"]
                elif avg_salary > 30000:
                    if bu.name == 'huntu':
                        scores[bu.name] += 2 * weights["hard_skills"]
                    elif bu.name == 'amigro':
                        scores[bu.name] += 1 * weights["ubicacion"]
                else:
                    if bu.name == 'amigro':
                        scores[bu.name] += 3 * weights["ubicacion"]
            except (ValueError, TypeError):
                logger.warning(f"⚠️ No se pudo parsear rango salarial: {salary_range}")

        # Experience adjustments
        if required_experience is not None:
            try:
                exp_years = float(required_experience) if isinstance(required_experience, (int, str)) else 0
                if exp_years >= 12:
                    if bu.name == 'huntRED® Executive':
                        scores[bu.name] += 3 * weights["personalidad"]
                    elif bu.name == 'huntRED®':
                        scores[bu.name] += 2 * weights["soft_skills"]
                elif exp_years >= 7:
                    if bu.name == 'huntRED®':
                        scores[bu.name] += 3 * weights["soft_skills"]
                    elif bu.name == 'huntu':
                        scores[bu.name] += 2 * weights["hard_skills"]
                elif exp_years >= 3:
                    if bu.name == 'huntu':
                        scores[bu.name] += 2 * weights["hard_skills"]
                else:
                    if bu.name == 'amigro':
                        scores[bu.name] += 2 * weights["ubicacion"]
                    elif bu.name == 'huntu':
                        scores[bu.name] += 1 * weights["hard_skills"]
            except ValueError:
                logger.warning(f"⚠️ No se pudo parsear experiencia requerida: {required_experience}")

        # Location adjustments
        if location:
            if any(term in location_lower for term in ['usa', 'europe', 'asia', 'mexico', 'latam', 'frontera', 'migración']):
                if bu.name == 'amigro':
                    scores[bu.name] += 3 * weights["ubicacion"]
            if any(term in location_lower for term in ['silicon valley', 'new york', 'london']):
                if bu.name == 'huntRED® Executive':
                    scores[bu.name] += 2 * weights["personalidad"]
                elif bu.name == 'huntu':
                    scores[bu.name] += 1 * weights["hard_skills"]

    # Selección de la unidad de negocio
    max_score = max(scores.values())
    candidates = [bu for bu, score in scores.items() if score == max_score]
    priority_order = ['huntRED® Executive', 'huntRED®', 'huntu', 'amigro']

    if candidates:
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
    else:
        chosen_bu = 'huntRED®'  # Default fallback

    try:
        bu_obj = await sync_to_async(BusinessUnit.objects.get)(name=chosen_bu)
        logger.info(f"✅ Unidad de negocio asignada: {chosen_bu} (ID: {bu_obj.id}) para '{job_title}'")
        return bu_obj.id
    except BusinessUnit.DoesNotExist:
        logger.warning(f"⚠️ Unidad de negocio '{chosen_bu}' no encontrada, usando huntRED® por defecto")
        try:
            default_bu = await sync_to_async(BusinessUnit.objects.get)(id=1)
            logger.info(f"🔧 Asignada huntRED® por defecto (ID: {default_bu.id}) para '{job_title}'")
            return default_bu.id
        except BusinessUnit.DoesNotExist:
            logger.error(f"❌ Unidad de negocio por defecto 'huntRED®' no encontrada en BD")
            return None

async def process_job_alert_email(mail, email_id, message, stats):
    """Procesa un correo de alerta de empleo y reporta errores al administrador."""
    try:
        sender = message["From"]
        subject = message["Subject"]

        if not sender or not subject:
            logger.warning(f"⚠️ Correo {email_id} sin remitente o asunto")
            stats["errors"] += 1
            return

        sender = sender.lower().strip()
        subject = subject.lower().strip()
        _, sender_email = parseaddr(sender)
        sender_email = sender_email.lower().strip()

        if sender_email in VALID_SENDERS or any(keyword in subject for keyword in JOB_KEYWORDS):
            logger.info(f"📧 Procesando correo {email_id} de {sender_email}")
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
                stats["errors"] += 1
                return

            job_listings = await extract_vacancies_from_html(body or "", sender_email, plain_text)
            logger.info(f"📑 Vacantes encontradas: {len(job_listings)}")
            stats["total_vacancies"] += len(job_listings)

            for job_data in job_listings:
                description = job_data.get("job_description", "")
                if description:
                    analysis = NLP_PROCESSOR.analyze_opportunity(description)
                    job_data["skills"] = analysis["details"].get("skills", job_data.get("skills", []))
                    job_data["location"] = analysis["details"].get("location") or job_data.get("location", "Unknown")
                    job_data["contract_type"] = analysis["details"].get("contract_type") or job_data.get("contract_type")
                    job_data["job_classification"] = analysis["job_classification"]
                    job_data["sentiment"] = analysis["sentiment"]

                business_unit_id = await assign_business_unit(
                    job_data["job_title"],
                    job_data["job_description"],
                    job_data.get("salary_range"),
                    job_data.get("experience_level"),
                    job_data.get("location")
                )

                if business_unit_id:
                    success = await create_vacancy_from_email(job_data, business_unit_id)
                    if success:
                        stats["vacancies_created"] += 1
                    else:
                        stats["errors"] += 1
                else:
                    logger.warning(f"⚠️ No se asignó unidad de negocio para '{job_data['job_title']}'")
                    stats["errors"] += 1

            await mail.copy(email_id, FOLDER_CONFIG["parsed_folder"])
            await mail.store(email_id, "+FLAGS", "\\Deleted")
            logger.info(f"📩 Correo {email_id} movido a {FOLDER_CONFIG['parsed_folder']}")

    except Exception as e:
        logger.error(f"❌ Error procesando correo {email_id}: {e}")
        await mail.copy(email_id, FOLDER_CONFIG["error_folder"])
        await mail.store(email_id, "+FLAGS", "\\Deleted")
        stats["errors"] += 1
        bu = await sync_to_async(BusinessUnit.objects.get)(name="huntRED®")
        if bu and bu.admin_email:
            await send_email(
                business_unit_name=bu.name,
                subject=f"Email Scraper Error: {email_id}",
                to_email=bu.admin_email,
                body=f"Error processing email {email_id}: {str(e)}",
                from_email="noreply@huntred.com"
            )

async def create_vacancy_from_email(job_data: dict, business_unit_id: int) -> bool:
    """Crea una nueva vacante desde datos de email."""
    try:
        job_listing = JobListing(
            title=job_data["job_title"],
            location=job_data["location"],
            company=job_data["company_name"],
            description=job_data["job_description"],
            url=job_data["job_link"],
            skills=job_data.get("skills", []),
            posted_date=job_data.get("posting_date"),
            salary=job_data.get("salary_range"),
            responsible=job_data.get("responsible"),
            contract_type=job_data.get("employment_type"),
            job_type=job_data.get("job_type"),
            benefits=job_data.get("benefits", [])
        )
        
        validated_data = validate_job_data(job_listing)
        if not validated_data:
            logger.error(f"❌ Datos inválidos para vacante: {job_data['job_title']}")
            return False
            
        vacante_manager = VacanteManager(validated_data)
        result = await vacante_manager.create_job_listing()
        
        if result:
            logger.info(f"✅ Vacante creada exitosamente: {job_data['job_title']}")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Error creando vacante: {e}")
        return False