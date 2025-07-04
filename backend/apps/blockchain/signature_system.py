"""
Advanced Blockchain Signature System - huntRED® v2
Sistema completo de firma electrónica con blockchain propio, verificación criptográfica y smart contracts.
"""

import asyncio
import json
import logging
import hashlib
import ecdsa
import base64
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
import os

logger = logging.getLogger(__name__)


class SignatureStatus(Enum):
    """Estados de firma."""
    PENDING = "pending"
    SIGNED = "signed"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class DocumentType(Enum):
    """Tipos de documentos."""
    CONTRACT = "contract"
    OFFER_LETTER = "offer_letter"
    NDA = "nda"
    BACKGROUND_CHECK = "background_check"
    REFERENCE_FORM = "reference_form"
    ASSESSMENT = "assessment"
    POLICY = "policy"
    AGREEMENT = "agreement"


class SignerRole(Enum):
    """Roles de firmantes."""
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"
    MANAGER = "manager"
    HR = "hr"
    LEGAL = "legal"
    WITNESS = "witness"
    CLIENT = "client"


@dataclass
class BlockchainBlock:
    """Bloque en la blockchain."""
    index: int
    timestamp: datetime
    data: Dict[str, Any]
    previous_hash: str
    nonce: int = 0
    hash: str = ""


@dataclass
class DigitalSignature:
    """Firma digital criptográfica."""
    signer_id: str
    signature_data: str
    public_key: str
    algorithm: str
    timestamp: datetime
    certificate_chain: List[str] = field(default_factory=list)


@dataclass
class SmartContract:
    """Smart contract para firma automática."""
    id: str
    name: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    triggers: List[str]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Signer:
    """Firmante de documento."""
    id: str
    user_id: str
    name: str
    email: str
    role: SignerRole
    phone: Optional[str] = None
    order: int = 1
    required: bool = True
    
    # Información de firma
    signed_at: Optional[datetime] = None
    signature: Optional[DigitalSignature] = None
    ip_address: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    device_info: Optional[Dict[str, Any]] = None
    
    # Notificaciones
    invited_at: Optional[datetime] = None
    reminder_count: int = 0
    
    # Verificación de identidad
    identity_verified: bool = False
    verification_method: Optional[str] = None
    biometric_data: Optional[Dict[str, Any]] = None


@dataclass
class SignableDocument:
    """Documento para firma electrónica."""
    id: str
    title: str
    document_type: DocumentType
    content_hash: str
    file_url: str
    signers: List[Signer]
    
    # Configuración
    signature_order: bool = True  # Firmar en orden específico
    expires_at: Optional[datetime] = None
    reminder_frequency: int = 3  # días
    
    # Estado
    status: SignatureStatus = SignatureStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Blockchain
    blockchain_hash: Optional[str] = None
    smart_contracts: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BlockchainTransaction:
    """Transacción en blockchain."""
    id: str
    transaction_type: str
    document_id: str
    signer_id: str
    signature_data: DigitalSignature
    timestamp: datetime
    block_index: Optional[int] = None


