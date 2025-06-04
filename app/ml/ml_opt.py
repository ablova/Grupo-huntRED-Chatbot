# /home/pablo/app/ml/ml_opt.py
import os
import psutil
import tensorflow as tf
import logging
from app.ml.ml_config import ML_CONFIG
from app.com.chatbot.migration_check import skip_on_migrate

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
    try:
        cpu_load = psutil.cpu_percent(interval=1)
        logger.info(f"Carga actual de la CPU: {cpu_load}%")
        return cpu_load < threshold
    except Exception as e:
        logger.warning(f"Error verificando carga de CPU: {str(e)}")
        return True  # Asumir carga baja si falla

@skip_on_migrate
def configure_tensorflow(intra_threads: int = 1, inter_threads: int = 1) -> None:
    """Configura TensorFlow con hilos especificados."""
    global TF_CONFIG_INITIALIZED
    if TF_CONFIG_INITIALIZED or tf.executing_eagerly():
        logger.info("Configuración de TensorFlow ya aplicada o contexto inicializado, omitiendo.")
        return
    try:
        # Deshabilitar GPU completamente
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "false"
        logger.info("GPU deshabilitada para evitar conflictos.")

        # Configuración de memoria
        tf.config.set_soft_device_placement(True)
        tf.keras.backend.set_floatx('float32')
        logger.info("Soft device placement y float32 habilitados.")

        # Configuración de hilos
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

@skip_on_migrate
def configure_tensorflow_based_on_load() -> None:
    """Configura TensorFlow según la carga del sistema."""
    global TF_CONFIG_INITIALIZED
    if TF_CONFIG_INITIALIZED or tf.executing_eagerly():
        logger.info("Configuración de TensorFlow ya aplicada o contexto inicializado, omitiendo.")
        return
    try:
        cpu_load = psutil.cpu_percent(interval=1)
        max_threads = ML_CONFIG.get('TENSORFLOW_THREADS', {}).get('MAX_THREADS', 8)
        logger.info(f"Carga actual de la CPU: {cpu_load}%")

        if cpu_load < 30:
            # Baja carga: más hilos
            configure_tensorflow(intra_threads=min(4, max_threads), inter_threads=2)
            logger.info("Configuración para baja carga: 4 hilos intra, 2 inter")
        elif cpu_load < 70:
            # Carga media: menos hilos
            configure_tensorflow(intra_threads=2, inter_threads=1)
            logger.info("Configuración para carga media: 2 hilos intra, 1 inter")
        else:
            # Carga alta: mínimo hilos
            configure_tensorflow(intra_threads=1, inter_threads=1)
            logger.info("Configuración para carga alta: 1 hilo intra, 1 inter")
    except Exception as e:
        logger.error(f"Error configurando TensorFlow basado en carga: {str(e)}")
        configure_tensorflow(intra_threads=1, inter_threads=1)  # Configuración mínima como respaldo        