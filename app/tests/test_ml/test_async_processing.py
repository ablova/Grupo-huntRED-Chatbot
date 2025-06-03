# /home/pablo/app/tests/test_ml/test_async_processing.py
#
# Implementación para el módulo. Proporciona funcionalidad específica del sistema.

"""
Tests para el módulo de procesamiento asíncrono.
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import numpy as np
import pandas as pd
from app.models import Person, Vacante, Application
from app.ats.ml.core.async_processing import AsyncProcessor
from app.ats.ml.core.data_cleaning import DataCleaner


class TestAsyncProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = AsyncProcessor()
        self.mock_model = MagicMock()
        self.mock_model.predict = AsyncMock(return_value=np.array([0.8]))
        self.mock_model.feature_importances_ = np.array([0.4, 0.3, 0.3])

    async def test_process_data_async(self):
        """Test de procesamiento de datos asíncrono."""
        test_data = {
            'skills_text': "Python, Machine Learning",
            'years_of_experience': 5,
            'education_level': 4,
            'salary_range': 100000,
            'location_score': 0.9,
            'description': "Position"
        }
        result = await self.processor.process_data_async(test_data)
        self.assertIsInstance(result, dict)
        self.assertTrue(all(isinstance(v, (str, float, int)) for v in result.values()))

    async def test_process_batch_async(self):
        """Test de procesamiento de lote asíncrono."""
        test_data_list = [{
            'skills_text': "Python, Machine Learning",
            'years_of_experience': 5,
            'education_level': 4,
            'salary_range': 100000,
            'location_score': 0.9,
            'description': "Position"
        } for _ in range(3)]
        results = await self.processor.process_batch_async(test_data_list)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 3)

    async def test_predict_async(self):
        """Test de predicción asíncrona."""
        features = pd.DataFrame({
            'feature1': [0.5],
            'feature2': [0.5],
            'feature3': [0.5]
        })
        predictions = await self.processor.predict_async(self.mock_model, features)
        self.assertIsInstance(predictions, np.ndarray)
        self.assertEqual(len(predictions), 1)

    async def test_train_model_async(self):
        """Test de entrenamiento de modelo asíncrono."""
        X = pd.DataFrame({
            'feature1': [0.5, 0.6, 0.7],
            'feature2': [0.5, 0.6, 0.7],
            'feature3': [0.5, 0.6, 0.7]
        })
        y = pd.Series([1, 0, 1])
        result = await self.processor.train_model_async(self.mock_model, X, y)
        self.assertTrue(result)

    async def test_evaluate_model_async(self):
        """Test de evaluación de modelo asíncrono."""
        X = pd.DataFrame({
            'feature1': [0.5, 0.6, 0.7],
            'feature2': [0.5, 0.6, 0.7],
            'feature3': [0.5, 0.6, 0.7]
        })
        y = pd.Series([1, 0, 1])
        metrics = await self.processor.evaluate_model_async(self.mock_model, X, y)
        self.assertIsInstance(metrics, dict)
        self.assertIn('accuracy', metrics)
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)

    async def test_process_pipeline_async(self):
        """Test de pipeline completo asíncrono."""
        test_data = {
            'skills_text': "Python, Machine Learning",
            'years_of_experience': 5,
            'education_level': 4,
            'salary_range': 100000,
            'location_score': 0.9,
            'description': "Position"
        }
        result = await self.processor.process_pipeline_async(test_data, self.mock_model)
        self.assertIsInstance(result, dict)
        self.assertIn('cleaned_data', result)
        self.assertIn('features', result)
        self.assertIn('prediction', result)
        self.assertIn('evaluation', result)

    def test_cache_usage(self):
        """Test de uso de caché."""
        test_data = {
            'skills_text': "Python, Machine Learning",
            'years_of_experience': 5,
            'education_level': 4,
            'salary_range': 100000,
            'location_score': 0.9,
            'description': "Position"
        }
        # Primera llamada (sin caché)
        asyncio.run(self.processor.process_data_async(test_data))
        # Segunda llamada (con caché)
        result = asyncio.run(self.processor.process_data_async(test_data))
        self.assertIsInstance(result, dict)

    def test_error_handling(self):
        """Test de manejo de errores."""
        test_data = {
            'invalid_key': "value"
        }
        result = asyncio.run(self.processor.process_data_async(test_data))
        self.assertIsInstance(result, dict)
        self.assertTrue(len(result) == 0)


if __name__ == '__main__':
    unittest.main()
