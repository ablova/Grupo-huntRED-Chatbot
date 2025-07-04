"""
⚙️ Configuración Unificada del Sistema ML - huntRED®

Sistema unificado de configuración que reemplaza ml_config.py y revolutionary_config.py
con validación robusta, jerarquía clara y gestión por entornos.
"""

import os
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class Environment(str, Enum):
    """Entornos de ejecución válidos"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class ModelType(str, Enum):
    """Tipos de modelos ML válidos"""
    SENTIMENT_ANALYZER = "sentiment_analyzer"
    RETENTION_PREDICTOR = "retention_predictor"
    SATISFACTION_PREDICTOR = "satisfaction_predictor"
    MATCHMAKING = "matchmaking"
    PERSONALITY_ANALYZER = "personality_analyzer"
    CULTURAL_ANALYZER = "cultural_analyzer"
    PROFESSIONAL_ANALYZER = "professional_analyzer"


@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    host: str = "localhost"
    port: int = 5432
    name: str = "huntred_ml"
    user: str = "huntred_user"
    password: str = ""
    pool_size: int = 10
    pool_max_overflow: int = 20
    pool_timeout: int = 30


@dataclass
class CacheConfig:
    """Configuración de cache unificada"""
    enabled: bool = True
    backend: str = "redis"  # redis, memcached, memory
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    
    # TTL por tipo de operación (en segundos)
    ttl_sentiment: int = 3600  # 1 hora
    ttl_analysis: int = 7200   # 2 horas
    ttl_models: int = 86400    # 24 horas
    ttl_config: int = 1800     # 30 minutos
    
    # Configuración avanzada
    max_memory: str = "512mb"
    eviction_policy: str = "allkeys-lru"
    compression: bool = True


@dataclass
class ModelConfig:
    """Configuración para un modelo específico"""
    type: ModelType
    version: str = "1.0.0"
    enabled: bool = True
    
    # Rutas
    model_path: Optional[str] = None
    data_path: Optional[str] = None
    
    # Parámetros de entrenamiento
    training_params: Dict[str, Any] = field(default_factory=dict)
    
    # Umbrales
    confidence_threshold: float = 0.7
    performance_threshold: float = 0.8
    
    # Límites de recursos
    max_memory_mb: int = 1024
    max_execution_time_seconds: int = 30
    
    # Cache específico
    cache_enabled: bool = True
    cache_ttl: int = 3600


@dataclass
class BusinessUnitConfig:
    """Configuración específica por unidad de negocio"""
    name: str
    weight: float = 1.0
    priority: int = 1
    
    # Umbrales específicos
    matching_threshold: float = 0.7
    satisfaction_threshold: float = 0.6
    retention_threshold: float = 0.8
    
    # Características habilitadas
    features_enabled: Dict[str, bool] = field(default_factory=lambda: {
        "personality_analysis": True,
        "cultural_analysis": True,
        "professional_analysis": True,
        "sentiment_analysis": True,
        "predictive_analysis": True
    })
    
    # Pesos para matching
    matching_weights: Dict[str, float] = field(default_factory=lambda: {
        "hard_skills": 0.30,
        "soft_skills": 0.15,
        "cultural_fit": 0.25,
        "experience": 0.20,
        "location": 0.10
    })


@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    encryption_enabled: bool = True
    encryption_key: Optional[str] = None
    
    # API Security
    api_key_required: bool = True
    rate_limiting_enabled: bool = True
    max_requests_per_minute: int = 100
    max_requests_per_hour: int = 1000
    
    # Data Privacy
    gdpr_compliance: bool = True
    data_anonymization: bool = True
    audit_logging: bool = True
    
    # Input Validation
    input_sanitization: bool = True
    max_input_size_mb: int = 10
    allowed_file_types: List[str] = field(default_factory=lambda: ['.csv', '.json', '.txt'])


@dataclass
class PerformanceConfig:
    """Configuración de rendimiento"""
    # Procesamiento
    max_workers: int = field(default_factory=lambda: os.cpu_count() or 4)
    batch_size: int = 1000
    async_enabled: bool = True
    
    # Timeouts
    default_timeout: int = 30
    model_timeout: int = 60
    database_timeout: int = 10
    
    # Memory Management
    max_memory_per_process_mb: int = 2048
    garbage_collection_enabled: bool = True
    memory_monitoring: bool = True
    
    # GPU (si disponible)
    gpu_enabled: bool = False
    gpu_memory_limit_mb: Optional[int] = None


@dataclass
class MonitoringConfig:
    """Configuración de monitoreo"""
    enabled: bool = True
    
    # Métricas
    collect_performance_metrics: bool = True
    collect_business_metrics: bool = True
    collect_error_metrics: bool = True
    
    # Alerting
    alerts_enabled: bool = True
    alert_channels: List[str] = field(default_factory=lambda: ["email", "slack"])
    
    # Thresholds para alertas
    error_rate_threshold: float = 0.05  # 5%
    response_time_threshold_ms: int = 5000  # 5 segundos
    memory_usage_threshold: float = 0.8  # 80%
    
    # Logging
    log_level: str = "INFO"
    structured_logging: bool = True
    log_retention_days: int = 30


@dataclass
class UniversityConfig:
    """Configuración de universidades (mejorada y actualizable)"""
    auto_update_enabled: bool = True
    update_frequency_days: int = 30
    external_ranking_api: Optional[str] = None
    
    # Cache de rankings
    rankings_cache_ttl: int = 86400 * 7  # 1 semana
    
    # Configuración por defecto para universidades
    default_scores: Dict[str, float] = field(default_factory=lambda: {
        "public_top_10": 0.9,
        "private_top_10": 0.95,
        "public_top_50": 0.7,
        "private_top_50": 0.8,
        "other": 0.6
    })


class UnifiedMLConfig:
    """
    🚀 Configuración Unificada del Sistema ML huntRED®
    
    Sistema centralizado que maneja toda la configuración del sistema ML
    con validación, jerarquía de entornos y capacidades de actualización en caliente.
    """
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # Configuraciones por componente
        self.database = DatabaseConfig()
        self.cache = CacheConfig()
        self.security = SecurityConfig()
        self.performance = PerformanceConfig()
        self.monitoring = MonitoringConfig()
        self.university = UniversityConfig()
        
        # Configuraciones de modelos
        self.models: Dict[str, ModelConfig] = {}
        
        # Configuraciones de unidades de negocio
        self.business_units: Dict[str, BusinessUnitConfig] = {}
        
        # Cargar configuración del entorno
        self._load_environment_config()
        self._setup_default_models()
        self._setup_default_business_units()
        
        # Validar configuración
        self._validate_config()
    
    def _load_environment_config(self):
        """Carga configuración específica del entorno"""
        config_file = self.config_dir / f"{self.environment.value}.json"
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                env_config = json.load(f)
                if env_config:
                    self._apply_environment_overrides(env_config)
    
    def _apply_environment_overrides(self, env_config: Dict[str, Any]):
        """Aplica configuraciones específicas del entorno"""
        if self.environment == Environment.PRODUCTION:
            # Configuración de producción
            self.cache.ttl_sentiment = 7200  # Cache más largo
            self.security.rate_limiting_enabled = True
            self.monitoring.alerts_enabled = True
            self.performance.max_workers = (os.cpu_count() or 4) * 2
            
        elif self.environment == Environment.DEVELOPMENT:
            # Configuración de desarrollo
            self.cache.ttl_sentiment = 300  # Cache más corto para testing
            self.security.rate_limiting_enabled = False
            self.monitoring.log_level = "DEBUG"
            
        elif self.environment == Environment.TESTING:
            # Configuración para tests
            self.cache.enabled = False  # No cache en tests
            self.database.pool_size = 1
            self.performance.async_enabled = False
    
    def _setup_default_models(self):
        """Configura modelos por defecto"""
        default_models = [
            ModelType.SENTIMENT_ANALYZER,
            ModelType.RETENTION_PREDICTOR,
            ModelType.SATISFACTION_PREDICTOR,
            ModelType.MATCHMAKING,
            ModelType.PERSONALITY_ANALYZER
        ]
        
        for model_type in default_models:
            self.models[model_type.value] = ModelConfig(
                type=model_type,
                model_path=f"models/{model_type.value}.joblib",
                data_path=f"data/{model_type.value}/",
                training_params=self._get_default_training_params(model_type)
            )
    
    def _setup_default_business_units(self):
        """Configura unidades de negocio por defecto"""
        business_units_config = {
            "huntred": BusinessUnitConfig(
                name="huntRED®",
                weight=1.5,
                priority=1,
                matching_threshold=0.8
            ),
            "huntu": BusinessUnitConfig(
                name="huntU",
                weight=1.2,
                priority=2,
                matching_threshold=0.7
            ),
            "amigro": BusinessUnitConfig(
                name="Amigro",
                weight=1.0,
                priority=3,
                matching_threshold=0.6
            ),
            "huntred_executive": BusinessUnitConfig(
                name="huntRED® Executive",
                weight=2.0,
                priority=1,
                matching_threshold=0.9
            )
        }
        
        self.business_units = business_units_config
    
    def _get_default_training_params(self, model_type: ModelType) -> Dict[str, Any]:
        """Obtiene parámetros de entrenamiento por defecto para cada tipo de modelo"""
        params_map = {
            ModelType.SENTIMENT_ANALYZER: {
                "algorithm": "gradient_boosting",
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 6
            },
            ModelType.RETENTION_PREDICTOR: {
                "algorithm": "random_forest",
                "n_estimators": 200,
                "max_depth": 10,
                "min_samples_split": 5
            },
            ModelType.MATCHMAKING: {
                "algorithm": "ensemble",
                "base_estimators": ["random_forest", "gradient_boosting"],
                "meta_learner": "logistic_regression"
            }
        }
        
        return params_map.get(model_type, {})
    
    def _validate_config(self):
        """Valida que la configuración sea coherente"""
        errors = []
        
        # Validar configuración de cache
        if self.cache.enabled and not self.cache.host:
            errors.append("Cache habilitado pero sin host configurado")
        
        # Validar configuración de base de datos
        if not self.database.host or not self.database.name:
            errors.append("Configuración de base de datos incompleta")
        
        # Validar umbrales
        for bu_name, bu_config in self.business_units.items():
            if not 0 <= bu_config.matching_threshold <= 1:
                errors.append(f"Threshold inválido para BU {bu_name}")
        
        if errors:
            raise ValueError(f"Errores de configuración: {errors}")
    
    def get_model_config(self, model_type: Union[str, ModelType]) -> Optional[ModelConfig]:
        """Obtiene configuración de un modelo específico"""
        if isinstance(model_type, ModelType):
            model_type = model_type.value
        
        return self.models.get(model_type)
    
    def get_business_unit_config(self, bu_name: str) -> Optional[BusinessUnitConfig]:
        """Obtiene configuración de una unidad de negocio"""
        return self.business_units.get(bu_name.lower())
    
    def update_model_config(self, model_type: str, updates: Dict[str, Any]):
        """Actualiza configuración de un modelo"""
        if model_type in self.models:
            model_config = self.models[model_type]
            for key, value in updates.items():
                if hasattr(model_config, key):
                    setattr(model_config, key, value)
    
    def get_cache_ttl(self, operation_type: str) -> int:
        """Obtiene TTL de cache para un tipo de operación"""
        ttl_map = {
            "sentiment": self.cache.ttl_sentiment,
            "analysis": self.cache.ttl_analysis,
            "models": self.cache.ttl_models,
            "config": self.cache.ttl_config
        }
        
        return ttl_map.get(operation_type, self.cache.ttl_analysis)
    
    def is_feature_enabled(self, feature: str, business_unit: Optional[str] = None) -> bool:
        """Verifica si una característica está habilitada"""
        if business_unit:
            bu_config = self.get_business_unit_config(business_unit)
            if bu_config:
                return bu_config.features_enabled.get(feature, False)
        
        # Configuración global por defecto
        global_features = {
            "personality_analysis": True,
            "cultural_analysis": True,
            "professional_analysis": True,
            "sentiment_analysis": True,
            "predictive_analysis": True,
            "caching": self.cache.enabled,
            "monitoring": self.monitoring.enabled,
            "security": True
        }
        
        return global_features.get(feature, False)
    
    def save_config(self):
        """Guarda la configuración actual en archivo"""
        config_file = self.config_dir / f"{self.environment.value}.json"
        
        config_data = {
            "environment": self.environment.value,
            "database": self.database.__dict__,
            "cache": self.cache.__dict__,
            "security": self.security.__dict__,
            "performance": self.performance.__dict__,
            "monitoring": self.monitoring.__dict__,
            "models": {k: v.__dict__ for k, v in self.models.items()},
            "business_units": {k: v.__dict__ for k, v in self.business_units.items()}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def reload_config(self):
        """Recarga la configuración desde archivo"""
        self._load_environment_config()
        self._validate_config()
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtiene información completa del sistema"""
        return {
            "environment": self.environment.value,
            "models_configured": len(self.models),
            "business_units_configured": len(self.business_units),
            "cache_enabled": self.cache.enabled,
            "security_enabled": self.security.encryption_enabled,
            "monitoring_enabled": self.monitoring.enabled,
            "performance_workers": self.performance.max_workers,
            "config_version": "2.0.0"
        }


# Instancia global de configuración
_config_instance: Optional[UnifiedMLConfig] = None

def get_config(environment: Optional[Environment] = None) -> UnifiedMLConfig:
    """
    Obtiene la instancia global de configuración (Singleton pattern)
    """
    global _config_instance
    
    if _config_instance is None or (environment and _config_instance.environment != environment):
        env_str = os.getenv('ML_ENVIRONMENT', 'development')
        env = environment or Environment(env_str)
        _config_instance = UnifiedMLConfig(env)
    
    return _config_instance


def reload_config():
    """Fuerza recarga de la configuración global"""
    global _config_instance
    _config_instance = None
    return get_config()


# Shortcuts para acceso rápido
def get_model_config(model_type: str) -> Optional[ModelConfig]:
    return get_config().get_model_config(model_type)

def get_cache_ttl(operation_type: str) -> int:
    return get_config().get_cache_ttl(operation_type)

def is_feature_enabled(feature: str, business_unit: Optional[str] = None) -> bool:
    return get_config().is_feature_enabled(feature, business_unit)