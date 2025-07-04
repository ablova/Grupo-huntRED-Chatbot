"""
🛡️ Validación de Datos para Sistema ML - huntRED®

Schemas de validación robustos usando Pydantic para todos los inputs del sistema ML.
"""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum


class SentimentLabel(str, Enum):
    """Etiquetas válidas de sentimiento"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class EngagementLevel(str, Enum):
    """Niveles válidos de engagement"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BusinessUnit(str, Enum):
    """Unidades de negocio válidas"""
    HUNTRED = "huntred"
    HUNTU = "huntu"
    AMIGRO = "amigro"
    HUNTRED_EXECUTIVE = "huntred_executive"


class LanguageCode(str, Enum):
    """Códigos de idioma válidos"""
    ES_MX = "es_MX"
    EN_US = "en_US"
    ES = "es"
    EN = "en"


class SentimentAnalysisInput(BaseModel):
    """Schema para entrada de análisis de sentimientos"""
    
    text: str = Field(..., min_length=1, max_length=10000, description="Texto a analizar")
    language: Optional[LanguageCode] = Field(None, description="Idioma del texto")
    context: Optional[str] = Field(None, max_length=500, description="Contexto adicional")
    user_id: Optional[int] = Field(None, gt=0, description="ID del usuario")
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("El texto no puede estar vacío")
        # Remover caracteres de control
        cleaned = ''.join(char for char in v if ord(char) >= 32 or char in '\n\r\t')
        return cleaned.strip()


class PersonAnalysisInput(BaseModel):
    """Schema para análisis de personas"""
    
    person_id: int = Field(..., gt=0, description="ID de la persona")
    include_personality: bool = Field(True, description="Incluir análisis de personalidad")
    include_cultural: bool = Field(True, description="Incluir análisis cultural")
    include_professional: bool = Field(True, description="Incluir análisis profesional")
    business_unit: Optional[BusinessUnit] = Field(None, description="Unidad de negocio")
    
    @validator('person_id')
    def validate_person_id(cls, v):
        if v <= 0:
            raise ValueError("person_id debe ser mayor a 0")
        return v


class OnboardingAnalysisInput(BaseModel):
    """Schema para análisis de onboarding"""
    
    person_id: int = Field(..., gt=0, description="ID de la persona")
    vacancy_id: int = Field(..., gt=0, description="ID de la vacante")
    hire_date: datetime = Field(..., description="Fecha de contratación")
    current_status: str = Field(..., min_length=1, description="Estado actual")
    survey_responses: Optional[Dict[str, Any]] = Field(None, description="Respuestas de encuesta")
    
    @validator('hire_date')
    def validate_hire_date(cls, v):
        if v > datetime.now():
            raise ValueError("La fecha de contratación no puede ser futura")
        return v
    
    @root_validator
    def validate_ids(cls, values):
        person_id = values.get('person_id')
        vacancy_id = values.get('vacancy_id')
        if person_id == vacancy_id:
            raise ValueError("person_id y vacancy_id no pueden ser iguales")
        return values


class NotificationOptimizationInput(BaseModel):
    """Schema para optimización de notificaciones"""
    
    user_id: int = Field(..., gt=0, description="ID del usuario")
    notification_type: str = Field(..., min_length=1, max_length=100, description="Tipo de notificación")
    base_content: str = Field(..., min_length=1, max_length=5000, description="Contenido base")
    business_unit: Optional[BusinessUnit] = Field(None, description="Unidad de negocio")
    priority: Optional[int] = Field(1, ge=1, le=5, description="Prioridad (1-5)")
    
    @validator('notification_type')
    def validate_notification_type(cls, v):
        allowed_types = [
            'welcome', 'reminder', 'update', 'alert', 'survey', 
            'feedback', 'promotion', 'info', 'warning', 'success'
        ]
        if v.lower() not in allowed_types:
            raise ValueError(f"Tipo de notificación debe ser uno de: {allowed_types}")
        return v.lower()


