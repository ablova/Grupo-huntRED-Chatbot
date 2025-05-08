import logging
from typing import Dict, Any
from datetime import datetime
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
from app.models import Person, Vacante, Application

logger = logging.getLogger(__name__)

class ATSMetrics:
    """
    Sistema de métricas para el ATS AI.
    
    Este sistema proporciona métricas detalladas para evaluar el rendimiento
    del sistema de emparejamiento y análisis predictivo.
    """
    
    def __init__(self):
        self.metrics = {}
        self._initialize_metrics()

    def _initialize_metrics(self) -> None:
        """
        Inicializa las métricas disponibles.
        """
        self.metrics = {
            'model_performance': {
                'accuracy': None,
                'precision': None,
                'recall': None,
                'f1_score': None,
                'roc_auc': None,
                'confusion_matrix': None
            },
            'business_metrics': {
                'time_to_hire': None,
                'match_rate': None,
                'transition_success_rate': None,
                'application_conversion_rate': None
            },
            'system_metrics': {
                'model_load_time': None,
                'feature_extraction_time': None,
                'prediction_time': None,
                'cache_hit_rate': None
            }
        }

    def calculate_model_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
        """
        Calcula métricas de rendimiento del modelo.
        
        Args:
            y_true: Valores reales
            y_pred: Predicciones del modelo
            
        Returns:
            Dict[str, Any]: Métricas de rendimiento
        """
        try:
            metrics = {
                'accuracy': accuracy_score(y_true, y_pred),
                'precision': precision_score(y_true, y_pred),
                'recall': recall_score(y_true, y_pred),
                'f1_score': f1_score(y_true, y_pred),
                'roc_auc': roc_auc_score(y_true, y_pred),
                'confusion_matrix': confusion_matrix(y_true, y_pred).tolist(),
                'classification_report': classification_report(y_true, y_pred, output_dict=True)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculando métricas del modelo: {e}")
            return {}

    def calculate_business_metrics(self, applications: List[Application]) -> Dict[str, Any]:
        """
        Calcula métricas de negocio.
        
        Args:
            applications: Lista de aplicaciones
            
        Returns:
            Dict[str, Any]: Métricas de negocio
        """
        try:
            metrics = {
                'time_to_hire': self._calculate_time_to_hire(applications),
                'match_rate': self._calculate_match_rate(applications),
                'transition_success_rate': self._calculate_transition_success_rate(applications),
                'application_conversion_rate': self._calculate_conversion_rate(applications)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculando métricas de negocio: {e}")
            return {}

    def _calculate_time_to_hire(self, applications: List[Application]) -> float:
        """
        Calcula el tiempo promedio de contratación.
        
        Args:
            applications: Lista de aplicaciones
            
        Returns:
            float: Tiempo promedio de contratación en días
        """
        try:
            successful_apps = [app for app in applications if app.status == 'contratado']
            if not successful_apps:
                return 0.0
                
            times = []
            for app in successful_apps:
                if app.date_hired and app.date_applied:
                    delta = app.date_hired - app.date_applied
                    times.append(delta.days)
                    
            return np.mean(times) if times else 0.0
            
        except Exception as e:
            logger.error(f"Error calculando tiempo de contratación: {e}")
            return 0.0

    def _calculate_match_rate(self, applications: List[Application]) -> float:
        """
        Calcula la tasa de coincidencia exitosa.
        
        Args:
            applications: Lista de aplicaciones
            
        Returns:
            float: Tasa de coincidencia (0-1)
        """
        try:
            successful = sum(1 for app in applications if app.status == 'contratado')
            total = len(applications)
            return successful / total if total > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculando tasa de coincidencia: {e}")
            return 0.0

    def _calculate_transition_success_rate(self, applications: List[Application]) -> float:
        """
        Calcula la tasa de éxito en transiciones.
        
        Args:
            applications: Lista de aplicaciones
            
        Returns:
            float: Tasa de éxito en transiciones (0-1)
        """
        try:
            transitions = [app for app in applications if app.transition_from]
            if not transitions:
                return 0.0
                
            successful = sum(1 for app in transitions if app.status == 'contratado')
            total = len(transitions)
            return successful / total if total > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculando tasa de transición: {e}")
            return 0.0

    def _calculate_conversion_rate(self, applications: List[Application]) -> float:
        """
        Calcula la tasa de conversión de aplicaciones a contrataciones.
        
        Args:
            applications: Lista de aplicaciones
            
        Returns:
            float: Tasa de conversión (0-1)
        """
        try:
            successful = sum(1 for app in applications if app.status == 'contratado')
            total = len(applications)
            return successful / total if total > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculando tasa de conversión: {e}")
            return 0.0

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """
        Genera datos para el dashboard de monitoreo.
        
        Returns:
            Dict[str, Any]: Datos para el dashboard
        """
        try:
            # Obtener métricas del sistema
            system_metrics = self.metrics['system_metrics'].copy()
            
            # Obtener métricas de negocio
            applications = Application.objects.all()
            business_metrics = self.calculate_business_metrics(applications)
            
            # Formatear datos para el dashboard
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': system_metrics,
                'business_metrics': business_metrics,
                'model_performance': self.metrics['model_performance'].copy()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generando datos del dashboard: {e}")
            return {}
