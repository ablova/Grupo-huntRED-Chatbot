"""
Script para corregir importaciones en el sistema Grupo huntRED®.
Este script aplica las reglas de importación definidas en import_config.py
y corrige las importaciones relativas a absolutas.
"""

import os
import ast
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple
from app.import_config import (
    IMPORT_MAPPINGS, IMPORT_RULES, get_absolute_import,
    validate_import_structure, get_import_path, should_process_file
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImportFixer:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.app_dir = self.base_dir / 'app'
        self.relative_imports = set()
        self.fixed_files = set()
        self.errors = {}
        
    def analyze_file(self, file_path: Path) -> None:
        """Analiza un archivo Python y encuentra importaciones relativas."""
        if not should_process_file(file_path):
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.level > 0:  # Es una importación relativa
                        self.relative_imports.add((file_path, node.module, node.level))
                        
        except Exception as e:
            if file_path not in self.errors:
                self.errors[file_path] = []
            self.errors[file_path].append(str(e))
            
    def fix_relative_imports(self, file_path: Path) -> bool:
        """Corrige las importaciones relativas en un archivo."""
        if not should_process_file(file_path):
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            lines = content.split('\n')
            modified = False
            
            for i, line in enumerate(lines):
                if line.strip().startswith('from .') or line.strip().startswith('from ..'):
                    # Encontrar la importación relativa correspondiente
                    for rel_file, module, level in self.relative_imports:
                        if rel_file == file_path:
                            # Obtener la ruta absoluta
                            abs_path = get_absolute_import(module)
                            
                            # Reemplazar la importación relativa
                            if level == 1:
                                new_line = line.replace('from .', f'from {abs_path}')
                            else:
                                new_line = line.replace('from ..', f'from {abs_path}')
                                
                            lines[i] = new_line
                            modified = True
                            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                logger.info(f"Corregidas importaciones en {file_path}")
                self.fixed_files.add(file_path)
                return True
                
            return False
            
        except Exception as e:
            if file_path not in self.errors:
                self.errors[file_path] = []
            self.errors[file_path].append(str(e))
            return False
            
    def process_directory(self) -> None:
        """Procesa todos los archivos Python en el directorio."""
        # Primero validar la estructura
        structure_errors = validate_import_structure()
        if structure_errors:
            logger.error("Errores en la estructura de directorios:")
            for package, errors in structure_errors.items():
                for error in errors:
                    logger.error(f"  {package}: {error}")
            return
            
        # Analizar archivos
        for file_path in self.app_dir.rglob('*.py'):
            self.analyze_file(file_path)
            
        # Corregir importaciones relativas
        for file_path, _, _ in self.relative_imports:
            self.fix_relative_imports(file_path)
            
        # Mostrar resumen
        self.show_summary()
        
    def show_summary(self) -> None:
        """Muestra un resumen de las correcciones realizadas."""
        logger.info("\n=== Resumen de correcciones ===")
        logger.info(f"Archivos procesados: {len(self.fixed_files)}")
        logger.info(f"Importaciones relativas encontradas: {len(self.relative_imports)}")
        
        if self.errors:
            logger.error("\nErrores encontrados:")
            for file_path, errors in self.errors.items():
                logger.error(f"\n{file_path}:")
                for error in errors:
                    logger.error(f"  - {error}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fixer = ImportFixer(base_dir)
    fixer.process_directory()

if __name__ == "__main__":
    main() 