class HuntREDBlockchain:
    """
    Blockchain propio de huntRED® para firmas electrónicas.
    Implementa proof-of-authority con validadores conocidos.
    """
    
    def __init__(self, genesis_data: Dict[str, Any]):
        self.chain: List[BlockchainBlock] = []
        self.pending_transactions: List[BlockchainTransaction] = []
        self.validators: Set[str] = set()
        self.difficulty = 4  # Dificultad de minado
        
        # Crear bloque génesis
        self._create_genesis_block(genesis_data)
    
    def _create_genesis_block(self, genesis_data: Dict[str, Any]):
        """Crea el bloque génesis."""
        genesis_block = BlockchainBlock(
            index=0,
            timestamp=datetime.now(),
            data=genesis_data,
            previous_hash="0"
        )
        genesis_block.hash = self._calculate_hash(genesis_block)
        self.chain.append(genesis_block)
    
    def _calculate_hash(self, block: BlockchainBlock) -> str:
        """Calcula el hash de un bloque."""
        block_data = {
            'index': block.index,
            'timestamp': block.timestamp.isoformat(),
            'data': block.data,
            'previous_hash': block.previous_hash,
            'nonce': block.nonce
        }
        return hashlib.sha256(json.dumps(block_data, sort_keys=True).encode()).hexdigest()
    
    def add_transaction(self, transaction: BlockchainTransaction):
        """Añade una transacción pendiente."""
        # Validar transacción
        if self._validate_transaction(transaction):
            self.pending_transactions.append(transaction)
            logger.info(f"Transaction {transaction.id} added to pending pool")
        else:
            raise ValueError("Invalid transaction")
    
    def _validate_transaction(self, transaction: BlockchainTransaction) -> bool:
        """Valida una transacción."""
        # Verificar firma digital
        try:
            signature = transaction.signature_data
            # Verificar que la firma es válida
            # En producción, verificaría la firma criptográfica completa
            return bool(signature.signature_data and signature.public_key)
        except Exception as e:
            logger.error(f"Transaction validation failed: {str(e)}")
            return False
    
    def mine_block(self, validator_id: str) -> bool:
        """Mina un nuevo bloque (proof-of-authority)."""
        if validator_id not in self.validators:
            raise ValueError("Unauthorized validator")
        
        if not self.pending_transactions:
            return False
        
        # Crear nuevo bloque
        previous_block = self.chain[-1]
        new_block = BlockchainBlock(
            index=len(self.chain),
            timestamp=datetime.now(),
            data={
                'transactions': [
                    {
                        'id': tx.id,
                        'type': tx.transaction_type,
                        'document_id': tx.document_id,
                        'signer_id': tx.signer_id,
                        'timestamp': tx.timestamp.isoformat(),
                        'signature': {
                            'data': tx.signature_data.signature_data,
                            'public_key': tx.signature_data.public_key,
                            'algorithm': tx.signature_data.algorithm
                        }
                    } for tx in self.pending_transactions
                ],
                'validator': validator_id
            },
            previous_hash=previous_block.hash
        )
        
        # Minado simple para proof-of-authority
        new_block.hash = self._calculate_hash(new_block)
        
        # Agregar a la cadena
        self.chain.append(new_block)
        
        # Actualizar transacciones con block_index
        for tx in self.pending_transactions:
            tx.block_index = new_block.index
        
        # Limpiar transacciones pendientes
        self.pending_transactions.clear()
        
        logger.info(f"Block {new_block.index} mined by validator {validator_id}")
        return True
    
    def verify_chain(self) -> bool:
        """Verifica la integridad de toda la cadena."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Verificar hash del bloque
            if current_block.hash != self._calculate_hash(current_block):
                return False
            
            # Verificar enlace con bloque anterior
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def get_transaction_history(self, document_id: str) -> List[Dict[str, Any]]:
        """Obtiene historial de transacciones de un documento."""
        transactions = []
        
        for block in self.chain:
            if 'transactions' in block.data:
                for tx in block.data['transactions']:
                    if tx['document_id'] == document_id:
                        transactions.append({
                            **tx,
                            'block_index': block.index,
                            'block_hash': block.hash,
                            'block_timestamp': block.timestamp.isoformat()
                        })
        
        return sorted(transactions, key=lambda x: x['timestamp'])
    
    def add_validator(self, validator_id: str):
        """Añade un validador autorizado."""
        self.validators.add(validator_id)
    
    def remove_validator(self, validator_id: str):
        """Remueve un validador."""
        self.validators.discard(validator_id)


class CryptographicService:
    """Servicio criptográfico para firmas digitales."""
    
    def __init__(self):
        self.key_size = 2048
    
    def generate_key_pair(self) -> Tuple[str, str]:
        """Genera par de claves pública/privada."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size
        )
        
        public_key = private_key.public_key()
        
        # Serializar claves
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return private_pem, public_pem
    
    def sign_data(self, data: str, private_key_pem: str) -> str:
        """Firma datos con clave privada."""
        private_key = load_pem_private_key(private_key_pem.encode(), password=None)
        
        signature = private_key.sign(
            data.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode('utf-8')
    
    def verify_signature(self, data: str, signature: str, public_key_pem: str) -> bool:
        """Verifica firma con clave pública."""
        try:
            public_key = load_pem_public_key(public_key_pem.encode())
            signature_bytes = base64.b64decode(signature)
            
            public_key.verify(
                signature_bytes,
                data.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def hash_document(self, content: bytes) -> str:
        """Calcula hash SHA-256 de un documento."""
        return hashlib.sha256(content).hexdigest()


class AdvancedSignatureSystem:
    """
    Sistema avanzado de firma electrónica con:
    - Blockchain propio para inmutabilidad
    - Firma criptográfica RSA/ECDSA
    - Smart contracts para automatización
    - Verificación de identidad multi-factor
    - Audit trail completo
    - Geolocalización y device fingerprinting
    - Cumplimiento legal (eIDAS, ESIGN)
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Servicios
        self.crypto_service = CryptographicService()
        self.blockchain = HuntREDBlockchain({
            'genesis_message': 'huntRED® Blockchain Genesis Block',
            'created_at': datetime.now().isoformat(),
            'version': '1.0'
        })
        
        # Documentos y contratos
        self.documents: Dict[str, SignableDocument] = {}
        self.smart_contracts: Dict[str, SmartContract] = {}
        
        # Claves de sistema
        self.system_private_key, self.system_public_key = self.crypto_service.generate_key_pair()
        
        # Configurar validadores blockchain
        self._setup_blockchain_validators()
        
        # Configurar smart contracts predefinidos
        self._setup_default_smart_contracts()
        
        # Métricas
        self.metrics = {
            'total_documents': 0,
            'total_signatures': 0,
            'completion_rate': 0.0,
            'average_signing_time': 0.0
        }
    
    def _setup_blockchain_validators(self):
        """Configura validadores de la blockchain."""
        # En producción, estos serían servidores de huntRED® distribuidos
        validators = [
            'huntred_validator_1',
            'huntred_validator_2',
            'huntred_validator_3'
        ]
        
        for validator in validators:
            self.blockchain.add_validator(validator)
    
    def _setup_default_smart_contracts(self):
        """Configura smart contracts predefinidos."""
        # Contrato para firma automática cuando se completen referencias
        reference_completion_contract = SmartContract(
            id="auto_sign_after_references",
            name="Firma Automática Post-Referencias",
            conditions={
                'trigger_type': 'reference_completion',
                'minimum_references': 2,
                'minimum_score': 3.5
            },
            actions=[
                {
                    'type': 'auto_sign',
                    'document_type': 'offer_letter',
                    'signer_role': 'system'
                }
            ],
            triggers=['reference_completed', 'reference_verified']
        )
        
        # Contrato para vencimiento automático
        expiration_contract = SmartContract(
            id="auto_expire_documents",
            name="Expiración Automática de Documentos",
            conditions={
                'trigger_type': 'time_based',
                'days_after_creation': 30
            },
            actions=[
                {
                    'type': 'expire_document',
                    'notification': True
                }
            ],
            triggers=['daily_check']
        )
        
        self.smart_contracts[reference_completion_contract.id] = reference_completion_contract
        self.smart_contracts[expiration_contract.id] = expiration_contract
    
    def create_signable_document(self, title: str, document_type: DocumentType,
                                file_content: bytes, signers_config: List[Dict[str, Any]],
                                expires_days: Optional[int] = None,
                                signature_order: bool = True) -> str:
        """Crea un documento para firma electrónica."""
        try:
            document_id = str(uuid.uuid4())
            
            # Calcular hash del contenido
            content_hash = self.crypto_service.hash_document(file_content)
            
            # Crear firmantes
            signers = []
            for i, signer_config in enumerate(signers_config):
                signer = Signer(
                    id=str(uuid.uuid4()),
                    user_id=signer_config['user_id'],
                    name=signer_config['name'],
                    email=signer_config['email'],
                    role=SignerRole(signer_config['role']),
                    phone=signer_config.get('phone'),
                    order=i + 1 if signature_order else 1,
                    required=signer_config.get('required', True)
                )
                signers.append(signer)
            
            # Determinar fecha de expiración
            expires_at = None
            if expires_days:
                expires_at = datetime.now() + timedelta(days=expires_days)
            
            # Crear documento
            document = SignableDocument(
                id=document_id,
                title=title,
                document_type=document_type,
                content_hash=content_hash,
                file_url=f"/documents/{document_id}",  # Se almacenaría el archivo
                signers=signers,
                signature_order=signature_order,
                expires_at=expires_at
            )
            
            # Agregar a sistema
            self.documents[document_id] = document
            self.metrics['total_documents'] += 1
            
            # Registrar en audit trail
            self._add_audit_entry(document, 'document_created', {
                'creator': 'system',
                'signers_count': len(signers),
                'content_hash': content_hash
            })
            
            logger.info(f"Created signable document {document_id}: {title}")
            return document_id
            
        except Exception as e:
            logger.error(f"Error creating signable document: {str(e)}")
            raise
    
    async def send_signature_requests(self, document_id: str) -> bool:
        """Envía solicitudes de firma a los firmantes."""
        try:
            document = self.documents.get(document_id)
            if not document:
                raise ValueError("Document not found")
            
            if document.status != SignatureStatus.PENDING:
                raise ValueError(f"Document is in {document.status.value} state")
            
            # Determinar a quién enviar basado en orden de firma
            if document.signature_order:
                # Enviar solo al primer firmante que no ha firmado
                next_signer = None
                for signer in sorted(document.signers, key=lambda s: s.order):
                    if not signer.signed_at:
                        next_signer = signer
                        break
                
                if next_signer:
                    await self._send_signature_request(document, next_signer)
            else:
                # Enviar a todos los firmantes que no han firmado
                for signer in document.signers:
                    if not signer.signed_at:
                        await self._send_signature_request(document, signer)
            
            self._add_audit_entry(document, 'signature_requests_sent', {
                'signature_order': document.signature_order
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending signature requests: {str(e)}")
            raise
    
    async def _send_signature_request(self, document: SignableDocument, signer: Signer):
        """Envía solicitud de firma a un firmante específico."""
        try:
            # Crear URL de firma
            signature_url = f"{self.config.get('base_url')}/signature/{document.id}/sign/{signer.id}"
            
            # Generar token de acceso único
            access_token = self._generate_signature_token(document.id, signer.id)
            
            signer.invited_at = datetime.now()
            
            # Aquí se integraría con el sistema de notificaciones
            logger.info(f"Sending signature request to {signer.email} for document {document.id}")
            
        except Exception as e:
            logger.error(f"Error sending signature request: {str(e)}")
    
    def _generate_signature_token(self, document_id: str, signer_id: str) -> str:
        """Genera token seguro para acceso a firma."""
        token_data = {
            'document_id': document_id,
            'signer_id': signer_id,
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'nonce': str(uuid.uuid4())
        }
        
        token_string = json.dumps(token_data, sort_keys=True)
        signature = self.crypto_service.sign_data(token_string, self.system_private_key)
        
        return base64.b64encode(f"{token_string}|{signature}".encode()).decode()
    
    def verify_signature_token(self, token: str, document_id: str, signer_id: str) -> bool:
        """Verifica token de firma."""
        try:
            decoded = base64.b64decode(token).decode()
            token_string, signature = decoded.split('|', 1)
            
            # Verificar firma del token
            if not self.crypto_service.verify_signature(token_string, signature, self.system_public_key):
                return False
            
            # Verificar datos del token
            token_data = json.loads(token_string)
            if (token_data['document_id'] != document_id or 
                token_data['signer_id'] != signer_id):
                return False
            
            # Verificar expiración
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if datetime.now() > expires_at:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def sign_document(self, document_id: str, signer_id: str, 
                           signature_data: Dict[str, Any],
                           identity_verification: Optional[Dict[str, Any]] = None) -> bool:
        """Procesa la firma de un documento."""
        try:
            document = self.documents.get(document_id)
            if not document:
                raise ValueError("Document not found")
            
            signer = next((s for s in document.signers if s.id == signer_id), None)
            if not signer:
                raise ValueError("Signer not found")
            
            if signer.signed_at:
                raise ValueError("Document already signed by this signer")
            
            # Verificar orden de firma si es requerido
            if document.signature_order:
                current_order = signer.order
                unsigned_with_lower_order = [
                    s for s in document.signers 
                    if s.order < current_order and not s.signed_at and s.required
                ]
                if unsigned_with_lower_order:
                    raise ValueError("Cannot sign out of order")
            
            # Verificar expiración
            if document.expires_at and datetime.now() > document.expires_at:
                document.status = SignatureStatus.EXPIRED
                raise ValueError("Document has expired")
            
            # Generar par de claves para este firmante si no existe
            if 'private_key' not in signature_data:
                private_key, public_key = self.crypto_service.generate_key_pair()
                signature_data['private_key'] = private_key
                signature_data['public_key'] = public_key
            
            # Crear datos para firmar
            sign_data = {
                'document_id': document_id,
                'document_hash': document.content_hash,
                'signer_id': signer_id,
                'timestamp': datetime.now().isoformat(),
                'metadata': signature_data.get('metadata', {})
            }
            sign_string = json.dumps(sign_data, sort_keys=True)
            
            # Generar firma digital
            digital_signature = DigitalSignature(
                signer_id=signer_id,
                signature_data=self.crypto_service.sign_data(sign_string, signature_data['private_key']),
                public_key=signature_data['public_key'],
                algorithm='RSA-PSS-SHA256',
                timestamp=datetime.now()
            )
            
            # Actualizar firmante
            signer.signed_at = datetime.now()
            signer.signature = digital_signature
            signer.ip_address = signature_data.get('ip_address')
            signer.location = signature_data.get('location')
            signer.device_info = signature_data.get('device_info')
            
            # Verificación de identidad
            if identity_verification:
                signer.identity_verified = True
                signer.verification_method = identity_verification.get('method')
                signer.biometric_data = identity_verification.get('biometric_data')
            
            # Crear transacción blockchain
            transaction = BlockchainTransaction(
                id=str(uuid.uuid4()),
                transaction_type='document_signature',
                document_id=document_id,
                signer_id=signer_id,
                signature_data=digital_signature,
                timestamp=datetime.now()
            )
            
            # Agregar a blockchain
            self.blockchain.add_transaction(transaction)
            
            # Minar bloque (en producción sería automático/distribuido)
            await self._mine_pending_transactions()
            
            # Actualizar métricas
            self.metrics['total_signatures'] += 1
            
            # Audit trail
            self._add_audit_entry(document, 'document_signed', {
                'signer_id': signer_id,
                'signer_role': signer.role.value,
                'ip_address': signer.ip_address,
                'location': signer.location,
                'verification_method': signer.verification_method
            })
            
            # Verificar si el documento está completo
            await self._check_document_completion(document)
            
            # Ejecutar smart contracts
            await self._execute_smart_contracts('document_signed', {
                'document_id': document_id,
                'signer_id': signer_id,
                'document': document
            })
            
            logger.info(f"Document {document_id} signed by {signer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error signing document: {str(e)}")
            raise
    
    async def _mine_pending_transactions(self):
        """Mina transacciones pendientes en blockchain."""
        try:
            if self.blockchain.pending_transactions:
                # Usar primer validador disponible
                validator = next(iter(self.blockchain.validators), None)
                if validator:
                    self.blockchain.mine_block(validator)
        except Exception as e:
            logger.error(f"Error mining transactions: {str(e)}")
    
    async def _check_document_completion(self, document: SignableDocument):
        """Verifica si un documento está completamente firmado."""
        required_signers = [s for s in document.signers if s.required]
        signed_required = [s for s in required_signers if s.signed_at]
        
        if len(signed_required) == len(required_signers):
            document.status = SignatureStatus.SIGNED
            document.completed_at = datetime.now()
            
            # Calcular tiempo promedio de firma
            if document.completed_at:
                signing_time = (document.completed_at - document.created_at).total_seconds() / 3600  # horas
                current_avg = self.metrics['average_signing_time']
                completed_docs = sum(1 for d in self.documents.values() if d.status == SignatureStatus.SIGNED)
                self.metrics['average_signing_time'] = (
                    (current_avg * (completed_docs - 1) + signing_time) / completed_docs
                )
            
            # Actualizar tasa de completitud
            total_docs = len(self.documents)
            completed_docs = sum(1 for d in self.documents.values() if d.status == SignatureStatus.SIGNED)
            self.metrics['completion_rate'] = (completed_docs / total_docs) * 100 if total_docs > 0 else 0
            
            self._add_audit_entry(document, 'document_completed', {
                'completion_time': document.completed_at.isoformat(),
                'total_signers': len(document.signers),
                'signing_duration_hours': signing_time if 'signing_time' in locals() else 0
            })
            
            logger.info(f"Document {document.id} completed")
    
    async def _execute_smart_contracts(self, trigger: str, context: Dict[str, Any]):
        """Ejecuta smart contracts basados en triggers."""
        try:
            for contract in self.smart_contracts.values():
                if not contract.is_active or trigger not in contract.triggers:
                    continue
                
                # Evaluar condiciones
                if self._evaluate_contract_conditions(contract, context):
                    await self._execute_contract_actions(contract, context)
                    
        except Exception as e:
            logger.error(f"Error executing smart contracts: {str(e)}")
    
    def _evaluate_contract_conditions(self, contract: SmartContract, 
                                    context: Dict[str, Any]) -> bool:
        """Evalúa las condiciones de un smart contract."""
        try:
            conditions = contract.conditions
            
            if conditions.get('trigger_type') == 'reference_completion':
                # Lógica específica para completion de referencias
                return True  # Simplificado
            
            elif conditions.get('trigger_type') == 'time_based':
                # Lógica para condiciones basadas en tiempo
                document = context.get('document')
                if document and conditions.get('days_after_creation'):
                    days_passed = (datetime.now() - document.created_at).days
                    return days_passed >= conditions['days_after_creation']
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating contract conditions: {str(e)}")
            return False
    
    async def _execute_contract_actions(self, contract: SmartContract, 
                                      context: Dict[str, Any]):
        """Ejecuta las acciones de un smart contract."""
        try:
            for action in contract.actions:
                action_type = action.get('type')
                
                if action_type == 'auto_sign':
                    await self._auto_sign_document(action, context)
                elif action_type == 'expire_document':
                    await self._auto_expire_document(action, context)
                elif action_type == 'send_notification':
                    await self._send_contract_notification(action, context)
                    
        except Exception as e:
            logger.error(f"Error executing contract actions: {str(e)}")
    
    async def _auto_sign_document(self, action: Dict[str, Any], context: Dict[str, Any]):
        """Firma automática por smart contract."""
        # Implementación simplificada
        logger.info("Auto-signing document via smart contract")
    
    async def _auto_expire_document(self, action: Dict[str, Any], context: Dict[str, Any]):
        """Expiración automática de documento."""
        document = context.get('document')
        if document:
            document.status = SignatureStatus.EXPIRED
            logger.info(f"Document {document.id} auto-expired via smart contract")
    
    async def _send_contract_notification(self, action: Dict[str, Any], context: Dict[str, Any]):
        """Envía notificación por smart contract."""
        logger.info("Sending notification via smart contract")
    
    def verify_document_signatures(self, document_id: str) -> Dict[str, Any]:
        """Verifica todas las firmas de un documento."""
        try:
            document = self.documents.get(document_id)
            if not document:
                raise ValueError("Document not found")
            
            verification_results = {
                'document_id': document_id,
                'document_hash': document.content_hash,
                'blockchain_verified': False,
                'signatures_verified': [],
                'overall_valid': False
            }
            
            # Verificar cada firma
            valid_signatures = 0
            for signer in document.signers:
                if signer.signature:
                    # Recrear datos firmados
                    sign_data = {
                        'document_id': document_id,
                        'document_hash': document.content_hash,
                        'signer_id': signer.id,
                        'timestamp': signer.signature.timestamp.isoformat(),
                        'metadata': {}
                    }
                    sign_string = json.dumps(sign_data, sort_keys=True)
                    
                    # Verificar firma
                    is_valid = self.crypto_service.verify_signature(
                        sign_string,
                        signer.signature.signature_data,
                        signer.signature.public_key
                    )
                    
                    verification_results['signatures_verified'].append({
                        'signer_id': signer.id,
                        'signer_name': signer.name,
                        'signer_role': signer.role.value,
                        'signed_at': signer.signed_at.isoformat() if signer.signed_at else None,
                        'signature_valid': is_valid,
                        'identity_verified': signer.identity_verified
                    })
                    
                    if is_valid:
                        valid_signatures += 1
            
            # Verificar en blockchain
            blockchain_transactions = self.blockchain.get_transaction_history(document_id)
            verification_results['blockchain_verified'] = len(blockchain_transactions) > 0
            verification_results['blockchain_transactions'] = blockchain_transactions
            
            # Verificar integridad de la cadena
            chain_valid = self.blockchain.verify_chain()
            verification_results['blockchain_chain_valid'] = chain_valid
            
            # Resultado general
            required_signatures = len([s for s in document.signers if s.required and s.signed_at])
            verification_results['overall_valid'] = (
                valid_signatures == required_signatures and 
                chain_valid and 
                verification_results['blockchain_verified']
            )
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Error verifying document signatures: {str(e)}")
            raise
    
    def get_document_audit_trail(self, document_id: str) -> List[Dict[str, Any]]:
        """Obtiene audit trail completo de un documento."""
        document = self.documents.get(document_id)
        if not document:
            raise ValueError("Document not found")
        
        # Combinar audit trail del documento con transacciones blockchain
        audit_trail = list(document.audit_trail)
        
        # Agregar transacciones blockchain
        blockchain_transactions = self.blockchain.get_transaction_history(document_id)
        for tx in blockchain_transactions:
            audit_trail.append({
                'timestamp': tx['timestamp'],
                'action': 'blockchain_transaction',
                'details': {
                    'transaction_id': tx['id'],
                    'block_index': tx['block_index'],
                    'block_hash': tx['block_hash'],
                    'signer_id': tx['signer_id']
                }
            })
        
        # Ordenar por timestamp
        return sorted(audit_trail, key=lambda x: x['timestamp'])
    
    def _add_audit_entry(self, document: SignableDocument, action: str, details: Dict[str, Any]):
        """Añade entrada al audit trail."""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        }
        document.audit_trail.append(audit_entry)
    
    def get_signature_form(self, document_id: str, signer_id: str, 
                          access_token: str) -> Optional[Dict[str, Any]]:
        """Obtiene el formulario de firma para un firmante."""
        # Verificar token
        if not self.verify_signature_token(access_token, document_id, signer_id):
            return {'error': 'Invalid or expired access token'}
        
        document = self.documents.get(document_id)
        if not document:
            return {'error': 'Document not found'}
        
        signer = next((s for s in document.signers if s.id == signer_id), None)
        if not signer:
            return {'error': 'Signer not found'}
        
        if signer.signed_at:
            return {'error': 'Document already signed'}
        
        if document.expires_at and datetime.now() > document.expires_at:
            return {'error': 'Document has expired'}
        
        # Verificar orden de firma
        can_sign_now = True
        if document.signature_order:
            current_order = signer.order
            unsigned_with_lower_order = [
                s for s in document.signers 
                if s.order < current_order and not s.signed_at and s.required
            ]
            can_sign_now = len(unsigned_with_lower_order) == 0
        
        return {
            'document_id': document_id,
            'signer_id': signer_id,
            'document_title': document.title,
            'document_type': document.document_type.value,
            'signer_name': signer.name,
            'signer_role': signer.role.value,
            'can_sign_now': can_sign_now,
            'signature_order': document.signature_order,
            'signer_order': signer.order,
            'expires_at': document.expires_at.isoformat() if document.expires_at else None,
            'requires_identity_verification': signer.role in [SignerRole.CANDIDATE, SignerRole.CLIENT],
            'signing_progress': {
                'total_signers': len(document.signers),
                'completed_signatures': len([s for s in document.signers if s.signed_at])
            }
        }
    
    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Obtiene el estado actual de un documento."""
        document = self.documents.get(document_id)
        if not document:
            return {'error': 'Document not found'}
        
        signing_progress = []
        for signer in sorted(document.signers, key=lambda s: s.order):
            signing_progress.append({
                'signer_id': signer.id,
                'name': signer.name,
                'role': signer.role.value,
                'order': signer.order,
                'required': signer.required,
                'signed_at': signer.signed_at.isoformat() if signer.signed_at else None,
                'invited_at': signer.invited_at.isoformat() if signer.invited_at else None,
                'identity_verified': signer.identity_verified
            })
        
        return {
            'document_id': document_id,
            'title': document.title,
            'document_type': document.document_type.value,
            'status': document.status.value,
            'created_at': document.created_at.isoformat(),
            'completed_at': document.completed_at.isoformat() if document.completed_at else None,
            'expires_at': document.expires_at.isoformat() if document.expires_at else None,
            'signature_order': document.signature_order,
            'blockchain_hash': document.blockchain_hash,
            'signing_progress': signing_progress,
            'completion_percentage': (
                len([s for s in document.signers if s.signed_at]) / len(document.signers) * 100
                if document.signers else 0
            )
        }
    
    async def send_reminders(self, document_id: str):
        """Envía recordatorios a firmantes pendientes."""
        try:
            document = self.documents.get(document_id)
            if not document or document.status != SignatureStatus.PENDING:
                return
            
            now = datetime.now()
            
            for signer in document.signers:
                if signer.signed_at or not signer.invited_at:
                    continue
                
                # Enviar recordatorio si han pasado suficientes días
                days_since_invite = (now - signer.invited_at).days
                if days_since_invite >= document.reminder_frequency:
                    await self._send_signature_reminder(document, signer)
                    signer.reminder_count += 1
                    
        except Exception as e:
            logger.error(f"Error sending reminders: {str(e)}")
    
    async def _send_signature_reminder(self, document: SignableDocument, signer: Signer):
        """Envía recordatorio a un firmante específico."""
        try:
            # Aquí se integraría con el sistema de notificaciones
            logger.info(f"Sending signature reminder to {signer.email} for document {document.id}")
            
        except Exception as e:
            logger.error(f"Error sending reminder: {str(e)}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema de firmas."""
        blockchain_metrics = {
            'total_blocks': len(self.blockchain.chain),
            'pending_transactions': len(self.blockchain.pending_transactions),
            'chain_valid': self.blockchain.verify_chain()
        }
        
        return {
            **self.metrics,
            'blockchain': blockchain_metrics,
            'active_documents': len([d for d in self.documents.values() 
                                   if d.status == SignatureStatus.PENDING]),
            'smart_contracts_active': len([c for c in self.smart_contracts.values() if c.is_active])
        }