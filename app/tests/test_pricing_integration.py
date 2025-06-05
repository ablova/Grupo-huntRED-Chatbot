# /home/pablo/app/tests/test_pricing_integration.py
#
# Pruebas para el módulo. Verifica la correcta funcionalidad de componentes específicos.

from django.test import TestCase, override_settings
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from app.models import (
    Proposal, Contract, PaymentMilestone, BusinessUnit, Company, Vacante, Person
)
from app.ats.pricing.utils import calculate_pricing, generate_proposal_pdf
from app.ats.chatbot.integrations.services import send_email, send_message
from app.tasks import send_whatsapp_message_task


class PricingIntegrationTestCase(TestCase):
    def setUp(self):
        # Crear datos de prueba
        self.company = Company.objects.create(
            name="Test Company",
            industry="Technology",
            size="50-200 employees"
        )

        self.business_unit = BusinessUnit.objects.create(
            name="huntU",
            description="Test Business Unit",
            pricing_config={
                'base_rate': '10000',
                'base_type': 'percentage',
                'addons': {
                    'recruitment': {
                        'type': 'percentage',
                        'rate': '20'
                    }
                }
            }
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

    def test_pricing_calculation(self):
        """Test del cálculo de pricing"""
        proposal = Proposal.objects.create(
            company=self.company
        )
        proposal.business_units.add(self.business_unit)
        proposal.vacancies.add(self.vacancy)

        pricing_details = calculate_pricing(proposal)

        # Verificar que el cálculo es correcto
        self.assertIn('total', pricing_details)
        self.assertIn('items', pricing_details)
        self.assertGreater(pricing_details['total'], 0)

        # Verificar que se aplican correctamente los addons
        item = pricing_details['items'][0]
        self.assertIn('recruitment', [addon['name'] for addon in item['addons']])

    def test_proposal_notification(self):
        """Test de notificaciones de propuesta"""
        proposal = Proposal.objects.create(
            company=self.company
        )
        proposal.business_units.add(self.business_unit)
        proposal.vacancies.add(self.vacancy)

        # Generar PDF
        generate_proposal_pdf(proposal)

        # Verificar que se generó el PDF
        self.assertTrue(proposal.pdf_file)

        # Enviar notificación por email
        send_email(
            subject="Nueva Propuesta",
            to_email="test@example.com",
            body="Se ha creado una nueva propuesta"
        )

        # Verificar que se envió el email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Nueva Propuesta")

    def test_contract_creation(self):
        """Test de creación de contrato"""
        proposal = Proposal.objects.create(
            company=self.company
        )
        proposal.business_units.add(self.business_unit)
        proposal.vacancies.add(self.vacancy)

        contract = Contract.objects.create(
            proposal=proposal,
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            status='PENDING_APPROVAL'
        )

        # Verificar que se crean los hitos de pago
        milestones = PaymentMilestone.objects.filter(contract=contract)
        self.assertGreater(milestones.count(), 0)

    def test_payment_milestone_notification(self):
        """Test de notificaciones de hitos de pago"""
        proposal = Proposal.objects.create(
            company=self.company
        )
        proposal.business_units.add(self.business_unit)
        proposal.vacancies.add(self.vacancy)

        contract = Contract.objects.create(
            proposal=proposal,
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            status='PENDING_APPROVAL'
        )

        milestone = PaymentMilestone.objects.create(
            contract=contract,
            name="Firma del contrato",
            percentage=20,
            trigger_event="CONTRACT_SIGNING",
            due_date_offset=7
        )

        # Simular envío de notificación por WhatsApp
        with self.settings(
            WHASTAPP_API_TOKEN='test_token',
            WHASTAPP_API_URL='http://test.whatsapp.com'
        ):
            send_whatsapp_message_task(
                recipient="52123456789",
                message="Recordatorio de pago pendiente",
                business_unit_id=self.business_unit.id
            )

        # Verificar que se envió la notificación
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Recordatorio de pago")
