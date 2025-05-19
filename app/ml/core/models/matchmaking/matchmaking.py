import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Optional, Tuple
from app.models import Person, Vacante
from app.ml.core.models.matchmaking.basebase import BaseModel

class MatchmakingModel(BaseModel):
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
        Inicializa el modelo de aprendizaje profundo.
        
        La arquitectura del modelo está diseñada para:
        - Manejar características de alta dimensionalidad
        - Reducir overfitting con regularización y dropout
        - Mantener la estabilidad con batch normalization
        - Proporcionar predicciones probabilísticas
        """
        self.model = models.Sequential([
            layers.Input(shape=(512,)),  # 512 características (embedding size)
            layers.Dense(256, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(128, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01)),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01)),
            layers.BatchNormalization(),
            layers.Dense(1, activation='sigmoid')
        ])
        
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC()]
        )

    def _build_model(self) -> models.Sequential:
        """
        Construye el modelo de aprendizaje profundo.
        
        La arquitectura del modelo está diseñada para:
        - Manejar características de alta dimensionalidad
        - Reducir overfitting con regularización y dropout
        - Mantener la estabilidad con batch normalization
        - Proporcionar predicciones probabilísticas
        """
        model = models.Sequential([
            layers.Input(shape=(512,)),  # 512 características (embedding size)
            layers.Dense(256, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(128, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01)),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01)),
            layers.BatchNormalization(),
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC()]
        )
        return model

    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 10, batch_size: int = 32) -> None:
        """
        Entrena el modelo con los datos proporcionados.
        
        Args:
            X: Características de entrada
            y: Etiquetas objetivo
            epochs: Número de épocas de entrenamiento
            batch_size: Tamaño del batch
        """
        try:
            # Escalar características
            X_scaled = self.scaler.fit_transform(X)
            
            # Entrenar modelo con early stopping
            self.model.fit(
                X_scaled, y,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=0.2,
                callbacks=[
                    tf.keras.callbacks.EarlyStopping(
                        monitor='val_loss',
                        patience=3,
                        restore_best_weights=True
                    )
                ]
            )
            
        except Exception as e:
            logger.error(f"Error entrenando modelo: {e}")
            raise

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evalúa el rendimiento del modelo.
        
        Args:
            X: Características de entrada
            y: Etiquetas objetivo
            
        Returns:
            Dict[str, float]: Métricas de evaluación
        """
        try:
            # Escalar características
            X_scaled = self.scaler.transform(X)
            
            # Evaluar
            metrics = self.model.evaluate(X_scaled, y, return_dict=True)
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluando modelo: {e}")
            return {}

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

    def _initialize_model(self) -> None:
        """
        Inicializa el modelo de aprendizaje profundo.
        """
        self.model = models.Sequential([
            layers.Input(shape=(512,)),  # 512 características (embedding size)
            layers.Dense(256, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(128, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01)),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01)),
            layers.BatchNormalization(),
            layers.Dense(1, activation='sigmoid')
        ])
        
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC()]
        )

    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 10, batch_size: int = 32) -> None:
        """
        Entrena el modelo con los datos proporcionados.
        
        Args:
            X: Características de entrada
            y: Etiquetas objetivo
            epochs: Número de épocas de entrenamiento
            batch_size: Tamaño del batch
        """
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(
            X_scaled, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            callbacks=[
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=3,
                    restore_best_weights=True
                )
            ]
        )

    def predict(self, person: Person, vacancy: Vacante) -> float:
        """
        Predice la probabilidad de coincidencia entre un candidato y una vacante.
        
        Args:
            person: Objeto Person
            vacancy: Objeto Vacante
            
        Returns:
            float: Probabilidad de coincidencia (0-1)
        """
        # Extraer características
        features = self._extract_features(person, vacancy)
        features_scaled = self.scaler.transform([features])
        
        # Predecir
        prediction = self.model.predict(features_scaled)[0][0]
        return float(prediction)

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evalúa el rendimiento del modelo.
        
        Args:
            X: Características de entrada
            y: Etiquetas objetivo
            
        Returns:
            Dict[str, float]: Métricas de evaluación
        """
        X_scaled = self.scaler.transform(X)
        metrics = self.model.evaluate(X_scaled, y, return_dict=True)
        return metrics

    def save(self, filepath: str) -> None:
        """
        Guarda el modelo y el escalador.
        
        Args:
            filepath: Ruta donde guardar el modelo
        """
        self.model.save(filepath)
        joblib.dump(self.scaler, filepath + '.scaler')

    def load(self, filepath: str) -> None:
        """
        Carga el modelo y el escalador.
        
        Args:
            filepath: Ruta del archivo del modelo
        """
        self.model = models.load_model(filepath)
        self.scaler = joblib.load(filepath + '.scaler')

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Obtiene la importancia de las características.
        
        Returns:
            Dict[str, float]: Importancia de cada característica
        """
        # Implementar método para obtener importancia de características
        raise NotImplementedError("Este método debe ser implementado")
