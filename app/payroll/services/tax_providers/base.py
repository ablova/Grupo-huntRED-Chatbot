"""
Interfaces base para proveedores de tablas fiscales
Define el contrato que deben implementar todos los proveedores
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import date


class TaxTableProvider(ABC):
    """
    Interfaz base para proveedores de tablas fiscales
    Cada país implementará su propia versión
    """
    
    @abstractmethod
    def get_tax_table(self, table_name: str, year: int, period: str = None) -> Dict[str, Any]:
        """
        Obtiene tabla fiscal específica
        
        Args:
            table_name: Nombre de la tabla (ej: "isr", "imss", "subsidio")
            year: Año de la tabla
            period: Periodo específico (opcional, ej: "monthly", "biweekly")
            
        Returns:
            Diccionario con la estructura de la tabla
        """
        pass
        
    @abstractmethod
    def get_constant(self, constant_name: str, year: int, period: str = None) -> float:
        """
        Obtiene constante fiscal específica
        
        Args:
            constant_name: Nombre de la constante (ej: "uma", "smg")
            year: Año de la constante
            period: Periodo específico (opcional)
            
        Returns:
            Valor de la constante
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si el proveedor está disponible
        
        Returns:
            True si el proveedor está activo y disponible
        """
        pass


class TaxProviderFactory:
    """
    Fábrica para crear instancias de proveedores fiscales
    según el país y configuración
    """
    
    @staticmethod
    def get_provider(country_code: str, config: Optional[Dict] = None) -> TaxTableProvider:
        """
        Obtiene proveedor adecuado según país
        
        Args:
            country_code: Código de país ISO (MX, CO, AR, etc)
            config: Configuración opcional para el proveedor
            
        Returns:
            Instancia de TaxTableProvider para el país especificado
        """
        from .mx_provider import MXTaxProvider
        from .default_provider import DefaultTaxProvider
        
        providers = {
            'MX': MXTaxProvider,
            # Añadir otros países cuando estén implementados
            # 'CO': COTaxProvider,
            # 'AR': ARTaxProvider,
        }
        
        provider_class = providers.get(country_code.upper(), DefaultTaxProvider)
        return provider_class(config)
