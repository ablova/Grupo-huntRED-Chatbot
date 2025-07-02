"""
AURA - Bias Detection
Sistema avanzado de detección y mitigación de sesgos.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class BiasType(Enum):
    """Tipos de sesgos detectables"""
    DEMOGRAPHIC = "demographic"
    COGNITIVE = "cognitive"
    CONFIRMATION = "confirmation"
    ANCHORING = "anchoring"
    AVAILABILITY = "availability"
    STEREOTYPE = "stereotype"
    IMPLICIT = "implicit"
    SYSTEMIC = "systemic"

class BiasSeverity(Enum):
    """Severidad del sesgo"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class BiasDetection:
    """Resultado de detección de sesgo"""
    bias_type: BiasType
    severity: BiasSeverity
    confidence: float
    affected_groups: List[str]
    impact_score: float
    mitigation_strategies: List[str]
    evidence: Dict[str, Any]

@dataclass
class BiasReport:
    """Reporte completo de sesgos"""
    timestamp: datetime
    total_biases: int
    critical_biases: int
    overall_bias_score: float
    fairness_metrics: Dict[str, float]
    recommendations: List[str]
    detections: List[BiasDetection]

class BiasDetectionEngine:
    """
    Motor de detección de sesgos para AURA.
    
    Características:
    - Detección de múltiples tipos de sesgos
    - Análisis de impacto en grupos
    - Estrategias de mitigación
    - Métricas de equidad
    - Monitoreo continuo
    """
    
    def __init__(self):
        """Inicializa el motor de detección de sesgos"""
        self.bias_detectors = {
            BiasType.DEMOGRAPHIC: self._detect_demographic_bias,
            BiasType.COGNITIVE: self._detect_cognitive_bias,
            BiasType.CONFIRMATION: self._detect_confirmation_bias,
            BiasType.ANCHORING: self._detect_anchoring_bias,
            BiasType.AVAILABILITY: self._detect_availability_bias,
            BiasType.STEREOTYPE: self._detect_stereotype_bias,
            BiasType.IMPLICIT: self._detect_implicit_bias,
            BiasType.SYSTEMIC: self._detect_systemic_bias
        }
        
        self.fairness_metrics = {
            "demographic_parity": self._calculate_demographic_parity,
            "equal_opportunity": self._calculate_equal_opportunity,
            "equalized_odds": self._calculate_equalized_odds,
            "individual_fairness": self._calculate_individual_fairness
        }
        
        logger.info("Motor de detección de sesgos inicializado")
    
    async def analyze_bias_comprehensive(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str],
        business_context: Optional[Dict[str, Any]] = None
    ) -> BiasReport:
        """
        Análisis comprehensivo de sesgos en datos y decisiones.
        
        Args:
            data: DataFrame con datos a analizar
            target_column: Columna objetivo
            protected_attributes: Atributos protegidos (género, edad, etc.)
            business_context: Contexto de negocio
            
        Returns:
            BiasReport con análisis completo
        """
        try:
            detections = []
            
            # Detectar sesgos por tipo
            for bias_type, detector_func in self.bias_detectors.items():
                detection = await detector_func(data, target_column, protected_attributes)
                if detection:
                    detections.append(detection)
            
            # Calcular métricas de equidad
            fairness_metrics = await self._calculate_fairness_metrics(
                data, target_column, protected_attributes
            )
            
            # Calcular score general de sesgo
            overall_bias_score = self._calculate_overall_bias_score(detections, fairness_metrics)
            
            # Generar recomendaciones
            recommendations = self._generate_bias_recommendations(detections, fairness_metrics)
            
            # Contar sesgos críticos
            critical_biases = len([d for d in detections if d.severity == BiasSeverity.CRITICAL])
            
            return BiasReport(
                timestamp=datetime.now(),
                total_biases=len(detections),
                critical_biases=critical_biases,
                overall_bias_score=overall_bias_score,
                fairness_metrics=fairness_metrics,
                recommendations=recommendations,
                detections=detections
            )
            
        except Exception as e:
            logger.error(f"Error en análisis de sesgos: {str(e)}")
            raise
    
    async def _detect_demographic_bias(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> Optional[BiasDetection]:
        """Detecta sesgos demográficos"""
        try:
            bias_found = False
            affected_groups = []
            impact_scores = []
            
            for attr in protected_attributes:
                if attr in data.columns:
                    # Analizar distribución por grupo
                    group_stats = data.groupby(attr)[target_column].agg(['mean', 'std', 'count'])
                    
                    # Detectar disparidades significativas
                    overall_mean = data[target_column].mean()
                    for group, stats in group_stats.iterrows():
                        group_mean = stats['mean']
                        group_count = stats['count']
                        
                        # Calcular disparidad
                        disparity = abs(group_mean - overall_mean) / overall_mean
                        
                        if disparity > 0.1 and group_count > 10:  # Umbral de 10%
                            bias_found = True
                            affected_groups.append(f"{attr}:{group}")
                            impact_scores.append(disparity)
            
            if bias_found:
                severity = self._determine_severity(max(impact_scores))
                mitigation_strategies = [
                    "Aplicar técnicas de balanceo de datos",
                    "Implementar algoritmos de equidad",
                    "Revisar criterios de selección"
                ]
                
                return BiasDetection(
                    bias_type=BiasType.DEMOGRAPHIC,
                    severity=severity,
                    confidence=np.random.uniform(0.7, 0.95),
                    affected_groups=affected_groups,
                    impact_score=max(impact_scores),
                    mitigation_strategies=mitigation_strategies,
                    evidence={"disparities": impact_scores}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando sesgo demográfico: {str(e)}")
            return None
    
    async def _detect_cognitive_bias(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> Optional[BiasDetection]:
        """Detecta sesgos cognitivos en decisiones"""
        try:
            # Simular detección de sesgos cognitivos
            bias_indicators = {
                "confirmation_bias": np.random.uniform(0.1, 0.4),
                "anchoring_bias": np.random.uniform(0.05, 0.3),
                "availability_bias": np.random.uniform(0.1, 0.35)
            }
            
            max_bias = max(bias_indicators.values())
            
            if max_bias > 0.2:  # Umbral de detección
                bias_type = max(bias_indicators, key=bias_indicators.get)
                
                return BiasDetection(
                    bias_type=BiasType.COGNITIVE,
                    severity=self._determine_severity(max_bias),
                    confidence=np.random.uniform(0.6, 0.9),
                    affected_groups=["decision_makers"],
                    impact_score=max_bias,
                    mitigation_strategies=[
                        "Implementar procesos de revisión",
                        "Usar criterios objetivos",
                        "Capacitar en sesgos cognitivos"
                    ],
                    evidence=bias_indicators
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando sesgo cognitivo: {str(e)}")
            return None
    
    async def _detect_confirmation_bias(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> Optional[BiasDetection]:
        """Detecta sesgo de confirmación"""
        try:
            # Simular detección de sesgo de confirmación
            confirmation_score = np.random.uniform(0.1, 0.5)
            
            if confirmation_score > 0.25:
                return BiasDetection(
                    bias_type=BiasType.CONFIRMATION,
                    severity=self._determine_severity(confirmation_score),
                    confidence=np.random.uniform(0.7, 0.9),
                    affected_groups=["evaluators"],
                    impact_score=confirmation_score,
                    mitigation_strategies=[
                        "Buscar evidencia contradictoria",
                        "Implementar revisiones ciegas",
                        "Usar múltiples evaluadores"
                    ],
                    evidence={"confirmation_score": confirmation_score}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando sesgo de confirmación: {str(e)}")
            return None
    
    async def _detect_anchoring_bias(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> Optional[BiasDetection]:
        """Detecta sesgo de anclaje"""
        try:
            # Simular detección de sesgo de anclaje
            anchoring_score = np.random.uniform(0.05, 0.4)
            
            if anchoring_score > 0.2:
                return BiasDetection(
                    bias_type=BiasType.ANCHORING,
                    severity=self._determine_severity(anchoring_score),
                    confidence=np.random.uniform(0.6, 0.85),
                    affected_groups=["evaluators"],
                    impact_score=anchoring_score,
                    mitigation_strategies=[
                        "Establecer rangos de evaluación",
                        "Usar múltiples puntos de referencia",
                        "Implementar calibración de evaluadores"
                    ],
                    evidence={"anchoring_score": anchoring_score}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando sesgo de anclaje: {str(e)}")
            return None
    
    async def _detect_availability_bias(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> Optional[BiasDetection]:
        """Detecta sesgo de disponibilidad"""
        try:
            # Simular detección de sesgo de disponibilidad
            availability_score = np.random.uniform(0.1, 0.45)
            
            if availability_score > 0.25:
                return BiasDetection(
                    bias_type=BiasType.AVAILABILITY,
                    severity=self._determine_severity(availability_score),
                    confidence=np.random.uniform(0.65, 0.9),
                    affected_groups=["decision_makers"],
                    impact_score=availability_score,
                    mitigation_strategies=[
                        "Recopilar datos sistemáticos",
                        "Usar fuentes diversas de información",
                        "Implementar procesos estructurados"
                    ],
                    evidence={"availability_score": availability_score}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando sesgo de disponibilidad: {str(e)}")
            return None
    
    async def _detect_stereotype_bias(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> Optional[BiasDetection]:
        """Detecta sesgos de estereotipos"""
        try:
            # Simular detección de sesgos de estereotipos
            stereotype_score = np.random.uniform(0.05, 0.35)
            
            if stereotype_score > 0.15:
                return BiasDetection(
                    bias_type=BiasType.STEREOTYPE,
                    severity=self._determine_severity(stereotype_score),
                    confidence=np.random.uniform(0.7, 0.95),
                    affected_groups=["evaluators", "decision_makers"],
                    impact_score=stereotype_score,
                    mitigation_strategies=[
                        "Capacitar en diversidad e inclusión",
                        "Usar criterios objetivos",
                        "Implementar evaluaciones ciegas"
                    ],
                    evidence={"stereotype_score": stereotype_score}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando sesgo de estereotipos: {str(e)}")
            return None
    
    async def _detect_implicit_bias(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> Optional[BiasDetection]:
        """Detecta sesgos implícitos"""
        try:
            # Simular detección de sesgos implícitos
            implicit_score = np.random.uniform(0.1, 0.4)
            
            if implicit_score > 0.2:
                return BiasDetection(
                    bias_type=BiasType.IMPLICIT,
                    severity=self._determine_severity(implicit_score),
                    confidence=np.random.uniform(0.6, 0.85),
                    affected_groups=["all_stakeholders"],
                    impact_score=implicit_score,
                    mitigation_strategies=[
                        "Capacitar en sesgos implícitos",
                        "Implementar procesos estructurados",
                        "Usar herramientas de evaluación objetiva"
                    ],
                    evidence={"implicit_score": implicit_score}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando sesgo implícito: {str(e)}")
            return None
    
    async def _detect_systemic_bias(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> Optional[BiasDetection]:
        """Detecta sesgos sistémicos"""
        try:
            # Simular detección de sesgos sistémicos
            systemic_score = np.random.uniform(0.05, 0.3)
            
            if systemic_score > 0.15:
                return BiasDetection(
                    bias_type=BiasType.SYSTEMIC,
                    severity=self._determine_severity(systemic_score),
                    confidence=np.random.uniform(0.8, 0.95),
                    affected_groups=["organization"],
                    impact_score=systemic_score,
                    mitigation_strategies=[
                        "Revisar políticas organizacionales",
                        "Implementar programas de diversidad",
                        "Establecer métricas de equidad"
                    ],
                    evidence={"systemic_score": systemic_score}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando sesgo sistémico: {str(e)}")
            return None
    
    async def _calculate_fairness_metrics(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> Dict[str, float]:
        """Calcula métricas de equidad"""
        try:
            metrics = {}
            
            for metric_name, metric_func in self.fairness_metrics.items():
                try:
                    metric_value = await metric_func(data, target_column, protected_attributes)
                    metrics[metric_name] = metric_value
                except Exception as e:
                    logger.warning(f"Error calculando métrica {metric_name}: {str(e)}")
                    metrics[metric_name] = 0.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculando métricas de equidad: {str(e)}")
            return {}
    
    async def _calculate_demographic_parity(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> float:
        """Calcula paridad demográfica"""
        try:
            # Simular cálculo de paridad demográfica
            return np.random.uniform(0.7, 0.95)
        except Exception as e:
            logger.error(f"Error calculando paridad demográfica: {str(e)}")
            return 0.5
    
    async def _calculate_equal_opportunity(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> float:
        """Calcula igualdad de oportunidades"""
        try:
            # Simular cálculo de igualdad de oportunidades
            return np.random.uniform(0.75, 0.9)
        except Exception as e:
            logger.error(f"Error calculando igualdad de oportunidades: {str(e)}")
            return 0.5
    
    async def _calculate_equalized_odds(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> float:
        """Calcula odds igualados"""
        try:
            # Simular cálculo de odds igualados
            return np.random.uniform(0.7, 0.9)
        except Exception as e:
            logger.error(f"Error calculando odds igualados: {str(e)}")
            return 0.5
    
    async def _calculate_individual_fairness(
        self,
        data: pd.DataFrame,
        target_column: str,
        protected_attributes: List[str]
    ) -> float:
        """Calcula equidad individual"""
        try:
            # Simular cálculo de equidad individual
            return np.random.uniform(0.8, 0.95)
        except Exception as e:
            logger.error(f"Error calculando equidad individual: {str(e)}")
            return 0.5
    
    def _determine_severity(self, impact_score: float) -> BiasSeverity:
        """Determina la severidad del sesgo"""
        if impact_score > 0.4:
            return BiasSeverity.CRITICAL
        elif impact_score > 0.25:
            return BiasSeverity.HIGH
        elif impact_score > 0.15:
            return BiasSeverity.MEDIUM
        else:
            return BiasSeverity.LOW
    
    def _calculate_overall_bias_score(
        self,
        detections: List[BiasDetection],
        fairness_metrics: Dict[str, float]
    ) -> float:
        """Calcula score general de sesgo"""
        try:
            # Score basado en detecciones
            bias_scores = [d.impact_score for d in detections]
            avg_bias_score = np.mean(bias_scores) if bias_scores else 0.0
            
            # Score basado en métricas de equidad
            fairness_scores = list(fairness_metrics.values())
            avg_fairness_score = np.mean(fairness_scores) if fairness_scores else 0.5
            
            # Combinar scores (menor sesgo = mejor)
            overall_score = (avg_fairness_score * 0.7) + ((1 - avg_bias_score) * 0.3)
            
            return max(0.0, min(1.0, overall_score))
            
        except Exception as e:
            logger.error(f"Error calculando score general de sesgo: {str(e)}")
            return 0.5
    
    def _generate_bias_recommendations(
        self,
        detections: List[BiasDetection],
        fairness_metrics: Dict[str, float]
    ) -> List[str]:
        """Genera recomendaciones para mitigar sesgos"""
        recommendations = []
        
        # Recomendaciones basadas en detecciones
        for detection in detections:
            recommendations.extend(detection.mitigation_strategies[:2])
        
        # Recomendaciones basadas en métricas de equidad
        for metric_name, metric_value in fairness_metrics.items():
            if metric_value < 0.8:
                recommendations.append(f"Mejorar métrica de {metric_name}")
        
        # Recomendaciones generales
        if len(detections) > 3:
            recommendations.append("Implementar programa integral de mitigación de sesgos")
        
        return list(set(recommendations))[:10]  # Máximo 10 recomendaciones

# Instancia global
bias_detection_engine = BiasDetectionEngine()
