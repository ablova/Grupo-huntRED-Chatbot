#Archivo: /home/pablo/app/utilidades/monitoring.py

from django.db.models import Count
from app.models import ChatState, Vacante
import logging
# En el módulo utilidades
logger = logging.getLogger(__name__)
logger.info("Inicio de la aplicación.")

def generate_dashboard_data():
    """
    Genera datos clave para el monitoreo.
    """
    data = {
        "active_chats": ChatState.objects.filter(applied=False).count(),
        "vacancies_active": Vacante.objects.filter(activa=True).count(),
        "applications_total": Vacante.objects.aggregate(total=Count('applications'))
    }
    return data