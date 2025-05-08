    import os
import psutil
import tensorflow as tf
import logging
from typing import Dict, Optional, Any
from app.ml.ml_config import ML_CONFIG
from app.chatbot.migration_check import skip_on_migrate
from app.ml.core.optimizers import BatchProcessor, GPUManager, QuantizationOptimizer
from app.settings import settings
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(settings.LOG_DIR, 'ml_optimizer.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Variable global para controlar configuración inicial
TF_CONFIG_INITIALIZED = False

class TensorFlowConfig:
    """
    Gestiona la configuración de TensorFlow.
    
    Args:
        config: Configuración del sistema
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialized = False
        self.gpu_manager = GPUManager()
        self.quantization_optimizer = QuantizationOptimizer()
        
    @property
    def initialized(self) -> bool:
        return self._initialized
        
    def initialize(self) -> None:
        """Inicializa la configuración de TensorFlow."""
        try:
            self._configure_gpu()
            self._configure_memory()
            self._configure_threads()
            self._configure_optimizer()
            
            self._initialized = True
            logger.info("Configuración de TensorFlow inicializada correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando TensorFlow: {str(e)}")
            raise
            
    def _configure_gpu(self) -> None:
        """Configura la GPU."""
        if not self.config['SYSTEM']['GPU_ENABLED']:
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
            os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "false"
            logger.info("GPU deshabilitada")
            
    def _configure_memory(self) -> None:
        """Configura la memoria."""
        tf.config.set_soft_device_placement(True)
        tf.keras.backend.set_floatx('float32')
        logger.info("Configuración de memoria aplicada")
        
    def _configure_threads(self) -> None:
        """Configura los hilos de ejecución."""
        tf.config.threading.set_intra_op_parallelism_threads(
            self.config['PERFORMANCE']['OPTIMIZATION']['INTRA_THREADS']
        )
        tf.config.threading.set_inter_op_parallelism_threads(
            self.config['PERFORMANCE']['OPTIMIZATION']['INTER_THREADS']
        )
        logger.info("Configuración de hilos aplicada")
        
    def _configure_optimizer(self) -> None:
        """Configura el optimizador de TensorFlow."""
        tf.config.optimizer.set_jit(True)
        logger.info("Optimizador XLA habilitado")

class SystemLoadMonitor:
    """
    Monitorea la carga del sistema.
    
    Args:
        config: Configuración del sistema
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._last_load = 0.0
        self._check_interval = config['SYSTEM']['MONITORING_INTERVAL']
        
    def check_load(self) -> float:
        """Verifica la carga del sistema."""
        try:
            cpu_load = psutil.cpu_percent(interval=self._check_interval)
            logger.info(f"Carga actual de la CPU: {cpu_load}%")
            self._last_load = cpu_load
            return cpu_load
            
        except Exception as e:
            logger.warning(f"Error verificando carga del sistema: {str(e)}")
            return self._last_load

class MLOptimizer:
    """
    Optimizador principal del sistema ML.
    
    Args:
        config: Configuración del sistema
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tensorflow_config = TensorFlowConfig(config)
        self.load_monitor = SystemLoadMonitor(config)
        self.batch_processor = BatchProcessor(
            batch_size=config['PERFORMANCE']['OPTIMIZATION']['BATCH_SIZE']
        )
        self._initialized = False
        
    @property
    def initialized(self) -> bool:
        return self._initialized
        
    def initialize(self) -> None:
        """Inicializa el optimizador."""
        try:
            self.tensorflow_config.initialize()
            self._initialized = True
            logger.info("Optimizador inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando optimizador: {str(e)}")
            raise
            
    def optimize_tensorflow(self) -> None:
        """Optimiza la configuración de TensorFlow."""
        try:
            cpu_load = self.load_monitor.check_load()
            
            if cpu_load < 30:
                # Baja carga: más hilos
                self.tensorflow_config._configure_threads(4, 2)
            elif cpu_load < 70:
                # Carga media: menos hilos
                self.tensorflow_config._configure_threads(2, 1)
            else:
                # Carga alta: mínimo hilos
                self.tensorflow_config._configure_threads(1, 1)
                
            logger.info(f"Configuración optimizada para carga de {cpu_load}%")
            
        except Exception as e:
            logger.error(f"Error optimizando TensorFlow: {str(e)}")
            self.tensorflow_config._configure_threads(1, 1)  # Configuración mínima como respaldo
            
    def optimize_data(self, data: List[Dict]) -> List[Dict]:
        """Optimiza el procesamiento de datos usando lotes."""
        return self.batch_processor.process(data)

    def optimize_model(self, model_path: str) -> bytes:
        """Optimiza un modelo usando cuantización."""
        return self.tensorflow_config.quantization_optimizer.optimize_model(model_path)

    def optimize_training(self, X_train: pd.DataFrame, y_train: pd.DataFrame, X_test: pd.DataFrame, y_test: pd.DataFrame) -> dict:
        """Optimiza el entrenamiento de un modelo."""
        try:
            batch_size = self.config['PERFORMANCE']['OPTIMIZATION']['BATCH_SIZE']
            n_batches = len(X_train) // batch_size
            if len(X_train) % batch_size != 0:
                n_batches += 1
            
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                n_jobs=-1,
                random_state=42
            )
            
            for i in range(n_batches):
                start_idx = i * batch_size
                end_idx = min((i + 1) * batch_size, len(X_train))
                
                X_batch = X_train.iloc[start_idx:end_idx]
                y_batch = y_train.iloc[start_idx:end_idx]
                
                # Entrenamiento incremental
                if i == 0:
                    model.fit(X_batch, y_batch)
                else:
                    model.partial_fit(X_batch, y_batch)
            
            # Evaluación
            y_pred = model.predict(X_test)
            report = classification_report(y_test, y_pred, output_dict=True)
            
            return {
                'model': model,
                'report': report,
                'accuracy': report['accuracy']
            }
            
        except Exception as e:
            logger.error(f"Error optimizando entrenamiento: {str(e)}")
            return {'error': str(e)}

# Singleton instance
ml_optimizer = MLOptimizer(ML_CONFIG)            # Métricas
            chatbot_metrics.track_message(
                'ml_training',
                'completed',
                success=True,
                response_time=report['macro avg']['f1-score']
            )
            
            return {
                'success': True,
                'model': model,
                'metrics': report,
                'batch_stats': {
                    'n_batches': n_batches,
                    'batch_size': batch_size,
                    'total_samples': len(X_train)
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizando entrenamiento: {str(e)}")
            chatbot_metrics.track_message(
                'ml_training',
                'completed',
                success=False,
                response_time=0
            )
            return {'success': False, 'error': str(e)}

    @staticmethod
    def optimize_predictions(
        model: RandomForestClassifier,
        X: pd.DataFrame,
        batch_size: int = 1000
    ) -> np.ndarray:
        """Optimiza las predicciones usando batch processing."""
        try:
            n_batches = len(X) // batch_size
            if len(X) % batch_size != 0:
                n_batches += 1
            
            predictions = []
            
            for i in range(n_batches):
                start_idx = i * batch_size
                end_idx = min((i + 1) * batch_size, len(X))
                
                X_batch = X.iloc[start_idx:end_idx]
                batch_pred = model.predict_proba(X_batch)
                predictions.append(batch_pred)
            
            return np.concatenate(predictions, axis=0)
            
        except Exception as e:
            logger.error(f"Error optimizando predicciones: {str(e)}")
            return np.zeros((len(X), 2))

    @staticmethod
    async def async_predict(
        model: RandomForestClassifier,
        X: pd.DataFrame,
        batch_size: int = 1000
    ) -> np.ndarray:
        """Realiza predicciones asíncronas con optimización."""
        try:
            # Dividir en lotes
            n_batches = len(X) // batch_size
            if len(X) % batch_size != 0:
                n_batches += 1
            
            # Crear tareas asíncronas
            tasks = []
            for i in range(n_batches):
                start_idx = i * batch_size
                end_idx = min((i + 1) * batch_size, len(X))
                
                X_batch = X.iloc[start_idx:end_idx]
                tasks.append(
                    asyncio.create_task(
                        MLOptimizer._async_predict_batch(model, X_batch)
                    )
                )
            
            # Esperar resultados
            results = await asyncio.gather(*tasks)
            
            # Combinar resultados
            return np.concatenate(results, axis=0)
            
        except Exception as e:
            logger.error(f"Error en predicción asíncrona: {str(e)}")
            return np.zeros((len(X), 2))

    @staticmethod
    async def _async_predict_batch(
        model: RandomForestClassifier,
        X_batch: pd.DataFrame
    ) -> np.ndarray:
        """Tarea asíncrona para predecir un lote."""
        try:
            return model.predict_proba(X_batch)
        except Exception as e:
            logger.error(f"Error en predicción de lote: {str(e)}")
            return np.zeros((len(X_batch), 2))

# Singleton instance
ml_optimizer = MLOptimizer()
