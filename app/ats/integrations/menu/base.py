# /home/pablo/app/ats/integrations/menu/base.py
"""
Clase base para manejar menús en las integraciones

Esta clase proporciona una interfaz común para la implementación de menús
en diferentes plataformas de mensajería (WhatsApp, Telegram, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable
from functools import wraps
import logging

from ..base.services import BaseService
from .options import (
    MENU_OPTIONS_BY_BU, 
    EVALUATIONS_MENU,
    MENU_STRUCTURE,
    MENU_TYPE_MAIN,
    MENU_TYPE_SUB,
    MENU_TYPE_ACTION
)

logger = logging.getLogger(__name__)

def check_permissions(required_permissions: List[str] = None, user_permissions: List[str] = None) -> bool:
    """
    Verifica si el usuario tiene los permisos necesarios.
    
    Args:
        required_permissions: Lista de permisos requeridos
        user_permissions: Lista de permisos del usuario
        
    Returns:
        bool: True si el usuario tiene los permisos necesarios
    """
    if not required_permissions:
        return True
        
    if not user_permissions:
        return False
        
    return all(perm in user_permissions for perm in required_permissions)

class BaseMenu(ABC):
    """Clase base para manejar menús en las integraciones"""
    
    def __init__(self, business_unit: str):
        """
        Inicializa el menú base
        
        Args:
            business_unit: Unidad de negocio (amigro/huntred/huntu)
        """
        self.business_unit = business_unit
        self.menu_structure = MENU_STRUCTURE.get(business_unit, {})
        self.menu_options = self._process_menu_options(MENU_OPTIONS_BY_BU.get(business_unit, []))
        self.evaluations_menu = self._process_menu_item(EVALUATIONS_MENU)
        self.handlers: Dict[str, Callable] = {}
        
    def _process_menu_options(self, options: List[Dict]) -> List[Dict]:
        """Procesa las opciones de menú para asegurar que tengan la estructura correcta"""
        return [self._process_menu_item(item) for item in options]
        
    def _process_menu_item(self, item: Dict) -> Dict:
        """Procesa un ítem de menú individual"""
        # Establecer valores por defecto
        item.setdefault('type', MENU_TYPE_MAIN)
        item.setdefault('required_permissions', [])
        item.setdefault('handler', None)
        
        # Procesar submenús recursivamente
        if 'submenu' in item and isinstance(item['submenu'], list):
            item['submenu'] = [self._process_menu_item(subitem) for subitem in item['submenu']]
            
        return item
        
    def register_handler(self, payload: str, handler: Callable):
        """
        Registra un manejador para un payload específico
        
        Args:
            payload: Identificador del menú/acción
            handler: Función que manejará la acción
        """
        self.handlers[payload] = handler
        return handler
        
    def get_handler(self, payload: str) -> Optional[Callable]:
        """
        Obtiene el manejador para un payload específico
        
        Args:
            payload: Identificador del menú/acción
            
        Returns:
            Callable: Función manejadora o None si no existe
        """
        return self.handlers.get(payload)
        
    def find_menu_item(self, payload: str, menu: List[Dict] = None) -> Optional[Dict]:
        """
        Busca un ítem de menú por su payload
        
        Args:
            payload: Identificador del ítem de menú
            menu: Menú donde buscar (por defecto usa el menú principal)
            
        Returns:
            Dict: El ítem de menú encontrado o None
        """
        if menu is None:
            menu = self.menu_options
            
        for item in menu:
            if item.get('payload') == payload:
                return item
                
            if 'submenu' in item and isinstance(item['submenu'], list):
                found = self.find_menu_item(payload, item['submenu'])
                if found:
                    return found
                    
        return None
        
    @abstractmethod
    def create_menu(self, options: List[Dict[str, Any]], **kwargs) -> Any:
        """
        Crea un menú con las opciones especificadas
        
        Args:
            options: Lista de opciones del menú
            **kwargs: Argumentos adicionales específicos de la plataforma
            
        Returns:
            Menú creado según la plataforma
            
        Nota:
            Las implementaciones deben manejar la creación del menú según
            las capacidades de la plataforma (botones, listas, etc.)
        """
        pass
        
    def create_submenu(self, parent: Any, options: List[Dict[str, Any]], **kwargs) -> Any:
        """
        Crea un submenú para una opción del menú
        
        Args:
            parent: Opción padre del submenú
            options: Lista de opciones del submenú
            **kwargs: Argumentos adicionales específicos de la plataforma
            
        Returns:
            Submenú creado según la plataforma
            
        Nota:
            Por defecto, delega a create_menu. Las implementaciones pueden
            sobrescribir este método si necesitan un comportamiento diferente.
        """
        return self.create_menu(options, **kwargs)
        
    def get_available_options(self, user_permissions: List[str] = None) -> List[Dict]:
        """
        Obtiene las opciones de menú disponibles para el usuario
        
        Args:
            user_permissions: Lista de permisos del usuario
            
        Returns:
            List[Dict]: Opciones de menú disponibles
        """
        return [
            self._filter_menu_item(item, user_permissions)
            for item in self.menu_options
            if self._is_menu_item_visible(item, user_permissions)
        ]
        
    def _is_menu_item_visible(self, item: Dict, user_permissions: List[str] = None) -> bool:
        """
        Verifica si un ítem de menú debe mostrarse al usuario
        
        Args:
            item: Ítem de menú a verificar
            user_permissions: Permisos del usuario
            
        Returns:
            bool: True si el ítem debe mostrarse
        """
        # Verificar permisos
        required_perms = item.get('required_permissions', [])
        if not check_permissions(required_perms, user_permissions):
            return False
            
        # Verificar visibilidad de submenús
        if 'submenu' in item and isinstance(item['submenu'], list):
            item['submenu'] = [
                subitem for subitem in item['submenu']
                if self._is_menu_item_visible(subitem, user_permissions)
            ]
            # Si no hay submenús visibles, ocultar el menú padre
            if not item['submenu']:
                return False
                
        return True
        
    def _filter_menu_item(self, item: Dict, user_permissions: List[str] = None) -> Dict:
        """
        Filtra la información sensible de un ítem de menú
        
        Args:
            item: Ítem de menú a filtrar
            user_permissions: Permisos del usuario
            
        Returns:
            Dict: Ítem de menú filtrado
        """
        filtered = {
            'title': item.get('title', ''),
            'payload': item.get('payload', ''),
            'description': item.get('description', '')
        }
        
        if 'submenu' in item and isinstance(item['submenu'], list):
            filtered['submenu'] = [
                self._filter_menu_item(subitem, user_permissions)
                for subitem in item['submenu']
            ]
            
        return filtered
        
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