from typing import Dict, List, Optional
from .recipients import BaseRecipient
from .channels import BaseChannel
from .templates import BaseTemplate
from .config import NotificationsConfig
import logging

logger = logging.getLogger('app.notifications.manager')

class NotificationsManager:
    """Gestor centralizado de notificaciones."""
    
    def __init__(self):
        self.channels = self._initialize_channels()
        self.templates = self._initialize_templates()
        
    def _initialize_channels(self) -> Dict[str, BaseChannel]:
        """Inicializa todos los canales de comunicación."""
        channels = {}
        for channel_type in NotificationsConfig.get_priority_channels():
            config = NotificationsConfig.get_channel_config(channel_type[0])
            if config:
                try:
                    channel_class = self._get_channel_class(channel_type[0])
                    channels[channel_type[0]] = channel_class(**config)
                except Exception as e:
                    logger.error(f"Error initializing channel {channel_type[0]}: {str(e)}")
        return channels
    
    def _initialize_templates(self) -> Dict[str, BaseTemplate]:
        """Inicializa todos los templates disponibles."""
        templates = {}
        for template_type in NotificationsConfig.get_template_config():
            try:
                template_class = self._get_template_class(template_type)
                templates[template_type] = template_class()
            except Exception as e:
                logger.error(f"Error initializing template {template_type}: {str(e)}")
        return templates
    
    def _get_channel_class(self, channel_type: str) -> BaseChannel:
        """Obtiene la clase correspondiente a un canal."""
        from .channels import EmailChannel, WhatsAppChannel, XChannel
        
        channel_classes = {
            'email': EmailChannel,
            'whatsapp': WhatsAppChannel,
            'x': XChannel
        }
        
        return channel_classes.get(channel_type, BaseChannel)
    
    def _get_template_class(self, template_type: str) -> BaseTemplate:
        """Obtiene la clase correspondiente a un template."""
        from .templates import ProposalTemplate, PaymentTemplate, OpportunityTemplate
        
        template_classes = {
            'proposal': ProposalTemplate,
            'payment': PaymentTemplate,
            'opportunity': OpportunityTemplate
        }
        
        return template_classes.get(template_type, BaseTemplate)
    
    def send_notification(
        self,
        recipient: BaseRecipient,
        notification_type: str,
        context: Dict
    ) -> bool:
        """Envía una notificación a un destinatario."""
        try:
            # Obtener template
            template = self.templates.get(notification_type)
            if not template:
                logger.error(f"Template not found for type: {notification_type}")
                return False
                
            # Renderizar mensaje
            message = template.render(context)
            
            # Obtener canales preferidos
            preferred_channels = recipient.get_preferred_channels()
            
            # Intentar enviar por cada canal
            for channel_type in preferred_channels:
                channel = self.channels.get(channel_type)
                if channel:
                    contact_info = recipient.get_contact_info()
                    success = channel.send(
                        contact_info,
                        message,
                        context
                    )
                    
                    if success:
                        logger.info(
                            f"Notification sent successfully to {recipient} via {channel_type}"
                        )
                        return True
                        
                    logger.warning(
                        f"Failed to send notification via {channel_type}, trying next channel"
                    )
            
            logger.error("All channels failed to send notification")
            return False
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    def send_bulk_notifications(
        self,
        recipients: List[BaseRecipient],
        notification_type: str,
        context: Dict
    ) -> Dict[str, bool]:
        """Envía notificaciones en masa a múltiples destinatarios."""
        results = {}
        for recipient in recipients:
            results[str(recipient)] = self.send_notification(
                recipient,
                notification_type,
                context
            )
        return results
    
    def get_delivery_status(
        self,
        recipient: BaseRecipient,
        notification_type: str
    ) -> Dict:
        """Obtiene el estado de entrega de una notificación."""
        # Aquí iría la lógica para consultar el estado de entrega
        # Por ahora solo simulamos
        return {
            'status': 'delivered',
            'timestamp': None,
            'channel': None
        }
