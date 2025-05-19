# /home/pablo/app/com/chatbot/workflow/__init__.py
"""
Inicialización del paquete de workflows del chatbot.

Define y registra los workflows disponibles en el sistema, incluyendo:
- Base para todos los workflows
- Workflows específicos por funcionalidad
- Gestor centralizado para creación y gestión de workflows
"""

import logging

# Importamos la clase base y el gestor de workflows
from app.com.chatbot.workflow.base_workflow import BaseWorkflow
from app.com.chatbot.workflow.workflow_manager import (
    WorkflowManager, workflow_manager, 
    get_workflow_manager, create_workflow, handle_workflow_message
)

# Importamos los módulos de workflow específicos
try:
    from app.com.chatbot.workflow.talent_analysis_workflow import TalentAnalysisWorkflow
    from app.com.chatbot.workflow.cultural_fit_workflow import CulturalFitWorkflow
except ImportError as e:
    logging.warning(f"Error importando workflows específicos: {e}")

__all__ = [
    # Módulos existentes
    'amigro',
    'common',
    'executive',
    'jobs',
    'personality',
    'profile_questions',
    
    # Nuevos módulos
    'base_workflow',
    'workflow_manager',
    'talent_analysis_workflow',
    'cultural_fit_workflow',
    
    # Clases y funciones expuestas
    'BaseWorkflow',
    'WorkflowManager',
    'TalentAnalysisWorkflow',
    'CulturalFitWorkflow',
    
    # Funciones utilitarias
    'get_workflow_manager',
    'create_workflow',
    'handle_workflow_message'
]

# Inicializamos el gestor de workflows (singleton)
logging.info("Inicializando gestor de workflows...")
workflow_manager_instance = get_workflow_manager()
