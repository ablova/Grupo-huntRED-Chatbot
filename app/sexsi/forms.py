# Ubicacion SEXSI -- /home/pablo/app/sexsi/forms.py

from django import forms
from app.sexsi.models import ConsentAgreement

class ConsentAgreementForm(forms.ModelForm):
    """Formulario para la creación y validación del Acuerdo SEXSI."""
    
    class Meta:
        model = ConsentAgreement
        fields = ['invitee_contact', 'date_of_encounter', 'location', 'agreement_text', 'consensual_activities']
        widgets = {
            'date_of_encounter': forms.DateInput(attrs={'type': 'date'}),
            'agreement_text': forms.Textarea(attrs={'rows': 4}),
            'consensual_activities': forms.CheckboxSelectMultiple()
        }

    accept_tos = forms.BooleanField(required=True, label="Acepto los Términos de Servicio y la Política de Privacidad.")
    identity_document = forms.ImageField(required=True, label="Sube tu INE, Licencia o Pasaporte")
    full_name_verified = forms.CharField(max_length=255, required=True, label="Nombre Completo (como en tu Identificacion Oficial)")
    birthdate_verified = forms.DateField(required=True, label="Fecha de Nacimiento (DD/MM/AAAA)")
    is_conscious = forms.BooleanField(required=True, label="Confirmo que estoy en pleno uso de mis facultades")
    is_sober = forms.BooleanField(required=True, label="Confirmo que no he consumido alcohol o drogas en las últimas 6 horas")

    def clean_birthdate_verified(self):
        """Validar que el usuario sea mayor de edad."""
        from datetime import datetime
        birth_date = self.cleaned_data['birthdate_verified']
        age = (datetime.now().date() - birth_date).days // 365
        if age < 18:
            raise forms.ValidationError("Debes ser mayor de edad para firmar este acuerdo.")
        return birth_date
