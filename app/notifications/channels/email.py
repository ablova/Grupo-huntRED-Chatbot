from app.notifications.channels.basebase import BaseChannel
from django.core.mail import send_mail
from django.template.loader import render_to_string
import logging

logger = logging.getLogger('app.notifications.channels.email')

class EmailChannel(BaseChannel):
    """Clase para el canal de correo electrónico."""
    
    def send(self, recipient: Dict, message: str, context: Dict) -> bool:
        """Envía un correo electrónico."""
        try:
            # Renderizar template
            html_message = render_to_string(
                'notifications/email_template.html',
                context
            )
            
            # Enviar correo
            send_mail(
                subject=context.get('subject', 'Notificación de huntRED'),
                message=message,
                from_email='notifications@huntred.com',
                recipient_list=[recipient['email']],
                html_message=html_message
            )
            
            self._log_message(recipient, message, True)
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            self._log_message(recipient, message, False)
            return False
