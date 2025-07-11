# app/ats/forms/workflow_forms.py
"""
Formularios para workflows del sistema ATS.
"""

from django import forms
from django.core.exceptions import ValidationError
from typing import Dict, Any, Optional


class WorkflowStageForm(forms.Form):
    """
    Formulario para gestionar etapas de workflow.
    """
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de la etapa'
        }),
        help_text='Nombre descriptivo de la etapa del workflow'
    )
    
    description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descripción de la etapa'
        }),
        help_text='Descripción detallada de la etapa'
    )
    
    order = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Orden'
        }),
        help_text='Orden de la etapa en el workflow'
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Indica si la etapa está activa'
    )
    
    estimated_duration = forms.IntegerField(
        min_value=1,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Duración estimada (días)'
        }),
        help_text='Duración estimada en días'
    )
    
    required_skills = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Habilidades requeridas (separadas por comas)'
        }),
        help_text='Habilidades requeridas para esta etapa'
    )
    
    auto_advance = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Avance automático a la siguiente etapa'
    )
    
    notification_template = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Plantilla de notificación'
        }),
        help_text='Plantilla para notificaciones de esta etapa'
    )
    
    def clean_name(self):
        """
        Validación personalizada para el nombre.
        """
        name = self.cleaned_data['name']
        if len(name.strip()) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres.')
        return name.strip()
    
    def clean_order(self):
        """
        Validación personalizada para el orden.
        """
        order = self.cleaned_data['order']
        if order < 1:
            raise ValidationError('El orden debe ser mayor a 0.')
        return order
    
    def clean_estimated_duration(self):
        """
        Validación personalizada para la duración estimada.
        """
        duration = self.cleaned_data.get('estimated_duration')
        if duration is not None and duration < 1:
            raise ValidationError('La duración estimada debe ser mayor a 0.')
        return duration
    
    def clean_required_skills(self):
        """
        Validación personalizada para las habilidades requeridas.
        """
        skills = self.cleaned_data.get('required_skills', '')
        if skills:
            # Limpiar y validar habilidades
            skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
            if len(skills_list) > 20:
                raise ValidationError('No se pueden especificar más de 20 habilidades.')
            return ', '.join(skills_list)
        return skills
    
    def get_skills_list(self) -> list:
        """
        Obtiene la lista de habilidades como una lista.
        """
        skills = self.cleaned_data.get('required_skills', '')
        if skills:
            return [skill.strip() for skill in skills.split(',') if skill.strip()]
        return []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el formulario a un diccionario.
        """
        if self.is_valid():
            data = self.cleaned_data.copy()
            data['required_skills'] = self.get_skills_list()
            return data
        return {}
    
    class Meta:
        """
        Metadatos del formulario.
        """
        fields = [
            'name', 'description', 'order', 'is_active',
            'estimated_duration', 'required_skills', 'auto_advance',
            'notification_template'
        ] 