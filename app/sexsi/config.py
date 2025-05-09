# Ubicacion SEXSI -- /home/pablo/app/sexsi/config.py
"""
Configuración específica para la unidad de negocio SEXSI.
"""
from typing import Dict, Any
from django.conf import settings

# Configuración de firma digital para SEXSI
SEXSI_SIGNATURE_CONFIG = {
    # Tipos de documentos que pueden ser firmados
    'document_types': {
        'mutual_agreement': {
            'template': 'sexsi/templates/mutual_agreement.html',
            'signature_type': 'handwritten',  # handwritten o digital
            'required_fields': [
                'full_name',
                'date_of_birth',
                'nationality',
                'identification_number'
            ]
        },
        'consent_agreement': {
            'template': 'sexsi/templates/consent_agreement.html',
            'signature_type': 'digital',
            'required_fields': [
                'full_name',
                'date_of_birth',
                'nationality',
                'identification_number',
                'consent_type'
            ]
        }
    },
    
    # Configuración de validación de identidad
    'identity_validation': {
        'required_documents': [
            'identification_card',
            'proof_of_address',
            'medical_certificate'
        ],
        'validation_steps': [
            'document_upload',
            'biometric_validation',
            'manual_review'
        ]
    },
    
    # Configuración de firma digital
    'digital_signature': {
        'provider': 'basic',  # basic o docusign
        'settings': {
            'template_id': 'sexsi_agreement_template',
            'signature_fields': {
                'signer': {
                    'x_position': 100,
                    'y_position': 100,
                    'page_number': 1
                },
                'witness': {
                    'x_position': 200,
                    'y_position': 100,
                    'page_number': 1
                }
            }
        }
    }
}

# Función para obtener todas las categorías de preferencias
# Diccionario de categorías de preferencias
# Define las categorías principales para clasificar preferencias de manera discreta, escalable y adaptable
PREFERENCE_CATEGORIES = {
    "common": {
        "name": "Preferencias Comunes",
        "description": "Interacciones íntimas estándar, aceptadas mutuamente, enfocadas en conexión emocional y física.",
        "level": "básico",
        "order": 1
    },
    "discrete": {
        "name": "Preferencias Discretas",
        "description": "Interacciones personalizadas que requieren confianza, privacidad y comunicación previa.",
        "level": "intermedio",
        "order": 2
    },
    "advanced": {
        "name": "Exploraciones Avanzadas",
        "description": "Interacciones complejas o especializadas que demandan consenso explícito y mayor creatividad.",
        "level": "avanzado",
        "order": 3
    },
    "exotic": {
        "name": "Exploraciones Exóticas",
        "description": "Interacciones únicas o no convencionales que requieren acuerdo detallado y confianza mutua.",
        "level": "especializado",
        "order": 4
    }
}

# Diccionario de prácticas específicas
# Contiene prácticas clasificadas por categoría, con códigos únicos y descripciones abstractas para discreción
PRACTICE_DICTIONARY = {
    # Preferencias Comunes (Básicas)
    "C-01": {
        "code": "C-01",
        "name": "Intimidad Consensual",
        "description": "Interacción íntima estándar entre un hombre y una mujer, enfocada en conexión mutua.",
        "category": "common",
        "complexity_level": "básico"
    },
    "C-02": {
        "code": "C-02",
        "name": "Intimidad Homosexual Masculina Básica",
        "description": "Interacción íntima estándar entre dos hombres, centrada en cercanía emocional y física.",
        "category": "common",
        "complexity_level": "básico"
    },
    "C-03": {
        "code": "C-03",
        "name": "Intimidad Homosexual Femenina Básica",
        "description": "Interacción íntima estándar entre dos mujeres, enfocada en conexión y bienestar.",
        "category": "common",
        "complexity_level": "básico"
    },
    # Preferencias Discretas (Intermedias)
    "D-01": {
        "code": "D-01",
        "name": "Exploración Heterosexual Avanzada",
        "description": "Interacción entre un hombre y una mujer con elementos personalizados que requieren confianza previa.",
        "category": "discrete",
        "complexity_level": "intermedio"
    },
    "D-02": {
        "code": "D-02",
        "name": "Exploración Homosexual Masculina Avanzada",
        "description": "Interacción entre dos hombres con dinámicas personalizadas y mayor grado de privacidad.",
        "category": "discrete",
        "complexity_level": "intermedio"
    },
    "D-03": {
        "code": "D-03",
        "name": "Exploración Homosexual Femenina Avanzada",
        "description": "Interacción entre dos mujeres con enfoques personalizados que respetan límites acordados.",
        "category": "discrete",
        "complexity_level": "intermedio"
    },
    # Exploraciones Avanzadas (Tríos y Dinámicas Grupales)
    "A-01": {
        "code": "A-01",
        "name": "Dinámica de Trío Heterosexual",
        "description": "Interacción consensuada entre tres personas, incluyendo al menos un hombre y una mujer, con coordinación explícita.",
        "category": "advanced",
        "complexity_level": "avanzado"
    },
    "A-02": {
        "code": "A-02",
        "name": "Dinámica de Trío Homosexual",
        "description": "Interacción consensuada entre tres personas del mismo género, con acuerdo detallado de límites.",
        "category": "advanced",
        "complexity_level": "avanzado"
    },
    "A-03": {
        "code": "A-03",
        "name": "Dinámica Grupal Mixta",
        "description": "Interacción consensuada entre múltiples personas de géneros diversos, requiriendo planificación y consenso claro.",
        "category": "advanced",
        "complexity_level": "avanzado"
    },
    # Exploraciones Exóticas (Prácticas No Convencionales)
    "E-01": {
        "code": "E-01",
        "name": "Experiencia Sensorial Única",
        "description": "Interacción que explora estímulos sensoriales no convencionales, acordada con detalle y confianza.",
        "category": "exotic",
        "complexity_level": "especializado"
    },
    "E-02": {
        "code": "E-02",
        "name": "Dinámica de Rol Especializada",
        "description": "Interacción basada en escenarios o roles específicos, requiriendo preparación y consenso explícito.",
        "category": "exotic",
        "complexity_level": "especializado"
    },
    "E-03": {
        "code": "E-03",
        "name": "Exploración de Fantasía Creativa",
        "description": "Interacción que incorpora elementos imaginativos o poco comunes, definida por acuerdo mutuo.",
        "category": "exotic",
        "complexity_level": "especializado"
    }
}

