# /home/pablo/app/utilidades/signature/identity_validation.py
from django.utils.timezone import now
import re

def validate_identity(name, birthdate, conscious, sober):
    """ Valida la identidad del usuario antes de permitir la firma """
    if not re.match(r"^[A-Za-zÁÉÍÓÚÑáéíóúñ\s]{5,}$", name):
        return False, "El nombre ingresado no es válido."

    age = (now().date() - birthdate).days // 365
    if age < 18:
        return False, "Debes ser mayor de edad para firmar."

    if conscious.lower() != "sí":
        return False, "Debes estar en pleno uso de tus facultades."

    if sober.lower() == "sí":
        return False, "No puedes firmar si has consumido alcohol o drogas recientemente."

    return True, "✅ Identidad validada."