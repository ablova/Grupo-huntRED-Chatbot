# /home/pablo/app/tests/test_ml/test_matchmaking.py
#
# Implementación para el módulo. Proporciona funcionalidad específica del sistema.

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from app.models import Person, Vacante, Application
from app.ml.core.models import MatchmakingModel, TransitionModel
from app.ml.monitoring.metrics import ATSMetrics
from datetime import datetime, timedelta

class TestATS(unittest.TestCase):
    def setUp(self):
        # Configurar datos de prueba
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

    def test_matchmaking_model(self):
        """Test del modelo de matchmaking"""
        model = MatchmakingModel()
        
        # Simular características
        features = np.array([0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
        
        # Testear predicción
        prediction = model.predict(features)
        self.assertIsInstance(prediction, float)
        self.assertGreaterEqual(prediction, 0.0)
        self.assertLessEqual(prediction, 1.0)

    def test_transition_model(self):
        """Test del modelo de transición"""
        model = TransitionModel()
        
        # Simular características
        features = np.array([0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
        
        # Testear predicción
        prediction = model.predict(features)
        self.assertIsInstance(prediction, float)
        self.assertGreaterEqual(prediction, 0.0)
        self.assertLessEqual(prediction, 1.0)

    def test_metrics(self):
        """Test de las métricas del sistema"""
        metrics = ATSMetrics()
        
        # Simular aplicaciones
        applications = [self.application]
        
        # Testear métricas de negocio
        business_metrics = metrics.calculate_business_metrics(applications)
        self.assertIn('time_to_hire', business_metrics)
        self.assertIn('match_rate', business_metrics)
        self.assertIn('transition_success_rate', business_metrics)
        self.assertIn('application_conversion_rate', business_metrics)

        # Testear métricas del modelo
        y_true = np.array([1, 0, 1, 1, 0])
        y_pred = np.array([0.9, 0.2, 0.8, 0.7, 0.3])
        model_metrics = metrics.calculate_model_metrics(y_true, y_pred)
        self.assertIn('accuracy', model_metrics)
        self.assertIn('precision', model_metrics)
        self.assertIn('recall', model_metrics)
        self.assertIn('f1_score', model_metrics)
        self.assertIn('roc_auc', model_metrics)

    def test_dashboard_data(self):
        """Test de los datos del dashboard"""
        metrics = ATSMetrics()
        
        # Simular aplicaciones
        applications = [self.application]
        
        # Testear generación de datos
        dashboard_data = metrics.generate_dashboard_data()
        self.assertIn('timestamp', dashboard_data)
        self.assertIn('system_metrics', dashboard_data)
        self.assertIn('business_metrics', dashboard_data)
        self.assertIn('model_performance', dashboard_data)

if __name__ == '__main__':
    unittest.main()
