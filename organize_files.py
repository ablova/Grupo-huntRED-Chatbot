#!/usr/bin/env python3
"""
Script para estandarizar los archivos en el proyecto Grupo huntRED®.

Este script añade un encabezado estándar a cada archivo que incluye:
- Ruta completa del archivo (/home/pablo/...)
- Descripción breve de la función del archivo

Organiza views, tests y urls.py según su módulo/submódulo para mantener consistencia.
"""

import os
import glob
import argparse
import logging
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('organize_files')

# Descripciones estándar por tipo de archivo
DESCRIPTIONS = {
    'urls.py': 'Configuración de URLs para el módulo. Define endpoints, vistas y patrones de URL.',
    'views': 'Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.',
    'tests': 'Pruebas para el módulo. Verifica la correcta funcionalidad de componentes específicos.',
    'models.py': 'Definición de modelos de datos para el módulo. Establece la estructura de la base de datos.',
    'admin.py': 'Configuración del panel de administración. Personaliza la gestión de modelos.',
    'forms.py': 'Formularios para el módulo. Gestiona la validación y procesamiento de datos de entrada.',
    'tasks.py': 'Tareas asíncronas para el módulo. Define procesos en segundo plano con Celery.',
    'utils': 'Utilidades para el módulo. Proporciona funciones auxiliares reutilizables.',
    'middleware': 'Middleware para el módulo. Intercepta peticiones y respuestas para procesamiento adicional.',
    'integrations': 'Integraciones con servicios externos. Implementa conexiones y adaptadores.',
    'workflow': 'Flujos de trabajo para el módulo. Define secuencias de operaciones y estados.',
    'serializers.py': 'Serializadores para el módulo. Convierte objetos complejos a/desde formatos transferibles.',
    'signals.py': 'Señales para el módulo. Define eventos y manejadores para comunicación interna.'
}

def get_description(file_path):
    """
    Determina la descripción adecuada para un archivo basado en su ruta.
    """
    file_name = os.path.basename(file_path)
    dir_name = os.path.basename(os.path.dirname(file_path))
    
    # Primero, verificar coincidencias exactas
    if file_name in DESCRIPTIONS:
        return DESCRIPTIONS[file_name]
    
    # Luego, verificar por directorio
    for key in DESCRIPTIONS:
        if key in file_name or key == dir_name:
            return DESCRIPTIONS[key]
    
    # Descripción genérica si no hay coincidencias
    return "Implementación para el módulo. Proporciona funcionalidad específica del sistema."

def add_header_to_file(file_path, dry_run=False):
    """
    Añade un encabezado estándar al archivo especificado.
    """
    try:
        # Leer el contenido actual
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Determinar si ya tiene un encabezado
        has_header = False
        if lines and lines[0].startswith('# /home/pablo/'):
            has_header = True
        
        if has_header:
            logger.info(f"El archivo ya tiene un encabezado: {file_path}")
            return True
        
        # Crear el nuevo encabezado
        # Convertir la ruta al formato esperado
        normalized_path = file_path.replace('\\', '/')
        if '/Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/' in normalized_path:
            rel_path = normalized_path.split('/Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/')[1]
            header_path = f"/home/pablo/{rel_path}"
        else:
            header_path = f"/home/pablo/{normalized_path}"
        
        # Obtener la descripción apropiada
        description = get_description(file_path)
        
        # Crear nuevo encabezado
        header = f"# {header_path}\n#\n# {description}\n\n"
        
        # Omitir cualquier comentario existente al inicio
        start_index = 0
        while start_index < len(lines) and (lines[start_index].startswith('#') or lines[start_index].strip() == ''):
            start_index += 1
        
        # Construir nuevo contenido
        new_content = header + ''.join(lines[start_index:])
        
        # Guardar el archivo si no es un dry run
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"Encabezado añadido a: {file_path}")
        else:
            logger.info(f"[DRY RUN] Se añadiría encabezado a: {file_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error al procesar {file_path}: {e}")
        return False

def process_files(base_dir, dry_run=False):
    """
    Procesa todos los archivos views, tests y urls.py en la base de código.
    """
    # Patrones de archivos a procesar
    patterns = [
        "app/**/views/**/*.py",
        "app/**/views.py",
        "app/**/tests/**/*.py",
        "app/**/tests.py",
        "app/**/urls.py"
    ]
    
    # Contadores para estadísticas
    stats = {
        'total': 0,
        'processed': 0,
        'skipped': 0,
        'failed': 0
    }
    
    # Procesar cada patrón
    for pattern in patterns:
        full_pattern = os.path.join(base_dir, pattern)
        
        # Encontrar archivos que coincidan con el patrón
        for file_path in glob.glob(full_pattern, recursive=True):
            stats['total'] += 1
            
            # Verificar si debemos procesar este archivo
            result = add_header_to_file(file_path, dry_run)
            
            if result:
                stats['processed'] += 1
            else:
                stats['failed'] += 1
    
    # Mostrar estadísticas
    logger.info(f"Procesamiento completado.")
    logger.info(f"Total de archivos: {stats['total']}")
    logger.info(f"Archivos procesados: {stats['processed']}")
    logger.info(f"Archivos omitidos: {stats['skipped']}")
    logger.info(f"Archivos fallidos: {stats['failed']}")

def main():
    """
    Función principal para ejecutar el script.
    """
    parser = argparse.ArgumentParser(description='Organizar y estandarizar archivos en el proyecto Grupo huntRED®.')
    parser.add_argument('--dry-run', action='store_true', help='Mostrar cambios sin aplicarlos')
    parser.add_argument('--base-dir', default='.', help='Directorio base del proyecto')
    
    args = parser.parse_args()
    
    # Iniciar procesamiento
    logger.info(f"Iniciando organización de archivos{'(DRY RUN)' if args.dry_run else ''}")
    process_files(args.base_dir, args.dry_run)

if __name__ == '__main__':
    main()
