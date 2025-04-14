# scripts/analyze_dependencies.py  - pip install pipdeptree
import os
import ast
from pathlib import Path

# Directorio raíz del proyecto Django
BASE_DIR = Path(__file__).resolve().parent.parent

def get_python_files(directoriy):
    """Obtiene todos los archivos .py en el directorio de forma recursiva."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def extract_imports(file_path):
    """Extrae todos los imports de un archivo Python."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    tree = ast.parse(content)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.add(name.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    return imports

def analyze_project_imports():
    """Analiza todos los imports en el proyecto."""
    all_imports = set()
    python_files = get_python_files(BASE_DIR)
    for file_path in python_files:
        file_imports = extract_imports(file_path)
        all_imports.update(file_imports)
    return all_imports

def main():
    # Obtener todos los imports del proyecto
    project_imports = analyze_project_imports()
    
    # Leer requirements.txt
    with open(BASE_DIR / 'requirements.txt', 'r') as f:
        requirements = {line.split('==')[0].split('@')[0].strip() for line in f if line.strip()}

    # Identificar paquetes no utilizados
    unused_packages = requirements - project_imports
    
    print("Paquetes en requirements.txt pero no importados en el código:")
    for pkg in sorted(unused_packages):
        print(f" - {pkg}")

if __name__ == "__main__":
    main()