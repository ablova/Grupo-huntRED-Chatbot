# /home/pablollh/app/utilidades/signature/digital_sign.py

import os
from django.core.files.storage import default_storage
from django.utils.timezone import now
from django.conf import settings
import uuid

def save_signature(user, signature_file):
    """ Guarda la firma digital del usuario en el almacenamiento """
    signature_path = f"signatures/{user.id}_{uuid.uuid4().hex}.png"
    default_storage.save(signature_path, signature_file)
    return signature_path

def validate_signature_data(user, signature_data):
    """ Valida si un usuario ya ha firmado o si la firma es válida """
    return bool(signature_data) and not user.has_signed()

def request_digital_signature(user, document_path, document_name):
    """ Simula el proceso de solicitud de firma digital """
    signature_request = {
        "user": user.id,
        "document": document_path,
        "status": "pending",
        "request_date": now()
    }
    return signature_request