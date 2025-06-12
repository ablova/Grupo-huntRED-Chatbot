# /home/pablo/app/ats/utils/scraping.py
import json
import random
import asyncio
import re
from django.db import transaction
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
import logging
from celery import shared_task
from asgiref.sync import sync_to_async
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
import trafilatura
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from app.ats.chatbot.utils.chatbot_utils import ChatbotUtils
from app.ats.utils.loader import DIVISION_SKILLS
from app.ats.chatbot.core.gpt import GPTHandler
from app.ats.chatbot.nlp.nlp import NLPProcessor
from app.ats.utils.vacantes import VacanteManager
from app.ats.utils.scraping_utils import ScrapingMetrics, SystemHealthMonitor, ScrapingCache, inicializar_contexto_playwright, visitar_pagina_humanizada, extraer_y_guardar_cookies
from app.ats.utils.parser import parse_job_listing, save_job_to_vacante
from app.ml.core.utils.scraping import MLScraper
from app.ats.utils.parser import parse_job_listing, save_job_to_vacante
import time
import aiohttp
from aiohttp import resolver
from urllib.parse import urljoin
from app.ats.utils.user_agent_rotator import UserAgentRotator
from playwright.async_api import async_playwright
import gc

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

class ScrapingPipeline:
    def __init__(self):
        self.cache = ScrapingCache()
        self.processor = NLPProcessor(language="es", mode="opportunity")
        self.gpt_handler = GPTHandler()
        self.ml_scraper = MLScraper()
        self.skill_classifier = SkillClassifier()
        self.health_monitor = SystemHealthMonitor()

    async def process(self, jobs: List[Dict]) -> List[Dict]:
        await self.gpt_handler.initialize()
        try:
            jobs = await self.clean_data(jobs)
            jobs = await self.enrich_data(jobs)
            jobs = await self.validate_data(jobs)
            jobs = await self.classify_skills(jobs)
        finally:
            await self.gpt_handler.close()
        return jobs

    async def classify_skills(self, jobs: List[Dict]) -> List[Dict]:
        """Clasifica las habilidades de cada trabajo usando múltiples sistemas."""
        for job in jobs:
            if job.get("skills"):
                skill_classification = await self.skill_classifier.classify_skills(job["skills"])
                job["skill_classification"] = skill_classification
                
                # Determinar la mejor clasificación para cada habilidad
                best_classifications = {}
                for skill, classifications in skill_classification.items():
                    best = await self.skill_classifier.get_best_classification(skill)
                    best_classifications[skill] = best
                job["best_skill_classification"] = best_classifications
        
        return jobs

    async def _process_batch(self, items: List[Dict]) -> List[Dict]:
        """Procesa un lote de elementos de manera asíncrona."""
        processed = []
        for item in items:
            processed.append(await self._process_item(item))
        return processed

    async def _process_item(self, item: Dict) -> Dict:
        """Procesa un elemento individual."""
        try:
            result = await self._process_data(item)
            await self._save_result(result)
            return result
        except Exception as e:
            logger.error(f"Error processing item: {e}")
            return {"error": str(e)}

    async def clean_data(self, jobs: List[Dict]) -> List[Dict]:
        """Limpia datos y enriquece con GPT si falta descripción."""
        from app.models import Vacante  # Importación local
        cleaned_jobs = []
        for job in jobs:
            if job.get('title') and job.get('url'):
                if not job.get('description') or job['description'] == "No disponible":
                    vacante = Vacante(
                        titulo=job['title'],
                        url_original=job['url'],
                        ubicacion=job.get('location', 'No especificada')
                    )
                    if await self.enrich_with_gpt(vacante):
                        job['description'] = vacante.descripcion
                        job['skills'] = vacante.skills_required
                cleaned_jobs.append(job)
        return cleaned_jobs

    async def enrich_with_gpt(self, vacante) -> bool:
        """Enriches a vacancy with GPT if critical fields are missing."""
        prompt = (
            f"Para el puesto '{vacante.titulo}' en {vacante.ubicacion or 'No especificada'}, "
            f"genera una descripción detallada de 200-300 palabras y una lista de al menos 10 habilidades relevantes. "
            f"Devuelve un JSON con las claves: 'description' (texto), 'skills' (lista)."
        )
        try:
            response = await self.gpt_handler.generate_response(prompt)
            response = response.strip().lstrip('```json').rstrip('```').strip()
            data = json.loads(response)
            vacante.descripcion = data.get("description", vacante.descripcion or "No disponible")[:3000]
            vacante.skills_required = data.get("skills", vacante.skills_required or [])
            vacante.procesamiento_count = getattr(vacante, 'procesamiento_count', 0) + 1
            await sync_to_async(vacante.save)()
            logger.info(f"Vacante enriquecida con GPT: {vacante.titulo}")
            return True
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error enriqueciendo vacante con GPT: {e}")
            return False
        
    async def enrich_data(self, jobs: List[Dict]) -> List[Dict]:
        """Enriquece los datos de los trabajos con análisis profundo."""
        for job in jobs:
            cache_key = f"{job['url']}_{job['title']}"
            cached = await self.cache.get(cache_key)
            if cached:
                job.update(cached)
            else:
                job['scraped_at'] = datetime.now().isoformat()
                if job["description"] != "No disponible":
                    analysis = await self.processor.analyze(job["description"])
                    job.update(analysis)
                    
                    # Agregar análisis adicional
                    job["salary_estimate"] = await self._estimate_salary(job)
                    job["requirement_complexity"] = await self._analyze_requirements(job)
                    
                    # Clasificar el trabajo
                    job["job_classification"] = await self._classify_job(job)
                
                # Guardar en cache con TTL
                await self.cache.set(cache_key, job, ttl=3600)  # 1 hora
                
                # Registrar métricas
                self.health_monitor.record_success()
        return jobs

    async def _estimate_salary(self, job: Dict) -> Dict:
        """Estima el salario basado en el análisis del trabajo."""
        if job.get("salary"):
            return job["salary"]
        
        # Usar el estimador de salario del NLPProcessor
        return await self.processor.salary_estimator.estimate(job["description"])

    async def _analyze_requirements(self, job: Dict) -> Dict:
        """Analiza la complejidad de los requisitos del trabajo."""
        requirements = job.get("requirements", [])
        complexity = {
            "technical": 0,
            "years": 0,
            "education": "none"
        }
        
        for req in requirements:
            if "años" in req.lower():
                complexity["years"] += 1
            if any(tech in req.lower() for tech in ["python", "java", "sql"]):
                complexity["technical"] += 1
            if any(edu in req.lower() for edu in ["licenciatura", "maestría"]):
                complexity["education"] = "required"
        
        return complexity

    async def _classify_job(self, job: Dict) -> Dict:
        """Clasifica el trabajo usando múltiples criterios."""
        classification = {
            "category": "unknown",
            "level": "unknown",
            "seniority": "unknown",
            "type": "unknown"
        }
        
        # Usar el clasificador de trabajos del NLPProcessor
        return await self.processor.job_classifier.classify(job["description"])

    async def validate_data(self, jobs: List[Dict]) -> List[Dict]:
        validated_jobs = []
        for job in jobs:
            validated = validate_job_data(JobListing(**job))
            if validated:
                validated_jobs.append(validated)
            else:
                enriched_job = await self.enrich_missing_fields(job)
                validated = validate_job_data(JobListing(**enriched_job))
                if validated:
                    validated_jobs.append(validated)
        return validated_jobs

    async def enrich_missing_fields(self, job: Dict) -> Dict:
        if not job.get("description") or job["description"] == "No disponible":
            details = await self.ml_scraper.extract_job_details(job["url"], job.get("plataforma", "default"))
            job.update(details)
        if not job.get("description") or job["description"] == "No disponible":
            vacante = Vacante(titulo=job["title"], url_original=job["url"])
            if await self.enrich_with_gpt(vacante):
                job["description"] = vacante.descripcion
                job["skills"] = vacante.skills_required
        return job

