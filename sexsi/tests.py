# Ubicacion SEXSI -- /home/pablollh/sexsi/tests.py

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils.timezone import now, timedelta
from .models import ConsentAgreement
import uuid
import base64

class SexsiTests(TestCase):
    def setUp(self):
        """Configuración inicial antes de cada prueba"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.agreement = ConsentAgreement.objects.create(
            creator=self.user,
            invitee_contact="+521234567890",
            agreement_text="Este es un acuerdo de prueba",
            token=uuid.uuid4(),
            token_expiry=now() + timedelta(hours=24)
        )

    def test_create_agreement(self):
        """Prueba la creación de un acuerdo"""
        self.client.login(username='testuser', password='password123')
        response = self.client.post('/sexsi/create/', {
            'invitee_contact': '+529876543210',
            'agreement_text': 'Nuevo acuerdo de prueba'
        })
        self.assertEqual(response.status_code, 302)  # Debe redirigir tras la creación

    def test_sign_agreement_with_valid_token(self):
        """Prueba la firma de un acuerdo con un token válido"""
        response = self.client.post(f'/sexsi/sign/{self.agreement.id}/?token={self.agreement.token}', {
            'signature': base64.b64encode(b"firma_de_prueba").decode()
        })
        self.agreement.refresh_from_db()
        self.assertTrue(self.agreement.is_signed_by_invitee)
        self.assertEqual(response.status_code, 302)

    def test_sign_agreement_with_invalid_token(self):
        """Prueba que un token inválido no permita la firma"""
        response = self.client.post(f'/sexsi/sign/{self.agreement.id}/?token=invalid_token', {
            'signature': base64.b64encode(b"firma_de_prueba").decode()
        })
        self.assertEqual(response.status_code, 400)

    def test_biometric_signature(self):
        """Prueba la firma biométrica con datos válidos"""
        biometric_data = base64.b64encode(b"firma_biometrica_prueba").decode()
        response = self.client.post(f'/sexsi/sign/biometric/{self.agreement.id}/?token={self.agreement.token}',
                                    data={'biometric_data': biometric_data},
                                    content_type='application/json')
        self.agreement.refresh_from_db()
        self.assertTrue(self.agreement.is_signed_by_invitee)
        self.assertEqual(response.status_code, 200)

    def test_expired_token(self):
        """Prueba que un token expirado no permita la firma"""
        self.agreement.token_expiry = now() - timedelta(hours=1)
        self.agreement.save()
        response = self.client.post(f'/sexsi/sign/{self.agreement.id}/?token={self.agreement.token}', {
            'signature': base64.b64encode(b"firma_expirada").decode()
        })
        self.assertEqual(response.status_code, 400)

    def test_agreement_detail_view(self):
        """Prueba que la vista detalle del acuerdo cargue correctamente"""
        response = self.client.get(f'/sexsi/agreement/{self.agreement.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este es un acuerdo de prueba")

    def test_delete_expired_tokens_task(self):
        """Prueba que la tarea de eliminación de tokens expirados funcione correctamente"""
        self.agreement.token_expiry = now() - timedelta(hours=1)
        self.agreement.save()
        from .tasks import delete_expired_tokens
        delete_expired_tokens()
        self.agreement.refresh_from_db()
        self.assertIsNone(self.agreement.token)

    def test_send_signature_reminder_task(self):
        """Prueba que la tarea de recordatorio de firma se ejecuta correctamente"""
        from .tasks import check_pending_signatures
        response = check_pending_signatures()
        self.assertIn("Recordatorios enviados", response)
