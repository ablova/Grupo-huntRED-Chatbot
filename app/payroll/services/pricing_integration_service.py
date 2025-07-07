"""
Servicio de Integración de Pricing - huntRED® Payroll
Conecta el pricing de Payroll con el sistema general de pricing de ATS
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from ..models import Company, Employee, PayrollPlan
from .. import PAYROLL_PRICING, PREMIUM_SERVICES, AI_SERVICES
from app.ats.pricing import PricingService as ATSPricingService
from app.ats.pricing.models import PricingStrategy, PricePoint, DiscountRule, PaymentGateway


class PricingIntegrationService:
    """
    Servicio para integrar el pricing de Payroll con el sistema general
    """
    
    def __init__(self):
        self.ats_pricing_service = ATSPricingService()
    
    def sync_payroll_pricing_to_ats(self) -> Dict:
        """
        Sincroniza los precios de Payroll con el sistema de pricing de ATS
        """
        sync_results = {
            'created_strategies': [],
            'updated_strategies': [],
            'errors': []
        }
        
        try:
            with transaction.atomic():
                # Crear estrategias de pricing para Payroll
                for plan_name, plan_data in PAYROLL_PRICING.items():
                    strategy_name = f"payroll_{plan_name}"
                    
                    # Buscar o crear estrategia
                    strategy, created = PricingStrategy.objects.get_or_create(
                        name=strategy_name,
                        defaults={
                            'description': f'Estrategia de pricing para Payroll {plan_name}',
                            'is_active': True,
                            'business_unit': 'payroll'
                        }
                    )
                    
                    if created:
                        sync_results['created_strategies'].append(strategy_name)
                    else:
                        sync_results['updated_strategies'].append(strategy_name)
                    
                    # Crear puntos de precio
                    self._create_price_points(strategy, plan_data)
                    
                    # Crear reglas de descuento
                    self._create_discount_rules(strategy, plan_name)
                
                # Sincronizar servicios premium
                self._sync_premium_services()
                
                # Sincronizar servicios de IA
                self._sync_ai_services()
                
        except Exception as e:
            sync_results['errors'].append(str(e))
        
        return sync_results
    
    def _create_price_points(self, strategy: PricingStrategy, plan_data: Dict):
        """
        Crea puntos de precio para una estrategia
        """
        # Precio por empleado
        PricePoint.objects.get_or_create(
            strategy=strategy,
            name='price_per_employee',
            defaults={
                'value': plan_data['price_per_employee'],
                'currency': 'USD',
                'description': 'Precio por empleado por mes'
            }
        )
        
        # Setup fee
        PricePoint.objects.get_or_create(
            strategy=strategy,
            name='setup_fee',
            defaults={
                'value': plan_data['setup_fee'],
                'currency': 'USD',
                'description': 'Cargo de configuración inicial'
            }
        )
        
        # Cargo base mensual
        PricePoint.objects.get_or_create(
            strategy=strategy,
            name='monthly_base_fee',
            defaults={
                'value': plan_data['monthly_base_fee'],
                'currency': 'USD',
                'description': 'Cargo base mensual'
            }
        )
    
    def _create_discount_rules(self, strategy: PricingStrategy, plan_name: str):
        """
        Crea reglas de descuento para una estrategia
        """
        from .. import VOLUME_DISCOUNTS
        
        # Descuentos por volumen de empleados
        for threshold, discount in VOLUME_DISCOUNTS['employee_discounts'].items():
            DiscountRule.objects.get_or_create(
                strategy=strategy,
                name=f'volume_discount_{threshold}',
                defaults={
                    'discount_type': 'percentage',
                    'discount_value': discount * 100,  # Convertir a porcentaje
                    'conditions': {
                        'min_employees': int(threshold.replace('+', '')),
                        'plan': plan_name
                    },
                    'description': f'Descuento por volumen: {threshold} empleados'
                }
            )
        
        # Descuentos por pago anual
        DiscountRule.objects.get_or_create(
            strategy=strategy,
            name='annual_payment_discount',
            defaults={
                'discount_type': 'percentage',
                'discount_value': VOLUME_DISCOUNTS['annual_discounts']['annual_payment'] * 100,
                'conditions': {
                    'payment_frequency': 'annual',
                    'plan': plan_name
                },
                'description': 'Descuento por pago anual'
            }
        )
    
    def _sync_premium_services(self):
        """
        Sincroniza servicios premium con el sistema de pricing
        """
        for service_name, service_data in PREMIUM_SERVICES.items():
            strategy_name = f"payroll_premium_{service_name}"
            
            strategy, created = PricingStrategy.objects.get_or_create(
                name=strategy_name,
                defaults={
                    'description': f'Servicio premium de Payroll: {service_name}',
                    'is_active': True,
                    'business_unit': 'payroll'
                }
            )
            
            # Crear punto de precio para el servicio
            if 'price_per_employee' in service_data:
                PricePoint.objects.get_or_create(
                    strategy=strategy,
                    name='price_per_employee',
                    defaults={
                        'value': service_data['price_per_employee'],
                        'currency': 'USD',
                        'description': f'Precio por empleado para {service_name}'
                    }
                )
    
    def _sync_ai_services(self):
        """
        Sincroniza servicios de IA con el sistema de pricing
        """
        for service_name, service_data in AI_SERVICES.items():
            strategy_name = f"payroll_ai_{service_name}"
            
            strategy, created = PricingStrategy.objects.get_or_create(
                name=strategy_name,
                defaults={
                    'description': f'Servicio de IA de Payroll: {service_name}',
                    'is_active': True,
                    'business_unit': 'payroll'
                }
            )
            
            # Crear punto de precio para el servicio
            PricePoint.objects.get_or_create(
                strategy=strategy,
                name='price_per_employee',
                defaults={
                    'value': service_data['price_per_employee'],
                    'currency': 'USD',
                    'description': f'Precio por empleado para {service_name}'
                }
            )
    
    def create_bundle_strategy(self, bundle_name: str, services: List[str], discount: float) -> PricingStrategy:
        """
        Crea una estrategia de pricing para un bundle
        """
        strategy_name = f"bundle_{bundle_name}"
        
        strategy, created = PricingStrategy.objects.get_or_create(
            name=strategy_name,
            defaults={
                'description': f'Bundle de servicios: {bundle_name}',
                'is_active': True,
                'business_unit': 'payroll'
            }
        )
        
        # Crear regla de descuento para el bundle
        DiscountRule.objects.get_or_create(
            strategy=strategy,
            name='bundle_discount',
            defaults={
                'discount_type': 'percentage',
                'discount_value': discount * 100,
                'conditions': {
                    'bundle_services': services,
                    'bundle_name': bundle_name
                },
                'description': f'Descuento de bundle: {discount * 100}%'
            }
        )
        
        return strategy
    
    def get_integrated_pricing(self, company: Company, services: List[str]) -> Dict:
        """
        Obtiene pricing integrado considerando todos los servicios
        """
        integrated_pricing = {
            'payroll': {},
            'ats': {},
            'aura': {},
            'bundles': {},
            'total': 0
        }
        
        # Pricing de Payroll
        if 'payroll' in services:
            payroll_plan = company.payroll_plan or 'professional'
            plan_data = PAYROLL_PRICING[payroll_plan]
            
            integrated_pricing['payroll'] = {
                'plan': payroll_plan,
                'price_per_employee': plan_data['price_per_employee'],
                'setup_fee': plan_data['setup_fee'],
                'monthly_base_fee': plan_data['monthly_base_fee'],
                'total_monthly': plan_data['price_per_employee'] * company.employees.count() + plan_data['monthly_base_fee']
            }
            
            integrated_pricing['total'] += integrated_pricing['payroll']['total_monthly']
        
        # Pricing de ATS (usando sistema de ATS)
        if 'ats' in services:
            ats_pricing = self.ats_pricing_service.get_pricing_for_company(company)
            integrated_pricing['ats'] = ats_pricing
            integrated_pricing['total'] += ats_pricing.get('total_monthly', 0)
        
        # Pricing de AURA (estimado)
        if 'aura' in services:
            aura_pricing = self._calculate_aura_pricing(company)
            integrated_pricing['aura'] = aura_pricing
            integrated_pricing['total'] += aura_pricing.get('total_monthly', 0)
        
        # Aplicar descuentos de bundle
        if len(services) > 1:
            bundle_discount = self._calculate_bundle_discount(services)
            integrated_pricing['bundle_discount'] = bundle_discount
            integrated_pricing['total'] *= (1 - bundle_discount)
        
        return integrated_pricing
    
    def _calculate_aura_pricing(self, company: Company) -> Dict:
        """
        Calcula pricing de AURA (estimado)
        """
        employee_count = company.employees.count()
        
        # Precios base de AURA
        aura_services = {
            'chatbot_hr': 8.0,  # USD por empleado/mes
            'recruitment_chatbot': 6.0,  # USD por empleado/mes
            'customer_service': 10.0,  # USD por empleado/mes
        }
        
        total_monthly = sum(aura_services.values()) * employee_count
        
        return {
            'services': aura_services,
            'total_monthly': total_monthly,
            'setup_fee': 2000.0  # USD
        }
    
    def _calculate_bundle_discount(self, services: List[str]) -> float:
        """
        Calcula descuento de bundle basado en número de servicios
        """
        if len(services) == 2:
            return 0.15  # 15% descuento
        elif len(services) == 3:
            return 0.25  # 25% descuento
        else:
            return 0.10  # 10% descuento
    
    def create_cross_sell_proposal(self, company: Company, target_services: List[str]) -> Dict:
        """
        Crea una propuesta de venta cruzada integrada
        """
        # Obtener pricing actual
        current_pricing = self.get_integrated_pricing(company, ['payroll'])
        
        # Obtener pricing con servicios adicionales
        proposed_pricing = self.get_integrated_pricing(company, target_services)
        
        # Calcular ahorros y ROI
        additional_cost = proposed_pricing['total'] - current_pricing['total']
        potential_savings = self._calculate_potential_savings(company, target_services)
        roi = ((potential_savings - additional_cost) / additional_cost) * 100 if additional_cost > 0 else 0
        
        proposal = {
            'company': {
                'name': company.name,
                'employees': company.employees.count(),
                'industry': company.industry
            },
            'current_pricing': current_pricing,
            'proposed_pricing': proposed_pricing,
            'additional_cost': additional_cost,
            'potential_savings': potential_savings,
            'roi_percentage': roi,
            'payback_months': (additional_cost / (potential_savings - additional_cost)) * 12 if (potential_savings - additional_cost) > 0 else 0,
            'recommendations': self._get_service_recommendations(company, target_services)
        }
        
        return proposal
    
    def _calculate_potential_savings(self, company: Company, services: List[str]) -> float:
        """
        Calcula ahorros potenciales por servicio
        """
        employee_count = company.employees.count()
        savings_per_employee = {
            'payroll': 50.0,  # USD/mes
            'ats': 30.0,      # USD/mes
            'aura': 25.0      # USD/mes
        }
        
        total_savings = 0
        for service in services:
            if service in savings_per_employee:
                total_savings += savings_per_employee[service] * employee_count
        
        return total_savings
    
    def _get_service_recommendations(self, company: Company, services: List[str]) -> List[Dict]:
        """
        Obtiene recomendaciones específicas por servicio
        """
        recommendations = []
        
        if 'ats' in services:
            recommendations.append({
                'service': 'ATS',
                'benefit': 'Reduce tiempo de contratación en 60%',
                'value': 'Mejora candidate experience y reduce costos de reclutamiento'
            })
        
        if 'aura' in services:
            recommendations.append({
                'service': 'AURA',
                'benefit': 'Automatiza 80% de consultas HR',
                'value': 'Mejora satisfacción de empleados y reduce carga administrativa'
            })
        
        return recommendations
    
    def sync_with_payment_gateways(self) -> Dict:
        """
        Sincroniza con gateways de pago
        """
        sync_results = {
            'gateways_configured': [],
            'errors': []
        }
        
        # Configurar gateways para Payroll
        gateways = [
            {
                'name': 'payroll_stripe',
                'gateway_type': 'stripe',
                'description': 'Gateway para pagos de Payroll',
                'is_active': True
            },
            {
                'name': 'payroll_paypal',
                'gateway_type': 'paypal',
                'description': 'Gateway PayPal para Payroll',
                'is_active': True
            }
        ]
        
        for gateway_config in gateways:
            try:
                gateway, created = PaymentGateway.objects.get_or_create(
                    name=gateway_config['name'],
                    defaults=gateway_config
                )
                
                if created:
                    sync_results['gateways_configured'].append(gateway_config['name'])
                    
            except Exception as e:
                sync_results['errors'].append(f"Error configurando {gateway_config['name']}: {str(e)}")
        
        return sync_results 