def validate_job_data(job: JobListing) -> Optional[Dict]:
    required_fields = ["title", "location", "company", "description", "url"]
    if not all(getattr(job, field) for field in required_fields):
        logger.warning(f"Missing required fields in job: {job.title}")
        return None
    return {
        "title": ChatbotUtils.clean_text(job.title),
        "location": ChatbotUtils.clean_text(job.location),
        "company": ChatbotUtils.clean_text(job.company),
        "description": ChatbotUtils.clean_text(job.description),
        "url": job.url,
        "skills": job.skills or extract_skills(job.description),
        "sectors": job.sectors or associate_divisions(job.skills or []),
        "salary": job.salary,
        "responsible": ChatbotUtils.clean_text(job.responsible) if job.responsible else None,
        "posted_date": job.posted_date,
        "contract_type": job.contract_type,
        "job_type": job.job_type,
        "benefits": job.benefits or [],
        "business_unit": assign_business_unit({"title": job.title, "description": job.description, "skills": job.skills, "location": job.location})
    }

    
async def assign_business_unit(job_title: str, job_description: str = None, salary_range: str = None, required_experience: str = None, location: str = None) -> Optional[int]:
    """Determina la unidad de negocio para una vacante con pesos dinámicos de forma asíncrona."""
    from app.models import BusinessUnit  # Importación local
    # Normalize inputs for case-insensitive matching
    job_title_lower = job_title.lower()
    job_desc_lower = job_description.lower() if job_description else ""
    location_lower = location.lower() if location else ""

    # Fetch all business units asynchronously
    bu_candidates = await sync_to_async(list)(BusinessUnit.objects.all())
    if not bu_candidates:
        logger.error("❌ No se encontraron BusinessUnits en la base de datos")
        return None
    scores = {bu.name: 0 for bu in bu_candidates}

    # Seniority scoring (optimized to avoid redundant checks)
    seniority_score = 0
    for keyword, score in SENIORITY_KEYWORDS.items():
        if keyword in job_title_lower:
            seniority_score = max(seniority_score, score)
            break  # Early exit if a high score is found

    # Industry scoring (single pass through keywords)
    industry_scores = {ind: 0 for ind in INDUSTRY_KEYWORDS}
    for ind, keywords in INDUSTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in job_title_lower or keyword in job_desc_lower:
                industry_scores[ind] += 1
    dominant_industry = max(industry_scores, key=industry_scores.get) if max(industry_scores.values()) > 0 else None

    # Dynamic scoring with weights
    for bu in bu_candidates:
        weighting = WeightingModel(bu)
        # Determine position level dynamically based on seniority
        position_level = (
            "alta_direccion" if seniority_score >= 5 else
            "gerencia_media" if seniority_score >= 3 else
            "operativo" if seniority_score >= 1 else
            "entry_level"
        )
        weights = weighting.get_weights(position_level)  # No await needed; sync method

        # Keyword scoring
        for keyword, weight in BUSINESS_UNITS_KEYWORDS.get(bu.name, {}).items():
            if keyword in job_title_lower or (job_desc_lower and keyword in job_desc_lower):
                scores[bu.name] += weight * weights["hard_skills"]

        # Seniority adjustments
        if seniority_score >= 5:  # Very senior roles
            if bu.name == 'huntRED® Executive':
                scores[bu.name] += 4 * weights["personalidad"]
            elif bu.name == 'huntRED®':
                scores[bu.name] += 2 * weights["soft_skills"]
        elif seniority_score >= 3:  # Mid-to-senior roles
            if bu.name == 'huntRED®':
                scores[bu.name] += 3 * weights["soft_skills"]
            elif bu.name == 'huntu':
                scores[bu.name] += 1 * weights["hard_skills"]
        elif seniority_score >= 1:  # Junior-to-mid roles
            if bu.name == 'huntu':
                scores[bu.name] += 2 * weights["hard_skills"]
            elif bu.name == 'amigro':
                scores[bu.name] += 1 * weights["ubicacion"]
        else:  # Entry-level or operational roles
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
        if job_desc_lower:
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
                salary = salary_range.replace(',', '').replace('$', '').replace('k', '000')
                if '-' in salary:
                    min_salary, max_salary = map(float, salary.split('-'))
                elif salary.isdigit():
                    min_salary = max_salary = float(salary)
                else:
                    min_salary = max_salary = 0
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
        if required_experience:
            try:
                exp_years = float(required_experience) if required_experience.isdigit() else 0
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
                logger.warning(f"⚠️ No se pudo parsear experiencia: {required_experience}")

        # Location adjustments
        if location_lower:
            if any(term in location_lower for term in ['usa', 'europe', 'asia', 'mexico', 'latam', 'frontera', 'migración']):
                if bu.name == 'amigro':
                    scores[bu.name] += 3 * weights["ubicacion"]
            if any(term in location_lower for term in ['silicon valley', 'new york', 'london']):
                if bu.name == 'huntRED® Executive':
                    scores[bu.name] += 2 * weights["personalidad"]
                elif bu.name == 'huntu':
                    scores[bu.name] += 1 * weights["hard_skills"]

    # Select the business unit with the highest score
    max_score = max(scores.values(), default=0)
    if max_score == 0:
        chosen_bu = 'huntRED®'  # Fallback if no scoring applies
    else:
        candidates = [bu for bu, score in scores.items() if score == max_score]
        priority_order = ['huntRED® Executive', 'huntRED®', 'huntu', 'amigro']
        chosen_bu = next((bu for bu in priority_order if bu in candidates), candidates[0])

    # Fetch the chosen business unit ID
    try:
        bu_obj = await sync_to_async(BusinessUnit.objects.get)(name=chosen_bu)
        logger.info(f"✅ Unidad de negocio asignada: {chosen_bu} (ID: {bu_obj.id}) para '{job_title}'")
        return bu_obj.id
    except BusinessUnit.DoesNotExist:
        logger.warning(f"⚠️ Unidad de negocio '{chosen_bu}' no encontrada, usando huntRED®")
        bu_obj, created = await sync_to_async(BusinessUnit.objects.get_or_create)(
            name='huntRED®', defaults={'name': 'huntRED®'}
        )
        logger.info(f"🔧 Asignada huntRED® por defecto (ID: {bu_obj.id}) para '{job_title}'")
        return bu_obj.id

