# /home/pablo/app/imports.py
"""
Sistema centralizado de importaciones para Grupo huntRED®.
"""
import importlib
import logging
from typing import Any, Dict, Optional, Callable

logger = logging.getLogger(__name__)

class ImportManager:
    """Gestor de importaciones para el proyecto."""
    
    _instance = None
    _modules: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info("Nueva instancia de ImportManager creada")
        return cls._instance
    
    def get_module(self, module_path: str) -> Any:
        """Obtiene un módulo, cacheándolo si es necesario."""
        if module_path not in self._modules:
            try:
                self._modules[module_path] = importlib.import_module(module_path)
                logger.debug(f"Módulo {module_path} importado y cacheado")
            except ImportError as e:
                logger.error(f"Error al importar {module_path}: {e}")
                raise
        return self._modules[module_path]
    
    def get_from_module(self, module_path: str, name: str) -> Any:
        """Obtiene un atributo específico de un módulo."""
        module = self.get_module(module_path)
        try:
            return getattr(module, name)
        except AttributeError as e:
            logger.error(f"Error al obtener {name} desde {module_path}: {e}")
            raise
            
    def add_lazy_module(self, name: str, module_path: str) -> None:
        """Registra un módulo para carga perezosa."""
        if name in self._modules:
            logger.debug(f"Módulo perezoso {name} ya registrado")
            return
            
        def lazy_import() -> Any:
            try:
                return importlib.import_module(module_path)
            except ImportError as e:
                logger.error(f"Error al cargar módulo perezoso {name} ({module_path}): {e}")
                raise
                
        self._modules[name] = lazy_import
        logger.debug(f"Módulo perezoso {name} registrado para {module_path}")

# Instancia global del gestor de importaciones
imports = ImportManager()

# Funciones de conveniencia para importaciones comunes
def get_model(model_name: str) -> Any:
    """Obtiene un modelo de la aplicación."""
    return imports.get_from_module('app.models', model_name)

def get_view(view_name: str) -> Any:
    """Obtiene una vista de la aplicación."""
    return imports.get_from_module('app.views', view_name)

def get_form(form_name: str) -> Any:
    """Obtiene un formulario de la aplicación."""
    return imports.get_from_module('app.forms', form_name)

def get_util(util_name: str) -> Any:
    """Obtiene una utilidad de la aplicación."""
    return imports.get_from_module('app.utils', util_name)

# Inicialización
logger.info("Sistema de importaciones inicializado correctamente")
