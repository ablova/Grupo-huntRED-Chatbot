"""Módulo app."""

# Este archivo es necesario para que Python trate los directorios como paquetes

# No es necesario agregar código aquí a menos que sea específicamente requerido
# Todas las importaciones deben manejarse a través de app.imports

default_app_config = 'app.apps.AppConfig'

# Configuración de logging
import logging
logger = logging.getLogger(__name__)
logger.info("Módulo app inicializado correctamente")

# Registrar modelos adicionales (p.ej. ContactImportJob)
# from . import contact_import_job  # noqa: E402
