#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks for Grupo huntRED®.
"""
import os
import sys
import logging
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    """Run administrative tasks."""
    # Usar configuración de desarrollo por defecto
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings.development')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        logger.error("Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable? Did you forget to activate a virtual environment?")
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
