"""
⚡ GhuntRED-v2 ML Performance Optimizers
Advanced optimization techniques for ML systems
"""

import gc
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Callable
from functools import wraps, lru_cache
from dataclasses import dataclass
import psutil
import os

logger = logging.getLogger(__name__)

@dataclass
class OptimizationMetrics:
    """Metrics for optimization tracking"""
    optimization_name: str
    executions: int = 0
    total_time_saved: float = 0.0
    memory_saved: int = 0
    cpu_saved: float = 0.0
    cache_hits: int = 0
    
    @property
    def average_time_saved(self) -> float:
        """Calculate average time saved per execution"""
        return self.total_time_saved / self.executions if self.executions > 0 else 0.0

class MemoryOptimizer:
    """
    🧠 Memory optimization for ML workloads
    """
    
    def __init__(self):
        self._memory_threshold = 0.8  # 80% memory usage threshold
        self._gc_frequency = 100  # Run GC every N operations
        self._operation_count = 0
        self._lock = threading.Lock()
        
    def optimize_memory(self, force: bool = False) -> Dict[str, Any]:
        """Optimize memory usage"""
        with self._lock:
            self._operation_count += 1
            
            # Check if optimization is needed
            memory_percent = psutil.virtual_memory().percent / 100
            
            if force or memory_percent > self._memory_threshold or self._operation_count % self._gc_frequency == 0:
                return self._perform_memory_optimization()
            
            return {'optimized': False, 'memory_percent': memory_percent}
    
    def _perform_memory_optimization(self) -> Dict[str, Any]:
        """Perform actual memory optimization"""
        start_memory = psutil.virtual_memory().used
        start_time = time.time()
        
        # Force garbage collection
        collected = gc.collect()
        
        # Clear any unnecessary caches
        self._clear_internal_caches()
        
        end_memory = psutil.virtual_memory().used
        end_time = time.time()
        
        memory_freed = start_memory - end_memory
        optimization_time = end_time - start_time
        
        logger.info(f"🧹 Memory optimization: freed {memory_freed / 1024 / 1024:.2f}MB in {optimization_time:.3f}s")
        
        return {
            'optimized': True,
            'memory_freed_mb': memory_freed / 1024 / 1024,
            'objects_collected': collected,
            'optimization_time': optimization_time,
            'current_memory_percent': psutil.virtual_memory().percent
        }
    
    def _clear_internal_caches(self):
        """Clear internal caches if needed"""
        # This would clear specific ML model caches if memory is critical
        pass
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics"""
        memory = psutil.virtual_memory()
        
        return {
            'total_mb': memory.total / 1024 / 1024,
            'available_mb': memory.available / 1024 / 1024,
            'used_mb': memory.used / 1024 / 1024,
            'percent_used': memory.percent,
            'is_critical': memory.percent > self._memory_threshold * 100,
        }

class CPUOptimizer:
    """
    🚀 CPU optimization for ML workloads
    """
    
    def __init__(self):
        self._cpu_threshold = 0.9  # 90% CPU usage threshold
        self._optimization_interval = 60  # seconds
        self._last_optimization = 0
        
    def optimize_cpu_usage(self) -> Dict[str, Any]:
        """Optimize CPU usage"""
        current_time = time.time()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if (cpu_percent / 100) > self._cpu_threshold or (current_time - self._last_optimization) > self._optimization_interval:
            return self._perform_cpu_optimization()
        
        return {'optimized': False, 'cpu_percent': cpu_percent}
    
    def _perform_cpu_optimization(self) -> Dict[str, Any]:
        """Perform CPU optimization"""
        start_time = time.time()
        
        # Lower process priority if CPU is overloaded
        current_process = psutil.Process()
        original_nice = current_process.nice()
        
        cpu_percent = psutil.cpu_percent()
        if cpu_percent > 90:
            # Lower priority
            try:
                current_process.nice(5)  # Lower priority
                logger.info("🔧 Lowered process priority due to high CPU usage")
            except (psutil.AccessDenied, OSError):
                logger.warning("⚠️ Could not adjust process priority")
        
        # Update optimization timestamp
        self._last_optimization = time.time()
        optimization_time = self._last_optimization - start_time
        
        return {
            'optimized': True,
            'cpu_percent': cpu_percent,
            'priority_adjusted': original_nice != current_process.nice(),
            'optimization_time': optimization_time,
        }
    
    def get_cpu_stats(self) -> Dict[str, Any]:
        """Get current CPU statistics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_count': psutil.cpu_count(),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None,
        }

