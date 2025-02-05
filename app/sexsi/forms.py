# Ubicacion SEXSI -- /home/pablollh/app/sexsi/forms.py

from django import forms
from app.sexsi.models import ConsentAgreement

class ConsentAgreementForm(forms.ModelForm):
    class Meta:
        model = ConsentAgreement
        fields = ['invitee_contact', 'date_of_encounter', 'location', 'agreement_text']
        widgets = {
            'date_of_encounter': forms.DateInput(attrs={'type': 'date'}),
            'agreement_text': forms.Textarea(attrs={'rows': 4}),
        }