# Synchronous wrapper
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
async def save_vacantes(jobs: List[Dict], dominio):
    """Guarda las vacantes en la base de datos."""
    from app.models import DominioScraping, RegistroScraping, Vacante  # Importación local
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
    return nlp_processor.extract_skills(ChatbotUtils.clean_text(text))

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

async def get_scraper(domain, ml_scraper: MLScraper):
    """Obtiene el scraper adecuado para un dominio."""
    from app.models import DominioScraping  # Importación local
    scraper_class = SCRAPER_MAP.get(domain.plataforma, SCRAPER_MAP["default"])
    if domain.mapeo_configuracion:
        selectors = domain.mapeo_configuracion.get("selectors", PLATFORM_SELECTORS.get(domain.plataforma, {}))
    else:
        selectors = await ml_scraper.identify_selectors(domain.dominio, domain.plataforma)
        if not selectors:
            selectors = PLATFORM_SELECTORS.get(domain.plataforma, {})
    return scraper_class(domain, ml_scraper, custom_selectors=selectors)

class RateLimiter:
    """Manejador de rate limiting por dominio."""
    def __init__(self):
        self.limits = {
            'linkedin': {'requests': 20, 'period': 60},  # 20 requests por minuto
            'indeed': {'requests': 30, 'period': 60},    # 30 requests por minuto
            'workday': {'requests': 15, 'period': 60},   # 15 requests por minuto
            'default': {'requests': 25, 'period': 60}    # 25 requests por minuto
        }
        self.request_timestamps = {}
        self.lock = asyncio.Lock()

    async def acquire(self, domain: str) -> None:
        """Adquiere un permiso para hacer una petición."""
        async with self.lock:
            domain_key = domain.split('.')[0]  # Extraer el dominio base
            limit = self.limits.get(domain_key, self.limits['default'])
            
            if domain not in self.request_timestamps:
                self.request_timestamps[domain] = []
            
            now = time.time()
            # Limpiar timestamps antiguos
            self.request_timestamps[domain] = [ts for ts in self.request_timestamps[domain] 
                                             if now - ts < limit['period']]
            
            if len(self.request_timestamps[domain]) >= limit['requests']:
                # Calcular tiempo de espera
                oldest_timestamp = self.request_timestamps[domain][0]
                wait_time = limit['period'] - (now - oldest_timestamp)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Limpiar timestamps después de esperar
                    self.request_timestamps[domain] = [ts for ts in self.request_timestamps[domain] 
                                                     if now - ts < limit['period']]
            
            self.request_timestamps[domain].append(now)

