# /home/pablo/app/ats/pricing/proposal_generator.py
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.cache import cache
from django.core.files.storage import default_storage
from weasyprint import HTML, CSS
from app.models import Proposal, Company, Vacante, Person, BusinessUnit, PremiumAddon
from app.ats.chatbot.core.gpt import GPTHandler
from app.ats.pricing.config import (
    PROPOSAL_TEMPLATES_DIR, PROPOSAL_PDF_DIR, PDF_CONFIG,
    CACHE_CONFIG, AI_CONFIG, OPTIMIZATION_CONFIG
)
from app.ats.pricing.strategy import PricingStrategy

logger = logging.getLogger(__name__)

class ProposalGenerator:
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.addons = self._get_available_addons()
        self.gpt_handler = GPTHandler()
        self.cache = cache
        self.pricing_strategy = PricingStrategy()
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
                business_unit=self.business_unit
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

    def _get_available_addons(self) -> List[Dict[str, Any]]:
        """Obtiene addons disponibles para la propuesta"""
        return [
            {
                'name': addon.name,
                'type': addon.type,
                'description': addon.description,
                'price': addon.price,
                'features': self._get_addon_features(addon)
            }
            for addon in PremiumAddon.objects.filter(is_active=True)
        ]
    
    def _get_addon_features(self, addon: PremiumAddon) -> List[str]:
        """Obtiene características del addon según su tipo"""
        features = {
            PremiumAddon.AddonType.MARKET_REPORT: [
                'Reportes mensuales de tendencias de mercado',
                'Análisis de demanda por habilidad',
                'Benchmarks de competencia',
                'Recomendaciones estratégicas'
            ],
            PremiumAddon.AddonType.SALARY_BENCHMARK: [
                'Actualización trimestral de salarios',
                'Análisis por ubicación y seniority',
                'Tendencias salariales por industria',
                'Recomendaciones de ajuste salarial'
            ],
            PremiumAddon.AddonType.LEARNING_ANALYTICS: [
                'Análisis de gaps de habilidades',
                'Rutas de aprendizaje personalizadas',
                'Recomendaciones de cursos',
                'Seguimiento de progreso'
            ],
            PremiumAddon.AddonType.ORGANIZATIONAL_ANALYSIS: [
                'Análisis anual de estructura organizacional',
                'Mapa de competencias',
                'Plan de sucesión',
                'Recomendaciones de desarrollo'
            ]
        }
        return features.get(addon.type, [])

    async def generate_proposal(self) -> Dict[str, Any]:
        """Genera propuesta completa"""
        try:
            # Obtener addons disponibles
            addons = await self._get_available_addons()
            
            # Generar estrategias de precios
            pricing_strategies = await self._get_pricing_strategies(addons)
            
            # Generar secciones de propuesta
            sections = await self._generate_sections(addons, pricing_strategies)
            
            return {
                'business_unit': self.business_unit.id,
                'generated_at': datetime.now(),
                'addons': addons,
                'pricing_strategies': pricing_strategies,
                'sections': sections
            }
            
        except Exception as e:
            self.logger.error(f"Error generando propuesta: {str(e)}")
            return None
    
    async def _get_pricing_strategies(
        self,
        addons: List[PremiumAddon]
    ) -> Dict[str, Any]:
        """Obtiene estrategias de precios para cada addon"""
        strategies = {}
        
        for addon in addons:
            strategy = await self.pricing_strategy.get_pricing_strategy(
                addon=addon,
                business_unit=self.business_unit
            )
            strategies[addon.id] = strategy
        
        return strategies
    
    async def _generate_sections(
        self,
        addons: List[PremiumAddon],
        pricing_strategies: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Genera secciones de la propuesta"""
        sections = []
        
        # Sección de valor
        sections.append(self._generate_value_section(addons))
        
        # Sección de precios
        sections.append(self._generate_pricing_section(
            addons,
            pricing_strategies
        ))
        
        # Sección de activación
        sections.append(self._generate_activation_section(
            addons,
            pricing_strategies
        ))
        
        return sections
    
    def _generate_value_section(
        self,
        addons: List[PremiumAddon]
    ) -> Dict[str, Any]:
        """Genera sección de valor"""
        return {
            'title': 'Valor y Beneficios',
            'content': [
                {
                    'addon_id': addon.id,
                    'name': addon.name,
                    'description': addon.description,
                    'benefits': self._get_addon_benefits(addon),
                    'roi': self._calculate_addon_roi(addon)
                }
                for addon in addons
            ]
        }
    
    def _generate_pricing_section(
        self,
        addons: List[PremiumAddon],
        pricing_strategies: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Genera sección de precios"""
        return {
            'title': 'Estrategia de Precios',
            'content': [
                {
                    'addon_id': addon.id,
                    'name': addon.name,
                    'base_price': addon.price,
                    'final_price': pricing_strategies[addon.id]['final_strategy']['final_price'],
                    'discounts': pricing_strategies[addon.id]['discount_strategy'],
                    'referral_fees': pricing_strategies[addon.id]['referral_strategy']
                }
                for addon in addons
            ]
        }
    
    def _generate_activation_section(
        self,
        addons: List[PremiumAddon],
        pricing_strategies: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Genera sección de activación"""
        return {
            'title': 'Plan de Activación',
            'content': [
                {
                    'addon_id': addon.id,
                    'name': addon.name,
                    'activation_plan': pricing_strategies[addon.id]['final_strategy']['activation_plan'],
                    'success_metrics': pricing_strategies[addon.id]['final_strategy']['success_metrics']
                }
                for addon in addons
            ]
        }
    
    def _get_addon_benefits(self, addon: PremiumAddon) -> List[str]:
        """Obtiene beneficios del addon"""
        # Implementar lógica real
        return []
    
    def _calculate_addon_roi(self, addon: PremiumAddon) -> Dict[str, Any]:
        """Calcula ROI del addon"""
        # Implementar lógica real
        return {
            'estimated_roi': 0,
            'payback_period': 0,
            'risk_level': 'low'
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
