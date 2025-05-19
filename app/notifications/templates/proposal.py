from app.notifications.templates.basebase import BaseTemplate
import logging

logger = logging.getLogger('app.notifications.templates.proposal')

class ProposalTemplate(BaseTemplate):
    """Template para notificaciones de propuestas."""
    
    def render(self, context: Dict) -> str:
        """Renderiza el template de propuesta."""
        try:
            template = """
            Estimado/a {name},
            
            Le informamos que hemos recibido su propuesta para la posición de {position}.
            
            Detalles:
            - Empresa: {company}
            - Ubicación: {location}
            - Salario: {salary}
            
            Estado actual: {status}
            
            Atentamente,
            El equipo de huntRED
            """
            
            rendered = template.format(
                name=context.get('name', 'candidato/a'),
                position=context.get('position', 'N/A'),
                company=context.get('company', 'N/A'),
                location=context.get('location', 'N/A'),
                salary=context.get('salary', 'N/A'),
                status=context.get('status', 'En revisión')
            )
            
            self._log_render(context, True)
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering proposal template: {str(e)}")
            self._log_render(context, False)
            return "Error rendering proposal template"
