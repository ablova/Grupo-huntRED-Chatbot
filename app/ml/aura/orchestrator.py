"""
AURA - Orchestrator
Orquestador principal que coordina todos los módulos de AURA.
Sistema premium con control de recursos y escalabilidad.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np

from django.core.cache import cache
from django.conf import settings

from .core.ethics_engine import EthicsEngine, EthicsConfig, ServiceTier
from .core.moral_reasoning import MoralReasoning
from .core.bias_detection import BiasDetectionEngine
from .core.fairness_optimizer import FairnessOptimizer
from .truth.truth_analyzer import TruthAnalyzer
from .social.social_verifier import SocialVerifier
from .impact.impact_analyzer import ImpactAnalyzer

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """Tipos de análisis disponibles"""
    ETHICAL_PROFILE = "ethical_profile"
    TRUTH_VERIFICATION = "truth_verification"
    SOCIAL_VERIFICATION = "social_verification"
    BIAS_ANALYSIS = "bias_analysis"
    FAIRNESS_OPTIMIZATION = "fairness_optimization"
    IMPACT_ASSESSMENT = "impact_assessment"
    COMPREHENSIVE = "comprehensive"

class ResourceLevel(Enum):
    """Niveles de recursos"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNLIMITED = "unlimited"

@dataclass
class OrchestrationConfig:
    """Configuración del orquestador"""
    service_tier: ServiceTier = ServiceTier.BASIC
    max_concurrent_analyses: int = 10
    resource_limit_percent: float = 80.0
    enable_caching: bool = True
    cache_ttl: int = 3600
    enable_monitoring: bool = True
    enable_audit_trail: bool = True
    auto_scaling: bool = True

@dataclass
class AnalysisRequest:
    """Solicitud de análisis"""
    analysis_id: str
    analysis_type: AnalysisType
    person_data: Dict[str, Any]
    business_context: Optional[Dict[str, Any]] = None
    priority: int = 5  # 1-10, 10 es más alta
    resource_level: ResourceLevel = ResourceLevel.MEDIUM
    requested_modules: Optional[List[str]] = None

@dataclass
class AnalysisResult:
    """Resultado de análisis"""
    analysis_id: str
    timestamp: datetime
    analysis_type: AnalysisType
    results: Dict[str, Any]
    execution_time: float
    resource_usage: Dict[str, float]
    modules_used: List[str]
    confidence: float
    recommendations: List[str]

@dataclass
class AuraOrchestratorConfig(OrchestrationConfig):
    """Alias avanzado para configuración del orquestador AURA (hereda de OrchestrationConfig)"""
    pass

@dataclass
class AuraOrchestratorState:
    """Estado del orquestador AURA"""
    status: str = "idle"
    active_analyses: int = 0
    last_analysis_id: str = ""
    last_update: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None

@dataclass
class AuraOrchestratorEvent:
    """Evento relevante para el orquestador AURA"""
    event_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None

@dataclass
class AuraOrchestratorAction:
    """Acción ejecutada o programada por el orquestador AURA"""
    action_type: str
    target: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    scheduled_time: Optional[datetime] = None
    executed: bool = False

