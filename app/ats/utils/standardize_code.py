"""
# /home/pablo/app/com/utils/standardize_code.py
#
# Herramienta de estandarización de código para el sistema huntRED®.
# Aplica encabezados estándar a archivos, organiza y formatea siguiendo las Windsurf Global Rules.
# Garantiza consistencia a través de views, tests y urls en toda la estructura modular.

import os
import sys
import re
import glob
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('standardize_code')

# Descripción estándar para tipos de archivo
FILE_TYPE_DESCRIPTIONS = {
    r'urls\.py$': 'Configuración de URLs para el módulo. Define las rutas y patrones URL para las vistas.',
    r'views/.*\.py$': 'Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.',
    r'tests/.*\.py$': 'Pruebas unitarias para el módulo. Verifica la correcta funcionalidad de componentes específicos.',
    r'models\.py$': 'Definición de modelos de datos para el módulo. Establece la estructura de la base de datos.',
    r'admin\.py$': 'Configuración del panel de administración para el módulo. Personaliza la interfaz de administración.',
    r'forms\.py$': 'Formularios para el módulo. Gestiona la validación y procesamiento de datos de entrada.',
    r'middleware/.*\.py$': 'Middleware para el módulo. Intercepta peticiones y respuestas para procesamiento adicional.',
    r'signals\.py$': 'Señales para el módulo. Implementa manejadores para eventos del sistema.',
    r'tasks\.py$': 'Tareas asíncronas para el módulo. Define procesos en segundo plano con Celery.',
    r'utils/.*\.py$': 'Utilidades para el módulo. Proporciona funciones auxiliares reutilizables.',
    r'serializers\.py$': 'Serializadores para el módulo. Convierte objetos complejos a/desde formatos transferibles.',
}

# Módulos principales del sistema
CORE_MODULES = [
    'chatbot', 'ml', 'pagos', 'publish', 'pricing', 'proposals', 'notifications', 
    'utils', 'workflow', 'integrations'
]

def add_standard_header(file_path: str, description: str = None, dry_run: bool = False) -> bool:
    """
Añade un encabezado estándar al archivo con la ruta completa y una descripción.
    
    Args:
        file_path: Ruta completa al archivo
        description: Descripción breve del propósito del archivo
        dry_run: Si es True, muestra los cambios pero no los aplica
        
    Returns:
        True si el encabezado se añadió correctamente, False en caso contrario
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"El archivo no existe: {file_path}")
            return False
            
        # Leer el contenido actual
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
            
        # Construir el encabezado estándar
        rel_path = file_path.split("Grupo-huntRED-Chatbot/")[-1]
        header_path = f"/home/pablo/{rel_path}"
        standard_header = f"# {header_path}\n"
        
        if description:
            standard_header += f"#\n# {description}\n"
            
        # Verificar si ya tiene un encabezado similar
        first_line = content[0].strip() if content else ""
        if first_line.startswith(f"# {header_path}"):
            logger.info(f"El archivo ya tiene un encabezado estándar: {file_path}")
            return True
            
        # Preparar el nuevo contenido
        new_content = [standard_header, "\n"]
        
        # Saltar líneas de comentarios existentes al inicio
        start_idx = 0
        while start_idx < len(content) and (
            content[start_idx].strip().startswith('#') or 
            content[start_idx].strip().startswith('"""') or 
            content[start_idx].strip().startswith("'''") or
            content[start_idx].strip() == ''
        ):
            start_idx += 1
        
        # Añadir el resto del contenido
        new_content.extend(content[start_idx:])
        
        # Aplicar los cambios si no es un dry run
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_content)
                
            logger.info(f"Encabezado estándar añadido a: {file_path}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error al añadir encabezado a {file_path}: {e}")
        return False

def get_file_description(file_path: str) -> str:
    """
    Determina la descripción adecuada para un archivo basado en su nombre y ubicación.
    
    Args:
        file_path: Ruta relativa del archivo
        
    Returns:
        Descripción apropiada para el archivo
    """
    # Búsqueda por patrón
    for pattern, desc in FILE_TYPE_DESCRIPTIONS.items():
        if re.search(pattern, file_path):
            return desc
            
    # Búsqueda por nombre de archivo
    filename = os.path.basename(file_path)
    if filename == 'urls.py':
        return "Configuración de URLs para el módulo. Define las rutas y patrones URL para las vistas."
    elif filename == 'views.py':
        return "Vistas para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP."
    elif filename == 'tests.py':
        return "Pruebas unitarias para el módulo. Verifica la correcta funcionalidad de componentes específicos."
    
    # Default
    return "Implementación para el módulo. Proporciona funcionalidad específica del sistema."

