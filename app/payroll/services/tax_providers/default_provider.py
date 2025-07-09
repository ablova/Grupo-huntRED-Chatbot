"""
Proveedor fiscal predeterminado
Utilizado como fallback cuando no hay proveedor específico para un país
"""
import logging
from typing import Dict, Any, Optional
from datetime import date

from .base import TaxTableProvider

logger = logging.getLogger(__name__)

class DefaultTaxProvider(TaxTableProvider):
    """
    Proveedor fiscal genérico para usar como fallback
    Proporciona valores básicos y genéricos cuando no hay proveedor específico
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el proveedor con configuración opcional
        
        Args:
            config: Configuración opcional del proveedor
        """
        self.config = config or {}
        self._init_fallback_values()
        
    def _init_fallback_values(self):
        """Inicializa valores de fallback genéricos"""
        self.constants = {
            "min_wage": {
                "2024": 250.0,
                "2023": 200.0,
                "2022": 175.0,
                "2021": 150.0,
                "2020": 125.0
            },
            "tax_threshold": {
                "2024": 1000.0,
                "2023": 950.0,
                "2022": 900.0,
                "2021": 850.0,
                "2020": 800.0
            }
        }
        
        self.tax_tables = {
            "income_tax": {
                "2024": {
                    "ranges": [
                        {"lower": 0.0, "upper": 1000.0, "fixed": 0.0, "percentage": 0.0},
                        {"lower": 1000.01, "upper": 5000.0, "fixed": 0.0, "percentage": 10.0},
                        {"lower": 5000.01, "upper": 10000.0, "fixed": 400.0, "percentage": 15.0},
                        {"lower": 10000.01, "upper": 20000.0, "fixed": 1150.0, "percentage": 20.0},
                        {"lower": 20000.01, "upper": float('inf'), "fixed": 3150.0, "percentage": 25.0}
                    ]
                }
            }
        }
    
    def get_tax_table(self, table_name: str, year: int, period: str = None) -> Dict[str, Any]:
        """
        Obtiene tabla fiscal genérica
        
        Args:
            table_name: Nombre de la tabla 
            year: Año de la tabla
            period: Periodo específico (opcional)
            
        Returns:
            Diccionario con la estructura de la tabla o vacío
        """
        logger.warning(f"Usando proveedor fiscal genérico para {table_name} {year}")
        
        # Normalizar nombre de tabla
        if "tax" not in table_name:
            table_name = "income_tax"  # Tabla por defecto
        
        # Obtener tabla para el año específico
        year_str = str(year)
        if table_name in self.tax_tables and year_str in self.tax_tables[table_name]:
            return self.tax_tables[table_name][year_str]
            
        # Si no hay tabla específica para ese año, usar el más reciente
        if table_name in self.tax_tables:
            years = sorted([int(y) for y in self.tax_tables[table_name].keys()], reverse=True)
            for y in years:
                if y <= year:
                    logger.warning(f"Tabla para {year} no encontrada, usando {y}")
                    return self.tax_tables[table_name][str(y)]
        
        # No hay tabla disponible
        logger.error(f"No hay tabla fiscal disponible para {table_name} {year}")
        return {}
    
    def get_constant(self, constant_name: str, year: int, period: str = None) -> float:
        """
        Obtiene constante fiscal genérica
        
        Args:
            constant_name: Nombre de la constante
            year: Año de la constante
            period: Periodo específico (opcional)
            
        Returns:
            Valor de la constante o 0.0
        """
        logger.warning(f"Usando proveedor fiscal genérico para constante {constant_name} {year}")
        
        # Normalizar nombre de constante
        if constant_name not in self.constants:
            constant_name = "min_wage"  # Constante por defecto
            
        # Obtener constante para el año específico
        year_str = str(year)
        if year_str in self.constants[constant_name]:
            return self.constants[constant_name][year_str]
            
        # Si no hay constante específica para ese año, usar la más reciente
        years = sorted([int(y) for y in self.constants[constant_name].keys()], reverse=True)
        for y in years:
            if y <= year:
                logger.warning(f"Constante para {year} no encontrada, usando {y}")
                return self.constants[constant_name][str(y)]
                
        return 0.0
        
    def is_available(self) -> bool:
        """
        Verifica si el proveedor está disponible
        Este proveedor siempre está disponible como fallback
        
        Returns:
            True siempre
        """
        return True
