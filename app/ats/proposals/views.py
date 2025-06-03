from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Proposal
from app.ats.ats.client_portal.models import ClientPortalAccess
from app.ats.notifications.services.whatsapp_service import WhatsAppService

def sign_proposal(request, proposal_id):
    if request.method == 'POST':
        proposal = Proposal.objects.get(id=proposal_id)
        
        # Procesar firma
        signature_name = request.POST.get('signature_name')
        signature_position = request.POST.get('signature_position')
        signature_email = request.POST.get('signature_email')
        include_portal = request.POST.get('include_portal') == 'on'
        
        # Actualizar propuesta
        proposal.signature_name = signature_name
        proposal.signature_position = signature_position
        proposal.signature_email = signature_email
        proposal.status = 'signed'
        proposal.save()
        
        # Si se incluye el portal, crear acceso
        if include_portal:
            # Generar credenciales temporales
            temp_password = User.objects.make_random_password()
            
            # Crear usuario
            user = User.objects.create(
                username=signature_email,
                email=signature_email,
                password=make_password(temp_password),
                first_name=signature_name.split()[0],
                last_name=' '.join(signature_name.split()[1:]) if len(signature_name.split()) > 1 else ''
            )
            
            # Crear acceso al portal
            portal_access = ClientPortalAccess.objects.create(
                user=user,
                company=proposal.company,
                is_active=True,
                access_level='premium'
            )
            
            # Enviar credenciales por correo
            context = {
                'name': signature_name,
                'email': signature_email,
                'password': temp_password,
                'portal_url': settings.PORTAL_URL
            }
            
            email_content = render_to_string('emails/portal_credentials.html', context)
            
            send_mail(
                'Bienvenido al Portal huntRED®',
                email_content,
                settings.DEFAULT_FROM_EMAIL,
                [signature_email],
                html_message=email_content
            )
            
            # Enviar notificación por WhatsApp
            whatsapp = WhatsAppService()
            whatsapp.send_portal_access_notification(
                phone=proposal.company.contact_phone,
                name=signature_name,
                email=signature_email
            )
        
        return redirect('proposals:proposal_detail', proposal_id=proposal.id)
    
    return render(request, 'proposals/sign_proposal.html', {'proposal': proposal}) 