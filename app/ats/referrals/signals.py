from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import ReferralProgram

@receiver(post_save, sender=ReferralProgram)
def handle_referral_creation(sender, instance, created, **kwargs):
    """
    Maneja eventos después de crear o actualizar una referencia
    """
    if created:
        # Enviar email al referidor
        send_mail(
            'Nueva Referencia Creada',
            f'''
            Has creado una nueva referencia para {instance.referred_company}.
            
            Código de Referencia: {instance.referral_code}
            Porcentaje de Comisión: {instance.commission_percentage}%
            
            Comparte este código con la empresa referida para que lo use al crear su propuesta.
            ''',
            settings.DEFAULT_FROM_EMAIL,
            [instance.referrer.email],
            fail_silently=True,
        )
    elif instance.is_completed and not instance._original_status:
        # Enviar email cuando la referencia se completa
        send_mail(
            'Referencia Completada',
            f'''
            ¡Felicidades! Tu referencia para {instance.referred_company} ha sido completada.
            
            Detalles:
            - Código de Referencia: {instance.referral_code}
            - Comisión: {instance.commission_percentage}%
            - Valor de la Propuesta: ${instance.proposal.total_value}
            - Comisión Calculada: ${instance.calculate_commission}
            
            El pago de tu comisión se realizará según los términos acordados.
            ''',
            settings.DEFAULT_FROM_EMAIL,
            [instance.referrer.email],
            fail_silently=True,
        )

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._original_status = self.status 