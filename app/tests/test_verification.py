# /home/pablo/app/tests/test_verification.py
#
# Pruebas para el módulo. Verifica la correcta funcionalidad de componentes específicos.

import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from app.models import BusinessUnit, ApiConfig
from app.com.chatbot.integrations.verification import VerificationService, InCodeClient, BlackTrustClient
import httpx
from unittest.mock import AsyncMock, patch

class TestVerificationService(TestCase):
    def setUp(self):
        self.business_unit = BusinessUnit.objects.create(
            name='huntRED',
            description='Recruitment platform'
        )
        self.api_config_incode = ApiConfig.objects.create(
            business_unit=self.business_unit,
            api_type='incode',
            api_key='test_incode_key',
            api_secret='test_incode_secret',
            description='INCODE verification configuration',
            additional_settings={
                'base_url': 'https://api.incode.com',
                'verification_types': ['INE', 'ID', 'passport']
            }
        )
        self.api_config_blacktrust = ApiConfig.objects.create(
            business_unit=self.business_unit,
            api_type='blacktrust',
            api_key='test_blacktrust_key',
            api_secret='test_blacktrust_secret',
            description='BlackTrust verification configuration',
            additional_settings={
                'base_url': 'https://api.blacktrust.com',
                'background_check_types': ['criminal', 'credit', 'employment']
            }
        )
        self.verification_service = VerificationService('huntRED')

    @patch('app.chatbot.integrations.verification.httpx.AsyncClient')
    async def test_verify_identity_incode(self, mock_async_client):
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            'success': True,
            'verification_id': '12345',
            'status': 'pending'
        }
        mock_async_client.return_value.post.return_value = mock_response

        result = await self.verification_service.verify_identity('user123', 'incode')
        
        self.assertIn('success', result)
        self.assertTrue(result['success'])
        self.assertIn('verification_id', result)

    @patch('app.chatbot.integrations.verification.httpx.AsyncClient')
    async def test_verify_identity_blacktrust(self, mock_async_client):
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            'success': True,
            'check_id': '67890',
            'status': 'processing'
        }
        mock_async_client.return_value.post.return_value = mock_response

        result = await self.verification_service.verify_identity('user123', 'blacktrust')
        
        self.assertIn('success', result)
        self.assertTrue(result['success'])
        self.assertIn('check_id', result)

    def test_invalid_verification_type(self):
        with self.assertRaises(ValueError):
            await self.verification_service.verify_identity('user123', 'invalid_type')

    def test_missing_config(self):
        with self.assertRaises(ValueError):
            await self.verification_service.verify_identity('user123', 'incode')

    def test_get_verification_settings(self):
        settings = self.api_config_incode.get_verification_settings()
        self.assertEqual(settings['base_url'], 'https://api.incode.com')
        self.assertEqual(settings['verification_types'], ['INE', 'ID', 'passport'])

class TestInCodeClient(TestCase):
    def setUp(self):
        self.client = InCodeClient(
            api_key='test_key',
            api_secret='test_secret',
            settings={
                'base_url': 'https://api.incode.com',
                'verification_types': ['INE', 'ID', 'passport']
            }
        )

    @patch('app.chatbot.integrations.verification.httpx.AsyncClient')
    async def test_verify_success(self, mock_async_client):
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            'success': True,
            'verification_id': '12345',
            'status': 'pending'
        }
        mock_async_client.return_value.post.return_value = mock_response

        result = await self.client.verify('user123')
        self.assertIn('success', result)
        self.assertTrue(result['success'])
        self.assertIn('verification_id', result)

class TestBlackTrustClient(TestCase):
    def setUp(self):
        self.client = BlackTrustClient(
            api_key='test_key',
            api_secret='test_secret',
            settings={
                'base_url': 'https://api.blacktrust.com',
                'background_check_types': ['criminal', 'credit', 'employment']
            }
        )

    @patch('app.chatbot.integrations.verification.httpx.AsyncClient')
    async def test_verify_success(self, mock_async_client):
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            'success': True,
            'check_id': '67890',
            'status': 'processing'
        }
        mock_async_client.return_value.post.return_value = mock_response

        result = await self.client.verify('user123')
        self.assertIn('success', result)
        self.assertTrue(result['success'])
        self.assertIn('check_id', result)
