"""
Sistema de Análisis Cultural huntRED® v2
=======================================

Funcionalidades:
- Análisis cultural completo candidato-empresa
- Machine Learning para matching cultural
- Evaluación de valores y comportamientos
- Predicción de fit y retención
- Recomendaciones de onboarding
- Dashboard cultural interactivo
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

logger = logging.getLogger(__name__)

class CulturalDimension(Enum):
    """Dimensiones culturales organizacionales."""
    HIERARCHY = "hierarchy"
    COLLABORATION = "collaboration"
    INNOVATION = "innovation"
    WORK_LIFE_BALANCE = "work_life_balance"
    COMMUNICATION = "communication"
    DECISION_MAKING = "decision_making"
    RISK_TOLERANCE = "risk_tolerance"
    PERFORMANCE_ORIENTATION = "performance_orientation"
    DIVERSITY_INCLUSION = "diversity_inclusion"
    LEARNING_DEVELOPMENT = "learning_development"

class PersonalityTrait(Enum):
    """Rasgos de personalidad relevantes."""
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"
    ADAPTABILITY = "adaptability"
    RESILIENCE = "resilience"
    LEADERSHIP = "leadership"

class WorkStyle(Enum):
    """Estilos de trabajo."""
    INDEPENDENT = "independent"
    COLLABORATIVE = "collaborative"
    STRUCTURED = "structured"
    FLEXIBLE = "flexible"
    DETAIL_ORIENTED = "detail_oriented"
    BIG_PICTURE = "big_picture"
    FAST_PACED = "fast_paced"
    METHODICAL = "methodical"

@dataclass
class CulturalProfile:
    """Perfil cultural de una persona u organización."""
    id: str
    name: str
    type: str  # "individual" o "organization"
    
    # Dimensiones culturales (0-100)
    dimensions: Dict[CulturalDimension, float] = field(default_factory=dict)
    
    # Rasgos de personalidad (0-100)
    personality_traits: Dict[PersonalityTrait, float] = field(default_factory=dict)
    
    # Estilos de trabajo preferidos
    work_styles: Dict[WorkStyle, float] = field(default_factory=dict)
    
    # Valores organizacionales
    core_values: List[str] = field(default_factory=list)
    anti_values: List[str] = field(default_factory=list)
    
    # Metadatos
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    
    # Datos de entrada
    survey_responses: Dict[str, Any] = field(default_factory=dict)
    behavioral_data: Dict[str, Any] = field(default_factory=dict)
    
    # Análisis
    confidence_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class CulturalMatch:
    """Resultado de matching cultural."""
    candidate_id: str
    organization_id: str
    overall_fit_score: float  # 0-100
    
    # Scores por dimensión
    dimension_scores: Dict[CulturalDimension, float] = field(default_factory=dict)
    personality_alignment: Dict[PersonalityTrait, float] = field(default_factory=dict)
    work_style_compatibility: Dict[WorkStyle, float] = field(default_factory=dict)
    
    # Análisis detallado
    strengths: List[str] = field(default_factory=list)
    potential_challenges: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Predicciones
    retention_probability: float = 0.0
    performance_prediction: float = 0.0
    integration_timeline: int = 90  # días
    
    # Metadatos
    analysis_date: datetime = field(default_factory=datetime.now)
    confidence_level: float = 0.0

class CulturalFitEngine:
    """Motor principal de análisis cultural."""
    
    def __init__(self):
        self.cultural_profiles: Dict[str, CulturalProfile] = {}
        self.matches: Dict[str, CulturalMatch] = {}
        
        # Modelos ML
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.cultural_weights = self._initialize_cultural_weights()
        
        # Configuración
        self.dimension_importance = {
            CulturalDimension.COLLABORATION: 0.15,
            CulturalDimension.COMMUNICATION: 0.12,
            CulturalDimension.WORK_LIFE_BALANCE: 0.10,
            CulturalDimension.INNOVATION: 0.10,
            CulturalDimension.HIERARCHY: 0.08,
            CulturalDimension.DECISION_MAKING: 0.08,
            CulturalDimension.PERFORMANCE_ORIENTATION: 0.08,
            CulturalDimension.RISK_TOLERANCE: 0.07,
            CulturalDimension.DIVERSITY_INCLUSION: 0.12,
            CulturalDimension.LEARNING_DEVELOPMENT: 0.10
        }
        
        # Setup inicial
        self._setup_sample_profiles()
    
    def _initialize_cultural_weights(self) -> Dict[str, float]:
        """Inicializa pesos para diferentes factores culturales."""
        
        return {
            "values_alignment": 0.25,
            "communication_style": 0.20,
            "work_preferences": 0.20,
            "personality_fit": 0.15,
            "growth_mindset": 0.10,
            "behavioral_indicators": 0.10
        }
    
    def _setup_sample_profiles(self):
        """Configura perfiles de ejemplo."""
        
        # Perfil organizacional ejemplo
        tech_company = CulturalProfile(
            id="org_tech_001",
            name="TechInnovate Corp",
            type="organization",
            dimensions={
                CulturalDimension.INNOVATION: 90,
                CulturalDimension.COLLABORATION: 85,
                CulturalDimension.HIERARCHY: 30,
                CulturalDimension.WORK_LIFE_BALANCE: 75,
                CulturalDimension.COMMUNICATION: 80,
                CulturalDimension.DECISION_MAKING: 70,
                CulturalDimension.RISK_TOLERANCE: 85,
                CulturalDimension.PERFORMANCE_ORIENTATION: 90,
                CulturalDimension.DIVERSITY_INCLUSION: 95,
                CulturalDimension.LEARNING_DEVELOPMENT: 90
            },
            work_styles={
                WorkStyle.COLLABORATIVE: 90,
                WorkStyle.FLEXIBLE: 85,
                WorkStyle.FAST_PACED: 80,
                WorkStyle.BIG_PICTURE: 75,
                WorkStyle.INDEPENDENT: 60,
                WorkStyle.STRUCTURED: 40,
                WorkStyle.DETAIL_ORIENTED: 50,
                WorkStyle.METHODICAL: 45
            },
            core_values=["Innovación", "Transparencia", "Diversidad", "Crecimiento", "Impacto"],
            anti_values=["Micromanagement", "Burocracia", "Conformismo"],
            industry="Technology",
            company_size="Startup",
            location="Remote-First"
        )
        
        # Perfil de candidato ejemplo
        candidate_profile = CulturalProfile(
            id="cand_001",
            name="Ana García",
            type="individual",
            dimensions={
                CulturalDimension.INNOVATION: 85,
                CulturalDimension.COLLABORATION: 90,
                CulturalDimension.HIERARCHY: 25,
                CulturalDimension.WORK_LIFE_BALANCE: 80,
                CulturalDimension.COMMUNICATION: 85,
                CulturalDimension.DECISION_MAKING: 75,
                CulturalDimension.RISK_TOLERANCE: 70,
                CulturalDimension.PERFORMANCE_ORIENTATION: 85,
                CulturalDimension.DIVERSITY_INCLUSION: 95,
                CulturalDimension.LEARNING_DEVELOPMENT: 95
            },
            personality_traits={
                PersonalityTrait.OPENNESS: 90,
                PersonalityTrait.CONSCIENTIOUSNESS: 85,
                PersonalityTrait.EXTRAVERSION: 75,
                PersonalityTrait.AGREEABLENESS: 85,
                PersonalityTrait.NEUROTICISM: 20,
                PersonalityTrait.ADAPTABILITY: 90,
                PersonalityTrait.RESILIENCE: 80,
                PersonalityTrait.LEADERSHIP: 75
            },
            work_styles={
                WorkStyle.COLLABORATIVE: 95,
                WorkStyle.FLEXIBLE: 90,
                WorkStyle.FAST_PACED: 75,
                WorkStyle.BIG_PICTURE: 80,
                WorkStyle.INDEPENDENT: 70,
                WorkStyle.STRUCTURED: 60,
                WorkStyle.DETAIL_ORIENTED: 65,
                WorkStyle.METHODICAL: 55
            }
        )
        
        self.cultural_profiles.update({
            "org_tech_001": tech_company,
            "cand_001": candidate_profile
        })
    
    async def create_cultural_profile(self, profile_data: Dict[str, Any]) -> str:
        """Crea un nuevo perfil cultural."""
        
        profile_id = profile_data.get("id", str(uuid.uuid4()))
        
        profile = CulturalProfile(
            id=profile_id,
            name=profile_data["name"],
            type=profile_data["type"],
            survey_responses=profile_data.get("survey_responses", {}),
            behavioral_data=profile_data.get("behavioral_data", {}),
            industry=profile_data.get("industry"),
            company_size=profile_data.get("company_size"),
            location=profile_data.get("location")
        )
        
        # Analizar datos para extraer dimensiones culturales
        await self._analyze_cultural_dimensions(profile)
        
        # Calcular confidence score
        profile.confidence_score = await self._calculate_confidence_score(profile)
        
        self.cultural_profiles[profile_id] = profile
        
        logger.info(f"Created cultural profile: {profile_id} - {profile.name}")
        return profile_id
    
    async def _analyze_cultural_dimensions(self, profile: CulturalProfile):
        """Analiza y extrae dimensiones culturales de los datos."""
        
        # Analizar respuestas de encuesta
        if profile.survey_responses:
            dimensions = await self._extract_dimensions_from_survey(profile.survey_responses)
            profile.dimensions.update(dimensions)
        
        # Analizar datos comportamentales
        if profile.behavioral_data:
            behavioral_dimensions = await self._extract_dimensions_from_behavior(profile.behavioral_data)
            profile.dimensions.update(behavioral_dimensions)
        
        # Analizar personalidad si es individual
        if profile.type == "individual" and profile.survey_responses:
            personality = await self._extract_personality_traits(profile.survey_responses)
            profile.personality_traits.update(personality)
        
        # Analizar estilos de trabajo
        work_styles = await self._extract_work_styles(profile)
        profile.work_styles.update(work_styles)
    
    async def _extract_dimensions_from_survey(self, survey_responses: Dict[str, Any]) -> Dict[CulturalDimension, float]:
        """Extrae dimensiones culturales de respuestas de encuesta."""
        
        dimensions = {}
        
        # Mapeo de preguntas a dimensiones (ejemplo simplificado)
        question_mappings = {
            "innovation_importance": CulturalDimension.INNOVATION,
            "collaboration_preference": CulturalDimension.COLLABORATION,
            "hierarchy_comfort": CulturalDimension.HIERARCHY,
            "work_life_balance": CulturalDimension.WORK_LIFE_BALANCE,
            "communication_style": CulturalDimension.COMMUNICATION,
            "decision_autonomy": CulturalDimension.DECISION_MAKING,
            "risk_appetite": CulturalDimension.RISK_TOLERANCE,
            "performance_focus": CulturalDimension.PERFORMANCE_ORIENTATION,
            "diversity_value": CulturalDimension.DIVERSITY_INCLUSION,
            "learning_growth": CulturalDimension.LEARNING_DEVELOPMENT
        }
        
        for question, dimension in question_mappings.items():
            if question in survey_responses:
                # Normalizar respuesta a escala 0-100
                raw_value = survey_responses[question]
                if isinstance(raw_value, (int, float)):
                    # Asumiendo escala 1-10, convertir a 0-100
                    normalized_value = ((raw_value - 1) / 9) * 100
                    dimensions[dimension] = max(0, min(100, normalized_value))
        
        return dimensions
    
    async def _extract_dimensions_from_behavior(self, behavioral_data: Dict[str, Any]) -> Dict[CulturalDimension, float]:
        """Extrae dimensiones culturales de datos comportamentales."""
        
        dimensions = {}
        
        # Analizar patrones de comunicación
        if "communication_frequency" in behavioral_data:
            freq = behavioral_data["communication_frequency"]
            dimensions[CulturalDimension.COMMUNICATION] = min(100, freq * 10)
        
        # Analizar horarios de trabajo
        if "work_hours" in behavioral_data:
            hours = behavioral_data["work_hours"]
            # Inferir work-life balance basado en horas trabajadas
            if hours <= 40:
                dimensions[CulturalDimension.WORK_LIFE_BALANCE] = 90
            elif hours <= 50:
                dimensions[CulturalDimension.WORK_LIFE_BALANCE] = 70
            else:
                dimensions[CulturalDimension.WORK_LIFE_BALANCE] = 40
        
        # Analizar colaboración
        if "collaboration_score" in behavioral_data:
            score = behavioral_data["collaboration_score"]
            dimensions[CulturalDimension.COLLABORATION] = score
        
        return dimensions
    
    async def _extract_personality_traits(self, survey_responses: Dict[str, Any]) -> Dict[PersonalityTrait, float]:
        """Extrae rasgos de personalidad de respuestas."""
        
        traits = {}
        
        # Mapeo simplificado Big Five
        trait_mappings = {
            "openness_score": PersonalityTrait.OPENNESS,
            "conscientiousness_score": PersonalityTrait.CONSCIENTIOUSNESS,
            "extraversion_score": PersonalityTrait.EXTRAVERSION,
            "agreeableness_score": PersonalityTrait.AGREEABLENESS,
            "neuroticism_score": PersonalityTrait.NEUROTICISM,
            "adaptability_score": PersonalityTrait.ADAPTABILITY,
            "resilience_score": PersonalityTrait.RESILIENCE,
            "leadership_score": PersonalityTrait.LEADERSHIP
        }
        
        for question, trait in trait_mappings.items():
            if question in survey_responses:
                raw_value = survey_responses[question]
                if isinstance(raw_value, (int, float)):
                    normalized_value = ((raw_value - 1) / 9) * 100
                    traits[trait] = max(0, min(100, normalized_value))
        
        return traits
    
    async def _extract_work_styles(self, profile: CulturalProfile) -> Dict[WorkStyle, float]:
        """Extrae estilos de trabajo preferidos."""
        
        work_styles = {}
        
        # Inferir estilos basado en dimensiones culturales
        if profile.dimensions:
            # Colaborativo vs Independiente
            collab_score = profile.dimensions.get(CulturalDimension.COLLABORATION, 50)
            work_styles[WorkStyle.COLLABORATIVE] = collab_score
            work_styles[WorkStyle.INDEPENDENT] = 100 - collab_score
            
            # Estructurado vs Flexible
            hierarchy_score = profile.dimensions.get(CulturalDimension.HIERARCHY, 50)
            work_styles[WorkStyle.STRUCTURED] = hierarchy_score
            work_styles[WorkStyle.FLEXIBLE] = 100 - hierarchy_score
            
            # Ritmo de trabajo
            performance_score = profile.dimensions.get(CulturalDimension.PERFORMANCE_ORIENTATION, 50)
            work_styles[WorkStyle.FAST_PACED] = performance_score
            work_styles[WorkStyle.METHODICAL] = 100 - performance_score
            
            # Enfoque
            innovation_score = profile.dimensions.get(CulturalDimension.INNOVATION, 50)
            work_styles[WorkStyle.BIG_PICTURE] = innovation_score
            work_styles[WorkStyle.DETAIL_ORIENTED] = 100 - innovation_score
        
        return work_styles
    
    async def _calculate_confidence_score(self, profile: CulturalProfile) -> float:
        """Calcula el score de confianza del perfil."""
        
        confidence = 0.0
        factors = 0
        
        # Factor: cantidad de datos de entrada
        if profile.survey_responses:
            response_ratio = len(profile.survey_responses) / 20  # 20 preguntas ideales
            confidence += min(1.0, response_ratio) * 30
            factors += 1
        
        if profile.behavioral_data:
            behavior_ratio = len(profile.behavioral_data) / 10  # 10 métricas ideales
            confidence += min(1.0, behavior_ratio) * 20
            factors += 1
        
        # Factor: completitud de dimensiones
        dimension_ratio = len(profile.dimensions) / len(CulturalDimension)
        confidence += dimension_ratio * 30
        factors += 1
        
        # Factor: consistencia de datos
        if len(profile.dimensions) > 3:
            # Verificar consistencia entre dimensiones relacionadas
            consistency_score = await self._check_dimension_consistency(profile.dimensions)
            confidence += consistency_score * 20
            factors += 1
        
        return confidence / factors if factors > 0 else 0.0
    
    async def _check_dimension_consistency(self, dimensions: Dict[CulturalDimension, float]) -> float:
        """Verifica consistencia entre dimensiones relacionadas."""
        
        consistency_checks = [
            # Colaboración y comunicación deberían estar correlacionadas
            (CulturalDimension.COLLABORATION, CulturalDimension.COMMUNICATION),
            # Innovación y tolerancia al riesgo
            (CulturalDimension.INNOVATION, CulturalDimension.RISK_TOLERANCE),
            # Jerarquía y toma de decisiones
            (CulturalDimension.HIERARCHY, CulturalDimension.DECISION_MAKING)
        ]
        
        consistency_scores = []
        
        for dim1, dim2 in consistency_checks:
            if dim1 in dimensions and dim2 in dimensions:
                diff = abs(dimensions[dim1] - dimensions[dim2])
                # Menor diferencia = mayor consistencia
                consistency = 1.0 - (diff / 100)
                consistency_scores.append(consistency)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5
    
    async def calculate_cultural_match(self, candidate_id: str, organization_id: str) -> str:
        """Calcula el matching cultural entre candidato y organización."""
        
        candidate = self.cultural_profiles.get(candidate_id)
        organization = self.cultural_profiles.get(organization_id)
        
        if not candidate or not organization:
            raise ValueError("Candidate or organization profile not found")
        
        match_id = f"{candidate_id}_{organization_id}_{int(datetime.now().timestamp())}"
        
        # Calcular scores por dimensión
        dimension_scores = await self._calculate_dimension_compatibility(candidate, organization)
        
        # Calcular alineación de personalidad
        personality_alignment = await self._calculate_personality_alignment(candidate, organization)
        
        # Calcular compatibilidad de estilos de trabajo
        work_style_compatibility = await self._calculate_work_style_compatibility(candidate, organization)
        
        # Calcular score general
        overall_score = await self._calculate_overall_fit_score(
            dimension_scores, personality_alignment, work_style_compatibility
        )
        
        # Generar análisis detallado
        strengths, challenges, recommendations = await self._generate_match_insights(
            candidate, organization, dimension_scores
        )
        
        # Predicciones ML
        retention_prob = await self._predict_retention(candidate, organization, overall_score)
        performance_pred = await self._predict_performance(candidate, organization, overall_score)
        integration_time = await self._estimate_integration_timeline(candidate, organization)
        
        # Crear resultado de matching
        match = CulturalMatch(
            candidate_id=candidate_id,
            organization_id=organization_id,
            overall_fit_score=overall_score,
            dimension_scores=dimension_scores,
            personality_alignment=personality_alignment,
            work_style_compatibility=work_style_compatibility,
            strengths=strengths,
            potential_challenges=challenges,
            recommendations=recommendations,
            retention_probability=retention_prob,
            performance_prediction=performance_pred,
            integration_timeline=integration_time,
            confidence_level=min(candidate.confidence_score, organization.confidence_score)
        )
        
        self.matches[match_id] = match
        
        logger.info(f"Cultural match calculated: {match_id} - Score: {overall_score:.1f}")
        return match_id
    
    async def _calculate_dimension_compatibility(self, candidate: CulturalProfile, 
                                               organization: CulturalProfile) -> Dict[CulturalDimension, float]:
        """Calcula compatibilidad por dimensión cultural."""
        
        compatibility_scores = {}
        
        for dimension in CulturalDimension:
            candidate_score = candidate.dimensions.get(dimension, 50)
            org_score = organization.dimensions.get(dimension, 50)
            
            # Calcular compatibilidad basada en cercanía de valores
            # Para algunas dimensiones, valores similares son mejores
            # Para otras, pueden ser complementarios
            
            if dimension in [CulturalDimension.COLLABORATION, CulturalDimension.COMMUNICATION,
                           CulturalDimension.DIVERSITY_INCLUSION, CulturalDimension.LEARNING_DEVELOPMENT]:
                # Dimensiones donde similaridad es buena
                difference = abs(candidate_score - org_score)
                compatibility = 100 - difference
            
            elif dimension == CulturalDimension.HIERARCHY:
                # Para jerarquía, candidato debería estar cómodo con nivel org
                if candidate_score >= org_score - 20:  # Tolerancia de 20 puntos
                    compatibility = 100 - abs(candidate_score - org_score)
                else:
                    compatibility = 50  # Mismatch significativo
            
            else:
                # Compatibilidad general basada en cercanía
                difference = abs(candidate_score - org_score)
                compatibility = 100 - (difference * 0.8)  # Factor de suavizado
            
            compatibility_scores[dimension] = max(0, min(100, compatibility))
        
        return compatibility_scores
    
    async def _calculate_personality_alignment(self, candidate: CulturalProfile,
                                             organization: CulturalProfile) -> Dict[PersonalityTrait, float]:
        """Calcula alineación de personalidad con cultura organizacional."""
        
        alignment_scores = {}
        
        # Mapeo de rasgos de personalidad a preferencias organizacionales
        trait_org_preferences = {
            PersonalityTrait.OPENNESS: [CulturalDimension.INNOVATION, CulturalDimension.LEARNING_DEVELOPMENT],
            PersonalityTrait.CONSCIENTIOUSNESS: [CulturalDimension.PERFORMANCE_ORIENTATION],
            PersonalityTrait.EXTRAVERSION: [CulturalDimension.COLLABORATION, CulturalDimension.COMMUNICATION],
            PersonalityTrait.AGREEABLENESS: [CulturalDimension.COLLABORATION, CulturalDimension.DIVERSITY_INCLUSION],
            PersonalityTrait.ADAPTABILITY: [CulturalDimension.INNOVATION, CulturalDimension.RISK_TOLERANCE],
            PersonalityTrait.LEADERSHIP: [CulturalDimension.DECISION_MAKING, CulturalDimension.PERFORMANCE_ORIENTATION]
        }
        
        for trait, related_dimensions in trait_org_preferences.items():
            candidate_trait_score = candidate.personality_traits.get(trait, 50)
            
            # Calcular promedio de dimensiones organizacionales relacionadas
            org_dimension_scores = [
                organization.dimensions.get(dim, 50) for dim in related_dimensions
            ]
            avg_org_score = sum(org_dimension_scores) / len(org_dimension_scores)
            
            # Calcular alineación
            difference = abs(candidate_trait_score - avg_org_score)
            alignment = 100 - difference
            
            alignment_scores[trait] = max(0, min(100, alignment))
        
        return alignment_scores
    
    async def _calculate_work_style_compatibility(self, candidate: CulturalProfile,
                                                organization: CulturalProfile) -> Dict[WorkStyle, float]:
        """Calcula compatibilidad de estilos de trabajo."""
        
        compatibility_scores = {}
        
        for style in WorkStyle:
            candidate_preference = candidate.work_styles.get(style, 50)
            org_preference = organization.work_styles.get(style, 50)
            
            # Calcular compatibilidad
            difference = abs(candidate_preference - org_preference)
            compatibility = 100 - difference
            
            compatibility_scores[style] = max(0, min(100, compatibility))
        
        return compatibility_scores
    
    async def _calculate_overall_fit_score(self, dimension_scores: Dict[CulturalDimension, float],
                                         personality_alignment: Dict[PersonalityTrait, float],
                                         work_style_compatibility: Dict[WorkStyle, float]) -> float:
        """Calcula el score general de fit cultural."""
        
        # Weighted average de diferentes componentes
        dimension_weight = 0.5
        personality_weight = 0.3
        work_style_weight = 0.2
        
        # Score ponderado por dimensiones culturales
        weighted_dimension_score = 0.0
        for dimension, score in dimension_scores.items():
            weight = self.dimension_importance.get(dimension, 0.1)
            weighted_dimension_score += score * weight
        
        # Score promedio de personalidad
        personality_score = sum(personality_alignment.values()) / len(personality_alignment) if personality_alignment else 50
        
        # Score promedio de estilos de trabajo
        work_style_score = sum(work_style_compatibility.values()) / len(work_style_compatibility) if work_style_compatibility else 50
        
        # Calcular score final
        overall_score = (
            weighted_dimension_score * dimension_weight +
            personality_score * personality_weight +
            work_style_score * work_style_weight
        )
        
        return max(0, min(100, overall_score))
    
    async def _generate_match_insights(self, candidate: CulturalProfile, organization: CulturalProfile,
                                     dimension_scores: Dict[CulturalDimension, float]) -> Tuple[List[str], List[str], List[str]]:
        """Genera insights detallados del matching."""
        
        strengths = []
        challenges = []
        recommendations = []
        
        # Analizar fortalezas (scores altos)
        strong_dimensions = [dim for dim, score in dimension_scores.items() if score >= 80]
        for dimension in strong_dimensions:
            if dimension == CulturalDimension.COLLABORATION:
                strengths.append("Excelente alineación en trabajo colaborativo y espíritu de equipo")
            elif dimension == CulturalDimension.INNOVATION:
                strengths.append("Fuerte compatibilidad en mentalidad innovadora y creatividad")
            elif dimension == CulturalDimension.COMMUNICATION:
                strengths.append("Muy buena alineación en estilos de comunicación")
            elif dimension == CulturalDimension.WORK_LIFE_BALANCE:
                strengths.append("Expectativas alineadas sobre balance vida-trabajo")
        
        # Analizar desafíos (scores bajos)
        weak_dimensions = [dim for dim, score in dimension_scores.items() if score <= 60]
        for dimension in weak_dimensions:
            if dimension == CulturalDimension.HIERARCHY:
                challenges.append("Posible desalineación en preferencias de estructura organizacional")
                recommendations.append("Clarificar expectativas sobre autonomía y niveles de aprobación")
            elif dimension == CulturalDimension.RISK_TOLERANCE:
                challenges.append("Diferencias en apetito de riesgo y toma de decisiones")
                recommendations.append("Establecer marcos claros para experimentación y tolerancia al fallo")
            elif dimension == CulturalDimension.COMMUNICATION:
                challenges.append("Estilos de comunicación potencialmente incompatibles")
                recommendations.append("Implementar sesiones de coaching en comunicación durante onboarding")
        
        # Recomendaciones generales
        if len(strong_dimensions) >= 6:
            recommendations.append("Candidato con excelente fit cultural - acelerar proceso de onboarding")
        elif len(weak_dimensions) >= 4:
            recommendations.append("Considerar período de prueba extendido con mentoring intensivo")
        
        recommendations.append("Realizar check-ins culturales a los 30, 60 y 90 días")
        
        return strengths, challenges, recommendations
    
    async def _predict_retention(self, candidate: CulturalProfile, organization: CulturalProfile, 
                               overall_score: float) -> float:
        """Predice probabilidad de retención basada en fit cultural."""
        
        # Modelo predictivo simplificado
        base_retention = overall_score / 100
        
        # Factores adicionales
        work_life_balance_score = candidate.dimensions.get(CulturalDimension.WORK_LIFE_BALANCE, 50)
        org_work_life_score = organization.dimensions.get(CulturalDimension.WORK_LIFE_BALANCE, 50)
        
        # Work-life balance es crítico para retención
        balance_factor = 1.0 - (abs(work_life_balance_score - org_work_life_score) / 100) * 0.3
        
        # Personalidad - baja neurosis mejora retención
        neuroticism = candidate.personality_traits.get(PersonalityTrait.NEUROTICISM, 50)
        stability_factor = 1.0 + ((50 - neuroticism) / 100) * 0.2
        
        retention_probability = base_retention * balance_factor * stability_factor
        return max(0.0, min(1.0, retention_probability))
    
    async def _predict_performance(self, candidate: CulturalProfile, organization: CulturalProfile,
                                 overall_score: float) -> float:
        """Predice rendimiento potencial basado en fit cultural."""
        
        base_performance = overall_score / 100
        
        # Conscientiousness predice rendimiento
        conscientiousness = candidate.personality_traits.get(PersonalityTrait.CONSCIENTIOUSNESS, 50)
        performance_factor = 1.0 + (conscientiousness / 100 - 0.5) * 0.3
        
        # Alineación en performance orientation
        candidate_perf_orient = candidate.dimensions.get(CulturalDimension.PERFORMANCE_ORIENTATION, 50)
        org_perf_orient = organization.dimensions.get(CulturalDimension.PERFORMANCE_ORIENTATION, 50)
        
        alignment_factor = 1.0 - (abs(candidate_perf_orient - org_perf_orient) / 100) * 0.2
        
        performance_prediction = base_performance * performance_factor * alignment_factor
        return max(0.0, min(1.0, performance_prediction))
    
    async def _estimate_integration_timeline(self, candidate: CulturalProfile, 
                                           organization: CulturalProfile) -> int:
        """Estima tiempo de integración en días."""
        
        base_timeline = 90  # 3 meses base
        
        # Adaptabilidad reduce tiempo
        adaptability = candidate.personality_traits.get(PersonalityTrait.ADAPTABILITY, 50)
        adaptability_factor = 1.0 - (adaptability / 100 - 0.5) * 0.4
        
        # Extraversión facilita integración social
        extraversion = candidate.personality_traits.get(PersonalityTrait.EXTRAVERSION, 50)
        social_factor = 1.0 - (extraversion / 100 - 0.5) * 0.3
        
        # Complejidad organizacional puede aumentar tiempo
        hierarchy_level = organization.dimensions.get(CulturalDimension.HIERARCHY, 50)
        complexity_factor = 1.0 + (hierarchy_level / 100) * 0.2
        
        estimated_days = base_timeline * adaptability_factor * social_factor * complexity_factor
        return max(30, min(180, int(estimated_days)))
    
    def get_cultural_insights(self, profile_id: str) -> Dict[str, Any]:
        """Obtiene insights detallados de un perfil cultural."""
        
        profile = self.cultural_profiles.get(profile_id)
        if not profile:
            return {"error": "Profile not found"}
        
        # Analizar fortalezas culturales
        strong_dimensions = {
            dim: score for dim, score in profile.dimensions.items() 
            if score >= 75
        }
        
        weak_dimensions = {
            dim: score for dim, score in profile.dimensions.items() 
            if score <= 40
        }
        
        # Generar recomendaciones
        recommendations = []
        
        if profile.type == "individual":
            # Recomendaciones para candidatos
            if CulturalDimension.LEARNING_DEVELOPMENT in strong_dimensions:
                recommendations.append("Buscar organizaciones con fuerte cultura de aprendizaje")
            
            if CulturalDimension.INNOVATION in strong_dimensions:
                recommendations.append("Considerar startups o empresas de tecnología")
            
            if weak_dimensions.get(CulturalDimension.HIERARCHY, 100) <= 40:
                recommendations.append("Evitar organizaciones muy jerárquicas o burocráticas")
        
        else:
            # Recomendaciones para organizaciones
            if CulturalDimension.DIVERSITY_INCLUSION in strong_dimensions:
                recommendations.append("Destacar iniciativas de diversidad en proceso de reclutamiento")
            
            if weak_dimensions.get(CulturalDimension.WORK_LIFE_BALANCE, 100) <= 40:
                recommendations.append("Implementar políticas de bienestar y flexibilidad laboral")
        
        return {
            "profile_id": profile_id,
            "name": profile.name,
            "type": profile.type,
            "confidence_score": profile.confidence_score,
            "dimensions": profile.dimensions,
            "personality_traits": profile.personality_traits,
            "work_styles": profile.work_styles,
            "strong_dimensions": strong_dimensions,
            "improvement_areas": weak_dimensions,
            "recommendations": recommendations,
            "core_values": profile.core_values,
            "anti_values": profile.anti_values
        }
    
    def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Obtiene detalles completos de un matching cultural."""
        
        match = self.matches.get(match_id)
        if not match:
            return {"error": "Match not found"}
        
        # Clasificar el nivel de fit
        if match.overall_fit_score >= 85:
            fit_level = "Excelente"
            fit_description = "Candidato altamente compatible con la cultura organizacional"
        elif match.overall_fit_score >= 70:
            fit_level = "Bueno"
            fit_description = "Buen ajuste cultural con algunas áreas de desarrollo"
        elif match.overall_fit_score >= 55:
            fit_level = "Moderado"
            fit_description = "Ajuste cultural moderado, requiere atención especial"
        else:
            fit_level = "Bajo"
            fit_description = "Fit cultural limitado, alto riesgo de desajuste"
        
        return {
            "match_id": match_id,
            "candidate_id": match.candidate_id,
            "organization_id": match.organization_id,
            "overall_fit_score": match.overall_fit_score,
            "fit_level": fit_level,
            "fit_description": fit_description,
            "dimension_scores": match.dimension_scores,
            "personality_alignment": match.personality_alignment,
            "work_style_compatibility": match.work_style_compatibility,
            "strengths": match.strengths,
            "potential_challenges": match.potential_challenges,
            "recommendations": match.recommendations,
            "predictions": {
                "retention_probability": match.retention_probability * 100,
                "performance_prediction": match.performance_prediction * 100,
                "integration_timeline_days": match.integration_timeline
            },
            "confidence_level": match.confidence_level,
            "analysis_date": match.analysis_date.isoformat()
        }

# Funciones de utilidad
async def quick_cultural_assessment(survey_data: Dict[str, Any], profile_type: str = "individual") -> str:
    """Función de conveniencia para evaluación cultural rápida."""
    
    engine = CulturalFitEngine()
    
    profile_data = {
        "name": survey_data.get("name", "Assessment"),
        "type": profile_type,
        "survey_responses": survey_data
    }
    
    return await engine.create_cultural_profile(profile_data)

# Exportaciones
__all__ = [
    'CulturalDimension', 'PersonalityTrait', 'WorkStyle',
    'CulturalProfile', 'CulturalMatch', 'CulturalFitEngine',
    'quick_cultural_assessment'
]