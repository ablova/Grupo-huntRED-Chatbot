# /home/pablo/app/utilidades/scraping.py
import json
import random
import asyncio
import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging
from celery import shared_task
from asgiref.sync import sync_to_async
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
import trafilatura
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from app.chatbot.utils import clean_text
from app.utilidades.loader import DIVISION_SKILLS
from app.chatbot.gpt import GPTHandler
from app.chatbot.nlp import NLPProcessor
from app.utilidades.vacantes import VacanteManager
from app.utilidades.scraping_utils import ScrapingMetrics, SystemHealthMonitor, ScrapingCache, inicializar_contexto_playwright, visitar_pagina_humanizada, extraer_y_guardar_cookies
from app.ml.utils.scrape import MLScraper

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

class BaseScraper:
    def __init__(self, domain: DominioScraping, ml_scraper: MLScraper, custom_selectors: Optional[Dict] = None):
        self.domain = domain
        self.plataforma = domain.plataforma
        self.selectors = custom_selectors or PLATFORM_SELECTORS.get(self.plataforma, {})
        self.response_type = "json" if self.plataforma in ["eightfold_ai", "oracle_hcm"] else "html"
        self.semaphore = asyncio.Semaphore(max(1, int(psutil.cpu_count() * 0.5)))
        self.delay = domain.frecuencia_scraping / 3600
        self.session = None
        self.cookies = domain.cookies or {}
        self.ml_scraper = ml_scraper
        self.metrics = ScrapingMetrics("web_scraper")
        self.health_monitor = SystemHealthMonitor()

    async def __aenter__(self):
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        self.session = ClientSession(headers=headers, timeout=ClientTimeout(total=30), cookies=self.cookies)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def refresh_cookies(self, url: str) -> Dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle")
            cookies = await context.cookies()
            await browser.close()
            return {cookie["name"]: cookie["value"] for cookie in cookies}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), 
           before_sleep=before_sleep_log(logger, logging.WARNING))
    async def fetch(self, url: str, use_playwright: bool = False) -> Optional[str]:
        if use_playwright or self.plataforma in ["linkedin", "workday", "phenom_people", "indeed", "glassdoor"]:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    context = await inicializar_contexto_playwright(self.domain, browser)
                    page = await context.new_page()
                    await visitar_pagina_humanizada(page, url)
                    content = await page.content()
                    await extraer_y_guardar_cookies(self.domain, context)
                    return content
                finally:
                    await browser.close()
        else:
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status in [403, 401]:
                        self.cookies = await self.refresh_cookies(url)
                        async with self.session.get(url, cookies=self.cookies) as retry_response:
                            if retry_response.status == 200:
                                return await retry_response.text()
                            logger.warning(f"Error HTTP {retry_response.status} al obtener {url}")
                            return None
                    else:
                        logger.warning(f"Error HTTP {response.status} al obtener {url}")
                        return None
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                self.metrics.errors_total.inc()
                return None


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

    def _build_url(self, page: int) -> str:
        pagination = self.selectors.get("pagination", {"param": "page", "step": 1})
        param, step = pagination.get("param", "page"), pagination.get("step", 1)
        return f"{self.domain.dominio}?{param}={page * step}"

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
        
        platform = await self.ml_scraper.classify_page(url, content)
        details = await self.ml_scraper.extract_job_details(content, platform)
        details["url"] = url
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
class LinkedInScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        async with self:
            while True:
                url = f"{self.domain.dominio}&start={page * 25}"
                logger.info(f"Scrapeando página {page}: {url}")
                content = await self.fetch(url, use_playwright=True)
                if not content:
                    break
                soup = BeautifulSoup(content, "html.parser")
                job_cards = soup.select("a.base-card__full-link, li.jobs-search-results__list-item a")
                if not job_cards:
                    break
                tasks = []
                for card in job_cards:
                    link = card.get("href", "")
                    if link and link not in seen_urls:
                        seen_urls.add(link)
                        tasks.append(self.get_job_details(link))
                details_list = await asyncio.gather(*tasks)
                for detail in details_list:
                    if detail:
                        vacantes.append(JobListing(**detail))
                page += 1
        return vacantes
    
    async def fetch(self, url: str, use_playwright: bool = False) -> Optional[str]:
        if use_playwright or self.plataforma in ["linkedin", "workday", "phenom_people"]:
            for attempt in range(MAX_RETRIES):
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    try:
                        context = await browser.new_context(
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
                            viewport={"width": 1280, "height": 720}
                        )
                        page = await context.new_page()
                        if self.cookies:
                            await page.context.add_cookies([
                                {"name": k, "value": v, "domain": "linkedin.com", "path": "/"}
                                for k, v in self.cookies.items()
                            ])
                        normalized_url = url.replace("/comm/jobs/", "/jobs/")
                        await page.goto(normalized_url, wait_until="networkidle", timeout=90000)
                        # Check for authentication prompt
                        login_prompt = await page.query_selector("input#session_key, input#username")
                        if login_prompt:
                            logger.warning(f"Authentication prompt detected for {url}, skipping")
                            return None
                        await page.wait_for_selector("h1, h2, div.jobs-unified-top-card", timeout=20000)
                        content = await page.content()
                        logger.debug(f"Successfully fetched content for {url} (attempt {attempt + 1})")
                        return content
                    except PlaywrightTimeoutError as e:
                        logger.warning(f"Playwright timeout for {url} (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                        if attempt < MAX_RETRIES - 1:
                            await asyncio.sleep(RETRY_DELAY)
                    except Exception as e:
                        logger.error(f"Playwright failed for {url} (attempt {attempt + 1}/{MAX_RETRIES}): {e}", exc_info=True)
                        return None
                    finally:
                        await browser.close()
            logger.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts")
            return None

    async def get_job_details(self, url: str) -> Dict:
        try:
            content = await self.fetch(url, use_playwright=True)
            if not content:
                raise Exception("No se pudo obtener el contenido")
            soup = BeautifulSoup(content, "html.parser")
            title = soup.select_one("h1.topcard__title")
            description = soup.select_one("div.description__text")
            location = soup.select_one("span.topcard__flavor--bullet")
            company = soup.select_one("a.topcard__org-name-link")
            return {
                "title": title.get_text(strip=True) if title else "No especificado",
                "description": description.get_text(strip=True) if description else "No disponible",
                "location": location.get_text(strip=True) if location else "Unknown",
                "company": company.get_text(strip=True) if company else "Unknown",
                "skills": extract_skills(content),
                "url": url
            }
        except Exception as e:
            logger.warning(f"Fallo en lógica personalizada para LinkedIn: {e}. Usando ML como respaldo.")
            return await super().get_job_details(url)
        
class WorkdayScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        base_url = self.domain.dominio.rsplit('/', 1)[0]
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
                if detail:
                    vacantes.append(JobListing(**detail))
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        try:
            content = await self.fetch(url, use_playwright=True)
            if not content:
                raise Exception("No se pudo obtener el contenido")
            soup = BeautifulSoup(content, "html.parser")
            title_elem = soup.select_one('h2[data-automation-id="jobTitle"]')
            desc_elem = soup.select_one('div[data-automation-id="jobPostingDescription"]')
            loc_elem = soup.select_one('div[data-automation-id="location"]')
            return {
                "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
                "description": desc_elem.get_text(strip=True) if desc_elem else "No disponible",
                "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
                "company": "Workday Employer",  # Ajustar según dominio si es dinámico
                "skills": extract_skills(content),
                "url": url
            }
        except Exception as e:
            logger.warning(f"Fallo en lógica personalizada para Workday: {e}. Usando ML como respaldo.")
            return await super().get_job_details(url)

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
        try:
            content = await self.fetch(url, use_playwright=True)
            if not content:
                raise Exception("No se pudo obtener el contenido")
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
        except Exception as e:
            logger.warning(f"Fallo en lógica personalizada para PhenomPeople: {e}. Usando ML como respaldo.")
            return await super().get_job_details(url)

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
        try:
            content = await self.fetch(url)
            if not content:
                raise Exception("No se pudo obtener el contenido")
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
        except Exception as e:
            logger.warning(f"Fallo en lógica personalizada para Indeed: {e}. Usando ML como respaldo.")
            return await super().get_job_details(url)
    
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
        try:
            content = await self.fetch(url)
            if not content:
                raise Exception("No se pudo obtener el contenido")
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
        except Exception as e:
            logger.warning(f"Fallo en lógica personalizada para Greenhouse: {e}. Usando ML como respaldo.")
            return await super().get_job_details(url)
    
class AccentureScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        base_url = self.domain.dominio.rsplit('/', 1)[0]

        while True:
            url = f"{self.domain.dominio}?page={page}"
            content = await self.fetch(url, use_playwright=True)  # Usar Playwright para JS
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.select('div.cmp-teaser.card')
            if not job_cards:
                break

            tasks = []
            for card in job_cards:
                title = card.select_one('h3.cmp-teaser__title').get_text(strip=True)
                relative_url = card.select_one('a.cmp-teaser__title-link')['href']
                full_url = f"{base_url}{relative_url}" if relative_url.startswith('/') else relative_url
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    tasks.append(self.get_job_details(full_url))

            details_list = await asyncio.gather(*tasks)
            vacantes.extend([JobListing(**detail) for detail in details_list if detail])
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        try:
            content = await self.fetch(url, use_playwright=True)
            if not content:
                raise Exception("No se pudo obtener el contenido")
            soup = BeautifulSoup(content, "html.parser")
            title_elem = soup.select_one('h1.cmp-teaser__title') or soup.select_one('h1')
            desc_elem = soup.select_one('div.job-description') or soup.select_one('div.description')
            loc_elem = soup.select_one('div.cmp-teaser-region, div.cmp-teaser-city')
            return {
                "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
                "description": desc_elem.get_text(strip=True) if desc_elem else "No disponible",
                "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
                "company": "Accenture",
                "skills": extract_skills(content),
                "url": url
            }
        except Exception as e:
            logger.warning(f"Fallo en lógica personalizada para Accenture: {e}. Usando ML como respaldo.")
            return await super().get_job_details(url)
    
class ADPScraper(BaseScraper):
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
                            company=job.get("company", "ADP Employer")
                        ))
                page += 1
            except json.JSONDecodeError:
                break
        return vacantes
    
