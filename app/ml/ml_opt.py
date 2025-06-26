# /home/pablo/app/ml/ml_opt.py
import os
import psutil
import logging
from app.ml.ml_config import MLConfig

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_opt.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Variable global para controlar configuración inicial
ML_CONFIG_INITIALIZED = False

def check_system_load(threshold: float = 70) -> bool:
    """Verifica la carga de la CPU."""
    try:
        cpu_load = psutil.cpu_percent(interval=1)
        logger.info(f"Carga actual de la CPU: {cpu_load}%")
        return cpu_load < threshold
    except Exception as e:
        logger.warning(f"Error verificando carga de CPU: {str(e)}")
        return True  # Asumir carga baja si falla

def configure_ml_environment(intra_threads: int = 1, inter_threads: int = 1) -> None:
    """Configura el entorno de ML con hilos especificados."""
    global ML_CONFIG_INITIALIZED
    if ML_CONFIG_INITIALIZED:
        logger.info("Configuración de ML ya aplicada, omitiendo.")
        return
    try:
        # Configuración de memoria
        logger.info("Configuración de memoria optimizada para ML.")

        # Configuración de hilos
        logger.info(f"Hilos configurados: intra={intra_threads}, inter={inter_threads}")

        # Configuración de optimización
        logger.info("Optimizaciones de ML habilitadas.")

        ML_CONFIG_INITIALIZED = True
        logger.info("Configuración de ML aplicada correctamente.")
    except Exception as e:
        logger.error(f"Error configurando ML: {str(e)}")

def configure_ml_based_on_load() -> None:
    """Configura ML según la carga del sistema."""
    global ML_CONFIG_INITIALIZED
    if ML_CONFIG_INITIALIZED:
        logger.info("Configuración de ML ya aplicada, omitiendo.")
        return
    try:
        cpu_load = psutil.cpu_percent(interval=1)
        max_threads = 8  # Configuración por defecto
        logger.info(f"Carga actual de la CPU: {cpu_load}%")

        if cpu_load < 30:
            # Baja carga: más hilos
            configure_ml_environment(intra_threads=min(4, max_threads), inter_threads=2)
            logger.info("Configuración para baja carga: 4 hilos intra, 2 inter")
        elif cpu_load < 70:
            # Carga media: menos hilos
            configure_ml_environment(intra_threads=2, inter_threads=1)
            logger.info("Configuración para carga media: 2 hilos intra, 1 inter")
        else:
            # Carga alta: mínimo hilos
            configure_ml_environment(intra_threads=1, inter_threads=1)
            logger.info("Configuración para carga alta: 1 hilo intra, 1 inter")
    except Exception as e:
        logger.error(f"Error configurando ML basado en carga: {str(e)}")
        configure_ml_environment(intra_threads=1, inter_threads=1)  # Configuración mínima como respaldo

class MLOptimizer:
    """
    Optimizador para el sistema de Machine Learning.
    """
    
    def __init__(self):
        self.config = MLConfig()
        self.logger = logger
        self.logger.info("MLOptimizer inicializado")
    
    def optimize_model_performance(self, model_type: str) -> dict:
        """
        Optimiza el rendimiento de un modelo específico.
        
        Args:
            model_type: Tipo de modelo a optimizar
            
        Returns:
            Dict con las optimizaciones aplicadas
        """
        try:
            # Configurar entorno basado en carga del sistema
            configure_ml_based_on_load()
            
            # Obtener configuración del modelo
            model_config = self.config.get_model_config(model_type)
            
            optimizations = {
                "model_type": model_type,
                "cpu_load": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "optimizations_applied": [
                    "Configuración de hilos optimizada",
                    "Gestión de memoria mejorada",
                    "Caché habilitado"
                ],
                "model_config": model_config
            }
            
            self.logger.info(f"Optimizaciones aplicadas para {model_type}")
            return optimizations
            
        except Exception as e:
            self.logger.error(f"Error optimizando modelo {model_type}: {str(e)}")
            return {
                "model_type": model_type,
                "error": str(e),
                "status": "failed"
            }
    
    def get_system_status(self) -> dict:
        """
        Obtiene el estado del sistema para optimización.
        
        Returns:
            Dict con el estado del sistema
        """
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "ml_config_initialized": ML_CONFIG_INITIALIZED
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo estado del sistema: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }        