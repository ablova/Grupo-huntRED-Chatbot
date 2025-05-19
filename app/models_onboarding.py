"""
Modelos para el sistema de onboarding y satisfacción.
Estos serán importados por app/models.py
"""
from django.db import models
import json
from django.utils import timezone

class OnboardingProcess(models.Model):
    """Proceso de onboarding de un candidato contratado"""
    person = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='onboarding_processes')
    vacancy = models.ForeignKey('Vacante', on_delete=models.CASCADE, related_name='onboarding_processes')
    hire_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Activo'),
        ('completed', 'Completado'),
        ('terminated', 'Terminado Anticipadamente')
    ], default='active')
    last_survey_date = models.DateTimeField(null=True, blank=True)
    completed_surveys = models.IntegerField(default=0)
    survey_responses = models.TextField(null=True, blank=True)  # JSON almacenado
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_responses(self):
        """Retorna las respuestas como diccionario Python"""
        if not self.survey_responses:
            return {}
        try:
            return json.loads(self.survey_responses)
        except json.JSONDecodeError:
            return {}
    
    def set_responses(self, responses_dict):
        """Almacena diccionario como JSON"""
        self.survey_responses = json.dumps(responses_dict)
    
    def add_response(self, period_days, question_id, response_value):
        """Añade una respuesta específica de encuesta"""
        responses = self.get_responses()
        
        # Convertir período a string para uso como clave
        period_key = str(period_days)
        
        # Inicializar período si no existe
        if period_key not in responses:
            responses[period_key] = {}
        
        # Añadir respuesta con timestamp
        responses[period_key][question_id] = {
            "value": response_value,
            "timestamp": timezone.now().isoformat()
        }
        
        # Guardar actualizaciones
        self.set_responses(responses)
    
    def get_satisfaction_score(self, period_days=None):
        """Calcula puntaje de satisfacción (0-10) basado en respuestas"""
        responses = self.get_responses()
        
        if not responses:
            return None
        
        # Si se especifica periodo, calcular solo para ese
        if period_days:
            period_key = str(period_days)
            if period_key not in responses:
                return None
            period_data = responses[period_key]
        else:
            # Usar el último período disponible
            periods = sorted([int(p) for p in responses.keys()])
            if not periods:
                return None
            period_key = str(periods[-1])
            period_data = responses[period_key]
        
        # Mapeo de valores de respuesta a puntajes numéricos
        value_mappings = {
            # Para pregunta "feeling"
            "😀 Muy bien": 5.0,
            "🙂 Bien": 4.0,
            "😐 Neutral": 3.0,
            "😕 No muy bien": 2.0,
            "😟 Mal": 1.0,
            
            # Para otras preguntas tipo Likert
            "Completamente": 5.0,
            "Totalmente": 5.0,
            "En su mayoría": 4.0,
            "Bastante": 4.0,
            "Parcialmente": 3.0,
            "Algo": 3.0,
            "Poco": 2.0,
            "No cumple": 1.0,
            "Nada": 1.0
        }
        
        # Calcular promedio de puntajes numéricos
        scores = []
        for question_id, response in period_data.items():
            if isinstance(response, dict) and "value" in response:
                value = response["value"]
                if value in value_mappings:
                    scores.append(value_mappings[value])
        
        if not scores:
            return None
        
        # Convertir escala 1-5 a escala 0-10
        avg_score = sum(scores) / len(scores)
        return (avg_score - 1) * 2.5
    
    class Meta:
        verbose_name = "Proceso de Onboarding"
        verbose_name_plural = "Procesos de Onboarding"
        unique_together = ('person', 'vacancy')
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['hire_date']),
            models.Index(fields=['person', 'status'])
        ]

class OnboardingTask(models.Model):
    """Tarea específica en el proceso de onboarding"""
    onboarding = models.ForeignKey(OnboardingProcess, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateTimeField()
    completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(null=True, blank=True)
    assignee_type = models.CharField(max_length=20, choices=[
        ('candidate', 'Candidato'),
        ('manager', 'Manager'),
        ('hr', 'Recursos Humanos'),
        ('system', 'Sistema')
    ])
    priority = models.CharField(max_length=10, choices=[
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja')
    ], default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def mark_completed(self):
        """Marca la tarea como completada"""
        self.completed = True
        self.completed_date = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = "Tarea de Onboarding"
        verbose_name_plural = "Tareas de Onboarding"
        indexes = [
            models.Index(fields=['due_date']),
            models.Index(fields=['completed'])
        ]
        ordering = ['due_date', 'priority']

class OnboardingMilestone(models.Model):
    """Hito importante en el proceso de onboarding"""
    onboarding = models.ForeignKey(OnboardingProcess, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=100)
    description = models.TextField()
    target_date = models.DateTimeField()
    completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(null=True, blank=True)
    days_from_hire = models.IntegerField(help_text="Días desde contratación")
    
    class Meta:
        verbose_name = "Hito de Onboarding"
        verbose_name_plural = "Hitos de Onboarding"
        ordering = ['target_date']
