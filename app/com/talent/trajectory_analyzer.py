# /home/pablo/app/com/talent/trajectory_analyzer.py
"""
Analizador de Trayectoria Profesional.

Este módulo analiza y predice trayectorias profesionales óptimas
basadas en el perfil del candidato, tendencias del mercado y datos históricos.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from django.conf import settings
from asgiref.sync import sync_to_async
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from app.models import Person, Experience, Skill, SkillAssessment, BusinessUnit
from app.com.utils.cv_generator.career_analyzer import CVCareerAnalyzer
from app.com.chatbot.workflow.assessments.personality.personality_workflow import PersonalityAssessment
from app.com.chatbot.workflow.assessments.professional_dna import ProfessionalDNAAnalysis
from app.com.chatbot.workflow.assessments.cultural.cultural_fit_workflow import CulturalFitWorkflow
from app.com.ml.skill_classifier import SkillClassifier

logger = logging.getLogger(__name__)

class TrajectoryAnalyzer:
    """
    Analiza la trayectoria profesional y predice rutas óptimas de desarrollo.
    
    Integra con los sistemas existentes para aprovechar datos históricos y
    modelos predictivos ya desarrollados.
    """
    
    def __init__(self, business_unit: str = None):
        """
        Inicializa el analizador de trayectoria.
        
        Args:
            business_unit: Unidad de negocio (opcional)
        """
        self.business_unit = business_unit
        self.values_principles = ValuesPrinciples()
        self.cv_career_analyzer = CVCareerAnalyzer()
        self.skill_classifier = SkillClassifier()
        
        # Cargar datos de mercado y modelos predictivos
        self.market_data = self._load_market_data()
        self.career_paths = self._load_career_paths()
    
    async def predict_optimal_path(self, 
                                 person_id: int, 
                                 time_horizon: int = 60,
                                 include_mentors: bool = True) -> Dict:
        """
        Predice el camino óptimo de desarrollo profesional.
        
        Args:
            person_id: ID del candidato
            time_horizon: Horizonte de tiempo en meses (default: 5 años)
            include_mentors: Si incluir recomendaciones de mentores
            
        Returns:
            Dict con rutas profesionales, habilidades clave y puntos de decisión
        """
        try:
            # Obtener perfil actual del candidato
            person = await self._get_person(person_id)
            if not person:
                logger.error(f"Persona no encontrada: {person_id}")
                return self._get_default_path()
            
            # Obtener datos de crecimiento ya calculados en el sistema existente
            career_potential = await self.cv_career_analyzer.analyze_career_potential(person_id)
            
            # Identificar la posición actual y potenciales posiciones futuras
            current_position = await self._get_current_position(person)
            
            # Identificar múltiples rutas posibles
            possible_paths = await self._generate_career_paths(
                person_id,
                current_position,
                time_horizon
            )
            
            # Evaluar cada ruta según criterios múltiples
            evaluated_paths = []
            for path in possible_paths:
                evaluation = {
                    'path': path,
                    'financial_projection': await self._calculate_financial_projection(path),
                    'satisfaction_score': await self._predict_satisfaction(path, person_id),
                    'market_demand': await self._analyze_market_demand(path),
                    'development_difficulty': await self._calculate_development_difficulty(path, person_id)
                }
                evaluated_paths.append(evaluation)
            
            # Ordenar rutas por puntuación global
            ranked_paths = sorted(
                evaluated_paths, 
                key=lambda x: (
                    x['satisfaction_score'] * 0.4 + 
                    x['market_demand'] * 0.3 + 
                    x['financial_projection']['growth_rate'] * 0.2 - 
                    x['development_difficulty'] * 0.1
                ),
                reverse=True
            )
            
            # Generar puntos de decisión en la trayectoria
            decision_points = self._identify_decision_points(ranked_paths[0]['path'])
            
            # Generar lista de habilidades críticas para toda la trayectoria
            critical_skills = await self._identify_critical_skills(ranked_paths[0]['path'], person_id)
            
            # Opcionalmente incluir recomendaciones de mentores
            mentors = [] 
            if include_mentors:
                mentors = await self._recommend_mentors(person_id, ranked_paths[0]['path'])
            
            # Añadir mensaje motivacional basado en valores
            values_message = self.values_principles.get_values_based_message(
                "desarrollo_profesional",
                {"nombre": person.nombre, "puesto": current_position}
            )
            
            return {
                'person_id': person_id,
                'current_position': current_position,
                'top_paths': [p['path'] for p in ranked_paths[:3]],
                'optimal_path': ranked_paths[0]['path'],
                'critical_skills': critical_skills,
                'decision_points': decision_points,
                'financial_projection': ranked_paths[0]['financial_projection'],
                'market_demand_analysis': ranked_paths[0]['market_demand'],
                'satisfaction_score': ranked_paths[0]['satisfaction_score'],
                'development_difficulty': ranked_paths[0]['development_difficulty'],
                'recommended_mentors': mentors,
                'values_message': values_message,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error prediciendo trayectoria: {str(e)}")
            return self._get_default_path()
    
    async def _get_person(self, person_id: int) -> Optional[Person]:
        """Obtiene la persona por ID."""
        try:
            from app.models import Person
            return await sync_to_async(Person.objects.get)(id=person_id)
        except Exception as e:
            logger.error(f"Error obteniendo Person: {str(e)}")
            return None
    
    async def _get_current_position(self, person) -> str:
        """Obtiene la posición actual del candidato."""
        try:
            # Obtener la experiencia actual
            current_experience = await sync_to_async(
                Experience.objects.filter(
                    person=person,
                    is_current=True
                ).first
            )()
            
            if current_experience:
                return current_experience.position
            return getattr(person, 'current_position', 'Profesional')
        except Exception as e:
            logger.error(f"Error obteniendo posición actual: {str(e)}")
            return 'Profesional'
    
    def _load_market_data(self):
        """Carga datos de mercado para análisis."""
        # Simulación - en un sistema real se cargarían datos de una fuente externa
        return {
            'positions': {
                'Analista Junior': {'demand': 65, 'growth': 3},
                'Analista Senior': {'demand': 75, 'growth': 4},
                'Gerente Junior': {'demand': 80, 'growth': 6},
                'Gerente Senior': {'demand': 85, 'growth': 5},
                'Director': {'demand': 90, 'growth': 4},
                'VP': {'demand': 92, 'growth': 3},
                'C-Level': {'demand': 95, 'growth': 2}
            }
        }
    
    def _load_career_paths(self):
        """Carga trayectorias profesionales típicas."""
        # Esto podría venir de una base de datos o archivo de configuración
        return {
            'huntRED': {
                'Analista': ['Gerente Junior', 'Gerente Senior', 'Director', 'VP', 'C-Level'],
                'Gerente Junior': ['Gerente Senior', 'Director', 'VP', 'C-Level'],
                'Gerente Senior': ['Director', 'VP', 'C-Level'],
            },
            'huntU': {
                'Practicante': ['Analista Junior', 'Analista Senior', 'Especialista', 'Líder de Proyecto'],
                'Analista Junior': ['Analista Senior', 'Especialista', 'Líder de Proyecto'],
            },
            'SEXSI': {
                'Consultor Junior': ['Consultor Senior', 'Especialista', 'Gerente de Cuenta'],
                'Consultor Senior': ['Especialista', 'Gerente de Cuenta'],
            }
        }
    
    async def _generate_career_paths(self, person_id, current_position, time_horizon):
        """Genera múltiples rutas profesionales posibles."""
        # Implementación básica - en un sistema real usaría un algoritmo más sofisticado
        
        # Obtener paths para la BU específica o default a huntRED
        bu_name = self.business_unit or 'huntRED'
        bu_paths = self.career_paths.get(bu_name, self.career_paths['huntRED'])
        
        # Si no hay path específico para esta posición, usar el primero disponible
        position_paths = bu_paths.get(current_position, next(iter(bu_paths.values())))
        
        # Generar múltiples paths con variaciones
        paths = []
        
        # Path estándar (secuencial)
        standard_path = self._create_path_steps(current_position, position_paths, time_horizon)
        paths.append(standard_path)
        
        # Path acelerado (menos tiempo entre posiciones)
        if len(position_paths) > 1:
            accelerated_path = self._create_path_steps(
                current_position, 
                position_paths, 
                time_horizon,
                acceleration=0.7  # 30% más rápido
            )
            paths.append(accelerated_path)
        
        # Path especializado (enfocado en profundizar en una posición)
        if len(position_paths) > 0:
            specialized_path = self._create_path_steps(
                current_position,
                position_paths[:1] * 2,  # Repetir primera posición
                time_horizon,
                specialization=True
            )
            paths.append(specialized_path)
        
        return paths
    
    def _create_path_steps(self, current_position, positions, time_horizon, 
                          acceleration=1.0, specialization=False):
        """Crea los pasos de una trayectoria profesional con tiempos."""
        # Tiempo estándar entre posiciones (meses)
        std_position_time = 24
        
        path = []
        current_month = 0
        
        # Añadir posición actual
        path.append({
            'position': current_position,
            'start_month': 0,
            'end_month': std_position_time * acceleration,
            'is_current': True
        })
        
        current_month = std_position_time * acceleration
        
        # Añadir futuras posiciones
        for i, position in enumerate(positions):
            # Si excedemos el horizonte temporal, parar
            if current_month >= time_horizon:
                break
                
            # Calcular tiempo en esta posición
            position_time = std_position_time
            
            # Para paths especializados, quedarse más tiempo en cada posición
            if specialization:
                position_time *= 1.5
                
            # Ajustar por factor de aceleración
            position_time *= acceleration
            
            # Calcular mes de finalización
            end_month = min(current_month + position_time, time_horizon)
            
            path.append({
                'position': position,
                'start_month': current_month,
                'end_month': end_month,
                'is_current': False
            })
            
            current_month = end_month
        
        return path
    
    async def _calculate_financial_projection(self, path):
        """Calcula la proyección financiera para una trayectoria."""
        # Simulación - en un sistema real esto usaría datos de mercado reales
        
        # Salarios base aproximados por posición
        base_salaries = {
            'Analista Junior': 25000,
            'Analista Senior': 40000,
            'Especialista': 50000,
            'Gerente Junior': 60000,
            'Gerente Senior': 90000,
            'Director': 120000,
            'VP': 200000,
            'C-Level': 350000,
            'Líder de Proyecto': 85000,
            'Gerente de Cuenta': 75000,
            'Consultor Junior': 30000,
            'Consultor Senior': 55000,
            'Practicante': 15000
        }
        
        # Calcular salario para cada etapa del path
        current_position = path[0]['position']
        current_salary = base_salaries.get(current_position, 50000)
        
        projections = []
        for step in path:
            position = step['position']
            step_salary = base_salaries.get(position, current_salary * 1.2)
            
            # Ajustar por tiempo
            month = step['start_month']
            
            projections.append({
                'position': position,
                'month': month,
                'salary': step_salary
            })
            
            current_salary = step_salary
        
        # Calcular métricas
        initial_salary = projections[0]['salary'] if projections else 0
        final_salary = projections[-1]['salary'] if projections else 0
        
        growth_amount = final_salary - initial_salary
        growth_rate = (final_salary / initial_salary - 1) * 100 if initial_salary > 0 else 0
        
        return {
            'initial_salary': initial_salary,
            'final_salary': final_salary,
            'growth_amount': growth_amount,
            'growth_rate': growth_rate,
            'projections': projections
        }
    
    async def _predict_satisfaction(self, path, person_id):
        """Predice satisfacción basada en match de personalidad y posiciones."""
        # Simulación - en un sistema real se usaría un modelo entrenado
        # con datos históricos de satisfacción laboral
        
        # Valor base (0-100)
        base_score = 75
        
        # Ajustar según características del path
        
        # Más posiciones = más oportunidades = mayor satisfacción
        positions_count = len(path)
        positions_factor = min(positions_count * 5, 15)  # Máx +15 puntos
        
        # Tiempo para alcanzar posición final
        time_factor = 0
        if positions_count > 1:
            last_position = path[-1]
            months_to_final = last_position['start_month']
            
            # Menos tiempo es mejor, hasta cierto punto
            if months_to_final < 36:
                time_factor = 10  # Rápido
            elif months_to_final < 48:
                time_factor = 5   # Moderado
            # Más de 48 meses no añade puntos
        
        # Simular satisfacción basada en personalidad
        personality_factor = 0
        try:
            # En un sistema real, esto vendría de un análisis real de personalidad
            from random import randint
            personality_factor = randint(-10, 10)
        except:
            pass
        
        final_score = base_score + positions_factor + time_factor + personality_factor
        
        # Asegurar rango 0-100
        return max(0, min(100, final_score))
    
    async def _analyze_market_demand(self, path):
        """Analiza la demanda del mercado para las posiciones en la trayectoria."""
        # Obtener datos de demanda de mercado
        market_data = self.market_data['positions']
        
        # Calcular demanda para cada posición en el path
        position_demands = []
        for step in path:
            position = step['position']
            demand_data = market_data.get(position, {'demand': 70, 'growth': 3})
            
            position_demands.append({
                'position': position,
                'demand_score': demand_data['demand'],
                'growth_rate': demand_data['growth'],
                'month': step['start_month']
            })
        
        # Calcular promedio ponderado (las posiciones más lejanas tienen menos peso)
        total_weight = 0
        weighted_demand = 0
        
        for i, demand in enumerate(position_demands):
            # Posiciones más cercanas tienen más peso
            weight = 1 / (i + 1)
            total_weight += weight
            weighted_demand += demand['demand_score'] * weight
        
        avg_demand = weighted_demand / total_weight if total_weight > 0 else 70
        
        return {
            'position_demands': position_demands,
            'overall_demand': avg_demand,
            'market_volatility': self._calculate_volatility(position_demands)
        }
    
    def _calculate_volatility(self, position_demands):
        """Calcula la volatilidad de la demanda del mercado."""
        if not position_demands:
            return 'medium'
            
        growth_rates = [p['growth_rate'] for p in position_demands]
        avg_growth = sum(growth_rates) / len(growth_rates)
        
        if avg_growth > 5:
            return 'high'
        elif avg_growth > 2:
            return 'medium'
        else:
            return 'low'
    
    async def _calculate_development_difficulty(self, path, person_id):
        """Calcula la dificultad de desarrollo para seguir esta trayectoria."""
        # Obtener habilidades actuales
        skills = await self._get_person_skills(person_id)
        
        # Obtener habilidades necesarias para el path
        path_skills = await self._identify_critical_skills(path, person_id)
        
        # Calcular gap de habilidades
        skill_gap = 0
        for skill in path_skills:
            current_level = 0
            for current_skill in skills:
                if current_skill['name'].lower() == skill['name'].lower():
                    current_level = current_skill['level']
                    break
            
            gap = max(0, skill['required_level'] - current_level)
            skill_gap += gap
        
        # Normalizar a 0-100
        avg_gap = skill_gap / len(path_skills) if path_skills else 0
        
        # Convertir a dificultad (0-100)
        difficulty = min(100, avg_gap)
        
        return difficulty
    
    async def _get_person_skills(self, person_id):
        """Obtiene las habilidades actuales de la persona."""
        try:
            from app.models import SkillAssessment
            
            person = await self._get_person(person_id)
            if not person:
                return []
                
            # Obtener evaluaciones de habilidades verificadas
            assessments = await sync_to_async(list)(
                SkillAssessment.objects.filter(
                    person=person,
                    is_verified=True
                ).select_related('skill')
            )
            
            # Agrupar evaluaciones por habilidad y calcular promedio
            skill_scores = {}
            for assessment in assessments:
                skill_name = assessment.skill.name
                if skill_name not in skill_scores:
                    skill_scores[skill_name] = {
                        'scores': [],
                        'category': assessment.skill.category
                    }
                skill_scores[skill_name]['scores'].append(assessment.score)
            
            # Calcular promedio de scores por habilidad
            return [
                {
                    'name': skill_name,
                    'level': sum(data['scores']) / len(data['scores']),
                    'category': data['category']
                }
                for skill_name, data in skill_scores.items()
            ]
            
        except Exception as e:
            logger.error(f"Error obteniendo habilidades: {str(e)}")
            return []
    
    async def _identify_critical_skills(self, path, person_id):
        """Identifica habilidades críticas para esta trayectoria."""
        # Simulación - en un sistema real esto se nutriría de datos reales
        
        # Habilidades base para todas las trayectorias
        base_skills = [
            {'name': 'Comunicación efectiva', 'required_level': 70},
            {'name': 'Gestión del tiempo', 'required_level': 65},
            {'name': 'Adaptabilidad', 'required_level': 75}
        ]
        
        # Habilidades por tipo de posición
        position_skills = {
            'Analista': [
                {'name': 'Análisis de datos', 'required_level': 80},
                {'name': 'Atención al detalle', 'required_level': 75}
            ],
            'Gerente': [
                {'name': 'Liderazgo', 'required_level': 85},
                {'name': 'Gestión de equipos', 'required_level': 80},
                {'name': 'Toma de decisiones', 'required_level': 75}
            ],
            'Director': [
                {'name': 'Pensamiento estratégico', 'required_level': 90},
                {'name': 'Negociación', 'required_level': 85},
                {'name': 'Visión de negocio', 'required_level': 85}
            ],
            'Consultor': [
                {'name': 'Presentación', 'required_level': 85},
                {'name': 'Resolución de problemas', 'required_level': 80}
            ],
            'Especialista': [
                {'name': 'Conocimiento técnico profundo', 'required_level': 90},
                {'name': 'Investigación', 'required_level': 85}
            ]
        }
        
        # Recopilar habilidades para cada posición en el path
        skills = base_skills.copy()
        
        for step in path:
            position = step['position']
            
            # Buscar habilidades según tipo de posición
            for position_type, position_type_skills in position_skills.items():
                if position_type in position:
                    for skill in position_type_skills:
                        # Evitar duplicados
                        if not any(s['name'] == skill['name'] for s in skills):
                            skills.append(skill)
        
        # Ordenar por nivel requerido
        return sorted(skills, key=lambda x: x['required_level'], reverse=True)
    
    def _identify_decision_points(self, path):
        """Identifica puntos de decisión críticos en la trayectoria."""
        # Buscar posiciones donde hay múltiples opciones
        decision_points = []
        
        for i, step in enumerate(path):
            if i == 0:  # Omitir posición actual
                continue
                
            position = step['position']
            month = step['start_month']
            
            # En un sistema real, esto identificaría puntos de bifurcación
            # en la trayectoria profesional
            
            # Simulación - consideramos cada cambio de posición un punto de decisión
            decision_points.append({
                'month': month - 3,  # 3 meses antes del cambio
                'current_position': path[i-1]['position'],
                'next_position': position,
                'options': [
                    {'position': position, 'probability': 0.7},
                    {'position': f"Senior {path[i-1]['position']}", 'probability': 0.3}
                ],
                'preparation_activities': [
                    f"Certificación en {position}",
                    f"Networking con profesionales en {position}",
                    f"Proyecto demostrativo de habilidades para {position}"
                ]
            })
        
        return decision_points
    
    async def _recommend_mentors(self, person_id, path):
        """Recomienda mentores para esta trayectoria profesional."""
        # En un sistema real, esto buscaría mentores relevantes en una base de datos
        # Simulación - generar mentores ficticios
        
        target_positions = [step['position'] for step in path[1:]][:2]  # Próximas 2 posiciones
        
        mentors = []
        for position in target_positions:
            mentors.append({
                'name': f"Mentor para {position}",
                'position': f"Senior {position}",
                'years_experience': 7 + (target_positions.index(position) * 3),
                'match_score': 85 - (target_positions.index(position) * 5),
                'specialties': [
                    f"Transición a {position}",
                    "Desarrollo de liderazgo",
                    "Networking efectivo"
                ],
                'availability': "2 horas/mes"
            })
        
        return mentors
    
    def _get_default_path(self):
        """Retorna una trayectoria predeterminada en caso de error."""
        return {
            'current_position': 'Profesional',
            'top_paths': [{
                'position': 'Especialista',
                'start_month': 0,
                'end_month': 24,
                'is_current': False
            }],
            'critical_skills': [
                {'name': 'Comunicación efectiva', 'required_level': 70},
                {'name': 'Adaptabilidad', 'required_level': 75},
                {'name': 'Resolución de problemas', 'required_level': 80}
            ],
            'decision_points': [],
            'financial_projection': {
                'initial_salary': 50000,
                'final_salary': 75000,
                'growth_rate': 50
            },
            'analyzed_at': datetime.now().isoformat()
        }
