import os
import shutil
from pathlib import Path

def cleanup_directory(directory):
    """
    Limpia archivos duplicados y temporales en el directorio especificado
    """
    # Archivos y patrones a eliminar
    patterns_to_remove = [
        '.DS_Store',
        '.bak.',
        'basebase.py',
        '__pycache__'
    ]
    
    # Recorrer el directorio
    for root, dirs, files in os.walk(directory):
        # Eliminar directorios __pycache__
        if '__pycache__' in dirs:
            shutil.rmtree(os.path.join(root, '__pycache__'))
            print(f"Eliminado: {os.path.join(root, '__pycache__')}")
        
        # Eliminar archivos que coincidan con los patrones
        for file in files:
            file_path = os.path.join(root, file)
            if any(pattern in file for pattern in patterns_to_remove):
                os.remove(file_path)
                print(f"Eliminado: {file_path}")

def main():
    # Directorio a limpiar
    target_dir = "app/ats"
    
    print(f"Iniciando limpieza en {target_dir}")
    cleanup_directory(target_dir)
    print("Limpieza completada")

if __name__ == "__main__":
    main() 