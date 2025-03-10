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