"""
Vistas para el procesamiento de firmas digitales de propuestas
Integrado con el sistema de notificaciones existente de huntRED®
"""

import json
import base64
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.conf import settings
import logging

from app.ats.utils.signature.digital_sign import DigitalSignatureProcessor
from app.ats.utils.signature.biometric_auth import BiometricValidator
from app.ats.utils.notification_service import NotificationService, NotificationChannel, NotificationPriority
from app.models import Proposal, Client, Company

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def process_proposal_signature(request):
    """
    Procesa la firma digital de una propuesta usando el sistema de notificaciones existente
    """
    try:
        # Parsear datos JSON
        data = json.loads(request.body)
        
        # Extraer datos de la propuesta
        proposal_data = {
            'client_name': data.get('clientName', 'Cliente'),
            'proposal_id': data.get('proposalId'),
            'total_amount': data.get('totalAmount', 0),
            'services': data.get('services', []),
            'contacts': data.get('contacts', []),
            'client_signature': data.get('clientSignature'),
            'consultant_signature': data.get('consultantSignature'),
            'timestamp': data.get('timestamp'),
            'ip_address': data.get('ipAddress'),
            'user_agent': data.get('userAgent')
        }
        
        # Validar firmas
        if not proposal_data['client_signature'] or not proposal_data['consultant_signature']:
            return JsonResponse({
                'success': False,
                'error': 'Ambas firmas son requeridas'
            }, status=400)
        
        # Procesar firmas digitales
        signature_processor = DigitalSignatureProcessor()
        biometric_validator = BiometricValidator()
        
        # Validar firma del cliente
        client_signature_valid = signature_processor.validate_signature(
            proposal_data['client_signature'],
            proposal_data['ip_address'],
            proposal_data['user_agent']
        )
        
        # Validar firma del consultor
        consultant_signature_valid = signature_processor.validate_signature(
            proposal_data['consultant_signature'],
            proposal_data['ip_address'],
            proposal_data['user_agent']
        )
        
        if not client_signature_valid or not consultant_signature_valid:
            return JsonResponse({
                'success': False,
                'error': 'Una o ambas firmas no son válidas'
            }, status=400)
        
        # Guardar propuesta firmada
        signed_proposal = save_signed_proposal(proposal_data)
        
        # Generar PDF final
        pdf_path = generate_final_pdf(signed_proposal, proposal_data)
        
        # Enviar notificaciones usando el sistema existente
        send_proposal_notifications(signed_proposal, proposal_data, pdf_path)
        
        # Registrar en logs
        logger.info(f"Propuesta {proposal_data['proposal_id']} firmada exitosamente por {proposal_data['client_name']}")
        
        return JsonResponse({
            'success': True,
            'message': 'Propuesta procesada y enviada exitosamente',
            'proposal_id': signed_proposal.id,
            'pdf_url': pdf_path
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error procesando firma de propuesta: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)

def save_signed_proposal(proposal_data):
    """
    Guarda la propuesta firmada en la base de datos
    """
    try:
        # Buscar o crear cliente
        client, created = Client.objects.get_or_create(
            name=proposal_data['client_name'],
            defaults={
                'email': proposal_data['contacts'][0] if proposal_data['contacts'] else '',
                'status': 'active'
            }
        )
        
        # Crear propuesta firmada
        proposal = Proposal.objects.create(
            client=client,
            total_amount=proposal_data['total_amount'],
            services_data=json.dumps(proposal_data['services']),
            client_signature=proposal_data['client_signature'],
            consultant_signature=proposal_data['consultant_signature'],
            signed_at=datetime.fromisoformat(proposal_data['timestamp'].replace('Z', '+00:00')),
            ip_address=proposal_data['ip_address'],
            user_agent=proposal_data['user_agent'],
            status='signed'
        )
        
        return proposal
        
    except Exception as e:
        logger.error(f"Error guardando propuesta firmada: {str(e)}")
        raise

def generate_final_pdf(proposal, proposal_data):
    """
    Genera el PDF final de la propuesta firmada
    """
    try:
        # Aquí usarías tu sistema de generación de PDF
        # Por ahora retornamos una ruta simulada
        pdf_filename = f"propuesta_firmada_{proposal.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = f"/media/proposals/{pdf_filename}"
        
        # TODO: Implementar generación real de PDF con firmas
        # pdf_generator = PDFGenerator()
        # pdf_path = pdf_generator.generate_signed_proposal(proposal, proposal_data)
        
        return pdf_path
        
    except Exception as e:
        logger.error(f"Error generando PDF final: {str(e)}")
        raise

def send_proposal_notifications(proposal, proposal_data, pdf_path):
    """
    Envía notificaciones usando el sistema de notificaciones existente de huntRED®
    """
    try:
        # Contexto común para todas las notificaciones
        common_context = {
            'client_name': proposal_data['client_name'],
            'proposal_id': proposal.id,
            'total_amount': proposal_data['total_amount'],
            'services': proposal_data['services'],
            'signed_date': proposal.signed_at.strftime('%d/%m/%Y %H:%M'),
            'pdf_url': pdf_path,
            'ip_address': proposal_data['ip_address']
        }
        
        # 1. NOTIFICACIÓN PARA EL CLIENTE (Email + WhatsApp)
        client_context = {
            **common_context,
            'notification_type': 'client_signed_proposal'
        }
        
        # Enviar a todos los contactos del cliente
        for contact_email in proposal_data['contacts']:
            # Email principal
            NotificationService.send_notification(
                recipient=contact_email,
                subject=f'✅ Propuesta Firmada - Grupo huntRED® - {proposal_data["client_name"]}',
                message=f'Su propuesta #{proposal.id} ha sido firmada exitosamente. Total: ${proposal_data["total_amount"]:,.2f}',
                channel=NotificationChannel.EMAIL,
                template='emails/proposal_signed_client.html',
                context=client_context,
                priority=NotificationPriority.HIGH,
                bu_name='huntRED',
                metadata={
                    'proposal_id': proposal.id,
                    'client_name': proposal_data['client_name'],
                    'notification_type': 'proposal_signed_client'
                }
            )
            
            # WhatsApp de confirmación
            NotificationService.send_notification(
                recipient=contact_email,
                subject='Propuesta Firmada - huntRED®',
                message=f'✅ Su propuesta #{proposal.id} ha sido firmada exitosamente. Nuestro equipo se pondrá en contacto en las próximas 24 horas.',
                channel=NotificationChannel.WHATSAPP,
                context=client_context,
                priority=NotificationPriority.HIGH,
                bu_name='huntRED',
                metadata={
                    'proposal_id': proposal.id,
                    'notification_type': 'proposal_signed_client_whatsapp'
                }
            )
        
        # 2. NOTIFICACIÓN PARA EL EQUIPO huntRED® (Email + Interna)
        team_context = {
            **common_context,
            'contacts': proposal_data['contacts'],
            'notification_type': 'team_new_signed_proposal'
        }
        
        # Email al equipo de huntRED®
        team_emails = [
            'pablo@huntred.com',  # Pablo Lelo de Larrea
            'admin@huntred.com',  # Admin general
            'consultores@huntred.com',  # Equipo de consultores
        ]
        
        for team_email in team_emails:
            NotificationService.send_notification(
                recipient=team_email,
                subject=f'🎉 Nueva Propuesta Firmada - {proposal_data["client_name"]}',
                message=f'Nueva propuesta #{proposal.id} firmada por {proposal_data["client_name"]} por ${proposal_data["total_amount"]:,.2f}',
                channel=NotificationChannel.EMAIL,
                template='emails/proposal_signed_team.html',
                context=team_context,
                priority=NotificationPriority.URGENT,
                bu_name='huntRED',
                metadata={
                    'proposal_id': proposal.id,
                    'client_name': proposal_data['client_name'],
                    'notification_type': 'proposal_signed_team'
                }
            )
        
        # 3. NOTIFICACIÓN INTERNA EN EL SISTEMA
        NotificationService.send_notification(
            recipient='system',  # Notificación interna
            subject=f'Nueva Propuesta Firmada - {proposal_data["client_name"]}',
            message=f'Propuesta #{proposal.id} firmada exitosamente. Cliente: {proposal_data["client_name"]}, Valor: ${proposal_data["total_amount"]:,.2f}',
            channel=NotificationChannel.INTERNAL,
            context=team_context,
            priority=NotificationPriority.HIGH,
            bu_name='huntRED',
            metadata={
                'proposal_id': proposal.id,
                'client_name': proposal_data['client_name'],
                'notification_type': 'proposal_signed_internal'
            }
        )
        
        # 4. NOTIFICACIÓN PUSH PARA CONSULTORES ACTIVOS (si aplica)
        # Esto se puede activar si tienes app móvil para consultores
        """
        NotificationService.send_notification(
            recipient='consultores_activos',
            subject='Nueva Propuesta Firmada',
            message=f'Cliente: {proposal_data["client_name"]} - ${proposal_data["total_amount"]:,.2f}',
            channel=NotificationChannel.PUSH,
            context=team_context,
            priority=NotificationPriority.HIGH,
            bu_name='huntRED'
        )
        """
        
        logger.info(f"Notificaciones enviadas para propuesta {proposal.id} usando sistema existente")
        
    except Exception as e:
        logger.error(f"Error enviando notificaciones de propuesta firmada: {str(e)}")
        raise

@login_required
def get_proposal_signature_status(request, proposal_id):
    """
    Obtiene el estado de firma de una propuesta
    """
    try:
        proposal = Proposal.objects.get(id=proposal_id)
        
        return JsonResponse({
            'success': True,
            'proposal_id': proposal.id,
            'status': proposal.status,
            'signed_at': proposal.signed_at.isoformat() if proposal.signed_at else None,
            'client_name': proposal.client.name,
            'total_amount': proposal.total_amount
        })
        
    except Proposal.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Propuesta no encontrada'
        }, status=404)
    except Exception as e:
        logger.error(f"Error obteniendo estado de propuesta: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500) 