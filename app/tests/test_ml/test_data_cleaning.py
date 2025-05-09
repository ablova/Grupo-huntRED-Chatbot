"""
Tests para el módulo de limpieza de datos.
"""

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from app.models import Person, Vacante, Application
from app.ml.core.data_cleaning import DataCleaner


class TestDataCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = DataCleaner()
        
        # Datos de prueba
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

    def test_clean_text(self):
        """Test de limpieza de texto."""
        test_text = "Python, Machine Learning, Data Science!"
        cleaned = self.cleaner.clean_text(test_text)
        self.assertTrue(all(c.isalpha() or c.isspace() for c in cleaned))
        self.assertTrue(all(word not in cleaned for word in ['y', 'o', 'en']))

    def test_clean_skills(self):
        """Test de limpieza de habilidades."""
        test_skills = "Python, Machine Learning, Data Science, AI"
        cleaned = self.cleaner.clean_skills(test_skills)
        self.assertIsInstance(cleaned, list)
        self.assertTrue(all(isinstance(skill, str) for skill in cleaned))

    def test_clean_experience(self):
        """Test de limpieza de años de experiencia."""
        test_cases = [
            (-1, 0),
            (0, 0),
            (5, 5),
            (100, 50)
        ]
        for input_val, expected in test_cases:
            cleaned = self.cleaner.clean_experience(input_val)
            self.assertEqual(cleaned, expected)

    def test_clean_salary(self):
        """Test de limpieza de salario."""
        test_cases = [
            (-1000, 0),
            (0, 0),
            (100000, 100000),
            (1000000, 500000)
        ]
        for input_val, expected in test_cases:
            cleaned = self.cleaner.clean_salary(input_val)
            self.assertEqual(cleaned, expected)

    def test_clean_location_score(self):
        """Test de limpieza de puntaje de ubicación."""
        test_cases = [
            (-0.5, 0.0),
            (0.0, 0.0),
            (0.5, 0.5),
            (1.5, 1.0)
        ]
        for input_val, expected in test_cases:
            cleaned = self.cleaner.clean_location_score(input_val)
            self.assertEqual(cleaned, expected)

    def test_clean_education_level(self):
        """Test de limpieza de nivel educativo."""
        test_cases = [
            (-1, 0),
            (0, 0),
            (4, 4),
            (10, 6)
        ]
        for input_val, expected in test_cases:
            cleaned = self.cleaner.clean_education_level(input_val)
            self.assertEqual(cleaned, expected)

    def test_clean_data(self):
        """Test de limpieza de datos completos."""
        test_data = {
            'skills_text': "Python, Machine Learning, Data Science",
            'years_of_experience': 5,
            'education_level': 4,
            'salary_range': 100000,
            'location_score': 0.9,
            'description': "Senior Data Scientist position"
        }
        cleaned = self.cleaner.clean_data(test_data)
        self.assertIsInstance(cleaned, dict)
        self.assertTrue(all(isinstance(v, (str, float, int)) for v in cleaned.values()))

    def test_transform_features(self):
        """Test de transformación de características."""
        features = pd.DataFrame({
            'experience': [5, 3, 7],
            'salary': [100000, 80000, 120000],
            'score': [0.9, 0.8, 0.7]
        })
        transformed = self.cleaner.transform_features(features)
        self.assertIsInstance(transformed, pd.DataFrame)
        self.assertEqual(len(transformed), len(features))

    def test_get_feature_importance(self):
        """Test de obtención de importancia de características."""
        mock_model = MagicMock()
        mock_model.feature_importances_ = np.array([0.4, 0.3, 0.3])
        feature_names = ['feature1', 'feature2', 'feature3']
        importance = self.cleaner.get_feature_importance(mock_model, feature_names)
        self.assertIsInstance(importance, dict)
        self.assertEqual(len(importance), 3)

    def test_validate_data(self):
        """Test de validación de datos."""
        valid_data = {
            'skills_text': "Python",
            'years_of_experience': 5,
            'education_level': 4,
            'salary_range': 100000,
            'location_score': 0.9,
            'description': "Position"
        }
        self.assertTrue(self.cleaner.validate_data(valid_data))

        invalid_data = {
            'skills_text': "Python",
            'years_of_experience': 5,
            'education_level': 4
        }
        self.assertFalse(self.cleaner.validate_data(invalid_data))


if __name__ == '__main__':
    unittest.main()
