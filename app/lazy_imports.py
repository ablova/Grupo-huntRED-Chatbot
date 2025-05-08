import importlib
import sys
from typing import Dict, Any
from pathlib import Path

class LazyModule:
    def __init__(self, module_path: str, package: str = None):
        self.module_path = module_path
        self.package = package
        self._module = None

    def __getattr__(self, name: str) -> Any:
        if self._module is None:
            if self.package:
                self._module = importlib.import_module(self.module_path, package=self.package)
            else:
                self._module = importlib.import_module(self.module_path)
        return getattr(self._module, name)

class LazyImports:
    def __init__(self):
        self.modules = {}
        self.package = None

    def set_package(self, package: str):
        self.package = package

    def register(self, name: str, module_path: str) -> None:
        self.modules[name] = LazyModule(module_path, package=self.package)

    def get(self, name: str) -> Any:
        return self.modules[name]

    def __getattr__(self, name: str) -> Any:
        if name not in self.modules:
            raise ImportError(f"Module {name} not registered")
        return self.modules[name]

# Crear una instancia global de LazyImports
lazy_imports = LazyImports()

# Función utilitaria para registrar nuevos módulos
def register_module(name: str, module_path: str, package: str = None) -> None:
    if package:
        lazy_imports.set_package(package)
    lazy_imports.register(name, module_path)

# Función utilitaria para obtener un módulo
def get_module(name: str) -> Any:
    return lazy_imports.get(name)

# Función utilitaria para obtener el nombre del paquete actual
def get_current_package():
    current_file = Path(__file__)
    app_dir = current_file.parent
    return app_dir.name
