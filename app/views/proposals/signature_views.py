# /home/pablo/app/views/proposals/signature_views.py
#
# Vista para manejar la firma de propuestas y notificación al equipo de finanzas.

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
from django.db import transaction
from django.conf import settings
from django.core.cache import caches
from django_ratelimit.decorators import ratelimit
from django_prometheus import exports

from app.ats.utils.email_utils import send_purchase_order_notification
from app.models import Proposal

import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class ProposalSignatureView(View):
    """
    Vista para manejar la firma de propuestas y notificación al equipo de finanzas.
    """
    
    @method_decorator(ratelimit(key='user', rate='100/m'))
    def post(self, request, proposal_id):
        """
        Maneja la firma de una propuesta y notifica al equipo de finanzas.
        """
        try:
            with transaction.atomic():
                # Obtener la propuesta
                proposal = get_object_or_404(Proposal, id=proposal_id)
                
                # Actualizar estado de la propuesta
                proposal.status = 'SIGNED'
                proposal.sign_date = timezone.now()
                proposal.save()
                
                # Notificar al equipo de finanzas
                if send_purchase_order_notification(proposal):
                    logger.info(f"Notificación de orden de compra enviada para propuesta {proposal_id}")
                else:
                    logger.error(f"Error al enviar notificación de orden de compra para propuesta {proposal_id}")
                    
            return JsonResponse({
                'success': True,
                'message': 'Propuesta firmada exitosamente'
            })
            
        except Exception as e:
            logger.error(f"Error al firmar propuesta {proposal_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def get(self, request, proposal_id):
        """
        Obtiene el estado de la firma de una propuesta.
        """
        try:
            proposal = get_object_or_404(Proposal, id=proposal_id)
            return JsonResponse({
                'success': True,
                'status': proposal.status,
                'signed_date': proposal.sign_date.isoformat() if proposal.sign_date else None
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
