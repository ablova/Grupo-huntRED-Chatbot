# /home/pablo/app/utils/email_utils.py
#
# Utilidades para el envío de correos electrónicos.

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

def send_purchase_order_notification(proposal):
    """
    Envía una notificación por email al equipo de finanzas cuando se firma una propuesta
    """
    subject = f"Nueva Orden de Compra - {proposal.client_name}"
    
    # Renderizar la plantilla del email
    email_body = render_to_string('emails/purchase_order_notification.html', {
        'proposal': proposal,
        'fiscal_data': proposal.fiscal_data if hasattr(proposal, 'fiscal_data') else None
    })
    
    # Configurar el email
    email = EmailMessage(
        subject=subject,
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.FINANCE_EMAIL],  # Debe estar definido en settings.py
        reply_to=[proposal.client_email]
    )
    
    # Establecer el contenido como HTML
    email.content_subtype = 'html'
    
    # Adjuntar la propuesta firmada si existe
    if proposal.signed_document:
        email.attach_file(proposal.signed_document.path)
    
    # Enviar el email
    try:
        email.send()
        return True
    except Exception as e:
        # Loggear el error
        print(f"Error al enviar email de notificación: {str(e)}")
        return False
