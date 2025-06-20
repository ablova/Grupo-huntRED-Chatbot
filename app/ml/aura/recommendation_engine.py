"""
Motor de Recomendaciones del Sistema Aura

Este módulo implementa el sistema de recomendaciones inteligentes que
genera sugerencias personalizadas basadas en el análisis de aura.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime, timedelta

from app.models import Person, Vacante, BusinessUnit

logger = logging.getLogger(__name__)

class RecommendationType(Enum):
    """Tipos de recomendaciones que puede generar el sistema."""
    CAREER_DEVELOPMENT = "career_development"
    SKILL_IMPROVEMENT = "skill_improvement"
    PERSONALITY_ENHANCEMENT = "personality_enhancement"
    CULTURAL_ADAPTATION = "cultural_adaptation"
    NETWORKING = "networking"
    LEARNING_PATH = "learning_path"
    ROLE_TRANSITION = "role_transition"
    TEAM_SYNERGY = "team_synergy"
    LEADERSHIP_GROWTH = "leadership_growth"
    WORK_LIFE_BALANCE = "work_life_balance"

class RecommendationPriority(Enum):
    """Prioridades de las recomendaciones."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Recommendation:
    """Estructura de una recomendación."""
    type: RecommendationType
    priority: RecommendationPriority
    title: str
    description: str
    action_items: List[str]
    expected_impact: float  # 0-100
    time_to_implement: str  # "short", "medium", "long"
    resources_needed: List[str]
    success_metrics: List[str]
    created_at: datetime

