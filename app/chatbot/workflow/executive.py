# executive.py - Workflow para HuntRED Executive
from celery import shared_task
from app.models import Candidate, Process
from app.chatbot.workflow.common import send_candidate_summary

@shared_task
def process_executive_candidate(candidate_id):
    """ Ejecuta el workflow cuando un candidato es contratado en HuntRED Executive """
    candidate = Candidate.objects.get(id=candidate_id)
    process = Process.objects.filter(candidate=candidate).first()

    if not process or not process.client:
        return "Candidato sin proceso o cliente asignado."

    send_candidate_summary(candidate, process.client)

    send_email(
        to="legal@huntred.com",
        subject=f"Confirmación de contratación Ejecutiva: {candidate.full_name} - {candidate.position}",
        body=f"El candidato {candidate.full_name} ha sido contratado en {process.client.name} para un puesto de alto nivel."
    )

    return f"Flujo de HuntRED Executive ejecutado para {candidate.full_name}"