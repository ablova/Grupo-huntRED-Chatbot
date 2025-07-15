#!/usr/bin/env python3
"""
Script para corregir referencias incorrectas a User en modelos Django.
"""

import os
import re

def fix_user_references_in_file(file_path):
    """Corrige las referencias a User en un archivo específico."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patrones para buscar y reemplazar
    patterns = [
        # ForeignKey(User, ...) -> ForeignKey(settings.AUTH_USER_MODEL, ...)
        (r'ForeignKey\(User,', 'ForeignKey(settings.AUTH_USER_MODEL,'),
        # OneToOneField(User, ...) -> OneToOneField(settings.AUTH_USER_MODEL, ...)
        (r'OneToOneField\(User,', 'OneToOneField(settings.AUTH_USER_MODEL,'),
        # ManyToManyField(User, ...) -> ManyToManyField(settings.AUTH_USER_MODEL, ...)
        (r'ManyToManyField\(User,', 'ManyToManyField(settings.AUTH_USER_MODEL,'),
        # models.ForeignKey(User, ...) -> models.ForeignKey(settings.AUTH_USER_MODEL, ...)
        (r'models\.ForeignKey\(User,', 'models.ForeignKey(settings.AUTH_USER_MODEL,'),
        # models.OneToOneField(User, ...) -> models.OneToOneField(settings.AUTH_USER_MODEL, ...)
        (r'models\.OneToOneField\(User,', 'models.OneToOneField(settings.AUTH_USER_MODEL,'),
        # models.ManyToManyField(User, ...) -> models.ManyToManyField(settings.AUTH_USER_MODEL, ...)
        (r'models\.ManyToManyField\(User,', 'models.ManyToManyField(settings.AUTH_USER_MODEL,'),
    ]
    
    original_content = content
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Solo escribir si hubo cambios
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Corregido: {file_path}")
        return True
    
    return False

def main():
    """Función principal."""
    # Archivos a procesar
    files_to_fix = [
        'app/models.py',
        'app/sexsi/models.py',
        'app/payroll/models.py',
        'app/ats/pricing/models.py',
        'app/ats/gamification/models.py',
        'app/ats/learning/models/learning_path.py',
        'app/ats/learning/models/enrollment.py',
        'app/ats/accounting/models.py',
        'app/ml/feedback/feedback_system.py',
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_user_references_in_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  Archivo no encontrado: {file_path}")
    
    print(f"\n🎉 Proceso completado. {fixed_count} archivos corregidos.")

if __name__ == "__main__":
    main() 