# Diccionario de opciones de duración
# Define las categorías de duración del acuerdo, permitiendo claridad y escalabilidad
DURATION_OPTIONS = {
    "single": {
        "name": "Interacción de Una Sola Vez",
        "description": "Un encuentro consensuado único, sin compromiso de continuidad.",
        "level": "puntual",
        "order": 1,
        "duration_options": []  # No tiene opciones de duración adicional
    },
    "short_term": {
        "name": "Acuerdo de Corto Plazo",
        "description": "Una serie de encuentros consensuados durante un período definido, acordado por las partes.",
        "level": "temporal",
        "order": 2,
        "duration_options": [
            {
                "unit": "days",
                "min": 1,
                "max": 7,
                "step": 1,
                "label": "Días",
                "description": "Duración de 1 a 7 días"
            },
            {
                "unit": "weeks",
                "min": 1,
                "max": 4,
                "step": 1,
                "label": "Semanas",
                "description": "Duración de 1 a 4 semanas"
            },
            {
                "unit": "months",
                "min": 1,
                "max": 3,
                "step": 1,
                "label": "Meses",
                "description": "Duración de 1 a 3 meses"
            }
        ]
    },
    "long_term": {
        "name": "Acuerdo de Largo Plazo",
        "description": "Un compromiso consensuado continuo, con posibilidad de renovación o ajuste periódico.",
        "level": "permanente",
        "order": 3,
        "duration_options": [
            {
                "unit": "months",
                "min": 6,
                "max": 12,
                "step": 1,
                "label": "Meses",
                "description": "Duración de 6 a 12 meses"
            },
            {
                "unit": "years",
                "min": 1,
                "max": 5,
                "step": 1,
                "label": "Años",
                "description": "Duración de 1 a 5 años"
            }
        ]
    }
}

# Función para obtener la configuración de un tipo de documento
def get_document_config(document_type: str) -> Dict[str, Any]:
    """
    Obtiene la configuración para un tipo específico de documento.
    
    Args:
        document_type: Tipo de documento (ej: 'mutual_agreement', 'consent_agreement')
        
    Returns:
        Configuración del documento
    """
    return SEXSI_SIGNATURE_CONFIG['document_types'].get(document_type, {})

# Función para validar los campos requeridos de un documento
def validate_document_fields(document_type: str, data: dict) -> bool:
    """
    Valida que se hayan proporcionado todos los campos requeridos para un documento.
    """
    config = get_document_config(document_type)
    if not config:
        return False
        
    required_fields = config.get('required_fields', [])
    for field in required_fields:
        if field not in data:
            return False
    
    return True

def get_preference_categories() -> dict:
    """
    Obtiene todas las categorías de preferencias disponibles.
    """
    return PREFERENCE_CATEGORIES

# Función para obtener las prácticas de una categoría específica
def get_practices_by_category(category_id: str) -> dict:
    """
    Obtiene todas las prácticas de una categoría específica.
    
    Args:
        category_id: ID de la categoría (ej: 'common', 'discrete')
        
    Returns:
        Diccionario con las prácticas de la categoría
    """
    practices = {}
    for practice_id, practice in PRACTICE_DICTIONARY.items():
        if practice['category'] == category_id:
            practices[practice_id] = practice
    return practices

# Función para validar una preferencia
def validate_preference(preference: dict) -> bool:
    """
    Valida que una preferencia sea válida según el diccionario.
    
    Args:
        preference: Diccionario con la preferencia a validar
        
    Returns:
        True si la preferencia es válida, False en caso contrario
    """
    if 'code' not in preference:
        return False
        
    if preference['code'] not in PRACTICE_DICTIONARY:
        return False
        
    practice = PRACTICE_DICTIONARY[preference['code']]
    
    # Validar que la categoría coincida
    if preference.get('category') and preference['category'] != practice['category']:
        return False
        
    return True

# Función para obtener la información completa de una práctica por su código
def get_practice_info(practice_code: str) -> dict:
    """
    Obtiene la información completa de una práctica por su código.
    
    Args:
        practice_code: Código de la práctica (ej: 'C-01')
        
    Returns:
        Diccionario con la información de la práctica
    """
    return PRACTICE_DICTIONARY.get(practice_code, {})
