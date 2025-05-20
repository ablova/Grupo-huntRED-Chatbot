# /home/pablo/app/lazy_imports.py
#
# Sistema de importación perezosa para módulos y componentes
# NOTA: Este módulo está siendo migrado gradualmente a app.module_registry
# pero se mantiene por compatibilidad con código existente.
#
import importlib
import logging
import sys
from typing import Any, Optional, Dict

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

# Instancia global del importador perezoso
lazy_importer = LazyImporter()

# Función de compatibilidad para registrar módulos
def register_module(name: str, module_path: str, **kwargs) -> None:
    """
    Registra un módulo para carga perezosa.
    
    NOTA: Esta función se mantiene para compatibilidad con código existente.
    Para nuevas implementaciones, usar module_registry.register_module.
    
    Args:
        name: Nombre para acceder al módulo
        module_path: Ruta completa del módulo o ruta relativa
        **kwargs: Argumentos adicionales como 'package' para rutas relativas
    """
    # Manejar rutas relativas (como '.module')
    if module_path.startswith('.') and 'package' in kwargs:
        package = kwargs['package']
        if module_path == '.':
            full_path = package
        else:
            full_path = f"{package}{module_path}"
    else:
        full_path = module_path
    
    # Registrar en la instancia global
    lazy_importer.register(name, full_path)
    
    # También intentar registrar en module_registry si está disponible
    try:
        from app.module_registry import module_registry
        module_registry.register_module(name, full_path)
    except ImportError:
        # Si module_registry no está disponible, solo usar lazy_importer
        pass

# Función de compatibilidad para obtener un módulo registrado
def get_module(name: str) -> Any:
    """
    Obtiene un módulo registrado previamente.
    
    NOTA: Esta función se mantiene para compatibilidad con código existente.
    Para nuevas implementaciones, usar module_registry.get_module.
    
    Args:
        name: Nombre del módulo a obtener
        
    Returns:
        El módulo cargado de forma perezosa o None si no está registrado
    """
    # Intentar primero obtener del importador perezoso
    module = lazy_importer.get_module(name)
    if module:
        return module
        
    # Si no está en lazy_importer, intentar con module_registry
    try:
        from app.module_registry import module_registry
        return module_registry.get_module(name)
    except (ImportError, AttributeError):
        # Si module_registry no está disponible o no tiene el módulo
        return None
