# /home/pablollh/app/utilidades/catalogs/loader.py

import json
import os
from django.conf import settings

def load_catalog_data():
    """
    Carga el JSON completo de catálogos y lo retorna como dict.
    """
    json_path = os.path.join(
        settings.BASE_DIR, 'app', 'utilidades', 'catalogs', 'catalogs.json'
    )
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def get_business_units():
    """
    Devuelve la lista (o dict) con las BUSINESS_UNITS.
    """
    data = load_catalog_data()
    return data.get("BUSINESS_UNITS", [])

def get_divisiones():
    data = load_catalog_data()
    return data.get("DIVISIONES", [])

def get_division_skills():
    data = load_catalog_data()
    return data.get("DIVISION_SKILLS", {})

# ...y así para cualquier otro catálogo que tengas