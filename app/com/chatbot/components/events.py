"""
Sistema de eventos para workflows del chatbot.
Permite la comunicación y coordinación entre diferentes workflows.
"""

from typing import Dict, Any, Callable, List
import logging
from django.core.cache import cache

logger = logging.getLogger('chatbot.workflow.events')

class WorkflowEventManager:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_cache = {}
        self.cache_timeout = 3600  # 1 hora

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Suscribe una función callback a un tipo de evento."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Elimina una suscripción a un tipo de evento."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]

    async def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publica un evento a todos los suscriptores."""
        logger.info(f"Publicando evento {event_type} con datos: {data}")
        
        # Almacenar evento en caché
        cache_key = f"workflow_event:{event_type}:{data.get('id', '')}"
        cache.set(cache_key, data, self.cache_timeout)
        
        # Notificar a suscriptores
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    await callback(event_type, data)
                except Exception as e:
                    logger.error(f"Error en callback para evento {event_type}: {e}")

    def get_event_history(self, event_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene el historial de eventos de un tipo específico."""
        # Implementar lógica para obtener historial de eventos
        return []

# Singleton para el gestor de eventos
workflow_event_manager = WorkflowEventManager()

# Tipos de eventos predefinidos
EVENT_TYPES = {
    'WORKFLOW_STARTED': 'workflow_started',
    'WORKFLOW_COMPLETED': 'workflow_completed',
    'WORKFLOW_FAILED': 'workflow_failed',
    'STEP_COMPLETED': 'step_completed',
    'USER_INPUT_RECEIVED': 'user_input_received',
    'BUSINESS_UNIT_CHANGED': 'business_unit_changed',
    'PROFILE_UPDATED': 'profile_updated',
    'EVALUATION_COMPLETED': 'evaluation_completed'
} 