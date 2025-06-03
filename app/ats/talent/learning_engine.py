# /home/pablo/app/com/talent/learning_engine.py
"""
Motor de Microaprendizaje.

Este módulo proporciona recomendaciones de aprendizaje personalizadas
basadas en brechas de habilidades y objetivos de carrera.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os

import numpy as np
from asgiref.sync import sync_to_async
from django.conf import settings

from app.models import Person, Skill, SkillAssessment
from app.ats.talent.trajectory_analyzer import TrajectoryAnalyzer
from app.ats.chatbot.values.core import ValuesPrinciples

logger = logging.getLogger(__name__)

class LearningEngine:
    """
    Motor de recomendación de aprendizaje contextual y personalizado.
    
    Proporciona recursos de aprendizaje en el momento óptimo según las
    necesidades del usuario, sus preferencias de aprendizaje y objetivos profesionales.
    """
    
    # Tipos de recursos de aprendizaje 
    RESOURCE_TYPES = [
        "Artículo", "Video", "Curso", "Libro", "Podcast", 
        "Webinar", "Ejercicio práctico", "Mentor", "Comunidad"
    ]
    
    # Modos de aprendizaje
    LEARNING_MODES = {
        "Teórico": ["Artículo", "Libro", "Podcast"],
        "Práctico": ["Ejercicio práctico", "Proyecto", "Simulación"],
        "Social": ["Mentor", "Comunidad", "Workshop"],
        "Visual": ["Video", "Infografía", "Diagrama"],
        "Auditivo": ["Podcast", "Audiobook", "Webinar"]
    }
    
    def __init__(self):
        """Inicializa el motor de aprendizaje."""
        self.values_principles = ValuesPrinciples()
        self.trajectory_analyzer = TrajectoryAnalyzer()
        self.resource_cache = {}
        
        # Usar el nuevo implementador para el análisis real
        try:
            from app.ats.ml.analyzers.learning_analyzer import LearningAnalyzerImpl
            self._impl = LearningAnalyzerImpl()
            self._using_new_impl = True
            logger.info("LearningEngine usando implementación mejorada")
        except ImportError:
            self._using_new_impl = False
            logger.warning("LearningEngine usando implementación original (no se encontró la mejorada)")
        except Exception as e:
            self._using_new_impl = False
            logger.error(f"Error al inicializar implementación mejorada: {str(e)}")
        
    async def generate_learning_sequence(self, 
                                      person_id: int, 
                                      skill_gap: Optional[Dict] = None,
                                      context: str = 'job_search') -> Dict:
        """
        Genera una secuencia personalizada de aprendizaje.
        
        Args:
            person_id: ID del usuario
            skill_gap: Diccionario de habilidades a desarrollar y niveles objetivo (opcional)
            context: Contexto del usuario ('job_search', 'new_position', 'development')
            
        Returns:
            Dict con secuencia de aprendizaje y timing óptimo
        """
        # Si tenemos disponible la implementación mejorada, usarla
        if hasattr(self, '_using_new_impl') and self._using_new_impl:
            try:
                # Preparar datos para el nuevo analyzer
                data = {
                    'person_id': person_id,
                    'skill_gap': skill_gap,
                    'context': context
                }
                
                # Llamar al implementador con los datos
                # Usamos sync_to_async para convertir el método sincrónico a asíncrono
                # ya que los analyzers implementan interfaces sincrónicas
                from asgiref.sync import sync_to_async
                analyze_async = sync_to_async(self._impl.analyze)
                result = await analyze_async(data, None)
                
                # Registrar uso exitoso
                logger.info(f"Usando implementación mejorada para generar secuencia de aprendizaje de persona {person_id}")
                
                return result
            except Exception as e:
                # Si falla la nueva implementación, caer al método original
                logger.error(f"Error en implementación mejorada: {str(e)}. Usando original.")
        
        # Implementación original como fallback
        try:
            # Obtener información del usuario
            person_data = await self._get_person_data(person_id)
            if not person_data:
                return self._get_default_sequence()
            
            # Si no se proporciona gap específico, identificarlo
            if not skill_gap:
                skill_gap = await self._identify_skill_gap(person_id, context)
            
            # Obtener preferencias de aprendizaje
            learning_preferences = await self._get_learning_preferences(person_id)
            
            # Filtrar recursos relevantes
            relevant_resources = await self._filter_relevant_resources(
                skill_gap,
                learning_preferences
            )
            
            # Ordenar por efectividad y preferencia
            ordered_resources = await self._order_by_effectiveness(
                relevant_resources,
                learning_preferences,
                person_data
            )
            
            # Crear secuencia con tiempos óptimos
            learning_sequence = []
            for skill_name, gap_info in skill_gap.items():
                # Recursos para esta habilidad
                skill_resources = [r for r in ordered_resources if skill_name in r['skills']]
                
                # Límite de recursos por habilidad
                max_resources = min(3, len(skill_resources))
                top_resources = skill_resources[:max_resources]
                
                for i, resource in enumerate(top_resources):
                    timing_days = i * 7  # Una semana entre recursos
                    
                    sequence_item = {
                        'resource': resource,
                        'skill': skill_name,
                        'current_level': gap_info['current_level'],
                        'target_level': gap_info['target_level'],
                        'gap': gap_info['gap'],
                        'timing_days': timing_days,
                        'impact': self._predict_impact(resource, gap_info),
                        'prerequisites': self._get_prerequisites(resource, skill_gap)
                    }
                    
                    learning_sequence.append(sequence_item)
            
            # Calcular duración total
            total_duration_days = max([item['timing_days'] for item in learning_sequence]) if learning_sequence else 0
            # Añadir duración promedio de recursos
            if learning_sequence:
                avg_resource_days = sum([item['resource'].get('duration_hours', 0) for item in learning_sequence]) / len(learning_sequence) / 2  # Asumiendo 2 horas/día
                total_duration_days += avg_resource_days
            
            # Compilar resultado
            result = {
                'person_id': person_id,
                'context': context,
                'skill_gap': skill_gap,
                'learning_sequence': learning_sequence,
                'estimated_duration_days': round(total_duration_days),
                'total_resources': len(learning_sequence),
                'generated_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generando secuencia de aprendizaje: {str(e)}")
            return self._get_default_sequence()
    
    async def _get_person_data(self, person_id: int) -> Optional[Dict]:
        """Obtiene datos básicos de la persona."""
        try:
            from app.models import Person
            
            person = await sync_to_async(Person.objects.get)(id=person_id)
            
            return {
                'id': person_id,
                'name': f"{person.first_name} {person.last_name}",
                'current_position': getattr(person, 'current_position', 'Profesional'),
                'years_experience': getattr(person, 'years_experience', 5)
            }
        except Exception as e:
            logger.error(f"Error obteniendo datos de persona: {str(e)}")
            return None
    
    async def _identify_skill_gap(self, person_id: int, context: str) -> Dict[str, Dict]:
        """Identifica brechas de habilidades para desarrollo."""
        try:
            # Obtener habilidades actuales
            current_skills = await self._get_person_skills(person_id)
            
            # Según el contexto, obtener habilidades objetivo de diferentes formas
            if context == 'job_search':
                # Para búsqueda de empleo, usar trayectoria óptima
                trajectory = await self.trajectory_analyzer.predict_optimal_path(person_id)
                target_skills = trajectory.get('critical_skills', [])
                
            elif context == 'new_position':
                # Para nueva posición, usar habilidades críticas para ese rol
                # En un sistema real, esto vendría de datos de la vacante
                target_skills = self._get_default_role_skills('Gerente')  # Simplificado
                
            else:  # 'development' u otros
                # Para desarrollo general, usar habilidades tendencia
                target_skills = self._get_trending_skills()
            
            # Calcular brecha para cada habilidad
            skill_gap = {}
            
            for target in target_skills:
                skill_name = target['name']
                required_level = target.get('required_level', 80)
                
                # Buscar nivel actual
                current_level = 0
                for skill in current_skills:
                    if skill['name'].lower() == skill_name.lower():
                        current_level = skill['level']
                        break
                
                # Calcular gap (si existe)
                gap = max(0, required_level - current_level)
                
                if gap > 10:  # Solo considerar gaps significativos
                    skill_gap[skill_name] = {
                        'current_level': current_level,
                        'target_level': required_level,
                        'gap': gap,
                        'priority': 'high' if gap > 30 else ('medium' if gap > 20 else 'low')
                    }
            
            return skill_gap
            
        except Exception as e:
            logger.error(f"Error identificando skill gap: {str(e)}")
            return {"Comunicación efectiva": {"current_level": 50, "target_level": 80, "gap": 30, "priority": "high"}}
    
    async def _get_person_skills(self, person_id: int) -> List[Dict]:
        """Obtiene las habilidades actuales de la persona."""
        try:
            from app.models import SkillAssessment
            
            person = await sync_to_async(Person.objects.get)(id=person_id)
            
            # Obtener evaluaciones de habilidades
            assessments = await sync_to_async(list)(
                SkillAssessment.objects.filter(person=person).select_related('skill')
            )
            
            return [
                {
                    'name': assessment.skill.name,
                    'level': assessment.score,
                    'category': assessment.skill.category,
                    'assessment_date': assessment.assessment_date
                }
                for assessment in assessments
            ]
        except Exception as e:
            logger.error(f"Error obteniendo habilidades: {str(e)}")
            return []
    
    def _get_default_role_skills(self, role: str) -> List[Dict]:
        """Obtiene habilidades relevantes para un rol específico."""
        # Simplificado - en un sistema real vendría de una base de datos de roles
        role_skills = {
            'Analista': [
                {'name': 'Análisis de datos', 'required_level': 80},
                {'name': 'Resolución de problemas', 'required_level': 75},
                {'name': 'Atención al detalle', 'required_level': 85}
            ],
            'Gerente': [
                {'name': 'Liderazgo', 'required_level': 85},
                {'name': 'Gestión de equipos', 'required_level': 80},
                {'name': 'Comunicación efectiva', 'required_level': 85},
                {'name': 'Toma de decisiones', 'required_level': 80}
            ],
            'Desarrollador': [
                {'name': 'Programación', 'required_level': 85},
                {'name': 'Resolución de problemas', 'required_level': 80},
                {'name': 'Trabajo en equipo', 'required_level': 75}
            ]
        }
        
        return role_skills.get(role, [
            {'name': 'Comunicación efectiva', 'required_level': 80},
            {'name': 'Adaptabilidad', 'required_level': 75}
        ])
    
    def _get_trending_skills(self) -> List[Dict]:
        """Obtiene habilidades tendencia en el mercado laboral."""
        # Simplificado - en un sistema real vendría de análisis de mercado
        return [
            {'name': 'Inteligencia Artificial', 'required_level': 70},
            {'name': 'Análisis de datos', 'required_level': 75},
            {'name': 'Transformación digital', 'required_level': 70},
            {'name': 'Resiliencia', 'required_level': 80},
            {'name': 'Aprendizaje continuo', 'required_level': 85}
        ]
    
    async def _get_learning_preferences(self, person_id: int) -> Dict:
        """Obtiene preferencias de aprendizaje del usuario."""
        try:
            # En un sistema real, esto vendría de la base de datos
            # Para esta demo, simulamos preferencias
            
            # Usar ID para crear preferencias consistentes
            import hashlib
            import random
            
            seed = int(hashlib.md5(str(person_id).encode()).hexdigest(), 16) % 10000
            random.seed(seed)
            
            # Modos de aprendizaje preferidos (elegir 2-3)
            modes = list(self.LEARNING_MODES.keys())
            preferred_modes = random.sample(modes, random.randint(2, 3))
            
            # Tipos de recursos preferidos
            preferred_types = []
            for mode in preferred_modes:
                preferred_types.extend(self.LEARNING_MODES[mode][:2])
            
            # Eliminar duplicados
            preferred_types = list(set(preferred_types))
            
            # Duración preferida (minutos)
            preferred_durations = random.choice([
                [5, 15],    # Corto
                [15, 30],   # Medio
                [30, 60],   # Largo
                [5, 60]     # Cualquiera
            ])
            
            # Frecuencia preferida (días)
            preferred_frequency = random.choice([1, 2, 3, 7])
            
            return {
                'preferred_modes': preferred_modes,
                'preferred_resource_types': preferred_types,
                'preferred_duration_range': preferred_durations,
                'preferred_frequency_days': preferred_frequency,
                'prefers_interactive': random.choice([True, False]),
                'prefers_structured': random.choice([True, False])
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo preferencias: {str(e)}")
            return {
                'preferred_modes': ['Práctico', 'Visual'],
                'preferred_resource_types': ['Video', 'Ejercicio práctico'],
                'preferred_duration_range': [15, 30],
                'preferred_frequency_days': 3,
                'prefers_interactive': True,
                'prefers_structured': True
            }
    
    async def _filter_relevant_resources(self, skill_gap: Dict, preferences: Dict) -> List[Dict]:
        """Filtra recursos relevantes para las habilidades objetivo."""
        # En un sistema real, esto consultaría una base de datos de recursos
        # Para esta demo, utilizamos recursos simulados
        
        all_resources = []
        
        for skill_name in skill_gap.keys():
            # Intentar cargar del caché
            if skill_name in self.resource_cache:
                skill_resources = self.resource_cache[skill_name]
            else:
                # Generar recursos simulados para esta habilidad
                skill_resources = self._generate_mock_resources(skill_name)
                self.resource_cache[skill_name] = skill_resources
            
            all_resources.extend(skill_resources)
        
        # Aplicar filtros según preferencias
        filtered_resources = []
        
        for resource in all_resources:
            # Filtrar por tipo
            if preferences.get('preferred_resource_types'):
                if resource['type'] not in preferences['preferred_resource_types']:
                    continue
            
            # Filtrar por duración
            if preferences.get('preferred_duration_range'):
                min_duration, max_duration = preferences['preferred_duration_range']
                if not (min_duration <= resource['duration_minutes'] <= max_duration):
                    continue
            
            # Filtrar por interactividad
            if preferences.get('prefers_interactive') is not None:
                if preferences['prefers_interactive'] != resource.get('is_interactive', False):
                    continue
            
            filtered_resources.append(resource)
        
        return filtered_resources
    
    def _generate_mock_resources(self, skill_name: str) -> List[Dict]:
        """Genera recursos simulados para una habilidad."""
        import random
        
        # Usar nombre de habilidad para seed consistente
        seed = hash(skill_name) % 10000
        random.seed(seed)
        
        # Crear 5-10 recursos por habilidad
        num_resources = random.randint(5, 10)
        resources = []
        
        for i in range(num_resources):
            resource_type = random.choice(self.RESOURCE_TYPES)
            
            # Ajustar duración según tipo
            if resource_type in ['Artículo', 'Podcast', 'Video']:
                duration = random.randint(5, 45)
            elif resource_type in ['Curso', 'Libro']:
                duration = random.randint(60, 480)
            else:
                duration = random.randint(15, 90)
            
            # Determinar nivel
            levels = ['Principiante', 'Intermedio', 'Avanzado']
            level_weights = [0.3, 0.5, 0.2]
            level = random.choices(levels, weights=level_weights, k=1)[0]
            
            # Crear recurso
            resource = {
                'id': f"{skill_name.replace(' ', '_')}_{i}",
                'title': f"{resource_type} sobre {skill_name} - {i+1}",
                'type': resource_type,
                'skills': [skill_name],
                'level': level,
                'duration_minutes': duration,
                'is_interactive': resource_type in ['Ejercicio práctico', 'Simulación', 'Workshop'],
                'provider': random.choice(['Coursera', 'Udemy', 'LinkedIn Learning', 'HuntRED Academy']),
                'effectiveness_score': random.randint(65, 95),
                'popularity_score': random.randint(1, 100),
                'description': f"Recurso para desarrollar la habilidad de {skill_name}.",
                'url': f"https://example.com/learn/{skill_name.replace(' ', '_')}/{i}"
            }
            
            resources.append(resource)
        
        return resources
    
    async def _order_by_effectiveness(self, resources: List[Dict], preferences: Dict, person_data: Dict) -> List[Dict]:
        """Ordena recursos por efectividad y ajuste a preferencias."""
        # Calcular puntuación de ajuste para cada recurso
        for resource in resources:
            # Base: effectiveness_score
            score = resource.get('effectiveness_score', 70)
            
            # Ajustar por tipo de recurso preferido
            if resource['type'] in preferences.get('preferred_resource_types', []):
                score += 10
            
            # Ajustar por nivel de experiencia
            years_exp = person_data.get('years_experience', 3)
            if (years_exp < 2 and resource['level'] == 'Principiante') or \
               (2 <= years_exp <= 5 and resource['level'] == 'Intermedio') or \
               (years_exp > 5 and resource['level'] == 'Avanzado'):
                score += 5
            
            # Ajustar por popularidad (menor efecto)
            score += min(5, resource.get('popularity_score', 0) / 20)
            
            # Guardar puntuación en el recurso
            resource['fit_score'] = min(100, score)
        
        # Ordenar por puntuación de ajuste
        return sorted(resources, key=lambda x: x.get('fit_score', 0), reverse=True)
    
    def _predict_impact(self, resource: Dict, gap_info: Dict) -> Dict:
        """Predice el impacto de un recurso en cerrar la brecha de habilidad."""
        # Calcular impacto base según efectividad y tipo
        effectiveness = resource.get('effectiveness_score', 70) / 100
        
        # Factores por tipo (algunos tipos tienen más impacto en el aprendizaje)
        type_factors = {
            'Curso': 1.0,
            'Ejercicio práctico': 0.9,
            'Mentor': 0.9,
            'Proyecto': 0.8,
            'Video': 0.7,
            'Libro': 0.7,
            'Webinar': 0.6,
            'Artículo': 0.5,
            'Podcast': 0.5,
            'Infografía': 0.3
        }
        
        type_factor = type_factors.get(resource['type'], 0.6)
        
        # Estimar puntos de mejora (sobre 100)
        max_improvement = 15  # Máximo por un solo recurso
        improvement_points = effectiveness * type_factor * max_improvement
        
        # Estimar nuevo nivel después del recurso
        current_level = gap_info['current_level']
        new_level = min(100, current_level + improvement_points)
        
        # Calcular porcentaje de brecha cerrada
        gap = gap_info['gap']
        gap_closed_percent = (improvement_points / gap) * 100 if gap > 0 else 100
        
        return {
            'improvement_points': round(improvement_points, 1),
            'expected_new_level': round(new_level, 1),
            'gap_closed_percent': min(100, round(gap_closed_percent, 1))
        }
    
    def _get_prerequisites(self, resource: Dict, skill_gap: Dict) -> List[str]:
        """Determina prerequeridos para un recurso si existen."""
        # Simplificado - en un sistema real analizaría dependencias entre habilidades
        level = resource.get('level', 'Intermedio')
        
        # Recursos avanzados pueden necesitar cierto nivel en otras habilidades
        if level == 'Avanzado' and len(skill_gap) > 1:
            # Seleccionar aleatoriamente otras habilidades como prerequerido
            import random
            
            skills = list(skill_gap.keys())
            main_skill = resource['skills'][0]
            other_skills = [s for s in skills if s != main_skill]
            
            if other_skills:
                # 50% de probabilidad de tener prerequerido
                if random.random() > 0.5:
                    return random.sample(other_skills, min(1, len(other_skills)))
        
        return []
    
    def _get_default_sequence(self) -> Dict:
        """Retorna una secuencia de aprendizaje predeterminada vacía."""
        return {
            'skill_gap': {},
            'learning_sequence': [],
            'estimated_duration_days': 0,
            'total_resources': 0,
            'generated_at': datetime.now().isoformat()
        }
