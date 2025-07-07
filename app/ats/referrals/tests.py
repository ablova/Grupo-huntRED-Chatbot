from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import ReferralProgram
from app.ats.models import Proposal

User = get_user_model()

class ReferralProgramTests(TestCase):
    def setUp(self):
        # Crear usuarios de prueba
        self.referrer = User.objects.create_user(
            username='referrer',
            email='referrer@test.com',
            password='testpass123'
        )
        self.referred = User.objects.create_user(
            username='referred',
            email='referred@test.com',
            password='testpass123'
        )
        
        # Crear cliente de prueba
        self.client = Client()
        self.client.login(username='referrer', password='testpass123')

    def test_create_referral(self):
        """Prueba la creación de una referencia"""
        response = self.client.post(reverse('referrals:create'), {
            'referred_company': 'Empresa Test',
            'commission_percentage': 10
        })
        self.assertEqual(response.status_code, 302)  # Redirección después de crear
        
        # Verificar que la referencia se creó correctamente
        referral = ReferralProgram.objects.first()
        self.assertEqual(referral.referred_company, 'Empresa Test')
        self.assertEqual(referral.commission_percentage, 10)
        self.assertEqual(referral.referrer, self.referrer)
        self.assertTrue(referral.referral_code)

    def test_invalid_commission(self):
        """Prueba la validación del porcentaje de comisión"""
        response = self.client.post(reverse('referrals:create'), {
            'referred_company': 'Empresa Test',
            'commission_percentage': 25  # Comisión inválida
        })
        self.assertEqual(response.status_code, 200)  # No redirecciona
        self.assertFormError(response, 'form', 'commission_percentage',
                           'El porcentaje de comisión debe estar entre 1% y 20%')

    def test_duplicate_referral(self):
        """Prueba la validación de referencias duplicadas"""
        # Crear primera referencia
        ReferralProgram.objects.create(
            referrer=self.referrer,
            referred_company='Empresa Test',
            commission_percentage=10
        )
        
        # Intentar crear referencia duplicada
        response = self.client.post(reverse('referrals:create'), {
            'referred_company': 'Empresa Test',
            'commission_percentage': 10
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'referred_company',
                           'Ya existe una referencia activa para esta empresa')

    def test_referral_completion(self):
        """Prueba la completación de una referencia"""
        # Crear referencia
        referral = ReferralProgram.objects.create(
            referrer=self.referrer,
            referred_company='Empresa Test',
            commission_percentage=10
        )
        
        # Crear propuesta asociada
        proposal = Proposal.objects.create(
            company=self.referred,
            total_value=1000,
            referral_code=referral.referral_code
        )
        
        # Completar referencia
        response = self.client.post(reverse('referrals:validate', args=[referral.id]))
        self.assertEqual(response.status_code, 302)
        
        # Verificar que la referencia se completó
        referral.refresh_from_db()
        self.assertTrue(referral.is_completed)
        self.assertEqual(referral.proposal, proposal)
        self.assertEqual(referral.calculate_commission(), 100)  # 10% de 1000

    def test_referral_dashboard(self):
        """Prueba el dashboard de referencias"""
        # Crear algunas referencias
        ReferralProgram.objects.create(
            referrer=self.referrer,
            referred_company='Empresa 1',
            commission_percentage=10
        )
        ReferralProgram.objects.create(
            referrer=self.referrer,
            referred_company='Empresa 2',
            commission_percentage=15,
            status=True
        )
        
        response = self.client.get(reverse('referrals:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'referrals/dashboard.html')
        
        # Verificar que se muestran las estadísticas correctas
        self.assertContains(response, 'Empresa 1')
        self.assertContains(response, 'Empresa 2')
        self.assertContains(response, '10%')
        self.assertContains(response, '15%') 