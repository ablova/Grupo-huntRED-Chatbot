# Ubicación: /home/pablo/app/utilidades/catalogs.py

import json
import logging
from app.utilidades.loader import BUSINESS_UNITS, DIVISIONES, load_unit_skills

logger = logging.getLogger(__name__)

# Caché simple para skills (opcional)
_skills_cache = {}

def get_business_units() -> list:
    """
    Devuelve las unidades de negocio disponibles.
    """
    return BUSINESS_UNITS

def get_divisiones() -> list:
    """
    Devuelve las divisiones disponibles.
    """
    return DIVISIONES

def get_skills_for_unit(unit_name: str) -> dict:
    """
    Devuelve las habilidades específicas para una unidad de negocio.
    Se utiliza caché para evitar recargas repetidas.
    
    Args:
        unit_name (str): Nombre de la unidad de negocio.
        
    Returns:
        dict: Diccionario con habilidades técnicas y blandas, o vacío si no se encuentra.
    """
    if unit_name in _skills_cache:
        logger.debug(f"Skills para {unit_name} obtenidas de caché.")
        return _skills_cache[unit_name]
    try:
        skills = load_unit_skills(unit_name)
        if not skills:
            logger.warning(f"No se encontraron habilidades para la unidad: {unit_name}")
            skills = {}
    except Exception as e:
        logger.error(f"Error al cargar skills para {unit_name}: {e}", exc_info=True)
        skills = {}
    _skills_cache[unit_name] = skills
    return skills

def validate_skill_in_unit(skill: str, unit_name: str) -> bool:
    """
    Valida si una habilidad pertenece a una unidad de negocio específica.
    
    Args:
        skill (str): Habilidad a validar.
        unit_name (str): Unidad de negocio donde buscar la habilidad.
        
    Returns:
        bool: True si la habilidad pertenece a la unidad, False de lo contrario.
    """
    skills = get_skills_for_unit(unit_name)
    all_skills = []
    for division, roles in skills.items():
        for role, attributes in roles.items():
            all_skills.extend(attributes.get("Habilidades Técnicas", []))
            all_skills.extend(attributes.get("Habilidades Blandas", []))
    return skill.lower() in [s.lower() for s in all_skills]

def get_all_skills_for_unit(unit_name: str) -> list:
    """
    Devuelve todas las habilidades (técnicas y blandas) para una unidad de negocio.
    
    Args:
        unit_name (str): Nombre de la unidad de negocio.
        
    Returns:
        list: Lista de todas las habilidades encontradas, sin duplicados.
    """
    skills = get_skills_for_unit(unit_name)
    all_skills = []
    for division, roles in skills.items():
        for role, attributes in roles.items():
            all_skills.extend(attributes.get("Habilidades Técnicas", []))
            all_skills.extend(attributes.get("Habilidades Blandas", []))
    return list(set(all_skills))
