"""
Analizador de Carrera para Generación de CVs Avanzados.

Este módulo extiende las capacidades del generador de CVs tradicional
incorporando análisis de carrera avanzado basado en:
1. Datos reales extraídos de conversaciones con chatbot
2. Análisis ML de habilidades y experiencia
3. Evaluación personalizada de potencial y crecimiento
4. Integración de valores de apoyo, solidaridad y sinergia
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from django.conf import settings
from asgiref.sync import sync_to_async

from app.models import Person, Skill, SkillAssessment, BusinessUnit
from app.kanban.ml_integration import get_candidate_growth_data
from app.com.chatbot.utils.conversation_extractor import extract_career_insights
from app.com.chatbot.core.values import ValuesPrinciples

logger = logging.getLogger(__name__)

class CVCareerAnalyzer:
    """
    Analizador avanzado de carrera para enriquecer CVs con análisis
    basado en ML y datos extraídos de conversaciones.
    """
    
    def __init__(self, integration_level: str = 'enhanced'):
        """
        Inicializa el analizador de carrera.
        
        Args:
            integration_level: Nivel de integración ('basic', 'enhanced', 'full')
        """
        self.integration_level = integration_level
        self.values_principles = ValuesPrinciples()
    
    async def analyze_career_potential(self, person_id: int) -> Dict[str, Any]:
        """
        Analiza el potencial de carrera de un candidato.
        
        Args:
            person_id: ID del candidato
            
        Returns:
            Diccionario con análisis de potencial
        """
        try:
            # Obtener objeto Person
            person = await self._get_person(person_id)
            if not person:
                return self._get_default_potential()
            
            # Obtener datos de crecimiento del candidato
            growth_data = await sync_to_async(get_candidate_growth_data)(person)
            
            # Extraer insights de conversaciones
            chat_insights = await extract_career_insights(person_id)
            
            # Calcular potencial basado en datos combinados
            potential_analysis = self._calculate_potential(growth_data, chat_insights)
            
            # Enriquecer con valores de apoyo y motivación
            enriched_analysis = self._enrich_with_values(potential_analysis, person)
            
            return enriched_analysis
        except Exception as e:
            logger.error(f"Error analizando potencial de carrera: {str(e)}")
            return self._get_default_potential()
    
    async def identify_critical_skills(self, person_id: int, business_unit: str) -> List[Dict]:
        """
        Identifica habilidades críticas para el siguiente nivel profesional.
        
        Args:
            person_id: ID del candidato
            business_unit: Unidad de negocio
            
        Returns:
            Lista de habilidades críticas
        """
        try:
            # Obtener objeto Person
            person = await self._get_person(person_id)
            if not person:
                return []
            
            # Obtener business unit
            bu = await self._get_business_unit(business_unit)
            
            # Obtener habilidades actuales del candidato
            current_skills = await self._get_person_skills(person)
            
            # Calcular habilidades críticas para el mercado
            market_critical_skills = await self._get_market_critical_skills(person, bu)
            
            # Mapear a formato enriquecido con información de brecha
            enriched_skills = []
            for skill in market_critical_skills:
                # Buscar si ya tiene la habilidad y su nivel
                current_level = 0
                for s in current_skills:
                    if s['name'].lower() == skill['name'].lower():
                        current_level = s['score']
                        break
                
                # Calcular brecha
                target_level = skill.get('target_level', 80)
                gap = target_level - current_level
                
                # Añadir a lista enriquecida
                enriched_skills.append({
                    'name': skill['name'],
                    'current_level': current_level,
                    'target_level': target_level,
                    'gap': gap,
                    'priority': 'Alta' if gap > 30 else ('Media' if gap > 15 else 'Baja'),
                    'growth_time_months': round(gap / 10),  # Estimación simple: 10 puntos por mes
                    'market_demand': skill.get('market_demand', 70)
                })
            
            # Ordenar por prioridad (mayor brecha primero)
            return sorted(enriched_skills, key=lambda s: s['gap'], reverse=True)
        except Exception as e:
            logger.error(f"Error identificando habilidades críticas: {str(e)}")
            return []
    
    async def generate_development_plan(self, person_id: int, business_unit: str) -> Dict[str, Any]:
        """
        Genera un plan de desarrollo personalizado.
        
        Args:
            person_id: ID del candidato
            business_unit: Unidad de negocio
            
        Returns:
            Diccionario con plan de desarrollo
        """
        try:
            # Obtener objeto Person
            person = await self._get_person(person_id)
            if not person:
                return self._get_default_development_plan()
            
            # Obtener critical skills
            critical_skills = await self.identify_critical_skills(person_id, business_unit)
            
            # Identificar próximo nivel profesional
            next_level = await self._identify_next_level(person, business_unit)
            
            # Generar recomendaciones específicas
            recommendations = self._generate_recommendations(critical_skills, next_level)
            
            # Calcular tiempo estimado de desarrollo
            development_time = max([s['growth_time_months'] for s in critical_skills], default=12)
            
            # Integrar valores de apoyo y solidaridad
            values_integration = self.values_principles.get_values_based_message(
                "desarrollo_profesional", 
                {"nombre": person.nombre, "apellido": person.apellido_paterno}
            )
            
            return {
                'next_level': next_level,
                'critical_skills': critical_skills[:5],  # Top 5 habilidades críticas
                'recommendations': recommendations,
                'development_time_months': development_time,
                'estimated_completion_date': (datetime.now().replace(month=datetime.now().month + development_time) 
                                            if development_time < 24 else 
                                            datetime.now().replace(year=datetime.now().year + 2)),
                'values_message': values_integration,
                'priority_areas': self._identify_priority_areas(critical_skills)
            }
        except Exception as e:
            logger.error(f"Error generando plan de desarrollo: {str(e)}")
            return self._get_default_development_plan()
    
    def personalize_cv_message(self, data: Dict, audience: str = 'client') -> str:
        """
        Genera un mensaje personalizado para incluir en el CV basado en 
        los valores de apoyo, solidaridad y sinergia.
        
        Args:
            data: Datos del candidato
            audience: Tipo de audiencia ('client', 'candidate', 'consultant')
            
        Returns:
            Mensaje personalizado
        """
        context = {
            'nombre': data.get('name', '').split()[0] if data.get('name') else 'Candidato',
            'posicion': data.get('title', 'profesional'),
            'experiencia_años': self._extract_experience_years(data)
        }
        
        message_type = f"cv_{audience}"
        message = self.values_principles.get_values_based_message(message_type, context)
        
        return message
    
    async def _get_person(self, person_id: int) -> Optional[Person]:
        """Obtiene objeto Person por ID."""
        try:
            from app.models import Person
            return await sync_to_async(Person.objects.get)(id=person_id)
        except Exception as e:
            logger.error(f"Error obteniendo Person: {str(e)}")
            return None
    
    async def _get_business_unit(self, business_unit: str) -> Optional[BusinessUnit]:
        """Obtiene objeto BusinessUnit por nombre."""
        try:
            return await sync_to_async(BusinessUnit.objects.get)(name=business_unit)
        except Exception as e:
            logger.error(f"Error obteniendo BusinessUnit: {str(e)}")
            return None
    
    async def _get_person_skills(self, person) -> List[Dict]:
        """Obtiene habilidades actuales del candidato."""
        try:
            skill_assessments = await sync_to_async(list)(
                SkillAssessment.objects.filter(person=person).select_related('skill')
            )
            
            return [
                {
                    'name': sa.skill.name,
                    'score': sa.score,
                    'assessment_date': sa.assessment_date
                }
                for sa in skill_assessments
            ]
        except Exception as e:
            logger.error(f"Error obteniendo habilidades: {str(e)}")
            return []
    
    async def _get_market_critical_skills(self, person, business_unit) -> List[Dict]:
        """Obtiene habilidades críticas para el mercado actual."""
        # En implementación real, esto podría consultar una API o modelo ML
        # Aquí usamos datos simulados
        
        # Habilidades base para todas las BUs
        base_skills = [
            {'name': 'Comunicación efectiva', 'target_level': 85, 'market_demand': 90},
            {'name': 'Gestión del tiempo', 'target_level': 80, 'market_demand': 85},
            {'name': 'Resolución de problemas', 'target_level': 85, 'market_demand': 88},
        ]
        
        # Habilidades específicas por BU
        bu_skills = {
            'huntRED': [
                {'name': 'Liderazgo ejecutivo', 'target_level': 90, 'market_demand': 95},
                {'name': 'Gestión de equipos', 'target_level': 85, 'market_demand': 90},
                {'name': 'Negociación avanzada', 'target_level': 85, 'market_demand': 88},
                {'name': 'Pensamiento estratégico', 'target_level': 90, 'market_demand': 92},
            ],
            'huntU': [
                {'name': 'Adaptabilidad', 'target_level': 80, 'market_demand': 85},
                {'name': 'Trabajo en equipo', 'target_level': 85, 'market_demand': 88},
                {'name': 'Comunicación digital', 'target_level': 85, 'market_demand': 90},
            ],
            'SEXSI': [
                {'name': 'Confidencialidad', 'target_level': 95, 'market_demand': 98},
                {'name': 'Empatía', 'target_level': 90, 'market_demand': 92},
                {'name': 'Negociación', 'target_level': 85, 'market_demand': 88},
            ],
            'Amigro': [
                {'name': 'Comunicación intercultural', 'target_level': 85, 'market_demand': 90},
                {'name': 'Resiliencia', 'target_level': 85, 'market_demand': 88},
                {'name': 'Adaptabilidad', 'target_level': 80, 'market_demand': 85},
            ]
        }
        
        # Obtener habilidades para la BU específica
        bu_name = getattr(business_unit, 'name', business_unit)
        specific_skills = bu_skills.get(bu_name, bu_skills.get('huntRED', []))
        
        # Combinar habilidades base con específicas
        return base_skills + specific_skills
    
    async def _identify_next_level(self, person, business_unit) -> Dict:
        """Identifica el siguiente nivel profesional."""
        # Esto podría conectarse con una API o base de datos de trayectorias profesionales
        # Aquí usamos datos simulados
        
        current_title = getattr(person, 'current_position', 'Profesional')
        
        # Trayectorias profesionales simples
        career_paths = {
            'huntRED': {
                'Analista': 'Gerente Junior',
                'Gerente Junior': 'Gerente Senior',
                'Gerente Senior': 'Director',
                'Director': 'VP',
                'VP': 'C-Level'
            },
            'huntU': {
                'Practicante': 'Analista Junior',
                'Analista Junior': 'Analista Senior',
                'Analista Senior': 'Especialista',
                'Especialista': 'Líder de Proyecto'
            },
            'SEXSI': {
                'Consultor Junior': 'Consultor Senior',
                'Consultor Senior': 'Especialista',
                'Especialista': 'Gerente de Cuenta'
            },
            'Amigro': {
                'Asistente': 'Coordinador',
                'Coordinador': 'Supervisor',
                'Supervisor': 'Gerente'
            }
        }
        
        # Obtener path para la BU
        bu_name = getattr(business_unit, 'name', business_unit)
        path = career_paths.get(bu_name, career_paths.get('huntRED', {}))
        
        # Encontrar siguiente nivel
        next_position = path.get(current_title, 'Especialista')
        
        return {
            'current_position': current_title,
            'next_position': next_position,
            'estimated_time_months': 18,
            'key_requirements': [
                'Demostrar liderazgo en proyectos clave',
                'Desarrollar habilidades técnicas específicas',
                'Mejorar comunicación con stakeholders'
            ]
        }
    
    def _generate_recommendations(self, critical_skills: List[Dict], next_level: Dict) -> List[str]:
        """Genera recomendaciones específicas basadas en habilidades críticas y siguiente nivel."""
        recommendations = [
            f"Enfócate en desarrollar {skill['name']} para alcanzar el nivel de {next_level['next_position']}"
            for skill in critical_skills[:3]  # Top 3 habilidades
        ]
        
        # Añadir recomendaciones generales
        general_recommendations = [
            f"Busca mentores con experiencia en el rol de {next_level['next_position']}",
            "Participa en proyectos transversales para ganar visibilidad",
            "Considera formación especializada en tu área de interés"
        ]
        
        return recommendations + general_recommendations
    
    def _identify_priority_areas(self, critical_skills: List[Dict]) -> List[str]:
        """Identifica áreas prioritarias de desarrollo."""
        # Agrupar habilidades en categorías
        skill_categories = {
            'técnicas': ['programación', 'análisis de datos', 'finanzas', 'contabilidad'],
            'liderazgo': ['liderazgo', 'gestión', 'dirección', 'supervisión'],
            'comunicación': ['comunicación', 'presentación', 'negociación'],
            'personales': ['adaptabilidad', 'resiliencia', 'empatía', 'confidencialidad']
        }
        
        # Contar habilidades por categoría
        category_count = {category: 0 for category in skill_categories}
        for skill in critical_skills:
            for category, keywords in skill_categories.items():
                if any(keyword in skill['name'].lower() for keyword in keywords):
                    category_count[category] += 1
                    break
        
        # Identificar categorías prioritarias (con más habilidades)
        priority_categories = sorted(category_count.items(), key=lambda x: x[1], reverse=True)
        
        # Devolver nombres amigables para las categorías prioritarias
        friendly_names = {
            'técnicas': 'Habilidades técnicas específicas',
            'liderazgo': 'Capacidades de liderazgo y gestión',
            'comunicación': 'Habilidades de comunicación efectiva',
            'personales': 'Competencias personales y sociales'
        }
        
        return [friendly_names[category] for category, count in priority_categories if count > 0][:2]
    
    def _calculate_potential(self, growth_data: Dict, chat_insights: Dict) -> Dict:
        """Calcula potencial basado en datos de crecimiento e insights de chat."""
        # Datos básicos
        potential = {
            'overall': growth_data.get('potential_score', 75),
            'strengths': growth_data.get('strengths', []),
            'growth_areas': growth_data.get('growth_areas', []),
            'time_to_next_level': growth_data.get('months_to_next_level', 24)
        }
        
        # Enriquecer con insights del chat si están disponibles
        if chat_insights:
            # Añadir fortalezas identificadas en conversaciones
            if 'strengths' in chat_insights:
                potential['strengths'].extend(chat_insights['strengths'])
                # Eliminar duplicados
                potential['strengths'] = list(set(potential['strengths']))
            
            # Añadir áreas de desarrollo
            if 'development_areas' in chat_insights:
                potential['growth_areas'].extend(chat_insights['development_areas'])
                # Eliminar duplicados
                potential['growth_areas'] = list(set(potential['growth_areas']))
        
        return potential
    
    def _enrich_with_values(self, analysis: Dict, person) -> Dict:
        """Enriquece el análisis con mensajes basados en valores."""
        # Contexto para mensajes
        context = {
            'nombre': getattr(person, 'nombre', ''),
            'apellido': getattr(person, 'apellido_paterno', ''),
            'fortalezas': ', '.join(analysis['strengths'][:3]) if analysis['strengths'] else 'profesionalismo',
            'potencial': 'alto' if analysis['overall'] > 70 else 'en desarrollo'
        }
        
        # Obtener mensaje motivacional
        motivational_message = self.values_principles.get_values_based_message(
            "potencial_profesional", 
            context
        )
        
        # Añadir mensaje al análisis
        enriched = analysis.copy()
        enriched['motivational_message'] = motivational_message
        
        return enriched
    
    def _get_default_potential(self) -> Dict:
        """Devuelve un análisis de potencial por defecto."""
        return {
            'overall': 75,
            'strengths': [
                'Adaptabilidad',
                'Comunicación efectiva',
                'Orientación a resultados'
            ],
            'growth_areas': [
                'Liderazgo estratégico',
                'Gestión de conflictos',
                'Comunicación ejecutiva'
            ],
            'time_to_next_level': 24,
            'motivational_message': "Tu perfil profesional muestra un gran potencial. Continúa desarrollando tus fortalezas y trabajando en tus áreas de oportunidad para alcanzar tus metas profesionales."
        }
    
    def _get_default_development_plan(self) -> Dict:
        """Devuelve un plan de desarrollo por defecto."""
        return {
            'next_level': {
                'current_position': 'Profesional',
                'next_position': 'Especialista',
                'estimated_time_months': 18,
                'key_requirements': [
                    'Desarrollar habilidades técnicas específicas',
                    'Ganar experiencia en proyectos clave',
                    'Mejorar habilidades de comunicación'
                ]
            },
            'critical_skills': [],
            'recommendations': [
                'Busca mentores con experiencia en tu área de interés',
                'Participa en proyectos transversales para ganar visibilidad',
                'Considera formación especializada en tu área'
            ],
            'development_time_months': 18,
            'estimated_completion_date': datetime.now().replace(month=datetime.now().month + 18),
            'values_message': "Tu desarrollo profesional es importante para nosotros. Estamos comprometidos en apoyarte para que alcances tu máximo potencial.",
            'priority_areas': [
                'Habilidades técnicas específicas',
                'Capacidades de comunicación efectiva'
            ]
        }
    
    def _extract_experience_years(self, data: Dict) -> int:
        """Extrae años de experiencia de los datos del candidato."""
        try:
            experience = data.get('experience', [])
            total_months = 0
            
            for exp in experience:
                # Convertir fechas de string a datetime
                start_date = datetime.strptime(exp['start_date'], '%m/%Y') if isinstance(exp['start_date'], str) else exp['start_date']
                
                if exp.get('end_date'):
                    end_date = datetime.strptime(exp['end_date'], '%m/%Y') if isinstance(exp['end_date'], str) else exp['end_date']
                else:
                    end_date = datetime.now()
                
                # Calcular meses
                months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                total_months += months
            
            return total_months // 12  # Convertir a años
        except Exception:
            return 5  # Valor por defecto


# Instancia global
career_analyzer = CVCareerAnalyzer()
