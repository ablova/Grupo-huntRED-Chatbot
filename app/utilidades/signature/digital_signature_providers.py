"""
Integración con diferentes proveedores de firma digital.
"""
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from app.models import ApiConfig

logger = logging.getLogger(__name__)

class DigitalSignatureProvider:
    """
    Base class para proveedores de firma digital.
    """
    def __init__(self, config: ApiConfig):
        self.config = config
        self.client = None
        self.initialize_client()

    def initialize_client(self):
        """
        Inicializa el cliente específico del proveedor.
        Debe ser implementado por las clases derivadas.
        """
        raise NotImplementedError

    def create_signature_request(self, document_path: str, recipients: list) -> Dict:
        """
        Crea una solicitud de firma digital.
        
        Args:
            document_path: Ruta del documento a firmar
            recipients: Lista de destinatarios que deben firmar
            
        Returns:
            Diccionario con la información de la solicitud
        """
        raise NotImplementedError

    def get_signature_status(self, request_id: str) -> Dict:
        """
        Obtiene el estado de una solicitud de firma.
        
        Args:
            request_id: ID de la solicitud de firma
            
        Returns:
            Diccionario con el estado de la solicitud
        """
        raise NotImplementedError

class DocuSignProvider(DigitalSignatureProvider):
    """
    Integración con DocuSign.
    """
    def initialize_client(self):
        """
        Inicializa el cliente de DocuSign.
        """
        try:
            from docusign_esign import ApiClient, Configuration
            config = Configuration(
                host=self.config.api_url,
                username=self.config.api_key,
                password=self.config.api_secret
            )
            self.client = ApiClient(config)
        except ImportError:
            logger.error("DocuSign SDK no instalado")
            raise

    def create_signature_request(self, document_path: str, recipients: list) -> Dict:
        """
        Crea una solicitud de firma usando DocuSign.
        """
        try:
            from docusign_esign import EnvelopesApi, EnvelopeDefinition
            
            # Configurar el envelope
            envelope_definition = EnvelopeDefinition(
                email_subject="Por favor, firme su documento",
                documents=[{
                    "documentBase64": self._read_document_base64(document_path),
                    "name": "Documento para firma",
                    "fileExtension": "pdf",
                    "documentId": "1"
                }],
                recipients={
                    "signers": [{
                        "email": recipient.email,
                        "name": recipient.name,
                        "recipientId": "1",
                        "tabs": {
                            "signHereTabs": [{
                                "xPosition": "100",
                                "yPosition": "100",
                                "documentId": "1",
                                "pageNumber": "1"
                            }]
                        }
                    } for recipient in recipients]
                },
                status="sent"
            )

            # Crear el envelope
            envelopes_api = EnvelopesApi(self.client)
            envelope_summary = envelopes_api.create_envelope(
                self.config.additional_settings.get('account_id'),
                envelope_definition=envelope_definition
            )

            return {
                "envelope_id": envelope_summary.envelope_id,
                "status": envelope_summary.status,
                "url": envelope_summary.recipients.signing_group.signer.signing_group_id
            }

        except Exception as e:
            logger.error(f"Error al crear solicitud de firma: {str(e)}")
            raise

    def get_signature_status(self, request_id: str) -> Dict:
        """
        Obtiene el estado de una solicitud de firma en DocuSign.
        """
        try:
            envelopes_api = EnvelopesApi(self.client)
            envelope_info = envelopes_api.get_envelope(
                self.config.additional_settings.get('account_id'),
                request_id
            )
            
            return {
                "status": envelope_info.status,
                "completed_date": envelope_info.completed_date_time,
                "signed_by": [signer.email for signer in envelope_info.recipients.signers]
            }
        except Exception as e:
            logger.error(f"Error al obtener estado de firma: {str(e)}")
            raise

    def _read_document_base64(self, document_path: str) -> str:
        """
        Lee un documento y lo convierte a base64.
        """
        with open(document_path, "rb") as file:
            return file.read().decode('base64')

class BasicSignatureProvider(DigitalSignatureProvider):
    """
    Proveedor básico de firma digital (sin integración externa).
    """
    def initialize_client(self):
        """
        No requiere inicialización.
        """
        pass

    def create_signature_request(self, document_path: str, recipients: list) -> Dict:
        """
        Crea una solicitud de firma básica.
        """
        return {
            "document_path": document_path,
            "recipients": [r.email for r in recipients],
            "status": "pending",
            "created_at": now().isoformat()
        }

    def get_signature_status(self, request_id: str) -> Dict:
        """
        Obtiene el estado de una solicitud de firma básica.
        """
        return {
            "status": "completed",
            "completed_date": now().isoformat(),
            "signed_by": recipients
        }

def get_signature_provider(business_unit: str) -> DigitalSignatureProvider:
    """
    Obtiene el proveedor de firma digital configurado para la unidad de negocio.
    
    Args:
        business_unit: Nombre de la unidad de negocio
        
    Returns:
        Instancia del proveedor de firma digital
    """
    try:
        config = ApiConfig.objects.get(
            business_unit=business_unit,
            api_name='digital_signature'
        )
        
        if config.api_key == 'basic':
            return BasicSignatureProvider(config)
        elif config.api_key == 'docusign':
            return DocuSignProvider(config)
        else:
            raise ValueError(f"Proveedor de firma digital no soportado: {config.api_key}")
    except ApiConfig.DoesNotExist:
        logger.warning(f"No se encontró configuración de firma digital para {business_unit}")
        return BasicSignatureProvider(None)
