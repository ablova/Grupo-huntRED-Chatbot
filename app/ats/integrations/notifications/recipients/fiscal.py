from app.ats.integrations.notifications.recipients.base import BaseRecipient
from app.models import Person

class FiscalRecipient(BaseRecipient):
    """Clase para destinatarios responsables fiscales."""
    
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
        return channels
        
    def get_notification_context(self) -> Dict:
        return {
            'name': self.person.full_name,
            'rfc': self.person.rfc,
            'company': self.person.company.name if self.person.company else 'N/A',
            'position': self.person.position
        }
