# Ubicacion SEXSI -- /home/pablo/app/sexsi/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from app.sexsi.models import ConsentAgreement

@receiver(post_save, sender=ConsentAgreement)
def track_agreement_updates(sender, instance, **kwargs):
    if instance.is_signed_by_creator and not instance.is_signed_by_invitee:
        print(f"Acuerdo {instance.id} firmado por el creador.")
    elif instance.is_signed_by_invitee and not instance.is_signed_by_creator:
        print(f"Acuerdo {instance.id} firmado por el invitado.")
    elif instance.is_signed_by_creator and instance.is_signed_by_invitee:
        print(f"Acuerdo {instance.id} completamente firmado.")
