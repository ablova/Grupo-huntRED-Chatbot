# app/ats/integrations/notifications/fix_lazy_loading.py
#!/usr/bin/env python

"""
Script para modificar archivos de notificaciones y aplicar patrón lazy loading.

Este script analiza todos los archivos .py en el directorio actual y modifica
aquellos que instancian servicios de notificación con BusinessUnit.objects.first()
durante la importación, aplicando un patrón de lazy loading para evitar errores
cuando la base de datos aún no está disponible durante las migraciones.
"""
import os
import re
import sys


def fix_file(file_path):
    """
    Modifica un archivo para aplicar el patrón lazy loading si es necesario.
    
    Args:
        file_path: Ruta al archivo a verificar/modificar
    
    Returns:
        bool: True si se hicieron cambios, False en caso contrario
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patrón para detectar la instanciación directa del servicio
    pattern = r'(\w+)_notifier\s*=\s*(\w+)\(BusinessUnit\.objects\.first\(\)\)'
    match = re.search(pattern, content)
    
    if not match:
        return False  # No se encontró el patrón en este archivo
    
    var_name = match.group(1)
    class_name = match.group(2)
    
    # Texto de reemplazo con el patrón lazy loading
    replacement = f"""# Utilizamos un patrón "lazy loading" para evitar consultar la base de datos durante la importación
_{var_name}_notifier = None

def get_{var_name}_notifier():
    """"Obtiene una instancia singleton del servicio de notificaciones.
    
    Utiliza lazy loading para evitar consultar la base de datos durante la importación
    del módulo.
    """"
    global _{var_name}_notifier
    if _{var_name}_notifier is None:
        from app.models import BusinessUnit
        business_unit = BusinessUnit.objects.first()
        if business_unit:
            _{var_name}_notifier = {class_name}(business_unit)
        else:
            # Fallback si no hay business_unit disponible
            _{var_name}_notifier = {class_name}(None)
    return _{var_name}_notifier

# Alias para mantener compatibilidad con código existente
{var_name}_notifier = get_{var_name}_notifier"""
    
    # Aplicar la sustitución
    new_content = re.sub(
        pattern, 
        lambda _: replacement, 
        content
    )
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    
    return False


def main():
    """Punto de entrada principal del script."""
    # Directorio donde están los archivos de notificaciones
    directory = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Buscando archivos en {directory}...")
    modified_files = []
    
    # Recorrer todos los archivos .py en el directorio
    for filename in os.listdir(directory):
        if filename.endswith('.py') and not filename.startswith('__') and filename != os.path.basename(__file__):
            file_path = os.path.join(directory, filename)
            
            if fix_file(file_path):
                modified_files.append(filename)
                print(f"✅ Modificado: {filename}")
            else:
                print(f"⏭️  Saltado: {filename}")
    
    print("\nResumen:")
    print(f"Total de archivos modificados: {len(modified_files)}")
    if modified_files:
        print("Archivos modificados:")
        for filename in modified_files:
            print(f"  - {filename}")
    else:
        print("No se encontraron archivos para modificar.")


if __name__ == "__main__":
    main()
