import logging
from app.advanced_features.example_logging import setup_module_logging

# Configurar logger para el módulo de payments
payments_logger = setup_module_logging('payments')

class PaymentProcessor:
    def process_payment(self, amount, customer):
        """Procesa un pago y registra el proceso."""
        payments_logger.info(f'Iniciando proceso de pago para {customer}')
        
        try:
            # Simulando proceso de pago
            result = self._execute_payment(amount, customer)
            payments_logger.debug(f'Estado del pago: {result}')
            return result
        except Exception as e:
            payments_logger.error(f'Error en el proceso de pago: {str(e)}', exc_info=True)
            raise
    
    def _execute_payment(self, amount, customer):
        """Ejecuta el pago."""
        # Simulando llamada a Stripe
        return {
            'status': 'completed',
            'amount': amount,
            'customer': customer,
            'timestamp': datetime.now()
        }
