# /home/pablo/app/views/candidates.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from app.models import Proposal, Opportunity, Person, Vacancy
from app.proposals.qrcode_generator import QRCodeGenerator
from datetime import timedelta

class CandidateNotification:
    def __init__(self, opportunity):
        self.opportunity = opportunity
        
    def generate_notification(self):
        """
        Genera y envía la notificación con candidatos potenciales.
        """
        # Verificar si hay una propuesta asociada
        proposal = self.opportunity.proposals.first()
        if not proposal:
            return False
            
        # Generar QR code si no existe
        if not proposal.qr_code:
            qr_generator = QRCodeGenerator(proposal)
            qr_generator.generate_qr_code()
            
        # Preparar datos para el template
        context = {
            'opportunity': self.opportunity,
            'proposal': proposal,
            'qr_code_url': f"https://{settings.DOMAIN}{settings.MEDIA_URL}{proposal.qr_code}",
            'proposal_url': f"https://{settings.DOMAIN}/proposals/{proposal.id}/"
        }
        
        # Renderizar template
        html_message = render_to_string('emails/candidate_notification.html', context)
        
        # Enviar correo
        send_mail(
            subject=f"Candidatos Potenciales para {self.opportunity.title}",
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.opportunity.company.email],
            html_message=html_message
        )
        
        return True

    def process_approval(self, proposal_id):
        """
        Procesa la aprobación de la propuesta y actualiza los CVs.
        """
        proposal = Proposal.objects.get(id=proposal_id)
        
        # Actualizar estado de la propuesta
        proposal.status = 'APPROVED'
        proposal.save()
        
        # Actualizar CVs de candidatos
        for vacancy in proposal.vacancies.all():
            for candidate in vacancy.candidates.all():
                if candidate.cv_blind:
                    candidate.cv = candidate.cv_blind
                    candidate.cv_blind = None
                    candidate.save()
        
        return True
