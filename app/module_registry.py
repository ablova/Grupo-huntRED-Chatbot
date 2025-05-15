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
from typing import Callable, Dict, List, Optional, Set, TypeVar
import logging
from pathlib import Path
from app.lazy_imports import LazyImporter, LazyModule

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ModuleRegistry:
    """Central registry for managing lazy loading of modules and __init__.py files."""

    def __init__(self):
        self._importer = LazyImporter()
        self._modules: Dict[str, str] = {}
        self._base_path = os.path.dirname(os.path.abspath(__file__))
        self._exclude_dirs = {'__pycache__', 'migrations', '.git', '.vscode', '.idea'}

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
        
    def manage_init_files(self, base_dir: str = None) -> None:
        """Gestiona automáticamente los archivos __init__.py en todo el proyecto.
        
        - Crea los archivos __init__.py faltantes
        - Corrige los existentes para evitar importaciones circulares
        - Mantiene consistencia en la estructura
        
        Args:
            base_dir: Directorio base para comenzar. Por defecto usa self._base_path
        """
        if base_dir is None:
            # Usar directorio de app
            base_dir = os.path.dirname(self._base_path)
        
        try:
            # Recopilar información sobre módulos y paquetes
            package_info = self._scan_packages(base_dir)
            
            # Generar/actualizar archivos __init__.py
            for pkg_dir, modules in package_info.items():
                self._update_init_file(pkg_dir, modules)
                
            logger.info(f"Archivos __init__.py gestionados correctamente en {base_dir}")
        except Exception as e:
            logger.error(f"Error gestionando archivos __init__.py: {str(e)}")
    
    def _scan_packages(self, base_dir: str) -> Dict[str, List[str]]:
        """Escanea el directorio para encontrar paquetes y módulos Python.
        
        Args:
            base_dir: Directorio base a escanear
            
        Returns:
            Dict[str, List[str]]: Diccionario con directorios como claves y listas de módulos como valores
        """
        package_info = {}
        
        for root, dirs, files in os.walk(base_dir):
            # Filtrar directorios excluidos
            dirs[:] = [d for d in dirs if d not in self._exclude_dirs]
            
            # Obtener módulos Python en este directorio
            py_modules = [f[:-3] for f in files if f.endswith('.py') and f != '__init__.py']
            
            if py_modules or any(os.path.isdir(os.path.join(root, d)) for d in dirs):
                package_info[root] = py_modules
        
        return package_info
    
    def _update_init_file(self, directory: str, modules: List[str]) -> None:
        """Actualiza o crea un archivo __init__.py en el directorio especificado.
        
        Args:
            directory: Ruta al directorio
            modules: Lista de módulos Python en el directorio
        """
        init_path = os.path.join(directory, '__init__.py')
        pkg_name = os.path.basename(directory)
        
        # Generar contenido optimizado para __init__.py
        content = [
            f"# {directory}/__init__.py",
            "",
            "# Auto-gestionado por ModuleRegistry",
            "# Evita importaciones circulares o importaciones directas de modelos aquí",
            ""
        ]
        
        # Solo agregar exportaciones para módulos no privados
        public_modules = [m for m in modules if not m.startswith('_')]
        if public_modules:
            content.append("# Exportaciones del módulo")
            content.append("__all__ = [")
            for module in sorted(public_modules):
                content.append(f"    '{module}',")
            content.append("]")
            content.append("")
        
        # Escribir el archivo
        with open(init_path, 'w') as f:
            f.write('\n'.join(content))

# Create a singleton instance
_REGISTRY = ModuleRegistry()

# Public API
def auto_register(base_package: str = 'app') -> None:
    """Automatically register all modules in the project.

    Args:
        base_package: The base package to start the scan from. Defaults to 'app'.
    """
    _REGISTRY.auto_register(base_package)

# Alias for backward compatibility
auto_register_modules = auto_register

def manage_init_files(base_dir: str = None) -> None:
    """Gestiona automáticamente los archivos __init__.py en todo el proyecto.

    Esta función:
    - Crea archivos __init__.py faltantes
    - Corrige archivos existentes para eliminar importaciones circulares
    - Mantiene una estructura consistente y segura

    Args:
        base_dir: Directorio base para comenzar. Por defecto usa el directorio de app.
    """
    _REGISTRY.manage_init_files(base_dir)

def init_project():
    """Inicializa el proyecto completo.
    
    1. Gestiona archivos __init__.py
    2. Registra módulos para lazy loading

    Esta función es ideal para ejecutarse durante el inicio de Django,
    después de que las migraciones estén completas.
    """
    # Verificar si estamos en un proceso de migración
    is_migration = False
    try:
        import sys
        is_migration = any(arg in sys.argv for arg in ['migrate', 'makemigrations', 'collectstatic', 'test'])
    except Exception:
        pass

    try:
        if is_migration:
            # En migraciones, hacer sólo lo esencial
            logger.info("Inicialización mínima durante migraciones")
            return
            
        # Primero gestionar los __init__.py
        _REGISTRY.manage_init_files()
        logger.info("Archivos __init__.py gestionados correctamente")
        
        # Luego registrar los módulos
        _REGISTRY.auto_register()
        logger.info("Módulos registrados correctamente")
    except Exception as e:
        logger.error(f"Error inicializando el proyecto: {str(e)}")

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
