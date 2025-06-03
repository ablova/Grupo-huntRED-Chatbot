# /home/pablo/app/tests/test_ats/test_feature_extraction/test_feature_extractor.py
#
# Implementación para el módulo. Proporciona funcionalidad específica del sistema.

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from app.models import Person, Vacante
from app.ml.core.features.feature_extractor import FeatureExtractor

class TestFeatureExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = FeatureExtractor()
        
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

    def test_extract_features(self):
        """Test de extracción de características"""
        features = self.extractor.extract_features(self.person, self.vacancy)
        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(features.shape, (512,))

    def test_cache_handling(self):
        """Test de manejo de caché"""
        # Primera extracción (debería guardar en caché)
        features1 = self.extractor.extract_features(self.person, self.vacancy)
        
        # Segunda extracción (debería usar caché)
        features2 = self.extractor.extract_features(self.person, self.vacancy)
        
        self.assertTrue(np.array_equal(features1, features2))

    def test_parallel_processing(self):
        """Test de procesamiento paralelo"""
        with patch('app.ml.core.features.feature_extractor.AsyncProcessor.process') as mock_process:
            self.extractor.extract_features(self.person, self.vacancy)
            mock_process.assert_called()

    def test_feature_vector(self):
        """Test de vector de características"""
        features = self.extractor.extract_features(self.person, self.vacancy)
        
        # Verificar que todas las características están presentes
        self.assertTrue(np.any(features))
        self.assertFalse(np.isnan(features).any())

if __name__ == '__main__':
    unittest.main()
