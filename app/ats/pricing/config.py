# /home/pablo/app/com/pricing/config.py
"""
Configuración para el módulo de pricing de Grupo huntRED®.

Este archivo contiene la configuración para la generación de propuestas,
plantillas, secciones reutilizables, y ajustes de PDF. Permite crear
propuestas modularizadas y personalizadas por Business Unit.
"""

import os
from django.conf import settings
from app.config import settings as global_settings

# Configuración de directorios
PROPOSAL_TEMPLATES_DIR = os.path.join(settings.BASE_DIR, 'app/templates/proposals')
PROPOSAL_SECTIONS_DIR = os.path.join(PROPOSAL_TEMPLATES_DIR, 'sections')
PROPOSAL_PDF_DIR = os.path.join(settings.MEDIA_ROOT, 'proposals/pdfs')
PROPOSAL_IMAGES_DIR = os.path.join(settings.MEDIA_ROOT, 'proposals/images')
ASSETS_DIR = os.path.join(settings.STATIC_ROOT, 'img/proposals')

# Secciones disponibles para propuestas modulares
AVAILABLE_SECTIONS = {
    'cover': 'sections/cover.html',
    'header': 'sections/header.html',
    'introduction': 'sections/introduction.html',
    'service_description': 'sections/service_description.html',
    'pricing': 'sections/pricing.html',
    'benefits': 'sections/benefits.html',
    'methodology': 'sections/methodology.html',
    'timeline': 'sections/timeline.html',
    'testimonials': 'sections/testimonials.html',
    'team': 'sections/team.html',
    'terms': 'sections/terms.html',
    'footer': 'sections/footer.html',
}

# Plantillas base para diferentes tipos de propuestas
BASE_TEMPLATES = {
    'standard': 'base_proposal.html',
    'detailed': 'detailed_proposal.html',
    'executive': 'executive_proposal.html',
    'talent_360': 'talent_360_proposal.html',
}

# Configuraciones predefinidas para diferentes tipos de propuestas
PROPOSAL_PRESETS = {
    'recruitment': {
        'template': 'standard',
        'sections': ['cover', 'header', 'introduction', 'service_description', 'pricing', 'terms', 'footer'],
    },
    'talent_360': {
        'template': 'talent_360',
        'sections': ['cover', 'header', 'introduction', 'service_description', 'methodology', 'pricing', 'benefits', 'terms', 'footer'],
    },
    'executive_search': {
        'template': 'executive',
        'sections': ['cover', 'header', 'introduction', 'service_description', 'team', 'methodology', 'pricing', 'testimonials', 'terms', 'footer'],
    },
    'hr_consulting': {
        'template': 'detailed',
        'sections': ['cover', 'header', 'introduction', 'service_description', 'methodology', 'timeline', 'pricing', 'team', 'benefits', 'terms', 'footer'],
    },
}

# Configuración específica por Business Unit
BU_PROPOSAL_CONFIG = {
    'huntRED': {
        'logo_path': os.path.join(ASSETS_DIR, 'huntRED-logo.png'),
        'color_scheme': {
            'primary': '#1f3544',  # hunt-blue
            'secondary': '#ff3300',  # hunt-red
            'accent': '#3498db',
        },
        'layout': 'standard',
    },
    'huntU': {
        'logo_path': os.path.join(ASSETS_DIR, 'huntU-logo.png'),
        'color_scheme': {
            'primary': '#1f3544',  # hunt-blue
            'secondary': '#ff3300',  # hunt-red
            'accent': '#27ae60',
        },
        'layout': 'standard',
    },
    'Amigro': {
        'logo_path': os.path.join(ASSETS_DIR, 'amigro-logo.png'),
        'color_scheme': {
            'primary': '#1f3544',  # hunt-blue
            'secondary': '#ff3300',  # hunt-red
            'accent': '#f1c40f',
        },
        'layout': 'standard',
    },
    'SEXSI': {
        'logo_path': os.path.join(ASSETS_DIR, 'sexsi-logo.png'),
        'color_scheme': {
            'primary': '#1f3544',  # hunt-blue
            'secondary': '#ff3300',  # hunt-red
            'accent': '#9b59b6',
        },
        'layout': 'detailed',
    },
}

