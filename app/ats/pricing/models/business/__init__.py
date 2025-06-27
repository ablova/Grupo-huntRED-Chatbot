"""
Modelos de negocio organizados.
"""
from .empleadores import (
    Empleador,
    Empleado
)

from .oportunidades import (
    Oportunidad,
    PagoRecurrente,
    SincronizacionLog,
    SincronizacionError
)

__all__ = [
    # Empleadores y empleados
    'Empleador',
    'Empleado',
    
    # Oportunidades y sincronización
    'Oportunidad',
    'PagoRecurrente',
    'SincronizacionLog',
    'SincronizacionError',
] 