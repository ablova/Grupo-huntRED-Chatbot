"""
Módulo para manejar el contexto de los workflows del chatbot.

Este módulo proporciona la clase WorkflowContext que gestiona el estado
y contexto de los workflows, permitiendo una gestión eficiente del
flujo de trabajo y sus transiciones.
"""

import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from app.models import Person, BusinessUnit, ChatState

logger = logging.getLogger(__name__)

class WorkflowContext:
    """
    Clase para gestionar el contexto de los workflows.
    
    Esta clase mantiene el estado y contexto de los workflows,
    permitiendo una gestión eficiente de las transiciones y
    el seguimiento del progreso.
    """
    
    def __init__(self, user: Optional[Person] = None, 
                 business_unit: Optional[BusinessUnit] = None,
                 chat_state: Optional[ChatState] = None):
        """
        Inicializa el contexto del workflow.
        
        Args:
            user: Instancia del modelo Person
            business_unit: Unidad de negocio actual
            chat_state: Estado actual del chat
        """
        self.user = user
        self.business_unit = business_unit
        self.chat_state = chat_state
        self.context = self._build_initial_context()
        self.metadata = {
            'created_at': timezone.now().isoformat(),
            'last_updated': timezone.now().isoformat()
        }
        
    def _build_initial_context(self) -> Dict[str, Any]:
        """
        Construye el contexto inicial del workflow.
        
        Returns:
            Dict[str, Any]: Contexto inicial
        """
        context = {
            'user_id': self.user.id if self.user else None,
            'business_unit': {
                'id': self.business_unit.id if self.business_unit else None,
                'name': self.business_unit.name if self.business_unit else None,
                'type': self.business_unit.type if self.business_unit else None
            } if self.business_unit else None,
            'chat_state': self.chat_state.state if self.chat_state else None,
            'timestamp': timezone.now().isoformat()
        }
        
        if self.chat_state and self.chat_state.context:
            context.update(self.chat_state.context)
            
        return context
    
    def update(self, new_context: Dict[str, Any]) -> None:
        """
        Actualiza el contexto con nueva información.
        
        Args:
            new_context: Nuevo contexto a añadir
        """
        self.context.update(new_context)
        self.metadata['last_updated'] = timezone.now().isoformat()
        logger.debug(f"Contexto actualizado: {new_context}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor del contexto.
        
        Args:
            key: Clave a buscar
            default: Valor por defecto si no se encuentra
            
        Returns:
            Any: Valor encontrado o el valor por defecto
        """
        return self.context.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Establece un valor en el contexto.
        
        Args:
            key: Clave a establecer
            value: Valor a asignar
        """
        self.context[key] = value
        self.metadata['last_updated'] = timezone.now().isoformat()
        logger.debug(f"Valor establecido en contexto: {key}={value}")
    
    def clear(self) -> None:
        """Limpia el contexto actual."""
        self.context = self._build_initial_context()
        self.metadata['last_updated'] = timezone.now().isoformat()
        logger.debug("Contexto limpiado")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el contexto a un diccionario.
        
        Returns:
            Dict[str, Any]: Diccionario con el contexto
        """
        return {
            'context': self.context,
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        """
        Representación en cadena del contexto.
        
        Returns:
            str: Representación textual del contexto
        """
        return f"WorkflowContext(user_id={self.context.get('user_id')}, " \
               f"business_unit={self.context.get('business_unit', {}).get('name')}, " \
               f"state={self.context.get('chat_state')})" 