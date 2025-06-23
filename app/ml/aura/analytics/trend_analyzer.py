"""
AURA - Trend Analyzer
Sistema avanzado de análisis de tendencias para identificar patrones, predicciones y oportunidades.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """
    Analizador de tendencias avanzado para AURA:
    - Análisis de tendencias temporales y estacionales
    - Predicciones basadas en patrones históricos
    - Detección de anomalías y cambios de tendencia
    - Análisis de correlaciones y causalidad
    - Integración con GNN para tendencias de red
    """
    
    def __init__(self):
        self.trend_cache = {}
        self.pattern_database = {}
        self.seasonal_factors = {}
        self.correlation_matrix = {}
        self.anomaly_thresholds = {}
        
        # Configurar factores estacionales por defecto
        self._setup_seasonal_factors()
        
    def _setup_seasonal_factors(self):
        """Configura factores estacionales por defecto."""
        self.seasonal_factors = {
            'monthly': {
                1: 0.8,   # Enero - post-vacaciones
                2: 0.9,   # Febrero - recuperación
                3: 1.0,   # Marzo - normal
                4: 1.1,   # Abril - crecimiento
                5: 1.0,   # Mayo - normal
                6: 0.9,   # Junio - pre-vacaciones
                7: 0.7,   # Julio - vacaciones
                8: 0.8,   # Agosto - vacaciones
                9: 1.2,   # Septiembre - post-vacaciones
                10: 1.1,  # Octubre - crecimiento
                11: 1.0,  # Noviembre - normal
                12: 0.8   # Diciembre - fin de año
            },
            'weekly': {
                0: 0.7,   # Lunes
                1: 0.9,   # Martes
                2: 1.0,   # Miércoles
                3: 1.1,   # Jueves
                4: 1.0,   # Viernes
                5: 0.5,   # Sábado
                6: 0.3    # Domingo
            },
            'daily': {
                6: 0.3,   # 6 AM
                7: 0.5,   # 7 AM
                8: 0.8,   # 8 AM
                9: 1.0,   # 9 AM
                10: 1.1,  # 10 AM
                11: 1.0,  # 11 AM
                12: 0.8,  # 12 PM
                13: 0.7,  # 1 PM
                14: 0.9,  # 2 PM
                15: 1.0,  # 3 PM
                16: 1.1,  # 4 PM
                17: 1.0,  # 5 PM
                18: 0.8,  # 6 PM
                19: 0.6,  # 7 PM
                20: 0.4,  # 8 PM
                21: 0.3,  # 9 PM
                22: 0.2,  # 10 PM
                23: 0.1   # 11 PM
            }
        }
    
    def analyze_trends(self, data: List[Dict[str, Any]], metric_name: str, 
                      time_range: str = '90d', business_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Analiza tendencias en un conjunto de datos.
        
        Args:
            data: Lista de datos con timestamps y valores
            metric_name: Nombre de la métrica a analizar
            time_range: Rango de tiempo para el análisis
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Dict con análisis completo de tendencias
        """
        if not data:
            return self._get_empty_trend_analysis()
        
        # Preparar datos para análisis
        processed_data = self._preprocess_data(data)
        
        # Análisis de tendencia general
        trend_analysis = self._calculate_trend_direction(processed_data)
        
        # Análisis de estacionalidad
        seasonality_analysis = self._analyze_seasonality(processed_data)
        
        # Detección de anomalías
        anomaly_analysis = self._detect_anomalies(processed_data)
        
        # Análisis de patrones
        pattern_analysis = self._analyze_patterns(processed_data)
        
        # Predicciones
        predictions = self._generate_predictions(processed_data, trend_analysis, seasonality_analysis)
        
        # Análisis de correlaciones
        correlation_analysis = self._analyze_correlations(processed_data, business_unit)
        
        # Insights y recomendaciones
        insights = self._generate_trend_insights(trend_analysis, seasonality_analysis, 
                                               anomaly_analysis, pattern_analysis)
        
        return {
            'metric_name': metric_name,
            'time_range': time_range,
            'business_unit': business_unit,
            'data_points': len(data),
            'trend_analysis': trend_analysis,
            'seasonality_analysis': seasonality_analysis,
            'anomaly_analysis': anomaly_analysis,
            'pattern_analysis': pattern_analysis,
            'predictions': predictions,
            'correlation_analysis': correlation_analysis,
            'insights': insights,
            'confidence_score': self._calculate_confidence_score(processed_data, trend_analysis),
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_multiple_metrics(self, metrics_data: Dict[str, List[Dict[str, Any]]], 
                               time_range: str = '90d', 
                               business_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Analiza tendencias en múltiples métricas simultáneamente.
        
        Args:
            metrics_data: Dict con métricas y sus datos
            time_range: Rango de tiempo para el análisis
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Dict con análisis de todas las métricas
        """
        results = {}
        cross_metric_analysis = {}
        
        # Analizar cada métrica individualmente
        for metric_name, data in metrics_data.items():
            results[metric_name] = self.analyze_trends(data, metric_name, time_range, business_unit)
        
        # Análisis cruzado de métricas
        if len(metrics_data) > 1:
            cross_metric_analysis = self._analyze_cross_metrics(metrics_data, results)
        
        return {
            'individual_metrics': results,
            'cross_metric_analysis': cross_metric_analysis,
            'summary': self._generate_summary_analysis(results),
            'time_range': time_range,
            'business_unit': business_unit,
            'total_metrics': len(metrics_data),
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_trend_changes(self, data: List[Dict[str, Any]], 
                           metric_name: str, 
                           sensitivity: float = 0.1) -> Dict[str, Any]:
        """
        Detecta cambios significativos en las tendencias.
        
        Args:
            data: Lista de datos con timestamps y valores
            metric_name: Nombre de la métrica
            sensitivity: Sensibilidad para detectar cambios (0-1)
            
        Returns:
            Dict con cambios de tendencia detectados
        """
        if not data:
            return {'changes': [], 'total_changes': 0}
        
        processed_data = self._preprocess_data(data)
        changes = []
        
        # Detectar cambios usando ventanas deslizantes
        window_size = max(7, len(processed_data) // 10)  # 10% de los datos o mínimo 7
        
        for i in range(window_size, len(processed_data)):
            window_before = processed_data[i-window_size:i]
            window_after = processed_data[i:i+window_size] if i+window_size <= len(processed_data) else processed_data[i:]
            
            if len(window_after) < 3:  # Necesitamos al menos 3 puntos para detectar cambio
                continue
            
            # Calcular tendencias antes y después
            trend_before = self._calculate_simple_trend(window_before)
            trend_after = self._calculate_simple_trend(window_after)
            
            # Detectar cambio significativo
            change_magnitude = abs(trend_after - trend_before)
            if change_magnitude > sensitivity:
                changes.append({
                    'timestamp': processed_data[i]['timestamp'],
                    'value': processed_data[i]['value'],
                    'trend_before': trend_before,
                    'trend_after': trend_after,
                    'change_magnitude': change_magnitude,
                    'change_type': 'increase' if trend_after > trend_before else 'decrease'
                })
        
        return {
            'changes': changes,
            'total_changes': len(changes),
            'sensitivity': sensitivity,
            'metric_name': metric_name,
            'most_recent_change': changes[-1] if changes else None
        }
    
    def forecast_metric(self, data: List[Dict[str, Any]], 
                      metric_name: str, 
                      forecast_periods: int = 30,
                      confidence_level: float = 0.95) -> Dict[str, Any]:
        """
        Genera pronósticos para una métrica específica.
        
        Args:
            data: Datos históricos
            metric_name: Nombre de la métrica
            forecast_periods: Número de períodos a pronosticar
            confidence_level: Nivel de confianza del pronóstico
            
        Returns:
            Dict con pronósticos y intervalos de confianza
        """
        if not data:
            return {'forecast': [], 'confidence_intervals': []}
        
        processed_data = self._preprocess_data(data)
        
        # Análisis de tendencia y estacionalidad
        trend_analysis = self._calculate_trend_direction(processed_data)
        seasonality_analysis = self._analyze_seasonality(processed_data)
        
        # Generar pronósticos
        forecasts = []
        confidence_intervals = []
        
        last_value = processed_data[-1]['value']
        trend_slope = trend_analysis.get('slope', 0)
        
        for i in range(1, forecast_periods + 1):
            # Pronóstico base con tendencia
            base_forecast = last_value + (trend_slope * i)
            
            # Ajustar por estacionalidad
            seasonal_factor = self._get_seasonal_factor(processed_data[-1]['timestamp'], i)
            adjusted_forecast = base_forecast * seasonal_factor
            
            # Calcular intervalo de confianza
            confidence_interval = self._calculate_confidence_interval(
                adjusted_forecast, processed_data, confidence_level
            )
            
            forecasts.append(adjusted_forecast)
            confidence_intervals.append(confidence_interval)
        
        return {
            'forecast': forecasts,
            'confidence_intervals': confidence_intervals,
            'forecast_periods': forecast_periods,
            'confidence_level': confidence_level,
            'metric_name': metric_name,
            'last_actual_value': last_value,
            'trend_slope': trend_slope,
            'forecast_accuracy': self._estimate_forecast_accuracy(processed_data)
        }
    
    def _preprocess_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preprocesa los datos para análisis."""
        processed = []
        
        for point in data:
            if 'timestamp' in point and 'value' in point:
                # Convertir timestamp a datetime si es string
                if isinstance(point['timestamp'], str):
                    try:
                        timestamp = datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00'))
                    except:
                        timestamp = datetime.now()
                else:
                    timestamp = point['timestamp']
                
                processed.append({
                    'timestamp': timestamp,
                    'value': float(point['value']),
                    'original_data': point
                })
        
        # Ordenar por timestamp
        processed.sort(key=lambda x: x['timestamp'])
        
        return processed
    
    def _calculate_trend_direction(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula la dirección y magnitud de la tendencia."""
        if len(data) < 2:
            return {'direction': 'stable', 'slope': 0, 'strength': 0}
        
        # Calcular regresión lineal simple
        x = np.arange(len(data))
        y = np.array([point['value'] for point in data])
        
        # Calcular pendiente y correlación
        slope = np.polyfit(x, y, 1)[0]
        correlation = np.corrcoef(x, y)[0, 1]
        
        # Determinar dirección
        if abs(slope) < 0.01:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        # Calcular fuerza de la tendencia
        strength = abs(correlation)
        
        return {
            'direction': direction,
            'slope': slope,
            'strength': strength,
            'correlation': correlation,
            'start_value': data[0]['value'],
            'end_value': data[-1]['value'],
            'total_change': data[-1]['value'] - data[0]['value'],
            'percentage_change': ((data[-1]['value'] - data[0]['value']) / data[0]['value']) * 100 if data[0]['value'] != 0 else 0
        }
    
    def _analyze_seasonality(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza patrones estacionales en los datos."""
        if len(data) < 30:  # Necesitamos suficientes datos para detectar estacionalidad
            return {'detected': False, 'patterns': {}}
        
        # Agrupar por diferentes períodos
        monthly_patterns = defaultdict(list)
        weekly_patterns = defaultdict(list)
        daily_patterns = defaultdict(list)
        
        for point in data:
            timestamp = point['timestamp']
            value = point['value']
            
            monthly_patterns[timestamp.month].append(value)
            weekly_patterns[timestamp.weekday()].append(value)
            daily_patterns[timestamp.hour].append(value)
        
        # Calcular promedios estacionales
        monthly_avg = {month: np.mean(values) for month, values in monthly_patterns.items()}
        weekly_avg = {day: np.mean(values) for day, values in weekly_patterns.items()}
        daily_avg = {hour: np.mean(values) for hour, values in daily_patterns.items()}
        
        # Detectar si hay estacionalidad significativa
        overall_mean = np.mean([point['value'] for point in data])
        monthly_variance = np.var(list(monthly_avg.values())) / (overall_mean ** 2) if overall_mean != 0 else 0
        
        has_seasonality = monthly_variance > 0.1  # Umbral para detectar estacionalidad
        
        return {
            'detected': has_seasonality,
            'patterns': {
                'monthly': monthly_avg,
                'weekly': weekly_avg,
                'daily': daily_avg
            },
            'seasonality_strength': monthly_variance,
            'overall_mean': overall_mean
        }
    
    def _detect_anomalies(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detecta anomalías en los datos."""
        if len(data) < 10:
            return {'anomalies': [], 'total_anomalies': 0}
        
        values = np.array([point['value'] for point in data])
        mean = np.mean(values)
        std = np.std(values)
        
        anomalies = []
        threshold = 2.0  # Número de desviaciones estándar
        
        for i, point in enumerate(data):
            z_score = abs((point['value'] - mean) / std) if std != 0 else 0
            
            if z_score > threshold:
                anomalies.append({
                    'timestamp': point['timestamp'],
                    'value': point['value'],
                    'z_score': z_score,
                    'index': i,
                    'severity': 'high' if z_score > 3 else 'medium'
                })
        
        return {
            'anomalies': anomalies,
            'total_anomalies': len(anomalies),
            'anomaly_rate': len(anomalies) / len(data),
            'threshold': threshold,
            'mean': mean,
            'std': std
        }
    
    def _analyze_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza patrones específicos en los datos."""
        if len(data) < 20:
            return {'patterns': [], 'total_patterns': 0}
        
        patterns = []
        values = [point['value'] for point in data]
        
        # Detectar patrones de crecimiento/declive
        growth_patterns = self._detect_growth_patterns(values)
        if growth_patterns:
            patterns.extend(growth_patterns)
        
        # Detectar patrones cíclicos
        cyclic_patterns = self._detect_cyclic_patterns(values)
        if cyclic_patterns:
            patterns.extend(cyclic_patterns)
        
        # Detectar patrones de volatilidad
        volatility_patterns = self._detect_volatility_patterns(values)
        if volatility_patterns:
            patterns.extend(volatility_patterns)
        
        return {
            'patterns': patterns,
            'total_patterns': len(patterns),
            'pattern_types': list(set([p['type'] for p in patterns]))
        }
    
    def _detect_growth_patterns(self, values: List[float]) -> List[Dict[str, Any]]:
        """Detecta patrones de crecimiento específicos."""
        patterns = []
        
        # Detectar crecimiento exponencial
        if len(values) >= 10:
            # Calcular tasas de crecimiento
            growth_rates = []
            for i in range(1, len(values)):
                if values[i-1] != 0:
                    rate = (values[i] - values[i-1]) / values[i-1]
                    growth_rates.append(rate)
            
            # Detectar si las tasas de crecimiento son consistentes
            if len(growth_rates) >= 5:
                growth_std = np.std(growth_rates)
                if growth_std < 0.1:  # Crecimiento consistente
                    patterns.append({
                        'type': 'consistent_growth',
                        'description': 'Crecimiento consistente',
                        'strength': 1 - growth_std
                    })
        
        return patterns
    
    def _detect_cyclic_patterns(self, values: List[float]) -> List[Dict[str, Any]]:
        """Detecta patrones cíclicos."""
        patterns = []
        
        # Implementar detección de patrones cíclicos
        # Por ahora retorna lista vacía
        return patterns
    
    def _detect_volatility_patterns(self, values: List[float]) -> List[Dict[str, Any]]:
        """Detecta patrones de volatilidad."""
        patterns = []
        
        if len(values) >= 10:
            # Calcular volatilidad móvil
            volatility_window = 5
            volatilities = []
            
            for i in range(volatility_window, len(values)):
                window_values = values[i-volatility_window:i]
                volatility = np.std(window_values)
                volatilities.append(volatility)
            
            # Detectar cambios en volatilidad
            if len(volatilities) >= 5:
                volatility_trend = np.polyfit(range(len(volatilities)), volatilities, 1)[0]
                
                if volatility_trend > 0.01:
                    patterns.append({
                        'type': 'increasing_volatility',
                        'description': 'Volatilidad creciente',
                        'strength': abs(volatility_trend)
                    })
                elif volatility_trend < -0.01:
                    patterns.append({
                        'type': 'decreasing_volatility',
                        'description': 'Volatilidad decreciente',
                        'strength': abs(volatility_trend)
                    })
        
        return patterns
    
    def _generate_predictions(self, data: List[Dict[str, Any]], 
                            trend_analysis: Dict[str, Any],
                            seasonality_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Genera predicciones basadas en tendencias y estacionalidad."""
        if len(data) < 10:
            return {'predictions': [], 'confidence': 0}
        
        predictions = []
        last_value = data[-1]['value']
        trend_slope = trend_analysis.get('slope', 0)
        
        # Generar predicciones para los próximos 7 días
        for i in range(1, 8):
            # Predicción base con tendencia
            base_prediction = last_value + (trend_slope * i)
            
            # Ajustar por estacionalidad si está disponible
            if seasonality_analysis.get('detected', False):
                # Usar factor estacional del día correspondiente
                future_date = data[-1]['timestamp'] + timedelta(days=i)
                seasonal_factor = self._get_seasonal_factor(data[-1]['timestamp'], i)
                adjusted_prediction = base_prediction * seasonal_factor
            else:
                adjusted_prediction = base_prediction
            
            predictions.append({
                'period': i,
                'prediction': adjusted_prediction,
                'confidence': max(0.5, trend_analysis.get('strength', 0.5))
            })
        
        return {
            'predictions': predictions,
            'confidence': trend_analysis.get('strength', 0.5),
            'trend_direction': trend_analysis.get('direction', 'stable')
        }
    
    def _analyze_correlations(self, data: List[Dict[str, Any]], 
                            business_unit: Optional[str]) -> Dict[str, Any]:
        """Analiza correlaciones con otras métricas."""
        # Implementar análisis de correlaciones
        # Por ahora retorna análisis básico
        return {
            'correlations': [],
            'strongest_correlation': None,
            'correlation_matrix': {}
        }
    
    def _generate_trend_insights(self, trend_analysis: Dict[str, Any],
                               seasonality_analysis: Dict[str, Any],
                               anomaly_analysis: Dict[str, Any],
                               pattern_analysis: Dict[str, Any]) -> List[str]:
        """Genera insights basados en el análisis de tendencias."""
        insights = []
        
        # Insights de tendencia
        direction = trend_analysis.get('direction', 'stable')
        strength = trend_analysis.get('strength', 0)
        percentage_change = trend_analysis.get('percentage_change', 0)
        
        if direction == 'increasing' and strength > 0.7:
            insights.append(f"Tendencia alcista fuerte: {percentage_change:.1f}% de crecimiento")
        elif direction == 'decreasing' and strength > 0.7:
            insights.append(f"Tendencia bajista fuerte: {abs(percentage_change):.1f}% de disminución")
        elif strength < 0.3:
            insights.append("Tendencia inestable - considerar factores externos")
        
        # Insights de estacionalidad
        if seasonality_analysis.get('detected', False):
            insights.append("Patrones estacionales detectados - optimizar para ciclos")
        
        # Insights de anomalías
        anomaly_rate = anomaly_analysis.get('anomaly_rate', 0)
        if anomaly_rate > 0.1:
            insights.append(f"Tasa de anomalías elevada ({anomaly_rate:.1%}) - investigar causas")
        
        # Insights de patrones
        for pattern in pattern_analysis.get('patterns', []):
            if pattern['type'] == 'consistent_growth':
                insights.append("Patrón de crecimiento consistente detectado")
            elif pattern['type'] == 'increasing_volatility':
                insights.append("Volatilidad creciente - preparar para fluctuaciones")
        
        return insights
    
    def _calculate_confidence_score(self, data: List[Dict[str, Any]], 
                                  trend_analysis: Dict[str, Any]) -> float:
        """Calcula el score de confianza del análisis."""
        if len(data) < 10:
            return 0.3
        
        # Factores que afectan la confianza
        data_points_factor = min(1.0, len(data) / 100)  # Más datos = más confianza
        trend_strength_factor = trend_analysis.get('strength', 0.5)
        data_consistency_factor = 1.0 - self._calculate_data_volatility(data)
        
        # Score compuesto
        confidence = (data_points_factor * 0.3 + 
                     trend_strength_factor * 0.4 + 
                     data_consistency_factor * 0.3)
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_data_volatility(self, data: List[Dict[str, Any]]) -> float:
        """Calcula la volatilidad de los datos."""
        if len(data) < 2:
            return 0.0
        
        values = [point['value'] for point in data]
        return np.std(values) / np.mean(values) if np.mean(values) != 0 else 0.0
    
    def _get_seasonal_factor(self, base_timestamp: datetime, days_ahead: int) -> float:
        """Obtiene el factor estacional para una fecha futura."""
        future_date = base_timestamp + timedelta(days=days_ahead)
        
        # Factor mensual
        monthly_factor = self.seasonal_factors['monthly'].get(future_date.month, 1.0)
        
        # Factor semanal
        weekly_factor = self.seasonal_factors['weekly'].get(future_date.weekday(), 1.0)
        
        # Factor diario (usar hora del timestamp base)
        daily_factor = self.seasonal_factors['daily'].get(base_timestamp.hour, 1.0)
        
        # Combinar factores (promedio ponderado)
        return (monthly_factor * 0.5 + weekly_factor * 0.3 + daily_factor * 0.2)
    
    def _calculate_simple_trend(self, data: List[Dict[str, Any]]) -> float:
        """Calcula una tendencia simple para una ventana de datos."""
        if len(data) < 2:
            return 0.0
        
        x = np.arange(len(data))
        y = np.array([point['value'] for point in data])
        
        return np.polyfit(x, y, 1)[0]
    
    def _calculate_confidence_interval(self, forecast: float, data: List[Dict[str, Any]], 
                                     confidence_level: float) -> Tuple[float, float]:
        """Calcula intervalo de confianza para un pronóstico."""
        if len(data) < 10:
            return (forecast * 0.8, forecast * 1.2)
        
        # Calcular error estándar basado en datos históricos
        values = [point['value'] for point in data]
        std_error = np.std(values) * 0.1  # Simplificado
        
        # Factor de confianza (aproximado)
        if confidence_level == 0.95:
            factor = 1.96
        elif confidence_level == 0.90:
            factor = 1.645
        else:
            factor = 1.0
        
        margin = std_error * factor
        
        return (forecast - margin, forecast + margin)
    
    def _estimate_forecast_accuracy(self, data: List[Dict[str, Any]]) -> float:
        """Estima la precisión esperada del pronóstico."""
        if len(data) < 20:
            return 0.5
        
        # Calcular precisión basada en estabilidad de datos
        volatility = self._calculate_data_volatility(data)
        trend_strength = abs(np.corrcoef(range(len(data)), [p['value'] for p in data])[0, 1])
        
        # Más estabilidad y tendencia fuerte = mayor precisión
        accuracy = (1 - volatility) * 0.6 + trend_strength * 0.4
        
        return min(1.0, max(0.0, accuracy))
    
    def _analyze_cross_metrics(self, metrics_data: Dict[str, List[Dict[str, Any]]], 
                             individual_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza correlaciones entre diferentes métricas."""
        # Implementar análisis cruzado de métricas
        return {
            'correlations': {},
            'leading_indicators': [],
            'lagging_indicators': []
        }
    
    def _generate_summary_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un resumen del análisis de múltiples métricas."""
        summary = {
            'total_metrics': len(results),
            'trending_up': 0,
            'trending_down': 0,
            'stable': 0,
            'anomalies_detected': 0,
            'seasonal_patterns': 0
        }
        
        for metric_name, result in results.items():
            trend_direction = result['trend_analysis']['direction']
            if trend_direction == 'increasing':
                summary['trending_up'] += 1
            elif trend_direction == 'decreasing':
                summary['trending_down'] += 1
            else:
                summary['stable'] += 1
            
            if result['anomaly_analysis']['total_anomalies'] > 0:
                summary['anomalies_detected'] += 1
            
            if result['seasonality_analysis']['detected']:
                summary['seasonal_patterns'] += 1
        
        return summary
    
    def _get_empty_trend_analysis(self) -> Dict[str, Any]:
        """Retorna análisis vacío cuando no hay datos."""
        return {
            'metric_name': 'unknown',
            'time_range': 'unknown',
            'business_unit': None,
            'data_points': 0,
            'trend_analysis': {'direction': 'stable', 'slope': 0, 'strength': 0},
            'seasonality_analysis': {'detected': False, 'patterns': {}},
            'anomaly_analysis': {'anomalies': [], 'total_anomalies': 0},
            'pattern_analysis': {'patterns': [], 'total_patterns': 0},
            'predictions': {'predictions': [], 'confidence': 0},
            'correlation_analysis': {'correlations': []},
            'insights': ['Datos insuficientes para análisis'],
            'confidence_score': 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def update_seasonal_factors(self, category: str, factors: Dict[int, float]):
        """Actualiza factores estacionales."""
        if category in self.seasonal_factors:
            self.seasonal_factors[category].update(factors)
            logger.info(f"Updated seasonal factors for '{category}'")
    
    def get_trend_history(self, metric_name: str, time_range: str = '90d') -> List[Dict[str, Any]]:
        """Obtiene historial de análisis de tendencias para una métrica."""
        # Implementar obtención de historial
        return []
    
    def clear_cache(self):
        """Limpia el cache de análisis de tendencias."""
        self.trend_cache.clear()
        logger.info("Cleared trend analysis cache")

# Instancia global
trend_analyzer = TrendAnalyzer() 