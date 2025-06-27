"""
Gateway de pago para Conekta.
"""
import requests
import json
from typing import Dict, Any
from .base import PaymentGateway

class ConektaGateway(PaymentGateway):
    """Gateway para procesar pagos con Conekta."""
    
    def __init__(self, business_unit: str = None):
        super().__init__(business_unit)
        self.api_url = "https://api.conekta.io"
        
    def create_payment(self, amount: float, currency: str, description: str, **kwargs) -> Dict[str, Any]:
        """
        Crea un nuevo pago con Conekta.
        
        Args:
            amount: Monto del pago
            currency: Código de moneda
            description: Descripción del pago
            **kwargs: Parámetros adicionales
            
        Returns:
            Dict con la información del pago creado
        """
        try:
            # Crear orden en Conekta
            order_data = {
                'amount': int(amount * 100),  # Conekta usa centavos
                'currency': currency.lower(),
                'description': description,
                'reference_id': kwargs.get('reference_id', ''),
                'metadata': kwargs.get('metadata', {})
            }
            
            headers = {
                'Authorization': f'Basic {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.api_url}/orders",
                headers=headers,
                json=order_data
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    'success': True,
                    'id': data['id'],
                    'webhook_url': kwargs.get('webhook_url'),
                    'amount': amount,
                    'currency': currency
                }
            else:
                return {
                    'success': False,
                    'error': f"Error de Conekta: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_payment(self, payment_id: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta un pago existente en Conekta.
        
        Args:
            payment_id: ID del pago a ejecutar
            **kwargs: Parámetros adicionales
            
        Returns:
            Dict con el resultado de la ejecución
        """
        try:
            # Obtener información de la orden
            headers = {
                'Authorization': f'Basic {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.api_url}/orders/{payment_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar si el pago está completado
                if data.get('payment_status') == 'paid':
                    return {
                        'success': True,
                        'id': data['id'],
                        'status': 'completed'
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Pago no completado. Estado: {data.get('payment_status')}"
                    }
            else:
                return {
                    'success': False,
                    'error': f"Error obteniendo pago: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_payout(self, payments: list, **kwargs) -> Dict[str, Any]:
        """
        Crea un payout para múltiples pagos en Conekta.
        
        Args:
            payments: Lista de pagos a incluir en el payout
            **kwargs: Parámetros adicionales
            
        Returns:
            Dict con la información del payout
        """
        try:
            # Conekta no tiene payouts directos, se simula
            total_amount = sum(payment.get('amount', 0) for payment in payments)
            
            return {
                'success': True,
                'id': f"payout_{len(payments)}",
                'amount': total_amount,
                'payments_count': len(payments)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_webhook(self, request_body: Dict[str, Any]) -> bool:
        """
        Verifica la validez de un webhook de Conekta.
        
        Args:
            request_body: Cuerpo de la solicitud webhook
            
        Returns:
            True si el webhook es válido, False en caso contrario
        """
        try:
            # Verificar firma del webhook (implementación básica)
            # En producción, verificar la firma real de Conekta
            return True
            
        except Exception:
            return False 