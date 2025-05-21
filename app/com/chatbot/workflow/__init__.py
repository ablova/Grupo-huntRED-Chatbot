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
from app.com.chatbot.workflow.core.base_workflow import BaseWorkflow
from app.com.chatbot.workflow.core.workflow_manager import (
    WorkflowManager, workflow_manager, 
    get_workflow_manager, create_workflow, handle_workflow_message
)
from app.com.chatbot.workflow.common.context import WorkflowContext

# Importamos los módulos de workflow específicos
try:
    from app.com.chatbot.workflow.assessments.talent.talent_analysis_workflow import TalentAnalysisWorkflow
    from app.com.chatbot.workflow.assessments.cultural.cultural_fit_workflow import CulturalFitWorkflow
    from app.com.chatbot.workflow.business_units.huntred_executive import (
        iniciar_flujo_huntred_executive,
        continuar_perfil_huntred_executive,
        manejar_respuesta_huntred_executive,
        process_huntred_executive_candidate
    )
    from app.com.chatbot.workflow.business_units.huntu import process_huntu_candidate
    from app.com.chatbot.workflow.business_units.huntred import process_huntred_candidate
    from app.com.chatbot.workflow.business_units.amigro import process_amigro_candidate
    from app.com.chatbot.workflow.business_units.sexsi import iniciar_flujo_sexsi, confirmar_pago_sexsi
except ImportError as e:
    logging.warning(f"Error importando workflows específicos: {e}")

__all__ = [
    # Módulos base
    'base_workflow',
    'workflow_manager',
    'context',
    
    # Workflows específicos
    'talent_analysis_workflow',
    'cultural_fit_workflow',
    'huntred_executive',
    'huntu',
    'huntred',
    'amigro',
    'sexsi',
    'jobs',
    'personality',
    'profile_questions',
    'common',
    
    # Clases y funciones expuestas
    'BaseWorkflow',
    'WorkflowManager',
    'TalentAnalysisWorkflow',
    'CulturalFitWorkflow',
    'WorkflowContext',
    
    # Funciones de HuntRED Executive
    'iniciar_flujo_huntred_executive',
    'continuar_perfil_huntred_executive',
    'manejar_respuesta_huntred_executive',
    'process_huntred_executive_candidate',
    
    # Funciones de otros workflows
    'process_huntu_candidate',
    'process_huntred_candidate',
    'process_amigro_candidate',
    'iniciar_flujo_sexsi',
    'confirmar_pago_sexsi',
    
    # Funciones utilitarias
    'get_workflow_manager',
    'create_workflow',
    'handle_workflow_message'
]

# Inicializamos el gestor de workflows (singleton)
logging.info("Inicializando gestor de workflows...")
workflow_manager_instance = get_workflow_manager()
