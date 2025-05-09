import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from app.ml.core.models.matchmaking import MatchmakingModel
from app.ml.core.models.transition import TransitionModel

class TestModelOptimizer(unittest.TestCase):
    def setUp(self):
        self.matchmaking_model = MatchmakingModel()
        self.transition_model = TransitionModel()
        
        # Datos de prueba
        self.X = np.random.rand(100, 512)
        self.y = np.random.randint(0, 2, 100)

    def test_matchmaking_optimization(self):
        """Test de optimización del modelo de matchmaking"""
        with patch('sklearn.model_selection.GridSearchCV') as mock_grid:
            self.matchmaking_model.optimize_parameters(self.X, self.y)
            mock_grid.assert_called()

    def test_transition_optimization(self):
        """Test de optimización del modelo de transición"""
        with patch('sklearn.model_selection.GridSearchCV') as mock_grid:
            self.transition_model.optimize_parameters(self.X, self.y)
            mock_grid.assert_called()

    def test_parameter_space(self):
        """Test del espacio de parámetros"""
        params = self.matchmaking_model.optimize_parameters(self.X, self.y)
        self.assertIn('batch_size', params)
        self.assertIn('epochs', params)
        self.assertIn('learning_rate', params)

    def test_model_performance(self):
        """Test del rendimiento del modelo optimizado"""
        # Entrenar modelo con parámetros optimizados
        params = self.matchmaking_model.optimize_parameters(self.X, self.y)
        self.matchmaking_model.train(self.X, self.y, **params)
        
        # Evaluar rendimiento
        metrics = self.matchmaking_model.evaluate(self.X, self.y)
        self.assertGreater(metrics['accuracy'], 0.5)

if __name__ == '__main__':
    unittest.main()
