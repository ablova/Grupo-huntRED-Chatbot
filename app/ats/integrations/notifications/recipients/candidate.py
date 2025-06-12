"""
Candidate notification handlers for the Grupo huntRED® Chatbot.

This module contains notification handlers specifically for candidate-facing
notifications, such as application updates, interview scheduling, and offer letters.
"""
import logging
from typing import Dict, Any, Optional, List, Union

from asgiref.sync import sync_to_async
from django.utils import timezone

from app.models import Person, Vacancy, CartaOferta, BusinessUnit
from ....core.service import get_notification_service

logger = logging.getLogger(__name__)

from app.ats.integrations.notifications.recipients.base import BaseRecipient
from app.models import Person

class CandidateRecipient(BaseRecipient):
    """Clase para destinatarios candidatos."""
    
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
            'position': self.person.current_position,
            'business_unit': self.person.business_unit.name if self.person.business_unit else 'N/A'
        }

class CandidateNotifier:
    """Handles notifications sent to candidates."""
    
    def __init__(self, candidate: Person):
        """
        Initialize the candidate notifier.
        
        Args:
            candidate: The candidate to send notifications to
        """
        self.candidate = candidate
        self.notification_service = get_notification_service()
    
    async def send_application_received(self, vacancy: Vacancy) -> Dict[str, bool]:
        """
        Send a notification to the candidate that their application was received.
        
        Args:
            vacancy: The vacancy the candidate applied to
            
        Returns:
            Dict mapping channel names to success status
        """
        context = {
            'candidate': {
                'name': self.candidate.nombre,
                'email': self.candidate.email,
            },
            'vacancy': {
                'title': vacancy.titulo,
                'id': vacancy.id,
            },
            'application_date': timezone.now().strftime('%Y-%m-%d')
        }
        
        return await self.notification_service.send_notification(
            recipient=self.candidate,
            template_name='candidate_application_received',
            context=context,
            notification_type='application_received',
            channels=['email', 'whatsapp']
        )
    
    async def send_interview_scheduled(
        self,
        vacancy: Vacancy,
        interview_date: str,
        interview_type: str,
        meeting_link: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Send a notification to the candidate about a scheduled interview.
        
        Args:
            vacancy: The vacancy the interview is for
            interview_date: The scheduled date and time of the interview
            interview_type: The type of interview (e.g., 'technical', 'hr')
            meeting_link: Optional meeting link for virtual interviews
            
        Returns:
            Dict mapping channel names to success status
        """
        context = {
            'candidate': {
                'name': self.candidate.nombre,
            },
            'vacancy': {
                'title': vacancy.titulo,
                'id': vacancy.id,
            },
            'interview': {
                'date': interview_date,
                'type': interview_type,
                'meeting_link': meeting_link,
                'is_virtual': bool(meeting_link)
            }
        }
        
        return await self.notification_service.send_notification(
            recipient=self.candidate,
            template_name='candidate_interview_scheduled',
            context=context,
            notification_type='interview_scheduled',
            channels=['email', 'whatsapp']
        )
    
    async def send_offer_letter(
        self,
        offer_letter: CartaOferta,
        document_url: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Send an offer letter to the candidate.
        
        Args:
            offer_letter: The offer letter to send
            document_url: Optional URL to the offer letter document
            
        Returns:
            Dict mapping channel names to success status
        """
        context = {
            'candidate': {
                'name': self.candidate.nombre,
            },
            'offer': {
                'id': offer_letter.id,
                'position': offer_letter.vacancy.titulo if offer_letter.vacancy else 'N/A',
                'salary': offer_letter.salary,
                'start_date': offer_letter.start_date.strftime('%Y-%m-%d') if offer_letter.start_date else 'N/A',
                'document_url': document_url,
                'expiration_date': offer_letter.expiration_date.strftime('%Y-%m-%d') if offer_letter.expiration_date else 'N/A'
            }
        }
        
        return await self.notification_service.send_notification(
            recipient=self.candidate,
            template_name='candidate_offer_letter',
            context=context,
            notification_type='offer_letter_sent',
            channels=['email', 'whatsapp']
        )
    
    async def send_onboarding_info(
        self,
        position: str,
        start_date: str,
        documents_needed: List[str],
        contact_person: Optional[Person] = None
    ) -> Dict[str, bool]:
        """
        Send onboarding information to the candidate.
        
        Args:
            position: The position the candidate was hired for
            start_date: The start date of employment
            documents_needed: List of documents the candidate needs to provide
            contact_person: Optional person to contact with questions
            
        Returns:
            Dict mapping channel names to success status
        """
        context = {
            'candidate': {
                'name': self.candidate.nombre,
            },
            'onboarding': {
                'position': position,
                'start_date': start_date,
                'documents_needed': documents_needed,
                'contact_person': {
                    'name': contact_person.nombre if contact_person else None,
                    'email': contact_person.email if contact_person else None,
                    'phone': contact_person.phone if contact_person else None
                } if contact_person else None
            }
        }
        
        return await self.notification_service.send_notification(
            recipient=self.candidate,
            template_name='candidate_onboarding_info',
            context=context,
            notification_type='onboarding_info',
            channels=['email']
        )
