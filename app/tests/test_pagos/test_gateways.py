# /home/pablo/app/tests/test_pagos/test_gateways.py
#
# Implementación para el módulo. Proporciona funcionalidad específica del sistema.

import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings
import stripe
from app.ats.pagos.gateways import PaymentGateway, StripeGateway, PayPalGateway, MercadoPagoGateway
from app.models import ApiConfig

class PaymentGatewayTest(TestCase):
    def setUp(self):
        self.business_unit = 'huntRED'
        self.amount = 100.0
        self.currency = 'MXN'
        self.description = 'Prueba de pago'

    def test_base_gateway_creation(self):
        """Test de creación de gateway base."""
        gateway = PaymentGateway(self.business_unit)
        self.assertEqual(gateway.business_unit, self.business_unit)

    @patch('app.ats.pagos.gateways.PaymentGateway.create_payment')
    def test_base_create_payment(self, mock_create):
        """Test de creación de pago base."""
        gateway = PaymentGateway(self.business_unit)
        mock_create.return_value = {'success': True, 'id': 'test_payment'}
        result = gateway.create_payment(self.amount, self.currency, self.description)
        self.assertTrue(result['success'])

    @patch('app.ats.pagos.gateways.PaymentGateway.execute_payment')
    def test_base_execute_payment(self, mock_execute):
        """Test de ejecución de pago base."""
        gateway = PaymentGateway(self.business_unit)
        mock_execute.return_value = {'success': True, 'status': 'completed'}
        result = gateway.execute_payment('test_payment')
        self.assertTrue(result['success'])

class StripeGatewayTest(TestCase):
    @patch('stripe.PaymentIntent.create')
    def test_stripe_create_payment(self, mock_create):
        """Test de creación de pago con Stripe."""
        mock_create.return_value = MagicMock(id='stripe_payment_123', client_secret='secret_123')
        gateway = StripeGateway()
        result = gateway.create_payment(100.0, 'MXN', 'Prueba')
        self.assertTrue(result['success'])
        self.assertEqual(result['id'], 'stripe_payment_123')

class PayPalGatewayTest(TestCase):
    @patch('paypalrestsdk.Payment.create')
    def test_paypal_create_payment(self, mock_create):
        """Test de creación de pago con PayPal."""
        mock_create.return_value = True
        gateway = PayPalGateway()
        result = gateway.create_payment(100.0, 'MXN', 'Prueba')
        self.assertTrue(result['success'])

class MercadoPagoGatewayTest(TestCase):
    @patch('mercadopago.SDK.create_payment')
    def test_mercadopago_create_payment(self, mock_create):
        """Test de creación de pago con MercadoPago."""
        mock_create.return_value = {'status': 201, 'response': {'id': 'mp_payment_123'}}
        gateway = MercadoPagoGateway()
        result = gateway.create_payment(100.0, 'MXN', 'Prueba')
        self.assertTrue(result['success'])
        self.assertEqual(result['id'], 'mp_payment_123')

class StripeGatewayTests(TestCase):
    def setUp(self):
        """Set up test dependencies and mock Stripe API key."""
        self.gateway = StripeGateway()
        settings.STRIPE_SECRET_KEY = 'test_secret_key'
        settings.STRIPE_CURRENCY = 'usd'

    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_success(self, mock_create):
        """Test successful creation of a payment intent."""
        mock_create.return_value = {'id': 'pi_123', 'status': 'requires_payment_method'}
        intent = self.gateway.create_payment_intent(100.00, "Test Payment", {'order_id': '123'})
        self.assertEqual(intent['id'], 'pi_123')
        mock_create.assert_called_once_with(
            amount=10000,
            currency='usd',
            description="Test Payment",
            metadata={'order_id': '123'},
            automatic_payment_methods={'enabled': True}
        )

    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_stripe_error(self, mock_create):
        """Test handling of Stripe API error during payment intent creation."""
        mock_create.side_effect = stripe.error.StripeError("API Error")
        with self.assertRaisesMessage(Exception, "Stripe error: API Error"):
            self.gateway.create_payment_intent(100.00, "Test Payment")

    @patch('stripe.PaymentIntent.confirm')
    def test_confirm_payment_intent_success(self, mock_confirm):
        """Test successful confirmation of a payment intent."""
        mock_confirm.return_value = {'id': 'pi_123', 'status': 'succeeded'}
        intent = self.gateway.confirm_payment_intent('pi_123')
        self.assertEqual(intent['status'], 'succeeded')
        mock_confirm.assert_called_once_with('pi_123')

    @patch('stripe.PaymentIntent.confirm')
    def test_confirm_payment_intent_error(self, mock_confirm):
        """Test handling of error during payment intent confirmation."""
        mock_confirm.side_effect = stripe.error.StripeError("Confirmation Error")
        with self.assertRaisesMessage(Exception, "Stripe error: Confirmation Error"):
            self.gateway.confirm_payment_intent('pi_123')

    @patch('stripe.Refund.create')
    def test_refund_payment_success(self, mock_refund):
        """Test successful refund of a payment."""
        mock_refund.return_value = {'id': 're_123', 'status': 'succeeded'}
        refund = self.gateway.refund_payment('ch_123', 50.00)
        self.assertEqual(refund['id'], 're_123')
        mock_refund.assert_called_once_with(charge='ch_123', amount=5000)

    @patch('stripe.Refund.create')
    def test_refund_payment_full_amount(self, mock_refund):
        """Test full refund of a payment without specifying amount."""
        mock_refund.return_value = {'id': 're_123', 'status': 'succeeded'}
        refund = self.gateway.refund_payment('ch_123')
        self.assertEqual(refund['id'], 're_123')
        mock_refund.assert_called_once_with(charge='ch_123')

    @patch('stripe.Refund.create')
    def test_refund_payment_error(self, mock_refund):
        """Test handling of error during refund processing."""
        mock_refund.side_effect = stripe.error.StripeError("Refund Error")
        with self.assertRaisesMessage(Exception, "Stripe error: Refund Error"):
            self.gateway.refund_payment('ch_123', 50.00)

    @patch('stripe.PaymentIntent.retrieve')
    def test_get_payment_status_success(self, mock_retrieve):
        """Test successful retrieval of payment intent status."""
        mock_retrieve.return_value = {'id': 'pi_123', 'status': 'succeeded'}
        status = self.gateway.get_payment_status('pi_123')
        self.assertEqual(status, 'succeeded')
        mock_retrieve.assert_called_once_with('pi_123')

    @patch('stripe.PaymentIntent.retrieve')
    def test_get_payment_status_error(self, mock_retrieve):
        """Test handling of error during payment status retrieval."""
        mock_retrieve.side_effect = stripe.error.StripeError("Status Error")
        with self.assertRaisesMessage(Exception, "Stripe error: Status Error"):
            self.gateway.get_payment_status('pi_123')
