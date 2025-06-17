from django.contrib import admin
from django.apps import apps

# Importar módulos de administración de forma controlada
from .notifications import *
from .chatbot import *
from .market import *
from .pricing import *
from .learning import *
from .analytics import *
from .core import *

# Lista de modelos que no deben registrarse automáticamente
EXCLUDED_MODELS = {
    'django_celery_results.TaskResult',
    'django_celery_results.GroupResult',
    'django_celery_beat.IntervalSchedule',
    'django_celery_beat.CrontabSchedule',
    'django_celery_beat.PeriodicTask',
} 