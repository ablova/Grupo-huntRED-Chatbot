# /home/pablo/app/com/utilidades/migration_fixer.py
"""
Herramienta para solucionar problemas comunes de migración en Django.

Este módulo proporciona funciones para:
1. Detectar y solucionar problemas de migración de manera automática
2. Preparar el entorno para migraciones seguras
3. Restaurar el proyecto después de una migración

Uso:
    from app.com.utilidades.migration_fixer import prepare_for_migration
    prepare_for_migration()
    
    # Ejecutar migraciones...
    
    from app.com.utilidades.migration_fixer import restore_after_migration
    restore_after_migration()
"""

import logging
import os
import sys
import tempfile
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class MigrationContext:
    """Contexto para gestionar el estado durante las migraciones."""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.backup_dir = os.path.join(tempfile.gettempdir(), 'django_migration_backup')
        self.backup_files = []
    
    def backup_file(self, file_path):
        """Crea una copia de seguridad de un archivo."""
        if not os.path.exists(file_path):
            return False
            
        rel_path = os.path.relpath(file_path, self.base_dir)
        backup_path = os.path.join(self.backup_dir, rel_path)
        
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(file_path, backup_path)
        self.backup_files.append((file_path, backup_path))
        return True
    
    def restore_file(self, original_path, backup_path):
        """Restaura un archivo desde su copia de seguridad."""
        if os.path.exists(backup_path):
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            shutil.copy2(backup_path, original_path)
            return True
        return False
    
    def restore_all(self):
        """Restaura todos los archivos desde sus copias de seguridad."""
        for original, backup in self.backup_files:
            self.restore_file(original, backup)
        return len(self.backup_files)


# Singleton para mantener el contexto entre llamadas
_migration_context = MigrationContext()

def prepare_for_migration():
    """Prepara el entorno para una migración segura.
    
    Esta función:
    1. Crea copias de seguridad de archivos críticos
    2. Simplifica archivos __init__.py para evitar errores
    3. Ajusta temporalmente las importaciones circulares
    
    Returns:
        str: Mensaje con el resultado de la operación
    """
    try:
        # Crear directorio para copias de seguridad
        if os.path.exists(_migration_context.backup_dir):
            shutil.rmtree(_migration_context.backup_dir)
        os.makedirs(_migration_context.backup_dir, exist_ok=True)
        
        # Hacer backup y simplificar __init__.py principales
        base_dir = _migration_context.base_dir
        main_init = os.path.join(base_dir, 'app', '__init__.py')
        
        # Backup del __init__.py principal
        _migration_context.backup_file(main_init)
        
        # Simplificar el __init__.py principal
        with open(main_init, 'w') as f:
            f.write("# Temporary simplified __init__.py for migration\ndefault_app_config = 'app.apps.AppConfig'\n")
        
        # Hacer backup de apps.py
        apps_py = os.path.join(base_dir, 'app', 'apps.py')
        _migration_context.backup_file(apps_py)
        
        # Simplificar apps.py
        with open(apps_py, 'r') as f:
            content = f.read()
            
        simplified = content.replace("init_project()", "# init_project() - disabled during migration")
        
        with open(apps_py, 'w') as f:
            f.write(simplified)
        
        # Backup de module_registry.py
        registry_py = os.path.join(base_dir, 'app', 'module_registry.py')
        _migration_context.backup_file(registry_py)
        
        logger.info("Entorno preparado para migración")
        return "✅ Sistema preparado para migración. Ejecuta tus comandos de migración ahora."
    except Exception as e:
        logger.error(f"Error preparando para migración: {str(e)}")
        return f"❌ Error preparando para migración: {str(e)}"

def restore_after_migration():
    """Restaura el entorno después de una migración.
    
    Esta función:
    1. Restaura todos los archivos desde sus copias de seguridad
    2. Elimina archivos temporales
    
    Returns:
        str: Mensaje con el resultado de la operación
    """
    try:
        count = _migration_context.restore_all()
        
        if os.path.exists(_migration_context.backup_dir):
            shutil.rmtree(_migration_context.backup_dir)
            
        logger.info(f"Restaurados {count} archivos después de la migración")
        return f"✅ Restaurados {count} archivos. El sistema ha vuelto a su estado normal."
    except Exception as e:
        logger.error(f"Error restaurando después de migración: {str(e)}")
        return f"❌ Error restaurando: {str(e)}"

def quick_fix():
    """Solución rápida para errores comunes de migración.
    
    Esta función detecta y corrige automáticamente varios errores comunes
    sin necesidad de preparar y restaurar completamente el entorno.
    
    Returns:
        str: Mensaje con el resultado
    """
    try:
        base_dir = _migration_context.base_dir
        fixed = []
        
        # Fix 1: Corregir __init__.py
        main_init = os.path.join(base_dir, 'app', '__init__.py')
        with open(main_init, 'r') as f:
            content = f.read()
            
        if 'auto_register' in content:
            with open(main_init, 'w') as f:
                f.write("# Simplified for migration\ndefault_app_config = 'app.apps.AppConfig'\n")
            fixed.append("__init__.py")
        
        # Fix 2: Verificar apps.py
        apps_py = os.path.join(base_dir, 'app', 'apps.py')
        with open(apps_py, 'r') as f:
            content = f.read()
            
        if 'init_project' in content and not '# init_project' in content:
            with open(apps_py, 'w') as f:
                f.write(content.replace("init_project()", "# init_project() - disabled for migration"))
            fixed.append("apps.py")
        
        if fixed:
            return f"✅ Correcciones aplicadas a: {', '.join(fixed)}. Intenta migrar nuevamente."
        else:
            return "ℹ️ No se detectaron problemas comunes para corregir."
    except Exception as e:
        logger.error(f"Error en quick_fix: {str(e)}")
        return f"❌ Error intentando corregir: {str(e)}"
