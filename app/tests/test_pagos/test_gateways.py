# /home/pablo/app/tests/test_pagos/test_gateways.py
#
# Implementación para el módulo. Proporciona funcionalidad específica del sistema.

import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from app.pagos.gateways import PaymentGateway, StripeGateway, PayPalGateway, MercadoPagoGateway
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

    @patch('app.pagos.gateways.PaymentGateway.create_payment')
    def test_base_create_payment(self, mock_create):
        """Test de creación de pago base."""
        gateway = PaymentGateway(self.business_unit)
        mock_create.return_value = {'success': True, 'id': 'test_payment'}
        result = gateway.create_payment(self.amount, self.currency, self.description)
        self.assertTrue(result['success'])

    @patch('app.pagos.gateways.PaymentGateway.execute_payment')
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
