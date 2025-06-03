import os
import base64
import logging
from datetime import datetime
from django.conf import settings
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class DigitalSignature:
    """
    Class for handling digital signatures with enhanced security features.
    """
    def __init__(self):
        """
        Initialize the digital signature system with key pair generation or loading.
        """
        self.private_key = None
        self.public_key = None
        self._load_or_generate_keys()
        logger.info("DigitalSignature initialized")

    def _load_or_generate_keys(self):
        """
        Load existing key pair from settings or generate a new one if not available.
        """
        try:
            if hasattr(settings, 'PRIVATE_KEY') and hasattr(settings, 'PUBLIC_KEY'):
                self.private_key = serialization.load_pem_private_key(
                    settings.PRIVATE_KEY.encode(),
                    password=None,
                    backend=default_backend()
                )
                self.public_key = serialization.load_pem_public_key(
                    settings.PUBLIC_KEY.encode(),
                    backend=default_backend()
                )
                logger.info("Key pair loaded from settings")
            else:
                # Generate new RSA key pair
                self.private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
                self.public_key = self.private_key.public_key()
                logger.info("New RSA key pair generated")
        except Exception as e:
            logger.error(f"Error loading or generating keys: {str(e)}")
            raise ValidationError(f"Failed to initialize digital signature keys: {str(e)}")

    def sign_document(self, document_data: bytes, user_id: str) -> str:
        """
        Sign a document with the private key.

        Args:
            document_data (bytes): The document content to sign.
            user_id (str): Identifier of the user signing the document.

        Returns:
            str: Base64 encoded signature.
        """
        try:
            signature = self.private_key.sign(
                document_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            encoded_signature = base64.b64encode(signature).decode('utf-8')
            # Log the signing action for audit trail
            self._log_signature_action(user_id, "sign", document_data, encoded_signature)
            logger.info(f"Document signed by user {user_id}")
            return encoded_signature
        except Exception as e:
            logger.error(f"Error signing document for user {user_id}: {str(e)}")
            raise ValidationError(f"Error signing document: {str(e)}")

    def verify_signature(self, document_data: bytes, signature: str, user_id: str) -> bool:
        """
        Verify a signature against the document data using the public key.

        Args:
            document_data (bytes): The original document content.
            signature (str): Base64 encoded signature to verify.
            user_id (str): Identifier of the user who signed the document.

        Returns:
            bool: True if signature is valid, False otherwise.
        """
        try:
            decoded_signature = base64.b64decode(signature)
            self.public_key.verify(
                decoded_signature,
                document_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            # Log the verification action for audit trail
            self._log_signature_action(user_id, "verify", document_data, signature)
            logger.info(f"Signature verified for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error verifying signature for user {user_id}: {str(e)}")
            self._log_signature_action(user_id, "verify_failed", document_data, signature, str(e))
            return False

    def _log_signature_action(self, user_id: str, action: str, document_data: bytes, signature: str, error: str = None):
        """
        Log signature actions for audit purposes.

        Args:
            user_id (str): Identifier of the user.
            action (str): Action performed (sign, verify, verify_failed).
            document_data (bytes): Document content involved.
            signature (str): Signature involved.
            error (str, optional): Error message if action failed.
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'action': action,
            'document_hash': hashes.Hash(hashes.SHA256(), backend=default_backend()).update(document_data).finalize().hex(),
            'signature_snippet': signature[:10] + "..." if len(signature) > 10 else signature,
            'error': error if error else 'none'
        }
        logger.info(f"Audit log for signature action: {log_entry}")
        # Optionally, write to a secure audit log file or database
        if hasattr(settings, 'AUDIT_LOG_PATH'):
            try:
                with open(settings.AUDIT_LOG_PATH, 'a') as log_file:
                    log_file.write(f"{log_entry}\n")
            except Exception as e:
                logger.error(f"Failed to write to audit log file: {str(e)}")
