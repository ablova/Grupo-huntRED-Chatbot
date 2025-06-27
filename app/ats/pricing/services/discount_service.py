# app/ats/pricing/services/discount_service.py
from typing import Dict, Any, List, Optional
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import timedelta

from app.models import BusinessUnit, Person, DiscountCoupon, Proposal

class DiscountService:
    """Servicio para gestión de descuentos y cupones"""
    
    @staticmethod
    def generate_discount_coupon(
        user: User,
        discount_percentage: int = 5,
        validity_hours: int = 4,
        proposal: Optional[Proposal] = None,
        description: str = "",
        max_uses: int = 1
    ) -> DiscountCoupon:
        """
        Genera un cupón de descuento con un porcentaje específico y validez limitada.
        
        Args:
            user: Usuario al que se le asigna el cupón
            discount_percentage: Porcentaje de descuento (por defecto 5%)
            validity_hours: Horas de validez del cupón (por defecto 4 horas)
            proposal: Propuesta asociada al cupón (opcional)
            description: Descripción personalizada del cupón
            max_uses: Número máximo de usos permitidos
            
        Returns:
            DiscountCoupon: El cupón generado
        """
        return DiscountCoupon.create_coupon(
            user=user,
            discount_percentage=discount_percentage,
            validity_hours=validity_hours,
            proposal=proposal,
            description=description or f"{discount_percentage}% de descuento por tiempo limitado",
            max_uses=max_uses
        )
    
    @staticmethod
    def apply_discount_coupon(
        coupon_code: str,
        user: User,
        original_amount: float
    ) -> dict:
        """
        Aplica un cupón de descuento a un monto.
        
        Args:
            coupon_code: Código del cupón
            user: Usuario que está usando el cupón
            original_amount: Monto original al que se aplicará el descuento
            
        Returns:
            dict: Resultado de la aplicación del cupón
        """
        try:
            coupon = DiscountCoupon.objects.get(code=coupon_code, user=user)
            
            if not coupon.is_valid():
                return {
                    'success': False,
                    'error': 'Cupón no válido o ya ha sido utilizado',
                    'discount_amount': 0,
                    'final_amount': original_amount
                }
            
            # Aplicar descuento
            discount_amount = coupon.get_discount_amount(original_amount)
            final_amount = max(original_amount - discount_amount, 0)
            
            # Marcar como usado
            coupon.mark_as_used()
            
            return {
                'success': True,
                'discount_percentage': coupon.discount_percentage,
                'discount_amount': discount_amount,
                'final_amount': final_amount,
                'coupon_code': coupon.code,
                'expires_in': coupon.get_time_remaining()
            }
            
        except DiscountCoupon.DoesNotExist:
            return {
                'success': False,
                'error': 'Cupón no encontrado',
                'discount_amount': 0,
                'final_amount': original_amount
            }
    
    @staticmethod
    def get_promotion_banner_data(user: Optional[User] = None) -> dict:
        """
        Genera datos para mostrar un banner de promoción atractivo.
        
        Args:
            user: Usuario actual (opcional)
            
        Returns:
            dict: Datos para el banner de promoción
        """
        # Fecha de la promoción (últimos 3 días del mes)
        today = timezone.now().date()
        end_of_month = today.replace(day=28) + timedelta(days=4)
        end_of_month = end_of_month.replace(day=1) - timedelta(days=1)
        
        # Calcular días restantes
        days_remaining = (end_of_month - today).days
        
        # Solo mostrar la promoción los últimos 3 días del mes
        if days_remaining > 3:
            return {'active': False}
        
        # Generar datos del banner
        banner_data = {
            'active': True,
            'title': '¡Oferta Especial de Fin de Mes!',
            'subtitle': 'Evaluación de Equipo Gratuita',
            'description': 'Obtén una evaluación detallada para 10 miembros de tu equipo',
            'highlight': '100% DE DESCUENTO',
            'days_remaining': days_remaining,
            'expires_at': end_of_month.strftime('%d de %B'),
            'cta_text': 'Aprovechar Oferta',
            'cta_link': '/pricing/team-evaluation/',
            'badge_text': '¡Limitado!',
            'badge_style': 'danger',
            'features': [
                'Evaluación para 10 miembros',
                'Informe detallado por colaborador',
                'Recomendaciones personalizadas',
                'Válido hasta agotar existentes'
            ]
        }
        
        return banner_data
