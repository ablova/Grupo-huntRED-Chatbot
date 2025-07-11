# app/ats/pagos/models.py
"""
Módulo puente para mantener compatibilidad con código legacy.
Este módulo reexporta modelos desde app.models para mantener compatibilidad
con código que aún importa desde app.ats.pagos.models.
"""

from app.models import Pago, Payment

# Reexportar otros modelos que puedan ser necesarios
# Agregar aquí según se necesite en el futuro

# Clase ficticia para Invoice si es necesaria
class Invoice:
    """
    Clase placeholder para Invoice.
    Reemplazar con la implementación correcta cuando esté disponible.
    """
    pass
