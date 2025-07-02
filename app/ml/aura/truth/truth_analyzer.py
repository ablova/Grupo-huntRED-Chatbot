"""
AURA - TruthSense™ Truth Analyzer
Analizador principal de veracidad para TruthSense™.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import numpy as np
import re
import json

logger = logging.getLogger(__name__)

class TruthIndicator(Enum):
    """Indicadores de veracidad"""
    CONSISTENCY = "consistency"
    CREDIBILITY = "credibility"
    EVIDENCE = "evidence"
    SOURCE_RELIABILITY = "source_reliability"
    LOGICAL_COHERENCE = "logical_coherence"
    FACTUAL_ACCURACY = "factual_accuracy"

class VeracityLevel(Enum):
    """Niveles de veracidad"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIABLE = "unverifiable"

@dataclass
class TruthAnalysis:
    """Resultado de análisis de veracidad"""
    overall_veracity_score: float
    veracity_level: VeracityLevel
    confidence: float
    indicators: Dict[str, float]
    red_flags: List[str]
    recommendations: List[str]
    evidence_sources: List[str]
    consistency_score: float

class TruthAnalyzer:
    """
    Analizador principal de veracidad para TruthSense™.
    
    Características:
    - Análisis multi-dimensional de veracidad
    - Detección de inconsistencias
    - Evaluación de credibilidad
    - Verificación de fuentes
    - Análisis de coherencia lógica
    """
    
    def __init__(self):
        """Inicializa el analizador de veracidad"""
        self.truth_indicators = {
            TruthIndicator.CONSISTENCY: self._analyze_consistency,
            TruthIndicator.CREDIBILITY: self._analyze_credibility,
            TruthIndicator.EVIDENCE: self._analyze_evidence,
            TruthIndicator.SOURCE_RELIABILITY: self._analyze_source_reliability,
            TruthIndicator.LOGICAL_COHERENCE: self._analyze_logical_coherence,
            TruthIndicator.FACTUAL_ACCURACY: self._analyze_factual_accuracy
        }
        
        # Patrones de detección
        self.credibility_patterns = {
            "vague_language": r"\b(some|many|several|various|numerous)\b",
            "exaggeration": r"\b(always|never|everyone|nobody|completely|absolutely)\b",
            "uncertainty": r"\b(maybe|perhaps|possibly|might|could)\b",
            "emotional_language": r"\b(amazing|incredible|terrible|horrible|fantastic)\b"
        }
        
        logger.info("TruthSense™ Truth Analyzer inicializado")
    
    async def analyze_veracity_comprehensive(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]] = None
    ) -> TruthAnalysis:
        """
        Análisis comprehensivo de veracidad.
        
        Args:
            person_data: Datos de la persona a analizar
            business_context: Contexto de negocio
            
        Returns:
            TruthAnalysis con análisis completo
        """
        try:
            indicators = {}
            red_flags = []
            evidence_sources = []
            
            # Analizar cada indicador de veracidad
            for indicator_name, analyzer_func in self.truth_indicators.items():
                try:
                    indicator_result = await analyzer_func(person_data, business_context)
                    indicators[indicator_name.value] = indicator_result["score"]
                    
                    # Recolectar red flags
                    if "red_flags" in indicator_result:
                        red_flags.extend(indicator_result["red_flags"])
                    
                    # Recolectar fuentes de evidencia
                    if "evidence_sources" in indicator_result:
                        evidence_sources.extend(indicator_result["evidence_sources"])
                        
                except Exception as e:
                    logger.error(f"Error analizando {indicator_name.value}: {str(e)}")
                    indicators[indicator_name.value] = 0.5
            
            # Calcular score general de veracidad
            overall_score = self._calculate_overall_veracity_score(indicators)
            
            # Determinar nivel de veracidad
            veracity_level = self._determine_veracity_level(overall_score)
            
            # Calcular confianza
            confidence = self._calculate_confidence(indicators, red_flags)
            
            # Generar recomendaciones
            recommendations = self._generate_veracity_recommendations(indicators, red_flags)
            
            # Calcular score de consistencia
            consistency_score = indicators.get("consistency", 0.5)
            
            return TruthAnalysis(
                overall_veracity_score=overall_score,
                veracity_level=veracity_level,
                confidence=confidence,
                indicators=indicators,
                red_flags=list(set(red_flags)),  # Eliminar duplicados
                recommendations=recommendations,
                evidence_sources=list(set(evidence_sources)),
                consistency_score=consistency_score
            )
            
        except Exception as e:
            logger.error(f"Error en análisis de veracidad: {str(e)}")
            raise
    
    async def _analyze_consistency(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analiza consistencia de información"""
        try:
            consistency_score = 0.8  # Base score
            red_flags = []
            
            # Verificar consistencia en fechas
            if "experience" in person_data:
                experience_data = person_data["experience"]
                if isinstance(experience_data, list):
                    dates = []
                    for exp in experience_data:
                        if "start_date" in exp and "end_date" in exp:
                            dates.append((exp["start_date"], exp["end_date"]))
                    
                    # Verificar solapamientos
                    for i, (start1, end1) in enumerate(dates):
                        for j, (start2, end2) in enumerate(dates[i+1:], i+1):
                            if start1 < end2 and start2 < end1:
                                red_flags.append("Solapamiento en fechas de experiencia")
                                consistency_score -= 0.1
            
            # Verificar consistencia en educación
            if "education" in person_data:
                education_data = person_data["education"]
                if isinstance(education_data, list):
                    degrees = [edu.get("degree", "") for edu in education_data]
                    if len(set(degrees)) != len(degrees):
                        red_flags.append("Grados duplicados en educación")
                        consistency_score -= 0.05
            
            # Verificar consistencia en ubicaciones
            if "location" in person_data and "experience" in person_data:
                current_location = person_data.get("location", "")
                experience_locations = []
                
                for exp in person_data["experience"]:
                    if "location" in exp:
                        experience_locations.append(exp["location"])
                
                if current_location and experience_locations:
                    if current_location not in experience_locations:
                        # No es necesariamente un problema, pero puede ser una red flag
                        if len(experience_locations) > 3:
                            red_flags.append("Ubicación actual no aparece en experiencia previa")
                            consistency_score -= 0.05
            
            return {
                "score": max(0.0, consistency_score),
                "red_flags": red_flags,
                "evidence_sources": ["internal_consistency_check"]
            }
            
        except Exception as e:
            logger.error(f"Error analizando consistencia: {str(e)}")
            return {"score": 0.5, "red_flags": [], "evidence_sources": []}
    
    async def _analyze_credibility(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analiza credibilidad de la información"""
        try:
            credibility_score = 0.7  # Base score
            red_flags = []
            evidence_sources = []
            
            # Analizar lenguaje en descripciones
            if "summary" in person_data:
                summary = person_data["summary"]
                if isinstance(summary, str):
                    # Detectar lenguaje vago o exagerado
                    for pattern_name, pattern in self.credibility_patterns.items():
                        matches = re.findall(pattern, summary.lower())
                        if len(matches) > 3:
                            red_flags.append(f"Lenguaje {pattern_name} detectado")
                            credibility_score -= 0.05
            
            # Verificar credenciales
            if "certifications" in person_data:
                certs = person_data["certifications"]
                if isinstance(certs, list):
                    for cert in certs:
                        if "issuer" in cert and "date" in cert:
                            # Verificar si la certificación es reciente
                            try:
                                cert_date = datetime.strptime(cert["date"], "%Y-%m-%d")
                                if (datetime.now() - cert_date).days > 365 * 5:  # 5 años
                                    red_flags.append("Certificación posiblemente expirada")
                                    credibility_score -= 0.03
                            except:
                                pass
            
            # Verificar experiencia laboral
            if "experience" in person_data:
                experience_data = person_data["experience"]
                if isinstance(experience_data, list):
                    total_experience = 0
                    for exp in experience_data:
                        if "start_date" in exp and "end_date" in exp:
                            try:
                                start = datetime.strptime(exp["start_date"], "%Y-%m-%d")
                                end = datetime.strptime(exp["end_date"], "%Y-%m-%d")
                                duration = (end - start).days / 365
                                total_experience += duration
                            except:
                                pass
                    
                    # Verificar si la experiencia total es razonable
                    if total_experience > 50:  # Más de 50 años
                        red_flags.append("Experiencia total excesiva")
                        credibility_score -= 0.1
            
            evidence_sources.append("credibility_analysis")
            
            return {
                "score": max(0.0, credibility_score),
                "red_flags": red_flags,
                "evidence_sources": evidence_sources
            }
            
        except Exception as e:
            logger.error(f"Error analizando credibilidad: {str(e)}")
            return {"score": 0.5, "red_flags": [], "evidence_sources": []}
    
    async def _analyze_evidence(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analiza evidencia disponible"""
        try:
            evidence_score = 0.6  # Base score
            evidence_sources = []
            
            # Verificar fuentes de evidencia
            evidence_types = [
                "linkedin_profile",
                "resume",
                "references",
                "certifications",
                "portfolio",
                "social_media"
            ]
            
            for evidence_type in evidence_types:
                if evidence_type in person_data:
                    evidence_score += 0.05
                    evidence_sources.append(evidence_type)
            
            # Verificar referencias
            if "references" in person_data:
                refs = person_data["references"]
                if isinstance(refs, list) and len(refs) >= 2:
                    evidence_score += 0.1
                    evidence_sources.append("multiple_references")
            
            # Verificar portfolio
            if "portfolio" in person_data:
                portfolio = person_data["portfolio"]
                if isinstance(portfolio, list) and len(portfolio) > 0:
                    evidence_score += 0.1
                    evidence_sources.append("portfolio_available")
            
            return {
                "score": min(1.0, evidence_score),
                "red_flags": [],
                "evidence_sources": evidence_sources
            }
            
        except Exception as e:
            logger.error(f"Error analizando evidencia: {str(e)}")
            return {"score": 0.5, "red_flags": [], "evidence_sources": []}
    
    async def _analyze_source_reliability(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analiza confiabilidad de fuentes"""
        try:
            reliability_score = 0.7  # Base score
            evidence_sources = []
            
            # Evaluar fuentes según confiabilidad
            source_reliability = {
                "linkedin": 0.8,
                "resume": 0.7,
                "references": 0.9,
                "certifications": 0.8,
                "portfolio": 0.6,
                "social_media": 0.4
            }
            
            for source, reliability in source_reliability.items():
                if source in person_data:
                    reliability_score = (reliability_score + reliability) / 2
                    evidence_sources.append(f"verified_{source}")
            
            # Verificar si hay múltiples fuentes
            source_count = len([s for s in source_reliability.keys() if s in person_data])
            if source_count >= 3:
                reliability_score += 0.1
                evidence_sources.append("multiple_sources")
            
            return {
                "score": min(1.0, reliability_score),
                "red_flags": [],
                "evidence_sources": evidence_sources
            }
            
        except Exception as e:
            logger.error(f"Error analizando confiabilidad de fuentes: {str(e)}")
            return {"score": 0.5, "red_flags": [], "evidence_sources": []}
    
    async def _analyze_logical_coherence(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analiza coherencia lógica"""
        try:
            coherence_score = 0.8  # Base score
            red_flags = []
            
            # Verificar coherencia entre educación y experiencia
            if "education" in person_data and "experience" in person_data:
                education_data = person_data["education"]
                experience_data = person_data["experience"]
                
                if isinstance(education_data, list) and isinstance(experience_data, list):
                    # Verificar si la experiencia es coherente con la educación
                    education_levels = [edu.get("level", "").lower() for edu in education_data]
                    experience_titles = [exp.get("title", "").lower() for exp in experience_data]
                    
                    # Detectar inconsistencias obvias
                    if "phd" in education_levels and "intern" in experience_titles:
                        red_flags.append("PhD con experiencia de intern")
                        coherence_score -= 0.1
            
            # Verificar progresión de carrera
            if "experience" in person_data:
                experience_data = person_data["experience"]
                if isinstance(experience_data, list) and len(experience_data) > 1:
                    # Verificar si hay progresión lógica
                    titles = [exp.get("title", "").lower() for exp in experience_data]
                    
                    # Detectar regresiones obvias
                    senior_keywords = ["senior", "lead", "manager", "director", "vp", "ceo"]
                    junior_keywords = ["junior", "intern", "assistant", "entry"]
                    
                    senior_positions = [i for i, title in enumerate(titles) if any(keyword in title for keyword in senior_keywords)]
                    junior_positions = [i for i, title in enumerate(titles) if any(keyword in title for keyword in junior_keywords)]
                    
                    if senior_positions and junior_positions:
                        if max(senior_positions) < max(junior_positions):
                            red_flags.append("Regresión en progresión de carrera")
                            coherence_score -= 0.1
            
            return {
                "score": max(0.0, coherence_score),
                "red_flags": red_flags,
                "evidence_sources": ["logical_analysis"]
            }
            
        except Exception as e:
            logger.error(f"Error analizando coherencia lógica: {str(e)}")
            return {"score": 0.5, "red_flags": [], "evidence_sources": []}
    
    async def _analyze_factual_accuracy(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analiza precisión factual"""
        try:
            accuracy_score = 0.7  # Base score
            red_flags = []
            evidence_sources = []
            
            # Verificar fechas
            if "experience" in person_data:
                experience_data = person_data["experience"]
                if isinstance(experience_data, list):
                    for exp in experience_data:
                        if "start_date" in exp and "end_date" in exp:
                            try:
                                start = datetime.strptime(exp["start_date"], "%Y-%m-%d")
                                end = datetime.strptime(exp["end_date"], "%Y-%m-%d")
                                
                                if start > end:
                                    red_flags.append("Fecha de inicio posterior a fecha de fin")
                                    accuracy_score -= 0.1
                                
                                if start > datetime.now():
                                    red_flags.append("Fecha de inicio en el futuro")
                                    accuracy_score -= 0.1
                                    
                            except:
                                red_flags.append("Formato de fecha inválido")
                                accuracy_score -= 0.05
            
            # Verificar información de contacto
            if "email" in person_data:
                email = person_data["email"]
                if isinstance(email, str):
                    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    if not re.match(email_pattern, email):
                        red_flags.append("Formato de email inválido")
                        accuracy_score -= 0.05
            
            evidence_sources.append("factual_verification")
            
            return {
                "score": max(0.0, accuracy_score),
                "red_flags": red_flags,
                "evidence_sources": evidence_sources
            }
            
        except Exception as e:
            logger.error(f"Error analizando precisión factual: {str(e)}")
            return {"score": 0.5, "red_flags": [], "evidence_sources": []}
    
    def _calculate_overall_veracity_score(self, indicators: Dict[str, float]) -> float:
        """Calcula score general de veracidad"""
        try:
            weights = {
                "consistency": 0.25,
                "credibility": 0.20,
                "evidence": 0.15,
                "source_reliability": 0.15,
                "logical_coherence": 0.15,
                "factual_accuracy": 0.10
            }
            
            weighted_sum = 0.0
            total_weight = 0.0
            
            for indicator_name, score in indicators.items():
                weight = weights.get(indicator_name, 0.1)
                weighted_sum += score * weight
                total_weight += weight
            
            return weighted_sum / total_weight if total_weight > 0 else 0.5
            
        except Exception as e:
            logger.error(f"Error calculando score de veracidad: {str(e)}")
            return 0.5
    
    def _determine_veracity_level(self, score: float) -> VeracityLevel:
        """Determina nivel de veracidad"""
        if score >= 0.8:
            return VeracityLevel.HIGH
        elif score >= 0.6:
            return VeracityLevel.MEDIUM
        elif score >= 0.4:
            return VeracityLevel.LOW
        else:
            return VeracityLevel.UNVERIFIABLE
    
    def _calculate_confidence(self, indicators: Dict[str, float], red_flags: List[str]) -> float:
        """Calcula nivel de confianza"""
        try:
            # Basado en consistencia de indicadores
            scores = list(indicators.values())
            score_variance = np.var(scores) if len(scores) > 1 else 0.0
            
            # Confianza base
            base_confidence = 0.8
            
            # Reducir confianza por varianza alta
            variance_penalty = min(0.2, score_variance)
            
            # Reducir confianza por red flags
            flag_penalty = min(0.1, len(red_flags) * 0.02)
            
            confidence = base_confidence - variance_penalty - flag_penalty
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculando confianza: {str(e)}")
            return 0.5
    
    def _generate_veracity_recommendations(
        self,
        indicators: Dict[str, float],
        red_flags: List[str]
    ) -> List[str]:
        """Genera recomendaciones de veracidad"""
        recommendations = []
        
        # Recomendaciones basadas en indicadores bajos
        for indicator_name, score in indicators.items():
            if score < 0.6:
                if indicator_name == "consistency":
                    recommendations.append("Verificar consistencia de fechas y ubicaciones")
                elif indicator_name == "credibility":
                    recommendations.append("Validar credenciales y certificaciones")
                elif indicator_name == "evidence":
                    recommendations.append("Solicitar evidencia adicional")
                elif indicator_name == "source_reliability":
                    recommendations.append("Verificar fuentes de información")
                elif indicator_name == "logical_coherence":
                    recommendations.append("Revisar progresión de carrera")
                elif indicator_name == "factual_accuracy":
                    recommendations.append("Verificar precisión de datos")
        
        # Recomendaciones basadas en red flags
        if len(red_flags) > 3:
            recommendations.append("Realizar verificación exhaustiva")
        
        if not recommendations:
            recommendations.append("Veracidad aceptable, continuar con proceso normal")
        
        return recommendations[:5]  # Máximo 5 recomendaciones

# Instancia global
truth_analyzer = TruthAnalyzer()
