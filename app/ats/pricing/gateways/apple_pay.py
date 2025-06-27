"""
Gateway de pago para Apple Pay.
"""
import requests
import json
from typing import Dict, Any
from .base import PaymentGateway

class ApplePayGateway(PaymentGateway):
    """Gateway para procesar pagos con Apple Pay."""
    
    def __init__(self, business_unit: str = None):
        super().__init__(business_unit)
        self.api_url = "https://api.apple.com/payments"
        
    def create_payment(self, amount: float, currency: str, description: str, **kwargs) -> Dict[str, Any]:
        """
        Crea un nuevo pago con Apple Pay.
        
        Args:
            amount: Monto del pago
            currency: Código de moneda
            description: Descripción del pago
            **kwargs: Parámetros adicionales
            
        Returns:
            Dict con la información del pago creado
        """
        try:
            # Crear sesión de pago de Apple Pay
            payment_data = {
                'amount': amount,
                'currency': currency.upper(),
                'description': description,
                'merchant_id': self.api_key,
                'domain': kwargs.get('domain', ''),
                'validation_url': kwargs.get('validation_url', ''),
                'payment_token': kwargs.get('payment_token', '')
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_secret}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.api_url}/sessions",
                headers=headers,
                json=payment_data
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'session_id': data.get('session_id'),
                    'merchant_session': data.get('merchant_session'),
                    'amount': amount,
                    'currency': currency
                }
            else:
                return {
                    'success': False,
                    'error': f"Error de Apple Pay: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_domain(self, domain: str) -> Dict[str, Any]:
        """
        Valida un dominio para Apple Pay.
        
        Args:
            domain: Dominio a validar
            
        Returns:
            Dict con el resultado de la validación
        """
        try:
            validation_data = {
                'domain': domain,
                'merchant_id': self.api_key
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_secret}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.api_url}/validate-domain",
                headers=headers,
                json=validation_data
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'valid': True,
                    'domain': domain
                }
            else:
                return {
                    'success': False,
                    'valid': False,
                    'error': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'valid': False,
                'error': str(e)
            }
    
    def process_payment_token(self, payment_token: str, amount: float, currency: str) -> Dict[str, Any]:
        """
        Procesa un token de pago de Apple Pay.
        
        Args:
            payment_token: Token de pago de Apple Pay
            amount: Monto del pago
            currency: Moneda del pago
            
        Returns:
            Dict con el resultado del procesamiento
        """
        try:
            payment_data = {
                'payment_token': payment_token,
                'amount': amount,
                'currency': currency.upper(),
                'merchant_id': self.api_key
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_secret}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.api_url}/process",
                headers=headers,
                json=payment_data
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'transaction_id': data.get('transaction_id'),
                    'status': 'completed',
                    'amount': amount,
                    'currency': currency
                }
            else:
                return {
                    'success': False,
                    'error': f"Error procesando pago: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            } 