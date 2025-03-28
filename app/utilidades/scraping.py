# /home/pablo/app/utilidades/scraping.py

import json
import random
import asyncio
from celery import shared_task
from asgiref.sync import sync_to_async
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from django.db import transaction
from django.utils.timezone import now
from django.core.cache import cache
from django.core.management.base import BaseCommand
from app.models import DominioScraping, RegistroScraping, Vacante, BusinessUnit, Worker, USER_AGENTS
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from app.chatbot.utils import clean_text
from app.utilidades.loader import DIVISION_SKILLS
from app.chatbot.nlp import NLPProcessor
from app.utilidades.vacantes import VacanteManager
from prometheus_client import Counter, Histogram, start_http_server
import logging

logger = logging.getLogger(__name__)

# Estructura de Datos
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
    responsible: Optional[str] = None
    contract_type: Optional[str] = None
    job_type: Optional[str] = None
    benefits: Optional[List[str]] = None
    sectors: Optional[List[str]] = None

# Configuración y Métricas
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
        self.TTL = 3600  # 1 hora

    async def get(self, key: str) -> Optional[Dict]:
        return await cache.get(key)  # Ensure async compatibility if using async cache backend

    async def set(self, key: str, value: Dict):
        serialized = json.dumps(value)
        await cache.set(key, serialized, timeout=self.TTL)
        logger.info(f"Cached {key}")
        return True

class ScrapingPipeline:
    def __init__(self, opportunity_db=None):
        self.cache = ScrapingCache()
        self.processor = NLPProcessor(language="es", mode="opportunity")

    async def process(self, jobs: List[Dict]) -> List[Dict]:
        jobs = await self.clean_data(jobs)
        jobs = await self.enrich_data(jobs)
        jobs = await self.validate_data(jobs)
        return jobs

    async def clean_data(self, jobs: List[Dict]) -> List[Dict]:
        return [job for job in jobs if job.get('title') and job.get('description')]

    async def enrich_data(self, jobs: List[Dict]) -> List[Dict]:
        for job in jobs:
            cache_key = f"{job['url']}_{job['title']}"
            cached = await self.cache.get(cache_key)
            if cached:
                job.update(cached)
            else:
                job['scraped_at'] = datetime.now().isoformat()
                if job["description"] != "No disponible":
                    analysis = self.processor.analyze_opportunity(job["description"])
                    job["skills"] = analysis.get("details", {}).get("skills", [])
                    job["contract_type"] = analysis.get("details", {}).get("contract_type")
                    job["job_classification"] = analysis.get("job_classification")
                    job["sentiment"] = analysis.get("sentiment")
                await self.cache.set(cache_key, job)
        return jobs

    async def validate_data(self, jobs: List[Dict]) -> List[Dict]:
        return [validated for job in jobs if (validated := validate_job_data(JobListing(**job)))]

# Funciones de Utilidad
def validate_job_data(job: JobListing) -> Optional[Dict]:
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
        "business_unit": assign_business_unit({"title": job.title})
    }

