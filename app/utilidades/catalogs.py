# /home/pablollh/app/utilidades/catalogs.py

from app.utilidades.loader import BUSINESS_UNITS, DIVISIONES, load_unit_skills
import logging

logger = logging.getLogger(__name__)

def get_business_units() -> list:
    """
    Devuelve las unidades de negocio disponibles.

    Returns:
        list: Lista de unidades de negocio.
    """
    return BUSINESS_UNITS

def get_divisiones() -> list:
    """
    Devuelve las divisiones disponibles.

    Returns:
        list: Lista de divisiones.
    """
    return DIVISIONES

def get_skills_for_unit(unit_name: str) -> dict:
    """
    Devuelve las habilidades específicas para una unidad de negocio.

    Args:
        unit_name (str): Nombre de la unidad de negocio.

    Returns:
        dict: Diccionario con habilidades técnicas y blandas, o vacío si no se encuentra.
    """
    skills = load_unit_skills(unit_name)
    if not skills:
        logger.warning(f"No se encontraron habilidades para la unidad: {unit_name}")
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
        list: Lista de todas las habilidades encontradas.
    """
    skills = get_skills_for_unit(unit_name)
    all_skills = []
    for division, roles in skills.items():
        for role, attributes in roles.items():
            all_skills.extend(attributes.get("Habilidades Técnicas", []))
            all_skills.extend(attributes.get("Habilidades Blandas", []))
    return list(set(all_skills))  # Eliminar duplicados