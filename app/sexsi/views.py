# app/sexsi/views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

 # Ubicacion SEXSI -- /home/pablo/app/sexsi/views.py
import paypalrestsdk
from django.shortcuts import redirect
from django.views.generic import ListView
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from django.contrib import messages
from weasyprint import HTML
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from app.sexsi.forms import ConsentAgreement, PaymentTransaction, Preference, ConsentAgreementForm, DiscountCoupon
from app.ats.integrations.services import send_message, email_service
from asgiref.sync import async_to_sync
import json
import os
import logging

logger = logging.getLogger(__name__)

####  📌 VISTAS PAYPAL
@csrf_exempt
def paypal_webhook(request):
    """ Recibe notificaciones de PayPal y actualiza el estado de los pagos """
    try:
        data = json.loads(request.body)
        event_type = data.get("event_type")

        if event_type == "PAYMENT.SALE.COMPLETED":
            transaction_id = data["resource"]["id"]
            agreement_id = data["resource"]["invoice_id"]  # Asegúrate de enviar este ID al crear el pago
            
            # Actualiza la transacción en la base de datos
            transaction = PaymentTransaction.objects.filter(paypal_transaction_id=transaction_id).first()
            if transaction:
                transaction.transaction_status = "completed"
                transaction.save()

                return JsonResponse({"status": "success", "message": "Pago procesado exitosamente."}, status=200)

        return JsonResponse({"status": "ignored", "message": "Evento no manejado."}, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


def process_payment(request, agreement_id):
    """Inicia el proceso de pago con PayPal."""
    agreement = ConsentAgreement.objects.get(id=agreement_id)
    
    paypalrestsdk.configure({
        "mode": "sandbox",  # Cambia a "live" en producción
        "client_id": PAYPAL_CLIENT_ID,
        "client_secret": PAYPAL_SECRET,
    })

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": PAYPAL_RETURN_URL,
            "cancel_url": PAYPAL_CANCEL_URL,
        },
        "transactions": [{
            "amount": {
                "total": str(agreement.amount),
                "currency": "USD",
            },
            "description": f"Pago por acuerdo SEXSI #{agreement.id}",
        }]
    })

    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return redirect(link.href)  # Redirige al usuario a PayPal

    return redirect("sexsi:payment_failed")

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
    """Vista para crear un nuevo acuerdo de consentimiento."""
    if request.method == 'POST':
        form = ConsentAgreementForm(request.POST, request.FILES)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.creator = request.user
            agreement.status = 'draft'
            
            # Verificación de edad del creador
            if agreement.creator_date_of_birth:
                agreement.creator_age_verified = True
                agreement.creator_age_verification_date = now()
            
            agreement.save()
            form.save_m2m()
            
            # Verificación de edad del invitado (si se especifica)
            if agreement.invitee and agreement.invitee_date_of_birth:
                agreement.invitee_age_verified = True
                agreement.invitee_age_verification_date = now()
                agreement.save()
            
            # Agregar preferencias seleccionadas
            if 'consensual_activities' in request.POST:
                agreement.preferences.set(request.POST.getlist('consensual_activities'))
            
            messages.success(request, 'El acuerdo ha sido creado exitosamente.')
            return redirect('sexsi:agreement_detail', agreement_id=agreement.id)
    else:
        form = ConsentAgreementForm()
    
    return render(request, 'consent_form.html', {'form': form})

@login_required
def agreement_detail(request, agreement_id):
    """Muestra los detalles de un acuerdo."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    return render(request, 'agreement_detail.html', {'agreement': agreement})

@login_required
def agreement_edit(request, agreement_id):
    """Edita un acuerdo existente."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    if request.method == 'POST':
        form = ConsentAgreementForm(request.POST, request.FILES, instance=agreement)
        if form.is_valid():
            form.save()
            messages.success(request, 'El acuerdo ha sido actualizado exitosamente.')
            return redirect('sexsi:agreement_detail', agreement_id=agreement.id)
    else:
        form = ConsentAgreementForm(instance=agreement)
    return render(request, 'consent_form.html', {'form': form})

@login_required
def sign_agreement(request, agreement_id, signer, token):
    """Firma un acuerdo."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    if validate_token(agreement, token):
        if signer == 'creator':
            agreement.is_signed_by_creator = True
        else:
            agreement.is_signed_by_invitee = True
        agreement.save()
        messages.success(request, 'El acuerdo ha sido firmado exitosamente.')
        return redirect('sexsi:agreement_detail', agreement_id=agreement.id)
    return redirect('sexsi:agreement_detail', agreement_id=agreement_id)

@login_required
def cancel_agreement(request, agreement_id):
    """Cancela un acuerdo."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    agreement.status = 'cancelled'
    agreement.save()
    messages.success(request, 'El acuerdo ha sido cancelado.')
    return redirect('sexsi:agreement_list')

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
            agreement.invitee_signature = selfie_path
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

