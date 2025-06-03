# /home/pablo/app/com/pricing/volume_pricing.py
"""
Módulo de precios por volumen para Grupo huntRED®.

Este módulo maneja estructuras de precios escalonadas para diferentes BusinessUnits
cuando se requieren múltiples vacantes de la misma posición o posiciones diferentes.
"""

from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.utils import timezone
from app.models import BusinessUnit, Opportunity, Vacancy, PricingBaseline


class VolumePricing:
    """
    Gestiona estructuras de precios por volumen para vacantes múltiples,
    con configuraciones específicas por BusinessUnit.
    """
    
    # Estructura de descuentos para vacantes de la misma posición
    SAME_POSITION_DISCOUNTS = {
        'huntRED': [
            {'min': 1, 'max': 2, 'discount_pct': Decimal('0.00')},
            {'min': 3, 'max': 5, 'discount_pct': Decimal('0.05')},
            {'min': 6, 'max': 10, 'discount_pct': Decimal('0.10')},
            {'min': 11, 'max': 20, 'discount_pct': Decimal('0.15')},
            {'min': 21, 'max': float('inf'), 'discount_pct': Decimal('0.20')}
        ],
        'huntU': [
            {'min': 1, 'max': 5, 'discount_pct': Decimal('0.00')},
            {'min': 6, 'max': 15, 'discount_pct': Decimal('0.08')},
            {'min': 16, 'max': 30, 'discount_pct': Decimal('0.12')},
            {'min': 31, 'max': float('inf'), 'discount_pct': Decimal('0.15')}
        ],
        'Amigro': [
            {'min': 1, 'max': 10, 'discount_pct': Decimal('0.00')},
            {'min': 11, 'max': 30, 'discount_pct': Decimal('0.10')},
            {'min': 31, 'max': 50, 'discount_pct': Decimal('0.15')},
            {'min': 51, 'max': 100, 'discount_pct': Decimal('0.20')},
            {'min': 101, 'max': float('inf'), 'discount_pct': Decimal('0.25')}
        ]
    }
    
    # Estructura de descuentos para vacantes de diferentes posiciones
    DIFFERENT_POSITION_DISCOUNTS = {
        'huntRED': [
            {'min': 1, 'max': 2, 'discount_pct': Decimal('0.00')},
            {'min': 3, 'max': 5, 'discount_pct': Decimal('0.03')},
            {'min': 6, 'max': 10, 'discount_pct': Decimal('0.07')},
            {'min': 11, 'max': float('inf'), 'discount_pct': Decimal('0.12')}
        ],
        'huntU': [
            {'min': 1, 'max': 5, 'discount_pct': Decimal('0.00')},
            {'min': 6, 'max': 15, 'discount_pct': Decimal('0.05')},
            {'min': 16, 'max': float('inf'), 'discount_pct': Decimal('0.10')}
        ],
        'Amigro': [
            {'min': 1, 'max': 15, 'discount_pct': Decimal('0.00')},
            {'min': 16, 'max': 40, 'discount_pct': Decimal('0.08')},
            {'min': 41, 'max': float('inf'), 'discount_pct': Decimal('0.15')}
        ]
    }
    
    @classmethod
    def calculate_volume_pricing(cls, business_unit_name, vacancies):
        """
        Calcula precios con descuento por volumen basado en estructura y grupo de vacantes.
        
        Args:
            business_unit_name: Nombre de la BusinessUnit
            vacancies: Lista de diccionarios con información de vacantes
                [
                    {
                        'position_id': 'ID_POSICION',
                        'position_name': 'Nombre de la posición',
                        'count': 5,  # Número de vacantes para esta posición
                        'base_price': Decimal('15000.00')  # Precio base por vacante
                    },
                    ...
                ]
        
        Returns:
            dict: Detalle completo del pricing con descuentos aplicados
        """
        if business_unit_name not in cls.SAME_POSITION_DISCOUNTS:
            raise ValueError(f"Business unit '{business_unit_name}' no tiene configuración de descuentos")
            
        # Agrupamiento por posición para determinar descuentos
        position_groups = {}
        total_vacancies = 0
        
        for vacancy in vacancies:
            position_id = vacancy['position_id']
            position_count = vacancy['count']
            total_vacancies += position_count
            
            if position_id in position_groups:
                position_groups[position_id]['count'] += position_count
            else:
                position_groups[position_id] = {
                    'position_id': position_id,
                    'position_name': vacancy['position_name'],
                    'count': position_count,
                    'base_price': vacancy['base_price']
                }
        
        # Cálculo de descuento para vacantes diferentes (total global)
        different_discount = Decimal('0.00')
        for tier in cls.DIFFERENT_POSITION_DISCOUNTS[business_unit_name]:
            if tier['min'] <= len(position_groups) <= tier['max']:
                different_discount = tier['discount_pct']
                break
                
        # Cálculo de precio final por posición
        pricing_details = []
        subtotal = Decimal('0.00')
        total_discount = Decimal('0.00')
        
        for position_id, position_info in position_groups.items():
            # Descuento por volumen de la misma posición
            same_position_discount = Decimal('0.00')
            for tier in cls.SAME_POSITION_DISCOUNTS[business_unit_name]:
                if tier['min'] <= position_info['count'] <= tier['max']:
                    same_position_discount = tier['discount_pct']
                    break
            
            # El descuento aplicado será el mayor entre vacantes iguales y vacantes diferentes
            effective_discount = max(same_position_discount, different_discount)
            base_total = position_info['base_price'] * position_info['count']
            discount_amount = base_total * effective_discount
            final_total = base_total - discount_amount
            
            position_detail = {
                'position_id': position_id,
                'position_name': position_info['position_name'],
                'count': position_info['count'],
                'base_price': position_info['base_price'],
                'discount_percentage': effective_discount * 100,
                'discount_amount': discount_amount,
                'base_total': base_total,
                'final_total': final_total
            }
            
            pricing_details.append(position_detail)
            subtotal += final_total
            total_discount += discount_amount
            
        # Calcular IVA
        iva = subtotal * Decimal('0.16')
        total = subtotal + iva
            
        # Construir respuesta final
        result = {
            'business_unit': business_unit_name,
            'pricing_details': pricing_details,
            'total_vacancies': total_vacancies,
            'total_positions': len(position_groups),
            'subtotal': subtotal,
            'total_discount': total_discount,
            'iva': iva,
            'total': total,
            'currency': 'MXN',
            'date': timezone.now().strftime('%d/%m/%Y')
        }
        
        return result


