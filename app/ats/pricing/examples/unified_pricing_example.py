# /home/pablo/app/ats/pricing/examples/unified_pricing_example.py
"""
Ejemplo de uso del sistema unificado de Pricing & Pagos.

Este archivo muestra cómo utilizar el UnifiedPricingService para gestionar
todos los aspectos del sistema de precios y pagos.
"""

import logging
from decimal import Decimal
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model

from app.models import (
    Service, BusinessUnit, Person, Company,
    PaymentSchedule, Payment, PaymentTransaction
)
from app.ats.pricing.services import UnifiedPricingService

logger = logging.getLogger(__name__)
User = get_user_model()

class UnifiedPricingExample:
    """
    Ejemplo completo de uso del sistema unificado de pricing y pagos.
    """
    
    def __init__(self):
        self.pricing_service = UnifiedPricingService()
    
    def create_sample_services(self, business_unit: BusinessUnit):
        """
        Crea servicios de ejemplo para una unidad de negocio.
        
        Args:
            business_unit: Unidad de negocio
        """
        services = [
            {
                'name': 'Reclutamiento Especializado',
                'description': 'Servicio completo de reclutamiento y selección',
                'service_type': 'recruitment',
                'billing_type': 'percentage',
                'base_price': Decimal('15.00'),  # 15% del salario anual
                'currency': 'MXN',
                'features': [
                    'Análisis de perfil',
                    'Búsqueda de candidatos',
                    'Evaluación técnica',
                    'Entrevistas',
                    'Presentación de candidatos'
                ],
                'requirements': [
                    'Descripción de puesto detallada',
                    'Perfil de competencias',
                    'Salario objetivo'
                ],
                'deliverables': [
                    'Reporte de candidatos',
                    'Evaluaciones técnicas',
                    'Recomendaciones finales'
                ],
                'payment_terms': 'net30',
                'payment_methods': ['TRANSFER', 'CARD'],
                'default_milestones': [
                    {'name': 'Anticipo', 'percentage': 25, 'days_offset': 0},
                    {'name': 'Pago Final', 'percentage': 75, 'days_offset': 30}
                ]
            },
            {
                'name': 'Análisis de Talento 360°',
                'description': 'Evaluación integral de competencias y habilidades',
                'service_type': 'talent_analysis',
                'billing_type': 'fixed',
                'base_price': Decimal('5000.00'),
                'currency': 'MXN',
                'features': [
                    'Evaluación de competencias',
                    'Análisis de personalidad',
                    'Assessment técnico',
                    'Reporte detallado',
                    'Recomendaciones de desarrollo'
                ],
                'requirements': [
                    'Perfil del candidato',
                    'Puesto objetivo',
                    'Competencias a evaluar'
                ],
                'deliverables': [
                    'Reporte de evaluación',
                    'Perfil de competencias',
                    'Plan de desarrollo'
                ],
                'payment_terms': 'net15',
                'payment_methods': ['TRANSFER', 'CARD'],
                'default_milestones': [
                    {'name': 'Pago Único', 'percentage': 100, 'days_offset': 0}
                ]
            },
            {
                'name': 'Consultoría de HR',
                'description': 'Asesoría especializada en recursos humanos',
                'service_type': 'consulting',
                'billing_type': 'hourly',
                'base_price': Decimal('800.00'),
                'currency': 'MXN',
                'features': [
                    'Análisis organizacional',
                    'Diseño de políticas',
                    'Implementación de procesos',
                    'Capacitación',
                    'Seguimiento'
                ],
                'requirements': [
                    'Descripción del proyecto',
                    'Objetivos específicos',
                    'Alcance del trabajo'
                ],
                'deliverables': [
                    'Diagnóstico organizacional',
                    'Propuesta de mejora',
                    'Plan de implementación'
                ],
                'payment_terms': 'net30',
                'payment_methods': ['TRANSFER', 'CARD'],
                'default_milestones': [
                    {'name': 'Anticipo', 'percentage': 50, 'days_offset': 0},
                    {'name': 'Pago Final', 'percentage': 50, 'days_offset': 30}
                ]
            }
        ]
        
        created_services = []
        for service_data in services:
            service = Service.objects.create(
                business_unit=business_unit,
                **service_data
            )
            created_services.append(service)
            logger.info(f"Servicio creado: {service.name}")
        
        return created_services
    
    def calculate_service_pricing_example(self, service: Service):
        """
        Ejemplo de cálculo de precios para diferentes tipos de servicios.
        
        Args:
            service: Servicio a calcular
        """
        logger.info(f"\n=== Cálculo de Precios para {service.name} ===")
        
        if service.billing_type == 'percentage':
            # Ejemplo: Reclutamiento (15% del salario anual)
            annual_salary = Decimal('600000.00')  # 50k mensual
            pricing = self.pricing_service.calculate_service_price(
                service=service,
                base_amount=annual_salary,
                quantity=1
            )
            logger.info(f"Salario anual: {annual_salary} MXN")
            logger.info(f"Comisión ({service.base_price}%): {pricing['calculation']['total']} MXN")
            
        elif service.billing_type == 'fixed':
            # Ejemplo: Análisis de Talento 360°
            pricing = self.pricing_service.calculate_service_price(
                service=service,
                quantity=1
            )
            logger.info(f"Precio fijo: {pricing['calculation']['total']} MXN")
            
        elif service.billing_type == 'hourly':
            # Ejemplo: Consultoría (800 MXN/hora)
            hours = 20
            pricing = self.pricing_service.calculate_service_price(
                service=service,
                duration=hours,
                quantity=1
            )
            logger.info(f"Horas: {hours}")
            logger.info(f"Total: {pricing['calculation']['total']} MXN")
        
        return pricing
    
    def create_payment_schedule_example(self, service: Service, client: Person, total_amount: Decimal):
        """
        Ejemplo de creación de programación de pagos.
        
        Args:
            service: Servicio
            client: Cliente
            total_amount: Monto total
        """
        logger.info(f"\n=== Creando Programación de Pagos ===")
        logger.info(f"Servicio: {service.name}")
        logger.info(f"Cliente: {client.nombre}")
        logger.info(f"Monto total: {total_amount} {service.currency}")
        
        # Crear programación de pagos
        schedule = self.pricing_service.create_payment_schedule(
            service=service,
            client=client,
            total_amount=total_amount,
            payment_structure='standard'
        )
        
        logger.info(f"Programación creada: {schedule.id}")
        logger.info(f"Estado: {schedule.status}")
        
        # Mostrar pagos creados
        for payment in schedule.payments.all():
            logger.info(f"  - Pago {payment.id}: {payment.amount} MXN - Vence: {payment.due_date}")
        
        return schedule
    
    def process_payment_example(self, payment: Payment):
        """
        Ejemplo de procesamiento de un pago.
        
        Args:
            payment: Pago a procesar
        """
        logger.info(f"\n=== Procesando Pago ===")
        logger.info(f"Pago ID: {payment.id}")
        logger.info(f"Monto: {payment.amount} MXN")
        logger.info(f"Estado actual: {payment.status}")
        
        # Simular procesamiento de pago
        transaction = self.pricing_service.process_payment(
            payment=payment,
            payment_method='TRANSFER',
            transaction_id=f"TXN_{payment.id}_{int(timezone.now().timestamp())}",
            metadata={
                'payment_gateway': 'internal',
                'processing_time': '2.5s',
                'reference': f"REF_{payment.id}"
            }
        )
        
        logger.info(f"Transacción creada: {transaction.transaction_id}")
        logger.info(f"Estado del pago: {payment.status}")
        
        return transaction
    
    def dashboard_example(self, business_unit: BusinessUnit = None):
        """
        Ejemplo de obtención de datos del dashboard.
        
        Args:
            business_unit: Unidad de negocio (opcional)
        """
        logger.info(f"\n=== Dashboard de Pricing & Pagos ===")
        
        # Obtener estadísticas
        stats = self.pricing_service.get_payment_dashboard_data(
            business_unit=business_unit,
            date_from=timezone.now().date() - timezone.timedelta(days=30),
            date_to=timezone.now().date()
        )
        
        logger.info("Estadísticas del último mes:")
        logger.info(f"  - Total de pagos: {stats['total_payments']}")
        logger.info(f"  - Monto total: {stats['total_amount']} MXN")
        logger.info(f"  - Pagos realizados: {stats['paid_payments']}")
        logger.info(f"  - Monto pagado: {stats['paid_amount']} MXN")
        logger.info(f"  - Pagos pendientes: {stats['pending_payments']}")
        logger.info(f"  - Monto pendiente: {stats['pending_amount']} MXN")
        logger.info(f"  - Pagos vencidos: {stats['overdue_payments']}")
        logger.info(f"  - Monto vencido: {stats['overdue_amount']} MXN")
        
        return stats
    
    def run_complete_example(self):
        """
        Ejecuta un ejemplo completo del sistema unificado.
        """
        logger.info("=== INICIANDO EJEMPLO COMPLETO DE PRICING & PAGOS ===")
        
        try:
            # 1. Obtener o crear Business Unit
            business_unit, created = BusinessUnit.objects.get_or_create(
                name='huntRED',
                defaults={
                    'code': 'HR',
                    'description': 'Unidad de negocio principal',
                    'active': True
                }
            )
            
            # 2. Crear servicios de ejemplo
            services = self.create_sample_services(business_unit)
            
            # 3. Obtener o crear cliente de ejemplo
            client, created = Person.objects.get_or_create(
                email='cliente@ejemplo.com',
                defaults={
                    'nombre': 'Juan Pérez',
                    'apellido_paterno': 'Pérez',
                    'apellido_materno': 'García'
                }
            )
            
            # 4. Calcular precios para cada servicio
            for service in services:
                pricing = self.calculate_service_pricing_example(service)
                
                # 5. Crear programación de pagos
                schedule = self.create_payment_schedule_example(
                    service=service,
                    client=client,
                    total_amount=pricing['calculation']['total']
                )
                
                # 6. Procesar el primer pago como ejemplo
                first_payment = schedule.payments.first()
                if first_payment:
                    self.process_payment_example(first_payment)
            
            # 7. Mostrar dashboard
            self.dashboard_example(business_unit)
            
            logger.info("=== EJEMPLO COMPLETADO EXITOSAMENTE ===")
            
        except Exception as e:
            logger.error(f"Error en el ejemplo: {e}")
            raise

