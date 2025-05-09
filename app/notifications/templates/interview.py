from .base import BaseTemplate
import logging

logger = logging.getLogger('app.notifications.templates.interview')

class InterviewTemplate(BaseTemplate):
    """Template para notificaciones de entrevistas."""
    
    def render(self, context: Dict) -> str:
        """Renderiza el template de entrevista."""
        try:
            template = """
            Estimado/a {name},
            
            Le informamos que su entrevista para la posición de {position} está programada para:
            
            Fecha y hora: {interview_time}
            Lugar: {interview_location}
            
            Entrevistadores:
            {interviewers}
            
            Por favor, confirme su asistencia.
            
            Atentamente,
            El equipo de huntRED
            """
            
            rendered = template.format(
                name=context.get('name', 'candidato/a'),
                position=context.get('position', 'N/A'),
                interview_time=context.get('interview_time', 'N/A'),
                interview_location=context.get('interview_location', 'N/A'),
                interviewers='\n'.join(context.get('interviewers', []))
            )
            
            self._log_render(context, True)
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering interview template: {str(e)}")
            self._log_render(context, False)
            return "Error rendering interview template"
