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
        configure_tensorflow(intra_threads=1, inter_threads=1)  # Configuración mínima como respaldo        # /home/pablo/app/ml/ml_opt.py
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
        configure_tensorflow(intra_threads=1, inter_threads=1)  # Configuración mínima como respaldo        import asyncio
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from joblib import dump, load
from app.ml.ml_model import MatchmakingLearningSystem
from app.chatbot.metrics import chatbot_metrics

logger = logging.getLogger(__name__)

class MLOptimizer:
    @staticmethod
    def optimize_model_training(
        df: pd.DataFrame,
        test_size: float = 0.2,
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """Optimiza el entrenamiento del modelo usando batch processing."""
        try:
            # Preprocesamiento optimizado
            X = df.drop(columns=["success_label"])
            y = df["success_label"]
            
            # Split optimizado
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
            
            # Batch processing
            n_batches = len(X_train) // batch_size
            if len(X_train) % batch_size != 0:
                n_batches += 1
            
            # Entrenamiento por lotes
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
            
            # Métricas
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
