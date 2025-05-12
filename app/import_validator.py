import os
import importlib
import logging
from pathlib import Path
from typing import Dict, Set, List
from app.lazy_imports import lazy_imports, register_package_modules

logger = logging.getLogger('import_validator')

def analyze_module_dependencies(module_path: str, visited: Set[str] = None) -> Dict[str, Set[str]]:
    """
    Analyze module dependencies recursively.
    
    Args:
        module_path: Path to the module to analyze
        visited: Set of already visited modules to prevent cycles
        
    Returns:
        Dictionary mapping modules to their dependencies
    """
    if visited is None:
        visited = set()
    
    if module_path in visited:
        return {}
    
    visited.add(module_path)
    
    try:
        module = importlib.import_module(module_path)
        dependencies = set()
        
        # Get all imports from __init__.py if it exists
        init_path = Path(module.__file__).parent / '__init__.py'
        if init_path.exists():
            with open(init_path, 'r') as f:
                content = f.read()
                # Buscar imports simples
                for line in content.split('\n'):
                    if line.strip().startswith('from '):
                        import_line = line.strip().split('import')[0].strip()
                        if '.' in import_line:
                            dependencies.add(import_line.split('from')[1].strip())
                    elif line.strip().startswith('import '):
                        import_line = line.strip().split('import')[1].strip()
                        if '.' in import_line:
                            dependencies.add(import_line.split('.')[0])
        
        # Analizar dependencias de submódulos
        submodules = {
            name: getattr(module, name)
            for name in dir(module)
            if not name.startswith('_') and 
               isinstance(getattr(module, name), type(module))
        }
        
        # Analizar cada submódulo recursivamente
        for submodule_name, submodule in submodules.items():
            submodule_path = f"{module_path}.{submodule_name}"
            sub_dependencies = analyze_module_dependencies(submodule_path, visited)
            dependencies.update(sub_dependencies.get(submodule_path, set()))
        
        return {module_path: dependencies}
        
    except ImportError as e:
        logger.error(f"Error importing {module_path}: {str(e)}")
        return {module_path: set()}

def validate_imports():
    """
    Validate all imports in the application and register lazy imports.
    """
    # Obtener todos los paquetes en la aplicación
    app_path = Path(__file__).parent
    packages = [d.name for d in app_path.iterdir() if d.is_dir() and not d.name.startswith('_')]
    
    # Registrar módulos de cada paquete
    for package in packages:
        try:
            register_package_modules(package)
            logger.info(f"Registered modules from package {package}")
        except Exception as e:
            logger.error(f"Error registering modules from {package}: {str(e)}")
    
    # Analizar dependencias
    dependency_graph = {}
    for package in packages:
        try:
            package_path = f"app.{package}"
            dependencies = analyze_module_dependencies(package_path)
            dependency_graph.update(dependencies)
        except Exception as e:
            logger.error(f"Error analyzing dependencies for {package}: {str(e)}")
    
    # Verificar ciclos en el grafo de dependencias
    def detect_cycles(graph: Dict[str, Set[str]], node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                if detect_cycles(graph, neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                logger.error(f"Circular dependency detected: {node} -> {neighbor}")
                return True
        
        rec_stack.remove(node)
        return False
    
    visited = set()
    rec_stack = set()
    
    for node in dependency_graph:
        if node not in visited:
            if detect_cycles(dependency_graph, node, visited, rec_stack):
                logger.error("Circular dependencies found in the application")
                return False
    
    logger.info("No circular dependencies found")
    return True

def main():
    """
    Main function to validate imports and register lazy imports.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if validate_imports():
        logger.info("Import validation completed successfully")
    else:
        logger.error("Import validation failed")

if __name__ == "__main__":
    main()
