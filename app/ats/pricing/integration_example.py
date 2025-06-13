# /home/pablo/app/ats/pricing/integration_example.py
"""
Ejemplo de integración del sistema de propuestas modulares con pricing avanzado.

Este archivo muestra cómo se integran todos los componentes del sistema:
1. Generación de precios con el sistema de pricing avanzado
2. Creación de propuestas modulares con secciones reutilizables
3. Personalización por Business Unit y tipo de servicio
"""

import os
import logging
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from django.test import TestCase
from django.contrib.auth import get_user_model

from app.models import BusinessUnit, Opportunity, Vacancy
from app.ats.pricing.volume_pricing import VolumePricing, RecurringServicePricing
from app.ats.pricing.progressive_billing import ProgressiveBilling
from app.ats.pricing.pricing_interface import PricingManager
from app.ats.pricing.proposal_renderer import ProposalRenderer, generate_proposal
from app.ats.pricing.talent_360_pricing import Talent360Pricing
from app.ats.pricing.models import (
    PricingStrategy,
    PricePoint,
    DiscountRule,
    ReferralFee,
    PricingCalculation,
    PricingPayment,
    PricingProposal,
    ProposalSection,
    ProposalTemplate
)
from app.ats.pricing.services import (
    PricingService,
    BillingService,
    RecommendationService
)

logger = logging.getLogger(__name__)

User = get_user_model()

class PricingIntegrationTest(TestCase):
    """Ejemplo de integración del módulo de pricing"""
    
    def setUp(self):
        """Configuración inicial"""
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear unidad de negocio
        self.business_unit = BusinessUnit.objects.create(
            name='Test Business Unit',
            owner=self.user
        )
        
        # Crear estrategia de pricing
        self.strategy = PricingStrategy.objects.create(
            name='Test Strategy',
            business_unit=self.business_unit,
            description='Test strategy description'
        )
        
        # Crear punto de precio
        self.price_point = PricePoint.objects.create(
            strategy=self.strategy,
            service_type='RECRUITMENT',
            base_price=1000.00,
            currency='USD'
        )
        
        # Crear regla de descuento
        self.discount_rule = DiscountRule.objects.create(
            strategy=self.strategy,
            service_type='RECRUITMENT',
            discount_type='PERCENTAGE',
            discount_value=10.00,
            min_amount=5000.00
        )
        
        # Crear comisión por referido
        self.referral_fee = ReferralFee.objects.create(
            strategy=self.strategy,
            service_type='RECRUITMENT',
            fee_type='PERCENTAGE',
            fee_value=5.00
        )
        
        # Crear plantilla de propuesta
        self.template = ProposalTemplate.objects.create(
            name='Test Template',
            description='Test template description',
            business_unit=self.business_unit,
            active=True
        )
    
    def test_create_proposal(self):
        """Prueba la creación de una propuesta"""
        # Crear propuesta
        proposal = PricingProposal.objects.create(
            oportunidad=self.opportunity,
            estado='BORRADOR',
            titulo='Test Proposal',
            descripcion='Test proposal description',
            monto_total=5000.00,
            moneda='USD'
        )
        
        # Crear secciones
        section1 = ProposalSection.objects.create(
            propuesta=proposal,
            tipo='INTRODUCCION',
            titulo='Introduction',
            contenido='Test introduction content',
            orden=1
        )
        
        section2 = ProposalSection.objects.create(
            propuesta=proposal,
            tipo='PRECIO',
            titulo='Pricing',
            contenido='Test pricing content',
            orden=2
        )
        
        # Verificar propuesta
        self.assertEqual(proposal.titulo, 'Test Proposal')
        self.assertEqual(proposal.estado, 'BORRADOR')
        self.assertEqual(proposal.monto_total, 5000.00)
        self.assertEqual(proposal.moneda, 'USD')
        
        # Verificar secciones
        self.assertEqual(proposal.secciones.count(), 2)
        self.assertEqual(section1.tipo, 'INTRODUCCION')
        self.assertEqual(section2.tipo, 'PRECIO')
    
    def test_calculate_price(self):
        """Prueba el cálculo de precio"""
        # Crear servicio de pricing
        service = PricingService()
        
        # Calcular precio
        result = service.calculate_price(
            business_unit=self.business_unit,
            service_type='RECRUITMENT',
            duration=30,
            complexity='MEDIUM',
            requirements=['requirement1', 'requirement2']
        )
        
        # Verificar resultado
        self.assertIn('base_price', result)
        self.assertIn('discounts', result)
        self.assertIn('total', result)
    
    def test_create_payment(self):
        """Prueba la creación de un pago"""
        # Crear servicio de facturación
        service = BillingService()
        
        # Crear pago
        result = service.create_payment(
            business_unit=self.business_unit,
            amount=5000.00,
            currency='USD',
            payment_method='CREDIT_CARD',
            metadata={'test': 'data'}
        )
        
        # Verificar resultado
        self.assertIn('payment_id', result)
        self.assertIn('status', result)
        self.assertIn('amount', result)
    
    def test_get_recommendations(self):
        """Prueba la obtención de recomendaciones"""
        # Crear servicio de recomendaciones
        service = RecommendationService()
        
        # Obtener recomendaciones
        result = service.get_recommendations(
            business_unit=self.business_unit,
            service_type='RECRUITMENT',
            market_data={'test': 'data'},
            historical_data={'test': 'data'}
        )
        
        # Verificar resultado
        self.assertIn('price_points', result)
        self.assertIn('discounts', result)
        self.assertIn('referral_fees', result)
        self.assertIn('market_analysis', result)
        self.assertIn('historical_analysis', result)


