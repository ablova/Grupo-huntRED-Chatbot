from .base import BaseTemplate
import logging

logger = logging.getLogger('app.notifications.templates.opportunity')

class OpportunityTemplate(BaseTemplate):
    """Template para notificaciones de oportunidades."""
    
    def render(self, context: Dict) -> str:
        """Renderiza el template de oportunidad."""
        try:
            template = """
            Estimado/a {name},
            
            Hemos encontrado una nueva oportunidad que podría interesarte:
            
            Detalles:
            - Puesto: {position}
            - Empresa: {company}
            - Ubicación: {location}
            - Salario: {salary}
            - Requisitos: {requirements}
            
            Para más información, por favor responde a este mensaje.
            
            Atentamente,
            El equipo de huntRED
            """
            
            rendered = template.format(
                name=context.get('name', 'candidato/a'),
                position=context.get('position', 'N/A'),
                company=context.get('company', 'N/A'),
                location=context.get('location', 'N/A'),
                salary=context.get('salary', 'N/A'),
                requirements=context.get('requirements', 'N/A')
            )
            
            self._log_render(context, True)
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering opportunity template: {str(e)}")
            self._log_render(context, False)
            return "Error rendering opportunity template"