def process_directory(base_dir: str, patterns: List[str], dry_run: bool = False) -> Dict:
    """
    Procesa todos los archivos que coinciden con los patrones especificados.
    
    Args:
        base_dir: Directorio base para buscar archivos
        patterns: Lista de patrones de glob para buscar archivos
        dry_run: Si es True, muestra los cambios pero no los aplica
        
    Returns:
        Diccionario con estadísticas de procesamiento
    """
    stats = {
        'total': 0,
        'processed': 0,
        'skipped': 0,
        'errors': 0,
        'by_module': {}
    }
    
    for pattern in patterns:
        full_pattern = os.path.join(base_dir, pattern)
        
        for file_path in glob.glob(full_pattern, recursive=True):
            stats['total'] += 1
            
            # Determinar el módulo
            rel_path = os.path.relpath(file_path, base_dir)
            parts = rel_path.split(os.sep)
            
            if parts[0] == 'com' and len(parts) > 1:
                module = f"com/{parts[1]}"
            else:
                module = parts[0]
                
            # Inicializar estadísticas para el módulo
            if module not in stats['by_module']:
                stats['by_module'][module] = {
                    'total': 0,
                    'processed': 0,
                    'skipped': 0,
                    'errors': 0
                }
            
            stats['by_module'][module]['total'] += 1
            
            # Obtener la descripción adecuada
            description = get_file_description(rel_path)
            
            # Procesar el archivo
            try:
                success = add_standard_header(file_path, description, dry_run)
                
                if success:
                    logger.info(f"Procesado: {rel_path}")
                    stats['processed'] += 1
                    stats['by_module'][module]['processed'] += 1
                else:
                    logger.warning(f"Omitido: {rel_path}")
                    stats['skipped'] += 1
                    stats['by_module'][module]['skipped'] += 1
                    
            except Exception as e:
                logger.error(f"Error procesando {rel_path}: {e}")
                stats['errors'] += 1
                stats['by_module'][module]['errors'] += 1
                
    return stats

def main():
    """Función principal para ejecutar la herramienta desde línea de comandos."""
    parser = argparse.ArgumentParser(description='Estandariza archivos del sistema Grupo huntRED.')
    parser.add_argument('--base-dir', default='.', help='Directorio base del proyecto')
    parser.add_argument('--patterns', nargs='+', default=['**/views/*.py', '**/views.py', '**/tests/*.py', '**/tests.py', '**/urls.py'], 
                      help='Patrones de archivos a procesar')
    parser.add_argument('--dry-run', action='store_true', help='Muestra cambios sin aplicarlos')
    parser.add_argument('--modules', nargs='+', default=[], help='Procesar solo módulos específicos')
    
    args = parser.parse_args()
    
    # Ajustar patrones si se especificaron módulos
    if args.modules:
        patterns = []
        for module in args.modules:
            for pattern in args.patterns:
                if module == 'com':
                    patterns.append(f"com/**/{pattern}")
                else:
                    patterns.append(f"{module}/{pattern}")
    else:
        patterns = args.patterns
    
    # Procesar archivos
    logger.info(f"Iniciando estandarización con patrones: {patterns}")
    stats = process_directory(args.base_dir, patterns, args.dry_run)
    
    # Mostrar estadísticas
    logger.info("==== Resumen de procesamiento ====")
    logger.info(f"Total de archivos: {stats['total']}")
    logger.info(f"Procesados: {stats['processed']}")
    logger.info(f"Omitidos: {stats['skipped']}")
    logger.info(f"Errores: {stats['errors']}")
    logger.info("==== Por módulo ====")
    
    for module, module_stats in stats['by_module'].items():
        logger.info(f"Módulo {module}:")
        logger.info(f"  Total: {module_stats['total']}")
        logger.info(f"  Procesados: {module_stats['processed']}")
        logger.info(f"  Omitidos: {module_stats['skipped']}")
        logger.info(f"  Errores: {module_stats['errors']}")

if __name__ == "__main__":
    main()
