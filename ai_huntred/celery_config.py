# /Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/ai_huntred/celery_config.py
#
# Configuración de Celery para el proyecto AI HuntRED.
# Mantiene la compatibilidad con el código existente que utiliza `app` directamente.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

from ai_huntred.celery_app import app as celery_app

# Opcional: Si quieres mantener retrocompatibilidad con código que usa `app` directamente desde celery.py
app = celery_app