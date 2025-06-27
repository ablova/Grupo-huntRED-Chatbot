"""
Gateway de pago para Clip (terminal físico).
"""
import requests
import json
from typing import Dict, Any
from .base import PaymentGateway

class ClipGateway(PaymentGateway):
    """Gateway para procesar pagos con terminal Clip."""
    
    def __init__(self, business_unit: str = None):
        super().__init__(business_unit)
        self.api_url = "https://api.clip.mx"
        
    def create_payment(self, amount: float, currency: str, description: str, **kwargs) -> Dict[str, Any]:
        """
        Crea un nuevo pago con Clip.
        
        Args:
            amount: Monto del pago
            currency: Código de moneda
            description: Descripción del pago
            **kwargs: Parámetros adicionales
            
        Returns:
            Dict con la información del pago creado
        """
        try:
            # Crear transacción en Clip
            payment_data = {
                'amount': int(amount * 100),  # Clip usa centavos
                'currency': currency.upper(),
                'description': description,
                'reference': kwargs.get('reference', ''),
                'terminal_id': kwargs.get('terminal_id', ''),
                'merchant_id': self.api_key
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_secret}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.api_url}/transactions",
                headers=headers,
                json=payment_data
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    'success': True,
                    'transaction_id': data.get('id'),
                    'terminal_id': data.get('terminal_id'),
                    'qr_code': data.get('qr_code'),
                    'amount': amount,
                    'currency': currency
                }
            else:
                return {
                    'success': False,
                    'error': f"Error de Clip: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de una transacción.
        
        Args:
            transaction_id: ID de la transacción
            
        Returns:
            Dict con el estado de la transacción
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_secret}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.api_url}/transactions/{transaction_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'status': data.get('status'),
                    'amount': data.get('amount'),
                    'currency': data.get('currency'),
                    'terminal_id': data.get('terminal_id'),
                    'created_at': data.get('created_at')
                }
            else:
                return {
                    'success': False,
                    'error': f"Error obteniendo estado: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def refund_transaction(self, transaction_id: str, amount: float = None) -> Dict[str, Any]:
        """
        Reembolsa una transacción.
        
        Args:
            transaction_id: ID de la transacción
            amount: Monto a reembolsar (si no se especifica, reembolsa todo)
            
        Returns:
            Dict con el resultado del reembolso
        """
        try:
            refund_data = {
                'transaction_id': transaction_id
            }
            
            if amount:
                refund_data['amount'] = int(amount * 100)
            
            headers = {
                'Authorization': f'Bearer {self.api_secret}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.api_url}/refunds",
                headers=headers,
                json=refund_data
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    'success': True,
                    'refund_id': data.get('id'),
                    'amount': data.get('amount'),
                    'status': 'completed'
                }
            else:
                return {
                    'success': False,
                    'error': f"Error en reembolso: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_terminals(self) -> Dict[str, Any]:
        """
        Obtiene la lista de terminales disponibles.
        
        Returns:
            Dict con la lista de terminales
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_secret}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.api_url}/terminals",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'terminals': data.get('terminals', [])
                }
            else:
                return {
                    'success': False,
                    'error': f"Error obteniendo terminales: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            } 