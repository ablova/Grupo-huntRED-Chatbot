"""Módulo de signals para Grupo huntRED®."""

import logging

logger = logging.getLogger(__name__)

# Importar signals específicos
from .user_signals import *  # noqa
from .model_signals import *  # noqa
from .system_signals import *  # noqa

logger.info("Signals inicializados correctamente") 