"""
Clase base para gateways bancarios con funcionalidad bidireccional.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import requests
import json
import hashlib
import hmac
import base64

from app.models import BusinessUnit, PaymentTransaction
from app.ats.pricing.models import BankAccount, PaymentGateway

logger = logging.getLogger(__name__)

class BaseBankGateway(ABC):
    """Clase base para gateways bancarios con pagos y cobros bidireccionales."""
    
    def __init__(self, business_unit: BusinessUnit, gateway_config: PaymentGateway):
        self.business_unit = business_unit
        self.gateway_config = gateway_config
        self.api_url = gateway_config.config.get('api_url', '')
        self.api_key = gateway_config.api_key
        self.api_secret = gateway_config.api_secret
        self.client_id = gateway_config.config.get('client_id', '')
        self.client_secret = gateway_config.config.get('client_secret', '')
        
        # Configuración específica del banco
        self.bank_code = gateway_config.config.get('bank_code', '')
        self.branch_code = gateway_config.config.get('branch_code', '')
        self.account_type = gateway_config.config.get('account_type', '')
        
        # Headers comunes
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'huntRED-BankGateway/1.0'
        }
    
    # ============================================================================
    # MÉTODOS ABSTRACTOS - DEBEN SER IMPLEMENTADOS POR CADA BANCO
    # ============================================================================
    
    @abstractmethod
    def authenticate(self) -> Dict[str, Any]:
        """Autenticación con el banco."""
        pass
    
    @abstractmethod
    def get_account_balance(self, account_number: str) -> Dict[str, Any]:
        """Obtiene el saldo de una cuenta."""
        pass
    
    @abstractmethod
    def transfer_money(
        self,
        from_account: str,
        to_account: str,
        amount: Decimal,
        description: str,
        reference: str
    ) -> Dict[str, Any]:
        """Transfiere dinero entre cuentas."""
        pass
    
    @abstractmethod
    def create_payment_order(
        self,
        beneficiary_account: str,
        beneficiary_name: str,
        amount: Decimal,
        description: str,
        reference: str,
        execution_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Crea una orden de pago."""
        pass
    
    @abstractmethod
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Obtiene el estado de un pago."""
        pass
    
    @abstractmethod
    def get_account_movements(
        self,
        account_number: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Obtiene movimientos de cuenta."""
        pass
    
    # ============================================================================
    # MÉTODOS COMUNES PARA PAGOS Y COBROS
    # ============================================================================
    
    def process_outgoing_payment(
        self,
        source_account: BankAccount,
        beneficiary_account: str,
        beneficiary_name: str,
        amount: Decimal,
        description: str,
        reference: str,
        execution_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Procesa un pago saliente (transferencia bancaria).
        
        Args:
            source_account: Cuenta de origen
            beneficiary_account: Cuenta del beneficiario
            beneficiary_name: Nombre del beneficiario
            amount: Monto a transferir
            description: Descripción del pago
            reference: Referencia del pago
            execution_date: Fecha de ejecución (opcional)
            
        Returns:
            Dict con el resultado del pago
        """
        try:
            # Autenticar con el banco
            auth_result = self.authenticate()
            if not auth_result.get('success'):
                return {
                    'success': False,
                    'error': f"Error de autenticación: {auth_result.get('error')}"
                }
            
            # Verificar saldo
            balance_result = self.get_account_balance(source_account.account_number)
            if not balance_result.get('success'):
                return {
                    'success': False,
                    'error': f"Error obteniendo saldo: {balance_result.get('error')}"
                }
            
            current_balance = Decimal(str(balance_result.get('balance', 0)))
            if current_balance < amount:
                return {
                    'success': False,
                    'error': f"Saldo insuficiente. Disponible: {current_balance}, Requerido: {amount}"
                }
            
            # Crear orden de pago
            payment_result = self.create_payment_order(
                beneficiary_account=beneficiary_account,
                beneficiary_name=beneficiary_name,
                amount=amount,
                description=description,
                reference=reference,
                execution_date=execution_date
            )
            
            if payment_result.get('success'):
                # Crear transacción en el sistema
                transaction = PaymentTransaction.objects.create(
                    user=None,  # Transacción del sistema
                    amount=amount,
                    currency='MXN',
                    payment_method='bank_transfer',
                    status='completed',
                    transaction_id=f"BANK-{payment_result.get('payment_id')}",
                    payment_details={
                        'gateway_type': self.gateway_config.gateway_type,
                        'source_account': source_account.account_number,
                        'beneficiary_account': beneficiary_account,
                        'beneficiary_name': beneficiary_name,
                        'reference': reference,
                        'bank_response': payment_result
                    }
                )
                
                return {
                    'success': True,
                    'transaction_id': transaction.transaction_id,
                    'payment_id': payment_result.get('payment_id'),
                    'amount': float(amount),
                    'message': 'Pago procesado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': payment_result.get('error', 'Error procesando pago')
                }
                
        except Exception as e:
            logger.error(f"Error procesando pago saliente: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_incoming_payment(
        self,
        destination_account: BankAccount,
        amount: Decimal,
        payer_account: str,
        payer_name: str,
        description: str,
        reference: str
    ) -> Dict[str, Any]:
        """
        Procesa un pago entrante (cobro).
        
        Args:
            destination_account: Cuenta de destino
            amount: Monto recibido
            payer_account: Cuenta del pagador
            payer_name: Nombre del pagador
            description: Descripción del pago
            reference: Referencia del pago
            
        Returns:
            Dict con el resultado del cobro
        """
        try:
            # Verificar que el pago fue recibido
            movements = self.get_account_movements(
                account_number=destination_account.account_number,
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now()
            )
            
            # Buscar el movimiento correspondiente
            matching_movement = None
            for movement in movements:
                if (movement.get('reference') == reference and
                    Decimal(str(movement.get('amount', 0))) == amount):
                    matching_movement = movement
                    break
            
            if not matching_movement:
                return {
                    'success': False,
                    'error': 'Pago no encontrado en movimientos bancarios'
                }
            
            # Crear transacción en el sistema
            transaction = PaymentTransaction.objects.create(
                user=None,  # Transacción del sistema
                amount=amount,
                currency='MXN',
                payment_method='bank_transfer',
                status='completed',
                transaction_id=f"BANK-IN-{matching_movement.get('transaction_id')}",
                payment_details={
                    'gateway_type': self.gateway_config.gateway_type,
                    'destination_account': destination_account.account_number,
                    'payer_account': payer_account,
                    'payer_name': payer_name,
                    'reference': reference,
                    'bank_movement': matching_movement
                }
            )
            
            return {
                'success': True,
                'transaction_id': transaction.transaction_id,
                'amount': float(amount),
                'payer_name': payer_name,
                'message': 'Cobro procesado exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error procesando cobro entrante: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def schedule_recurring_payment(
        self,
        source_account: BankAccount,
        beneficiary_account: str,
        beneficiary_name: str,
        amount: Decimal,
        description: str,
        frequency: str,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Programa un pago recurrente.
        
        Args:
            source_account: Cuenta de origen
            beneficiary_account: Cuenta del beneficiario
            beneficiary_name: Nombre del beneficiario
            amount: Monto a transferir
            description: Descripción del pago
            frequency: Frecuencia ('daily', 'weekly', 'monthly')
            start_date: Fecha de inicio
            end_date: Fecha de fin (opcional)
            
        Returns:
            Dict con el resultado de la programación
        """
        try:
            # Crear pago programado en el sistema
            from app.ats.pricing.models import ScheduledPayment
            
            scheduled_payment = ScheduledPayment.objects.create(
                name=f"Pago recurrente: {description}",
                payment_type='other',
                business_unit=self.business_unit,
                amount=amount,
                currency='MXN',
                frequency=frequency,
                start_date=start_date,
                end_date=end_date,
                next_payment_date=start_date,
                beneficiary_name=beneficiary_name,
                beneficiary_account=beneficiary_account,
                source_account=source_account,
                description=description,
                reference=f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            
            return {
                'success': True,
                'scheduled_payment_id': str(scheduled_payment.id),
                'message': 'Pago recurrente programado exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error programando pago recurrente: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_receipt(self, transaction_id: str) -> Dict[str, Any]:
        """
        Genera un recibo de pago.
        
        Args:
            transaction_id: ID de la transacción
            
        Returns:
            Dict con los datos del recibo
        """
        try:
            transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
            
            receipt_data = {
                'transaction_id': transaction.transaction_id,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'payment_method': transaction.payment_method,
                'status': transaction.status,
                'created_at': transaction.created_at.isoformat(),
                'payment_details': transaction.payment_details
            }
            
            return {
                'success': True,
                'receipt': receipt_data
            }
            
        except PaymentTransaction.DoesNotExist:
            return {
                'success': False,
                'error': 'Transacción no encontrada'
            }
        except Exception as e:
            logger.error(f"Error generando recibo: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # MÉTODOS DE UTILIDAD
    # ============================================================================
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Realiza una petición HTTP al banco."""
        try:
            url = f"{self.api_url}{endpoint}"
            request_headers = {**self.headers}
            if headers:
                request_headers.update(headers)
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=request_headers)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=request_headers)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=request_headers)
            else:
                return {'success': False, 'error': f'Método HTTP no soportado: {method}'}
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'error': f'Error HTTP {response.status_code}: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error en petición HTTP: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_signature(self, data: str) -> str:
        """Genera firma para autenticación."""
        if self.api_secret:
            return hmac.new(
                self.api_secret.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        return ""
    
    def _validate_response(self, response: Dict[str, Any]) -> bool:
        """Valida la respuesta del banco."""
        return response.get('success', False) and 'error' not in response 