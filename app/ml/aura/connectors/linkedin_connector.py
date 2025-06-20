"""
Conector de LinkedIn para el Sistema Aura

Este módulo integra datos de LinkedIn para enriquecer la red de relaciones
profesionales y validar información del sistema principal.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import asyncio
import aiohttp
from urllib.parse import urlencode
import numpy as np

from app.models import Person, BusinessUnit

logger = logging.getLogger(__name__)

@dataclass
class LinkedInProfile:
    """Perfil de LinkedIn enriquecido."""
    linkedin_id: str
    person_id: int  # ID del sistema huntRED
    full_name: str
    headline: str
    current_company: Optional[str]
    current_position: Optional[str]
    location: Optional[str]
    industry: Optional[str]
    summary: Optional[str]
    connections_count: int
    verified: bool
    last_updated: datetime

@dataclass
class LinkedInExperience:
    """Experiencia laboral de LinkedIn."""
    company: str
    position: str
    start_date: Optional[date]
    end_date: Optional[date]
    duration_months: int
    description: Optional[str]
    verified: bool

@dataclass
class LinkedInConnection:
    """Conexión de LinkedIn."""
    connection_id: str
    name: str
    headline: str
    company: Optional[str]
    position: Optional[str]
    mutual_connections: int
    connection_strength: float  # 0-1

class LinkedInConnector:
    """
    Conector para integrar datos de LinkedIn con el sistema Aura.
    
    Enriquece la información del sistema principal con datos externos
    para construir una red de relaciones profesionales más completa.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el conector de LinkedIn.
        
        Args:
            api_key: Clave de API de LinkedIn (opcional para desarrollo)
        """
        self.api_key = api_key
        self.base_url = "https://api.linkedin.com/v2"
        self.session = None
        
        # Configuración de rate limiting
        self.rate_limit = 100  # requests per hour
        self.request_count = 0
        self.last_reset = datetime.now()
        
        logger.info("Conector de LinkedIn inicializado")
    
    async def enrich_person_data(
        self,
        person: Person,
        force_update: bool = False
    ) -> Optional[LinkedInProfile]:
        """
        Enriquece los datos de una persona con información de LinkedIn.
        
        Args:
            person: Persona del sistema huntRED
            force_update: Forzar actualización aunque ya exista
            
        Returns:
            Perfil de LinkedIn enriquecido
        """
        try:
            # Verificar si ya tenemos datos recientes
            if not force_update:
                existing_profile = await self._get_cached_profile(person.id)
                if existing_profile and self._is_profile_recent(existing_profile):
                    logger.info(f"Usando perfil en caché para persona {person.id}")
                    return existing_profile
            
            # Buscar perfil en LinkedIn
            linkedin_profile = await self._find_linkedin_profile(person)
            
            if linkedin_profile:
                # Enriquecer con datos adicionales
                await self._enrich_profile_data(linkedin_profile)
                
                # Guardar en caché
                await self._cache_profile(linkedin_profile)
                
                # Actualizar sistema principal
                await self._update_main_system(person, linkedin_profile)
                
                return linkedin_profile
            
            return None
            
        except Exception as e:
            logger.error(f"Error enriqueciendo datos de persona {person.id}: {str(e)}")
            return None
    
    async def find_professional_connections(
        self,
        person: Person,
        max_connections: int = 100
    ) -> List[LinkedInConnection]:
        """
        Encuentra conexiones profesionales de LinkedIn.
        
        Args:
            person: Persona del sistema huntRED
            max_connections: Máximo número de conexiones a obtener
            
        Returns:
            Lista de conexiones profesionales
        """
        try:
            # Obtener perfil de LinkedIn
            linkedin_profile = await self.enrich_person_data(person)
            
            if not linkedin_profile:
                return []
            
            # Obtener conexiones
            connections = await self._get_linkedin_connections(
                linkedin_profile.linkedin_id,
                max_connections
            )
            
            # Enriquecer conexiones con datos del sistema
            enriched_connections = await self._enrich_connections_data(connections)
            
            return enriched_connections
            
        except Exception as e:
            logger.error(f"Error obteniendo conexiones de LinkedIn: {str(e)}")
            return []
    
    async def validate_experience(
        self,
        person: Person,
        company: str,
        position: str,
        start_date: date,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Valida experiencia laboral usando LinkedIn.
        
        Args:
            person: Persona a validar
            company: Empresa
            position: Posición
            start_date: Fecha de inicio
            end_date: Fecha de fin (opcional)
            
        Returns:
            Resultado de validación
        """
        try:
            # Obtener perfil de LinkedIn
            linkedin_profile = await self.enrich_person_data(person)
            
            if not linkedin_profile:
                return {
                    'validated': False,
                    'confidence': 0.0,
                    'reason': 'No se encontró perfil de LinkedIn'
                }
            
            # Buscar experiencia en LinkedIn
            linkedin_experience = await self._find_experience_in_linkedin(
                linkedin_profile.linkedin_id,
                company,
                position,
                start_date,
                end_date
            )
            
            if linkedin_experience:
                return {
                    'validated': True,
                    'confidence': 0.9,
                    'source': 'linkedin',
                    'linkedin_data': linkedin_experience,
                    'verification_date': datetime.now().isoformat()
                }
            else:
                return {
                    'validated': False,
                    'confidence': 0.3,
                    'reason': 'Experiencia no encontrada en LinkedIn',
                    'verification_date': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error validando experiencia: {str(e)}")
            return {
                'validated': False,
                'confidence': 0.0,
                'reason': f'Error en validación: {str(e)}'
            }
    
    async def find_cross_references(
        self,
        person: Person,
        target_company: str,
        target_position: str
    ) -> List[Dict[str, Any]]:
        """
        Encuentra referencias cruzadas para validar experiencia.
        
        Args:
            person: Persona a validar
            target_company: Empresa objetivo
            target_position: Posición objetivo
            
        Returns:
            Lista de referencias cruzadas
        """
        try:
            # Obtener conexiones de LinkedIn
            connections = await self.find_professional_connections(person)
            
            # Filtrar conexiones que trabajaron en la empresa objetivo
            relevant_connections = []
            
            for connection in connections:
                if connection.company and target_company.lower() in connection.company.lower():
                    # Verificar si la conexión puede validar la experiencia
                    validation_potential = await self._assess_validation_potential(
                        connection, target_company, target_position
                    )
                    
                    if validation_potential > 0.5:
                        relevant_connections.append({
                            'connection': connection,
                            'validation_potential': validation_potential,
                            'validation_reason': self._get_validation_reason(connection, target_company)
                        })
            
            # Ordenar por potencial de validación
            relevant_connections.sort(key=lambda x: x['validation_potential'], reverse=True)
            
            return relevant_connections
            
        except Exception as e:
            logger.error(f"Error encontrando referencias cruzadas: {str(e)}")
            return []
    
    async def detect_network_hubs(
        self,
        person: Person
    ) -> List[Dict[str, Any]]:
        """
        Detecta hubs de red en las conexiones de LinkedIn.
        
        Args:
            person: Persona del sistema huntRED
            
        Returns:
            Lista de hubs detectados
        """
        try:
            # Obtener conexiones
            connections = await self.find_professional_connections(person, max_connections=200)
            
            # Analizar hubs basado en conexiones y mutual connections
            hubs = []
            
            for connection in connections:
                hub_score = self._calculate_hub_score(connection)
                
                if hub_score > 0.7:  # Umbral para considerar hub
                    hubs.append({
                        'connection': connection,
                        'hub_score': hub_score,
                        'hub_type': self._classify_hub_type(connection),
                        'recommendations': self._generate_hub_recommendations(connection)
                    })
            
            # Ordenar por score de hub
            hubs.sort(key=lambda x: x['hub_score'], reverse=True)
            
            return hubs[:10]  # Top 10 hubs
            
        except Exception as e:
            logger.error(f"Error detectando hubs de red: {str(e)}")
            return []
    
    async def _find_linkedin_profile(self, person: Person) -> Optional[LinkedInProfile]:
        """Busca el perfil de LinkedIn de una persona."""
        try:
            # Estrategia de búsqueda: nombre + empresa actual
            search_criteria = {
                'name': person.name,
                'company': getattr(person, 'current_company', None),
                'position': getattr(person, 'current_role', None)
            }
            
            # En una implementación real, esto haría una llamada a la API de LinkedIn
            # Por ahora, simulamos la búsqueda
            
            # Simular perfil encontrado
            if person.name and len(person.name.split()) >= 2:
                linkedin_profile = LinkedInProfile(
                    linkedin_id=f"linkedin_{person.id}",
                    person_id=person.id,
                    full_name=person.name,
                    headline=getattr(person, 'current_role', 'Professional'),
                    current_company=getattr(person, 'current_company', None),
                    current_position=getattr(person, 'current_role', None),
                    location=getattr(person, 'location', None),
                    industry='Technology',  # Default
                    summary=None,
                    connections_count=150,  # Simulado
                    verified=True,
                    last_updated=datetime.now()
                )
                
                return linkedin_profile
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando perfil de LinkedIn: {str(e)}")
            return None
    
    async def _enrich_profile_data(self, profile: LinkedInProfile) -> None:
        """Enriquece los datos del perfil con información adicional."""
        try:
            # Obtener experiencia laboral
            experience = await self._get_linkedin_experience(profile.linkedin_id)
            profile.metadata = {'experience': experience}
            
            # Obtener educación
            education = await self._get_linkedin_education(profile.linkedin_id)
            if 'metadata' not in profile.__dict__:
                profile.metadata = {}
            profile.metadata['education'] = education
            
            # Obtener habilidades
            skills = await self._get_linkedin_skills(profile.linkedin_id)
            profile.metadata['skills'] = skills
            
        except Exception as e:
            logger.error(f"Error enriqueciendo datos del perfil: {str(e)}")
    
    async def _get_linkedin_experience(self, linkedin_id: str) -> List[LinkedInExperience]:
        """Obtiene la experiencia laboral de LinkedIn."""
        # Simulación de experiencia
        return [
            LinkedInExperience(
                company="huntRED",
                position="Senior Developer",
                start_date=date(2022, 1, 1),
                end_date=None,
                duration_months=24,
                description="Desarrollo de aplicaciones web y móviles",
                verified=True
            ),
            LinkedInExperience(
                company="TechCorp",
                position="Developer",
                start_date=date(2020, 1, 1),
                end_date=date(2021, 12, 31),
                duration_months=24,
                description="Desarrollo frontend y backend",
                verified=True
            )
        ]
    
    async def _get_linkedin_education(self, linkedin_id: str) -> List[Dict[str, Any]]:
        """Obtiene la educación de LinkedIn."""
        return [
            {
                'institution': 'Universidad Tecnológica',
                'degree': 'Ingeniería en Sistemas',
                'field': 'Computer Science',
                'start_date': '2016',
                'end_date': '2020'
            }
        ]
    
    async def _get_linkedin_skills(self, linkedin_id: str) -> List[str]:
        """Obtiene las habilidades de LinkedIn."""
        return [
            'Python', 'JavaScript', 'React', 'Node.js', 'Django',
            'Machine Learning', 'Data Analysis', 'Agile', 'Git'
        ]
    
    async def _get_linkedin_connections(
        self,
        linkedin_id: str,
        max_connections: int
    ) -> List[LinkedInConnection]:
        """Obtiene las conexiones de LinkedIn."""
        # Simulación de conexiones
        connections = []
        
        for i in range(min(max_connections, 50)):  # Simular 50 conexiones
            connection = LinkedInConnection(
                connection_id=f"conn_{i}",
                name=f"Connection {i}",
                headline=f"Professional at Company {i}",
                company=f"Company {i}",
                position=f"Position {i}",
                mutual_connections=np.random.randint(5, 50),
                connection_strength=np.random.uniform(0.3, 1.0)
            )
            connections.append(connection)
        
        return connections
    
    async def _enrich_connections_data(
        self,
        connections: List[LinkedInConnection]
    ) -> List[LinkedInConnection]:
        """Enriquece los datos de las conexiones."""
        try:
            for connection in connections:
                # Verificar si la conexión existe en nuestro sistema
                system_person = await self._find_person_in_system(connection.name)
                
                if system_person:
                    connection.metadata = {
                        'in_system': True,
                        'system_id': system_person.id,
                        'system_role': system_person.current_role
                    }
                else:
                    connection.metadata = {
                        'in_system': False
                    }
            
            return connections
            
        except Exception as e:
            logger.error(f"Error enriqueciendo conexiones: {str(e)}")
            return connections
    
    async def _find_experience_in_linkedin(
        self,
        linkedin_id: str,
        company: str,
        position: str,
        start_date: date,
        end_date: Optional[date] = None
    ) -> Optional[LinkedInExperience]:
        """Busca experiencia específica en LinkedIn."""
        try:
            # Obtener toda la experiencia
            experience = await self._get_linkedin_experience(linkedin_id)
            
            # Buscar coincidencias
            for exp in experience:
                if (exp.company.lower() == company.lower() and
                    exp.position.lower() == position.lower()):
                    
                    # Verificar fechas
                    if exp.start_date == start_date:
                        if end_date is None or exp.end_date == end_date:
                            return exp
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando experiencia en LinkedIn: {str(e)}")
            return None
    
    async def _assess_validation_potential(
        self,
        connection: LinkedInConnection,
        target_company: str,
        target_position: str
    ) -> float:
        """Evalúa el potencial de validación de una conexión."""
        try:
            score = 0.0
            
            # Factor 1: Trabaja en la empresa objetivo
            if connection.company and target_company.lower() in connection.company.lower():
                score += 0.4
            
            # Factor 2: Posición similar
            if connection.position and target_position.lower() in connection.position.lower():
                score += 0.3
            
            # Factor 3: Conexión fuerte
            score += connection.connection_strength * 0.2
            
            # Factor 4: Muchas conexiones mutuas
            if connection.mutual_connections > 20:
                score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error evaluando potencial de validación: {str(e)}")
            return 0.0
    
    def _get_validation_reason(
        self,
        connection: LinkedInConnection,
        target_company: str
    ) -> str:
        """Obtiene la razón de validación."""
        reasons = []
        
        if connection.company and target_company.lower() in connection.company.lower():
            reasons.append(f"Trabaja en {connection.company}")
        
        if connection.position:
            reasons.append(f"Posición: {connection.position}")
        
        if connection.mutual_connections > 20:
            reasons.append(f"{connection.mutual_connections} conexiones mutuas")
        
        return "; ".join(reasons) if reasons else "Conexión profesional"
    
    def _calculate_hub_score(self, connection: LinkedInConnection) -> float:
        """Calcula el score de hub de una conexión."""
        try:
            score = 0.0
            
            # Factor 1: Número de conexiones mutuas
            mutual_score = min(1.0, connection.mutual_connections / 100)
            score += mutual_score * 0.4
            
            # Factor 2: Fuerza de conexión
            score += connection.connection_strength * 0.3
            
            # Factor 3: Posición en empresa reconocida
            if connection.company and len(connection.company) > 0:
                score += 0.2
            
            # Factor 4: Headline atractiva
            if connection.headline and len(connection.headline) > 10:
                score += 0.1
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculando score de hub: {str(e)}")
            return 0.0
    
    def _classify_hub_type(self, connection: LinkedInConnection) -> str:
        """Clasifica el tipo de hub."""
        if connection.mutual_connections > 50:
            return "super_connector"
        elif connection.mutual_connections > 30:
            return "connector"
        elif connection.connection_strength > 0.8:
            return "strong_tie"
        else:
            return "regular_connection"
    
    def _generate_hub_recommendations(self, connection: LinkedInConnection) -> List[str]:
        """Genera recomendaciones para un hub."""
        recommendations = []
        
        if connection.mutual_connections > 30:
            recommendations.append("Excelente para networking y referencias")
        
        if connection.connection_strength > 0.8:
            recommendations.append("Conexión fuerte para colaboraciones")
        
        if connection.company:
            recommendations.append(f"Puente hacia {connection.company}")
        
        return recommendations
    
    async def _find_person_in_system(self, name: str) -> Optional[Person]:
        """Busca una persona en el sistema principal."""
        try:
            # En una implementación real, esto consultaría la base de datos
            # Por ahora, retornamos None
            return None
        except Exception as e:
            logger.error(f"Error buscando persona en sistema: {str(e)}")
            return None
    
    async def _update_main_system(self, person: Person, linkedin_profile: LinkedInProfile) -> None:
        """Actualiza el sistema principal con datos de LinkedIn."""
        try:
            # En una implementación real, esto actualizaría la base de datos
            # Por ahora, solo registramos la actualización
            logger.info(f"Actualizando sistema principal con datos de LinkedIn para persona {person.id}")
            
        except Exception as e:
            logger.error(f"Error actualizando sistema principal: {str(e)}")
    
    async def _get_cached_profile(self, person_id: int) -> Optional[LinkedInProfile]:
        """Obtiene perfil en caché."""
        # Implementación básica de caché
        return None
    
    def _is_profile_recent(self, profile: LinkedInProfile) -> bool:
        """Verifica si el perfil es reciente."""
        # Considerar reciente si se actualizó en las últimas 24 horas
        return (datetime.now() - profile.last_updated).days < 1
    
    async def _cache_profile(self, profile: LinkedInProfile) -> None:
        """Guarda perfil en caché."""
        # Implementación básica de caché
        pass 