"""
💰 MÓDULO DE IMPUESTOS - huntRED

Modelos para gestión fiscal completa:
- Configuración de impuestos
- Cálculo automático
- Retenciones
- Declaraciones fiscales
"""

from .tax_configuration import TaxConfiguration, TaxRate, TaxExemption
from .tax_calculations import TaxCalculation, TaxRetention, TaxDeclaration
from .fiscal_regimes import FiscalRegime, FiscalObligation

__all__ = [
    # Configuración de impuestos
    'TaxConfiguration', 'TaxRate', 'TaxExemption',
    
    # Cálculos fiscales
    'TaxCalculation', 'TaxRetention', 'TaxDeclaration',
    
    # Régimen fiscal
    'FiscalRegime', 'FiscalObligation',
] 