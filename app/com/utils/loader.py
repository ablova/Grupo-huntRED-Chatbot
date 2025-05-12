# /home/pablo/app/com/utils/loader.py

import os
import json
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Ruta base para los archivos JSON
BASE_PATH = os.path.join(settings.BASE_DIR, 'app', 'com', 'utils', 'catalogs')

def load_json_file(file_name: str) -> dict:
    """
    Carga un archivo JSON desde la ruta base especificada.

    Args:
        file_name (str): Nombre del archivo JSON.

    Returns:
        dict | list: Datos cargados desde el JSON o vacío si ocurre un error.
    """
    cache_key = f"json_file_{file_name}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        logger.info(f"Cargando {file_name} desde caché")
        return cached_data

    file_path = os.path.join(BASE_PATH, file_name)
    if not os.path.exists(file_path):
        logger.error(f"Archivo no encontrado: {file_path}")
        return {} if file_name.endswith('.json') else []

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if not isinstance(data, (dict, list)):
                logger.error(f"Formato inesperado en {file_name}: se esperaba un dict o list.")
                return {}
            cache.set(cache_key, data, timeout=None)  # Almacenar sin expiración
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error de formato JSON en {file_name}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error cargando {file_name}: {e}")
        return {}

def load_unit_skills(unit_name: str) -> dict:
    """
    Carga el archivo `skills.json` específico para una unidad de negocio.

    Args:
        unit_name (str): Nombre de la unidad de negocio.

    Returns:
        dict: Habilidades específicas de la unidad de negocio.
    """
    cache_key = f"unit_skills_{unit_name}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        logger.info(f"Cargando skills.json para {unit_name} desde caché")
        return cached_data

    unit_path = os.path.join(BASE_PATH, unit_name, 'skills.json')
    if not os.path.exists(unit_path):
        logger.warning(f"No se encontró el archivo skills.json para la unidad: {unit_name}")
        return {}

    try:
        with open(unit_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            cache.set(cache_key, data, timeout=None)  # Almacenar sin expiración
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error de formato JSON en {unit_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error cargando skills.json para la unidad {unit_name}: {e}")
        return {}

# Cargar los datos desde los archivos JSON
BUSINESS_UNITS = load_json_file('business_units.json')
DIVISIONES = load_json_file('divisiones.json')
DIVISION_SKILLS = load_json_file('skills.json')

# Verificar la carga
logger.info(f"BUSINESS_UNITS: {len(BUSINESS_UNITS)} elementos cargados.")
logger.info(f"DIVISIONES: {len(DIVISIONES)} elementos cargados.")
logger.info(f"DIVISION_SKILLS: {len(DIVISION_SKILLS)} divisiones cargadas.")