# /home/pablo/app/tests/test_pricing.py
#
# Pruebas para el módulo. Verifica la correcta funcionalidad de componentes específicos.

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from app.models import (
    Proposal, Contract, PaymentMilestone, BusinessUnit, Company, Vacante, Person
)
from app.ats.pricing.utils import calculate_pricing


class PricingModelsTestCase(TestCase):
    def setUp(self):
        # Crear datos de prueba
        self.company = Company.objects.create(
            name="Test Company",
            industry="Technology",
            size="50-200 employees"
        )

        self.business_unit = BusinessUnit.objects.create(
            name="huntU",
            description="Test Business Unit"
        )

        self.person = Person.objects.create(
            nombre="Test",
            apellido_paterno="User",
            email="test@example.com"
        )

        self.worker = Worker.objects.create(
            person=self.person,
            company=self.company,
            name="Test Worker"
        )

        self.vacancy = Vacante.objects.create(
            titulo="Test Job",
            empresa=self.worker,
            business_unit=self.business_unit,
            salario=100000,
            ubicacion="CDMX"
        )

    def test_proposal_creation(self):
        """Test de creación de propuesta"""
        proposal = Proposal.objects.create(
            company=self.company
        )
        proposal.business_units.add(self.business_unit)
        proposal.vacancies.add(self.vacancy)

        self.assertEqual(proposal.business_units.count(), 1)
        self.assertEqual(proposal.vacancies.count(), 1)
        self.assertEqual(proposal.status, 'DRAFT')

    def test_contract_creation(self):
        """Test de creación de contrato"""
        proposal = Proposal.objects.create(
            company=self.company
        )
        proposal.business_units.add(self.business_unit)
        proposal.vacancies.add(self.vacancy)

        contract = Contract.objects.create(
            proposal=proposal
        )

        self.assertIsNotNone(contract.pdf_file)
        self.assertEqual(contract.status, 'PENDING_APPROVAL')

    def test_payment_milestone_creation(self):
        """Test de creación de hitos de pago"""
        proposal = Proposal.objects.create(
            company=self.company
        )
        proposal.business_units.add(self.business_unit)
        proposal.vacancies.add(self.vacancy)

        contract = Contract.objects.create(
            proposal=proposal
        )

        milestone = PaymentMilestone.objects.create(
            contract=contract,
            name="Firma del contrato",
            percentage=20,
            trigger_event="CONTRACT_SIGNING",
            due_date_offset=7
        )

        self.assertEqual(milestone.status, 'PENDING')
        self.assertEqual(milestone.percentage, 20)

    def test_calculate_pricing(self):
        """Test del cálculo de pricing"""
        proposal = Proposal.objects.create(
            company=self.company
        )
        proposal.business_units.add(self.business_unit)
        proposal.vacancies.add(self.vacancy)

        pricing_details = calculate_pricing(proposal)

        self.assertIn('total', pricing_details)
        self.assertIn('items', pricing_details)
        self.assertGreater(pricing_details['total'], 0)


class PricingViewsTestCase(TestCase):
    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

        # Crear datos de prueba
        self.company = Company.objects.create(
            name="Test Company",
            industry="Technology",
            size="50-200 employees"
        )

        self.business_unit = BusinessUnit.objects.create(
            name="huntU",
            description="Test Business Unit"
        )

        self.person = Person.objects.create(
            nombre="Test",
            apellido_paterno="User",
            email="test@example.com"
        )

        self.worker = Worker.objects.create(
            person=self.person,
            company=self.company,
            name="Test Worker"
        )

        self.vacancy = Vacante.objects.create(
            titulo="Test Job",
            empresa=self.worker,
            business_unit=self.business_unit,
            salario=100000,
            ubicacion="CDMX"
        )

    def test_proposal_list_view(self):
        """Test de la vista de lista de propuestas"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('proposal_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pricing/proposal_list.html')

    def test_proposal_create_view(self):
        """Test de la vista de creación de propuesta"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('proposal_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pricing/proposal_create.html')

    def test_proposal_detail_view(self):
        """Test de la vista de detalles de propuesta"""
        proposal = Proposal.objects.create(
            company=self.company
        )
        proposal.business_units.add(self.business_unit)
        proposal.vacancies.add(self.vacancy)

        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('proposal_detail', args=[proposal.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pricing/proposal_detail.html')
