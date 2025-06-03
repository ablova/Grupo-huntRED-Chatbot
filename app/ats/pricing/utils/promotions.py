"""
Utilidades para gestionar promociones y ofertas especiales.
"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from app.ats.pricing.models import PromotionBanner, TeamEvaluation, DiscountCoupon
from app.models import User

def get_active_promotions(user=None):
    """
    Obtiene las promociones activas para mostrar al usuario.
    
    Args:
        user: Usuario autenticado (opcional)
        
    Returns:
        dict: Diccionario con las promociones activas
    """
    cache_key = 'active_promotions'
    promotions = cache.get(cache_key)
    
    if promotions is None:
        now = timezone.now()
        
        # Obtener banners promocionales activos
        banners = PromotionBanner.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-priority')
        
        # Obtener promoción de evaluación de equipo si el usuario está autenticado
        team_evaluation = None
        if user and user.is_authenticated:
            team_evaluation = TeamEvaluation.objects.filter(
                user=user,
                status__in=['pending', 'in_progress'],
                expires_at__gt=now
            ).order_by('expires_at').first()
        
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
            'banners': [banner for banner in banners if banner.is_currently_active()],
            'team_evaluation': team_evaluation,
            'special_offers': special_offers,
            'timestamp': now.isoformat()
        }
        
        # Cachear por 1 hora o hasta que la próxima promoción esté por comenzar
        next_promotion = PromotionBanner.objects.filter(
            is_active=True,
            start_date__gt=now
        ).order_by('start_date').first()
        
        if next_promotion:
            cache_timeout = (next_promotion.start_date - now).total_seconds()
        else:
            cache_timeout = 3600  # 1 hora por defecto
            
        cache.set(cache_key, promotions, min(cache_timeout, 3600))
    
    return promotions

def create_end_of_month_promotion():
    """
    Crea automáticamente una promoción de fin de mes.
    """
    now = timezone.now()
    start_date = now.replace(day=28, hour=0, minute=0, second=0, microsecond=0)
    end_date = (start_date + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    # Verificar si ya existe una promoción para este mes
    existing = PromotionBanner.objects.filter(
        title__icontains='fin de mes',
        start_date__year=now.year,
        start_date__month=now.month
    ).exists()
    
    if not existing and now.day >= 28:  # Solo crear si estamos en los últimos días del mes
        PromotionBanner.objects.create(
            title='¡Oferta Especial de Fin de Mes!',
            subtitle='Hasta 20% de descuento en todos nuestros servicios',
            content='<p>Aprovecha nuestros descuentos especiales de fin de mes. Válido hasta agotar existentes.</p>',
            start_date=start_date,
            end_date=end_date.replace(hour=23, minute=59, second=59),
            button_text='¡Aprovechar Ahora!',
            badge_text='¡Oferta!',
            badge_style='danger',
            priority=10,
            target_url='/ofertas/fin-de-mes/'
        )

def generate_team_evaluation_offer(user, team_size=10, validity_days=7):
    """
    Genera una oferta de evaluación de equipo para un usuario.
    
    Args:
        user: Usuario al que se le ofrece la evaluación
        team_size: Número de miembros del equipo
        validity_days: Días de validez de la oferta
        
    Returns:
        dict: Detalles de la oferta
    """
    from app.ats.pricing.services.discount_service import PricingService
    
    # Verificar si ya tiene una evaluación pendiente
    existing_evaluation = TeamEvaluation.objects.filter(
        user=user,
        status__in=['pending', 'in_progress'],
        expires_at__gt=timezone.now()
    ).first()
    
    if existing_evaluation:
        return {
            'success': False,
            'error': 'Ya tienes una evaluación pendiente',
            'evaluation': existing_evaluation
        }
    
    # Crear la oferta
    return PricingService.create_team_evaluation_offer(
        user=user,
        team_size=team_size,
        validity_days=validity_days
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
    banner = promotions.get('banners', [None])[0] if promotions.get('banners') else None
    
    if not banner and promotions.get('team_evaluation'):
        # Mostrar banner de evaluación de equipo si no hay otro banner activo
        evaluation = promotions['team_evaluation']
        return {
            'show_promotion': True,
            'promotion_type': 'team_evaluation',
            'title': '¡Evaluación de Equipo Gratuita!',
            'subtitle': f'Para {evaluation.team_size} miembros de tu equipo',
            'description': 'Obtén un análisis detallado del rendimiento de tu equipo',
            'badge_text': '¡Limitado!',
            'badge_style': 'success',
            'expires_at': evaluation.expires_at,
            'days_remaining': evaluation.get_time_remaining().days,
            'cta_text': 'Comenzar Evaluación',
            'cta_link': '/equipo/evaluacion/'
        }
    elif banner and banner.is_currently_active():
        # Mostrar banner promocional estándar
        return {
            'show_promotion': True,
            'promotion_type': 'banner',
            'title': banner.title,
            'subtitle': banner.subtitle,
            'description': banner.content,
            'badge_text': banner.badge_text,
            'badge_style': banner.badge_style,
            'expires_at': banner.end_date,
            'days_remaining': banner.days_remaining(),
            'cta_text': banner.button_text,
            'cta_link': banner.target_url or '#',
            'has_countdown': True,
            'countdown_data': banner.get_countdown_data()
        }
    
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
    from app.ats.pricing.services.discount_service import PricingService
    
    # Verificar si es un cupón de descuento
    try:
        coupon = DiscountCoupon.objects.get(
            code=code,
            is_used=False,
            expiration_date__gt=timezone.now()
        )
        return PricingService.apply_discount_coupon(code, user, amount)
    except DiscountCoupon.DoesNotExist:
        pass
    
    # Aquí se pueden agregar más tipos de códigos promocionales
    
    return {
        'success': False,
        'error': 'Código no válido o expirado',
        'discount_amount': 0,
        'final_amount': amount
    }
