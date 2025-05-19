# /home/pablo/app/com/pricing/triggers.py
"""
Módulo de triggers para la generación automática de propuestas en Grupo huntRED®.

Este módulo implementa los disparadores que generan automáticamente propuestas
basadas en diferentes eventos del sistema, como la creación de oportunidades o
solicitudes de análisis de talento 360°.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from django.db.models.signals import post_save, post_init
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from app.models import Opportunity, BusinessUnit, Contact, TalentAnalysisRequest
from app.com.pricing.proposal_renderer import generate_proposal
from app.com.pricing.talent_360_pricing import Talent360Pricing
from app.com.pricing.progressive_billing import ProgressiveBilling
from app.com.pricing.pricing_interface import PricingManager

logger = logging.getLogger(__name__)

# Directorio para guardar propuestas generadas
PROPOSALS_DIR = os.path.join(settings.MEDIA_ROOT, 'proposals')
os.makedirs(PROPOSALS_DIR, exist_ok=True)


@receiver(post_save, sender=TalentAnalysisRequest)
def generate_talent_360_proposal(sender, instance, created, **kwargs):
    """
    Genera automáticamente una propuesta cuando se crea una solicitud de análisis de talento.
    
    Args:
        sender: Modelo que envía la señal
        instance: Instancia del modelo guardada
        created: Indica si es una nueva instancia
    """
    # Solo generar propuestas para nuevas solicitudes
    if not created:
        return
    
    logger.info(f"Generando propuesta automática para solicitud de análisis de talento ID: {instance.id}")
    
    try:
        # Obtener datos necesarios
        opportunity = instance.opportunity
        business_unit = opportunity.business_unit or BusinessUnit.objects.get(name='huntRED')
        company_name = opportunity.company_name
        contact = opportunity.contact
        user_count = instance.user_count or 10  # Default a 10 si no está especificado
        
        # Calcular pricing con el sistema avanzado
        pricing_data = Talent360Pricing.calculate_total(user_count=user_count)
        
        # Generar plan de pagos
        payment_schedule = ProgressiveBilling.generate_payment_schedule(
            business_unit_name=business_unit.name,
            start_date=timezone.now().date(),
            contract_amount=pricing_data['total'],
            service_type='talent_analysis'
        )
        
        # Preparar datos para la propuesta
        proposal_data = {
            'company': {
                'name': company_name,
                'contact': {
                    'name': contact.name if contact else None,
                    'email': contact.email if contact else None,
                    'phone': contact.phone if contact else None
                }
            },
            'service': {
                'name': 'Análisis de Talento 360°',
                'type': 'talent_analysis',
                'description': 'Evaluación integral de competencias y habilidades para optimizar el talento organizacional',
                # Resto de datos del servicio...
            },
            'pricing': pricing_data,
            'payment_schedule': payment_schedule,
            'business_unit': {
                'id': business_unit.id,
                'name': business_unit.name
            },
            'service_type': 'talent_analysis',
            'opportunity': {
                'id': opportunity.id,
                'name': opportunity.name,
                'description': opportunity.description
            }
        }
        
        # Generar nombre de archivo para la propuesta
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"Propuesta_Talent360_{company_name.replace(' ', '_')}_{timestamp}"
        
        # Generar la propuesta en HTML y PDF
        html_path = os.path.join(PROPOSALS_DIR, f"{file_name}.html")
        pdf_path = os.path.join(PROPOSALS_DIR, f"{file_name}.pdf")
        
        # Generar versión HTML
        generate_proposal(
            proposal_data=proposal_data,
            output_format='html',
            output_file=html_path
        )
        
        # Generar versión PDF
        pdf_file = generate_proposal(
            proposal_data=proposal_data,
            output_format='pdf',
            output_file=pdf_path
        )
        
        # Actualizar la solicitud con las rutas a las propuestas
        instance.proposal_html_path = html_path
        instance.proposal_pdf_path = pdf_path
        instance.proposal_generated_at = timezone.now()
        instance.save(update_fields=['proposal_html_path', 'proposal_pdf_path', 'proposal_generated_at'])
        
        # Enviar notificación si está configurado
        if instance.send_proposal_email and contact and contact.email:
            send_proposal_notification(instance, pdf_file)
        
        logger.info(f"Propuesta generada exitosamente para solicitud de análisis de talento ID: {instance.id}")
        
    except Exception as e:
        logger.error(f"Error al generar propuesta automática: {str(e)}", exc_info=True)


@receiver(post_save, sender=Opportunity)
def check_opportunity_for_proposal(sender, instance, created, **kwargs):
    """
    Verifica si una oportunidad requiere generar automáticamente una propuesta.
    
    Args:
        sender: Modelo que envía la señal
        instance: Instancia del modelo guardada
        created: Indica si es una nueva instancia
    """
    # Verificar si la oportunidad requiere una propuesta según sus atributos
    if not hasattr(instance, 'service_type'):
        return
    
    # Si no es una oportunidad nueva pero se actualizó y requiere propuesta
    if not created and instance.requires_proposal and not instance.has_proposal:
        logger.info(f"Generando propuesta para oportunidad actualizada ID: {instance.id}")
        generate_proposal_for_opportunity(instance)
    
    # Si es una oportunidad nueva y es de ciertos tipos específicos
    elif created and instance.service_type in ['talent_analysis', 'executive_search']:
        logger.info(f"Generando propuesta para nueva oportunidad ID: {instance.id}")
        generate_proposal_for_opportunity(instance)


def generate_proposal_for_opportunity(opportunity):
    """
    Genera una propuesta para una oportunidad específica.
    
    Args:
        opportunity: Instancia de Opportunity
    """
    try:
        # Generar propuesta según el tipo de servicio
        if opportunity.service_type == 'talent_analysis':
            # Crear una solicitud de análisis de talento si no existe
            if not hasattr(opportunity, 'talent_analysis_request'):
                from app.models import TalentAnalysisRequest
                TalentAnalysisRequest.objects.create(
                    opportunity=opportunity,
                    user_count=opportunity.headcount or 10,
                    send_proposal_email=True
                )
                # La propuesta se generará automáticamente por el trigger de TalentAnalysisRequest
            
        elif opportunity.service_type == 'recruitment':
            # Usar la interfaz PricingManager para generar una propuesta de reclutamiento
            proposal_data = PricingManager.generate_proposal(
                opportunity_id=opportunity.id,
                payment_schedule=True
            )
            
            # Generar nombre de archivo para la propuesta
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            company_name = opportunity.company_name.replace(' ', '_')
            file_name = f"Propuesta_Recruitment_{company_name}_{timestamp}"
            
            # Generar la propuesta en HTML y PDF
            html_path = os.path.join(PROPOSALS_DIR, f"{file_name}.html")
            pdf_path = os.path.join(PROPOSALS_DIR, f"{file_name}.pdf")
            
            # Generar versiones HTML y PDF
            generate_proposal(
                proposal_data=proposal_data,
                output_format='html',
                output_file=html_path
            )
            
            pdf_file = generate_proposal(
                proposal_data=proposal_data,
                output_format='pdf',
                output_file=pdf_path
            )
            
            # Actualizar la oportunidad
            opportunity.proposal_html_path = html_path
            opportunity.proposal_pdf_path = pdf_path
            opportunity.has_proposal = True
            opportunity.save(update_fields=['proposal_html_path', 'proposal_pdf_path', 'has_proposal'])
            
            # Enviar notificación si hay contacto
            if opportunity.contact and opportunity.contact.email:
                send_proposal_notification(opportunity, pdf_file)
    
    except Exception as e:
        logger.error(f"Error al generar propuesta para oportunidad ID {opportunity.id}: {str(e)}", exc_info=True)


def send_proposal_notification(instance, pdf_file=None):
    """
    Envía una notificación por email con la propuesta generada.
    
    Args:
        instance: Instancia que generó la propuesta (Opportunity o TalentAnalysisRequest)
        pdf_file: Ruta al archivo PDF de la propuesta (opcional)
    """
    try:
        # Obtener datos relevantes
        if hasattr(instance, 'opportunity'):
            # Es una solicitud de análisis de talento
            opportunity = instance.opportunity
        else:
            # Es una oportunidad directamente
            opportunity = instance
        
        company_name = opportunity.company_name
        contact = opportunity.contact
        business_unit = opportunity.business_unit
        
        # Verificar si tenemos a quién enviar el email
        if not contact or not contact.email:
            logger.warning(f"No se puede enviar notificación: contacto o email no disponible")
            return
        
        # Preparar contexto para la plantilla
        context = {
            'company_name': company_name,
            'contact_name': contact.name,
            'service_name': 'Análisis de Talento 360°' if hasattr(instance, 'user_count') else 'Servicios de Reclutamiento',
            'business_unit': business_unit.name,
            'generated_date': timezone.now().strftime('%d/%m/%Y'),
        }
        
        # Renderizar plantilla HTML para el email
        html_content = render_to_string('emails/proposal_notification.html', context)
        text_content = render_to_string('emails/proposal_notification.txt', context)
        
        # Crear el email
        subject = f"Propuesta de {business_unit.name} para {company_name}"
        from_email = f"{business_unit.name} <propuestas@grupohuntred.com>"
        to_email = contact.email
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        
        # Adjuntar PDF si está disponible
        if pdf_file and os.path.exists(pdf_file):
            with open(pdf_file, 'rb') as f:
                msg.attach(os.path.basename(pdf_file), f.read(), 'application/pdf')
        
        # Enviar email
        msg.send()
        logger.info(f"Notificación de propuesta enviada a {to_email}")
        
    except Exception as e:
        logger.error(f"Error al enviar notificación de propuesta: {str(e)}", exc_info=True)


# Conectar las señales a las funciones receptoras
def connect_signals():
    """
    Conecta todas las señales a sus receptores correspondientes.
    Esta función debe ser llamada durante la inicialización de la aplicación.
    """
    # Las conexiones ya se realizan automáticamente con los decoradores @receiver
    # pero esta función puede usarse para verificar o manipular las conexiones
    logger.info("Señales de generación automática de propuestas conectadas")


# Desconectar las señales (útil para testing)
def disconnect_signals():
    """
    Desconecta todas las señales.
    Útil para testing o para desactivar temporalmente la funcionalidad.
    """
    post_save.disconnect(generate_talent_360_proposal, sender=TalentAnalysisRequest)
    post_save.disconnect(check_opportunity_for_proposal, sender=Opportunity)
    logger.info("Señales de generación automática de propuestas desconectadas")
