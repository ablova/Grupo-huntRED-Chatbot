# /home/pablo/app/com/talent/intervention_system.py
"""
Sistema de Intervención para Retención.

Este módulo proporciona recomendaciones personalizadas para acciones
de intervención que mejoren la retención de talento valioso.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

import numpy as np
from asgiref.sync import sync_to_async
from django.conf import settings

from app.models import Person, Manager, InterventionAction, PerformanceReview, Activity, BusinessUnit, Mentor, MentorSkill, MentorSession
from app.ats.talent.retention_predictor import RetentionPredictor
from app.ats.chatbot.values.principles import ValuesPrinciples

# Importar el nuevo analizador si está disponible
try:
    from app.ats.ml.analyzers.intervention_analyzer import InterventionAnalyzerImpl
    USE_NEW_ANALYZER = True
except ImportError:
    USE_NEW_ANALYZER = False
    logger = logging.getLogger(__name__)
    logger.warning("InterventionAnalyzerImpl no encontrado, usando implementación original")

logger = logging.getLogger(__name__)

class InterventionSystem:
    """
    Sistema de intervención para retención de talento.
    
    Genera planes personalizados de intervención basados en
    factores causales de riesgo de desvinculación.
    """
    
    def __init__(self):
        """Inicializa el sistema de intervención."""
        self.retention_predictor = RetentionPredictor()
        self.values_principles = ValuesPrinciples()
        
        # Inicializar el nuevo analizador si está disponible
        if USE_NEW_ANALYZER:
            self.analyzer = InterventionAnalyzerImpl()
        
    async def generate_intervention_plan(self, 
                                        person_id: int,
                                        causal_factors: Optional[List[Dict]] = None) -> Dict:
        """
        Genera un plan de intervención personalizado basado en los factores de riesgo identificados.
        
        Args:
            person_id: ID de la persona
            causal_factors: Factores causales (opcional, si ya se conocen)
            
        Returns:
            Plan de intervención con acciones recomendadas
        """
        # Usar el nuevo analizador si está disponible
        if USE_NEW_ANALYZER:
            try:
                # Obtener el contexto de business unit si es necesario
                person = await self._get_person(person_id)
                business_unit = getattr(person, 'business_unit', None)
                
                # Si no se especificaron factores causales, obtenerlos del predictor de retención
                if not causal_factors:
                    retention_analysis = await self.retention_predictor.analyze_retention_risk(person_id)
                    causal_factors = retention_analysis.get('causal_factors', [])
                
                # Preparar datos para el analizador
                data = {
                    'person_id': person_id,
                    'risk_factors': causal_factors
                }
                
                # Usar el nuevo analizador
                result = self.analyzer.analyze(data, business_unit)
                
                # Registrar el plan generado
                await self._log_intervention_plan(person_id, result)
                
                return result
            except Exception as e:
                logger.error(f"Error usando nuevo analizador: {str(e)}. Volviendo a implementación original.")
                # Fallback a la implementación original
        
        # Implementación original si el nuevo analizador no está disponible o falla
        try:
            # Obtener datos de la persona
            person = await self._get_person(person_id)
            if not person:
                logger.warning(f"Persona con ID {person_id} no encontrada")
                return self._get_default_plan(person_id)
            
            # Si no se especificaron factores causales, obtenerlos del predictor de retención
            if not causal_factors:
                retention_analysis = await self.retention_predictor.analyze_retention_risk(person_id)
                causal_factors = retention_analysis.get('causal_factors', [])
                risk_level = retention_analysis.get('risk_level', 'medium')
            else:
                # Determinar nivel de riesgo basado en factores proporcionados
                avg_risk = sum([factor.get('risk', 50) for factor in causal_factors]) / len(causal_factors) if causal_factors else 50
                risk_level = 'high' if avg_risk >= 75 else 'medium' if avg_risk >= 50 else 'low'
            
            # Generar intervenciones para cada factor causal
            interventions = []
            for factor in causal_factors:
                factor_name = factor.get('factor')
                if not factor_name or factor_name == 'insufficient_data':
                    continue
                    
                intervention = await self._generate_factor_intervention(factor, person_id, person)
                if intervention:
                    interventions.append(intervention)
            
            # Determinar métricas de éxito basadas en los factores
            success_metrics = self._determine_success_metrics(causal_factors)
            
            # Crear programación de seguimiento basada en nivel de riesgo
            follow_up_schedule = self._create_follow_up_schedule(risk_level)
            
            # Generar recomendaciones de capacitación
            training_recommendations = await self._recommend_training(causal_factors, person_id)
            
            # Identificar necesidad de un mentor específico
            mentor_recommendation = await self._recommend_mentor(causal_factors, person_id)
            
            # Crear reporte final
            plan = {
                'person_id': person_id,
                'risk_level': risk_level,
                'interventions': interventions,
                'success_metrics': success_metrics,
                'follow_up_schedule': follow_up_schedule,
                'training_recommendations': training_recommendations,
                'mentor_recommendation': mentor_recommendation,
                'plan_duration': '90 days' if risk_level == 'high' else '180 days',
                'generated_at': datetime.now().isoformat()
            }
            
            # Registrar el plan para seguimiento
            await self._log_intervention_plan(person_id, plan)
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generando plan de intervención: {str(e)}")
            return self._get_default_plan(person_id)
            
    async def _get_person(self, person_id: int) -> Optional[Person]:
        """Obtiene los datos de la persona desde la base de datos."""
        try:
            # Usando Django sync_to_async para operaciones de BD
            from app.models import Person
            get_person = sync_to_async(lambda: Person.objects.filter(id=person_id).first())()
            return await get_person
        except Exception as e:
            logger.error(f"Error obteniendo datos de persona {person_id}: {str(e)}")
            return None
    
    async def _generate_factor_intervention(self, factor: Dict, person_id: int, person: Person) -> Optional[Dict]:
        """Genera intervenciones específicas para un factor causal."""
        factor_name = factor.get('factor')
        trend = factor.get('trend', 'stable')
        risk = factor.get('risk', 50)
        
        # Determinar urgencia basada en riesgo
        urgency = 'high' if risk >= 75 else 'medium' if risk >= 50 else 'low'
        
        # Intervenciones basadas en el factor
        if factor_name == 'job_satisfaction':
            return {
                'factor': 'job_satisfaction',
                'factor_label': 'Satisfacción Laboral',
                'current_score': factor.get('score', 50),
                'target_score': min(factor.get('score', 50) + 15, 100),
                'actions': [
                    {
                        'action': 'Realizar reunión de check-in personalizada',
                        'description': 'Sesión uno a uno para identificar áreas específicas de insatisfacción',
                        'owner': 'manager',
                        'timeline': '1 week' if urgency == 'high' else '2 weeks',
                        'expected_impact': 'high'
                    },
                    {
                        'action': 'Programa de reconocimiento específico',
                        'description': 'Implementar sistema personalizado de reconocimiento basado en preferencias',
                        'owner': 'hr',
                        'timeline': '1 month',
                        'expected_impact': 'medium'
                    }
                ]
            }
            
        elif factor_name == 'career_growth':
            return {
                'factor': 'career_growth',
                'factor_label': 'Desarrollo Profesional',
                'current_score': factor.get('score', 50),
                'target_score': min(factor.get('score', 50) + 20, 100),
                'actions': [
                    {
                        'action': 'Crear plan de desarrollo personalizado',
                        'description': 'Definir objetivos de carrera a corto y mediano plazo con acciones específicas',
                        'owner': 'manager',
                        'timeline': '2 weeks',
                        'expected_impact': 'high'
                    },
                    {
                        'action': 'Asignar a proyecto estratégico',
                        'description': 'Identificar proyecto de alto impacto alineado con intereses de desarrollo',
                        'owner': 'manager',
                        'timeline': '1 month',
                        'expected_impact': 'high'
                    },
                    {
                        'action': 'Revisar opciones de movilidad interna',
                        'description': 'Explorar oportunidades de rotación o promoción en la organización',
                        'owner': 'hr',
                        'timeline': '3 months',
                        'expected_impact': 'medium'
                    }
                ]
            }
            
        elif factor_name == 'compensation_satisfaction':
            return {
                'factor': 'compensation_satisfaction',
                'factor_label': 'Compensación',
                'current_score': factor.get('score', 50),
                'target_score': min(factor.get('score', 50) + 15, 100),
                'actions': [
                    {
                        'action': 'Realizar análisis comparativo salarial',
                        'description': 'Comparar compensación actual con mercado y equidad interna',
                        'owner': 'hr',
                        'timeline': '2 weeks',
                        'expected_impact': 'medium'
                    },
                    {
                        'action': 'Revisar paquete de beneficios',
                        'description': 'Ajustar beneficios no monetarios según preferencias personales',
                        'owner': 'hr',
                        'timeline': '1 month',
                        'expected_impact': 'medium'
                    }
                ]
            }
            
        elif factor_name == 'work_life_balance':
            return {
                'factor': 'work_life_balance',
                'factor_label': 'Balance Vida-Trabajo',
                'current_score': factor.get('score', 50),
                'target_score': min(factor.get('score', 50) + 20, 100),
                'actions': [
                    {
                        'action': 'Analizar carga de trabajo actual',
                        'description': 'Evaluar distribución de tareas y establecer prioridades claras',
                        'owner': 'manager',
                        'timeline': 'immediate' if urgency == 'high' else '1 week',
                        'expected_impact': 'high'
                    },
                    {
                        'action': 'Implementar acuerdos de flexibilidad',
                        'description': 'Definir horarios o modalidades de trabajo que favorezcan mejor balance',
                        'owner': 'manager',
                        'timeline': '2 weeks',
                        'expected_impact': 'high'
                    }
                ]
            }
            
        elif factor_name == 'engagement':
            return {
                'factor': 'engagement',
                'factor_label': 'Compromiso y Motivación',
                'current_score': factor.get('score', 50),
                'target_score': min(factor.get('score', 50) + 15, 100),
                'actions': [
                    {
                        'action': 'Identificar motivadores personales',
                        'description': 'Realizar evaluación de factores motivacionales específicos',
                        'owner': 'manager',
                        'timeline': '1 week',
                        'expected_impact': 'high'
                    },
                    {
                        'action': 'Asignar responsabilidades de liderazgo',
                        'description': 'Delegar tareas que incrementen autonomía y sentido de propósito',
                        'owner': 'manager',
                        'timeline': '1 month',
                        'expected_impact': 'high'
                    }
                ]
            }
            
        elif factor_name == 'performance_trend':
            return {
                'factor': 'performance_trend',
                'factor_label': 'Desempeño',
                'current_score': factor.get('score', 50),
                'target_score': min(factor.get('score', 50) + 15, 100),
                'actions': [
                    {
                        'action': 'Crear plan de mejora de desempeño',
                        'description': 'Identificar áreas específicas de desarrollo con metas claras',
                        'owner': 'manager',
                        'timeline': '1 week',
                        'expected_impact': 'high'
                    },
                    {
                        'action': 'Implementar sesiones de coaching',
                        'description': 'Programar sesiones periódicas de feedback y desarrollo',
                        'owner': 'manager',
                        'timeline': 'ongoing',
                        'expected_impact': 'high'
                    }
                ]
            }
        
        return None
    
    def _determine_success_metrics(self, causal_factors: List[Dict]) -> List[str]:
        """Determina métricas de éxito apropiadas para el plan de intervención."""
        metrics = [
            'Mejora en índice general de satisfacción',
            'Reducción de riesgo de rotación'
        ]
        
        # Agregar métricas específicas según los factores causales
        factor_metrics = {
            'job_satisfaction': [
                'Mejora en puntuación de satisfacción laboral',
                'Incremento en encuestas de clima favorable'
            ],
            'career_growth': [
                'Claridad en objetivos de carrera',
                'Percepción positiva de oportunidades de crecimiento'
            ],
            'compensation_satisfaction': [
                'Mejora en percepción de equidad salarial',
                'Satisfacción con paquete total de compensación'
            ],
            'work_life_balance': [
                'Reducción en horas extra trabajadas',
                'Mejora en indicadores de bienestar'
            ],
            'engagement': [
                'Incremento en participación en iniciativas',
                'Mayor nivel de contribuciones voluntarias'
            ],
            'performance_trend': [
                'Mejora en evaluaciones de desempeño',
                'Incremento en productividad medible'
            ]
        }
        
        # Agregar métricas relevantes basadas en los factores
        for factor in causal_factors:
            factor_name = factor.get('factor')
            if factor_name in factor_metrics:
                metrics.extend(factor_metrics[factor_name])
        
        # Eliminar duplicados y limitar a 5 métricas para no sobrecargar
        return list(dict.fromkeys(metrics))[:5]
    
    def _create_follow_up_schedule(self, risk_level: str) -> Dict:
        """Crea una programación de seguimiento basada en el nivel de riesgo."""
        # Ajustar frecuencia según nivel de riesgo
        if risk_level == 'high':
            return {
                'first_check': '2 weeks',
                'second_check': '30 days',
                'third_check': '60 days',
                'final_assessment': '90 days',
                'check_format': 'Reunión personal con consultor huntRED® y gerente directo',
                'frequency': 'Alta - Seguimiento quincenal'
            }
        elif risk_level == 'medium':
            return {
                'first_check': '30 days',
                'second_check': '60 days',
                'third_check': '90 days',
                'final_assessment': '120 days',
                'check_format': 'Alternando reuniones personales y reportes de progreso',
                'frequency': 'Media - Seguimiento mensual'
            }
        else:  # low
            return {
                'first_check': '45 days',
                'second_check': '90 days',
                'final_assessment': '180 days',
                'check_format': 'Reportes de progreso y reunión final',
                'frequency': 'Baja - Seguimiento trimestral'
            }
    
    async def _recommend_training(self, causal_factors: List[Dict], person_id: int) -> List[Dict]:
        """Genera recomendaciones de capacitación basadas en factores causales."""
        training_recommendations = []
        
        # Mapeo de factores a entrenamientos recomendados
        training_map = {
            'job_satisfaction': [
                {
                    'name': 'Gestión efectiva de expectativas laborales',
                    'type': 'Workshop',
                    'duration': '4 hours',
                    'priority': 'medium'
                }
            ],
            'career_growth': [
                {
                    'name': 'Diseño estratégico de carrera',
                    'type': 'Course',
                    'duration': '8 hours',
                    'priority': 'high'
                },
                {
                    'name': 'Autogestión profesional en mercados dinámicos',
                    'type': 'Workshop',
                    'duration': '6 hours',
                    'priority': 'medium'
                }
            ],
            'performance_trend': [
                {
                    'name': 'Productividad y gestión del tiempo',
                    'type': 'Course',
                    'duration': '8 hours',
                    'priority': 'high'
                }
            ],
            'work_life_balance': [
                {
                    'name': 'Técnicas de manejo de estrés',
                    'type': 'Workshop',
                    'duration': '4 hours',
                    'priority': 'medium'
                }
            ],
            'engagement': [
                {
                    'name': 'Propósito y motivación profesional',
                    'type': 'Workshop',
                    'duration': '4 hours',
                    'priority': 'high'
                }
            ]
        }
        
        # Obtener habilidades y rol de la persona para personalizar
        person_skills = await self._get_person_skills(person_id)
        
        # Agregar entrenamientos relevantes basados en factores
        for factor in causal_factors:
            factor_name = factor.get('factor')
            if factor_name in training_map:
                # Filtrar entrenamientos ya realizados o redundantes
                relevant_trainings = training_map[factor_name]
                for training in relevant_trainings:
                    # Personalizar título si es posible
                    if hasattr(person, 'current_position') and person.current_position:
                        training = training.copy()
                        training['name'] = training['name'] + f" para {person.current_position}"
                    
                    training_recommendations.append(training)
        
        # Agregar un entrenamiento genérico si no hay recomendaciones específicas
        if not training_recommendations:
            training_recommendations.append({
                'name': 'Desarrollo profesional integral',
                'type': 'Course',
                'duration': '16 hours',
                'priority': 'medium'
            })
        
        # Limitar a 3 recomendaciones para no sobrecargar
        return training_recommendations[:3]
    
    async def _recommend_mentor(self, causal_factors: List[Dict], person_id: int) -> Optional[Dict]:
        """Identifica si se necesita un mentor específico basado en factores causales."""
        # Evaluar si los factores justifican un mentor
        mentor_needed = False
        mentor_focus = []
        mentor_types = []
        
        for factor in causal_factors:
            factor_name = factor.get('factor')
            risk = factor.get('risk', 0)
            
            # Factores que más se benefician de mentoría y su mapeo a tipos de mentoría
            if risk > 60:
                if factor_name == 'career_growth':
                    mentor_needed = True
                    mentor_focus.append('desarrollo de carrera')
                    mentor_types.append('CAREER')
                elif factor_name == 'performance_trend':
                    mentor_needed = True
                    mentor_focus.append('mejora de desempeño')
                    mentor_types.append('TECHNICAL')
                elif factor_name == 'engagement':
                    mentor_needed = True
                    mentor_focus.append('engagement y motivación')
                    mentor_types.extend(['WORK_LIFE', 'LEADERSHIP'])
                elif factor_name == 'leadership':
                    mentor_needed = True
                    mentor_focus.append('desarrollo de liderazgo')
                    mentor_types.append('LEADERSHIP')
                elif factor_name == 'work_life_balance':
                    mentor_needed = True
                    mentor_focus.append('equilibrio vida-trabajo')
                    mentor_types.append('WORK_LIFE')
        
        if not mentor_needed:
            return None
        
        try:
            # Primero intentar usar el MentorMatcher para una recomendación óptima
            from app.ats.talent.mentor_matcher import MentorMatcher
            mentor_matcher = MentorMatcher()
            
            mentor_match = await mentor_matcher.find_optimal_mentors(
                person_id=person_id,
                goal=mentor_focus[0] if mentor_focus else None,
                limit=1
            )
            
            if mentor_match and 'mentors' in mentor_match and mentor_match['mentors']:
                top_mentor = mentor_match['mentors'][0]
                return {
                    'recommended': True,
                    'mentor': {
                        'id': top_mentor.get('id'),
                        'name': top_mentor.get('name'),
                        'position': top_mentor.get('position'),
                        'match_score': top_mentor.get('match_score')
                    },
                    'focus_areas': mentor_focus,
                    'session_frequency': 'weekly' if any(factor.get('risk', 0) > 80 for factor in causal_factors) else 'biweekly',
                    'suggested_duration': '3 months'
                }
            
            # Si el matcher no devolvió resultados, intentar búsqueda directa en modelo
            if not mentor_match or not mentor_match.get('mentors'):
                # Convertir la operación asíncrona a síncrona ya que estamos accediendo a la DB
                @sync_to_async
                def find_mentors_by_type():
                    # Buscar mentores activos que tengan alguno de los tipos de mentoría necesarios
                    mentors = []
                    
                    # Si no hay tipos específicos, usar cualquier mentor activo
                    if not mentor_types:
                        return list(Mentor.objects.filter(is_active=True).select_related('person')[:3])
                    
                    # Buscar por tipos de mentoría específicos
                    mentor_query = Mentor.objects.filter(is_active=True)
                    
                    # Filtrar por tipos de mentoría requeridos
                    # En ArrayField podemos usar contains para encontrar elementos
                    for mentor_type in set(mentor_types):
                        mentors.extend(list(mentor_query.filter(mentoring_types__contains=[mentor_type]).select_related('person')[:2]))
                    
                    # Si no encontramos mentores específicos, devolver cualquier mentor activo
                    if not mentors:
                        mentors = list(mentor_query[:3])
                    
                    return mentors
                
                # Ejecutar la búsqueda
                db_mentors = await find_mentors_by_type()
                
                if db_mentors:
                    # Tomar el primer mentor encontrado
                    top_db_mentor = db_mentors[0]
                    
                    return {
                        'recommended': True,
                        'mentor': {
                            'id': top_db_mentor.id,
                            'name': str(top_db_mentor.person),
                            'position': getattr(top_db_mentor.person, 'position', 'Especialista'),
                            'specialty': top_db_mentor.specialty,
                            'match_score': 75  # Puntuación estándar para recomendaciones no optimizadas
                        },
                        'focus_areas': mentor_focus,
                        'session_frequency': 'weekly' if any(factor.get('risk', 0) > 80 for factor in causal_factors) else 'biweekly',
                        'suggested_duration': '3 months'
                    }
        except Exception as e:
            logger.error(f"Error al recomendar mentor: {str(e)}")
            
        # Fallback si no se puede obtener mentor específico
        return {
            'recommended': True,
            'mentor': None,  # Indicar que se necesita mentor pero no hay match específico
            'focus_areas': mentor_focus,
            'session_frequency': 'biweekly',
            'suggested_duration': '3 months',
            'note': 'Seleccionar mentor con experiencia en ' + ', '.join(mentor_focus)
        }
    
    async def _log_intervention_plan(self, person_id: int, plan: Dict):
        """Registra el plan de intervención para seguimiento futuro."""
        # En un sistema real, guardaría el plan en la base de datos
        # para futuro seguimiento y análisis de efectividad
        logger.info(f"Plan de intervención generado para persona {person_id} con nivel de riesgo {plan['risk_level']}")
        
        # Aquí se podría implementar la creación de tareas en sistema para los owners
        # y notificaciones automáticas según la programación de seguimiento
        
        # También se registraría la métrica para poder evaluar efectividad
        # de los planes de intervención en el futuro
    
    def _get_default_plan(self, person_id: int) -> Dict:
        """Retorna un plan genérico cuando no hay datos suficientes."""
        return {
            'person_id': person_id,
            'risk_level': 'medium',  # Valor predeterminado neutral
            'interventions': [
                {
                    'factor': 'general_retention',
                    'factor_label': 'Retención General',
                    'current_score': 50,
                    'target_score': 70,
                    'actions': [
                        {
                            'action': 'Realizar entrevista de satisfacción',
                            'description': 'Entrevista estructurada para identificar factores de riesgo específicos',
                            'owner': 'hr',
                            'timeline': '2 weeks',
                            'expected_impact': 'high'
                        },
                        {
                            'action': 'Establecer plan de desarrollo básico',
                            'description': 'Plan general con elementos clave para retención',
                            'owner': 'manager',
                            'timeline': '1 month',
                            'expected_impact': 'medium'
                        }
                    ]
                }
            ],
            'success_metrics': [
                'Identificación de factores de riesgo específicos',
                'Establecimiento de plan detallado basado en datos',
                'Mejora en métricas generales de satisfacción'
            ],
            'follow_up_schedule': {
                'first_check': '30 days',
                'second_check': '90 days',
                'check_format': 'Reunión de seguimiento con consultor huntRED®'
            },
            'training_recommendations': [
                {
                    'name': 'Desarrollo profesional integral',
                    'type': 'Workshop',
                    'duration': '4 hours',
                    'priority': 'medium'
                }
            ],
            'generated_at': datetime.now().isoformat(),
            'note': 'Plan genérico - Se requiere más información para personalizar'
        }