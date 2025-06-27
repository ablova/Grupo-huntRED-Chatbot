from datetime import datetime, timedelta
from app.models import DiscountCoupon, User, Proposal

class CouponService:
    @staticmethod
    def generate_coupon(user: User, discount_percentage: int = 5, validity_hours: int = 4, proposal: Proposal = None, description: str = None, max_uses: int = 1, campaign: str = None, bundle: str = None) -> DiscountCoupon:
        """
        Genera un cupón de descuento alineado con el modelo DiscountCoupon y campañas/bundles.
        """
        return DiscountCoupon.create_coupon(
            user=user,
            discount_percentage=discount_percentage,
            validity_hours=validity_hours,
            proposal=proposal,
            description=description or f"{discount_percentage}% de descuento por tiempo limitado",
            max_uses=max_uses,
            campaign=campaign,
            bundle=bundle
        )

    @staticmethod
    def validate_coupon(coupon_code: str, user: User, bundle: str = None, campaign: str = None) -> bool:
        """
        Valida si un cupón es válido para el usuario, campaña y/o bundle.
        """
        try:
            coupon = DiscountCoupon.objects.get(code=coupon_code, user=user)
            if not coupon.is_valid():
                return False
            if bundle and coupon.bundle != bundle:
                return False
            if campaign and coupon.campaign != campaign:
                return False
            return True
        except DiscountCoupon.DoesNotExist:
            return False

    @staticmethod
    def apply_coupon(coupon_code: str, user: User, original_amount: float) -> dict:
        """
        Aplica un cupón de descuento y retorna el resultado.
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
            discount_amount = coupon.get_discount_amount(original_amount)
            final_amount = max(original_amount - discount_amount, 0)
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
    def mark_coupon_used(coupon_code: str, user: User):
        """
        Marca un cupón como usado.
        """
        try:
            coupon = DiscountCoupon.objects.get(code=coupon_code, user=user)
            coupon.mark_as_used()
        except DiscountCoupon.DoesNotExist:
            pass

    @staticmethod
    def associate_coupon_to_campaign(coupon_code: str, campaign: str):
        """
        Asocia un cupón a una campaña específica.
        """
        try:
            coupon = DiscountCoupon.objects.get(code=coupon_code)
            coupon.campaign = campaign
            coupon.save()
        except DiscountCoupon.DoesNotExist:
            pass

    @staticmethod
    def associate_coupon_to_bundle(coupon_code: str, bundle: str):
        """
        Asocia un cupón a un bundle específico.
        """
        try:
            coupon = DiscountCoupon.objects.get(code=coupon_code)
            coupon.bundle = bundle
            coupon.save()
        except DiscountCoupon.DoesNotExist:
            pass 