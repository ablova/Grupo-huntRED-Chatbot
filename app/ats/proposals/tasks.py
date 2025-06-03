from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
import os
from app.models import Proposal
from app.ats.utils.notification_handler import NotificationHandler

@shared_task
def send_proposal_email(proposal_id):
    """
    Envía un correo electrónico con la propuesta adjunta.
    
    Args:
        proposal_id: ID de la propuesta
    """
    proposal = Proposal.objects.get(id=proposal_id)
    
    # Construir el mensaje
    subject = f"Propuesta de Servicios - {proposal.company.name}"
    message = f"Estimado(a) {proposal.company.name},\n\nAdjunto encontrará nuestra propuesta de servicios para las oportunidades identificadas.\n\nAtentamente,\nEl equipo de Grupo huntRED®"
    
    # Crear el email
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[proposal.company.email],
        cc=[settings.DEFAULT_FROM_EMAIL]
    )
    
    # Adjuntar el PDF de la propuesta
    pdf_path = os.path.join(settings.MEDIA_ROOT, 'proposals', f"proposal_{proposal_id}.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            email.attach(f"proposal_{proposal_id}.pdf", f.read(), 'application/pdf')
    
    # Enviar el email
    email.send()
    
    # Notificar al equipo
    notification_handler = NotificationHandler()
    message = f"Propuesta enviada a {proposal.company.name}"
    notification_handler.send_notification(
        recipient='pablo@huntred.com',
        message=message,
        subject='Propuesta Enviada'
    )

@shared_task
def generate_monthly_report():
    """
    Genera un reporte mensual de propuestas.
    """
    from datetime import datetime, timedelta
    from django.db.models import Count, Sum
    
    # Obtener fecha de inicio del mes
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Obtener estadísticas
    proposals = Proposal.objects.filter(
        created_at__gte=start_of_month
    ).aggregate(
        total_count=Count('id'),
        total_value=Sum('pricing_total')
    )
    
    # Notificar al equipo
    notification_handler = NotificationHandler()
    message = f"Reporte Mensual de Propuestas:\n\nTotal de Propuestas: {proposals['total_count']}\nValor Total: ${proposals['total_value']:.2f}"
    notification_handler.send_notification(
        recipient='pablo@huntred.com',
        message=message,
        subject='Reporte Mensual de Propuestas'
    )
