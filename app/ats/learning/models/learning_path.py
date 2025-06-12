"""
Modelo para rutas de aprendizaje.
"""
from django.db import models
from app.models import BusinessUnit, User
from .skill import Skill
from .course import Course

class LearningPath(models.Model):
    """Modelo para rutas de aprendizaje."""
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    # Metadatos
    target_skills = models.ManyToManyField(Skill, related_name='learning_paths')
    estimated_duration = models.DurationField()
    difficulty = models.CharField(max_length=20)
    
    # Estado
    status = models.CharField(max_length=20, default='pending')
    progress = models.FloatField(default=0.0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['user']),
            models.Index(fields=['business_unit']),
            models.Index(fields=['status'])
        ]
    
    def __str__(self):
        return f"{self.name} - {self.user}"

class LearningPathStep(models.Model):
    """Modelo para pasos en una ruta de aprendizaje."""
    
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='steps')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order = models.IntegerField()
    
    # Estado
    status = models.CharField(max_length=20, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['learning_path']),
            models.Index(fields=['course']),
            models.Index(fields=['status'])
        ]
    
    def __str__(self):
        return f"{self.learning_path} - Step {self.order}" 