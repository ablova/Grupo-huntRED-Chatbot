# /home/pablo/manage.py
#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks for Grupo huntRED®.
Incorpora inicialización de las optimizaciones del sistema.
"""
import os
import sys
import logging
from pathlib import Path


def main():
    """
    Run administrative tasks with system optimizations.
    Initializes performance tracking, logging, and configuration systems.
    """
    # Configurando settings por defecto
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')
    
    # Configurar path básico del proyecto
    BASE_DIR = Path(__file__).resolve().parent
    
    try:
        from django.core.management import execute_from_command_line
        
        # Verificar si estamos en modo servidor (runserver)
        is_runserver = 'runserver' in sys.argv
        
        if is_runserver:
            # Inicializar sistemas de optimización al iniciar el servidor
            try:
                print("Inicializando sistemas de optimización Grupo huntRED®...")
                
                # Registrar inicialización de los sistemas
                initialization_steps = []
                
                # 1. Configurar sistema de logging optimizado
                try:
                    from app.utils.logging_manager import LoggingManager
                    LoggingManager.setup_logging()
                    initialization_steps.append("✓ Sistema de logging centralizado")
                except ImportError:
                    pass
                
                # 2. Inicializar configuración del sistema
                try:
                    from app.utils.system_config import initialize_system_config
                    initialize_system_config()
                    initialization_steps.append("✓ Configuración centralizada")
                except ImportError:
                    pass
                
                # 3. Inicializar tracking de rendimiento
                try:
                    from app.utils.system_optimization import PerformanceTracker
                    tracker = PerformanceTracker()
                    initialization_steps.append("✓ Monitoreo de rendimiento")
                except ImportError:
                    pass
                
                # Mostrar pasos inicializados
                for step in initialization_steps:
                    print(step)
                    
                if initialization_steps:
                    print("Sistema de optimización Grupo huntRED® inicializado correctamente.")
            except Exception as e:
                print(f"Advertencia: No se pudieron inicializar todas las optimizaciones: {str(e)}")
                logging.warning(f"Error inicializando optimizaciones: {str(e)}")
        
        # Ejecutar comando de Django
        execute_from_command_line(sys.argv)
        
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc


if __name__ == '__main__':
    main()
