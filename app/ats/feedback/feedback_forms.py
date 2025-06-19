# /home/pablo/app/com/pricing/feedback_forms.py
"""
Formularios para el sistema de retroalimentación de propuestas de Grupo huntRED®.

Este módulo contiene los formularios necesarios para capturar retroalimentación 
sobre las propuestas enviadas, entender por qué los clientes contratan o no los 
servicios, y facilitar la programación de reuniones con el Managing Director.
"""

from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.forms.widgets import TextInput, Textarea, Select, CheckboxInput, NumberInput, RadioSelect

from app.ats.pricing.models.feedback import ProposalFeedback, MeetingRequest


class ProposalFeedbackForm(forms.ModelForm):
    """
    Formulario para capturar retroalimentación sobre propuestas enviadas.
    
    Este formulario está diseñado para ser lo más sencillo posible para maximizar
    las respuestas, con campos estratégicos que nos permiten entender mejor por qué
    los clientes contratan o no nuestros servicios.
    """
    
    # Campo oculto para el token de seguridad
    token = forms.CharField(widget=forms.HiddenInput())
    
    # Retroalimentación inicial simplificada
    response_type = forms.ChoiceField(
        label="¿Cuál es su interés en nuestro servicio de Análisis de Talento 360°?",
        choices=ProposalFeedback.RESPONSE_CHOICES,
        widget=RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    # Formulario condicional - solo aparece si no están interesados
    rejection_reason = forms.ChoiceField(
        label="¿Cuál es la principal razón por la que no contratará el servicio ahora?",
        choices=ProposalFeedback.REJECTION_REASONS,
        required=False,
        widget=Select(attrs={'class': 'form-select'})
    )
    
    # Información adicional valiosa
    how_found_us = forms.ChoiceField(
        label="¿Cómo conoció a Grupo huntRED®?",
        choices=ProposalFeedback.SOURCE_CHOICES,
        required=False,
        widget=Select(attrs={'class': 'form-select'})
    )
    
    price_perception = forms.IntegerField(
        label="¿Cómo percibe nuestros precios? (1: Muy accesible, 5: Muy costoso)",
        min_value=1,
        max_value=5,
        required=False,
        widget=forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)],
                                attrs={'class': 'form-check-inline'})
    )
    
    missing_info = forms.CharField(
        label="¿Qué información adicional habría sido útil incluir en nuestra propuesta?",
        required=False,
        widget=Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    
    improvement_suggestions = forms.CharField(
        label="¿Tiene alguna sugerencia para mejorar nuestra propuesta o servicio?",
        required=False,
        widget=Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    
    # Opción para solicitar una reunión con el Managing Director
    meeting_requested = forms.BooleanField(
        label="Me gustaría una reunión personal con Pablo Lelo de Larrea H. (Managing Partner)",
        required=False,
        initial=False,
        widget=CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = ProposalFeedback
        fields = [
            'token', 'response_type', 'rejection_reason', 
            'how_found_us', 'price_perception', 'missing_info',
            'improvement_suggestions', 'meeting_requested'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer que algunos campos sean opcionales para aumentar tasa de respuesta
        optional_fields = ['how_found_us', 'price_perception', 'missing_info', 'improvement_suggestions']
        for field in optional_fields:
            self.fields[field].required = False
        
        # Añadir textos explicativos
        self.fields['response_type'].help_text = "Esta información nos ayudará a entender mejor sus necesidades."
        self.fields['meeting_requested'].help_text = "Nuestro Managing Partner estará encantado de resolver personalmente cualquier duda sobre el servicio."


class MeetingRequestForm(forms.ModelForm):
    """
    Formulario para programar una reunión con el Managing Director.
    
    Este formulario aparece cuando un cliente solicita una reunión en el formulario
    de retroalimentación, permitiéndoles elegir fecha, hora y tema para la reunión.
    """
    
    # Campos específicos para la reunión
    preferred_date = forms.DateField(
        label="Fecha preferida",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text="Seleccione su fecha preferida para la reunión"
    )
    
    preferred_time_range = forms.ChoiceField(
        label="Horario preferido",
        choices=[
            ('morning', 'Mañana (9:00 - 12:00)'),
            ('afternoon', 'Tarde (12:00 - 17:00)'),
            ('evening', 'Tarde-Noche (17:00 - 20:00)'),
        ],
        widget=Select(attrs={'class': 'form-select'})
    )
    
    meeting_type = forms.ChoiceField(
        label="Tema principal de la reunión",
        choices=MeetingRequest.MEETING_TYPES,
        widget=Select(attrs={'class': 'form-select'})
    )
    
    notes = forms.CharField(
        label="Temas específicos que le gustaría tratar",
        required=False,
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3, 
                               'placeholder': 'Indique cualquier tema específico que le gustaría discutir en la reunión'})
    )
    
    # Campos adicionales para asegurar que tenemos la información correcta
    contact_phone = forms.CharField(
        label="Teléfono de contacto",
        required=True,
        widget=TextInput(attrs={'class': 'form-control', 
                               'placeholder': 'Para confirmación de la reunión'})
    )
    
    class Meta:
        model = MeetingRequest
        fields = [
            'meeting_type', 'preferred_date', 'preferred_time_range',
            'contact_phone', 'notes'
        ]
    
    def clean_preferred_date(self):
        date = self.cleaned_data.get('preferred_date')
        today = timezone.now().date()
        
        # Verificar que la fecha sea futura
        if date < today:
            raise ValidationError("Por favor seleccione una fecha futura.")
        
        # Verificar que no sea fin de semana
        if date.weekday() >= 5:  # 5=Sábado, 6=Domingo
            raise ValidationError("Por favor seleccione un día entre semana (Lunes a Viernes).")
        
        return date
        
    def __init__(self, *args, **kwargs):
        # Extraer datos del cliente si se proporcionan
        client_data = kwargs.pop('client_data', None)
        super().__init__(*args, **kwargs)
        
        # Pre-llenar campos si tenemos la información del cliente
        if client_data:
            if 'contact_phone' in client_data:
                self.fields['contact_phone'].initial = client_data['contact_phone']
