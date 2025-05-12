import pytest
from unittest.mock import patch, MagicMock
from app.com.utils.signature import DigitalSignature


@pytest.fixture
def digital_signature():
    return DigitalSignature()


def test_sign_document_success(digital_signature):
    # Test successful document signing
    with patch.object(digital_signature, '_load_private_key', return_value=MagicMock()) as mock_load_key:
        with patch.object(digital_signature, '_log_audit_action', return_value=None) as mock_log:
            with patch('cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey.sign', return_value=b'signature') as mock_sign:
                result = digital_signature.sign_document(b'test document', 'user123')
                assert result is not None
                mock_load_key.assert_called_once()
                mock_log.assert_called_once_with('user123', 'sign', True, None)
                mock_sign.assert_called_once()


def test_sign_document_failure(digital_signature):
    # Test signing failure due to exception
    with patch.object(digital_signature, '_load_private_key', side_effect=Exception('Key load failed')) as mock_load_key:
        with patch.object(digital_signature, '_log_audit_action', return_value=None) as mock_log:
            result = digital_signature.sign_document(b'test document', 'user123')
            assert result is None
            mock_load_key.assert_called_once()
            mock_log.assert_called_once_with('user123', 'sign', False, 'Key load failed')


def test_verify_signature_success(digital_signature):
    # Test successful signature verification
    with patch.object(digital_signature, '_load_public_key', return_value=MagicMock()) as mock_load_key:
        with patch.object(digital_signature, '_log_audit_action', return_value=None) as mock_log:
            with patch('cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey.verify', return_value=None) as mock_verify:
                result = digital_signature.verify_signature(b'test document', b'signature', 'user123')
                assert result is True
                mock_load_key.assert_called_once()
                mock_log.assert_called_once_with('user123', 'verify', True, None)
                mock_verify.assert_called_once()


def test_verify_signature_failure(digital_signature):
    # Test verification failure due to exception
    with patch.object(digital_signature, '_load_public_key', return_value=MagicMock()) as mock_load_key:
        with patch.object(digital_signature, '_log_audit_action', return_value=None) as mock_log:
            with patch('cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey.verify', side_effect=Exception('Invalid signature')) as mock_verify:
                result = digital_signature.verify_signature(b'test document', b'signature', 'user123')
                assert result is False
                mock_load_key.assert_called_once()
                mock_log.assert_called_once_with('user123', 'verify', False, 'Invalid signature')
                mock_verify.assert_called_once()
