# /home/pablo/app/com/utils/optimizers.py
"""
Optimizadores para el sistema Grupo huntRED®.
Este módulo registra optimizaciones para NLP, GPT y componentes relacionados
sin modificar la estructura de código existente.
"""

import logging
import importlib
import sys
import os
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

# Registro de componentes optimizados disponibles
OPTIMIZED_COMPONENTS = {}

def import_if_exists(module_path: str) -> Optional[Any]:
    """Importa un módulo si existe, devuelve None si no"""
    try:
        return importlib.import_module(module_path)
    except ImportError:
        return None

def register_optimizer(name: str, module_path: str, class_name: str) -> bool:
    """
    Registra un componente optimizado
    
    Args:
        name: Nombre del componente
        module_path: Ruta al módulo
        class_name: Nombre de la clase
        
    Returns:
        True si se registró correctamente
    """
    try:
        module = import_if_exists(module_path)
        if not module:
            logger.debug(f"Módulo {module_path} no encontrado")
            return False
            
        component_class = getattr(module, class_name, None)
        if not component_class:
            logger.debug(f"Clase {class_name} no encontrada en {module_path}")
            return False
            
        OPTIMIZED_COMPONENTS[name] = {
            'module': module,
            'class': component_class,
            'path': module_path
        }
        logger.info(f"Componente optimizado registrado: {name}")
        return True
    except Exception as e:
        logger.error(f"Error registrando optimizador {name}: {str(e)}")
        return False

def get_optimized_component(name: str) -> Optional[Any]:
    """
    Obtiene un componente optimizado por nombre
    
    Args:
        name: Nombre del componente
        
    Returns:
        Clase del componente o None si no existe
    """
    component = OPTIMIZED_COMPONENTS.get(name)
    return component['class'] if component else None

def initialize_optimizers() -> Dict[str, bool]:
    """
    Inicializa todos los optimizadores disponibles
    
    Returns:
        Dict con estado de cada optimizador
    """
    results = {}
    
    # 1. Verificar disponibilidad de optimizadores
    try:
        # Optimizadores de AI (GPT)
        results['ai_adapters'] = register_optimizer(
            'gpt_handler',
            'app.utils.ai_adapters',
            'ModelAdapterFactory'
        )
        
        # Optimizadores de NLP
        results['nlp_processor'] = register_optimizer(
            'nlp_processor',
            'app.utils.nlp_processor',
            'NLPProcessor'
        )
        
        # Conectores para compatibilidad
        results['gpt_connector'] = register_optimizer(
            'gpt_connector',
            'app.com.chatbot.optimized_connectors',
            'OptimizedGPTConnector'
        )
        
        results['nlp_connector'] = register_optimizer(
            'nlp_connector',
            'app.com.chatbot.optimized_connectors',
            'OptimizedNLPConnector'
        )
        
        # 2. Intentar monkey-patching si es necesario
        try:
            from app.import_config import register_handler
            
            if results['gpt_connector']:
                register_handler('gpt_handler', 'app.com.chatbot.optimized_connectors', 'OptimizedGPTConnector')
                logger.info("GPT optimizado registrado en el sistema de importación")
                
            if results['nlp_connector']:
                register_handler('nlp_processor', 'app.com.chatbot.optimized_connectors', 'OptimizedNLPConnector')
                logger.info("NLP optimizado registrado en el sistema de importación")
                
        except ImportError:
            logger.debug("Sistema de registro de handlers no disponible")
        
        # 3. Verificar si estamos en un entorno Django y registrar señales
        try:
            from django.apps import apps
            if apps.is_installed('django.contrib.admin'):
                logger.info("Entorno Django detectado, registrando optimizadores")
                
                # Registrar señales para carga perezosa
                try:
                    from django.core.signals import request_started
                    
                    def load_optimizations(sender, **kwargs):
                        request_started.disconnect(load_optimizations)
                        logger.info("Cargando optimizaciones por señal de solicitud")
                        try:
                            from app.utils.system_integrator import SystemIntegrator
                            SystemIntegrator.initialize()
                        except ImportError:
                            pass
                    
                    request_started.connect(load_optimizations, weak=False)
                    logger.info("Optimizaciones registradas para carga perezosa")
                except ImportError:
                    pass
        except ImportError:
            pass
            
        # Resultado global
        success = any(results.values())
        logger.info(f"Inicialización de optimizadores: {'Éxito' if success else 'Fallida'}")
        return results
        
    except Exception as e:
        logger.error(f"Error general inicializando optimizadores: {str(e)}")
        return {'error': str(e)}

# Intentar optimización de CPU global
def optimize_cpu_usage():
    """Configura el entorno para optimizar uso de CPU"""
    try:
        # TensorFlow (si está disponible)
        try:
            import tensorflow as tf
            # Configuración de logs
            os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # 0=INFO, 1=WARNING, 2=ERROR, 3=FATAL
            os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"  # Deshabilitar optimizaciones oneDNN
            
            # Configuración de GPU/CPU
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                try:
                    # Restringir el crecimiento de memoria de la GPU
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    logger.info(f"TensorFlow usando GPU: {gpus}")
                except RuntimeError as e:
                    logger.warning(f"Error configurando GPU: {e}")
            else:
                # Configuración para CPU
                os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Deshabilitar GPU
                tf.config.threading.set_inter_op_parallelism_threads(1)
                tf.config.threading.set_intra_op_parallelism_threads(1)
                logger.info("TensorFlow optimizado para CPU")
                
            # Configuración de rendimiento
            tf.config.optimizer.set_jit(True)  # Habilitar XLA JIT
            tf.config.optimizer.set_experimental_options({
                'layout_optimizer': True,
                'constant_folding': True,
                'shape_optimization': True,
                'remapping': True,
            })
            
        except ImportError as e:
            logger.warning(f"TensorFlow no está disponible: {e}")
            
        # NumPy (si está disponible)
        try:
            import numpy as np
            try:
                # Usar MKL optimizado si está disponible
                np_cores = os.cpu_count()
                np.set_num_threads(min(4, np_cores) if np_cores else 1)
                logger.info(f"NumPy optimizado para CPU (hilos: {np.get_num_threads()})")
            except (AttributeError, RuntimeError) as e:
                logger.warning(f"No se pudo optimizar NumPy: {e}")
        except ImportError as e:
            logger.warning(f"NumPy no está disponible: {e}")
            
        return True
    except Exception as e:
        logger.error(f"Error optimizando CPU: {str(e)}")
        return False

# Ejecutar optimización al importar
optimize_cpu_usage()
initialize_optimizers()
