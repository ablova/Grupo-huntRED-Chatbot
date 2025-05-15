# /home/pablo/app/lazy_imports.py
import importlib
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

class LazyModule:
    def __init__(self, module_name: str):
        self._module_name = module_name
        self._module = None
        self._initialized = False

    def __getattr__(self, name: str) -> Any:
        if not self._initialized:
            try:
                self._module = importlib.import_module(self._module_name)
                self._initialized = True
            except ImportError as e:
                logger.error(f"Error importing {self._module_name}: {str(e)}")
                raise
        return getattr(self._module, name)

class LazyImporter:
    def __init__(self):
        self._modules = {}

    def register(self, name: str, module_path: str) -> None:
        """
        Register a module for lazy loading.
        
        Args:
            name: The name to use when accessing the module
            module_path: The full module path (e.g., 'app.com.chatbot.chatbot')
        """
        if name in self._modules:
            logger.warning(f"Module {name} already registered")
            return
        self._modules[name] = LazyModule(module_path)

    def get_module(self, name: str) -> Optional[LazyModule]:
        """Get a registered module."""
        return self._modules.get(name)

    def get(self, name: str, attr: str) -> Any:
        """Get an attribute from a registered module."""
        module = self._modules.get(name)
        if module:
            return getattr(module, attr)
        return None