class PeopleSoftScraper(BaseScraper):
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
            job_cards = soup.select('div.job-card')
            if not job_cards:
                break
            tasks = []
            for card in job_cards:
                title = card.find('h3').get_text(strip=True) if card.find('h3') else "No especificado"
                url_elem = card.find('a', href=True)
                link = url_elem['href'] if url_elem else ""
                link = link if link.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{link}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    tasks.append(self.get_job_details(link))
            details_list = await asyncio.gather(*tasks)
            vacantes.extend([JobListing(**detail) for detail in details_list if detail])
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        try:
            content = await self.fetch(url)
            if not content:
                raise Exception("No se pudo obtener el contenido")
            soup = BeautifulSoup(content, "html.parser")
            title_elem = soup.select_one('h1') or soup.select_one('h2')
            desc_elem = soup.select_one('div.job-desc') or soup.select_one('div.description')
            loc_elem = soup.select_one('span.location') or soup.select_one('span.city')
            return {
                "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
                "description": desc_elem.get_text(strip=True) if desc_elem else "No disponible",
                "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
                "company": "PeopleSoft Employer",
                "skills": extract_skills(content),
                "url": url
            }
        except Exception as e:
            logger.warning(f"Fallo en lógica personalizada para PeopleSoft: {e}. Usando ML como respaldo.")
            return await super().get_job_details(url)
    