# Ejemplo de uso en tests
class UnifiedPricingTestCase(TestCase):
    """Test case para el sistema unificado de pricing y pagos."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.business_unit = BusinessUnit.objects.create(
            name='huntRED',
            code='HR',
            description='Unidad de negocio de prueba',
            active=True,
            owner=self.user
        )
        
        self.client = Person.objects.create(
            nombre='Cliente Test',
            email='cliente@test.com'
        )
        
        self.pricing_service = UnifiedPricingService(self.business_unit)
    
    def test_service_creation(self):
        """Test de creación de servicios."""
        service = Service.objects.create(
            name='Servicio de Prueba',
            description='Descripción de prueba',
            service_type='recruitment',
            billing_type='fixed',
            base_price=Decimal('1000.00'),
            business_unit=self.business_unit,
            created_by=self.user
        )
        
        self.assertEqual(service.name, 'Servicio de Prueba')
        self.assertEqual(service.base_price, Decimal('1000.00'))
        self.assertEqual(service.status, 'active')
    
    def test_pricing_calculation(self):
        """Test de cálculo de precios."""
        service = Service.objects.create(
            name='Servicio de Prueba',
            service_type='recruitment',
            billing_type='fixed',
            base_price=Decimal('1000.00'),
            business_unit=self.business_unit,
            created_by=self.user
        )
        
        pricing = self.pricing_service.calculate_service_price(service)
        
        self.assertIn('calculation', pricing)
        self.assertIn('total', pricing['calculation'])
        self.assertEqual(pricing['calculation']['subtotal'], Decimal('1000.00'))
    
    def test_payment_schedule_creation(self):
        """Test de creación de programación de pagos."""
        service = Service.objects.create(
            name='Servicio de Prueba',
            service_type='recruitment',
            billing_type='fixed',
            base_price=Decimal('1000.00'),
            business_unit=self.business_unit,
            created_by=self.user
        )
        
        schedule = self.pricing_service.create_payment_schedule(
            service=service,
            client=self.client,
            total_amount=Decimal('1000.00')
        )
        
        self.assertEqual(schedule.service, service)
        self.assertEqual(schedule.client, self.client)
        self.assertEqual(schedule.total_amount, Decimal('1000.00'))
        self.assertTrue(schedule.payments.exists())
    
    def test_payment_processing(self):
        """Test de procesamiento de pagos."""
        service = Service.objects.create(
            name='Servicio de Prueba',
            service_type='recruitment',
            billing_type='fixed',
            base_price=Decimal('1000.00'),
            business_unit=self.business_unit,
            created_by=self.user
        )
        
        schedule = self.pricing_service.create_payment_schedule(
            service=service,
            client=self.client,
            total_amount=Decimal('1000.00')
        )
        
        payment = schedule.payments.first()
        transaction = self.pricing_service.process_payment(
            payment=payment,
            payment_method='TRANSFER',
            transaction_id='TEST_TXN_001'
        )
        
        self.assertEqual(transaction.status, 'completed')
        self.assertEqual(payment.status, 'PAID')
        self.assertIsNotNone(payment.payment_date)

if __name__ == '__main__':
    # Ejecutar ejemplo
    example = UnifiedPricingExample()
    example.run_complete_example() 