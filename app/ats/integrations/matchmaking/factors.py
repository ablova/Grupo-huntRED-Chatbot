# /home/pablo/app/ats/integrations/matchmaking/factors.py
"""
Módulo de factores de matchmaking mejorado.
Integra datos de CV, LinkedIn, assessments y análisis de comportamiento.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MatchFactorCategory(Enum):
    """Categorías principales de factores de matchmaking."""
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    CULTURAL = "cultural"
    CAREER = "career"
    PERSONAL = "personal"
    NETWORK = "network"
    INNOVATION = "innovation"
    LEADERSHIP = "leadership"
    GROUP = "group"  # Nueva categoría para relaciones grupales

@dataclass
class MatchFactor:
    """Factor individual de matchmaking."""
    category: MatchFactorCategory
    name: str
    weight: float
    source: str
    confidence: float
    value: Any
    metadata: Dict[str, Any]

class EnhancedMatchmakingFactors:
    """Sistema mejorado de factores de matchmaking."""
    
    def __init__(self):
        self.factors = {
            MatchFactorCategory.TECHNICAL: {
                'skills': {
                    'weight': 1.0,
                    'sources': ['cv', 'linkedin', 'assessments'],
                    'subcategories': [
                        'technical_skills',
                        'soft_skills',
                        'domain_knowledge',
                        'certifications',
                        'languages'
                    ]
                },
                'experience': {
                    'weight': 0.9,
                    'sources': ['cv', 'linkedin'],
                    'subcategories': [
                        'years_experience',
                        'industry_experience',
                        'role_experience',
                        'project_experience',
                        'team_size'
                    ]
                },
                'education': {
                    'weight': 0.8,
                    'sources': ['cv', 'linkedin'],
                    'subcategories': [
                        'academic_level',
                        'field_of_study',
                        'institution_ranking',
                        'relevant_courses',
                        'academic_achievements'
                    ]
                }
            },
            MatchFactorCategory.BEHAVIORAL: {
                'personality': {
                    'weight': 0.9,
                    'sources': ['assessments', 'linkedin_activity'],
                    'subcategories': [
                        'big_five_traits',
                        'work_style',
                        'communication_style',
                        'stress_management',
                        'decision_making'
                    ]
                },
                'derailers': {
                    'weight': 0.8,
                    'sources': ['assessments'],
                    'subcategories': [
                        'risk_factors',
                        'mitigation_strategies',
                        'self_awareness',
                        'adaptability'
                    ]
                },
                'values': {
                    'weight': 0.9,
                    'sources': ['assessments', 'linkedin_content'],
                    'subcategories': [
                        'personal_values',
                        'work_values',
                        'ethical_standards',
                        'cultural_values'
                    ]
                }
            },
            MatchFactorCategory.CULTURAL: {
                'organizational_fit': {
                    'weight': 0.95,
                    'sources': ['assessments', 'linkedin_network'],
                    'subcategories': [
                        'company_values',
                        'team_dynamics',
                        'work_environment',
                        'communication_style'
                    ]
                },
                'diversity': {
                    'weight': 0.85,
                    'sources': ['cv', 'linkedin', 'assessments'],
                    'subcategories': [
                        'cultural_background',
                        'international_experience',
                        'inclusive_practices',
                        'diversity_awareness'
                    ]
                }
            },
            MatchFactorCategory.CAREER: {
                'trajectory': {
                    'weight': 0.9,
                    'sources': ['cv', 'linkedin'],
                    'subcategories': [
                        'career_progression',
                        'role_changes',
                        'industry_changes',
                        'geographic_mobility'
                    ]
                },
                'goals': {
                    'weight': 0.85,
                    'sources': ['assessments', 'linkedin_content'],
                    'subcategories': [
                        'career_aspirations',
                        'growth_potential',
                        'learning_goals',
                        'leadership_goals'
                    ]
                }
            },
            MatchFactorCategory.PERSONAL: {
                'work_life': {
                    'weight': 0.8,
                    'sources': ['assessments', 'linkedin_activity'],
                    'subcategories': [
                        'work_preferences',
                        'location_preferences',
                        'schedule_preferences',
                        'remote_work'
                    ]
                },
                'wellbeing': {
                    'weight': 0.75,
                    'sources': ['assessments'],
                    'subcategories': [
                        'stress_management',
                        'work_life_balance',
                        'health_considerations',
                        'personal_development'
                    ]
                }
            },
            MatchFactorCategory.NETWORK: {
                'professional_network': {
                    'weight': 0.85,
                    'sources': ['linkedin'],
                    'subcategories': [
                        'network_size',
                        'network_quality',
                        'industry_connections',
                        'influence_level'
                    ]
                },
                'community': {
                    'weight': 0.8,
                    'sources': ['linkedin', 'cv'],
                    'subcategories': [
                        'community_participation',
                        'professional_groups',
                        'industry_events',
                        'thought_leadership'
                    ]
                }
            },
            MatchFactorCategory.INNOVATION: {
                'creativity': {
                    'weight': 0.85,
                    'sources': ['assessments', 'linkedin_content'],
                    'subcategories': [
                        'problem_solving',
                        'innovation_approach',
                        'change_management',
                        'digital_transformation'
                    ]
                },
                'adaptability': {
                    'weight': 0.9,
                    'sources': ['assessments', 'cv'],
                    'subcategories': [
                        'change_adaptation',
                        'learning_agility',
                        'technology_adoption',
                        'market_awareness'
                    ]
                }
            },
            MatchFactorCategory.LEADERSHIP: {
                'leadership_style': {
                    'weight': 0.9,
                    'sources': ['assessments', 'linkedin_content'],
                    'subcategories': [
                        'leadership_approach',
                        'team_management',
                        'decision_making',
                        'influence_style'
                    ]
                },
                'executive_presence': {
                    'weight': 0.85,
                    'sources': ['assessments', 'linkedin'],
                    'subcategories': [
                        'communication_impact',
                        'strategic_thinking',
                        'stakeholder_management',
                        'business_acumen'
                    ]
                }
            },
            MatchFactorCategory.GROUP: {
                'family_network': {
                    'weight': 0.95,  # Alto peso para relaciones familiares
                    'sources': ['cv', 'linkedin', 'interviews'],
                    'subcategories': [
                        'family_members_in_company',
                        'family_work_history',
                        'family_recommendations',
                        'family_success_stories'
                    ]
                },
                'group_dynamics': {
                    'weight': 0.9,
                    'sources': ['interviews', 'assessments'],
                    'subcategories': [
                        'group_travel_history',
                        'group_work_experience',
                        'group_success_rate',
                        'group_stability'
                    ]
                },
                'social_capital': {
                    'weight': 0.85,
                    'sources': ['linkedin', 'interviews'],
                    'subcategories': [
                        'community_integration',
                        'social_support_network',
                        'cultural_adaptation',
                        'language_community'
                    ]
                }
            }
        }
        
        # Ajustes específicos por unidad de negocio
        self.business_unit_adjustments = {
            'Amigro': {
                MatchFactorCategory.GROUP: 0.25,  # 25% de peso para factores grupales
                MatchFactorCategory.CULTURAL: 0.20,  # 20% para factores culturales
                MatchFactorCategory.PERSONAL: 0.15,  # 15% para factores personales
                MatchFactorCategory.TECHNICAL: 0.20,  # 20% para factores técnicos
                MatchFactorCategory.BEHAVIORAL: 0.10,  # 10% para factores conductuales
                MatchFactorCategory.NETWORK: 0.05,  # 5% para factores de red general
                MatchFactorCategory.INNOVATION: 0.03,  # 3% para factores de innovación
                MatchFactorCategory.LEADERSHIP: 0.02   # 2% para factores de liderazgo
            }
        }
        
    def get_factors_for_business_unit(self, business_unit: str) -> Dict[MatchFactorCategory, Dict[str, Any]]:
        """
        Obtiene los factores ajustados para una unidad de negocio específica.
        
        Args:
            business_unit: Nombre de la unidad de negocio
            
        Returns:
            Dict con factores ajustados
        """
        if business_unit not in self.business_unit_adjustments:
            return self.factors
            
        adjustments = self.business_unit_adjustments[business_unit]
        adjusted_factors = self.factors.copy()
        
        # Ajustar pesos según la unidad de negocio
        for category, weight in adjustments.items():
            if category in adjusted_factors:
                for factor in adjusted_factors[category].values():
                    factor['weight'] *= weight
                    
        return adjusted_factors
        
    def calculate_match_score(self, candidate_data: Dict, job_data: Dict) -> float:
        """
        Calcula el score de match entre candidato y vacante.
        
        Args:
            candidate_data: Datos del candidato
            job_data: Datos de la vacante
            
        Returns:
            float: Score de match (0-1)
        """
        total_score = 0
        total_weight = 0
        
        for category, factors in self.factors.items():
            category_score = self._calculate_category_score(
                category,
                factors,
                candidate_data,
                job_data
            )
            total_score += category_score
            total_weight += 1
            
        return total_score / total_weight if total_weight > 0 else 0
        
    def _calculate_category_score(
        self,
        category: MatchFactorCategory,
        factors: Dict,
        candidate_data: Dict,
        job_data: Dict
    ) -> float:
        """Calcula el score para una categoría específica."""
        category_score = 0
        category_weight = 0
        
        for factor_name, factor_data in factors.items():
            factor_score = self._calculate_factor_score(
                factor_name,
                factor_data,
                candidate_data,
                job_data
            )
            category_score += factor_score * factor_data['weight']
            category_weight += factor_data['weight']
            
        return category_score / category_weight if category_weight > 0 else 0
        
    def _calculate_factor_score(
        self,
        factor_name: str,
        factor_data: Dict,
        candidate_data: Dict,
        job_data: Dict
    ) -> float:
        """Calcula el score para un factor específico."""
        # Implementar lógica específica para cada factor
        return 0.0  # Placeholder 