class ErrorHandler:
    """Manejador de errores para el scraping."""
    def __init__(self):
        self.error_counts = {}
        self.error_thresholds = {
            'connection_error': 5,
            'parsing_error': 3,
            'rate_limit_error': 2,
            'timeout_error': 4
        }
        self.recovery_strategies = {
            'connection_error': self._handle_connection_error,
            'parsing_error': self._handle_parsing_error,
            'rate_limit_error': self._handle_rate_limit_error,
            'timeout_error': self._handle_timeout_error
        }

    async def handle_error(self, error: Exception, domain: str) -> bool:
        """Maneja un error y determina si se debe continuar o detener."""
        error_type = self._classify_error(error)
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        if self.error_counts[error_type] >= self.error_thresholds.get(error_type, 3):
            logger.error(f"Demasiados errores de tipo {error_type} para {domain}. Deteniendo scraping.")
            return False
            
        recovery_strategy = self.recovery_strategies.get(error_type)
        if recovery_strategy:
            await recovery_strategy(domain)
        return True

    def _classify_error(self, error: Exception) -> str:
        """Clasifica el tipo de error."""
        if isinstance(error, (aiohttp.ClientError, ConnectionError)):
            return 'connection_error'
        elif isinstance(error, (BeautifulSoup.ParserError, json.JSONDecodeError)):
            return 'parsing_error'
        elif isinstance(error, asyncio.TimeoutError):
            return 'timeout_error'
        elif 'rate limit' in str(error).lower():
            return 'rate_limit_error'
        return 'unknown_error'

    async def _handle_connection_error(self, domain: str):
        """Maneja errores de conexión."""
        await asyncio.sleep(random.uniform(5, 10))
        logger.info(f"Reintentando conexión a {domain} después de error")

    async def _handle_parsing_error(self, domain: str):
        """Maneja errores de parsing."""
        logger.warning(f"Error de parsing en {domain}, intentando método alternativo")
        await asyncio.sleep(1)

    async def _handle_rate_limit_error(self, domain: str):
        """Maneja errores de rate limiting."""
        wait_time = random.uniform(30, 60)
        logger.warning(f"Rate limit alcanzado para {domain}, esperando {wait_time:.2f} segundos")
        await asyncio.sleep(wait_time)

    async def _handle_timeout_error(self, domain: str):
        """Maneja errores de timeout."""
        await asyncio.sleep(random.uniform(2, 5))
        logger.info(f"Reintentando después de timeout en {domain}")

class ProxyRotator:
    """Sistema de rotación de proxies para evitar bloqueos."""
    def __init__(self, proxies: Optional[List[str]] = None):
        self.proxies = proxies or []
        self.index = 0
        self.last_used = {}
        self.failed_proxies = set()
        self.lock = asyncio.Lock()

    async def get_proxy(self) -> Optional[str]:
        """Obtiene el siguiente proxy disponible."""
        async with self.lock:
            if not self.proxies:
                return None

            # Limpiar proxies fallidos después de 1 hora
            now = time.time()
            self.failed_proxies = {
                proxy for proxy, last_fail in self.last_used.items()
                if now - last_fail < 3600
            }

            available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
            if not available_proxies:
                logger.warning("No hay proxies disponibles, usando conexión directa")
                return None

            proxy = available_proxies[self.index]
            self.index = (self.index + 1) % len(available_proxies)
            return proxy

    async def mark_failed(self, proxy: str):
        """Marca un proxy como fallido."""
        async with self.lock:
            self.failed_proxies.add(proxy)
            self.last_used[proxy] = time.time()