class RecurringServicePricing:
    """
    Gestiona precios para servicios recurrentes con descuentos por duración
    de contrato y número de servicios.
    """
    
    # Descuentos por duración de contrato (meses)
    CONTRACT_DURATION_DISCOUNTS = [
        {'min_months': 1, 'max_months': 2, 'discount_pct': Decimal('0.00')},
        {'min_months': 3, 'max_months': 5, 'discount_pct': Decimal('0.05')},
        {'min_months': 6, 'max_months': 11, 'discount_pct': Decimal('0.10')},
        {'min_months': 12, 'max_months': 23, 'discount_pct': Decimal('0.15')},
        {'min_months': 24, 'max_months': float('inf'), 'discount_pct': Decimal('0.20')}
    ]
    
    @classmethod
    def calculate_recurring_pricing(cls, service_base_price, service_count, duration_months):
        """
        Calcula precios para servicios recurrentes con descuentos por duración.
        
        Args:
            service_base_price: Precio base mensual del servicio
            service_count: Número de servicios/unidades
            duration_months: Duración del contrato en meses
            
        Returns:
            dict: Detalle del pricing para servicios recurrentes
        """
        # Calcular descuento por duración
        duration_discount = Decimal('0.00')
        for tier in cls.CONTRACT_DURATION_DISCOUNTS:
            if tier['min_months'] <= duration_months <= tier['max_months']:
                duration_discount = tier['discount_pct']
                break
                
        # Cálculo de precios
        monthly_base = service_base_price * service_count
        monthly_discount_amount = monthly_base * duration_discount
        monthly_discounted = monthly_base - monthly_discount_amount
        
        total_contract_base = monthly_base * duration_months
        total_contract_discount = monthly_discount_amount * duration_months
        total_contract_discounted = monthly_discounted * duration_months
        
        # Calcular IVA
        monthly_iva = monthly_discounted * Decimal('0.16')
        total_contract_iva = monthly_iva * duration_months
        
        monthly_total = monthly_discounted + monthly_iva
        total_contract_total = total_contract_discounted + total_contract_iva
        
        # Construir respuesta final
        result = {
            'service_base_price': service_base_price,
            'service_count': service_count,
            'duration_months': duration_months,
            'discount_percentage': duration_discount * 100,
            'monthly': {
                'base': monthly_base,
                'discount_amount': monthly_discount_amount,
                'discounted': monthly_discounted,
                'iva': monthly_iva,
                'total': monthly_total
            },
            'total_contract': {
                'base': total_contract_base,
                'discount_amount': total_contract_discount,
                'discounted': total_contract_discounted,
                'iva': total_contract_iva,
                'total': total_contract_total
            },
            'currency': 'MXN',
            'date': timezone.now().strftime('%d/%m/%Y')
        }
        
        return result