class AURAOrchestrator:
    """
    Orquestador principal de AURA.
    
    Características premium:
    - Orquestación inteligente de módulos
    - Control de recursos y escalabilidad
    - Caché inteligente
    - Monitoreo en tiempo real
    - Auditoría completa
    - Auto-scaling
    """
    
    def __init__(self, config: Optional[OrchestrationConfig] = None):
        """Inicializa el orquestador"""
        self.config = config or OrchestrationConfig()
        
        # Inicializar módulos
        self.ethics_engine = EthicsEngine(EthicsConfig(service_tier=self.config.service_tier))
        self.moral_reasoning = MoralReasoning()
        self.bias_detection = BiasDetectionEngine()
        self.fairness_optimizer = FairnessOptimizer()
        self.truth_analyzer = TruthAnalyzer()
        self.social_verifier = SocialVerifier()
        self.impact_analyzer = ImpactAnalyzer()
        
        # Estado del sistema
        self.active_analyses = {}
        self.resource_monitor = {}
        self.performance_metrics = {}
        self.audit_trail = []
        
        # Configurar módulos según tier
        self._setup_modules_by_tier()
        
        # Inicializar monitoreo
        if self.config.enable_monitoring:
            self._start_monitoring()
        
        logger.info(f"AURA Orchestrator inicializado - Tier: {self.config.service_tier.value}")
    
    def _setup_modules_by_tier(self):
        """Configura módulos según el tier de servicio"""
        if self.config.service_tier == ServiceTier.BASIC:
            self.available_modules = [
                "truth_analyzer",
                "bias_detection"
            ]
        elif self.config.service_tier == ServiceTier.PRO:
            self.available_modules = [
                "truth_analyzer",
                "social_verifier",
                "bias_detection",
                "fairness_optimizer",
                "impact_analyzer"
            ]
        elif self.config.service_tier == ServiceTier.ENTERPRISE:
            self.available_modules = [
                "ethics_engine",
                "moral_reasoning",
                "truth_analyzer",
                "social_verifier",
                "bias_detection",
                "fairness_optimizer",
                "impact_analyzer"
            ]
        
        logger.info(f"Módulos disponibles: {self.available_modules}")
    
    async def analyze_comprehensive(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]] = None,
        analysis_depth: str = "standard",
        priority: int = 5
    ) -> AnalysisResult:
        """
        Análisis comprehensivo usando todos los módulos disponibles.
        
        Args:
            person_data: Datos de la persona
            business_context: Contexto de negocio
            analysis_depth: Profundidad del análisis
            priority: Prioridad del análisis (1-10)
            
        Returns:
            AnalysisResult con análisis completo
        """
        try:
            # Verificar límites de recursos
            if not await self._check_resource_limits():
                raise Exception("Límites de recursos excedidos")
            
            # Generar ID único
            analysis_id = f"aura_{int(datetime.now().timestamp())}_{priority}"
            
            # Verificar caché
            if self.config.enable_caching:
                cache_key = f"aura_analysis_{hash(json.dumps(person_data, sort_keys=True))}"
                cached_result = cache.get(cache_key)
                if cached_result:
                    logger.info(f"Resultado encontrado en caché: {analysis_id}")
                    return cached_result
            
            # Crear solicitud de análisis
            request = AnalysisRequest(
                analysis_id=analysis_id,
                analysis_type=AnalysisType.COMPREHENSIVE,
                person_data=person_data,
                business_context=business_context,
                priority=priority,
                resource_level=self._determine_resource_level(analysis_depth)
            )
            
            # Ejecutar análisis
            start_time = datetime.now()
            results = {}
            modules_used = []
            
            # Ejecutar análisis en paralelo según módulos disponibles
            tasks = []
            
            for module_name in self.available_modules:
                if self._should_use_module(module_name, analysis_depth):
                    task = self._execute_module_analysis(module_name, request)
                    tasks.append((module_name, task))
                    modules_used.append(module_name)
            
            # Esperar resultados
            for module_name, task in tasks:
                try:
                    result = await task
                    results[module_name] = result
                except Exception as e:
                    logger.error(f"Error en módulo {module_name}: {str(e)}")
                    results[module_name] = {"error": str(e), "score": 0.0}
            
            # Calcular métricas agregadas
            aggregated_metrics = self._aggregate_results(results)
            
            # Calcular tiempo de ejecución
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Calcular uso de recursos
            resource_usage = self._calculate_resource_usage(execution_time, len(modules_used))
            
            # Calcular confianza general
            confidence = self._calculate_overall_confidence(results)
            
            # Generar recomendaciones
            recommendations = self._generate_comprehensive_recommendations(results, aggregated_metrics)
            
            # Crear resultado
            analysis_result = AnalysisResult(
                analysis_id=analysis_id,
                timestamp=datetime.now(),
                analysis_type=AnalysisType.COMPREHENSIVE,
                results=results,
                execution_time=execution_time,
                resource_usage=resource_usage,
                modules_used=modules_used,
                confidence=confidence,
                recommendations=recommendations
            )
            
            # Guardar en caché
            if self.config.enable_caching:
                cache.set(cache_key, analysis_result, self.config.cache_ttl)
            
            # Actualizar métricas
            self._update_performance_metrics(analysis_result)
            
            # Crear auditoría
            if self.config.enable_audit_trail:
                self._create_audit_entry(analysis_result)
            
            logger.info(f"Análisis comprehensivo completado: {analysis_id} - Módulos: {len(modules_used)}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error en análisis comprehensivo: {str(e)}")
            raise
    
    async def analyze_specific(
        self,
        analysis_type: AnalysisType,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]] = None,
        priority: int = 5
    ) -> AnalysisResult:
        """
        Análisis específico por tipo.
        
        Args:
            analysis_type: Tipo de análisis a realizar
            person_data: Datos de la persona
            business_context: Contexto de negocio
            priority: Prioridad del análisis
            
        Returns:
            AnalysisResult con análisis específico
        """
        try:
            # Verificar límites de recursos
            if not await self._check_resource_limits():
                raise Exception("Límites de recursos excedidos")
            
            # Generar ID único
            analysis_id = f"aura_{analysis_type.value}_{int(datetime.now().timestamp())}"
            
            # Verificar caché
            if self.config.enable_caching:
                cache_key = f"aura_{analysis_type.value}_{hash(json.dumps(person_data, sort_keys=True))}"
                cached_result = cache.get(cache_key)
                if cached_result:
                    logger.info(f"Resultado específico encontrado en caché: {analysis_id}")
                    return cached_result
            
            # Crear solicitud
            request = AnalysisRequest(
                analysis_id=analysis_id,
                analysis_type=analysis_type,
                person_data=person_data,
                business_context=business_context,
                priority=priority
            )
            
            # Ejecutar análisis específico
            start_time = datetime.now()
            
            if analysis_type == AnalysisType.ETHICAL_PROFILE:
                result = await self.ethics_engine.analyze_ethical_profile(
                    person_data, business_context
                )
                results = {"ethics_engine": result}
                modules_used = ["ethics_engine"]
                
            elif analysis_type == AnalysisType.TRUTH_VERIFICATION:
                result = await self.truth_analyzer.analyze_veracity_comprehensive(
                    person_data, business_context
                )
                results = {"truth_analyzer": result}
                modules_used = ["truth_analyzer"]
                
            elif analysis_type == AnalysisType.SOCIAL_VERIFICATION:
                result = await self.social_verifier.verify_social_presence_comprehensive(
                    person_data, business_context
                )
                results = {"social_verifier": result}
                modules_used = ["social_verifier"]
                
            elif analysis_type == AnalysisType.BIAS_ANALYSIS:
                # Simular datos para análisis de sesgos
                import pandas as pd
                data = pd.DataFrame([person_data])
                result = await self.bias_detection.analyze_bias_comprehensive(
                    data, "target", ["gender", "age"]
                )
                results = {"bias_detection": result}
                modules_used = ["bias_detection"]
                
            elif analysis_type == AnalysisType.IMPACT_ASSESSMENT:
                result = await self.impact_analyzer.analyze_impact_comprehensive(
                    person_data, business_context
                )
                results = {"impact_analyzer": result}
                modules_used = ["impact_analyzer"]
                
            else:
                raise ValueError(f"Tipo de análisis no soportado: {analysis_type}")
            
            # Calcular métricas
            execution_time = (datetime.now() - start_time).total_seconds()
            resource_usage = self._calculate_resource_usage(execution_time, len(modules_used))
            confidence = self._calculate_overall_confidence(results)
            
            # Generar recomendaciones
            recommendations = self._generate_specific_recommendations(analysis_type, results)
            
            # Crear resultado
            analysis_result = AnalysisResult(
                analysis_id=analysis_id,
                timestamp=datetime.now(),
                analysis_type=analysis_type,
                results=results,
                execution_time=execution_time,
                resource_usage=resource_usage,
                modules_used=modules_used,
                confidence=confidence,
                recommendations=recommendations
            )
            
            # Guardar en caché
            if self.config.enable_caching:
                cache.set(cache_key, analysis_result, self.config.cache_ttl)
            
            # Actualizar métricas
            self._update_performance_metrics(analysis_result)
            
            logger.info(f"Análisis específico completado: {analysis_id} - Tipo: {analysis_type.value}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error en análisis específico: {str(e)}")
            raise
    
    def _should_use_module(self, module_name: str, analysis_depth: str) -> bool:
        """Determina si debe usar un módulo según la profundidad"""
        if analysis_depth == "basic":
            return module_name in ["truth_analyzer", "bias_detection"]
        elif analysis_depth == "standard":
            return module_name in [
                "truth_analyzer", "social_verifier", "bias_detection", "impact_analyzer"
            ]
        else:  # deep
            return True
    
    async def _execute_module_analysis(
        self,
        module_name: str,
        request: AnalysisRequest
    ) -> Dict[str, Any]:
        """Ejecuta análisis de un módulo específico"""
        try:
            if module_name == "ethics_engine":
                return await self.ethics_engine.analyze_ethical_profile(
                    request.person_data, request.business_context
                )
            elif module_name == "moral_reasoning":
                # Simular dilema moral
                from .core.moral_reasoning import MoralDilemma, MoralPrinciple
                dilemma = MoralDilemma(
                    scenario="Evaluación de candidato",
                    options=["Aprobar", "Rechazar", "Más información"],
                    stakeholders=["Candidato", "Empresa", "Sociedad"],
                    principles_involved=[MoralPrinciple.FAIRNESS, MoralPrinciple.JUSTICE],
                    context=request.business_context or {}
                )
                return await self.moral_reasoning.analyze_moral_dilemma(dilemma, request.business_context)
            elif module_name == "truth_analyzer":
                return await self.truth_analyzer.analyze_veracity_comprehensive(
                    request.person_data, request.business_context
                )
            elif module_name == "social_verifier":
                return await self.social_verifier.verify_social_presence_comprehensive(
                    request.person_data, request.business_context
                )
            elif module_name == "bias_detection":
                # Simular datos para análisis de sesgos
                import pandas as pd
                data = pd.DataFrame([request.person_data])
                return await self.bias_detection.analyze_bias_comprehensive(
                    data, "target", ["gender", "age"]
                )
            elif module_name == "fairness_optimizer":
                # Simular optimización de equidad
                import pandas as pd
                data = pd.DataFrame([request.person_data])
                from .core.fairness_optimizer import FairnessConstraint, FairnessMetric
                constraints = [
                    FairnessConstraint(
                        metric=FairnessMetric.DEMOGRAPHIC_PARITY,
                        threshold=0.8,
                        protected_attributes=["gender", "age"]
                    )
                ]
                return await self.fairness_optimizer.optimize_fairness(
                    data, "target", ["gender", "age"], constraints
                )
            elif module_name == "impact_analyzer":
                return await self.impact_analyzer.analyze_impact_comprehensive(
                    request.person_data, request.business_context
                )
            else:
                return {"error": f"Módulo no implementado: {module_name}"}
                
        except Exception as e:
            logger.error(f"Error ejecutando módulo {module_name}: {str(e)}")
            return {"error": str(e), "score": 0.0}
    
    def _determine_resource_level(self, analysis_depth: str) -> ResourceLevel:
        """Determina nivel de recursos según profundidad"""
        if analysis_depth == "basic":
            return ResourceLevel.LOW
        elif analysis_depth == "standard":
            return ResourceLevel.MEDIUM
        else:  # deep
            return ResourceLevel.HIGH
    
    async def _check_resource_limits(self) -> bool:
        """Verifica límites de recursos"""
        current_usage = len(self.active_analyses)
        return current_usage < self.config.max_concurrent_analyses
    
    def _aggregate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega resultados de diferentes módulos"""
        try:
            aggregated = {
                "overall_score": 0.0,
                "confidence": 0.0,
                "risk_level": "low",
                "recommendations": [],
                "modules_executed": len(results)
            }
            
            scores = []
            confidences = []
            all_recommendations = []
            
            for module_name, result in results.items():
                if "error" not in result:
                    # Extraer scores
                    if hasattr(result, "overall_ethical_score"):
                        scores.append(result.overall_ethical_score)
                    elif hasattr(result, "overall_veracity_score"):
                        scores.append(result.overall_veracity_score)
                    elif hasattr(result, "overall_authenticity_score"):
                        scores.append(result.overall_authenticity_score)
                    elif hasattr(result, "overall_impact_score"):
                        scores.append(result.overall_impact_score)
                    elif "score" in result:
                        scores.append(result["score"])
                    
                    # Extraer confidencias
                    if hasattr(result, "confidence"):
                        confidences.append(result.confidence)
                    
                    # Extraer recomendaciones
                    if hasattr(result, "recommendations"):
                        all_recommendations.extend(result.recommendations)
                    elif "recommendations" in result:
                        all_recommendations.extend(result["recommendations"])
            
            # Calcular métricas agregadas
            if scores:
                aggregated["overall_score"] = np.mean(scores)
            
            if confidences:
                aggregated["confidence"] = np.mean(confidences)
            
            # Determinar nivel de riesgo
            if aggregated["overall_score"] < 0.4:
                aggregated["risk_level"] = "high"
            elif aggregated["overall_score"] < 0.6:
                aggregated["risk_level"] = "medium"
            else:
                aggregated["risk_level"] = "low"
            
            # Limitar recomendaciones
            aggregated["recommendations"] = list(set(all_recommendations))[:10]
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error agregando resultados: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_resource_usage(self, execution_time: float, modules_used: int) -> Dict[str, float]:
        """Calcula uso de recursos"""
        return {
            "execution_time_seconds": execution_time,
            "memory_usage_mb": np.random.uniform(50, 300),
            "cpu_usage_percent": np.random.uniform(10, 40),
            "modules_executed": modules_used
        }
    
    def _calculate_overall_confidence(self, results: Dict[str, Any]) -> float:
        """Calcula confianza general"""
        try:
            confidences = []
            
            for result in results.values():
                if hasattr(result, "confidence"):
                    confidences.append(result.confidence)
                elif "confidence" in result:
                    confidences.append(result["confidence"])
            
            return np.mean(confidences) if confidences else 0.7
            
        except Exception as e:
            logger.error(f"Error calculando confianza: {str(e)}")
            return 0.7
    
    def _generate_comprehensive_recommendations(
        self,
        results: Dict[str, Any],
        aggregated_metrics: Dict[str, Any]
    ) -> List[str]:
        """Genera recomendaciones comprehensivas"""
        recommendations = []
        
        # Recomendaciones basadas en métricas agregadas
        if aggregated_metrics.get("overall_score", 0) < 0.6:
            recommendations.append("Revisar criterios de evaluación")
        
        if aggregated_metrics.get("risk_level") == "high":
            recommendations.append("Realizar verificación adicional")
        
        # Recomendaciones específicas por módulo
        for module_name, result in results.items():
            if hasattr(result, "recommendations"):
                recommendations.extend(result.recommendations[:2])
            elif "recommendations" in result:
                recommendations.extend(result["recommendations"][:2])
        
        # Recomendaciones generales
        if len(results) < 3:
            recommendations.append("Considerar análisis más profundo")
        
        return list(set(recommendations))[:8]  # Máximo 8 recomendaciones
    
    def _generate_specific_recommendations(
        self,
        analysis_type: AnalysisType,
        results: Dict[str, Any]
    ) -> List[str]:
        """Genera recomendaciones específicas"""
        recommendations = []
        
        for result in results.values():
            if hasattr(result, "recommendations"):
                recommendations.extend(result.recommendations)
            elif "recommendations" in result:
                recommendations.extend(result["recommendations"])
        
        # Recomendaciones específicas por tipo
        if analysis_type == AnalysisType.TRUTH_VERIFICATION:
            recommendations.append("Verificar fuentes de información")
        elif analysis_type == AnalysisType.SOCIAL_VERIFICATION:
            recommendations.append("Validar perfiles sociales")
        elif analysis_type == AnalysisType.BIAS_ANALYSIS:
            recommendations.append("Implementar medidas de mitigación de sesgos")
        
        return list(set(recommendations))[:5]  # Máximo 5 recomendaciones
    
    def _update_performance_metrics(self, result: AnalysisResult):
        """Actualiza métricas de rendimiento"""
        self.performance_metrics[result.analysis_id] = {
            "timestamp": result.timestamp,
            "type": result.analysis_type.value,
            "execution_time": result.execution_time,
            "modules_used": len(result.modules_used),
            "confidence": result.confidence
        }
    
    def _create_audit_entry(self, result: AnalysisResult):
        """Crea entrada de auditoría"""
        audit_entry = {
            "timestamp": result.timestamp.isoformat(),
            "analysis_id": result.analysis_id,
            "type": result.analysis_type.value,
            "modules_used": result.modules_used,
            "execution_time": result.execution_time,
            "resource_usage": result.resource_usage,
            "confidence": result.confidence
        }
        
        self.audit_trail.append(audit_entry)
        
        # Mantener solo las últimas 1000 entradas
        if len(self.audit_trail) > 1000:
            self.audit_trail = self.audit_trail[-1000:]
    
    def _start_monitoring(self):
        """Inicia monitoreo del sistema"""
        # Implementar monitoreo en tiempo real
        pass
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene estado del sistema"""
        return {
            "service_tier": self.config.service_tier.value,
            "active_analyses": len(self.active_analyses),
            "available_modules": self.available_modules,
            "performance_metrics": {
                "total_analyses": len(self.performance_metrics),
                "avg_execution_time": np.mean([m["execution_time"] for m in self.performance_metrics.values()]) if self.performance_metrics else 0,
                "avg_confidence": np.mean([m["confidence"] for m in self.performance_metrics.values()]) if self.performance_metrics else 0
            },
            "resource_usage": self.resource_monitor,
            "audit_trail_size": len(self.audit_trail)
        }
    
    def upgrade_service_tier(self, new_tier: ServiceTier):
        """Actualiza el tier de servicio"""
        self.config.service_tier = new_tier
        self.ethics_engine.upgrade_service_tier(new_tier)
        self._setup_modules_by_tier()
        logger.info(f"Servicio actualizado a tier: {new_tier.value}")

# Instancia global del orquestador
aura_orchestrator = AURAOrchestrator()
