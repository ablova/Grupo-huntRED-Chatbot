"""
Sistema centralizado de señales para Grupo huntRED®.
Proporciona un registro y gestión unificados de las señales en toda la aplicación.
"""

import logging
import importlib
from typing import Dict, List, Callable, Any, Optional
from django.dispatch import Signal, receiver
from django.db.models.signals import (
    pre_save, post_save, pre_delete, post_delete,
    m2m_changed, pre_migrate, post_migrate
)
from django.core.signals import request_started, request_finished
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed

# Logger configurado por LoggingManager
logger = logging.getLogger(__name__)

# Señales personalizadas para la aplicación
business_unit_changed = Signal()
candidate_state_changed = Signal()
document_processed = Signal()
notification_sent = Signal()
payment_processed = Signal()
whatsapp_message_received = Signal()

# Registro de receptores para facilitar la gestión
signal_registry = {}


def register_signal_handler(signal: Signal, handler: Callable, sender=None, **kwargs):
    """
    Registra un manejador de señal con monitoreo de rendimiento y errores.
    
    Args:
        signal: Señal a la que conectarse
        handler: Función que manejará la señal
        sender: Remitente específico (modelo) para el que actuar
        **kwargs: Argumentos adicionales para el receptor
    """
    # Crear un wrapper que monitorea el rendimiento y maneja errores
    @receiver(signal, sender=sender, **kwargs)
    def monitored_handler(*args, **kwargs):
        # Obtener contexto para logs
        sender_name = sender.__name__ if hasattr(sender, '__name__') else str(sender)
        handler_name = handler.__name__ if hasattr(handler, '__name__') else str(handler)
        
        # Intentar obtener contexto de BU
        bu_name = None
        if 'instance' in kwargs and hasattr(kwargs['instance'], 'business_unit'):
            bu = kwargs['instance'].business_unit
            bu_name = bu.name if hasattr(bu, 'name') else str(bu)
        
        try:
            # Monitorear rendimiento si existe el tracker
            try:
                from app.utils.system_integrator import SystemIntegrator
                performance_tracker = SystemIntegrator.get_component('performance_tracker')
                
                if performance_tracker:
                    with performance_tracker.measure(f"signal:{handler_name}"):
                        return handler(*args, **kwargs)
            except ImportError:
                # Si no existe el integrador, usar monitoreo básico
                import time
                start_time = time.time()
                result = handler(*args, **kwargs)
                elapsed = time.time() - start_time
                
                if elapsed > 0.5:  # Advertir si tarda más de 500ms
                    logger.warning(
                        f"Signal handler slow execution: {handler_name} for {sender_name} "
                        f"took {elapsed:.2f}s",
                        extra={'bu_name': bu_name}
                    )
                return result
                
            # Sin monitoreo
            return handler(*args, **kwargs)
            
        except Exception as e:
            # Registrar error
            logger.error(
                f"Error in signal handler {handler_name} for {sender_name}: {str(e)}",
                exc_info=True,
                extra={'bu_name': bu_name}
            )
            # No propagar para evitar romper la cadena de señales
            return None
    
    # Registrar en nuestro registro
    signal_key = f"{signal}"
    if signal_key not in signal_registry:
        signal_registry[signal_key] = []
    
    signal_registry[signal_key].append({
        'handler': handler.__name__ if hasattr(handler, '__name__') else str(handler),
        'sender': sender.__name__ if hasattr(sender, '__name__') else str(sender),
        'monitored_handler': monitored_handler
    })
    
    # Devolver el manejador monitoreado por si se necesita desconectar
    return monitored_handler


def disconnect_signal_handler(signal: Signal, handler: Callable, sender=None):
    """
    Desconecta un manejador de señal.
    
    Args:
        signal: Señal de la que desconectar
        handler: Manejador original registrado
        sender: Remitente específico
    """
    signal_key = f"{signal}"
    
    if signal_key in signal_registry:
        handlers = signal_registry[signal_key]
        
        for i, h in enumerate(handlers):
            if h['handler'] == (handler.__name__ if hasattr(handler, '__name__') else str(handler)):
                # Desconectar
                signal.disconnect(h['monitored_handler'], sender=sender)
                # Eliminar del registro
                del signal_registry[signal_key][i]
                logger.debug(f"Disconnected signal handler: {h['handler']} for {signal_key}")
                return True
    
    return False


def register_model_signals():
    """
    Registra todas las señales relacionadas con modelos.
    Busca archivos de señales en app/signals/ y los carga.
    """
    # Modelos críticos que siempre deben tener señales
    critical_models = [
        ('app', 'BusinessUnit'),
        ('app', 'Person'),
        ('app', 'Vacante'),
        ('app', 'Pago'),
        ('app', 'NotificationChannel'),
    ]
    
    # Primero registrar señales para modelos críticos
    for app_label, model_name in critical_models:
        try:
            # Importar el modelo
            from django.apps import apps
            model = apps.get_model(app_label, model_name)
            
            # Nombre del módulo específico de señales
            signal_module_name = f"app.signals.{model_name.lower()}_signals"
            
            try:
                # Intentar importar
                importlib.import_module(signal_module_name)
                logger.info(f"Registered signals for {model_name}")
            except ImportError:
                logger.debug(f"No signal module found for {model_name}")
        except Exception as e:
            logger.error(f"Error registering signals for {model_name}: {str(e)}")
    
    # Cargar todos los módulos de señales en app/signals/
    try:
        import os
        from django.conf import settings
        
        signals_dir = os.path.join(settings.BASE_DIR, 'app', 'signals')
        if os.path.exists(signals_dir):
            for filename in os.listdir(signals_dir):
                if filename.endswith('_signals.py'):
                    module_name = f"app.signals.{filename[:-3]}"
                    try:
                        importlib.import_module(module_name)
                        logger.debug(f"Loaded signal module: {module_name}")
                    except Exception as e:
                        logger.error(f"Error loading signal module {module_name}: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading signal modules: {str(e)}")


def get_signal_registry() -> Dict:
    """
    Obtiene un registro de todas las señales registradas.
    
    Returns:
        Diccionario con información de señales
    """
    return {
        signal_name: [
            {'handler': h['handler'], 'sender': h['sender']}
            for h in handlers
        ]
        for signal_name, handlers in signal_registry.items()
    }


# Inicializar registros
def initialize_signals():
    """
    Inicializa el sistema de señales.
    """
    # Registrar señales específicas para modelos
    register_model_signals()
    
    # Intentar registrar manejadores de rendimiento global
    try:
        from app.utils.system_optimization import PerformanceTracker
        
        # Monitorear inicio y fin de peticiones
        @receiver(request_started)
        def on_request_started(sender, **kwargs):
            PerformanceTracker.start_request()
        
        @receiver(request_finished)
        def on_request_finished(sender, **kwargs):
            PerformanceTracker.end_request()
        
        logger.info("Registered performance monitoring signals")
    except ImportError:
        pass
    
    logger.info("Signal system initialized")
    return True
