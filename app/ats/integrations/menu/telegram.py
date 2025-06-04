# /home/pablo/app/ats/integrations/menu/telegram.py
"""
Implementación de menús para Telegram
"""

from typing import Dict, List, Any
from .base import BaseMenu

class TelegramMenu(BaseMenu):
    """Implementación de menús para Telegram"""
    
    def create_menu(self, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crea un menú de Telegram con las opciones especificadas
        
        Args:
            options: Lista de opciones del menú
            
        Returns:
            Diccionario con el menú de Telegram
        """
        keyboard = []
        for option in options:
            keyboard.append([{
                "text": option["title"],
                "callback_data": option["payload"]
            }])
            
        menu = {
            "text": "Selecciona una opción:",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }
        
        return menu
        
    def create_submenu(self, parent: Dict[str, Any], options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crea un submenú de Telegram para una opción del menú
        
        Args:
            parent: Opción padre del submenú
            options: Lista de opciones del submenú
            
        Returns:
            Diccionario con el submenú de Telegram
        """
        keyboard = []
        for option in options:
            keyboard.append([{
                "text": option["title"],
                "callback_data": option["payload"]
            }])
            
        # Agregar botón de regreso
        keyboard.append([{
            "text": "⬅️ Regresar",
            "callback_data": "menu_principal"
        }])
            
        submenu = {
            "text": f"{parent['title']}\n{parent.get('description', 'Selecciona una opción:')}",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }
        
        return submenu
        
    def create_evaluations_menu(self) -> Dict[str, Any]:
        """
        Crea el menú de evaluaciones para Telegram
        
        Returns:
            Diccionario con el menú de evaluaciones
        """
        keyboard = []
        for option in self.evaluations_menu["options"]:
            keyboard.append([{
                "text": option["title"],
                "callback_data": option["payload"]
            }])
            
        # Agregar botón de regreso
        keyboard.append([{
            "text": "⬅️ Regresar",
            "callback_data": "menu_principal"
        }])
            
        menu = {
            "text": f"{self.evaluations_menu['title']}\n{self.evaluations_menu['description']}",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }
        
        return menu 