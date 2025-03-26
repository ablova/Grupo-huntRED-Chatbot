import os
import json
import base64
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from django.conf import settings
from app.sexsi.models import ConsentAgreement

def save_biometric_signature(request, agreement_id):
    """Guarda la firma biométrica junto con la ubicación del firmante."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    token = request.GET.get("token")
    signer = request.GET.get("signer", "invitee")

    # 📌 Validar el token de autenticidad
    if not agreement.token or agreement.token != token or agreement.token_expiry < now():
        return JsonResponse({"status": "error", "message": "⚠️ El token ha expirado o es inválido."}, status=400)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            biometric_data = data.get("biometric_data")
            latitude = data.get("latitude")
            longitude = data.get("longitude")

            # 📌 Validar si recibimos datos biométricos
            if not biometric_data:
                return JsonResponse({"status": "error", "message": "⚠️ No se recibió la firma biométrica."}, status=400)

            # 📌 Guardar la firma en la carpeta correspondiente
            biometric_filename = f"biometric_{agreement_id}_{signer}.png"
            biometric_dir = os.path.join(settings.MEDIA_ROOT, "biometric_signatures")
            os.makedirs(biometric_dir, exist_ok=True)
            biometric_path = os.path.join(biometric_dir, biometric_filename)

            with open(biometric_path, "wb") as f:
                f.write(base64.b64decode(biometric_data))

            biometric_url = os.path.join(settings.MEDIA_URL, "biometric_signatures", biometric_filename)

            # 📌 Guardar la firma en el modelo
            if signer == "creator":
                agreement.creator_signature = biometric_url
                agreement.is_signed_by_creator = True
                agreement.creator_latitude = latitude
                agreement.creator_longitude = longitude
            else:
                agreement.invitee_signature = biometric_url
                agreement.is_signed_by_invitee = True
                agreement.invitee_latitude = latitude
                agreement.invitee_longitude = longitude

            agreement.save()
            return JsonResponse({
                "status": "success",
                "message": "✅ Firma biométrica registrada correctamente.",
                "biometric_url": biometric_url,
                "latitude": latitude,
                "longitude": longitude
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"⚠️ Error procesando la firma: {str(e)}"}, status=500)

    return JsonResponse({"status": "error", "message": "⚠️ Método no permitido."}, status=405)