"""
Servicio de Venta Cruzada - huntRED® Payroll
Integra Payroll con ATS y AURA para maximizar el valor del cliente
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.contrib.auth.models import User
from ..models import Company, Employee, PayrollPlan
from .. import PAYROLL_PRICING, PREMIUM_SERVICES, AI_SERVICES
from app.ats.pricing import PricingService as ATSPricingService
from app.ats.pricing.models import PricingStrategy, PricePoint, DiscountRule


class CrossSellService:
    """
    Servicio para manejar venta cruzada entre Payroll, ATS y AURA
    """
    
    def __init__(self, company: Optional[Company] = None):
        self.company = company
        self.ats_pricing_service = ATSPricingService()
    
    def get_cross_sell_opportunities(self, company: Company) -> Dict:
        """
        Identifica oportunidades de venta cruzada para una empresa
        """
        opportunities = {
            'ats_opportunities': self._get_ats_opportunities(company),
            'aura_opportunities': self._get_aura_opportunities(company),
            'bundle_opportunities': self._get_bundle_opportunities(company),
            'upgrade_opportunities': self._get_upgrade_opportunities(company),
            'recommendations': self._get_cross_sell_recommendations(company)
        }
        
        return opportunities
    
    def _get_ats_opportunities(self, company: Company) -> Dict:
        """
        Identifica oportunidades de ATS basadas en el perfil de la empresa
        """
        employee_count = company.employees.count()
        industry = company.industry
        current_plan = company.payroll_plan
        
        opportunities = {
            'recruitment_services': {
                'priority': 'high' if employee_count > 50 else 'medium',
                'reasoning': f'Empresa con {employee_count} empleados necesita reclutamiento eficiente',
                'estimated_value': self._calculate_ats_value(employee_count, 'recruitment'),
                'discount_available': 0.20,  # 20% descuento para clientes de Payroll
                'features': [
                    'ATS inteligente con IA',
                    'Integración con LinkedIn y Indeed',
                    'Evaluación automatizada de candidatos',
                    'Onboarding digital',
                    'Analytics de reclutamiento'
                ]
            },
            'talent_management': {
                'priority': 'high' if employee_count > 100 else 'medium',
                'reasoning': 'Gestión integral del talento para empresas en crecimiento',
                'estimated_value': self._calculate_ats_value(employee_count, 'talent_management'),
                'discount_available': 0.25,  # 25% descuento para clientes de Payroll
                'features': [
                    'Gestión de performance',
                    'Planes de carrera',
                    'Evaluación 360°',
                    'Desarrollo de competencias',
                    'Succession planning'
                ]
            },
            'executive_search': {
                'priority': 'medium' if employee_count > 200 else 'low',
                'reasoning': 'Búsqueda de ejecutivos para empresas establecidas',
                'estimated_value': self._calculate_ats_value(employee_count, 'executive_search'),
                'discount_available': 0.15,  # 15% descuento para clientes de Payroll
                'features': [
                    'Búsqueda de ejecutivos',
                    'Evaluación de competencias',
                    'Assessment center',
                    'Onboarding ejecutivo',
                    'Consultoría de liderazgo'
                ]
            }
        }
        
        return opportunities
    
    def _get_aura_opportunities(self, company: Company) -> Dict:
        """
        Identifica oportunidades de AURA (IA conversacional) basadas en el perfil
        """
        employee_count = company.employees.count()
        industry = company.industry
        
        opportunities = {
            'chatbot_hr': {
                'priority': 'high' if employee_count > 30 else 'medium',
                'reasoning': 'Chatbot de RRHH para automatizar consultas frecuentes',
                'estimated_value': self._calculate_aura_value(employee_count, 'chatbot_hr'),
                'discount_available': 0.30,  # 30% descuento para clientes de Payroll
                'features': [
                    'Chatbot 24/7 para empleados',
                    'Respuestas automáticas a consultas HR',
                    'Integración con WhatsApp',
                    'Analytics de consultas',
                    'Personalización por empresa'
                ]
            },
            'recruitment_chatbot': {
                'priority': 'high' if employee_count > 50 else 'medium',
                'reasoning': 'Chatbot de reclutamiento para mejorar candidate experience',
                'estimated_value': self._calculate_aura_value(employee_count, 'recruitment_chatbot'),
                'discount_available': 0.25,  # 25% descuento para clientes de Payroll
                'features': [
                    'Chatbot de reclutamiento',
                    'Screening automático de candidatos',
                    'Agendamiento de entrevistas',
                    'Feedback automático',
                    'Integración con ATS'
                ]
            },
            'customer_service_chatbot': {
                'priority': 'medium' if company.has_customer_service else 'low',
                'reasoning': 'Chatbot de atención al cliente para mejorar CX',
                'estimated_value': self._calculate_aura_value(employee_count, 'customer_service'),
                'discount_available': 0.20,  # 20% descuento para clientes de Payroll
                'features': [
                    'Chatbot de atención al cliente',
                    'Integración con CRM',
                    'Escalamiento inteligente',
                    'Analytics de satisfacción',
                    'Multiidioma'
                ]
            }
        }
        
        return opportunities
    
    def _get_bundle_opportunities(self, company: Company) -> Dict:
        """
        Identifica oportunidades de bundling (paquetes integrados)
        """
        employee_count = company.employees.count()
        current_plan = company.payroll_plan
        
        bundles = {
            'payroll_ats_bundle': {
                'name': 'Payroll + ATS Bundle',
                'description': 'Solución integral de nómina y reclutamiento',
                'original_price': self._calculate_bundle_price(employee_count, ['payroll', 'ats']),
                'bundle_price': self._calculate_bundle_price(employee_count, ['payroll', 'ats']) * 0.85,  # 15% descuento
                'savings': self._calculate_bundle_price(employee_count, ['payroll', 'ats']) * 0.15,
                'features': [
                    'Nómina completa con compliance automático',
                    'ATS inteligente con IA',
                    'Integración perfecta entre sistemas',
                    'Dashboard unificado',
                    'Soporte dedicado'
                ],
                'priority': 'high' if employee_count > 25 else 'medium'
            },
            'payroll_aura_bundle': {
                'name': 'Payroll + AURA Bundle',
                'description': 'Nómina con IA conversacional integrada',
                'original_price': self._calculate_bundle_price(employee_count, ['payroll', 'aura']),
                'bundle_price': self._calculate_bundle_price(employee_count, ['payroll', 'aura']) * 0.80,  # 20% descuento
                'savings': self._calculate_bundle_price(employee_count, ['payroll', 'aura']) * 0.20,
                'features': [
                    'Nómina completa',
                    'Chatbot de RRHH 24/7',
                    'WhatsApp integrado',
                    'Analytics predictivo',
                    'Compliance automático'
                ],
                'priority': 'high' if employee_count > 20 else 'medium'
            },
            'complete_solution_bundle': {
                'name': 'Complete Solution Bundle',
                'description': 'Payroll + ATS + AURA - Solución completa',
                'original_price': self._calculate_bundle_price(employee_count, ['payroll', 'ats', 'aura']),
                'bundle_price': self._calculate_bundle_price(employee_count, ['payroll', 'ats', 'aura']) * 0.75,  # 25% descuento
                'savings': self._calculate_bundle_price(employee_count, ['payroll', 'ats', 'aura']) * 0.25,
                'features': [
                    'Nómina completa con compliance',
                    'ATS inteligente',
                    'Chatbots de RRHH y reclutamiento',
                    'Dashboard unificado',
                    'Analytics avanzado',
                    'Soporte premium 24/7'
                ],
                'priority': 'high' if employee_count > 50 else 'medium'
            }
        }
        
        return bundles
    
    def _get_upgrade_opportunities(self, company: Company) -> Dict:
        """
        Identifica oportunidades de upgrade dentro del mismo servicio
        """
        current_plan = company.payroll_plan
        employee_count = company.employees.count()
        
        upgrades = {}
        
        # Upgrades de Payroll
        if current_plan == 'starter' and employee_count > 30:
            upgrades['payroll_professional'] = {
                'from_plan': 'starter',
                'to_plan': 'professional',
                'additional_cost': self._calculate_upgrade_cost(employee_count, 'starter', 'professional'),
                'additional_features': [
                    'Analytics predictivo',
                    'Compliance automático',
                    'Workflow automation',
                    'Multi-país',
                    'API access'
                ],
                'roi_improvement': 0.40  # 40% mejora en ROI
            }
        
        if current_plan in ['starter', 'professional'] and employee_count > 100:
            upgrades['payroll_enterprise'] = {
                'from_plan': current_plan,
                'to_plan': 'enterprise',
                'additional_cost': self._calculate_upgrade_cost(employee_count, current_plan, 'enterprise'),
                'additional_features': [
                    'White label options',
                    'Custom development',
                    'Priority support',
                    'Advanced dashboard',
                    'Dedicated account manager'
                ],
                'roi_improvement': 0.60  # 60% mejora en ROI
            }
        
        return upgrades
    
    def _get_cross_sell_recommendations(self, company: Company) -> List[Dict]:
        """
        Genera recomendaciones personalizadas de venta cruzada
        """
        employee_count = company.employees.count()
        industry = company.industry
        current_plan = company.payroll_plan
        
        recommendations = []
        
        # Recomendación 1: ATS para empresas en crecimiento
        if employee_count > 25 and not company.has_ats:
            recommendations.append({
                'type': 'ats',
                'priority': 'high',
                'title': 'Implementar ATS Inteligente',
                'description': f'Con {employee_count} empleados, necesitas un ATS para optimizar el reclutamiento',
                'estimated_roi': 0.300,  # 300% ROI
                'implementation_time': '2-4 semanas',
                'discount': 0.20
            })
        
        # Recomendación 2: AURA para mejorar experiencia de empleados
        if employee_count > 30:
            recommendations.append({
                'type': 'aura',
                'priority': 'high',
                'title': 'Chatbot de RRHH con AURA',
                'description': 'Automatiza consultas frecuentes y mejora la experiencia de empleados',
                'estimated_roi': 0.250,  # 250% ROI
                'implementation_time': '1-2 semanas',
                'discount': 0.30
            })
        
        # Recomendación 3: Bundle completo para empresas medianas
        if employee_count > 50:
            recommendations.append({
                'type': 'bundle',
                'priority': 'high',
                'title': 'Solución Completa huntRED',
                'description': 'Payroll + ATS + AURA - Todo integrado con 25% descuento',
                'estimated_roi': 0.400,  # 400% ROI
                'implementation_time': '4-6 semanas',
                'discount': 0.25
            })
        
        # Recomendación 4: Upgrade de plan para más funcionalidades
        if current_plan == 'starter' and employee_count > 40:
            recommendations.append({
                'type': 'upgrade',
                'priority': 'medium',
                'title': 'Upgrade a Professional',
                'description': 'Accede a analytics predictivo y compliance automático',
                'estimated_roi': 0.200,  # 200% ROI
                'implementation_time': '1 semana',
                'discount': 0.10
            })
        
        return recommendations
    
    def _calculate_ats_value(self, employee_count: int, service_type: str) -> float:
        """
        Calcula el valor estimado de servicios ATS
        """
        base_prices = {
            'recruitment': 15.0,  # USD por empleado/mes
            'talent_management': 12.0,  # USD por empleado/mes
            'executive_search': 25.0,  # USD por empleado/mes
        }
        
        base_price = base_prices.get(service_type, 15.0)
        
        # Descuentos por volumen
        if employee_count > 100:
            base_price *= 0.85
        elif employee_count > 50:
            base_price *= 0.90
        
        return base_price * employee_count
    
    def _calculate_aura_value(self, employee_count: int, service_type: str) -> float:
        """
        Calcula el valor estimado de servicios AURA
        """
        base_prices = {
            'chatbot_hr': 8.0,  # USD por empleado/mes
            'recruitment_chatbot': 6.0,  # USD por empleado/mes
            'customer_service': 10.0,  # USD por empleado/mes
        }
        
        base_price = base_prices.get(service_type, 8.0)
        
        # Descuentos por volumen
        if employee_count > 100:
            base_price *= 0.80
        elif employee_count > 50:
            base_price *= 0.85
        
        return base_price * employee_count
    
    def _calculate_bundle_price(self, employee_count: int, services: List[str]) -> float:
        """
        Calcula el precio de un bundle de servicios
        """
        total_price = 0.0
        
        for service in services:
            if service == 'payroll':
                # Usar precio actual de Payroll
                plan_data = PAYROLL_PRICING['professional']
                total_price += plan_data['price_per_employee'] * employee_count + plan_data['monthly_base_fee']
            elif service == 'ats':
                total_price += self._calculate_ats_value(employee_count, 'recruitment')
            elif service == 'aura':
                total_price += self._calculate_aura_value(employee_count, 'chatbot_hr')
        
        return total_price
    
    def _calculate_upgrade_cost(self, employee_count: int, from_plan: str, to_plan: str) -> float:
        """
        Calcula el costo adicional de un upgrade
        """
        from_plan_data = PAYROLL_PRICING[from_plan]
        to_plan_data = PAYROLL_PRICING[to_plan]
        
        from_price = from_plan_data['price_per_employee'] * employee_count + from_plan_data['monthly_base_fee']
        to_price = to_plan_data['price_per_employee'] * employee_count + to_plan_data['monthly_base_fee']
        
        return to_price - from_price
    
    def create_cross_sell_proposal(self, company: Company, opportunities: Dict) -> Dict:
        """
        Crea una propuesta de venta cruzada personalizada
        """
        proposal = {
            'company_info': {
                'name': company.name,
                'employees': company.employees.count(),
                'industry': company.industry,
                'current_plan': company.payroll_plan
            },
            'opportunities': opportunities,
            'total_potential_value': self._calculate_total_potential_value(opportunities),
            'recommended_next_steps': self._get_recommended_next_steps(opportunities),
            'timeline': self._get_implementation_timeline(opportunities),
            'roi_projections': self._get_roi_projections(opportunities)
        }
        
        return proposal
    
    def _calculate_total_potential_value(self, opportunities: Dict) -> float:
        """
        Calcula el valor total potencial de todas las oportunidades
        """
        total_value = 0.0
        
        # Valor de oportunidades ATS
        for opportunity in opportunities.get('ats_opportunities', {}).values():
            total_value += opportunity.get('estimated_value', 0)
        
        # Valor de oportunidades AURA
        for opportunity in opportunities.get('aura_opportunities', {}).values():
            total_value += opportunity.get('estimated_value', 0)
        
        # Valor de bundles
        for bundle in opportunities.get('bundle_opportunities', {}).values():
            total_value += bundle.get('bundle_price', 0)
        
        return total_value
    
    def _get_recommended_next_steps(self, opportunities: Dict) -> List[str]:
        """
        Obtiene los próximos pasos recomendados
        """
        steps = []
        
        # Priorizar por valor y facilidad de implementación
        if opportunities.get('bundle_opportunities'):
            steps.append("Presentar propuesta de bundle completo")
        
        if opportunities.get('ats_opportunities'):
            steps.append("Demo del ATS inteligente")
        
        if opportunities.get('aura_opportunities'):
            steps.append("Demo del chatbot de RRHH")
        
        if opportunities.get('upgrade_opportunities'):
            steps.append("Presentar beneficios del upgrade")
        
        return steps
    
    def _get_implementation_timeline(self, opportunities: Dict) -> Dict:
        """
        Obtiene la línea de tiempo de implementación
        """
        timeline = {
            'week_1': ['Análisis de necesidades', 'Configuración inicial'],
            'week_2': ['Implementación de ATS' if opportunities.get('ats_opportunities') else 'Configuración de AURA'],
            'week_3': ['Configuración de AURA' if opportunities.get('aura_opportunities') else 'Integración de sistemas'],
            'week_4': ['Entrenamiento del equipo', 'Go-live'],
            'week_5': ['Soporte post-implementación', 'Optimización']
        }
        
        return timeline
    
    def _get_roi_projections(self, opportunities: Dict) -> Dict:
        """
        Obtiene proyecciones de ROI
        """
        projections = {
            'month_3': 0.150,  # 15% ROI
            'month_6': 0.300,  # 30% ROI
            'month_12': 0.500,  # 50% ROI
            'year_2': 0.800,   # 80% ROI
        }
        
        return projections 