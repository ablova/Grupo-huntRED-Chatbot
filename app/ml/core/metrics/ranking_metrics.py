"""
Sistema de métricas para rankings educativos.
"""
from typing import Dict, List, Optional, Any, Union
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt

class RankingMetrics:
    """Sistema de métricas para rankings educativos."""
    
    def __init__(self):
        """Inicializa el sistema de métricas."""
        self.metrics_history: List[Dict[str, Any]] = []
        
    def calculate_ranking_metrics(self,
                                predictions: List[float],
                                actuals: List[float]) -> Dict[str, float]:
        """
        Calcula métricas para rankings.
        
        Args:
            predictions: Lista de predicciones
            actuals: Lista de valores reales
            
        Returns:
            Diccionario con métricas
        """
        metrics = {
            'mse': mean_squared_error(actuals, predictions),
            'rmse': np.sqrt(mean_squared_error(actuals, predictions)),
            'r2': r2_score(actuals, predictions),
            'mae': np.mean(np.abs(np.array(predictions) - np.array(actuals))),
            'mape': np.mean(np.abs((np.array(actuals) - np.array(predictions)) / np.array(actuals))) * 100
        }
        
        # Agregar timestamp
        metrics['timestamp'] = datetime.now().isoformat()
        
        # Guardar en historial
        self.metrics_history.append(metrics)
        
        return metrics
        
    def calculate_program_metrics(self,
                                program_data: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Calcula métricas para programas específicos.
        
        Args:
            program_data: Diccionario con datos de programas
            
        Returns:
            Diccionario con métricas
        """
        metrics = {
            'total_programs': len(program_data),
            'avg_ranking': np.mean([d['rank'] for d in program_data.values()]),
            'avg_score': np.mean([d['score'] for d in program_data.values()]),
            'std_ranking': np.std([d['rank'] for d in program_data.values()]),
            'std_score': np.std([d['score'] for d in program_data.values()])
        }
        
        # Calcular percentiles
        rankings = [d['rank'] for d in program_data.values()]
        scores = [d['score'] for d in program_data.values()]
        
        metrics.update({
            'p25_ranking': np.percentile(rankings, 25),
            'p50_ranking': np.percentile(rankings, 50),
            'p75_ranking': np.percentile(rankings, 75),
            'p25_score': np.percentile(scores, 25),
            'p50_score': np.percentile(scores, 50),
            'p75_score': np.percentile(scores, 75)
        })
        
        # Agregar timestamp
        metrics['timestamp'] = datetime.now().isoformat()
        
        # Guardar en historial
        self.metrics_history.append(metrics)
        
        return metrics
        
    def calculate_university_metrics(self,
                                   university_data: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        Calcula métricas para universidades.
        
        Args:
            university_data: Diccionario con datos de universidades
            
        Returns:
            Diccionario con métricas
        """
        metrics = {
            'total_universities': len(university_data),
            'avg_ranking': np.mean([d['rank'] for d in university_data.values()]),
            'avg_score': np.mean([d['score'] for d in university_data.values()]),
            'std_ranking': np.std([d['rank'] for d in university_data.values()]),
            'std_score': np.std([d['score'] for d in university_data.values()])
        }
        
        # Calcular métricas por país
        country_metrics = {}
        for data in university_data.values():
            country = data.get('country')
            if country:
                if country not in country_metrics:
                    country_metrics[country] = {
                        'count': 0,
                        'rankings': [],
                        'scores': []
                    }
                country_metrics[country]['count'] += 1
                country_metrics[country]['rankings'].append(data['rank'])
                country_metrics[country]['scores'].append(data['score'])
                
        # Calcular métricas agregadas por país
        for country, data in country_metrics.items():
            metrics[f'{country}_count'] = data['count']
            metrics[f'{country}_avg_ranking'] = np.mean(data['rankings'])
            metrics[f'{country}_avg_score'] = np.mean(data['scores'])
            
        # Agregar timestamp
        metrics['timestamp'] = datetime.now().isoformat()
        
        # Guardar en historial
        self.metrics_history.append(metrics)
        
        return metrics
        
    def calculate_trend_metrics(self,
                              historical_data: pd.DataFrame,
                              window: int = 30) -> Dict[str, float]:
        """
        Calcula métricas de tendencia.
        
        Args:
            historical_data: DataFrame con datos históricos
            window: Ventana de tiempo en días
            
        Returns:
            Diccionario con métricas
        """
        # Convertir timestamp a datetime
        historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'])
        
        # Ordenar por timestamp
        historical_data = historical_data.sort_values('timestamp')
        
        # Calcular métricas de tendencia
        metrics = {
            'trend_direction': 0,
            'trend_strength': 0,
            'volatility': 0,
            'seasonality': 0
        }
        
        if len(historical_data) < 2:
            return metrics
            
        # Calcular dirección de tendencia
        first_value = historical_data['score'].iloc[0]
        last_value = historical_data['score'].iloc[-1]
        metrics['trend_direction'] = 1 if last_value > first_value else -1
        
        # Calcular fuerza de tendencia
        metrics['trend_strength'] = abs(last_value - first_value) / first_value
        
        # Calcular volatilidad
        metrics['volatility'] = historical_data['score'].std()
        
        # Calcular estacionalidad
        if len(historical_data) >= window:
            rolling_mean = historical_data['score'].rolling(window=window).mean()
            metrics['seasonality'] = np.mean(np.abs(historical_data['score'] - rolling_mean))
            
        # Agregar timestamp
        metrics['timestamp'] = datetime.now().isoformat()
        
        # Guardar en historial
        self.metrics_history.append(metrics)
        
        return metrics
        
    def get_metrics_history(self,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Obtiene historial de métricas.
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            
        Returns:
            Lista de métricas
        """
        if not start_date and not end_date:
            return self.metrics_history
            
        filtered_metrics = []
        for metric in self.metrics_history:
            timestamp = datetime.fromisoformat(metric['timestamp'])
            if start_date and timestamp < start_date:
                continue
            if end_date and timestamp > end_date:
                continue
            filtered_metrics.append(metric)
            
        return filtered_metrics
        
    def get_metrics_summary(self,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> Dict[str, float]:
        """
        Obtiene resumen de métricas.
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            
        Returns:
            Diccionario con resumen de métricas
        """
        metrics = self.get_metrics_history(start_date, end_date)
        
        if not metrics:
            return {}
            
        # Calcular promedios
        summary = {}
        for key in metrics[0].keys():
            if key != 'timestamp':
                values = [m[key] for m in metrics if key in m]
                if values:
                    summary[f'avg_{key}'] = np.mean(values)
                    summary[f'std_{key}'] = np.std(values)
                    summary[f'min_{key}'] = np.min(values)
                    summary[f'max_{key}'] = np.max(values)
                    
        return summary
        
    def export_metrics(self,
                      file_path: str,
                      format: str = 'csv') -> None:
        """
        Exporta métricas a archivo.
        
        Args:
            file_path: Ruta del archivo
            format: Formato de exportación ('csv' o 'json')
        """
        if format == 'csv':
            df = pd.DataFrame(self.metrics_history)
            df.to_csv(file_path, index=False)
        elif format == 'json':
            with open(file_path, 'w') as f:
                json.dump(self.metrics_history, f)
                
    def plot_metrics(self,
                    metric_name: str,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> None:
        """
        Genera gráfico de métricas.
        
        Args:
            metric_name: Nombre de la métrica
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
        """
        metrics = self.get_metrics_history(start_date, end_date)
        
        if not metrics:
            return
            
        # Preparar datos
        timestamps = [datetime.fromisoformat(m['timestamp']) for m in metrics]
        values = [m[metric_name] for m in metrics if metric_name in m]
        
        if not values:
            return
            
        # Crear gráfico
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, values)
        plt.title(f'{metric_name} over time')
        plt.xlabel('Time')
        plt.ylabel(metric_name)
        plt.grid(True)
        plt.show() 