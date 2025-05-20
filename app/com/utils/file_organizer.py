"""
# /home/pablo/app/com/utils/file_organizer.py
#
# Utilidad para organizar archivos del sistema según estructura modular.
# Facilita la creación de encabezados estandarizados y optimiza la organización de código.
# Implementado siguiendo las Windsurf Global Rules para consistencia en la codebase.

import os
import re
import glob
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

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
            content = f.read()
            
        # Construir el encabezado estándar
        header_path = "/home/pablo/" + file_path.split("/Grupo-huntRED-Chatbot/")[1]
        standard_header = f"# {header_path}\n"
        
        if description:
            standard_header += f"#\n# {description}\n"
            
        # Verificar si ya tiene un encabezado similar
        if content.startswith(f"# {header_path}"):
            logger.info(f"El archivo ya tiene un encabezado estándar: {file_path}")
            return True
            
        # Eliminar cualquier encabezado existente que comience con #
        lines = content.split('\n')
        start_idx = 0
        
        # Saltar líneas que comienzan con # o que son docstrings al inicio
        while start_idx < len(lines) and (lines[start_idx].startswith('#') or 
                                         lines[start_idx].startswith('"""') or 
                                         lines[start_idx].startswith("'''") or
                                         lines[start_idx].strip() == ''):
            start_idx += 1
            
        # Si hay un docstring, mantenerlo pero después del encabezado
        docstring_start = -1
        for i, line in enumerate(lines):
            if line.startswith('"""') or line.startswith("'''"):
                docstring_start = i
                break
                
        # Construir el nuevo contenido
        if docstring_start >= 0 and docstring_start < start_idx:
            # Extraer el docstring y colocarlo después del encabezado
            docstring_content = '\n'.join(lines[docstring_start:start_idx])
            new_content = standard_header + '\n' + docstring_content + '\n' + '\n'.join(lines[start_idx:])
        else:
            # No hay docstring al inicio, solo agregar el encabezado
            new_content = standard_header + '\n' + '\n'.join(lines[start_idx:])
        
        # Aplicar los cambios si no es un dry run
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            logger.info(f"Encabezado estándar añadido a: {file_path}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error al añadir encabezado a {file_path}: {e}")
        return False

def organize_files_by_module(base_dir: str, file_patterns: List[str], descriptions: Dict[str, str] = None, 
                           dry_run: bool = False) -> Dict[str, List[str]]:
    """
    Organiza los archivos según módulo y añade encabezados estándar.
    
    Args:
        base_dir: Directorio base donde buscar archivos
        file_patterns: Patrones de archivos a procesar (e.g. ["**/*.py", "views/*.py"])
        descriptions: Diccionario de descripciones por patrón de archivo
        dry_run: Si es True, muestra los cambios pero no los aplica
        
    Returns:
        Diccionario con información de los archivos procesados por módulo
    """
    results = {}
    descriptions = descriptions or {}
    
    try:
        for pattern in file_patterns:
            full_pattern = os.path.join(base_dir, pattern)
            matching_files = glob.glob(full_pattern, recursive=True)
            
            for file_path in matching_files:
                # Extraer el módulo/submódulo del path
                rel_path = os.path.relpath(file_path, base_dir)
                path_parts = rel_path.split(os.sep)
                
                if len(path_parts) > 1:
                    module = path_parts[0]
                else:
                    module = "core"
                    
                # Determinar la descripción adecuada
                description = None
                for desc_pattern, desc in descriptions.items():
                    if re.search(desc_pattern, rel_path):
                        description = desc
                        break
                        
                # Añadir el encabezado estándar
                success = add_standard_header(file_path, description, dry_run)
                
                # Registrar el resultado
                if module not in results:
                    results[module] = []
                
                results[module].append({
                    'path': file_path,
                    'rel_path': rel_path,
                    'success': success
                })
                
        return results
        
    except Exception as e:
        logger.error(f"Error al organizar archivos: {e}")
        return results

def get_module_structure(base_dir: str) -> Dict[str, List[str]]:
    """
    Obtiene la estructura de módulos y submódulos del proyecto.
    
    Args:
        base_dir: Directorio base del proyecto
        
    Returns:
        Diccionario con la estructura de módulos y sus archivos
    """
    structure = {}
    
    try:
        # Buscar directorios de primer nivel (módulos)
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            
            if os.path.isdir(item_path) and not item.startswith('.') and not item.startswith('__'):
                structure[item] = []
                
                # Buscar archivos Python en este módulo
                for root, _, files in os.walk(item_path):
                    for file in files:
                        if file.endswith('.py'):
                            rel_path = os.path.relpath(os.path.join(root, file), base_dir)
                            structure[item].append(rel_path)
        
        return structure
        
    except Exception as e:
        logger.error(f"Error al obtener estructura de módulos: {e}")
        return structure
