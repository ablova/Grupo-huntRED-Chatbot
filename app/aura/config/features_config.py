"""
AURA - Features Configuration
Configuración central para habilitar/deshabilitar funcionalidades por fases
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Phase(Enum):
    """Fases de implementación de AURA"""
    PHASE_1 = "phase_1"  # IA Avanzada
    PHASE_2 = "phase_2"  # Integración Multiplataforma
    PHASE_3 = "phase_3"  # Experiencia Futurista
    PHASE_4 = "phase_4"  # Escalabilidad Global


@dataclass
class FeatureConfig:
    """Configuración de una funcionalidad"""
    name: str
    description: str
    phase: Phase
    enabled: bool = False
    dependencies: List[str] = None
    config: Dict[str, Any] = None


class AuraFeaturesConfig:
    """
    Configuración central de funcionalidades de AURA
    """
    
    def __init__(self):
        self.features = {}
        self.current_phase = Phase.PHASE_1
        self._initialize_features()
        self._load_environment_config()
    
    def _initialize_features(self):
        """Inicializa todas las funcionalidades disponibles"""
        
        # FASE 1: INTELIGENCIA AVANZADA
        self.features.update({
            "career_predictor": FeatureConfig(
                name="Career Movement Predictor",
                description="Sistema de IA para predecir movimientos profesionales",
                phase=Phase.PHASE_1,
                enabled=False,
                dependencies=[],
                config={
                    "prediction_horizon_months": 12,
                    "confidence_threshold": 0.7,
                    "update_frequency_hours": 24
                }
            ),
            
            "market_predictor": FeatureConfig(
                name="Market Labor Predictor",
                description="Predicción de tendencias del mercado laboral",
                phase=Phase.PHASE_1,
                enabled=False,
                dependencies=[],
                config={
                    "forecast_periods": [3, 6, 12, 24],  # meses
                    "industries": ["tech", "finance", "healthcare", "education"],
                    "update_frequency_days": 7
                }
            ),
            
            "sentiment_analyzer": FeatureConfig(
                name="Sentiment Analyzer",
                description="Análisis de sentimientos para satisfacción laboral",
                phase=Phase.PHASE_1,
                enabled=False,
                dependencies=[],
                config={
                    "analysis_categories": ["job_satisfaction", "work_environment", "compensation"],
                    "confidence_threshold": 0.8,
                    "batch_size": 100
                }
            ),
            
            "executive_analytics": FeatureConfig(
                name="Executive Analytics",
                description="Dashboard ejecutivo con KPIs y insights",
                phase=Phase.PHASE_1,
                enabled=False,
                dependencies=[],
                config={
                    "kpi_refresh_minutes": 15,
                    "alert_thresholds": {
                        "network_growth": 0.1,
                        "engagement_rate": 0.05,
                        "churn_risk": 0.7
                    }
                }
            )
        })
        
        # FASE 2: INTEGRACIÓN MULTIPLATAFORMA
        self.features.update({
            "multi_platform_connector": FeatureConfig(
                name="Multi-Platform Connector",
                description="Conectores para múltiples plataformas profesionales",
                phase=Phase.PHASE_2,
                enabled=False,
                dependencies=["career_predictor"],
                config={
                    "platforms": ["linkedin", "github", "twitter", "stack_overflow"],
                    "sync_frequency_hours": 6,
                    "rate_limits": {
                        "linkedin": 100,
                        "github": 5000,
                        "twitter": 300
                    }
                }
            ),
            
            "real_time_sync": FeatureConfig(
                name="Real-Time Synchronization",
                description="Sincronización en tiempo real de datos",
                phase=Phase.PHASE_2,
                enabled=False,
                dependencies=["multi_platform_connector"],
                config={
                    "sync_interval_seconds": 300,
                    "batch_size": 50,
                    "retry_attempts": 3
                }
            ),
            
            "mobile_app": FeatureConfig(
                name="Mobile Application",
                description="Aplicación móvil nativa",
                phase=Phase.PHASE_2,
                enabled=False,
                dependencies=[],
                config={
                    "platforms": ["ios", "android"],
                    "features": ["notifications", "offline_mode", "biometrics"],
                    "update_frequency_days": 7
                }
            )
        })
        
        # FASE 3: EXPERIENCIA FUTURISTA
        self.features.update({
            "ar_network_viewer": FeatureConfig(
                name="AR Network Viewer",
                description="Visualización de redes en realidad aumentada",
                phase=Phase.PHASE_3,
                enabled=False,
                dependencies=[],
                config={
                    "supported_devices": ["hololens", "magic_leap", "mobile_ar"],
                    "max_nodes": 1000,
                    "interaction_distance": 2.0,
                    "animation_speed": 1.0
                }
            ),
            
            "strategic_gamification": FeatureConfig(
                name="Strategic Gamification",
                description="Sistema de competencias profesionales",
                phase=Phase.PHASE_3,
                enabled=False,
                dependencies=[],
                config={
                    "competition_types": ["networking", "skills", "influence"],
                    "max_concurrent_competitions": 5,
                    "reward_multipliers": {
                        "early_bird": 1.2,
                        "streak": 1.1,
                        "team_collaboration": 1.3
                    }
                }
            ),
            
            "3d_visualization": FeatureConfig(
                name="3D Network Visualization",
                description="Visualización 3D de redes profesionales",
                phase=Phase.PHASE_3,
                enabled=False,
                dependencies=[],
                config={
                    "render_engine": "threejs",
                    "max_nodes": 500,
                    "layouts": ["force", "spherical", "hierarchical"],
                    "export_formats": ["png", "json", "gltf"]
                }
            ),
            
            "ai_conversational": FeatureConfig(
                name="AI Conversational Assistant",
                description="Asistente conversacional con IA (core para todos los productos)",
                phase=Phase.PHASE_3,
                enabled=True,  # Habilitado por defecto para todos
                dependencies=["sentiment_analyzer"],
                config={
                    "model": "gpt-4",
                    "context_window": 4000,
                    "response_timeout": 30,
                    "languages": ["en", "es", "fr", "de"]
                }
            )
        })
        
        # FASE 4: ESCALABILIDAD GLOBAL
        self.features.update({
            "multi_language_system": FeatureConfig(
                name="Multi-Language System",
                description="Sistema de multi-idioma y localización",
                phase=Phase.PHASE_4,
                enabled=False,
                dependencies=[],
                config={
                    "supported_languages": ["en", "es", "fr", "de", "pt", "it", "zh", "ja", "ko", "ar"],
                    "auto_translation": True,
                    "cultural_adaptation": True,
                    "regional_formats": True
                }
            ),
            
            "compliance_manager": FeatureConfig(
                name="Compliance Manager",
                description="Gestión de compliance internacional",
                phase=Phase.PHASE_4,
                enabled=False,
                dependencies=[],
                config={
                    "regulations": ["gdpr", "ccpa", "lgpd", "pipeda"],
                    "consent_management": True,
                    "data_portability": True,
                    "audit_logging": True
                }
            ),
            
            "global_scalability": FeatureConfig(
                name="Global Scalability",
                description="Escalabilidad global y distribución",
                phase=Phase.PHASE_4,
                enabled=False,
                dependencies=["multi_language_system", "compliance_manager"],
                config={
                    "regions": ["na", "sa", "eu", "ap", "me", "af", "oc"],
                    "cdn_enabled": True,
                    "load_balancing": True,
                    "auto_scaling": True
                }
            ),
            
            "marketplace_platform": FeatureConfig(
                name="Marketplace Platform",
                description="Plataforma de marketplace de talento",
                phase=Phase.PHASE_4,
                enabled=False,
                dependencies=["global_scalability"],
                config={
                    "transaction_types": ["hiring", "consulting", "mentoring"],
                    "payment_methods": ["credit_card", "paypal", "crypto"],
                    "escrow_enabled": True,
                    "dispute_resolution": True
                }
            )
        })
    
    def _load_environment_config(self):
        """Carga configuración desde variables de entorno"""
        # Cargar fase actual
        phase_env = os.getenv("AURA_CURRENT_PHASE", "phase_1")
        try:
            self.current_phase = Phase(phase_env)
        except ValueError:
            logger.warning(f"Invalid phase {phase_env}, using PHASE_1")
            self.current_phase = Phase.PHASE_1
        
        # Cargar configuraciones específicas de funcionalidades
        for feature_name in self.features.keys():
            env_var = f"AURA_{feature_name.upper()}_ENABLED"
            if env_var in os.environ:
                self.features[feature_name].enabled = os.getenv(env_var, "false").lower() == "true"
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Verifica si una funcionalidad está habilitada
        """
        feature = self.features.get(feature_name)
        if not feature:
            return False
        
        # Verificar si la fase actual permite esta funcionalidad
        if feature.phase.value > self.current_phase.value:
            return False
        
        # Verificar dependencias
        if feature.dependencies:
            for dependency in feature.dependencies:
                if not self.is_feature_enabled(dependency):
                    logger.warning(f"Feature {feature_name} disabled: dependency {dependency} not enabled")
                    return False
        
        return feature.enabled
    
    def enable_feature(self, feature_name: str) -> bool:
        """
        Habilita una funcionalidad
        """
        if feature_name not in self.features:
            logger.error(f"Feature {feature_name} not found")
            return False
        
        feature = self.features[feature_name]
        
        # Verificar fase
        if feature.phase.value > self.current_phase.value:
            logger.error(f"Cannot enable {feature_name}: current phase {self.current_phase.value} < required phase {feature.phase.value}")
            return False
        
        # Verificar dependencias
        if feature.dependencies:
            for dependency in feature.dependencies:
                if not self.is_feature_enabled(dependency):
                    logger.error(f"Cannot enable {feature_name}: dependency {dependency} not enabled")
                    return False
        
        feature.enabled = True
        logger.info(f"Feature {feature_name} enabled")
        return True
    
    def disable_feature(self, feature_name: str) -> bool:
        """
        Deshabilita una funcionalidad
        """
        if feature_name not in self.features:
            logger.error(f"Feature {feature_name} not found")
            return False
        
        # Verificar dependencias inversas
        dependent_features = [
            name for name, feature in self.features.items()
            if feature.dependencies and feature_name in feature.dependencies
        ]
        
        if dependent_features:
            logger.warning(f"Disabling {feature_name} will also disable: {dependent_features}")
            for dep_feature in dependent_features:
                self.features[dep_feature].enabled = False
        
        self.features[feature_name].enabled = False
        logger.info(f"Feature {feature_name} disabled")
        return True
    
    def get_enabled_features(self) -> List[str]:
        """
        Obtiene lista de funcionalidades habilitadas
        """
        return [
            name for name, feature in self.features.items()
            if self.is_feature_enabled(name)
        ]
    
    def get_features_by_phase(self, phase: Phase) -> List[Dict[str, Any]]:
        """
        Obtiene funcionalidades por fase
        """
        phase_features = []
        for name, feature in self.features.items():
            if feature.phase == phase:
                phase_features.append({
                    "name": name,
                    "display_name": feature.name,
                    "description": feature.description,
                    "enabled": self.is_feature_enabled(name),
                    "dependencies": feature.dependencies,
                    "config": feature.config
                })
        
        return phase_features
    
    def get_feature_config(self, feature_name: str) -> Dict[str, Any]:
        """
        Obtiene configuración de una funcionalidad
        """
        feature = self.features.get(feature_name)
        if not feature:
            return {}
        
        return {
            "name": feature.name,
            "description": feature.description,
            "phase": feature.phase.value,
            "enabled": self.is_feature_enabled(feature_name),
            "dependencies": feature.dependencies,
            "config": feature.config
        }
    
    def update_feature_config(self, feature_name: str, config: Dict[str, Any]) -> bool:
        """
        Actualiza configuración de una funcionalidad
        """
        feature = self.features.get(feature_name)
        if not feature:
            return False
        
        feature.config.update(config)
        logger.info(f"Feature {feature_name} config updated")
        return True
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Obtiene estado general del sistema
        """
        enabled_features = self.get_enabled_features()
        total_features = len(self.features)
        
        phase_stats = {}
        for phase in Phase:
            phase_features = self.get_features_by_phase(phase)
            enabled_count = sum(1 for f in phase_features if f["enabled"])
            phase_stats[phase.value] = {
                "total": len(phase_features),
                "enabled": enabled_count,
                "percentage": (enabled_count / len(phase_features) * 100) if phase_features else 0
            }
        
        return {
            "current_phase": self.current_phase.value,
            "total_features": total_features,
            "enabled_features": len(enabled_features),
            "enabled_percentage": (len(enabled_features) / total_features * 100),
            "phase_statistics": phase_stats,
            "enabled_feature_list": enabled_features
        }
    
    def export_config(self) -> Dict[str, Any]:
        """
        Exporta configuración completa
        """
        return {
            "current_phase": self.current_phase.value,
            "features": {
                name: {
                    "name": feature.name,
                    "description": feature.description,
                    "phase": feature.phase.value,
                    "enabled": feature.enabled,
                    "dependencies": feature.dependencies,
                    "config": feature.config
                }
                for name, feature in self.features.items()
            }
        }
    
    def import_config(self, config: Dict[str, Any]) -> bool:
        """
        Importa configuración
        """
        try:
            # Actualizar fase actual
            if "current_phase" in config:
                self.current_phase = Phase(config["current_phase"])
            
            # Actualizar funcionalidades
            if "features" in config:
                for name, feature_config in config["features"].items():
                    if name in self.features:
                        feature = self.features[name]
                        feature.enabled = feature_config.get("enabled", False)
                        if "config" in feature_config:
                            feature.config.update(feature_config["config"])
            
            logger.info("Configuration imported successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False


# Instancia global de configuración
aura_config = AuraFeaturesConfig()

# Funciones de conveniencia para verificar funcionalidades
def is_career_predictor_enabled():
    """Verifica si el predictor de carrera está habilitado"""
    return aura_config.is_feature_enabled("career_predictor")

def is_market_predictor_enabled():
    """Verifica si el predictor de mercado está habilitado"""
    return aura_config.is_feature_enabled("market_predictor")

def is_sentiment_analyzer_enabled():
    """Verifica si el analizador de sentimientos está habilitado"""
    return aura_config.is_feature_enabled("sentiment_analyzer")

def is_3d_visualization_enabled():
    """Verifica si la visualización 3D está habilitada"""
    return aura_config.is_feature_enabled("3d_visualization")

def is_ar_viewer_enabled():
    """Verifica si el visualizador AR está habilitado"""
    return aura_config.is_feature_enabled("ar_network_viewer")

def is_gamification_enabled():
    """Verifica si la gamificación está habilitada"""
    return aura_config.is_feature_enabled("strategic_gamification")

def is_multi_language_enabled():
    """Verifica si el sistema multi-idioma está habilitado"""
    return aura_config.is_feature_enabled("multi_language_system")

def is_compliance_enabled():
    """Verifica si el gestor de compliance está habilitado"""
    return aura_config.is_feature_enabled("compliance_manager") 