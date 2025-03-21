# /home/pablo/app/ml/ml_opt.py

import os
import psutil
import tensorflow as tf
import logging

logger = logging.getLogger(__name__)

def check_system_load(threshold=70):
    """
    Verifica la carga de la CPU. Retorna True si la carga es menor al umbral.
    """
    cpu_load = psutil.cpu_percent(interval=1)
    logger.info(f"Carga actual de la CPU: {cpu_load}%")
    return cpu_load < threshold

def configure_tensorflow_based_on_load():
    """
    Configura TensorFlow según la carga del sistema, incluyendo hilos y uso de memoria.
    """
    # Configuración de memoria para GPUs (si están disponibles)
    tf.config.set_soft_device_placement(True)
    for gpu in tf.config.experimental.list_physical_devices('GPU'):
        tf.config.experimental.set_memory_growth(gpu, True)
    logger.info("Configuración de memoria de TensorFlow aplicada: soft device placement y memory growth habilitados")

    # Configuración de hilos según la carga de la CPU
    cpu_load = psutil.cpu_percent(interval=1)
    try:
        max_threads = os.cpu_count() or 4  # Default a 4 si no se detecta
    except AttributeError as e:
        logger.error(f"Error al obtener el número de CPUs: {e}. Usando valor por defecto.")
        max_threads = 4  # Valor por defecto si os.cpu_count() falla

    if cpu_load < 30:
        # Baja carga: más hilos
        tf.config.threading.set_intra_op_parallelism_threads(min(4, max_threads))
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
    logger.info(f"Hilos configurados: intra={tf.config.threading.get_intra_op_parallelism_threads()}, inter={tf.config.threading.get_inter_op_parallelism_threads()}")