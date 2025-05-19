from app.notifications.recipients.basebase import BaseRecipient
from app.models import Person

class InterviewRecipient(BaseRecipient):
    """Clase para destinatarios de entrevistas."""
    
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
            'position': self.person.position,
            'interview_time': self.person.interview_time,
            'interview_location': self.person.interview_location,
            'interviewers': self.person.interviewers
        }
