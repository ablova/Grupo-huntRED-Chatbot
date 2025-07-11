# app/ats/pricing/models/pac_configuration.py
"""
Módulo para la configuración de Proveedores Autorizados de Certificación (PAC)
para facturación electrónica en México.

Este módulo importa la clase PACConfiguration desde gateways.py para evitar
conflictos de modelos en Django.
"""

# Importamos la clase PACConfiguration desde gateways.py para evitar duplicación
from app.ats.pricing.models.payments.gateways import PACConfiguration

# No definimos la clase nuevamente para evitar el error:
# RuntimeError: Conflicting 'pacconfiguration' models in application 'app'
