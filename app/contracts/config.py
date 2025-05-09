import os
from django.conf import settings

# Configuración de paths
CONTRACTS_DIR = os.path.join(settings.MEDIA_ROOT, 'contracts')
SIGNED_CONTRACTS_DIR = os.path.join(CONTRACTS_DIR, 'signed')
TEMP_CONTRACTS_DIR = os.path.join(CONTRACTS_DIR, 'temp')

# Configuración de firma
SIGNATURE_CONFIG = {
    'positions': {
        'client': {
            'x': 0.75,  # Posición X (0.0 - 1.0)
            'y': 0.95,  # Posición Y (0.0 - 1.0)
            'width': 100  # Ancho en pixels
        },
        'consultant': {
            'x': 0.25,
            'y': 0.95,
            'width': 100
        }
    },
    'validation_required': True,
    'superuser_approval_required': True
}

# Configuración de IA para análisis
AI_CONFIG = {
    'enabled': True,
    'providers': {
        'grok': {
            'enabled': True,
            'prompt_template': 'contracts/prompts/contract_analysis_prompt.txt',
            'max_tokens': 1000,
            'temperature': 0.7
        }
    },
    'risk_categories': [
        'Legal Compliance',
        'Financial Terms',
        'Confidentiality',
        'Termination Conditions'
    ]
}

# Configuración de blockchain
BLOCKCHAIN_CONFIG = {
    'enabled': False,  # Deshabilitado por defecto hasta implementación
    'network': 'ethereum',
    'contract_address': '',
    'abi_path': 'contracts/blockchain/contract_abi.json'
}

# Configuración de correo
EMAIL_CONFIG = {
    'subject': 'Solicitud de Firma de Contrato - huntRED',
    'template': 'contracts/emails/signature_request.html',
    'from_email': 'contracts@huntred.com'
}

# Configuración de caché
CACHE_CONFIG = {
    'enabled': True,
    'timeout': 3600,  # 1 hora
    'key_prefix': 'contract_',
    'validation': 'contract_validation_',
    'signature': 'contract_signature_'
}
