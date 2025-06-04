# /home/pablo/app/ats/integrations/menu/whatsapp.py
"""
Implementación de menús para WhatsApp

Esta clase maneja la creación y presentación de menús interactivos en WhatsApp,
adaptándose a las capacidades de la plataforma y respetando los permisos del usuario.
"""

from typing import Dict, List, Any, Optional
import logging
from ..base.services import BaseService
from .base import BaseMenu, check_permissions

logger = logging.getLogger(__name__)

class WhatsAppMenu(BaseMenu):
    """Implementación de menús para WhatsApp"""
    
    def __init__(self, business_unit: str, wa_business_account_id: str = None):
        """
        Inicializa el menú de WhatsApp
        
        Args:
            business_unit: Unidad de negocio (amigro/huntred/huntu)
            wa_business_account_id: ID de la cuenta de WhatsApp Business (opcional)
        """
        super().__init__(business_unit)
        self.wa_business_account_id = wa_business_account_id
        
    def create_menu(self, options: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Crea un menú de WhatsApp con las opciones especificadas
        
        Args:
            options: Lista de opciones del menú
            **kwargs: Argumentos adicionales:
                - user_permissions: Lista de permisos del usuario
                - header_text: Texto personalizado para el encabezado
                - body_text: Texto personalizado para el cuerpo
                
        Returns:
            Dict: Estructura del menú de WhatsApp
        """
        user_permissions = kwargs.get('user_permissions', [])
        header_text = kwargs.get('header_text', 'Menú Principal')
        body_text = kwargs.get('body_text', 'Selecciona una opción:')
        
        # Filtrar opciones visibles para el usuario
        visible_options = [
            option for option in options
            if self._is_menu_item_visible(option, user_permissions)
        ]
        
        # Si hay más de 10 opciones, dividir en secciones
        if len(visible_options) > 10:
            sections = []
            for i in range(0, len(visible_options), 10):
                section_options = visible_options[i:i+10]
                sections.append({
                    'title': f'Opciones {i//10 + 1}',
                    'rows': [
                        self._create_menu_row(option, user_permissions)
                        for option in section_options
                    ]
                })
            action = {
                'button': 'Ver Opciones',
                'sections': sections
            }
        else:
            action = {
                'button': 'Ver Opciones',
                'sections': [{
                    'title': 'Opciones Disponibles',
                    'rows': [
                        self._create_menu_row(option, user_permissions)
                        for option in visible_options
                    ]
                }]
            }
        
        menu = {
            'type': 'interactive',
            'interactive': {
                'type': 'list',
                'header': {
                    'type': 'text',
                    'text': header_text[:60]  # Límite de WhatsApp
                },
                'body': {
                    'text': body_text[:1024]  # Límite de WhatsApp
                },
                'action': action
            }
        }
        
        return menu
        
    def _create_menu_row(self, option: Dict[str, Any], user_permissions: List[str] = None) -> Dict[str, str]:
        """
        Crea una fila de menú para WhatsApp
        
        Args:
            option: Opción de menú
            user_permissions: Permisos del usuario
            
        Returns:
            Dict: Fila de menú para WhatsApp
        """
        return {
            'id': option.get('payload', ''),
            'title': option.get('title', '')[:24],  # Límite de WhatsApp
            'description': option.get('description', '')[:72]  # Límite de WhatsApp
        }
        
    def create_submenu(self, parent: Dict[str, Any], options: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Crea un submenú para una opción del menú en WhatsApp
        
        Args:
            parent: Opción padre del submenú
            options: Lista de opciones del submenú
            **kwargs: Argumentos adicionales:
                - user_permissions: Lista de permisos del usuario
                
        Returns:
            Dict: Estructura del submenú de WhatsApp
        """
        user_permissions = kwargs.get('user_permissions', [])
        
        # Filtrar opciones visibles para el usuario
        visible_options = [
            option for option in options
            if self._is_menu_item_visible(option, user_permissions)
        ]
        
        # Crear secciones para el submenú
        sections = []
        current_section = []
        
        for option in visible_options:
            if len(current_section) >= 10:  # WhatsApp limita a 10 opciones por sección
                sections.append({
                    'rows': [self._create_menu_row(opt, user_permissions) for opt in current_section]
                })
                current_section = []
            current_section.append(option)
            
        if current_section:
            sections.append({
                'rows': [self._create_menu_row(opt, user_permissions) for opt in current_section]
            })
        
        menu = {
            'type': 'interactive',
            'interactive': {
                'type': 'list',
                'header': {
                    'type': 'text',
                    'text': parent.get('title', 'Submenú')[:60]  # Límite de WhatsApp
                },
                'body': {
                    'text': parent.get('description', 'Selecciona una opción:')[:1024]  # Límite de WhatsApp
                },
                'action': {
                    'button': 'Ver Opciones',
                    'sections': [
                        {
                            'title': parent.get('title', 'Opciones')[:24],  # Límite de WhatsApp
                            'rows': [self._create_menu_row(opt, user_permissions) for opt in visible_options[:10]]
                        }
                    ]
                }
            }
        }
        
        return menu
        
    def handle_menu_selection(self, payload: str, user_permissions: List[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Maneja la selección de una opción de menú
        
        Args:
            payload: Payload de la opción seleccionada
            user_permissions: Permisos del usuario
            **kwargs: Argumentos adicionales específicos de la implementación
            
        Returns:
            Dict: Respuesta a enviar al usuario
        """
        menu_item = self.find_menu_item(payload)
        if not menu_item:
            return self._create_text_message("Opción no válida. Por favor, inténtalo de nuevo.")
            
        # Verificar permisos
        required_perms = menu_item.get('required_permissions', [])
        if not check_permissions(required_perms, user_permissions):
            return self._create_text_message("No tienes permiso para acceder a esta opción.")
            
        # Manejar la acción del menú
        handler_name = menu_item.get('handler')
        if handler_name:
            handler = self.get_handler(handler_name)
            if handler:
                return handler(menu_item, **kwargs)
                
        # Si es un submenú, mostrarlo
        if 'submenu' in menu_item and menu_item['submenu']:
            return self.create_submenu(
                menu_item, 
                menu_item['submenu'],
                user_permissions=user_permissions,
                **kwargs
            )
            
        # Si no hay manejador ni submenú, mostrar un mensaje por defecto
        return self._create_text_message(f"Has seleccionado: {menu_item.get('title', 'Opción')}")
        
    def _create_text_message(self, text: str) -> Dict[str, Any]:
        """
        Crea un mensaje de texto simple para WhatsApp
        
        Args:
            text: Texto del mensaje
            
        Returns:
            Dict: Estructura del mensaje de texto
        """
        return {
            'type': 'text',
            'text': text
        }
        
    def create_evaluations_menu(self) -> Dict[str, Any]:
        """
        Crea el menú de evaluaciones para WhatsApp
        
        Returns:
            Dict: Estructura del menú de evaluaciones
            Diccionario con el menú de evaluaciones
        """
        menu = {
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": self.evaluations_menu["title"]
                },
                "body": {
                    "text": self.evaluations_menu["description"]
                },
                "action": {
                    "button": "Ver Evaluaciones",
                    "sections": [
                        {
                            "title": "Evaluaciones Disponibles",
                            "rows": [
                                {
                                    "id": option["payload"],
                                    "title": option["title"],
                                    "description": option["description"]
                                }
                                for option in self.evaluations_menu["options"]
                            ]
                        }
                    ]
                }
            }
        }
        
        return menu 