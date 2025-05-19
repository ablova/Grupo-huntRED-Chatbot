from app.notifications.templates.basebase import BaseTemplate
import logging

logger = logging.getLogger('app.notifications.templates.payment')

class PaymentTemplate(BaseTemplate):
    """Template para notificaciones de pago."""
    
    def render(self, context: Dict) -> str:
        """Renderiza el template de pago."""
        try:
            template = """
            Estimado/a {name},
            
            Le informamos sobre el estado de su pago:
            
            Detalles:
            - Referencia: {reference}
            - Monto: ${amount:.2f}
            - Fecha: {date}
            - Estado: {status}
            
            Atentamente,
            El equipo de huntRED
            """
            
            rendered = template.format(
                name=context.get('name', 'cliente'),
                reference=context.get('reference', 'N/A'),
                amount=context.get('amount', 0.0),
                date=context.get('date', 'N/A'),
                status=context.get('status', 'Pendiente')
            )
            
            self._log_render(context, True)
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering payment template: {str(e)}")
            self._log_render(context, False)
            return "Error rendering payment template"