class RecommendationEngine:
    """
    Motor de recomendaciones inteligentes.
    
    Genera recomendaciones personalizadas basadas en el análisis
    de aura y el contexto específico de cada persona.
    """
    
    def __init__(self):
        """Inicializa el motor de recomendaciones."""
        self.recommendation_templates = self._load_recommendation_templates()
        self.impact_weights = {
            'skills': 0.25,
            'experience': 0.20,
            'personality': 0.15,
            'culture': 0.15,
            'network': 0.10,
            'leadership': 0.10,
            'balance': 0.05
        }
        
        logger.info("Motor de recomendaciones inicializado")
    
    async def generate_compatibility_recommendations(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any],
        compatibility_score: float
    ) -> List[str]:
        """
        Genera recomendaciones para mejorar la compatibilidad.
        
        Args:
            person_data: Datos de la persona
            vacancy_data: Datos de la vacante
            compatibility_score: Score de compatibilidad actual
            
        Returns:
            Lista de recomendaciones
        """
        try:
            recommendations = []
            
            # Análisis de gaps
            gaps = await self._identify_compatibility_gaps(person_data, vacancy_data)
            
            # Generar recomendaciones por gap
            for gap in gaps:
                gap_recommendations = await self._generate_gap_recommendations(gap)
                recommendations.extend(gap_recommendations)
            
            # Recomendaciones basadas en el score
            if compatibility_score < 60:
                recommendations.append("Considerar desarrollo adicional antes de aplicar")
            elif compatibility_score > 85:
                recommendations.append("Destacar fortalezas específicas en la entrevista")
            
            # Limitar a las mejores recomendaciones
            return recommendations[:5]
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones de compatibilidad: {str(e)}")
            return ["Completar perfil para recomendaciones más precisas"]
    
    async def generate_career_recommendations(
        self,
        person: Person,
        analysis_results: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Genera recomendaciones de carrera personalizadas.
        
        Args:
            person: Persona para generar recomendaciones
            analysis_results: Resultados del análisis de aura
            
        Returns:
            Lista de recomendaciones de carrera
        """
        try:
            person_data = await self._extract_person_data(person)
            
            recommendations = []
            
            # Análisis de trayectoria profesional
            career_analysis = await self._analyze_career_trajectory(person_data, analysis_results)
            
            # Generar recomendaciones por área de desarrollo
            for area, analysis in career_analysis.items():
                area_recommendations = await self._generate_area_recommendations(
                    area, analysis, person_data
                )
                recommendations.extend(area_recommendations)
            
            # Ordenar por prioridad e impacto
            recommendations.sort(
                key=lambda r: (self._get_priority_score(r.priority), r.expected_impact),
                reverse=True
            )
            
            return recommendations[:10]  # Top 10 recomendaciones
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones de carrera: {str(e)}")
            return []
    
    async def generate_team_recommendations(
        self,
        person: Person,
        analysis_results: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Genera recomendaciones para trabajo en equipo.
        
        Args:
            person: Persona para generar recomendaciones
            analysis_results: Resultados del análisis de aura
            
        Returns:
            Lista de recomendaciones de equipo
        """
        try:
            person_data = await self._extract_person_data(person)
            
            recommendations = []
            
            # Análisis de dinámicas de equipo
            team_analysis = await self._analyze_team_dynamics(person_data, analysis_results)
            
            # Generar recomendaciones específicas
            if team_analysis.get('collaboration_level', 0) < 70:
                recommendations.append(Recommendation(
                    type=RecommendationType.TEAM_SYNERGY,
                    priority=RecommendationPriority.HIGH,
                    title="Mejorar Habilidades de Colaboración",
                    description="Desarrollar capacidades de trabajo en equipo y comunicación efectiva",
                    action_items=[
                        "Participar en proyectos colaborativos",
                        "Tomar cursos de comunicación efectiva",
                        "Practicar feedback constructivo"
                    ],
                    expected_impact=85.0,
                    time_to_implement="medium",
                    resources_needed=["Cursos online", "Proyectos de equipo"],
                    success_metrics=["Feedback positivo de colegas", "Participación activa en equipos"],
                    created_at=datetime.now()
                ))
            
            if team_analysis.get('leadership_potential', 0) > 80:
                recommendations.append(Recommendation(
                    type=RecommendationType.LEADERSHIP_GROWTH,
                    priority=RecommendationPriority.MEDIUM,
                    title="Desarrollar Liderazgo de Equipo",
                    description="Aprovechar el potencial de liderazgo para roles de gestión",
                    action_items=[
                        "Buscar oportunidades de liderar proyectos",
                        "Mentorear colegas junior",
                        "Tomar cursos de gestión de equipos"
                    ],
                    expected_impact=90.0,
                    time_to_implement="long",
                    resources_needed=["Programas de liderazgo", "Experiencia práctica"],
                    success_metrics=["Liderazgo exitoso de proyectos", "Promoción a roles de gestión"],
                    created_at=datetime.now()
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones de equipo: {str(e)}")
            return []
    
    async def generate_learning_recommendations(
        self,
        person: Person,
        skill_gaps: List[str],
        learning_style: str = "mixed"
    ) -> List[Recommendation]:
        """
        Genera recomendaciones de aprendizaje personalizadas.
        
        Args:
            person: Persona para generar recomendaciones
            skill_gaps: Lista de habilidades a desarrollar
            learning_style: Estilo de aprendizaje preferido
            
        Returns:
            Lista de recomendaciones de aprendizaje
        """
        try:
            recommendations = []
            
            for skill in skill_gaps[:5]:  # Top 5 habilidades
                learning_path = await self._create_learning_path(skill, learning_style)
                
                recommendations.append(Recommendation(
                    type=RecommendationType.LEARNING_PATH,
                    priority=RecommendationPriority.HIGH if skill in skill_gaps[:2] else RecommendationPriority.MEDIUM,
                    title=f"Desarrollar {skill}",
                    description=f"Plan de aprendizaje personalizado para {skill}",
                    action_items=learning_path['action_items'],
                    expected_impact=learning_path['expected_impact'],
                    time_to_implement=learning_path['time_to_implement'],
                    resources_needed=learning_path['resources_needed'],
                    success_metrics=learning_path['success_metrics'],
                    created_at=datetime.now()
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones de aprendizaje: {str(e)}")
            return []
    
    async def generate_personality_recommendations(
        self,
        person: Person,
        personality_analysis: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Genera recomendaciones para desarrollo de personalidad.
        
        Args:
            person: Persona para generar recomendaciones
            personality_analysis: Análisis de personalidad
            
        Returns:
            Lista de recomendaciones de personalidad
        """
        try:
            recommendations = []
            
            # Análisis de rasgos de personalidad
            traits = personality_analysis.get('traits', {})
            work_style = personality_analysis.get('work_style', '')
            
            # Recomendaciones basadas en rasgos
            if traits.get('introversion', 0) > 70:
                recommendations.append(Recommendation(
                    type=RecommendationType.PERSONALITY_ENHANCEMENT,
                    priority=RecommendationPriority.MEDIUM,
                    title="Desarrollar Habilidades de Networking",
                    description="Mejorar la capacidad de networking manteniendo la introversión",
                    action_items=[
                        "Participar en eventos profesionales pequeños",
                        "Usar LinkedIn para networking digital",
                        "Preparar elevator pitch"
                    ],
                    expected_impact=75.0,
                    time_to_implement="medium",
                    resources_needed=["Eventos profesionales", "Recursos de networking"],
                    success_metrics=["Conexiones profesionales", "Oportunidades de carrera"],
                    created_at=datetime.now()
                ))
            
            if traits.get('stress_management', 0) < 60:
                recommendations.append(Recommendation(
                    type=RecommendationType.WORK_LIFE_BALANCE,
                    priority=RecommendationPriority.HIGH,
                    title="Mejorar Gestión del Estrés",
                    description="Desarrollar técnicas efectivas de manejo del estrés",
                    action_items=[
                        "Practicar mindfulness o meditación",
                        "Establecer límites claros trabajo-vida",
                        "Desarrollar hobbies relajantes"
                    ],
                    expected_impact=80.0,
                    time_to_implement="short",
                    resources_needed=["Apps de meditación", "Actividades recreativas"],
                    success_metrics=["Reducción del estrés", "Mejor balance vida-trabajo"],
                    created_at=datetime.now()
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones de personalidad: {str(e)}")
            return []
    
    async def _identify_compatibility_gaps(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identifica gaps de compatibilidad entre persona y vacante."""
        gaps = []
        
        # Gap de habilidades
        person_skills = set(person_data.get('skills', []))
        required_skills = set(vacancy_data.get('requirements', {}).get('skills', []))
        missing_skills = required_skills - person_skills
        
        if missing_skills:
            gaps.append({
                'type': 'skills',
                'missing': list(missing_skills),
                'priority': 'high' if len(missing_skills) > 3 else 'medium'
            })
        
        # Gap de experiencia
        person_experience = person_data.get('experience_years', 0)
        required_experience = vacancy_data.get('requirements', {}).get('experience_years', 0)
        
        if person_experience < required_experience:
            gaps.append({
                'type': 'experience',
                'missing': required_experience - person_experience,
                'priority': 'high' if (required_experience - person_experience) > 2 else 'medium'
            })
        
        # Gap de liderazgo
        if vacancy_data.get('leadership_requirements') and not person_data.get('leadership_style'):
            gaps.append({
                'type': 'leadership',
                'missing': 'leadership_skills',
                'priority': 'medium'
            })
        
        return gaps
    
    async def _generate_gap_recommendations(self, gap: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones para un gap específico."""
        recommendations = []
        
        if gap['type'] == 'skills':
            missing_skills = gap['missing']
            recommendations.append(f"Desarrollar habilidades: {', '.join(missing_skills[:3])}")
            recommendations.append("Tomar cursos certificados en las áreas requeridas")
            
        elif gap['type'] == 'experience':
            years_needed = gap['missing']
            recommendations.append(f"Ganar {years_needed} años más de experiencia en el campo")
            recommendations.append("Buscar proyectos freelance o voluntariado para ganar experiencia")
            
        elif gap['type'] == 'leadership':
            recommendations.append("Desarrollar habilidades de liderazgo a través de proyectos")
            recommendations.append("Buscar oportunidades de mentoría")
        
        return recommendations
    
    async def _analyze_career_trajectory(
        self,
        person_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza la trayectoria profesional de la persona."""
        return {
            'current_stage': self._determine_career_stage(person_data),
            'growth_potential': analysis_results.get('growth_potential', {}).get('score', 0),
            'skill_gaps': self._identify_skill_gaps(person_data),
            'leadership_readiness': self._assess_leadership_readiness(person_data),
            'industry_alignment': self._assess_industry_alignment(person_data),
            'salary_progression': self._analyze_salary_progression(person_data)
        }
    
    async def _generate_area_recommendations(
        self,
        area: str,
        analysis: Any,
        person_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """Genera recomendaciones para un área específica."""
        recommendations = []
        
        if area == 'skill_gaps':
            for skill in analysis[:3]:  # Top 3 skills
                recommendations.append(await self._create_skill_recommendation(skill))
                
        elif area == 'leadership_readiness':
            if analysis > 80:
                recommendations.append(await self._create_leadership_recommendation())
                
        elif area == 'growth_potential':
            if analysis > 85:
                recommendations.append(await self._create_growth_recommendation())
        
        return recommendations
    
    async def _create_learning_path(self, skill: str, learning_style: str) -> Dict[str, Any]:
        """Crea un plan de aprendizaje personalizado para una habilidad."""
        learning_paths = {
            'technical': {
                'action_items': [
                    "Tomar curso online certificado",
                    "Practicar con proyectos personales",
                    "Participar en hackathons o competencias"
                ],
                'expected_impact': 90.0,
                'time_to_implement': 'medium',
                'resources_needed': ["Plataformas de aprendizaje", "Proyectos prácticos"],
                'success_metrics': ["Certificación obtenida", "Proyectos completados"]
            },
            'soft_skills': {
                'action_items': [
                    "Tomar taller presencial",
                    "Practicar en situaciones reales",
                    "Buscar feedback de colegas"
                ],
                'expected_impact': 85.0,
                'time_to_implement': 'long',
                'resources_needed': ["Talleres", "Experiencia práctica"],
                'success_metrics': ["Feedback positivo", "Mejora observable"]
            }
        }
        
        # Determinar tipo de habilidad
        skill_type = 'technical' if skill.lower() in ['programming', 'data analysis', 'design'] else 'soft_skills'
        
        return learning_paths[skill_type]
    
    def _determine_career_stage(self, person_data: Dict[str, Any]) -> str:
        """Determina la etapa de carrera de la persona."""
        experience_years = person_data.get('experience_years', 0)
        
        if experience_years < 2:
            return 'entry_level'
        elif experience_years < 5:
            return 'early_career'
        elif experience_years < 10:
            return 'mid_career'
        elif experience_years < 15:
            return 'senior'
        else:
            return 'expert'
    
    def _identify_skill_gaps(self, person_data: Dict[str, Any]) -> List[str]:
        """Identifica gaps de habilidades basados en el perfil."""
        current_skills = set(person_data.get('skills', []))
        
        # Habilidades demandadas en el mercado
        market_skills = {
            'Python', 'JavaScript', 'Data Analysis', 'Machine Learning',
            'Project Management', 'Leadership', 'Communication', 'Agile'
        }
        
        return list(market_skills - current_skills)
    
    def _assess_leadership_readiness(self, person_data: Dict[str, Any]) -> float:
        """Evalúa la preparación para liderazgo."""
        factors = [
            person_data.get('leadership_style', 0),
            person_data.get('communication_style', 0),
            person_data.get('collaboration', 0),
            person_data.get('initiative', 0)
        ]
        
        return np.mean(factors) if factors else 0.0
    
    def _assess_industry_alignment(self, person_data: Dict[str, Any]) -> float:
        """Evalúa la alineación con la industria."""
        # Implementación básica
        return 75.0
    
    def _analyze_salary_progression(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza la progresión salarial."""
        return {
            'current_level': 'market_average',
            'growth_rate': 'stable',
            'recommendations': ['Negociar aumentos basados en logros', 'Buscar roles con mayor responsabilidad']
        }
    
    async def _create_skill_recommendation(self, skill: str) -> Recommendation:
        """Crea una recomendación para desarrollo de habilidad."""
        return Recommendation(
            type=RecommendationType.SKILL_IMPROVEMENT,
            priority=RecommendationPriority.HIGH,
            title=f"Desarrollar {skill}",
            description=f"Mejorar competencias en {skill} para mayor competitividad",
            action_items=[
                f"Tomar curso certificado de {skill}",
                f"Practicar {skill} en proyectos reales",
                f"Buscar mentoría en {skill}"
            ],
            expected_impact=85.0,
            time_to_implement="medium",
            resources_needed=["Cursos online", "Proyectos prácticos", "Mentoría"],
            success_metrics=[f"Certificación en {skill}", f"Proyectos exitosos con {skill}"],
            created_at=datetime.now()
        )
    
    async def _create_leadership_recommendation(self) -> Recommendation:
        """Crea una recomendación para desarrollo de liderazgo."""
        return Recommendation(
            type=RecommendationType.LEADERSHIP_GROWTH,
            priority=RecommendationPriority.MEDIUM,
            title="Desarrollar Liderazgo Ejecutivo",
            description="Aprovechar el potencial de liderazgo para roles ejecutivos",
            action_items=[
                "Tomar programa de liderazgo ejecutivo",
                "Buscar roles de gestión de equipos",
                "Desarrollar estrategia de negocio"
            ],
            expected_impact=90.0,
            time_to_implement="long",
            resources_needed=["Programas ejecutivos", "Experiencia de gestión"],
            success_metrics=["Promoción a rol ejecutivo", "Liderazgo exitoso de equipos"],
            created_at=datetime.now()
        )
    
    async def _create_growth_recommendation(self) -> Recommendation:
        """Crea una recomendación para crecimiento profesional."""
        return Recommendation(
            type=RecommendationType.CAREER_DEVELOPMENT,
            priority=RecommendationPriority.HIGH,
            title="Acelerar Crecimiento Profesional",
            description="Maximizar el potencial de crecimiento identificado",
            action_items=[
                "Buscar roles con mayor responsabilidad",
                "Desarrollar habilidades estratégicas",
                "Construir red profesional ejecutiva"
            ],
            expected_impact=95.0,
            time_to_implement="long",
            resources_needed=["Roles estratégicos", "Red profesional", "Desarrollo ejecutivo"],
            success_metrics=["Promoción rápida", "Roles de mayor impacto"],
            created_at=datetime.now()
        )
    
    async def _analyze_team_dynamics(
        self,
        person_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza las dinámicas de equipo de la persona."""
        return {
            'collaboration_level': person_data.get('collaboration', 0),
            'leadership_potential': person_data.get('leadership_style', 0),
            'communication_style': person_data.get('communication_style', ''),
            'team_role': 'contributor',  # Implementar lógica más sofisticada
            'conflict_resolution': 'diplomatic'  # Implementar lógica más sofisticada
        }
    
    async def _extract_person_data(self, person: Person) -> Dict[str, Any]:
        """Extrae y estructura los datos de una persona."""
        return {
            'id': person.id,
            'name': person.name,
            'skills': person.skills.split(',') if person.skills else [],
            'experience_years': person.experience_years or 0,
            'education': person.education or '',
            'personality_traits': person.personality_traits or {},
            'cultural_preferences': getattr(person, 'cultural_preferences', {}),
            'career_goals': getattr(person, 'career_goals', []),
            'work_style': getattr(person, 'work_style', ''),
            'values': getattr(person, 'values', {}),
            'motivations': getattr(person, 'motivations', []),
            'learning_style': getattr(person, 'learning_style', ''),
            'communication_style': getattr(person, 'communication_style', ''),
            'leadership_style': getattr(person, 'leadership_style', ''),
            'team_preferences': getattr(person, 'team_preferences', {}),
            'stress_management': getattr(person, 'stress_management', ''),
            'adaptability': getattr(person, 'adaptability', 0),
            'innovation_capacity': getattr(person, 'innovation_capacity', 0),
            'emotional_intelligence': getattr(person, 'emotional_intelligence', 0),
            'analytical_thinking': getattr(person, 'analytical_thinking', 0),
            'creativity': getattr(person, 'creativity', 0),
            'collaboration': getattr(person, 'collaboration', 0),
            'initiative': getattr(person, 'initiative', 0),
            'resilience': getattr(person, 'resilience', 0)
        }
    
    def _get_priority_score(self, priority: RecommendationPriority) -> int:
        """Convierte prioridad a score numérico."""
        priority_scores = {
            RecommendationPriority.CRITICAL: 4,
            RecommendationPriority.HIGH: 3,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 1
        }
        return priority_scores.get(priority, 0)
    
    def _load_recommendation_templates(self) -> Dict[str, Any]:
        """Carga plantillas de recomendaciones."""
        return {
            'skill_development': {
                'title_template': "Desarrollar {skill}",
                'description_template': "Mejorar competencias en {skill} para mayor competitividad",
                'action_items_template': [
                    "Tomar curso certificado de {skill}",
                    "Practicar {skill} en proyectos reales",
                    "Buscar mentoría en {skill}"
                ]
            },
            'career_growth': {
                'title_template': "Acelerar Crecimiento Profesional",
                'description_template': "Maximizar el potencial de crecimiento identificado",
                'action_items_template': [
                    "Buscar roles con mayor responsabilidad",
                    "Desarrollar habilidades estratégicas",
                    "Construir red profesional ejecutiva"
                ]
            }
        } 