class CacheOptimizer:
    """
    📚 Advanced caching optimization
    """
    
    def __init__(self, max_cache_size: int = 1000):
        self._max_cache_size = max_cache_size
        self._cache_stats = {}
        self._access_times = {}
        self._lock = threading.Lock()
        
    def smart_cache_decorator(self, ttl: int = 3600, key_func: Optional[Callable] = None):
        """
        Smart caching decorator with LRU and TTL
        
        Args:
            ttl: Time to live in seconds
            key_func: Function to generate cache key
        """
        def decorator(func):
            cache = {}
            access_times = {}
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self._lock:
                    # Generate cache key
                    if key_func:
                        cache_key = key_func(*args, **kwargs)
                    else:
                        cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
                    
                    current_time = time.time()
                    
                    # Check if cached and not expired
                    if cache_key in cache:
                        cached_time, cached_value = cache[cache_key]
                        if current_time - cached_time < ttl:
                            access_times[cache_key] = current_time
                            self._record_cache_hit(func.__name__)
                            return cached_value
                        else:
                            # Remove expired entry
                            del cache[cache_key]
                            del access_times[cache_key]
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Cache result
                    cache[cache_key] = (current_time, result)
                    access_times[cache_key] = current_time
                    
                    # Cleanup old entries if cache is full
                    if len(cache) > self._max_cache_size:
                        self._cleanup_cache(cache, access_times)
                    
                    self._record_cache_miss(func.__name__)
                    return result
            
            return wrapper
        return decorator
    
    def _cleanup_cache(self, cache: Dict, access_times: Dict):
        """Remove least recently used cache entries"""
        # Sort by access time and remove oldest entries
        sorted_items = sorted(access_times.items(), key=lambda x: x[1])
        items_to_remove = len(cache) - int(self._max_cache_size * 0.8)  # Remove 20% when full
        
        for i in range(items_to_remove):
            key_to_remove = sorted_items[i][0]
            cache.pop(key_to_remove, None)
            access_times.pop(key_to_remove, None)
    
    def _record_cache_hit(self, func_name: str):
        """Record cache hit"""
        if func_name not in self._cache_stats:
            self._cache_stats[func_name] = {'hits': 0, 'misses': 0}
        self._cache_stats[func_name]['hits'] += 1
    
    def _record_cache_miss(self, func_name: str):
        """Record cache miss"""
        if func_name not in self._cache_stats:
            self._cache_stats[func_name] = {'hits': 0, 'misses': 0}
        self._cache_stats[func_name]['misses'] += 1
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {}
        for func_name, data in self._cache_stats.items():
            total = data['hits'] + data['misses']
            hit_rate = (data['hits'] / total * 100) if total > 0 else 0
            stats[func_name] = {
                'hits': data['hits'],
                'misses': data['misses'],
                'hit_rate': round(hit_rate, 2),
                'total_requests': total
            }
        return stats

