# Ubicación: /home/pablollh/app/utilidades/catalogs.py

import json
import logging
from app.utilidades.loader import BUSINESS_UNITS, DIVISIONES, load_unit_skills

logger = logging.getLogger(__name__)


# Caché simple para skills
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
    Se utiliza como base el archivo 'skill_db_relax_20.json'. Además, si se
    encuentran habilidades adicionales mediante load_unit_skills, se fusionan,
    evitando duplicados.
    """
    if unit_name in _skills_cache:
        logger.debug(f"Skills para {unit_name} obtenidas de caché.")
        return _skills_cache[unit_name]
    
    try:
        with open("/home/pablollh/skills_data/skill_db_relax_20.json", 'r', encoding='utf-8') as f:
            base_skills = json.load(f)
        logger.info("Se cargaron las habilidades base desde skill_db_relax_20.json.")
    except Exception as e:
        logger.error(f"Error al cargar skill_db_relax_20.json: {e}", exc_info=True)
        base_skills = {}

    try:
        additional_skills = load_unit_skills(unit_name)
        if additional_skills:
            logger.info(f"Se encontraron habilidades adicionales para {unit_name}.")
        else:
            logger.info(f"No se encontraron habilidades adicionales para {unit_name}.")
    except Exception as e:
        logger.error(f"Error al cargar habilidades adicionales para {unit_name}: {e}", exc_info=True)
        additional_skills = {}

    # Fusionar las dos fuentes sin duplicados
    merged_skills = base_skills.copy()
    if additional_skills:
        for division, roles in additional_skills.items():
            if division in merged_skills:
                for role, attributes in roles.items():
                    if role in merged_skills[division]:
                        for key in ["Habilidades Técnicas", "Habilidades Blandas"]:
                            base_list = merged_skills[division][role].get(key, [])
                            add_list = attributes.get(key, [])
                            merged_list = list(set(base_list) | set(add_list))
                            merged_skills[division][role][key] = merged_list
                    else:
                        merged_skills[division][role] = attributes
            else:
                merged_skills[division] = roles

    _skills_cache[unit_name] = merged_skills
    return merged_skills

def validate_skill_in_unit(skill: str, unit_name: str) -> bool:
    skills = get_skills_for_unit(unit_name)
    all_skills = []
    for division, roles in skills.items():
        for role, attributes in roles.items():
            all_skills.extend(attributes.get("Habilidades Técnicas", []))
            all_skills.extend(attributes.get("Habilidades Blandas", []))
    return skill.lower() in [s.lower() for s in all_skills]

def get_all_skills_for_unit(unit_name: str) -> list:
    skills = get_skills_for_unit(unit_name)
    all_skills = []
    for division, roles in skills.items():
        for role, attributes in roles.items():
            all_skills.extend(attributes.get("Habilidades Técnicas", []))
            all_skills.extend(attributes.get("Habilidades Blandas", []))
    return list(set(all_skills))

def map_skill_to_database(skill, database_skills):
    return skill if skill in database_skills else None

