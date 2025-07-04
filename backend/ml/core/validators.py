"""
✅ GhuntRED-v2 ML Validators
Comprehensive input validation for ML systems
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .exceptions import ValidationError

logger = logging.getLogger(__name__)

@dataclass
class ValidationRule:
    """A single validation rule"""
    name: str
    validator_func: callable
    error_message: str
    severity: str = "error"  # "error", "warning", "info"
    
class BaseValidator(ABC):
    """Base validator class"""
    
    @abstractmethod
    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        """Validate data and return (is_valid, errors)"""
        pass

class TextValidator(BaseValidator):
    """Validator for text inputs"""
    
    def __init__(self, 
                 min_length: int = 1,
                 max_length: int = 10000,
                 allow_empty: bool = False,
                 patterns: List[str] = None,
                 forbidden_patterns: List[str] = None):
        self.min_length = min_length
        self.max_length = max_length
        self.allow_empty = allow_empty
        self.patterns = patterns or []
        self.forbidden_patterns = forbidden_patterns or []
    
    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        """Validate text data"""
        errors = []
        
        # Check if data is string
        if not isinstance(data, str):
            return False, [f"Expected string, got {type(data).__name__}"]
        
        # Check empty
        if not data.strip() and not self.allow_empty:
            errors.append("Text cannot be empty")
        
        # Check length
        if len(data) < self.min_length:
            errors.append(f"Text too short (min: {self.min_length}, got: {len(data)})")
        
        if len(data) > self.max_length:
            errors.append(f"Text too long (max: {self.max_length}, got: {len(data)})")
        
        # Check required patterns
        for pattern in self.patterns:
            if not re.search(pattern, data):
                errors.append(f"Text does not match required pattern: {pattern}")
        
        # Check forbidden patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, data):
                errors.append(f"Text contains forbidden pattern: {pattern}")
        
        return len(errors) == 0, errors

class NumericValidator(BaseValidator):
    """Validator for numeric inputs"""
    
    def __init__(self,
                 min_value: Optional[float] = None,
                 max_value: Optional[float] = None,
                 integer_only: bool = False,
                 positive_only: bool = False):
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only
        self.positive_only = positive_only
    
    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        """Validate numeric data"""
        errors = []
        
        # Check if numeric
        if not isinstance(data, (int, float)):
            try:
                data = float(data)
            except (ValueError, TypeError):
                return False, [f"Expected numeric value, got {type(data).__name__}"]
        
        # Check integer requirement
        if self.integer_only and not isinstance(data, int) and not data.is_integer():
            errors.append("Value must be an integer")
        
        # Check positive requirement
        if self.positive_only and data <= 0:
            errors.append("Value must be positive")
        
        # Check range
        if self.min_value is not None and data < self.min_value:
            errors.append(f"Value too small (min: {self.min_value}, got: {data})")
        
        if self.max_value is not None and data > self.max_value:
            errors.append(f"Value too large (max: {self.max_value}, got: {data})")
        
        return len(errors) == 0, errors

class ListValidator(BaseValidator):
    """Validator for list inputs"""
    
    def __init__(self,
                 min_length: int = 0,
                 max_length: int = 1000,
                 item_validator: Optional[BaseValidator] = None,
                 unique_items: bool = False):
        self.min_length = min_length
        self.max_length = max_length
        self.item_validator = item_validator
        self.unique_items = unique_items
    
    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        """Validate list data"""
        errors = []
        
        # Check if list
        if not isinstance(data, (list, tuple)):
            return False, [f"Expected list/tuple, got {type(data).__name__}"]
        
        # Check length
        if len(data) < self.min_length:
            errors.append(f"List too short (min: {self.min_length}, got: {len(data)})")
        
        if len(data) > self.max_length:
            errors.append(f"List too long (max: {self.max_length}, got: {len(data)})")
        
        # Check uniqueness
        if self.unique_items and len(data) != len(set(data)):
            errors.append("List items must be unique")
        
        # Validate items
        if self.item_validator:
            for i, item in enumerate(data):
                item_valid, item_errors = self.item_validator.validate(item)
                if not item_valid:
                    errors.extend([f"Item {i}: {error}" for error in item_errors])
        
        return len(errors) == 0, errors

class DictValidator(BaseValidator):
    """Validator for dictionary inputs"""
    
    def __init__(self,
                 required_keys: List[str] = None,
                 optional_keys: List[str] = None,
                 key_validators: Dict[str, BaseValidator] = None,
                 allow_extra_keys: bool = True):
        self.required_keys = required_keys or []
        self.optional_keys = optional_keys or []
        self.key_validators = key_validators or {}
        self.allow_extra_keys = allow_extra_keys
    
    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        """Validate dictionary data"""
        errors = []
        
        # Check if dict
        if not isinstance(data, dict):
            return False, [f"Expected dictionary, got {type(data).__name__}"]
        
        # Check required keys
        for key in self.required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")
        
        # Check extra keys
        if not self.allow_extra_keys:
            allowed_keys = set(self.required_keys + self.optional_keys)
            extra_keys = set(data.keys()) - allowed_keys
            if extra_keys:
                errors.append(f"Unexpected keys: {', '.join(extra_keys)}")
        
        # Validate individual keys
        for key, validator in self.key_validators.items():
            if key in data:
                key_valid, key_errors = validator.validate(data[key])
                if not key_valid:
                    errors.extend([f"Key '{key}': {error}" for error in key_errors])
        
        return len(errors) == 0, errors

class EmailValidator(BaseValidator):
    """Validator for email addresses"""
    
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        """Validate email format"""
        if not isinstance(data, str):
            return False, ["Email must be a string"]
        
        if not self.EMAIL_PATTERN.match(data):
            return False, ["Invalid email format"]
        
        return True, []

class URLValidator(BaseValidator):
    """Validator for URLs"""
    
    URL_PATTERN = re.compile(
        r'^https?://(?:[-\w.])+(?:\.[a-zA-Z]{2,})+(?::\d+)?(?:/[^?\s]*)?(?:\?[^#\s]*)?(?:#[^\s]*)?$'
    )
    
    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        """Validate URL format"""
        if not isinstance(data, str):
            return False, ["URL must be a string"]
        
        if not self.URL_PATTERN.match(data):
            return False, ["Invalid URL format"]
        
        return True, []

class CandidateDataValidator(DictValidator):
    """Specialized validator for candidate data"""
    
    def __init__(self):
        super().__init__(
            required_keys=['name', 'email'],
            optional_keys=['phone', 'resume_text', 'skills', 'experience_years', 'linkedin_url'],
            key_validators={
                'name': TextValidator(min_length=2, max_length=100),
                'email': EmailValidator(),
                'phone': TextValidator(min_length=10, max_length=20, patterns=[r'^\+?[\d\s\-\(\)]+$']),
                'resume_text': TextValidator(min_length=50, max_length=50000, allow_empty=True),
                'skills': ListValidator(max_length=50, item_validator=TextValidator(max_length=100)),
                'experience_years': NumericValidator(min_value=0, max_value=50),
                'linkedin_url': URLValidator(),
            }
        )

class JobDataValidator(DictValidator):
    """Specialized validator for job data"""
    
    def __init__(self):
        super().__init__(
            required_keys=['title', 'description', 'business_unit'],
            optional_keys=['requirements', 'location', 'salary_range', 'experience_required'],
            key_validators={
                'title': TextValidator(min_length=5, max_length=200),
                'description': TextValidator(min_length=50, max_length=10000),
                'business_unit': TextValidator(patterns=[r'^(huntRED|amigro|sexsi|huntu|huntred_executive)$']),
                'requirements': ListValidator(max_length=20, item_validator=TextValidator(max_length=500)),
                'location': TextValidator(max_length=100),
                'salary_range': DictValidator(
                    required_keys=['min', 'max', 'currency'],
                    key_validators={
                        'min': NumericValidator(min_value=0, positive_only=True),
                        'max': NumericValidator(min_value=0, positive_only=True),
                        'currency': TextValidator(patterns=[r'^[A-Z]{3}$'])
                    }
                ),
                'experience_required': NumericValidator(min_value=0, max_value=30),
            }
        )

class MLInputValidator(DictValidator):
    """Specialized validator for ML prediction inputs"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        
        # Define validators based on model type
        if 'sentiment' in model_name.lower():
            super().__init__(
                required_keys=['text'],
                key_validators={
                    'text': TextValidator(min_length=5, max_length=5000),
                    'language': TextValidator(patterns=[r'^(es|en)$'], allow_empty=True),
                }
            )
        elif 'personality' in model_name.lower():
            super().__init__(
                required_keys=['responses'],
                key_validators={
                    'responses': ListValidator(
                        min_length=10,
                        max_length=100,
                        item_validator=NumericValidator(min_value=1, max_value=5, integer_only=True)
                    ),
                }
            )
        elif 'skills' in model_name.lower():
            super().__init__(
                required_keys=['text'],
                key_validators={
                    'text': TextValidator(min_length=20, max_length=10000),
                    'document_type': TextValidator(patterns=[r'^(resume|job_description|profile)$']),
                }
            )
        elif 'matching' in model_name.lower():
            super().__init__(
                required_keys=['candidate_data', 'job_data'],
                key_validators={
                    'candidate_data': CandidateDataValidator(),
                    'job_data': JobDataValidator(),
                }
            )
        elif 'aura' in model_name.lower() or 'holistic' in model_name.lower():
            super().__init__(
                required_keys=['energy_data'],
                key_validators={
                    'energy_data': DictValidator(
                        required_keys=['chakras', 'aura_colors', 'vibrational_frequency'],
                        key_validators={
                            'chakras': ListValidator(
                                min_length=7,
                                max_length=7,
                                item_validator=NumericValidator(min_value=0, max_value=100)
                            ),
                            'aura_colors': ListValidator(
                                min_length=1,
                                max_length=10,
                                item_validator=TextValidator(patterns=[r'^#[0-9A-Fa-f]{6}$'])
                            ),
                            'vibrational_frequency': NumericValidator(min_value=0, max_value=1000),
                        }
                    ),
                }
            )
        else:
            # Generic validator
            super().__init__(
                required_keys=['data'],
                key_validators={
                    'data': ListValidator(item_validator=NumericValidator()),
                }
            )

