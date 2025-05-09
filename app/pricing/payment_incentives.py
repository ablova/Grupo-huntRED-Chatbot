from decimal import Decimal
from datetime import timedelta
from app.models import Proposal

class PaymentIncentiveCalculator:
    def __init__(self):
        self.base_discount = Decimal('0.05')  # 5% base
        self.additional_discount_rate = Decimal('0.01')  # 1% extra por cada semana
        self.max_discount = Decimal('0.10')  # Máximo 10%
        
    def calculate_discount(self, amount, days_early):
        """
        Calcula el descuento por pago anticipado.
        
        Args:
            amount: Monto total
            days_early: Días antes del vencimiento
            
        Returns:
            Tuple: (descuento, monto_final)
        """
        # Calcular descuento base
        discount = self.base_discount
        
        # Añadir descuento adicional por cada semana
        weeks_early = days_early // 7
        additional_discount = self.additional_discount_rate * weeks_early
        
        # Aplicar máximo
        total_discount = min(discount + additional_discount, self.max_discount)
        
        # Calcular monto final
        final_amount = amount * (1 - total_discount)
        
        return total_discount, final_amount
        
    def apply_incentive(self, proposal, days_early):
        """
        Aplica el incentivo al pago de una propuesta.
        
        Args:
            proposal: Propuesta
            days_early: Días antes del vencimiento
            
        Returns:
            Dict con detalles del incentivo
        """
        discount, final_amount = self.calculate_discount(
            proposal.pricing_total,
            days_early
        )
        
        return {
            'original_amount': proposal.pricing_total,
            'discount': discount,
            'final_amount': final_amount,
            'savings': proposal.pricing_total - final_amount
        }
