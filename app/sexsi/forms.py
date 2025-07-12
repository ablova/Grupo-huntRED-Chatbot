# Ubicacion SEXSI -- /home/pablo/app/sexsi/forms.py

from django import forms
from app.sexsi.models import ConsentAgreement, Preference
from datetime import datetime

def calculate_age(birth_date):
    age = (datetime.now().date() - birth_date).days // 365
    return age

class ConsentAgreementForm(forms.ModelForm):
    """Formulario para la creación y validación del Acuerdo SEXSI."""
    
    class Meta:
        model = ConsentAgreement
        fields = [
            'date_of_encounter', 
            'location', 
            'agreement_text',
            'duration_type',
            'duration_amount',
            'duration_unit',
            'creator_full_name_verified',
            'creator_birthdate_verified',
            'creator_is_conscious',
            'creator_is_sober',
            'invitee_contact',
            'consensual_activities'
        ]
        widgets = {
            'date_of_encounter': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'agreement_text': forms.Textarea(attrs={'rows': 4}),
            'creator_birthdate_verified': forms.DateInput(attrs={'type': 'date'}),
            'consensual_activities': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    # Campos adicionales para validación
    accept_tos = forms.BooleanField(required=True, label="Acepto los Términos de Servicio y la Política de Privacidad.")
    identity_document = forms.ImageField(required=True, label="Sube tu INE, Licencia o Pasaporte")

    def clean_creator_birthdate_verified(self):
        """Validar que el usuario sea mayor de edad."""
        from datetime import datetime
        birth_date = self.cleaned_data['creator_birthdate_verified']
        if birth_date:
            age = (datetime.now().date() - birth_date).days // 365
            if age < 18:
                raise forms.ValidationError("Debes ser mayor de edad para firmar este acuerdo.")
        return birth_date
