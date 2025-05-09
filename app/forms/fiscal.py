from django import forms
from app.models import Person

class FiscalDataForm(forms.ModelForm):
    rfc = forms.CharField(
        max_length=13,
        label='RFC',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    razon_social = forms.CharField(
        max_length=255,
        label='Razón Social',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    direccion_fiscal = forms.CharField(
        label='Dirección Fiscal',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    class Meta:
        model = Person
        fields = ['rfc', 'razon_social', 'direccion_fiscal']
        
    def clean_rfc(self):
        rfc = self.cleaned_data.get('rfc')
        if not rfc:
            raise forms.ValidationError('Este campo es requerido')
        return rfc.upper()
