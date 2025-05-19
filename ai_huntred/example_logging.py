import logging

# Ejemplo de cómo usar logging en cada módulo
def setup_module_logging(module_name):
    """Configura el logging para un módulo específico."""
    logger = logging.getLogger(f'app.{module_name}')
    return logger

def example_usage():
    # Ejemplo de uso en el módulo de analytics
    analytics_logger = setup_module_logging('analytics')
    analytics_logger.info('Iniciando análisis de datos')
    
    try:
        # Simulando una operación
        result = some_operation()
        analytics_logger.debug(f'Resultado de la operación: {result}')
    except Exception as e:
        analytics_logger.error(f'Error en el análisis: {str(e)}', exc_info=True)
    
    # Ejemplo de uso en el módulo de payments
    payments_logger = setup_module_logging('payments')
    payments_logger.info('Iniciando proceso de pago')
    
    try:
        # Simulando un proceso de pago
        payment_result = process_payment()
        payments_logger.debug(f'Estado del pago: {payment_result}')
    except Exception as e:
        payments_logger.error(f'Error en el proceso de pago: {str(e)}', exc_info=True)

def some_operation():
    """Simula una operación."""
    return {'status': 'success', 'data': 'some_data'}

def process_payment():
    """Simula un proceso de pago."""
    return {'status': 'completed', 'amount': 100.00}
