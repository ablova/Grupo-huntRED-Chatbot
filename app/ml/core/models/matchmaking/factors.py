# /home/pablo/app/ml/core/models/matchmaking/factors.py
"""
Factores ponderados para el sistema de matchmaking.

Este módulo define los factores y sus pesos para el sistema de matchmaking,
integrando todas las dimensiones de análisis disponibles.
"""
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class FactorCategory(Enum):
    """Categorías principales de factores."""
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
class Factor:
    """Estructura para definir un factor."""
    name: str
    weight: float
    description: str
    sources: List[str]
    min_score: float = 0.0
    max_score: float = 1.0

class MatchmakingFactors:
    """Factores ponderados para matchmaking."""
    
    # Pesos por categoría principal (default para todas las BUs excepto Amigro)
    DEFAULT_CATEGORY_WEIGHTS = {
        FactorCategory.TECHNICAL: 0.25,    # 25%
        FactorCategory.BEHAVIORAL: 0.20,   # 20%
        FactorCategory.CULTURAL: 0.15,     # 15%
        FactorCategory.CAREER: 0.15,       # 15%
        FactorCategory.PERSONAL: 0.10,     # 10%
        FactorCategory.NETWORK: 0.05,      # 5%
        FactorCategory.INNOVATION: 0.05,   # 5%
        FactorCategory.LEADERSHIP: 0.05    # 5%
    }
    
    # Pesos específicos para Amigro
    AMIGRO_CATEGORY_WEIGHTS = {
        FactorCategory.TECHNICAL: 0.20,    # 20%
        FactorCategory.BEHAVIORAL: 0.15,   # 15%
        FactorCategory.CULTURAL: 0.10,     # 10%
        FactorCategory.CAREER: 0.15,       # 15%
        FactorCategory.PERSONAL: 0.10,     # 10%
        FactorCategory.NETWORK: 0.05,      # 5%
        FactorCategory.INNOVATION: 0.05,   # 5%
        FactorCategory.LEADERSHIP: 0.05,   # 5%
        FactorCategory.GROUP: 0.15         # 15%
    }
    
    @classmethod
    def get_category_weights(cls, business_unit: str) -> Dict[FactorCategory, float]:
        """Obtiene los pesos de categoría según la business unit."""
        if business_unit == 'amigro':
            return cls.AMIGRO_CATEGORY_WEIGHTS
        return cls.DEFAULT_CATEGORY_WEIGHTS
    
    # Factores técnicos
    TECHNICAL_FACTORS = {
        'hard_skills': Factor(
            name="Habilidades Técnicas",
            weight=0.40,
            description="Dominio de habilidades técnicas específicas",
            sources=['cv', 'linkedin', 'talent']
        ),
        'experience': Factor(
            name="Experiencia",
            weight=0.30,
            description="Años y relevancia de la experiencia",
            sources=['cv', 'linkedin', 'professional']
        ),
        'education': Factor(
            name="Educación",
            weight=0.15,
            description="Nivel y relevancia de la educación",
            sources=['cv', 'linkedin']
        ),
        'certifications': Factor(
            name="Certificaciones",
            weight=0.15,
            description="Certificaciones relevantes",
            sources=['cv', 'linkedin']
        )
    }
    
    # Factores conductuales
    BEHAVIORAL_FACTORS = {
        'personality_traits': Factor(
            name="Rasgos de Personalidad",
            weight=0.35,
            description="Rasgos de personalidad y estilo de trabajo",
            sources=['personality', 'assessments']
        ),
        'work_style': Factor(
            name="Estilo de Trabajo",
            weight=0.25,
            description="Preferencias y patrones de trabajo",
            sources=['personality', 'assessments']
        ),
        'communication': Factor(
            name="Comunicación",
            weight=0.20,
            description="Habilidades de comunicación",
            sources=['linkedin', 'assessments']
        ),
        'adaptability': Factor(
            name="Adaptabilidad",
            weight=0.20,
            description="Capacidad de adaptación al cambio",
            sources=['personality', 'assessments']
        )
    }
    
    # Factores culturales
    CULTURAL_FACTORS = {
        'values_alignment': Factor(
            name="Alineación de Valores",
            weight=0.40,
            description="Alineación con valores organizacionales",
            sources=['cultural', 'assessments']
        ),
        'work_environment': Factor(
            name="Ambiente Laboral",
            weight=0.30,
            description="Preferencias de ambiente laboral",
            sources=['cultural', 'personality']
        ),
        'team_culture': Factor(
            name="Cultura de Equipo",
            weight=0.30,
            description="Compatibilidad con cultura de equipo",
            sources=['team', 'cultural']
        )
    }
    
    # Factores de carrera
    CAREER_FACTORS = {
        'career_goals': Factor(
            name="Objetivos de Carrera",
            weight=0.35,
            description="Alineación con objetivos de carrera",
            sources=['professional', 'linkedin']
        ),
        'growth_potential': Factor(
            name="Potencial de Crecimiento",
            weight=0.30,
            description="Potencial de desarrollo profesional",
            sources=['professional', 'talent']
        ),
        'stability': Factor(
            name="Estabilidad",
            weight=0.20,
            description="Preferencia por estabilidad",
            sources=['professional', 'personality']
        ),
        'compensation': Factor(
            name="Compensación",
            weight=0.15,
            description="Expectativas de compensación",
            sources=['professional', 'motivational']
        )
    }
    
    # Factores personales
    PERSONAL_FACTORS = {
        'work_life_balance': Factor(
            name="Equilibrio Vida-Trabajo",
            weight=0.30,
            description="Preferencias de equilibrio",
            sources=['personality', 'motivational']
        ),
        'location_preference': Factor(
            name="Preferencia de Ubicación",
            weight=0.25,
            description="Preferencias de ubicación",
            sources=['location']
        ),
        'schedule_flexibility': Factor(
            name="Flexibilidad Horaria",
            weight=0.25,
            description="Preferencias de horario",
            sources=['personality', 'motivational']
        ),
        'remote_work': Factor(
            name="Trabajo Remoto",
            weight=0.20,
            description="Preferencias de trabajo remoto",
            sources=['location', 'personality']
        )
    }
    
    # Factores de red
    NETWORK_FACTORS = {
        'professional_network': Factor(
            name="Red Profesional",
            weight=0.40,
            description="Tamaño y calidad de la red profesional",
            sources=['linkedin', 'team']
        ),
        'industry_connections': Factor(
            name="Conexiones en la Industria",
            weight=0.30,
            description="Conexiones relevantes en la industria",
            sources=['linkedin']
        ),
        'referral_quality': Factor(
            name="Calidad de Referencias",
            weight=0.30,
            description="Calidad de las referencias",
            sources=['references']
        )
    }
    
    # Factores de innovación
    INNOVATION_FACTORS = {
        'creativity': Factor(
            name="Creatividad",
            weight=0.35,
            description="Capacidad creativa e innovadora",
            sources=['talent', 'personality']
        ),
        'problem_solving': Factor(
            name="Resolución de Problemas",
            weight=0.35,
            description="Habilidades de resolución de problemas",
            sources=['talent', 'professional']
        ),
        'learning_agility': Factor(
            name="Agilidad de Aprendizaje",
            weight=0.30,
            description="Capacidad de aprendizaje rápido",
            sources=['talent', 'professional']
        )
    }
    
    # Factores de liderazgo
    LEADERSHIP_FACTORS = {
        'leadership_style': Factor(
            name="Estilo de Liderazgo",
            weight=0.35,
            description="Estilo y enfoque de liderazgo",
            sources=['professional', 'personality']
        ),
        'team_management': Factor(
            name="Gestión de Equipos",
            weight=0.30,
            description="Habilidades de gestión de equipos",
            sources=['team', 'professional']
        ),
        'strategic_thinking': Factor(
            name="Pensamiento Estratégico",
            weight=0.35,
            description="Capacidad de pensamiento estratégico",
            sources=['professional', 'talent']
        )
    }
    
    # Factores grupales (solo aplican a Amigro)
    GROUP_FACTORS = {
        'family_network': Factor(
            name="Red Familiar",
            weight=0.40,
            description="Red de familiares en la empresa",
            sources=['family_relationships', 'social_connections']
        ),
        'group_dynamics': Factor(
            name="Dinámica Grupal",
            weight=0.30,
            description="Historial y éxito en trabajo grupal",
            sources=['group_work_history', 'performance']
        ),
        'social_capital': Factor(
            name="Capital Social",
            weight=0.30,
            description="Integración y estabilidad en grupos",
            sources=['community_integration', 'group_stability']
        )
    }
    
    @classmethod
    def get_factors_for_business_unit(cls, business_unit: str) -> Dict[str, Dict[str, Factor]]:
        """Obtiene los factores relevantes según la business unit."""
        factors = {
            FactorCategory.TECHNICAL.value: cls.TECHNICAL_FACTORS,
            FactorCategory.BEHAVIORAL.value: cls.BEHAVIORAL_FACTORS,
            FactorCategory.CULTURAL.value: cls.CULTURAL_FACTORS,
            FactorCategory.CAREER.value: cls.CAREER_FACTORS,
            FactorCategory.PERSONAL.value: cls.PERSONAL_FACTORS,
            FactorCategory.NETWORK.value: cls.NETWORK_FACTORS,
            FactorCategory.INNOVATION.value: cls.INNOVATION_FACTORS,
            FactorCategory.LEADERSHIP.value: cls.LEADERSHIP_FACTORS
        }
        
        # Solo agregar factores grupales para Amigro
        if business_unit == 'amigro':
            factors[FactorCategory.GROUP.value] = cls.GROUP_FACTORS
            
        return factors
    
    @classmethod
    def get_factor_weight(cls, category: str, factor: str) -> float:
        """Obtiene el peso de un factor específico."""
        factors = getattr(cls, f"{category.upper()}_FACTORS", {})
        factor_obj = factors.get(factor)
        return factor_obj.weight if factor_obj else 0.0
    
    @classmethod
    def calculate_weighted_score(
        cls,
        category: str,
        factor_scores: Dict[str, float]
    ) -> float:
        """
        Calcula el score ponderado para una categoría.
        
        Args:
            category: Categoría a evaluar
            factor_scores: Scores de los factores
            
        Returns:
            Score ponderado
        """
        factors = getattr(cls, f"{category.upper()}_FACTORS", {})
        total_weight = sum(factor.weight for factor in factors.values())
        
        if total_weight == 0:
            return 0.0
            
        weighted_sum = sum(
            factor_scores.get(factor_name, 0.0) * factor.weight
            for factor_name, factor in factors.items()
        )
        
        return weighted_sum / total_weight 