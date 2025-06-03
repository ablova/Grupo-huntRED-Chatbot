import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.cache import cache
from django.core.files.storage import default_storage
from weasyprint import HTML, CSS
from app.models import Proposal, Company, Vacante, Person, BusinessUnit
from app.ats.chatbot.gpt import GPTHandler
from app.ats.pricing.config import (
    PROPOSAL_TEMPLATES_DIR, PROPOSAL_PDF_DIR, PDF_CONFIG,
    CACHE_CONFIG, AI_CONFIG, OPTIMIZATION_CONFIG
)

logger = logging.getLogger(__name__)

class ProposalGenerator:
    def __init__(self):
        self.gpt_handler = GPTHandler()
        self.cache = cache
        self._ensure_directories()

    def _ensure_directories(self):
        """Asegura que los directorios necesarios existan"""
        required_dirs = [
            PROPOSAL_TEMPLATES_DIR,
            PROPOSAL_PDF_DIR,
            os.path.join(PROPOSAL_TEMPLATES_DIR, 'styles'),
            os.path.join(PROPOSAL_TEMPLATES_DIR, 'images'),
            os.path.join(PROPOSAL_TEMPLATES_DIR, 'prompts')
        ]
        
        for directory in required_dirs:
            os.makedirs(directory, exist_ok=True)

    async def generate_ai_introduction(self, company: Company, vacancies: List[Vacante]) -> str:
        """Genera una introducción personalizada usando IA"""
        prompt_data = {
            'company': {
                'name': company.name,
                'industry': company.industry,
                'size': company.size,
                'description': company.description
            },
            'vacancies': [{
                'title': v.title,
                'description': v.description,
                'requirements': v.requirements
            } for v in vacancies]
        }

        prompt = await self._load_prompt('grok_prompt.txt')
        formatted_prompt = prompt.format(**prompt_data)

        try:
            response = await self.gpt_handler.generate_response(
                formatted_prompt,
                business_unit=BusinessUnit.objects.first()  # TODO: Obtener BU correcto
            )
            return response
        except Exception as e:
            logger.error(f"Error generating AI introduction: {str(e)}")
            return ""

    async def _load_prompt(self, filename: str) -> str:
        """Carga un prompt desde archivo"""
        path = os.path.join(PROPOSAL_TEMPLATES_DIR, 'prompts', filename)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _generate_pricing_details(self, proposal: Proposal) -> Dict:
        """Genera los detalles de pricing"""
        pricing_details = {
            'total': 0,
            'items': []
        }

        for vacancy in proposal.vacancies.all():
            bu = vacancy.business_unit
            base_price = self._calculate_base_price(vacancy, bu)
            addons = self._calculate_addons(vacancy, bu)
            
            item_total = base_price + sum(addon['price'] for addon in addons)
            
            pricing_details['items'].append({
                'vacancy': vacancy,
                'bu': bu,
                'base': base_price,
                'addons': addons,
                'total': item_total
            })
            
            pricing_details['total'] += item_total

        return pricing_details

    def _calculate_base_price(self, vacancy: Vacante, bu: BusinessUnit) -> float:
        """Calcula el precio base"""
        if bu.pricing_config.get('base_type') == 'percentage':
            return float(vacancy.salary) * (float(bu.pricing_config.get('base_rate', '0')) / 100)
        return float(bu.pricing_config.get('base_rate', '0'))

    def _calculate_addons(self, vacancy: Vacante, bu: BusinessUnit) -> List[Dict]:
        """Calcula los addons para una vacante"""
        addons = []
        for addon_name, config in bu.pricing_config.get('addons', {}).items():
            addon_price = 0
            if config.get('type') == 'percentage':
                addon_price = float(vacancy.salary) * (float(config.get('rate', '0')) / 100)
            else:
                addon_price = float(config.get('amount', '0'))
            
            addons.append({
                'name': addon_name,
                'description': config.get('description', ''),
                'price': addon_price
            })
        return addons

    async def generate_proposal(self, proposal_id: int) -> Dict:
        """Genera una propuesta completa"""
        proposal = Proposal.objects.get(id=proposal_id)
        company = proposal.company
        vacancies = list(proposal.vacancies.all())
        
        # Generar introducción con IA
        ai_introduction = await self.generate_ai_introduction(company, vacancies)
        
        # Generar detalles de pricing
        pricing_details = self._generate_pricing_details(proposal)
        
        # Preparar contexto para renderizado
        context = {
            'company': company,
            'vacancies': vacancies,
            'pricing_details': pricing_details,
            'ai_introduction': ai_introduction,
            'today': timezone.now().strftime("%Y-%m-%d"),
            'proposal': proposal,
            'contact_person': proposal.contact_person,
            'consultant': proposal.consultant
        }
        
        # Renderizar plantilla HTML
        html_content = render_to_string('pricing/proposal_template.html', context)
        
        # Convertir a PDF
        pdf_path = await self.convert_to_pdf(html_content, proposal.id)
        
        return {
            'html': html_content,
            'pdf': pdf_path,
            'pricing_details': pricing_details
        }

    async def convert_to_pdf(self, html_content: str, proposal_id: int) -> str:
        """Convierte HTML a PDF"""
        # Optimizar HTML
        optimized_html = self._optimize_html(html_content)
        
        # Generar nombre de archivo
        filename = f"proposal_{proposal_id}_{timezone.now().strftime('%Y%m%d')}.pdf"
        output_path = os.path.join(PROPOSAL_PDF_DIR, filename)
        
        # Convertir a PDF
        HTML(string=optimized_html).write_pdf(
            output_path,
            stylesheets=PDF_CONFIG['stylesheets'],
            presentational_hints=True,
            **PDF_CONFIG['options']
        )
        
        return output_path

    def _optimize_html(self, html_content: str) -> str:
        """Optimiza el HTML para la conversión a PDF"""
        # TODO: Implementar optimizaciones específicas
        return html_content

    def _cache_key(self, proposal_id: int, section: str) -> str:
        """Genera una clave de caché"""
        return f"{CACHE_CONFIG['key_prefix']}{section}_{proposal_id}"

    async def get_cached_proposal(self, proposal_id: int) -> Optional[Dict]:
        """Obtiene una propuesta desde caché"""
        cache_key = self._cache_key(proposal_id, 'content')
        return self.cache.get(cache_key)

    async def cache_proposal(self, proposal_id: int, data: Dict):
        """Almacena una propuesta en caché"""
        cache_key = self._cache_key(proposal_id, 'content')
        self.cache.set(cache_key, data, timeout=CACHE_CONFIG['timeout'])
