# /home/pablo/app/scraping.py (Parte 1)

import json
import asyncio
import logging
import random
import aiohttp
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
from django.db import transaction
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from prometheus_client import Counter, Histogram, start_http_server
import spacy
from app.chatbot.nlp import NLPProcessor
from app.models import (
    DominioScraping, Vacante, RegistroScraping, ConfiguracionBU, BusinessUnit, Worker
)
from app.utilidades.loader import DIVISION_SKILLS
from app.models import USER_AGENTS
from app.chatbot.utils import clean_text
#from app.utilidades.vacantes import get_session, login, login_to_wordpress, register, solicitud, exportar_vacantes_a_wordpress

# En el módulo utilidades
logger = logging.getLogger(__name__)


nlp = spacy.load("en_core_web_md")
sn = NLPProcessor # Se obtiene solo cuando se necesita
if not sn:
    logger.warning("⚠ NLPProcessor no está disponible. Se usarán métodos alternativos de extracción.")

# ========================
# Configuración General
# ========================
class ScrapingConfig:
    def __init__(self):
        self.RATE_LIMIT = 2  # Requests por segundo
        self.MAX_RETRIES = 3
        self.TIMEOUT = 30    # Tiempo máximo por solicitud (segundos)
        self.MAX_CONCURRENT_REQUESTS = 10
        self.USER_AGENTS = USER_AGENTS

class ScrapingMetrics:
    def __init__(self):
        self.jobs_scraped = Counter('jobs_scraped_total', 'Total jobs scraped')
        self.scraping_duration = Histogram('scraping_duration_seconds', 'Time spent scraping')
        self.errors_total = Counter('scraping_errors_total', 'Total scraping errors')
        try:
            start_http_server(8001)
            logger.info("Prometheus server started on port 8001")
        except OSError as e:
            logger.warning(f"Failed to start Prometheus server: {e}")

