"""
📊 GhuntRED-v2 ML Metrics
Performance tracking and monitoring for ML systems
"""

import time
import threading
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
import statistics

@dataclass
class ModelMetrics:
    """Metrics for a specific ML model"""
    model_name: str
    business_unit: str
    prediction_count: int = 0
    error_count: int = 0
    total_prediction_time: float = 0.0
    prediction_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    last_used: float = field(default_factory=time.time)
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def average_prediction_time(self) -> float:
        """Calculate average prediction time"""
        if self.prediction_count == 0:
            return 0.0
        return self.total_prediction_time / self.prediction_count
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage"""
        total_operations = self.prediction_count + self.error_count
        if total_operations == 0:
            return 0.0
        return (self.error_count / total_operations) * 100
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate as percentage"""
        total_cache_operations = self.cache_hits + self.cache_misses
        if total_cache_operations == 0:
            return 0.0
        return (self.cache_hits / total_cache_operations) * 100
    
    @property
    def recent_prediction_times(self) -> List[float]:
        """Get recent prediction times"""
        return list(self.prediction_times)
    
    @property
    def p95_prediction_time(self) -> float:
        """Calculate 95th percentile prediction time"""
        if not self.prediction_times:
            return 0.0
        sorted_times = sorted(self.prediction_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]
    
    @property
    def p99_prediction_time(self) -> float:
        """Calculate 99th percentile prediction time"""
        if not self.prediction_times:
            return 0.0
        sorted_times = sorted(self.prediction_times)
        index = int(0.99 * len(sorted_times))
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]

