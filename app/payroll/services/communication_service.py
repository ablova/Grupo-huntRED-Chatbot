from app.payroll.models import PayrollEmployee
from django.core.mail import send_mail
from django.conf import settings

class CommunicationService:
    """
    Servicio para comunicación supervisor-empleado sin exponer datos personales
    """
    def enviar_mensaje_a_supervisor(self, empleado: PayrollEmployee, mensaje: str):
        supervisor = empleado.supervisor
        if supervisor and supervisor.email:
            send_mail(
                subject=f"Mensaje de {empleado.get_full_name()} (Payroll)",
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[supervisor.email],
            )
        # Aquí puedes integrar WhatsApp si está disponible
        # Ejemplo: WhatsAppService.send_message(supervisor, mensaje)
        return True

    def enviar_respuesta_a_empleado(self, supervisor, empleado: PayrollEmployee, mensaje: str):
        if empleado and empleado.user.email:
            send_mail(
                subject=f"Respuesta de tu supervisor {supervisor.get_full_name()}",
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[empleado.user.email],
            )
        # WhatsApp opcional
        return True 