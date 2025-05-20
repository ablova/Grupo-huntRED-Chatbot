# app/__init__.py

# Exports for app module
default_app_config = 'app.apps.AppConfig'
__all__ = ['models', 'views', 'admin', 'forms', 'api', 'tasks', 'signals']

# Inicializar el registro de módulos
# La inicialización del registro de módulos se realizará en apps.py
# después de que se complete la migración inicial

# Evitar la carga de TensorFlow durante las migraciones
import sys
import os
if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
    try:
        import tensorflow as tf
        # Configurar TensorFlow para usar CPU
        tf.config.set_visible_devices([], 'GPU')
        # Deshabilitar AVX
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    except ImportError:
        pass