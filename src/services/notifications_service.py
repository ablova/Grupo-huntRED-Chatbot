"""
HuntRED® v2 - Notifications Service
Complete multi-channel notification system
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from enum import Enum
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    IN_APP = "in_app"

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"

class NotificationCategory(Enum):
    PAYROLL = "payroll"
    ATTENDANCE = "attendance"
    HR = "hr"
    SYSTEM = "system"
    MARKETING = "marketing"
    ALERTS = "alerts"
    REMINDERS = "reminders"

class NotificationsService:
    """Complete multi-channel notification system"""
    
    def __init__(self, db):
        self.db = db
        
        # Notification channels configuration
        self.channels = {
            "email": {
                "enabled": True,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "notifications@huntred.com",
                "password": "app_password",
                "from_email": "HuntRED® <notifications@huntred.com>",
                "rate_limit": 100,  # per minute
                "retry_attempts": 3
            },
            "sms": {
                "enabled": True,
                "provider": "twilio",
                "account_sid": "AC123456789",
                "auth_token": "auth_token",
                "from_number": "+525512345678",
                "rate_limit": 50,  # per minute
                "retry_attempts": 2
            },
            "whatsapp": {
                "enabled": True,
                "provider": "twilio",
                "account_sid": "AC123456789",
                "auth_token": "auth_token",
                "from_number": "whatsapp:+525512345678",
                "rate_limit": 30,  # per minute
                "retry_attempts": 2
            },
            "push": {
                "enabled": True,
                "provider": "firebase",
                "server_key": "firebase_server_key",
                "rate_limit": 1000,  # per minute
                "retry_attempts": 3
            },
            "slack": {
                "enabled": True,
                "webhook_url": "https://hooks.slack.com/services/...",
                "rate_limit": 1,  # per second
                "retry_attempts": 2
            },
            "teams": {
                "enabled": True,
                "webhook_url": "https://outlook.office.com/webhook/...",
                "rate_limit": 1,  # per second
                "retry_attempts": 2
            }
        }
        
        # Notification templates
        self.templates = {
            "payroll_processed": {
                "subject": "Nómina Procesada - {company_name}",
                "email_template": "payroll_processed_email.html",
                "sms_template": "Tu nómina ha sido procesada. Monto: ${amount} MXN",
                "whatsapp_template": "🎉 ¡Tu nómina está lista! Monto: ${amount} MXN. Consulta detalles en la app.",
                "push_template": {
                    "title": "Nómina Procesada",
                    "body": "Tu nómina de ${amount} MXN ha sido procesada"
                }
            },
            "attendance_reminder": {
                "subject": "Recordatorio de Asistencia",
                "email_template": "attendance_reminder_email.html",
                "sms_template": "Recordatorio: No olvides marcar tu asistencia hoy",
                "whatsapp_template": "⏰ Recordatorio: No olvides marcar tu entrada/salida",
                "push_template": {
                    "title": "Recordatorio de Asistencia",
                    "body": "No olvides marcar tu asistencia"
                }
            },
            "overtime_approved": {
                "subject": "Horas Extra Aprobadas",
                "email_template": "overtime_approved_email.html",
                "sms_template": "Tus horas extra han sido aprobadas: {hours} horas",
                "whatsapp_template": "✅ Horas extra aprobadas: {hours} horas. Serán incluidas en tu próxima nómina.",
                "push_template": {
                    "title": "Horas Extra Aprobadas",
                    "body": "{hours} horas extra han sido aprobadas"
                }
            },
            "system_alert": {
                "subject": "Alerta del Sistema - {alert_type}",
                "email_template": "system_alert_email.html",
                "slack_template": "🚨 *Alerta del Sistema*\n*Tipo:* {alert_type}\n*Mensaje:* {message}",
                "teams_template": "🚨 **Alerta del Sistema**\n**Tipo:** {alert_type}\n**Mensaje:** {message}"
            }
        }
        
        # User preferences
        self.default_preferences = {
            "email": True,
            "sms": False,
            "whatsapp": True,
            "push": True,
            "quiet_hours": {
                "enabled": True,
                "start": "22:00",
                "end": "07:00"
            },
            "categories": {
                "payroll": {"email": True, "whatsapp": True, "push": True},
                "attendance": {"email": False, "sms": True, "push": True},
                "hr": {"email": True, "whatsapp": False, "push": False},
                "system": {"email": True, "slack": True},
                "marketing": {"email": True, "whatsapp": False, "push": False}
            }
        }
    
    async def send_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification through appropriate channels"""
        try:
            notification_id = str(uuid.uuid4())
            
            # Extract notification data
            recipient = notification_data["recipient"]
            template_name = notification_data["template"]
            priority = NotificationPriority(notification_data.get("priority", "medium"))
            category = NotificationCategory(notification_data.get("category", "system"))
            variables = notification_data.get("variables", {})
            
            # Get user preferences
            user_preferences = await self._get_user_preferences(recipient.get("user_id"))
            
            # Determine channels to use
            channels = self._determine_channels(category, priority, user_preferences)
            
            # Create notification record
            notification = {
                "id": notification_id,
                "recipient": recipient,
                "template": template_name,
                "priority": priority.value,
                "category": category.value,
                "variables": variables,
                "channels": channels,
                "status": NotificationStatus.PENDING.value,
                "created_at": datetime.now(),
                "scheduled_at": notification_data.get("scheduled_at"),
                "attempts": 0,
                "results": {}
            }
            
            # Check if notification should be sent now or scheduled
            if notification_data.get("scheduled_at"):
                scheduled_time = datetime.fromisoformat(notification_data["scheduled_at"])
                if scheduled_time > datetime.now():
                    # Schedule notification
                    await self._schedule_notification(notification)
                    return {
                        "success": True,
                        "notification_id": notification_id,
                        "status": "scheduled",
                        "scheduled_at": scheduled_time.isoformat()
                    }
            
            # Send notification immediately
            results = await self._send_notification_to_channels(notification)
            notification["results"] = results
            notification["status"] = self._determine_overall_status(results)
            
            # Save notification
            # await self._save_notification(notification)
            
            logger.info(f"Notification {notification_id} sent successfully")
            
            return {
                "success": True,
                "notification_id": notification_id,
                "status": notification["status"],
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user notification preferences"""
        # Mock implementation - in real app, query from database
        return self.default_preferences
    
    def _determine_channels(self, category: NotificationCategory, 
                          priority: NotificationPriority, 
                          user_preferences: Dict[str, Any]) -> List[str]:
        """Determine which channels to use based on category, priority, and preferences"""
        
        channels = []
        
        # Get category preferences
        category_prefs = user_preferences.get("categories", {}).get(category.value, {})
        
        # Priority overrides for critical notifications
        if priority == NotificationPriority.CRITICAL:
            channels = ["email", "sms", "whatsapp", "push"]
        elif priority == NotificationPriority.HIGH:
            channels = ["email", "whatsapp", "push"]
        else:
            # Use user preferences
            for channel, enabled in category_prefs.items():
                if enabled:
                    channels.append(channel)
        
        # Filter by globally enabled channels
        enabled_channels = [ch for ch in channels if user_preferences.get(ch, False)]
        
        return enabled_channels
    
    async def _schedule_notification(self, notification: Dict[str, Any]) -> None:
        """Schedule notification for later delivery"""
        # Mock implementation - in real app, use task queue like Celery
        logger.info(f"Notification {notification['id']} scheduled for {notification['scheduled_at']}")
    
    async def _send_notification_to_channels(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification to all specified channels"""
        
        results = {}
        template_name = notification["template"]
        variables = notification["variables"]
        recipient = notification["recipient"]
        
        # Send to each channel
        for channel in notification["channels"]:
            try:
                if channel == "email":
                    result = await self._send_email(template_name, recipient, variables)
                elif channel == "sms":
                    result = await self._send_sms(template_name, recipient, variables)
                elif channel == "whatsapp":
                    result = await self._send_whatsapp(template_name, recipient, variables)
                elif channel == "push":
                    result = await self._send_push(template_name, recipient, variables)
                elif channel == "slack":
                    result = await self._send_slack(template_name, recipient, variables)
                elif channel == "teams":
                    result = await self._send_teams(template_name, recipient, variables)
                else:
                    result = {"success": False, "error": f"Unknown channel: {channel}"}
                
                results[channel] = result
                
            except Exception as e:
                logger.error(f"Error sending to {channel}: {e}")
                results[channel] = {"success": False, "error": str(e)}
        
        return results
    
    def _determine_overall_status(self, results: Dict[str, Any]) -> str:
        """Determine overall notification status based on channel results"""
        
        if not results:
            return NotificationStatus.FAILED.value
        
        successful = sum(1 for r in results.values() if r.get("success", False))
        total = len(results)
        
        if successful == total:
            return NotificationStatus.SENT.value
        elif successful > 0:
            return NotificationStatus.SENT.value  # Partial success still counts as sent
        else:
            return NotificationStatus.FAILED.value
    
    async def _send_email(self, template_name: str, recipient: Dict[str, Any], 
                         variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send email notification"""
        try:
            template = self.templates.get(template_name, {})
            subject = template.get("subject", "Notificación").format(**variables)
            
            # Generate email content
            content = await self._generate_email_content(template_name, variables)
            
            # Mock email sending
            # In real implementation, use SMTP or email service
            email_data = {
                "to": recipient.get("email"),
                "subject": subject,
                "content": content,
                "sent_at": datetime.now().isoformat()
            }
            
            logger.info(f"Email sent to {recipient.get('email')}")
            
            return {
                "success": True,
                "message_id": f"email_{uuid.uuid4().hex[:8]}",
                "data": email_data
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_sms(self, template_name: str, recipient: Dict[str, Any], 
                       variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            template = self.templates.get(template_name, {})
            message = template.get("sms_template", "Notificación").format(**variables)
            
            # Mock SMS sending
            # In real implementation, use Twilio or similar
            sms_data = {
                "to": recipient.get("phone"),
                "message": message,
                "sent_at": datetime.now().isoformat()
            }
            
            logger.info(f"SMS sent to {recipient.get('phone')}")
            
            return {
                "success": True,
                "message_id": f"sms_{uuid.uuid4().hex[:8]}",
                "data": sms_data
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_whatsapp(self, template_name: str, recipient: Dict[str, Any], 
                           variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send WhatsApp notification"""
        try:
            template = self.templates.get(template_name, {})
            message = template.get("whatsapp_template", "Notificación").format(**variables)
            
            # Mock WhatsApp sending
            # In real implementation, use Twilio WhatsApp API
            whatsapp_data = {
                "to": f"whatsapp:{recipient.get('phone')}",
                "message": message,
                "sent_at": datetime.now().isoformat()
            }
            
            logger.info(f"WhatsApp sent to {recipient.get('phone')}")
            
            return {
                "success": True,
                "message_id": f"whatsapp_{uuid.uuid4().hex[:8]}",
                "data": whatsapp_data
            }
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_push(self, template_name: str, recipient: Dict[str, Any], 
                        variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send push notification"""
        try:
            template = self.templates.get(template_name, {})
            push_template = template.get("push_template", {})
            
            title = push_template.get("title", "Notificación").format(**variables)
            body = push_template.get("body", "").format(**variables)
            
            # Mock push notification
            # In real implementation, use Firebase Cloud Messaging
            push_data = {
                "to": recipient.get("device_token"),
                "title": title,
                "body": body,
                "sent_at": datetime.now().isoformat()
            }
            
            logger.info(f"Push notification sent to {recipient.get('user_id')}")
            
            return {
                "success": True,
                "message_id": f"push_{uuid.uuid4().hex[:8]}",
                "data": push_data
            }
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_slack(self, template_name: str, recipient: Dict[str, Any], 
                         variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send Slack notification"""
        try:
            template = self.templates.get(template_name, {})
            message = template.get("slack_template", "Notificación").format(**variables)
            
            # Mock Slack sending
            # In real implementation, use Slack webhooks
            slack_data = {
                "channel": recipient.get("slack_channel", "#general"),
                "message": message,
                "sent_at": datetime.now().isoformat()
            }
            
            logger.info(f"Slack message sent to {recipient.get('slack_channel')}")
            
            return {
                "success": True,
                "message_id": f"slack_{uuid.uuid4().hex[:8]}",
                "data": slack_data
            }
            
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_teams(self, template_name: str, recipient: Dict[str, Any], 
                         variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send Microsoft Teams notification"""
        try:
            template = self.templates.get(template_name, {})
            message = template.get("teams_template", "Notificación").format(**variables)
            
            # Mock Teams sending
            # In real implementation, use Teams webhooks
            teams_data = {
                "channel": recipient.get("teams_channel"),
                "message": message,
                "sent_at": datetime.now().isoformat()
            }
            
            logger.info(f"Teams message sent to {recipient.get('teams_channel')}")
            
            return {
                "success": True,
                "message_id": f"teams_{uuid.uuid4().hex[:8]}",
                "data": teams_data
            }
            
        except Exception as e:
            logger.error(f"Error sending Teams message: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_email_content(self, template_name: str, 
                                    variables: Dict[str, Any]) -> str:
        """Generate email content from template"""
        
        # Mock email content generation
        # In real implementation, use templating engine like Jinja2
        base_content = f"""
        <html>
        <body>
            <h2>HuntRED® Notification</h2>
            <p>Template: {template_name}</p>
            <p>Variables: {json.dumps(variables, indent=2)}</p>
            <hr>
            <p>Este es un mensaje automático de HuntRED®</p>
        </body>
        </html>
        """
        
        return base_content
    
    async def send_bulk_notification(self, bulk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification to multiple recipients"""
        try:
            bulk_id = str(uuid.uuid4())
            recipients = bulk_data["recipients"]
            template_name = bulk_data["template"]
            variables = bulk_data.get("variables", {})
            
            # Process notifications in batches
            batch_size = 50
            batches = [recipients[i:i + batch_size] for i in range(0, len(recipients), batch_size)]
            
            results = {
                "bulk_id": bulk_id,
                "total_recipients": len(recipients),
                "successful": 0,
                "failed": 0,
                "results": []
            }
            
            for batch in batches:
                batch_results = await self._process_batch(batch, template_name, variables)
                results["results"].extend(batch_results)
                
                # Update counters
                for result in batch_results:
                    if result.get("success", False):
                        results["successful"] += 1
                    else:
                        results["failed"] += 1
            
            logger.info(f"Bulk notification {bulk_id} completed: {results['successful']}/{results['total_recipients']} successful")
            
            return {
                "success": True,
                "bulk_id": bulk_id,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error sending bulk notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_batch(self, recipients: List[Dict[str, Any]], 
                           template_name: str, variables: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a batch of recipients"""
        
        tasks = []
        for recipient in recipients:
            notification_data = {
                "recipient": recipient,
                "template": template_name,
                "variables": variables,
                "priority": "medium",
                "category": "system"
            }
            
            task = self.send_notification(notification_data)
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "recipient": recipients[i],
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append({
                    "recipient": recipients[i],
                    "success": result.get("success", False),
                    "notification_id": result.get("notification_id")
                })
        
        return processed_results
    
    async def update_user_preferences(self, user_id: str, 
                                    preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user notification preferences"""
        try:
            # Validate preferences
            if not self._validate_preferences(preferences):
                return {"success": False, "error": "Invalid preferences"}
            
            # Save preferences
            # await self._save_user_preferences(user_id, preferences)
            
            logger.info(f"Notification preferences updated for user {user_id}")
            
            return {
                "success": True,
                "user_id": user_id,
                "preferences": preferences
            }
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Validate notification preferences"""
        # Mock validation
        return True
    
    async def get_notification_history(self, user_id: str, 
                                     filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get notification history for a user"""
        try:
            # Mock notification history
            notifications = [
                {
                    "id": "notif_1",
                    "template": "payroll_processed",
                    "category": "payroll",
                    "priority": "high",
                    "status": "delivered",
                    "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
                    "channels": ["email", "whatsapp"]
                },
                {
                    "id": "notif_2",
                    "template": "attendance_reminder",
                    "category": "attendance",
                    "priority": "medium",
                    "status": "sent",
                    "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
                    "channels": ["push"]
                }
            ]
            
            return {
                "success": True,
                "user_id": user_id,
                "notifications": notifications,
                "total": len(notifications)
            }
            
        except Exception as e:
            logger.error(f"Error getting notification history: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_notification_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a notification campaign"""
        try:
            campaign_id = str(uuid.uuid4())
            
            campaign = {
                "id": campaign_id,
                "name": campaign_data["name"],
                "description": campaign_data.get("description"),
                "template": campaign_data["template"],
                "target_audience": campaign_data["target_audience"],
                "schedule": campaign_data.get("schedule"),
                "variables": campaign_data.get("variables", {}),
                "status": "draft",
                "created_at": datetime.now(),
                "stats": {
                    "total_recipients": 0,
                    "sent": 0,
                    "delivered": 0,
                    "failed": 0
                }
            }
            
            # Save campaign
            # await self._save_campaign(campaign)
            
            logger.info(f"Notification campaign {campaign_id} created")
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "campaign": campaign
            }
            
        except Exception as e:
            logger.error(f"Error creating notification campaign: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_notification_analytics(self, date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Get notification analytics"""
        try:
            # Mock analytics data
            analytics = {
                "period": date_range,
                "total_notifications": 1250,
                "by_channel": {
                    "email": 650,
                    "whatsapp": 300,
                    "push": 200,
                    "sms": 100
                },
                "by_category": {
                    "payroll": 400,
                    "attendance": 350,
                    "hr": 200,
                    "system": 150,
                    "marketing": 150
                },
                "by_status": {
                    "delivered": 1100,
                    "sent": 100,
                    "failed": 50
                },
                "delivery_rate": 88.0,
                "open_rate": 65.0,
                "click_rate": 12.0
            }
            
            return {
                "success": True,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting notification analytics: {e}")
            return {"success": False, "error": str(e)}

# Global notifications service
def get_notifications_service(db) -> NotificationsService:
    """Get notifications service instance"""
    return NotificationsService(db)