"""
Módulo centralizado de signals para Grupo huntRED®.
Este archivo registra todos los signals disponibles en el sistema
y proporciona un sistema optimizado de gestión de señales.

Sigue la estructura modular de Django y las reglas globales de Grupo huntRED®.
"""

import logging
import warnings

logger = logging.getLogger(__name__)

# Advertencia para el archivo de signals obsoleto
from django.utils.deprecation import RemovedInNextVersionWarning
warnings.warn(
    "El archivo app/signals.py está obsoleto. Usa los módulos específicos en app/signals/",
    RemovedInNextVersionWarning, stacklevel=2
)

# Inicializar sistema core de señales
try:
    from app.signals.core import (
        initialize_signals, register_signal_handler,
        # Exportar señales personalizadas centralizadas
        business_unit_changed, candidate_state_changed, document_processed,
        notification_sent, payment_processed, whatsapp_message_received
    )
    
    logger.info("Sistema optimizado de señales inicializado")
except ImportError as e:
    logger.debug(f"Sistema core de señales no disponible: {str(e)}")

# Importar señales personalizadas de los módulos
try:
    # Chatbot
    from app.signals.chatbot import (
        process_chat_message, initialize_chat_session
    )
    
    # Vacantes
    from app.signals.vacancies import (
        vacancy_published, vacancy_matched,
        update_vacancy_timestamps, vacancy_tags_changed, application_created
    )
    
    # Pagos
    from app.signals.payments import (
        payment_processed, payment_failed, invoice_generated,
        handle_payment_update, handle_invoice_creation
    )
    
    # Usuarios
    from app.signals.user import (
        profile_completed, cv_analyzed,
        analyze_cv, create_person_profile
    )
    
    # Publicaciones
    from app.signals.publish import (
        publication_created, publication_updated, publication_failed,
        auto_publish_vacancy, handle_publication_result
    )
    
    # Notificaciones
    from app.signals.notifications import (
        notification_created, notification_sent, notification_failed,
        handle_notification_created, process_notification_queue
    )
    
    logger.info("Módulos de señales cargados correctamente")
except ImportError as e:
    logger.error(f"Error cargando módulos de señales: {str(e)}")

# Definir qué funciones y señales se exponen al importar desde app.signals
__all__ = [
    # Core de señales
    'initialize_signals', 'register_signal_handler',
    
    # Señales personalizadas centralizadas
    'business_unit_changed', 'candidate_state_changed', 'document_processed',
    'notification_sent', 'payment_processed', 'whatsapp_message_received',
    
    # Señales de chatbot
    'process_chat_message', 'initialize_chat_session',
    
    # Señales de vacantes
    'vacancy_published', 'vacancy_matched',
    'update_vacancy_timestamps', 'vacancy_tags_changed', 'application_created',
    
    # Señales de pagos
    'payment_processed', 'payment_failed', 'invoice_generated',
    'handle_payment_update', 'handle_invoice_creation',
    
    # Señales de usuarios
    'profile_completed', 'cv_analyzed',
    'analyze_cv', 'create_person_profile',
    
    # Señales de publicaciones
    'publication_created', 'publication_updated', 'publication_failed',
    'auto_publish_vacancy', 'handle_publication_result',
    
    # Señales de notificaciones
    'notification_created', 'notification_sent', 'notification_failed',
    'handle_notification_created', 'process_notification_queue'
]

# Inicializar sistema de señales
try:
    initialize_signals()
    logger.info("Sistema de señales inicializado correctamente")
except Exception as e:
    logger.error(f"Error inicializando sistema de señales: {str(e)}")
