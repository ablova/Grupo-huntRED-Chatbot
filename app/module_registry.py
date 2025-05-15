# /home/pablo/app/module_registry.py
"""
Module Registry for Lazy Loading

This module provides a centralized registry for lazy loading of application modules
to improve startup performance.
"""

import importlib
import os
import pkgutil
import sys
from typing import Callable, Dict, Optional, TypeVar
import logging
from app.lazy_imports import LazyImporter, LazyModule

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ModuleRegistry:
    """Central registry for managing lazy loading of modules."""

    def __init__(self):
        self._importer = LazyImporter()
        self._modules: Dict[str, str] = {}
        self._base_path = os.path.dirname(os.path.abspath(__file__))

    def auto_register(self, base_package: str = 'app') -> None:
        """Automatically register all modules within the specified package.

        Args:
            base_package: The base package to start the scan from. Defaults to 'app'.
        """
        try:
            base_module = importlib.import_module(base_package)
            base_path = os.path.dirname(base_module.__file__)

            for _, module_name, _ in pkgutil.walk_packages([base_path], prefix=base_package + '.'):
                # Skip test modules and private modules
                if module_name.endswith('.tests') or module_name.split('.')[-1].startswith('_'):
                    continue

                self._importer.register(module_name, module_name)
                self._modules[module_name] = module_name

        except Exception as e:
            logger.error(f"Error auto-registering modules: {str(e)}")

    def get_module(self, module_name: str) -> Optional[LazyModule]:
        """Get a lazy-loaded module by name.

        Args:
            module_name: The name of the module to retrieve.

        Returns:
            Optional[LazyModule]: The lazy-loaded module or None if not found.
        """
        return self._importer.get_module(module_name)

    def register_module(self, name: str, module_path: str) -> None:
        """Register a module for lazy loading.

        Args:
            name: The name to use when accessing the module
            module_path: The full module path (e.g., 'app.com.chatbot.chatbot')
        """
        if name in self._modules:
            logger.warning(f"Module {name} already registered")
            return
        
        self._importer.register(name, module_path)
        self._modules[name] = module_path

    def get(self, name: str, attr: str) -> any:
        """Get an attribute from a registered module.

        Args:
            name: The name of the module
            attr: The attribute to get from the module

        Returns:
            Any: The requested attribute or None if not found
        """
        return self._importer.get(name, attr)

# Create a singleton instance
_REGISTRY = ModuleRegistry()

# Public API
def auto_register_modules(base_package: str = 'app') -> None:
    """Automatically register all modules in the project.

    Args:
        base_package: The base package to start the scan from. Defaults to 'app'.
    """
    _REGISTRY.auto_register(base_package)

def get_module(module_name: str) -> Optional[object]:
    """Get a module by name.

    Args:
        module_name: The name of the module to retrieve.

    Returns:
        Optional[object]: The module or None if not found.
    """
    return _REGISTRY.get_module(module_name)

def list_modules() -> list[str]:
    """List all registered module names.

    Returns:
        A sorted list of registered module names.
    """
    return _REGISTRY.list_registered_modules()
