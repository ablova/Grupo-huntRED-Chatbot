"""
Servicio para ejecutar pagos programados desde múltiples fuentes.
"""
import logging
from typing import Dict, Any, List
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta

from app.ats.models import ScheduledPayment, ScheduledPaymentExecution, BankAccount
from app.models import PaymentTransaction  # Importar desde app.models
from app.ats.pricing.gateways import StripeGateway, PayPalGateway, ConektaGateway

logger = logging.getLogger('scheduled_payments')

class ScheduledPaymentService:
    """Servicio para gestionar y ejecutar pagos programados."""
    
    def __init__(self, business_unit):
        self.business_unit = business_unit
    
    def get_due_payments(self) -> List[ScheduledPayment]:
        """Obtiene los pagos programados que vencen hoy."""
        today = timezone.now().date()
        return ScheduledPayment.objects.filter(
            business_unit=self.business_unit,
            status='active',
            is_active=True,
            next_payment_date__date__lte=today
        )
    
    def execute_payment(self, scheduled_payment: ScheduledPayment, execution_source: str = 'system') -> Dict[str, Any]:
        """
        Ejecuta un pago programado desde diferentes fuentes.
        
        Args:
            scheduled_payment: Pago programado a ejecutar
            execution_source: Fuente de ejecución ('system', 'paypal', 'stripe', 'manual')
            
        Returns:
            Dict con el resultado de la ejecución
        """
        try:
            # Crear registro de ejecución
            execution = ScheduledPaymentExecution.objects.create(
                scheduled_payment=scheduled_payment,
                scheduled_date=scheduled_payment.next_payment_date,
                amount=scheduled_payment.amount,
                status='processing'
            )
            
            # Ejecutar según la fuente
            if execution_source == 'paypal':
                result = self._execute_via_paypal(scheduled_payment, execution)
            elif execution_source == 'stripe':
                result = self._execute_via_stripe(scheduled_payment, execution)
            elif execution_source == 'bank_transfer':
                result = self._execute_via_bank_transfer(scheduled_payment, execution)
            else:
                result = self._execute_via_system(scheduled_payment, execution)
            
            # Actualizar ejecución
            if result.get('success'):
                execution.status = 'completed'
                execution.success = True
                execution.executed_date = timezone.now()
                execution.execution_log = result
            else:
                execution.status = 'failed'
                execution.success = False
                execution.error_message = result.get('error', 'Error desconocido')
                execution.execution_log = result
            
            execution.save()
            
            return result
            
        except Exception as e:
            logger.error(f"Error ejecutando pago programado {scheduled_payment.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_via_paypal(self, scheduled_payment: ScheduledPayment, execution: ScheduledPaymentExecution) -> Dict[str, Any]:
        """Ejecuta pago programado vía PayPal."""
        try:
            # Configurar gateway PayPal
            paypal_gateway = PayPalGateway(self.business_unit.name)
            
            # Crear pago en PayPal
            payment_data = {
                'amount': float(scheduled_payment.amount),
                'currency': scheduled_payment.currency,
                'description': f"Pago programado: {scheduled_payment.name}",
                'reference_id': f"SP-{scheduled_payment.id}",
                'webhook_url': f"/webhooks/paypal/{scheduled_payment.id}/"
            }
            
            result = paypal_gateway.create_payment(**payment_data)
            
            if result.get('success'):
                # Crear transacción usando el modelo de app.models
                transaction_obj = PaymentTransaction.objects.create(
                    user=scheduled_payment.created_by.user if scheduled_payment.created_by else None,
                    amount=scheduled_payment.amount,
                    currency=scheduled_payment.currency,
                    payment_method='paypal',
                    status='completed',
                    transaction_id=f"SP-{scheduled_payment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    payment_details={
                        'scheduled_payment_id': str(scheduled_payment.id),
                        'execution_source': 'paypal',
                        'gateway_response': result
                    }
                )
                
                execution.transaction = transaction_obj
                execution.save()
                
                return {
                    'success': True,
                    'transaction_id': transaction_obj.transaction_id,
                    'paypal_order_id': result.get('id'),
                    'message': 'Pago creado en PayPal exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Error en PayPal')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_via_stripe(self, scheduled_payment: ScheduledPayment, execution: ScheduledPaymentExecution) -> Dict[str, Any]:
        """Ejecuta pago programado vía Stripe."""
        try:
            # Configurar gateway Stripe
            stripe_gateway = StripeGateway(self.business_unit.name)
            
            # Crear pago en Stripe
            payment_data = {
                'amount': float(scheduled_payment.amount),
                'currency': scheduled_payment.currency,
                'description': f"Pago programado: {scheduled_payment.name}",
                'reference_id': f"SP-{scheduled_payment.id}",
                'webhook_url': f"/webhooks/stripe/{scheduled_payment.id}/"
            }
            
            result = stripe_gateway.create_payment(**payment_data)
            
            if result.get('success'):
                # Crear transacción usando el modelo de app.models
                transaction_obj = PaymentTransaction.objects.create(
                    user=scheduled_payment.created_by.user if scheduled_payment.created_by else None,
                    amount=scheduled_payment.amount,
                    currency=scheduled_payment.currency,
                    payment_method='credit_card',
                    status='completed',
                    transaction_id=f"SP-{scheduled_payment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    payment_details={
                        'scheduled_payment_id': str(scheduled_payment.id),
                        'execution_source': 'stripe',
                        'gateway_response': result
                    }
                )
                
                execution.transaction = transaction_obj
                execution.save()
                
                return {
                    'success': True,
                    'transaction_id': transaction_obj.transaction_id,
                    'stripe_payment_intent_id': result.get('id'),
                    'message': 'Pago creado en Stripe exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Error en Stripe')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_via_bank_transfer(self, scheduled_payment: ScheduledPayment, execution: ScheduledPaymentExecution) -> Dict[str, Any]:
        """Ejecuta pago programado vía transferencia bancaria."""
        try:
            # Verificar que existe cuenta de origen
            if not scheduled_payment.source_account:
                return {
                    'success': False,
                    'error': 'No se ha configurado cuenta de origen'
                }
            
            # Aquí se integraría con el servicio bancario real
            # Por ahora simulamos la transferencia
            
            # Crear transacción usando el modelo de app.models
            transaction_obj = PaymentTransaction.objects.create(
                user=scheduled_payment.created_by.user if scheduled_payment.created_by else None,
                amount=scheduled_payment.amount,
                currency=scheduled_payment.currency,
                payment_method='bank_transfer',
                status='completed',
                transaction_id=f"SP-{scheduled_payment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                payment_details={
                    'scheduled_payment_id': str(scheduled_payment.id),
                    'execution_source': 'bank_transfer',
                    'transfer_id': f"TRF-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    'status': 'completed',
                    'message': 'Transferencia ejecutada exitosamente'
                }
            )
            
            execution.transaction = transaction_obj
            execution.save()
            
            return {
                'success': True,
                'transaction_id': transaction_obj.transaction_id,
                'transfer_id': f"TRF-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                'message': 'Transferencia bancaria ejecutada exitosamente'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_via_system(self, scheduled_payment: ScheduledPayment, execution: ScheduledPaymentExecution) -> Dict[str, Any]:
        """Ejecuta pago programado vía sistema interno."""
        try:
            # Crear transacción interna usando el modelo de app.models
            transaction_obj = PaymentTransaction.objects.create(
                user=scheduled_payment.created_by.user if scheduled_payment.created_by else None,
                amount=scheduled_payment.amount,
                currency=scheduled_payment.currency,
                payment_method='other',
                status='completed',
                transaction_id=f"SP-{scheduled_payment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                payment_details={
                    'scheduled_payment_id': str(scheduled_payment.id),
                    'execution_source': 'system',
                    'system_execution': True,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            execution.transaction = transaction_obj
            execution.save()
            
            return {
                'success': True,
                'transaction_id': transaction_obj.transaction_id,
                'message': 'Pago ejecutado por sistema exitosamente'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_next_payment_date(self, scheduled_payment: ScheduledPayment):
        """Actualiza la próxima fecha de pago."""
        scheduled_payment.next_payment_date = scheduled_payment.calculate_next_payment_date()
        
        # Verificar si debe terminar
        if scheduled_payment.end_date and scheduled_payment.next_payment_date > scheduled_payment.end_date:
            scheduled_payment.status = 'completed'
            scheduled_payment.is_active = False
        
        scheduled_payment.save()
    
    def execute_all_due_payments(self, execution_source: str = 'system') -> Dict[str, Any]:
        """
        Ejecuta todos los pagos programados que vencen hoy.
        
        Args:
            execution_source: Fuente de ejecución
            
        Returns:
            Dict con estadísticas de ejecución
        """
        due_payments = self.get_due_payments()
        stats = {
            'total': len(due_payments),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for payment in due_payments:
            result = self.execute_payment(payment, execution_source)
            
            if result.get('success'):
                stats['success'] += 1
                # Actualizar próxima fecha de pago
                self.update_next_payment_date(payment)
            else:
                stats['failed'] += 1
                stats['errors'].append({
                    'payment_id': payment.id,
                    'error': result.get('error', 'Error desconocido')
                })
        
        return stats
    
    def get_payment_schedule(self, scheduled_payment: ScheduledPayment) -> List[Dict[str, Any]]:
        """Obtiene el cronograma de pagos para un pago programado."""
        executions = ScheduledPaymentExecution.objects.filter(
            scheduled_payment=scheduled_payment
        ).order_by('scheduled_date')
        
        schedule = []
        for execution in executions:
            schedule.append({
                'scheduled_date': execution.scheduled_date,
                'executed_date': execution.executed_date,
                'amount': execution.amount,
                'status': execution.status,
                'success': execution.success,
                'error_message': execution.error_message
            })
        
        return schedule
    
    def pause_payment(self, scheduled_payment: ScheduledPayment):
        """Pausa un pago programado."""
        scheduled_payment.pause_payment()
        logger.info(f"Pago programado {scheduled_payment.id} pausado")
    
    def resume_payment(self, scheduled_payment: ScheduledPayment):
        """Reanuda un pago programado."""
        scheduled_payment.resume_payment()
        logger.info(f"Pago programado {scheduled_payment.id} reanudado")
    
    def cancel_payment(self, scheduled_payment: ScheduledPayment):
        """Cancela un pago programado."""
        scheduled_payment.cancel_payment()
        logger.info(f"Pago programado {scheduled_payment.id} cancelado")


# ============================================================================
# TAREAS CELERY PARA EJECUCIÓN AUTOMÁTICA
# ============================================================================

def execute_scheduled_payments_task():
    """Tarea Celery para ejecutar pagos programados automáticamente."""
    from app.models import BusinessUnit
    
    business_units = BusinessUnit.objects.all()
    total_stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    for business_unit in business_units:
        service = ScheduledPaymentService(business_unit)
        stats = service.execute_all_due_payments('system')
        
        total_stats['total'] += stats['total']
        total_stats['success'] += stats['success']
        total_stats['failed'] += stats['failed']
        total_stats['errors'].extend(stats['errors'])
    
    logger.info(f"Ejecución automática completada: {total_stats}")
    return total_stats


def execute_paypal_scheduled_payments_task():
    """Tarea Celery para ejecutar pagos programados vía PayPal."""
    from app.models import BusinessUnit
    
    business_units = BusinessUnit.objects.all()
    total_stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    for business_unit in business_units:
        service = ScheduledPaymentService(business_unit)
        stats = service.execute_all_due_payments('paypal')
        
        total_stats['total'] += stats['total']
        total_stats['success'] += stats['success']
        total_stats['failed'] += stats['failed']
        total_stats['errors'].extend(stats['errors'])
    
    logger.info(f"Ejecución PayPal completada: {total_stats}")
    return total_stats


def execute_stripe_scheduled_payments_task():
    """Tarea Celery para ejecutar pagos programados vía Stripe."""
    from app.models import BusinessUnit
    
    business_units = BusinessUnit.objects.all()
    total_stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    for business_unit in business_units:
        service = ScheduledPaymentService(business_unit)
        stats = service.execute_all_due_payments('stripe')
        
        total_stats['total'] += stats['total']
        total_stats['success'] += stats['success']
        total_stats['failed'] += stats['failed']
        total_stats['errors'].extend(stats['errors'])
    
    logger.info(f"Ejecución Stripe completada: {total_stats}")
    return total_stats 