class MLMetrics:
    """
    🎯 Comprehensive metrics tracking for ML systems
    
    Features:
    - Model-specific metrics
    - System-wide metrics
    - Performance tracking
    - Cache monitoring
    - Thread-safe operations
    """
    
    def __init__(self):
        self._model_metrics: Dict[str, ModelMetrics] = {}
        self._system_metrics = {
            'total_predictions': 0,
            'total_errors': 0,
            'total_cache_hits': 0,
            'total_cache_misses': 0,
            'start_time': time.time(),
        }
        self._lock = threading.RLock()
        
        # System-wide performance tracking
        self._system_prediction_times = deque(maxlen=10000)
        self._hourly_stats = defaultdict(lambda: {
            'predictions': 0,
            'errors': 0,
            'total_time': 0.0
        })
        
    def _get_model_key(self, model_name: str, business_unit: str = 'default') -> str:
        """Generate unique key for model metrics"""
        return f"{business_unit}:{model_name}"
    
    def _ensure_model_metrics(self, model_name: str, business_unit: str = 'default') -> ModelMetrics:
        """Ensure model metrics exist"""
        key = self._get_model_key(model_name, business_unit)
        if key not in self._model_metrics:
            self._model_metrics[key] = ModelMetrics(
                model_name=model_name,
                business_unit=business_unit
            )
        return self._model_metrics[key]
    
    def record_prediction_time(self, model_name: str, execution_time: float, business_unit: str = 'default'):
        """Record prediction execution time"""
        with self._lock:
            model_metrics = self._ensure_model_metrics(model_name, business_unit)
            
            # Update model-specific metrics
            model_metrics.total_prediction_time += execution_time
            model_metrics.prediction_times.append(execution_time)
            model_metrics.last_used = time.time()
            
            # Update system-wide metrics
            self._system_prediction_times.append(execution_time)
            
            # Update hourly stats
            current_hour = int(time.time() // 3600)
            self._hourly_stats[current_hour]['total_time'] += execution_time
    
    def increment_prediction_count(self, model_name: str, business_unit: str = 'default'):
        """Increment prediction count for a model"""
        with self._lock:
            model_metrics = self._ensure_model_metrics(model_name, business_unit)
            model_metrics.prediction_count += 1
            model_metrics.last_used = time.time()
            
            # Update system metrics
            self._system_metrics['total_predictions'] += 1
            
            # Update hourly stats
            current_hour = int(time.time() // 3600)
            self._hourly_stats[current_hour]['predictions'] += 1
    
    def increment_error_count(self, model_name: str, business_unit: str = 'default'):
        """Increment error count for a model"""
        with self._lock:
            model_metrics = self._ensure_model_metrics(model_name, business_unit)
            model_metrics.error_count += 1
            model_metrics.last_used = time.time()
            
            # Update system metrics
            self._system_metrics['total_errors'] += 1
            
            # Update hourly stats
            current_hour = int(time.time() // 3600)
            self._hourly_stats[current_hour]['errors'] += 1
    
    def increment_cache_hit(self, model_name: str = None, business_unit: str = 'default'):
        """Increment cache hit count"""
        with self._lock:
            if model_name:
                model_metrics = self._ensure_model_metrics(model_name, business_unit)
                model_metrics.cache_hits += 1
            
            self._system_metrics['total_cache_hits'] += 1
    
    def increment_cache_miss(self, model_name: str = None, business_unit: str = 'default'):
        """Increment cache miss count"""
        with self._lock:
            if model_name:
                model_metrics = self._ensure_model_metrics(model_name, business_unit)
                model_metrics.cache_misses += 1
            
            self._system_metrics['total_cache_misses'] += 1
    
    def get_model_metrics(self, model_name: str, business_unit: str = 'default') -> Dict[str, Any]:
        """Get comprehensive metrics for a specific model"""
        with self._lock:
            key = self._get_model_key(model_name, business_unit)
            if key not in self._model_metrics:
                return {}
            
            metrics = self._model_metrics[key]
            return {
                'model_name': metrics.model_name,
                'business_unit': metrics.business_unit,
                'prediction_count': metrics.prediction_count,
                'error_count': metrics.error_count,
                'error_rate': round(metrics.error_rate, 2),
                'average_prediction_time': round(metrics.average_prediction_time, 2),
                'p95_prediction_time': round(metrics.p95_prediction_time, 2),
                'p99_prediction_time': round(metrics.p99_prediction_time, 2),
                'cache_hit_rate': round(metrics.cache_hit_rate, 2),
                'cache_hits': metrics.cache_hits,
                'cache_misses': metrics.cache_misses,
                'last_used': metrics.last_used,
                'last_used_ago': round(time.time() - metrics.last_used, 2),
                'recent_prediction_times': metrics.recent_prediction_times[-10:],  # Last 10
            }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        with self._lock:
            total_predictions = self._system_metrics['total_predictions']
            total_errors = self._system_metrics['total_errors']
            total_cache_hits = self._system_metrics['total_cache_hits']
            total_cache_misses = self._system_metrics['total_cache_misses']
            
            # Calculate system-wide rates
            total_operations = total_predictions + total_errors
            error_rate = (total_errors / total_operations * 100) if total_operations > 0 else 0
            
            total_cache_operations = total_cache_hits + total_cache_misses
            cache_hit_rate = (total_cache_hits / total_cache_operations * 100) if total_cache_operations > 0 else 0
            
            # Calculate average response time
            avg_response_time = statistics.mean(self._system_prediction_times) if self._system_prediction_times else 0
            
            # Calculate uptime
            uptime_seconds = time.time() - self._system_metrics['start_time']
            
            return {
                'total_predictions': total_predictions,
                'total_errors': total_errors,
                'error_rate': round(error_rate, 2),
                'total_cache_hits': total_cache_hits,
                'total_cache_misses': total_cache_misses,
                'cache_hit_rate': round(cache_hit_rate, 2),
                'average_response_time': round(avg_response_time, 2),
                'uptime_seconds': round(uptime_seconds, 2),
                'uptime_hours': round(uptime_seconds / 3600, 2),
                'registered_models': len(self._model_metrics),
                'active_models': len([m for m in self._model_metrics.values() if m.prediction_count > 0]),
                'requests_per_hour': round(total_predictions / (uptime_seconds / 3600), 2) if uptime_seconds > 0 else 0,
            }
    
    def get_business_unit_metrics(self, business_unit: str) -> Dict[str, Any]:
        """Get metrics for a specific business unit"""
        with self._lock:
            bu_models = {k: v for k, v in self._model_metrics.items() if v.business_unit == business_unit}
            
            if not bu_models:
                return {}
            
            total_predictions = sum(m.prediction_count for m in bu_models.values())
            total_errors = sum(m.error_count for m in bu_models.values())
            total_cache_hits = sum(m.cache_hits for m in bu_models.values())
            total_cache_misses = sum(m.cache_misses for m in bu_models.values())
            
            # Calculate rates
            total_operations = total_predictions + total_errors
            error_rate = (total_errors / total_operations * 100) if total_operations > 0 else 0
            
            total_cache_operations = total_cache_hits + total_cache_misses
            cache_hit_rate = (total_cache_hits / total_cache_operations * 100) if total_cache_operations > 0 else 0
            
            # Calculate average response time for this BU
            all_times = []
            for model in bu_models.values():
                all_times.extend(model.recent_prediction_times)
            
            avg_response_time = statistics.mean(all_times) if all_times else 0
            
            return {
                'business_unit': business_unit,
                'model_count': len(bu_models),
                'total_predictions': total_predictions,
                'total_errors': total_errors,
                'error_rate': round(error_rate, 2),
                'cache_hit_rate': round(cache_hit_rate, 2),
                'average_response_time': round(avg_response_time, 2),
                'models': {k.split(':', 1)[1]: self.get_model_metrics(v.model_name, business_unit) 
                          for k, v in bu_models.items()}
            }
    
    def get_hourly_stats(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get hourly statistics for the last N hours"""
        with self._lock:
            current_hour = int(time.time() // 3600)
            stats = []
            
            for i in range(hours):
                hour = current_hour - i
                hour_stats = self._hourly_stats.get(hour, {
                    'predictions': 0,
                    'errors': 0,
                    'total_time': 0.0
                })
                
                avg_time = (hour_stats['total_time'] / hour_stats['predictions']) if hour_stats['predictions'] > 0 else 0
                
                stats.append({
                    'hour': hour,
                    'timestamp': hour * 3600,
                    'predictions': hour_stats['predictions'],
                    'errors': hour_stats['errors'],
                    'average_time': round(avg_time, 2),
                    'error_rate': round((hour_stats['errors'] / (hour_stats['predictions'] + hour_stats['errors']) * 100), 2) if hour_stats['predictions'] + hour_stats['errors'] > 0 else 0
                })
            
            return list(reversed(stats))  # Most recent first
    
    def get_top_models(self, limit: int = 10, sort_by: str = 'prediction_count') -> List[Dict[str, Any]]:
        """Get top performing models"""
        with self._lock:
            models_data = []
            
            for key, metrics in self._model_metrics.items():
                model_data = self.get_model_metrics(metrics.model_name, metrics.business_unit)
                models_data.append(model_data)
            
            # Sort by specified metric
            if sort_by in ['prediction_count', 'error_rate', 'average_prediction_time', 'cache_hit_rate']:
                reverse = sort_by in ['prediction_count', 'cache_hit_rate']  # Higher is better for these
                models_data.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
            
            return models_data[:limit]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a comprehensive performance summary"""
        with self._lock:
            system_metrics = self.get_system_metrics()
            
            # Get business unit breakdown
            business_units = set(m.business_unit for m in self._model_metrics.values())
            bu_metrics = {bu: self.get_business_unit_metrics(bu) for bu in business_units}
            
            # Get top models
            top_by_usage = self.get_top_models(5, 'prediction_count')
            top_by_performance = self.get_top_models(5, 'average_prediction_time')
            
            return {
                'system': system_metrics,
                'business_units': bu_metrics,
                'top_models_by_usage': top_by_usage,
                'top_models_by_performance': top_by_performance,
                'hourly_trends': self.get_hourly_stats(24),
                'timestamp': time.time()
            }
    
    def reset_metrics(self, model_name: str = None, business_unit: str = None):
        """Reset metrics for a specific model or all models"""
        with self._lock:
            if model_name and business_unit:
                # Reset specific model
                key = self._get_model_key(model_name, business_unit)
                if key in self._model_metrics:
                    del self._model_metrics[key]
            else:
                # Reset all metrics
                self._model_metrics.clear()
                self._system_metrics = {
                    'total_predictions': 0,
                    'total_errors': 0,
                    'total_cache_hits': 0,
                    'total_cache_misses': 0,
                    'start_time': time.time(),
                }
                self._system_prediction_times.clear()
                self._hourly_stats.clear()
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for external monitoring systems"""
        with self._lock:
            return {
                'system_metrics': self.get_system_metrics(),
                'model_metrics': {k: self.get_model_metrics(v.model_name, v.business_unit) 
                                for k, v in self._model_metrics.items()},
                'hourly_stats': self.get_hourly_stats(168),  # Last week
                'export_timestamp': time.time()
            }
    
    # Convenience properties
    def get_cache_hit_rate(self) -> float:
        """Get overall cache hit rate"""
        total_hits = self._system_metrics['total_cache_hits']
        total_misses = self._system_metrics['total_cache_misses']
        total = total_hits + total_misses
        return (total_hits / total * 100) if total > 0 else 0
    
    def get_total_predictions(self) -> int:
        """Get total number of predictions"""
        return self._system_metrics['total_predictions']
    
    def get_average_response_time(self) -> float:
        """Get average response time"""
        return statistics.mean(self._system_prediction_times) if self._system_prediction_times else 0
    
    def get_error_rate(self) -> float:
        """Get overall error rate"""
        total_predictions = self._system_metrics['total_predictions']
        total_errors = self._system_metrics['total_errors']
        total = total_predictions + total_errors
        return (total_errors / total * 100) if total > 0 else 0

# Export main components
__all__ = [
    'MLMetrics',
    'ModelMetrics'
]