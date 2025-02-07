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
    """Sube la firma y la selfie con identificación."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    signer = request.GET.get("signer")  # 🔹 Obtenemos 'signer' de la consulta GET

    if request.method == "POST":
        signature = request.FILES.get("signature")
        selfie = request.FILES.get("selfie")

        if not signature or not selfie:
            logger.warning(f"⚠️ Firma y/o selfie faltante para acuerdo {agreement.id}")
            return JsonResponse({"success": False, "message": "Firma y selfie son requeridas."}, status=400)

        # Validar formatos permitidos
        allowed_formats = ["image/png", "image/jpeg"]
        if signature.content_type not in allowed_formats or selfie.content_type not in allowed_formats:
            logger.error(f"⛔ Formato inválido en acuerdo {agreement.id}")
            return JsonResponse({"success": False, "message": "Formato inválido. Solo se permiten PNG y JPG."}, status=400)

        # Guardar con nombres únicos
        signature_path = f"signatures/{signer}_{agreement.id}_{now().timestamp()}.png"
        selfie_path = f"selfies/{signer}_{agreement.id}_{now().timestamp()}.png"
        default_storage.save(signature_path, ContentFile(signature.read()))
        default_storage.save(selfie_path, ContentFile(selfie.read()))

        if signer == "creator":
            agreement.creator_signature = signature_path
            agreement.creator_selfie = selfie_path
            agreement.is_signed_by_creator = True
        else:
            agreement.invitee_signature = signature_path
            agreement.invitee_selfie = selfie_path
            agreement.is_signed_by_invitee = True

        agreement.save()
        logger.info(f"✅ Firma y selfie guardadas para acuerdo {agreement.id}")
        messages.success(request, "✅ Firma y selfie registradas con éxito.")
        return JsonResponse({"success": True, "message": "✅ Firma y selfie registradas con éxito."})

    return JsonResponse({"success": False, "message": "⚠️ Método no permitido."}, status=405)

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