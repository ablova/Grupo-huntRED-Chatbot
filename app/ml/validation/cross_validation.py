from django.utils import timezone
from celery import shared_task
from typing import Dict, List, Optional
import numpy as np
from sklearn.model_selection import KFold
import logging
from datetime import datetime, time

logger = logging.getLogger(__name__)

class CrossValidationScheduler:
    """Clase para programar y ejecutar validación cruzada en horarios de baja carga"""
    
    LOW_TRAFFIC_HOURS = [
        (time(2, 0), time(4, 0)),    # 2 AM - 4 AM
        (time(14, 0), time(16, 0)),  # 2 PM - 4 PM (siesta)
    ]
    
    def __init__(self):
        self.n_splits = 5
        self.min_samples = 100
        self.max_samples = 10000
        self.random_state = 42

    def is_low_traffic_time(self) -> bool:
        """Verifica si es un horario de baja carga"""
        current_time = timezone.now().time()
        return any(start <= current_time <= end 
                  for start, end in self.LOW_TRAFFIC_HOURS)

    def prepare_validation_data(self, model_data: Dict) -> Dict:
        """Prepara los datos para validación cruzada"""
        features = np.array(model_data['features'])
        labels = np.array(model_data['labels'])
        
        if len(features) < self.min_samples:
            return {
                'status': 'error',
                'reason': f'Insuficientes muestras. Mínimo requerido: {self.min_samples}'
            }
            
        if len(features) > self.max_samples:
            # Muestreo aleatorio para mantener el rendimiento
            indices = np.random.choice(
                len(features), 
                self.max_samples, 
                replace=False
            )
            features = features[indices]
            labels = labels[indices]
            
        return {
            'status': 'success',
            'features': features,
            'labels': labels
        }

    def perform_cross_validation(self, model_data: Dict) -> Dict:
        """Realiza validación cruzada en los datos del modelo"""
        if not self.is_low_traffic_time():
            return {
                'status': 'skipped',
                'reason': 'No es horario de baja carga'
            }

        prepared_data = self.prepare_validation_data(model_data)
        if prepared_data['status'] == 'error':
            return prepared_data

        features = prepared_data['features']
        labels = prepared_data['labels']

        kf = KFold(
            n_splits=self.n_splits,
            shuffle=True,
            random_state=self.random_state
        )

        metrics = {
            'accuracy': [],
            'precision': [],
            'recall': [],
            'f1_score': []
        }

        for train_idx, val_idx in kf.split(features):
            X_train, X_val = features[train_idx], features[val_idx]
            y_train, y_val = labels[train_idx], labels[val_idx]

            # Aquí iría el entrenamiento y evaluación del modelo
            # Por ahora simulamos los resultados
            fold_metrics = {
                'accuracy': np.random.uniform(0.8, 0.95),
                'precision': np.random.uniform(0.8, 0.95),
                'recall': np.random.uniform(0.8, 0.95),
                'f1_score': np.random.uniform(0.8, 0.95)
            }

            for metric, value in fold_metrics.items():
                metrics[metric].append(value)

        # Calcular promedios y desviaciones estándar
        results = {
            'status': 'success',
            'n_splits': self.n_splits,
            'metrics': {
                metric: {
                    'mean': np.mean(values),
                    'std': np.std(values)
                }
                for metric, values in metrics.items()
            },
            'timestamp': timezone.now().isoformat()
        }

        return results

@shared_task
def scheduled_cross_validation(model_id: str):
    """Tarea Celery para ejecutar validación cruzada programada"""
    scheduler = CrossValidationScheduler()
    
    try:
        # Aquí iría la lógica para obtener los datos del modelo
        model_data = {
            'features': [],  # Simulado
            'labels': []     # Simulado
        }
        
        results = scheduler.perform_cross_validation(model_data)
        
        if results['status'] == 'success':
            logger.info(f"Validación cruzada completada para modelo {model_id}")
            # Aquí iría la lógica para guardar los resultados
        else:
            logger.warning(f"Validación cruzada omitida para modelo {model_id}: {results['reason']}")
            
        return results
        
    except Exception as e:
        logger.error(f"Error en validación cruzada para modelo {model_id}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        } 