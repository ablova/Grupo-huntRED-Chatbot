import logging
import os
from typing import Dict, List, Optional
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.cache import cache
from app.ats.ats.models import Contract, Person, BusinessUnit, ApiConfig
from app.ats.ats.utils.signature.signature_handler import generate_and_send_contract
from app.ats.ats.utils.signature.digital_signature_providers import get_signature_provider
from app.ats.ats.chatbot.gpt import GPTHandler
from app.ats.ats.ats.contracts.config import (
    CONTRACTS_DIR, SIGNED_CONTRACTS_DIR, TEMP_CONTRACTS_DIR,
    SIGNATURE_CONFIG, AI_CONFIG, BLOCKCHAIN_CONFIG, EMAIL_CONFIG,
    CACHE_CONFIG
)

logger = logging.getLogger(__name__)

class ContractManager:
    def __init__(self):
        self.gpt_handler = GPTHandler()
        self._ensure_directories()

    def _ensure_directories(self):
        """Asegura que los directorios necesarios existan"""
        required_dirs = [
            CONTRACTS_DIR,
            SIGNED_CONTRACTS_DIR,
            TEMP_CONTRACTS_DIR
        ]
        
        for directory in required_dirs:
            os.makedirs(directory, exist_ok=True)

    async def send_for_approval(self, contract_id: int, superuser_email: str) -> Dict:
        """
        Envía el contrato para aprobación del superuser.
        
        Args:
            contract_id: ID del contrato
            superuser_email: Email del superuser
            
        Returns:
            Diccionario con el estado de la solicitud
        """
        contract = Contract.objects.get(id=contract_id)
        
        # Verificar si se requiere aprobación del superuser
        if not SIGNATURE_CONFIG['superuser_approval_required']:
            return {
                'status': 'success',
                'message': 'Aprobación automática habilitada'
            }
            
        # Verificar si el consultor es el superuser
        if contract.consultant.email == superuser_email:
            return {
                'status': 'success',
                'message': 'Consultor es superuser, aprobación automática'
            }
            
        # Preparar destinatarios
        recipients = [
            {
                'email': superuser_email,
                'name': 'Superuser'
            },
            {
                'email': contract.client.email,
                'name': contract.client.full_name
            },
            {
                'email': contract.consultant.email,
                'name': contract.consultant.full_name
            }
        ]
        
        # Obtener proveedor de firma
        signature_provider = get_signature_provider(contract.business_unit.name)
        
        # Crear solicitud de firma
        signature_request = signature_provider.create_signature_request(
            document_path=contract.document_path,
            recipients=recipients
        )
        
        # Actualizar estado del contrato
        contract.status = 'awaiting_approval'
        contract.save()
        
        return {
            'status': 'success',
            'signature_request': signature_request
        }

    async def send_for_signature(self, contract_id: int, client_email: str) -> Dict:
        """
        Envía el contrato para firma al cliente.
        
        Args:
            contract_id: ID del contrato
            client_email: Email del cliente
            
        Returns:
            Diccionario con el estado de la solicitud
        """
        contract = Contract.objects.get(id=contract_id)
        
        # Verificar estado del contrato
        if contract.status != 'approved':
            raise ValueError('El contrato debe estar aprobado antes de enviar para firma')
            
        # Preparar destinatarios
        recipients = [
            {
                'email': client_email,
                'name': contract.client.full_name
            },
            {
                'email': contract.consultant.email,
                'name': contract.consultant.full_name
            }
        ]
        
        # Obtener proveedor de firma
        signature_provider = get_signature_provider(contract.business_unit.name)
        
        # Crear solicitud de firma
        signature_request = signature_provider.create_signature_request(
            document_path=contract.document_path,
            recipients=recipients
        )
        
        # Actualizar estado del contrato
        contract.status = 'awaiting_signature'
        contract.save()
        
        return {
            'status': 'success',
            'signature_request': signature_request
        }

    async def store_contract(self, contract_id: int, signed_pdf_path: str) -> Dict:
        """
        Almacena el contrato firmado.
        
        Args:
            contract_id: ID del contrato
            signed_pdf_path: Ruta del PDF firmado
            
        Returns:
            Diccionario con el estado de almacenamiento
        """
        contract = Contract.objects.get(id=contract_id)
        
        # Mover archivo a directorio de contratos firmados
        filename = f"contract_{contract_id}_{contract.client.id}.pdf"
        destination_path = os.path.join(SIGNED_CONTRACTS_DIR, filename)
        
        os.rename(signed_pdf_path, destination_path)
        
        # Actualizar información del contrato
        contract.signed_document_path = destination_path
        contract.status = 'signed'
        contract.save()
        
        return {
            'status': 'success',
            'signed_path': destination_path
        }

    async def analyze_contract_risks(self, contract_id: int) -> Dict:
        """
        Analiza riesgos del contrato usando IA.
        
        Args:
            contract_id: ID del contrato
            
        Returns:
            Diccionario con el análisis de riesgos
        """
        if not AI_CONFIG['enabled']:
            return {
                'status': 'warning',
                'message': 'Análisis de IA deshabilitado'
            }
            
        contract = Contract.objects.get(id=contract_id)
        
        # Preparar datos para el análisis
        contract_data = {
            'terms': contract.terms,
            'business_unit': contract.business_unit.name,
            'client': contract.client.full_name,
            'consultant': contract.consultant.full_name
        }
        
        # Generar análisis usando IA
        analysis = await self._generate_ai_analysis(contract_data)
        
        return {
            'status': 'success',
            'analysis': analysis
        }

    async def _generate_ai_analysis(self, contract_data: Dict) -> Dict:
        """Genera análisis de riesgos usando IA"""
        prompt = await self._load_prompt('contract_analysis_prompt.txt')
        formatted_prompt = prompt.format(**contract_data)
        
        try:
            response = await self.gpt_handler.generate_response(
                formatted_prompt,
                business_unit=contract_data['business_unit']
            )
            
            # Parsear respuesta para categorías de riesgo
            analysis = self._parse_risk_analysis(response)
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating AI analysis: {str(e)}")
            return {
                'error': str(e),
                'risk_categories': AI_CONFIG['risk_categories']
            }

    def _parse_risk_analysis(self, analysis_text: str) -> Dict:
        """Parsea el análisis de riesgos desde el texto de IA"""
        # TODO: Implementar lógica de parsing
        return {
            'legal_risks': [],
            'financial_risks': [],
            'confidentiality_risks': [],
            'termination_risks': []
        }

    def _cache_key(self, contract_id: int, section: str) -> str:
        """Genera una clave de caché"""
        return f"{CACHE_CONFIG['key_prefix']}{section}_{contract_id}"

    async def get_cached_contract(self, contract_id: int) -> Optional[Dict]:
        """Obtiene un contrato desde caché"""
        cache_key = self._cache_key(contract_id, 'content')
        return cache.get(cache_key)

    async def cache_contract(self, contract_id: int, data: Dict):
        """Almacena un contrato en caché"""
        cache_key = self._cache_key(contract_id, 'content')
        self.cache.set(cache_key, data, timeout=CACHE_CONFIG['timeout'])