class BaseScraper:
    """Clase base para scrapers con funcionalidades comunes."""
    
    def __init__(self, domain: DominioScraping, use_playwright: bool = True):
        self.domain = domain
        self.use_playwright = use_playwright
        self.user_agent_rotator = UserAgentRotator()
        self._browser = None
        self._context = None
        self._page = None
        self._lock = asyncio.Lock()
        self._metrics = ScrapingMetrics()
        self._health_monitor = SystemHealthMonitor()
        self._cache = ScrapingCache()
        
    async def __aenter__(self):
        """Context manager entry."""
        if self.use_playwright:
            await self.initialize_playwright()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.cleanup()
        
    async def initialize_playwright(self):
        """Inicializa Playwright de manera optimizada."""
        if not self._browser:
            async with self._lock:
                if not self._browser:  # Double-check pattern
                    self._playwright = await async_playwright().start()
                    self._browser = await self._playwright.chromium.launch(
                        headless=True,
                        args=[
                            '--disable-gpu',
                            '--disable-dev-shm-usage',
                            '--disable-setuid-sandbox',
                            '--no-sandbox',
                            '--disable-web-security',
                            '--disable-features=IsolateOrigins,site-per-process',
                        ]
                    )
                    
    async def cleanup(self):
        """Limpieza de recursos."""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if hasattr(self, '_playwright'):
            await self._playwright.stop()
            
    async def fetch_content(self, url: str, method: str = "GET", data: dict = None) -> str:
        """
        Obtiene contenido de una URL usando Playwright o requests.
        
        Args:
            url: URL a obtener
            method: Método HTTP
            data: Datos para POST/PUT
            
        Returns:
            str: Contenido de la página
        """
        cache_key = f"content_{url}_{method}_{hash(str(data))}"
        cached_content = await self._cache.get(cache_key)
        if cached_content:
            return cached_content
            
        try:
            if self.use_playwright:
                return await self._fetch_with_playwright(url, method, data)
            else:
                return await self._fetch_with_requests(url, method, data)
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
            
    async def _fetch_with_playwright(self, url: str, method: str, data: dict) -> str:
        """Obtiene contenido usando Playwright."""
        if not self._context:
            self._context = await inicializar_contexto_playwright(self.domain, self._browser)
            
        if not self._page:
            self._page = await self._context.new_page()
            
        # Configurar headers y user agent
        headers = await self.user_agent_rotator.get_headers(
            device_type='desktop',
            browser='chrome'
        )
        await self._page.set_extra_http_headers(headers)
        
        # Configurar timeout y otras opciones
        await self._page.set_default_timeout(30000)
        await self._page.set_default_navigation_timeout(30000)
        
        try:
            if method == "GET":
                await self._page.goto(url, wait_until="networkidle")
            else:
                await self._page.goto(url)
                if data:
                    await self._page.fill('form', data)
                    await self._page.click('button[type="submit"]')
                    
            # Simular comportamiento humano
            await PlaywrightAntiDeteccion.simular_comportamiento_humano(self._page)
            
            # Obtener contenido
            content = await self._page.content()
            
            # Guardar en caché
            await self._cache.set(f"content_{url}_{method}_{hash(str(data))}", content)
            
            return content
            
        except Exception as e:
            logger.error(f"Error en Playwright para {url}: {e}")
            raise
            
    async def _fetch_with_requests(self, url: str, method: str, data: dict) -> str:
        """Obtiene contenido usando requests."""
        headers = await self.user_agent_rotator.get_headers(
            device_type='desktop',
            browser='chrome'
        )
        
        async with aiohttp.ClientSession() as session:
            try:
                if method == "GET":
                    async with session.get(url, headers=headers) as response:
                        response.raise_for_status()
                        content = await response.text()
                else:
                    async with session.request(method, url, json=data, headers=headers) as response:
                        response.raise_for_status()
                        content = await response.text()
                        
                # Guardar en caché
                await self._cache.set(f"content_{url}_{method}_{hash(str(data))}", content)
                
                return content
                
            except Exception as e:
                logger.error(f"Error en requests para {url}: {e}")
                raise
                
    async def extract_data(self, content: str) -> dict:
        """
        Extrae datos del contenido HTML.
        Debe ser implementado por las clases hijas.
        """
        raise NotImplementedError("Las clases hijas deben implementar extract_data")
        
    async def process_url(self, url: str) -> dict:
        """
        Procesa una URL completa: obtiene contenido y extrae datos.
        """
        with self._metrics.scraping_duration.time():
            try:
                content = await self.fetch_content(url)
                data = await self.extract_data(content)
                self._metrics.jobs_scraped.inc()
                return data
            except Exception as e:
                self._metrics.errors_total.inc()
                logger.error(f"Error procesando {url}: {e}")
                raise
                
    async def process_batch(self, urls: List[str], batch_size: int = 5) -> List[dict]:
        """
        Procesa un lote de URLs de manera eficiente.
        """
        results = []
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            tasks = [self.process_url(url) for url in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error en batch: {result}")
                else:
                    results.append(result)
                    
            # Verificar salud del sistema
            health = await self._health_monitor.check_health(
                processed=len(results),
                errors=sum(1 for r in results if isinstance(r, Exception))
            )
            
            if health.get('run_gc'):
                gc.collect()
            if health.get('reduce_batch'):
                batch_size = max(1, batch_size - 1)
            if health.get('increase_delay'):
                await asyncio.sleep(self._health_monitor.retry_delay)
                
        return results

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
    "cornerstone": CornerstoneScraper,
    "ukg": UKGScraper,
    "glassdoor": GlassdoorScraper,
    "computrabajo": ComputrabajoScraper,
    "flexible": FlexibleScraper,
    "default": BaseScraper,
}

