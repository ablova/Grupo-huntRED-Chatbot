"""
Gateway para BBVA con funcionalidad bidireccional.
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import requests
import json

from .base_bank_gateway import BaseBankGateway
from app.models import BusinessUnit, PaymentTransaction
from app.ats.models import BankAccount, PaymentGateway

logger = logging.getLogger(__name__)

class BBVAGateway(BaseBankGateway):
    """Gateway para BBVA México."""
    
    def __init__(self, business_unit: BusinessUnit, gateway_config: PaymentGateway):
        super().__init__(business_unit, gateway_config)
        self.api_url = self.api_url or "https://api.bbva.com.mx"
        self.client_id = gateway_config.config.get('client_id', '')
        self.client_secret = gateway_config.config.get('client_secret', '')
        self.access_token = None
        self.token_expires_at = None
    
    def authenticate(self) -> Dict[str, Any]:
        """Autenticación OAuth2 con BBVA."""
        try:
            # Verificar si ya tenemos un token válido
            if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
                return {'success': True, 'access_token': self.access_token}
            
            # Obtener nuevo token
            auth_url = f"{self.api_url}/oauth/token"
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(auth_url, data=auth_data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Actualizar headers con el token
                self.headers['Authorization'] = f"Bearer {self.access_token}"
                
                return {
                    'success': True,
                    'access_token': self.access_token
                }
            else:
                return {
                    'success': False,
                    'error': f'Error de autenticación BBVA: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Error autenticando con BBVA: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_balance(self, account_number: str) -> Dict[str, Any]:
        """Obtiene el saldo de una cuenta BBVA."""
        try:
            endpoint = f"/accounts/{account_number}/balance"
            response = self._make_request('GET', endpoint)
            
            if response.get('success'):
                data = response.get('data', {})
                return {
                    'success': True,
                    'balance': data.get('available_balance', 0),
                    'currency': data.get('currency', 'MXN'),
                    'account_number': account_number
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"Error obteniendo saldo BBVA: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def transfer_money(
        self,
        from_account: str,
        to_account: str,
        amount: Decimal,
        description: str,
        reference: str
    ) -> Dict[str, Any]:
        """Transfiere dinero entre cuentas BBVA."""
        try:
            endpoint = "/transfers"
            transfer_data = {
                'from_account': from_account,
                'to_account': to_account,
                'amount': float(amount),
                'currency': 'MXN',
                'description': description,
                'reference': reference,
                'execution_date': datetime.now().isoformat()
            }
            
            response = self._make_request('POST', endpoint, transfer_data)
            
            if response.get('success'):
                data = response.get('data', {})
                return {
                    'success': True,
                    'transfer_id': data.get('transfer_id'),
                    'status': data.get('status'),
                    'amount': float(amount),
                    'message': 'Transferencia creada exitosamente'
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"Error en transferencia BBVA: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_payment_order(
        self,
        beneficiary_account: str,
        beneficiary_name: str,
        amount: Decimal,
        description: str,
        reference: str,
        execution_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Crea una orden de pago BBVA."""
        try:
            endpoint = "/payment-orders"
            payment_data = {
                'beneficiary_account': beneficiary_account,
                'beneficiary_name': beneficiary_name,
                'amount': float(amount),
                'currency': 'MXN',
                'description': description,
                'reference': reference,
                'execution_date': (execution_date or datetime.now()).isoformat(),
                'payment_type': 'SPEI'  # Sistema de Pagos Electrónicos Interbancarios
            }
            
            response = self._make_request('POST', endpoint, payment_data)
            
            if response.get('success'):
                data = response.get('data', {})
                return {
                    'success': True,
                    'payment_id': data.get('payment_id'),
                    'status': data.get('status'),
                    'amount': float(amount),
                    'message': 'Orden de pago creada exitosamente'
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"Error creando orden de pago BBVA: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Obtiene el estado de un pago BBVA."""
        try:
            endpoint = f"/payment-orders/{payment_id}/status"
            response = self._make_request('GET', endpoint)
            
            if response.get('success'):
                data = response.get('data', {})
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'status': data.get('status'),
                    'amount': data.get('amount'),
                    'execution_date': data.get('execution_date'),
                    'confirmation_date': data.get('confirmation_date')
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"Error obteniendo estado de pago BBVA: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_movements(
        self,
        account_number: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Obtiene movimientos de cuenta BBVA."""
        try:
            endpoint = f"/accounts/{account_number}/movements"
            params = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'limit': 100
            }
            
            response = self._make_request('GET', endpoint, params=params)
            
            if response.get('success'):
                data = response.get('data', {})
                movements = data.get('movements', [])
                
                return [
                    {
                        'transaction_id': mov.get('transaction_id'),
                        'date': mov.get('date'),
                        'description': mov.get('description'),
                        'amount': mov.get('amount'),
                        'type': mov.get('type'),
                        'reference': mov.get('reference'),
                        'balance': mov.get('balance')
                    }
                    for mov in movements
                ]
            else:
                logger.error(f"Error obteniendo movimientos BBVA: {response.get('error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo movimientos BBVA: {str(e)}")
            return []
    
    def create_spei_payment(
        self,
        beneficiary_clabe: str,
        beneficiary_name: str,
        amount: Decimal,
        description: str,
        reference: str
    ) -> Dict[str, Any]:
        """Crea un pago SPEI específico de BBVA."""
        try:
            endpoint = "/spei-payments"
            spei_data = {
                'beneficiary_clabe': beneficiary_clabe,
                'beneficiary_name': beneficiary_name,
                'amount': float(amount),
                'description': description,
                'reference': reference,
                'payment_type': 'SPEI'
            }
            
            response = self._make_request('POST', endpoint, spei_data)
            
            if response.get('success'):
                data = response.get('data', {})
                return {
                    'success': True,
                    'spei_id': data.get('spei_id'),
                    'status': data.get('status'),
                    'amount': float(amount),
                    'message': 'Pago SPEI creado exitosamente'
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"Error creando pago SPEI BBVA: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_spei_status(self, spei_id: str) -> Dict[str, Any]:
        """Obtiene el estado de un pago SPEI."""
        try:
            endpoint = f"/spei-payments/{spei_id}/status"
            response = self._make_request('GET', endpoint)
            
            if response.get('success'):
                data = response.get('data', {})
                return {
                    'success': True,
                    'spei_id': spei_id,
                    'status': data.get('status'),
                    'confirmation_date': data.get('confirmation_date'),
                    'tracking_key': data.get('tracking_key')
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"Error obteniendo estado SPEI BBVA: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            } 