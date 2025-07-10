# /home/pablo/app/com/utils/loader.py

import os
import json
import logging
from typing import Dict, List, Any
from pathlib import Path
from django.conf import settings
from django.core.cache import cache

# Configurar logger
logger = logging.getLogger(__name__)

# Definir rutas base
import tempfile
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = Path("/tmp/grupo-huntred-data")
CONFIG_DIR = DATA_DIR / "catalogs"

# Asegurar que los directorios existan
DATA_DIR.mkdir(exist_ok=True, parents=True)
CONFIG_DIR.mkdir(exist_ok=True, parents=True)

# Asegurar que los directorios existan
DATA_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

# Archivos de configuración
BUSINESS_UNITS_FILE = CONFIG_DIR / "business_units.json"
DIVISIONES_FILE = CONFIG_DIR / "divisiones.json"
SKILLS_FILE = CONFIG_DIR / "skills.json"

# Estructuras de datos globales
BUSINESS_UNITS: Dict[str, Any] = {}
DIVISIONES: Dict[str, Any] = {}
DIVISION_SKILLS: Dict[str, List[str]] = {}

def load_business_units() -> Dict[str, Any]:
    """Carga las unidades de negocio desde el archivo de configuración."""
    try:
        if BUSINESS_UNITS_FILE.exists():
            with open(BUSINESS_UNITS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Crear archivo con estructura básica si no existe
            default_units = {
                "IT": {
                    "name": "Tecnología",
                    "description": "Unidad de Tecnología e Innovación",
                    "skills": []
                },
                "HR": {
                    "name": "Recursos Humanos",
                    "description": "Unidad de Recursos Humanos",
                    "skills": []
                }
            }
            with open(BUSINESS_UNITS_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_units, f, indent=4, ensure_ascii=False)
            return default_units
    except Exception as e:
        logger.error(f"Error cargando unidades de negocio: {str(e)}")
        return {}

def load_divisiones() -> Dict[str, Any]:
    """Carga las divisiones desde el archivo de configuración."""
    try:
        if DIVISIONES_FILE.exists():
            with open(DIVISIONES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Crear archivo con estructura básica si no existe
            default_divisiones = {
                "DEV": {
                    "name": "Desarrollo",
                    "business_unit": "IT",
                    "skills": []
                },
                "QA": {
                    "name": "Calidad",
                    "business_unit": "IT",
                    "skills": []
                }
            }
            with open(DIVISIONES_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_divisiones, f, indent=4, ensure_ascii=False)
            return default_divisiones
    except Exception as e:
        logger.error(f"Error cargando divisiones: {str(e)}")
        return {}

def load_unit_skills() -> Dict[str, List[str]]:
    """Carga las habilidades por unidad de negocio."""
    try:
        if SKILLS_FILE.exists():
            with open(SKILLS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Crear archivo con estructura básica si no existe
            default_skills = {
                "IT": [
                    "Python",
                    "Java",
                    "JavaScript",
                    "SQL",
                    "DevOps"
                ],
                "HR": [
                    "Recruitment",
                    "Employee Relations",
                    "Training",
                    "Compensation"
                ]
            }
            with open(SKILLS_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_skills, f, indent=4, ensure_ascii=False)
            return default_skills
    except Exception as e:
        logger.error(f"Error cargando habilidades: {str(e)}")
        return {}

# Cargar datos al importar el módulo
BUSINESS_UNITS = load_business_units()
DIVISIONES = load_divisiones()
DIVISION_SKILLS = load_unit_skills()

# Logging de carga
logger.info(f"BUSINESS_UNITS: {len(BUSINESS_UNITS)} unidades de negocio cargadas")
logger.info(f"DIVISIONES: {len(DIVISIONES)} divisiones cargadas")
logger.info(f"DIVISION_SKILLS: {len(DIVISION_SKILLS)} conjuntos de habilidades cargados")

# Ruta base para los archivos JSON
BASE_PATH = Path(settings.BASE_DIR) / 'app' / 'com' / 'utils' / 'catalogs'

# Crear el directorio si no existe
BASE_PATH.mkdir(parents=True, exist_ok=True)

def load_json_file(file_name: str, use_cache: bool = False) -> dict:
    """
    Carga un archivo JSON desde la ruta base especificada.
    Si el archivo no existe, devuelve un diccionario vacío.

    Args:
        file_name (str): Nombre del archivo JSON.
        use_cache (bool): Indica si se debe usar la caché. Por defecto es False.

    Returns:
        dict: Datos cargados desde el JSON o diccionario vacío si hay error.
    """
    file_path = CONFIG_DIR / file_name
    
    # Definir cache_key aquí para que esté disponible en todo el método
    cache_key = f"json_file_{file_name}"
    
    # Verificar si los datos están en caché (solo si use_cache es True)
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Datos cargados desde caché para {file_name}")
            return cached_data
    
    # Si no está en caché o no se debe usar caché, cargar desde el archivo
    try:
        if not file_path.exists():
            logger.warning(f"Archivo no encontrado: {file_path}")
            # Si el archivo no existe, intentar crearlo con datos por defecto
            if file_name == "business_units.json":
                default_data = {
                    "huntRED": {
                        "name": "huntRED",
                        "display_name": "huntRED",
                        "description": "Middle/Top Management Recruitment",
                        "is_active": True
                    },
                    "huntU": {
                        "name": "huntU",
                        "display_name": "huntU",
                        "description": "University Graduates Recruitment",
                        "is_active": True
                    },
                    "Amigro": {
                        "name": "Amigro",
                        "display_name": "Amigro",
                        "description": "Migrant Job Opportunities",
                        "is_active": True
                    },
                    "huntRED_Executive": {
                        "name": "huntRED_Executive",
                        "display_name": "huntRED Executive",
                        "description": "C-level/Board Recruitment",
                        "is_active": True
                    },
                    "SEXSI": {
                        "name": "SEXSI",
                        "display_name": "SEXSI",
                        "description": "Intimate Contracts",
                        "is_active": True
                    },
                    "MilkyLeak": {
                        "name": "MilkyLeak",
                        "display_name": "MilkyLeak",
                        "description": "Social Media Project",
                        "is_active": True
                    }
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Archivo {file_name} creado con datos por defecto en {file_path}")
                return default_data
            elif file_name == "divisiones.json":
                default_data = {
                    "Tecnología": "Tecnología",
                    "Ventas": "Ventas",
                    "Marketing": "Marketing",
                    "Recursos Humanos": "Recursos Humanos",
                    "Finanzas": "Finanzas",
                    "Operaciones": "Operaciones",
                    "Legal": "Legal",
                    "Servicio al Cliente": "Servicio al Cliente"
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Archivo {file_name} creado con datos por defecto en {file_path}")
                return default_data
            return {}
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Guardar en caché por 1 hora
        cache.set(cache_key, data, timeout=3600)
        logger.debug(f"Datos cargados desde archivo: {file_path}")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON en {file_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error inesperado al cargar {file_path}: {e}")
        logger.exception("Detalles del error:")
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
try:
    BUSINESS_UNITS = load_json_file('business_units.json')
    DIVISIONES = load_json_file('divisiones.json')
    logger.info(f"Business units cargadas: {list(BUSINESS_UNITS.keys())}")
    logger.info(f"Divisiones cargadas: {list(DIVISIONES.keys())}")
except Exception as e:
    logger.error(f"Error al cargar datos iniciales: {e}")
    logger.exception("Detalles del error:")
    # Inicializar con diccionarios vacíos para evitar errores
    BUSINESS_UNITS = {}
    DIVISIONES = {}
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