# app/ml/analyzers/linkedin_profile_analyzer.py
"""
LinkedIn Profile Analyzer - Analizador avanzado de perfiles de LinkedIn
Integra extracción robusta, anti-detección y análisis de datos de perfiles.
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from urllib.parse import urlparse

# Django imports
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone as django_timezone

# Local imports
from app.models import Person, BusinessUnit, USER_AGENTS
from app.ats.utils.linkedin import (
    scrape_linkedin_profile,
    scrape_with_selenium,
    extract_skills,
    normalize_skills,
    associate_divisions,
    update_person_from_scrape
)
from app.config.api_config import LINKEDIN_CONFIG
from app.ats.utils.monitoring.monitoring import monitor_linkedin_request, track_scrape_duration

# Playwright imports
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logger = logging.getLogger(__name__)


@dataclass
class LinkedInProfileData:
    """Estructura de datos para información de perfil de LinkedIn."""
    profile_url: str
    personal_info: Dict[str, Any]
    about: Optional[str]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: List[str]
    contact_info: Dict[str, Any]
    languages: List[str]
    certifications: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    publications: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    volunteer_experience: List[Dict[str, Any]]
    honors_awards: List[Dict[str, Any]]
    organizations: List[Dict[str, Any]]
    scraped_at: datetime
    metadata: Dict[str, Any]


class LinkedInProfileAnalyzer:
    """
    Analizador avanzado de perfiles de LinkedIn con capacidades de:
    - Extracción robusta con anti-detección
    - Rotación de user agents
    - Análisis de datos extraídos
    - Enriquecimiento de modelos Person
    - Cache inteligente
    """
    
    def __init__(self, business_unit: Optional[BusinessUnit] = None):
        self.business_unit = business_unit
        self.user_agents = USER_AGENTS
        self.session_count = 0
        self.last_request_time = 0
        self.min_delay = LINKEDIN_CONFIG.get('MIN_DELAY', 8)
        self.max_delay = LINKEDIN_CONFIG.get('MAX_DELAY', 18)
        
    def _get_random_user_agent(self) -> str:
        """Obtiene un user agent aleatorio de la lista configurada."""
        return random.choice(self.user_agents)
    
    def _calculate_delay(self) -> float:
        """Calcula un delay aleatorio entre requests para evitar detección."""
        return random.uniform(self.min_delay, self.max_delay)
    
    async def _respect_rate_limits(self):
        """Respeta límites de rate para evitar bloqueos."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            delay_needed = self._calculate_delay() - time_since_last
            if delay_needed > 0:
                logger.info(f"Esperando {delay_needed:.2f}s para respetar rate limits")
                await asyncio.sleep(delay_needed)
        
        self.last_request_time = time.time()
    
    def _generate_cache_key(self, profile_url: str) -> str:
        """Genera una clave única para el cache."""
        import hashlib
        return f"linkedin_profile_{hashlib.md5(profile_url.encode()).hexdigest()}"
    
    @monitor_linkedin_request
    @track_scrape_duration()
    async def analyze_profile(
        self, 
        profile_url: str, 
        force_refresh: bool = False,
        extract_contact: bool = True
    ) -> Optional[LinkedInProfileData]:
        """
        Analiza un perfil de LinkedIn y devuelve datos estructurados.
        
        Args:
            profile_url: URL del perfil de LinkedIn
            force_refresh: Si True, ignora el cache
            extract_contact: Si True, intenta extraer información de contacto
            
        Returns:
            LinkedInProfileData con toda la información extraída
        """
        if not profile_url or 'linkedin.com/in/' not in profile_url:
            logger.error(f"URL de LinkedIn no válida: {profile_url}")
            return None
        
        # Normalizar URL
        if not profile_url.startswith(('http://', 'https://')):
            profile_url = f"https://{profile_url}"
        
        # Verificar cache
        cache_key = self._generate_cache_key(profile_url)
        if not force_refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Datos en cache encontrados para {profile_url}")
                return LinkedInProfileData(**cached_data)
        
        # Respeta rate limits
        await self._respect_rate_limits()
        
        # Determinar unidad de negocio
        unit = self.business_unit.name.lower() if self.business_unit else "default"
        
        try:
            # Extraer datos usando la lógica robusta existente
            raw_data = await scrape_linkedin_profile(profile_url, unit)
            
            if not raw_data:
                logger.warning(f"No se pudieron extraer datos de {profile_url}")
                return None
            
            # Procesar y estructurar los datos
            profile_data = self._process_raw_data(raw_data, profile_url)
            
            # Guardar en cache
            cache_timeout = LINKEDIN_CONFIG.get('CACHE_TIMEOUT', 60*60*24)  # 24 horas
            if cache_timeout > 0:
                cache.set(cache_key, profile_data.__dict__, timeout=cache_timeout)
            
            self.session_count += 1
            logger.info(f"Perfil analizado exitosamente: {profile_url}")
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Error analizando perfil {profile_url}: {str(e)}", exc_info=True)
            return None
    
    def _process_raw_data(self, raw_data: Dict[str, Any], profile_url: str) -> LinkedInProfileData:
        """Procesa los datos raw extraídos y los estructura."""
        return LinkedInProfileData(
            profile_url=profile_url,
            personal_info=raw_data.get('personal_info', {}),
            about=raw_data.get('about'),
            experience=raw_data.get('experience', []),
            education=raw_data.get('education', []),
            skills=raw_data.get('skills', []),
            contact_info=raw_data.get('contact_info', {}),
            languages=raw_data.get('languages', []),
            certifications=raw_data.get('certifications', []),
            recommendations=raw_data.get('recommendations', []),
            publications=raw_data.get('publications', []),
            projects=raw_data.get('projects', []),
            volunteer_experience=raw_data.get('volunteer_experience', []),
            honors_awards=raw_data.get('honors_awards', []),
            organizations=raw_data.get('organizations', []),
            scraped_at=datetime.now(timezone.utc),
            metadata=raw_data.get('metadata', {})
        )
    
    async def enrich_person(
        self, 
        person: Person, 
        profile_data: LinkedInProfileData,
        update_existing: bool = True
    ) -> bool:
        """
        Enriquece un modelo Person con datos del perfil de LinkedIn.
        
        Args:
            person: Instancia de Person a enriquecer
            profile_data: Datos del perfil extraídos
            update_existing: Si True, actualiza campos existentes
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            with transaction.atomic():
                updated = False
                
                # Actualizar información básica si no existe o si update_existing=True
                if profile_data.personal_info.get('name') and (not person.nombre or update_existing):
                    person.nombre = profile_data.personal_info['name']
                    updated = True
                
                if profile_data.personal_info.get('headline') and (not person.metadata.get('headline') or update_existing):
                    person.metadata['headline'] = profile_data.personal_info['headline']
                    updated = True
                
                # Actualizar LinkedIn URL si no existe
                if not person.linkedin_url:
                    person.linkedin_url = profile_data.profile_url
                    updated = True
                
                # Actualizar información de contacto
                if profile_data.contact_info:
                    if profile_data.contact_info.get('email') and (not person.email or update_existing):
                        person.email = profile_data.contact_info['email']
                        updated = True
                    
                    if profile_data.contact_info.get('phone') and (not person.phone or update_existing):
                        person.phone = profile_data.contact_info['phone']
                        updated = True
                
                # Actualizar skills
                if profile_data.skills:
                    existing_skills = person.metadata.get('skills', [])
                    new_skills = list(set(existing_skills + profile_data.skills))
                    if new_skills != existing_skills:
                        person.metadata['skills'] = new_skills
                        person.skills = ', '.join(new_skills)
                        updated = True
                
                # Actualizar experiencia
                if profile_data.experience:
                    person.metadata['linkedin_experience'] = profile_data.experience
                    updated = True
                
                # Actualizar educación
                if profile_data.education:
                    person.metadata['linkedin_education'] = profile_data.education
                    updated = True
                
                # Actualizar información adicional
                person.metadata.update({
                    'linkedin_about': profile_data.about,
                    'linkedin_languages': profile_data.languages,
                    'linkedin_certifications': profile_data.certifications,
                    'linkedin_recommendations': profile_data.recommendations,
                    'linkedin_publications': profile_data.publications,
                    'linkedin_projects': profile_data.projects,
                    'linkedin_volunteer': profile_data.volunteer_experience,
                    'linkedin_honors': profile_data.honors_awards,
                    'linkedin_organizations': profile_data.organizations,
                    'linkedin_last_updated': django_timezone.now().isoformat(),
                    'linkedin_analysis_metadata': profile_data.metadata
                })
                
                if updated:
                    person.save()
                    logger.info(f"Persona enriquecida exitosamente: {person.nombre}")
                
                return updated
                
        except Exception as e:
            logger.error(f"Error enriqueciendo persona {person.nombre}: {str(e)}", exc_info=True)
            return False
    
    async def analyze_multiple_profiles(
        self, 
        profile_urls: List[str], 
        max_concurrent: int = 3
    ) -> List[Optional[LinkedInProfileData]]:
        """
        Analiza múltiples perfiles de LinkedIn de forma concurrente.
        
        Args:
            profile_urls: Lista de URLs de perfiles
            max_concurrent: Número máximo de requests concurrentes
            
        Returns:
            Lista de LinkedInProfileData (None para errores)
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_single(url: str) -> Optional[LinkedInProfileData]:
            async with semaphore:
                return await self.analyze_profile(url)
        
        tasks = [analyze_single(url) for url in profile_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error en análisis concurrente: {str(result)}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    def analyze_skills_distribution(self, profile_data: LinkedInProfileData) -> Dict[str, Any]:
        """
        Analiza la distribución de habilidades del perfil.
        
        Args:
            profile_data: Datos del perfil
            
        Returns:
            Análisis de distribución de habilidades
        """
        skills = profile_data.skills
        
        # Análisis básico
        analysis = {
            'total_skills': len(skills),
            'unique_skills': len(set(skills)),
            'skill_categories': {},
            'top_skills': [],
            'skill_frequency': {}
        }
        
        if not skills:
            return analysis
        
        # Contar frecuencia de habilidades
        skill_counts = {}
        for skill in skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Top skills
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        analysis['top_skills'] = sorted_skills[:10]
        analysis['skill_frequency'] = skill_counts
        
        # Categorizar habilidades (implementación básica)
        technical_keywords = ['python', 'java', 'javascript', 'sql', 'react', 'node.js', 'aws', 'docker']
        soft_keywords = ['leadership', 'communication', 'teamwork', 'problem solving', 'project management']
        
        technical_count = sum(1 for skill in skills if any(keyword in skill.lower() for keyword in technical_keywords))
        soft_count = sum(1 for skill in skills if any(keyword in skill.lower() for keyword in soft_keywords))
        
        analysis['skill_categories'] = {
            'technical': technical_count,
            'soft_skills': soft_count,
            'other': len(skills) - technical_count - soft_count
        }
        
        return analysis
    
    def analyze_experience_trends(self, profile_data: LinkedInProfileData) -> Dict[str, Any]:
        """
        Analiza tendencias en la experiencia laboral.
        
        Args:
            profile_data: Datos del perfil
            
        Returns:
            Análisis de tendencias de experiencia
        """
        experience = profile_data.experience
        
        analysis = {
            'total_positions': len(experience),
            'current_position': None,
            'average_duration': 0,
            'career_progression': [],
            'industries': {},
            'companies': {}
        }
        
        if not experience:
            return analysis
        
        # Analizar cada posición
        total_duration = 0
        for exp in experience:
            # Duración de la posición
            start_date = exp.get('start_date')
            end_date = exp.get('end_date')
            is_current = exp.get('is_current', False)
            
            if is_current:
                analysis['current_position'] = exp
            
            # Contar industrias y empresas
            industry = exp.get('industry', 'Unknown')
            company = exp.get('company', 'Unknown')
            
            analysis['industries'][industry] = analysis['industries'].get(industry, 0) + 1
            analysis['companies'][company] = analysis['companies'].get(company, 0) + 1
        
        # Calcular duración promedio
        if experience:
            analysis['average_duration'] = total_duration / len(experience)
        
        return analysis
    
    def generate_profile_summary(self, profile_data: LinkedInProfileData) -> Dict[str, Any]:
        """
        Genera un resumen completo del perfil.
        
        Args:
            profile_data: Datos del perfil
            
        Returns:
            Resumen estructurado del perfil
        """
        skills_analysis = self.analyze_skills_distribution(profile_data)
        experience_analysis = self.analyze_experience_trends(profile_data)
        
        summary = {
            'profile_url': profile_data.profile_url,
            'personal_info': profile_data.personal_info,
            'headline': profile_data.personal_info.get('headline'),
            'about_summary': profile_data.about[:200] + '...' if profile_data.about and len(profile_data.about) > 200 else profile_data.about,
            'skills_summary': skills_analysis,
            'experience_summary': experience_analysis,
            'education_count': len(profile_data.education),
            'languages_count': len(profile_data.languages),
            'certifications_count': len(profile_data.certifications),
            'recommendations_count': len(profile_data.recommendations),
            'publications_count': len(profile_data.publications),
            'projects_count': len(profile_data.projects),
            'volunteer_count': len(profile_data.volunteer_experience),
            'scraped_at': profile_data.scraped_at.isoformat(),
            'metadata': profile_data.metadata
        }
        
        return summary
    
    async def find_or_create_person(
        self, 
        profile_data: LinkedInProfileData,
        business_unit: Optional[BusinessUnit] = None
    ) -> Optional[Person]:
        """
        Busca o crea una persona basada en los datos del perfil.
        
        Args:
            profile_data: Datos del perfil
            business_unit: Unidad de negocio (usa self.business_unit si no se proporciona)
            
        Returns:
            Instancia de Person encontrada o creada
        """
        if not business_unit:
            business_unit = self.business_unit
        
        if not business_unit:
            logger.error("No se proporcionó business_unit")
            return None
        
        try:
            # Buscar por LinkedIn URL
            if profile_data.profile_url:
                person = Person.objects.filter(linkedin_url=profile_data.profile_url).first()
                if person:
                    logger.info(f"Persona encontrada por LinkedIn URL: {person.nombre}")
                    return person
            
            # Buscar por nombre y email
            name = profile_data.personal_info.get('name', '')
            email = profile_data.contact_info.get('email')
            
            if name and email:
                person = Person.objects.filter(
                    nombre__iexact=name,
                    email__iexact=email
                ).first()
                if person:
                    logger.info(f"Persona encontrada por nombre y email: {person.nombre}")
                    return person
            
            # Crear nueva persona
            person_data = {
                'nombre': name,
                'email': email,
                'linkedin_url': profile_data.profile_url,
                'phone': profile_data.contact_info.get('phone'),
                'skills': ', '.join(profile_data.skills) if profile_data.skills else '',
                'metadata': {
                    'linkedin_headline': profile_data.personal_info.get('headline'),
                    'linkedin_about': profile_data.about,
                    'linkedin_experience': profile_data.experience,
                    'linkedin_education': profile_data.education,
                    'linkedin_languages': profile_data.languages,
                    'linkedin_certifications': profile_data.certifications,
                    'linkedin_recommendations': profile_data.recommendations,
                    'linkedin_publications': profile_data.publications,
                    'linkedin_projects': profile_data.projects,
                    'linkedin_volunteer': profile_data.volunteer_experience,
                    'linkedin_honors': profile_data.honors_awards,
                    'linkedin_organizations': profile_data.organizations,
                    'linkedin_analysis_metadata': profile_data.metadata,
                    'created_from_linkedin': True,
                    'linkedin_last_updated': django_timezone.now().isoformat()
                }
            }
            
            person = Person.objects.create(**person_data)
            logger.info(f"Nueva persona creada desde LinkedIn: {person.nombre}")
            
            return person
            
        except Exception as e:
            logger.error(f"Error buscando/creando persona: {str(e)}", exc_info=True)
            return None
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del analizador.
        
        Returns:
            Estadísticas de uso del analizador
        """
        return {
            'sessions_processed': self.session_count,
            'last_request_time': self.last_request_time,
            'business_unit': self.business_unit.name if self.business_unit else None,
            'user_agents_available': len(self.user_agents),
            'rate_limits': {
                'min_delay': self.min_delay,
                'max_delay': self.max_delay
            }
        }


# Funciones de conveniencia para uso directo
async def analyze_linkedin_profile(
    profile_url: str,
    business_unit: Optional[BusinessUnit] = None,
    enrich_person: bool = False
) -> Optional[Union[LinkedInProfileData, Person]]:
    """
    Función de conveniencia para analizar un perfil de LinkedIn.
    
    Args:
        profile_url: URL del perfil
        business_unit: Unidad de negocio
        enrich_person: Si True, busca/crea y enriquece una persona
        
    Returns:
        LinkedInProfileData o Person según enrich_person
    """
    analyzer = LinkedInProfileAnalyzer(business_unit)
    
    try:
        profile_data = await analyzer.analyze_profile(profile_url)
        
        if not profile_data:
            return None
        
        if enrich_person:
            person = await analyzer.find_or_create_person(profile_data, business_unit)
            if person:
                await analyzer.enrich_person(person, profile_data)
                return person
        
        return profile_data
        
    except Exception as e:
        logger.error(f"Error en análisis de perfil {profile_url}: {str(e)}", exc_info=True)
        return None


async def batch_analyze_profiles(
    profile_urls: List[str],
    business_unit: Optional[BusinessUnit] = None,
    max_concurrent: int = 3
) -> List[Optional[LinkedInProfileData]]:
    """
    Función de conveniencia para análisis en lote.
    
    Args:
        profile_urls: Lista de URLs
        business_unit: Unidad de negocio
        max_concurrent: Máximo de requests concurrentes
        
    Returns:
        Lista de LinkedInProfileData
    """
    analyzer = LinkedInProfileAnalyzer(business_unit)
    return await analyzer.analyze_multiple_profiles(profile_urls, max_concurrent) 