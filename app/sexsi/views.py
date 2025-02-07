 # Ubicacion SEXSI -- /home/pablollh/app/sexsi/views.py

from django.views.generic import ListView
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from django.contrib import messages
from weasyprint import HTML
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from app.sexsi.models import ConsentAgreement
from app.sexsi.forms import ConsentAgreementForm
from app.chatbot.integrations.services import send_message
from asgiref.sync import async_to_sync
import json
import os
import logging

logger = logging.getLogger(__name__)

STATUS_TRANSITIONS = {
    "draft": "pending_review",
    "pending_review": "signed",
    "signed": "completed",
    "needs_revision": "pending_review"
}
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
    if request.method == 'POST':
        form = ConsentAgreementForm(request.POST)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.creator = request.user
            agreement.status = "draft"
            agreement.tos_accepted = request.POST.get("accept_tos") == "on"
            agreement.tos_accepted_timestamp = now() if agreement.tos_accepted else None
            agreement.save()
            messages.success(request, "✅ Acuerdo creado exitosamente.")
            return redirect('sexsi:agreement_detail', agreement.id)
    else:
        form = ConsentAgreementForm()
    return render(request, 'create_agreement.html', {'form': form})

@login_required
def agreement_detail(request, agreement_id):
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    return render(request, 'agreement_detail.html', {'agreement': agreement})

def sign_agreement(request, agreement_id, signer, token):
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    if not validate_token(agreement, token):
        messages.error(request, "⚠️ Token inválido o expirado.")
        return redirect("sexsi:agreement_detail", agreement_id=agreement.id)
    return render(request, "sign_agreement.html", {"agreement": agreement, "signer": signer, "token": token})

@login_required
def upload_signature_and_selfie(request, agreement_id):
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    signer = request.GET.get("signer", "invitee")

    if request.method == "POST":
        signature = request.FILES.get("signature")
        selfie = request.FILES.get("selfie")

        if not signature or not selfie:
            return JsonResponse({"success": False, "message": "⚠️ Debes subir una firma y una selfie."}, status=400)

        signature_path = f"signatures/{signer}_{agreement.id}_{now().timestamp()}.png"
        selfie_path = f"selfies/{signer}_{agreement.id}_{now().timestamp()}.png"
        default_storage.save(signature_path, ContentFile(signature.read()))
        default_storage.save(selfie_path, ContentFile(selfie.read()))

        if signer == "creator":
            agreement.creator_signature = signature_path
            agreement.creator_selfie = selfie_path
            agreement.is_signed_by_creator = True
            agreement.status = "pending_review"
        else:
            agreement.invitee_signature = signature_path
            agreement.invitee_selfie = selfie_path
            agreement.is_signed_by_invitee = True
            if agreement.is_signed_by_creator:
                agreement.status = "signed"
        
        agreement.save()
        return JsonResponse({"success": True, "message": "✅ Firma y selfie registradas correctamente."})

@login_required
def request_revision(request, agreement_id):
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    if request.method == 'POST':
        agreement.status = 'needs_revision'
        agreement.is_signed_by_creator = False
        agreement.is_signed_by_invitee = False
        agreement.save()
        return JsonResponse({"success": True, "message": "✅ Solicitud de revisión enviada."})
    
@login_required
def revoke_agreement(request, agreement_id):
    """Permite al invitado rechazar el acuerdo y devolverlo al creador sin posibilidad de modificación."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)

    if request.method == 'POST':
        agreement.status = 'revoked'
        agreement.is_signed_by_creator = False
        agreement.is_signed_by_invitee = False
        agreement.save()

        messages.warning(request, "🚨 El acuerdo ha sido revocado y notificado al creador.")
        return JsonResponse({"success": True, "message": "✅ Acuerdo revocado correctamente."})

    return JsonResponse({"success": False, "message": "⚠️ Método no permitido."}, status=405)

@login_required
def finalize_agreement(request, agreement_id, signer, token):
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    if not validate_token(agreement, token):
        return JsonResponse({"success": False, "message": "⚠️ Token inválido o expirado."}, status=400)

    if signer == "creator":
        agreement.is_signed_by_creator = True
        agreement.status = "pending_review"
    elif signer == "invitee":
        agreement.is_signed_by_invitee = True
        if agreement.is_signed_by_creator:
            agreement.status = "signed"

    agreement.save()
    return JsonResponse({"success": True, "message": "✅ Acuerdo actualizado."})

@login_required
def download_pdf(request, agreement_id):
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    if agreement.status == "signed":
        return generate_pdf_response(agreement)
    else:
        return HttpResponse("⚠️ El acuerdo no está completamente firmado.", status=403)

def generate_pdf_response(agreement):
    html_string = render_to_string('pdf_template.html', {'agreement': agreement})
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="agreement_{agreement.id}.pdf"'
    return response

# Funciones auxiliares

def validate_token(agreement, token):
    """Valida que el token de firma sea válido y no haya expirado."""
    return agreement.token == token and agreement.token_expiry > now()
