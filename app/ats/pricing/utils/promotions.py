"""
Utilidades para gestionar promociones y ofertas especiales.
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import timedelta

from app.models import BusinessUnit, Person, DiscountCoupon

def get_active_promotions(user=None):
    """
    Obtiene todas las promociones activas para un usuario.
    
    Args:
        user: Usuario actual (opcional)
        
    Returns:
        dict: Promociones activas
    """
    cache_key = f'active_promotions_{user.id if user else "anonymous"}'
    promotions = cache.get(cache_key)
    
    if promotions is None:
        now = timezone.now()
        
        # Obtener ofertas especiales (ej: descuentos por tiempo limitado)
        special_offers = []
        
        # Oferta de fin de mes
        today = timezone.now().date()
        end_of_month = today.replace(day=28) + timedelta(days=4)
        end_of_month = end_of_month.replace(day=1) - timedelta(days=1)
        days_remaining = (end_of_month - today).days
        
        if 0 <= days_remaining <= 3:  # Últimos 3 días del mes
            special_offers.append({
                'type': 'end_of_month',
                'title': '¡Oferta de Fin de Mes!',
                'description': 'Aprovecha hasta un 20% de descuento en todos nuestros servicios',
                'discount_percentage': 20,
                'days_remaining': days_remaining,
                'expires_at': end_of_month.strftime('%d de %B'),
                'cta_text': 'Ver Oferta',
                'cta_link': '/ofertas/fin-de-mes/'
            })
        
        promotions = {
            'special_offers': special_offers,
            'timestamp': now.isoformat()
        }
        
        # Cachear por 1 hora
        cache.set(cache_key, promotions, 3600)
    
    return promotions

def create_end_of_month_promotion():
    """
    Crea automáticamente una promoción de fin de mes usando cupones de descuento.
    """
    now = timezone.now()
    start_date = now.replace(day=28, hour=0, minute=0, second=0, microsecond=0)
    end_date = (start_date + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    # Verificar si ya existe una promoción para este mes
    existing = DiscountCoupon.objects.filter(
        description__icontains='fin de mes',
        created_at__year=now.year,
        created_at__month=now.month
    ).exists()
    
    if not existing and now.day >= 28:  # Solo crear si estamos en los últimos días del mes
        # Crear cupón de descuento especial
        from app.ats.pricing.services.discount_service import DiscountService
        
        # Crear cupón para usuarios anónimos (se asignará cuando se use)
        DiscountService.generate_discount_coupon(
            user=None,  # Se asignará al primer usuario que lo use
            discount_percentage=20,
            validity_hours=72,  # 3 días
            description='Oferta Especial de Fin de Mes - 20% de descuento',
            max_uses=100  # Permitir múltiples usos
        )

def get_promotion_banner_context(user=None):
    """
    Genera el contexto para mostrar un banner de promoción.
    
    Args:
        user: Usuario actual (opcional)
        
    Returns:
        dict: Contexto para la plantilla de promoción
    """
    promotions = get_active_promotions(user)
    
    # No hay promociones activas
    return {'show_promotion': False}

def apply_promotion_code(user, code, amount):
    """
    Aplica un código de promoción o descuento a un monto.
    
    Args:
        user: Usuario que aplica el código
        code: Código de promoción
        amount: Monto original
        
    Returns:
        dict: Resultado de la aplicación del código
    """
    from app.ats.pricing.services.discount_service import DiscountService
    
    # Verificar si es un cupón de descuento
    try:
        coupon = DiscountCoupon.objects.get(
            code=code,
            is_used=False,
            expiration_date__gt=timezone.now()
        )
        return DiscountService.apply_discount_coupon(code, user, amount)
    except DiscountCoupon.DoesNotExist:
        pass
    
    # Si no es un cupón válido
    return {
        'success': False,
        'error': 'Código de promoción no válido',
        'discount_amount': 0,
        'final_amount': amount
    }
