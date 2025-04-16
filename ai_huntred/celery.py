# /home/pablollh/ai_huntred/celery.py
from .celery_app import app as celery_app

# Opcional: Si quieres mantener retrocompatibilidad con código que usa `app` directamente desde celery.py
app = celery_app