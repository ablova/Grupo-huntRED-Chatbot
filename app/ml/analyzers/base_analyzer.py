# /home/pablo/app/ml/analyzers/base_analyzer.py
"""
Base Analyzer module for Grupo huntRED® assessment system.

This module provides the abstract base class for all analyzers in the ML system.
All specialized analyzers (personality, cultural, professional, talent) must inherit from this class.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from django.core.cache import cache

from app.models import BusinessUnit  # Usando la importación centralizada

logger = logging.getLogger(__name__)

class BaseAnalyzer(ABC):
    """
    Base abstract class for all assessment analyzers.
    
    Provides common functionality for:
    - Caching
    - Error handling
    - Logging
    - Business Unit context
    
    All specialized analyzers must implement the analyze method.
    """
    
    def __init__(self):
        """Initialize the analyzer with default cache timeout."""
        self.cache_timeout = 3600  # 1 hour (in seconds)
        
    @abstractmethod
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analyze the provided data in the context of a business unit.
        
        Args:
            data: Dictionary containing assessment data to analyze
            business_unit: Optional business unit for contextual analysis
            
        Returns:
            Dict containing analysis results
        """
        pass
        
    def get_cache_key(self, data: Dict, prefix: str = "analysis") -> str:
        """
        Generate a cache key for the given data.
        
        Args:
            data: Input data to generate key for
            prefix: Optional prefix for the key
            
        Returns:
            A unique cache key as string
        """
        # Generate a hash based on significant data points
        # This avoids using the entire data dictionary which could be large
        key_components = []
        
        # Use id if available
        if 'id' in data:
            key_components.append(str(data['id']))
            
        # Use user_id if available
        if 'user_id' in data:
            key_components.append(str(data['user_id']))
            
        # Use assessment_type if available
        if 'assessment_type' in data:
            key_components.append(data['assessment_type'])
            
        # Add timestamp if available to handle updates
        if 'timestamp' in data:
            key_components.append(str(data['timestamp']))
            
        # If no identifying components found, use hash of stringified data
        if not key_components:
            key_components.append(str(hash(str(data))))
            
        # Join components and create final key
        return f"{prefix}_{'-'.join(key_components)}"
        
    def get_cached_result(self, data: Dict, prefix: str = "analysis") -> Optional[Dict]:
        """
        Retrieve cached analysis result if available.
        
        Args:
            data: Input data to check cache for
            prefix: Optional prefix for the cache key
            
        Returns:
            Cached result or None if not found
        """
        cache_key = self.get_cache_key(data, prefix)
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Using cached {prefix} for {cache_key}")
            return cached_result
            
        return None
        
    def set_cached_result(self, data: Dict, result: Dict, prefix: str = "analysis") -> None:
        """
        Cache analysis result for future use.
        
        Args:
            data: Input data that was analyzed
            result: Analysis result to cache
            prefix: Optional prefix for the cache key
        """
        try:
            cache_key = self.get_cache_key(data, prefix)
            cache.set(cache_key, result, self.cache_timeout)
            logger.debug(f"Cached {prefix} result for {cache_key}")
        except Exception as e:
            logger.error(f"Error caching {prefix} result: {str(e)}")
            
    def get_default_result(self, error_message: str = "") -> Dict:
        """
        Provide a default result in case of analysis failure.
        
        Args:
            error_message: Optional error message to include
            
        Returns:
            A minimal valid result dictionary
        """
        return {
            'status': 'error',
            'message': error_message or 'An error occurred during analysis',
            'data': {
                'note': 'This is a default result due to an error in the analysis process',
                'recommendations': [
                    'Try again with more complete information',
                    'Contact support if the problem persists'
                ]
            }
        }
        
    def validate_input(self, data: Dict) -> Tuple[bool, str]:
        """
        Validate that input data has the minimum required fields.
        
        Args:
            data: Input data to validate
            
        Returns:
            (is_valid, error_message) tuple
        """
        if not data:
            return False, "Input data is empty"
            
        required_fields = self.get_required_fields()
        
        for field in required_fields:
            if field not in data:
                return False, f"Required field '{field}' is missing"
                
        return True, ""
        
    def get_required_fields(self) -> List[str]:
        """
        Get the list of required fields for this analyzer.
        Override in subclasses to specify analyzer-specific requirements.
        
        Returns:
            List of required field names
        """
        # Base implementation requires minimal fields
        # Subclasses should override with their specific requirements
        return ['assessment_type']
        
    def get_business_unit_name(self, business_unit: Optional[Any]) -> str:
        """
        Extract the business unit name from various input types.
        
        Args:
            business_unit: BusinessUnit object, string, or dict
            
        Returns:
            Business unit name as string
        """
        if business_unit is None:
            return "default"
            
        if isinstance(business_unit, str):
            return business_unit
            
        if isinstance(business_unit, BusinessUnit):
            return business_unit.name
            
        if isinstance(business_unit, dict) and 'name' in business_unit:
            return business_unit['name']
            
        # Fallback to string representation
        return str(business_unit)
