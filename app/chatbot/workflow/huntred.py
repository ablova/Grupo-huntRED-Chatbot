# /home/pablo/app/chatbot/workflow/huntred.py
from celery import shared_task
from app.models import Person, Vacante, BusinessUnit, Application
from app.chatbot.workflow.common import generate_and_send_contract

@shared_task
def process_huntred_candidate(candidate_id):
    """Genera la Carta Propuesta y la envía para firma digital en HuntRED."""
    candidate = Person.objects.get(id=candidate_id)
    application = Application.objects.filter(user=candidate).first()

    if not application or not application.vacancy:
        return "Candidato sin vacante asignada."

    # Generar y enviar contrato para firma digital
    generate_and_send_contract(candidate, application.vacancy, application.vacancy.titulo, application.business_unit)

    return f"Contrato generado y enviado a {candidate.nombre}"