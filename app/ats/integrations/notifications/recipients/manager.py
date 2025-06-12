"""
Manager notification handlers for the Grupo huntRED® Chatbot.

This module contains notification handlers specifically for managers and team leads,
including team performance metrics, approval requests, and important updates.
"""
import logging
from typing import Dict, Any, Optional, List, Union

from asgiref.sync import sync_to_async
from django.utils import timezone

from app.models import Person, BusinessUnit, Vacancy, CartaOferta, Team
from ....core.service import get_notification_service

logger = logging.getLogger(__name__)

class ManagerNotifier:
    """Handles notifications for managers and team leads."""
    
    def __init__(self, manager: Person, business_unit: Optional[BusinessUnit] = None):
        """
        Initialize the manager notifier.
        
        Args:
            manager: The manager to send notifications to
            business_unit: Optional business unit for the notification context
        """
        self.manager = manager
        self.business_unit = business_unit or manager.business_unit
        self.notification_service = get_notification_service()
    
    async def send_team_performance_report(
        self,
        team: Team,
        metrics: Dict[str, Any],
        time_period: str = 'weekly'
    ) -> Dict[str, bool]:
        """
        Send a team performance report to the manager.
        
        Args:
            team: The team the report is for
            metrics: Dictionary of performance metrics
            time_period: Time period the report covers (weekly, monthly, quarterly)
            
        Returns:
            Dict mapping channel names to success status
        """
        context = {
            'manager': {
                'name': self.manager.nombre,
                'title': self.manager.title or 'Manager'
            },
            'team': {
                'name': team.name,
                'member_count': await sync_to_async(team.members.count)()
            },
            'metrics': metrics,
            'report': {
                'time_period': time_period,
                'generated_at': timezone.now().strftime('%Y-%m-%d'),
                'timezone': 'UTC'
            },
            'business_unit': await self._get_business_unit_context()
        }
        
        return await self.notification_service.send_notification(
            recipient=self.manager,
            template_name='manager_team_performance_report',
            context=context,
            notification_type=f'team_performance_{time_period}',
            business_unit=self.business_unit,
            channels=['email']  # Performance reports are typically email-only
        )
    
    async def send_approval_request(
        self,
        request_type: str,
        requester: Person,
        details: Dict[str, Any],
        approval_url: str,
        due_date: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Send an approval request to the manager.
        
        Args:
            request_type: Type of approval needed (e.g., 'time_off', 'expense', 'hiring')
            requester: The person making the request
            details: Details of what needs approval
            approval_url: URL to approve/reject the request
            due_date: Optional due date for the approval
            
        Returns:
            Dict mapping channel names to success status
        """
        context = {
            'manager': {
                'name': self.manager.nombre,
            },
            'requester': {
                'name': requester.nombre,
                'title': requester.title or 'Team Member',
                'department': requester.department or 'N/A'
            },
            'request': {
                'type': request_type.replace('_', ' ').title(),
                'details': details,
                'submitted_at': timezone.now().strftime('%Y-%m-%d %H:%M'),
                'approval_url': approval_url,
                'due_date': due_date or (timezone.now() + timezone.timedelta(days=2)).strftime('%Y-%m-%d')
            },
            'business_unit': await self._get_business_unit_context()
        }
        
        return await self.notification_service.send_notification(
            recipient=self.manager,
            template_name=f'manager_approval_request_{request_type}',
            context=context,
            notification_type=f'approval_request_{request_type}',
            business_unit=self.business_unit,
            channels=['email', 'telegram']
        )
    
    async def send_budget_alert(
        self,
        budget_type: str,
        current_amount: float,
        budget_amount: float,
        threshold: float,
        time_period: str = 'monthly'
    ) -> Dict[str, bool]:
        """
        Send a budget alert to the manager.
        
        Args:
            budget_type: Type of budget (e.g., 'department', 'project', 'team')
            current_amount: Current amount spent/used
            budget_amount: Total budget amount
            threshold: Threshold percentage that triggered the alert
            time_period: Time period the budget applies to
            
        Returns:
            Dict mapping channel names to success status
        """
        percentage_used = (current_amount / budget_amount) * 100
        
        context = {
            'manager': {
                'name': self.manager.nombre,
            },
            'budget': {
                'type': budget_type,
                'current_amount': current_amount,
                'budget_amount': budget_amount,
                'percentage_used': round(percentage_used, 2),
                'threshold': threshold,
                'time_period': time_period,
                'remaining_amount': budget_amount - current_amount,
                'is_over_budget': percentage_used >= 100
            },
            'alert': {
                'severity': 'warning' if percentage_used < 90 else 'critical',
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M')
            },
            'business_unit': await self._get_business_unit_context()
        }
        
        return await self.notification_service.send_notification(
            recipient=self.manager,
            template_name='manager_budget_alert',
            context=context,
            notification_type='budget_alert',
            business_unit=self.business_unit,
            channels=['email', 'whatsapp'] if percentage_used >= 90 else ['email']
        )
    
    async def send_team_announcement(
        self,
        announcement: str,
        importance: str = 'normal',
        recipients: Optional[List[Person]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Dict[str, bool]]:
        """
        Send an announcement to team members on behalf of the manager.
        
        Args:
            announcement: The announcement content
            importance: Importance level (low, normal, high, critical)
            recipients: Optional list of specific recipients (defaults to manager's team)
            attachments: Optional list of file attachments
            
        Returns:
            Dict mapping recipient emails to dict of channel statuses
        """
        if recipients is None:
            # Default to manager's direct reports if no specific recipients provided
            team = await sync_to_async(lambda: self.manager.team_set.first())()
            if team:
                recipients = await sync_to_async(list)(team.members.all())
            else:
                recipients = []
        
        if attachments is None:
            attachments = []
        
        results = {}
        
        for recipient in recipients:
            context = {
                'recipient': {
                    'name': recipient.nombre,
                },
                'manager': {
                    'name': self.manager.nombre,
                    'title': self.manager.title or 'Manager',
                    'email': self.manager.email,
                    'phone': self.manager.phone
                },
                'announcement': {
                    'content': announcement,
                    'importance': importance,
                    'date': timezone.now().strftime('%Y-%m-%d')
                },
                'business_unit': await self._get_business_unit_context()
            }
            
            channel_status = await self.notification_service.send_notification(
                recipient=recipient,
                template_name='manager_team_announcement',
                context=context,
                notification_type='team_announcement',
                business_unit=self.business_unit,
                channels=self._get_announcement_channels(importance),
                attachments=attachments
            )
            
            results[recipient.email] = channel_status
        
        return results
    
    async def send_recruiting_update(
        self,
        vacancy: Vacancy,
        metrics: Dict[str, Any],
        time_period: str = 'weekly'
    ) -> Dict[str, bool]:
        """
        Send a recruiting update to the hiring manager.
        
        Args:
            vacancy: The vacancy being recruited for
            metrics: Dictionary of recruiting metrics
            time_period: Time period the update covers
            
        Returns:
            Dict mapping channel names to success status
        """
        context = {
            'manager': {
                'name': self.manager.nombre,
            },
            'vacancy': {
                'title': vacancy.titulo,
                'id': vacancy.id,
                'department': vacancy.department or 'N/A',
                'location': vacancy.location or 'Remote',
                'status': vacancy.status or 'Open',
                'open_date': vacancy.created_at.strftime('%Y-%m-%d') if vacancy.created_at else 'N/A'
            },
            'metrics': metrics,
            'report': {
                'time_period': time_period,
                'generated_at': timezone.now().strftime('%Y-%m-%d'),
                'timezone': 'UTC'
            },
            'business_unit': await self._get_business_unit_context()
        }
        
        return await self.notification_service.send_notification(
            recipient=self.manager,
            template_name='manager_recruiting_update',
            context=context,
            notification_type='recruiting_update',
            business_unit=self.business_unit,
            channels=['email']
        )
    
    # Helper methods
    
    async def _get_business_unit_context(self) -> Dict[str, str]:
        """Get business unit context for notifications."""
        if not self.business_unit:
            return {}
            
        return {
            'name': self.business_unit.name,
            'code': self.business_unit.code,
            'contact_email': getattr(self.business_unit, 'contact_email', 'support@huntred.com'),
            'support_phone': getattr(self.business_unit, 'support_phone', '+52 55 1234 5678')
        }
    
    @staticmethod
    def _get_announcement_channels(importance: str) -> List[str]:
        """Determine appropriate channels for announcements based on importance."""
        if importance in ['critical', 'high']:
            return ['email', 'whatsapp', 'telegram']
        return ['email']
