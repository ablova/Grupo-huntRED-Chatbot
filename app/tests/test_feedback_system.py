from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json

from ..models import FeedbackEntry
from ..ml.feedback.feedback_system import FeedbackAggregator, ModelRetrainer

class FeedbackSystemTest(TestCase):
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear algunos feedback de prueba
        self.feedback_data = {
            'candidate_id': 'test_candidate_1',
            'skill_id': 'python',
            'feedback_type': 'CORRECT',
            'confidence_score': 0.85,
            'original_prediction': {'score': 0.85, 'context': 'test'},
            'feedback_notes': 'Test feedback'
        }
        
        self.feedback = FeedbackEntry.objects.create(
            user=self.user,
            **self.feedback_data
        )

    def test_feedback_creation(self):
        """Prueba la creación de feedback"""
        self.assertEqual(self.feedback.user, self.user)
        self.assertEqual(self.feedback.skill_id, 'python')
        self.assertEqual(self.feedback.feedback_type, 'CORRECT')
        self.assertEqual(self.feedback.confidence_score, 0.85)

    def test_feedback_aggregator(self):
        """Prueba el agregador de feedback"""
        aggregator = FeedbackAggregator()
        
        # Crear más feedback para el mismo skill
        for i in range(15):  # Más del mínimo requerido
            FeedbackEntry.objects.create(
                user=self.user,
                candidate_id=f'test_candidate_{i}',
                skill_id='python',
                feedback_type='CORRECT',
                confidence_score=0.85,
                original_prediction={'score': 0.85, 'context': 'test'},
                feedback_notes=f'Test feedback {i}'
            )
        
        stats = aggregator.get_skill_feedback_stats('python')
        
        self.assertEqual(stats['status'], 'sufficient_data')
        self.assertGreaterEqual(stats['total_feedback'], 10)
        self.assertIn('accuracy', stats)
        self.assertIn('feedback_distribution', stats)

    def test_model_retrainer(self):
        """Prueba el re-entrenador de modelos"""
        retrainer = ModelRetrainer()
        
        # Crear suficiente feedback para re-entrenamiento
        for i in range(100):  # Mínimo para re-entrenamiento
            FeedbackEntry.objects.create(
                user=self.user,
                candidate_id=f'test_candidate_{i}',
                skill_id='python',
                feedback_type='CORRECT',
                confidence_score=0.85,
                original_prediction={'score': 0.85, 'context': 'test'},
                feedback_notes=f'Test feedback {i}'
            )
        
        # Probar preparación de datos
        training_data = retrainer.prepare_training_data('python')
        self.assertIn('features', training_data)
        self.assertIn('labels', training_data)
        self.assertIn('weights', training_data)
        
        # Probar re-entrenamiento
        result = retrainer.retrain_model('python')
        self.assertEqual(result['status'], 'success')
        self.assertIn('samples_used', result)
        self.assertIn('training_metrics', result)

    def test_feedback_types(self):
        """Prueba diferentes tipos de feedback"""
        feedback_types = [ft[0] for ft in FeedbackEntry.FEEDBACK_TYPES]
        
        for feedback_type in feedback_types:
            feedback = FeedbackEntry.objects.create(
                user=self.user,
                candidate_id='test_candidate',
                skill_id='python',
                feedback_type=feedback_type,
                confidence_score=0.85,
                original_prediction={'score': 0.85, 'context': 'test'},
                feedback_notes=f'Test {feedback_type} feedback'
            )
            
            self.assertEqual(feedback.feedback_type, feedback_type)

    def test_feedback_window(self):
        """Prueba la ventana de tiempo del feedback"""
        # Crear feedback antiguo
        old_feedback = FeedbackEntry.objects.create(
            user=self.user,
            candidate_id='old_candidate',
            skill_id='python',
            feedback_type='CORRECT',
            confidence_score=0.85,
            original_prediction={'score': 0.85, 'context': 'test'},
            feedback_notes='Old feedback',
            created_at=timezone.now() - timedelta(days=31)
        )
        
        aggregator = FeedbackAggregator()
        stats = aggregator.get_skill_feedback_stats('python')
        
        # El feedback antiguo no debería contar
        self.assertEqual(stats['total_feedback'], 1)  # Solo el feedback nuevo

    def test_feedback_validation(self):
        """Prueba la validación de datos de feedback"""
        # Intentar crear feedback con datos inválidos
        with self.assertRaises(Exception):
            FeedbackEntry.objects.create(
                user=self.user,
                candidate_id='test_candidate',
                skill_id='python',
                feedback_type='INVALID_TYPE',  # Tipo inválido
                confidence_score=0.85,
                original_prediction={'score': 0.85, 'context': 'test'},
                feedback_notes='Test feedback'
            ) 