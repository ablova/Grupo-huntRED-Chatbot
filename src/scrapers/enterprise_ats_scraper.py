"""
HuntRED® v2 - Enterprise ATS Scraper
Scraper completo para Workday, Phenom, Level, Oracle HCM, BambooHR, SuccessFactors
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

class ATSPlatform(Enum):
    WORKDAY = "workday"
    PHENOM = "phenom"
    LEVEL = "level"
    ORACLE_HCM = "oracle_hcm"
    BAMBOOHR = "bamboohr"
    SUCCESSFACTORS = "successfactors"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    JOBVITE = "jobvite"
    SMARTRECRUITERS = "smartrecruiters"
    ICIMS = "icims"
    CORNERSTONE = "cornerstone"
    TALEO = "taleo"
    WORKABLE = "workable"
    RECRUITERBOX = "recruiterbox"

@dataclass
class ATSJobPosting:
    """Estructura de datos para ofertas de ATS Enterprise"""
    job_id: str
    title: str
    company: str
    company_id: str
    location: str
    department: str
    salary_range: Optional[str]
    description: str
    requirements: List[str]
    benefits: List[str]
    posted_date: datetime
    expires_date: Optional[datetime]
    job_type: str
    experience_level: str
    education_required: Optional[str]
    skills_required: List[str]
    ats_platform: ATSPlatform
    ats_job_url: str
    company_url: str
    apply_url: str
    scraped_at: datetime
    remote_work: bool
    visa_sponsorship: bool
    employment_type: str
    career_level: str
    industry: str
    company_size: Optional[str]
    hiring_manager: Optional[str]
    hr_contact: Optional[str]
    confidence_score: float
    data_completeness: float

@dataclass
class ATSCompanyProfile:
    """Perfil completo de empresa extraído de ATS"""
    company_id: str
    name: str
    industry: str
    size: Optional[str]
    headquarters: str
    locations: List[str]
    website: str
    description: str
    founded_year: Optional[int]
    employees_count_range: Optional[str]
    revenue_estimate: Optional[str]
    ats_platform: ATSPlatform
    ats_company_url: str
    career_page_url: str
    active_jobs_count: int
    departments: List[str]
    hiring_patterns: Dict[str, Any]
    growth_indicators: List[str]
    company_culture: Dict[str, Any]
    benefits_offered: List[str]
    tech_stack: List[str]
    contact_info: Dict[str, Any]
    social_media: Dict[str, str]
    recent_news: List[Dict[str, Any]]
    scraped_at: datetime
    confidence_score: float

class EnterpriseATSScraper:
    """Scraper unificado para todas las plataformas ATS Enterprise"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
        
        # Rate limits específicos por ATS
        self.rate_limits = {
            ATSPlatform.WORKDAY: {"requests_per_minute": 8, "delay": 8.0},
            ATSPlatform.PHENOM: {"requests_per_minute": 12, "delay": 5.0},
            ATSPlatform.LEVEL: {"requests_per_minute": 15, "delay": 4.0},
            ATSPlatform.ORACLE_HCM: {"requests_per_minute": 6, "delay": 10.0},
            ATSPlatform.BAMBOOHR: {"requests_per_minute": 10, "delay": 6.0},
            ATSPlatform.SUCCESSFACTORS: {"requests_per_minute": 8, "delay": 8.0},
            ATSPlatform.GREENHOUSE: {"requests_per_minute": 20, "delay": 3.0},
            ATSPlatform.LEVER: {"requests_per_minute": 18, "delay": 3.5},
            ATSPlatform.JOBVITE: {"requests_per_minute": 12, "delay": 5.0},
            ATSPlatform.SMARTRECRUITERS: {"requests_per_minute": 15, "delay": 4.0},
            ATSPlatform.ICIMS: {"requests_per_minute": 10, "delay": 6.0},
            ATSPlatform.CORNERSTONE: {"requests_per_minute": 8, "delay": 8.0},
            ATSPlatform.TALEO: {"requests_per_minute": 6, "delay": 10.0},
            ATSPlatform.WORKABLE: {"requests_per_minute": 20, "delay": 3.0},
            ATSPlatform.RECRUITERBOX: {"requests_per_minute": 15, "delay": 4.0}
        }
        
        # Configuraciones específicas por ATS
        self.ats_configs = {
            ATSPlatform.WORKDAY: {
                "api_base": "https://{company}.myworkdayjobs.com",
                "jobs_endpoint": "/jobs",
                "company_endpoint": "/company",
                "search_patterns": {
                    "job_cards": ".css-19uc56f",
                    "job_title": "[data-automation-id='jobTitle']",
                    "job_location": "[data-automation-id='locations']",
                    "job_department": "[data-automation-id='jobDepartment']",
                    "job_description": "[data-automation-id='jobDescription']",
                    "apply_button": "[data-automation-id='applyButton']"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/html, */*",
                    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
                    "Referer": "https://www.workday.com/"
                }
            },
            ATSPlatform.PHENOM: {
                "api_base": "https://{company}.phenompeople.com",
                "jobs_endpoint": "/jobs",
                "api_endpoint": "/api/v1/jobs",
                "search_patterns": {
                    "job_cards": ".job-card",
                    "job_title": ".job-title",
                    "job_location": ".job-location",
                    "job_department": ".job-department",
                    "job_description": ".job-description",
                    "apply_button": ".apply-button"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest"
                }
            },
            ATSPlatform.LEVEL: {
                "api_base": "https://jobs.level.co",
                "jobs_endpoint": "/jobs",
                "api_endpoint": "/api/jobs",
                "search_patterns": {
                    "job_cards": ".job-listing",
                    "job_title": ".job-title",
                    "job_location": ".job-location",
                    "job_salary": ".job-salary",
                    "job_description": ".job-description"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            },
            ATSPlatform.ORACLE_HCM: {
                "api_base": "https://{company}.oracle.com",
                "jobs_endpoint": "/hcmRestApi/resources/latest/recruitingCEJobRequisitions",
                "career_site": "/careers",
                "search_patterns": {
                    "job_cards": ".job-item",
                    "job_title": ".job-title",
                    "job_location": ".job-location",
                    "job_department": ".job-department"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                    "Authorization": "Bearer {token}"
                }
            },
            ATSPlatform.BAMBOOHR: {
                "api_base": "https://{company}.bamboohr.com",
                "jobs_endpoint": "/jobs",
                "api_endpoint": "/api/gateway.php/{company}/v1/applicant_tracking/jobs",
                "search_patterns": {
                    "job_cards": ".job-board-job",
                    "job_title": ".job-title",
                    "job_location": ".job-location",
                    "job_description": ".job-description"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                    "Authorization": "Basic {credentials}"
                }
            },
            ATSPlatform.SUCCESSFACTORS: {
                "api_base": "https://{company}.successfactors.com",
                "jobs_endpoint": "/career",
                "api_endpoint": "/odata/v2/JobRequisition",
                "search_patterns": {
                    "job_cards": ".jobTile",
                    "job_title": ".jobTitle",
                    "job_location": ".jobLocation",
                    "job_department": ".jobDepartment"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                    "X-CSRF-Token": "fetch"
                }
            },
            ATSPlatform.GREENHOUSE: {
                "api_base": "https://boards.greenhouse.io",
                "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/{company}/jobs",
                "jobs_endpoint": "/{company}",
                "search_patterns": {
                    "job_cards": ".opening",
                    "job_title": ".opening a",
                    "job_location": ".location",
                    "job_department": ".department"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json"
                }
            },
            ATSPlatform.LEVER: {
                "api_base": "https://jobs.lever.co",
                "api_endpoint": "https://api.lever.co/v0/postings/{company}",
                "jobs_endpoint": "/{company}",
                "search_patterns": {
                    "job_cards": ".posting",
                    "job_title": ".posting-name",
                    "job_location": ".posting-location",
                    "job_commitment": ".posting-commitment"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json"
                }
            }
        }
    
    async def scrape_all_ats_platforms(self, target_companies: List[str], 
                                     platforms: List[ATSPlatform] = None) -> Dict[str, Any]:
        """Scraping completo de todas las plataformas ATS"""
        
        if not platforms:
            platforms = list(ATSPlatform)
        
        results = {
            "total_jobs": 0,
            "total_companies": 0,
            "total_ats_platforms": len(platforms),
            "platform_results": {},
            "company_profiles": [],
            "top_hiring_companies": [],
            "trending_skills_by_ats": {},
            "salary_insights_by_ats": {},
            "hiring_patterns": {},
            "scraping_metadata": {
                "start_time": datetime.now(),
                "target_companies": target_companies,
                "platforms_scraped": [],
                "companies_found": []
            }
        }
        
        # Crear sesión HTTP optimizada para ATS
        connector = aiohttp.TCPConnector(
            limit=50,  # Límite más conservador para ATS
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        timeout = aiohttp.ClientTimeout(total=60)  # Timeout más largo para ATS
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            self.session = session
            
            # Scraping paralelo por ATS platform
            tasks = []
            for platform in platforms:
                if platform in self.ats_configs:
                    task = self._scrape_ats_platform(platform, target_companies)
                    tasks.append(task)
            
            # Ejecutar en paralelo con control de concurrencia
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            for i, result in enumerate(platform_results):
                platform = platforms[i] if i < len(platforms) else None
                
                if isinstance(result, Exception):
                    logger.error(f"Error scraping {platform.value if platform else 'unknown'}: {result}")
                    continue
                
                if isinstance(result, dict) and platform:
                    results["platform_results"][platform.value] = result
                    results["total_jobs"] += result.get("jobs_count", 0)
                    results["total_companies"] += result.get("companies_count", 0)
                    results["scraping_metadata"]["platforms_scraped"].append(platform.value)
                    
                    # Agregar empresas encontradas
                    companies = result.get("companies", [])
                    results["company_profiles"].extend(companies)
        
        # Análisis consolidado
        results["top_hiring_companies"] = await self._analyze_top_hiring_companies(results["platform_results"])
        results["trending_skills_by_ats"] = await self._analyze_trending_skills_by_ats(results["platform_results"])
        results["salary_insights_by_ats"] = await self._analyze_salary_insights_by_ats(results["platform_results"])
        results["hiring_patterns"] = await self._analyze_hiring_patterns(results["platform_results"])
        
        # Deduplicar empresas
        results["company_profiles"] = self._deduplicate_companies(results["company_profiles"])
        results["total_companies"] = len(results["company_profiles"])
        
        results["scraping_metadata"]["end_time"] = datetime.now()
        results["scraping_metadata"]["total_duration"] = (
            results["scraping_metadata"]["end_time"] - 
            results["scraping_metadata"]["start_time"]
        ).total_seconds()
        
        logger.info(f"✅ ATS Scraping completed: {results['total_jobs']} jobs from {results['total_companies']} companies across {len(results['scraping_metadata']['platforms_scraped'])} platforms")
        
        return results
    
    async def _scrape_ats_platform(self, platform: ATSPlatform, 
                                  target_companies: List[str]) -> Dict[str, Any]:
        """Scraping específico por plataforma ATS"""
        
        config = self.ats_configs[platform]
        rate_limit = self.rate_limits[platform]
        
        platform_results = {
            "platform": platform.value,
            "jobs": [],
            "companies": [],
            "jobs_count": 0,
            "companies_count": 0,
            "companies_scraped": 0,
            "errors": [],
            "metadata": {
                "start_time": datetime.now(),
                "target_companies": target_companies,
                "rate_limit": rate_limit
            }
        }
        
        try:
            # Scraping por empresa objetivo
            for company in target_companies:
                
                # Rate limiting
                await asyncio.sleep(rate_limit["delay"])
                
                try:
                    # Detectar si la empresa usa este ATS
                    company_info = await self._detect_company_ats(company, platform)
                    
                    if not company_info:
                        continue
                    
                    # Scraping de trabajos de la empresa
                    jobs_data = await self._scrape_company_jobs(platform, company_info)
                    if jobs_data:
                        platform_results["jobs"].extend(jobs_data.get("jobs", []))
                        platform_results["companies_scraped"] += 1
                        
                        # Crear perfil de empresa
                        company_profile = await self._extract_company_profile(platform, company_info, jobs_data)
                        if company_profile:
                            platform_results["companies"].append(company_profile)
                    
                    # Control de rate limiting adicional
                    if platform_results["companies_scraped"] % 5 == 0:
                        await asyncio.sleep(rate_limit["delay"] * 2)
                
                except Exception as e:
                    logger.warning(f"Error scraping {company} on {platform.value}: {e}")
                    platform_results["errors"].append(f"{company}: {str(e)}")
                    continue
            
            # Eliminar duplicados
            platform_results["jobs"] = self._remove_duplicate_ats_jobs(platform_results["jobs"])
            platform_results["companies"] = self._remove_duplicate_ats_companies(platform_results["companies"])
            
            platform_results["jobs_count"] = len(platform_results["jobs"])
            platform_results["companies_count"] = len(platform_results["companies"])
            
            logger.info(f"✅ {platform.value}: {platform_results['jobs_count']} jobs from {platform_results['companies_count']} companies")
            
        except Exception as e:
            logger.error(f"❌ Error scraping {platform.value}: {e}")
            platform_results["errors"].append(str(e))
        
        platform_results["metadata"]["end_time"] = datetime.now()
        return platform_results
    
    async def _detect_company_ats(self, company: str, platform: ATSPlatform) -> Optional[Dict[str, Any]]:
        """Detecta si una empresa usa un ATS específico"""
        
        config = self.ats_configs[platform]
        
        # Construir URLs potenciales
        potential_urls = []
        
        company_slug = company.lower().replace(' ', '').replace('-', '').replace('_', '')
        company_dash = company.lower().replace(' ', '-').replace('_', '-')
        company_underscore = company.lower().replace(' ', '_').replace('-', '_')
        
        if platform == ATSPlatform.WORKDAY:
            potential_urls = [
                f"https://{company_slug}.myworkdayjobs.com",
                f"https://{company_dash}.myworkdayjobs.com",
                f"https://{company_underscore}.myworkdayjobs.com"
            ]
        elif platform == ATSPlatform.PHENOM:
            potential_urls = [
                f"https://{company_slug}.phenompeople.com",
                f"https://{company_dash}.phenompeople.com",
                f"https://careers.{company_slug}.com"
            ]
        elif platform == ATSPlatform.GREENHOUSE:
            potential_urls = [
                f"https://boards.greenhouse.io/{company_slug}",
                f"https://boards.greenhouse.io/{company_dash}"
            ]
        elif platform == ATSPlatform.LEVER:
            potential_urls = [
                f"https://jobs.lever.co/{company_slug}",
                f"https://jobs.lever.co/{company_dash}"
            ]
        elif platform == ATSPlatform.BAMBOOHR:
            potential_urls = [
                f"https://{company_slug}.bamboohr.com/jobs",
                f"https://{company_dash}.bamboohr.com/jobs"
            ]
        
        # Probar URLs para detectar ATS
        for url in potential_urls:
            try:
                async with self.session.get(url, headers=config["headers"]) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Verificar si es realmente el ATS correcto
                        if await self._verify_ats_platform(content, platform):
                            return {
                                "company": company,
                                "company_slug": company_slug,
                                "ats_url": url,
                                "base_url": url,
                                "verified": True
                            }
                        
            except Exception as e:
                logger.debug(f"Failed to check {url}: {e}")
                continue
        
        return None
    
    async def _verify_ats_platform(self, content: str, platform: ATSPlatform) -> bool:
        """Verifica si el contenido corresponde al ATS correcto"""
        
        platform_indicators = {
            ATSPlatform.WORKDAY: ["workday", "myworkdayjobs", "data-automation-id"],
            ATSPlatform.PHENOM: ["phenompeople", "phenom", "PhenomPeople"],
            ATSPlatform.GREENHOUSE: ["greenhouse", "boards.greenhouse", "greenhouse-board"],
            ATSPlatform.LEVER: ["lever.co", "lever", "jobs.lever"],
            ATSPlatform.BAMBOOHR: ["bamboohr", "BambooHR", "bamboo"],
            ATSPlatform.SUCCESSFACTORS: ["successfactors", "SuccessFactors", "sap-sf"],
            ATSPlatform.ORACLE_HCM: ["oracle", "hcm", "taleo"],
            ATSPlatform.LEVEL: ["level.co", "jobs.level"],
            ATSPlatform.PHENOM: ["phenompeople", "phenom-people"]
        }
        
        indicators = platform_indicators.get(platform, [])
        content_lower = content.lower()
        
        return any(indicator.lower() in content_lower for indicator in indicators)
    
    async def _scrape_company_jobs(self, platform: ATSPlatform, 
                                  company_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Scraping de trabajos de una empresa específica"""
        
        config = self.ats_configs[platform]
        base_url = company_info["ats_url"]
        
        jobs_data = {
            "jobs": [],
            "total_pages": 0,
            "company_info": company_info
        }
        
        try:
            if platform == ATSPlatform.WORKDAY:
                jobs_data = await self._scrape_workday_jobs(base_url, config)
            elif platform == ATSPlatform.PHENOM:
                jobs_data = await self._scrape_phenom_jobs(base_url, config)
            elif platform == ATSPlatform.GREENHOUSE:
                jobs_data = await self._scrape_greenhouse_jobs(base_url, config, company_info["company_slug"])
            elif platform == ATSPlatform.LEVER:
                jobs_data = await self._scrape_lever_jobs(base_url, config, company_info["company_slug"])
            elif platform == ATSPlatform.BAMBOOHR:
                jobs_data = await self._scrape_bamboohr_jobs(base_url, config)
            # Agregar más ATS según sea necesario
            
            # Enriquecer trabajos con información de la empresa
            for job in jobs_data.get("jobs", []):
                job.company_id = company_info["company_slug"]
                job.company = company_info["company"]
                job.ats_platform = platform
                job.scraped_at = datetime.now()
            
            return jobs_data
            
        except Exception as e:
            logger.error(f"Error scraping jobs for {company_info['company']} on {platform.value}: {e}")
            return None
    
    async def _scrape_workday_jobs(self, base_url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Scraping específico para Workday"""
        
        jobs = []
        
        try:
            # Workday usa endpoints específicos
            jobs_url = f"{base_url}/jobs"
            
            async with self.session.get(jobs_url, headers=config["headers"]) as response:
                if response.status != 200:
                    return {"jobs": jobs}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Seleccionar tarjetas de trabajo
                job_cards = soup.select(config["search_patterns"]["job_cards"])
                
                for card in job_cards:
                    try:
                        job = await self._extract_workday_job_details(card, base_url, config)
                        if job:
                            jobs.append(job)
                    except Exception as e:
                        logger.debug(f"Error extracting Workday job: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Error scraping Workday jobs: {e}")
        
        return {"jobs": jobs}
    
    async def _extract_workday_job_details(self, card, base_url: str, config: Dict[str, Any]) -> Optional[ATSJobPosting]:
        """Extrae detalles de un trabajo de Workday"""
        
        try:
            patterns = config["search_patterns"]
            
            # Extraer información básica
            title_element = card.select_one(patterns["job_title"])
            title = title_element.get_text(strip=True) if title_element else ""
            
            location_element = card.select_one(patterns["job_location"])
            location = location_element.get_text(strip=True) if location_element else ""
            
            dept_element = card.select_one(patterns["job_department"])
            department = dept_element.get_text(strip=True) if dept_element else ""
            
            # Extraer URL del trabajo
            job_link = title_element.get('href') if title_element and title_element.name == 'a' else None
            if not job_link:
                job_link_parent = card.select_one('a')
                job_link = job_link_parent.get('href') if job_link_parent else ""
            
            job_url = urljoin(base_url, job_link) if job_link else ""
            
            if not title:
                return None
            
            # Generar ID único
            job_id = hashlib.md5(f"workday_{title}_{location}_{department}".encode()).hexdigest()
            
            # Crear objeto ATSJobPosting
            job = ATSJobPosting(
                job_id=job_id,
                title=title,
                company="",  # Se llenará después
                company_id="",  # Se llenará después
                location=location,
                department=department,
                salary_range=None,
                description="",  # Se puede obtener con scraping adicional
                requirements=[],
                benefits=[],
                posted_date=datetime.now(),  # Workday no siempre muestra fecha
                expires_date=None,
                job_type="full-time",
                experience_level="",
                education_required=None,
                skills_required=[],
                ats_platform=ATSPlatform.WORKDAY,
                ats_job_url=job_url,
                company_url=base_url,
                apply_url=job_url,
                scraped_at=datetime.now(),
                remote_work=self._detect_remote_work_ats(title, ""),
                visa_sponsorship=False,
                employment_type="full-time",
                career_level="",
                industry="",
                company_size=None,
                hiring_manager=None,
                hr_contact=None,
                confidence_score=0.8,
                data_completeness=0.6
            )
            
            return job
            
        except Exception as e:
            logger.debug(f"Error extracting Workday job details: {e}")
            return None
    
    async def _scrape_greenhouse_jobs(self, base_url: str, config: Dict[str, Any], company_slug: str) -> Dict[str, Any]:
        """Scraping específico para Greenhouse"""
        
        jobs = []
        
        try:
            # Greenhouse tiene API pública
            api_url = config["api_endpoint"].format(company=company_slug)
            
            async with self.session.get(api_url, headers=config["headers"]) as response:
                if response.status != 200:
                    return {"jobs": jobs}
                
                data = await response.json()
                
                for job_data in data.get("jobs", []):
                    try:
                        job = await self._extract_greenhouse_job_details(job_data, base_url)
                        if job:
                            jobs.append(job)
                    except Exception as e:
                        logger.debug(f"Error extracting Greenhouse job: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Error scraping Greenhouse jobs: {e}")
        
        return {"jobs": jobs}
    
    async def _extract_greenhouse_job_details(self, job_data: Dict[str, Any], base_url: str) -> Optional[ATSJobPosting]:
        """Extrae detalles de un trabajo de Greenhouse"""
        
        try:
            title = job_data.get("title", "")
            location = job_data.get("location", {}).get("name", "")
            department = job_data.get("departments", [{}])[0].get("name", "")
            
            if not title:
                return None
            
            job_id = str(job_data.get("id", hashlib.md5(f"greenhouse_{title}".encode()).hexdigest()))
            
            job = ATSJobPosting(
                job_id=job_id,
                title=title,
                company="",
                company_id="",
                location=location,
                department=department,
                salary_range=None,
                description=job_data.get("content", ""),
                requirements=[],
                benefits=[],
                posted_date=datetime.now(),
                expires_date=None,
                job_type="full-time",
                experience_level="",
                education_required=None,
                skills_required=[],
                ats_platform=ATSPlatform.GREENHOUSE,
                ats_job_url=job_data.get("absolute_url", ""),
                company_url=base_url,
                apply_url=job_data.get("absolute_url", ""),
                scraped_at=datetime.now(),
                remote_work=self._detect_remote_work_ats(title, job_data.get("content", "")),
                visa_sponsorship=False,
                employment_type="full-time",
                career_level="",
                industry="",
                company_size=None,
                hiring_manager=None,
                hr_contact=None,
                confidence_score=0.9,
                data_completeness=0.8
            )
            
            return job
            
        except Exception as e:
            logger.debug(f"Error extracting Greenhouse job details: {e}")
            return None
    
    # Métodos auxiliares
    
    def _detect_remote_work_ats(self, title: str, description: str) -> bool:
        """Detecta trabajo remoto en ATS"""
        
        remote_keywords = [
            "remote", "remoto", "trabajo remoto", "home office", "desde casa",
            "virtual", "distributed", "anywhere", "location independent"
        ]
        
        text = f"{title} {description}".lower()
        return any(keyword in text for keyword in remote_keywords)
    
    def _remove_duplicate_ats_jobs(self, jobs: List[ATSJobPosting]) -> List[ATSJobPosting]:
        """Elimina trabajos duplicados"""
        
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = f"{job.title}_{job.company}_{job.location}_{job.ats_platform.value}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _remove_duplicate_ats_companies(self, companies: List[ATSCompanyProfile]) -> List[ATSCompanyProfile]:
        """Elimina empresas duplicadas"""
        
        seen = set()
        unique_companies = []
        
        for company in companies:
            key = f"{company.name}_{company.ats_platform.value}"
            if key not in seen:
                seen.add(key)
                unique_companies.append(company)
        
        return unique_companies
    
    async def _extract_company_profile(self, platform: ATSPlatform, 
                                     company_info: Dict[str, Any], 
                                     jobs_data: Dict[str, Any]) -> Optional[ATSCompanyProfile]:
        """Extrae perfil completo de empresa"""
        
        try:
            jobs = jobs_data.get("jobs", [])
            
            # Análizar patrones de contratación
            departments = list(set([job.department for job in jobs if job.department]))
            locations = list(set([job.location for job in jobs if job.location]))
            
            hiring_patterns = {
                "total_open_positions": len(jobs),
                "departments_hiring": len(departments),
                "locations_hiring": len(locations),
                "remote_positions": len([job for job in jobs if job.remote_work]),
                "recent_postings": len([job for job in jobs if job.posted_date > datetime.now() - timedelta(days=30)])
            }
            
            # Indicadores de crecimiento
            growth_indicators = []
            if hiring_patterns["total_open_positions"] > 10:
                growth_indicators.append("high_volume_hiring")
            if hiring_patterns["departments_hiring"] > 5:
                growth_indicators.append("multi_department_expansion")
            if hiring_patterns["remote_positions"] > 5:
                growth_indicators.append("remote_work_adoption")
            
            company_profile = ATSCompanyProfile(
                company_id=company_info["company_slug"],
                name=company_info["company"],
                industry="",  # Se puede enriquecer
                size=None,
                headquarters="",
                locations=locations,
                website="",
                description="",
                founded_year=None,
                employees_count_range=None,
                revenue_estimate=None,
                ats_platform=platform,
                ats_company_url=company_info["ats_url"],
                career_page_url=company_info["ats_url"],
                active_jobs_count=len(jobs),
                departments=departments,
                hiring_patterns=hiring_patterns,
                growth_indicators=growth_indicators,
                company_culture={},
                benefits_offered=[],
                tech_stack=[],
                contact_info={},
                social_media={},
                recent_news=[],
                scraped_at=datetime.now(),
                confidence_score=0.8
            )
            
            return company_profile
            
        except Exception as e:
            logger.error(f"Error extracting company profile: {e}")
            return None
    
    def _deduplicate_companies(self, companies: List[ATSCompanyProfile]) -> List[ATSCompanyProfile]:
        """Elimina empresas duplicadas entre plataformas"""
        
        seen_companies = {}
        unique_companies = []
        
        for company in companies:
            key = company.name.lower().strip()
            
            if key not in seen_companies:
                seen_companies[key] = company
                unique_companies.append(company)
            else:
                # Merge información de múltiples ATS
                existing = seen_companies[key]
                existing.active_jobs_count += company.active_jobs_count
                existing.departments = list(set(existing.departments + company.departments))
                existing.locations = list(set(existing.locations + company.locations))
                existing.growth_indicators = list(set(existing.growth_indicators + company.growth_indicators))
        
        return unique_companies
    
    # Métodos de análisis
    
    async def _analyze_top_hiring_companies(self, platform_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analiza las empresas que más están contratando"""
        
        company_hiring = {}
        
        for platform, results in platform_results.items():
            for company in results.get("companies", []):
                name = company.name
                if name not in company_hiring:
                    company_hiring[name] = {
                        "company_name": name,
                        "total_jobs": 0,
                        "ats_platforms": set(),
                        "departments": set(),
                        "locations": set(),
                        "growth_indicators": set()
                    }
                
                company_hiring[name]["total_jobs"] += company.active_jobs_count
                company_hiring[name]["ats_platforms"].add(platform)
                company_hiring[name]["departments"].update(company.departments)
                company_hiring[name]["locations"].update(company.locations)
                company_hiring[name]["growth_indicators"].update(company.growth_indicators)
        
        # Convertir sets a listas y ordenar
        top_companies = []
        for company_data in company_hiring.values():
            company_data["ats_platforms"] = list(company_data["ats_platforms"])
            company_data["departments"] = list(company_data["departments"])
            company_data["locations"] = list(company_data["locations"])
            company_data["growth_indicators"] = list(company_data["growth_indicators"])
            top_companies.append(company_data)
        
        # Ordenar por total de trabajos
        top_companies.sort(key=lambda x: x["total_jobs"], reverse=True)
        
        return top_companies[:25]  # Top 25 empresas
    
    async def _analyze_trending_skills_by_ats(self, platform_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza skills trending por ATS"""
        
        skills_by_ats = {}
        
        for platform, results in platform_results.items():
            skills_count = {}
            
            for job in results.get("jobs", []):
                # Extraer skills del título y descripción
                text = f"{job.title} {job.description}".lower()
                
                # Skills técnicos comunes
                tech_skills = [
                    "python", "java", "javascript", "react", "node.js", "sql", "aws",
                    "docker", "kubernetes", "git", "agile", "scrum", "machine learning",
                    "data science", "cloud computing", "devops", "api", "rest"
                ]
                
                for skill in tech_skills:
                    if skill in text:
                        skills_count[skill] = skills_count.get(skill, 0) + 1
            
            # Top 10 skills por ATS
            sorted_skills = sorted(skills_count.items(), key=lambda x: x[1], reverse=True)
            skills_by_ats[platform] = sorted_skills[:10]
        
        return skills_by_ats
    
    async def _analyze_salary_insights_by_ats(self, platform_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza insights salariales por ATS"""
        
        salary_insights = {}
        
        for platform, results in platform_results.items():
            jobs_with_salary = [job for job in results.get("jobs", []) if job.salary_range]
            
            salary_insights[platform] = {
                "total_jobs": len(results.get("jobs", [])),
                "jobs_with_salary": len(jobs_with_salary),
                "salary_transparency": len(jobs_with_salary) / len(results.get("jobs", [])) if results.get("jobs") else 0,
                "remote_jobs": len([job for job in results.get("jobs", []) if job.remote_work]),
                "remote_percentage": len([job for job in results.get("jobs", []) if job.remote_work]) / len(results.get("jobs", [])) if results.get("jobs") else 0
            }
        
        return salary_insights
    
    async def _analyze_hiring_patterns(self, platform_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza patrones de contratación"""
        
        patterns = {
            "total_companies_analyzed": 0,
            "avg_jobs_per_company": 0,
            "top_departments": {},
            "top_locations": {},
            "ats_adoption": {},
            "hiring_velocity": {}
        }
        
        all_companies = []
        department_counts = {}
        location_counts = {}
        
        for platform, results in platform_results.items():
            companies = results.get("companies", [])
            all_companies.extend(companies)
            
            patterns["ats_adoption"][platform] = len(companies)
            
            for company in companies:
                for dept in company.departments:
                    department_counts[dept] = department_counts.get(dept, 0) + 1
                
                for loc in company.locations:
                    location_counts[loc] = location_counts.get(loc, 0) + 1
        
        patterns["total_companies_analyzed"] = len(all_companies)
        if all_companies:
            patterns["avg_jobs_per_company"] = sum(c.active_jobs_count for c in all_companies) / len(all_companies)
        
        # Top 10 departamentos y ubicaciones
        patterns["top_departments"] = sorted(department_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        patterns["top_locations"] = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return patterns

# Métodos adicionales específicos para otros ATS
# (Phenom, Level, Oracle, etc. - implementación similar)

def get_enterprise_ats_scraper(config: Dict[str, Any]) -> EnterpriseATSScraper:
    """Factory function para el scraper de ATS Enterprise"""
    return EnterpriseATSScraper(config)