# Funciones de publicación y ejecución
async def publish_to_internal_system(jobs: List[Dict], business_unit) -> bool:
    """Publica los trabajos en el sistema interno."""
    from app.models import BusinessUnit  # Importación local
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

async def scrape_and_publish(domains: List) -> None:
    """Ejecuta el scraping y publicación para una lista de dominios."""
    from app.models import DominioScraping  # Importación local
    pipeline = ScrapingPipeline()
    tasks = []
    for domain in domains:
        registro = await sync_to_async(RegistroScraping.objects.create)(dominio=domain, estado='parcial')
        scraper = await get_scraper(domain, pipeline.ml_scraper)
        tasks.append(process_domain(scraper, domain, registro, pipeline))
    results = await asyncio.gather(*tasks)
    jobs_by_bu = {}
    for domain, jobs in results:
        if jobs:
            bu_name = jobs[0]["business_unit"]
            jobs_by_bu.setdefault(bu_name, []).extend(jobs)
    for bu_name, jobs in jobs_by_bu.items():
        bu = await sync_to_async(BusinessUnit.objects.get)(name=bu_name)
        await publish_to_internal_system(jobs, bu)

async def process_domain(scraper, domain, registro, pipeline: ScrapingPipeline) -> tuple:
    """Procesa un dominio específico."""
    from app.models import DominioScraping, RegistroScraping  # Importación local
    try:
        async with asyncio.timeout(3600):
            async with scraper:
                with scraper.metrics.scraping_duration.time():
                    raw_jobs = await scraper.scrape()
                    processed_jobs = await pipeline.process([vars(job) for job in raw_jobs])
                    await save_vacantes(processed_jobs, domain)
                    registro.vacantes_encontradas = len(processed_jobs)
                    registro.estado = 'exitoso'
                    await pipeline.ml_scraper.save_training_data(domain, processed_jobs, "success")
                    return domain, processed_jobs
    except Exception as e:
        registro.estado = 'fallido'
        registro.error_log = str(e)
        logger.error(f"Scraping failed for {domain.dominio}: {e}")
        scraper.metrics.errors_total.inc()
        await pipeline.ml_scraper.save_training_data(domain, [], "failed", str(e))
        bu = await sync_to_async(BusinessUnit.objects.filter)(scraping_domains=domain).first()
        if bu and bu.admin_email:
            from app.ats.integrations.services import send_email
            await send_email(
                business_unit_name=bu.name,
                subject=f"Scraping Error for {domain.dominio}",
                body=f"Error: {str(e)}\nDetails: {registro.error_log}",
                from_email="noreply@huntred.com",
            )
    finally:
        registro.fecha_fin = now()
        await sync_to_async(registro.save)()
        return domain, []

@shared_task
async def run_all_scrapers() -> None:
    """Ejecuta todos los scrapers configurados."""
    from app.models import DominioScraping  # Importación local
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