def generate_talent_360_proposal_example(opportunity_id, output_format='html', output_file=None):
    """
    Genera una propuesta completa para el servicio de Análisis de Talento 360°.
    
    Este ejemplo muestra la integración del sistema de pricing avanzado con 
    propuestas modulares para el servicio de Análisis de Talento 360°.
    
    Args:
        opportunity_id: ID de la oportunidad
        output_format: Formato de salida ('html', 'pdf')
        output_file: Ruta donde guardar el archivo generado (opcional)
        
    Returns:
        str: Contenido HTML o ruta del archivo generado
    """
    try:
        # 1. Obtener datos de la oportunidad
        opportunity = Opportunity.objects.get(id=opportunity_id)
        business_unit = opportunity.business_unit
        company_name = opportunity.company_name
        contact = opportunity.contact
        
        # 2. Calcular pricing con el sistema avanzado
        user_count = opportunity.headcount or 10  # Default a 10 si no está especificado
        pricing_data = Talent360Pricing.calculate_total(user_count=user_count, include_iva=True)
        
        # 3. Generar plan de pagos progresivos
        payment_schedule = ProgressiveBilling.generate_payment_schedule(
            business_unit_name=business_unit.name,
            start_date=timezone.now().date(),
            contract_amount=pricing_data['total'],
            service_type='talent_analysis'
        )
        
        # 4. Crear los datos completos para la propuesta
        proposal_data = {
            'company': {
                'name': company_name,
                'logo': None,  # En un caso real se obtendría del sistema
                'contact': {
                    'name': contact.name if contact else None,
                    'email': contact.email if contact else None,
                    'phone': contact.phone if contact else None
                }
            },
            'service': {
                'name': 'Análisis de Talento 360°',
                'type': 'talent_analysis',
                'description': 'Evaluación integral de competencias y habilidades para optimizar el talento organizacional',
                'provider': 'huntRED® Solutions',
                'features': [
                    'Evaluación de competencias técnicas y blandas',
                    'Análisis de alineación con valores organizacionales',
                    'Identificación de áreas de oportunidad y desarrollo',
                    'Recomendaciones personalizadas de desarrollo',
                    'Dashboard interactivo para seguimiento de KPIs',
                    'Reportes comparativos por equipos y departamentos'
                ],
                'benefits': [
                    'Optimización de procesos de selección y retención',
                    'Reducción de costos de rotación',
                    'Mejora en la productividad y clima organizacional',
                    'Alineación del talento con la estrategia de negocio',
                    'Desarrollo de planes de carrera personalizados'
                ],
                'process': [
                    {'step': 1, 'name': 'Diagnóstico', 'description': 'Análisis de necesidades y objetivos organizacionales'},
                    {'step': 2, 'name': 'Implementación', 'description': 'Lanzamiento y seguimiento del proceso de evaluación'},
                    {'step': 3, 'name': 'Análisis', 'description': 'Procesamiento y análisis de resultados'},
                    {'step': 4, 'name': 'Reporte', 'description': 'Generación de informes y recomendaciones'},
                    {'step': 5, 'name': 'Seguimiento', 'description': 'Plan de acción y monitoreo de resultados'}
                ]
            },
            'pricing': pricing_data,
            'payment_schedule': payment_schedule,
            'business_unit': {
                'id': business_unit.id,
                'name': business_unit.name
            },
            'service_type': 'talent_analysis',
            'consultant': {
                'name': 'Pablo Lledó',
                'email': 'pablo@grupohuntred.com',
                'position': 'Consultor Senior'
            },
            'opportunities': [
                {
                    'id': opportunity.id,
                    'name': opportunity.name,
                    'description': opportunity.description
                }
            ]
        }
        
        # 5. Generar la propuesta modular con las secciones configuradas
        # Usar configuración predefinida para Talent 360
        from app.ats.pricing.config import PROPOSAL_PRESETS
        preset = PROPOSAL_PRESETS.get('talent_360', {})
        template_type = preset.get('template', 'standard')
        sections = preset.get('sections', None)
        
        # 6. Renderizar y devolver la propuesta
        return generate_proposal(
            proposal_data=proposal_data,
            sections=sections,
            template_type=template_type,
            output_format=output_format,
            output_file=output_file
        )
        
    except Opportunity.DoesNotExist:
        logger.error(f"No se encontró la oportunidad con ID {opportunity_id}")
        raise ValueError(f"No se encontró la oportunidad con ID {opportunity_id}")
    except Exception as e:
        logger.error(f"Error al generar propuesta: {str(e)}")
        raise


