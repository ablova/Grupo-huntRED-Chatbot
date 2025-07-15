# app/ats/pricing/__init__.py
"""
Módulo de pricing unificado para huntRED.

Este módulo incluye:
- Estrategias de pricing y precios
- Gateways de pago y transacciones
- Facturación electrónica SAT
- Pagos programados
- Integraciones con WordPress
- Modelos migrados (empleadores, empleados, oportunidades)
"""

# ============================================================================
# MODELOS DE PRICING
# ============================================================================
# Los modelos se importan de forma lazy para evitar AppRegistryNotReady

# ============================================================================
# SERVICIOS
# ============================================================================
# Los servicios se importan de forma lazy para evitar AppRegistryNotReady

# ============================================================================
# TAREAS
# ============================================================================
# Las tareas se importan de forma lazy para evitar AppRegistryNotReady

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
default_app_config = 'app.ats.pricing.apps.PricingConfig'

# ============================================================================
# CONSTANTES
# ============================================================================
PAYMENT_METHODS = [
    ('credit_card', 'Tarjeta de Crédito'),
    ('debit_card', 'Tarjeta de Débito'),
    ('paypal', 'PayPal'),
    ('bank_transfer', 'Transferencia Bancaria'),
    ('cash', 'Efectivo'),
    ('apple_pay', 'Apple Pay'),
    ('google_pay', 'Google Pay'),
    ('clip', 'Clip'),
]

GATEWAY_TYPES = [
    ('stripe', 'Stripe'),
    ('paypal', 'PayPal'),
    ('conekta', 'Conekta'),
    ('clip', 'Clip'),
    ('banorte', 'Banorte'),
    ('banamex', 'Banamex'),
    ('bbva', 'BBVA'),
]

PAYMENT_FREQUENCIES = [
    ('daily', 'Diario'),
    ('weekly', 'Semanal'),
    ('biweekly', 'Quincenal'),
    ('monthly', 'Mensual'),
    ('quarterly', 'Trimestral'),
    ('semiannual', 'Semestral'),
    ('annual', 'Anual'),
    ('custom', 'Personalizado'),
]

EXHIBITION_TYPES = [
    ('PUE', 'Pago en una sola exhibición'),
    ('PPD', 'Pago en parcialidades o diferido'),
]

PAYMENT_STATUSES = [
    ('pending', 'Pendiente'),
    ('processing', 'Procesando'),
    ('completed', 'Completado'),
    ('failed', 'Fallido'),
    ('cancelled', 'Cancelado'),
    ('refunded', 'Reembolsado'),
]

# ============================================================================
# VERSION
# ============================================================================
__version__ = '2.0.0'
__author__ = 'huntRED Team'
__description__ = 'Módulo de pricing unificado con facturación electrónica y pagos programados'

__all__ = []
