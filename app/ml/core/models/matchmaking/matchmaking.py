# /home/pablo/app/ml/core/models/matchmaking/matchmaking.py
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Optional, Tuple
from app.models import Person, Vacante
from app.ml.core.models.base import BaseMLModel

class MatchmakingModel(BaseMLModel):
    """
    Modelo de emparejamiento para el sistema ATS AI.
    
    Este modelo utiliza una arquitectura de red neuronal profunda para predecir
    la compatibilidad entre candidatos y vacantes.
    """
    
    def __init__(self):
        """
        Inicializa el modelo de matchmaking.
        """
        self.model = None
        self.scaler = StandardScaler()
        self._initialize_model()

    def _initialize_model(self) -> None:
        """
        Inicializa el modelo de aprendizaje profundo con una arquitectura mejorada.
        """
        # Capa de entrada para características del candidato
        candidate_input = layers.Input(shape=(256,), name='candidate_input')
        
        # Capa de entrada para características de la vacante
        vacancy_input = layers.Input(shape=(256,), name='vacancy_input')
        
        # Procesamiento del candidato
        candidate_features = layers.Dense(128, activation='relu')(candidate_input)
        candidate_features = layers.BatchNormalization()(candidate_features)
        candidate_features = layers.Dropout(0.3)(candidate_features)
        
        # Procesamiento de la vacante
        vacancy_features = layers.Dense(128, activation='relu')(vacancy_input)
        vacancy_features = layers.BatchNormalization()(vacancy_features)
        vacancy_features = layers.Dropout(0.3)(vacancy_features)
        
        # Fusión de características
        merged = layers.Concatenate()([candidate_features, vacancy_features])
        
        # Capas ocultas con skip connections
        x = layers.Dense(256, activation='relu')(merged)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.4)(x)
        
        # Skip connection
        skip = x
        
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        # Combinar con skip connection
        x = layers.Add()([x, skip])
        
        # Capa de salida
        output = layers.Dense(1, activation='sigmoid')(x)
        
        # Crear modelo
        self.model = models.Model(
            inputs=[candidate_input, vacancy_input],
            outputs=output
        )
        
        # Compilar modelo con optimizador Adam y learning rate adaptativo
        optimizer = tf.keras.optimizers.Adam(
            learning_rate=tf.keras.optimizers.schedules.ExponentialDecay(
                initial_learning_rate=0.001,
                decay_steps=1000,
                decay_rate=0.9
            )
        )
        
        self.model.compile(
            optimizer=optimizer,
            loss='binary_crossentropy',
            metrics=[
                'accuracy',
                tf.keras.metrics.AUC(),
                tf.keras.metrics.Precision(),
                tf.keras.metrics.Recall()
            ]
        )

    def train(self, X_candidate: np.ndarray, X_vacancy: np.ndarray, y: np.ndarray,
              validation_split: float = 0.2, epochs: int = 100, batch_size: int = 32) -> Dict:
        """
        Entrena el modelo con datos de candidatos y vacantes.
        
        Args:
            X_candidate: Características de los candidatos
            X_vacancy: Características de las vacantes
            y: Etiquetas (1 para match exitoso, 0 para no match)
            validation_split: Proporción de datos para validación
            epochs: Número de épocas de entrenamiento
            batch_size: Tamaño del batch
            
        Returns:
            Dict con historial de entrenamiento
        """
        # Escalar características
        X_candidate_scaled = self.scaler.fit_transform(X_candidate)
        X_vacancy_scaled = self.scaler.transform(X_vacancy)
        
        # Callbacks para mejor entrenamiento
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5
            )
        ]
        
        # Entrenar modelo
        history = self.model.fit(
            [X_candidate_scaled, X_vacancy_scaled],
            y,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks
        )
        
        return history.history

    def predict(self, X_candidate: np.ndarray, X_vacancy: np.ndarray) -> np.ndarray:
        """
        Realiza predicciones de compatibilidad.
        
        Args:
            X_candidate: Características de los candidatos
            X_vacancy: Características de las vacantes
            
        Returns:
            Array con probabilidades de match
        """
        X_candidate_scaled = self.scaler.transform(X_candidate)
        X_vacancy_scaled = self.scaler.transform(X_vacancy)
        
        return self.model.predict([X_candidate_scaled, X_vacancy_scaled])

    def evaluate(self, X_candidate: np.ndarray, X_vacancy: np.ndarray, y: np.ndarray) -> Dict:
        """
        Evalúa el rendimiento del modelo.
        
        Args:
            X_candidate: Características de los candidatos
            X_vacancy: Características de las vacantes
            y: Etiquetas reales
            
        Returns:
            Dict con métricas de evaluación
        """
        X_candidate_scaled = self.scaler.transform(X_candidate)
        X_vacancy_scaled = self.scaler.transform(X_vacancy)
        
        return self.model.evaluate(
            [X_candidate_scaled, X_vacancy_scaled],
            y,
            return_dict=True
        )

    def save(self, filepath: str) -> None:
        """
        Guarda el modelo y el escalador.
        
        Args:
            filepath: Ruta donde guardar el modelo
        """
        try:
            # Guardar modelo
            self.model.save(filepath)
            
            # Guardar escalador
            import joblib
            scaler_path = filepath.replace('.h5', '_scaler.joblib')
            joblib.dump(self.scaler, scaler_path)
            
        except Exception as e:
            logger.error(f"Error guardando modelo: {e}")
            raise

    def load(self, filepath: str) -> None:
        """
        Carga el modelo y el escalador.
        
        Args:
            filepath: Ruta del modelo
        """
        try:
            # Cargar modelo
            self.model = tf.keras.models.load_model(filepath)
            
            # Cargar escalador
            import joblib
            scaler_path = filepath.replace('.h5', '_scaler.joblib')
            self.scaler = joblib.load(scaler_path)
            
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            raise

    def optimize_parameters(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        Optimiza los parámetros del modelo.
        
        Args:
            X: Características de entrada
            y: Etiquetas objetivo
            
        Returns:
            Dict: Mejores parámetros
        """
        try:
            from sklearn.model_selection import GridSearchCV
            from tensorflow.keras.wrappers.scikit_learn import KerasClassifier
            
            # Definir función para crear modelo
            def create_model(learning_rate=0.001):
                model = models.Sequential([
                    layers.Input(shape=(512,)),
                    layers.Dense(256, activation='relu'),
                    layers.BatchNormalization(),
                    layers.Dropout(0.3),
                    layers.Dense(128, activation='relu'),
                    layers.BatchNormalization(),
                    layers.Dropout(0.2),
                    layers.Dense(64, activation='relu'),
                    layers.BatchNormalization(),
                    layers.Dense(1, activation='sigmoid')
                ])
                
                optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
                model.compile(
                    optimizer=optimizer,
                    loss='binary_crossentropy',
                    metrics=['accuracy', tf.keras.metrics.AUC()]
                )
                return model
            
            # Crear wrapper de scikit-learn
            model = KerasClassifier(build_fn=create_model, verbose=0)
            
            # Definir parámetros a optimizar
            param_grid = {
                'batch_size': [32, 64, 128],
                'epochs': [10, 20, 30],
                'learning_rate': [0.001, 0.01, 0.1]
            }
            
            # Realizar búsqueda de parámetros
            grid = GridSearchCV(
                estimator=model,
                param_grid=param_grid,
                cv=3,
                scoring='accuracy'
            )
            
            # Escalar características
            X_scaled = self.scaler.transform(X)
            
            # Realizar búsqueda
            grid_result = grid.fit(X_scaled, y)
            
            # Devolver mejores parámetros
            return grid_result.best_params_
            
        except Exception as e:
            logger.error(f"Error optimizando parámetros: {e}")
            return {}

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Obtiene la importancia de las características.
        
        Returns:
            Dict[str, float]: Importancia de cada característica
        """
        # Implementar método para obtener importancia de características
        raise NotImplementedError("Este método debe ser implementado")
