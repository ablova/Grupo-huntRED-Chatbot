from datetime import timedelta, datetime
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.conf import settings
import uuid

from app.models import DiscountCoupon, Proposal, User
from app.ats.pricing.models import TeamEvaluation

class PricingService:
    """
    Servicio principal para la gestión de precios y promociones.
    """
    
    @staticmethod
    def generate_discount_coupon(
        user: User,
        discount_percentage: int = 5,
        validity_hours: int = 4,
        proposal: Proposal = None,
        description: str = None,
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
        from app.ats.pricing.models import DiscountCoupon
        
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
        from app.ats.pricing.models import DiscountCoupon
        
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
    def create_team_evaluation_offer(
        user: User,
        team_size: int = 10,
        validity_days: int = 7,
        discount_percentage: int = 100
    ) -> dict:
        """
        Crea una oferta especial de evaluación de equipo.
        
        Args:
            user: Usuario al que se ofrece la evaluación
            team_size: Número de miembros del equipo a evaluar
            validity_days: Días de validez de la oferta
            discount_percentage: Porcentaje de descuento (100% = gratuito)
            
        Returns:
            dict: Detalles de la oferta
        """
        from app.ats.pricing.models import TeamEvaluation
        
        # Crear la evaluación de equipo
        evaluation = TeamEvaluation.objects.create(
            user=user,
            team_size=team_size,
            status='pending',
            expires_at=timezone.now() + timedelta(days=validity_days),
            discount_percentage=discount_percentage
        )
        
        # Generar un código de descuento para la evaluación
        coupon = PricingService.generate_discount_coupon(
            user=user,
            discount_percentage=discount_percentage,
            validity_hours=validity_days * 24,  # Convertir días a horas
            description=f"Evaluación para {team_size} miembros del equipo"
        )
        
        return {
            'success': True,
            'evaluation_id': evaluation.id,
            'coupon_code': coupon.code,
            'team_size': team_size,
            'discount_percentage': discount_percentage,
            'expires_at': evaluation.expires_at,
            'status': evaluation.status
        }
    
    @staticmethod
    def get_promotion_banner_data(user: User = None) -> dict:
        """
        Genera datos para mostrar un banner de promoción atractivo.
        
        Args:
            user: Usuario actual (opcional)
            
        Returns:
            dict: Datos para el banner de promoción
        """
        from django.utils.timezone import now
        
        # Fecha de la promoción (últimos 3 días del mes)
        today = now().date()
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
        
        # Si hay un usuario autenticado, verificar si ya tiene una evaluación pendiente
        if user and user.is_authenticated:
            from app.ats.pricing.models import TeamEvaluation
            has_pending_evaluation = TeamEvaluation.objects.filter(
                user=user,
                status='pending',
                expires_at__gt=now()
            ).exists()
            
            if has_pending_evaluation:
                banner_data.update({
                    'title': '¡Tienes una evaluación pendiente!',
                    'subtitle': 'Completa tu evaluación de equipo',
                    'cta_text': 'Continuar Evaluación',
                    'badge_text': 'Activo',
                    'badge_style': 'success'
                })
        
        return banner_data
