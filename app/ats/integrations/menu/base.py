"""
Clase base para manejar menús en las integraciones
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from ..base.services import BaseService
from .options import MENU_OPTIONS_BY_BU, EVALUATIONS_MENU

class BaseMenu(ABC):
    """Clase base para manejar menús en las integraciones"""
    
    def __init__(self, business_unit: str):
        """
        Inicializa el menú base
        
        Args:
            business_unit: Unidad de negocio (amigro/huntred)
        """
        self.business_unit = business_unit
        self.menu_options = MENU_OPTIONS_BY_BU.get(business_unit, [])
        self.evaluations_menu = EVALUATIONS_MENU
        
    @abstractmethod
    def create_menu(self, options: List[Dict[str, Any]]) -> Any:
        """
        Crea un menú con las opciones especificadas
        
        Args:
            options: Lista de opciones del menú
            
        Returns:
            Menú creado según la plataforma
        """
        pass
        
    @abstractmethod
    def create_submenu(self, parent: Any, options: List[Dict[str, Any]]) -> Any:
        """
        Crea un submenú para una opción del menú
        
        Args:
            parent: Opción padre del submenú
            options: Lista de opciones del submenú
            
        Returns:
            Submenú creado según la plataforma
        """
        pass
        
    def get_menu_options(self) -> List[Dict[str, Any]]:
        """
        Obtiene las opciones del menú principal
        
        Returns:
            Lista de opciones del menú
        """
        return self.menu_options
        
    def get_evaluations_menu(self) -> Dict[str, Any]:
        """
        Obtiene el menú de evaluaciones
        
        Returns:
            Diccionario con las opciones del menú de evaluaciones
        """
        return self.evaluations_menu
        
    def get_menu_by_payload(self, payload: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene una opción del menú por su payload
        
        Args:
            payload: Payload de la opción a buscar
            
        Returns:
            Opción del menú si existe, None en caso contrario
        """
        for option in self.menu_options:
            if option["payload"] == payload:
                return option
            if "submenu" in option:
                for suboption in option["submenu"]:
                    if suboption["payload"] == payload:
                        return suboption
        return None
        
    def get_evaluation_by_payload(self, payload: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene una evaluación por su payload
        
        Args:
            payload: Payload de la evaluación a buscar
            
        Returns:
            Evaluación si existe, None en caso contrario
        """
        for option in self.evaluations_menu["options"]:
            if option["payload"] == payload:
                return option
        return None 