def generate_recruitment_proposal_example(opportunity_id, output_format='html', output_file=None):
    """
    Genera una propuesta completa para servicios de reclutamiento con múltiples vacantes.
    
    Este ejemplo muestra cómo usar el sistema de pricing por volumen para múltiples
    vacantes en diferentes posiciones, con descuentos progresivos.
    
    Args:
        opportunity_id: ID de la oportunidad
        output_format: Formato de salida ('html', 'pdf')
        output_file: Ruta donde guardar el archivo generado (opcional)
        
    Returns:
        str: Contenido HTML o ruta del archivo generado
    """
    try:
        # 1. Obtener datos de la oportunidad y vacantes
        opportunity = Opportunity.objects.get(id=opportunity_id)
        business_unit = opportunity.business_unit
        vacancies = Vacancy.objects.filter(opportunity=opportunity)
        
        # 2. Procesar datos para el cálculo de pricing por volumen
        vacancy_groups = []
        for vacancy in vacancies:
            # Agrupar por posición
            position_exists = False
            for group in vacancy_groups:
                if group['position_id'] == vacancy.position_id:
                    group['count'] += 1
                    position_exists = True
                    break
            
            if not position_exists:
                # Base price: porcentaje del salario máximo según BU
                base_price = Decimal(str(vacancy.salary_range_max * 0.15))  # Ejemplo: 15% del salario
                vacancy_groups.append({
                    'position_id': vacancy.position_id,
                    'position_name': vacancy.position_name,
                    'count': 1,
                    'base_price': base_price
                })
        
        # 3. Calcular pricing con descuentos por volumen
        pricing_data = VolumePricing.calculate_volume_pricing(
            business_unit_name=business_unit.name,
            vacancies=vacancy_groups
        )
        
        # 4. Generar plan de pagos progresivos
        payment_schedule = ProgressiveBilling.generate_payment_schedule(
            business_unit_name=business_unit.name,
            start_date=timezone.now().date(),
            contract_amount=pricing_data['total'],
            service_type='recruitment'
        )
        
        # 5. Crear los datos completos para la propuesta
        proposal_data = {
            'company': {
                'name': opportunity.company_name,
                'logo': None,
                'contact': {
                    'name': opportunity.contact.name if opportunity.contact else None,
                    'email': opportunity.contact.email if opportunity.contact else None,
                    'phone': opportunity.contact.phone if opportunity.contact else None
                }
            },
            'service': {
                'name': 'Servicios de Reclutamiento y Selección',
                'type': 'recruitment',
                'description': 'Solución integral para la identificación y selección de talento alineado con los valores y objetivos de su organización',
                'provider': business_unit.name,
                'features': [
                    'Búsqueda especializada por posición',
                    'Evaluación integral de candidatos',
                    'Background checks',
                    'Garantía de reemplazo',
                    'Seguimiento post-contratación'
                ],
                'benefits': [
                    'Reducción del tiempo de contratación',
                    'Disminución de costos de rotación',
                    'Acceso a talento pre-evaluado',
                    'Proceso de selección estructurado y eficiente',
                    'Acompañamiento durante todo el proceso'
                ]
            },
            'pricing': pricing_data,
            'payment_schedule': payment_schedule,
            'business_unit': {
                'id': business_unit.id,
                'name': business_unit.name
            },
            'service_type': 'recruitment',
            'vacancies': [
                {
                    'position_name': group['position_name'],
                    'count': group['count'],
                    'base_price': group['base_price']
                } for group in vacancy_groups
            ]
        }
        
        # 6. Generar la propuesta modular con las secciones configuradas
        # Usar configuración predefinida para Recruitment
        from app.ats.pricing.config import PROPOSAL_PRESETS
        preset = PROPOSAL_PRESETS.get('recruitment', {})
        template_type = preset.get('template', 'standard')
        sections = preset.get('sections', None)
        
        # 7. Renderizar y devolver la propuesta
        return generate_proposal(
            proposal_data=proposal_data,
            sections=sections,
            template_type=template_type,
            output_format=output_format,
            output_file=output_file
        )
        
    except Opportunity.DoesNotExist:
        logger.error(f"No se encontró la oportunidad con ID {opportunity_id}")
        raise ValueError(f"No se encontró la oportunidad con ID {opportunity_id}")
    except Exception as e:
        logger.error(f"Error al generar propuesta: {str(e)}")
        raise