class MLValidator:
    """
    🛡️ Comprehensive ML validation system
    
    Features:
    - Input validation for all ML models
    - Custom validators for different data types
    - Business rule validation
    - Performance optimization
    """
    
    def __init__(self):
        self._validators: Dict[str, BaseValidator] = {}
        self._setup_default_validators()
    
    def _setup_default_validators(self):
        """Setup default validators for common data types"""
        self._validators.update({
            'text': TextValidator(),
            'email': EmailValidator(),
            'url': URLValidator(),
            'number': NumericValidator(),
            'list': ListValidator(),
            'dict': DictValidator(),
            'candidate': CandidateDataValidator(),
            'job': JobDataValidator(),
        })
    
    def register_validator(self, name: str, validator: BaseValidator):
        """Register a custom validator"""
        self._validators[name] = validator
        logger.info(f"✅ Registered validator: {name}")
    
    def validate_input(self, data: Any, model_name: str) -> bool:
        """
        Validate input data for a specific ML model
        
        Args:
            data: Input data to validate
            model_name: Name of the ML model
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Get appropriate validator for the model
            validator = self._get_model_validator(model_name)
            
            # Perform validation
            is_valid, errors = validator.validate(data)
            
            if not is_valid:
                error_msg = f"Validation failed for model '{model_name}': " + "; ".join(errors)
                raise ValidationError(
                    message=error_msg,
                    field='input_data',
                    value=str(data)[:100]  # Truncate for logging
                )
            
            logger.debug(f"✅ Input validation passed for model: {model_name}")
            return True
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Convert unexpected errors
            raise ValidationError(
                message=f"Unexpected validation error: {str(e)}",
                field='validation_system',
                value=model_name
            )
    
    def _get_model_validator(self, model_name: str) -> BaseValidator:
        """Get appropriate validator for a model"""
        # Try to get model-specific validator
        if model_name in self._validators:
            return self._validators[model_name]
        
        # Create model-specific validator based on name
        validator = MLInputValidator(model_name)
        self._validators[model_name] = validator
        
        return validator
    
    def validate_business_unit(self, business_unit: str) -> bool:
        """Validate business unit"""
        valid_units = ['huntRED', 'amigro', 'sexsi', 'huntu', 'huntred_executive']
        
        if business_unit not in valid_units:
            raise ValidationError(
                message=f"Invalid business unit: {business_unit}",
                field='business_unit',
                value=business_unit
            )
        
        return True
    
    def validate_model_name(self, model_name: str) -> bool:
        """Validate model name format"""
        # Model names should be alphanumeric with underscores
        pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
        
        if not re.match(pattern, model_name):
            raise ValidationError(
                message=f"Invalid model name format: {model_name}",
                field='model_name',
                value=model_name
            )
        
        return True
    
    def validate_batch_input(self, data_list: List[Any], model_name: str) -> bool:
        """Validate batch input data"""
        if not isinstance(data_list, list):
            raise ValidationError(
                message="Batch input must be a list",
                field='batch_data',
                value=str(type(data_list))
            )
        
        if len(data_list) == 0:
            raise ValidationError(
                message="Batch input cannot be empty",
                field='batch_data',
                value='empty_list'
            )
        
        if len(data_list) > 1000:  # Reasonable batch size limit
            raise ValidationError(
                message=f"Batch size too large: {len(data_list)} (max: 1000)",
                field='batch_size',
                value=str(len(data_list))
            )
        
        # Validate each item in the batch
        for i, item in enumerate(data_list):
            try:
                self.validate_input(item, model_name)
            except ValidationError as e:
                raise ValidationError(
                    message=f"Batch item {i}: {e.message}",
                    field=f'batch_item_{i}',
                    value=str(item)[:100]
                )
        
        return True
    
    def get_validation_schema(self, model_name: str) -> Dict[str, Any]:
        """Get validation schema for a model"""
        validator = self._get_model_validator(model_name)
        
        # This is a simplified schema representation
        # In a full implementation, you'd want to create a more detailed schema
        schema = {
            'model_name': model_name,
            'validator_type': type(validator).__name__,
            'description': f"Validation schema for {model_name}",
        }
        
        if hasattr(validator, 'required_keys'):
            schema['required_fields'] = validator.required_keys
        
        if hasattr(validator, 'optional_keys'):
            schema['optional_fields'] = validator.optional_keys
        
        return schema
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on validation system"""
        return {
            'status': 'healthy',
            'registered_validators': len(self._validators),
            'available_validators': list(self._validators.keys()),
        }

# Export main components
__all__ = [
    'MLValidator',
    'BaseValidator',
    'TextValidator',
    'NumericValidator',
    'ListValidator', 
    'DictValidator',
    'EmailValidator',
    'URLValidator',
    'CandidateDataValidator',
    'JobDataValidator',
    'MLInputValidator',
    'ValidationRule',
]