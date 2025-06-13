from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class PaymentGateway(ABC):
    """
    Clase base abstracta para gateways de pago.
    
    Todos los gateways de pago deben heredar de esta clase y implementar
    los métodos abstractos definidos.
    """
    
    def __init__(self, business_unit: Optional[str] = None):
        """
        Inicializa el gateway.
        
        Args:
            business_unit: Unidad de negocio asociada (opcional)
        """
        self.business_unit = business_unit
        
    @abstractmethod
    def create_payment(self, amount: float, currency: str, description: str, **kwargs) -> Dict[str, Any]:
        """
        Crea un nuevo pago.
        
        Args:
            amount: Monto del pago
            currency: Código de moneda (ej: 'MXN', 'USD')
            description: Descripción del pago
            **kwargs: Parámetros adicionales específicos del gateway
            
        Returns:
            Diccionario con la información del pago creado
        """
        pass
    
    @abstractmethod
    def execute_payment(self, payment_id: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta un pago existente.
        
        Args:
            payment_id: ID del pago a ejecutar
            **kwargs: Parámetros adicionales específicos del gateway
            
        Returns:
            Diccionario con el resultado de la ejecución
        """
        pass
    
    @abstractmethod
    def create_payout(self, payments: list, **kwargs) -> Dict[str, Any]:
        """
        Crea un payout para múltiples pagos.
        
        Args:
            payments: Lista de pagos a incluir en el payout
            **kwargs: Parámetros adicionales específicos del gateway
            
        Returns:
            Diccionario con la información del payout
        """
        pass
    
    @abstractmethod
    def verify_webhook(self, request_body: Dict[str, Any]) -> bool:
        """
        Verifica la validez de un webhook de pago.
        
        Args:
            request_body: Cuerpo de la solicitud webhook
            
        Returns:
            True si el webhook es válido, False en caso contrario
        """
        pass