async def assign_business_unit(job: Dict) -> str:
    from app.models import WeightingModel, BusinessUnit
    title_lower = job["title"].lower()
    desc_lower = job.get("description", "").lower()
    skills = job.get("skills", [])
    location = job.get("location", "").lower()
    
    # Fetch all business units
    bu_candidates = await sync_to_async(list)(BusinessUnit.objects.all())
    scores = {}
    
    for bu in bu_candidates:
        weighting = WeightingModel(bu)
        weights = weighting.get_weights("operativo")  # Default level, adjust dynamically if needed
        score = 0
        
        # Title-based scoring
        keywords = {
            "huntRED": {"subdirector", "director", "vp", "ceo", "presidente", "board", "consejero", "estratégico", "executive", "alta dirección", "gerente", "chief"},
            "huntu": {"trainee", "junior", "recién egresado", "entry level", "practicante", "pasante", "becario", "líder", "coordinador", "analista", "senior", "lead"},
            "amigro": {"migrante", "trabajador internacional", "operativo", "cajero", "auxiliar", "soporte", "campos agrícolas", "construcción", "servicio", "operador"},
        }.get(bu.name, set())
        if any(keyword in title_lower for keyword in keywords):
            score += weights["hard_skills"] * 0.5  # Partial weight for title match
        
        # Skills-based scoring
        if skills:
            skill_overlap = len(set(skills) & set(DIVISION_SKILLS.get(bu.name, {}).get("skills", [])))
            score += weights["hard_skills"] * (skill_overlap / max(len(skills), 1))
        
        # Location-based scoring
        if "remote" in location or "remoto" in desc_lower:
            score += weights["ubicacion"] * 0.8
        if "mexico" in location or "usa" in location:
            score += weights["ubicacion"] * 0.5
        
        # Description-based scoring
        if "leadership" in desc_lower or "liderazgo" in desc_lower:
            score += weights["soft_skills"] * 0.3
        
        scores[bu.name] = score
    
    # Return highest scoring BU, default to "amigro" if no matches
    return max(scores, key=scores.get, default="amigro")

@transaction.atomic
async def save_vacantes(jobs: List[Dict], dominio: DominioScraping):
    for job in jobs:
        try:
            bu_name = assign_business_unit(job)
            business_unit = await sync_to_async(BusinessUnit.objects.get)(name=bu_name)
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
                    "sentiment": job.get("sentiment"),
                    "job_classification": job.get("job_classification"),
                }
            )
            logger.info(f"Vacante {'creada' if created else 'actualizada'}: {vacante.titulo}")
            if job.get("responsible"):
                worker, worker_created = await sync_to_async(Worker.objects.get_or_create)(
                    name=job["responsible"],
                    defaults={
                        "company": job["company"],
                        "job_id": str(vacante.id),
                        "job_description": job["description"],
                        "required_skills": ", ".join(job["skills"]),
                    }
                )
                logger.info(f"Worker {'creado' if worker_created else 'asociado'}: {worker.name}")
        except Exception as e:
            logger.error(f"Error saving job {job['title']}: {e}")

async def validar_url(url: str, check_content: bool = False) -> bool:
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

nlp_processor = NLPProcessor(language="es", mode="opportunity")

def extract_skills(text: str) -> List[str]:
    return nlp_processor.extract_skills(clean_text(text))

def associate_divisions(skills: List[str]) -> List[str]:
    divisions = set()
    for skill in skills:
        for division, div_skills in DIVISION_SKILLS.items():
            if skill in div_skills:
                divisions.add(division)
    return list(divisions)

def extract_field(element: BeautifulSoup, selector: str, attribute: Optional[str] = None) -> Optional[str]:
    try:
        elem = element.select_one(selector)
        if elem:
            return elem[attribute] if attribute else elem.text.strip()
        return None
    except Exception as e:
        logger.warning(f"Error extracting field with selector {selector}: {e}")
        return None

async def get_scraper(domain: DominioScraping):
    scraper_class = SCRAPER_MAP.get(domain.plataforma, SCRAPER_MAP["default"])
    if domain.mapeo_configuracion:
        selectors = domain.mapeo_configuracion.get("selectors", PLATFORM_SELECTORS.get(domain.plataforma, {}))
    else:
        selectors = PLATFORM_SELECTORS.get(domain.plataforma, {})
    return scraper_class(domain, custom_selectors=selectors)

