# /home/pablo/app/chatbot/workflow/executive.py
import logging
from celery import shared_task
from app.models import Person, Vacante, BusinessUnit, Application
from app.chatbot.workflow.common import generate_and_send_contract

logger = logging.getLogger(__name__)


@shared_task
def process_executive_candidate(candidate_id):
    """Genera la Carta Propuesta y la envía para firma digital en HuntRED Executive."""
    candidate = Person.objects.get(id=candidate_id)
    application = Application.objects.filter(user=candidate).first()

    if not application or not application.vacancy:
        return "Candidato sin vacante asignada."

    # Generar y enviar contrato para firma digital
    generate_and_send_contract(candidate, application.vacancy, application.vacancy.titulo, application.business_unit)

    return f"Contrato generado y enviado a {candidate.nombre}"