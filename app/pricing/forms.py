"""
Formularios para el módulo de precios.
"""
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import DiscountCoupon, TeamEvaluation, PromotionBanner


class DiscountCouponForm(forms.ModelForm):
    """Formulario para crear/editar cupones de descuento."""
    class Meta:
        model = DiscountCoupon
        fields = [
            'code', 'discount_percentage', 'description', 'expiration_date',
            'max_uses', 'user'
        ]
        widgets = {
            'expiration_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].required = False
        self.fields['expiration_date'].input_formats = ['%Y-%m-%dT%H:%M']
        
        # Establecer la fecha mínima como la fecha actual
        now = timezone.now()
        self.fields['expiration_date'].widget.attrs['min'] = now.strftime('%Y-%m-%dT%H:%M')
        
        # Si es una edición, establecer la fecha actual como mínimo
        if self.instance and self.instance.pk:
            self.fields['code'].disabled = True
    
    def clean_expiration_date(self):
        """Valida que la fecha de expiración sea futura."""
        expiration_date = self.cleaned_data.get('expiration_date')
        if expiration_date and expiration_date <= timezone.now():
            raise ValidationError('La fecha de expiración debe ser futura')
        return expiration_date
    
    def clean_discount_percentage(self):
        """Valida que el porcentaje de descuento esté entre 1 y 100."""
        discount = self.cleaned_data.get('discount_percentage')
        if discount < 1 or discount > 100:
            raise ValidationError('El porcentaje debe estar entre 1 y 100')
        return discount


class TeamEvaluationRequestForm(forms.Form):
    """Formulario para solicitar una evaluación de equipo."""
    team_size = forms.IntegerField(
        label='Tamaño del equipo',
        min_value=1,
        max_value=100,
        help_text='Número de miembros del equipo a evaluar',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    notes = forms.CharField(
        label='Notas adicionales',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Información adicional sobre tu equipo...'
        })
    )


class TeamEvaluationCompleteForm(forms.ModelForm):
    """Formulario para completar una evaluación de equipo."""
    class Meta:
        model = TeamEvaluation
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Detalles sobre la evaluación de tu equipo...'
            })
        }


class PromotionBannerForm(forms.ModelForm):
    """Formulario para crear/editar banners promocionales."""
    class Meta:
        model = PromotionBanner
        fields = [
            'title', 'subtitle', 'content', 'image', 'is_active', 'priority',
            'start_date', 'end_date', 'button_text', 'target_url', 'badge_text',
            'badge_style'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'content': forms.Textarea(attrs={'rows': 4}),
            'badge_style': forms.Select(choices=PromotionBanner.BADGE_STYLE_CHOICES),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_date'].input_formats = ['%Y-%m-%dT%H:%M']
        
        # Establecer la fecha mínima como la fecha actual
        now = timezone.now()
        self.fields['start_date'].widget.attrs['min'] = now.strftime('%Y-%m-%dT%H:%M')
        self.fields['end_date'].widget.attrs['min'] = now.strftime('%Y-%m-%dT%H:%M')
    
    def clean(self):
        """Valida que las fechas sean coherentes."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError({
                'end_date': 'La fecha de finalización debe ser posterior a la de inicio'
            })
        
        return cleaned_data


class ApplyCouponForm(forms.Form):
    """Formulario para aplicar un cupón de descuento."""
    code = forms.CharField(
        label='Código de descuento',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu código de descuento...'
        })
    )
    
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_code(self):
        """Valida el código de descuento."""
        from .models import DiscountCoupon
        
        code = self.cleaned_data.get('code')
        if not code:
            return code
            
        try:
            coupon = DiscountCoupon.objects.get(
                code__iexact=code,
                is_used=False,
                expiration_date__gt=timezone.now()
            )
            
            # Verificar si el cupón ha alcanzado el máximo de usos
            if coupon.use_count >= coupon.max_uses:
                raise ValidationError('Este cupón ha alcanzado su límite de usos')
                
            # Verificar si el cupón es de un solo uso y ya fue usado por el usuario
            if coupon.max_uses == 1 and coupon.user and coupon.user != self.user:
                raise ValidationError('Este cupón no es válido para tu cuenta')
                
            return coupon
            
        except DiscountCoupon.DoesNotExist:
            raise ValidationError('Código de descuento no válido o expirado')
        except Exception as e:
            raise ValidationError('Error al validar el cupón. Por favor, inténtalo de nuevo.')