class JobScraper:
    """Enhanced job scraper using playwright for dynamic content and robust error handling."""

    def __init__(self, domains=None, max_depth=2, max_pages=10, concurrency=3):
        self.domains = domains or []
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.concurrency = concurrency
        self.visited_urls = set()
        self.scraped_data = []
        self.session = None
        logger.info("JobScraper initialized")

    async def initialize(self):
        """Initialize the playwright browser session."""
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            self.session = browser
            logger.info("Playwright browser session initialized")
            return self.session
        except Exception as e:
            logger.error(f"Error initializing playwright session: {str(e)}", exc_info=True)
            raise

    async def scrape_page(self, page, url, depth=0):
        """Scrape a single page for job listings with error handling."""
        try:
            logger.info(f"Scraping URL: {url} at depth {depth}")
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle")
            
            content = await page.content()
            job_info = parse_job_listing(content, url, source_type="web")
            if job_info:
                self.scraped_data.append(job_info)
                logger.info(f"Found job: {job_info['title']} at {job_info['company']}")
            
            if depth < self.max_depth:
                soup = BeautifulSoup(content, "html.parser")
                links = soup.find_all("a", href=True)
                tasks = []
                for link in links:
                    next_url = urljoin(url, link["href"])
                    if next_url not in self.visited_urls and any(domain in next_url for domain in self.domains):
                        self.visited_urls.add(next_url)
                        tasks.append(self.scrape_page(page, next_url, depth + 1))
                        if len(tasks) >= self.max_pages:
                            break
                await asyncio.gather(*tasks[:self.concurrency])
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}", exc_info=True)

    async def scrape(self):
        """Main scraping method with batch processing and robust error handling."""
        try:
            await self.initialize()
            context = await self.session.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()
            
            tasks = []
            for domain in self.domains:
                start_url = f"https://{domain}/jobs" if not domain.startswith("http") else f"{domain}/jobs"
                tasks.append(self.scrape_page(page, start_url))
                if len(tasks) >= self.concurrency:
                    await asyncio.gather(*tasks)
                    tasks = []
            
            if tasks:
                await asyncio.gather(*tasks)
            
            await context.close()
            await self.session.close()
            logger.info(f"Scraping completed. Found {len(self.scraped_data)} job listings.")
            return self.scraped_data
        except Exception as e:
            logger.error(f"Error in scrape: {str(e)}", exc_info=True)
            raise
        finally:
            if self.session:
                await self.session.close()
                logger.info("Browser session closed")

    async def save_to_vacante(self, bu):
        """Save scraped job data to Vacante model with async operation."""
        try:
            for job_info in self.scraped_data:
                await save_job_to_vacante(job_info, bu)
        except Exception as e:
            logger.error(f"Error saving scraped vacante: {str(e)}", exc_info=True)

class JobAnalyzer:
    """Analizador avanzado de vacantes."""
    def __init__(self):
        self.salary_patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:MXN|USD)?',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|K)?',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:mil|millones)?'
        ]
        self.experience_patterns = [
            r'(\d+)\s*(?:años|years|yr|yrs)',
            r'(\d+)\s*(?:meses|months)',
            r'(\d+)\s*(?:días|days)'
        ]
        self.education_patterns = [
            r'(licenciatura|ingeniería|maestría|doctorado|bachelor|master|phd)',
            r'(universidad|college|instituto)',
            r'(certificación|certification)'
        ]

    async def analyze_job(self, job: JobListing) -> Dict:
        """Realiza un análisis completo de la vacante."""
        analysis = {
            'salary': await self.analyze_salary(job.description),
            'experience': await self.analyze_experience(job.description),
            'education': await self.analyze_education(job.description),
            'sentiment': await self.analyze_sentiment(job.description),
            'complexity': await self.analyze_complexity(job.description),
            'keywords': await self.extract_keywords(job.description)
        }
        return analysis

    async def analyze_salary(self, text: str) -> Optional[Dict]:
        """Analiza el rango salarial en el texto."""
        if not text:
            return None

        for pattern in self.salary_patterns:
            matches = re.findall(pattern, text)
            if len(matches) >= 2:
                try:
                    min_salary = float(matches[0].replace(',', ''))
                    max_salary = float(matches[-1].replace(',', ''))
                    return {
                        'min': min_salary,
                        'max': max_salary,
                        'currency': 'MXN' if 'MXN' in text else 'USD'
                    }
                except ValueError:
                    continue
        return None

    async def analyze_experience(self, text: str) -> Optional[Dict]:
        """Analiza los requisitos de experiencia."""
        if not text:
            return None

        experience = {}
        for pattern in self.experience_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    years = float(matches[0])
                    experience['years'] = years
                    experience['unit'] = 'years' if 'años' in pattern or 'years' in pattern else 'months'
                    break
                except ValueError:
                    continue
        return experience

    async def analyze_education(self, text: str) -> List[str]:
        """Analiza los requisitos educativos."""
        if not text:
            return []

        education = []
        for pattern in self.education_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            education.extend(matches)
        return list(set(education))

    async def analyze_sentiment(self, text: str) -> Dict:
        """Analiza el sentimiento del texto."""
        if not text:
            return {'score': 0, 'label': 'neutral'}

        # Implementación básica - podrías usar una librería más sofisticada
        positive_words = {'excelente', 'bueno', 'gran', 'óptimo', 'perfecto', 'ideal'}
        negative_words = {'difícil', 'complejo', 'desafiante', 'estresante', 'exigente'}

        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        total = len(words)

        if total == 0:
            return {'score': 0, 'label': 'neutral'}

        score = (positive_count - negative_count) / total
        label = 'positive' if score > 0.1 else 'negative' if score < -0.1 else 'neutral'

        return {'score': score, 'label': label}

    async def analyze_complexity(self, text: str) -> Dict:
        """Analiza la complejidad del trabajo."""
        if not text:
            return {'level': 'unknown', 'score': 0}

        # Métricas de complejidad
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+', text))
        avg_word_length = sum(len(word) for word in text.split()) / word_count if word_count > 0 else 0

        # Calcular score de complejidad
        complexity_score = (word_count * 0.3 + sentence_count * 0.3 + avg_word_length * 0.4) / 10

        # Determinar nivel
        if complexity_score > 7:
            level = 'high'
        elif complexity_score > 4:
            level = 'medium'
        else:
            level = 'low'

        return {'level': level, 'score': complexity_score}

    async def extract_keywords(self, text: str) -> List[str]:
        """Extrae palabras clave relevantes del texto."""
        if not text:
            return []

        # Eliminar palabras comunes
        stop_words = {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'en', 'de', 'con'}
        words = text.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 3]

        # Contar frecuencia
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Ordenar por frecuencia
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:10]]

