from typing import Dict
from app.ats.notifications.templates.base import BaseTemplate
import logging

logger = logging.getLogger('app.ats.notifications.templates.payment')

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
            - Monto: ${amount}
            - Fecha: {date}
            - Estado: {status}
            
            Atentamente,
            El equipo de huntRED
            """
            # Asegurarse de que amount sea string y tenga formato correcto
            amount = context.get('amount', 0.0)
            if isinstance(amount, (int, float)):
                amount_str = f"{amount:,.2f}"
            else:
                try:
                    amount_str = f"{float(amount):,.2f}"
                except Exception:
                    amount_str = str(amount)
            
            rendered = template.format(
                name=context.get('name', 'cliente'),
                reference=context.get('reference', 'N/A'),
                amount=amount_str,
                date=context.get('date', 'N/A'),
                status=context.get('status', 'Pendiente')
            )
            
            self._log_render(context, True)
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering payment template: {str(e)}")
            self._log_render(context, False)
            return "Error rendering payment template"
