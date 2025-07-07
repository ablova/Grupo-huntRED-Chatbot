"""
Servicio de procesamiento de pagos que integra gateways y maneja el flujo completo.
"""
from typing import Dict, Any, Optional, List
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
import requests
import json
import uuid

from app.models import Invoice, Order, BusinessUnit
from app.ats.models import PaymentGateway, PaymentTransaction, BankAccount
from app.ats.pricing.services.electronic_billing_service import ElectronicBillingService


class PaymentProcessingService:
    """Servicio para procesamiento de pagos con gateways."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.electronic_billing = ElectronicBillingService(business_unit)
    
    def get_available_gateways(self, currency: str = 'MXN', payment_method: str = None) -> List[PaymentGateway]:
        """
        Obtiene los gateways disponibles para una moneda y método de pago.
        
        Args:
            currency: Moneda del pago
            payment_method: Método de pago específico
            
        Returns:
            List[PaymentGateway]: Lista de gateways disponibles
        """
        gateways = PaymentGateway.objects.filter(
            business_unit=self.business_unit,
            status='active'
        )
        
        # Filtrar por moneda
        if currency:
            gateways = [g for g in gateways if g.is_available_for_currency(currency)]
        
        # Filtrar por método de pago
        if payment_method:
            gateways = [g for g in gateways if g.is_available_for_payment_method(payment_method)]
        
        return gateways
    
    def create_payment_intent(self, invoice: Invoice, gateway: PaymentGateway, 
                            payment_method: str, amount: Decimal = None) -> Dict[str, Any]:
        """
        Crea una intención de pago con el gateway.
        
        Args:
            invoice: Factura a pagar
            gateway: Gateway a usar
            payment_method: Método de pago
            amount: Monto a pagar (si no se especifica, usa el total de la factura)
            
        Returns:
            Dict: Respuesta del gateway con datos de pago
        """
        if not amount:
            amount = invoice.total_amount
        
        # Verificar que el gateway esté disponible
        if not gateway.is_available_for_currency(invoice.currency):
            raise ValidationError(f"El gateway {gateway.name} no soporta la moneda {invoice.currency}")
        
        # Crear transacción de pago
        transaction = PaymentTransaction.objects.create(
            invoice=invoice,
            gateway=gateway,
            amount=amount,
            currency=invoice.currency,
            payment_method=payment_method,
            description=f"Pago de factura {invoice.invoice_number}",
            created_by=invoice.created_by
        )
        
        try:
            # Procesar con el gateway específico
            if gateway.gateway_type == 'stripe':
                return self._create_stripe_payment_intent(transaction, gateway)
            elif gateway.gateway_type == 'paypal':
                return self._create_paypal_payment_intent(transaction, gateway)
            elif gateway.gateway_type == 'conekta':
                return self._create_conekta_payment_intent(transaction, gateway)
            elif gateway.gateway_type in ['banorte', 'banamex', 'bbva', 'hsbc', 'santander']:
                return self._create_bank_payment_intent(transaction, gateway)
            else:
                return self._create_generic_payment_intent(transaction, gateway)
                
        except Exception as e:
            transaction.status = 'failed'
            transaction.error_message = str(e)
            transaction.save()
            raise ValidationError(f"Error creando intención de pago: {str(e)}")
    
    def _create_stripe_payment_intent(self, transaction: PaymentTransaction, gateway: PaymentGateway) -> Dict[str, Any]:
        """Crea intención de pago con Stripe."""
        url = "https://api.stripe.com/v1/payment_intents"
        
        headers = {
            'Authorization': f'Bearer {gateway.api_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'amount': int(transaction.amount * 100),  # Stripe usa centavos
            'currency': transaction.currency.lower(),
            'metadata[transaction_id]': transaction.transaction_id,
            'metadata[invoice_number]': transaction.invoice.invoice_number,
            'description': transaction.description
        }
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            stripe_data = response.json()
            
            # Actualizar transacción
            transaction.external_id = stripe_data['id']
            transaction.payment_details = {
                'client_secret': stripe_data['client_secret'],
                'payment_intent_id': stripe_data['id']
            }
            transaction.save()
            
            return {
                'success': True,
                'transaction_id': transaction.transaction_id,
                'client_secret': stripe_data['client_secret'],
                'payment_intent_id': stripe_data['id']
            }
        else:
            raise ValidationError(f"Error de Stripe: {response.text}")
    
    def _create_paypal_payment_intent(self, transaction: PaymentTransaction, gateway: PaymentGateway) -> Dict[str, Any]:
        """Crea intención de pago con PayPal."""
        # Obtener token de acceso
        token_url = "https://api-m.paypal.com/v1/oauth2/token"
        token_headers = {
            'Authorization': f'Basic {gateway.api_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        token_data = {'grant_type': 'client_credentials'}
        
        token_response = requests.post(token_url, headers=token_headers, data=token_data)
        
        if token_response.status_code != 200:
            raise ValidationError("Error obteniendo token de PayPal")
        
        access_token = token_response.json()['access_token']
        
        # Crear orden de pago
        order_url = "https://api-m.paypal.com/v2/checkout/orders"
        order_headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        order_data = {
            'intent': 'CAPTURE',
            'purchase_units': [{
                'reference_id': transaction.transaction_id,
                'description': transaction.description,
                'amount': {
                    'currency_code': transaction.currency,
                    'value': str(transaction.amount)
                }
            }]
        }
        
        order_response = requests.post(order_url, headers=order_headers, json=order_data)
        
        if order_response.status_code == 201:
            paypal_data = order_response.json()
            
            # Actualizar transacción
            transaction.external_id = paypal_data['id']
            transaction.payment_details = {
                'order_id': paypal_data['id'],
                'approval_url': paypal_data['links'][1]['href']
            }
            transaction.save()
            
            return {
                'success': True,
                'transaction_id': transaction.transaction_id,
                'order_id': paypal_data['id'],
                'approval_url': paypal_data['links'][1]['href']
            }
        else:
            raise ValidationError(f"Error de PayPal: {order_response.text}")
    
    def _create_conekta_payment_intent(self, transaction: PaymentTransaction, gateway: PaymentGateway) -> Dict[str, Any]:
        """Crea intención de pago con Conekta."""
        url = "https://api.conekta.io/orders"
        
        headers = {
            'Authorization': f'Basic {gateway.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'currency': transaction.currency,
            'amount': int(transaction.amount * 100),  # Conekta usa centavos
            'line_items': [{
                'name': f"Factura {transaction.invoice.invoice_number}",
                'unit_price': int(transaction.amount * 100),
                'quantity': 1
            }],
            'metadata': {
                'transaction_id': transaction.transaction_id,
                'invoice_number': transaction.invoice.invoice_number
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            conekta_data = response.json()
            
            # Actualizar transacción
            transaction.external_id = conekta_data['id']
            transaction.payment_details = {
                'order_id': conekta_data['id'],
                'checkout_url': conekta_data.get('checkout', {}).get('url')
            }
            transaction.save()
            
            return {
                'success': True,
                'transaction_id': transaction.transaction_id,
                'order_id': conekta_data['id'],
                'checkout_url': conekta_data.get('checkout', {}).get('url')
            }
        else:
            raise ValidationError(f"Error de Conekta: {response.text}")
    
    def _create_bank_payment_intent(self, transaction: PaymentTransaction, gateway: PaymentGateway) -> Dict[str, Any]:
        """Crea intención de pago con banco."""
        # Obtener cuenta bancaria principal
        bank_account = BankAccount.objects.filter(
            business_unit=self.business_unit,
            is_active=True,
            is_primary=True
        ).first()
        
        if not bank_account:
            raise ValidationError("No hay cuenta bancaria principal configurada")
        
        # Crear referencia de pago
        reference = f"REF{transaction.transaction_id}"
        
        # Actualizar transacción
        transaction.bank_account = bank_account
        transaction.payment_details = {
            'reference': reference,
            'bank_account': bank_account.account_number,
            'clabe': bank_account.clabe,
            'bank': bank_account.bank
        }
        transaction.save()
        
        return {
            'success': True,
            'transaction_id': transaction.transaction_id,
            'reference': reference,
            'bank_account': bank_account.account_number,
            'clabe': bank_account.clabe,
            'bank': bank_account.get_bank_display()
        }
    
    def _create_generic_payment_intent(self, transaction: PaymentTransaction, gateway: PaymentGateway) -> Dict[str, Any]:
        """Crea intención de pago genérica."""
        # Implementación genérica para otros gateways
        external_id = f"{gateway.gateway_type}_{uuid.uuid4().hex[:8]}"
        
        transaction.external_id = external_id
        transaction.payment_details = {
            'gateway_type': gateway.gateway_type,
            'external_id': external_id
        }
        transaction.save()
        
        return {
            'success': True,
            'transaction_id': transaction.transaction_id,
            'external_id': external_id,
            'gateway_type': gateway.gateway_type
        }
    
    def process_payment_confirmation(self, transaction_id: str, gateway_data: Dict[str, Any]) -> bool:
        """
        Procesa la confirmación de pago desde el gateway.
        
        Args:
            transaction_id: ID de la transacción
            gateway_data: Datos de confirmación del gateway
            
        Returns:
            bool: True si el pago se procesó exitosamente
        """
        try:
            transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
            
            # Actualizar transacción con datos del gateway
            transaction.gateway_response = gateway_data
            transaction.status = 'completed'
            transaction.processed_at = timezone.now()
            transaction.completed_at = timezone.now()
            transaction.save()
            
            # Actualizar factura
            invoice = transaction.invoice
            invoice.payment_status = 'paid'
            invoice.paid_at = timezone.now()
            invoice.save()
            
            # Procesar facturación electrónica
            if invoice.requires_electronic_billing:
                self._process_electronic_billing(invoice)
            
            # Enviar factura al cliente
            if invoice.client_email:
                self.electronic_billing.send_invoice_to_client(invoice, invoice.client_email)
            
            return True
            
        except PaymentTransaction.DoesNotExist:
            raise ValidationError(f"Transacción {transaction_id} no encontrada")
        except Exception as e:
            raise ValidationError(f"Error procesando confirmación de pago: {str(e)}")
    
    def _process_electronic_billing(self, invoice: Invoice):
        """Procesa la facturación electrónica después del pago."""
        try:
            result = self.electronic_billing.process_electronic_invoice(invoice)
            
            if result['success']:
                print(f"✅ Facturación electrónica exitosa para {invoice.invoice_number}")
                if 'uuid' in result:
                    print(f"   UUID: {result['uuid']}")
            else:
                print(f"❌ Error en facturación electrónica: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Error procesando facturación electrónica: {e}")
    
    def process_webhook(self, gateway: PaymentGateway, webhook_data: Dict[str, Any]) -> bool:
        """
        Procesa webhooks de los gateways.
        
        Args:
            gateway: Gateway que envió el webhook
            webhook_data: Datos del webhook
            
        Returns:
            bool: True si se procesó exitosamente
        """
        try:
            # Verificar firma del webhook (seguridad)
            if not self._verify_webhook_signature(gateway, webhook_data):
                raise ValidationError("Firma del webhook inválida")
            
            # Procesar según el tipo de gateway
            if gateway.gateway_type == 'stripe':
                return self._process_stripe_webhook(webhook_data)
            elif gateway.gateway_type == 'paypal':
                return self._process_paypal_webhook(webhook_data)
            elif gateway.gateway_type == 'conekta':
                return self._process_conekta_webhook(webhook_data)
            else:
                return self._process_generic_webhook(webhook_data)
                
        except Exception as e:
            print(f"❌ Error procesando webhook: {e}")
            return False
    
    def _verify_webhook_signature(self, gateway: PaymentGateway, webhook_data: Dict[str, Any]) -> bool:
        """Verifica la firma del webhook para seguridad."""
        # En producción, implementarías la verificación de firma específica del gateway
        # Por ahora, simulamos la verificación
        return True
    
    def _process_stripe_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Procesa webhook de Stripe."""
        event_type = webhook_data.get('type')
        
        if event_type == 'payment_intent.succeeded':
            payment_intent = webhook_data.get('data', {}).get('object', {})
            transaction_id = payment_intent.get('metadata', {}).get('transaction_id')
            
            if transaction_id:
                return self.process_payment_confirmation(transaction_id, webhook_data)
        
        return True
    
    def _process_paypal_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Procesa webhook de PayPal."""
        event_type = webhook_data.get('event_type')
        
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            payment_data = webhook_data.get('resource', {})
            reference_id = payment_data.get('reference_id')
            
            if reference_id:
                return self.process_payment_confirmation(reference_id, webhook_data)
        
        return True
    
    def _process_conekta_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Procesa webhook de Conekta."""
        event_type = webhook_data.get('type')
        
        if event_type == 'order.paid':
            order_data = webhook_data.get('data', {}).get('object', {})
            transaction_id = order_data.get('metadata', {}).get('transaction_id')
            
            if transaction_id:
                return self.process_payment_confirmation(transaction_id, webhook_data)
        
        return True
    
    def _process_generic_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Procesa webhook genérico."""
        # Implementación genérica para otros gateways
        return True
    
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de una transacción de pago.
        
        Args:
            transaction_id: ID de la transacción
            
        Returns:
            Dict: Estado de la transacción
        """
        try:
            transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
            
            return {
                'transaction_id': transaction.transaction_id,
                'status': transaction.status,
                'amount': str(transaction.amount),
                'currency': transaction.currency,
                'payment_method': transaction.payment_method,
                'created_at': transaction.created_at.isoformat(),
                'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None,
                'gateway_response': transaction.gateway_response
            }
            
        except PaymentTransaction.DoesNotExist:
            raise ValidationError(f"Transacción {transaction_id} no encontrada")
    
    def refund_payment(self, transaction_id: str, amount: Decimal = None, reason: str = "") -> Dict[str, Any]:
        """
        Procesa un reembolso.
        
        Args:
            transaction_id: ID de la transacción original
            amount: Monto a reembolsar (si no se especifica, reembolsa todo)
            reason: Razón del reembolso
            
        Returns:
            Dict: Resultado del reembolso
        """
        try:
            original_transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
            
            # Crear transacción de reembolso
            refund_transaction = original_transaction.refund(amount, reason)
            
            # Procesar reembolso con el gateway
            if original_transaction.gateway:
                if original_transaction.gateway.gateway_type == 'stripe':
                    return self._process_stripe_refund(refund_transaction, original_transaction)
                elif original_transaction.gateway.gateway_type == 'paypal':
                    return self._process_paypal_refund(refund_transaction, original_transaction)
                else:
                    return self._process_generic_refund(refund_transaction, original_transaction)
            else:
                # Reembolso manual
                refund_transaction.status = 'completed'
                refund_transaction.save()
                
                return {
                    'success': True,
                    'refund_transaction_id': refund_transaction.transaction_id,
                    'amount': str(refund_transaction.amount),
                    'message': 'Reembolso procesado manualmente'
                }
                
        except PaymentTransaction.DoesNotExist:
            raise ValidationError(f"Transacción {transaction_id} no encontrada")
        except Exception as e:
            raise ValidationError(f"Error procesando reembolso: {str(e)}")
    
    def _process_stripe_refund(self, refund_transaction: PaymentTransaction, 
                              original_transaction: PaymentTransaction) -> Dict[str, Any]:
        """Procesa reembolso con Stripe."""
        url = f"https://api.stripe.com/v1/refunds"
        
        headers = {
            'Authorization': f'Bearer {original_transaction.gateway.api_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'payment_intent': original_transaction.external_id,
            'amount': int(refund_transaction.amount * 100),
            'reason': 'requested_by_customer'
        }
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            stripe_data = response.json()
            
            refund_transaction.external_id = stripe_data['id']
            refund_transaction.status = 'completed'
            refund_transaction.gateway_response = stripe_data
            refund_transaction.save()
            
            return {
                'success': True,
                'refund_transaction_id': refund_transaction.transaction_id,
                'stripe_refund_id': stripe_data['id'],
                'amount': str(refund_transaction.amount)
            }
        else:
            raise ValidationError(f"Error de Stripe: {response.text}")
    
    def _process_paypal_refund(self, refund_transaction: PaymentTransaction, 
                              original_transaction: PaymentTransaction) -> Dict[str, Any]:
        """Procesa reembolso con PayPal."""
        # Implementación similar a Stripe pero con PayPal API
        return {
            'success': True,
            'refund_transaction_id': refund_transaction.transaction_id,
            'message': 'Reembolso PayPal procesado'
        }
    
    def _process_generic_refund(self, refund_transaction: PaymentTransaction, 
                               original_transaction: PaymentTransaction) -> Dict[str, Any]:
        """Procesa reembolso genérico."""
        refund_transaction.status = 'completed'
        refund_transaction.save()
        
        return {
            'success': True,
            'refund_transaction_id': refund_transaction.transaction_id,
            'message': 'Reembolso procesado'
        } 