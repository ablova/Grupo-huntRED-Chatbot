#!/usr/bin/env python3
"""
Script para actualizar las importaciones de app.ats.ml a app.ml
"""

import os
import re
from pathlib import Path

def update_imports(directory):
    """Actualiza las importaciones en todos los archivos Python del directorio"""
    pattern = re.compile(r'from app\.ats\.ml\.(.*?) import')
    replacement = r'from app.ml.\1 import'
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Verificar si hay importaciones que actualizar
                    if 'from app.ats.ml' in content:
                        new_content = pattern.sub(replacement, content)
                        
                        # Solo escribir si hubo cambios
                        if new_content != content:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            print(f"Actualizado: {file_path}")
                except Exception as e:
                    print(f"Error procesando {file_path}: {e}")

if __name__ == '__main__':
    app_dir = 'app'
    print("Iniciando actualización de importaciones...")
    update_imports(app_dir)
    print("¡Actualización completada!") 