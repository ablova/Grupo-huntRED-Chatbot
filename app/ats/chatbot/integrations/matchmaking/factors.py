"""
Factores ponderados para el sistema de matchmaking.

Este módulo define los factores y sus pesos para el sistema de matchmaking,
integrando todas las dimensiones de análisis disponibles y adaptándose a las
diferentes unidades de negocio.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class BusinessUnit(Enum):
    """Unidades de negocio."""
    HUNTRED = "huntRED"
    HUNTRED_EXECUTIVE = "huntRED® executive"
    HUNTU = "huntU"
    AMIGRO = "Amigro"
    SEXSI = "SEXSI"

class DEIRequirement(Enum):
    """Tipos de requisitos DEI."""
    NONE = "none"
    DIVERSITY = "diversity"
    INCLUSION = "inclusion"
    EQUITY = "equity"
    ALL = "all"

@dataclass
class DEIConfig:
    """Configuración de requisitos DEI para una posición."""
    requirement_type: DEIRequirement
    is_required: bool
    weight: float
    description: str
    sources: List[str]

class DEIManager:
    """Gestor de requisitos DEI."""
    
    # Configuraciones DEI por unidad de negocio
    DEI_CONFIGS = {
        BusinessUnit.HUNTRED: {
            DEIRequirement.DIVERSITY: DEIConfig(
                requirement_type=DEIRequirement.DIVERSITY,
                is_required=False,
                weight=0.05,
                description="Representación diversa en posiciones específicas",
                sources=['linkedin', 'cv']
            ),
            DEIRequirement.INCLUSION: DEIConfig(
                requirement_type=DEIRequirement.INCLUSION,
                is_required=False,
                weight=0.03,
                description="Experiencia en liderazgo inclusivo",
                sources=['linkedin', 'assessments']
            )
        },
        BusinessUnit.HUNTRED_EXECUTIVE: {
            DEIRequirement.ALL: DEIConfig(
                requirement_type=DEIRequirement.ALL,
                is_required=True,
                weight=0.10,
                description="Requisitos completos de DEI para posiciones ejecutivas",
                sources=['linkedin', 'cv', 'assessments', 'references']
            )
        }
    }
    
    @classmethod
    def should_apply_dei(cls, business_unit: BusinessUnit, position_description: str) -> bool:
        """
        Determina si se deben aplicar factores DEI.
        
        Args:
            business_unit: Unidad de negocio
            position_description: Descripción del puesto
            
        Returns:
            bool: True si se deben aplicar factores DEI
        """
        # Solo aplicar para huntRED y huntRED executive
        if business_unit not in [BusinessUnit.HUNTRED, BusinessUnit.HUNTRED_EXECUTIVE]:
            return False
            
        # Verificar si la descripción menciona requisitos DEI
        dei_keywords = [
            'diversidad', 'inclusión', 'equidad', 'DEI',
            'diversity', 'inclusion', 'equity',
            'grupos subrepresentados', 'underrepresented groups',
            'perspectivas diversas', 'diverse perspectives'
        ]
        
        return any(keyword.lower() in position_description.lower() for keyword in dei_keywords)
    
    @classmethod
    def get_dei_weight(cls, business_unit: BusinessUnit, position_description: str) -> float:
        """
        Obtiene el peso DEI para una posición.
        
        Args:
            business_unit: Unidad de negocio
            position_description: Descripción del puesto
            
        Returns:
            float: Peso DEI (0.0 si no aplica)
        """
        if not cls.should_apply_dei(business_unit, position_description):
            return 0.0
            
        configs = cls.DEI_CONFIGS.get(business_unit, {})
        if business_unit == BusinessUnit.HUNTRED_EXECUTIVE:
            return configs[DEIRequirement.ALL].weight
            
        # Para huntRED, sumar los pesos de los requisitos que apliquen
        total_weight = 0.0
        for config in configs.values():
            if config.is_required:
                total_weight += config.weight
                
        return total_weight
    
    @classmethod
    def get_dei_sources(cls, business_unit: BusinessUnit, position_description: str) -> List[str]:
        """
        Obtiene las fuentes de datos DEI para una posición.
        
        Args:
            business_unit: Unidad de negocio
            position_description: Descripción del puesto
            
        Returns:
            List[str]: Lista de fuentes de datos
        """
        if not cls.should_apply_dei(business_unit, position_description):
            return []
            
        configs = cls.DEI_CONFIGS.get(business_unit, {})
        if business_unit == BusinessUnit.HUNTRED_EXECUTIVE:
            return configs[DEIRequirement.ALL].sources
            
        # Para huntRED, unir todas las fuentes
        sources = set()
        for config in configs.values():
            if config.is_required:
                sources.update(config.sources)
                
        return list(sources)

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
    DEI = "dei"  # Diversidad, Equidad e Inclusión

@dataclass
class Factor:
    """Estructura para definir un factor."""
    name: str
    weight: float
    description: str
    sources: List[str]
    min_score: float = 0.0
    max_score: float = 1.0
    business_units: Optional[List[BusinessUnit]] = None  # None significa todas las unidades

class MatchmakingFactors:
    """Factores ponderados para matchmaking."""
    
    # Pesos base por categoría principal
    BASE_CATEGORY_WEIGHTS = {
        FactorCategory.TECHNICAL: 0.25,    # 25%
        FactorCategory.BEHAVIORAL: 0.20,   # 20%
        FactorCategory.CULTURAL: 0.15,     # 15%
        FactorCategory.CAREER: 0.15,       # 15%
        FactorCategory.PERSONAL: 0.10,     # 10%
        FactorCategory.NETWORK: 0.05,      # 5%
        FactorCategory.INNOVATION: 0.05,   # 5%
        FactorCategory.LEADERSHIP: 0.05,   # 5%
        FactorCategory.DEI: 0.00          # 0% por defecto
    }
    
    # Ajustes por unidad de negocio
    BUSINESS_UNIT_ADJUSTMENTS = {
        BusinessUnit.HUNTRED: {
            FactorCategory.LEADERSHIP: 0.15,  # +10%
            FactorCategory.TECHNICAL: 0.20,   # -5%
            FactorCategory.DEI: 0.05          # +5% para posiciones ejecutivas
        },
        BusinessUnit.HUNTRED_EXECUTIVE: {
            FactorCategory.LEADERSHIP: 0.15,  # +10%
            FactorCategory.TECHNICAL: 0.20,   # -5%
            FactorCategory.DEI: 0.05          # +5% para posiciones ejecutivas
        },
        BusinessUnit.HUNTU: {
            FactorCategory.TECHNICAL: 0.30,   # +5%
            FactorCategory.INNOVATION: 0.10,  # +5%
            FactorCategory.LEADERSHIP: 0.00   # -5%
        },
        BusinessUnit.AMIGRO: {
            FactorCategory.CULTURAL: 0.20,    # +5%
            FactorCategory.PERSONAL: 0.15,    # +5%
            FactorCategory.TECHNICAL: 0.20    # -5%
        },
        BusinessUnit.SEXSI: {
            FactorCategory.BEHAVIORAL: 0.25,  # +5%
            FactorCategory.CULTURAL: 0.20,    # +5%
            FactorCategory.TECHNICAL: 0.20    # -5%
        }
    }
    
    # Factores DEI (solo para posiciones específicas)
    DEI_FACTORS = {
        'diversity_representation': Factor(
            name="Representación Diversa",
            weight=0.40,
            description="Representación de grupos subrepresentados",
            sources=['linkedin', 'cv'],
            business_units=[BusinessUnit.HUNTRED]  # Solo para huntRED
        ),
        'inclusive_leadership': Factor(
            name="Liderazgo Inclusivo",
            weight=0.30,
            description="Experiencia en liderazgo inclusivo",
            sources=['linkedin', 'assessments'],
            business_units=[BusinessUnit.HUNTRED, BusinessUnit.HUNTU]
        ),
        'cultural_competence': Factor(
            name="Competencia Cultural",
            weight=0.30,
            description="Habilidad para trabajar en entornos diversos",
            sources=['assessments', 'references'],
            business_units=[BusinessUnit.HUNTRED, BusinessUnit.AMIGRO]
        )
    }
    
    @classmethod
    def get_category_weights(cls, business_unit: BusinessUnit, position_description: str) -> Dict[FactorCategory, float]:
        """
        Obtiene los pesos de categoría ajustados para una unidad de negocio.
        
        Args:
            business_unit: Unidad de negocio
            position_description: Descripción del puesto
            
        Returns:
            Dict con pesos ajustados
        """
        weights = cls.BASE_CATEGORY_WEIGHTS.copy()
        
        # Aplicar ajustes de la unidad de negocio
        if business_unit in cls.BUSINESS_UNIT_ADJUSTMENTS:
            for category, adjustment in cls.BUSINESS_UNIT_ADJUSTMENTS[business_unit].items():
                weights[category] = adjustment
                
        # Aplicar peso DEI si corresponde
        dei_weight = DEIManager.get_dei_weight(business_unit, position_description)
        if dei_weight > 0:
            weights[FactorCategory.DEI] = dei_weight
            
        # Normalizar pesos
        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}
    
    @classmethod
    def get_factors_for_position(
        cls,
        business_unit: BusinessUnit,
        position_type: str,
        position_description: str
    ) -> Dict[str, Dict[str, Factor]]:
        """
        Obtiene los factores relevantes para una posición específica.
        
        Args:
            business_unit: Unidad de negocio
            position_type: Tipo de posición
            position_description: Descripción del puesto
            
        Returns:
            Dict con factores filtrados
        """
        all_factors = cls.get_all_factors()
        filtered_factors = {}
        
        # Verificar si se deben aplicar factores DEI
        should_apply_dei = DEIManager.should_apply_dei(business_unit, position_description)
        
        for category, factors in all_factors.items():
            # Filtrar factores por unidad de negocio y requisitos DEI
            category_factors = {
                name: factor for name, factor in factors.items()
                if (factor.business_units is None or business_unit in factor.business_units) and
                   (category != FactorCategory.DEI.value or should_apply_dei)
            }
            
            if category_factors:
                filtered_factors[category] = category_factors
                
        return filtered_factors
    
    @classmethod
    def calculate_weighted_score(
        cls,
        category: str,
        factor_scores: Dict[str, float],
        business_unit: BusinessUnit,
        position_type: str
    ) -> float:
        """
        Calcula el score ponderado para una categoría.
        
        Args:
            category: Categoría a evaluar
            factor_scores: Scores de los factores
            business_unit: Unidad de negocio
            position_type: Tipo de posición
            
        Returns:
            Score ponderado
        """
        factors = cls.get_factors_for_position(business_unit, position_type).get(category, {})
        total_weight = sum(factor.weight for factor in factors.values())
        
        if total_weight == 0:
            return 0.0
            
        weighted_sum = sum(
            factor_scores.get(factor_name, 0.0) * factor.weight
            for factor_name, factor in factors.items()
        )
        
        return weighted_sum / total_weight 