"""
Gateways bancarios para pagos y cobros bidireccionales.
"""
from .bbva import BBVAGateway
from .santander import SantanderGateway
from .banamex import BanamexGateway
from .banorte import BanorteGateway

__all__ = [
    'BBVAGateway',
    'SantanderGateway', 
    'BanamexGateway',
    'BanorteGateway',
]

# Ejemplo de hook para notificación de pago exitoso
# from app.ats.integrations.notifications.recipients.client import ClientNotifier
# from app.models import Person
#
# def on_payment_success(client_id, amount, payment_date, payment_method, reference):
#     client = Person.objects.get(id=client_id)
#     notifier = ClientNotifier(client)
#     await notifier.send_payment_confirmation(amount, payment_date, payment_method, reference) 