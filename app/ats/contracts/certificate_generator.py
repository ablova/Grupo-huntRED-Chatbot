import logging
import json
import hashlib
import ipfshttpclient
from datetime import datetime
from app.ats.ats.models import Certificate
import opentimestamps as ots
from opentimestamps.core.serialize import SerializationError, DeserializationError, List
from pathlib import Path
from typing import Dict
from app.ats.ats.models import Contract, Person
from app.ats.ats.ats.contracts.config import CONTRACTS_DIR

logger = logging.getLogger(__name__)

class CertificateGenerator:
    def __init__(self):
        self.ipfs_client = None
        self.ots_client = None
        self._initialize_clients()

    def _initialize_clients(self):
        """Inicializa los clientes de IPFS y OpenTimestamps"""
        try:
            self.ipfs_client = ipfshttpclient.connect()
            self.ots_client = Client()
        except Exception as e:
            logger.error(f"Error initializing clients: {str(e)}")

    def generate_certificate(self, contract: Contract) -> Dict:
        """
        Genera un certificado para un contrato firmado.
        
        Args:
            contract: Instancia del contrato firmado
            
        Returns:
            dict: Información del certificado generado
        """
        try:
            # Crear datos del certificado
            certificate_data = self._create_certificate_data(contract)
            
            # Generar hash del certificado
            certificate_hash = self._generate_hash(certificate_data)
            
            # Almacenar en IPFS
            ipfs_cid = self._store_on_ipfs(certificate_data)
            
            # Crear timestamp usando OpenTimestamps
            timestamp = Timestamp.now()
            try:
                # Serializar el timestamp
                timestamp_hex = timestamp.to_hex()
                
                # Crear y guardar el certificado
                certificate = Certificate(
                    contract=contract,
                    certificate_hash=timestamp_hex,
                    ipfs_cid=ipfs_cid,
                    status='pending'
                )
                certificate.save()
                
                return {
                    'certificate_id': str(certificate.certificate_id),
                    'ipfs_cid': ipfs_cid,
                    'status': certificate.status,
                    'timestamp': timestamp.get_time()
                }
                
            except SerializationError:
                raise Exception("Error al serializar el timestamp")
                
        except ImportError:
            raise Exception("OpenTimestamps no está instalado. Instale con: pip install opentimestamps")
            
        except Exception as e:
            raise Exception(f"Error al generar el certificado: {str(e)}")

    def _create_certificate_data(self, contract: Contract) -> Dict:
        """Crea los datos del certificado"""
        return {
            'contract_id': contract.id,
            'signatures': self._get_signatures_data(contract),
            'metadata': {
                'business_unit': contract.business_unit.name,
                'created_at': str(contract.created_at),
                'signed_at': str(contract.signed_at),
                'document_hash': self._generate_hash(contract.signed_document_path)
            },
            'certificate_info': {
                'issuer': 'huntRED',
                'certificate_type': 'contract_signature',
                'version': '1.0'
            }
        }

    def _get_signatures_data(self, contract: Contract) -> List[Dict]:
        """Obtiene información de las firmas"""
        signatures = []
        
        for signer in [contract.client, contract.consultant]:
            signature_data = {
                'name': signer.full_name,
                'email': signer.email,
                'position': self._get_signer_position(signer, contract),
                'signature_date': str(contract.signed_at),
                'location': self._get_signer_location(signer),
                'verification_hash': self._generate_hash(f"{signer.email}{contract.id}")
            }
            signatures.append(signature_data)
            
        return signatures

    def _get_signer_position(self, signer: Person, contract: Contract) -> str:
        """Determina la posición del firmante"""
        if signer.id == contract.client.id:
            return 'Cliente'
        elif signer.id == contract.consultant.id:
            return 'Consultor'
        return 'Firmante'

    def _get_signer_location(self, signer: Person) -> str:
        """Obtiene la ubicación del firmante"""
        # TODO: Implementar lógica para obtener ubicación
        return 'Desconocida'

    def _generate_hash(self, data) -> str:
        """Genera un hash SHA-256"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif isinstance(data, dict):
            data = json.dumps(data, sort_keys=True).encode('utf-8')
        
        return hashlib.sha256(data).hexdigest()

    def _store_in_ipfs(self, data: Dict) -> str:
        """Almacena los datos en IPFS"""
        try:
            # Convertir a JSON
            json_data = json.dumps(data, indent=2)
            
            # Almacenar en IPFS
            result = self.ipfs_client.add_str(json_data)
            
            return result
        except Exception as e:
            logger.error(f"Error storing in IPFS: {str(e)}")
            raise

    def _get_timestamp(self) -> str:
        """Obtiene el timestamp actual"""
        return datetime.utcnow().isoformat()

    def verify_certificate(self, certificate_hash: str) -> bool:
        """Verifica la integridad del certificado"""
        try:
            # Verificar hash
            if not self._verify_hash(certificate_hash):
                return False
            
            # Verificar timestamp
            if not self._verify_timestamp(certificate_hash):
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error verifying certificate: {str(e)}")
            return False

    def _verify_hash(self, certificate_hash: str) -> bool:
        """Verifica la integridad del hash"""
        # TODO: Implementar lógica de verificación de hash
        return True

    def _verify_timestamp(self, certificate_hash: str) -> bool:
        """Verifica el timestamp usando OpenTimestamps"""
        # TODO: Implementar lógica de verificación de timestamp
        return True

    def generate_certificate_pdf(self, certificate_data: Dict) -> str:
        """Genera un PDF del certificado"""
        # TODO: Implementar generación de PDF
        return ""

    def store_certificate(self, certificate_data: Dict) -> str:
        """Almacena el certificado en el sistema"""
        # TODO: Implementar almacenamiento persistente
        return ""
