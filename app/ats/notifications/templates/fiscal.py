from typing import Dict
from app.ats.notifications.templates.base import BaseTemplate
import logging

logger = logging.getLogger('app.ats.notifications.templates.fiscal')

class FiscalTemplate(BaseTemplate):
    """Template para notificaciones fiscales."""
    
    def render(self, context: Dict) -> str:
        """Renderiza el template fiscal."""
        try:
            template = """
            Estimado/a {name},
            
            Le recordamos que es responsable fiscal de {company}.
            
            Detalles:
            - RFC: {rfc}
            - Posición: {position}
            - Estado: {status}
            
            Por favor, revise su información fiscal en el portal.
            
            Atentamente,
            El equipo de huntRED
            """
            
            rendered = template.format(
                name=context.get('name', 'responsable fiscal'),
                company=context.get('company', 'N/A'),
                rfc=context.get('rfc', 'N/A'),
                position=context.get('position', 'N/A'),
                status=context.get('status', 'Activo')
            )
            
            self._log_render(context, True)
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering fiscal template: {str(e)}")
            self._log_render(context, False)
            return "Error rendering fiscal template"