class GenericScraper(BaseScraper):  # Usar para Meta4, Cornerstone, UKG
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
            job_cards = soup.select('div.job-item')  # Ajustar selector
            if not job_cards:
                break
            tasks = []
            for card in job_cards:
                title = card.find('h3').get_text(strip=True) if card.find('h3') else "No especificado"
                url_elem = card.find('a', href=True)
                link = url_elem['href'] if url_elem else ""
                link = link if link.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{link}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    tasks.append(self.get_job_details(link))
            details_list = await asyncio.gather(*tasks)
            vacantes.extend([JobListing(**detail) for detail in details_list if detail])
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        content = await self.fetch(url)
        if not content:
            return {}
        soup = BeautifulSoup(content, "html.parser")
        title_elem = soup.select_one('h1') or soup.select_one('h2')
        desc_elem = soup.select_one('div.job-details') or soup.select_one('div.description')
        loc_elem = soup.select_one('span.location') or soup.select_one('span.city')
        return {
            "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
            "description": desc_elem.get_text(strip=True) if desc_elem else "No disponible",
            "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
            "company": self.__class__.__name__.replace("Scraper", " Employer"),
            "skills": self.extract_skills(content),
            "url": url
        }
    
class CornerstoneScraper(BaseScraper):
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
            job_cards = soup.select('div.job-item')  # Ajustar selector
            if not job_cards:
                break
            tasks = []
            for card in job_cards:
                title = card.find('h3').get_text(strip=True) if card.find('h3') else "No especificado"
                url_elem = card.find('a', href=True)
                link = url_elem['href'] if url_elem else ""
                link = link if link.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{link}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    tasks.append(self.get_job_details(link))
            details_list = await asyncio.gather(*tasks)
            vacantes.extend([JobListing(**detail) for detail in details_list if detail])
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        try:
            content = await self.fetch(url)
            if not content:
                raise Exception("No se pudo obtener el contenido")
            soup = BeautifulSoup(content, "html.parser")
            title_elem = soup.select_one('h1') or soup.select_one('h2')
            desc_elem = soup.select_one('div.job-details') or soup.select_one('div.description')
            loc_elem = soup.select_one('span.location') or soup.select_one('span.city')
            return {
                "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
                "description": desc_elem.get_text(strip=True) if desc_elem else "No disponible",
                "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
                "company": self.__class__.__name__.replace("Scraper", " Employer"),
                "skills": extract_skills(content),
                "url": url
            }
        except Exception as e:
            logger.warning(f"Fallo en lógica personalizada para Cornerstone: {e}. Usando ML como respaldo.")
            return await super().get_job_details(url)