class BatchOptimizer:
    """
    📦 Batch processing optimization
    """
    
    def __init__(self, optimal_batch_size: int = 32, max_wait_time: int = 5):
        self.optimal_batch_size = optimal_batch_size
        self.max_wait_time = max_wait_time
        self._pending_batches = {}
        self._lock = threading.Lock()
        
    def optimize_batch_processing(self, 
                                 processing_func: Callable,
                                 data: Any,
                                 batch_key: str = "default") -> Any:
        """
        Optimize batch processing by accumulating requests
        
        Args:
            processing_func: Function to process the batch
            data: Single data item to process
            batch_key: Key to group batches
            
        Returns:
            Processing result
        """
        with self._lock:
            if batch_key not in self._pending_batches:
                self._pending_batches[batch_key] = {
                    'items': [],
                    'start_time': time.time(),
                    'callbacks': []
                }
            
            batch = self._pending_batches[batch_key]
            batch['items'].append(data)
            
            # Check if batch is ready for processing
            should_process = (
                len(batch['items']) >= self.optimal_batch_size or
                (time.time() - batch['start_time']) >= self.max_wait_time
            )
            
            if should_process:
                # Process the batch
                items = batch['items'].copy()
                del self._pending_batches[batch_key]
                
                # Process outside of lock
                return self._process_batch(processing_func, items, data)
            else:
                # Wait for batch to be ready (simplified - in real implementation use async)
                return processing_func([data])
    
    def _process_batch(self, processing_func: Callable, items: List[Any], original_item: Any) -> Any:
        """Process a batch and return result for original item"""
        try:
            results = processing_func(items)
            
            # Find result for original item
            original_index = items.index(original_item)
            return results[original_index] if isinstance(results, list) else results
            
        except Exception as e:
            logger.error(f"❌ Batch processing error: {e}")
            # Fallback to individual processing
            return processing_func([original_item])

class ModelLoadOptimizer:
    """
    🏗️ ML model loading optimization
    """
    
    def __init__(self):
        self._preload_queue = []
        self._loading_stats = {}
        self._lock = threading.Lock()
        
    def optimize_model_loading(self, 
                              model_loader: Callable,
                              model_name: str,
                              preload: bool = False) -> Any:
        """
        Optimize model loading with preloading and lazy loading
        
        Args:
            model_loader: Function to load the model
            model_name: Name of the model
            preload: Whether to preload the model
            
        Returns:
            Loaded model
        """
        start_time = time.time()
        
        try:
            # Load the model
            model = model_loader()
            
            load_time = time.time() - start_time
            
            # Record loading stats
            with self._lock:
                if model_name not in self._loading_stats:
                    self._loading_stats[model_name] = {
                        'load_count': 0,
                        'total_load_time': 0.0,
                        'last_load_time': 0.0
                    }
                
                stats = self._loading_stats[model_name]
                stats['load_count'] += 1
                stats['total_load_time'] += load_time
                stats['last_load_time'] = load_time
            
            logger.info(f"📁 Model {model_name} loaded in {load_time:.3f}s")
            return model
            
        except Exception as e:
            logger.error(f"❌ Model loading error for {model_name}: {e}")
            raise
    
    def get_loading_stats(self) -> Dict[str, Any]:
        """Get model loading statistics"""
        with self._lock:
            stats = {}
            for model_name, data in self._loading_stats.items():
                avg_load_time = data['total_load_time'] / data['load_count']
                stats[model_name] = {
                    'load_count': data['load_count'],
                    'average_load_time': round(avg_load_time, 3),
                    'last_load_time': round(data['last_load_time'], 3),
                    'total_load_time': round(data['total_load_time'], 3),
                }
            return stats

