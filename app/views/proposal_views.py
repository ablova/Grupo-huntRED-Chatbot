"""
Vistas para manejar propuestas y sus operaciones.
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from weasyprint import HTML, CSS
from django.conf import settings
import tempfile
import os

from app.models import Proposal

def download_proposal_pdf(request, proposal_id):
    """
    Genera y descarga un PDF de la propuesta.
    
    Args:
        request: Solicitud HTTP
        proposal_id: ID de la propuesta
        
    Returns:
        HttpResponse con el PDF adjunto
    """
    # Obtener la propuesta
    proposal = get_object_or_404(Proposal, id=proposal_id)
    
    # Verificar permisos (opcional)
    # Aquí se puede añadir lógica para verificar que el usuario tenga acceso a esta propuesta
    
    # Preparar el contexto para el template
    context = {
        'proposal': proposal,
        'client': proposal.client,
        'company': proposal.company,
        # Si hay una relación con vacantes, obtener la primera para la propuesta
        'vacancy': proposal.vacancy_set.first() if hasattr(proposal, 'vacancy_set') else None,
        # Otros datos necesarios para el template
    }
    
    # Crear un archivo temporal para el PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        # Renderizar el template HTML
        template = get_template('proposals/proposal_template.html')
        html_string = template.render(context)
        
        # Obtener CSS para impresión
        css_url = os.path.join(settings.STATIC_ROOT, 'css/proposal_print.css')
        css = CSS(filename=css_url) if os.path.exists(css_url) else None
        
        # Generar el PDF
        HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(tmp.name, stylesheets=[css] if css else None)
        
        # Preparar la respuesta con el PDF adjunto
        with open(tmp.name, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="propuesta_{proposal.id}.pdf"'
            
        # Eliminar el archivo temporal
        os.unlink(tmp.name)
        
    return response
