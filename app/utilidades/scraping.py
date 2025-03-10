# /home/pablo/app/utilidades/scraping.py

# Importaciones necesarias
import json
import random
from typing import List, Dict, Optional
from datetime import datetime
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
from app.models import DominioScraping, Vacante, USER_AGENTS  # Importamos USER_AGENTS desde models.py
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
import logging

logger = logging.getLogger(__name__)

# Clase JobListing para estructurar los datos de las vacantes
class JobListing:
    def __init__(self, title: str, url: str, description: str, location: str, company: str, responsible: Optional[str] = None, job_type: Optional[str] = None, posted_date: Optional[str] = None):
        self.title = title
        self.url = url
        self.description = description
        self.location = location
        self.company = company
        self.responsible = responsible
        self.job_type = job_type
        self.posted_date = posted_date

# Funciones generales

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), before_sleep=before_sleep_log(logger, logging.WARNING))
async def fetch(session: ClientSession, url: str) -> Optional[str]:
    """Función para hacer solicitudes HTTP con retries."""
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        raise

def extract_field(element: BeautifulSoup, selector: str, attribute: Optional[str] = None) -> Optional[str]:
    """Extrae un campo de un elemento BeautifulSoup usando un selector y opcionalmente un atributo."""
    try:
        elem = element.select_one(selector)
        if elem:
            return elem[attribute] if attribute else elem.text.strip()
        return None
    except Exception as e:
        logger.warning(f"Error extracting field with selector {selector}: {e}")
        return None

async def get_description(session: ClientSession, url: str, selector: str) -> Optional[str]:
    """Obtiene la descripción de una vacante desde su URL usando el selector proporcionado."""
    content = await fetch(session, url)
    if not content:
        return "No disponible"
    soup = BeautifulSoup(content, "html.parser")
    desc_elem = soup.select_one(selector)
    return desc_elem.text.strip() if desc_elem else "No disponible"