class ModelTrainingInput(BaseModel):
    """Schema para entrenamiento de modelos"""
    
    model_type: str = Field(..., min_length=1, description="Tipo de modelo")
    training_data_path: str = Field(..., min_length=1, description="Ruta a datos de entrenamiento")
    validation_split: float = Field(0.2, ge=0.1, le=0.5, description="Proporción para validación")
    hyperparameters: Optional[Dict[str, Any]] = Field(None, description="Hiperparámetros")
    
    @validator('model_type')
    def validate_model_type(cls, v):
        allowed_models = [
            'sentiment_analyzer', 'retention_predictor', 'satisfaction_predictor',
            'matchmaking', 'personality_analyzer', 'cultural_analyzer'
        ]
        if v not in allowed_models:
            raise ValueError(f"Tipo de modelo debe ser uno de: {allowed_models}")
        return v
    
    @validator('training_data_path')
    def validate_data_path(cls, v):
        if not v.endswith(('.csv', '.json', '.parquet')):
            raise ValueError("Archivo debe ser CSV, JSON o Parquet")
        return v


class AnalysisResponse(BaseModel):
    """Schema para respuestas de análisis"""
    
    success: bool = Field(..., description="Indica si el análisis fue exitoso")
    analysis_type: str = Field(..., description="Tipo de análisis realizado")
    results: Dict[str, Any] = Field(..., description="Resultados del análisis")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confianza del resultado")
    execution_time_ms: Optional[int] = Field(None, ge=0, description="Tiempo de ejecución en ms")
    model_version: Optional[str] = Field(None, description="Versión del modelo usado")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp del análisis")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Confianza debe estar entre 0 y 1")
        return v


class ErrorResponse(BaseModel):
    """Schema para respuestas de error"""
    
    success: bool = Field(False, description="Siempre False para errores")
    error_type: str = Field(..., description="Tipo de error")
    error_code: str = Field(..., description="Código de error")
    message: str = Field(..., description="Mensaje de error")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto del error")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp del error")


class ConfigValidation(BaseModel):
    """Schema para validación de configuración"""
    
    model_paths: Dict[str, str] = Field(..., description="Rutas de modelos")
    cache_settings: Dict[str, Any] = Field(..., description="Configuración de cache")
    thresholds: Dict[str, float] = Field(..., description="Umbrales del sistema")
    business_units: List[BusinessUnit] = Field(..., description="Unidades de negocio activas")
    
    @validator('thresholds')
    def validate_thresholds(cls, v):
        required_thresholds = ['confidence', 'sentiment_positive', 'sentiment_negative']
        for threshold in required_thresholds:
            if threshold not in v:
                raise ValueError(f"Threshold requerido faltante: {threshold}")
            if not 0 <= v[threshold] <= 1:
                raise ValueError(f"Threshold {threshold} debe estar entre 0 y 1")
        return v


def validate_input(schema_class: BaseModel, data: Dict[str, Any]) -> BaseModel:
    """
    Valida datos de entrada usando un schema Pydantic.
    
    Args:
        schema_class: Clase del schema de validación
        data: Datos a validar
        
    Returns:
        Instancia validada del schema
        
    Raises:
        ValidationError: Si los datos no son válidos
    """
    try:
        return schema_class(**data)
    except Exception as e:
        from app.ml.core.exceptions import ValidationError
        raise ValidationError(
            message=f"Error de validación: {str(e)}",
            context={'schema': schema_class.__name__, 'data_keys': list(data.keys())}
        )


def validate_response(schema_class: BaseModel, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida datos de respuesta y los serializa.
    
    Args:
        schema_class: Clase del schema de validación
        data: Datos a validar
        
    Returns:
        Diccionario validado y serializado
    """
    try:
        validated = schema_class(**data)
        return validated.dict()
    except Exception as e:
        # Para respuestas, solo loggear el error y devolver estructura básica
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error validando respuesta: {e}")
        
        return ErrorResponse(
            error_type="ValidationError",
            error_code="RESPONSE_VALIDATION_FAILED",
            message=str(e),
            context={'schema': schema_class.__name__}
        ).dict()


# Decorator para validación automática de entrada
def validate_ml_input(input_schema: BaseModel):
    """
    Decorator para validación automática de entrada en funciones ML.
    
    Usage:
        @validate_ml_input(SentimentAnalysisInput)
        def analyze_sentiment(validated_input):
            # validated_input es una instancia del schema validada
            pass
    """
    def decorator(func):
        def wrapper(data, *args, **kwargs):
            if isinstance(data, dict):
                validated_input = validate_input(input_schema, data)
            else:
                validated_input = data  # Asume que ya está validado
            
            return func(validated_input, *args, **kwargs)
        return wrapper
    return decorator