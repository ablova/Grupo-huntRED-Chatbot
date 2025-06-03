import os
import re
from pathlib import Path

def update_imports(directory):
    """
    Actualiza las referencias de app.com a app.ats en todos los archivos Python
    """
    # Patrones de búsqueda y reemplazo
    patterns = [
        (r'from app\.com\.', 'from app.ats.'),
        (r'import app\.com\.', 'import app.ats.'),
        (r'app\.com\.', 'app.ats.')
    ]
    
    # Directorios a excluir
    exclude_dirs = {'.git', 'venv', '__pycache__', 'migrations'}
    
    # Contador de cambios
    changes = 0
    
    # Recorrer todos los archivos Python
    for root, dirs, files in os.walk(directory):
        # Excluir directorios
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    # Leer el contenido del archivo
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Aplicar los patrones de reemplazo
                    new_content = content
                    for pattern, replacement in patterns:
                        new_content = re.sub(pattern, replacement, new_content)
                    
                    # Si hubo cambios, escribir el archivo
                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        changes += 1
                        print(f"Actualizado: {file_path}")
                        
                except Exception as e:
                    print(f"Error procesando {file_path}: {str(e)}")
    
    return changes

if __name__ == "__main__":
    # Directorio raíz del proyecto
    root_dir = "."
    
    # Actualizar imports
    total_changes = update_imports(root_dir)
    print(f"\nTotal de archivos actualizados: {total_changes}") 