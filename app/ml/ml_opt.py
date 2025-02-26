# /home/pablo/app/ml/ml_opt.py

import psutil
import tensorflow as tf
import logging

logger = logging.getLogger("app.ml.ml_opt")

def check_system_load(threshold=70):
    """
    Verifica la carga de la CPU. Retorna True si la carga es menor al umbral.
    """
    cpu_load = psutil.cpu_percent(interval=1)
    logger.info(f"Carga actual de la CPU: {cpu_load}%")
    return cpu_load < threshold

def configure_tensorflow_based_on_load():
    """
    Configura los hilos de TensorFlow según la carga del sistema.
    """
    cpu_load = psutil.cpu_percent(interval=1)
    if cpu_load < 30:
        # Baja carga: más hilos
        tf.config.threading.set_intra_op_parallelism_threads(4)
        tf.config.threading.set_inter_op_parallelism_threads(2)
        logger.info("Configuración para baja carga: 4 hilos intra, 2 inter")
    elif cpu_load < 70:
        # Carga media: menos hilos
        tf.config.threading.set_intra_op_parallelism_threads(2)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        logger.info("Configuración para carga media: 2 hilos intra, 1 inter")
    else:
        # Carga alta: mínimo hilos
        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        logger.info("Configuración para carga alta: 1 hilo intra, 1 inter")