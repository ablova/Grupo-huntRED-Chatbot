"""
Servicio de Pricing - huntRED® Payroll
Maneja cálculos de precios, costos, márgenes y análisis de rentabilidad
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from ..models import Company, Employee, PayrollPlan
from .. import PAYROLL_PRICING, PREMIUM_SERVICES, AI_SERVICES, IMPLEMENTATION_SERVICES, VOLUME_DISCOUNTS, COST_BREAKDOWN


class PricingService:
    """
    Servicio para manejar todos los cálculos de pricing y análisis de costos
    """
    
    def __init__(self, company: Optional[Company] = None):
        self.company = company
    
    def calculate_company_pricing(self, 
                                employees: int, 
                                plan: str = 'professional',
                                country: str = 'MX',
                                addons: List[str] = None,
                                setup_type: str = 'standard_setup') -> Dict:
        """
        Calcula el pricing completo para una empresa
        """
        if addons is None:
            addons = []
        
        # Obtener datos del plan
        plan_data = PAYROLL_PRICING[plan]
        
        # Cálculo base
        base_price = plan_data['price_per_employee'] * employees
        setup_fee = plan_data['setup_fee']
        monthly_base_fee = plan_data['monthly_base_fee']
        
        # Descuentos por volumen
        volume_discount = self._calculate_volume_discount(employees)
        discounted_price = base_price * (1 - volume_discount)
        
        # Add-ons
        addon_total = self._calculate_addon_costs(employees, addons)
        
        # Setup fee
        implementation_fee = IMPLEMENTATION_SERVICES[setup_type]['price']
        
        # Totales
        monthly_total = discounted_price + monthly_base_fee + addon_total
        annual_total = monthly_total * 12
        setup_total = setup_fee + implementation_fee
        
        # ROI calculation
        roi_data = self._calculate_roi(employees, annual_total, setup_total)
        
        return {
            'pricing_breakdown': {
                'base_price': float(base_price),
                'volume_discount': float(volume_discount * 100),
                'discounted_price': float(discounted_price),
                'monthly_base_fee': float(monthly_base_fee),
                'addon_total': float(addon_total),
                'monthly_total': float(monthly_total),
                'annual_total': float(annual_total)
            },
            'setup_costs': {
                'plan_setup_fee': float(setup_fee),
                'implementation_fee': float(implementation_fee),
                'total_setup': float(setup_total)
            },
            'roi_analysis': roi_data,
            'plan_details': {
                'plan_name': plan,
                'employees': employees,
                'country': country,
                'addons': addons,
                'setup_type': setup_type
            }
        }
    
    def _calculate_volume_discount(self, employees: int) -> float:
        """
        Calcula el descuento por volumen de empleados
        """
        volume_discount = 0.0
        
        for threshold, discount in VOLUME_DISCOUNTS['employee_discounts'].items():
            threshold_employees = int(threshold.replace('+', ''))
            if employees >= threshold_employees:
                volume_discount = discount
                break
        
        return volume_discount
    
    def _calculate_addon_costs(self, employees: int, addons: List[str]) -> float:
        """
        Calcula el costo total de los add-ons
        """
        addon_total = 0.0
        
        for addon in addons:
            if addon in PREMIUM_SERVICES:
                addon_price = PREMIUM_SERVICES[addon].get('price_per_employee', 0) * employees
                addon_total += addon_price
            elif addon in AI_SERVICES:
                addon_price = AI_SERVICES[addon]['price_per_employee'] * employees
                addon_total += addon_price
        
        # Descuento por múltiples add-ons
        if len(addons) >= 3:
            addon_discount = VOLUME_DISCOUNTS['addon_discounts']['3_addons']
            addon_total *= (1 - addon_discount)
        
        return addon_total
    
    def _calculate_roi(self, employees: int, annual_cost: float, setup_cost: float) -> Dict:
        """
        Calcula el ROI y análisis de ahorro
        """
        # Estimado de ahorro por empleado (basado en eficiencia y automatización)
        cost_savings_per_employee = 50.0  # USD/mes
        annual_savings = cost_savings_per_employee * employees * 12
        
        net_savings = annual_savings - annual_cost
        roi_percentage = ((annual_savings - annual_cost) / annual_cost) * 100 if annual_cost > 0 else 0
        
        # Tiempo de recuperación
        payback_months = (setup_cost / (annual_savings - annual_cost)) * 12 if (annual_savings - annual_cost) > 0 else float('inf')
        
        return {
            'annual_savings': float(annual_savings),
            'annual_cost': float(annual_cost),
            'net_savings': float(net_savings),
            'roi_percentage': float(roi_percentage),
            'payback_months': float(payback_months) if payback_months != float('inf') else 0
        }
    
    def get_profitability_analysis(self) -> Dict:
        """
        Análisis de rentabilidad por plan
        """
        profitability = {}
        
        for plan_name, plan_data in PAYROLL_PRICING.items():
            # Costos mensuales base
            monthly_costs = COST_BREAKDOWN['infrastructure_per_company']['total_monthly']
            
            # Ingresos por empleado
            revenue_per_employee = plan_data['price_per_employee']
            
            # Break even point
            break_even = plan_data['break_even_employees']
            
            # Margen de contribución
            contribution_margin = revenue_per_employee * 0.75  # Estimado
            
            profitability[plan_name] = {
                'monthly_costs': monthly_costs,
                'revenue_per_employee': revenue_per_employee,
                'break_even_employees': break_even,
                'contribution_margin': contribution_margin,
                'profit_margin': plan_data['profit_margin'],
                'monthly_profit_at_break_even': (revenue_per_employee * break_even) - monthly_costs
            }
        
        return profitability
    
    def get_cost_breakdown(self) -> Dict:
        """
        Obtiene el desglose detallado de costos
        """
        return {
            'infrastructure': COST_BREAKDOWN['infrastructure_per_company'],
            'setup_costs': COST_BREAKDOWN['setup_costs'],
            'profit_margins': COST_BREAKDOWN['profit_margins'],
            'monthly_breakdown': {
                'whatsapp_bot': 300.00,
                'ai_servers': 400.00,
                'compliance_automation': 200.00,
                'support': 150.00,
                'backup_storage': 100.00,
                'total': 1150.00
            }
        }
    
    def get_competitive_analysis(self) -> Dict:
        """
        Análisis competitivo vs otros proveedores
        """
        return {
            'runa': {
                'price_per_employee': 45.00,  # USD
                'setup_fee': 0,
                'features': ['basic_payroll', 'basic_reports'],
                'our_advantage': 'WhatsApp + IA + Compliance automático'
            },
            'worky': {
                'price_per_employee': 38.00,  # USD
                'setup_fee': 1000,
                'features': ['payroll', 'hr_management'],
                'our_advantage': 'Analytics predictivo + Workflow automation'
            },
            'contpaqi': {
                'price_per_employee': 25.00,  # USD
                'setup_fee': 5000,
                'features': ['accounting', 'payroll'],
                'our_advantage': 'IA avanzada + Multi-país + WhatsApp'
            },
            'aspel_noi': {
                'price_per_employee': 20.00,  # USD
                'setup_fee': 3000,
                'features': ['payroll', 'basic_reports'],
                'our_advantage': 'Compliance automático + Analytics + Workflows'
            }
        }
    
    def get_revenue_projection(self, scenario: str = 'moderate') -> Dict:
        """
        Proyección de ingresos por diferentes escenarios
        """
        scenarios = {
            'conservative': {
                'companies_month_1': 5,
                'companies_month_6': 25,
                'companies_month_12': 50,
                'avg_employees_per_company': 75,
                'avg_plan': 'professional',
                'avg_monthly_revenue_per_company': 2100,  # USD
                'projected_annual_revenue': 1260000  # USD
            },
            'moderate': {
                'companies_month_1': 10,
                'companies_month_6': 50,
                'companies_month_12': 100,
                'avg_employees_per_company': 100,
                'avg_plan': 'professional',
                'avg_monthly_revenue_per_company': 2800,  # USD
                'projected_annual_revenue': 3360000  # USD
            },
            'aggressive': {
                'companies_month_1': 20,
                'companies_month_6': 100,
                'companies_month_12': 200,
                'avg_employees_per_company': 125,
                'avg_plan': 'professional',
                'avg_monthly_revenue_per_company': 3500,  # USD
                'projected_annual_revenue': 8400000  # USD
            }
        }
        
        return scenarios.get(scenario, scenarios['moderate'])
    
    def calculate_optimal_pricing(self, 
                                target_market: str,
                                competitors: List[str],
                                target_margin: float = 0.80) -> Dict:
        """
        Calcula el pricing óptimo basado en el mercado objetivo y competencia
        """
        # Análisis de competidores
        competitor_prices = []
        for competitor in competitors:
            if competitor in self.get_competitive_analysis():
                competitor_prices.append(
                    self.get_competitive_analysis()[competitor]['price_per_employee']
                )
        
        if competitor_prices:
            avg_competitor_price = sum(competitor_prices) / len(competitor_prices)
            # Precio 15% menor que el promedio de competidores
            optimal_price = avg_competitor_price * 0.85
        else:
            optimal_price = 28.00  # Precio base
        
        # Ajustar por margen objetivo
        cost_per_employee = COST_BREAKDOWN['infrastructure_per_company']['total_monthly'] / 50  # Estimado
        min_price = cost_per_employee / (1 - target_margin)
        
        final_price = max(optimal_price, min_price)
        
        return {
            'optimal_price_per_employee': final_price,
            'competitor_average': avg_competitor_price if competitor_prices else None,
            'cost_per_employee': cost_per_employee,
            'target_margin': target_margin,
            'recommended_plan': self._get_recommended_plan(target_market, final_price)
        }
    
    def _get_recommended_plan(self, target_market: str, price: float) -> str:
        """
        Obtiene el plan recomendado basado en el mercado objetivo
        """
        if target_market == 'startup' or target_market == 'micro':
            return 'starter'
        elif target_market == 'sme' or target_market == 'medium':
            return 'professional'
        else:
            return 'enterprise'
    
    def get_pricing_recommendations(self, company_size: str, industry: str) -> Dict:
        """
        Obtiene recomendaciones de pricing específicas para una empresa
        """
        recommendations = {
            'plan_recommendation': self._get_plan_recommendation(company_size),
            'addon_recommendations': self._get_addon_recommendations(industry),
            'pricing_strategy': self._get_pricing_strategy(company_size, industry),
            'implementation_recommendation': self._get_implementation_recommendation(company_size)
        }
        
        return recommendations
    
    def _get_plan_recommendation(self, company_size: str) -> Dict:
        """
        Recomienda el plan basado en el tamaño de la empresa
        """
        size_mapping = {
            'micro': 'starter',
            'small': 'starter',
            'medium': 'professional',
            'large': 'enterprise'
        }
        
        recommended_plan = size_mapping.get(company_size, 'professional')
        
        return {
            'plan': recommended_plan,
            'reasoning': f'Plan {recommended_plan} optimizado para empresas {company_size}',
            'estimated_monthly_cost': PAYROLL_PRICING[recommended_plan]['price_per_employee'] * 50  # Estimado
        }
    
    def _get_addon_recommendations(self, industry: str) -> List[str]:
        """
        Recomienda add-ons basado en la industria
        """
        industry_addons = {
            'technology': ['predictive_analytics', 'workflow_automation'],
            'manufacturing': ['compliance_automation', 'workflow_automation'],
            'healthcare': ['compliance_automation', 'predictive_analytics'],
            'retail': ['predictive_analytics', 'sentiment_analysis'],
            'finance': ['compliance_automation', 'predictive_analytics'],
            'default': ['compliance_automation']
        }
        
        return industry_addons.get(industry, industry_addons['default'])
    
    def _get_pricing_strategy(self, company_size: str, industry: str) -> str:
        """
        Obtiene la estrategia de pricing recomendada
        """
        if company_size in ['micro', 'small']:
            return 'penetration'  # Precios bajos para penetrar el mercado
        elif industry in ['technology', 'finance']:
            return 'premium'  # Precios premium para industrias de alto valor
        else:
            return 'competitive'  # Precios competitivos
    
    def _get_implementation_recommendation(self, company_size: str) -> str:
        """
        Recomienda el tipo de implementación
        """
        if company_size in ['micro', 'small']:
            return 'basic_setup'
        elif company_size == 'medium':
            return 'standard_setup'
        else:
            return 'enterprise_setup' 