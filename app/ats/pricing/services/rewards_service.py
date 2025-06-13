from typing import Dict, List, Optional
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from app.models import Company, Proposal
from app.ats.pricing.models import DiscountCoupon, PricingCalculation

class RewardsService:
    def __init__(self):
        self.base_points = 100  # Puntos base por propuesta
        self.early_payment_bonus = 50  # Puntos extra por pago anticipado
        self.referral_bonus = 200  # Puntos por referido exitoso
        self.points_to_discount = 1000  # Puntos necesarios para 5% de descuento

    def calculate_points(self, company: Company) -> Dict:
        """
        Calcula los puntos de recompensa para una empresa.
        
        Args:
            company: Instancia de Company
            
        Returns:
            Dict: Detalles de puntos y recompensas
        """
        # Obtener propuestas de los últimos 12 meses
        proposals = Proposal.objects.filter(
            company=company,
            created_at__gte=timezone.now() - timedelta(days=365)
        )
        
        # Calcular puntos base
        base_points = proposals.count() * self.base_points
        
        # Calcular puntos por pagos anticipados
        early_payment_points = self._calculate_early_payment_points(company)
        
        # Calcular puntos por referidos
        referral_points = self._calculate_referral_points(company)
        
        # Calcular total de puntos
        total_points = base_points + early_payment_points + referral_points
        
        # Calcular descuentos disponibles
        available_discounts = self._calculate_available_discounts(total_points)
        
        return {
            'total_points': total_points,
            'base_points': base_points,
            'early_payment_points': early_payment_points,
            'referral_points': referral_points,
            'available_discounts': available_discounts,
            'next_discount': self._calculate_next_discount(total_points)
        }

    def _calculate_early_payment_points(self, company: Company) -> int:
        """
        Calcula puntos por pagos anticipados.
        
        Args:
            company: Instancia de Company
            
        Returns:
            int: Puntos por pagos anticipados
        """
        early_payments = PricingCalculation.objects.filter(
            company=company,
            created_at__gte=timezone.now() - timedelta(days=365),
            payment_status='received',
            payment_date__lt=models.F('due_date')
        )
        
        return early_payments.count() * self.early_payment_bonus

    def _calculate_referral_points(self, company: Company) -> int:
        """
        Calcula puntos por referidos exitosos.
        
        Args:
            company: Instancia de Company
            
        Returns:
            int: Puntos por referidos
        """
        successful_referrals = Proposal.objects.filter(
            referred_by=company,
            status='completed',
            created_at__gte=timezone.now() - timedelta(days=365)
        )
        
        return successful_referrals.count() * self.referral_bonus

    def _calculate_available_discounts(self, total_points: int) -> List[Dict]:
        """
        Calcula los descuentos disponibles según puntos.
        
        Args:
            total_points: Total de puntos acumulados
            
        Returns:
            List[Dict]: Lista de descuentos disponibles
        """
        available_discounts = []
        current_points = total_points
        
        while current_points >= self.points_to_discount:
            discount_percentage = (current_points // self.points_to_discount) * 5
            if discount_percentage > 20:  # Máximo 20% de descuento
                break
                
            available_discounts.append({
                'percentage': discount_percentage,
                'points_required': self.points_to_discount,
                'points_remaining': current_points % self.points_to_discount
            })
            
            current_points -= self.points_to_discount
        
        return available_discounts

    def _calculate_next_discount(self, total_points: int) -> Dict:
        """
        Calcula el próximo descuento disponible.
        
        Args:
            total_points: Total de puntos acumulados
            
        Returns:
            Dict: Detalles del próximo descuento
        """
        points_to_next = self.points_to_discount - (total_points % self.points_to_discount)
        next_discount = ((total_points // self.points_to_discount) + 1) * 5
        
        if next_discount > 20:  # Máximo 20% de descuento
            return {
                'available': False,
                'message': 'Has alcanzado el máximo descuento disponible'
            }
        
        return {
            'available': True,
            'points_needed': points_to_next,
            'discount_percentage': next_discount,
            'estimated_time': self._estimate_time_to_next(points_to_next)
        }

    def _estimate_time_to_next(self, points_needed: int) -> str:
        """
        Estima el tiempo para alcanzar el próximo descuento.
        
        Args:
            points_needed: Puntos necesarios
            
        Returns:
            str: Tiempo estimado
        """
        # Calcular promedio de puntos por mes
        avg_points_per_month = self.base_points * 2  # Asumiendo 2 propuestas por mes
        
        months_needed = points_needed / avg_points_per_month
        
        if months_needed <= 1:
            return "Menos de 1 mes"
        elif months_needed <= 2:
            return "1-2 meses"
        else:
            return "Más de 2 meses"

    def generate_reward_coupon(self, company: Company, discount_percentage: int) -> Optional[DiscountCoupon]:
        """
        Genera un cupón de descuento por puntos.
        
        Args:
            company: Instancia de Company
            discount_percentage: Porcentaje de descuento
            
        Returns:
            Optional[DiscountCoupon]: Cupón generado o None si no hay puntos suficientes
        """
        points_info = self.calculate_points(company)
        
        # Verificar si el descuento está disponible
        available_discount = next(
            (d for d in points_info['available_discounts'] 
             if d['percentage'] == discount_percentage),
            None
        )
        
        if not available_discount:
            return None
        
        # Generar cupón
        return DiscountCoupon.create_coupon(
            user=company.contact_person,
            discount_percentage=discount_percentage,
            validity_hours=168,  # 1 semana
            description=f"Descuento de {discount_percentage}% por programa de recompensas"
        ) 