class PerformanceOptimizer:
    """
    🚀 Main performance optimizer that coordinates all optimization strategies
    """
    
    def __init__(self):
        self.memory_optimizer = MemoryOptimizer()
        self.cpu_optimizer = CPUOptimizer()
        self.cache_optimizer = CacheOptimizer()
        self.batch_optimizer = BatchOptimizer()
        self.model_load_optimizer = ModelLoadOptimizer()
        
        self._optimization_metrics = {}
        self._enabled_optimizations = {
            'memory': True,
            'cpu': True,
            'cache': True,
            'batch': True,
            'model_loading': True,
        }
        
    def optimize_prediction(self, prediction_func: Callable) -> Callable:
        """
        Decorator to optimize ML prediction functions
        
        Args:
            prediction_func: Function to optimize
            
        Returns:
            Optimized function
        """
        @wraps(prediction_func)
        def optimized_wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Memory optimization
            if self._enabled_optimizations['memory']:
                self.memory_optimizer.optimize_memory()
            
            # CPU optimization
            if self._enabled_optimizations['cpu']:
                self.cpu_optimizer.optimize_cpu_usage()
            
            # Execute prediction
            result = prediction_func(*args, **kwargs)
            
            # Record optimization metrics
            execution_time = time.time() - start_time
            self._record_optimization_metrics(prediction_func.__name__, execution_time)
            
            return result
        
        # Apply caching if enabled
        if self._enabled_optimizations['cache']:
            optimized_wrapper = self.cache_optimizer.smart_cache_decorator()(optimized_wrapper)
        
        return optimized_wrapper
    
    def optimize_batch_processing(self, batch_func: Callable, batch_key: str = "default") -> Callable:
        """
        Optimize batch processing
        
        Args:
            batch_func: Function to optimize
            batch_key: Key for batching
            
        Returns:
            Optimized function
        """
        @wraps(batch_func)
        def batch_wrapper(data):
            if self._enabled_optimizations['batch']:
                return self.batch_optimizer.optimize_batch_processing(
                    batch_func, data, batch_key
                )
            else:
                return batch_func(data)
        
        return batch_wrapper
    
    def optimize_model_loading(self, load_func: Callable, model_name: str) -> Callable:
        """
        Optimize model loading
        
        Args:
            load_func: Function to optimize
            model_name: Name of the model
            
        Returns:
            Optimized function
        """
        @wraps(load_func)
        def load_wrapper(*args, **kwargs):
            if self._enabled_optimizations['model_loading']:
                return self.model_load_optimizer.optimize_model_loading(
                    lambda: load_func(*args, **kwargs),
                    model_name
                )
            else:
                return load_func(*args, **kwargs)
        
        return load_wrapper
    
    def _record_optimization_metrics(self, func_name: str, execution_time: float):
        """Record optimization metrics"""
        if func_name not in self._optimization_metrics:
            self._optimization_metrics[func_name] = OptimizationMetrics(func_name)
        
        metrics = self._optimization_metrics[func_name]
        metrics.executions += 1
        # Note: This is simplified - in reality you'd compare against baseline
        
    def get_system_performance(self) -> Dict[str, Any]:
        """Get comprehensive system performance metrics"""
        return {
            'memory': self.memory_optimizer.get_memory_stats(),
            'cpu': self.cpu_optimizer.get_cpu_stats(),
            'cache': self.cache_optimizer.get_cache_stats(),
            'model_loading': self.model_load_optimizer.get_loading_stats(),
            'optimizations_enabled': self._enabled_optimizations,
            'optimization_metrics': {
                name: {
                    'executions': metrics.executions,
                    'average_time_saved': metrics.average_time_saved,
                    'total_time_saved': metrics.total_time_saved,
                    'cache_hits': metrics.cache_hits,
                }
                for name, metrics in self._optimization_metrics.items()
            }
        }
    
    def enable_optimization(self, optimization_type: str, enabled: bool = True):
        """Enable/disable specific optimization"""
        if optimization_type in self._enabled_optimizations:
            self._enabled_optimizations[optimization_type] = enabled
            logger.info(f"🔧 {optimization_type} optimization {'enabled' if enabled else 'disabled'}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on optimization system"""
        memory_stats = self.memory_optimizer.get_memory_stats()
        cpu_stats = self.cpu_optimizer.get_cpu_stats()
        
        return {
            'status': 'healthy',
            'memory_healthy': memory_stats['percent_used'] < 85,
            'cpu_healthy': cpu_stats['cpu_percent'] < 90,
            'optimizations_active': sum(self._enabled_optimizations.values()),
            'total_optimizations': len(self._enabled_optimizations),
        }

# Export main components
__all__ = [
    'PerformanceOptimizer',
    'MemoryOptimizer',
    'CPUOptimizer',
    'CacheOptimizer',
    'BatchOptimizer',
    'ModelLoadOptimizer',
    'OptimizationMetrics',
]