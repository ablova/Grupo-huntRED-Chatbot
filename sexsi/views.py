# Ubicacion SEXSI -- /home/pablollh/sexsi/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
from weasyprint import HTML
from .models import ConsentAgreement
from .forms import ConsentAgreementForm
from django.utils.timezone import now
from django.contrib import messages
import datetime
import json

# Se utiliza la función send_message ya implementada en el chatbot.
from app.chatbot.integrations.services import send_message

from django.views.generic import ListView

class ConsentAgreementListView(ListView):
    model = ConsentAgreement
    template_name = "sexsi/consent_list.html"
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
            agreement.save()
            # Se genera el link único para que la contraparte revise y firme
            invitation_link = request.build_absolute_uri(
                reverse('sexsi:agreement_detail', args=[agreement.id])
            ) + f"?token={agreement.token}"
            # Se asume que se utiliza el mismo canal (por ejemplo, WhatsApp)
            platform = "whatsapp"
            # Se intenta obtener la BusinessUnit del usuario (si está definida)
            business_unit = (request.user.businessunit_set.first() 
                             if request.user.businessunit_set.exists() else None)
            message = (
                "Hola, tienes un acuerdo pendiente para revisar y firmar. "
                f"Por favor, visita el siguiente enlace: {invitation_link}"
            )
            # Se envía el mensaje utilizando el desarrollo actual del chatbot
            async_to_sync(send_message)(platform, agreement.invitee_contact, message, business_unit)
            return redirect('sexsi:agreement_detail', agreement_id=agreement.id)
    else:
        form = ConsentAgreementForm()
    return render(request, 'sexsi/create_agreement.html', {'form': form})

@login_required
def agreement_detail(request, agreement_id):
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    return render(request, 'sexsi/agreement_detail.html', {'agreement': agreement})

# Verificar Token Expirable y Validar Firma

def sign_agreement(request, agreement_id):
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    token = request.GET.get("token")
    signer = request.GET.get("signer", "invitee")
    
    # Verificar que el token sea válido y no haya expirado (24h de validez)
    if not agreement.token or agreement.token != token or agreement.token_expiry < now():
        messages.error(request, "El token de firma ha expirado o no es válido.")
        return redirect("sexsi:agreement_detail", agreement_id=agreement.id)
    
    if request.method == "POST":
        signature = request.FILES.get("signature")
        user_lat = request.COOKIES.get("user_lat")
        user_lon = request.COOKIES.get("user_lon")
        
        if not signature:
            messages.error(request, "Debe subir una firma válida.")
            return redirect("sexsi:sign_agreement", agreement_id=agreement.id, token=token)
        
        # Guardar firma y ubicación
        if signer == "creator":
            agreement.creator_signature = signature
            agreement.creator_location = f"{user_lat}, {user_lon}" if user_lat and user_lon else "Ubicación no disponible"
            agreement.is_signed_by_creator = True
        else:
            agreement.invitee_signature = signature
            agreement.invitee_location = f"{user_lat}, {user_lon}" if user_lat and user_lon else "Ubicación no disponible"
            agreement.is_signed_by_invitee = True
        
        agreement.save()
        messages.success(request, "Firma registrada con éxito.")
        return redirect("sexsi:agreement_detail", agreement_id=agreement.id)
    
    return render(request, "sign_agreement.html", {"agreement": agreement, "token": token})


@login_required
def download_pdf(request, agreement_id):
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    # Solo se permite la descarga si ambos han firmado el acuerdo.
    if not (agreement.is_signed_by_creator and agreement.is_signed_by_invitee):
        return HttpResponse("El acuerdo no está completamente firmado.", status=403)
    html_string = render_to_string('sexsi/pdf_template.html', {'agreement': agreement})
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="acuerdo_sexsi.pdf"'
    return response