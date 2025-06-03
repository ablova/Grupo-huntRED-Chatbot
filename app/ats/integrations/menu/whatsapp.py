"""
Implementación de menús para WhatsApp
"""

from typing import Dict, List, Any
from .base import BaseMenu

class WhatsAppMenu(BaseMenu):
    """Implementación de menús para WhatsApp"""
    
    def create_menu(self, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crea un menú de WhatsApp con las opciones especificadas
        
        Args:
            options: Lista de opciones del menú
            
        Returns:
            Diccionario con el menú de WhatsApp
        """
        menu = {
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": "Menú Principal"
                },
                "body": {
                    "text": "Selecciona una opción:"
                },
                "action": {
                    "button": "Ver Opciones",
                    "sections": [
                        {
                            "title": "Opciones Disponibles",
                            "rows": [
                                {
                                    "id": option["payload"],
                                    "title": option["title"],
                                    "description": option.get("description", "")
                                }
                                for option in options
                            ]
                        }
                    ]
                }
            }
        }
        
        return menu
        
    def create_submenu(self, parent: Dict[str, Any], options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crea un submenú de WhatsApp para una opción del menú
        
        Args:
            parent: Opción padre del submenú
            options: Lista de opciones del submenú
            
        Returns:
            Diccionario con el submenú de WhatsApp
        """
        submenu = {
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": parent["title"]
                },
                "body": {
                    "text": parent.get("description", "Selecciona una opción:")
                },
                "action": {
                    "button": "Ver Opciones",
                    "sections": [
                        {
                            "title": "Opciones Disponibles",
                            "rows": [
                                {
                                    "id": option["payload"],
                                    "title": option["title"],
                                    "description": option.get("description", "")
                                }
                                for option in options
                            ]
                        }
                    ]
                }
            }
        }
        
        return submenu
        
    def create_evaluations_menu(self) -> Dict[str, Any]:
        """
        Crea el menú de evaluaciones para WhatsApp
        
        Returns:
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