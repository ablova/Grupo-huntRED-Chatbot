""
Señales para el módulo de precios.
"""
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import DiscountCoupon, TeamEvaluation, PromotionBanner


@receiver(pre_save, sender=DiscountCoupon)
def validate_discount_coupon(sender, instance, **kwargs):
    """
    Valida los datos de un cupón de descuento antes de guardarlo.
    """
    instance.full_clean()


@receiver(post_save, sender=TeamEvaluation)
def create_team_evaluation_coupon(sender, instance, created, **kwargs):
    """
    Crea automáticamente un cupón de descuento cuando se crea una evaluación de equipo.
    """
    from .services.discount_service import PricingService
    
    if created and not instance.coupon:
        # Crear un cupón de descuento del 100% para la evaluación
        coupon = PricingService.generate_discount_coupon(
            user=instance.user,
            discount_percentage=instance.discount_percentage,
            validity_hours=24 * (instance.expires_at - timezone.now()).days,
            description=f"Evaluación para {instance.team_size} miembros del equipo",
            max_uses=1
        )
        instance.coupon = coupon
        instance.save(update_fields=['coupon'])


@receiver(pre_save, sender=PromotionBanner)
def validate_promotion_banner_dates(sender, instance, **kwargs):
    """
    Valida que las fechas del banner de promoción sean coherentes.
    """
    if instance.start_date >= instance.end_date:
        raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin")


@receiver(pre_save, sender=DiscountCoupon)
def update_coupon_status(sender, instance, **kwargs):
    """
    Actualiza el estado del cupón basado en la fecha de expiración y usos.
    """
    if instance.use_count >= instance.max_uses:
        instance.is_used = True
        instance.used_at = timezone.now()
    
    if instance.expiration_date <= timezone.now() and not instance.is_used:
        instance.is_used = True
        instance.used_at = timezone.now()


@receiver(pre_delete, sender=TeamEvaluation)
def cleanup_team_evaluation(sender, instance, **kwargs):
    """
    Limpia los recursos asociados a una evaluación de equipo al eliminarla.
    """
    if instance.coupon:
        # Opcional: eliminar el cupón asociado
        # instance.coupon.delete()
        pass
