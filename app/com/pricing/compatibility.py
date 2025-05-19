# /home/pablo/app/com/pricing/compatibility.py
"""
Módulo de compatibilidad para el sistema de precios de Grupo huntRED®.

Este módulo proporciona compatibilidad entre la estructura antigua (/app/pricing/)
y la estructura correcta (/app/com/pricing/) para garantizar que todas las
partes del sistema utilicen el módulo de pricing actualizado.

Siguiendo los principios de Apoyo, Solidaridad y Sinergia, este módulo asegura
que todo el sistema funcione correctamente durante la transición a la nueva
estructura.
"""

import os
import sys
import logging
import importlib
import inspect
from pathlib import Path
from types import ModuleType

logger = logging.getLogger(__name__)

# Mapeo entre rutas antiguas y nuevas
PATH_MAPPING = {
    'app.pricing.': 'app.com.pricing.',
    'app/pricing/': 'app/com/pricing/',
}

# Módulos a redireccionar
MODULES_TO_REDIRECT = [
    'utils',
    'config',
    'proposal_generator',
    'payment_incentives',
    'models',
]


def redirect_imports():
    """
    Redirecciona importaciones del módulo antiguo al nuevo.
    
    Esta función intercepta importaciones del módulo antiguo (app.pricing)
    y las redirecciona al módulo correcto (app.com.pricing).
    """
    # Verificar si ya existe el módulo antiguo en sys.modules
    if 'app.pricing' in sys.modules:
        logger.info("Redireccionando importaciones del módulo antiguo app.pricing")
        
        # Crear módulos proxy para cada submódulo
        for module_name in MODULES_TO_REDIRECT:
            old_module_name = f'app.pricing.{module_name}'
            new_module_name = f'app.com.pricing.{module_name}'
            
            # Intentar importar el módulo nuevo
            try:
                new_module = importlib.import_module(new_module_name)
                
                # Crear un módulo proxy para el módulo antiguo
                proxy_module = ModuleType(old_module_name)
                
                # Copiar todos los atributos del módulo nuevo al proxy
                for attr_name in dir(new_module):
                    if not attr_name.startswith('_'):  # Excluir atributos privados
                        setattr(proxy_module, attr_name, getattr(new_module, attr_name))
                
                # Registrar el módulo proxy en sys.modules
                sys.modules[old_module_name] = proxy_module
                logger.debug(f"Redireccionado: {old_module_name} -> {new_module_name}")
                
            except ImportError as e:
                logger.warning(f"No se pudo importar {new_module_name}: {e}")
    
    # También modificar sys.path si es necesario
    for i, path in enumerate(sys.path):
        for old_path, new_path in PATH_MAPPING.items():
            if old_path in path:
                sys.path[i] = path.replace(old_path, new_path)
                logger.debug(f"Modificado sys.path: {path} -> {sys.path[i]}")


def update_imports_in_file(file_path):
    """
    Actualiza las importaciones en un archivo de Python.
    
    Args:
        file_path: Ruta al archivo a actualizar
    
    Returns:
        bool: True si se realizaron cambios, False en caso contrario
    """
    if not os.path.exists(file_path) or not file_path.endswith('.py'):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar y reemplazar patrones de importación
        modified = False
        for old_pattern, new_pattern in PATH_MAPPING.items():
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                modified = True
        
        # Guardar cambios si se realizaron modificaciones
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Actualizadas importaciones en {file_path}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error al actualizar importaciones en {file_path}: {e}")
        return False


def scan_and_update_imports(base_dir=None):
    """
    Escanea y actualiza importaciones en todos los archivos Python del proyecto.
    
    Args:
        base_dir: Directorio base a escanear. Si es None, se usa el directorio
                 base de la aplicación (app/).
    
    Returns:
        tuple: (total_files_scanned, total_files_updated)
    """
    if base_dir is None:
        # Obtener directorio base de la aplicación
        import app
        base_dir = os.path.dirname(app.__file__)
    
    logger.info(f"Escaneando archivos Python en {base_dir}")
    
    total_files = 0
    updated_files = 0
    
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py'):
                total_files += 1
                file_path = os.path.join(root, file)
                if update_imports_in_file(file_path):
                    updated_files += 1
    
    logger.info(f"Escaneo completado. {updated_files} de {total_files} archivos actualizados.")
    return total_files, updated_files


def create_symlinks():
    """
    Crea enlaces simbólicos desde la ruta antigua a la nueva.
    
    Esta función es útil para sistemas que puedan soportar enlaces simbólicos
    (principalmente entornos Unix/Linux).
    """
    try:
        from django.conf import settings
        
        # Obtener rutas
        old_dir = os.path.join(settings.BASE_DIR, 'app/pricing')
        new_dir = os.path.join(settings.BASE_DIR, 'app/com/pricing')
        
        # Verificar que existan los directorios
        if not os.path.exists(new_dir):
            logger.error(f"El directorio destino no existe: {new_dir}")
            return False
        
        # Si el directorio antiguo existe, renombrarlo como backup
        if os.path.exists(old_dir):
            backup_dir = f"{old_dir}_backup"
            os.rename(old_dir, backup_dir)
            logger.info(f"Renombrado directorio antiguo: {old_dir} -> {backup_dir}")
        
        # Crear un enlace simbólico desde la ruta antigua a la nueva
        os.symlink(new_dir, old_dir)
        logger.info(f"Creado enlace simbólico: {old_dir} -> {new_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error al crear enlaces simbólicos: {e}")
        return False


def initialize_compatibility():
    """
    Inicializa el sistema de compatibilidad.
    
    Esta función debe ser llamada durante la inicialización de la aplicación
    para asegurar que todas las partes del sistema utilicen el módulo de pricing
    correcto.
    """
    logger.info("Inicializando sistema de compatibilidad para el módulo de pricing")
    
    # Redireccionar importaciones
    redirect_imports()
    
    # Intentar crear enlaces simbólicos si estamos en un entorno que lo soporte
    if sys.platform != 'win32':
        try:
            create_symlinks()
        except Exception as e:
            logger.warning(f"No se pudieron crear enlaces simbólicos: {e}")
    
    logger.info("Sistema de compatibilidad inicializado correctamente")


# Inicializar sistema de compatibilidad automáticamente al importar este módulo
if __name__ != '__main__':
    initialize_compatibility()