class ScrapingCache:
    def __init__(self):
        self.cache = {}
        self.TTL = 3600  # 1 hora

    async def get(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if (datetime.now() - timestamp).seconds < self.TTL:
                return data
            del self.cache[key]
        return None

    async def set(self, key: str, value: Dict):
        self.cache[key] = (value, datetime.now())

# ========================
# Estructura de Datos
# ========================
@dataclass
class JobListing:
    title: str
    location: str
    company: Optional[str] = None
    description: Optional[str] = None
    skills: Optional[List[str]] = None
    posted_date: Optional[str] = None
    url: Optional[str] = None
    salary: Optional[Dict[str, str]] = None
    responsible: Optional[str] = None  # Persona o equipo responsable, vinculado a Worker
    contract_type: Optional[str] = None
    job_type: Optional[str] = None
    benefits: Optional[List[str]] = None
    sectors: Optional[List[str]] = None

# ========================
# Funciones de Utilidad
# ========================
def validate_job_data(job: JobListing) -> Optional[Dict]:
    """Valida y limpia los datos de una vacante."""
    required_fields = ["title", "location", "company", "description", "url"]
    if not all(getattr(job, field) for field in required_fields):
        logger.warning(f"Missing required fields in job: {job.title}")
        return None
    return {
        "title": clean_text(job.title),
        "location": clean_text(job.location),
        "company": clean_text(job.company),
        "description": clean_text(job.description),
        "url": job.url,
        "skills": job.skills or extract_skills(job.description),
        "sectors": job.sectors or associate_divisions(job.skills or []),
        "salary": job.salary,
        "responsible": clean_text(job.responsible) if job.responsible else None,
        "posted_date": job.posted_date,
        "contract_type": job.contract_type,
        "job_type": job.job_type,
        "benefits": job.benefits or [],
    }

def assign_business_unit(job: Dict) -> str:
    """Asigna una BusinessUnit basada en el título del trabajo."""
    business_rules = {
        "huntRED": {"subdirector", "director", "vp", "ceo", "presidente", "board", "consejero", "estratégico", "executive", "alta dirección", "gerente", "chief"},
        "huntu": {"trainee", "junior", "recién egresado", "entry level", "practicante", "pasante", "becario", "líder", "coordinador", "analista", "senior", "lead"},
        "amigro": {"migrante", "trabajador internacional", "operativo", "cajero", "auxiliar", "soporte", "campos agrícolas", "construcción", "servicio", "operador"},
    }
    title = job["title"].lower()
    for bu, keywords in business_rules.items():
        if any(keyword in title for keyword in keywords):
            return bu
    return "amigro"

@transaction.atomic
async def save_vacantes(jobs: List[Dict], dominio: DominioScraping):
    """Guarda las vacantes en la base de datos y asocia un Worker si hay responsible."""
    for job in jobs:
        try:
            bu_name = assign_business_unit(job)
            business_unit = await sync_to_async(BusinessUnit.objects.get)(name=bu_name)
            
            # Crear o actualizar Vacante
            vacante, created = await sync_to_async(Vacante.objects.update_or_create)(
                titulo=job["title"],
                empresa=job["company"],
                url_original=job["url"],
                defaults={
                    "salario": job.get("salary", {}).get("min") if job.get("salary") else None,
                    "ubicacion": job["location"],
                    "descripcion": job["description"],
                    "skills_required": job["skills"],
                    "divisiones": job["sectors"],
                    "dominio_origen": dominio,
                    "business_unit": business_unit,
                    "fecha_publicacion": job.get("posted_date") or now(),
                    "remote_friendly": "remote" in (job.get("job_type", "").lower() or ""),
                    "contract_type": job.get("contract_type"),
                    "job_type": job.get("job_type"),
                    "beneficios": ", ".join(job.get("benefits", [])),
                }
            )
            logger.info(f"Vacante {'creada' if created else 'actualizada'}: {vacante.titulo}")

            # Si hay responsible, crear o vincular Worker
            if job.get("responsible"):
                worker, worker_created = await sync_to_async(Worker.objects.get_or_create)(
                    name=job["responsible"],
                    defaults={
                        "company": job["company"],
                        "job_id": str(vacante.id),  # Vincular al ID de la vacante
                        "job_description": job["description"],
                        "required_skills": ", ".join(job["skills"]),
                    }
                )
                if worker_created:
                    logger.info(f"Worker creado: {worker.name} para vacante {vacante.titulo}")
                else:
                    logger.debug(f"Worker existente asociado: {worker.name}")

        except Exception as e:
            logger.error(f"Error saving job {job['title']}: {e}")

async def validar_url(url: str, check_content: bool = False) -> bool:
    """Valida si una URL es accesible y opcionalmente su contenido."""
    async with ClientSession() as session:
        try:
            async with session.head(url, timeout=5) as response:
                if response.status != 200:
                    logger.warning(f"URL inaccessible: {url} - Status {response.status}")
                    return False
            if check_content:
                async with session.get(url, timeout=10) as response:
                    content = await response.text()
                    if 'job' not in content.lower():
                        logger.warning(f"No job-related content in {url}")
                        return False
            return True
        except Exception as e:
            logger.error(f"Error validating URL {url}: {e}")
            return False

def extract_skills(text: str) -> List[str]:
    """Extrae habilidades del texto usando SkillNer."""
    try:
        results = sn.extract_skills(text)
        return [skill["skill"] for skill in results.get("results", [])]
    except Exception as e:
        logger.error(f"Error extracting skills: {e}")
        return []

def associate_divisions(skills: List[str]) -> List[str]:
    """Asocia divisiones basadas en habilidades."""
    divisions = set()
    for skill in skills:
        for division, div_skills in DIVISION_SKILLS.items():
            if skill in div_skills:
                divisions.add(division)
    return list(divisions)

# ========================
# Clase Base Abstracta
# ========================
class BaseScraper:
    def __init__(self, domain: DominioScraping, config: Optional[ScrapingConfig] = None):
        self.domain = domain
        self.url = domain.dominio
        self.config = config or ScrapingConfig()
        self.cookies = json.loads(domain.cookies or "{}")
        self.session = None

    async def __aenter__(self):
        headers = {'User-Agent': random.choice(self.config.USER_AGENTS)}
        self.session = ClientSession(headers=headers, cookies=self.cookies, timeout=ClientTimeout(total=self.config.TIMEOUT))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), before_sleep=before_sleep_log(logger, logging.WARNING))
    async def fetch(self, url: str) -> Optional[str]:
        """Realiza una solicitud HTTP con reintentos."""
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            logger.error(f"Fetch failed for {url}: {e}")
            raise

    async def scrape(self) -> List[JobListing]:
        """Método abstracto para scraping."""
        raise NotImplementedError("Subclasses must implement scrape method.")



