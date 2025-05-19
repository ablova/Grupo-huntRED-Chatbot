# /home/pablo/app/com/omnichannel.py
#
# Gestiona la comunicación omnicanal.
#
from django.core.mail import send_mail
import requests
from app.models import Person

class Omnichannel:
    def __init__(self):
        self.channels = {
            'email': self.send_email,
            'whatsapp': self.send_whatsapp,
            'x': self.send_x_dm
        }
        
    def send_email(self, recipient, message):
        """Envía un correo electrónico."""
        send_mail(
            subject="Notificación de Grupo huntRED®",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=False
        )
        
    def send_whatsapp(self, phone, message):
        """Envía un mensaje por WhatsApp."""
        if not phone:
            return False
            
        # Aquí iría la integración con WhatsApp Business API
        # Por ahora simulamos
        print(f"Enviando WhatsApp a {phone}: {message[:50]}...")
        return True
        
    def send_x_dm(self, handle, message):
        """Envía un DM en X."""
        if not handle:
            return False
            
        # Aquí iría la integración con X API
        # Por ahora simulamos
        print(f"Enviando DM a {handle}: {message[:50]}...")
        return True
        
    def send_notification(self, recipient, message):
        """
        Envía una notificación a través de múltiples canales.
        
        Args:
            recipient: Objeto Person
            message: Mensaje a enviar
            
        Returns:
            Dict con resultados por canal
        """
        results = {}
        
        # Email
        try:
            self.send_email(recipient, message)
            results['email'] = True
        except Exception as e:
            results['email'] = str(e)
            
        # WhatsApp
        if recipient.phone:
            try:
                self.send_whatsapp(recipient.phone, message)
                results['whatsapp'] = True
            except Exception as e:
                results['whatsapp'] = str(e)
                
        # X DM
        if recipient.social_handles and 'x' in recipient.social_handles:
            try:
                self.send_x_dm(recipient.social_handles['x'], message)
                results['x'] = True
            except Exception as e:
                results['x'] = str(e)
                
        return results
