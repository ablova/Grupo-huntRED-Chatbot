"""
Sistema de Métricas del Sistema Aura

Este módulo implementa el sistema de métricas para el análisis de Aura,
registrando y analizando datos de rendimiento y efectividad.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime, timedelta
import json

from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Tipos de métricas del sistema Aura."""
    COMPATIBILITY_SCORE = "compatibility_score"
    ENERGY_ALIGNMENT = "energy_alignment"
    VIBRATIONAL_RESONANCE = "vibrational_resonance"
    HOLISTIC_BALANCE = "holistic_balance"
    ANALYSIS_ACCURACY = "analysis_accuracy"
    RECOMMENDATION_EFFECTIVENESS = "recommendation_effectiveness"
    USER_SATISFACTION = "user_satisfaction"
    SYSTEM_PERFORMANCE = "system_performance"

class MetricCategory(Enum):
    """Categorías de métricas."""
    TECHNICAL = "technical"
    BUSINESS = "business"
    USER_EXPERIENCE = "user_experience"
    SYSTEM_HEALTH = "system_health"

@dataclass
class AuraMetric:
    """Estructura de una métrica de Aura."""
    metric_type: MetricType
    category: MetricCategory
    value: float
    timestamp: datetime
    context: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class MetricAggregation:
    """Agregación de métricas."""
    metric_type: MetricType
    count: int
    mean: float
    std: float
    min: float
    max: float
    median: float
    percentile_25: float
    percentile_75: float
    time_period: str

