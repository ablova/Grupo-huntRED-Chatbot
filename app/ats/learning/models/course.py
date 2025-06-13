"""
Modelo para cursos en el sistema de aprendizaje.
"""
from django.db import models
from app.models import BusinessUnit, Skill

class Course(models.Model):
    """Modelo para cursos."""
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    provider = models.CharField(max_length=100)
    url = models.URLField()
    skills = models.ManyToManyField(Skill, related_name='courses')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    # Metadatos
    duration = models.DurationField()
    level = models.CharField(max_length=20)
    rating = models.FloatField(default=0.0)
    reviews_count = models.IntegerField(default=0)
    
    # Precios
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Estado
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['provider']),
            models.Index(fields=['business_unit']),
            models.Index(fields=['is_active'])
        ]
    
    def __str__(self):
        return f"{self.name} ({self.provider})" 