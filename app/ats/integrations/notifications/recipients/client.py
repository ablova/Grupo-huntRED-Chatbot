# app/ats/integrations/notifications/recipients/client.py
"""
Client notification handlers for the Grupo huntRED® Chatbot.

This module contains notification handlers specifically for client-facing
notifications, such as new candidate submissions, interview feedback, and
hiring decisions.
"""
import logging
from typing import Dict, Any, Optional, List, Union

from asgiref.sync import sync_to_async
from django.utils import timezone

from app.models import Person, Vacancy, CartaOferta, BusinessUnit
from app.ats.integrations.notifications.core.service import get_notification_service

logger = logging.getLogger(__name__)

from app.ats.integrations.notifications.recipients.base import BaseRecipient
from app.models import Person

class ClientRecipient(BaseRecipient):
    """Clase para destinatarios clientes."""
    
    def __init__(self, person: Person):
        self.person = person
        
    def get_contact_info(self) -> Dict[str, str]:
        return {
            'email': self.person.email,
            'phone': self.person.phone,
            'whatsapp': self.person.whatsapp,
            'x': self.person.x_handle
        }
        
    def get_preferred_channels(self) -> List[str]:
        channels = []
        if self.person.email:
            channels.append('email')
        if self.person.whatsapp:
            channels.append('whatsapp')
        if self.person.x_handle:
            channels.append('x')
        return channels
        
    def get_notification_context(self) -> Dict:
        return {
            'name': self.person.full_name,
            'company': self.person.company.name if self.person.company else 'N/A',
            'position': self.person.position
        }

class ClientNotifier:
    """Handles notifications sent to clients."""
    
    def __init__(self, client: Person, business_unit: Optional[BusinessUnit] = None):
        """
        Initialize the client notifier.
        
        Args:
            client: The client contact to send notifications to
            business_unit: Optional business unit for the notification context
        """
        self.client = client
        self.business_unit = business_unit or client.business_unit
        self.notification_service = get_notification_service()
    
    async def send_new_candidate_submission(
        self,
        candidate: Person,
        vacancy: Vacancy,
        resume_url: Optional[str] = None,
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Notify the client about a new candidate submission.
        
        Args:
            candidate: The candidate who was submitted
            vacancy: The vacancy the candidate was submitted for
            resume_url: Optional URL to the candidate's resume
            channels: Override default channels for this notification
            
        Returns:
            Dict mapping channel names to success status
            
        Note:
            - For SENIOR contacts: Only sends if resume_url is provided (CV en Blind)
            - For BILLING contacts: Not sent (not relevant for billing)
        """
        # Skip billing contacts for candidate submissions
        if self.contact_type == ClientContactType.BILLING:
            logger.info(f"Skipping candidate submission notification for billing contact: {self.client_contact.email}")
            return {}
            
        # For senior contacts, only send if resume is provided (CV en Blind)
        if self.contact_type == ClientContactType.SENIOR and not resume_url:
            logger.info(f"Skipping senior contact notification - no resume provided for candidate: {candidate.email}")
            return {}
        
        # Determine channels to use
        use_channels = channels or self.default_channels
        
        context = {
            'client': {
                'name': self.client_contact.nombre,
                'contact_type': self.contact_type.name.lower(),
            },
            'candidate': {
                'name': candidate.nombre,
                'title': candidate.title or 'Candidate',
                'resume_url': resume_url
            },
            'vacancy': {
                'title': vacancy.titulo,
                'id': vacancy.id,
                'department': vacancy.department or 'N/A'
            },
            'submission_date': timezone.now().strftime('%Y-%m-%d')
        }
        
        return await self.notification_service.send_notification(
            recipient=self.client,
            template_name='client_new_candidate_submission',
            context=context,
            notification_type='new_candidate',
            business_unit=self.business_unit,
            channels=channels or ['email']
        )
    
    async def send_interview_scheduled(
        self,
        candidate: Person,
        vacancy: Vacancy,
        interview_date: str,
        interview_type: str,
        meeting_link: Optional[str] = None,
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Notify the client about a scheduled interview.
        
        Args:
            candidate: The candidate being interviewed
            vacancy: The position being interviewed for
            interview_date: Scheduled date/time of the interview
            interview_type: Type of interview (e.g., 'technical', 'cultural')
            meeting_link: Optional link for virtual interviews
            channels: Override default channels for this notification
            
        Returns:
            Dict mapping channel names to success status
        """
        context = {
            'client': {
                'name': self.client.nombre,
            },
            'candidate': {
                'name': candidate.nombre,
                'title': candidate.title or 'Candidate'
            },
            'vacancy': {
                'title': vacancy.titulo,
                'id': vacancy.id
            },
            'interview': {
                'date': interview_date,
                'type': interview_type,
                'meeting_link': meeting_link
            }
        }
        
        return await self.notification_service.send_notification(
            recipient=self.client,
            template_name='client_interview_scheduled',
            context=context,
            notification_type='interview_scheduled',
            business_unit=self.business_unit,
            channels=channels or ['email']
        )
    
    async def send_offer_approval_request(
        self,
        candidate: Person,
        vacancy: Vacancy,
        offer_details: Dict[str, Any],
        approval_url: str,
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Request approval for a job offer from the client.
        
        Args:
            candidate: The candidate receiving the offer
            vacancy: The vacancy the offer is for
            offer_details: Details of the offer (salary, start date, etc.)
            approval_url: URL to approve/reject the offer
            channels: Override default channels for this notification
            
        Returns:
            Dict mapping channel names to success status
        """
        context = {
            'client': {
                'name': self.client.nombre,
            },
            'candidate': {
                'name': candidate.nombre,
                'title': candidate.title or 'Candidate'
            },
            'vacancy': {
                'title': vacancy.titulo,
                'id': vacancy.id,
                'department': vacancy.department or 'N/A'
            },
            'offer': {
                **offer_details,
                'approval_url': approval_url,
                'expiration_date': (timezone.now() + timezone.timedelta(days=3)).strftime('%Y-%m-%d')
            }
        }
        
        return await self.notification_service.send_notification(
            recipient=self.client,
            template_name='client_offer_approval_request',
            context=context,
            notification_type='offer_approval_request',
            business_unit=self.business_unit,
            channels=channels or ['email']
        )
    
    async def send_hire_confirmation(
        self,
        candidate: Person,
        vacancy: Vacancy,
        start_date: str,
        onboarding_details: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Confirm a hire to the client.
        
        Args:
            candidate: The candidate who was hired
            vacancy: The position they were hired for
            start_date: The candidate's start date
            onboarding_details: Optional onboarding information
            channels: Override default channels for this notification
            
        Returns:
            Dict mapping channel names to success status
        """
        context = {
            'client': {
                'name': self.client.nombre,
            },
            'candidate': {
                'name': candidate.nombre,
                'email': candidate.email,
                'phone': candidate.phone
            },
            'position': {
                'title': vacancy.titulo,
                'department': vacancy.department or 'N/A',
                'start_date': start_date,
                'location': vacancy.location or 'Remote',
                'manager': vacancy.hiring_manager.name if vacancy.hiring_manager else 'TBD'
            },
            'onboarding': onboarding_details or {}
        }
        
        return await self.notification_service.send_notification(
            recipient=self.client,
            template_name='client_hire_confirmation',
            context=context,
            notification_type='hire_confirmation',
            business_unit=self.business_unit,
            channels=channels or ['email']
        )
