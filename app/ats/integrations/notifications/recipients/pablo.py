"""
Notification handlers for system monitoring and control in Grupo huntRED®.

This module handles all system monitoring notifications and alerts,
including task assignments, system health, and performance metrics.
Primarily used for system administration and monitoring purposes.
"""
import logging
from typing import Dict, Any, Optional, List, Union

from asgiref.sync import sync_to_async
from django.utils import timezone

from app.models import Person, BusinessUnit, Vacancy, CartaOferta
from app.ats.integrations.notifications.core.service import get_notification_service
from app.ats.integrations.notifications.recipients.base import BaseRecipient

logger = logging.getLogger(__name__)

class PabloNotifier:
    """Handles system monitoring and control notifications.
    
    This class is responsible for sending notifications related to system monitoring,
    alerts, and administrative tasks. It's the primary way the system communicates
    with administrators and monitoring systems.
    """
    
    def __init__(self, business_unit: Optional[BusinessUnit] = None):
        """
        Initialize the system monitoring notifier.
        
        Args:
            business_unit: Optional business unit for the notification context
        """
        self.business_unit = business_unit
        self.notification_service = get_notification_service()
    
    async def send_task_assignment(
        self,
        assignee: Person,
        task_title: str,
        task_description: str,
        due_date: Optional[str] = None,
        priority: str = 'medium',
        task_url: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Notify a team member about a new task assignment.
        
        Args:
            assignee: The team member who is assigned the task
            task_title: Title of the task
            task_description: Detailed description of the task
            due_date: Optional due date for the task
            priority: Priority level (low, medium, high, critical)
            task_url: Optional URL to view the task details
            
        Returns:
            Dict mapping channel names to success status
        """
        context = {
            'assignee': {
                'name': assignee.nombre,
            },
            'task': {
                'title': task_title,
                'description': task_description,
                'due_date': due_date or 'No due date',
                'priority': priority.lower(),
                'url': task_url,
                'assigned_date': timezone.now().strftime('%Y-%m-%d')
            },
            'business_unit': self._get_business_unit_context()
        }
        
        return await self.notification_service.send_notification(
            recipient=assignee,
            template_name='internal_task_assignment',
            context=context,
            notification_type='task_assignment',
            business_unit=self.business_unit,
            channels=['email', 'telegram']
        )
    
    async def send_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = 'warning',
        related_object: Optional[Any] = None,
        recipients: Optional[List[Person]] = None
    ) -> Dict[str, Dict[str, bool]]:
        """
        Send a system alert to the relevant team members.
        
        Args:
            alert_type: Type of alert (e.g., 'error', 'warning', 'info')
            message: Detailed message about the alert
            severity: Severity level (info, warning, error, critical)
            related_object: Optional related object (e.g., a model instance)
            recipients: Optional list of specific recipients
            
        Returns:
            Dict mapping recipient emails to dict of channel statuses
        """
        if not recipients:
            # Default to system administrators if no specific recipients provided
            recipients = await self._get_system_recipients(alert_type, severity)
        
        results = {}
        
        for recipient in recipients:
            context = {
                'alert': {
                    'type': alert_type,
                    'message': message,
                    'severity': severity,
                    'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'related_object': self._format_related_object(related_object)
                },
                'business_unit': self._get_business_unit_context()
            }
            
            channel_status = await self.notification_service.send_notification(
                recipient=recipient,
                template_name='internal_system_alert',
                context=context,
                notification_type=f'system_alert_{alert_type}',
                business_unit=self.business_unit,
                channels=self._get_alert_channels(severity)
            )
            
            results[recipient.email] = channel_status
        
        return results
    
    async def send_metrics_report(
        self,
        metrics: Dict[str, Any],
        time_period: str = 'daily',
        recipients: Optional[List[Person]] = None
    ) -> Dict[str, Dict[str, bool]]:
        """
        Send a metrics report to the relevant team members.
        
        Args:
            metrics: Dictionary of metrics to include in the report
            time_period: Time period the report covers (daily, weekly, monthly)
            recipients: Optional list of specific recipients
            
        Returns:
            Dict mapping recipient emails to dict of channel statuses
        """
        if not recipients:
            # Default to managers and above if no specific recipients provided
            recipients = await self._get_report_recipients()
        
        results = {}
        
        for recipient in recipients:
            context = {
                'metrics': metrics,
                'report': {
                    'time_period': time_period,
                    'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M'),
                    'timezone': 'UTC'
                },
                'recipient': {
                    'name': recipient.nombre,
                    'role': recipient.role or 'Team Member'
                },
                'business_unit': self._get_business_unit_context()
            }
            
            channel_status = await self.notification_service.send_notification(
                recipient=recipient,
                template_name='internal_metrics_report',
                context=context,
                notification_type=f'metrics_report_{time_period}',
                business_unit=self.business_unit,
                channels=['email']  # Metrics reports are typically email-only
            )
            
            results[recipient.email] = channel_status
        
        return results
    
    async def send_offer_letter_notification(
        self,
        offer_letter: CartaOferta,
        action: str,
        additional_context: Optional[Dict] = None
    ) -> Dict[str, bool]:
        """
        Send a notification about an offer letter action.
        
        Args:
            offer_letter: The offer letter in question
            action: The action taken (created, sent, signed, expired, etc.)
            additional_context: Additional context for the notification
            
        Returns:
            Dict mapping channel names to success status
        """
        if additional_context is None:
            additional_context = {}
            
        context = {
            'offer_letter': {
                'id': offer_letter.id,
                'candidate_name': offer_letter.user.nombre if offer_letter.user else 'Unknown',
                'position': offer_letter.vacancy.titulo if offer_letter.vacancy else 'Unknown Position',
                'status': offer_letter.status,
                'created_at': offer_letter.created_at.strftime('%Y-%m-%d') if offer_letter.created_at else 'N/A',
                'expiration_date': offer_letter.expiration_date.strftime('%Y-%m-%d') if offer_letter.expiration_date else 'N/A'
            },
            'action': action,
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            **additional_context
        }
        
        # Determine recipients based on the action
        recipients = await self._get_offer_letter_recipients(offer_letter, action)
        
        results = {}
        for recipient in recipients:
            channel_status = await self.notification_service.send_notification(
                recipient=recipient,
                template_name=f'internal_offer_letter_{action}',
                context={
                    **context,
                    'recipient': {
                        'name': recipient.nombre,
                        'role': recipient.role or 'Team Member'
                    }
                },
                notification_type=f'offer_letter_{action}',
                business_unit=self.business_unit,
                channels=['email', 'telegram']
            )
            results[recipient.email] = channel_status
        
        return results
    
    # Helper methods
    
    def _get_business_unit_context(self) -> Dict[str, str]:
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
    async def _get_system_recipients(alert_type: str, severity: str) -> List[Person]:
        """Get appropriate recipients for system alerts."""
        from app.models import Person
        
        # Base query for system administrators
        query = Person.objects.filter(is_staff=True, is_active=True)
        
        # For critical alerts, include additional team members
        if severity in ['error', 'critical']:
            query = query.filter(role__in=['admin', 'manager', 'devops'])
        
        # Convert to list to force evaluation of the queryset
        return await sync_to_async(list)(query)
    
    @staticmethod
    async def _get_report_recipients() -> List[Person]:
        """Get recipients for reports."""
        from app.models import Person
        
        # Typically managers and above receive reports
        query = Person.objects.filter(
            is_active=True,
            role__in=['manager', 'director', 'vp', 'executive']
        )
        
        return await sync_to_async(list)(query)
    
    @staticmethod
    async def _get_offer_letter_recipients(offer_letter: CartaOferta, action: str) -> List[Person]:
        """Get appropriate recipients for offer letter notifications."""
        from app.models import Person
        
        recipients = set()
        
        # Always include the recruiter/account manager
        if offer_letter.vacancy and offer_letter.vacancy.recruiter:
            recipients.add(offer_letter.vacancy.recruiter)
        
        # For signed/expired offers, include hiring manager
        if action in ['signed', 'expired'] and offer_letter.vacancy and offer_letter.vacancy.hiring_manager:
            recipients.add(offer_letter.vacancy.hiring_manager)
        
        # For critical actions, include department head
        if action in ['expired', 'rejected'] and offer_letter.vacancy and offer_letter.vacancy.department:
            dept_head_query = Person.objects.filter(
                department=offer_letter.vacancy.department,
                role__in=['manager', 'director'],
                is_active=True
            )
            dept_heads = await sync_to_async(list)(dept_head_query)
            recipients.update(dept_heads)
        
        return list(recipients)
    
    @staticmethod
    def _get_alert_channels(severity: str) -> List[str]:
        """Determine appropriate channels for alerts based on severity."""
        if severity in ['critical', 'error']:
            return ['email', 'telegram', 'whatsapp']
        elif severity == 'warning':
            return ['email', 'telegram']
        return ['email']
    
    @staticmethod
    def _format_related_object(obj: Any) -> Optional[Dict]:
        """Format a related object for inclusion in notifications."""
        if not obj:
            return None
            
        return {
            'type': obj.__class__.__name__,
            'id': getattr(obj, 'id', None),
            'name': getattr(obj, 'name', None) or getattr(obj, 'title', None) or str(obj)
        }
