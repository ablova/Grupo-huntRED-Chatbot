# /Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/ai_huntred/config/development.py
#
# Configuración de desarrollo para AI HuntRED.
# Configura la base de datos, permisos y modo de desarrollo.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

from ai_huntred.settings import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}