def ejemplo_uso_sistema_completo():
    """
    Muestra el flujo completo de uso del sistema integrado de pricing y propuestas.
    """
    print("# EJEMPLO DE USO DEL SISTEMA INTEGRADO DE PRICING Y PROPUESTAS")
    print("\n## 1. Cálculo de pricing con el sistema avanzado")
    print("Supongamos que tenemos una oportunidad de Análisis de Talento 360° para 50 usuarios")
    
    # Ejemplo de cálculo de pricing para Talento 360°
    pricing_talent_360 = Talent360Pricing.calculate_total(user_count=50, include_iva=True)
    print(f"Precio base por usuario: ${pricing_talent_360['base_price']}")
    print(f"Descuento aplicado: {pricing_talent_360['discount_percentage']}%")
    print(f"Precio con descuento por usuario: ${pricing_talent_360['price_per_user']}")
    print(f"Subtotal: ${pricing_talent_360['subtotal']}")
    print(f"IVA: ${pricing_talent_360['iva']}")
    print(f"Total: ${pricing_talent_360['total']}")
    
    print("\n## 2. Generación de plan de pagos con facturación progresiva")
    # Ejemplo de cálculo de plan de pagos
    payment_schedule = ProgressiveBilling.generate_payment_schedule(
        business_unit_name='huntRED',
        start_date=timezone.now().date(),
        contract_amount=pricing_talent_360['total'],
        service_type='talent_analysis'
    )
    print(f"Plan de pagos generado con {len(payment_schedule['milestones'])} hitos")
    for i, milestone in enumerate(payment_schedule['milestones'], 1):
        print(f"Hito {i}: {milestone['description']} - ${milestone['amount']} - {milestone['due_date']}")
    
    print("\n## 3. Generación de propuesta modular")
    print("La propuesta se generaría utilizando las secciones configuradas en PROPOSAL_PRESETS['talent_360']")
    from app.ats.pricing.config import PROPOSAL_PRESETS
    sections = PROPOSAL_PRESETS.get('talent_360', {}).get('sections', [])
    print(f"Secciones incluidas: {', '.join(sections)}")
    
    print("\n## 4. Las propuestas mantienen la estructura que te gusta")
    print("Con las secciones modulares, mantenemos el diseño que te gusta de proposal_template.html")
    print("pero ahora podemos reutilizar secciones como la portada entre diferentes tipos de propuestas.")
    
    print("\n## 5. Ventajas del nuevo sistema")
    print("- Propuestas consistentes en todas las Business Units")
    print("- Reutilización de secciones entre diferentes tipos de propuestas")
    print("- Personalización por BU con colores y logos específicos")
    print("- Integración con el sistema de pricing avanzado")
    print("- Mantenimiento del diseño que te gusta, pero más flexible y modular")


if __name__ == "__main__":
    # Este código solo se ejecuta si se ejecuta el archivo directamente
    ejemplo_uso_sistema_completo()