class BaseScraper:
    def __init__(self, domain: DominioScraping, custom_selectors: Optional[Dict] = None):
        self.domain = domain
        self.plataforma = domain.plataforma
        self.selectors = custom_selectors or PLATFORM_SELECTORS.get(self.plataforma, {})
        self.response_type = "json" if self.plataforma in ["eightfold_ai", "oracle_hcm"] else "html"
        self.semaphore = asyncio.Semaphore(10)  # Adjust based on domain
        self.delay = domain.frecuencia_scraping / 3600  # Convert hours to seconds
        self.session = None

    async def __aenter__(self):
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        self.session = ClientSession(headers=headers, timeout=ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), 
           before_sleep=before_sleep_log(logger, logging.WARNING))
    async def fetch(self, url: str, use_playwright: bool = False) -> Optional[str]:
        
        if use_playwright:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url)
                await asyncio.sleep(2)  # Wait for dynamic content
                content = await page.content()
                await browser.close()
                return content
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise

    def _build_url(self, page: int) -> str:
        param = self.selectors.get("pagination_param", "page")
        step = self.selectors.get("pagination_step", 1)
        return f"{self.domain.dominio}?{param}={page * step}"

    async def scrape(self) -> List[JobListing]:
        if not self.selectors:
            raise NotImplementedError(f"No selectors defined for {self.plataforma}")
        vacantes = []
        page = 1
        seen_urls = set()
        async with self:
            while True:
                url = self._build_url(page)
                content = await self.fetch(url, use_playwright=self.plataforma in ["workday", "linkedin", "phenom_people"])
                if not content:
                    break
                if self.response_type == "json":
                    new_vacantes = await self._parse_json(content, seen_urls)
                else:
                    new_vacantes = await self._parse_html(content, seen_urls)
                if not new_vacantes:
                    break
                vacantes.extend(new_vacantes)
                page += 1
        return vacantes

    async def _parse_json(self, content: str, seen_urls: set) -> List[JobListing]:
        try:
            data = json.loads(content)
            jobs = data.get("jobs", data.get("jobList", []))
            vacantes = []
            for job in jobs:
                url = job.get("url", job.get("detailUrl", ""))
                if url not in seen_urls:
                    seen_urls.add(url)
                    vacantes.append(JobListing(
                        title=job.get("title", "No especificado"),
                        url=url,
                        location=job.get("locations", [{}])[0].get("name", "Unknown"),
                        company=job.get("company_name", "Unknown"),
                        description="No disponible",  # Can be enriched with get_job_details if needed
                    ))
            return vacantes
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return []

    async def _parse_html(self, content: str, seen_urls: set) -> List[JobListing]:
        soup = BeautifulSoup(content, "html.parser")
        job_cards = soup.select(self.selectors.get("job_cards", "div.job-card"))
        vacantes = []
        for card in job_cards:
            url_elem = extract_field(card, self.selectors["url"], "href")
            link = url_elem if url_elem and url_elem.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{url_elem or ''}"
            if link not in seen_urls:
                seen_urls.add(link)
                title = extract_field(card, self.selectors["title"]) or "No especificado"
                details = await self.get_job_details(link)
                vacantes.append(JobListing(
                    title=title,
                    url=link,
                    location=details.get("location", "Unknown"),
                    company=details.get("company", "Unknown"),
                    description=details.get("description", "No disponible"),
                    skills=details.get("skills", []),
                    posted_date=details.get("posted_date"),
                ))
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible", "location": "Unknown", "company": "Unknown"}
        soup = BeautifulSoup(content, "html.parser")
        description = soup.select_one(self.selectors.get("description"))
        location = soup.select_one(self.selectors.get("location"))
        company = soup.select_one(self.selectors.get("company"))
        posted_date = soup.select_one(self.selectors.get("posted_date"))
        details = {
            "description": description.text.strip() if description else "No disponible",
            "location": location.text.strip() if location else "Unknown",
            "company": company.text.strip() if company else "Unknown",
            "posted_date": posted_date.text.strip() if posted_date else None,
        }
        if details["description"] != "No disponible":
            analysis = await self.analyze_description(details["description"])
            details.update(analysis["details"])
        return details

    async def analyze_description(self, description: str) -> Dict:
        analysis = nlp_processor.analyze_opportunity(description)
        return {
            "details": {
                "skills": analysis.get("details", {}).get("skills", []),
                "contract_type": analysis.get("details", {}).get("contract_type"),
            },
            "sentiment": analysis.get("sentiment"),
            "job_classification": analysis.get("job_classification"),
        }
    
