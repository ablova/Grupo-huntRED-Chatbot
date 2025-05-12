# /home/pablo/app/tests/proposals/tests.py
#
# Pruebas para el módulo. Verifica la correcta funcionalidad de componentes específicos.

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Proposal, Opportunity, Vacancy, Person
from app.views.proposals import ProposalView
from app.pricing.utils import calculate_pricing
from datetime import timedelta

class ProposalViewTests(TestCase):
    def setUp(self):
        """
        Configura los datos de prueba.
        """
        self.company = Person.objects.create(
            name="Test Company",
            email="test@company.com",
            phone="1234567890"
        )
        
        self.opportunity = Opportunity.objects.create(
            company=self.company,
            title="Test Opportunity",
            industry="tech",
            location="Mexico City",
            salary_range=100000,
            source="scraping",
            status="active"
        )
        
        self.vacancy = Vacancy.objects.create(
            opportunity=self.opportunity,
            title="Test Vacancy",
            salary=100000,
            location="Mexico City",
            seniority_level="senior"
        )
        
    def test_generate_proposal(self):
        """
        Testea la generación de una propuesta.
        """
        response = self.client.post(
            reverse('generate_proposal', args=[self.opportunity.id])
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que se creó la propuesta
        proposal = Proposal.objects.first()
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.company, self.company)
        
    def test_convert_to_contract(self):
        """
        Testea la conversión de propuesta a contrato.
        """
        # Crear propuesta de prueba
        pricing = calculate_pricing(self.opportunity.id)
        proposal = Proposal.objects.create(
            company=self.company,
            pricing_total=pricing['total'],
            pricing_details=pricing
        )
        proposal.vacancies.add(self.vacancy)
        
        response = self.client.post(
            reverse('convert_to_contract', args=[proposal.id])
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que se creó el contrato
        from app.models import Contract
        contract = Contract.objects.first()
        self.assertIsNotNone(contract)
        self.assertEqual(contract.proposal, proposal)
        
    def test_proposal_email_notification(self):
        """
        Testea la notificación por email de una propuesta.
        """
        from app.proposals.tasks import send_proposal_email
        
        # Crear propuesta de prueba
        pricing = calculate_pricing(self.opportunity.id)
        proposal = Proposal.objects.create(
            company=self.company,
            pricing_total=pricing['total'],
            pricing_details=pricing
        )
        proposal.vacancies.add(self.vacancy)
        
        # Enviar email
        send_proposal_email(proposal.id)
        
        # Verificar que se envió el email
        from django.core import mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.company.email])
