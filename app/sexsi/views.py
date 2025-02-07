import logging
import json
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.contrib import messages
from weasyprint import HTML
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from app.sexsi.models import ConsentAgreement
from app.sexsi.forms import ConsentAgreementForm
from app.chatbot.integrations.services import send_message
from asgiref.sync import async_to_sync
from django.views.generic import ListView

# Inicializar logger
logger = logging.getLogger(__name__)

### 📌 VISTAS PRINCIPALES

class ConsentAgreementListView(ListView):
    """Vista para listar acuerdos creados por el usuario."""
    model = ConsentAgreement
    template_name = "consent_list.html"
    context_object_name = "agreements"

    def get_queryset(self):
        return ConsentAgreement.objects.filter(creator=self.request.user)

@login_required
def create_agreement(request):
    """Vista para crear un nuevo acuerdo."""
    if request.method == 'POST':
        form = ConsentAgreementForm(request.POST)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.creator = request.user
            agreement.tos_accepted = request.POST.get("accept_tos") == "on"
            agreement.tos_accepted_timestamp = now() if agreement.tos_accepted else None
            agreement.save()
            messages.success(request, "✅ Acuerdo creado exitosamente.")
            send_invitation(agreement)
            return redirect('sexsi:agreement_detail', agreement.id)
    else:
        form = ConsentAgreementForm()
    return render(request, 'create_agreement.html', {'form': form})

@login_required
def agreement_detail(request, agreement_id):
    """Muestra los detalles de un acuerdo específico."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    return render(request, 'agreement_detail.html', {'agreement': agreement})

def sign_agreement(request, agreement_id, signer, token):
    """Página de firma del acuerdo."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)

    if not validate_token(agreement, token):
        messages.error(request, "⚠️ Token inválido o expirado.")
        return redirect("sexsi:agreement_detail", agreement_id=agreement.id)

    return render(request, "sign_agreement.html", {"agreement": agreement, "signer": signer, "token": token})

@login_required
def upload_signature_and_selfie(request, agreement_id):
    """Sube la firma, la selfie con identificación y almacena la ubicación."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    signer = request.GET.get("signer")
    
    if request.method == "POST":
        signature = request.FILES.get("signature")
        biometric_data = request.POST.get("biometric_data")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        if not signature and not biometric_data:
            logger.warning(f"⚠️ Firma faltante para acuerdo {agreement.id}")
            return JsonResponse({"status": "error", "message": "Se requiere una firma (imagen o digital)."}, status=400)

        # Guardado seguro con nombres únicos
        if signature:
            signature_path = f"signatures/{signer}_{agreement.id}_{now().timestamp()}.png"
            default_storage.save(signature_path, ContentFile(signature.read()))
            if signer == "creator":
                agreement.creator_signature = signature_path
            else:
                agreement.invitee_signature = signature_path
        
        if biometric_data:
            biometric_path = f"signatures/{signer}_biometric_{agreement.id}_{now().timestamp()}.png"
            format, imgstr = biometric_data.split(';base64,')
            ext = format.split('/')[-1]
            biometric_file = ContentFile(base64.b64decode(imgstr), name=f"{biometric_path}.{ext}")
            default_storage.save(biometric_path, biometric_file)
            if signer == "creator":
                agreement.creator_signature = biometric_path
            else:
                agreement.invitee_signature = biometric_path
        
        # Guardar ubicación
        if signer == "creator":
            agreement.creator_location = f"{latitude}, {longitude}" if latitude and longitude else "Ubicación no disponible"
            agreement.is_signed_by_creator = True
        else:
            agreement.invitee_location = f"{latitude}, {longitude}" if latitude and longitude else "Ubicación no disponible"
            agreement.is_signed_by_invitee = True
        
        agreement.save()
        logger.info(f"✅ Firma registrada con éxito para acuerdo {agreement.id}")
        messages.success(request, "✅ Firma registrada con éxito.")
        return redirect("sexsi:agreement_detail", agreement_id=agreement.id)
    
    return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)

@login_required
def download_pdf(request, agreement_id):
    """Genera y permite la descarga del acuerdo en PDF."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    if agreement.is_signed_by_creator and agreement.is_signed_by_invitee:
        return generate_pdf_response(agreement)
    else:
        return HttpResponse("⚠️ El acuerdo no está completamente firmado.", status=403)

# Funciones auxiliares

def validate_token(agreement, token):
    """Valida que el token de firma sea válido y no haya expirado."""
    return agreement.token == token and agreement.token_expiry > now()

def generate_pdf_response(agreement):
    """Genera un PDF con los datos del acuerdo."""
    html_string = render_to_string('pdf_template.html', {'agreement': agreement})
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{agreement.get_pdf_filename()}"'
    return response