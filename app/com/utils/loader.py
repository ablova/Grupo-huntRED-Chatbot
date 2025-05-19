# /home/pablo/app/com/utils/loader.py

import os
import json
import logging
from pathlib import Path
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Ruta base para los archivos JSON
BASE_PATH = Path(settings.BASE_DIR) / 'app' / 'com' / 'utils' / 'catalogs'

# Crear el directorio si no existe
BASE_PATH.mkdir(parents=True, exist_ok=True)

def load_json_file(file_name: str) -> dict:
    """
    Carga un archivo JSON desde la ruta base especificada.
    Si el archivo no existe, devuelve un diccionario vacío.

    Args:
        file_name (str): Nombre del archivo JSON.

    Returns:
        dict: Datos cargados desde el JSON o diccionario vacío si hay error.
    """
    try:
        cache_key = f"json_file_{file_name}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Cargando {file_name} desde caché")
            return cached_data

        file_path = BASE_PATH / file_name
        if not file_path.exists():
            logger.warning(f"Archivo no encontrado: {file_path}")
            return {}

        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if not isinstance(data, dict):
                logger.warning(f"Formato inesperado en {file_name}: se esperaba un diccionario")
                return {}
            
            # Almacenar en caché indefinidamente
            cache.set(cache_key, data, timeout=None)
            return data
            
    except Exception as e:
        logger.error(f"Error cargando {file_name}: {str(e)}", exc_info=True)
        return {}

def load_unit_skills(unit_name: str) -> dict:
    """
    Carga el archivo `skills.json` específico para una unidad de negocio.

    Args:
        unit_name (str): Nombre de la unidad de negocio.

    Returns:
        dict: Habilidades específicas de la unidad de negocio o diccionario vacío.
    """
    try:
        cache_key = f"unit_skills_{unit_name}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Cargando skills.json para {unit_name} desde caché")
            return cached_data

        unit_path = BASE_PATH / unit_name / 'skills.json'
        if not unit_path.exists():
            logger.warning(f"No se encontró el archivo skills.json para la unidad: {unit_name}")
            return {}

        with open(unit_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if not isinstance(data, dict):
                logger.warning(f"Formato inesperado en skills.json para {unit_name}")
                return {}
                
            cache.set(cache_key, data, timeout=None)
            return data
            
    except Exception as e:
        logger.error(f"Error cargando skills.json para {unit_name}: {str(e)}", exc_info=True)
        return {}

# Cargar los datos desde los archivos JSON
# Usar get() para evitar KeyError si las claves no existen
BUSINESS_UNITS = load_json_file('business_units.json')
DIVISIONES = load_json_file('divisiones.json')
DIVISION_SKILLS = load_json_file('skills.json')

# Solo registrar los logs si estamos en modo debug
if settings.DEBUG:
    logger.debug(f"BUSINESS_UNITS: {len(BUSINESS_UNITS)} elementos cargados.")
    logger.debug(f"DIVISIONES: {len(DIVISIONES)} elementos cargados.")
    logger.debug(f"DIVISION_SKILLS: {len(DIVISION_SKILLS)} divisiones cargadas.")
    for unit in BUSINESS_UNITS.keys():
        logger.debug(f"Unidad de negocio encontrada: {unit}")
else:
    logger.warning("BUSINESS_UNITS no es un diccionario")

# Verificar la carga con más detalle
if isinstance(BUSINESS_UNITS, dict):
    logger.info(f"BUSINESS_UNITS: {len(BUSINESS_UNITS)} unidades de negocio cargadas")
    for unit in BUSINESS_UNITS.keys():
        logger.debug(f"Unidad de negocio encontrada: {unit}")
else:
    logger.warning("BUSINESS_UNITS no es un diccionario")

if isinstance(DIVISIONES, dict):
    logger.info(f"DIVISIONES: {len(DIVISIONES)} divisiones cargadas")
    for division in DIVISIONES.keys():
        logger.debug(f"División encontrada: {division}")
else:
    logger.warning("DIVISIONES no es un diccionario")

if isinstance(DIVISION_SKILLS, dict):
    logger.info(f"DIVISION_SKILLS: {len(DIVISION_SKILLS)} conjuntos de habilidades cargados")
    for skill_set in DIVISION_SKILLS.keys():
        logger.debug(f"Conjunto de habilidades encontrado: {skill_set}")
else:
    logger.warning("DIVISION_SKILLS no es un diccionario")