"""
Tareas para el envío de notificaciones de evaluaciones culturales.

Este módulo contiene las tareas asíncronas para el envío de invitaciones
y recordatorios relacionados con el Sistema de Análisis Cultural.
Optimizado siguiendo reglas globales.
"""

import logging
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils import timezone
from celery import shared_task
from app.models import CulturalAssessment, OrganizationalCulture
from app.utils.http import send_email
from app.utils.common import generate_qr_code

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_cultural_invitation_task(self, assessment_id, is_reminder=False):
    """
    Envía una invitación o recordatorio para realizar una evaluación cultural.
    
    Args:
        assessment_id (int): ID de la evaluación cultural
        is_reminder (bool): Si es un recordatorio o invitación inicial
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Recuperar la evaluación cultural
        assessment = CulturalAssessment.objects.select_related(
            'person', 'organization', 'organizational_culture', 'business_unit'
        ).get(id=assessment_id)
        
        # Verificar si podemos enviar la invitación
        if assessment.status not in ['invited', 'pending'] or not assessment.invitation_token:
            logger.warning(
                f"No se puede enviar invitación para evaluación {assessment_id}: "
                f"Estado '{assessment.status}' o token no válido"
            )
            return False
            
        # Obtener datos necesarios
        person = assessment.person
        organization = assessment.organization
        
        # Generar URL de acceso
        base_url = settings.BASE_URL or 'https://app.grupohr.io'
        access_url = f"{base_url}/cultural-assessment/{assessment.invitation_token}/"
        
        # Generar código QR
        qr_code_img = generate_qr_code(access_url)
        
        # Preparar datos para la plantilla
        template_data = {
            'person_name': f"{person.first_name} {person.last_name}",
            'organization_name': organization.name,
            'business_unit_name': assessment.business_unit.name,
            'access_url': access_url,
            'qr_code': qr_code_img,
            'expiration_date': assessment.expiration_date,
            'is_reminder': is_reminder,
            'logo_url': f"{base_url}/static/img/logo-grupo-huntred.png"
        }
        
        # Definir asunto y plantilla según si es recordatorio o invitación inicial
        if is_reminder:
            subject = f"Recordatorio: Evaluación de cultura organizacional para {organization.name}"
            template_name = 'emails/cultural_assessment_reminder.html'
        else:
            subject = f"Invitación: Evaluación de cultura organizacional para {organization.name}"
            template_name = 'emails/cultural_assessment_invitation.html'
            
        # Renderizar el cuerpo del correo
        email_body = render_to_string(template_name, template_data)
        
        # Enviar el correo
        sent = send_email(
            recipient=person.email,
            subject=subject,
            body=email_body,
            is_html=True,
            attachment_data=None
        )
        
        # Actualizar el estado si se envió correctamente
        if sent:
            if not is_reminder and assessment.status == 'invited':
                assessment.status = 'pending'
                assessment.invited_at = timezone.now()
                assessment.save(update_fields=['status', 'invited_at'])
            
            assessment.last_interaction = timezone.now()
            assessment.save(update_fields=['last_interaction'])
            
            logger.info(
                f"{'Recordatorio' if is_reminder else 'Invitación'} enviada a {person.email} "
                f"para evaluación cultural de {organization.name}"
            )
            return True
        else:
            logger.error(
                f"Error al enviar {'recordatorio' if is_reminder else 'invitación'} "
                f"a {person.email} para evaluación cultural"
            )
            return False
            
    except CulturalAssessment.DoesNotExist:
        logger.error(f"No se encontró la evaluación cultural con ID {assessment_id}")
        return False
    except Exception as e:
        logger.exception(f"Error enviando invitación cultural: {str(e)}")
        # Reintento con backoff exponencial
        self.retry(exc=e)
        return False


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_report_notification_task(self, report_id):
    """
    Envía una notificación de disponibilidad de reporte cultural.
    
    Args:
        report_id (int): ID del reporte cultural
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        from app.models import CulturalReport
        
        # Recuperar el reporte
        report = CulturalReport.objects.select_related(
            'organization', 'business_unit'
        ).get(id=report_id)
        
        # Verificar si podemos enviar la notificación
        if not report.is_public or not report.access_token or report.status != 'completed':
            logger.warning(
                f"No se puede enviar notificación para reporte {report_id}: "
                f"No es público, no tiene token o no está completo"
            )
            return False
            
        # Obtener datos necesarios
        organization = report.organization
        
        # Buscar contacto principal de la organización
        from app.models import Contact
        contacts = Contact.objects.filter(
            organization=organization,
            is_primary=True,
            active=True
        ).order_by('-created_at')
        
        if not contacts.exists():
            logger.warning(f"No se encontró contacto principal para {organization.name}")
            # Intentar con cualquier contacto
            contacts = Contact.objects.filter(
                organization=organization,
                active=True
            ).order_by('-created_at')
            
            if not contacts.exists():
                logger.error(f"No se encontró ningún contacto para {organization.name}")
                return False
        
        contact = contacts.first()
        
        # Generar URL de acceso
        base_url = settings.BASE_URL or 'https://app.grupohr.io'
        report_url = f"{base_url}/reports/cultural/{report.access_token}/"
        
        # Preparar datos para la plantilla
        template_data = {
            'contact_name': contact.name,
            'organization_name': organization.name,
            'report_title': report.title,
            'report_type': dict(CulturalReport.report_type.field.choices).get(report.report_type, ""),
            'report_date': report.report_date,
            'report_url': report_url,
            'logo_url': f"{base_url}/static/img/logo-grupo-huntred.png"
        }
        
        # Renderizar el cuerpo del correo
        email_body = render_to_string('emails/cultural_report_notification.html', template_data)
        
        # Enviar el correo
        subject = f"Reporte de Cultura Organizacional disponible para {organization.name}"
        sent = send_email(
            recipient=contact.email,
            subject=subject,
            body=email_body,
            is_html=True,
            attachment_data=None
        )
        
        if sent:
            logger.info(f"Notificación de reporte enviada a {contact.email} para {organization.name}")
            
            # Marcar que la notificación se envió
            report.notification_sent = True
            report.notification_date = timezone.now()
            report.save(update_fields=['notification_sent', 'notification_date'])
            
            return True
        else:
            logger.error(f"Error al enviar notificación de reporte a {contact.email}")
            return False
            
    except Exception as e:
        logger.exception(f"Error enviando notificación de reporte: {str(e)}")
        # Reintento con backoff exponencial
        self.retry(exc=e)
        return False
