"""
Servicio unificado de Pricing & Pagos para Grupo huntRED®.

Este módulo proporciona una interfaz unificada para gestionar todos los aspectos
del sistema de precios y pagos, integrando los diferentes componentes existentes.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from app.models import (
    Service, BusinessUnit, Person, Company, 
    PaymentSchedule, Payment, PaymentTransaction,
    PaymentMilestone, PaymentNotification
)
from app.ats.pricing.models import (
    PricingCalculation, PricingPayment,
    PricingStrategy, PricePoint, DiscountRule
)
from app.ats.pricing.progressive_billing import ProgressiveBilling
from app.ats.pricing.volume_pricing import VolumePricing, RecurringServicePricing
from app.ats.pricing.services.billing_service import BillingService

logger = logging.getLogger(__name__)

class UnifiedPricingService:
    """
    Servicio unificado para gestionar pricing y pagos.
    
    Integra todos los componentes del sistema de precios y pagos:
    - Cálculo de precios
    - Gestión de descuentos
    - Programación de pagos
    - Facturación progresiva
    - Notificaciones
    - Transacciones
    """
    
    def __init__(self, business_unit: BusinessUnit = None):
        self.business_unit = business_unit
        self.billing_service = BillingService()
    
    def calculate_service_price(
        self,
        service: Service,
        quantity: int = 1,
        duration: Optional[int] = None,
        base_amount: Optional[Decimal] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Calcula el precio de un servicio considerando todos los factores.
        
        Args:
            service: Servicio a calcular
            quantity: Cantidad de unidades
            duration: Duración (horas, días, meses según billing_type)
            base_amount: Monto base para cálculos de porcentaje
            **kwargs: Parámetros adicionales
            
        Returns:
            Dict con el desglose completo del pricing
        """
        try:
            # Precio base según tipo de facturación
            if service.billing_type == 'percentage' and base_amount:
                base_price = (service.base_price * base_amount) / 100
            elif service.billing_type in ['hourly', 'daily', 'monthly'] and duration:
                base_price = service.base_price * duration
            elif service.billing_type == 'recurring' and duration:
                base_price = service.base_price * duration
            else:
                base_price = service.base_price
            
            # Aplicar cantidad
            subtotal = base_price * quantity
            
            # Aplicar descuentos por volumen
            volume_discount = self._calculate_volume_discount(subtotal, quantity)
            subtotal_after_volume = subtotal - volume_discount
            
            # Aplicar descuentos por lealtad
            loyalty_discount = self._calculate_loyalty_discount(
                subtotal_after_volume, 
                kwargs.get('client_id')
            )
            subtotal_after_loyalty = subtotal_after_volume - loyalty_discount
            
            # Aplicar descuentos por estrategia de pricing
            strategy_discount = self._calculate_strategy_discount(
                subtotal_after_loyalty,
                service,
                kwargs.get('opportunity_id')
            )
            subtotal_after_strategy = subtotal_after_loyalty - strategy_discount
            
            # Calcular IVA
            iva = subtotal_after_strategy * Decimal('0.16')
            total = subtotal_after_strategy + iva
            
            return {
                'service': {
                    'id': service.id,
                    'name': service.name,
                    'type': service.service_type,
                    'billing_type': service.billing_type,
                    'base_price': service.base_price,
                    'currency': service.currency
                },
                'calculation': {
                    'quantity': quantity,
                    'duration': duration,
                    'base_amount': base_amount,
                    'subtotal': subtotal,
                    'volume_discount': volume_discount,
                    'loyalty_discount': loyalty_discount,
                    'strategy_discount': strategy_discount,
                    'subtotal_after_discounts': subtotal_after_strategy,
                    'iva': iva,
                    'total': total
                },
                'payment_terms': service.payment_terms,
                'payment_methods': service.payment_methods,
                'created_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculando precio para servicio {service.id}: {e}")
            raise ValidationError(f"Error en cálculo de precio: {e}")
    
    def create_payment_schedule(
        self,
        service: Service,
        client: Person,
        total_amount: Decimal,
        payment_structure: str = 'standard',
        start_date: Optional[timezone.date] = None,
        custom_milestones: Optional[List[Dict]] = None
    ) -> PaymentSchedule:
        """
        Crea una programación de pagos para un servicio.
        
        Args:
            service: Servicio asociado
            client: Cliente
            total_amount: Monto total
            payment_structure: Estructura de pagos
            start_date: Fecha de inicio
            custom_milestones: Hitos personalizados
            
        Returns:
            PaymentSchedule creado
        """
        if start_date is None:
            start_date = timezone.now().date()
        
        # Crear programación de pagos
        schedule = PaymentSchedule.objects.create(
            service=service,
            client=client,
            total_amount=total_amount,
            schedule_type='INSTALLMENTS',
            start_date=start_date,
            frequency='MONTHLY',
            status='PENDING'
        )
        
        # Generar hitos de pago
        if custom_milestones:
            milestones = custom_milestones
        else:
            milestones = self._get_default_milestones(service, payment_structure)
        
        # Crear pagos individuales
        for i, milestone in enumerate(milestones, 1):
            amount = (total_amount * Decimal(str(milestone['percentage']))) / 100
            due_date = start_date + timezone.timedelta(days=milestone['days_offset'])
            
            Payment.objects.create(
                schedule=schedule,
                amount=amount,
                due_date=due_date,
                payment_method='TRANSFER',
                status='PENDING',
                notes=f"Hito {i}: {milestone['name']}"
            )
        
        return schedule
    
    def process_payment(
        self,
        payment: Payment,
        payment_method: str,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        metadata: Optional[Dict] = None
    ) -> PaymentTransaction:
        """
        Procesa un pago y crea la transacción correspondiente.
        
        Args:
            payment: Pago a procesar
            payment_method: Método de pago
            transaction_id: ID de la transacción
            amount: Monto (si es diferente al programado)
            metadata: Metadatos adicionales
            
        Returns:
            PaymentTransaction creado
        """
        if amount is None:
            amount = payment.amount
        
        with transaction.atomic():
            # Crear transacción
            payment_transaction = PaymentTransaction.objects.create(
                user=payment.schedule.client.user if hasattr(payment.schedule.client, 'user') else None,
                amount=amount,
                currency=payment.schedule.service.currency,
                payment_method=payment_method,
                status='completed',
                transaction_id=transaction_id,
                payment_details=metadata or {}
            )
            
            # Actualizar estado del pago
            payment.payment_date = timezone.now()
            payment.status = 'PAID'
            payment.transaction_id = transaction_id
            payment.save()
            
            # Verificar si todos los pagos están completados
            all_payments = payment.schedule.payments.all()
            if all_payments.filter(status='PAID').count() == all_payments.count():
                payment.schedule.status = 'COMPLETED'
                payment.schedule.save()
            
            # Enviar notificación de recibo
            self._send_payment_receipt(payment, payment_transaction)
            
            return payment_transaction
    
    def get_payment_dashboard_data(
        self,
        business_unit: Optional[BusinessUnit] = None,
        date_from: Optional[timezone.date] = None,
        date_to: Optional[timezone.date] = None
    ) -> Dict[str, Any]:
        """
        Obtiene datos para el dashboard de pagos.
        
        Args:
            business_unit: Unidad de negocio (opcional)
            date_from: Fecha desde
            date_to: Fecha hasta
            
        Returns:
            Dict con estadísticas de pagos
        """
        filters = {}
        if business_unit:
            filters['schedule__service__business_unit'] = business_unit
        if date_from:
            filters['due_date__gte'] = date_from
        if date_to:
            filters['due_date__lte'] = date_to
        
        payments = Payment.objects.filter(**filters)
        
        return {
            'total_payments': payments.count(),
            'total_amount': payments.aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0'),
            'paid_payments': payments.filter(status='PAID').count(),
            'paid_amount': payments.filter(status='PAID').aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0'),
            'pending_payments': payments.filter(status='PENDING').count(),
            'pending_amount': payments.filter(status='PENDING').aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0'),
            'overdue_payments': payments.filter(status='OVERDUE').count(),
            'overdue_amount': payments.filter(status='OVERDUE').aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0'),
            'payment_schedules': PaymentSchedule.objects.filter(**filters).count(),
            'active_schedules': PaymentSchedule.objects.filter(
                status='ACTIVE', **filters
            ).count(),
            'completed_schedules': PaymentSchedule.objects.filter(
                status='COMPLETED', **filters
            ).count()
        }
    
    def send_payment_reminders(self) -> List[PaymentNotification]:
        """
        Envía recordatorios de pagos próximos a vencer.
        
        Returns:
            Lista de notificaciones enviadas
        """
        today = timezone.now().date()
        upcoming_payments = Payment.objects.filter(
            due_date__lte=today + timezone.timedelta(days=7),
            status='PENDING'
        )
        
        notifications = []
        for payment in upcoming_payments:
            notification = self._send_payment_reminder(payment)
            if notification:
                notifications.append(notification)
        
        return notifications
    
    def _calculate_volume_discount(self, subtotal: Decimal, quantity: int) -> Decimal:
        """Calcula descuento por volumen"""
        if quantity >= 5:
            return subtotal * Decimal('0.10')  # 10% descuento
        elif quantity >= 3:
            return subtotal * Decimal('0.05')  # 5% descuento
        return Decimal('0')
    
    def _calculate_loyalty_discount(self, subtotal: Decimal, client_id: Optional[int]) -> Decimal:
        """Calcula descuento por lealtad"""
        if not client_id:
            return Decimal('0')
        
        # Aquí podrías implementar lógica más compleja basada en historial
        return Decimal('0')
    
    def _calculate_strategy_discount(self, subtotal: Decimal, service: Service, opportunity_id: Optional[int]) -> Decimal:
        """Calcula descuento por estrategia de pricing"""
        # Implementar lógica de descuentos estratégicos
        return Decimal('0')
    
    def _get_default_milestones(self, service: Service, payment_structure: str) -> List[Dict]:
        """Obtiene hitos por defecto según la estructura de pago"""
        if payment_structure == 'standard':
            return [
                {'name': 'Anticipo', 'percentage': 25, 'days_offset': 0},
                {'name': 'Pago Final', 'percentage': 75, 'days_offset': 30}
            ]
        elif payment_structure == 'extended':
            return [
                {'name': 'Anticipo 1', 'percentage': 17.5, 'days_offset': 0},
                {'name': 'Anticipo 2', 'percentage': 17.5, 'days_offset': 15},
                {'name': 'Pago Final', 'percentage': 65, 'days_offset': 30}
            ]
        else:  # recurring
            return [
                {'name': 'Anticipo', 'percentage': 35, 'days_offset': 0},
                {'name': 'Pago 1', 'percentage': 32.5, 'days_offset': 30},
                {'name': 'Pago 2', 'percentage': 32.5, 'days_offset': 60}
            ]
    
    def _send_payment_receipt(self, payment: Payment, transaction: PaymentTransaction):
        """Envía recibo de pago"""
        try:
            PaymentNotification.objects.create(
                payment=payment,
                notification_type='PAID',
                recipient=payment.schedule.client,
                message=f"Recibo por pago de {payment.amount} {payment.schedule.service.currency}",
                sent_at=timezone.now(),
                status='SENT'
            )
        except Exception as e:
            logger.error(f"Error enviando recibo: {e}")
    
    def _send_payment_reminder(self, payment: Payment) -> Optional[PaymentNotification]:
        """Envía recordatorio de pago"""
        try:
            notification = PaymentNotification.objects.create(
                payment=payment,
                notification_type='DUE',
                recipient=payment.schedule.client,
                message=f"Recordatorio: Pago de {payment.amount} vence el {payment.due_date}",
                sent_at=timezone.now(),
                status='SENT'
            )
            return notification
        except Exception as e:
            logger.error(f"Error enviando recordatorio: {e}")
            return None 