class AuraMetrics:
    """
    Sistema de métricas para el análisis de Aura.
    
    Registra, analiza y reporta métricas de rendimiento y efectividad
    del sistema Aura para optimización continua.
    """
    
    def __init__(self):
        """Inicializa el sistema de métricas."""
        self.metrics_cache_ttl = 3600  # 1 hora
        self.aggregation_cache_ttl = 7200  # 2 horas
        
        # Configuración de alertas
        self.alert_thresholds = {
            MetricType.COMPATIBILITY_SCORE: {'min': 60, 'max': 95},
            MetricType.ENERGY_ALIGNMENT: {'min': 50, 'max': 90},
            MetricType.VIBRATIONAL_RESONANCE: {'min': 55, 'max': 85},
            MetricType.HOLISTIC_BALANCE: {'min': 65, 'max': 90},
            MetricType.ANALYSIS_ACCURACY: {'min': 70, 'max': 95},
            MetricType.RECOMMENDATION_EFFECTIVENESS: {'min': 60, 'max': 90},
            MetricType.USER_SATISFACTION: {'min': 70, 'max': 95},
            MetricType.SYSTEM_PERFORMANCE: {'min': 80, 'max': 99}
        }
        
        logger.info("Sistema de métricas Aura inicializado")
    
    async def record_analysis(
        self,
        person_id: int,
        analysis_results: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra métricas de un análisis de Aura.
        
        Args:
            person_id: ID de la persona analizada
            analysis_results: Resultados del análisis
            context: Contexto adicional del análisis
        """
        try:
            timestamp = datetime.now()
            context = context or {}
            
            # Extraer métricas de los resultados
            metrics = []
            
            # Métrica de compatibilidad
            if 'compatibility' in analysis_results:
                compatibility_score = analysis_results['compatibility'].score
                metrics.append(AuraMetric(
                    metric_type=MetricType.COMPATIBILITY_SCORE,
                    category=MetricCategory.BUSINESS,
                    value=compatibility_score,
                    timestamp=timestamp,
                    context={'person_id': person_id, **context},
                    metadata={'analysis_type': 'compatibility'}
                ))
            
            # Métrica de energía
            if 'energy_match' in analysis_results:
                energy_score = analysis_results['energy_match'].score
                metrics.append(AuraMetric(
                    metric_type=MetricType.ENERGY_ALIGNMENT,
                    category=MetricCategory.TECHNICAL,
                    value=energy_score,
                    timestamp=timestamp,
                    context={'person_id': person_id, **context},
                    metadata={'analysis_type': 'energy'}
                ))
            
            # Métrica vibracional
            if 'vibrational_alignment' in analysis_results:
                vibrational_score = analysis_results['vibrational_alignment'].score
                metrics.append(AuraMetric(
                    metric_type=MetricType.VIBRATIONAL_RESONANCE,
                    category=MetricCategory.TECHNICAL,
                    value=vibrational_score,
                    timestamp=timestamp,
                    context={'person_id': person_id, **context},
                    metadata={'analysis_type': 'vibrational'}
                ))
            
            # Métrica holística
            if 'holistic_assessment' in analysis_results:
                holistic_score = analysis_results['holistic_assessment'].score
                metrics.append(AuraMetric(
                    metric_type=MetricType.HOLISTIC_BALANCE,
                    category=MetricCategory.BUSINESS,
                    value=holistic_score,
                    timestamp=timestamp,
                    context={'person_id': person_id, **context},
                    metadata={'analysis_type': 'holistic'}
                ))
            
            # Guardar métricas
            await self._save_metrics(metrics)
            
            # Verificar alertas
            await self._check_alerts(metrics)
            
            logger.info(f"Métricas registradas para persona {person_id}: {len(metrics)} métricas")
            
        except Exception as e:
            logger.error(f"Error registrando métricas de análisis: {str(e)}")
    
    async def record_recommendation_effectiveness(
        self,
        person_id: int,
        recommendation_type: str,
        effectiveness_score: float,
        feedback: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra la efectividad de las recomendaciones.
        
        Args:
            person_id: ID de la persona
            recommendation_type: Tipo de recomendación
            effectiveness_score: Score de efectividad (0-100)
            feedback: Feedback adicional
        """
        try:
            metric = AuraMetric(
                metric_type=MetricType.RECOMMENDATION_EFFECTIVENESS,
                category=MetricCategory.USER_EXPERIENCE,
                value=effectiveness_score,
                timestamp=datetime.now(),
                context={'person_id': person_id, 'recommendation_type': recommendation_type},
                metadata={'feedback': feedback or {}}
            )
            
            await self._save_metrics([metric])
            
            logger.info(f"Efectividad de recomendación registrada: {effectiveness_score}")
            
        except Exception as e:
            logger.error(f"Error registrando efectividad de recomendación: {str(e)}")
    
    async def record_user_satisfaction(
        self,
        person_id: int,
        satisfaction_score: float,
        analysis_type: str,
        feedback: Optional[str] = None
    ) -> None:
        """
        Registra la satisfacción del usuario.
        
        Args:
            person_id: ID de la persona
            satisfaction_score: Score de satisfacción (0-100)
            analysis_type: Tipo de análisis
            feedback: Feedback del usuario
        """
        try:
            metric = AuraMetric(
                metric_type=MetricType.USER_SATISFACTION,
                category=MetricCategory.USER_EXPERIENCE,
                value=satisfaction_score,
                timestamp=datetime.now(),
                context={'person_id': person_id, 'analysis_type': analysis_type},
                metadata={'feedback': feedback}
            )
            
            await self._save_metrics([metric])
            
            logger.info(f"Satisfacción de usuario registrada: {satisfaction_score}")
            
        except Exception as e:
            logger.error(f"Error registrando satisfacción de usuario: {str(e)}")
    
    async def record_system_performance(
        self,
        performance_metrics: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra métricas de rendimiento del sistema.
        
        Args:
            performance_metrics: Métricas de rendimiento
            context: Contexto adicional
        """
        try:
            timestamp = datetime.now()
            context = context or {}
            metrics = []
            
            for metric_name, value in performance_metrics.items():
                metric = AuraMetric(
                    metric_type=MetricType.SYSTEM_PERFORMANCE,
                    category=MetricCategory.SYSTEM_HEALTH,
                    value=value,
                    timestamp=timestamp,
                    context=context,
                    metadata={'metric_name': metric_name}
                )
                metrics.append(metric)
            
            await self._save_metrics(metrics)
            
            logger.info(f"Métricas de rendimiento registradas: {len(metrics)} métricas")
            
        except Exception as e:
            logger.error(f"Error registrando métricas de rendimiento: {str(e)}")
    
    async def get_metrics_summary(
        self,
        time_period: str = "24h",
        metric_types: Optional[List[MetricType]] = None
    ) -> Dict[str, Any]:
        """
        Obtiene un resumen de métricas para un período de tiempo.
        
        Args:
            time_period: Período de tiempo ("1h", "24h", "7d", "30d")
            metric_types: Tipos de métricas a incluir
            
        Returns:
            Resumen de métricas
        """
        try:
            if metric_types is None:
                metric_types = list(MetricType)
            
            summary = {
                'time_period': time_period,
                'generated_at': datetime.now().isoformat(),
                'metrics': {}
            }
            
            for metric_type in metric_types:
                aggregation = await self._get_metric_aggregation(metric_type, time_period)
                if aggregation:
                    summary['metrics'][metric_type.value] = {
                        'count': aggregation.count,
                        'mean': aggregation.mean,
                        'std': aggregation.std,
                        'min': aggregation.min,
                        'max': aggregation.max,
                        'median': aggregation.median,
                        'percentile_25': aggregation.percentile_25,
                        'percentile_75': aggregation.percentile_75
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de métricas: {str(e)}")
            return {'error': str(e)}
    
    async def get_trend_analysis(
        self,
        metric_type: MetricType,
        time_period: str = "7d"
    ) -> Dict[str, Any]:
        """
        Obtiene análisis de tendencias para una métrica específica.
        
        Args:
            metric_type: Tipo de métrica
            time_period: Período de tiempo
            
        Returns:
            Análisis de tendencias
        """
        try:
            # Obtener datos históricos
            historical_data = await self._get_historical_metrics(metric_type, time_period)
            
            if not historical_data:
                return {'error': 'No hay datos históricos disponibles'}
            
            # Calcular tendencias
            values = [metric.value for metric in historical_data]
            timestamps = [metric.timestamp for metric in historical_data]
            
            # Tendencia lineal
            if len(values) > 1:
                x = np.arange(len(values))
                slope, intercept = np.polyfit(x, values, 1)
                trend_direction = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
                trend_strength = abs(slope)
            else:
                trend_direction = 'insufficient_data'
                trend_strength = 0.0
            
            # Análisis de estacionalidad (simplificado)
            seasonality = self._analyze_seasonality(values, timestamps)
            
            # Predicción simple
            prediction = self._simple_prediction(values)
            
            return {
                'metric_type': metric_type.value,
                'time_period': time_period,
                'data_points': len(values),
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'current_value': values[-1] if values else 0,
                'prediction_next_period': prediction,
                'seasonality': seasonality,
                'volatility': np.std(values) if len(values) > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"Error analizando tendencias: {str(e)}")
            return {'error': str(e)}
    
    async def get_comparison_analysis(
        self,
        metric_type: MetricType,
        time_periods: List[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene análisis comparativo entre períodos de tiempo.
        
        Args:
            metric_type: Tipo de métrica
            time_periods: Lista de períodos a comparar
            
        Returns:
            Análisis comparativo
        """
        try:
            if time_periods is None:
                time_periods = ["24h", "7d", "30d"]
            
            comparison = {
                'metric_type': metric_type.value,
                'comparisons': {}
            }
            
            for period in time_periods:
                aggregation = await self._get_metric_aggregation(metric_type, period)
                if aggregation:
                    comparison['comparisons'][period] = {
                        'mean': aggregation.mean,
                        'count': aggregation.count,
                        'std': aggregation.std
                    }
            
            # Calcular cambios porcentuales
            if len(comparison['comparisons']) > 1:
                periods = list(comparison['comparisons'].keys())
                for i in range(1, len(periods)):
                    current_mean = comparison['comparisons'][periods[i]]['mean']
                    previous_mean = comparison['comparisons'][periods[i-1]]['mean']
                    
                    if previous_mean > 0:
                        change_percentage = ((current_mean - previous_mean) / previous_mean) * 100
                    else:
                        change_percentage = 0
                    
                    comparison['comparisons'][periods[i]]['change_from_previous'] = change_percentage
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error en análisis comparativo: {str(e)}")
            return {'error': str(e)}
    
    async def get_alert_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de alertas activas.
        
        Returns:
            Resumen de alertas
        """
        try:
            alerts = []
            
            for metric_type, thresholds in self.alert_thresholds.items():
                # Obtener métrica más reciente
                recent_metrics = await self._get_recent_metrics(metric_type, "1h")
                
                if recent_metrics:
                    latest_value = recent_metrics[-1].value
                    
                    # Verificar umbrales
                    if latest_value < thresholds['min']:
                        alerts.append({
                            'metric_type': metric_type.value,
                            'alert_type': 'below_threshold',
                            'current_value': latest_value,
                            'threshold': thresholds['min'],
                            'severity': 'high' if latest_value < thresholds['min'] * 0.8 else 'medium'
                        })
                    elif latest_value > thresholds['max']:
                        alerts.append({
                            'metric_type': metric_type.value,
                            'alert_type': 'above_threshold',
                            'current_value': latest_value,
                            'threshold': thresholds['max'],
                            'severity': 'medium'
                        })
            
            return {
                'alerts_count': len(alerts),
                'alerts': alerts,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de alertas: {str(e)}")
            return {'error': str(e)}
    
    async def _save_metrics(self, metrics: List[AuraMetric]) -> None:
        """Guarda métricas en el sistema de almacenamiento."""
        try:
            # En una implementación real, esto guardaría en base de datos
            # Por ahora, usamos caché como almacenamiento temporal
            
            for metric in metrics:
                cache_key = f"aura_metric_{metric.metric_type.value}_{metric.timestamp.isoformat()}"
                cache.set(cache_key, self._serialize_metric(metric), self.metrics_cache_ttl)
            
            # Actualizar agregaciones
            await self._update_aggregations(metrics)
            
        except Exception as e:
            logger.error(f"Error guardando métricas: {str(e)}")
    
    async def _update_aggregations(self, metrics: List[AuraMetric]) -> None:
        """Actualiza las agregaciones de métricas."""
        try:
            # Agrupar métricas por tipo
            metrics_by_type = {}
            for metric in metrics:
                if metric.metric_type not in metrics_by_type:
                    metrics_by_type[metric.metric_type] = []
                metrics_by_type[metric.metric_type].append(metric)
            
            # Actualizar agregaciones para cada tipo
            for metric_type, type_metrics in metrics_by_type.items():
                await self._update_metric_aggregation(metric_type, type_metrics)
                
        except Exception as e:
            logger.error(f"Error actualizando agregaciones: {str(e)}")
    
    async def _update_metric_aggregation(
        self,
        metric_type: MetricType,
        new_metrics: List[AuraMetric]
    ) -> None:
        """Actualiza la agregación para un tipo de métrica específico."""
        try:
            # Obtener métricas existentes
            existing_metrics = await self._get_recent_metrics(metric_type, "24h")
            
            # Combinar con nuevas métricas
            all_metrics = existing_metrics + new_metrics
            
            # Calcular agregaciones para diferentes períodos
            periods = ["1h", "24h", "7d", "30d"]
            
            for period in periods:
                period_metrics = self._filter_metrics_by_period(all_metrics, period)
                
                if period_metrics:
                    aggregation = self._calculate_aggregation(period_metrics)
                    aggregation.time_period = period
                    
                    # Guardar agregación
                    cache_key = f"aura_aggregation_{metric_type.value}_{period}"
                    cache.set(cache_key, self._serialize_aggregation(aggregation), self.aggregation_cache_ttl)
                    
        except Exception as e:
            logger.error(f"Error actualizando agregación de métrica {metric_type}: {str(e)}")
    
    def _calculate_aggregation(self, metrics: List[AuraMetric]) -> MetricAggregation:
        """Calcula la agregación de un conjunto de métricas."""
        values = [metric.value for metric in metrics]
        
        return MetricAggregation(
            metric_type=metrics[0].metric_type if metrics else MetricType.COMPATIBILITY_SCORE,
            count=len(values),
            mean=np.mean(values) if values else 0.0,
            std=np.std(values) if len(values) > 1 else 0.0,
            min=np.min(values) if values else 0.0,
            max=np.max(values) if values else 0.0,
            median=np.median(values) if values else 0.0,
            percentile_25=np.percentile(values, 25) if values else 0.0,
            percentile_75=np.percentile(values, 75) if values else 0.0,
            time_period=""
        )
    
    def _filter_metrics_by_period(self, metrics: List[AuraMetric], period: str) -> List[AuraMetric]:
        """Filtra métricas por período de tiempo."""
        now = datetime.now()
        
        if period == "1h":
            cutoff = now - timedelta(hours=1)
        elif period == "24h":
            cutoff = now - timedelta(days=1)
        elif period == "7d":
            cutoff = now - timedelta(days=7)
        elif period == "30d":
            cutoff = now - timedelta(days=30)
        else:
            return metrics
        
        return [metric for metric in metrics if metric.timestamp >= cutoff]
    
    async def _get_metric_aggregation(
        self,
        metric_type: MetricType,
        time_period: str
    ) -> Optional[MetricAggregation]:
        """Obtiene la agregación de una métrica para un período específico."""
        try:
            cache_key = f"aura_aggregation_{metric_type.value}_{time_period}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return self._deserialize_aggregation(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo agregación de métrica: {str(e)}")
            return None
    
    async def _get_historical_metrics(
        self,
        metric_type: MetricType,
        time_period: str
    ) -> List[AuraMetric]:
        """Obtiene métricas históricas para análisis de tendencias."""
        try:
            # En una implementación real, esto consultaría la base de datos
            # Por ahora, retornamos una lista vacía
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas históricas: {str(e)}")
            return []
    
    async def _get_recent_metrics(
        self,
        metric_type: MetricType,
        time_period: str
    ) -> List[AuraMetric]:
        """Obtiene métricas recientes."""
        try:
            # En una implementación real, esto consultaría la base de datos
            # Por ahora, retornamos una lista vacía
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas recientes: {str(e)}")
            return []
    
    async def _check_alerts(self, metrics: List[AuraMetric]) -> None:
        """Verifica si las métricas activan alertas."""
        try:
            for metric in metrics:
                if metric.metric_type in self.alert_thresholds:
                    thresholds = self.alert_thresholds[metric.metric_type]
                    
                    if metric.value < thresholds['min']:
                        await self._trigger_alert(metric, 'below_threshold', thresholds['min'])
                    elif metric.value > thresholds['max']:
                        await self._trigger_alert(metric, 'above_threshold', thresholds['max'])
                        
        except Exception as e:
            logger.error(f"Error verificando alertas: {str(e)}")
    
    async def _trigger_alert(
        self,
        metric: AuraMetric,
        alert_type: str,
        threshold: float
    ) -> None:
        """Activa una alerta."""
        try:
            alert = {
                'metric_type': metric.metric_type.value,
                'alert_type': alert_type,
                'current_value': metric.value,
                'threshold': threshold,
                'timestamp': metric.timestamp.isoformat(),
                'context': metric.context
            }
            
            # En una implementación real, esto enviaría la alerta
            logger.warning(f"Alerta Aura: {alert}")
            
        except Exception as e:
            logger.error(f"Error activando alerta: {str(e)}")
    
    def _analyze_seasonality(self, values: List[float], timestamps: List[datetime]) -> Dict[str, Any]:
        """Analiza la estacionalidad de los datos."""
        try:
            if len(values) < 24:  # Necesitamos suficientes datos
                return {'detected': False, 'reason': 'insufficient_data'}
            
            # Análisis básico de estacionalidad
            hourly_values = {}
            for i, timestamp in enumerate(timestamps):
                hour = timestamp.hour
                if hour not in hourly_values:
                    hourly_values[hour] = []
                hourly_values[hour].append(values[i])
            
            # Calcular variación por hora
            hourly_means = {hour: np.mean(hourly_values[hour]) for hour in hourly_values}
            overall_mean = np.mean(values)
            
            # Detectar patrones
            max_hour = max(hourly_means, key=hourly_means.get)
            min_hour = min(hourly_means, key=hourly_means.get)
            
            variation = (hourly_means[max_hour] - hourly_means[min_hour]) / overall_mean
            
            return {
                'detected': variation > 0.1,  # 10% de variación
                'variation_percentage': variation * 100,
                'peak_hour': max_hour,
                'low_hour': min_hour,
                'hourly_pattern': hourly_means
            }
            
        except Exception as e:
            logger.error(f"Error analizando estacionalidad: {str(e)}")
            return {'detected': False, 'reason': 'analysis_error'}
    
    def _simple_prediction(self, values: List[float]) -> float:
        """Realiza una predicción simple basada en tendencia."""
        try:
            if len(values) < 2:
                return values[-1] if values else 0.0
            
            # Predicción basada en promedio móvil
            window_size = min(5, len(values))
            recent_values = values[-window_size:]
            
            # Tendencia simple
            if len(values) >= 2:
                trend = (values[-1] - values[-2]) / values[-2] if values[-2] > 0 else 0
                prediction = values[-1] * (1 + trend)
            else:
                prediction = np.mean(recent_values)
            
            return max(0.0, min(100.0, prediction))
            
        except Exception as e:
            logger.error(f"Error en predicción simple: {str(e)}")
            return values[-1] if values else 0.0
    
    def _serialize_metric(self, metric: AuraMetric) -> str:
        """Serializa una métrica para almacenamiento."""
        return json.dumps({
            'metric_type': metric.metric_type.value,
            'category': metric.category.value,
            'value': metric.value,
            'timestamp': metric.timestamp.isoformat(),
            'context': metric.context,
            'metadata': metric.metadata
        })
    
    def _deserialize_metric(self, data: str) -> AuraMetric:
        """Deserializa una métrica desde almacenamiento."""
        data_dict = json.loads(data)
        return AuraMetric(
            metric_type=MetricType(data_dict['metric_type']),
            category=MetricCategory(data_dict['category']),
            value=data_dict['value'],
            timestamp=datetime.fromisoformat(data_dict['timestamp']),
            context=data_dict['context'],
            metadata=data_dict['metadata']
        )
    
    def _serialize_aggregation(self, aggregation: MetricAggregation) -> str:
        """Serializa una agregación para almacenamiento."""
        return json.dumps({
            'metric_type': aggregation.metric_type.value,
            'count': aggregation.count,
            'mean': aggregation.mean,
            'std': aggregation.std,
            'min': aggregation.min,
            'max': aggregation.max,
            'median': aggregation.median,
            'percentile_25': aggregation.percentile_25,
            'percentile_75': aggregation.percentile_75,
            'time_period': aggregation.time_period
        })
    
    def _deserialize_aggregation(self, data: str) -> MetricAggregation:
        """Deserializa una agregación desde almacenamiento."""
        data_dict = json.loads(data)
        return MetricAggregation(
            metric_type=MetricType(data_dict['metric_type']),
            count=data_dict['count'],
            mean=data_dict['mean'],
            std=data_dict['std'],
            min=data_dict['min'],
            max=data_dict['max'],
            median=data_dict['median'],
            percentile_25=data_dict['percentile_25'],
            percentile_75=data_dict['percentile_75'],
            time_period=data_dict['time_period']
        ) 