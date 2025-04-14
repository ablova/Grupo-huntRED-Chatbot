# /home/pablo/app/ml/ml_opt.py
import os
import psutil
import tensorflow as tf
import logging
from app.ml.ml_config import ML_CONFIG
from app.chatbot.migration_check import skip_on_migrate

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pablo/logs/ml_opt.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Variable global para controlar configuración inicial
TF_CONFIG_INITIALIZED = False

def check_system_load(threshold: float = 70) -> bool:
    """Verifica la carga de la CPU."""
    cpu_load = psutil.cpu_percent(interval=1)
    logger.info(f"Carga actual de la CPU: {cpu_load}%")
    return cpu_load < threshold

@skip_on_migrate
def configure_tensorflow() -> None:
    """Configura TensorFlow solo cuando no estamos migrando."""
    global TF_CONFIG_INITIALIZED
    if TF_CONFIG_INITIALIZED:
        logger.info("Configuración de TensorFlow ya aplicada, omitiendo.")
        return
    try:
        # Deshabilitar GPU explícitamente
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        logger.info("GPU deshabilitada para evitar conflictos.")

        # Configuración de memoria
        tf.config.set_soft_device_placement(True)
        logger.info("Soft device placement habilitado.")

        # Configuración de hilos
        intra_threads = ML_CONFIG.get('TENSORFLOW_THREADS', {}).get('INTRA_OP', 1)
        inter_threads = ML_CONFIG.get('TENSORFLOW_THREADS', {}).get('INTER_OP', 1)
        tf.config.threading.set_intra_op_parallelism_threads(intra_threads)
        tf.config.threading.set_inter_op_parallelism_threads(inter_threads)
        logger.info(f"Hilos configurados: intra={intra_threads}, inter={inter_threads}")

        # Habilitar XLA
        tf.config.optimizer.set_jit(True)
        logger.info("Compilación XLA habilitada.")

        TF_CONFIG_INITIALIZED = True
        logger.info("Configuración de TensorFlow aplicada correctamente.")
    except Exception as e:
        logger.error(f"Error configurando TensorFlow: {str(e)}")

def configure_tensorflow_based_on_load() -> None:
    """Configura TensorFlow según la carga del sistema."""
    global TF_CONFIG_INITIALIZED
    if not TF_CONFIG_INITIALIZED:
        configure_tensorflow()
        max_threads = 4  # Valor por defecto si os.cpu_count() falla

#    if cpu_load < 30:
#        # Baja carga: más hilos
#        tf.config.threading.set_intra_op_parallelism_threads(min(4, max_threads))
#        tf.config.threading.set_inter_op_parallelism_threads(2)
#        logger.info("Configuración para baja carga: 4 hilos intra, 2 inter")
#    elif cpu_load < 70:
#        # Carga media: menos hilos
#        tf.config.threading.set_intra_op_parallelism_threads(2)
#        tf.config.threading.set_inter_op_parallelism_threads(1)
#        logger.info("Configuración para carga media: 2 hilos intra, 1 inter")
#    else:
#        # Carga alta: mínimo hilos
#        tf.config.threading.set_intra_op_parallelism_threads(1)
#        tf.config.threading.set_inter_op_parallelism_threads(1)
#        logger.info("Configuración para carga alta: 1 hilo intra, 1 inter")
#    logger.info(f"Hilos configurados: intra={tf.config.threading.get_intra_op_parallelism_threads()}, inter={tf.config.threading.get_inter_op_parallelism_threads()}")