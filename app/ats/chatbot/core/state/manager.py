# app/ats/chatbot/core/state/manager.py
"""
Gestor de estado del chatbot.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ChatStateManager:
    """
    Gestor de estado para el chatbot.
    """
    
    def __init__(self):
        self.states = {}
        logger.info("ChatStateManager inicializado")
    
    def get_state(self, conversation_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de una conversación.
        """
        return self.states.get(conversation_id, {})
    
    def set_state(self, conversation_id: str, state: Dict[str, Any]) -> None:
        """
        Establece el estado de una conversación.
        """
        self.states[conversation_id] = state
        logger.debug(f"Estado actualizado para conversación {conversation_id}")
    
    def update_state(self, conversation_id: str, updates: Dict[str, Any]) -> None:
        """
        Actualiza el estado de una conversación.
        """
        current_state = self.get_state(conversation_id)
        current_state.update(updates)
        self.set_state(conversation_id, current_state)
    
    def clear_state(self, conversation_id: str) -> None:
        """
        Limpia el estado de una conversación.
        """
        if conversation_id in self.states:
            del self.states[conversation_id]
            logger.debug(f"Estado limpiado para conversación {conversation_id}")
    
    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Obtiene el contexto de una conversación.
        """
        state = self.get_state(conversation_id)
        return state.get('context', {})
    
    def set_conversation_context(self, conversation_id: str, context: Dict[str, Any]) -> None:
        """
        Establece el contexto de una conversación.
        """
        self.update_state(conversation_id, {'context': context})
    
    def add_message_to_history(self, conversation_id: str, message: Dict[str, Any]) -> None:
        """
        Agrega un mensaje al historial de la conversación.
        """
        state = self.get_state(conversation_id)
        if 'message_history' not in state:
            state['message_history'] = []
        
        message['timestamp'] = datetime.now().isoformat()
        state['message_history'].append(message)
        self.set_state(conversation_id, state)
    
    def get_message_history(self, conversation_id: str) -> list:
        """
        Obtiene el historial de mensajes de una conversación.
        """
        state = self.get_state(conversation_id)
        return state.get('message_history', [])
    
    def set_workflow_state(self, conversation_id: str, workflow_state: str) -> None:
        """
        Establece el estado del workflow para una conversación.
        """
        self.update_state(conversation_id, {'workflow_state': workflow_state})
    
    def get_workflow_state(self, conversation_id: str) -> Optional[str]:
        """
        Obtiene el estado del workflow de una conversación.
        """
        state = self.get_state(conversation_id)
        return state.get('workflow_state')
    
    def set_user_data(self, conversation_id: str, user_data: Dict[str, Any]) -> None:
        """
        Establece los datos del usuario para una conversación.
        """
        self.update_state(conversation_id, {'user_data': user_data})
    
    def get_user_data(self, conversation_id: str) -> Dict[str, Any]:
        """
        Obtiene los datos del usuario de una conversación.
        """
        state = self.get_state(conversation_id)
        return state.get('user_data', {})
    
    def is_conversation_active(self, conversation_id: str) -> bool:
        """
        Verifica si una conversación está activa.
        """
        state = self.get_state(conversation_id)
        return state.get('active', False)
    
    def activate_conversation(self, conversation_id: str) -> None:
        """
        Activa una conversación.
        """
        self.update_state(conversation_id, {'active': True, 'activated_at': datetime.now().isoformat()})
    
    def deactivate_conversation(self, conversation_id: str) -> None:
        """
        Desactiva una conversación.
        """
        self.update_state(conversation_id, {'active': False, 'deactivated_at': datetime.now().isoformat()}) 