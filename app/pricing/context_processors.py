"""
Procesadores de contexto para el módulo de precios.
"""
from django.conf import settings

from app.pricing.utils.promotions import get_promotion_banner_context


def promotions(request):
    """
    Añade información de promociones activas al contexto de todas las plantillas.
    
    Args:
        request: Objeto HttpRequest
        
    Returns:
        dict: Contexto con información de promociones
    """
    if not getattr(settings, 'SHOW_PROMOTIONS', True):
        return {'show_promotion': False}
    
    return get_promotion_banner_context(
        request.user if hasattr(request, 'user') else None
    )
