"""
🚀 GhuntRED-v2 ML Metrics
Performance tracking and monitoring for ML operations
"""

import time
import threading
from typing import Dict, List
from collections import defaultdict, deque

class MLMetrics:
    """Thread-safe metrics tracking for ML operations"""
    
    _lock = threading.Lock()
    _analysis_times = defaultdict(deque)  # Store last 100 analysis times per type
    _analysis_counts = defaultdict(int)
    _error_counts = defaultdict(int)
    
    @classmethod
    def record_analysis(cls, analysis_type: str, execution_time: float):
        """Record analysis execution time"""
        with cls._lock:
            cls._analysis_times[analysis_type].append(execution_time)
            # Keep only last 100 measurements
            if len(cls._analysis_times[analysis_type]) > 100:
                cls._analysis_times[analysis_type].popleft()
            cls._analysis_counts[analysis_type] += 1
    
    @classmethod
    def record_error(cls, analysis_type: str):
        """Record analysis error"""
        with cls._lock:
            cls._error_counts[analysis_type] += 1
    
    @classmethod
    def get_metrics(cls) -> dict:
        """Get aggregated metrics"""
        with cls._lock:
            metrics = {
                'analysis_types': {},
                'overall': {
                    'total_analyses': sum(cls._analysis_counts.values()),
                    'total_errors': sum(cls._error_counts.values()),
                }
            }
            
            for analysis_type, times in cls._analysis_times.items():
                if times:
                    metrics['analysis_types'][analysis_type] = {
                        'count': cls._analysis_counts[analysis_type],
                        'errors': cls._error_counts[analysis_type],
                        'avg_time': sum(times) / len(times),
                        'min_time': min(times),
                        'max_time': max(times),
                        'error_rate': cls._error_counts[analysis_type] / cls._analysis_counts[analysis_type] if cls._analysis_counts[analysis_type] > 0 else 0,
                    }
            
            return metrics