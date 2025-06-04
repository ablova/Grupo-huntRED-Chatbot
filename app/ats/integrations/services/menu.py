# /home/pablo/app/ats/integrations/services/menu.py
"""
Sistema de Menú Dinámico para Grupo huntRED® Chatbot

Este módulo proporciona un sistema de menú flexible y dinámico que permite:
- Registro automático de menús y evaluaciones
- Gestión de permisos por unidad de negocio
- Personalización de opciones según el contexto
- Integración con workflows y evaluaciones
"""

from typing import Dict, List, Optional, TypedDict, Literal, Any
from enum import Enum
import logging
from dataclasses import dataclass, field
import importlib
import inspect

from app.models import BusinessUnit
from app.ats.chatbot.workflow.core.workflow_manager import WorkflowManager

logger = logging.getLogger(__name__)

class MenuItemType(Enum):
    """Tipos de elementos de menú disponibles"""
    MENU = "menu"
    ASSESSMENT = "assessment"
    ACTION = "action"
    WORKFLOW = "workflow"

class MenuItem(TypedDict):
    """Estructura para elementos de menú"""
    title: str
    payload: str
    description: str
    type: MenuItemType
    handler: Optional[str]
    icon: Optional[str]
    children: List[dict]
    required_permissions: List[str]
    metadata: Dict[str, Any]
    business_units: List[str]

@dataclass
class MenuSystem:
    """Sistema de menú dinámico para evaluaciones y workflows"""
    
    def __init__(self):
        self._menus: Dict[str, MenuItem] = {}
        self._assessments: Dict[str, dict] = {}
        self._workflows: Dict[str, dict] = {}
        self._actions: Dict[str, dict] = {}
        self.workflow_manager = WorkflowManager()
    
    def register_menu(self, name: str, title: str, description: str = "", 
                     icon: str = "", permissions: List[str] = None,
                     business_units: List[str] = None, metadata: Dict = None) -> 'MenuSystem':
        """Registra una nueva categoría de menú"""
        self._menus[name] = {
            "title": title,
            "payload": f"menu_{name}",
            "description": description,
            "type": MenuItemType.MENU,
            "icon": icon,
            "children": [],
            "required_permissions": permissions or [],
            "business_units": business_units or [],
            "metadata": metadata or {},
            "handler": None
        }
        return self
    
    def register_assessment(self, name: str, title: str, description: str = "", 
                           icon: str = "", menu: str = "evaluations",
                           handler: str = None, permissions: List[str] = None,
                           business_units: List[str] = None, metadata: Dict = None) -> 'MenuSystem':
        """Registra una nueva evaluación"""
        assessment = {
            "title": title,
            "payload": f"assessment_{name}",
            "description": description,
            "type": MenuItemType.ASSESSMENT,
            "icon": icon,
            "handler": handler or f"handle_{name}_assessment",
            "required_permissions": permissions or [],
            "business_units": business_units or [],
            "metadata": metadata or {},
            "children": []
        }
        
        self._assessments[name] = assessment
        
        # Añadir al menú especificado
        if menu in self._menus:
            self._menus[menu]["children"].append(assessment)
        
        return self
    
    def register_workflow(self, name: str, title: str, description: str = "",
                         icon: str = "", menu: str = "workflows",
                         handler: str = None, permissions: List[str] = None,
                         business_units: List[str] = None, metadata: Dict = None) -> 'MenuSystem':
        """Registra un nuevo workflow en el menú"""
        workflow = {
            "title": title,
            "payload": f"workflow_{name}",
            "description": description,
            "type": MenuItemType.WORKFLOW,
            "icon": icon,
            "handler": handler or f"handle_{name}_workflow",
            "required_permissions": permissions or [],
            "business_units": business_units or [],
            "metadata": metadata or {},
            "children": []
        }
        
        self._workflows[name] = workflow
        
        # Añadir al menú especificado
        if menu in self._menus:
            self._menus[menu]["children"].append(workflow)
        
        return self
    
    def register_action(self, name: str, title: str, description: str = "",
                       icon: str = "", menu: str = "actions",
                       handler: str = None, permissions: List[str] = None,
                       business_units: List[str] = None, metadata: Dict = None) -> 'MenuSystem':
        """Registra una nueva acción en el menú"""
        action = {
            "title": title,
            "payload": f"action_{name}",
            "description": description,
            "type": MenuItemType.ACTION,
            "icon": icon,
            "handler": handler or f"handle_{name}_action",
            "required_permissions": permissions or [],
            "business_units": business_units or [],
            "metadata": metadata or {},
            "children": []
        }
        
        self._actions[name] = action
        
        # Añadir al menú especificado
        if menu in self._menus:
            self._menus[menu]["children"].append(action)
        
        return self
    
    def get_menu(self, name: str) -> Optional[MenuItem]:
        """Obtiene un menú por nombre"""
        return self._menus.get(name)
    
    def get_assessment(self, name: str) -> Optional[dict]:
        """Obtiene una evaluación por nombre"""
        return self._assessments.get(name)
    
    def get_workflow(self, name: str) -> Optional[dict]:
        """Obtiene un workflow por nombre"""
        return self._workflows.get(name)
    
    def get_action(self, name: str) -> Optional[dict]:
        """Obtiene una acción por nombre"""
        return self._actions.get(name)
    
    def get_available_items(self, business_unit: str = None, 
                          user_permissions: List[str] = None) -> List[dict]:
        """Obtiene todos los elementos disponibles para un usuario"""
        if user_permissions is None:
            user_permissions = []
            
        available_items = []
        
        # Filtrar por unidad de negocio y permisos
        def filter_item(item):
            if business_unit and item.get("business_units") and business_unit not in item["business_units"]:
                return False
            if item.get("required_permissions") and not any(p in user_permissions for p in item["required_permissions"]):
                return False
            return True
        
        # Añadir menús
        for menu in self._menus.values():
            if filter_item(menu):
                filtered_menu = menu.copy()
                filtered_menu["children"] = [
                    child for child in menu["children"]
                    if filter_item(child)
                ]
                available_items.append(filtered_menu)
        
        return available_items
    
    def get_available_assessments(self, business_unit: str = None,
                                user_permissions: List[str] = None) -> List[dict]:
        """Obtiene las evaluaciones disponibles para un usuario"""
        if user_permissions is None:
            user_permissions = []
            
        return [
            {k: v for k, v in a.items() if k != "handler"}
            for a in self._assessments.values()
            if (not business_unit or not a.get("business_units") or business_unit in a["business_units"]) and
               (not a.get("required_permissions") or any(p in user_permissions for p in a["required_permissions"]))
        ]
    
    def get_available_workflows(self, business_unit: str = None,
                              user_permissions: List[str] = None) -> List[dict]:
        """Obtiene los workflows disponibles para un usuario"""
        if user_permissions is None:
            user_permissions = []
            
        return [
            {k: v for k, v in w.items() if k != "handler"}
            for w in self._workflows.values()
            if (not business_unit or not w.get("business_units") or business_unit in w["business_units"]) and
               (not w.get("required_permissions") or any(p in user_permissions for p in w["required_permissions"]))
        ]
    
    def get_available_actions(self, business_unit: str = None,
                            user_permissions: List[str] = None) -> List[dict]:
        """Obtiene las acciones disponibles para un usuario"""
        if user_permissions is None:
            user_permissions = []
            
        return [
            {k: v for k, v in a.items() if k != "handler"}
            for a in self._actions.values()
            if (not business_unit or not a.get("business_units") or business_unit in a["business_units"]) and
               (not a.get("required_permissions") or any(p in user_permissions for p in a["required_permissions"]))
        ]

