"""
Enhanced logging system for integrations.
Provides structured logging with different levels and handlers.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from django.conf import settings
import os

class IntegrationLogger:
    """
    Enhanced logger for integration events and errors.
    Provides structured logging with different levels and handlers.
    """
    
    def __init__(self, name: str):
        """
        Initialize the logger with a specific name.
        
        Args:
            name: Logger name (usually module name)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(settings.BASE_DIR, 'logs', 'integrations')
        os.makedirs(logs_dir, exist_ok=True)
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            os.path.join(logs_dir, f'{name}.log'),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # File handler for errors only
        error_handler = logging.FileHandler(
            os.path.join(logs_dir, f'{name}_error.log'),
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'File: %(pathname)s:%(lineno)d\n'
            'Function: %(funcName)s\n'
            'Message: %(message)s'
        )
        
        # Set formatters
        file_handler.setFormatter(file_formatter)
        error_handler.setFormatter(error_formatter)
        console_handler.setFormatter(file_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def _format_log_data(self, event_type: str, data: Dict[str, Any]) -> str:
        """
        Format log data as JSON string.
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            str: Formatted log data
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'data': data
        }
        return json.dumps(log_data, ensure_ascii=False)
    
    def info(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log info level message.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        self.logger.info(self._format_log_data(event_type, data))
    
    def error(self, event_type: str, data: Dict[str, Any], exc_info: bool = True) -> None:
        """
        Log error level message.
        
        Args:
            event_type: Type of event
            data: Event data
            exc_info: Whether to include exception info
        """
        self.logger.error(
            self._format_log_data(event_type, data),
            exc_info=exc_info
        )
    
    def warning(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log warning level message.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        self.logger.warning(self._format_log_data(event_type, data))
    
    def debug(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log debug level message.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        self.logger.debug(self._format_log_data(event_type, data))

def get_integration_logger(name: str) -> IntegrationLogger:
    """
    Get an integration logger instance.
    
    Args:
        name: Logger name (usually module name)
        
    Returns:
        IntegrationLogger: Logger instance
    """
    return IntegrationLogger(name) 