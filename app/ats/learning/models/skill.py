"""
Modelo para skills en el sistema de aprendizaje.
"""
from django.db import models
from app.models import BusinessUnit

class Skill(models.Model):
    """Modelo para skills."""
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    description = models.TextField()
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('name', 'business_unit')
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['business_unit'])
        ]
    
    def __str__(self):
        return f"{self.name} ({self.category})" 