from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.conf import settings
import uuid

from app.models import DiscountCoupon, Proposal
from app.models import User

class DiscountService:
    """
    Servicio para manejar la lógica de descuentos y cupones.
    """
    
    @staticmethod
    def generate_discount_coupon(
        user: User,
        discount_percentage: int = 5,
        validity_hours: int = 4,
        proposal: Proposal = None
    ) -> DiscountCoupon:
        """
        Genera un cupón de descuento con un porcentaje específico y validez limitada.
        
        Args:
            user: Usuario al que se le asigna el cupón
            discount_percentage: Porcentaje de descuento (por defecto 5%)
            validity_hours: Horas de validez del cupón (por defecto 4 horas)
            proposal: Propuesta asociada al cupón (opcional)
            
        Returns:
            DiscountCoupon: El cupón generado
        """
        # Validar que el porcentaje esté entre 1 y 100
        if not 1 <= discount_percentage <= 100:
            raise ValueError("El porcentaje de descuento debe estar entre 1 y 100")
            
        # Generar un código único
        coupon_code = f"HUNT{uuid.uuid4().hex[:6].upper()}"
        
        # Calcular fecha de expiración
        expiration_date = timezone.now() + timedelta(hours=validity_hours)
        
        # Crear el cupón
        coupon = DiscountCoupon.objects.create(
            user=user,
            code=coupon_code,
            discount_percentage=discount_percentage,
            expiration_date=expiration_date,
            is_used=False,
            proposal=proposal  # Asociar con la propuesta si se proporciona
        )
        
        # Cachear el cupón para búsquedas rápidas
        cache_key = f'discount_coupon_{coupon_code}'
        cache.set(cache_key, {
            'id': coupon.id,
            'code': coupon.code,
            'discount_percentage': coupon.discount_percentage,
            'expiration_date': coupon.expiration_date.isoformat(),
            'is_used': coupon.is_used,
            'user_id': coupon.user_id,
            'proposal_id': coupon.proposal_id if hasattr(coupon, 'proposal_id') else None
        }, timeout=validity_hours * 3600)  # Cachear por el tiempo de validez
        
        return coupon
    
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
            dict: Diccionario con los resultados de la aplicación del cupón
        """
        # Verificar si el cupón está en caché
        cache_key = f'discount_coupon_{coupon_code}'
        cached_coupon = cache.get(cache_key)
        
        if cached_coupon:
            # Si el cupón está en caché, verificar si ha expirado
            from datetime import datetime
            expiration_date = datetime.fromisoformat(cached_coupon['expiration_date'])
            if expiration_date < timezone.now():
                return {
                    'success': False,
                    'error': 'El cupón ha expirado',
                    'discount_amount': 0,
                    'final_amount': original_amount
                }
                
            if cached_coupon['is_used']:
                return {
                    'success': False,
                    'error': 'El cupón ya ha sido utilizado',
                    'discount_amount': 0,
                    'final_amount': original_amount
                }
                
            # Calcular descuento
            discount_percentage = cached_coupon['discount_percentage']
            discount_amount = (original_amount * discount_percentage) / 100
            final_amount = max(original_amount - discount_amount, 0)
            
            # Marcar como usado en la base de datos (sin bloquear la respuesta)
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE app_discountcoupon SET is_used = TRUE WHERE code = %s AND is_used = FALSE",
                    [coupon_code]
                )
                
            # Actualizar caché
            cache.set(cache_key, {
                **cached_coupon,
                'is_used': True
            }, timeout=3600 * 24)  # Mantener en caché por 24 horas después de usado
            
            return {
                'success': True,
                'discount_percentage': discount_percentage,
                'discount_amount': discount_amount,
                'final_amount': final_amount,
                'coupon_code': coupon_code
            }
        
        # Si no está en caché, buscar en la base de datos
        try:
            with transaction.atomic():
                coupon = DiscountCoupon.objects.select_for_update().get(
                    code=coupon_code,
                    is_used=False,
                    expiration_date__gt=timezone.now(),
                    user=user
                )
                
                # Calcular descuento
                discount_amount = (original_amount * coupon.discount_percentage) / 100
                final_amount = max(original_amount - discount_amount, 0)
                
                # Marcar como usado
                coupon.is_used = True
                coupon.used_at = timezone.now()
                coupon.save()
                
                # Actualizar caché
                cache.set(cache_key, {
                    'id': coupon.id,
                    'code': coupon.code,
                    'discount_percentage': coupon.discount_percentage,
                    'expiration_date': coupon.expiration_date.isoformat(),
                    'is_used': True,
                    'user_id': coupon.user_id,
                    'proposal_id': coupon.proposal_id if hasattr(coupon, 'proposal_id') else None
                }, timeout=3600 * 24)  # Mantener en caché por 24 horas después de usado
                
                return {
                    'success': True,
                    'discount_percentage': coupon.discount_percentage,
                    'discount_amount': discount_amount,
                    'final_amount': final_amount,
                    'coupon_code': coupon.code
                }
                
        except DiscountCoupon.DoesNotExist:
            return {
                'success': False,
                'error': 'Cupón no válido o ya ha sido utilizado',
                'discount_amount': 0,
                'final_amount': original_amount
            }
    
    @staticmethod
    def get_coupon_status(coupon_code: str, user: User) -> dict:
        """
        Obtiene el estado actual de un cupón.
        
        Args:
            coupon_code: Código del cupón
            user: Usuario propietario del cupón
            
        Returns:
            dict: Información del estado del cupón
        """
        try:
            coupon = DiscountCoupon.objects.get(code=coupon_code, user=user)
            return {
                'code': coupon.code,
                'discount_percentage': coupon.discount_percentage,
                'expiration_date': coupon.expiration_date,
                'is_used': coupon.is_used,
                'is_valid': coupon.is_valid(),
                'created_at': coupon.created_at,
                'proposal_id': getattr(coupon, 'proposal_id', None)
            }
        except DiscountCoupon.DoesNotExist:
            return None
