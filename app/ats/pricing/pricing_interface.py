# /home/pablo/app/com/pricing/pricing_interface.py
"""
Interfaz de gestión de precios para Grupo huntRED®.

Este módulo proporciona una interfaz unificada para gestionar todos los aspectos
del sistema de precios avanzado, incluyendo descuentos por volumen, addons,
paquetes, y facturación progresiva.
"""

from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from app.models import BusinessUnit, Proposal, Opportunity, Vacancy
from app.ats.pricing.utils import calculate_pricing, get_registered_addon
from app.ats.pricing.volume_pricing import VolumePricing, RecurringServicePricing, BundlePricing
from app.ats.pricing.progressive_billing import ProgressiveBilling


class PricingManager:
    """
    Administrador central para gestionar todos los aspectos del sistema de precios.
    
    Esta clase sirve como punto de entrada principal para el cálculo de precios,
    descuentos, propuestas y planes de pago.
    """
    
    @classmethod
    def generate_proposal(cls, opportunity_id, include_addons=None, include_bundles=None, 
                         payment_schedule=True, custom_milestones=None, include_assessments=None):
        """
        Genera una propuesta completa para una oportunidad, incorporando todos los 
        aspectos del sistema de precios avanzado.
        
        Args:
            opportunity_id: ID de la Opportunity
            include_addons: Lista de IDs de addons a incluir (opcional)
            include_bundles: Lista de IDs de bundles a incluir (opcional)
            payment_schedule: Indica si se debe generar plan de pagos (por defecto True)
            custom_milestones: Configuración personalizada de hitos de pago (opcional)
            include_assessments: Lista de tipos de evaluaciones a incluir (opcional)
            
        Returns:
            dict: Datos completos para la propuesta
        """
        opportunity = Opportunity.objects.get(id=opportunity_id)
        business_unit = opportunity.business_unit
        vacancies = Vacancy.objects.filter(opportunity=opportunity)
        
        # 1. Agrupar vacantes por posición para determinar descuentos por volumen
        positions = {}
        for vacancy in vacancies:
            position_id = vacancy.position_id
            if position_id in positions:
                positions[position_id]['count'] += 1
            else:
                positions[position_id] = {
                    'position_id': position_id,
                    'position_name': vacancy.position_name,
                    'count': 1,
                    'base_price': Decimal(str(vacancy.salary_range_max * business_unit.pricing_config.get('base_rate', 0) / 100))
                }
                
        # 2. Calcular pricing con descuentos por volumen
        vacancy_groups = [
            {
                'position_id': data['position_id'],
                'position_name': data['position_name'],
                'count': data['count'],
                'base_price': data['base_price']
            } 
            for data in positions.values()
        ]
        
        volume_pricing_data = VolumePricing.calculate_volume_pricing(
            business_unit_name=business_unit.name,
            vacancies=vacancy_groups
        )
        
        # 3. Procesar addons si se especificaron
        addons_data = []
        if include_addons:
            for addon_id in include_addons:
                addon_info = get_registered_addon(addon_id)
                if addon_info:
                    # Para simplificar, asumimos que la información de pricing se proporciona en la solicitud
                    # En una implementación real, habría una lógica más compleja aquí
                    addon_data = {
                        'id': addon_id,
                        'name': addon_info['name'],
                        'description': addon_info['description'],
                        'price': addon_info['pricing'].calculate_total(
                            user_count=opportunity.headcount or 1
                        )
                    }
                    addons_data.append(addon_data)
        
        # 4. Procesar bundles si se especificaron
        bundles_data = []
        if include_bundles:
            for bundle_id in include_bundles:
                # Para simplificar, asumimos datos básicos del bundle
                # En una implementación real, habría una lógica más compleja aquí
                try:
                    selected_services = [
                        {'service_id': 'recruitment', 'price': Decimal('15000.00'), 'quantity': 1}
                    ]
                    bundle_data = BundlePricing.calculate_bundle_pricing(
                        bundle_id=bundle_id,
                        selected_services=selected_services
                    )
                    bundles_data.append(bundle_data)
                except ValueError as e:
                    # Registrar error pero continuar
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Error al procesar bundle {bundle_id}: {e}")
                    continue
        
        # 5. Generar plan de pagos si se solicitó
        payment_schedule_data = None
        if payment_schedule:
            start_date = timezone.now().date()
            contract_amount = volume_pricing_data['total']
            
            # Añadir montos de addons y bundles al contrato para facturación
            for addon in addons_data:
                if 'price' in addon and 'total' in addon['price']:
                    contract_amount += addon['price']['total']
                    
            for bundle in bundles_data:
                if 'total' in bundle:
                    contract_amount += bundle['total']
                    
            payment_schedule_data = ProgressiveBilling.generate_payment_schedule(
                business_unit_name=business_unit.name,
                start_date=start_date,
                contract_amount=contract_amount,
                service_type=opportunity.service_type,
                custom_milestones=custom_milestones
            )
        
        # Procesar evaluaciones si se especificaron
        assessments_data = None
        if include_assessments:
            assessments_data = cls.calculate_assessment_pricing(
                opportunity_id=opportunity_id,
                assessment_types=include_assessments,
                user_count=opportunity.headcount or 1
            )
            
            # Añadir el total de evaluaciones al contrato para facturación
            if assessments_data and 'total' in assessments_data:
                contract_amount += assessments_data['total']
        
        # 6. Construir la respuesta final con todos los componentes
        proposal_data = {
            'opportunity': {
                'id': opportunity.id,
                'name': opportunity.name,
                'description': opportunity.description,
                'business_unit': {
                    'id': business_unit.id,
                    'name': business_unit.name
                }
            },
            'pricing': {
                'volume': volume_pricing_data,
                'addons': addons_data,
                'bundles': bundles_data,
                'assessments': assessments_data
            },
            'payment_schedule': payment_schedule_data,
            'totals': {
                'subtotal': volume_pricing_data['subtotal'] + (assessments_data['subtotal'] if assessments_data else Decimal('0.00')),
                'iva': volume_pricing_data['iva'] + (assessments_data['iva'] if assessments_data else Decimal('0.00')),
                'total': volume_pricing_data['total'] + (assessments_data['total'] if assessments_data else Decimal('0.00')),
                'currency': 'MXN',
                'date': timezone.now().strftime('%d/%m/%Y'),
                'valid_until': (timezone.now() + timezone.timedelta(days=30)).strftime('%d/%m/%Y')
            }
        }
        
        return proposal_data
    
    @classmethod
    def calculate_recurring_service(cls, business_unit_name, service_type, base_monthly_price, 
                                   service_count, duration_months):
        """
        Calcula el precio para un servicio recurrente con descuentos por duración.
        
        Args:
            business_unit_name: Nombre de la BusinessUnit
            service_type: Tipo de servicio recurrente
            base_monthly_price: Precio base mensual por unidad
            service_count: Número de unidades/servicios
            duration_months: Duración del contrato en meses
            
        Returns:
            dict: Datos completos del pricing recurrente
        """
        recurring_pricing = RecurringServicePricing.calculate_recurring_pricing(
            service_base_price=base_monthly_price,
            service_count=service_count,
            duration_months=duration_months
        )
        
        return {
            'business_unit': business_unit_name,
            'service_type': service_type,
            'recurring_pricing': recurring_pricing
        }
        
    @classmethod
    def simulate_pricing_scenarios(cls, business_unit_name, base_data, scenarios=None):
        """
        Simula diferentes escenarios de pricing para ayudar en la toma de decisiones.
        
        Args:
            business_unit_name: Nombre de la BusinessUnit
            base_data: Datos base para la simulación (depende del contexto)
            scenarios: Lista de escenarios a simular (opcional)
            
        Returns:
            dict: Resultados de los escenarios simulados
        """
        # En una implementación real, aquí habría lógica para simular diferentes
        # configuraciones de pricing, descuentos, etc.
        
        # Por ahora, simplemente devolvemos un mensaje de que la funcionalidad
        # está pendiente de implementación
        return {
            'status': 'pending',
            'message': 'La simulación de escenarios de pricing está pendiente de implementación'
        }
        
    @classmethod
    def get_pricing_summary(cls, entity_id, entity_type):
        """
        Obtiene un resumen del pricing para una entidad específica (Opportunity, Proposal, Contract).
        
        Args:
            entity_id: ID de la entidad
            entity_type: Tipo de entidad ('opportunity', 'proposal', 'contract')
            
        Returns:
            dict: Resumen del pricing para la entidad
        """
        # En una implementación real, aquí habría lógica para obtener y formatear
        # la información de pricing según el tipo de entidad
        
        # Por ahora, simplemente devolvemos un mensaje de que la funcionalidad
        # está pendiente de implementación
        return {
            'status': 'pending',
            'message': 'El resumen de pricing está pendiente de implementación'
        }

    @classmethod
    def calculate_assessment_pricing(cls, opportunity_id, assessment_types, user_count):
        """
        Calcula el precio para las evaluaciones basado en el tipo y número de usuarios.
        
        Args:
            opportunity_id: ID de la Opportunity
            assessment_types: Lista de tipos de evaluaciones a incluir
            user_count: Número de usuarios a evaluar
            
        Returns:
            dict: Datos de pricing para las evaluaciones
        """
        opportunity = Opportunity.objects.get(id=opportunity_id)
        business_unit = opportunity.business_unit
        
        assessment_pricing = {
            'assessments': [],
            'subtotal': Decimal('0.00'),
            'iva': Decimal('0.00'),
            'total': Decimal('0.00')
        }
        
        for assessment_type in assessment_types:
            # Obtener configuración de pricing para el tipo de evaluación
            assessment_config = business_unit.pricing_config.get('assessments', {}).get(assessment_type, {})
            base_price = Decimal(str(assessment_config.get('base_price', 0)))
            
            # Calcular precio por usuario
            price_per_user = base_price * user_count
            
            assessment_data = {
                'type': assessment_type,
                'name': assessment_config.get('name', assessment_type),
                'description': assessment_config.get('description', ''),
                'price_per_user': base_price,
                'user_count': user_count,
                'subtotal': price_per_user
            }
            
            assessment_pricing['assessments'].append(assessment_data)
            assessment_pricing['subtotal'] += price_per_user
        
        # Calcular IVA y total
        assessment_pricing['iva'] = assessment_pricing['subtotal'] * Decimal('0.16')
        assessment_pricing['total'] = assessment_pricing['subtotal'] + assessment_pricing['iva']
        
        return assessment_pricing
