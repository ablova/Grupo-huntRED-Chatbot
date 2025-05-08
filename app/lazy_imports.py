import importlib
import sys
from typing import Dict, Any

class LazyModule:
    def __init__(self, module_path: str):
        self.module_path = module_path
        self._module = None

    def __getattr__(self, name: str) -> Any:
        if self._module is None:
            self._module = importlib.import_module(self.module_path)
        return getattr(self._module, name)

class LazyImports:
    def __init__(self):
        self.modules = {}

    def register(self, name: str, module_path: str) -> None:
        self.modules[name] = LazyModule(module_path)

    def get(self, name: str) -> Any:
        return self.modules[name]

    def __getattr__(self, name: str) -> Any:
        if name not in self.modules:
            raise ImportError(f"Module {name} not registered")
        return self.modules[name]

# Crear una instancia global de LazyImports
lazy_imports = LazyImports()

# Registrar todos los módulos que necesitan importaciones lazy
lazy_imports.register('scraping', '.utilidades.scraping')
lazy_imports.register('scraping_utils', '.utilidades.scraping_utils')
lazy_imports.register('linkedin', '.utilidades.linkedin')
lazy_imports.register('email_scraper', '.utilidades.email_scraper')
lazy_imports.register('models', '.models')
lazy_imports.register('celery_app', 'ai_huntred.celery_app')

# Función utilitaria para registrar nuevos módulos
def register_module(name: str, module_path: str) -> None:
    lazy_imports.register(name, module_path)

# Función utilitaria para obtener un módulo
# Se puede usar como: get_module('scraping').ScrapingPipeline
def get_module(name: str) -> Any:
    return lazy_imports.get(name)
