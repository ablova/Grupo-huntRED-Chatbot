"""
Optimizador de rendimiento para el sistema ATS AI.
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
import tensorflow as tf
import psutil
import os
from functools import lru_cache
from app.ml.core.utils import LRUCache
from app.ats.chatbot.migration_check import skip_on_migrate

logger = logging.getLogger(__name__)

# Variable global para controlar configuración inicial
TF_CONFIG_INITIALIZED = False

class TensorFlowConfigurator:
    """Configurador de TensorFlow con optimizaciones de rendimiento."""
    
    @staticmethod
    def check_system_load(threshold: float = 70) -> bool:
        """Verifica la carga de la CPU."""
        try:
            cpu_load = psutil.cpu_percent(interval=1)
            logger.info(f"Carga actual de la CPU: {cpu_load}%")
            return cpu_load < threshold
        except Exception as e:
            logger.warning(f"Error verificando carga de CPU: {str(e)}")
            return True  # Asumir carga baja si falla

    @staticmethod
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

    @staticmethod
    @skip_on_migrate
    def configure_tensorflow_based_on_load() -> None:
        """Configura TensorFlow según la carga del sistema."""
        global TF_CONFIG_INITIALIZED
        if TF_CONFIG_INITIALIZED or tf.executing_eagerly():
            logger.info("Configuración de TensorFlow ya aplicada o contexto inicializado, omitiendo.")
            return
        try:
            cpu_load = psutil.cpu_percent(interval=1)
            max_threads = 8  # Valor por defecto
            logger.info(f"Carga actual de la CPU: {cpu_load}%")

            if cpu_load < 30:
                # Baja carga: más hilos
                TensorFlowConfigurator.configure_tensorflow(intra_threads=min(4, max_threads), inter_threads=2)
                logger.info("Configuración para baja carga: 4 hilos intra, 2 inter")
            elif cpu_load < 70:
                # Carga media: menos hilos
                TensorFlowConfigurator.configure_tensorflow(intra_threads=2, inter_threads=1)
                logger.info("Configuración para carga media: 2 hilos intra, 1 inter")
            else:
                # Carga alta: mínimo hilos
                TensorFlowConfigurator.configure_tensorflow(intra_threads=1, inter_threads=1)
                logger.info("Configuración para carga alta: 1 hilo intra, 1 inter")
        except Exception as e:
            logger.error(f"Error configurando TensorFlow basado en carga: {str(e)}")
            TensorFlowConfigurator.configure_tensorflow(intra_threads=1, inter_threads=1)  # Configuración mínima como respaldo

class BatchProcessor:
    def __init__(self, batch_size: int = 1000):
        """Inicializa el procesador por lotes."""
        self.batch_size = batch_size
        self.cache = LRUCache(max_size=1000)

    def process(self, data: List[Dict]) -> List[Dict]:
        """
        Procesa datos por lotes optimizados.
        
        Args:
            data: Lista de datos a procesar
            
        Returns:
            List[Dict]: Datos procesados
        """
        try:
            results = []
            
            # Procesar por lotes
            for i in range(0, len(data), self.batch_size):
                batch = data[i:i + self.batch_size]
                processed_batch = self._process_batch(batch)
                results.extend(processed_batch)
                
            return results
            
        except Exception as e:
            logger.error(f"Error procesando datos por lotes: {e}")
            return [{} for _ in data]

    def _process_batch(self, batch: List[Dict]) -> List[Dict]:
        """
        Procesa un lote de datos con optimizaciones de rendimiento.
        
        Args:
            batch: Lote de datos a procesar
            
        Returns:
            List[Dict]: Lote procesado
        """
        try:
            processed_batch = []
            
            # Procesar cada elemento del lote
            for item in batch:
                # Verificar cache
                cache_key = f"processed_{item.get('id', '')}"
                cached_result = self.cache.get(cache_key)
                
                if cached_result is not None:
                    processed_batch.append(cached_result)
                    continue
                
                # Procesar item
                processed_item = self._process_item(item)
                
                # Almacenar en cache
                self.cache.set(cache_key, processed_item)
                
                processed_batch.append(processed_item)
                
            return processed_batch
            
        except Exception as e:
            logger.error(f"Error procesando lote: {e}")
            return [{} for _ in batch]

    def _process_item(self, item: Dict) -> Dict:
        """
        Procesa un item individual con optimizaciones.
        
        Args:
            item: Item a procesar
            
        Returns:
            Dict: Item procesado
        """
        try:
            # Aplicar optimizaciones específicas
            processed_item = item.copy()
            
            # Optimizar características numéricas
            for key, value in item.items():
                if isinstance(value, (int, float)):
                    processed_item[key] = self._normalize_value(value)
            
            return processed_item
            
        except Exception as e:
            logger.error(f"Error procesando item: {e}")
            return item

    def _normalize_value(self, value: float) -> float:
        """
        Normaliza un valor numérico.
        
        Args:
            value: Valor a normalizar
            
        Returns:
            float: Valor normalizado
        """
        return max(0, min(1, value))

class GPUManager:
    def __init__(self):
        """Inicializa el administrador de GPU."""
        self._check_gpu_availability()
        self._configure_gpu()

    def _check_gpu_availability(self):
        """Verifica la disponibilidad de GPU."""
        try:
            self.has_gpu = tf.config.list_physical_devices('GPU')
            logger.info(f"GPU disponible: {self.has_gpu}")
            
        except Exception as e:
            logger.error(f"Error verificando GPU: {e}")
            self.has_gpu = False

    def _configure_gpu(self):
        """Configura el uso de GPU."""
        try:
            if self.has_gpu:
                tf.config.experimental.set_memory_growth(
                    tf.config.list_physical_devices('GPU')[0],
                    True
                )
                logger.info("Configuración de GPU completada")
            
        except Exception as e:
            logger.error(f"Error configurando GPU: {e}")

class QuantizationOptimizer:
    def __init__(self):
        """Inicializa el optimizador de cuantización."""
        self._initialize_quantization()
        self.quantized_models = {}

    def _initialize_quantization(self):
        """Inicializa la cuantización."""
        try:
            self.converter = tf.lite.TFLiteConverter.from_saved_model
            self.quantizer = tf.lite.TFLiteConverter.experimental_new_converter
            
        except Exception as e:
            logger.error(f"Error inicializando cuantización: {e}")
            raise

    def quantize_model(self, model_path: str, output_path: str) -> None:
        """
        Cuantiza un modelo de TensorFlow.
        
        Args:
            model_path: Ruta del modelo original
            output_path: Ruta para el modelo cuantizado
        """
        try:
            # Convertir a TFLite
            converter = self.converter(model_path)
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            
            # Establecer representación de entrada
            def representative_dataset():
                for _ in range(100):
                    yield [np.random.rand(1, 512).astype(np.float32)]
            
            converter.representative_dataset = representative_dataset
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
            converter.inference_input_type = tf.int8
            converter.inference_output_type = tf.int8
            
            # Convertir y guardar
            tflite_model = converter.convert()
            with open(output_path, 'wb') as f:
                f.write(tflite_model)
                
            # Almacenar en cache
            self.quantized_models[model_path] = output_path
            
        except Exception as e:
            logger.error(f"Error cuantizando modelo: {e}")
            raise

    def load_quantized_model(self, model_path: str) -> tf.lite.Interpreter:
        """
        Carga un modelo cuantizado.
        
        Args:
            model_path: Ruta del modelo original
            
        Returns:
            tf.lite.Interpreter: Interprete del modelo cuantizado
        """
        try:
            # Verificar si ya está cuantizado
            if model_path in self.quantized_models:
                quantized_path = self.quantized_models[model_path]
            else:
                # Crear ruta de salida
                quantized_path = model_path.replace('.h5', '_quant.tflite')
                self.quantize_model(model_path, quantized_path)
            
            # Cargar modelo cuantizado
            interpreter = tf.lite.Interpreter(model_path=quantized_path)
            interpreter.allocate_tensors()
            
            return interpreter
            
        except Exception as e:
            logger.error(f"Error cargando modelo cuantizado: {e}")
            raise

    def optimize_model(self, model_path: str) -> bytes:
        """
        Optimiza un modelo usando cuantización.
        
        Args:
            model_path: Ruta al modelo a optimizar
            
        Returns:
            bytes: Modelo optimizado
        """
        try:
            converter = self.converter(model_path)
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.float16]
            
            tflite_model = converter.convert()
            logger.info("Modelo optimizado con éxito")
            
            return tflite_model
            
        except Exception as e:
            logger.error(f"Error optimizando modelo: {e}")
            return b''
