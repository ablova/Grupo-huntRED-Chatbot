# /home/pablo/app/utilidades/scraping.py
import json
import random
import asyncio
import re
from celery import shared_task
from asgiref.sync import sync_to_async
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
import trafilatura
from playwright.async_api import async_playwright
from django.db import transaction
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.core.management.base import BaseCommand
from app.models import DominioScraping, RegistroScraping, Vacante, BusinessUnit, ConfiguracionBU, Worker, USER_AGENTS, WeightingModel
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from app.chatbot.utils import clean_text
from app.utilidades.loader import DIVISION_SKILLS
from app.chatbot.gpt import GPTHandler
from app.chatbot.nlp import NLPProcessor
from app.utilidades.vacantes import VacanteManager
from prometheus_client import Counter, Histogram, start_http_server
import logging

logger = logging.getLogger(__name__)


# Constantes para assign_business_unit
BUSINESS_UNITS_KEYWORDS = {
    'huntRED®': {
        'manager': 2, 'director': 3, 'leadership': 2, 'senior manager': 4, 'operations manager': 3,
        'project manager': 3, 'head of': 4, 'gerente': 2, 'director de': 3, 'jefe de': 4, 'subdirector':3
    },
    'huntRED® Executive': {
        'strategic': 3, 'board': 4, 'global': 3, 'vp': 4, 'president': 4, 'cfo': 5, 'ceo': 5, 'coo': 5, 'consejero':4,
        'executive': 4, 'cto': 5, 'chief': 4, 'executive director': 5, 'senior vp': 5, 'vice president': 4,
        'estrategico': 3, 'global': 3, 'presidente': 4, 'chief':4
    },
    'huntu': {
        'trainee': 3, 'junior': 3, 'entry-level': 4, 'intern': 3, 'graduate': 3, 'developer': 2, 'engineer': 2,
        'senior developer': 3, 'lead developer': 3, 'software engineer': 2, 'data analyst': 2, 'it specialist': 2,
        'technical lead': 3, 'architect': 3, 'analyst': 2, 'specialist': 2, 'consultant': 2, 'programador': 2,
        'ingeniero': 2, 'analista': 2, 'recié egresado': 2, 'practicante': 2, 'pasante': 2, 'becario': 2, 'líder': 2, 'coordinardor': 2, 
    },
    'amigro': {
        'migration': 4, 'bilingual': 3, 'visa sponsorship': 4, 'temporary job': 3, 'worker': 2, 'operator': 2,
        'constructor': 2, 'laborer': 2, 'assistant': 2, 'technician': 2, 'support': 2, 'seasonal': 2,
        'entry-level': 2, 'no experience': 3, 'trabajador': 2, 'operador': 2, 'asistente': 2, 'migración': 4, 'ejecutivo': 2, 'auxiliar': 3, 'soporte': 3, 
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
        return await cache.get(key)

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
        "business_unit": assign_business_unit({"title": job.title, "description": job.description, "skills": job.skills, "location": job.location})
    }

class WeightingModel:
    def __init__(self, business_unit):
        self.business_unit = business_unit
        self.weights = self._load_weights()

    @sync_to_async
    def _load_weights(self):
        """Carga los pesos de la configuración de la unidad de negocio de forma asíncrona."""
        try:
            config = ConfiguracionBU.objects.get(business_unit=self.business_unit)
            return {
                "hard_skills": config.hard_skills_weight,
                "soft_skills": config.soft_skills_weight,
                "personalidad": config.personality_weight,
                "ubicacion": config.location_weight
            }
        except ConfiguracionBU.DoesNotExist:
            # Valores por defecto si no hay configuración
            return {
                "hard_skills": 1.0,
                "soft_skills": 1.0,
                "personalidad": 1.0,
                "ubicacion": 1.0
            }

    def get_weights(self, level: str):
        """Devuelve los pesos para el nivel especificado."""
        return self.weights

async def assign_business_unit(job_title: str, job_description: str = None, salary_range: str = None, required_experience: str = None, location: str = None) -> Optional[int]:
    """Determina la unidad de negocio para una vacante con pesos dinámicos de forma asíncrona."""
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
        weighting = WeightingModel(bu)  # _load_weights ya es asíncrono gracias a @sync_to_async
        weights = await weighting.get_weights("operativo")  # Añadimos await aquí porque es asíncrono

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
                elif bu.name == 'huntRED®':
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
                chosen_bu = next(bu for bu in priority_order if bu in candidates)
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
            default_bu = await sync_to_async(BusinessUnit.objects.get)(name='huntRED®')
            logger.info(f"🔧 Asignada huntRED® por defecto (ID: {default_bu.id}) para '{job_title}'")
            return default_bu.id
        except BusinessUnit.DoesNotExist:
            logger.error(f"❌ Unidad de negocio por defecto 'huntRED®' no encontrada en BD")
            return None
        
# Wrapper síncrono para assign_business_unit
def assign_business_unit_sync(*args, **kwargs) -> Optional[int]:
    return asyncio.run(assign_business_unit(*args, **kwargs))

# Función genérica para enriquecer vacantes con GPT
async def enrich_with_gpt(vacante, gpt_handler: GPTHandler) -> bool:
    """Enriquece una vacante usando un modelo GPT configurado."""
    prompt = (
        f"Para el puesto '{vacante.titulo}' en {vacante.ubicacion}, genera una descripción con 10-12 actividades específicas, "
        f"una lista de al menos 15 habilidades relevantes y un salario estimado en MXN. "
        f"Devuelve un JSON con las claves: 'description' (texto), 'skills' (lista), 'salary' (dict con 'min' y 'max')."
    )
    response = await gpt_handler.generate_response(prompt)
    try:
        data = json.loads(response)
        vacante.descripcion = data.get("description", "No disponible")
        vacante.skills_required = data.get("skills", [])
        vacante.salario = data.get("salary", {"min": None, "max": None})["min"]
        vacante.modalidad = "Híbrido"  # Valor por defecto
        vacante.beneficios = ""
        vacante.procesamiento_count += 1
        await sync_to_async(vacante.save)()  # Guardamos de forma asíncrona
        return True
    except json.JSONDecodeError:
        logger.error(f"Respuesta de GPT no válida: {response}")
        return False

@transaction.atomic
async def save_vacantes(jobs: List[Dict], dominio: DominioScraping):
    seen_keys = set()
    for job in jobs:
        key = f"{job['title']}:{job['company']}:{job['location']}"
        if key in seen_keys:
            logger.info(f"Vacante duplicada omitida: {job['title']}")
            continue
        seen_keys.add(key)
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

def extract_field(html: str, selectors: List[str], attribute: Optional[str] = None) -> Optional[str]:
    cleaned_text = trafilatura.extract(html) or html
    soup = BeautifulSoup(html, "html.parser")
    for selector in selectors:
        try:
            elem = soup.select_one(selector)
            if elem:
                return elem[attribute] if attribute else elem.text.strip()
        except Exception as e:
            logger.warning(f"Error con selector {selector}: {e}")
    if not attribute:
        match = re.search(r"(?:job[- ]?title|puesto)[\s:]*([^<\n]+)", cleaned_text, re.IGNORECASE)
        return match.group(1).strip() if match else None
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
        self.semaphore = asyncio.Semaphore(10)
        self.delay = domain.frecuencia_scraping / 3600
        self.session = None
        # Cargar cookies desde la base de datos
        self.cookies = domain.cookies or {}

    async def __aenter__(self):
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        self.session = ClientSession(headers=headers, timeout=ClientTimeout(total=30), cookies=self.cookies)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), 
           before_sleep=before_sleep_log(logger, logging.WARNING))
    async def fetch(self, url: str, use_playwright: bool = False) -> Optional[str]:
        if use_playwright or self.plataforma in ["linkedin", "workday", "phenom_people"]:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                # Aplicar cookies desde la base de datos
                if self.cookies:
                    await page.context.add_cookies([{"name": k, "value": v, "domain": self.domain.dominio.split('/')[2], "path": "/"} for k, v in self.cookies.items()])
                await page.goto(url, wait_until="networkidle")
                await asyncio.sleep(2)  # Espera para carga dinámica
                content = await page.content()
                await browser.close()
                return content
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.text()

    def _build_url(self, page: int) -> str:
        pagination = self.selectors.get("pagination", {"param": "page", "step": 1})
        param, step = pagination.get("param", "page"), pagination.get("step", 1)
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
                logger.info(f"Scrapeando página {page}: {url}")
                content = await self.fetch(url, use_playwright=self.plataforma in ["workday", "linkedin", "phenom_people"])
                if not content:
                    logger.info(f"No hay más contenido en página {page}")
                    break
                if self.response_type == "json":
                    new_vacantes = await self._parse_json(content, seen_urls)
                else:
                    new_vacantes = await self._parse_html(content, seen_urls)
                if not new_vacantes:
                    logger.info(f"No se encontraron más vacantes en página {page}")
                    break
                vacantes.extend(new_vacantes)
                page += 1
                await asyncio.sleep(self.delay)
        logger.info(f"Scraping finalizado con {len(vacantes)} vacantes")
        return vacantes

    async def _parse_json(self, content: str, seen_urls: set) -> List[JobListing]:
        try:
            data = json.loads(content)
            jobs = data.get("jobs") or data.get("jobList") or data.get("results", {}).get("jobs", [])
            vacantes = []
            for job in jobs:
                url = job.get("url") or job.get("detailUrl") or job.get("applyUrl", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    location = (job.get("locations") or [{}])[0].get("name") or job.get("location", {}).get("city", "Unknown")
                    vacantes.append(JobListing(
                        title=job.get("title", "No especificado"),
                        url=url,
                        location=location,
                        company=job.get("company_name") or job.get("organization", "Unknown"),
                        description=job.get("description", "No disponible"),
                    ))
            return vacantes
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return []

    async def _parse_html(self, content: str, seen_urls: set) -> List[JobListing]:
        cleaned_text = trafilatura.extract(content) or content
        soup = BeautifulSoup(content, "html.parser")
        job_cards = soup.select(self.selectors.get("job_cards", "div.job-card"))
        vacantes = []
        tasks = []
        for card in job_cards:
            url_elem = extract_field(str(card), [self.selectors["url"]], "href")
            link = url_elem if url_elem and url_elem.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{url_elem or ''}"
            if link not in seen_urls:
                seen_urls.add(link)
                title = extract_field(str(card), [self.selectors["title"]]) or "No especificado"
                tasks.append(self.get_job_details(link))
        details_list = await asyncio.gather(*tasks)
        for idx, detail in enumerate(details_list):
            vacantes.append(JobListing(
                title=extract_field(str(job_cards[idx]), [self.selectors["title"]]) or "No especificado",
                url=link,
                location=detail.get("location", "Unknown"),
                company=detail.get("company", "Unknown"),
                description=detail.get("description", "No disponible"),
                skills=detail.get("skills", []),
                posted_date=detail.get("posted_date"),
            ))
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        content = await self.fetch(url)
        if not content:
            return {"description": "No disponible", "location": "Unknown", "company": "Unknown"}
        description = extract_field(content, [self.selectors.get("description", "div.job-description")])
        location = extract_field(content, [self.selectors.get("location", "span.location")])
        company = extract_field(content, [self.selectors.get("company", "span.company")])
        posted_date = extract_field(content, [self.selectors.get("posted_date", "span.posted-date")])
        details = {
            "description": description or "No disponible",
            "location": location or "Unknown",
            "company": company or "Unknown",
            "posted_date": posted_date,
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
        base_url = self.domain.dominio.rsplit('/', 1)[0]  # Ajustar según el dominio real

        while True:
            url = f"{self.domain.dominio}?page={page}"
            content = await self.fetch(url, use_playwright=True)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.select('a[data-automation-id="jobTitle"]')
            if not job_cards:
                break

            tasks = []
            for card in job_cards:
                title = card.get_text(strip=True)
                relative_url = card.get("href", "")
                full_url = f"{base_url}{relative_url}" if relative_url.startswith('/') else relative_url
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    tasks.append(self.get_job_details(full_url))

            details_list = await asyncio.gather(*tasks)
            for detail in details_list:
                if detail:  # Asegurarse de que se obtuvieron detalles
                    vacantes.append(JobListing(
                        title=detail.get("title", "No especificado"),
                        location=detail.get("location", "Unknown"),
                        company=detail.get("company", "Santander"),
                        url=detail.get("original_url", ""),
                        description=detail.get("description", "No disponible"),
                        skills=detail.get("skills", [])
                    ))
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        content = await self.fetch(url, use_playwright=True)
        if not content:
            return {}
        soup = BeautifulSoup(content, "html.parser")
        title_elem = soup.select_one('h2[data-automation-id="jobTitle"]') or soup.select_one('h1')
        desc_elem = soup.select_one('div[data-automation-id="jobPostingDescription"]') or soup.select_one('div.job-description')
        loc_elem = soup.select_one('div[data-automation-id="location"]') or soup.select_one('span.location')
        return {
            "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
            "description": desc_elem.get_text(strip=True) if desc_elem else "No disponible",
            "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
            "company": "Santander",  # Ajustar según dominio si no es fijo
            "skills": extract_skills(content),
            "original_url": url
        }

class LinkedInScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        async with self:
            while True:
                url = f"{self.domain.dominio}&start={page * 25}"
                logger.info(f"Scrapeando página {page}: {url}")
                try:
                    async with asyncio.timeout(180):  # Timeout de 180 segundos
                        content = await self.fetch(url, use_playwright=True)
                except asyncio.TimeoutError:
                    logger.error(f"Timeout al scrapear página {page}: {url}")
                    break
                if not content:
                    logger.info("No hay más contenido para scrapear.")
                    break
                soup = BeautifulSoup(content, "html.parser")
                job_cards = soup.select("a.base-card__full-link, li.jobs-search-results__list-item a")
                if not job_cards:
                    logger.info("No se encontraron más tarjetas de trabajo.")
                    break
                tasks = []
                for card in job_cards:
                    link = card.get("href", "")
                    if link and link not in seen_urls:
                        seen_urls.add(link)
                        tasks.append(self.get_job_details(link))
                logger.info(f"Encontradas {len(tasks)} vacantes en página {page}")
                details_list = await asyncio.gather(*tasks)
                for detail in details_list:
                    if detail:
                        vacantes.append(JobListing(
                            title=detail.get("title", "No especificado"),
                            location=detail.get("location", "Unknown"),
                            company=detail.get("company", "Unknown"),
                            url=detail.get("original_url", ""),
                            description=detail.get("description", "No disponible"),
                            skills=detail.get("skills", []),
                            posted_date=detail.get("posted_date"),
                            job_type=detail.get("job_type"),
                            benefits=detail.get("benefits", []),
                        ))
                page += 1
        logger.info(f"Scraping finalizado con {len(vacantes)} vacantes.")
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        content = await self.fetch(url, use_playwright=True)
        if not content:
            return {}
        soup = BeautifulSoup(content, "html.parser")
        title_elem = soup.select_one("h1.topcard__title, h1")
        desc_elem = soup.select_one("div.description__text, div.show-more-less-html__markup, div.jobs-description-content__text")
        loc_elem = soup.select_one("span.topcard__flavor--bullet, span.jobs-unified-top-card__bullet")
        comp_elem = soup.select_one("a.topcard__org-name-link, span.jobs-unified-top-card__company-name")
        date_elem = soup.select_one("span.posted-time-ago__text, span.jobs-unified-top-card__posted-date")
        modality_elem = soup.select_one("span.jobs-unified-top-card__workplace-type")
        benefits_elem = soup.select("div.jobs-description__details--benefits ul li")
        
        description = desc_elem.get_text(strip=True) if desc_elem else "No disponible"
        skills = extract_skills(description)
        
        # Buscar enlace a descripción completa (como UCPath)
        apply_link_elem = soup.select_one("a.jobs-apply-button, a[href*='marketpayjobs']")
        external_details = {}
        if apply_link_elem:
            external_url = apply_link_elem.get("href")
            if "marketpayjobs" in external_url:
                external_content = await self.fetch(external_url, use_playwright=True)
                if external_content:
                    ext_soup = BeautifulSoup(external_content, "html.parser")
                    ext_desc_elem = ext_soup.select_one("div.job-description, div#content")
                    if ext_desc_elem:
                        description = ext_desc_elem.get_text(strip=True)
                        skills = extract_skills(description)
                    ext_benefits_elem = ext_soup.select("div.benefits ul li")
                    external_details["benefits"] = [elem.get_text(strip=True) for elem in ext_benefits_elem] if ext_benefits_elem else []

        return {
            "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
            "description": description,
            "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
            "company": comp_elem.get_text(strip=True) if comp_elem else "Unknown",
            "posted_date": date_elem.get_text(strip=True) if date_elem else None,
            "skills": skills,
            "original_url": url,
            "job_type": modality_elem.get_text(strip=True) if modality_elem else None,  # Corrección aquí
            "benefits": external_details.get("benefits", [b.get_text(strip=True) for b in benefits_elem]) if benefits_elem else [],
        }
    
class PhenomPeopleScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        seen_urls = set()
        base_url = self.domain.dominio.rsplit('/', 1)[0]  # Ajustar según el dominio real

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            if self.cookies:
                await page.context.add_cookies([{"name": k, "value": v, "domain": self.domain.dominio.split('/')[2], "path": "/"} for k, v in self.cookies.items()])
            await page.goto(self.domain.dominio, wait_until="networkidle")

            while True:
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                job_cards = soup.select('a.job-title-link')
                if not job_cards:
                    break

                tasks = []
                for card in job_cards:
                    title = card.get_text(strip=True)
                    relative_url = card.get("href", "")
                    full_url = f"{base_url}{relative_url}" if relative_url.startswith('/') else relative_url
                    if full_url not in seen_urls:
                        seen_urls.add(full_url)
                        tasks.append(self.get_job_details(full_url))

                details_list = await asyncio.gather(*tasks)
                for detail in details_list:
                    if detail:
                        vacantes.append(JobListing(
                            title=detail.get("title", "No especificado"),
                            location=detail.get("location", "Unknown"),
                            company=detail.get("company", "Honeywell"),
                            url=detail.get("original_url", ""),
                            description=detail.get("description", "No disponible"),
                            skills=detail.get("skills", [])
                        ))

                load_more_button = await page.query_selector('button.load-more')
                if load_more_button:
                    await load_more_button.click()
                    await page.wait_for_load_state('networkidle')
                else:
                    break

            await browser.close()
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        content = await self.fetch(url, use_playwright=True)
        if not content:
            return {}
        soup = BeautifulSoup(content, "html.parser")
        title_elem = soup.select_one('h1.job-title') or soup.select_one('h1')
        desc_elem = soup.select_one('div.job-description') or soup.select_one('div.description')
        loc_elem = soup.select_one('span.job-location') or soup.select_one('span.location')
        return {
            "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
            "description": desc_elem.get_text(strip=True) if desc_elem else "No disponible",
            "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
            "company": "Honeywell",  # Ajustar según dominio si no es fijo
            "skills": extract_skills(content),
            "original_url": url
        }

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
            job_cards = soup.select(self.selectors.get("job_cards", "div.job-item"))
            if not job_cards:
                break
            tasks = []
            for card in job_cards:
                url_elem = extract_field(str(card), [self.selectors["url"]], "href")
                link = url_elem if url_elem and url_elem.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{url_elem}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    tasks.append(self.get_job_details(link))
            details_list = await asyncio.gather(*tasks)
            for detail in details_list:
                if detail:
                    vacantes.append(JobListing(**detail))
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
            tasks = []
            for card in job_cards:
                title = extract_field(str(card), [self.selectors["title"]]) or "No especificado"
                url_elem = extract_field(str(card), [self.selectors["url"]], "href")
                link = f"https://www.indeed.com{url_elem}" if url_elem and not url_elem.startswith("http") else url_elem
                if link and link not in seen_urls:
                    seen_urls.add(link)
                    tasks.append(self.get_job_details(link))
            details_list = await asyncio.gather(*tasks)
            for detail in details_list:
                if detail:
                    vacantes.append(JobListing(
                        title=detail.get("title", "No especificado"),
                        location=detail.get("location", "Unknown"),
                        company=detail.get("company", "Unknown"),
                        url=detail.get("original_url", ""),
                        description=detail.get("description", "No disponible"),
                        skills=detail.get("skills", []),
                        posted_date=detail.get("posted_date"),
                    ))
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        content = await self.fetch(url)
        if not content:
            return {}
        soup = BeautifulSoup(content, "html.parser")
        title_elem = soup.select_one("h1.jobTitle") or soup.select_one("h1")
        desc_elem = soup.select_one("div#jobDescriptionText") or soup.select_one("div.job-description")
        loc_elem = soup.select_one("div.companyLocation") or soup.select_one("span.location")
        comp_elem = soup.select_one("span.companyName") or soup.select_one("span.company")
        date_elem = soup.select_one("span.date") or soup.select_one("span.posted-date")
        return {
            "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
            "description": desc_elem.get_text(strip=True) if desc_elem else "No disponible",
            "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
            "company": comp_elem.get_text(strip=True) if comp_elem else "Unknown",
            "posted_date": date_elem.get_text(strip=True) if date_elem else None,
            "skills": extract_skills(content),
            "original_url": url
        }
    
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
            tasks = []
            for card in job_cards:
                title = extract_field(str(card), [self.selectors["title"]]) or "No especificado"
                url_elem = extract_field(str(card), [self.selectors["url"]], "href")
                link = url_elem if url_elem and url_elem.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{url_elem}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    tasks.append(self.get_job_details(link))
            details_list = await asyncio.gather(*tasks)
            for detail in details_list:
                if detail:
                    vacantes.append(JobListing(
                        title=detail.get("title", "No especificado"),
                        location=detail.get("location", "Unknown"),
                        company=detail.get("company", "Greenhouse Employer"),
                        url=detail.get("original_url", ""),
                        description=detail.get("description", "No disponible"),
                        skills=detail.get("skills", []),
                        posted_date=detail.get("posted_date"),
                    ))
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        content = await self.fetch(url)
        if not content:
            return {}
        soup = BeautifulSoup(content, "html.parser")
        title_elem = soup.select_one("h1.app-title") or soup.select_one("h1")
        desc_elem = soup.select_one("div#content") or soup.select_one("div.job-description")
        loc_elem = soup.select_one("div.location") or soup.select_one("span.location")
        comp_elem = soup.select_one("span.company-name") or soup.select_one("span.company")
        date_elem = soup.select_one("span.posted-date") or soup.select_one("time")
        return {
            "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
            "description": desc_elem.get_text(strip=True) if desc_elem else "No disponible",
            "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
            "company": comp_elem.get_text(strip=True) if comp_elem else "Greenhouse Employer",
            "posted_date": date_elem.get_text(strip=True) if date_elem else None,
            "skills": extract_skills(content),
            "original_url": url
        }
    
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
        scraper = await get_scraper(domain)
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
        async with asyncio.timeout(3600):
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
            from app.chatbot.integrations.services import send_email
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
        return domain, []

@shared_task
async def run_all_scrapers() -> None:
    domains = await sync_to_async(list)(DominioScraping.objects.filter(activo=True, business_units__scrapping_enabled=True))
    await scrape_and_publish(domains)

# Selectors
PLATFORM_SELECTORS = {
    "workday": {
        "job_cards": "a[data-automation-id='jobTitle']",
        "title": "h2[data-automation-id='jobTitle']",
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
        "title": "h1.topcard__title",
        "url": "a.base-card__full-link",
        "description": "div.description__text",
        "location": "span.topcard__flavor--bullet",
        "company": "a.topcard__org-name-link",
        "posted_date": "span.posted-time-ago__text",
        "pagination_param": "start",
        "pagination_step": 25,
    },
    "indeed": {
        "job_cards": "div.job_seen_beacon",
        "title": "h1.jobTitle",
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
        "title": "h1.app-title",
        "url": "a",
        "description": "div#content",
        "location": "div.location",
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
        "job_cards": None,
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
        "job_cards": "a.job-title-link",
        "title": "h1.job-title",
        "url": "a.job-title-link",
        "description": "div.job-description",
        "location": "span.job-location",
        "company": "span.company-name",
        "posted_date": "span.posted-date",
        "pagination_param": "page",
        "pagination_step": 1,
    },
    "oracle_hcm": {
        "job_cards": None,
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

# Comando para ejecutar scrapers manualmente
class Command(BaseCommand):
    help = 'Ejecuta el scraper para todos los dominios activos'

    def handle(self, *args, **options):
        asyncio.run(run_all_scrapers())