"""
Core del sistema de workflows del chatbot.
Proporciona la funcionalidad base y los componentes esenciales.
"""

from app.com.chatbot.workflow.core.base_workflow import BaseWorkflow
from app.com.chatbot.workflow.core.workflow_manager import (
    WorkflowManager, workflow_manager,
    get_workflow_manager, create_workflow, handle_workflow_message
)
from app.com.chatbot.components.metrics import ChatBotMetrics, chatbot_metrics
from app.com.chatbot.components.events import (
    WorkflowEventManager, workflow_event_manager, EVENT_TYPES
)

__all__ = [
    # Clases base
    'BaseWorkflow',
    'WorkflowManager',
    'ChatBotMetrics',
    'WorkflowEventManager',
    
    # Instancias singleton
    'workflow_manager',
    'chatbot_metrics',
    'workflow_event_manager',
    
    # Funciones utilitarias
    'get_workflow_manager',
    'create_workflow',
    'handle_workflow_message',
    
    # Constantes
    'EVENT_TYPES'
]
