# Ubicacion SEXSI -- /home/pablollh/app/sexsi/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.contrib import messages
from weasyprint import HTML

from app.sexsi.models import ConsentAgreement
from app.sexsi.forms import ConsentAgreementForm

from app.chatbot.integrations.services import send_message
from asgiref.sync import async_to_sync

from django.views.generic import ListView

import logging
import base64
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

class ConsentAgreementListView(ListView):
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
            agreement.tos_accepted = request.POST.get("accept_tos") == "on"
            agreement.tos_accepted_timestamp = now() if agreement.tos_accepted else None
            agreement.save()
            messages.success(request, "Acuerdo creado exitosamente. Recuerda que debes aceptar los Términos de Servicio y la Política de Privacidad.")
            invitation_link = send_invitation(agreement)
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
        messages.error(request, "El token de firma ha expirado o no es válido.")
        return redirect("sexsi:agreement_detail", agreement_id=agreement.id)

    return render(request, "sign_agreement.html", {"agreement": agreement, "signer": signer, "token": token})

@login_required
def upload_signature_and_selfie(request, agreement_id):
    """Sube tanto la firma autógrafa como la selfie con identificación para validación."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    signer = request.GET.get("signer")
    
    if request.method == "POST":
        signature = request.FILES.get("signature")
        selfie = request.FILES.get("selfie")
        
        if not signature or not selfie:
            logger.warning(f"Firma y/o selfie faltante para acuerdo {agreement.id}")
            return JsonResponse({"status": "error", "message": "Ambos archivos (firma y selfie) son requeridos."}, status=400)
        
        # Validación de formato
        allowed_formats = ["image/png", "image/jpeg"]
        if signature.content_type not in allowed_formats or selfie.content_type not in allowed_formats:
            logger.error(f"Formato de archivo inválido para acuerdo {agreement.id}")
            return JsonResponse({"status": "error", "message": "Formato inválido. Solo se permiten PNG y JPG."}, status=400)
        
        # Guardado seguro con nombres únicos
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
        logger.info(f"Firma y selfie registradas correctamente para acuerdo {agreement.id}")
        messages.success(request, "Firma y selfie registradas con éxito.")
        return redirect("sexsi:agreement_detail", agreement_id=agreement.id)
    
    return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)


@login_required
def download_pdf(request, agreement_id):
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    if agreement.is_signed_by_creator and agreement.is_signed_by_invitee:
        return generate_pdf_response(agreement)
    else:
        return HttpResponse("El acuerdo no está completamente firmado.", status=403)

# Helper functions
def send_invitation(agreement):
    invitation_link = agreement.build_invitation_link()
    send_message_to_invitee(invitation_link, agreement.invitee_contact)
    return invitation_link

def validate_token(agreement, token):
    return agreement.token == token and agreement.token_expiry > now()

def process_signature(agreement, request):
    signature = request.FILES.get("signature")
    user_lat = request.COOKIES.get("user_lat")
    user_lon = request.COOKIES.get("user_lon")
    if signature:
        agreement.invitee_signature = signature
        agreement.invitee_location = f"{user_lat}, {user_lon}" if user_lat and user_lon else "Ubicación no disponible"
        agreement.is_signed_by_invitee = True
        agreement.save()

def generate_pdf_response(agreement):
    html_string = render_to_string('pdf_template.html', {'agreement': agreement})
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{agreement.get_pdf_filename()}"'
    return response