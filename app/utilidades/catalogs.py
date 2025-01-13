# /home/pablollh/app/utilidades/catalogs.py
import json
import os
from django.conf import settings

# Ruta al archivo
JSON_PATH = os.path.join(settings.BASE_DIR, 'app', 'utilidades', 'catalogs', 'catalogs.json')

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

BUSINESS_UNITS = data["BUSINESS_UNITS"]
DIVISIONES = data["DIVISIONES"]
DIVISION_SKILLS = data["DIVISION_SKILLS"]