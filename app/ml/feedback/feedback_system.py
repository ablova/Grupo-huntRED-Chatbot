from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import numpy as np
from typing import Dict, List, Optional
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class FeedbackEntry(models.Model):
    """Modelo para almacenar feedback de usuarios sobre predicciones de skills"""
    FEEDBACK_TYPES = [
        ('CORRECT', 'Predicción Correcta'),
        ('INCORRECT', 'Predicción Incorrecta'),
        ('PARTIAL', 'Predicción Parcialmente Correcta'),
        ('MISSING', 'Skill No Detectado'),
        ('EXTRA', 'Skill Detectado Incorrectamente')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    candidate_id = models.CharField(max_length=100)
    skill_id = models.CharField(max_length=100)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    confidence_score = models.FloatField()
    original_prediction = models.JSONField()
    feedback_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['skill_id']),
            models.Index(fields=['feedback_type']),
            models.Index(fields=['created_at'])
        ]

class FeedbackAggregator:
    """Clase para agregar y analizar feedback"""
    
    def __init__(self):
        self.feedback_window = 30  # días
        self.min_feedback_threshold = 10
        self.confidence_threshold = 0.7

    def get_skill_feedback_stats(self, skill_id: str) -> Dict:
        """Obtiene estadísticas de feedback para un skill específico"""
        recent_feedback = FeedbackEntry.objects.filter(
            skill_id=skill_id,
            created_at__gte=timezone.now() - timezone.timedelta(days=self.feedback_window)
        )

        total = recent_feedback.count()
        if total < self.min_feedback_threshold:
            return {
                'status': 'insufficient_data',
                'total_feedback': total,
                'required_feedback': self.min_feedback_threshold
            }

        feedback_counts = {
            feedback_type: recent_feedback.filter(feedback_type=feedback_type).count()
            for feedback_type, _ in FeedbackEntry.FEEDBACK_TYPES
        }

        accuracy = (feedback_counts['CORRECT'] + 0.5 * feedback_counts['PARTIAL']) / total

        return {
            'status': 'sufficient_data',
            'total_feedback': total,
            'accuracy': accuracy,
            'feedback_distribution': feedback_counts,
            'needs_retraining': accuracy < self.confidence_threshold
        }

class ModelRetrainer:
    """Clase para manejar el re-entrenamiento de modelos basado en feedback"""
    
    def __init__(self):
        self.retraining_threshold = 0.7
        self.min_samples_for_retraining = 100
        self.batch_size = 32

    def should_retrain(self, skill_id: str) -> bool:
        """Determina si un modelo necesita re-entrenamiento"""
        aggregator = FeedbackAggregator()
        stats = aggregator.get_skill_feedback_stats(skill_id)
        
        if stats['status'] == 'insufficient_data':
            return False
            
        return (stats['needs_retraining'] and 
                stats['total_feedback'] >= self.min_samples_for_retraining)

    def prepare_training_data(self, skill_id: str) -> Dict:
        """Prepara datos para re-entrenamiento basado en feedback"""
        feedback_entries = FeedbackEntry.objects.filter(
            skill_id=skill_id,
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).order_by('-created_at')

        training_data = {
            'features': [],
            'labels': [],
            'weights': []
        }

        for entry in feedback_entries:
            # Convertir feedback a etiquetas de entrenamiento
            if entry.feedback_type == 'CORRECT':
                label = 1
                weight = 1.0
            elif entry.feedback_type == 'PARTIAL':
                label = 1
                weight = 0.5
            else:
                label = 0
                weight = 1.0

            training_data['features'].append(entry.original_prediction)
            training_data['labels'].append(label)
            training_data['weights'].append(weight)

        return training_data

    def retrain_model(self, skill_id: str) -> Dict:
        """Ejecuta el re-entrenamiento del modelo"""
        if not self.should_retrain(skill_id):
            return {
                'status': 'skipped',
                'reason': 'No cumple criterios de re-entrenamiento'
            }

        try:
            training_data = self.prepare_training_data(skill_id)
            
            # Aquí iría la lógica de re-entrenamiento específica
            # Por ahora solo simulamos el proceso
            
            return {
                'status': 'success',
                'samples_used': len(training_data['features']),
                'training_metrics': {
                    'accuracy': 0.85,  # Simulado
                    'precision': 0.82,  # Simulado
                    'recall': 0.88     # Simulado
                }
            }
        except Exception as e:
            logger.error(f"Error en re-entrenamiento para skill {skill_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            } 