from typing import Dict
from app.ats.notifications.templates.base import BaseTemplate
import logging

logger = logging.getLogger('app.ats.notifications.templates.collector')

class CollectorTemplate(BaseTemplate):
    """Template para notificaciones de cobro."""
    
    def render(self, context: Dict) -> str:
        """Renderiza el template de cobro."""
        try:
            template = """
            Estimado/a {name},
            
            Le recordamos que es responsable de cobro para {company}.
            
            Detalles:
            - Posición: {position}
            - Términos de pago: {payment_terms}
            - Estado: {status}
            
            Por favor, revise los pagos pendientes en el portal.
            
            Atentamente,
            El equipo de huntRED
            """
            
            rendered = template.format(
                name=context.get('name', 'responsable de cobro'),
                company=context.get('company', 'N/A'),
                position=context.get('position', 'N/A'),
                payment_terms=context.get('payment_terms', 'N/A'),
                status=context.get('status', 'Activo')
            )
            
            self._log_render(context, True)
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering collector template: {str(e)}")
            self._log_render(context, False)
            return "Error rendering collector template"
