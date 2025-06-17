"""
Vistas para el sistema de propuestas y contratos.

Responsabilidades:
- Generación de propuestas
- Gestión de contratos
- Integración con ATS y chatbot
- Reportes y análisis
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.core.files.storage import default_storage
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.core.cache import caches
from django_ratelimit.decorators import ratelimit
from django_prometheus import exports

from app.ats.decorators import (
    bu_complete_required, bu_division_required,
    permission_required, verified_user_required
)
from app.models import (
    Proposal, Opportunity, Vacancy, Person,
    Application, Interview, Contract
)
from app.ats.pricing.utils import calculate_pricing
from app.ats.ats.contracts.contract_generator import ContractGenerator
from app.ats.proposals.forms import ProposalFilterForm
from app.ats.utils import get_business_unit, get_user_permissions
from app.decorators import *

import logging
import pdfkit
import os
import json
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class ProposalViews(View):
    """
    Vistas principales para el sistema de propuestas.
    """
    
    @method_decorator(login_required)
    @method_decorator(bu_complete_required)
    def proposal_list(self, request):
        """
        Lista de propuestas con filtros y estadísticas.
        """
        business_unit = get_business_unit(request.user)
        
        # Crear formulario de filtros
        filter_form = ProposalFilterForm(request.GET)
        
        # Obtener queryset base con optimizaciones
        proposals = Proposal.objects.filter(
            company__business_unit=business_unit
        ).select_related(
            'company',
            'created_by',
            'approved_by'
        ).prefetch_related(
            'vacancies',
            'contracts'
        ).order_by('-created_at')
        
        # Aplicar filtros
        if filter_form.is_valid():
            proposals = filter_form.filter_queryset(proposals)
        
        # Estadísticas
        stats = {
            'total': proposals.count(),
            'approved': proposals.filter(status='APPROVED').count(),
            'pending': proposals.filter(status='PENDING').count(),
            'rejected': proposals.filter(status='REJECTED').count()
        }
        
        # Paginación
        paginator = Paginator(proposals, 10)
        page_number = request.GET.get('page', 1)
        proposals = paginator.get_page(page_number)
        
        context = {
            'proposals': proposals,
            'filter_form': filter_form,
            'stats': stats,
            'business_unit': business_unit
        }
        return render(request, 'proposals/proposal_list.html', context)
    
    @method_decorator(login_required)
    @method_decorator(bu_complete_required)
    @method_decorator(ratelimit(key='user', rate='100/m'))
    def generate_proposal(self, request, opportunity_id):
        """
        Genera una propuesta para una oportunidad.
        """
        if request.method != 'POST':
            return JsonResponse({'error': 'Método no permitido'}, status=405)
            
        opportunity = get_object_or_404(Opportunity, id=opportunity_id)
        
        # Verificar permisos
        if not request.user.has_perm('can_generate_proposal'):
            return JsonResponse({'error': 'No tienes permisos para generar propuestas'}, status=403)
            
        try:
            with transaction.atomic():
                # Calcular pricing
                pricing = calculate_pricing(opportunity_id)
                
                # Crear propuesta
                proposal = Proposal.objects.create(
                    company=opportunity.company,
                    pricing_total=pricing['total'],
                    pricing_details=pricing,
                    created_by=request.user,
                    status='PENDING'
                )
                
                # Asociar vacantes
                for vacancy in opportunity.vacancies.all():
                    proposal.vacancies.add(vacancy)
                
                # Generar PDF
                pdf_content = self._generate_proposal_pdf(proposal)
                
                # Guardar PDF
                pdf_path = self._save_proposal_pdf(proposal, pdf_content)
                
                # Notificar al chatbot
                self._notify_chatbot(proposal)
                
                # Crear registro de auditoría
                self._create_audit_log(request.user, proposal, 'CREATED')
                
                return JsonResponse({
                    'proposal_id': proposal.id,
                    'pdf_url': pdf_path,
                    'pricing': pricing
                })
                
        except Exception as e:
            logger.error(f"Error generando propuesta: {e}", exc_info=True)
            return JsonResponse({'error': 'Error generando propuesta'}, status=500)
    
    async def _notify_chatbot(self, proposal):
        """
        Notifica al chatbot sobre la nueva propuesta.
        """
        from app.ats.integrations.services import MessageService
        
        message_service = MessageService()
        
        # Enviar mensaje a los responsables
        for person in proposal.company.responsible_persons.all():
            await message_service.send_message(
                'whatsapp',
                person.phone_number,
                f'Nueva propuesta generada para {proposal.company.name}'
            )
    
    def _create_audit_log(self, user, proposal, action):
        """
        Crea un registro de auditoría.
        """
        from app.models import AuditLog
        
        AuditLog.objects.create(
            user=user,
            proposal=proposal,
            action=action,
            timestamp=timezone.now()
        )
        
    def generate_proposal(self, request, opportunity_id):
        """
        Genera una propuesta para una oportunidad.
        
        Args:
            request: HttpRequest
            opportunity_id: ID de la oportunidad
            
        Returns:
            HttpResponse: PDF de la propuesta
        """
        # Obtener oportunidad
        opportunity = get_object_or_404(Opportunity, id=opportunity_id)
        
        # Calcular pricing
        pricing = calculate_pricing(opportunity_id)
        
        # Crear propuesta
        proposal = Proposal.objects.create(
            company=opportunity.company,
            pricing_total=pricing['total'],
            pricing_details=pricing
        )
        
        # Asociar vacantes
        for vacancy in opportunity.vacancies.all():
            proposal.vacancies.add(vacancy)
            
        # Generar PDF
        pdf_content = self._generate_proposal_pdf(proposal)
        
        # Guardar PDF
        pdf_path = self._save_proposal_pdf(proposal, pdf_content)
        
        return JsonResponse({
            'proposal_id': proposal.id,
            'pdf_url': pdf_path,
            'pricing': pricing
        })
        
    def _generate_proposal_pdf(self, proposal):
        """
        Genera el PDF de la propuesta.
        
        Args:
            proposal: Instancia de Proposal
            
        Returns:
            str: Contenido del PDF
        """
        # Inicializar el proveedor de datos de evaluaciones
        from app.ats.chatbot.workflow.assessments.assessment_data_provider import AssessmentDataProvider
        assessment_provider = AssessmentDataProvider()
        
        # Renderizar template
        html_content = render_to_string('proposals/proposal_template.html', {
            'proposal': proposal,
            'pricing': proposal.pricing_details,
            'company': proposal.company,
            'available_assessments': assessment_provider.get_available_assessments(),
            'additional_services': assessment_provider.get_additional_services()
        })
        
        # Generar PDF
        pdf_content = pdfkit.from_string(html_content, False)
        
        return pdf_content
        
    def _save_proposal_pdf(self, proposal, pdf_content):
        """
        Guarda el PDF de la propuesta.
        
        Args:
            proposal: Instancia de Proposal
            pdf_content: Contenido del PDF
            
        Returns:
            str: URL del PDF
        """
        # Crear directorio si no existe
        proposals_dir = os.path.join(settings.MEDIA_ROOT, 'proposals')
        os.makedirs(proposals_dir, exist_ok=True)
        
        # Generar nombre del archivo
        filename = f"proposal_{proposal.id}.pdf"
        filepath = os.path.join(proposals_dir, filename)
        
        # Guardar PDF
        with open(filepath, 'wb') as f:
            f.write(pdf_content)
        
        # Generar URL
        return os.path.join(settings.MEDIA_URL, 'proposals', filename)
        
    def convert_to_contract(self, request, proposal_id):
        """
        Convierte una propuesta en contrato.
        
        Args:
            request: HttpRequest
            proposal_id: ID de la propuesta
            
        Returns:
            JsonResponse: Estado de la conversión
        """
        # Obtener propuesta
        proposal = get_object_or_404(Proposal, id=proposal_id)
        
        # Inicializar generador de contratos
        contract_generator = ContractGenerator()
        
        try:
            # Convertir a contrato
            contract = contract_generator.convert_opportunity_to_contract(
                proposal.opportunity.id
            )
            
            # Actualizar estado de la propuesta
            proposal.status = 'CONVERTED'
            proposal.save()
            
            return JsonResponse({
                'status': 'success',
                'contract_id': contract.id
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
