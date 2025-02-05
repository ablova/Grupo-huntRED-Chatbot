# Ubicacion SEXSI -- /home/pablollh/sexsi/biometric_auth.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils.timezone import now
from django.contrib import messages
from .models import ConsentAgreement
import base64
import json

# Función para guardar la firma biométrica (huella digital o reconocimiento facial)
def save_biometric_signature(request, agreement_id):
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    token = request.GET.get("token")
    signer = request.GET.get("signer", "invitee")
    
    # Verificar validez del token
    if not agreement.token or agreement.token != token or agreement.token_expiry < now():
        return JsonResponse({"status": "error", "message": "El token de firma ha expirado o no es válido."}, status=400)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            biometric_data = data.get("biometric_data")  # Se espera en formato base64
            
            if not biometric_data:
                return JsonResponse({"status": "error", "message": "Datos biométricos no recibidos."}, status=400)
            
            # Decodificar la imagen biométrica en base64 y guardarla como archivo
            biometric_filename = f"biometric_{agreement_id}_{signer}.png"
            biometric_path = f"media/biometric_signatures/{biometric_filename}"
            with open(biometric_path, "wb") as f:
                f.write(base64.b64decode(biometric_data))
            
            # Guardar en el modelo de ConsentAgreement
            if signer == "creator":
                agreement.creator_signature = biometric_path
                agreement.is_signed_by_creator = True
            else:
                agreement.invitee_signature = biometric_path
                agreement.is_signed_by_invitee = True
            
            agreement.save()
            return JsonResponse({"status": "success", "message": "Firma biométrica registrada correctamente."})
        
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error procesando datos biométricos: {str(e)}"}, status=500)
    
    return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)
