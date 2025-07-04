"""
🚨 GhuntRED-v2 ML Exceptions
Custom exceptions for ML systems with detailed error information
"""

class MLException(Exception):
    """Base exception for all ML-related errors"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or 'ML_ERROR'
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to dictionary for API responses"""
        return {
            'error': self.error_code,
            'message': self.message,
            'details': self.details
        }

class ModelNotFoundError(MLException):
    """Raised when a requested ML model is not found"""
    
    def __init__(self, message: str, model_name: str = None, business_unit: str = None):
        super().__init__(
            message=message,
            error_code='MODEL_NOT_FOUND',
            details={
                'model_name': model_name,
                'business_unit': business_unit
            }
        )

class PredictionError(MLException):
    """Raised when ML prediction fails"""
    
    def __init__(self, message: str, model_name: str = None, input_data: dict = None):
        super().__init__(
            message=message,
            error_code='PREDICTION_ERROR',
            details={
                'model_name': model_name,
                'input_data_type': type(input_data).__name__ if input_data else None
            }
        )

class ValidationError(MLException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        super().__init__(
            message=message,
            error_code='VALIDATION_ERROR',
            details={
                'field': field,
                'value': str(value) if value else None
            }
        )

class ModelLoadError(MLException):
    """Raised when model loading fails"""
    
    def __init__(self, message: str, model_path: str = None, original_error: str = None):
        super().__init__(
            message=message,
            error_code='MODEL_LOAD_ERROR',
            details={
                'model_path': model_path,
                'original_error': original_error
            }
        )

class ConfigurationError(MLException):
    """Raised when ML system configuration is invalid"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message=message,
            error_code='CONFIGURATION_ERROR',
            details={
                'config_key': config_key
            }
        )

class ResourceError(MLException):
    """Raised when system resources are insufficient"""
    
    def __init__(self, message: str, resource_type: str = None, required: str = None, available: str = None):
        super().__init__(
            message=message,
            error_code='RESOURCE_ERROR',
            details={
                'resource_type': resource_type,
                'required': required,
                'available': available
            }
        )

class TimeoutError(MLException):
    """Raised when ML operation times out"""
    
    def __init__(self, message: str, operation: str = None, timeout_seconds: float = None):
        super().__init__(
            message=message,
            error_code='TIMEOUT_ERROR',
            details={
                'operation': operation,
                'timeout_seconds': timeout_seconds
            }
        )

class CacheError(MLException):
    """Raised when cache operations fail"""
    
    def __init__(self, message: str, cache_key: str = None, operation: str = None):
        super().__init__(
            message=message,
            error_code='CACHE_ERROR',
            details={
                'cache_key': cache_key,
                'operation': operation
            }
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

class PersonalityAnalysisError(GenIAException):
    """Raised when personality analysis fails"""
    
    def __init__(self, message: str, candidate_id: str = None):
        super().__init__(
            message=message,
            error_code='PERSONALITY_ANALYSIS_ERROR',
            details={'candidate_id': candidate_id}
        )

class SkillsExtractionError(GenIAException):
    """Raised when skills extraction fails"""
    
    def __init__(self, message: str, document_type: str = None):
        super().__init__(
            message=message,
            error_code='SKILLS_EXTRACTION_ERROR',
            details={'document_type': document_type}
        )

class MatchingError(GenIAException):
    """Raised when candidate matching fails"""
    
    def __init__(self, message: str, job_id: str = None, candidate_count: int = None):
        super().__init__(
            message=message,
            error_code='MATCHING_ERROR',
            details={
                'job_id': job_id,
                'candidate_count': candidate_count
            }
        )

# AURA specific exceptions
class AURAException(MLException):
    """Base exception for AURA system"""
    
    def __init__(self, message: str, error_code: str = 'AURA_ERROR', details: dict = None):
        super().__init__(message, error_code, details)

class HolisticAssessmentError(AURAException):
    """Raised when holistic assessment fails"""
    
    def __init__(self, message: str, person_id: str = None, assessment_type: str = None):
        super().__init__(
            message=message,
            error_code='HOLISTIC_ASSESSMENT_ERROR',
            details={
                'person_id': person_id,
                'assessment_type': assessment_type
            }
        )

class VibrationalMatchingError(AURAException):
    """Raised when vibrational matching fails"""
    
    def __init__(self, message: str, energy_signature: dict = None):
        super().__init__(
            message=message,
            error_code='VIBRATIONAL_MATCHING_ERROR',
            details={
                'energy_signature_keys': list(energy_signature.keys()) if energy_signature else None
            }
        )

class CompatibilityAnalysisError(AURAException):
    """Raised when compatibility analysis fails"""
    
    def __init__(self, message: str, candidate_id: str = None, job_id: str = None):
        super().__init__(
            message=message,
            error_code='COMPATIBILITY_ANALYSIS_ERROR',
            details={
                'candidate_id': candidate_id,
                'job_id': job_id
            }
        )

class EnergyProfilingError(AURAException):
    """Raised when energy profiling fails"""
    
    def __init__(self, message: str, profile_data: dict = None):
        super().__init__(
            message=message,
            error_code='ENERGY_PROFILING_ERROR',
            details={
                'profile_data_size': len(profile_data) if profile_data else None
            }
        )

# Error handling utilities
def handle_ml_exception(func):
    """Decorator to handle ML exceptions gracefully"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MLException:
            # Re-raise ML exceptions as-is
            raise
        except Exception as e:
            # Convert other exceptions to MLException
            raise MLException(
                message=f"Unexpected error in {func.__name__}: {str(e)}",
                error_code='UNEXPECTED_ERROR',
                details={
                    'function': func.__name__,
                    'original_exception': type(e).__name__
                }
            )
    return wrapper

def get_error_response(exception: MLException, status_code: int = 500) -> dict:
    """Get standardized error response for API"""
    return {
        'success': False,
        'error': exception.to_dict(),
        'status_code': status_code,
        'timestamp': '2024-01-01T00:00:00Z'  # Would use timezone.now() in real implementation
    }

# Export all exceptions
__all__ = [
    'MLException',
    'ModelNotFoundError',
    'PredictionError',
    'ValidationError',
    'ModelLoadError',
    'ConfigurationError',
    'ResourceError',
    'TimeoutError',
    'CacheError',
    'GenIAException',
    'SentimentAnalysisError',
    'PersonalityAnalysisError',
    'SkillsExtractionError',
    'MatchingError',
    'AURAException',
    'HolisticAssessmentError',
    'VibrationalMatchingError',
    'CompatibilityAnalysisError',
    'EnergyProfilingError',
    'handle_ml_exception',
    'get_error_response'
]