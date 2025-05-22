# /home/pablo/app/ml/analyzers/intervention_analyzer.py
"""
Intervention Analyzer module for Grupo huntRED® assessment system.

This module provides analysis and recommendations for personalized
interventions to improve retention of valuable talent based on risk factors.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import random
import json

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.cache import cache

from app.models import BusinessUnit
from app.ml.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class InterventionAnalyzerImpl(BaseAnalyzer):
    """
    Analyzer for generating personalized intervention plans.
    
    Evaluates retention risk factors and provides tailored intervention
    strategies to improve employee engagement and retention.
    """
    
    # Intervention categories and their primary impact areas
    INTERVENTION_CATEGORIES = {
        'career_development': {
            'primary_impact': ['career_stagnation', 'skill_underutilization', 'growth_opportunities'],
            'effectiveness': 0.85
        },
        'compensation_benefits': {
            'primary_impact': ['compensation_dissatisfaction', 'benefits_gap', 'market_competitiveness'],
            'effectiveness': 0.70
        },
        'work_environment': {
            'primary_impact': ['work_life_balance', 'cultural_misfit', 'workplace_flexibility'],
            'effectiveness': 0.75
        },
        'management_leadership': {
            'primary_impact': ['management_relationship', 'leadership_issues', 'recognition_feedback'],
            'effectiveness': 0.80
        },
        'engagement_motivation': {
            'primary_impact': ['low_engagement', 'purpose_alignment', 'job_satisfaction'],
            'effectiveness': 0.78
        }
    }
    
    # Specific intervention actions by category
    INTERVENTION_ACTIONS = {
        'career_development': [
            {
                'action': 'Crear plan de desarrollo personalizado',
                'description': 'Elaborar un plan de carrera con objetivos a corto y largo plazo',
                'owner': 'manager_hr',
                'timeline': '2 weeks',
                'expected_impact': 'high'
            },
            {
                'action': 'Asignar a proyecto de alta visibilidad',
                'description': 'Incorporar a un proyecto estratégico que ofrezca exposición y aprendizaje',
                'owner': 'manager',
                'timeline': '1 month',
                'expected_impact': 'high'
            },
            {
                'action': 'Implementar rotación de roles',
                'description': 'Programa de rotación para ampliar experiencia en diferentes áreas',
                'owner': 'hr',
                'timeline': '3 months',
                'expected_impact': 'medium'
            }
        ],
        'compensation_benefits': [
            {
                'action': 'Revisión de compensación',
                'description': 'Análisis competitivo del paquete salarial y ajuste si es necesario',
                'owner': 'hr_finance',
                'timeline': '1 month',
                'expected_impact': 'high'
            },
            {
                'action': 'Implementar beneficios personalizados',
                'description': 'Ofrecer beneficios flexibles según necesidades individuales',
                'owner': 'hr',
                'timeline': '1 month',
                'expected_impact': 'medium'
            },
            {
                'action': 'Programa de reconocimiento especial',
                'description': 'Establecer bonos o incentivos por objetivos específicos',
                'owner': 'manager_hr',
                'timeline': '2 weeks',
                'expected_impact': 'medium'
            }
        ],
        'work_environment': [
            {
                'action': 'Implementar horario flexible',
                'description': 'Establecer opciones de flexibilidad horaria o trabajo remoto',
                'owner': 'hr_manager',
                'timeline': '2 weeks',
                'expected_impact': 'high'
            },
            {
                'action': 'Ajustar carga de trabajo',
                'description': 'Revisión y redistribución de responsabilidades para equilibrio',
                'owner': 'manager',
                'timeline': '1 week',
                'expected_impact': 'high'
            },
            {
                'action': 'Programa de bienestar',
                'description': 'Implementar iniciativas de bienestar físico y mental',
                'owner': 'hr',
                'timeline': '1 month',
                'expected_impact': 'medium'
            }
        ],
        'management_leadership': [
            {
                'action': 'Coaching para el manager',
                'description': 'Programa de coaching para mejorar estilo de liderazgo',
                'owner': 'hr',
                'timeline': '1 month',
                'expected_impact': 'high'
            },
            {
                'action': 'Sesiones 1:1 estructuradas',
                'description': 'Implementar reuniones periódicas con agenda enfocada en desarrollo',
                'owner': 'manager',
                'timeline': '1 week',
                'expected_impact': 'medium'
            },
            {
                'action': 'Sistema de feedback 360',
                'description': 'Implementar evaluación integral con feedback de múltiples fuentes',
                'owner': 'hr',
                'timeline': '1 month',
                'expected_impact': 'medium'
            }
        ],
        'engagement_motivation': [
            {
                'action': 'Alineación con propósito organizacional',
                'description': 'Sesiones para conectar trabajo individual con misión de la empresa',
                'owner': 'hr_manager',
                'timeline': '2 weeks',
                'expected_impact': 'high'
            },
            {
                'action': 'Rediseño de rol',
                'description': 'Ajustar responsabilidades para mejor alineación con fortalezas',
                'owner': 'manager',
                'timeline': '1 month',
                'expected_impact': 'high'
            },
            {
                'action': 'Programa de reconocimiento',
                'description': 'Implementar sistema formal de reconocimiento de logros',
                'owner': 'hr',
                'timeline': '2 weeks',
                'expected_impact': 'medium'
            }
        ]
    }
    
    # Training recommendations by risk factor
    TRAINING_RECOMMENDATIONS = {
        'career_stagnation': [
            {
                'name': 'Planificación de Carrera Estratégica',
                'type': 'Workshop',
                'duration': '8 hours',
                'priority': 'high'
            },
            {
                'name': 'Autogestión del Desarrollo Profesional',
                'type': 'Online Course',
                'duration': '10 hours',
                'priority': 'medium'
            }
        ],
        'skill_underutilization': [
            {
                'name': 'Desarrollo de Habilidades de Liderazgo',
                'type': 'Program',
                'duration': '3 months',
                'priority': 'high'
            },
            {
                'name': 'Certificación Técnica Avanzada',
                'type': 'Certification',
                'duration': '6 weeks',
                'priority': 'medium'
            }
        ],
        'management_relationship': [
            {
                'name': 'Comunicación Efectiva en Entornos Laborales',
                'type': 'Workshop',
                'duration': '6 hours',
                'priority': 'high'
            },
            {
                'name': 'Gestión de Conflictos',
                'type': 'Course',
                'duration': '8 hours',
                'priority': 'medium'
            }
        ],
        'work_life_balance': [
            {
                'name': 'Gestión del Tiempo y Productividad',
                'type': 'Workshop',
                'duration': '4 hours',
                'priority': 'high'
            },
            {
                'name': 'Bienestar y Manejo del Estrés',
                'type': 'Program',
                'duration': '6 weeks',
                'priority': 'medium'
            }
        ],
        'purpose_alignment': [
            {
                'name': 'Descubrimiento de Propósito Profesional',
                'type': 'Workshop',
                'duration': '8 hours',
                'priority': 'high'
            },
            {
                'name': 'Alineación de Valores Personales y Organizacionales',
                'type': 'Course',
                'duration': '6 hours',
                'priority': 'medium'
            }
        ]
    }
    
    # Mentor focus areas by risk factor
    MENTOR_FOCUS_AREAS = {
        'career_stagnation': ['career_strategy', 'advancement_opportunities'],
        'skill_underutilization': ['skill_development', 'project_opportunities'],
        'management_relationship': ['workplace_politics', 'communication_strategies'],
        'work_life_balance': ['boundary_setting', 'productivity_techniques'],
        'purpose_alignment': ['career_purpose', 'organizational_alignment'],
        'recognition_feedback': ['visibility_strategies', 'self_advocacy'],
        'growth_opportunities': ['professional_growth', 'networking'],
        'leadership_issues': ['leadership_development', 'influence_strategies'],
        'job_satisfaction': ['job_crafting', 'motivation_techniques']
    }
    
    def __init__(self):
        """Initialize the intervention analyzer."""
        super().__init__()
        # Cache timeout in seconds (12 hours)
        self.cache_timeout = 43200
        
    def get_required_fields(self) -> List[str]:
        """Get required fields for intervention analysis."""
        return ['person_id', 'risk_factors']
        
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Generate a personalized intervention plan based on risk factors.
        
        Args:
            data: Dictionary containing person_id and risk_factors
            business_unit: Business unit context for analysis
            
        Returns:
            Dict with personalized intervention plan
        """
        try:
            # Extract required data
            person_id = data.get('person_id')
            risk_factors = data.get('risk_factors', [])
            
            # Validate input
            if not person_id or not isinstance(person_id, (int, str)):
                return self.get_default_result("Missing or invalid person_id")
                
            if not risk_factors or not isinstance(risk_factors, list):
                return self.get_default_result(f"Missing or invalid risk factors for person {person_id}")
                
            # Check cache first
            cache_key = f"intervention_plan_{person_id}_{hash(json.dumps(risk_factors))}"
            cached_result = self.get_cached_result(data, cache_key)
            if cached_result:
                return cached_result
                
            # Get business unit context
            bu_name = self.get_business_unit_name(business_unit)
                
            # Determine risk level based on factors
            risk_level = self._determine_risk_level(risk_factors)
            
            # Generate interventions for each factor
            interventions = self._generate_factor_interventions(risk_factors, person_id)
            
            # Determine success metrics based on the factors
            success_metrics = self._determine_success_metrics(risk_factors)
            
            # Create follow-up schedule based on risk level
            follow_up_schedule = self._create_follow_up_schedule(risk_level)
            
            # Generate training recommendations
            training_recommendations = self._recommend_training(risk_factors)
            
            # Identify need for specific mentor
            mentor_recommendation = self._recommend_mentor(risk_factors)
            
            # Create final plan
            intervention_plan = {
                'person_id': person_id,
                'risk_level': risk_level,
                'interventions': interventions,
                'success_metrics': success_metrics,
                'follow_up_schedule': follow_up_schedule,
                'training_recommendations': training_recommendations,
                'mentor_recommendation': mentor_recommendation,
                'business_unit': bu_name,
                'generated_at': datetime.now().isoformat()
            }
            
            # Cache the result
            self.set_cached_result(data, intervention_plan, cache_key)
            
            return intervention_plan
            
        except Exception as e:
            logger.error(f"Error generating intervention plan: {str(e)}")
            return self.get_default_result(f"Analysis error: {str(e)}")
            
    def _determine_risk_level(self, risk_factors: List[Dict]) -> str:
        """
        Determine overall risk level based on factors.
        
        Args:
            risk_factors: List of risk factors with scores
            
        Returns:
            Risk level (low, medium, high)
        """
        if not risk_factors:
            return 'low'
            
        # Calculate average risk score
        avg_risk = sum([factor.get('risk', 50) for factor in risk_factors]) / len(risk_factors)
        
        if avg_risk >= 75:
            return 'high'
        elif avg_risk >= 50:
            return 'medium'
        else:
            return 'low'
            
    def _generate_factor_interventions(self, risk_factors: List[Dict], person_id: int) -> List[Dict]:
        """
        Generate interventions for each risk factor.
        
        Args:
            risk_factors: List of risk factors
            person_id: Person ID
            
        Returns:
            List of interventions by factor
        """
        interventions = []
        
        for factor in risk_factors:
            factor_name = factor.get('factor')
            if not factor_name or factor_name == 'insufficient_data':
                continue
                
            # Determine best intervention category for this factor
            category = self._determine_intervention_category(factor_name)
            risk_score = factor.get('risk', 50)
            
            # Get actions for this category
            actions = self._get_intervention_actions(category, risk_score)
            
            # Calculate improvement target
            current_score = 100 - risk_score  # Invert risk score to get positive metric
            target_improvement = min(30, (100 - current_score) * 0.6)  # Aim for 60% improvement toward perfect score
            target_score = current_score + target_improvement
            
            interventions.append({
                'factor': factor_name,
                'factor_label': factor.get('label', factor_name.replace('_', ' ').title()),
                'current_score': current_score,
                'target_score': target_score,
                'category': category,
                'actions': actions
            })
            
        return interventions
        
    def _determine_intervention_category(self, factor_name: str) -> str:
        """
        Determine best intervention category for a factor.
        
        Args:
            factor_name: Name of the risk factor
            
        Returns:
            Best matching intervention category
        """
        for category, info in self.INTERVENTION_CATEGORIES.items():
            if factor_name in info['primary_impact']:
                return category
                
        # Default mappings for common factors
        factor_to_category = {
            'career_stagnation': 'career_development',
            'skill_underutilization': 'career_development',
            'growth_opportunities': 'career_development',
            'compensation_dissatisfaction': 'compensation_benefits',
            'benefits_gap': 'compensation_benefits',
            'market_competitiveness': 'compensation_benefits',
            'work_life_balance': 'work_environment',
            'cultural_misfit': 'work_environment',
            'workplace_flexibility': 'work_environment',
            'management_relationship': 'management_leadership',
            'leadership_issues': 'management_leadership',
            'recognition_feedback': 'management_leadership',
            'low_engagement': 'engagement_motivation',
            'purpose_alignment': 'engagement_motivation',
            'job_satisfaction': 'engagement_motivation'
        }
        
        return factor_to_category.get(factor_name, 'engagement_motivation')
        
    def _get_intervention_actions(self, category: str, risk_score: float) -> List[Dict]:
        """
        Get intervention actions for a category.
        
        Args:
            category: Intervention category
            risk_score: Risk score (0-100)
            
        Returns:
            List of intervention actions
        """
        # Get all actions for the category
        all_actions = self.INTERVENTION_ACTIONS.get(category, [])
        
        # Number of actions depends on risk level
        num_actions = 3 if risk_score >= 75 else (2 if risk_score >= 50 else 1)
        
        # Select most relevant actions
        selected_actions = all_actions[:num_actions]
        
        # For high risk, adjust timelines to be more urgent
        if risk_score >= 75:
            for action in selected_actions:
                if '1 month' in action['timeline']:
                    action['timeline'] = '2 weeks'
                elif '2 weeks' in action['timeline']:
                    action['timeline'] = '1 week'
                    
        return selected_actions
        
    def _determine_success_metrics(self, risk_factors: List[Dict]) -> List[str]:
        """
        Determine success metrics for intervention plan.
        
        Args:
            risk_factors: List of risk factors
            
        Returns:
            List of success metrics
        """
        # Standard metrics by category
        category_metrics = {
            'career_development': [
                'Mejora en puntuación de desarrollo profesional',
                'Claridad en ruta de carrera',
                'Aumento en utilización de habilidades'
            ],
            'compensation_benefits': [
                'Mejora en satisfacción con compensación',
                'Percepción positiva del paquete de beneficios',
                'Competitividad salarial vs mercado'
            ],
            'work_environment': [
                'Mejora en balance vida-trabajo',
                'Satisfacción con ambiente laboral',
                'Reducción en niveles de estrés'
            ],
            'management_leadership': [
                'Mejora en relación con management',
                'Satisfacción con liderazgo',
                'Calidad y frecuencia del feedback'
            ],
            'engagement_motivation': [
                'Aumento en nivel de engagement',
                'Alineación con propósito organizacional',
                'Satisfacción laboral general'
            ]
        }
        
        # Determine categories based on risk factors
        categories = set()
        for factor in risk_factors:
            factor_name = factor.get('factor')
            if factor_name and factor_name != 'insufficient_data':
                category = self._determine_intervention_category(factor_name)
                categories.add(category)
                
        # Collect metrics for all relevant categories
        metrics = []
        for category in categories:
            metrics.extend(category_metrics.get(category, [])[:2])  # Take top 2 from each category
            
        # Add general metrics
        general_metrics = [
            'Reducción en probabilidad de salida',
            'Mejora en índice de satisfacción general'
        ]
        
        metrics.extend(general_metrics)
        
        # Limit to 5-7 metrics
        return metrics[:7]
        
    def _create_follow_up_schedule(self, risk_level: str) -> Dict:
        """
        Create follow-up schedule based on risk level.
        
        Args:
            risk_level: Risk level (low, medium, high)
            
        Returns:
            Follow-up schedule
        """
        if risk_level == 'high':
            return {
                'first_check': '7 days',
                'second_check': '30 days',
                'third_check': '60 days',
                'final_assessment': '90 days',
                'check_format': 'Reunión semanal de seguimiento con consultor huntRED®'
            }
        elif risk_level == 'medium':
            return {
                'first_check': '14 days',
                'second_check': '45 days',
                'third_check': '90 days',
                'check_format': 'Reunión quincenal de seguimiento con consultor huntRED®'
            }
        else:  # low
            return {
                'first_check': '30 days',
                'second_check': '90 days',
                'check_format': 'Reunión mensual de seguimiento con consultor huntRED®'
            }
            
    def _recommend_training(self, risk_factors: List[Dict]) -> List[Dict]:
        """
        Generate training recommendations based on risk factors.
        
        Args:
            risk_factors: List of risk factors
            
        Returns:
            List of recommended trainings
        """
        if not risk_factors:
            return []
            
        # Identify relevant factors for training
        training_recs = []
        high_priority_count = 0
        
        for factor in risk_factors:
            factor_name = factor.get('factor')
            risk = factor.get('risk', 0)
            
            if factor_name in self.TRAINING_RECOMMENDATIONS:
                factor_trainings = self.TRAINING_RECOMMENDATIONS[factor_name]
                
                # Select training based on risk level
                if risk >= 75 and high_priority_count < 2:
                    # For high risk, select high priority training
                    for training in factor_trainings:
                        if training['priority'] == 'high':
                            training_recs.append(training)
                            high_priority_count += 1
                            break
                elif risk >= 50:
                    # For medium risk, select medium priority training if available
                    for training in factor_trainings:
                        if training['priority'] == 'medium':
                            training_recs.append(training)
                            break
                    
        # If no specific trainings found, add general recommendation
        if not training_recs:
            training_recs.append({
                'name': 'Desarrollo Profesional Integral',
                'type': 'Program',
                'duration': '6 weeks',
                'priority': 'medium'
            })
            
        # Limit to 3 recommendations
        return training_recs[:3]
        
    def _recommend_mentor(self, risk_factors: List[Dict]) -> Dict:
        """
        Identify if specific mentor is needed based on risk factors.
        
        Args:
            risk_factors: List of risk factors
            
        Returns:
            Mentor recommendation
        """
        if not risk_factors:
            return {'recommended': False}
            
        # Determine if mentor is needed based on factors
        mentor_threshold = 70  # Risk threshold for recommending mentor
        high_risk_factors = [f for f in risk_factors if f.get('risk', 0) >= mentor_threshold]
        
        if not high_risk_factors:
            return {'recommended': False}
            
        # Identify focus areas for mentoring
        mentor_focus = []
        for factor in high_risk_factors:
            factor_name = factor.get('factor')
            if factor_name in self.MENTOR_FOCUS_AREAS:
                mentor_focus.extend(self.MENTOR_FOCUS_AREAS[factor_name])
                
        # Ensure unique focus areas
        mentor_focus = list(set(mentor_focus))
        
        # Determine session frequency based on risk level
        avg_risk = sum([factor.get('risk', 0) for factor in high_risk_factors]) / len(high_risk_factors)
        session_frequency = 'weekly' if avg_risk >= 85 else 'biweekly'
        
        # In actual implementation, mentor selection would be done here
        # For now, we'll return the recommendation without a specific mentor
        return {
            'recommended': True,
            'focus_areas': mentor_focus[:3],  # Limit to top 3 focus areas
            'session_frequency': session_frequency,
            'suggested_duration': '3 months',
            'note': 'Seleccionar mentor con experiencia en ' + ', '.join(mentor_focus[:3])
        }
        
    def get_default_result(self, error_message: str = None) -> Dict:
        """
        Get default intervention result.
        
        Args:
            error_message: Optional error message
            
        Returns:
            Default intervention plan
        """
        return {
            'person_id': None,
            'risk_level': 'medium',  # Default neutral value
            'interventions': [
                {
                    'factor': 'general_retention',
                    'factor_label': 'Retención General',
                    'current_score': 50,
                    'target_score': 70,
                    'category': 'engagement_motivation',
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
            'mentor_recommendation': {
                'recommended': False
            },
            'generated_at': datetime.now().isoformat(),
            'error': error_message,
            'note': 'Plan genérico - Se requiere más información para personalizar'
        }
