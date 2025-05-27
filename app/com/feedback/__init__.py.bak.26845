# /home/pablo/app/com/feedback/__init__.py
"""
Sistema integral de retroalimentación para Grupo huntRED®.

Este módulo proporciona una plataforma unificada para gestionar la retroalimentación
en todas las etapas del ciclo de vida del servicio:

1. Pre-servicio (propuestas)
2. Durante el servicio (implementación)
3. Post-servicio (evaluación final)

El sistema incluye herramientas para recopilar, analizar y actuar sobre la retroalimentación
con el fin de mejorar continuamente los servicios ofrecidos.
"""

import logging
from django.conf import settings

# Configuración del logger
logger = logging.getLogger(__name__)

# Etapas del ciclo de vida del feedback
FEEDBACK_STAGES = {
    'proposal': {
        'name': 'Propuesta',
        'description': 'Retroalimentación sobre propuestas enviadas'
    },
    'ongoing': {
        'name': 'Servicio en Curso',
        'description': 'Retroalimentación durante la prestación del servicio'
    },
    'completed': {
        'name': 'Servicio Concluido',
        'description': 'Evaluación final al concluir el servicio'
    }
}

# Tipos de servicio que ofrecemos
SERVICE_TYPES = {
    'talent_analysis': 'Análisis de Talento 360°',
    'recruitment': 'Reclutamiento Especializado',
    'executive_search': 'Búsqueda de Ejecutivos',
    'consulting': 'Consultoría de HR',
    'outplacement': 'Outplacement',
    'training': 'Capacitación',
}

# Inicializar el módulo
def initialize_module():
    """Inicializa los componentes del sistema de retroalimentación."""
    try:
        logger.info("Inicializando sistema de feedback...")
        
        # Inicializar trackers para las distintas etapas
        try:
            from app.com.pricing.proposal_tracker import get_proposal_tracker
            proposal_tracker = get_proposal_tracker()
            logger.info("Tracker de propuestas inicializado")
        except ImportError as e:
            logger.warning(f"No se pudo inicializar el tracker de propuestas: {e}")
            
        try:
            from app.com.feedback.ongoing_tracker import get_ongoing_service_tracker
            ongoing_tracker = get_ongoing_service_tracker()
            logger.info("Tracker de servicios en curso inicializado")
        except ImportError as e:
            logger.warning(f"No se pudo inicializar el tracker de servicios en curso: {e}")
            
        try:
            from app.com.feedback.completion_tracker import get_service_completion_tracker
            completion_tracker = get_service_completion_tracker()
            logger.info("Tracker de servicios concluidos inicializado")
        except ImportError as e:
            logger.warning(f"No se pudo inicializar el tracker de servicios concluidos: {e}")
            
        # Registrar señales para eventos automáticos
        try:
            from app.com.feedback.signals import connect_feedback_signals
            connect_feedback_signals()
            logger.info("Señales de feedback registradas correctamente")
        except ImportError as e:
            logger.warning(f"No se pudieron registrar las señales de feedback: {e}")
        
        logger.info("Sistema de feedback inicializado completamente")
        
    except Exception as e:
        logger.error(f"Error al inicializar sistema de feedback: {e}")

# Función auxiliar para obtener el tracker adecuado según la etapa
def get_feedback_tracker(stage):
    """
    Obtiene el tracker de feedback adecuado según la etapa del ciclo de vida.
    
    Args:
        stage (str): Etapa del servicio ('proposal', 'ongoing', 'completed')
        
    Returns:
        object: Instancia del tracker correspondiente
    """
    if stage == 'proposal':
        from app.com.pricing.proposal_tracker import get_proposal_tracker
        return get_proposal_tracker()
    elif stage == 'ongoing':
        from app.com.feedback.ongoing_tracker import get_ongoing_service_tracker
        return get_ongoing_service_tracker()
    elif stage == 'completed':
        from app.com.feedback.completion_tracker import get_service_completion_tracker
        return get_service_completion_tracker()
    else:
        raise ValueError(f"Etapa de feedback no válida: {stage}")

# Inicializar el módulo cuando se importa
initialize_module()
