"""
Validation utilities for integration data.
Provides functions to validate data before processing.
"""

from typing import Dict, Any, List, Optional, Union
from .exceptions import ValidationError

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that all required fields are present in the data.
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            context={'missing_fields': missing_fields}
        )

def validate_field_type(field_name: str, value: Any, expected_type: Union[type, tuple]) -> None:
    """
    Validate that a field has the expected type.
    
    Args:
        field_name: Name of the field
        value: Value to validate
        expected_type: Expected type or tuple of types
        
    Raises:
        ValidationError: If the field has an unexpected type
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Field '{field_name}' must be of type {expected_type}, got {type(value)}",
            context={
                'field_name': field_name,
                'expected_type': expected_type,
                'actual_type': type(value)
            }
        )

def validate_string_length(field_name: str, value: str, min_length: Optional[int] = None, max_length: Optional[int] = None) -> None:
    """
    Validate that a string field has the expected length.
    
    Args:
        field_name: Name of the field
        value: String value to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Raises:
        ValidationError: If the string length is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Field '{field_name}' must be a string",
            context={'field_name': field_name, 'value': value}
        )
        
    length = len(value)
    if min_length is not None and length < min_length:
        raise ValidationError(
            f"Field '{field_name}' must be at least {min_length} characters long",
            context={
                'field_name': field_name,
                'min_length': min_length,
                'actual_length': length
            }
        )
        
    if max_length is not None and length > max_length:
        raise ValidationError(
            f"Field '{field_name}' must be at most {max_length} characters long",
            context={
                'field_name': field_name,
                'max_length': max_length,
                'actual_length': length
            }
        )

def validate_numeric_range(field_name: str, value: Union[int, float], min_value: Optional[Union[int, float]] = None, max_value: Optional[Union[int, float]] = None) -> None:
    """
    Validate that a numeric field is within the expected range.
    
    Args:
        field_name: Name of the field
        value: Numeric value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Raises:
        ValidationError: If the value is outside the allowed range
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"Field '{field_name}' must be numeric",
            context={'field_name': field_name, 'value': value}
        )
        
    if min_value is not None and value < min_value:
        raise ValidationError(
            f"Field '{field_name}' must be at least {min_value}",
            context={
                'field_name': field_name,
                'min_value': min_value,
                'actual_value': value
            }
        )
        
    if max_value is not None and value > max_value:
        raise ValidationError(
            f"Field '{field_name}' must be at most {max_value}",
            context={
                'field_name': field_name,
                'max_value': max_value,
                'actual_value': value
            }
        )

def validate_enum_value(field_name: str, value: Any, allowed_values: List[Any]) -> None:
    """
    Validate that a field has one of the allowed values.
    
    Args:
        field_name: Name of the field
        value: Value to validate
        allowed_values: List of allowed values
        
    Raises:
        ValidationError: If the value is not in the allowed values
    """
    if value not in allowed_values:
        raise ValidationError(
            f"Field '{field_name}' must be one of {allowed_values}",
            context={
                'field_name': field_name,
                'allowed_values': allowed_values,
                'actual_value': value
            }
        )

def validate_url(field_name: str, value: str) -> None:
    """
    Validate that a field contains a valid URL.
    
    Args:
        field_name: Name of the field
        value: URL string to validate
        
    Raises:
        ValidationError: If the URL is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Field '{field_name}' must be a string",
            context={'field_name': field_name, 'value': value}
        )
        
    if not value.startswith(('http://', 'https://')):
        raise ValidationError(
            f"Field '{field_name}' must be a valid URL starting with http:// or https://",
            context={'field_name': field_name, 'value': value}
        )

def validate_email(field_name: str, value: str) -> None:
    """
    Validate that a field contains a valid email address.
    
    Args:
        field_name: Name of the field
        value: Email string to validate
        
    Raises:
        ValidationError: If the email is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Field '{field_name}' must be a string",
            context={'field_name': field_name, 'value': value}
        )
        
    if '@' not in value or '.' not in value:
        raise ValidationError(
            f"Field '{field_name}' must be a valid email address",
            context={'field_name': field_name, 'value': value}
        )

def validate_phone_number(field_name: str, value: str) -> None:
    """
    Validate that a field contains a valid phone number.
    
    Args:
        field_name: Name of the field
        value: Phone number string to validate
        
    Raises:
        ValidationError: If the phone number is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Field '{field_name}' must be a string",
            context={'field_name': field_name, 'value': value}
        )
        
    # Remove any non-digit characters
    digits = ''.join(filter(str.isdigit, value))
    
    if len(digits) < 10:
        raise ValidationError(
            f"Field '{field_name}' must be a valid phone number with at least 10 digits",
            context={'field_name': field_name, 'value': value}
        ) 