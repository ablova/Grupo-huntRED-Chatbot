import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from app.models import Person, Vacante, Application
from app.ml.monitoring.metrics import ATSMetrics
from datetime import datetime, timedelta

class TestATSMetrics(unittest.TestCase):
    def setUp(self):
        self.person = Person(
            id=1,
            skills_text="Python, Machine Learning, Data Science",
            years_of_experience=5,
            education_level=4,
            current_vacancy=None
        )

        self.vacancy = Vacante(
            id=1,
            title="Data Scientist",
            description="Senior Data Scientist position",
            required_experience=5,
            required_education=4,
            salary_range=100000,
            location_score=0.9,
            industry="Technology",
            level="Senior",
            main_skill="Python",
            activa=True
        )

        self.application = Application(
            id=1,
            person=self.person,
            vacancy=self.vacancy,
            status="contratado",
            date_applied=datetime.now() - timedelta(days=10),
            date_hired=datetime.now()
        )

    def test_calculate_model_metrics(self):
        """Test de cálculo de métricas del modelo"""
        metrics = ATSMetrics()
        
        # Datos de prueba
        y_true = np.array([1, 0, 1, 1, 0])
        y_pred = np.array([0.9, 0.2, 0.8, 0.7, 0.3])
        
        # Calcular métricas
        model_metrics = metrics.calculate_model_metrics(y_true, y_pred)
        
        # Verificar métricas
        self.assertIn('accuracy', model_metrics)
        self.assertIn('precision', model_metrics)
        self.assertIn('recall', model_metrics)
        self.assertIn('f1_score', model_metrics)
        self.assertIn('roc_auc', model_metrics)

    def test_calculate_business_metrics(self):
        """Test de cálculo de métricas de negocio"""
        metrics = ATSMetrics()
        
        # Simular aplicaciones
        applications = [self.application]
        
        # Calcular métricas
        business_metrics = metrics.calculate_business_metrics(applications)
        
        # Verificar métricas
        self.assertIn('time_to_hire', business_metrics)
        self.assertIn('match_rate', business_metrics)
        self.assertIn('transition_success_rate', business_metrics)
        self.assertIn('application_conversion_rate', business_metrics)

    def test_generate_dashboard_data(self):
        """Test de generación de datos para dashboard"""
        metrics = ATSMetrics()
        
        # Simular aplicaciones
        applications = [self.application]
        
        # Generar datos
        dashboard_data = metrics.generate_dashboard_data()
        
        # Verificar estructura
        self.assertIn('timestamp', dashboard_data)
        self.assertIn('system_metrics', dashboard_data)
        self.assertIn('business_metrics', dashboard_data)
        self.assertIn('model_performance', dashboard_data)

    def test_time_to_hire(self):
        """Test de cálculo de tiempo de contratación"""
        metrics = ATSMetrics()
        
        # Simular aplicaciones
        applications = [self.application]
        
        # Calcular tiempo
        time_to_hire = metrics._calculate_time_to_hire(applications)
        
        # Verificar resultado
        self.assertGreaterEqual(time_to_hire, 0.0)

if __name__ == '__main__':
    unittest.main()
