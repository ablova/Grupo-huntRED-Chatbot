"""
HuntRED® v2 - Job Boards Scraper
Scraper completo para Indeed, Monster, OCC Mundial, CompuTrabajo
Parte del círculo virtuoso de scraping → ML → propuestas
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import re
import time
from urllib.parse import urljoin, urlparse, quote
import hashlib
from bs4 import BeautifulSoup
import random

logger = logging.getLogger(__name__)

class JobBoardPlatform(Enum):
    INDEED = "indeed"
    MONSTER = "monster"
    OCC_MUNDIAL = "occ_mundial"
    COMPUTRABAJO = "computrabajo"
    LINKEDIN = "linkedin"
    GLASSDOOR = "glassdoor"

@dataclass
class JobPosting:
    """Estructura de datos para ofertas de trabajo"""
    job_id: str
    title: str
    company: str
    location: str
    salary: Optional[str]
    description: str
    requirements: List[str]
    benefits: List[str]
    posted_date: datetime
    expires_date: Optional[datetime]
    job_type: str  # full-time, part-time, contract, etc.
    experience_level: str
    industry: str
    platform: JobBoardPlatform
    url: str
    scraped_at: datetime
    contact_info: Dict[str, Any]
    company_size: Optional[str]
    company_industry: Optional[str]
    skills_required: List[str]
    education_required: Optional[str]
    remote_work: bool
    confidence_score: float

@dataclass
class CompanyProfile:
    """Perfil de empresa extraído del scraping"""
    company_id: str
    name: str
    industry: str
    size: Optional[str]
    location: str
    website: Optional[str]
    description: str
    founded_year: Optional[int]
    employees_count: Optional[int]
    revenue_estimate: Optional[str]
    growth_indicators: List[str]
    contact_info: Dict[str, Any]
    social_media: Dict[str, str]
    job_postings_count: int
    hiring_trends: Dict[str, Any]
    scraped_at: datetime
    platform: JobBoardPlatform
    confidence_score: float

class JobBoardsScraper:
    """Scraper unificado para todas las plataformas de empleo"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
        self.rate_limits = {
            JobBoardPlatform.INDEED: {"requests_per_minute": 20, "delay": 3.0},
            JobBoardPlatform.MONSTER: {"requests_per_minute": 15, "delay": 4.0},
            JobBoardPlatform.OCC_MUNDIAL: {"requests_per_minute": 25, "delay": 2.5},
            JobBoardPlatform.COMPUTRABAJO: {"requests_per_minute": 30, "delay": 2.0},
            JobBoardPlatform.LINKEDIN: {"requests_per_minute": 10, "delay": 6.0},
            JobBoardPlatform.GLASSDOOR: {"requests_per_minute": 12, "delay": 5.0}
        }
        
        # Configuraciones específicas por plataforma
        self.platform_configs = {
            JobBoardPlatform.INDEED: {
                "base_url": "https://mx.indeed.com",
                "search_path": "/jobs",
                "job_detail_path": "/viewjob",
                "company_path": "/cmp",
                "selectors": {
                    "job_title": "[data-jk] .jobTitle a",
                    "company": ".companyName",
                    "location": ".companyLocation",
                    "salary": ".salary-snippet",
                    "description": ".jobsearch-jobDescriptionText",
                    "job_type": ".jobMetadataHeader-item",
                    "posted_date": ".date"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive"
                }
            },
            JobBoardPlatform.OCC_MUNDIAL: {
                "base_url": "https://www.occ.com.mx",
                "search_path": "/empleos",
                "job_detail_path": "/empleo",
                "company_path": "/empresa",
                "selectors": {
                    "job_title": ".job-title",
                    "company": ".company-name",
                    "location": ".location",
                    "salary": ".salary",
                    "description": ".job-description",
                    "requirements": ".requirements",
                    "benefits": ".benefits"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "es-MX,es;q=0.9",
                    "Referer": "https://www.occ.com.mx/"
                }
            },
            JobBoardPlatform.COMPUTRABAJO: {
                "base_url": "https://www.computrabajo.com.mx",
                "search_path": "/empleos",
                "job_detail_path": "/empleo-de-",
                "company_path": "/empresa",
                "selectors": {
                    "job_title": ".js-o-link",
                    "company": ".fc_base",
                    "location": ".dIB.mr5",
                    "salary": ".tag.base.mb10",
                    "description": ".mbB",
                    "posted_date": ".color_base.dIB.w_90"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8"
                }
            },
            JobBoardPlatform.MONSTER: {
                "base_url": "https://www.monster.com.mx",
                "search_path": "/empleos/buscar",
                "job_detail_path": "/empleo",
                "company_path": "/empresa",
                "selectors": {
                    "job_title": ".JobTitle",
                    "company": ".CompanyName",
                    "location": ".Location",
                    "salary": ".SalaryEstimate",
                    "description": ".JobDescription",
                    "job_type": ".JobType"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Accept-Language": "es-MX,es;q=0.9"
                }
            }
        }
    
    async def scrape_all_platforms(self, search_terms: List[str], 
                                 locations: List[str] = None,
                                 max_pages: int = 10) -> Dict[str, Any]:
        """Scraping completo de todas las plataformas"""
        
        if not locations:
            locations = ["Ciudad de México", "Guadalajara", "Monterrey", "Puebla", "Tijuana"]
        
        results = {
            "total_jobs": 0,
            "total_companies": 0,
            "platform_results": {},
            "top_companies": [],
            "trending_skills": [],
            "salary_insights": {},
            "market_trends": {},
            "scraping_metadata": {
                "start_time": datetime.now(),
                "search_terms": search_terms,
                "locations": locations,
                "platforms_scraped": []
            }
        }
        
        # Crear sesión HTTP
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            self.session = session
            
            # Scraping paralelo de todas las plataformas
            tasks = []
            for platform in JobBoardPlatform:
                if platform in self.platform_configs:
                    task = self._scrape_platform(platform, search_terms, locations, max_pages)
                    tasks.append(task)
            
            # Ejecutar en paralelo
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            for i, result in enumerate(platform_results):
                platform = list(JobBoardPlatform)[i]
                
                if isinstance(result, Exception):
                    logger.error(f"Error scraping {platform.value}: {result}")
                    continue
                
                if platform.value in [p.value for p in JobBoardPlatform]:
                    results["platform_results"][platform.value] = result
                    results["total_jobs"] += result.get("jobs_count", 0)
                    results["total_companies"] += result.get("companies_count", 0)
                    results["scraping_metadata"]["platforms_scraped"].append(platform.value)
        
        # Análisis consolidado
        results["top_companies"] = await self._analyze_top_companies(results["platform_results"])
        results["trending_skills"] = await self._analyze_trending_skills(results["platform_results"])
        results["salary_insights"] = await self._analyze_salary_trends(results["platform_results"])
        results["market_trends"] = await self._analyze_market_trends(results["platform_results"])
        
        results["scraping_metadata"]["end_time"] = datetime.now()
        results["scraping_metadata"]["total_duration"] = (
            results["scraping_metadata"]["end_time"] - 
            results["scraping_metadata"]["start_time"]
        ).total_seconds()
        
        logger.info(f"✅ Scraping completed: {results['total_jobs']} jobs, {results['total_companies']} companies")
        
        return results
    
    async def _scrape_platform(self, platform: JobBoardPlatform, 
                              search_terms: List[str], 
                              locations: List[str], 
                              max_pages: int) -> Dict[str, Any]:
        """Scraping específico por plataforma"""
        
        config = self.platform_configs[platform]
        rate_limit = self.rate_limits[platform]
        
        platform_results = {
            "platform": platform.value,
            "jobs": [],
            "companies": [],
            "jobs_count": 0,
            "companies_count": 0,
            "pages_scraped": 0,
            "errors": [],
            "metadata": {
                "start_time": datetime.now(),
                "search_terms_used": search_terms,
                "locations_used": locations
            }
        }
        
        try:
            # Scraping por término de búsqueda y ubicación
            for search_term in search_terms:
                for location in locations:
                    
                    # Rate limiting
                    await asyncio.sleep(rate_limit["delay"])
                    
                    # Buscar trabajos
                    jobs_data = await self._search_jobs(platform, search_term, location, max_pages)
                    platform_results["jobs"].extend(jobs_data["jobs"])
                    platform_results["pages_scraped"] += jobs_data["pages_scraped"]
                    
                    # Extraer información de empresas
                    companies_data = await self._extract_companies_info(platform, jobs_data["jobs"])
                    platform_results["companies"].extend(companies_data)
                    
                    # Control de rate limiting
                    if len(platform_results["jobs"]) % 50 == 0:
                        await asyncio.sleep(rate_limit["delay"] * 2)
            
            # Eliminar duplicados
            platform_results["jobs"] = self._remove_duplicate_jobs(platform_results["jobs"])
            platform_results["companies"] = self._remove_duplicate_companies(platform_results["companies"])
            
            platform_results["jobs_count"] = len(platform_results["jobs"])
            platform_results["companies_count"] = len(platform_results["companies"])
            
            logger.info(f"✅ {platform.value}: {platform_results['jobs_count']} jobs, {platform_results['companies_count']} companies")
            
        except Exception as e:
            logger.error(f"❌ Error scraping {platform.value}: {e}")
            platform_results["errors"].append(str(e))
        
        platform_results["metadata"]["end_time"] = datetime.now()
        return platform_results
    
    async def _search_jobs(self, platform: JobBoardPlatform, 
                          search_term: str, location: str, 
                          max_pages: int) -> Dict[str, Any]:
        """Búsqueda de trabajos en plataforma específica"""
        
        config = self.platform_configs[platform]
        jobs = []
        pages_scraped = 0
        
        for page in range(1, max_pages + 1):
            try:
                # Construir URL de búsqueda
                search_url = await self._build_search_url(platform, search_term, location, page)
                
                # Realizar request
                async with self.session.get(search_url, headers=config["headers"]) as response:
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} for {search_url}")
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extraer trabajos de la página
                    page_jobs = await self._extract_jobs_from_page(platform, soup, search_url)
                    
                    if not page_jobs:
                        logger.info(f"No more jobs found on page {page} for {platform.value}")
                        break
                    
                    jobs.extend(page_jobs)
                    pages_scraped += 1
                    
                    # Rate limiting entre páginas
                    await asyncio.sleep(self.rate_limits[platform]["delay"])
                    
            except Exception as e:
                logger.error(f"Error scraping page {page} of {platform.value}: {e}")
                continue
        
        return {
            "jobs": jobs,
            "pages_scraped": pages_scraped
        }
    
    async def _build_search_url(self, platform: JobBoardPlatform, 
                               search_term: str, location: str, page: int) -> str:
        """Construye URL de búsqueda específica por plataforma"""
        
        config = self.platform_configs[platform]
        base_url = config["base_url"]
        search_path = config["search_path"]
        
        # Codificar términos de búsqueda
        encoded_term = quote(search_term)
        encoded_location = quote(location)
        
        if platform == JobBoardPlatform.INDEED:
            return f"{base_url}{search_path}?q={encoded_term}&l={encoded_location}&start={page*10}"
        
        elif platform == JobBoardPlatform.OCC_MUNDIAL:
            return f"{base_url}{search_path}?palabra_clave={encoded_term}&ubicacion={encoded_location}&pagina={page}"
        
        elif platform == JobBoardPlatform.COMPUTRABAJO:
            return f"{base_url}{search_path}?q={encoded_term}&l={encoded_location}&p={page}"
        
        elif platform == JobBoardPlatform.MONSTER:
            return f"{base_url}{search_path}?q={encoded_term}&where={encoded_location}&page={page}"
        
        else:
            return f"{base_url}{search_path}?q={encoded_term}&location={encoded_location}&page={page}"
    
    async def _extract_jobs_from_page(self, platform: JobBoardPlatform, 
                                     soup: BeautifulSoup, page_url: str) -> List[JobPosting]:
        """Extrae trabajos de una página específica"""
        
        config = self.platform_configs[platform]
        selectors = config["selectors"]
        jobs = []
        
        try:
            # Seleccionar elementos de trabajo según la plataforma
            if platform == JobBoardPlatform.INDEED:
                job_elements = soup.select('[data-jk]')
            elif platform == JobBoardPlatform.OCC_MUNDIAL:
                job_elements = soup.select('.job-item')
            elif platform == JobBoardPlatform.COMPUTRABAJO:
                job_elements = soup.select('.w-100.p20')
            elif platform == JobBoardPlatform.MONSTER:
                job_elements = soup.select('.JobCard')
            else:
                job_elements = soup.select('.job-listing')
            
            for element in job_elements:
                try:
                    job = await self._extract_job_details(platform, element, selectors)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"Error extracting job details: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error extracting jobs from page: {e}")
        
        return jobs
    
    async def _extract_job_details(self, platform: JobBoardPlatform, 
                                  element, selectors: Dict[str, str]) -> Optional[JobPosting]:
        """Extrae detalles de un trabajo específico"""
        
        try:
            # Extraer información básica
            title = self._safe_extract_text(element, selectors.get("job_title"))
            company = self._safe_extract_text(element, selectors.get("company"))
            location = self._safe_extract_text(element, selectors.get("location"))
            salary = self._safe_extract_text(element, selectors.get("salary"))
            
            if not title or not company:
                return None
            
            # Generar ID único
            job_id = hashlib.md5(f"{platform.value}_{title}_{company}_{location}".encode()).hexdigest()
            
            # Extraer URL del trabajo
            job_url = self._extract_job_url(element, platform)
            
            # Extraer descripción (si está disponible en la página de listado)
            description = self._safe_extract_text(element, selectors.get("description", ""))
            
            # Extraer fecha de publicación
            posted_date = self._extract_posted_date(element, selectors.get("posted_date"))
            
            # Extraer tipo de trabajo
            job_type = self._safe_extract_text(element, selectors.get("job_type", ""))
            
            # Crear objeto JobPosting
            job = JobPosting(
                job_id=job_id,
                title=title.strip(),
                company=company.strip(),
                location=location.strip() if location else "",
                salary=salary.strip() if salary else None,
                description=description.strip() if description else "",
                requirements=[],  # Se extraerá en detalle si es necesario
                benefits=[],
                posted_date=posted_date,
                expires_date=None,
                job_type=job_type.strip() if job_type else "full-time",
                experience_level="",
                industry="",
                platform=platform,
                url=job_url,
                scraped_at=datetime.now(),
                contact_info={},
                company_size=None,
                company_industry=None,
                skills_required=[],
                education_required=None,
                remote_work=self._detect_remote_work(title, description),
                confidence_score=self._calculate_job_confidence(title, company, location, description)
            )
            
            return job
            
        except Exception as e:
            logger.debug(f"Error extracting job details: {e}")
            return None
    
    def _safe_extract_text(self, element, selector: str) -> str:
        """Extrae texto de forma segura"""
        if not selector:
            return ""
        
        try:
            found_element = element.select_one(selector)
            if found_element:
                return found_element.get_text(strip=True)
        except Exception:
            pass
        
        return ""
    
    def _extract_job_url(self, element, platform: JobBoardPlatform) -> str:
        """Extrae URL del trabajo"""
        
        config = self.platform_configs[platform]
        base_url = config["base_url"]
        
        try:
            if platform == JobBoardPlatform.INDEED:
                link = element.select_one('a[data-jk]')
                if link:
                    return f"{base_url}/viewjob?jk={link.get('data-jk')}"
            
            elif platform == JobBoardPlatform.OCC_MUNDIAL:
                link = element.select_one('a.job-title')
                if link:
                    return urljoin(base_url, link.get('href'))
            
            elif platform == JobBoardPlatform.COMPUTRABAJO:
                link = element.select_one('a.js-o-link')
                if link:
                    return urljoin(base_url, link.get('href'))
            
            elif platform == JobBoardPlatform.MONSTER:
                link = element.select_one('a.JobTitle')
                if link:
                    return urljoin(base_url, link.get('href'))
        
        except Exception:
            pass
        
        return ""
    
    def _extract_posted_date(self, element, selector: str) -> datetime:
        """Extrae fecha de publicación"""
        
        date_text = self._safe_extract_text(element, selector)
        
        if not date_text:
            return datetime.now()
        
        # Patrones comunes de fechas
        try:
            # "Hace 2 días"
            if "hace" in date_text.lower():
                if "día" in date_text.lower():
                    days = re.search(r'(\d+)', date_text)
                    if days:
                        return datetime.now() - timedelta(days=int(days.group(1)))
                elif "hora" in date_text.lower():
                    hours = re.search(r'(\d+)', date_text)
                    if hours:
                        return datetime.now() - timedelta(hours=int(hours.group(1)))
            
            # "Hoy"
            if "hoy" in date_text.lower():
                return datetime.now()
            
            # "Ayer"
            if "ayer" in date_text.lower():
                return datetime.now() - timedelta(days=1)
        
        except Exception:
            pass
        
        return datetime.now()
    
    def _detect_remote_work(self, title: str, description: str) -> bool:
        """Detecta si el trabajo es remoto"""
        
        remote_keywords = [
            "remoto", "remote", "home office", "trabajo desde casa",
            "teletrabajo", "virtual", "a distancia", "desde casa"
        ]
        
        text = f"{title} {description}".lower()
        
        return any(keyword in text for keyword in remote_keywords)
    
    def _calculate_job_confidence(self, title: str, company: str, 
                                 location: str, description: str) -> float:
        """Calcula score de confianza del trabajo"""
        
        confidence = 0.5  # Base score
        
        # Título completo
        if title and len(title) > 10:
            confidence += 0.2
        
        # Empresa conocida
        if company and len(company) > 3:
            confidence += 0.15
        
        # Ubicación específica
        if location and len(location) > 5:
            confidence += 0.1
        
        # Descripción detallada
        if description and len(description) > 100:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    async def _extract_companies_info(self, platform: JobBoardPlatform, 
                                    jobs: List[JobPosting]) -> List[CompanyProfile]:
        """Extrae información de empresas de los trabajos"""
        
        companies = {}
        
        for job in jobs:
            company_name = job.company
            
            if company_name not in companies:
                companies[company_name] = CompanyProfile(
                    company_id=hashlib.md5(f"{platform.value}_{company_name}".encode()).hexdigest(),
                    name=company_name,
                    industry=job.company_industry or "",
                    size=job.company_size,
                    location=job.location,
                    website=None,
                    description="",
                    founded_year=None,
                    employees_count=None,
                    revenue_estimate=None,
                    growth_indicators=[],
                    contact_info={},
                    social_media={},
                    job_postings_count=1,
                    hiring_trends={"active_jobs": 1, "recent_postings": 1},
                    scraped_at=datetime.now(),
                    platform=platform,
                    confidence_score=0.7
                )
            else:
                companies[company_name].job_postings_count += 1
                companies[company_name].hiring_trends["active_jobs"] += 1
        
        return list(companies.values())
    
    def _remove_duplicate_jobs(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """Elimina trabajos duplicados"""
        
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = f"{job.title}_{job.company}_{job.location}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _remove_duplicate_companies(self, companies: List[CompanyProfile]) -> List[CompanyProfile]:
        """Elimina empresas duplicadas"""
        
        seen = set()
        unique_companies = []
        
        for company in companies:
            if company.name not in seen:
                seen.add(company.name)
                unique_companies.append(company)
        
        return unique_companies
    
    async def _analyze_top_companies(self, platform_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analiza las mejores empresas por número de ofertas"""
        
        company_counts = {}
        
        for platform, results in platform_results.items():
            for company in results.get("companies", []):
                name = company.name
                if name not in company_counts:
                    company_counts[name] = {
                        "name": name,
                        "total_jobs": 0,
                        "platforms": set(),
                        "locations": set(),
                        "industries": set()
                    }
                
                company_counts[name]["total_jobs"] += company.job_postings_count
                company_counts[name]["platforms"].add(platform)
                company_counts[name]["locations"].add(company.location)
                if company.industry:
                    company_counts[name]["industries"].add(company.industry)
        
        # Convertir sets a listas y ordenar
        top_companies = []
        for company_data in company_counts.values():
            company_data["platforms"] = list(company_data["platforms"])
            company_data["locations"] = list(company_data["locations"])
            company_data["industries"] = list(company_data["industries"])
            top_companies.append(company_data)
        
        # Ordenar por número de trabajos
        top_companies.sort(key=lambda x: x["total_jobs"], reverse=True)
        
        return top_companies[:50]  # Top 50 empresas
    
    async def _analyze_trending_skills(self, platform_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analiza habilidades en tendencia"""
        
        skills_count = {}
        
        # Palabras clave técnicas comunes
        tech_skills = [
            "python", "java", "javascript", "react", "node.js", "sql", "aws",
            "docker", "kubernetes", "git", "agile", "scrum", "machine learning",
            "data science", "artificial intelligence", "cloud computing",
            "devops", "microservices", "api", "rest", "json", "html", "css"
        ]
        
        for platform, results in platform_results.items():
            for job in results.get("jobs", []):
                text = f"{job.title} {job.description}".lower()
                
                for skill in tech_skills:
                    if skill in text:
                        if skill not in skills_count:
                            skills_count[skill] = {"skill": skill, "count": 0, "platforms": set()}
                        skills_count[skill]["count"] += 1
                        skills_count[skill]["platforms"].add(platform)
        
        # Convertir y ordenar
        trending_skills = []
        for skill_data in skills_count.values():
            skill_data["platforms"] = list(skill_data["platforms"])
            trending_skills.append(skill_data)
        
        trending_skills.sort(key=lambda x: x["count"], reverse=True)
        
        return trending_skills[:20]  # Top 20 skills
    
    async def _analyze_salary_trends(self, platform_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza tendencias salariales"""
        
        salary_data = {
            "total_jobs_with_salary": 0,
            "salary_ranges": [],
            "average_by_location": {},
            "average_by_industry": {},
            "remote_vs_onsite": {"remote": [], "onsite": []}
        }
        
        for platform, results in platform_results.items():
            for job in results.get("jobs", []):
                if job.salary:
                    salary_data["total_jobs_with_salary"] += 1
                    
                    # Extraer números del salario
                    salary_numbers = re.findall(r'\d+', job.salary.replace(',', ''))
                    if salary_numbers:
                        salary_value = int(salary_numbers[0])
                        salary_data["salary_ranges"].append(salary_value)
                        
                        # Por ubicación
                        location = job.location
                        if location not in salary_data["average_by_location"]:
                            salary_data["average_by_location"][location] = []
                        salary_data["average_by_location"][location].append(salary_value)
                        
                        # Remoto vs presencial
                        if job.remote_work:
                            salary_data["remote_vs_onsite"]["remote"].append(salary_value)
                        else:
                            salary_data["remote_vs_onsite"]["onsite"].append(salary_value)
        
        # Calcular promedios
        if salary_data["salary_ranges"]:
            salary_data["overall_average"] = sum(salary_data["salary_ranges"]) / len(salary_data["salary_ranges"])
        
        for location, salaries in salary_data["average_by_location"].items():
            if salaries:
                salary_data["average_by_location"][location] = sum(salaries) / len(salaries)
        
        return salary_data
    
    async def _analyze_market_trends(self, platform_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza tendencias del mercado"""
        
        trends = {
            "total_jobs_analyzed": 0,
            "remote_work_percentage": 0,
            "top_locations": {},
            "job_types": {},
            "posting_trends": {},
            "growth_indicators": []
        }
        
        total_jobs = 0
        remote_jobs = 0
        
        for platform, results in platform_results.items():
            for job in results.get("jobs", []):
                total_jobs += 1
                
                # Trabajo remoto
                if job.remote_work:
                    remote_jobs += 1
                
                # Ubicaciones
                location = job.location
                if location not in trends["top_locations"]:
                    trends["top_locations"][location] = 0
                trends["top_locations"][location] += 1
                
                # Tipos de trabajo
                job_type = job.job_type
                if job_type not in trends["job_types"]:
                    trends["job_types"][job_type] = 0
                trends["job_types"][job_type] += 1
        
        trends["total_jobs_analyzed"] = total_jobs
        if total_jobs > 0:
            trends["remote_work_percentage"] = (remote_jobs / total_jobs) * 100
        
        return trends

# Función para obtener el scraper
def get_job_boards_scraper(config: Dict[str, Any]) -> JobBoardsScraper:
    """Factory function para el scraper"""
    return JobBoardsScraper(config)