# /home/pablo/app/ats/learning/models/enrollment.py
from app.ats.learning.models.course import Course
from app.ats.learning.models.learning_path import LearningPath, LearningPathStep

from app.models import Skill

__all__ = [
    'Course',
    'LearningPath',
    'LearningPathStep',
    'Enrollment',
    'Skill'
] 
"""
Modelo para manejar las inscripciones a cursos.
"""
from django.db import models
from django.utils import timezone
from app.models import User, BusinessUnit
from .course import Course

class Enrollment(models.Model):
    """Modelo para inscripciones a cursos."""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('active', 'Activo'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('expired', 'Expirado')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.FloatField(default=0.0)
    score = models.FloatField(null=True, blank=True)
    
    # Fechas
    enrolled_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    certificate_url = models.URLField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'course']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['course']),
            models.Index(fields=['business_unit']),
            models.Index(fields=['status']),
            models.Index(fields=['enrolled_at']),
            models.Index(fields=['expires_at'])
        ]
    
    def __str__(self):
        return f"{self.user} - {self.course}"
    
    def save(self, *args, **kwargs):
        # Si el estado cambia a 'active', establecer started_at
        if self.status == 'active' and not self.started_at:
            self.started_at = timezone.now()
        
        # Si el estado cambia a 'completed', establecer completed_at
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            self.progress = 100.0
        
        super().save(*args, **kwargs) 