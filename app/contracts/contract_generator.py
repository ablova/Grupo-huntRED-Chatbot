import logging
import json
import hashlib
import ipfshttpclient
from datetime import datetime
from app.models import Contract, Proposal, Opportunity, Person
from app.contracts.config import CONTRACTS_DIR
from app.contracts.certificate_generator import CertificateGenerator

logger = logging.getLogger(__name__)

class ContractGenerator:
    def __init__(self):
        self.certificate_generator = CertificateGenerator()
        
    def convert_opportunity_to_contract(self, opportunity_id):
        """
        Convierte una oportunidad en un contrato.
        
        Args:
            opportunity_id: ID de la oportunidad
            
        Returns:
            Contract: Contrato generado
        """
        try:
            # Obtener oportunidad
            opportunity = Opportunity.objects.get(id=opportunity_id)
            
            # Crear propuesta
            proposal = self._create_proposal(opportunity)
            
            # Generar contrato
            contract = self._generate_contract(proposal)
            
            # Iniciar flujo de firma
            self._initiate_signing_process(contract)
            
            # Generar certificado
            self.certificate_generator.generate_certificate(contract)
            
            return contract
            
        except Exception as e:
            logger.error(f"Error al convertir oportunidad: {str(e)}")
            raise
            
    def _create_proposal(self, opportunity):
        """
        Crea una propuesta basada en la oportunidad.
        
        Args:
            opportunity: Instancia de Opportunity
            
        Returns:
            Proposal: Propuesta generada
        """
        # Calcular pricing
        pricing = calculate_pricing_opportunity(opportunity.id)
        
        # Crear propuesta
        proposal = Proposal.objects.create(
            company=opportunity.company,
            pricing_total=pricing['total'],
            pricing_details=pricing
        )
        
        # Asociar vacantes
        for vacancy in opportunity.vacancies.all():
            proposal.vacancies.add(vacancy)
            
        return proposal
        
    def _generate_contract(self, proposal):
        """
        Genera un contrato basado en la propuesta.
        
        Args:
            proposal: Instancia de Proposal
            
        Returns:
            Contract: Contrato generado
        """
        # Crear contrato
        contract = Contract.objects.create(
            proposal=proposal,
            status='PENDING_APPROVAL'
        )
        
        # Generar PDF del contrato
        self._generate_contract_pdf(contract)
        
        return contract
        
    def _initiate_signing_process(self, contract):
        """
        Inicia el proceso de firma del contrato.
        
        Args:
            contract: Instancia de Contract
        """
        # Notificar a superuser para aprobación
        self._notify_superuser(contract)
        
    def _notify_superuser(self, contract):
        """
        Notifica al superuser sobre el contrato pendiente de aprobación.
        
        Args:
            contract: Instancia de Contract
        """
        from app.utilidades.notification_handler import NotificationHandler
        
        notification_handler = NotificationHandler()
        message = f"Nuevo contrato pendiente de aprobación: {contract.proposal.company}"
        notification_handler.send_notification(
            recipient='pablo@huntred.com',
            message=message,
            subject='Aprobación de Contrato'
        )
