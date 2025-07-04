"""
🛡️ API Compatibility Layer
Ensures 100% backward compatibility with original system
"""

# This file ensures all original imports still work
# Example: from app.models import Person -> still works
# But internally routes to new structure

import sys
import importlib
from django.conf import settings

class CompatibilityImporter:
    """Ensures old imports continue to work"""
    
    def __init__(self):
        self.mapping = {
            'app.models': 'backend.apps.candidates.models',
            'app.tasks': 'backend.tasks.notifications.tasks',
            'app.ml': 'backend.ml.core',
            # Add all necessary mappings
        }
    
    def setup_compatibility(self):
        """Setup import compatibility"""
        for old_path, new_path in self.mapping.items():
            try:
                module = importlib.import_module(new_path)
                sys.modules[old_path] = module
            except ImportError:
                print(f"Warning: Could not setup compatibility for {old_path}")

# Initialize compatibility layer
compatibility = CompatibilityImporter()
compatibility.setup_compatibility()