# Scrapers específicos
class WorkdayScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        while True:
            url = f"{self.domain.dominio}?{self.selectors.get('pagination_param', 'page')}={page * self.selectors.get('pagination_step', 1)}"
            content = await self.fetch(url, use_playwright=True)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.select(self.selectors["job_cards"])
            if not job_cards:
                break
            for card in job_cards:
                title = extract_field(card, self.selectors["title"]) or "No especificado"
                url_elem = extract_field(card, self.selectors["url"], "href")
                link = url_elem if url_elem.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{url_elem}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=title,
                        location=details.get("location", "Unknown"),
                        company=details.get("company", "Workday Employer"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=details.get("skills", []),
                        posted_date=details.get("posted_date"),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type"),
                    ))
            page += 1
        return vacantes

class LinkedInScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        while True:
            url = f"{self.domain.dominio}?{self.selectors.get('pagination_param', 'start')}={page * self.selectors.get('pagination_step', 25)}"
            content = await self.fetch(url, use_playwright=True)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.select(self.selectors["job_cards"])
            if not job_cards:
                break
            for card in job_cards:
                title = extract_field(card, self.selectors["title"]) or "No especificado"
                url_elem = extract_field(card, self.selectors["url"], "href")
                link = url_elem if url_elem.startswith("http") else f"https://www.linkedin.com{url_elem}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=title,
                        location=details.get("location", "Unknown"),
                        company=details.get("company", "Unknown"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=details.get("skills", []),
                        posted_date=details.get("posted_date"),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type"),
                    ))
            page += 1
        return vacantes

class PhenomPeopleScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        while True:
            url = f"{self.domain.dominio}?{self.selectors.get('pagination_param', 'page')}={page * self.selectors.get('pagination_step', 1)}"
            content = await self.fetch(url, use_playwright=True)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.select(self.selectors["job_cards"])
            if not job_cards:
                break
            for card in job_cards:
                title = extract_field(card, self.selectors["title"]) or "No especificado"
                url_elem = extract_field(card, self.selectors["url"], "href")
                link = url_elem if url_elem.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{url_elem}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=title,
                        location=details.get("location", "Unknown"),
                        company=details.get("company", "Phenom Employer"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=details.get("skills", []),
                        posted_date=details.get("posted_date"),
                        responsible=details.get("responsible"),
                        job_type=details.get("job_type"),
                    ))
            page += 1
        return vacantes

class SAPScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        while True:
            url = f"{self.domain.dominio}/jobs?page={page}"
            content = await self.fetch(url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.select(self.selectors.get("job_cards", ""))
            if not job_cards:
                break
            for card in job_cards:
                url_elem = extract_field(card, self.selectors["url"], "href")
                link = url_elem if url_elem.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{url_elem}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(**details))
            page += 1
        return vacantes

class EightfoldScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        while True:
            url = f"{self.domain.dominio}?page={page}&sort_by=relevance"
            content = await self.fetch(url)
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
                        vacantes.append(JobListing(
                            title=job.get("title", "No especificado"),
                            url=url,
                            description=job.get("description", "No disponible"),
                            location=job.get("locations", [{}])[0].get("name", "Unknown"),
                            company=job.get("company_name", "Eightfold Employer"),
                            responsible=job.get("responsible"),
                            job_type=job.get("job_type"),
                            posted_date=job.get("posted_date"),
                        ))
                page += 1
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}")
                break
        return vacantes

class OracleScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        while True:
            url = f"{self.domain.dominio}/jobs?page={page}"
            content = await self.fetch(url)
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
                        vacantes.append(JobListing(
                            title=job.get("title", "No especificado"),
                            url=url,
                            description=job.get("description", "No disponible"),
                            location=job.get("location", {}).get("city", "Unknown"),
                            company=job.get("company", "Oracle Employer"),
                            responsible=job.get("responsible"),
                            job_type=job.get("job_type"),
                            posted_date=job.get("posted_date"),
                        ))
                page += 1
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}")
                break
        return vacantes

