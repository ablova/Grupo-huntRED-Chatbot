"""
Sistema de Conexión con Mentores.

Este módulo proporciona emparejamiento algoritmo de candidatos con mentores
basado en objetivos profesionales, personalidades compatibles y experiencia relevante.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

import numpy as np
from asgiref.sync import sync_to_async
from django.conf import settings

from app.models import Person, Mentor, MentorSkill, MentorSession
from app.com.talent.trajectory_analyzer import TrajectoryAnalyzer
from app.com.chatbot.workflow.personality import PersonalityAnalyzer
from app.com.chatbot.core.values import ValuesPrinciples

logger = logging.getLogger(__name__)

class MentorMatcher:
    """
    Sistema de emparejamiento algorítmico con mentores ideales.
    
    Analiza perfiles de mentores y candidatos para crear conexiones
    óptimas basadas en múltiples factores de compatibilidad.
    """
    
    # Factores de compatibilidad y sus pesos
    COMPATIBILITY_FACTORS = {
        'career_alignment': 0.30,
        'skill_match': 0.25,
        'personality_compatibility': 0.20,
        'industry_experience': 0.15,
        'mentoring_style': 0.10
    }
    
    # Tipos de mentoría
    MENTORING_TYPES = [
        "Carrera", "Habilidades técnicas", "Liderazgo", 
        "Emprendimiento", "Equilibrio vida-trabajo", "Networking"
    ]
    
    def __init__(self):
        """Inicializa el emparejador de mentores."""
        self.trajectory_analyzer = TrajectoryAnalyzer()
        self.personality_analyzer = PersonalityAnalyzer()
        self.values_principles = ValuesPrinciples()
        
    async def find_optimal_mentors(self, 
                                 person_id: int, 
                                 goal: Optional[str] = None,
                                 business_unit: Optional[str] = None,
                                 mentoring_type: Optional[str] = None,
                                 limit: int = 5) -> Dict:
        """
        Encuentra los mentores óptimos para un candidato.
        
        Args:
            person_id: ID del candidato
            goal: Objetivo específico de la mentoría (opcional)
            business_unit: Unidad de negocio (opcional)
            mentoring_type: Tipo de mentoría deseada (opcional)
            limit: Número máximo de mentores a retornar
            
        Returns:
            Dict con mentores recomendados y análisis de compatibilidad
        """
        try:
            # Obtener información del candidato
            person_data = await self._get_person_data(person_id)
            if not person_data:
                return self._get_default_matches()
            
            # Si no se especifica objetivo, intentar determinarlo
            if not goal:
                goal = await self._determine_mentoring_goal(person_id)
            
            # Obtener mentores disponibles, filtrando por BU si es necesario
            available_mentors = await self._get_available_mentors(business_unit)
            if not available_mentors:
                return self._get_default_matches()
            
            # Filtrar por tipo de mentoría si es necesario
            if mentoring_type:
                available_mentors = [
                    m for m in available_mentors 
                    if mentoring_type in m.get('mentoring_types', [])
                ]
            
            # Calcular compatibilidad con cada mentor
            mentor_matches = []
            for mentor in available_mentors:
                # Análisis multifactorial de compatibilidad
                compatibility = await self._analyze_compatibility(
                    person_data,
                    mentor,
                    goal
                )
                
                # Añadir a resultados
                mentor_matches.append({
                    'mentor': mentor,
                    'compatibility': compatibility,
                    'overall_score': compatibility['overall_score']
                })
            
            # Ordenar por puntuación general
            ranked_matches = sorted(
                mentor_matches,
                key=lambda x: x['overall_score'],
                reverse=True
            )
            
            # Limitar cantidad
            top_matches = ranked_matches[:limit]
            
            # Añadir mensaje basado en valores
            message = self.values_principles.get_values_based_message(
                "mentoría",
                {"nombre": person_data['name'], "objetivo": goal}
            )
            
            return {
                'person_id': person_id,
                'goal': goal,
                'mentoring_type': mentoring_type,
                'matches': top_matches,
                'values_message': message,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error encontrando mentores: {str(e)}")
            return self._get_default_matches()
    
    async def _get_person_data(self, person_id: int) -> Optional[Dict]:
        """Obtiene datos del candidato relevantes para matching."""
        try:
            from app.models import Person, SkillAssessment
            
            person = await sync_to_async(Person.objects.get)(id=person_id)
            
            # Obtener habilidades
            assessments = await sync_to_async(list)(
                SkillAssessment.objects.filter(person=person).select_related('skill')
            )
            
            skills = [
                {
                    'name': assessment.skill.name,
                    'level': assessment.score,
                    'category': assessment.skill.category
                }
                for assessment in assessments
            ]
            
            # Obtener análisis de personalidad
            personality = await self.personality_analyzer.analyze_personality(person_id)
            
            # Obtener trayectoria profesional
            trajectory = await self.trajectory_analyzer.predict_optimal_path(
                person_id,
                time_horizon=36,  # 3 años
                include_mentors=False  # Evitar recursión
            )
            
            return {
                'id': person_id,
                'name': f"{person.first_name} {person.last_name}",
                'current_position': getattr(person, 'current_position', 'Profesional'),
                'skills': skills,
                'personality': personality,
                'career_trajectory': trajectory,
                'years_experience': getattr(person, 'years_experience', 3),
                'industry': getattr(person, 'industry', 'Technology')
            }
        except Exception as e:
            logger.error(f"Error obteniendo datos de candidato: {str(e)}")
            return None
    
    async def _get_available_mentors(self, business_unit: Optional[str] = None) -> List[Dict]:
        """Obtiene mentores disponibles, opcionalmente filtrados por BU."""
        try:
            # En un sistema real, esto consultaría la base de datos
            # Para esta demo, creamos mentores simulados
            
            # Si hay business_unit, filtrar mentores por esa BU
            mentors = self._generate_mock_mentors(business_unit)
            
            return mentors
            
        except Exception as e:
            logger.error(f"Error obteniendo mentores: {str(e)}")
            return []
    
    def _generate_mock_mentors(self, business_unit: Optional[str] = None) -> List[Dict]:
        """Genera mentores simulados para demostración."""
        # Lista de posibles industrias
        industries = [
            "Tecnología", "Finanzas", "Consultoría", "Marketing", 
            "Manufactura", "Salud", "Educación", "Retail"
        ]
        
        # Lista de posibles posiciones
        positions = [
            "Director", "Gerente Senior", "VP", "CTO", "CEO", 
            "Líder de Proyecto", "Especialista Senior", "Consultor"
        ]
        
        # Crear mentores con datos consistentes
        import hashlib
        import random
        
        # BUs disponibles
        business_units = ["huntRED", "huntU", "Amigro", "SEXSI", "MilkyLeak"]
        
        mentors = []
        
        # Generar 15-20 mentores
        for i in range(15):
            # Usar ID para datos consistentes
            seed = i + 1000
            random.seed(seed)
            
            # Asignar BU aleatoria o la especificada
            if business_unit:
                mentor_bu = business_unit
            else:
                mentor_bu = random.choice(business_units)
            
            # Solo incluir si coincide con el filtro o no hay filtro
            if business_unit and mentor_bu != business_unit:
                continue
                
            # Generar mentor
            mentor = {
                'id': seed,
                'name': f"Mentor {seed}",
                'position': random.choice(positions),
                'years_experience': random.randint(7, 25),
                'industry': random.choice(industries),
                'business_unit': mentor_bu,
                'expertise_areas': random.sample([
                    "Liderazgo", "Gestión de equipos", "Finanzas", 
                    "Marketing", "Ventas", "Tecnología", "Operaciones",
                    "RRHH", "Estrategia", "Innovación", "Producto"
                ], k=random.randint(2, 4)),
                'mentoring_types': random.sample(self.MENTORING_TYPES, k=random.randint(1, 3)),
                'skills': [
                    {'name': 'Liderazgo', 'level': random.randint(70, 95)},
                    {'name': 'Comunicación', 'level': random.randint(75, 95)},
                    {'name': random.choice([
                        "Análisis estratégico", "Innovación", "Gestión financiera",
                        "Marketing digital", "Desarrollo de equipos", "Negociación"
                    ]), 'level': random.randint(80, 95)}
                ],
                'personality_type': random.choice([
                    "Analítico", "Colaborativo", "Director", "Innovador"
                ]),
                'availability': {
                    'hours_per_month': random.choice([1, 2, 4, 8]),
                    'format': random.choice(["Presencial", "Virtual", "Híbrido"])
                },
                'languages': ["Español"] + (["Inglés"] if random.random() > 0.3 else []),
                'rating': round(random.uniform(4.0, 5.0), 1),
                'mentees_count': random.randint(1, 15)
            }
            
            mentors.append(mentor)
        
        return mentors
    
    async def _determine_mentoring_goal(self, person_id: int) -> str:
        """Determina el objetivo de mentoría más apropiado."""
        try:
            # Obtener trayectoria profesional
            trajectory = await self.trajectory_analyzer.predict_optimal_path(
                person_id,
                time_horizon=36,  # 3 años
                include_mentors=False  # Evitar recursión
            )
            
            # Analizar puntos de decisión
            decision_points = trajectory.get('decision_points', [])
            
            if decision_points:
                # Tomar el primer punto de decisión como referencia
                first_decision = decision_points[0]
                next_position = first_decision.get('next_position', '')
                
                return f"Transición a {next_position}"
            
            # Si no hay puntos de decisión, usar posición actual
            current_position = trajectory.get('current_position', 'Profesional')
            
            return f"Desarrollo en {current_position}"
            
        except Exception as e:
            logger.error(f"Error determinando objetivo: {str(e)}")
            return "Desarrollo profesional general"
    
    async def _analyze_compatibility(self, person_data: Dict, mentor: Dict, goal: str) -> Dict:
        """Analiza compatibilidad multifactorial entre candidato y mentor."""
        # Analizar diferentes factores de compatibilidad
        
        # 1. Alineación de carrera y trayectoria
        career_alignment = self._calculate_career_alignment(
            person_data.get('career_trajectory', {}),
            mentor
        )
        
        # 2. Match de habilidades y competencias
        skill_match = self._calculate_skill_match(
            person_data.get('skills', []),
            mentor.get('skills', [])
        )
        
        # 3. Compatibilidad de personalidad y valores
        personality_compatibility = self._calculate_personality_compatibility(
            person_data.get('personality', {}).get('type', 'Equilibrado'),
            mentor.get('personality_type', 'Equilibrado'),
            person_data.get('values', {}),
            mentor.get('values', {})
        )
        
        # 4. Experiencia y contexto
        experience_match = self._calculate_experience_match(
            person_data.get('experience', {}),
            mentor.get('experience', {}),
            person_data.get('industry', ''),
            mentor.get('industry', '')
        )
        
        # 5. Estilo de mentoría y objetivos
        mentoring_style = self._calculate_mentoring_style_match(
            goal,
            mentor.get('mentoring_types', []),
            person_data.get('learning_style', {}),
            mentor.get('teaching_style', {})
        )
        
        # 6. Compatibilidad cultural y de equipo
        cultural_fit = self._calculate_cultural_fit(
            person_data.get('cultural_preferences', {}),
            mentor.get('team_culture', {}),
            person_data.get('work_style', {}),
            mentor.get('work_style', {})
        )
        
        # 7. Potencial de crecimiento
        growth_potential = self._calculate_growth_potential(
            person_data.get('career_goals', {}),
            mentor.get('expertise_areas', []),
            person_data.get('learning_curve', {}),
            mentor.get('mentoring_approach', {})
        )
        
        # Calcular puntuación global ponderada
        weights = self._get_dynamic_weights(person_data, mentor, goal)
        overall_score = (
            career_alignment * weights['career_alignment'] +
            skill_match * weights['skill_match'] +
            personality_compatibility * weights['personality_compatibility'] +
            experience_match * weights['experience_match'] +
            mentoring_style * weights['mentoring_style'] +
            cultural_fit * weights['cultural_fit'] +
            growth_potential * weights['growth_potential']
        )
        
        return {
            'overall_score': min(100, overall_score),
            'factors': {
                'career_alignment': career_alignment,
                'skill_match': skill_match,
                'personality_compatibility': personality_compatibility,
                'experience_match': experience_match,
                'mentoring_style': mentoring_style,
                'cultural_fit': cultural_fit,
                'growth_potential': growth_potential
            },
            'compatibility_reasons': self._generate_compatibility_reasons(
                person_data,
                mentor,
                goal,
                {
                    'career_alignment': career_alignment,
                    'skill_match': skill_match,
                    'personality_compatibility': personality_compatibility,
                    'experience_match': experience_match,
                    'mentoring_style': mentoring_style,
                    'cultural_fit': cultural_fit,
                    'growth_potential': growth_potential
                }
            )
        }
    
    def _calculate_career_alignment(self, trajectory: Dict, mentor: Dict) -> float:
        """Calcula alineación entre trayectoria del candidato y experiencia del mentor."""
        # Obtener posiciones futuras del candidato
        future_positions = []
        
        for path in trajectory.get('top_paths', []):
            if isinstance(path, dict) and 'position' in path:
                future_positions.append(path['position'])
            elif isinstance(path, list):
                for step in path:
                    if isinstance(step, dict) and 'position' in step:
                        future_positions.append(step['position'])
        
        # Si no hay futuras posiciones, usar posición actual
        if not future_positions and 'current_position' in trajectory:
            future_positions = [trajectory['current_position']]
        
        # Calcular alineación con expertise del mentor
        mentor_expertise = mentor.get('expertise_areas', [])
        mentor_position = mentor.get('position', '')
        
        alignment_score = 0
        
        # Verificar si la posición del mentor coincide con alguna posición futura
        for position in future_positions:
            # Coincidencia exacta o parcial
            if position == mentor_position:
                alignment_score += 40
            elif position in mentor_position or mentor_position in position:
                alignment_score += 20
        
        # Verificar si las áreas de expertise del mentor son relevantes
        for expertise in mentor_expertise:
            for position in future_positions:
                if expertise.lower() in position.lower():
                    alignment_score += 15
                    break
        
        # Limitar a 100
        return min(100, alignment_score)
    
    def _calculate_skill_match(self, person_skills: List[Dict], mentor_skills: List[Dict]) -> float:
        """Calcula coincidencia de habilidades entre candidato y mentor."""
        if not person_skills or not mentor_skills:
            return 50  # Valor neutral si no hay datos
        
        # Extraer nombres de habilidades
        person_skill_names = [s['name'].lower() for s in person_skills]
        mentor_skill_names = [s['name'].lower() for s in mentor_skills]
        
        # Contar coincidencias
        matching_skills = set(person_skill_names).intersection(set(mentor_skill_names))
        
        # Calcular porcentaje de match
        match_percentage = len(matching_skills) / len(person_skill_names) * 100 if person_skill_names else 0
        
        # Evaluar nivel en habilidades coincidentes
        level_score = 0
        if matching_skills:
            for skill_name in matching_skills:
                # Encontrar niveles
                person_level = next((s['level'] for s in person_skills if s['name'].lower() == skill_name), 0)
                mentor_level = next((s['level'] for s in mentor_skills if s['name'].lower() == skill_name), 0)
                
                # El mentor debe tener mayor nivel para ser efectivo
                if mentor_level > person_level:
                    level_diff = mentor_level - person_level
                    # Una diferencia ideal es 20-30 puntos
                    if 15 <= level_diff <= 35:
                        level_score += 100
                    else:
                        level_score += max(0, 100 - abs(level_diff - 25) * 2)
            
            level_score /= len(matching_skills)
        
        # Combinar match de habilidades con diferencia de nivel
        return (match_percentage * 0.6) + (level_score * 0.4)
    
    def _calculate_personality_compatibility(self, person_type: str, mentor_type: str,
                                          person_values: Dict, mentor_values: Dict) -> float:
        """Calcula compatibilidad de personalidades y valores."""
        # Matriz de compatibilidad (simplificada)
        compatibility_matrix = {
            'Analítico': {
                'Analítico': 70,    # Buena, pero puede faltar dinamismo
                'Colaborativo': 85,  # Muy buena, el colaborativo ayuda al analítico a aplicar
                'Director': 65,     # Regular, puede haber tensión
                'Innovador': 90     # Excelente, complementarios
            },
            'Colaborativo': {
                'Analítico': 75,    # Buena, el analítico aporta rigor
                'Colaborativo': 80,  # Muy buena, ambiente positivo
                'Director': 85,     # Muy buena, el director aporta dirección clara
                'Innovador': 70     # Buena, pero puede faltar estructura
            },
            'Director': {
                'Analítico': 70,    # Buena, el analítico aporta datos
                'Colaborativo': 80,  # Muy buena, el colaborativo suaviza
                'Director': 60,     # Regular, puede haber dominancia
                'Innovador': 75     # Buena, el innovador aporta nuevas ideas
            },
            'Innovador': {
                'Analítico': 85,    # Muy buena, el analítico aporta estructura
                'Colaborativo': 75,  # Buena, el colaborativo ayuda a implementar
                'Director': 80,     # Muy buena, el director ayuda a concretar
                'Innovador': 65     # Regular, puede faltar practicidad
            },
            'Equilibrado': {
                'Analítico': 80,
                'Colaborativo': 80,
                'Director': 80,
                'Innovador': 80,
                'Equilibrado': 75
            }
        }
        
        # Si alguno no está definido, usar "Equilibrado"
        person_type = person_type if person_type in compatibility_matrix else 'Equilibrado'
        mentor_type = mentor_type if mentor_type in compatibility_matrix.get(person_type, {}) else 'Equilibrado'
        
        # Obtener compatibilidad
        compatibility = compatibility_matrix.get(person_type, {}).get(mentor_type, 70)
        
        # Ajustar por valores
        person_values_score = sum(person_values.get(value, 0) for value in mentor_values)
        mentor_values_score = sum(mentor_values.get(value, 0) for value in person_values)
        
        values_compatibility = (person_values_score + mentor_values_score) / 2
        
        return compatibility * values_compatibility
    
    def _calculate_experience_match(self, person_experience: Dict, mentor_experience: Dict,
                                  person_industry: str, mentor_industry: str) -> float:
        """Calcula coincidencia entre experiencia del candidato y mentor."""
        # Base: años de experiencia
        if mentor_experience.get('years_experience', 0) <= 5:
            base_score = 50
        elif mentor_experience.get('years_experience', 0) <= 10:
            base_score = 70
        elif mentor_experience.get('years_experience', 0) <= 15:
            base_score = 85
        else:
            base_score = 95
        
        # Ajuste por coincidencia de industria
        if not person_industry or not mentor_industry:
            industry_factor = 0.8  # Neutral si falta información
        elif person_industry.lower() == mentor_industry.lower():
            industry_factor = 1.2  # Bonus por coincidencia exacta
        else:
            # Industrias relacionadas (simplificado)
            related_industries = {
                'Tecnología': ['Consultoría', 'Telecomunicaciones'],
                'Finanzas': ['Consultoría', 'Seguros', 'Banca'],
                'Manufactura': ['Logística', 'Ingeniería'],
                'Salud': ['Farmacéutica', 'Biotecnología'],
                'Retail': ['Ecommerce', 'Logística']
            }
            
            if (person_industry in related_industries.get(mentor_industry, []) or
                mentor_industry in related_industries.get(person_industry, [])):
                industry_factor = 1.0  # Neutral para industrias relacionadas
            else:
                industry_factor = 0.7  # Penalización para industrias diferentes
        
        return min(100, base_score * industry_factor)
    
    def _calculate_mentoring_style_match(self, goal: str, mentoring_types: List[str],
                                      person_learning_style: Dict, mentor_teaching_style: Dict) -> float:
        """Calcula coincidencia entre objetivo y tipos de mentoría."""
        if not mentoring_types:
            return 50  # Valor neutral si no hay datos
        
        # Mapeo de objetivos a tipos ideales de mentoría
        goal_to_type = {
            'Desarrollo profesional general': ["Carrera", "Habilidades técnicas"],
            'Transición a Gerente': ["Liderazgo", "Carrera"],
            'Transición a Director': ["Liderazgo", "Carrera"],
            'Transición a VP': ["Liderazgo", "Networking"],
            'Transición a C-Level': ["Liderazgo", "Estrategia", "Networking"],
            'Desarrollo en Analista': ["Habilidades técnicas", "Carrera"],
            'Desarrollo en Gerente': ["Liderazgo", "Gestión de equipos"],
            'Cambio de industria': ["Networking", "Carrera"],
            'Emprendimiento': ["Emprendimiento", "Liderazgo"]
        }
        
        # Buscar tipos ideales para el objetivo
        # Usar coincidencias parciales si no hay exacta
        ideal_types = []
        for key, types in goal_to_type.items():
            if key == goal:
                ideal_types = types
                break
            elif key in goal or goal in key:
                ideal_types = types
                break
        
        # Si no se encontró, usar valores predeterminados
        if not ideal_types:
            if "Transición" in goal:
                ideal_types = ["Carrera", "Liderazgo"]
            elif "Desarrollo" in goal:
                ideal_types = ["Habilidades técnicas", "Carrera"]
            else:
                ideal_types = ["Carrera"]
        
        # Contar coincidencias
        matching_types = set(ideal_types).intersection(set(mentoring_types))
        
        # Calcular puntuación
        if not ideal_types:
            return 50
            
        match_percentage = len(matching_types) / len(ideal_types) * 100
        
        return match_percentage
    
    def _calculate_cultural_fit(self, person_culture: Dict, mentor_culture: Dict,
                              person_work_style: Dict, mentor_work_style: Dict) -> float:
        """Calcula la compatibilidad cultural y de estilo de trabajo."""
        if not all([person_culture, mentor_culture, person_work_style, mentor_work_style]):
            return 50  # Valor neutral si faltan datos
            
        # Calcular alineación de valores culturales
        cultural_alignment = self._calculate_values_alignment(
            person_culture.get('values', []),
            mentor_culture.get('values', [])
        )
        
        # Calcular compatibilidad de estilo de trabajo
        work_style_compatibility = self._calculate_work_style_compatibility(
            person_work_style,
            mentor_work_style
        )
        
        # Calcular dinámica de equipo
        team_dynamics = self._calculate_team_dynamics(
            person_culture.get('team_preferences', {}),
            mentor_culture.get('team_approach', {})
        )
        
        # Combinar factores con pesos
        return (
            cultural_alignment * 0.4 +
            work_style_compatibility * 0.4 +
            team_dynamics * 0.2
        )

    def _calculate_growth_potential(self, person_goals: Dict, mentor_expertise: List,
                                  person_learning: Dict, mentor_approach: Dict) -> float:
        """Calcula el potencial de crecimiento y desarrollo."""
        if not all([person_goals, mentor_expertise, person_learning, mentor_approach]):
            return 50  # Valor neutral si faltan datos
            
        # Calcular alineación de objetivos
        goals_alignment = self._calculate_goals_alignment(
            person_goals.get('short_term', []),
            person_goals.get('long_term', []),
            mentor_expertise
        )
        
        # Calcular compatibilidad de aprendizaje
        learning_compatibility = self._calculate_learning_compatibility(
            person_learning.get('style', ''),
            person_learning.get('pace', ''),
            mentor_approach.get('teaching_style', ''),
            mentor_approach.get('mentoring_approach', '')
        )
        
        # Calcular potencial de desarrollo
        development_potential = self._calculate_development_potential(
            person_goals.get('career_path', {}),
            mentor_expertise,
            mentor_approach.get('development_focus', [])
        )
        
        # Combinar factores con pesos
        return (
            goals_alignment * 0.4 +
            learning_compatibility * 0.3 +
            development_potential * 0.3
        )

    def _get_dynamic_weights(self, person_data: Dict, mentor: Dict, goal: str) -> Dict:
        """Obtiene pesos dinámicos basados en el contexto y objetivos."""
        # Pesos base
        base_weights = {
            'career_alignment': 0.25,
            'skill_match': 0.20,
            'personality_compatibility': 0.15,
            'experience_match': 0.15,
            'mentoring_style': 0.10,
            'cultural_fit': 0.10,
            'growth_potential': 0.05
        }
        
        # Ajustar pesos según el objetivo
        if 'carrera' in goal.lower():
            base_weights['career_alignment'] += 0.05
            base_weights['growth_potential'] += 0.05
            base_weights['skill_match'] -= 0.05
            base_weights['experience_match'] -= 0.05
        elif 'habilidades' in goal.lower():
            base_weights['skill_match'] += 0.05
            base_weights['experience_match'] += 0.05
            base_weights['career_alignment'] -= 0.05
            base_weights['growth_potential'] -= 0.05
        elif 'liderazgo' in goal.lower():
            base_weights['personality_compatibility'] += 0.05
            base_weights['cultural_fit'] += 0.05
            base_weights['skill_match'] -= 0.05
            base_weights['mentoring_style'] -= 0.05
            
        # Ajustar pesos según la experiencia del mentor
        if mentor.get('years_experience', 0) > 10:
            base_weights['experience_match'] += 0.05
            base_weights['career_alignment'] -= 0.05
            
        # Normalizar pesos
        total = sum(base_weights.values())
        return {k: v/total for k, v in base_weights.items()}
    
    def _generate_compatibility_reasons(self, person_data: Dict, mentor: Dict, 
                                      goal: str, factors: Dict) -> List[str]:
        """Genera razones de compatibilidad para explicar el match."""
        reasons = []
        
        # Ordenar factores de mayor a menor
        sorted_factors = sorted(
            factors.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Generar razones para los factores principales
        for factor_name, score in sorted_factors[:3]:
            if score < 60:
                continue  # No mencionar factores bajos
                
            if factor_name == 'career_alignment' and score > 70:
                if 'position' in mentor:
                    reasons.append(f"Trayectoria alineada con la posición de {mentor['position']}")
                if 'expertise_areas' in mentor:
                    reasons.append(f"Experiencia en {', '.join(mentor['expertise_areas'][:2])}")
                    
            elif factor_name == 'skill_match' and score > 70:
                if 'skills' in mentor:
                    skill_names = [s['name'] for s in mentor['skills']]
                    reasons.append(f"Dominio en habilidades clave: {', '.join(skill_names[:2])}")
                    
            elif factor_name == 'personality_compatibility' and score > 70:
                if 'personality_type' in mentor:
                    person_type = person_data.get('personality', {}).get('type', 'Equilibrado')
                    reasons.append(f"Compatibilidad entre {person_type} y {mentor['personality_type']}")
                    
            elif factor_name == 'experience_match' and score > 70:
                if 'years_experience' in mentor and 'industry' in mentor:
                    reasons.append(f"{mentor['years_experience']} años en {mentor['industry']}")
                    
            elif factor_name == 'mentoring_style' and score > 70:
                if 'mentoring_types' in mentor:
                    reasons.append(f"Especializado en {', '.join(mentor['mentoring_types'][:2])}")
        
        # Añadir razones específicas adicionales
        if mentor.get('rating', 0) >= 4.5:
            reasons.append(f"Alta calificación de {mentor['rating']}/5.0")
            
        if goal in str(mentor.get('expertise_areas', [])):
            reasons.append(f"Especialista en {goal}")
            
        if person_data.get('industry') == mentor.get('industry'):
            reasons.append("Misma industria")
            
        # Limitar a 3 razones
        return reasons[:3]
    
    def _get_default_matches(self) -> Dict:
        """Retorna un resultado de emparejamiento predeterminado vacío."""
        return {
            'goal': "Desarrollo profesional general",
            'matches': [],
            'analyzed_at': datetime.now().isoformat()
        }