class UKGScraper(BaseScraper):
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
            job_cards = soup.select('div.job-item')  # Ajustar selector
            if not job_cards:
                break
            tasks = []
            for card in job_cards:
                title = card.find('h3').get_text(strip=True) if card.find('h3') else "No especificado"
                url_elem = card.find('a', href=True)
                link = url_elem['href'] if url_elem else ""
                link = link if link.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{link}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    tasks.append(self.get_job_details(link))
            details_list = await asyncio.gather(*tasks)
            vacantes.extend([JobListing(**detail) for detail in details_list if detail])
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        try:
            content = await self.fetch(url)
            if not content:
                raise Exception("No se pudo obtener el contenido")
            soup = BeautifulSoup(content, "html.parser")
            title_elem = soup.select_one('h1') or soup.select_one('h2')
            desc_elem = soup.select_one('div.job-details') or soup.select_one('div.description')
            loc_elem = soup.select_one('span.location') or soup.select_one('span.city')
            return {
                "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
                "description": desc_elem.get_text(strip=True) if desc_elem else "No disponible",
                "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
                "company": self.__class__.__name__.replace("Scraper", " Employer"),
                "skills": extract_skills(content),
                "url": url
            }
        except Exception as e:
            logger.warning(f"Fallo en lógica personalizada para UKG: {e}. Usando ML como respaldo.")
            return await super().get_job_details(url)

class GlassdoorScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        while True:
            url = f"{self.domain.dominio}?page={page}"
            content = await self.fetch(url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.select('li.react-job-listing')
            if not job_cards:
                break
            tasks = []
            for card in job_cards:
                title = card.find('a', class_='jobLink').get_text(strip=True) if card.find('a', class_='jobLink') else "No especificado"
                url_elem = card.find('a', class_='jobLink', href=True)
                link = url_elem['href'] if url_elem else ""
                link = link if link.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{link}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    tasks.append(self.get_job_details(link))
            details_list = await asyncio.gather(*tasks)
            vacantes.extend([JobListing(**detail) for detail in details_list if detail])
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        try:
            content = await self.fetch(url)
            if not content:
                raise Exception("No se pudo obtener el contenido")
            soup = BeautifulSoup(content, "html.parser")
            title_elem = soup.select_one('h1') or soup.select_one('h2')
            desc_elem = soup.select_one('div.job-description') or soup.select_one('div.description')
            loc_elem = soup.select_one('span.jobLocation') or soup.select_one('span.location')
            return {
                "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
                "description": desc_elem.get_text(strip=True) if desc_elem else "No disponible",
                "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
                "company": "Glassdoor Employer",
                "skills": extract_skills(content),
                "url": url
            }
        except Exception as e:
            logger.warning(f"Fallo en lógica personalizada para Glassdoor: {e}. Usando ML como respaldo.")
            return await super().get_job_details(url)
    
class ComputrabajoScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        seen_urls = set()
        while True:
            url = f"{self.domain.dominio}?p={page}"
            content = await self.fetch(url)
            if not content:
                break
            soup = BeautifulSoup(content, "html.parser")
            job_cards = soup.select('article.box_border')
            if not job_cards:
                break
            tasks = []
            for card in job_cards:
                title = card.find('h1').get_text(strip=True) if card.find('h1') else "No especificado"
                url_elem = card.find('a', class_='js-o-link', href=True)
                link = url_elem['href'] if url_elem else ""
                link = link if link.startswith("http") else f"{self.domain.dominio.rsplit('/', 1)[0]}{link}"
                if link not in seen_urls:
                    seen_urls.add(link)
                    tasks.append(self.get_job_details(link))
            details_list = await asyncio.gather(*tasks)
            vacantes.extend([JobListing(**detail) for detail in details_list if detail])
            page += 1
        return vacantes

    async def get_job_details(self, url: str) -> Dict:
        try:
            content = await self.fetch(url)
            if not content:
                raise Exception("No se pudo obtener el contenido")
            soup = BeautifulSoup(content, "html.parser")
            title_elem = soup.select_one('h1') or soup.select_one('h2')
            desc_elem = soup.select_one('div.job-description') or soup.select_one('div.description')
            loc_elem = soup.select_one('span.location') or soup.select_one('span.city')
            return {
                "title": title_elem.get_text(strip=True) if title_elem else "No especificado",
                "description": desc_elem.get_text(strip=True) if desc_elem else "No disponible",
                "location": loc_elem.get_text(strip=True) if loc_elem else "Unknown",
                "company": "Computrabajo Employer",
                "skills": extract_skills(content),
                "url": url
            }
        except Exception as e:
            logger.warning(f"Fallo en lógica personalizada para Computrabajo: {e}. Usando ML como respaldo.")
            return await super().get_job_details(url)
    
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
            from app.chatbot.integrations.services import send_email
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
