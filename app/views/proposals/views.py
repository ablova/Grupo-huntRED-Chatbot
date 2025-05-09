from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.core.files.storage import default_storage
from django.conf import settings
import pdfkit
import os
from app.models import Proposal, Opportunity, Vacancy, Person
from app.pricing.utils import calculate_pricing
from app.contracts.contract_generator import ContractGenerator
from app.proposals.forms import ProposalFilterForm

class ProposalView:
    def proposal_list(self, request):
        """
        Muestra la lista de propuestas con filtros.
        
        Args:
            request: HttpRequest
            
        Returns:
            HttpResponse: Página con la lista de propuestas
        """
        # Crear formulario de filtros
        filter_form = ProposalFilterForm(request.GET)
        
        # Obtener queryset base
        proposals = Proposal.objects.all().order_by('-created_at')
        
        # Aplicar filtros
        if filter_form.is_valid():
            proposals = filter_form.filter_queryset(proposals)
        
        # Paginación
        from django.core.paginator import Paginator
        paginator = Paginator(proposals, 10)  # 10 propuestas por página
        page_number = request.GET.get('page', 1)
        proposals = paginator.get_page(page_number)
        
        return render(request, 'proposals/proposal_list.html', {
            'proposals': proposals,
            'filter_form': filter_form
        })
        
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
        # Renderizar template
        html_content = render_to_string('proposals/proposal_template.html', {
            'proposal': proposal,
            'pricing': proposal.pricing_details,
            'company': proposal.company
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
