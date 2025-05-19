# /home/pablo/app/pricing/config.py
import os
from django.conf import settings

# Configuración de paths
PROPOSAL_TEMPLATES_DIR = os.path.join(settings.BASE_DIR, 'app/templates/pricing')
PROPOSAL_PDF_DIR = os.path.join(settings.MEDIA_ROOT, 'proposals/pdfs')
PROPOSAL_IMAGES_DIR = os.path.join(settings.MEDIA_ROOT, 'proposals/images')

# Configuración de plantillas
TEMPLATE_CONFIG = {
    'html': 'proposal_template.html',
    'pdf': 'proposal_pdf_template.html',
    'sections': {
        'header': 'templates/proposal_header.html',
        'job_description': 'templates/proposal_job_description.html',
        'pricing': 'templates/proposal_pricing.html',
        'company_info': 'templates/proposal_company_info.html',
        'consultant_info': 'templates/proposal_consultant_info.html'
    }
}

# Configuración de PDF
PDF_CONFIG = {
    'stylesheets': [
        os.path.join(PROPOSAL_TEMPLATES_DIR, 'styles/proposal.css'),
        os.path.join(PROPOSAL_TEMPLATES_DIR, 'styles/pricing.css')
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
