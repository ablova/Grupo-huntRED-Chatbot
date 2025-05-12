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

from app.lazy_imports import LazyImporter, LazyModule

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
        base_module = importlib.import_module(base_package)
        base_path = os.path.dirname(base_module.__file__)

        for _, module_name, _ in pkgutil.walk_packages([base_path], prefix=base_package + '.'):
            # Skip test modules and private modules
            if module_name.endswith('.tests') or module_name.split('.')[-1].startswith('_'):
                continue

            # Create a loader for each module
            def create_loader(full_module_name: str) -> Callable[[], object]:
                def loader():
                    return importlib.import_module(full_module_name)
                return loader

            self._importer.register(module_name, create_loader(module_name))
            self._modules[module_name] = module_name

    def get_module(self, module_name: str) -> Optional[LazyModule]:
        """Get a lazy-loaded module by name.

        Args:
            module_name: The full name of the module to load.

        Returns:
            A LazyModule instance if registered, None otherwise.
        """
        return self._importer.get(module_name)

    def list_registered_modules(self) -> list[str]:
        """List all registered module names.

        Returns:
            A sorted list of registered module names.
        """
        return sorted(self._modules.keys())

# Create a singleton instance
_REGISTRY = ModuleRegistry()

# Public API
def auto_register_modules(base_package: str = 'app') -> None:
    """Automatically register all modules in the project.

    Args:
        base_package: The base package to start the scan from. Defaults to 'app'.
    """
    _REGISTRY.auto_register(base_package)

def get_module(module_name: str) -> Optional[LazyModule]:
    """Get a lazy-loaded module by name.

    Args:
        module_name: The full name of the module to load.

    Returns:
        A LazyModule instance if registered, None otherwise.
    """
    return _REGISTRY.get_module(module_name)

def list_modules() -> list[str]:
    """List all registered module names.

    Returns:
        A sorted list of registered module names.
    """
    return _REGISTRY.list_registered_modules()