def validate_internal_token(signature, token):
    """Valida que el token de firma interna sea válido y no haya expirado."""
    return str(signature.token) == token and signature.is_token_valid()

@login_required
def create_internal_signature(request):
    """Crea una nueva firma interna."""
    if request.method == 'POST':
        document_name = request.POST.get('document_name')
        document_description = request.POST.get('document_description')
        document_file = request.FILES.get('document_file')
        reviewer_id = request.POST.get('reviewer_id')
        business_unit_id = request.POST.get('business_unit_id')
        
        if not all([document_name, document_description, document_file, business_unit_id]):
            messages.error(request, "⚠️ Todos los campos son requeridos.")
            return redirect('sexsi:internal_signature_list')

        try:
            reviewer = Person.objects.get(id=reviewer_id)
            business_unit = BusinessUnit.objects.get(id=business_unit_id)
            
            signature = InternalDocumentSignature.objects.create(
                creator=request.user,
                reviewer=reviewer,
                document_name=document_name,
                document_description=document_description,
                document_file=document_file,
                business_unit=business_unit
            )
            
            messages.success(request, "✅ Firma interna creada exitosamente.")
            return redirect('sexsi:internal_signature_detail', pk=signature.pk)
            
        except (Person.DoesNotExist, BusinessUnit.DoesNotExist):
            messages.error(request, "⚠️ Usuario o Unidad de Negocio no encontrado.")
            return redirect('sexsi:internal_signature_list')
    
    business_units = BusinessUnit.objects.all()
    return render(request, 'internal_signature_form.html', {
        'business_units': business_units,
        'action': 'create'
    })

@login_required
def internal_signature_list(request):
    """Lista todas las firmas internas del usuario."""
    signatures = InternalDocumentSignature.objects.filter(creator=request.user)
    return render(request, 'internal_signature_list.html', {
        'signatures': signatures
    })

@login_required
def internal_signature_detail(request, pk):
    """Muestra los detalles de una firma interna."""
    signature = get_object_or_404(InternalDocumentSignature, pk=pk)
    
    if signature.creator != request.user and signature.reviewer != request.user:
        messages.error(request, "⚠️ No tienes permiso para ver esta firma.")
        return redirect('sexsi:internal_signature_list')
    
    return render(request, 'internal_signature_detail.html', {
        'signature': signature
    })

@login_required
def internal_signature_sign(request, pk, signer, token):
    """Maneja el proceso de firma de un documento interno."""
    signature = get_object_or_404(InternalDocumentSignature, pk=pk)
    
    if not validate_internal_token(signature, token):
        messages.error(request, "⚠️ Token inválido o expirado.")
        return redirect('sexsi:internal_signature_detail', pk=pk)
    
    if request.method == 'POST':
        signature_file = request.FILES.get('signature')
        
        if not signature_file:
            messages.error(request, "⚠️ Debes subir una firma.")
            return redirect('sexsi:internal_signature_detail', pk=pk)
        
        if signer == 'creator':
            signature.creator_signature = signature_file
            signature.mark_as_signed_by_creator()
        elif signer == 'reviewer':
            signature.reviewer_signature = signature_file
            signature.mark_as_signed_by_reviewer()
        
        messages.success(request, "✅ Firma registrada exitosamente.")
        return redirect('sexsi:internal_signature_detail', pk=pk)
    
    return render(request, 'internal_signature_sign.html', {
        'signature': signature,
        'signer': signer,
        'token': token
    })

@login_required
def internal_signature_cancel(request, pk):
    """Cancela una firma interna."""
    signature = get_object_or_404(InternalDocumentSignature, pk=pk)
    
    if signature.creator != request.user:
        messages.error(request, "⚠️ No tienes permiso para cancelar esta firma.")
        return redirect('sexsi:internal_signature_detail', pk=pk)
    
    signature.cancel()
    messages.success(request, "✅ Firma cancelada exitosamente.")
    return redirect('sexsi:internal_signature_list')

# Funciones auxiliares

def validate_token(agreement, token):
    """Valida que el token de firma sea válido y no haya expirado."""
    return agreement.token == token and agreement.token_expiry > now()

async def process_incoming_message(message, user_id):
    # Implementa la lógica de procesamiento aquí
    pass