# Otros scrapers como placeholders
class IndeedScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        while True:
            url = f"{self.domain.dominio}?start={page * self.selectors.get('pagination_step', 10)}"
            content = await self.fetch(url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.select(self.selectors["job_cards"])
            if not job_cards:
                break
            for card in job_cards:
                title = extract_field(card, self.selectors["title"]) or "No especificado"
                url_elem = extract_field(card, self.selectors["url"], "href")
                link = f"https://www.indeed.com{url_elem}" if url_elem else ""
                if link not in seen_urls:
                    seen_urls.add(link)
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=title,
                        location=details.get("location", "Unknown"),
                        company=details.get("company", "Unknown"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=details.get("skills", []),
                        posted_date=details.get("posted_date"),
                    ))
            page += 1
        return vacantes
    
class GreenhouseScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        while True:
            url = f"{self.domain.dominio}?{self.selectors.get('pagination_param', 'page')}={page * self.selectors.get('pagination_step', 1)}"
            content = await self.fetch(url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.select(self.selectors["job_cards"])
            if not job_cards:
                break
            for card in job_cards:
                title = extract_field(card, self.selectors["title"]) or "No especificado"
                url_elem = extract_field(card, self.selectors["url"], "href")
                link = url_elem if url_elem.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{url_elem}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    details = await self.get_job_details(link)
                    vacantes.append(JobListing(
                        title=title,
                        location=details.get("location", "Unknown"),
                        company=details.get("company", "Greenhouse Employer"),
                        url=link,
                        description=details.get("description", "No disponible"),
                        skills=details.get("skills", []),
                        posted_date=details.get("posted_date"),
                    ))
            page += 1
        return vacantes
    
class AccentureScraper(BaseScraper): pass
class ADPScraper(BaseScraper): pass
class PeopleSoftScraper(BaseScraper): pass
class Meta4Scraper(BaseScraper): pass
class CornerstoneScraper(BaseScraper): pass
class UKGScraper(BaseScraper): pass
class GlassdoorScraper(BaseScraper): pass
class ComputrabajoScraper(BaseScraper): pass
class FlexibleScraper(BaseScraper): pass

# Mapeo de Scrapers
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

# Funciones de publicación y ejecución
async def publish_to_internal_system(jobs: List[Dict], business_unit: BusinessUnit) -> bool:
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
        bu = await sync_to_async(BusinessUnit.objects.filter)(scraping_domains=domain).first()
        if bu and bu.admin_email:
            await send_email(
                business_unit_name=bu.name,
                subject=f"Scraping Error for {domain.dominio}",
                to_email=bu.admin_email,
                body=f"Error: {str(e)}\nDetails: {registro.error_log}",
                from_email="noreply@huntred.com",
            )
    finally:
        registro.fecha_fin = now()
        await sync_to_async(registro.save)()

@shared_task
async def run_all_scrapers() -> None:
    domains = await sync_to_async(list)(DominioScraping.objects.filter(activo=True, business_units__scrapping_enabled=True))
    await scrape_and_publish(domains)


# Selectors (mantén tu definición de PLATFORM_SELECTORS aquí)
PLATFORM_SELECTORS = {
    "workday": {
        "job_cards": "a[data-automation-id='jobTitle']",
        "title": "a[data-automation-id='jobTitle']",
        "url": "a[data-automation-id='jobTitle']",
        "description": "div[data-automation-id='jobPostingDescription']",
        "location": "div[data-automation-id='location']",
        "company": "div[data-automation-id='company']",
        "posted_date": "span[data-automation-id='postedDate']",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "linkedin": {
        "job_cards": "a.base-card__full-link",
        "title": "span.job-title",
        "url": "a.base-card__full-link",
        "description": "div.job-description",
        "location": "span.location",
        "company": "span.company",
        "posted_date": "time",
        "pagination_param": "start",
        "pagination_step": 25,
    },
    "indeed": {
        "job_cards": "div.job_seen_beacon",
        "title": "h2.jobTitle",
        "url": "a.jcs-JobTitle",
        "description": "div#jobDescriptionText",
        "location": "div.companyLocation",
        "company": "span.companyName",
        "posted_date": "span.date",
        "pagination_param": "start",
        "pagination_step": 10,
    },
    "greenhouse": {
        "job_cards": "div.opening",
        "title": "a",
        "url": "a",
        "description": "div.section-wrapper",
        "location": "span.location",
        "company": "span.company-name",
        "posted_date": "span.posted-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "accenture": {
        "job_cards": "div.cmp-teaser.card",
        "title": "h3.cmp-teaser__title",
        "url": "a.cmp-teaser__title-link",
        "description": "div.job-description",
        "location": "div.cmp-teaser-region, div.cmp-teaser-city",
        "company": "span.company-name",
        "posted_date": "p.cmp-teaser__job-listing-posted-date",
        "pagination_param": "pg",
        "pagination_step": 1,
    },
    "eightfold_ai": {
        "job_cards": None,  # Usa JSON, no selectores directos
        "title": None,
        "url": None,
        "description": "div.job-details",
        "location": "span.job-location",
        "company": "span.company-name",
        "posted_date": "span.posted-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "phenom_people": {
        "job_cards": "div.job-card",
        "title": "h3",
        "url": "a",
        "description": "div.job-details",
        "location": "span.job-location",
        "company": "span.company-name",
        "posted_date": "span.posted-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "oracle_hcm": {
        "job_cards": None,  # Usa JSON
        "title": None,
        "url": None,
        "description": "div.job-description",
        "location": "span.location",
        "company": "span.company",
        "posted_date": "span.posted-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "sap_successfactors": {
        "job_cards": "div.job-item",
        "title": "h3.job-title",
        "url": "a.job-url",
        "description": "div.job-description",
        "location": "span.job-location",
        "company": "span.job-company",
        "posted_date": "span.post-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "adp": {
        "job_cards": "li.job-posting",
        "title": "a.job-title",
        "url": "a.job-title",
        "description": "div.job-content",
        "location": "span.location",
        "company": "span.company",
        "posted_date": "span.posted-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "peoplesoft": {
        "job_cards": "div.job-card",
        "title": "h3",
        "url": "a",
        "description": "div.job-desc",
        "location": "span.location",
        "company": "span.company",
        "posted_date": "span.posted-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "meta4": {
        "job_cards": "div.job-item",
        "title": "h3",
        "url": "a",
        "description": "div.job-info",
        "location": "span.location",
        "company": "span.company",
        "posted_date": "span.posted-date",
        "pagination_param": "p",
        "pagination_step": 1,
    },
    "cornerstone": {
        "job_cards": "li.job",
        "title": "a.job-title",
        "url": "a.job-title",
        "description": "div.job-description",
        "location": "span.job-location",
        "company": "span.job-company",
        "posted_date": "span.posted-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "ukg": {
        "job_cards": "div.job-entry",
        "title": "h2",
        "url": "a",
        "description": "div.job-details",
        "location": "span.job-location",
        "company": "span.job-company",
        "posted_date": "span.posted-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "glassdoor": {
        "job_cards": "li.react-job-listing",
        "title": "a.jobLink",
        "url": "a.jobLink",
        "description": "div.job-description",
        "location": "span.jobLocation",
        "company": "div.jobCompany",
        "posted_date": "span.posted-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "computrabajo": {
        "job_cards": "article.box_border",
        "title": "h1",
        "url": "a.js-o-link",
        "description": "div.job-description",
        "location": "span.location",
        "company": "span.company",
        "posted_date": "span.posted-date",
        "pagination_param": "p",
        "pagination_step": 1,
    }
}
