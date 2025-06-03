#!/usr/bin/env python3
"""
Script para sincronizar cambios con el servidor y mantener el formato de commit AI huntRED®
"""

import os
import re
import subprocess
import json
from pathlib import Path
from datetime import datetime

CONFIG_FILE = 'sync_config.json'
VERSION = "2.2"
BASE_COMMIT_MSG = f"AI huntRED® {VERSION} BIG IMPROVEMENTS"

def load_config():
    """Carga la configuración del contador y último commit"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {'last_commit': '', 'change_count': 0}

def save_config(config):
    """Guarda la configuración actual"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_git_changes():
    """Obtiene los cambios desde el último commit registrado"""
    config = load_config()
    last_commit = config['last_commit']
    
    if not last_commit:
        # Si no hay último commit, obtener todos los archivos Python
        cmd = ['git', 'ls-files', '*.py']
    else:
        # Obtener cambios desde el último commit
        cmd = ['git', 'diff', '--name-only', last_commit, 'HEAD', '*.py']
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip().split('\n') if result.stdout.strip() else []

def update_imports(directory):
    """Actualiza las importaciones en todos los archivos Python del directorio"""
    pattern = re.compile(r'from app\.ats\.ml\.(.*?) import')
    replacement = r'from app.ml.\1 import'
    updated_files = []
    
    # Obtener archivos modificados desde Git
    changed_files = get_git_changes()
    
    for file_path in changed_files:
        if not file_path.endswith('.py'):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'from app.ats.ml' in content:
                new_content = pattern.sub(replacement, content)
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    updated_files.append(file_path)
                    print(f"Actualizado: {file_path}")
        except Exception as e:
            print(f"Error procesando {file_path}: {e}")
    
    return updated_files

def sync_to_server(updated_files):
    """Sincroniza los archivos actualizados con el servidor"""
    if not updated_files:
        print("No hay archivos para sincronizar")
        return
    
    # Crear archivo temporal con la lista de archivos actualizados
    temp_file = f"sync_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(temp_file, 'w') as f:
        for file in updated_files:
            f.write(f"{file}\n")
    
    try:
        # Sincronizar archivos usando rsync
        rsync_cmd = [
            'rsync',
            '-avz',
            '--files-from=' + temp_file,
            '.',
            'grupo-huntred:/home/pablo/'
        ]
        
        print("\nSincronizando archivos con el servidor...")
        subprocess.run(rsync_cmd, check=True)
        print("¡Sincronización completada!")
        
    except subprocess.CalledProcessError as e:
        print(f"Error durante la sincronización: {e}")
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_file):
            os.remove(temp_file)

def update_git_status():
    """Actualiza el estado de Git y el contador de cambios"""
    config = load_config()
    
    # Obtener el último commit
    result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                          capture_output=True, text=True)
    current_commit = result.stdout.strip()
    
    if current_commit != config['last_commit']:
        config['last_commit'] = current_commit
        config['change_count'] += 1
        save_config(config)
        print(f"\nContador de cambios actualizado: {config['change_count']}")

def main():
    app_dir = 'app'
    print("Iniciando actualización de importaciones...")
    updated_files = update_imports(app_dir)
    
    if updated_files:
        print(f"\nTotal de archivos actualizados: {len(updated_files)}")
        sync_to_server(updated_files)
        
        # Crear commit con el formato específico
        subprocess.run(['git', 'add', '.'])
        commit_msg = f"{BASE_COMMIT_MSG} - Ajustes +{len(updated_files)}"
        subprocess.run(['git', 'commit', '-m', commit_msg])
        
        # Actualizar estado de Git
        update_git_status()
    else:
        print("No se encontraron archivos que necesiten actualización")

if __name__ == '__main__':
    main() 