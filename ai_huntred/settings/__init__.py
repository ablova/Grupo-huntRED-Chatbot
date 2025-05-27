"""
Módulo de configuración de Django para Grupo huntRED®.
"""
import os
from pathlib import Path

# Determinar el entorno actual
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')

# Importar la configuración correspondiente
if ENVIRONMENT == 'production':
    from .production import *
else:
    from .development import * 