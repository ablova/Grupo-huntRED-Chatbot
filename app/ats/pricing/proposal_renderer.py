# /home/pablo/app/ats/pricing/proposal_renderer.py
"""
Módulo para la renderización modular de propuestas en Grupo huntRED®.

Este módulo proporciona funcionalidades para renderizar propuestas modulares, 
combinando secciones reutilizables para diferentes tipos de propuestas y
servicios, asegurando consistencia en el diseño y personalización por BU.
"""

import os
import logging
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from app.ats.pricing.models import PricingProposal, ProposalSection, ProposalTemplate

logger = logging.getLogger(__name__)


class ProposalRenderer:
    """
    Renderizador modular de propuestas que combina secciones reutilizables.
    
    Esta clase permite construir propuestas dinámicas combinando secciones
    modulares como portada, pricing, descripción de servicios, etc., manteniendo
    un diseño consistente pero adaptable por BU y tipo de servicio.
    """
    
    # Directorios base para plantillas y recursos
    TEMPLATES_BASE_DIR = os.path.join(settings.BASE_DIR, 'app/templates/proposals')
    SECTIONS_DIR = os.path.join(TEMPLATES_BASE_DIR, 'sections')
    ASSETS_DIR = os.path.join(settings.STATIC_ROOT, 'img/proposals')
    OUTPUT_DIR = os.path.join(settings.MEDIA_ROOT, 'proposals')
    
    # Secciones disponibles para las propuestas
    AVAILABLE_SECTIONS = {
        'cover': 'sections/cover.html',
        'header': 'sections/header.html',
        'introduction': 'sections/introduction.html',
        'service_description': 'sections/service_description.html',
        'pricing': 'sections/pricing.html',
        'benefits': 'sections/benefits.html',
        'methodology': 'sections/methodology.html',
        'timeline': 'sections/timeline.html',
        'testimonials': 'sections/testimonials.html',
        'team': 'sections/team.html',
        'terms': 'sections/terms.html',
        'footer': 'sections/footer.html',
    }
    
    # Plantillas base para diferentes tipos de propuestas
    BASE_TEMPLATES = {
        'standard': 'base_proposal.html',
        'detailed': 'detailed_proposal.html',
        'executive': 'executive_proposal.html',
    }
    
    def __init__(self, proposal):
        """
        Inicializa el renderizador con una propuesta
        
        Args:
            proposal: Instancia de PricingProposal
        """
        self.proposal = proposal
        self.sections = proposal.secciones.all().order_by('orden')
    
    def render_html(self):
        """
        Renderiza la propuesta en HTML
        
        Returns:
            str: HTML de la propuesta
        """
        context = {
            'proposal': self.proposal,
            'sections': self.sections
        }
        return render_to_string('pricing/proposal_template.html', context)
    
    def render_pdf(self):
        """
        Renderiza la propuesta en PDF
        
        Returns:
            bytes: PDF de la propuesta
        """
        html = self.render_html()
        pdf = HTML(string=html).write_pdf()
        return pdf
    
    def render_email(self):
        """
        Renderiza la propuesta para email
        
        Returns:
            str: HTML de la propuesta para email
        """
        context = {
            'proposal': self.proposal,
            'sections': self.sections,
            'is_email': True
        }
        return render_to_string('pricing/proposal_email.html', context)
    
    def render_preview(self):
        """
        Renderiza una vista previa de la propuesta
        
        Returns:
            str: HTML de la vista previa
        """
        context = {
            'proposal': self.proposal,
            'sections': self.sections,
            'is_preview': True
        }
        return render_to_string('pricing/proposal_preview.html', context)
    
    @classmethod
    def render_proposal(cls, proposal_data, sections=None, base_template='standard', 
                       output_format='html', output_file=None):
        """
        Renderiza una propuesta completa combinando secciones modulares.
        
        Args:
            proposal_data: Diccionario con datos para la propuesta
            sections: Lista de secciones a incluir (opcional, si no se especifica
                     se utilizan todas las secciones relevantes por defecto)
            base_template: Plantilla base a utilizar ('standard', 'detailed', 'executive')
            output_format: Formato de salida ('html', 'pdf')
            output_file: Ruta donde guardar el archivo generado (opcional)
            
        Returns:
            Si output_file es None, devuelve el contenido de la propuesta.
            Si output_file se especifica, guarda la propuesta y devuelve la ruta.
        """
        logger.info(f"Generando propuesta en formato {output_format} usando "
                    f"plantilla base {base_template}")
        
        # Si no se especifican secciones, usar conjunto predeterminado basado en el tipo
        if sections is None:
            sections = cls._get_default_sections(proposal_data)
        
        # Generar contexto para la plantilla
        context = cls._prepare_context(proposal_data, sections)
        
        # Renderizar la propuesta
        base_template_path = cls.BASE_TEMPLATES.get(base_template, cls.BASE_TEMPLATES['standard'])
        html_content = render_to_string(f"proposals/{base_template_path}", context)
        
        # Manejar diferentes formatos de salida
        if output_format == 'pdf':
            return cls._generate_pdf(html_content, output_file, proposal_data)
        else:
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                return output_file
            return html_content
    
    @classmethod
    def _prepare_context(cls, proposal_data, sections):
        """
        Prepara el contexto para renderizar la plantilla de la propuesta.
        
        Args:
            proposal_data: Datos para la propuesta
            sections: Secciones a incluir
            
        Returns:
            dict: Contexto listo para renderizar la plantilla
        """
        # Contexto básico que siempre se incluye
        context = {
            'proposal_data': proposal_data,
            'sections': sections,
            'generation_date': timezone.now().strftime('%d-%m-%Y'),
            'valid_until': (timezone.now() + timezone.timedelta(days=30)).strftime('%d-%m-%Y'),
        }
        
        # Contexto para secciones específicas
        rendered_sections = {}
        for section in sections:
            template_path = cls.AVAILABLE_SECTIONS.get(section)
            if template_path:
                # Crear contexto específico para esta sección
                section_context = {**context}
                # Añadir datos adicionales específicos para algunas secciones
                if section == 'pricing' and 'pricing' in proposal_data:
                    section_context['pricing'] = proposal_data['pricing']
                
                # Renderizar la sección
                rendered_sections[section] = render_to_string(f"proposals/{template_path}", section_context)
        
        # Añadir las secciones renderizadas al contexto
        context['rendered_sections'] = rendered_sections
        
        return context
    
    @classmethod
    def _get_default_sections(cls, proposal_data):
        """
        Determina qué secciones incluir por defecto según el tipo de propuesta.
        
        Args:
            proposal_data: Datos de la propuesta
            
        Returns:
            list: Lista de secciones a incluir
        """
        # Obtener el tipo de servicio o propuesta
        service_type = proposal_data.get('service_type', 'recruitment')
        
        # Secciones estándar que siempre se incluyen
        standard_sections = ['cover', 'header', 'introduction', 'service_description', 
                           'pricing', 'benefits', 'terms', 'footer']
        
        # Añadir secciones adicionales según el tipo de servicio
        if service_type == 'talent_analysis':
            # Para análisis de talento incluir metodología y timeline
            return standard_sections + ['methodology', 'timeline']
        elif service_type == 'executive_search':
            # Para búsqueda ejecutiva incluir equipo y testimonios
            return standard_sections + ['team', 'testimonials', 'methodology']
        elif service_type == 'hr_consulting':
            # Para consultoría de RRHH incluir todas las secciones
            return list(cls.AVAILABLE_SECTIONS.keys())
        
        # Para otros tipos, usar secciones estándar
        return standard_sections
    
    @classmethod
    def _generate_pdf(cls, html_content, output_file, proposal_data):
        """
        Genera un PDF a partir del contenido HTML de la propuesta.
        
        Args:
            html_content: Contenido HTML de la propuesta
            output_file: Ruta donde guardar el PDF (opcional)
            proposal_data: Datos de la propuesta para nombrar el archivo
            
        Returns:
            str: Ruta del archivo PDF generado
        """
        # Si no se especificó un archivo de salida, generar uno
        if not output_file:
            # Crear nombre de archivo basado en datos de la propuesta
            company = proposal_data.get('company', {}).get('name', 'client')
            service = proposal_data.get('service', {}).get('name', 'proposal')
            date_str = timezone.now().strftime('%Y%m%d')
            filename = f"Propuesta_{company}_{service}_{date_str}.pdf"
            filename = filename.replace(' ', '_').lower()
            
            # Asegurar que el directorio existe
            os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
            output_file = os.path.join(cls.OUTPUT_DIR, filename)
        
        # Ruta a los CSS
        css_files = [
            os.path.join(settings.STATIC_ROOT, 'css/proposals/base.css'),
            os.path.join(settings.STATIC_ROOT, 'css/proposals/print.css')
        ]
        
        # Cargar CSS
        stylesheets = [CSS(filename=css_file) for css_file in css_files if os.path.exists(css_file)]
        
        # Generar PDF
        try:
            html = HTML(string=html_content)
            html.write_pdf(output_file, stylesheets=stylesheets)
            logger.info(f"PDF generado exitosamente: {output_file}")
            return output_file
        except ImportError:
            logger.warning("WeasyPrint no está disponible. Se devuelve el HTML como bytes.")
            return html_content.encode('utf-8')


def generate_proposal(proposal_data, sections=None, template_type='standard', 
                    output_format='html', output_file=None):
    """
    Función auxiliar para generar propuestas usando el ProposalRenderer.
    
    Args:
        proposal_data: Datos para la propuesta
        sections: Secciones a incluir (opcional)
        template_type: Tipo de plantilla ('standard', 'detailed', 'executive')
        output_format: Formato ('html', 'pdf')
        output_file: Ruta de salida (opcional)
    
    Returns:
        str: Contenido HTML o ruta al archivo generado
    """
    return ProposalRenderer.render_proposal(
        proposal_data=proposal_data,
        sections=sections,
        base_template=template_type,
        output_format=output_format,
        output_file=output_file
    )
