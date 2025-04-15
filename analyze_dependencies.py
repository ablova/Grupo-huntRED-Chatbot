import os
import ast
from pathlib import Path
import subprocess
import json
from typing import Set, List

# Directorio raíz del proyecto Django
BASE_DIR = Path('/home/pablo')

def get_python_files(directory: Path) -> List[Path]:
    """
    Obtiene todos los archivos .py en el directorio de forma recursiva.
    Excluye directorios y archivos no relevantes.
    """
    python_files = []
    exclude_dirs = {
        'venv', 'env', '__pycache__', '.git', 'migrations',
        'nltk_data', 'tfhub_cache', 'playwright-browsers', 'cache', 'logs', 'staticfiles'
    }
    exclude_files = {'shell.py'}  # Excluir archivo problemático
    for file_path in directory.rglob('*.py'):
        if (not any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs) and
                file_path.name not in exclude_files):
            python_files.append(file_path)
    return python_files

def extract_imports(file_path: Path) -> Set[str]:
    """
    Extrae todos los imports de un archivo Python usando AST.
    Maneja errores de sintaxis o codificación.
    """
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Error procesando {file_path}: {e}")
    return imports

def get_pipdeptree_dependencies() -> Set[str]:
    """
    Obtiene dependencias reales usando pipdeptree.
    Normaliza nombres para comparación.
    """
    try:
        result = subprocess.run(
            ['pipdeptree', '--json'],
            capture_output=True,
            text=True,
            check=True
        )
        dependencies = json.loads(result.stdout)
        return {dep['package']['package_name'].replace('-', '_').lower() for dep in dependencies}
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error ejecutando pipdeptree: {e}")
        return set()

def analyze_project_imports() -> Set[str]:
    """
    Analiza imports y combina con dependencias reales.
    Imprime información de depuración.
    """
    all_imports = set()
    python_files = get_python_files(BASE_DIR)
    
    print(f"Archivos .py encontrados: {len(python_files)}")
    for file_path in python_files:
        print(f"Procesando: {file_path}")
        all_imports.update(extract_imports(file_path))
    
    pipdeptree_deps = get_pipdeptree_dependencies()
    print(f"Dependencias de pipdeptree: {sorted(pipdeptree_deps)}")
    all_imports.update(pipdeptree_deps)
    
    print(f"Total de imports únicos: {len(all_imports)}")
    return all_imports

def main():
    """
    Analiza imports y compara con requirements.txt.
    """
    print("Iniciando análisis de dependencias...")
    project_imports = analyze_project_imports()
    
    requirements_path = BASE_DIR / 'requirements.txt'
    requirements = set()
    try:
        with open(requirements_path, 'r') as f:
            requirements = {
                line.split('==')[0].split('@')[0].strip().replace('-', '_').lower()
                for line in f
                if line.strip() and not line.startswith('#')
            }
        print(f"Paquetes en requirements.txt: {sorted(requirements)}")
    except FileNotFoundError:
        print(f"No se encontró {requirements_path}")
        return

    unused_packages = requirements - project_imports
    
    if unused_packages:
        print("Paquetes en requirements.txt pero no importados ni usados como dependencias:")
        for pkg in sorted(unused_packages):
            print(f" - {pkg}")
    else:
        print("No se encontraron paquetes no utilizados.")

if __name__ == "__main__":
    main()