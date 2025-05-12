# Ubicacion SEXSI -- /home/pablo/app/sexsi/forms.py

from django import forms
from app.models import ConsentAgreement, Preference
from datetime import datetime

def calculate_age(birth_date):
    age = (datetime.now().date() - birth_date).days // 365
    return age

class ConsentAgreementForm(forms.ModelForm):
    """Formulario para la creación y validación del Acuerdo SEXSI."""
    
    class Meta:
        model = ConsentAgreement
        fields = [
            'invitee_contact', 
            'date_of_encounter', 
            'location', 
            'agreement_text', 
            'consensual_activities',
            'duration_type',
            'duration_amount',
            'duration_unit',
            'creator_date_of_birth',
            'creator_age_verified',
            'invitee_date_of_birth',
            'invitee_age_verified'
        ]
        widgets = {
            'date_of_encounter': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'agreement_text': forms.Textarea(attrs={'rows': 4}),
            'consensual_activities': forms.CheckboxSelectMultiple(),
            'duration_amount': forms.NumberInput(attrs={'min': 1}),
            'duration_unit': forms.Select(),
            'creator_date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'invitee_date_of_birth': forms.DateInput(attrs={'type': 'date'})
        }

    accept_tos = forms.BooleanField(required=True, label="Acepto los Términos de Servicio y la Política de Privacidad.")
    identity_document = forms.ImageField(required=True, label="Sube tu INE, Licencia o Pasaporte")
    full_name_verified = forms.CharField(max_length=255, required=True, label="Nombre Completo (como en tu Identificacion Oficial)")
    birthdate_verified = forms.DateField(required=True, label="Fecha de Nacimiento (DD/MM/AAAA)")
    is_conscious = forms.BooleanField(required=True, label="Confirmo que estoy en pleno uso de mis facultades")
    is_sober = forms.BooleanField(required=True, label="Confirmo que no he consumido alcohol o drogas en las últimas 6 horas")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['duration_type'].choices = ConsentAgreement.DURATION_CHOICES
        self.fields['duration_unit'].choices = [
            ('days', 'Días'),
            ('weeks', 'Semanas'),
            ('months', 'Meses'),
            ('years', 'Años')
        ]

    def clean(self):
        cleaned_data = super().clean()
        duration_type = cleaned_data.get('duration_type')
        duration_amount = cleaned_data.get('duration_amount')
        duration_unit = cleaned_data.get('duration_unit')

        if duration_type != 'single':
            if not duration_amount or not duration_unit:
                raise forms.ValidationError(
                    "Para acuerdos de corto o largo plazo, debes especificar la duración y la unidad de tiempo."
                )

        return cleaned_data

    def clean_birthdate_verified(self):
        """Validar que el usuario sea mayor de edad."""
        from datetime import datetime
        birth_date = self.cleaned_data['birthdate_verified']
        age = (datetime.now().date() - birth_date).days // 365
        if age < 18:
            raise forms.ValidationError("Debes ser mayor de edad para firmar este acuerdo.")
        return birth_date
