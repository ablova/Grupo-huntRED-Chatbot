"""
huntRED® v2 - Base Task Utilities
Core utilities for Celery task system
"""

import logging
import functools
from typing import Any, Callable, Optional
from celery import shared_task
from celery.exceptions import Retry
import time

# Configure task logger
task_logger = logging.getLogger('huntred.tasks')

def with_retry(
    max_retries: int = 3,
    default_retry_delay: int = 60,
    backoff: bool = True,
    jitter: bool = True
):
    """
    Decorator for adding retry logic to Celery tasks.
    
    Args:
        max_retries: Maximum number of retry attempts
        default_retry_delay: Default delay between retries in seconds
        backoff: Whether to use exponential backoff
        jitter: Whether to add random jitter to delay
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as exc:
                if self.request.retries < max_retries:
                    delay = default_retry_delay
                    
                    if backoff:
                        delay *= (2 ** self.request.retries)
                    
                    if jitter:
                        import random
                        delay += random.uniform(0, 30)
                    
                    task_logger.warning(
                        f"Task {func.__name__} failed (attempt {self.request.retries + 1}/{max_retries + 1}). "
                        f"Retrying in {delay} seconds. Error: {str(exc)}"
                    )
                    
                    raise self.retry(exc=exc, countdown=delay)
                else:
                    task_logger.error(
                        f"Task {func.__name__} failed permanently after {max_retries} retries. "
                        f"Final error: {str(exc)}"
                    )
                    raise exc
        
        return wrapper
    return decorator


class TaskMetrics:
    """Class for tracking task execution metrics"""
    
    @staticmethod
    def track_execution_time(func: Callable) -> Callable:
        """Decorator to track task execution time"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                task_logger.info(
                    f"Task {func.__name__} completed successfully in {execution_time:.2f} seconds"
                )
                return result
            except Exception as exc:
                execution_time = time.time() - start_time
                task_logger.error(
                    f"Task {func.__name__} failed after {execution_time:.2f} seconds. Error: {str(exc)}"
                )
                raise exc
        return wrapper
    
    @staticmethod
    def log_task_info(task_name: str, **kwargs):
        """Log task execution information"""
        task_logger.info(f"Starting task: {task_name}", extra=kwargs)


def get_business_unit(business_unit_id: Optional[int] = None, default_name: str = "huntRED"):
    """
    Utility function to get BusinessUnit instance.
    Migrated from original system for compatibility.
    """
    from ..models.company import Company
    
    if business_unit_id:
        try:
            # In our new system, we'll use Company model as equivalent to BusinessUnit
            return Company.query.filter_by(id=business_unit_id).first()
        except:
            task_logger.error(f"BusinessUnit with ID {business_unit_id} not found")
            return None
    else:
        # Get default business unit
        try:
            return Company.query.filter_by(name=default_name).first()
        except:
            task_logger.error(f"Default BusinessUnit '{default_name}' not found")
            return None


@shared_task
def health_check_task():
    """Basic health check task for monitoring"""
    task_logger.info("Health check task executed successfully")
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "message": "huntRED® v2 task system operational"
    }


@shared_task
def simple_add_task(x: int, y: int) -> int:
    """Simple addition task for testing"""
    result = x + y
    task_logger.info(f"Addition task: {x} + {y} = {result}")
    return result