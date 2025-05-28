from django.db import models
from django.utils import timezone
from typing import List, Optional
import logging

from app.models import Person, BusinessUnit

logger = logging.getLogger(__name__)

class OnboardingProcess(models.Model):
    """
    Modelo para gestionar el proceso de onboarding de un candidato.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado')
    ]
    
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='onboarding_processes'
    )
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='onboarding_processes'
    )
    
    start_date = models.DateTimeField(
        default=timezone.now,
        help_text='Fecha de inicio del proceso de onboarding'
    )
    
    completion_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha de finalización del proceso de onboarding'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Estado actual del proceso de onboarding'
    )
    
    completed_steps = models.JSONField(
        default=list,
        help_text='Lista de pasos completados en el proceso'
    )
    
    check_ins = models.JSONField(
        default=list,
        help_text='Registro de check-ins realizados'
    )
    
    feedback_data = models.JSONField(
        default=dict,
        help_text='Datos de feedback recopilados durante el proceso'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Proceso de Onboarding'
        verbose_name_plural = 'Procesos de Onboarding'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Onboarding de {self.person.nombre} - {self.status}"
    
    async def complete_step(self, step: str) -> bool:
        """
        Marca un paso como completado en el proceso de onboarding.
        """
        try:
            if step not in self.completed_steps:
                self.completed_steps.append(step)
                await self.asave()
            return True
        except Exception as e:
            logger.error(f"Error completing step: {str(e)}")
            return False
    
    async def register_check_in(self) -> bool:
        """
        Registra un nuevo check-in en el proceso.
        """
        try:
            check_in = {
                'date': timezone.now().isoformat(),
                'status': self.status,
                'completed_steps': self.completed_steps
            }
            self.check_ins.append(check_in)
            await self.asave()
            return True
        except Exception as e:
            logger.error(f"Error registering check-in: {str(e)}")
            return False
    
    async def get_check_in_count(self) -> int:
        """
        Obtiene el número total de check-ins realizados.
        """
        return len(self.check_ins)
    
    async def add_feedback(self, feedback_type: str, data: dict) -> bool:
        """
        Agrega datos de feedback al proceso.
        """
        try:
            if feedback_type not in self.feedback_data:
                self.feedback_data[feedback_type] = []
            self.feedback_data[feedback_type].append({
                'date': timezone.now().isoformat(),
                'data': data
            })
            await self.asave()
            return True
        except Exception as e:
            logger.error(f"Error adding feedback: {str(e)}")
            return False
    
    async def get_latest_feedback(self, feedback_type: str) -> Optional[dict]:
        """
        Obtiene el feedback más reciente de un tipo específico.
        """
        try:
            if feedback_type in self.feedback_data and self.feedback_data[feedback_type]:
                return self.feedback_data[feedback_type][-1]
            return None
        except Exception as e:
            logger.error(f"Error getting latest feedback: {str(e)}")
            return None 