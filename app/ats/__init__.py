"""Módulo ATS (Applicant Tracking System)."""

# Configuración del módulo
default_app_config = 'app.ats.apps.AtsConfig'

# Configuración de logging
import logging
logger = logging.getLogger(__name__)
logger.info("Módulo ATS inicializado correctamente") 