class BundlePricing:
    """
    Gestiona precios para paquetes de servicios diferentes
    con descuentos por compra combinada.
    """
    
    # Configuraciones de bundles predefinidos
    PREDEFINED_BUNDLES = {
        'talent_acquisition': {
            'name': 'Paquete de Adquisición de Talento',
            'description': 'Solución integral para atraer, evaluar y contratar talento',
            'services': [
                {'service_id': 'recruitment', 'name': 'Reclutamiento Ejecutivo', 'required': True},
                {'service_id': 'talent_360', 'name': 'Análisis de Talento 360°', 'required': False},
                {'service_id': 'background_check', 'name': 'Verificación de Antecedentes', 'required': False},
                {'service_id': 'onboarding', 'name': 'Programa de Onboarding', 'required': False}
            ],
            'bundle_discount': {
                2: Decimal('0.05'),  # 5% al contratar 2 servicios
                3: Decimal('0.10'),  # 10% al contratar 3 servicios
                4: Decimal('0.15')   # 15% al contratar 4 servicios
            }
        },
        'talent_development': {
            'name': 'Paquete de Desarrollo de Talento',
            'description': 'Solución integral para desarrollar y retener talento',
            'services': [
                {'service_id': 'talent_360', 'name': 'Análisis de Talento 360°', 'required': True},
                {'service_id': 'career_planning', 'name': 'Planeación de Carrera', 'required': False},
                {'service_id': 'coaching', 'name': 'Coaching Ejecutivo', 'required': False},
                {'service_id': 'performance_management', 'name': 'Gestión del Desempeño', 'required': False}
            ],
            'bundle_discount': {
                2: Decimal('0.05'),  # 5% al contratar 2 servicios
                3: Decimal('0.08'),  # 8% al contratar 3 servicios
                4: Decimal('0.12')   # 12% al contratar 4 servicios
            }
        }
    }
    
    @classmethod
    def calculate_bundle_pricing(cls, bundle_id, selected_services):
        """
        Calcula precios para un bundle de servicios con descuentos aplicados.
        
        Args:
            bundle_id: Identificador del bundle predefinido
            selected_services: Lista de servicios seleccionados con precios
                [
                    {
                        'service_id': 'recruitment',
                        'price': Decimal('15000.00'),
                        'quantity': 1
                    },
                    ...
                ]
                
        Returns:
            dict: Detalle del pricing para el bundle de servicios
        """
        if bundle_id not in cls.PREDEFINED_BUNDLES:
            raise ValueError(f"Bundle '{bundle_id}' no existe")
            
        bundle_config = cls.PREDEFINED_BUNDLES[bundle_id]
        
        # Validar que los servicios requeridos estén incluidos
        required_services = [s['service_id'] for s in bundle_config['services'] if s['required']]
        selected_service_ids = [s['service_id'] for s in selected_services]
        
        missing_required = set(required_services) - set(selected_service_ids)
        if missing_required:
            raise ValueError(f"Faltan servicios requeridos: {', '.join(missing_required)}")
            
        # Validar que todos los servicios seleccionados pertenezcan al bundle
        allowed_services = [s['service_id'] for s in bundle_config['services']]
        invalid_services = set(selected_service_ids) - set(allowed_services)
        if invalid_services:
            raise ValueError(f"Servicios no válidos para este bundle: {', '.join(invalid_services)}")
            
        # Determinar descuento aplicable
        service_count = len(selected_services)
        discount_pct = Decimal('0.00')
        
        for count, discount in bundle_config['bundle_discount'].items():
            if service_count >= count:
                discount_pct = discount
        
        # Calcular precios
        services_detail = []
        subtotal_base = Decimal('0.00')
        
        for service in selected_services:
            service_id = service['service_id']
            service_price = service['price']
            service_quantity = service.get('quantity', 1)
            
            service_config = next((s for s in bundle_config['services'] if s['service_id'] == service_id), None)
            
            service_subtotal = service_price * service_quantity
            service_discount = service_subtotal * discount_pct
            service_final = service_subtotal - service_discount
            
            service_detail = {
                'service_id': service_id,
                'name': service_config['name'],
                'price': service_price,
                'quantity': service_quantity,
                'subtotal': service_subtotal,
                'discount_amount': service_discount,
                'final': service_final
            }
            
            services_detail.append(service_detail)
            subtotal_base += service_subtotal
        
        # Calcular totales
        total_discount = subtotal_base * discount_pct
        subtotal = subtotal_base - total_discount
        iva = subtotal * Decimal('0.16')
        total = subtotal + iva
        
        # Construir respuesta final
        result = {
            'bundle_id': bundle_id,
            'bundle_name': bundle_config['name'],
            'bundle_description': bundle_config['description'],
            'services': services_detail,
            'discount_percentage': discount_pct * 100,
            'subtotal_base': subtotal_base,
            'total_discount': total_discount,
            'subtotal': subtotal,
            'iva': iva,
            'total': total,
            'currency': 'MXN',
            'date': timezone.now().strftime('%d/%m/%Y')
        }
        
        return result