# Clase BaseScraper optimizada
class BaseScraper:
    def __init__(self, domain: DominioScraping, plataforma: str, selectors: Dict[str, str]):
        self.domain = domain
        self.plataforma = plataforma
        self.selectors = selectors
        self.session = None

    async def __aenter__(self):
        headers = {'User-Agent': random.choice(USER_AGENTS)}  # Rotamos USER_AGENTS desde models.py
        self.session = ClientSession(headers=headers, timeout=ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def scrape(self) -> List[JobListing]:
        """Método genérico para scrapear vacantes de plataformas HTML."""
        vacantes = []
        page = 1
        step = self.selectors.get("pagination_step", 1)
        param = self.selectors.get("pagination_param", "page")
        seen_urls = set()  # Para evitar duplicados

        while True:
            url = f"{self.domain.dominio}?{param}={page * step}"
            content = await fetch(self.session, url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.select(self.selectors.get("job_cards", ""))
            if not job_cards:
                break
            for card in job_cards:
                details = await self.extract_job_details(card)
                if details and details["url"] not in seen_urls:
                    seen_urls.add(details["url"])
                    vacantes.append(JobListing(**details))
            page += 1
        return vacantes

    async def extract_job_details(self, card: BeautifulSoup) -> Optional[Dict]:
        """Extrae los detalles de una vacante desde una tarjeta HTML."""
        title = extract_field(card, self.selectors.get("title", ""))
        link = extract_field(card, self.selectors.get("url", ""), attribute="href")
        if not link:
            return None
        full_link = link if link.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{link}"
        description = await get_description(self.session, full_link, self.selectors.get("description", ""))
        location = extract_field(card, self.selectors.get("location", ""))
        company = extract_field(card, self.selectors.get("company", "")) or "Unknown"
        responsible = extract_field(card, self.selectors.get("responsible", ""))
        job_type = extract_field(card, self.selectors.get("job_type", ""))
        posted_date = extract_field(card, self.selectors.get("posted_date", ""))

        return {
            "title": title or "No especificado",
            "url": full_link,
            "description": description or "No disponible",
            "location": location or "Unknown",
            "company": company,
            "responsible": responsible,
            "job_type": job_type,
            "posted_date": posted_date
        }

    
# selectors.py
PLATFORM_SELECTORS = {
    "indeed": {
        "job_cards": "div.job_seen_beacon",
        "title": "h2.jobTitle",
        "url": "a.jcs-JobTitle",
        "description": "div#jobDescriptionText",
        "location": "span.companyLocation",
        "company": "span.companyName",
        "responsible": "span.recruiter-name",  # Puede no estar disponible, ajustar según inspección
        "job_type": "div.jobsearch-JobInfoHeader-subtitle",
        "posted_date": "span.date",
        "pagination_param": "start",
        "pagination_step": 10,
    },
    "workday": {
        "job_cards": "div[data-automation-id='jobPosting']",
        "title": "a[data-automation-id='jobTitle']",
        "url": "a[data-automation-id='jobTitle']",
        "description": "div[data-automation-id='jobPostingDescription']",
        "location": "div[data-automation-id='location']",
        "company": "div[data-automation-id='company']",
        "responsible": "span.contact-name",  # Puede requerir ajuste
        "job_type": "span[data-automation-id='jobType']",
        "posted_date": "span[data-automation-id='postedDate']",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "linkedin": {
        "job_cards": "li.jobs-search-results__list-item",
        "title": "h3.job-card-list__title",
        "url": "a.job-card-list__title",
        "description": "div.jobs-description-content__text",
        "location": "span.job-card-container__metadata-item",
        "company": "span.job-card-container__company-name",
        "posted_date": "time.job-card-container__time",
        "pagination_param": "start",
        "pagination_step": 25,
    },
    "greenhouse": {
        "job_cards": "div.opening",
        "title": "a",
        "url": "a",
        "description": "div.section-wrapper",
        "location": "span.location",
        "company": "span.company-name",
        "responsible": "span.contact-name",  # Ejemplo, ajustar según necesidad
        "job_type": "div.job-type",
        "posted_date": "span.posted-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "accenture": {
        "job_cards": "div.cmp-teaser.card",
        "title": "h3.cmp-teaser__title",
        "url": "a.cmp-teaser__title-link",
        "description": "div.job-description-container",
        "location": "div.cmp-teaser-region, div.cmp-teaser-city",
        "company": "span.company-name",
        "responsible": "span.contact-name",
        "job_type": "div.job-type",
        "posted_date": "p.cmp-teaser__job-listing-posted-date",
        "pagination_param": "pg",
        "pagination_step": 1,
    },
    "glassdoor": {
        "job_cards": "li.react-job-listing",
        "title": "a.jobLink",
        "url": "a.jobLink",
        "description": "div.job-description",
        "location": "span.jobLocation",
        "company": "div.jobCompany",
        "responsible": "span.recruiter",
        "job_type": "span.jobType",
        "posted_date": "span.posted-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "computrabajo": {
        "job_cards": "article.box_border",
        "title": "h1",
        "url": "a.js-o-link",
        "description": "div#jobDescription",
        "location": "span.location",
        "company": "span.company",
        "responsible": "span.responsible",
        "job_type": "span.job-type",
        "posted_date": "span.posted",
        "pagination_param": "p",
        "pagination_step": 1,
    },
}

class EightfoldScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()  # Para evitar duplicados
        while True:
            url = f"{self.domain.dominio}?page={page}&sort_by=relevance"
            content = await fetch(self.session, url)
            if not content:
                break
            try:
                data = json.loads(content)
                jobs = data.get("jobs", [])
                if not jobs:
                    break
                for job in jobs:
                    url = job.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        details = {
                            "title": job.get("title", "No especificado"),
                            "url": url,
                            "description": job.get("description", "No disponible"),
                            "location": job.get("locations", [{}])[0].get("name", "Unknown"),
                            "company": job.get("company_name", "Eightfold Employer"),
                            "responsible": job.get("responsible", None),
                            "job_type": job.get("job_type", None),
                            "posted_date": job.get("posted_date", None),
                        }
                        vacantes.append(JobListing(**details))
                page += 1
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}")
                break
        return vacantes

class OracleScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()  # Para evitar duplicados
        while True:
            url = f"{self.domain.dominio}/jobs?page={page}"
            content = await fetch(self.session, url)
            if not content:
                break
            try:
                data = json.loads(content)
                jobs = data.get("jobList", [])
                if not jobs:
                    break
                for job in jobs:
                    url = job.get("detailUrl", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        details = {
                            "title": job.get("title", "No especificado"),
                            "url": url,
                            "description": job.get("description", "No disponible"),
                            "location": job.get("location", {}).get("city", "Unknown"),
                            "company": job.get("company", "Oracle Employer"),
                            "responsible": job.get("responsible", None),
                            "job_type": job.get("job_type", None),
                            "posted_date": job.get("posted_date", None),
                        }
                        vacantes.append(JobListing(**details))
                page += 1
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}")
                break
        return vacantes
    

