from django.db import models
from django.utils import timezone
from app.models import Person, Vacante, BusinessUnit

class CandidatePreselection(models.Model):
    """
    Modelo para manejar las pre-selecciones de candidatos y su feedback.
    """
    STATUS_CHOICES = [
        ('pending_review', 'Pendiente de Revisión'),
        ('mp_reviewed', 'Revisado por MP'),
        ('client_sent', 'Enviado al Cliente'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado')
    ]

    vacancy = models.ForeignKey(Vacante, on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_review')
    
    # Datos de la pre-selección
    preselection_data = models.JSONField()
    
    # Feedback del MP
    mp_feedback = models.JSONField(null=True, blank=True)
    mp_notes = models.TextField(null=True, blank=True)
    
    # Candidatos finales seleccionados
    final_candidates = models.ManyToManyField(Person, related_name='preselections')
    
    # Aprendizaje del sistema
    learning_insights = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vacancy', 'status']),
            models.Index(fields=['business_unit', 'status']),
            models.Index(fields=['created_at'])
        ]

    def __str__(self):
        return f"Pre-selección para {self.vacancy.titulo} ({self.get_status_display()})"

    def get_candidates(self):
        """
        Obtiene los candidatos de la pre-selección.
        """
        return self.preselection_data.get('candidates', [])

    def get_selected_candidates(self):
        """
        Obtiene los candidatos seleccionados por el MP.
        """
        if not self.mp_feedback:
            return []
        return self.final_candidates.all()

    def get_rejected_candidates(self):
        """
        Obtiene los candidatos rechazados por el MP.
        """
        if not self.mp_feedback:
            return []
        selected_ids = set(self.mp_feedback.get('selected_candidates', []))
        return [c for c in self.get_candidates() if c['id'] not in selected_ids]

    def get_learning_points(self):
        """
        Obtiene los puntos de aprendizaje del sistema.
        """
        return self.learning_insights or {}

    def update_status(self, new_status: str, notes: str = None):
        """
        Actualiza el estado de la pre-selección.
        """
        if new_status not in dict(self.STATUS_CHOICES):
            raise ValueError(f"Estado inválido: {new_status}")
            
        self.status = new_status
        if new_status == 'mp_reviewed':
            self.reviewed_at = timezone.now()
        if notes:
            self.mp_notes = notes
        self.save()

    def add_mp_feedback(self, feedback: dict):
        """
        Agrega el feedback del MP.
        """
        self.mp_feedback = feedback
        self.status = 'mp_reviewed'
        self.reviewed_at = timezone.now()
        self.save()

    def add_learning_insights(self, insights: dict):
        """
        Agrega insights de aprendizaje del sistema.
        """
        self.learning_insights = insights
        self.save() 