# ========================
# Scrapers Específicos
# ========================

class WorkdayScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para Workday con paginación."""
        vacantes = []
        page = 1
        while True:
            url = f"{self.url}?page={page}"
            content = await self.fetch(url)
            if not content:
                logger.info(f"No more content at page {page} for {self.url}")
                break
            soup = BeautifulSoup(content, "html.parser")
            job_elements = soup.find_all("a", {"data-automation-id": "jobTitle"})
            if not job_elements:
                logger.info(f"No jobs found at page {page} for {self.url}")
                break
            for job in job_elements:
                title = job.text.strip()
                link = f"{self.url.split('/job-search')[0]}{job['href']}"
                details = await self.get_job_details(link)
                vacantes.append(JobListing(
                    title=title,
                    location=details.get("location", "Unknown"),
                    company=details.get("company", "Workday Employer"),
                    url=link,
                    description=details.get("description", "No disponible"),
                    skills=extract_skills(details.get("description", "")),
                    responsible=details.get("responsible"),
                    job_type=details.get("job_type")
                ))
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en Workday."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible", "location": "Unknown", "company": "Unknown"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", {"data-automation-id": "jobPostingDescription"})
        location = soup.find("div", {"data-automation-id": "location"})
        company = soup.find("div", {"data-automation-id": "company"})
        responsible = soup.find("span", class_="contact-name")  # Ejemplo, ajustar según HTML real
        job_type = soup.find("span", {"data-automation-id": "jobType"})
        return {
            "description": description.text.strip() if description else "No disponible",
            "location": location.text.strip() if location else "Unknown",
            "company": company.text.strip() if company else "Unknown",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class LinkedInScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para LinkedIn con paginación."""
        vacantes = []
        page = 0
        while True:
            url = f"{self.url}?start={page * 25}"
            content = await self.fetch(url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.find_all("div", class_="job-card-container")
            if not job_cards:
                break
            for card in job_cards:
                title_elem = card.find("h3", class_="job-card-list__title")
                company_elem = card.find("a", class_="job-card-container__company-name")
                location_elem = card.find("span", class_="job-card-container__metadata-item")
                link_elem = card.find("a", class_="job-card-container__link")
                if title_elem and link_elem:
                    title = title_elem.text.strip()
                    link = f"https://linkedin.com{link_elem['href']}"
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=title,
                        location=location_elem.text.strip() if location_elem else "Unknown",
                        company=company_elem.text.strip() if company_elem else "Unknown",
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type")
                    ))
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en LinkedIn."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="description__text")
        responsible = soup.find("a", class_="recruiter-name")  # Ejemplo, ajustar según LinkedIn
        job_type = soup.find("span", class_="job-criteria__text--criteria")
        return {
            "description": description.text.strip() if description else "No disponible",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class IndeedScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para Indeed con paginación."""
        vacantes = []
        page = 0
        while True:
            url = f"{self.url}?start={page * 10}"
            content = await self.fetch(url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.find_all("div", class_="job_seen_beacon")
            if not job_cards:
                break
            for card in job_cards:
                title_elem = card.find("h2", class_="jobTitle")
                company_elem = card.find("span", class_="companyName")
                location_elem = card.find("div", class_="companyLocation")
                link_elem = card.find("a", class_="jcs-JobTitle")
                if title_elem and link_elem:
                    title = title_elem.text.strip()
                    link = f"https://indeed.com{link_elem['href']}"
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=title,
                        location=location_elem.text.strip() if location_elem else "Unknown",
                        company=company_elem.text.strip() if company_elem else "Unknown",
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type")
                    ))
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en Indeed."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", id="jobDescriptionText")
        responsible = soup.find("span", class_="recruiter-name")  # Ajustar según Indeed
        job_type = soup.find("div", class_="jobsearch-JobInfoHeader-subtitle")
        return {
            "description": description.text.strip() if description else "No disponible",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type and "contract" in job_type.text.lower() else None
        }

class GreenhouseScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para Greenhouse con paginación."""
        vacantes = []
        page = 1
        while True:
            url = f"{self.url}?page={page}"
            content = await self.fetch(url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.find_all("div", class_="opening")
            if not job_cards:
                break
            for job in job_cards:
                title_elem = job.find("a")
                location_elem = job.find("span", class_="location")
                if title_elem:
                    title = title_elem.text.strip()
                    link = f"{self.url.rsplit('/', 1)[0]}{title_elem['href']}"
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=title,
                        location=location_elem.text.strip() if location_elem else "Unknown",
                        company=details.get("company", "Greenhouse Employer"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type")
                    ))
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en Greenhouse."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible", "company": "Unknown"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="section-wrapper")
        company = soup.find("span", class_="company-name")
        responsible = soup.find("span", class_="contact-name")  # Ajustar según Greenhouse
        job_type = soup.find("div", class_="job-type")
        return {
            "description": description.text.strip() if description else "No disponible",
            "company": company.text.strip() if company else "Unknown",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class AccentureScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para Accenture con paginación."""
        vacantes = []
        page = 1
        while True:
            url = f"{self.url}/mx-es/careers/jobsearch?pg={page}"
            content = await self.fetch(url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.find_all("div", class_="cmp-teaser card")
            if not job_cards:
                break
            for card in job_cards:
                title_elem = card.find("h3", class_="cmp-teaser__title")
                detail_link = card.find("a", class_="cmp-teaser__title-link")
                if title_elem and detail_link:
                    title = title_elem.text.strip()
                    link = f"https://www.accenture.com{detail_link['href']}"
                    details = await self.get_job_details(link)
                    region_elem = card.find("div", class_="cmp-teaser-region")
                    city_elem = card.find("div", class_="cmp-teaser-city")
                    location = f"{region_elem.text.strip() if region_elem else 'Unknown'}, {city_elem.text.strip() if city_elem else 'Unknown'}"
                    posted_date = card.find("p", class_="cmp-teaser__job-listing-posted-date")
                    vacantes.append(JobListing(
                        title=title,
                        location=location,
                        company="Accenture",
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        posted_date=posted_date.text.strip() if posted_date else None,
                        job_type=details.get("job_type")
                    ))
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en Accenture."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="job-description")
        responsible = soup.find("span", class_="recruiter-contact")  # Ejemplo, ajustar según Accenture
        job_type = soup.find("div", class_="job-type-info")
        return {
            "description": description.text.strip() if description else "No disponible",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class EightfoldScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para Eightfold AI con paginación."""
        vacantes = []
        page = 1
        while True:
            url = f"{self.url}?page={page}&sort_by=relevance"
            content = await self.fetch(url)
            if not content:
                break
            try:
                data = json.loads(content)
                jobs = data.get("jobs", [])
                if not jobs:
                    break
                for job in jobs:
                    link = job.get("url", "")
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=job.get("title", "No especificado"),
                        location=job.get("locations", [{}])[0].get("name", "Unknown"),
                        company=job.get("company_name", "Eightfold Employer"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type")
                    ))
                page += 1
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON for Eightfold: {e}")
                break
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en Eightfold."""
        if not url:
            return {"description": "No disponible"}
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="job-description")
        responsible = soup.find("span", class_="recruiter-name")  # Ejemplo
        job_type = soup.find("div", class_="employment-type")
        return {
            "description": description.text.strip() if description else "No disponible",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class PhenomPeopleScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para Phenom People con paginación."""
        vacantes = []
        page = 1
        while True:
            url = f"{self.url}?page={page}"
            content = await self.fetch(url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.find_all("div", class_="job-card")
            if not job_cards:
                break
            for card in job_cards:
                title_elem = card.find("h3")
                link_elem = card.find("a", href=True)
                location_elem = card.find("span", class_="job-location")
                if title_elem and link_elem:
                    title = title_elem.text.strip()
                    link = link_elem["href"] if link_elem["href"].startswith("http") else f"{self.url}{link_elem['href']}"
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=title,
                        location=location_elem.text.strip() if location_elem else "Unknown",
                        company=details.get("company", "Phenom Employer"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type")
                    ))
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en Phenom People."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible", "company": "Unknown"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="job-details-description")
        company = soup.find("span", class_="company-name")
        responsible = soup.find("span", class_="contact-name")  # Ejemplo
        job_type = soup.find("div", class_="job-type")
        return {
            "description": description.text.strip() if description else "No disponible",
            "company": company.text.strip() if company else "Unknown",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class OracleScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para Oracle HCM con paginación."""
        vacantes = []
        page = 1
        while True:
            url = f"{self.url}/jobs?page={page}"
            content = await self.fetch(url)
            if not content:
                break
            try:
                data = json.loads(content)
                jobs = data.get("jobList", [])
                if not jobs:
                    break
                for job in jobs:
                    link = job.get("detailUrl", "")
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=job.get("title", "No especificado"),
                        location=job.get("location", {}).get("city", "Unknown"),
                        company=job.get("company", "Oracle Employer"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type")
                    ))
                page += 1
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON for Oracle: {e}")
                break
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en Oracle HCM."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="job-description")
        responsible = soup.find("span", class_="recruiter-contact")  # Ejemplo
        job_type = soup.find("div", class_="employment-type")
        return {
            "description": description.text.strip() if description else "No disponible",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class SAPScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para SAP SuccessFactors con paginación."""
        vacantes = []
        page = 1
        while True:
            url = f"{self.url}/jobs?page={page}"
            content = await self.fetch(url)
            if not content:
                break
            try:
                data = json.loads(content)
                jobs = data.get("jobs", [])
                if not jobs:
                    break
                for job in jobs:
                    link = job.get("detailUrl", "")
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=job.get("title", "No especificado"),
                        location=job.get("location", {}).get("city", "Unknown"),
                        company=job.get("company", "SAP Employer"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type")
                    ))
                page += 1
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON for SAP: {e}")
                break
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en SAP SuccessFactors."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="job-description")
        responsible = soup.find("span", class_="job-contact")  # Ejemplo
        job_type = soup.find("div", class_="job-type")
        return {
            "description": description.text.strip() if description else "No disponible",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class ADPScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para ADP con paginación."""
        vacantes = []
        page = 1
        while True:
            url = f"{self.url}/search?page={page}"
            content = await self.fetch(url)
            if not content:
                break
            try:
                data = json.loads(content)
                jobs = data.get("jobs", [])
                if not jobs:
                    break
                for job in jobs:
                    link = job.get("jobUrl", "")
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=job.get("jobTitle", "No especificado"),
                        location=job.get("jobLocation", "Unknown"),
                        company=job.get("company", "ADP Employer"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type")
                    ))
                page += 1
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON for ADP: {e}")
                break
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en ADP."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="job-details")
        responsible = soup.find("span", class_="posting-contact")  # Ejemplo
        job_type = soup.find("div", class_="employment-status")
        return {
            "description": description.text.strip() if description else "No disponible",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class PeopleSoftScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para PeopleSoft."""
        vacantes = []
        url = f"{self.url}/joblist"
        content = await self.fetch(url)
        if not content:
            return vacantes
        soup = BeautifulSoup(content, "html.parser")
        job_cards = soup.find_all("div", class_="job-card")
        for card in job_cards:
            title_elem = card.find("h3")
            link_elem = card.find("a", href=True)
            location_elem = card.find("span", class_="location")
            if title_elem and link_elem:
                title = title_elem.text.strip()
                link = link_elem["href"] if link_elem["href"].startswith("http") else f"{self.url}{link_elem['href']}"
                details = await self.get_job_details(link)
                vacantes.append(JobListing(
                    title=title,
                    location=location_elem.text.strip() if location_elem else "Unknown",
                    company=details.get("company", "PeopleSoft Employer"),
                    url=link,
                    description=details.get("description", "No disponible"),
                    skills=extract_skills(details.get("description", "")),
                    responsible=details.get("responsible"),
                    job_type=details.get("job_type")
                ))
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en PeopleSoft."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible", "company": "Unknown"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="job-details")
        company = soup.find("span", class_="company-name")
        responsible = soup.find("span", class_="contact-name")  # Ejemplo
        job_type = soup.find("div", class_="job-type")
        return {
            "description": description.text.strip() if description else "No disponible",
            "company": company.text.strip() if company else "Unknown",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class Meta4Scraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para Meta4."""
        vacantes = []
        url = f"{self.url}/opportunities"
        content = await self.fetch(url)
        if not content:
            return vacantes
        soup = BeautifulSoup(content, "html.parser")
        job_items = soup.find_all("div", class_="job-item")
        for item in job_items:
            title_elem = item.find("h3")
            link_elem = item.find("a", href=True)
            location_elem = item.find("span", class_="location")
            if title_elem and link_elem:
                title = title_elem.text.strip()
                link = link_elem["href"] if link_elem["href"].startswith("http") else f"{self.url}{link_elem['href']}"
                details = await self.get_job_details(link)
                vacantes.append(JobListing(
                    title=title,
                    location=location_elem.text.strip() if location_elem else "Unknown",
                    company=details.get("company", "Meta4 Employer"),
                    url=link,
                    description=details.get("description", "No disponible"),
                    skills=extract_skills(details.get("description", "")),
                    responsible=details.get("responsible"),
                    job_type=details.get("job_type")
                ))
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en Meta4."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible", "company": "Unknown"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="job-description")
        company = soup.find("span", class_="company-name")
        responsible = soup.find("span", class_="contact-name")  # Ejemplo
        job_type = soup.find("div", class_="employment-type")
        return {
            "description": description.text.strip() if description else "No disponible",
            "company": company.text.strip() if company else "Unknown",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class CornerstoneScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para Cornerstone con paginación."""
        vacantes = []
        page = 1
        while True:
            url = f"{self.url}/joblist?page={page}"
            content = await self.fetch(url)
            if not content:
                break
            try:
                data = json.loads(content)
                jobs = data.get("jobs", [])
                if not jobs:
                    break
                for job in jobs:
                    link = job.get("url", "")
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=job.get("title", "No especificado"),
                        location=job.get("location", "Unknown"),
                        company=job.get("company", "Cornerstone Employer"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type")
                    ))
                page += 1
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON for Cornerstone: {e}")
                break
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en Cornerstone."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="job-details")
        responsible = soup.find("span", class_="contact-name")  # Ejemplo
        job_type = soup.find("div", class_="employment-type")
        return {
            "description": description.text.strip() if description else "No disponible",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class UKGScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para UKG con paginación."""
        vacantes = []
        page = 1
        while True:
            url = f"{self.url}/search?page={page}"
            content = await self.fetch(url)
            if not content:
                break
            try:
                data = json.loads(content)
                jobs = data.get("results", [])
                if not jobs:
                    break
                for job in jobs:
                    link = job.get("url", "")
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=job.get("title", "No especificado"),
                        location=job.get("location", "Unknown"),
                        company=job.get("company", "UKG Employer"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type")
                    ))
                page += 1
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON for UKG: {e}")
                break
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en UKG."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="job-details")
        responsible = soup.find("span", class_="contact-name")  # Ejemplo
        job_type = soup.find("div", class_="employment-type")
        return {
            "description": description.text.strip() if description else "No disponible",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class GlassdoorScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para Glassdoor con paginación (pendiente de implementación completa)."""
        vacantes = []
        page = 1
        while True:
            url = f"{self.url}?page={page}"
            content = await self.fetch(url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.find_all("li", class_="react-job-listing")
            if not job_cards:
                break
            for card in job_cards:
                title_elem = card.find("a", class_="jobLink")
                company_elem = card.find("div", class_="jobCompany")
                location_elem = card.find("span", class_="jobLocation")
                if title_elem:
                    title = title_elem.text.strip()
                    link = f"https://glassdoor.com{title_elem['href']}"
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=title,
                        location=location_elem.text.strip() if location_elem else "Unknown",
                        company=company_elem.text.strip() if company_elem else "Unknown",
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type")
                    ))
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en Glassdoor."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="desc")
        responsible = soup.find("span", class_="recruiter-name")  # Ejemplo
        job_type = soup.find("div", class_="job-type")
        return {
            "description": description.text.strip() if description else "No disponible",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class ComputrabajoScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper para Computrabajo con paginación (pendiente de implementación completa)."""
        vacantes = []
        page = 1
        while True:
            url = f"{self.url}?p={page}"
            content = await self.fetch(url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.find_all("article", class_="box_border")
            if not job_cards:
                break
            for card in job_cards:
                title_elem = card.find("h1")
                company_elem = card.find("span", class_="company")
                location_elem = card.find("span", class_="location")
                link_elem = card.find("a", class_="js-o-link")
                if title_elem and link_elem:
                    title = title_elem.text.strip()
                    link = link_elem["href"] if link_elem["href"].startswith("http") else f"https://computrabajo.com{link_elem['href']}"
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=title,
                        location=location_elem.text.strip() if location_elem else "Unknown",
                        company=company_elem.text.strip() if company_elem else "Unknown",
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=extract_skills(details.get("description", "")),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type")
                    ))
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        """Extrae detalles de una vacante en Computrabajo."""
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.find("div", class_="box_detail")
        responsible = soup.find("span", class_="contact-name")  # Ejemplo
        job_type = soup.find("span", class_="tipo-contrato")
        return {
            "description": description.text.strip() if description else "No disponible",
            "responsible": responsible.text.strip() if responsible else None,
            "job_type": job_type.text.strip() if job_type else None
        }

class FlexibleScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        """Scraper flexible usando selectores de DominioScraping."""
        content = await self.fetch(self.url)
        if not content:
            return []
        soup = BeautifulSoup(content, "html.parser")
        job_cards = soup.select(self.domain.selector_job_cards or "div.job-card")
        vacantes = []
        for card in job_cards:
            title = self.extract_field(card, self.domain.selector_titulo, "title")
            link = self.extract_field(card, self.domain.selector_url, "href", attribute=True) or self.url
            description = self.extract_field(card, self.domain.selector_descripcion, "description")
            location = self.extract_field(card, self.domain.selector_ubicacion, "location")
            company = self.extract_field(card, self.domain.mapeo_configuracion.get("company_selector") if self.domain.mapeo_configuracion else None, "company") or "Unknown"
            responsible = self.extract_field(card, self.domain.mapeo_configuracion.get("responsible_selector") if self.domain.mapeo_configuracion else None, "responsible")
            vacantes.append(JobListing(
                title=title or "No especificado",
                location=location or "Unknown",
                company=company,
                url=link,
                description=description or "No disponible",
                skills=extract_skills(description or ""),
                responsible=responsible
            ))
        return vacantes

    def extract_field(self, element, selector: Optional[str], field_name: str, attribute: bool = False) -> Optional[str]:
        """Extrae un campo usando un selector dinámico."""
        if not selector:
            return None
        try:
            elem = element.select_one(selector)
            if elem:
                return elem["href"] if attribute else elem.text.strip()
            logger.debug(f"No {field_name} found with selector {selector}")
            return None
        except Exception as e:
            logger.warning(f"Error extracting {field_name} with selector {selector}: {e}")
            return None

# Mapeo de Scrapers (se usará en Parte 3)
SCRAPER_MAP = {
    "workday": WorkdayScraper,
    "linkedin": LinkedInScraper,
    "indeed": IndeedScraper,
    "greenhouse": GreenhouseScraper,
    "accenture": AccentureScraper,
    "eightfold_ai": EightfoldScraper,
    "phenom_people": PhenomPeopleScraper,
    "oracle_hcm": OracleScraper,
    "sap_successfactors": SAPScraper,
    "adp": ADPScraper,
    "peoplesoft": PeopleSoftScraper,
    "meta4": Meta4Scraper,
    "cornerstone": CornerstoneScraper,
    "ukg": UKGScraper,
    "glassdoor": GlassdoorScraper,
    "computrabajo": ComputrabajoScraper,
    "flexible": FlexibleScraper,
    "default": BaseScraper,
}


class ScrapingPipeline:
    """Procesa datos scraped antes de guardar o publicar."""
    def __init__(self):
        self.cache = ScrapingCache()

    async def process(self, jobs: List[Dict]) -> List[Dict]:
        """Procesa trabajos: limpia, enriquece y valida."""
        jobs = await self.clean_data(jobs)
        jobs = await self.enrich_data(jobs)
        jobs = await self.validate_data(jobs)
        return jobs

    async def clean_data(self, jobs: List[Dict]) -> List[Dict]:
        """Limpia datos eliminando entradas incompletas."""
        return [job for job in jobs if job.get('title') and job.get('description')]

    async def enrich_data(self, jobs: List[Dict]) -> List[Dict]:
        """Añade metadatos como timestamp."""
        for job in jobs:
            job['scraped_at'] = datetime.now().isoformat()
        return jobs

    async def validate_data(self, jobs: List[Dict]) -> List[Dict]:
        """Valida datos asegurando campos requeridos."""
        return [validated for job in jobs if (validated := validate_job_data(JobListing(**job)))]

async def publish_to_internal_system(jobs: List[Dict], business_unit: BusinessUnit) -> bool:
    """Publica trabajos al sistema interno usando VacanteManager."""
    from app.utilidades.vacantes import VacanteManager
    try:
        for job in jobs:
            job_data = {
                "business_unit": business_unit.id,
                "job_title": job["title"],
                "job_description": job["description"],
                "company_name": job["company"],
                "celular_responsable": job.get("responsible_whatsapp", ""),
                "job_employee-email": job.get("responsible_email", ""),
                "job_employee": job["responsible"],
            }
            manager = VacanteManager(job_data)
            result = await manager.create_job_listing()
            if result["status"] != "success":
                logger.error(f"Failed to publish {job['title']}: {result['message']}")
                return False
        logger.info(f"Published {len(jobs)} jobs for {business_unit.name}")
        return True
    except Exception as e:
        logger.error(f"Error publishing: {e}")
        return False

async def scrape_and_publish(domains: List[DominioScraping]) -> None:
    """Ejecuta scraping y publicación para todos los dominios."""
    pipeline = ScrapingPipeline()
    metrics = ScrapingMetrics()
    tasks = []

    for domain in domains:
        registro = await sync_to_async(RegistroScraping.objects.create)(dominio=domain, estado='parcial')
        scraper = SCRAPER_MAP.get(domain.plataforma, SCRAPER_MAP["default"])(domain)
        tasks.append(process_domain(scraper, domain, registro, pipeline, metrics))

    results = await asyncio.gather(*tasks)
    
    jobs_by_bu = {}
    for domain, jobs in results:
        if jobs:
            bu_name = jobs[0]["business_unit"]
            jobs_by_bu.setdefault(bu_name, []).extend(jobs)
    
    for bu_name, jobs in jobs_by_bu.items():
        bu = await sync_to_async(BusinessUnit.objects.get)(name=bu_name)
        await publish_to_internal_system(jobs, bu)
        metrics.jobs_scraped.inc(len(jobs))

async def process_domain(scraper, domain: DominioScraping, registro: RegistroScraping, pipeline: ScrapingPipeline, metrics: ScrapingMetrics) -> tuple:
    """Procesa un dominio: scrapea, valida y guarda."""
    try:
        async with scraper:
            with metrics.scraping_duration.time():
                raw_jobs = await scraper.scrape()
                processed_jobs = await pipeline.process([vars(job) for job in raw_jobs])
                await save_vacantes(processed_jobs, domain)
                registro.vacantes_encontradas = len(processed_jobs)
                registro.estado = 'exitoso'
                return domain, processed_jobs
    except Exception as e:
        registro.estado = 'fallido'
        registro.error_log = str(e)
        logger.error(f"Scraping failed for {domain.dominio}: {e}")
        metrics.errors_total.inc()
        return domain, []
    finally:
        registro.fecha_fin = now()
        await sync_to_async(registro.save)()

async def run_all_scrapers() -> None:
    """Ejecuta el scraping completo."""
    domains = await sync_to_async(list)(DominioScraping.objects.filter(activo=True))
    await scrape_and_publish(domains)

class Command(BaseCommand):
    """Comando Django para ejecutar el scraping."""
    help = "Run job scraping across all active domains"

    def handle(self, *args, **kwargs):
        asyncio.run(run_all_scrapers())