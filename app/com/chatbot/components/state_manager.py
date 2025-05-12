from typing import Optional
from django.utils import timezone
from app.models import Person, BusinessUnit, ChatState, StateTransition
import logging

logger = logging.getLogger(__name__)

class StateManager:
    """
    Gestor de estados para el chatbot.
    
    Características:
    - Manejo de transiciones de estado
    - Validación de estados
    - Seguimiento de historial
    - Manejo de timeouts
    """

    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el gestor de estados.
        
        Args:
            business_unit (BusinessUnit): Unidad de negocio asociada
        """
        self.business_unit = business_unit
        self._transitions = None

    async def determine_next_state(self, intent: str) -> Optional[str]:
        """
        Determina el siguiente estado basado en el intent.
        
        Args:
            intent (str): Intent detectado
            
        Returns:
            Optional[str]: Estado siguiente o None si no se puede determinar
        """
        try:
            if not self._transitions:
                await self._load_transitions()

            # Buscar transiciones válidas para el intent
            for transition in self._transitions:
                if transition.matches(intent):
                    return transition.target_state

            return self._get_default_transition(intent)

        except Exception as e:
            logger.error(f"Error determining next state: {str(e)}", exc_info=True)
            return None

    async def update_state(self, chat_state: ChatState, new_state: str) -> bool:
        """
        Actualiza el estado del chat.
        
        Args:
            chat_state (ChatState): Estado actual del chat
            new_state (str): Nuevo estado
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        try:
            # Validar transición
            if not await self._validate_transition(chat_state.state, new_state):
                return False

            # Actualizar estado
            chat_state.state = new_state
            chat_state.last_transition = timezone.now()
            await chat_state.asave()
            
            # Actualizar historial
            await self._update_history(chat_state, new_state)
            
            return True

        except Exception as e:
            logger.error(f"Error updating state: {str(e)}", exc_info=True)
            return False

    async def _load_transitions(self):
        """Carga las transiciones de estado desde la base de datos."""
        self._transitions = await StateTransition.objects.filter(
            business_unit=self.business_unit,
            is_active=True
        ).aall()

    async def _validate_transition(self, current_state: str, new_state: str) -> bool:
        """Valida si la transición de estado es válida."""
        # Implementar lógica de validación
        return True

    async def _update_history(self, chat_state: ChatState, new_state: str):
        """Actualiza el historial de estados."""
        chat_state.history.append({
            'state': new_state,
            'timestamp': timezone.now()
        })
        await chat_state.asave()
