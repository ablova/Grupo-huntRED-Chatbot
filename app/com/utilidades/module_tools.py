# /home/pablo/app/com/utilidades/module_tools.py
"""
Herramientas para la gestión de módulos y evitar conflictos en el proyecto.

Este módulo proporciona utilidades para:
1. Gestionar archivos __init__.py
2. Corregir importaciones circulares
3. Optimizar la estructura del proyecto
"""

import importlib
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional

# Importamos el registro de módulos (ya implementado)
from app.module_registry import manage_init_files, init_project

logger = logging.getLogger(__name__)

def fix_circular_imports(module_name: str) -> bool:
    """Intenta corregir importaciones circulares en un módulo específico.
    
    Args:
        module_name: Nombre del módulo con importaciones circulares
        
    Returns:
        bool: True si se corrigió el problema, False en caso contrario
    """
    try:
        # Intentamos importar el módulo para verificar si hay errores
        importlib.import_module(module_name)
        return True
    except ImportError as e:
        logger.warning(f"Importación circular detectada en {module_name}: {str(e)}")
        
        # Regeneramos los archivos __init__.py en ese módulo específicamente
        module_path = module_name.replace('.', '/')
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), module_path)
        
        if os.path.exists(base_dir):
            manage_init_files(base_dir)
            logger.info(f"Regenerados archivos __init__.py en {base_dir}")
            
            # Volvemos a intentar la importación
            try:
                importlib.import_module(module_name)
                return True
            except ImportError as e2:
                logger.error(f"No se pudo resolver la importación circular en {module_name}: {str(e2)}")
                return False
        else:
            logger.error(f"No se encontró el directorio para el módulo {module_name}")
            return False

def optimize_imports(file_path: str) -> bool:
    """Optimiza las importaciones en un archivo Python específico.
    
    Convierte importaciones relativas a absolutas para evitar problemas.
    
    Args:
        file_path: Ruta al archivo Python a optimizar
        
    Returns:
        bool: True si se optimizó el archivo, False en caso contrario
    """
    if not os.path.exists(file_path) or not file_path.endswith('.py'):
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Detectar importaciones relativas problemáticas
        lines = content.split('\n')
        modified = False
        
        for i, line in enumerate(lines):
            # Convertir importaciones relativas de modelos
            if 'from .' in line and 'models' in line:
                lines[i] = line.replace('from .', 'from app.')
                modified = True
            
            # Convertir otras importaciones relativas problemáticas
            if 'from ..' in line:
                module_parts = file_path.replace('/', '.').split('.')
                new_import = f"from app.{'.'.join(module_parts[1:-1])}"
                lines[i] = line.replace('from ..', new_import)
                modified = True
        
        if modified:
            with open(file_path, 'w') as f:
                f.write('\n'.join(lines))
            logger.info(f"Optimizadas importaciones en {file_path}")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error optimizando importaciones en {file_path}: {str(e)}")
        return False

def clean_init_files() -> None:
    """Limpia todos los archivos __init__.py para eliminar importaciones problemáticas.
    
    Esta función es útil cuando se han introducido nuevos módulos o reorganizado
    la estructura del proyecto.
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        manage_init_files(base_dir)
        logger.info("Limpieza de archivos __init__.py completada con éxito")
    except Exception as e:
        logger.error(f"Error limpiando archivos __init__.py: {str(e)}")

def optimize_all_modules() -> None:
    """Optimiza todos los módulos Python del proyecto.
    
    Esta función:
    1. Regenera los archivos __init__.py
    2. Corrige importaciones circulares
    3. Optimiza las importaciones
    """
    try:
        # Primero limpiamos todos los __init__.py
        clean_init_files()
        
        # Luego recorremos todos los archivos Python
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    file_path = os.path.join(root, file)
                    optimize_imports(file_path)
        
        # Finalmente inicializamos el proyecto completo
        init_project()
        
        logger.info("Optimización de todos los módulos completada con éxito")
    except Exception as e:
        logger.error(f"Error optimizando módulos: {str(e)}")

# Función de conveniencia para ejecutar desde el shell de Django
def fix_all():
    """Soluciona todos los problemas comunes de módulos e importaciones.
    
    Uso desde shell de Django:
    from app.com.utilidades.module_tools import fix_all
    fix_all()
    """
    optimize_all_modules()
    return "Optimización completada. Revisa los logs para más detalles."
