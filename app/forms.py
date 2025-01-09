# /home/pablollh/app/forms.py

from django import forms
from app.models import WorkflowStage

class WorkflowStageForm(forms.ModelForm):
    class Meta:
        model = WorkflowStage
        fields = ['name', 'description']  # Ajusta los campos según tu modelo 