# Configuración de PDF
PDF_CONFIG = {
    'stylesheets': [
        os.path.join(settings.STATIC_ROOT, 'css/proposals/base.css'),
        os.path.join(settings.STATIC_ROOT, 'css/proposals/print.css')
    ],
    'options': {
        'page-size': 'A4',
        'margin-top': '20mm',
        'margin-right': '20mm',
        'margin-bottom': '20mm',
        'margin-left': '20mm',
        'encoding': 'UTF-8',
        'no-outline': None,
        'disable-smart-shrinking': False,
        'dpi': 300
    }
}

# Configuración de caché
CACHE_CONFIG = {
    'enabled': True,
    'timeout': 3600,  # 1 hora
    'key_prefix': 'proposal_',
    'sections': {
        'templates': 'proposal_templates_',
        'pricing': 'proposal_pricing_',
        'content': 'proposal_content_'
    }
}

# Configuración de IA
AI_CONFIG = {
    'providers': {
        'grok': {
            'enabled': True,
            'prompt_template': os.path.join(PROPOSAL_TEMPLATES_DIR, 'prompts/grok_prompt.txt'),
            'max_tokens': 1500,
            'temperature': 0.7
        },
        'openai': {
            'enabled': True,
            'model': 'gpt-4',
            'max_tokens': 2000,
            'temperature': 0.7
        }
    }
}

# Configuración de optimización
OPTIMIZATION_CONFIG = {
    'pdf': {
        'compression': True,
        'image_quality': 85,
        'font_subsetting': True
    },
    'html': {
        'minify': True,
        'remove_comments': True,
        'remove_empty_elements': True
    }
}

# Exportar la configuración de precios
PRICING_CONFIG = global_settings.pricing

# Exportar configuraciones específicas
PROGRESSIVE_CONFIG = PRICING_CONFIG.progressive
VOLUME_CONFIG = PRICING_CONFIG.volume
PROPOSAL_CONFIG = PRICING_CONFIG.proposal
TRACKING_CONFIG = PRICING_CONFIG.tracking
NOTIFICATION_CONFIG = PRICING_CONFIG.notifications
VALIDATION_CONFIG = PRICING_CONFIG.validation
SECURITY_CONFIG = PRICING_CONFIG.security
CACHE_CONFIG = PRICING_CONFIG.cache
LOGGING_CONFIG = PRICING_CONFIG.logging

# Exportar funciones de utilidad
def get_tier_config(tier_name: str):
    """Obtiene la configuración de un nivel específico."""
    return PRICING_CONFIG.get_tier_config(tier_name)

def get_volume_tier_config(tier_name: str):
    """Obtiene la configuración de un nivel de volumen específico."""
    return PRICING_CONFIG.get_volume_tier_config(tier_name)

def get_template_config(template: str):
    """Obtiene la configuración de una plantilla específica."""
    return PRICING_CONFIG.get_template_config(template)

def is_template_enabled(template: str) -> bool:
    """Verifica si una plantilla está habilitada."""
    return PRICING_CONFIG.is_template_enabled(template)

def calculate_progressive_price(volume: int) -> float:
    """Calcula el precio progresivo para un volumen dado."""
    return PRICING_CONFIG.calculate_progressive_price(volume)

def calculate_volume_price(volume: int) -> float:
    """Calcula el precio por volumen para un volumen dado."""
    return PRICING_CONFIG.calculate_volume_price(volume)

# Exportar todo
__all__ = [
    'PRICING_CONFIG',
    'PROGRESSIVE_CONFIG',
    'VOLUME_CONFIG',
    'PROPOSAL_CONFIG',
    'TRACKING_CONFIG',
    'NOTIFICATION_CONFIG',
    'VALIDATION_CONFIG',
    'SECURITY_CONFIG',
    'CACHE_CONFIG',
    'LOGGING_CONFIG',
    'get_tier_config',
    'get_volume_tier_config',
    'get_template_config',
    'is_template_enabled',
    'calculate_progressive_price',
    'calculate_volume_price'
]
