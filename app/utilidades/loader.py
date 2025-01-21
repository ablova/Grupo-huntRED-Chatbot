# /home/pablollh/app/utilidades/loader.py

import os
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Ruta base para los archivos JSON
BASE_PATH = os.path.join(settings.BASE_DIR, 'app', 'utilidades', 'catalogs')

def load_json_file(file_name: str) -> dict:
    """
    Carga un archivo JSON desde la ruta base especificada.

    Args:
        file_name (str): Nombre del archivo JSON.

    Returns:
        dict | list: Datos cargados desde el JSON o vacío si ocurre un error.
    """
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
    unit_path = os.path.join(BASE_PATH, unit_name, 'skills.json')
    if not os.path.exists(unit_path):
        logger.warning(f"No se encontró el archivo skills.json para la unidad: {unit_name}")
        return {}

    try:
        with open(unit_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        logger.error(f"Error de formato JSON en {unit_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error cargando skills.json para la unidad {unit_name}: {e}")
        return {}


# Cargar los datos desde los archivos JSON
BUSINESS_UNITS = load_json_file('business_units.json')
DIVISIONES = load_json_file('divisiones.json')
DIVISION_SKILLS = load_unit_skills('skills.json')

# Verificar la carga
logger.info(f"BUSINESS_UNITS: {len(BUSINESS_UNITS)} elementos cargados.")
logger.info(f"DIVISIONES: {len(DIVISIONES)} elementos cargados.")
logger.info(f"DIVISION_SKILLS: {len(DIVISION_SKILLS)} divisiones cargadas.")


# ...y así para cualquier otro catálogo que tengas