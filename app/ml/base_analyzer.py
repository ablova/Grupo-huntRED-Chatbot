"""
🛡️ BaseAnalyzer Robusto - huntRED®

Clase base robusta para analizadores de ML con validación, manejo de errores,
métricas integradas y interfaces bien definidas.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import logging
import time
import traceback
from dataclasses import dataclass

# Excepciones locales
class AnalysisError(Exception):
    """Error durante análisis ML"""
    pass

class InvalidInputError(Exception):
    """Datos de entrada inválidos"""
    pass

class PerformanceError(Exception):
    """Error de performance (timeout, etc.)"""
    pass

logger = logging.getLogger(__name__)

@dataclass
class AnalysisMetrics:
    """Métricas de análisis"""
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    success: bool = False
    error_message: Optional[str] = None
    input_size: int = 0
    output_size: int = 0
    confidence: Optional[float] = None

class BaseAnalyzer(ABC):
    """
    🔬 Clase base abstracta robusta para analizadores de datos y evaluaciones.
    
    Proporciona:
    - Validación automática de entrada
    - Manejo robusto de errores
    - Métricas de rendimiento
    - Logging estructurado
    - Interfaz consistente
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logger.getChild(self.__class__.__name__)
        self.config = config or {}
        self.metrics_history: List[AnalysisMetrics] = []
        
        # Configuración por defecto
        self.timeout_seconds = self.config.get('timeout_seconds', 30)
        self.max_input_size = self.config.get('max_input_size', 1024 * 1024)  # 1MB
        self.enable_metrics = self.config.get('enable_metrics', True)
        self.enable_validation = self.config.get('enable_validation', True)
        
        self.logger.info(f"Inicializando {self.__class__.__name__}")
    
    @abstractmethod
    def _perform_analysis(self, validated_data: Any) -> Dict[str, Any]:
        """
        Método abstracto para realizar el análisis específico.
        
        Args:
            validated_data: Datos ya validados
            
        Returns:
            Diccionario con resultados del análisis
            
        Raises:
            AnalysisError: Si ocurre un error durante el análisis
        """
        pass
    
    @abstractmethod
    def _validate_input_schema(self, data: Any) -> Any:
        """
        Método abstracto para validar esquema de entrada específico.
        
        Args:
            data: Datos de entrada
            
        Returns:
            Datos validados
            
        Raises:
            InvalidInputError: Si los datos no son válidos
        """
        pass
    
    def analyze(self, data: Any) -> Dict[str, Any]:
        """
        Método principal de análisis con validación, métricas y manejo de errores.
        
        Args:
            data: Datos a analizar
            
        Returns:
            Diccionario con resultados del análisis
        """
        metrics = AnalysisMetrics(
            start_time=datetime.now(),
            input_size=self._calculate_input_size(data)
        )
        
        try:
            # Validación de entrada
            if self.enable_validation:
                validated_data = self._validate_and_sanitize_input(data)
            else:
                validated_data = data
            
            # Verificar timeout
            start_time = time.time()
            
            # Realizar análisis específico
            results = self._perform_analysis(validated_data)
            
            # Verificar que no excedió el timeout
            execution_time = time.time() - start_time
            if execution_time > self.timeout_seconds:
                raise PerformanceError(
                    f"Análisis excedió timeout de {self.timeout_seconds}s: {execution_time:.2f}s"
                )
            
            # Validar resultados
            validated_results = self._validate_output(results)
            
            # Actualizar métricas
            metrics.end_time = datetime.now()
            metrics.execution_time_ms = int(execution_time * 1000)
            metrics.success = True
            metrics.output_size = self._calculate_output_size(validated_results)
            metrics.confidence = validated_results.get('confidence')
            
            # Agregar metadatos
            validated_results.update({
                'analysis_metadata': {
                    'analyzer_type': self.__class__.__name__,
                    'execution_time_ms': metrics.execution_time_ms,
                    'timestamp': metrics.start_time.isoformat(),
                    'success': True,
                    'input_size': metrics.input_size,
                    'output_size': metrics.output_size
                }
            })
            
            self.logger.info(
                f"Análisis completado exitosamente en {metrics.execution_time_ms}ms",
                extra={
                    'execution_time_ms': metrics.execution_time_ms,
                    'input_size': metrics.input_size,
                    'output_size': metrics.output_size,
                    'confidence': metrics.confidence
                }
            )
            
            return validated_results
            
        except Exception as e:
            # Manejar errores
            metrics.end_time = datetime.now()
            metrics.success = False
            metrics.error_message = str(e)
            
            error_context = {
                'analyzer_type': self.__class__.__name__,
                'input_data_type': type(data).__name__,
                'error_type': type(e).__name__,
                'execution_time_ms': int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0
            }
            
            self.logger.error(
                f"Error en análisis: {str(e)}",
                extra=error_context,
                exc_info=True
            )
            
            # Retornar error estructurado
            return {
                'success': False,
                'error': {
                    'type': type(e).__name__,
                    'message': str(e),
                    'context': error_context
                },
                'analysis_metadata': {
                    'analyzer_type': self.__class__.__name__,
                    'timestamp': metrics.start_time.isoformat(),
                    'success': False
                }
            }
            
        finally:
            # Guardar métricas
            if self.enable_metrics:
                self.metrics_history.append(metrics)
                # Limitar historial a últimas 1000 entradas
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
    
    def _validate_and_sanitize_input(self, data: Any) -> Any:
        """Valida y sanitiza datos de entrada"""
        # Verificar tamaño de entrada
        input_size = self._calculate_input_size(data)
        if input_size > self.max_input_size:
            raise InvalidInputError(
                f"Tamaño de entrada excede el límite: {input_size} > {self.max_input_size} bytes"
            )
        
        # Verificar que no sea None
        if data is None:
            raise InvalidInputError("Los datos de entrada no pueden ser None")
        
        # Validación específica del analizador
        return self._validate_input_schema(data)
    
    def _validate_output(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Valida resultados de salida"""
        if not isinstance(results, dict):
            raise AnalysisError("Los resultados deben ser un diccionario")
        
        # Agregar campos requeridos si no existen
        if 'success' not in results:
            results['success'] = True
        
        if 'confidence' not in results:
            results['confidence'] = None
        
        return results
    
    def _calculate_input_size(self, data: Any) -> int:
        """Calcula tamaño aproximado de datos de entrada"""
        try:
            if isinstance(data, str):
                return len(data.encode('utf-8'))
            elif isinstance(data, (dict, list)):
                import sys
                return sys.getsizeof(str(data))
            elif hasattr(data, '__len__'):
                return len(data)
            else:
                import sys
                return sys.getsizeof(data)
        except:
            return 0
    
    def _calculate_output_size(self, data: Any) -> int:
        """Calcula tamaño aproximado de datos de salida"""
        return self._calculate_input_size(data)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento"""
        if not self.metrics_history:
            return {
                'total_analyses': 0,
                'success_rate': 0.0,
                'avg_execution_time_ms': 0,
                'avg_confidence': 0.0
            }
        
        successful = [m for m in self.metrics_history if m.success]
        
        avg_execution_time = sum(
            m.execution_time_ms for m in self.metrics_history 
            if m.execution_time_ms is not None
        ) / len(self.metrics_history)
        
        confidences = [
            m.confidence for m in successful 
            if m.confidence is not None
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            'total_analyses': len(self.metrics_history),
            'successful_analyses': len(successful),
            'success_rate': len(successful) / len(self.metrics_history),
            'avg_execution_time_ms': int(avg_execution_time),
            'avg_confidence': round(avg_confidence, 3),
            'last_analysis': self.metrics_history[-1].start_time.isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica salud del analizador"""
        try:
            # Test básico con datos dummy
            test_result = self.analyze("test")
            
            # Verificar métricas recientes
            recent_metrics = self.get_performance_metrics()
            
            is_healthy = (
                recent_metrics['success_rate'] > 0.8 and
                recent_metrics['avg_execution_time_ms'] < self.timeout_seconds * 1000
            )
            
            return {
                'healthy': is_healthy,
                'analyzer_type': self.__class__.__name__,
                'test_success': test_result.get('success', False),
                'metrics': recent_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'analyzer_type': self.__class__.__name__,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


class NotificationAnalyzer(BaseAnalyzer):
    """
    🔔 Implementación robusta de analizador de notificaciones.
    """
    
    def _validate_input_schema(self, data: Any) -> Any:
        """Valida esquema específico para notificaciones"""
        if isinstance(data, str):
            if len(data.strip()) == 0:
                raise InvalidInputError("El texto de notificación no puede estar vacío")
            return {"text": data.strip()}
        
        elif isinstance(data, dict):
            if 'text' not in data:
                raise InvalidInputError("El diccionario debe contener campo 'text'")
            if not data['text'] or not data['text'].strip():
                raise InvalidInputError("El campo 'text' no puede estar vacío")
            return data
        
        else:
            raise InvalidInputError(
                f"Tipo de datos no soportado: {type(data)}. Se esperaba str o dict"
            )
    
    def _perform_analysis(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza datos de notificaciones"""
        text = validated_data['text']
        
        # Análisis básico de notificación
        analysis = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'urgency_level': self._analyze_urgency(text),
            'sentiment': self._analyze_basic_sentiment(text),
            'priority_score': self._calculate_priority_score(text),
            'confidence': 0.85  # Confianza fija para este ejemplo
        }
        
        return analysis
    
    def _analyze_urgency(self, text: str) -> str:
        """Analiza nivel de urgencia del texto"""
        urgent_keywords = ['urgente', 'inmediato', 'ahora', 'emergency', 'urgent']
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in urgent_keywords):
            return 'high'
        elif '!' in text or text.isupper():
            return 'medium'
        else:
            return 'low'
    
    def _analyze_basic_sentiment(self, text: str) -> str:
        """Análisis básico de sentimiento"""
        positive_words = ['bien', 'bueno', 'excelente', 'perfecto', 'gracias']
        negative_words = ['mal', 'error', 'problema', 'falla', 'urgente']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_priority_score(self, text: str) -> float:
        """Calcula score de prioridad (0-1)"""
        base_score = 0.5
        
        # Ajustar por longitud
        if len(text) > 100:
            base_score += 0.1
        
        # Ajustar por palabras clave
        if any(word in text.lower() for word in ['error', 'falla', 'problema']):
            base_score += 0.3
        
        if any(word in text.lower() for word in ['urgente', 'inmediato']):
            base_score += 0.2
        
        return min(base_score, 1.0) 