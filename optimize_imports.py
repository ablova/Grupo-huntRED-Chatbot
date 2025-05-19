import os
import ast
import logging
from pathlib import Path
from typing import List, Dict, Set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImportOptimizer:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.app_dir = self.base_dir / 'app'
        self.imports_map = {}
        self.relative_imports = set()
        
    def analyze_file(self, file_path: Path) -> None:
        """Analiza un archivo Python y encuentra importaciones relativas."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.level > 0:  # Es una importación relativa
                        self.relative_imports.add((file_path, node.module, node.level))
                        
        except Exception as e:
            logger.error(f"Error analizando {file_path}: {str(e)}")
            
    def get_absolute_import_path(self, file_path: Path, relative_module: str, level: int) -> str:
        """Convierte una importación relativa en absoluta."""
        # Obtener la ruta relativa desde app/
        rel_path = file_path.relative_to(self.app_dir)
        parts = rel_path.parts[:-1]  # Excluir el archivo actual
        
        # Subir según el nivel de la importación relativa
        parts = parts[:-(level-1)] if level > 1 else parts
        
        # Construir la ruta absoluta
        if relative_module:
            return f"app.{'.'.join(parts)}.{relative_module}"
        return f"app.{'.'.join(parts)}"
        
    def fix_relative_imports(self, file_path: Path) -> bool:
        """Corrige las importaciones relativas en un archivo."""
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
                            abs_path = self.get_absolute_import_path(file_path, module, level)
                            new_line = line.replace('from .', f'from {abs_path}')
                            new_line = new_line.replace('from ..', f'from {abs_path}')
                            lines[i] = new_line
                            modified = True
                            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                logger.info(f"Corregidas importaciones en {file_path}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error corrigiendo importaciones en {file_path}: {str(e)}")
            return False
            
    def process_directory(self) -> None:
        """Procesa todos los archivos Python en el directorio."""
        for file_path in self.app_dir.rglob('*.py'):
            if file_path.name == '__init__.py':
                continue
                
            self.analyze_file(file_path)
            
        # Corregir importaciones relativas
        for file_path, _, _ in self.relative_imports:
            self.fix_relative_imports(file_path)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    optimizer = ImportOptimizer(base_dir)
    optimizer.process_directory()
    logger.info("Proceso de optimización completado")

if __name__ == "__main__":
    main() 