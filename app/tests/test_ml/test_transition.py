# /home/pablo/app/tests/test_ml/test_transition.py
#
# Implementación para el módulo. Proporciona funcionalidad específica del sistema.

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from app.models import Person, Vacante, Application
from app.ml.core.models.transition import TransitionModel
from datetime import datetime, timedelta

class TestTransitionModel(unittest.TestCase):
    def setUp(self):
        self.person = Person(
            id=1,
            skills_text="Python, Machine Learning, Data Science",
            years_of_experience=5,
            education_level=4,
            current_vacancy=None
        )

        self.current_vacancy = Vacante(
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

        self.target_vacancy = Vacante(
            id=2,
            title="AI Team Lead",
            description="AI Team Lead position",
            required_experience=7,
            required_education=4,
            salary_range=150000,
            location_score=0.95,
            industry="Technology",
            level="Lead",
            main_skill="Python",
            activa=True
        )

        self.application = Application(
            id=1,
            person=self.person,
            vacancy=self.target_vacancy,
            status="contratado",
            date_applied=datetime.now() - timedelta(days=10),
            date_hired=datetime.now()
        )

    def test_predict(self):
        """Test de la predicción de transición"""
        model = TransitionModel()
        
        # Simular características
        features = np.array([0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
        
        # Testear predicción
        prediction = model.predict(features)
        self.assertIsInstance(prediction, float)
        self.assertGreaterEqual(prediction, 0.0)
        self.assertLessEqual(prediction, 1.0)

    def test_train(self):
        """Test del entrenamiento del modelo"""
        model = TransitionModel()
        
        # Simular datos de entrenamiento
        X = np.random.rand(100, 512)
        y = np.random.randint(0, 2, 100)
        
        # Testear entrenamiento
        model.train(X, y)
        self.assertIsNotNone(model.model)

    def test_evaluate(self):
        """Test de la evaluación del modelo"""
        model = TransitionModel()
        
        # Simular datos de evaluación
        X = np.random.rand(100, 512)
        y = np.random.randint(0, 2, 100)
        
        # Testear evaluación
        metrics = model.evaluate(X, y)
        self.assertIn('accuracy', metrics)
        self.assertIn('auc', metrics)

if __name__ == '__main__':
    unittest.main()
