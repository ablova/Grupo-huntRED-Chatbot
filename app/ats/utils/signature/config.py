"""
Configuración del sistema de firmas electrónicas.
"""
from typing import Dict, List
from app.models import APIConfig

# Configuración de tipos de documentos
DOCUMENT_TYPES = {
    'offer_letter': {
        'name': 'Carta de Oferta',
        'required_fields': ['candidate_name', 'position', 'salary', 'start_date'],
        'signature_required': True,
        'biometric_required': True,
        'blockchain_required': True
    },
    'proposal': {
        'name': 'Propuesta',
        'required_fields': ['client_name', 'project_name', 'total_amount', 'validity_date'],
        'signature_required': True,
        'biometric_required': True,
        'blockchain_required': True
    },
    'agreement': {
        'name': 'Acuerdo',
        'required_fields': ['party1_name', 'party2_name', 'agreement_type', 'effective_date'],
        'signature_required': True,
        'biometric_required': True,
        'blockchain_required': True
    }
}

# Configuración de INCODE
INCODE_CONFIG = {
    'api_key': APIConfig.get_value('INCODE_API_KEY'),
    'api_secret': APIConfig.get_value('INCODE_API_SECRET'),
    'base_url': APIConfig.get_value('INCODE_BASE_URL', 'https://api.incode.com/v1'),
    'endpoints': {
        'face_match': '/face/match',
        'liveness': '/liveness',
        'document_verification': '/document/verify',
        'electronic_signature': '/signature/verify'
    },
    'thresholds': {
        'face_match': APIConfig.get_value('INCODE_FACE_MATCH_THRESHOLD', 0.7),
        'liveness': APIConfig.get_value('INCODE_LIVENESS_THRESHOLD', 0.7),
        'document_verification': APIConfig.get_value('INCODE_DOC_VERIFY_THRESHOLD', 0.7),
        'signature_verification': APIConfig.get_value('INCODE_SIGNATURE_THRESHOLD', 0.7)
    },
    'timeout': APIConfig.get_value('INCODE_TIMEOUT', 30),  # segundos
    'retry_attempts': APIConfig.get_value('INCODE_RETRY_ATTEMPTS', 3),
    'cache_ttl': APIConfig.get_value('INCODE_CACHE_TTL', 3600)  # segundos
}

# Configuración de validación biométrica
BIOMETRIC_CONFIG = {
    'provider': APIConfig.get_value('BIOMETRIC_PROVIDER', 'incode'),  # 'incode' o 'local'
    'min_face_confidence': 0.7,
    'min_liveness_score': 0.7,
    'min_document_authenticity': 0.7,
    'required_methods': ['face_recognition', 'liveness_detection', 'document_verification'],
    'image_quality': {
        'min_resolution': (640, 480),
        'min_brightness': 0.3,
        'min_sharpness': 0.5
    },
    'cache': {
        'enabled': True,
        'ttl': 3600  # segundos
    }
}

# Configuración de blockchain
BLOCKCHAIN_CONFIG = {
    'network': 'mainnet',
    'min_confirmations': 3,
    'gas_limit': 3000000,
    'gas_price': 20,
    'contract_address': '0x1234567890abcdef1234567890abcdef12345678',
    'async_processing': True  # Procesamiento asíncrono
}

# Configuración de almacenamiento
STORAGE_CONFIG = {
    'signature_path': 'storage/signatures/',
    'document_path': 'storage/documents/',
    'allowed_extensions': ['.pdf', '.doc', '.docx'],
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'encryption': {
        'enabled': True,
        'algorithm': 'AES-256-GCM'
    }
}

# Configuración de notificaciones
NOTIFICATION_CONFIG = {
    'email': {
        'enabled': True,
        'template_path': 'templates/emails/signature/',
        'subject_prefix': '[huntRED] '
    },
    'sms': {
        'enabled': True,
        'provider': 'messagebird',
        'template_path': 'templates/sms/signature/'
    }
}

# Configuración de seguridad
SECURITY_CONFIG = {
    'max_attempts': 3,
    'lockout_duration': 30,  # minutos
    'session_timeout': 60,  # minutos
    'ip_whitelist': [
        '127.0.0.1',
        '192.168.1.0/24'
    ],
    'rate_limit': {
        'requests': 100,
        'period': 60  # segundos
    },
    'token': {
        'algorithm': 'HS256',
        'expiry': 3600  # segundos
    }
}

# Configuración de logs
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'logs/signature.log',
    'security_events': {
        'enabled': True,
        'file': 'logs/security_events.log'
    }
}

# Configuración de caché
CACHE_CONFIG = {
    'enabled': True,
    'backend': 'redis',
    'ttl': 3600,  # segundos
    'prefix': 'signature_',
    'biometric': {
        'enabled': True,
        'ttl': 3600  # segundos
    }
}

# Configuración de API
API_CONFIG = {
    'version': 'v1',
    'base_url': '/api/signature/',
    'rate_limit': {
        'requests': 100,
        'period': 60  # segundos
    },
    'documentation': {
        'enabled': True,
        'path': '/api/docs/signature/'
    }
}

# Configuración de UI
UI_CONFIG = {
    'theme': 'light',
    'language': 'es',
    'timezone': 'America/Mexico_City',
    'date_format': '%d/%m/%Y',
    'time_format': '%H:%M:%S',
    'error_messages': {
        'biometric_failed': 'La validación biométrica ha fallado. Por favor, intente nuevamente.',
        'signature_invalid': 'La firma no es válida. Por favor, intente nuevamente.',
        'document_expired': 'El documento ha expirado.',
        'too_many_attempts': 'Demasiados intentos fallidos. Por favor, intente más tarde.'
    }
}

def get_document_config(document_type: str) -> Dict:
    """
    Obtiene la configuración para un tipo de documento específico.
    
    Args:
        document_type: Tipo de documento
        
    Returns:
        Diccionario con la configuración del documento
    """
    return DOCUMENT_TYPES.get(document_type, {})

def get_required_fields(document_type: str) -> List[str]:
    """
    Obtiene los campos requeridos para un tipo de documento.
    
    Args:
        document_type: Tipo de documento
        
    Returns:
        Lista de campos requeridos
    """
    config = get_document_config(document_type)
    return config.get('required_fields', [])

def is_signature_required(document_type: str) -> bool:
    """
    Verifica si se requiere firma para un tipo de documento.
    
    Args:
        document_type: Tipo de documento
        
    Returns:
        True si se requiere firma, False en caso contrario
    """
    config = get_document_config(document_type)
    return config.get('signature_required', False)

def is_biometric_required(document_type: str) -> bool:
    """
    Verifica si se requiere validación biométrica para un tipo de documento.
    
    Args:
        document_type: Tipo de documento
        
    Returns:
        True si se requiere validación biométrica, False en caso contrario
    """
    config = get_document_config(document_type)
    return config.get('biometric_required', False)

def is_blockchain_required(document_type: str) -> bool:
    """
    Verifica si se requiere blockchain para un tipo de documento.
    
    Args:
        document_type: Tipo de documento
        
    Returns:
        True si se requiere blockchain, False en caso contrario
    """
    config = get_document_config(document_type)
    return config.get('blockchain_required', False)

def get_incode_config() -> Dict:
    """
    Obtiene la configuración de INCODE.
    
    Returns:
        Diccionario con la configuración de INCODE
    """
    return INCODE_CONFIG

def get_biometric_config() -> Dict:
    """
    Obtiene la configuración biométrica.
    
    Returns:
        Diccionario con la configuración biométrica
    """
    return BIOMETRIC_CONFIG 