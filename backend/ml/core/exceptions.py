"""
� GhuntRED-v2 ML Exceptions
Comprehensive error handling for ML operations
"""

class MLException(Exception):
    """Base exception for all ML operations"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or "ML_ERROR"
        self.details = details or {}
        super().__init__(self.message)

class ModelNotFound(MLException):
    """Raised when a requested model is not found"""
    def __init__(self, model_name: str):
        super().__init__(
            f"Model '{model_name}' not found",
            error_code="MODEL_NOT_FOUND",
            details={"model_name": model_name}
        )

class ValidationError(MLException):
    """Raised when input validation fails"""
    def __init__(self, field: str, message: str):
        super().__init__(
            f"Validation error in field '{field}': {message}",
            error_code="VALIDATION_ERROR",
            details={"field": field, "validation_message": message}
        )

class PredictionError(MLException):
    """Raised when prediction fails"""
    def __init__(self, model_name: str, reason: str):
        super().__init__(
            f"Prediction failed for model '{model_name}': {reason}",
            error_code="PREDICTION_ERROR",
            details={"model_name": model_name, "reason": reason}
        )

class ModelInitializationError(MLException):
    """Raised when model initialization fails"""
    def __init__(self, model_name: str, reason: str):
        super().__init__(
            f"Failed to initialize model '{model_name}': {reason}",
            error_code="MODEL_INIT_ERROR",
            details={"model_name": model_name, "reason": reason}
        )

class InsufficientDataError(MLException):
    """Raised when there's not enough data for analysis"""
    def __init__(self, required_fields: list, missing_fields: list):
        super().__init__(
            f"Insufficient data: missing {missing_fields}",
            error_code="INSUFFICIENT_DATA",
            details={"required_fields": required_fields, "missing_fields": missing_fields}
        )

class ModelTimeoutError(MLException):
    """Raised when model operation times out"""
    def __init__(self, model_name: str, timeout_seconds: int):
        super().__init__(
            f"Model '{model_name}' timed out after {timeout_seconds} seconds",
            error_code="MODEL_TIMEOUT",
            details={"model_name": model_name, "timeout_seconds": timeout_seconds}
        )

# GenIA specific exceptions
class GenIAException(MLException):
    """Base exception for GenIA system"""
    
    def __init__(self, message: str, error_code: str = 'GENIA_ERROR', details: dict = None):
        super().__init__(message, error_code, details)

class SentimentAnalysisError(GenIAException):
    """Raised when sentiment analysis fails"""
    
    def __init__(self, message: str, text: str = None):
        super().__init__(
            message=message,
            error_code='SENTIMENT_ANALYSIS_ERROR',
            details={'text_length': len(text) if text else None}
        )

# AURA specific exceptions
class AURAException(MLException):
    """Base exception for AURA system"""
    
    def __init__(self, message: str, error_code: str = 'AURA_ERROR', details: dict = None):
        super().__init__(message, error_code, details)

class HolisticAssessmentError(AURAException):
    """Raised when holistic assessment fails"""
    
    def __init__(self, message: str, person_id: str = None):
        super().__init__(
            message=message,
            error_code='HOLISTIC_ASSESSMENT_ERROR',
            details={'person_id': person_id}
        )

# Export all exceptions
__all__ = [
    'MLException',
    'ModelNotFound',
    'ValidationError',
    'PredictionError',
    'ModelInitializationError',
    'InsufficientDataError',
    'ModelTimeoutError',
    'GenIAException',
    'SentimentAnalysisError',
    'AURAException',
    'HolisticAssessmentError',
]