class ScrapingMonitor:
    """Sistema de monitoreo y alertas para el scraping."""
    def __init__(self):
        self.error_counts = {}
        self.success_counts = {}
        self.last_notification = {}
        self.notification_cooldown = 3600  # 1 hora

    async def record_error(self, domain: str, error: str):
        """Registra un error y envía notificación si es necesario."""
        if domain not in self.error_counts:
            self.error_counts[domain] = {}
        
        if error not in self.error_counts[domain]:
            self.error_counts[domain][error] = 0
        
        self.error_counts[domain][error] += 1
        
        # Verificar si debemos enviar notificación
        if self._should_notify(domain, error):
            await self._send_notification(domain, error)

    async def record_success(self, domain: str):
        """Registra un scraping exitoso."""
        if domain not in self.success_counts:
            self.success_counts[domain] = 0
        self.success_counts[domain] += 1

    def _should_notify(self, domain: str, error: str) -> bool:
        """Determina si se debe enviar una notificación."""
        now = time.time()
        last_notif = self.last_notification.get((domain, error), 0)
        
        if now - last_notif < self.notification_cooldown:
            return False
            
        error_count = self.error_counts[domain].get(error, 0)
        return error_count >= 3  # Notificar después de 3 errores

    async def _send_notification(self, domain: str, error: str):
        """Envía una notificación sobre el error."""
        from app.ats.integrations.services import send_email
        
        subject = f"⚠️ Error de Scraping: {domain}"
        body = f"""
        Se han detectado múltiples errores en el scraping de {domain}:
        
        Error: {error}
        Conteo: {self.error_counts[domain][error]}
        Último éxito: {self.success_counts.get(domain, 0)}
        
        Por favor, revisar la configuración y el estado del dominio.
        """
        
        try:
            await send_email(
                subject=subject,
                body=body,
                to_email="admin@huntred.com"
            )
            self.last_notification[(domain, error)] = time.time()
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")

# Modificar BaseScraper para usar JobAnalyzer y ScrapingMonitor
class BaseScraper:
    def __init__(self, domain: DominioScraping, ml_scraper: MLScraper, custom_selectors: Optional[Dict] = None):
        self.domain = domain
        self.ml_scraper = ml_scraper
        self.selectors = custom_selectors or {}
        self.metrics = ScrapingMetrics(registry_name=f"scraper_{domain.plataforma}")
        self.cache = ScrapingCache(max_size=2000, ttl=7200)
        self.health_monitor = SystemHealthMonitor()
        self.delay = random.uniform(1, 3)
        self.response_type = "html"
        self.max_retries = 3
        self.timeout = 30
        self.rate_limiter = RateLimiter()
        self.error_handler = ErrorHandler()
        self.proxy_rotator = ProxyRotator()
        self.job_analyzer = JobAnalyzer()
        self.monitor = ScrapingMonitor()
        self.user_agent_rotator = UserAgentRotator()

    async def _process_page_content(self, content: str, seen_urls: set) -> List[JobListing]:
        """Procesa el contenido de una página y extrae las vacantes."""
        if self.response_type == "json":
            return await self._parse_json(content, seen_urls)
        
        soup = BeautifulSoup(content, "html.parser")
        job_cards = soup.select(self.selectors.get("job_cards", "div.job-card"))
        vacantes = []
        tasks = []

        for card in job_cards:
            url_elem = extract_field(str(card), [self.selectors["url"]], "href")
            link = url_elem if url_elem and url_elem.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{url_elem or ''}"
            
            if link not in seen_urls:
                seen_urls.add(link)
                tasks.append(self.get_job_details(link))

        details_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for idx, detail in enumerate(details_list):
            if isinstance(detail, Exception):
                logger.error(f"Error getting job details: {detail}")
                await self.monitor.record_error(self.domain.dominio, str(detail))
                continue
                
            if detail:
                job = JobListing(
                    title=extract_field(str(job_cards[idx]), [self.selectors["title"]]) or "No especificado",
                    url=link,
                    location=detail.get("location", "Unknown"),
                    company=detail.get("company", "Unknown"),
                    description=detail.get("description", "No disponible"),
                    skills=detail.get("skills", []),
                    posted_date=detail.get("posted_date"),
                )
                
                # Analizar la vacante
                analysis = await self.job_analyzer.analyze_job(job)
                job.salary = analysis['salary']
                job.sentiment = analysis['sentiment']
                job.complexity = analysis['complexity']
                job.keywords = analysis['keywords']
                
                vacantes.append(job)
                await self.monitor.record_success(self.domain.dominio)

        return vacantes
