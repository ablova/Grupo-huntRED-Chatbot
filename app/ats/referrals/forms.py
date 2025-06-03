from django import forms
from .models import ReferralProgram

class ReferralForm(forms.ModelForm):
    class Meta:
        model = ReferralProgram
        fields = ['referred_company', 'commission_percentage']
        widgets = {
            'referred_company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa referida'
            }),
            'commission_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '20',
                'step': '0.5'
            })
        }

    def clean_commission_percentage(self):
        commission = self.cleaned_data.get('commission_percentage')
        if commission < 1 or commission > 20:
            raise forms.ValidationError(
                'El porcentaje de comisión debe estar entre 1% y 20%'
            )
        return commission

    def clean_referred_company(self):
        company = self.cleaned_data.get('referred_company')
        if ReferralProgram.objects.filter(
            referred_company=company,
            status=True
        ).exists():
            raise forms.ValidationError(
                'Ya existe una referencia activa para esta empresa'
            )
        return company 