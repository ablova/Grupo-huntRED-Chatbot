#!/usr/bin/env python3
"""
Script para agregar importaciones de settings en archivos que usan settings.AUTH_USER_MODEL.
"""

import os
import re

def add_settings_import(file_path):
    """Agrega la importación de settings si no existe."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya existe la importación
    if 'from django.conf import settings' in content:
        print(f"✅ Ya tiene importación: {file_path}")
        return False
    
    # Buscar líneas de importación existentes
    lines = content.split('\n')
    import_lines = []
    other_lines = []
    
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            import_lines.append((i, line))
        else:
            other_lines.append((i, line))
    
    # Encontrar la posición correcta para insertar la importación
    insert_position = 0
    for i, line in import_lines:
        if 'django' in line:
            insert_position = i + 1
            break
    
    # Insertar la importación
    lines.insert(insert_position, 'from django.conf import settings')
    
    # Escribir el archivo
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Agregada importación: {file_path}")
    return True

def main():
    """Función principal."""
    # Archivos que necesitan la importación de settings
    files_to_fix = [
        'app/ats/gamification/models.py',
        'app/ats/learning/models/learning_path.py',
        'app/ats/learning/models/enrollment.py',
        'app/ats/accounting/models.py',
        'app/ats/pricing/models.py',
        'app/ats/publish/models.py',
        'app/ats/client_portal/models.py',
        'app/ats/core/offlimits/models.py',
        'app/sexsi/models.py',
        'app/payroll/models.py',
        'app/ml/feedback/feedback_system.py',
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if add_settings_import(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  Archivo no encontrado: {file_path}")
    
    print(f"\n🎉 Proceso completado. {fixed_count} archivos corregidos.")

if __name__ == "__main__":
    main() 