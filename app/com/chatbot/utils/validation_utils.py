# /home/pablo/app/com/chatbot/utils/validation_utils.py∫
"""
Utilidades para validación de datos.
"""
import logging
import re
from typing import Dict, List, Optional, Any
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

class ValidationUtils:
    """Utilidades para validación de datos."""

    # Patrones de validación
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^\+?[0-9]{10,15}$'
    URL_PATTERN = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    DATE_PATTERN = r'^\d{4}-\d{2}-\d{2}$'

    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida un correo electrónico."""
        if not email:
            return False
        return bool(re.match(ValidationUtils.EMAIL_PATTERN, email))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valida un número de teléfono."""
        if not phone:
            return False
        return bool(re.match(ValidationUtils.PHONE_PATTERN, phone))

    @staticmethod
    def validate_url(url: str) -> bool:
        """Valida una URL."""
        if not url:
            return False
        return bool(re.match(ValidationUtils.URL_PATTERN, url))

    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Valida una fecha en formato YYYY-MM-DD."""
        if not date_str:
            return False
        if not re.match(ValidationUtils.DATE_PATTERN, date_str):
            return False
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_required_fields(data: Dict, required_fields: List[str]) -> None:
        """Valida que los campos requeridos estén presentes y no vacíos."""
        missing_fields = []
        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(
                _('Faltan los siguientes campos requeridos: %(fields)s'),
                params={'fields': ', '.join(missing_fields)}
            )

    @staticmethod
    def validate_field_type(value: Any, expected_type: type) -> bool:
        """Valida que un valor sea del tipo esperado."""
        return isinstance(value, expected_type)

    @staticmethod
    def validate_string_length(value: str, min_length: int = 0, max_length: Optional[int] = None) -> bool:
        """Valida la longitud de una cadena de texto."""
        if not isinstance(value, str):
            return False
        
        if len(value) < min_length:
            return False
        
        if max_length is not None and len(value) > max_length:
            return False
        
        return True

    @staticmethod
    def validate_numeric_range(value: float, min_value: Optional[float] = None, max_value: Optional[float] = None) -> bool:
        """Valida que un número esté dentro de un rango."""
        if not isinstance(value, (int, float)):
            return False
        
        if min_value is not None and value < min_value:
            return False
        
        if max_value is not None and value > max_value:
            return False
        
        return True

    @staticmethod
    def validate_choice(value: Any, valid_choices: List[Any]) -> bool:
        """Valida que un valor esté en una lista de opciones válidas."""
        return value in valid_choices

    @staticmethod
    def sanitize_input(value: str) -> str:
        """Limpia y sanitiza una entrada de texto."""
        if not isinstance(value, str):
            return str(value)
        
        # Eliminar caracteres de control
        value = ''.join(char for char in value if ord(char) >= 32)
        
        # Eliminar espacios múltiples
        value = ' '.join(value.split())
        
        return value.strip()

    @staticmethod
    def validate_json_structure(data: Dict, schema: Dict) -> bool:
        """Valida que un diccionario cumpla con una estructura JSON esperada."""
        try:
            for key, value_type in schema.items():
                if key not in data:
                    return False
                
                if not isinstance(data[key], value_type):
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validando estructura JSON: {str(e)}")
            return False 