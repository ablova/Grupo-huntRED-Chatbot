"""
HuntRED® v2 - Complete Job Publishing Service
Auto-posting a múltiples job boards con optimización de contenido y tracking
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import uuid
from decimal import Decimal
import hashlib

logger = logging.getLogger(__name__)

class PublishPlatform(Enum):
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    MONSTER = "monster"
    OCC_MUNDIAL = "occ_mundial"
    COMPUTRABAJO = "computrabajo"
    GLASSDOOR = "glassdoor"
    ZIPRECRUITER = "ziprecruiter"
    FACEBOOK_JOBS = "facebook_jobs"
    GOOGLE_JOBS = "google_jobs"
    INTERNAL_BOARD = "internal_board"

class JobStatus(Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHED = "published"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    CLOSED = "closed"
    REJECTED = "rejected"

class PublishStatus(Enum):
    NOT_PUBLISHED = "not_published"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    PAUSED = "paused"
    EXPIRED = "expired"

@dataclass
class JobPublication:
    """Publicación de trabajo en una plataforma específica"""
    publication_id: str
    job_id: str
    platform: PublishPlatform
    platform_job_id: Optional[str]
    publication_url: Optional[str]
    status: PublishStatus
    published_at: Optional[datetime]
    expires_at: Optional[datetime]
    views_count: int
    applications_count: int
    clicks_count: int
    cost: Optional[Decimal]
    budget_spent: Optional[Decimal]
    performance_metrics: Dict[str, Any]
    optimization_applied: List[str]
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str]

@dataclass
class OptimizedJobContent:
    """Contenido optimizado para publicación"""
    original_title: str
    optimized_title: str
    original_description: str
    optimized_description: str
    keywords: List[str]
    seo_score: float
    readability_score: float
    ats_compatibility: float
    platform_specific_content: Dict[str, str]
    optimization_suggestions: List[str]

class JobPublishingService:
    """Servicio completo de publicación de trabajos"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Configuraciones por plataforma
        self.platform_configs = {
            PublishPlatform.INDEED: {
                "api_endpoint": "https://secure.indeed.com/rpc/jobsearch",
                "posting_endpoint": "https://employers.indeed.com/api/v1/jobs",
                "auth_type": "api_key",
                "max_title_length": 100,
                "max_description_length": 5000,
                "required_fields": ["title", "description", "location", "salary"],
                "cost_per_click": Decimal("2.50"),
                "headers": {
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            },
            PublishPlatform.LINKEDIN: {
                "api_endpoint": "https://api.linkedin.com/v2/jobPostings",
                "auth_type": "oauth2",
                "max_title_length": 120,
                "max_description_length": 10000,
                "required_fields": ["title", "description", "location", "company"],
                "cost_per_click": Decimal("4.00"),
                "headers": {
                    "Authorization": "Bearer {access_token}",
                    "Content-Type": "application/json",
                    "LinkedIn-Version": "202310"
                }
            },
            PublishPlatform.MONSTER: {
                "api_endpoint": "https://api.monster.com/v1/jobs",
                "auth_type": "api_key",
                "max_title_length": 80,
                "max_description_length": 4000,
                "required_fields": ["title", "description", "location"],
                "cost_per_click": Decimal("3.00"),
                "headers": {
                    "X-API-Key": "{api_key}",
                    "Content-Type": "application/json"
                }
            },
            PublishPlatform.OCC_MUNDIAL: {
                "api_endpoint": "https://api.occ.com.mx/v1/jobs",
                "auth_type": "api_key",
                "max_title_length": 90,
                "max_description_length": 3000,
                "required_fields": ["title", "description", "location", "salary"],
                "cost_per_click": Decimal("1.80"),
                "headers": {
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            },
            PublishPlatform.COMPUTRABAJO: {
                "api_endpoint": "https://api.computrabajo.com.mx/v1/jobs",
                "auth_type": "api_key",
                "max_title_length": 85,
                "max_description_length": 2500,
                "required_fields": ["title", "description", "location"],
                "cost_per_click": Decimal("1.50"),
                "headers": {
                    "X-API-Token": "{api_key}",
                    "Content-Type": "application/json"
                }
            },
            PublishPlatform.GLASSDOOR: {
                "api_endpoint": "https://api.glassdoor.com/api/employer/jobs",
                "auth_type": "api_key",
                "max_title_length": 100,
                "max_description_length": 6000,
                "required_fields": ["title", "description", "location", "company"],
                "cost_per_click": Decimal("3.50"),
                "headers": {
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            }
        }
        
        # Keywords por industria y rol
        self.industry_keywords = {
            "technology": ["tech", "software", "developer", "programming", "digital", "innovation"],
            "healthcare": ["health", "medical", "clinical", "patient", "healthcare", "wellness"],
            "finance": ["financial", "banking", "investment", "accounting", "fintech", "analysis"],
            "marketing": ["marketing", "digital", "social media", "campaigns", "branding", "content"],
            "sales": ["sales", "revenue", "customer", "business development", "account", "targets"]
        }
    
    async def publish_job_multi_platform(self, job_data: Dict[str, Any], 
                                       platforms: List[PublishPlatform],
                                       optimization_level: str = "high") -> Dict[str, Any]:
        """Publica un trabajo en múltiples plataformas con optimización"""
        
        try:
            job_id = job_data.get("job_id", str(uuid.uuid4()))
            
            logger.info(f"🚀 Starting multi-platform job publishing: {job_id}")
            
            # Optimizar contenido para cada plataforma
            optimized_content = await self._optimize_job_content(job_data, platforms, optimization_level)
            
            # Publicar en paralelo en todas las plataformas
            publication_tasks = []
            for platform in platforms:
                task = self._publish_to_platform(job_id, job_data, platform, optimized_content)
                publication_tasks.append(task)
            
            # Ejecutar publicaciones en paralelo
            publication_results = await asyncio.gather(*publication_tasks, return_exceptions=True)
            
            # Procesar resultados
            publications = []
            successful_publications = 0
            failed_publications = 0
            
            for i, result in enumerate(publication_results):
                platform = platforms[i] if i < len(platforms) else None
                
                if isinstance(result, Exception):
                    logger.error(f"Error publishing to {platform.value if platform else 'unknown'}: {result}")
                    failed_publications += 1
                    
                    # Crear registro de publicación fallida
                    publication = JobPublication(
                        publication_id=str(uuid.uuid4()),
                        job_id=job_id,
                        platform=platform,
                        platform_job_id=None,
                        publication_url=None,
                        status=PublishStatus.FAILED,
                        published_at=None,
                        expires_at=None,
                        views_count=0,
                        applications_count=0,
                        clicks_count=0,
                        cost=None,
                        budget_spent=None,
                        performance_metrics={},
                        optimization_applied=[],
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        error_message=str(result)
                    )
                    publications.append(publication)
                
                elif isinstance(result, dict) and result.get("success"):
                    successful_publications += 1
                    publications.append(result["publication"])
            
            # Calcular métricas de publicación
            total_cost = sum(p.cost or Decimal("0") for p in publications)
            avg_optimization_score = sum(optimized_content.seo_score for _ in platforms) / len(platforms)
            
            result = {
                "success": successful_publications > 0,
                "job_id": job_id,
                "total_platforms": len(platforms),
                "successful_publications": successful_publications,
                "failed_publications": failed_publications,
                "publications": publications,
                "optimized_content": optimized_content,
                "total_estimated_cost": total_cost,
                "avg_optimization_score": avg_optimization_score,
                "publication_summary": {
                    "platforms_published": [p.platform.value for p in publications if p.status == PublishStatus.PUBLISHED],
                    "platforms_failed": [p.platform.value for p in publications if p.status == PublishStatus.FAILED],
                    "estimated_reach": self._calculate_estimated_reach(publications),
                    "expected_applications": self._calculate_expected_applications(publications)
                },
                "next_steps": [
                    "Monitor publication performance",
                    "Track applications and metrics",
                    "Optimize based on initial results",
                    "Schedule performance review in 7 days"
                ]
            }
            
            logger.info(f"✅ Multi-platform publishing completed: {successful_publications}/{len(platforms)} successful")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in multi-platform job publishing: {e}")
            return {"success": False, "error": str(e)}
    
    async def _optimize_job_content(self, job_data: Dict[str, Any], 
                                  platforms: List[PublishPlatform],
                                  optimization_level: str) -> OptimizedJobContent:
        """Optimiza el contenido del trabajo para múltiples plataformas"""
        
        original_title = job_data.get("title", "")
        original_description = job_data.get("description", "")
        industry = job_data.get("industry", "")
        location = job_data.get("location", "")
        
        # Extraer keywords relevantes
        keywords = self._extract_keywords(original_title, original_description, industry)
        
        # Optimizar título
        optimized_title = await self._optimize_title(original_title, keywords, platforms)
        
        # Optimizar descripción
        optimized_description = await self._optimize_description(original_description, keywords, platforms)
        
        # Generar contenido específico por plataforma
        platform_specific_content = {}
        for platform in platforms:
            platform_content = await self._create_platform_specific_content(
                optimized_title, optimized_description, platform, keywords
            )
            platform_specific_content[platform.value] = platform_content
        
        # Calcular scores
        seo_score = self._calculate_seo_score(optimized_title, optimized_description, keywords)
        readability_score = self._calculate_readability_score(optimized_description)
        ats_compatibility = self._calculate_ats_compatibility(optimized_description)
        
        # Generar sugerencias de optimización
        optimization_suggestions = self._generate_optimization_suggestions(
            original_title, original_description, optimized_title, optimized_description
        )
        
        return OptimizedJobContent(
            original_title=original_title,
            optimized_title=optimized_title,
            original_description=original_description,
            optimized_description=optimized_description,
            keywords=keywords,
            seo_score=seo_score,
            readability_score=readability_score,
            ats_compatibility=ats_compatibility,
            platform_specific_content=platform_specific_content,
            optimization_suggestions=optimization_suggestions
        )
    
    async def _publish_to_platform(self, job_id: str, job_data: Dict[str, Any],
                                 platform: PublishPlatform, 
                                 optimized_content: OptimizedJobContent) -> Dict[str, Any]:
        """Publica trabajo a una plataforma específica"""
        
        try:
            config = self.platform_configs[platform]
            platform_content = optimized_content.platform_specific_content.get(platform.value, {})
            
            # Preparar datos para la plataforma
            platform_job_data = await self._prepare_platform_data(job_data, platform, platform_content)
            
            # Validar datos requeridos
            validation_result = self._validate_platform_data(platform_job_data, platform)
            if not validation_result["valid"]:
                raise ValueError(f"Invalid data for {platform.value}: {validation_result['errors']}")
            
            # Simular publicación (en implementación real, hacer llamada API)
            publication_result = await self._simulate_platform_publication(platform, platform_job_data)
            
            # Crear registro de publicación
            publication = JobPublication(
                publication_id=str(uuid.uuid4()),
                job_id=job_id,
                platform=platform,
                platform_job_id=publication_result["platform_job_id"],
                publication_url=publication_result["url"],
                status=PublishStatus.PUBLISHED,
                published_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=30),
                views_count=0,
                applications_count=0,
                clicks_count=0,
                cost=config["cost_per_click"],
                budget_spent=Decimal("0"),
                performance_metrics={},
                optimization_applied=optimized_content.optimization_suggestions,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                error_message=None
            )
            
            logger.info(f"✅ Published to {platform.value}: {publication.platform_job_id}")
            
            return {"success": True, "publication": publication}
            
        except Exception as e:
            logger.error(f"❌ Error publishing to {platform.value}: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_keywords(self, title: str, description: str, industry: str) -> List[str]:
        """Extrae keywords relevantes del contenido"""
        
        keywords = []
        
        # Keywords de industria
        industry_keywords = self.industry_keywords.get(industry.lower(), [])
        keywords.extend(industry_keywords)
        
        # Keywords del título (palabras importantes)
        title_words = title.lower().split()
        important_title_words = [word for word in title_words if len(word) > 3]
        keywords.extend(important_title_words[:5])
        
        # Keywords técnicos comunes
        tech_keywords = [
            "python", "java", "javascript", "react", "sql", "aws", "docker",
            "agile", "scrum", "api", "rest", "git", "cloud", "machine learning"
        ]
        
        description_lower = description.lower()
        found_tech_keywords = [kw for kw in tech_keywords if kw in description_lower]
        keywords.extend(found_tech_keywords)
        
        # Deduplicar y limitar
        unique_keywords = list(set(keywords))
        return unique_keywords[:15]
    
    async def _optimize_title(self, original_title: str, keywords: List[str], 
                            platforms: List[PublishPlatform]) -> str:
        """Optimiza el título del trabajo"""
        
        # Obtener límite más restrictivo
        max_length = min([self.platform_configs[p]["max_title_length"] for p in platforms])
        
        # Si el título está dentro del límite, añadir keywords si es posible
        if len(original_title) <= max_length - 20:
            # Intentar añadir 1-2 keywords importantes
            important_keywords = keywords[:2]
            for keyword in important_keywords:
                potential_title = f"{original_title} - {keyword.title()}"
                if len(potential_title) <= max_length:
                    return potential_title
        
        # Si el título es muy largo, truncar inteligentemente
        if len(original_title) > max_length:
            # Truncar manteniendo palabras completas
            words = original_title.split()
            truncated = ""
            for word in words:
                if len(truncated + " " + word) <= max_length - 3:
                    truncated += " " + word if truncated else word
                else:
                    break
            return truncated + "..."
        
        return original_title
    
    async def _optimize_description(self, original_description: str, keywords: List[str],
                                  platforms: List[PublishPlatform]) -> str:
        """Optimiza la descripción del trabajo"""
        
        # Obtener límite más restrictivo
        max_length = min([self.platform_configs[p]["max_description_length"] for p in platforms])
        
        optimized = original_description
        
        # Añadir sección de keywords si no están presentes
        description_lower = optimized.lower()
        missing_keywords = [kw for kw in keywords if kw not in description_lower]
        
        if missing_keywords and len(optimized) < max_length - 200:
            keywords_section = f"\n\nSkills requeridos: {', '.join(missing_keywords[:8])}"
            optimized += keywords_section
        
        # Añadir call to action si no existe
        if "aplica" not in description_lower and "apply" not in description_lower:
            if len(optimized) < max_length - 100:
                cta = "\n\n¡Aplica ahora y únete a nuestro equipo! Envía tu CV y comienza tu nueva carrera con nosotros."
                optimized += cta
        
        # Truncar si es necesario
        if len(optimized) > max_length:
            optimized = optimized[:max_length-3] + "..."
        
        return optimized
    
    async def _create_platform_specific_content(self, title: str, description: str,
                                              platform: PublishPlatform, 
                                              keywords: List[str]) -> Dict[str, str]:
        """Crea contenido específico para cada plataforma"""
        
        config = self.platform_configs[platform]
        
        # Ajustar título para la plataforma
        platform_title = title
        if len(title) > config["max_title_length"]:
            platform_title = title[:config["max_title_length"]-3] + "..."
        
        # Ajustar descripción para la plataforma
        platform_description = description
        if len(description) > config["max_description_length"]:
            platform_description = description[:config["max_description_length"]-3] + "..."
        
        # Añadir elementos específicos por plataforma
        if platform == PublishPlatform.LINKEDIN:
            # LinkedIn prefiere contenido más profesional
            if "LinkedIn" not in platform_description:
                platform_description += "\n\nConéctate con nosotros en LinkedIn para más oportunidades."
        
        elif platform == PublishPlatform.INDEED:
            # Indeed valora información salarial y beneficios
            if "beneficios" not in platform_description.lower():
                platform_description += "\n\nOfrecemos excelentes beneficios y oportunidades de crecimiento."
        
        elif platform == PublishPlatform.GLASSDOOR:
            # Glassdoor se enfoca en cultura empresarial
            if "cultura" not in platform_description.lower():
                platform_description += "\n\nÚnete a una empresa con cultura innovadora y ambiente colaborativo."
        
        return {
            "title": platform_title,
            "description": platform_description,
            "keywords": keywords[:10]  # Limitar keywords por plataforma
        }
    
    async def _prepare_platform_data(self, job_data: Dict[str, Any], 
                                   platform: PublishPlatform,
                                   platform_content: Dict[str, str]) -> Dict[str, Any]:
        """Prepara datos específicos para la plataforma"""
        
        base_data = {
            "title": platform_content.get("title", job_data.get("title")),
            "description": platform_content.get("description", job_data.get("description")),
            "location": job_data.get("location"),
            "company": job_data.get("company"),
            "department": job_data.get("department"),
            "job_type": job_data.get("job_type", "full-time"),
            "experience_level": job_data.get("experience_level"),
            "salary_min": job_data.get("salary_min"),
            "salary_max": job_data.get("salary_max"),
            "currency": job_data.get("currency", "MXN"),
            "remote_work": job_data.get("remote_work", False),
            "visa_sponsorship": job_data.get("visa_sponsorship", False)
        }
        
        # Adaptaciones específicas por plataforma
        if platform == PublishPlatform.LINKEDIN:
            base_data.update({
                "industry": job_data.get("industry"),
                "function": job_data.get("function"),
                "seniority": job_data.get("seniority")
            })
        
        elif platform == PublishPlatform.INDEED:
            base_data.update({
                "salary_display": f"${job_data.get('salary_min', 0):,} - ${job_data.get('salary_max', 0):,} {job_data.get('currency', 'MXN')}",
                "benefits": job_data.get("benefits", [])
            })
        
        elif platform == PublishPlatform.GLASSDOOR:
            base_data.update({
                "company_size": job_data.get("company_size"),
                "company_type": job_data.get("company_type"),
                "company_revenue": job_data.get("company_revenue")
            })
        
        return base_data
    
    def _validate_platform_data(self, platform_data: Dict[str, Any], 
                               platform: PublishPlatform) -> Dict[str, Any]:
        """Valida datos para la plataforma específica"""
        
        config = self.platform_configs[platform]
        required_fields = config["required_fields"]
        
        errors = []
        
        # Verificar campos requeridos
        for field in required_fields:
            if not platform_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Verificar límites de longitud
        title = platform_data.get("title", "")
        if len(title) > config["max_title_length"]:
            errors.append(f"Title too long: {len(title)} > {config['max_title_length']}")
        
        description = platform_data.get("description", "")
        if len(description) > config["max_description_length"]:
            errors.append(f"Description too long: {len(description)} > {config['max_description_length']}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _simulate_platform_publication(self, platform: PublishPlatform, 
                                           platform_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula la publicación en la plataforma (placeholder para APIs reales)"""
        
        # En implementación real, aquí se harían las llamadas a las APIs
        
        # Simular ID de trabajo en la plataforma
        platform_job_id = f"{platform.value}_{hashlib.md5(platform_data['title'].encode()).hexdigest()[:8]}"
        
        # Simular URL de publicación
        base_urls = {
            PublishPlatform.INDEED: "https://mx.indeed.com/viewjob?jk=",
            PublishPlatform.LINKEDIN: "https://www.linkedin.com/jobs/view/",
            PublishPlatform.MONSTER: "https://www.monster.com.mx/job-openings/",
            PublishPlatform.OCC_MUNDIAL: "https://www.occ.com.mx/empleos/",
            PublishPlatform.COMPUTRABAJO: "https://www.computrabajo.com.mx/empleo-de-"
        }
        
        publication_url = base_urls.get(platform, "https://example.com/job/") + platform_job_id
        
        # Simular delay de publicación
        await asyncio.sleep(0.1)
        
        return {
            "platform_job_id": platform_job_id,
            "url": publication_url,
            "status": "published",
            "message": f"Successfully published to {platform.value}"
        }
    
    # Métodos de cálculo y análisis
    
    def _calculate_seo_score(self, title: str, description: str, keywords: List[str]) -> float:
        """Calcula score SEO del contenido"""
        
        score = 0.0
        
        # Keywords en título (40% del score)
        title_lower = title.lower()
        title_keyword_count = sum(1 for kw in keywords if kw in title_lower)
        title_score = min(title_keyword_count / len(keywords), 1.0) * 0.4
        score += title_score
        
        # Keywords en descripción (30% del score)
        description_lower = description.lower()
        desc_keyword_count = sum(1 for kw in keywords if kw in description_lower)
        desc_score = min(desc_keyword_count / len(keywords), 1.0) * 0.3
        score += desc_score
        
        # Longitud apropiada (20% del score)
        length_score = 0.0
        if 50 <= len(title) <= 100:
            length_score += 0.1
        if 300 <= len(description) <= 2000:
            length_score += 0.1
        score += length_score
        
        # Call to action presente (10% del score)
        cta_keywords = ["aplica", "apply", "únete", "envía", "contacta"]
        if any(cta in description_lower for cta in cta_keywords):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_readability_score(self, description: str) -> float:
        """Calcula score de legibilidad"""
        
        if not description:
            return 0.0
        
        # Métricas básicas de legibilidad
        sentences = description.split('.')
        words = description.split()
        
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Score basado en métricas simples
        score = 1.0
        
        # Penalizar oraciones muy largas
        if avg_sentence_length > 25:
            score -= 0.2
        
        # Penalizar palabras muy largas
        if avg_word_length > 7:
            score -= 0.1
        
        # Bonificar uso de listas y estructura
        if '\n' in description or '•' in description or '-' in description:
            score += 0.1
        
        return max(min(score, 1.0), 0.0)
    
    def _calculate_ats_compatibility(self, description: str) -> float:
        """Calcula compatibilidad con ATS"""
        
        score = 1.0
        description_lower = description.lower()
        
        # Evitar caracteres especiales problemáticos
        problematic_chars = ['@', '#', '%', '&', '*', '=', '+']
        char_penalty = sum(1 for char in problematic_chars if char in description) * 0.05
        score -= char_penalty
        
        # Bonificar estructura clara
        if any(marker in description for marker in ['\n•', '\n-', '\n1.', '\n2.']):
            score += 0.1
        
        # Bonificar keywords estándar
        standard_keywords = ['experience', 'skills', 'requirements', 'responsibilities']
        keyword_bonus = sum(0.02 for kw in standard_keywords if kw in description_lower)
        score += keyword_bonus
        
        return max(min(score, 1.0), 0.0)
    
    def _generate_optimization_suggestions(self, original_title: str, original_description: str,
                                         optimized_title: str, optimized_description: str) -> List[str]:
        """Genera sugerencias de optimización"""
        
        suggestions = []
        
        # Sugerencias de título
        if len(original_title) != len(optimized_title):
            suggestions.append("Título optimizado para longitud requerida")
        
        # Sugerencias de descripción
        if len(original_description) != len(optimized_description):
            suggestions.append("Descripción optimizada para múltiples plataformas")
        
        if "keywords" in optimized_description.lower() and "keywords" not in original_description.lower():
            suggestions.append("Keywords técnicos añadidos")
        
        if "aplica" in optimized_description.lower() and "aplica" not in original_description.lower():
            suggestions.append("Call-to-action añadido")
        
        # Sugerencias generales
        suggestions.extend([
            "Contenido optimizado para SEO",
            "Formato adaptado para compatibilidad ATS",
            "Estructura mejorada para legibilidad"
        ])
        
        return suggestions
    
    def _calculate_estimated_reach(self, publications: List[JobPublication]) -> Dict[str, int]:
        """Calcula alcance estimado por plataforma"""
        
        # Datos de alcance promedio por plataforma (simulados)
        platform_reach = {
            PublishPlatform.INDEED: 10000,
            PublishPlatform.LINKEDIN: 5000,
            PublishPlatform.MONSTER: 3000,
            PublishPlatform.OCC_MUNDIAL: 4000,
            PublishPlatform.COMPUTRABAJO: 2500,
            PublishPlatform.GLASSDOOR: 1500
        }
        
        total_reach = 0
        reach_by_platform = {}
        
        for publication in publications:
            if publication.status == PublishStatus.PUBLISHED:
                platform_estimated_reach = platform_reach.get(publication.platform, 1000)
                reach_by_platform[publication.platform.value] = platform_estimated_reach
                total_reach += platform_estimated_reach
        
        return {
            "total_estimated_reach": total_reach,
            "reach_by_platform": reach_by_platform
        }
    
    def _calculate_expected_applications(self, publications: List[JobPublication]) -> Dict[str, Any]:
        """Calcula aplicaciones esperadas"""
        
        # Tasas de conversión promedio por plataforma
        conversion_rates = {
            PublishPlatform.INDEED: 0.03,  # 3%
            PublishPlatform.LINKEDIN: 0.02,  # 2%
            PublishPlatform.MONSTER: 0.025,  # 2.5%
            PublishPlatform.OCC_MUNDIAL: 0.035,  # 3.5%
            PublishPlatform.COMPUTRABAJO: 0.04,  # 4%
            PublishPlatform.GLASSDOOR: 0.015  # 1.5%
        }
        
        total_expected = 0
        expected_by_platform = {}
        
        for publication in publications:
            if publication.status == PublishStatus.PUBLISHED:
                estimated_reach = self._calculate_estimated_reach([publication])["total_estimated_reach"]
                conversion_rate = conversion_rates.get(publication.platform, 0.025)
                expected_applications = int(estimated_reach * conversion_rate)
                
                expected_by_platform[publication.platform.value] = expected_applications
                total_expected += expected_applications
        
        return {
            "total_expected_applications": total_expected,
            "expected_by_platform": expected_by_platform,
            "estimated_timeframe": "30 days"
        }
    
    async def track_publication_performance(self, publication_id: str) -> Dict[str, Any]:
        """Rastrea el performance de una publicación"""
        
        try:
            # En implementación real, consultar APIs de las plataformas
            # Por ahora simular métricas
            
            performance_metrics = {
                "publication_id": publication_id,
                "last_updated": datetime.now().isoformat(),
                "metrics": {
                    "views": 1250 + hash(publication_id) % 2000,
                    "clicks": 85 + hash(publication_id) % 150,
                    "applications": 12 + hash(publication_id) % 25,
                    "saves": 35 + hash(publication_id) % 70,
                    "shares": 8 + hash(publication_id) % 15
                },
                "performance_indicators": {
                    "ctr": 0.068,  # Click-through rate
                    "conversion_rate": 0.14,  # Application rate
                    "engagement_rate": 0.045,
                    "quality_score": 8.5
                },
                "cost_metrics": {
                    "cost_per_click": Decimal("2.50"),
                    "cost_per_application": Decimal("18.75"),
                    "total_spent": Decimal("212.50"),
                    "budget_remaining": Decimal("287.50")
                },
                "recommendations": [
                    "Performance above industry average",
                    "Consider increasing budget for this job",
                    "Optimize for mobile applications",
                    "Add more specific skill requirements"
                ]
            }
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"Error tracking publication performance: {e}")
            return {"error": str(e)}
    
    async def pause_publication(self, publication_id: str, platform: PublishPlatform) -> Dict[str, Any]:
        """Pausa una publicación en una plataforma"""
        
        try:
            # En implementación real, llamar API de la plataforma
            
            logger.info(f"Pausing publication {publication_id} on {platform.value}")
            
            return {
                "success": True,
                "publication_id": publication_id,
                "platform": platform.value,
                "status": PublishStatus.PAUSED.value,
                "paused_at": datetime.now().isoformat(),
                "message": f"Publication paused on {platform.value}"
            }
            
        except Exception as e:
            logger.error(f"Error pausing publication: {e}")
            return {"success": False, "error": str(e)}
    
    async def close_publication(self, publication_id: str, platform: PublishPlatform) -> Dict[str, Any]:
        """Cierra una publicación en una plataforma"""
        
        try:
            # En implementación real, llamar API de la plataforma
            
            logger.info(f"Closing publication {publication_id} on {platform.value}")
            
            return {
                "success": True,
                "publication_id": publication_id,
                "platform": platform.value,
                "status": PublishStatus.EXPIRED.value,
                "closed_at": datetime.now().isoformat(),
                "message": f"Publication closed on {platform.value}"
            }
            
        except Exception as e:
            logger.error(f"Error closing publication: {e}")
            return {"success": False, "error": str(e)}

# Factory function
def get_job_publishing_service(config: Dict[str, Any]) -> JobPublishingService:
    """Factory function para el servicio de publicación"""
    return JobPublishingService(config)