# Inicializar el sistema de menú global
menu_system = MenuSystem()

# Registrar menús por defecto
menu_system \
    .register_menu("evaluations", "🎯 Evaluaciones", 
                  "Completa evaluaciones para mejorar tu perfil", "📊",
                  business_units=["huntred", "huntred_executive", "huntu"]) \
    .register_menu("profile", "👤 Mi Perfil", 
                  "Gestiona tu perfil profesional", "👤",
                  business_units=["huntred", "huntred_executive", "huntu"]) \
    .register_menu("jobs", "🔍 Buscar Empleo", 
                  "Encuentra trabajos específicos", "💼",
                  business_units=["huntred", "huntred_executive", "huntu"])

# Registrar evaluaciones
menu_system \
    .register_assessment(
        "cultural_fit",
        "🌍 Compatibilidad Cultural",
        "Evalúa tu alineación con la cultura organizacional y descubre cómo tus valores y preferencias se alinean con diferentes entornos laborales",
        "🌍",
        "evaluations",
        "handle_cultural_fit_assessment",
        ["can_take_assessments"],
        ["huntred", "huntred_executive", "huntu"]
    ) \
    .register_assessment(
        "professional_dna",
        "🧬 ADN Profesional",
        "Descubre tu perfil profesional único y cómo se alinea con diferentes roles y organizaciones",
        "🧬",
        "evaluations",
        "handle_professional_dna_assessment",
        ["can_take_assessments"],
        ["huntred", "huntred_executive", "huntu"]
    ) \
    .register_assessment(
        "personality",
        "🧠 Prueba de Personalidad",
        "Conoce más sobre tu personalidad laboral y cómo influye en tu desarrollo profesional",
        "🧠",
        "evaluations",
        "handle_personality_assessment",
        ["can_take_assessments"],
        ["huntred", "huntred_executive", "huntu"]
    )

# Funciones helper
def get_available_assessments(business_unit: str = None, user_permissions: List[str] = None) -> List[dict]:
    """
    Obtiene las evaluaciones disponibles para una unidad de negocio.
    
    Args:
        business_unit: Unidad de negocio para filtrar evaluaciones
        user_permissions: Permisos del usuario para filtrar evaluaciones disponibles
        
    Returns:
        List[dict]: Lista de evaluaciones disponibles
    """
    return menu_system.get_available_assessments(business_unit, user_permissions)

def get_menus(business_unit: str = None, user_permissions: List[str] = None) -> List[dict]:
    """
    Obtiene todos los menús para una unidad de negocio.
    
    Args:
        business_unit: Unidad de negocio para filtrar menús
        user_permissions: Permisos del usuario para filtrar menús disponibles
        
    Returns:
        List[dict]: Lista de menús disponibles
    """
    return menu_system.get_available_items(business_unit, user_permissions)

def get_assessment_handler(assessment_name: str) -> Optional[str]:
    """
    Obtiene el nombre de la función manejadora para una evaluación.
    
    Args:
        assessment_name: Nombre de la evaluación
        
    Returns:
        Optional[str]: Nombre de la función manejadora o None si no existe
    """
    assessment = menu_system.get_assessment(assessment_name)
    return assessment["handler"] if assessment else None
