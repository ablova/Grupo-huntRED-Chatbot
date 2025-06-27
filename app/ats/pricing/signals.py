"""
Señales para el módulo de precios.
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache

from .models import DiscountCoupon


@receiver(post_save, sender=DiscountCoupon)
def validate_discount_coupon(sender, instance, created, **kwargs):
    """
    Valida los datos de un cupón de descuento antes de guardarlo.
    """
    if created:
        # Limpiar cache de promociones
        cache.delete_pattern('active_promotions_*')


@receiver(post_save, sender=DiscountCoupon)
def update_coupon_status(sender, instance, **kwargs):
    """
    Actualiza el estado del cupón cuando se usa.
    """
    if instance.is_used:
        # Limpiar cache de promociones
        cache.delete_pattern('active_promotions_*')


@receiver(pre_delete, sender=DiscountCoupon)
def cleanup_team_evaluation(sender, instance, **kwargs):
    """
    Limpia datos relacionados cuando se elimina un cupón.
    """
    # Limpiar cache de promociones
    cache.delete_pattern('active_promotions_*')
