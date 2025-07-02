"""
AURA - Impact Analyzer
Analizador de impacto social y sostenibilidad.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class ImpactDimension(Enum):
    """Dimensiones de impacto"""
    SOCIAL = "social"
    ENVIRONMENTAL = "environmental"
    ECONOMIC = "economic"
    GOVERNANCE = "governance"
    INNOVATION = "innovation"

class ImpactLevel(Enum):
    """Niveles de impacto"""
    TRANSFORMATIVE = "transformative"
    SIGNIFICANT = "significant"
    MODERATE = "moderate"
    MINIMAL = "minimal"
    NEGATIVE = "negative"

@dataclass
class ImpactAssessment:
    """Evaluación de impacto"""
    overall_impact_score: float
    impact_level: ImpactLevel
    dimension_scores: Dict[str, float]
    sustainability_metrics: Dict[str, float]
    recommendations: List[str]
    risk_factors: List[str]

class ImpactAnalyzer:
    """
    Analizador de impacto social y sostenibilidad para AURA.
    
    Características:
    - Análisis multi-dimensional de impacto
    - Métricas de sostenibilidad
    - Evaluación de responsabilidad social
    - Análisis de innovación social
    - Recomendaciones de mejora
    """
    
    def __init__(self):
        """Inicializa el analizador de impacto"""
        self.impact_dimensions = {
            ImpactDimension.SOCIAL: self._analyze_social_impact,
            ImpactDimension.ENVIRONMENTAL: self._analyze_environmental_impact,
            ImpactDimension.ECONOMIC: self._analyze_economic_impact,
            ImpactDimension.GOVERNANCE: self._analyze_governance_impact,
            ImpactDimension.INNOVATION: self._analyze_innovation_impact
        }
        
        logger.info("Impact Analyzer inicializado")
    
    async def analyze_impact_comprehensive(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]] = None
    ) -> ImpactAssessment:
        """
        Análisis comprehensivo de impacto.
        
        Args:
            person_data: Datos de la persona
            business_context: Contexto de negocio
            
        Returns:
            ImpactAssessment con análisis completo
        """
        try:
            dimension_scores = {}
            all_recommendations = []
            all_risk_factors = []
            
            # Analizar cada dimensión de impacto
            for dimension_name, analyzer_func in self.impact_dimensions.items():
                try:
                    dimension_result = await analyzer_func(person_data, business_context)
                    dimension_scores[dimension_name.value] = dimension_result["score"]
                    
                    # Recolectar recomendaciones y riesgos
                    if "recommendations" in dimension_result:
                        all_recommendations.extend(dimension_result["recommendations"])
                    
                    if "risk_factors" in dimension_result:
                        all_risk_factors.extend(dimension_result["risk_factors"])
                        
                except Exception as e:
                    logger.error(f"Error analizando {dimension_name.value}: {str(e)}")
                    dimension_scores[dimension_name.value] = 0.5
            
            # Calcular score general de impacto
            overall_score = self._calculate_overall_impact_score(dimension_scores)
            
            # Determinar nivel de impacto
            impact_level = self._determine_impact_level(overall_score)
            
            # Calcular métricas de sostenibilidad
            sustainability_metrics = await self._calculate_sustainability_metrics(
                dimension_scores, person_data
            )
            
            # Generar recomendaciones finales
            final_recommendations = self._generate_impact_recommendations(
                dimension_scores, overall_score, all_risk_factors
            )
            
            return ImpactAssessment(
                overall_impact_score=overall_score,
                impact_level=impact_level,
                dimension_scores=dimension_scores,
                sustainability_metrics=sustainability_metrics,
                recommendations=final_recommendations,
                risk_factors=list(set(all_risk_factors))  # Eliminar duplicados
            )
            
        except Exception as e:
            logger.error(f"Error en análisis de impacto: {str(e)}")
            raise
    
    async def _analyze_social_impact(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analiza impacto social"""
        try:
            social_score = 0.6  # Base score
            recommendations = []
            risk_factors = []
            
            # Analizar experiencia en proyectos sociales
            if "experience" in person_data:
                experience_data = person_data["experience"]
                if isinstance(experience_data, list):
                    social_projects = 0
                    for exp in experience_data:
                        title = exp.get("title", "").lower()
                        description = exp.get("description", "").lower()
                        
                        # Detectar proyectos sociales
                        social_keywords = [
                            "social", "community", "non-profit", "ngo", "charity",
                            "volunteer", "outreach", "development", "welfare"
                        ]
                        
                        if any(keyword in title or keyword in description for keyword in social_keywords):
                            social_projects += 1
                    
                    if social_projects > 0:
                        social_score += min(0.2, social_projects * 0.05)
                        recommendations.append("Experiencia en proyectos sociales identificada")
                    else:
                        risk_factors.append("Sin experiencia en proyectos sociales")
            
            # Analizar certificaciones sociales
            if "certifications" in person_data:
                certs = person_data["certifications"]
                if isinstance(certs, list):
                    social_certs = 0
                    for cert in certs:
                        cert_name = cert.get("name", "").lower()
                        social_cert_keywords = [
                            "social responsibility", "csr", "sustainability",
                            "community", "diversity", "inclusion"
                        ]
                        
                        if any(keyword in cert_name for keyword in social_cert_keywords):
                            social_certs += 1
                    
                    if social_certs > 0:
                        social_score += 0.1
                        recommendations.append("Certificaciones en responsabilidad social")
            
            # Analizar educación en temas sociales
            if "education" in person_data:
                education_data = person_data["education"]
                if isinstance(education_data, list):
                    for edu in education_data:
                        degree = edu.get("degree", "").lower()
                        field = edu.get("field", "").lower()
                        
                        social_education_keywords = [
                            "social work", "sociology", "anthropology", "public policy",
                            "international development", "social justice"
                        ]
                        
                        if any(keyword in degree or keyword in field for keyword in social_education_keywords):
                            social_score += 0.1
                            recommendations.append("Educación en ciencias sociales")
                            break
            
            return {
                "score": min(1.0, social_score),
                "recommendations": recommendations,
                "risk_factors": risk_factors
            }
            
        except Exception as e:
            logger.error(f"Error analizando impacto social: {str(e)}")
            return {"score": 0.5, "recommendations": [], "risk_factors": []}
    
    async def _analyze_environmental_impact(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analiza impacto ambiental"""
        try:
            environmental_score = 0.5  # Base score
            recommendations = []
            risk_factors = []
            
            # Analizar experiencia en sostenibilidad
            if "experience" in person_data:
                experience_data = person_data["experience"]
                if isinstance(experience_data, list):
                    sustainability_projects = 0
                    for exp in experience_data:
                        title = exp.get("title", "").lower()
                        description = exp.get("description", "").lower()
                        
                        # Detectar proyectos de sostenibilidad
                        sustainability_keywords = [
                            "sustainability", "environmental", "green", "renewable",
                            "energy", "climate", "carbon", "recycling", "waste"
                        ]
                        
                        if any(keyword in title or keyword in description for keyword in sustainability_keywords):
                            sustainability_projects += 1
                    
                    if sustainability_projects > 0:
                        environmental_score += min(0.3, sustainability_projects * 0.1)
                        recommendations.append("Experiencia en proyectos de sostenibilidad")
                    else:
                        risk_factors.append("Sin experiencia en sostenibilidad ambiental")
            
            # Analizar certificaciones ambientales
            if "certifications" in person_data:
                certs = person_data["certifications"]
                if isinstance(certs, list):
                    for cert in certs:
                        cert_name = cert.get("name", "").lower()
                        environmental_cert_keywords = [
                            "iso 14001", "leed", "green building", "carbon footprint",
                            "environmental management", "sustainability"
                        ]
                        
                        if any(keyword in cert_name for keyword in environmental_cert_keywords):
                            environmental_score += 0.2
                            recommendations.append("Certificaciones ambientales")
                            break
            
            # Analizar educación en temas ambientales
            if "education" in person_data:
                education_data = person_data["education"]
                if isinstance(education_data, list):
                    for edu in education_data:
                        degree = edu.get("degree", "").lower()
                        field = edu.get("field", "").lower()
                        
                        environmental_education_keywords = [
                            "environmental science", "ecology", "sustainability",
                            "renewable energy", "climate science"
                        ]
                        
                        if any(keyword in degree or keyword in field for keyword in environmental_education_keywords):
                            environmental_score += 0.15
                            recommendations.append("Educación en ciencias ambientales")
                            break
            
            return {
                "score": min(1.0, environmental_score),
                "recommendations": recommendations,
                "risk_factors": risk_factors
            }
            
        except Exception as e:
            logger.error(f"Error analizando impacto ambiental: {str(e)}")
            return {"score": 0.5, "recommendations": [], "risk_factors": []}
    
    async def _analyze_economic_impact(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analiza impacto económico"""
        try:
            economic_score = 0.6  # Base score
            recommendations = []
            risk_factors = []
            
            # Analizar experiencia en finanzas sostenibles
            if "experience" in person_data:
                experience_data = person_data["experience"]
                if isinstance(experience_data, list):
                    financial_impact_projects = 0
                    for exp in experience_data:
                        title = exp.get("title", "").lower()
                        description = exp.get("description", "").lower()
                        
                        # Detectar proyectos de impacto económico
                        economic_keywords = [
                            "financial inclusion", "microfinance", "social enterprise",
                            "impact investing", "economic development", "poverty alleviation"
                        ]
                        
                        if any(keyword in title or keyword in description for keyword in economic_keywords):
                            financial_impact_projects += 1
                    
                    if financial_impact_projects > 0:
                        economic_score += min(0.25, financial_impact_projects * 0.08)
                        recommendations.append("Experiencia en proyectos de impacto económico")
            
            # Analizar educación en economía
            if "education" in person_data:
                education_data = person_data["education"]
                if isinstance(education_data, list):
                    for edu in education_data:
                        degree = edu.get("degree", "").lower()
                        field = edu.get("field", "").lower()
                        
                        economic_education_keywords = [
                            "economics", "finance", "business administration",
                            "development economics", "social economics"
                        ]
                        
                        if any(keyword in degree or keyword in field for keyword in economic_education_keywords):
                            economic_score += 0.1
                            recommendations.append("Educación en economía o finanzas")
                            break
            
            return {
                "score": min(1.0, economic_score),
                "recommendations": recommendations,
                "risk_factors": risk_factors
            }
            
        except Exception as e:
            logger.error(f"Error analizando impacto económico: {str(e)}")
            return {"score": 0.5, "recommendations": [], "risk_factors": []}
    
    async def _analyze_governance_impact(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analiza impacto en gobernanza"""
        try:
            governance_score = 0.5  # Base score
            recommendations = []
            risk_factors = []
            
            # Analizar experiencia en gobernanza
            if "experience" in person_data:
                experience_data = person_data["experience"]
                if isinstance(experience_data, list):
                    governance_roles = 0
                    for exp in experience_data:
                        title = exp.get("title", "").lower()
                        
                        # Detectar roles de gobernanza
                        governance_keywords = [
                            "director", "board", "committee", "governance",
                            "compliance", "ethics", "policy", "regulatory"
                        ]
                        
                        if any(keyword in title for keyword in governance_keywords):
                            governance_roles += 1
                    
                    if governance_roles > 0:
                        governance_score += min(0.3, governance_roles * 0.1)
                        recommendations.append("Experiencia en roles de gobernanza")
            
            # Analizar certificaciones de compliance
            if "certifications" in person_data:
                certs = person_data["certifications"]
                if isinstance(certs, list):
                    for cert in certs:
                        cert_name = cert.get("name", "").lower()
                        governance_cert_keywords = [
                            "compliance", "governance", "ethics", "risk management",
                            "audit", "regulatory"
                        ]
                        
                        if any(keyword in cert_name for keyword in governance_cert_keywords):
                            governance_score += 0.15
                            recommendations.append("Certificaciones en gobernanza")
                            break
            
            return {
                "score": min(1.0, governance_score),
                "recommendations": recommendations,
                "risk_factors": risk_factors
            }
            
        except Exception as e:
            logger.error(f"Error analizando impacto en gobernanza: {str(e)}")
            return {"score": 0.5, "recommendations": [], "risk_factors": []}
    
    async def _analyze_innovation_impact(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analiza impacto en innovación"""
        try:
            innovation_score = 0.6  # Base score
            recommendations = []
            risk_factors = []
            
            # Analizar experiencia en innovación
            if "experience" in person_data:
                experience_data = person_data["experience"]
                if isinstance(experience_data, list):
                    innovation_projects = 0
                    for exp in experience_data:
                        title = exp.get("title", "").lower()
                        description = exp.get("description", "").lower()
                        
                        # Detectar proyectos de innovación
                        innovation_keywords = [
                            "innovation", "research", "development", "startup",
                            "technology", "digital transformation", "disruption"
                        ]
                        
                        if any(keyword in title or keyword in description for keyword in innovation_keywords):
                            innovation_projects += 1
                    
                    if innovation_projects > 0:
                        innovation_score += min(0.25, innovation_projects * 0.08)
                        recommendations.append("Experiencia en proyectos de innovación")
            
            # Analizar patentes o publicaciones
            if "patents" in person_data or "publications" in person_data:
                patents_count = len(person_data.get("patents", []))
                publications_count = len(person_data.get("publications", []))
                
                if patents_count > 0:
                    innovation_score += min(0.2, patents_count * 0.05)
                    recommendations.append(f"Patentes registradas: {patents_count}")
                
                if publications_count > 0:
                    innovation_score += min(0.15, publications_count * 0.02)
                    recommendations.append(f"Publicaciones: {publications_count}")
            
            # Analizar educación en innovación
            if "education" in person_data:
                education_data = person_data["education"]
                if isinstance(education_data, list):
                    for edu in education_data:
                        degree = edu.get("degree", "").lower()
                        field = edu.get("field", "").lower()
                        
                        innovation_education_keywords = [
                            "engineering", "computer science", "technology",
                            "research", "innovation", "entrepreneurship"
                        ]
                        
                        if any(keyword in degree or keyword in field for keyword in innovation_education_keywords):
                            innovation_score += 0.1
                            recommendations.append("Educación en campos de innovación")
                            break
            
            return {
                "score": min(1.0, innovation_score),
                "recommendations": recommendations,
                "risk_factors": risk_factors
            }
            
        except Exception as e:
            logger.error(f"Error analizando impacto en innovación: {str(e)}")
            return {"score": 0.5, "recommendations": [], "risk_factors": []}
    
    def _calculate_overall_impact_score(self, dimension_scores: Dict[str, float]) -> float:
        """Calcula score general de impacto"""
        try:
            weights = {
                "social": 0.3,
                "environmental": 0.25,
                "economic": 0.2,
                "governance": 0.15,
                "innovation": 0.1
            }
            
            weighted_sum = 0.0
            total_weight = 0.0
            
            for dimension_name, score in dimension_scores.items():
                weight = weights.get(dimension_name, 0.1)
                weighted_sum += score * weight
                total_weight += weight
            
            return weighted_sum / total_weight if total_weight > 0 else 0.5
            
        except Exception as e:
            logger.error(f"Error calculando score de impacto: {str(e)}")
            return 0.5
    
    def _determine_impact_level(self, score: float) -> ImpactLevel:
        """Determina nivel de impacto"""
        if score >= 0.8:
            return ImpactLevel.TRANSFORMATIVE
        elif score >= 0.6:
            return ImpactLevel.SIGNIFICANT
        elif score >= 0.4:
            return ImpactLevel.MODERATE
        elif score >= 0.2:
            return ImpactLevel.MINIMAL
        else:
            return ImpactLevel.NEGATIVE
    
    async def _calculate_sustainability_metrics(
        self,
        dimension_scores: Dict[str, float],
        person_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calcula métricas de sostenibilidad"""
        try:
            metrics = {
                "esg_score": np.mean(list(dimension_scores.values())),
                "social_responsibility": dimension_scores.get("social", 0.5),
                "environmental_stewardship": dimension_scores.get("environmental", 0.5),
                "economic_sustainability": dimension_scores.get("economic", 0.5),
                "governance_quality": dimension_scores.get("governance", 0.5),
                "innovation_capacity": dimension_scores.get("innovation", 0.5)
            }
            
            # Calcular métricas adicionales
            metrics["sustainability_balance"] = np.std(list(dimension_scores.values()))
            metrics["overall_sustainability"] = np.mean(list(dimension_scores.values()))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculando métricas de sostenibilidad: {str(e)}")
            return {}
    
    def _generate_impact_recommendations(
        self,
        dimension_scores: Dict[str, float],
        overall_score: float,
        risk_factors: List[str]
    ) -> List[str]:
        """Genera recomendaciones de impacto"""
        recommendations = []
        
        # Recomendaciones basadas en dimensiones bajas
        for dimension_name, score in dimension_scores.items():
            if score < 0.5:
                if dimension_name == "social":
                    recommendations.append("Desarrollar experiencia en proyectos sociales")
                elif dimension_name == "environmental":
                    recommendations.append("Obtener certificaciones en sostenibilidad")
                elif dimension_name == "economic":
                    recommendations.append("Participar en proyectos de impacto económico")
                elif dimension_name == "governance":
                    recommendations.append("Adquirir experiencia en roles de gobernanza")
                elif dimension_name == "innovation":
                    recommendations.append("Involucrarse en proyectos de innovación")
        
        # Recomendaciones generales
        if overall_score < 0.6:
            recommendations.append("Desarrollar perfil de impacto social y sostenibilidad")
        
        if len(risk_factors) > 2:
            recommendations.append("Abordar áreas de mejora identificadas")
        
        if not recommendations:
            recommendations.append("Perfil de impacto sólido, continuar desarrollo")
        
        return recommendations[:5]  # Máximo 5 recomendaciones

# Instancia global
impact_analyzer = ImpactAnalyzer()
