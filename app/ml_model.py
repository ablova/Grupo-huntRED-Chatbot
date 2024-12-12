# ml_model.py

import os
import logging
from pathlib import Path

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

from joblib import dump, load

import pandas as pd
import numpy as np
import tensorflow as tf

from app.models import Person, Application  # Asegúrate de que Application está correctamente definido en models.py

# Configuración de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(os.path.join(settings.BASE_DIR, 'logs', 'ml_model.log'))
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class MatchmakingLearningSystem:
    def __init__(self, business_unit=None):
        """
        Sistema de aprendizaje de matchmaking con soporte para
        configuraciones globales o específicas por unidad de negocio.
        """
        self.business_unit = business_unit
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.pipeline = self._create_pipeline()
        self.model_file = os.path.join(
            settings.ML_MODELS_DIR, 
            f"matchmaking_model_{business_unit or 'global'}.pkl"
        )

    def _create_pipeline(self):
        """
        Crea un pipeline de preprocesamiento y modelo.
        """
        return Pipeline([
            ('scaler', self.scaler),
            ('model', self.model)
        ])

    def prepare_training_data(self):
        """
        Prepara los datos históricos para entrenamiento del modelo.
        """
        applications = self._get_applications()
        data = []
        for app in applications:
            # Verifica que vacante esté presente
            if not app.vacancy:
                logger.warning(f"Aplicación sin vacante: {app.id}")
                continue

            features = {
                'experience_years': app.person.experience_years or 0,
                'hard_skills_match': self._calculate_hard_skills_match(app),
                'soft_skills_match': self._calculate_soft_skills_match(app),
                'salary_alignment': self._calculate_salary_alignment(app),
                'age': self._calculate_age(app.person),
                'is_successful': 1 if app.status == 'contratado' else 0
            }
            data.append(features)
        df = pd.DataFrame(data)
        logger.info(f"Datos de entrenamiento preparados con {len(df)} registros.")
        return df

    def _get_applications(self):
        """
        Recupera aplicaciones históricas, filtrando por unidad de negocio si aplica.
        """
        if self.business_unit:
            applications = Application.objects.filter(
                vacancy__business_unit=self.business_unit,
                status__in=['contratado', 'rechazado']
            )
        else:
            applications = Application.objects.filter(status__in=['contratado', 'rechazado'])
        logger.info(f"Aplicaciones recuperadas: {applications.count()}")
        return applications

    def train_model(self):
        """
        Entrena el modelo de Machine Learning con datos preparados.
        """
        df = self.prepare_training_data()
        if df.empty:
            logger.error("No hay datos para entrenar el modelo.")
            return None

        X = df.drop('is_successful', axis=1)
        y = df['is_successful']

        X_scaled = self.scaler.fit_transform(X)
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        self.model.fit(X_train, y_train)
        accuracy = self.model.score(X_test, y_test)
        dump(self.pipeline, self.model_file)
        logger.info(f"Modelo entrenado con precisión: {accuracy:.2f}")
        return accuracy

    def predict_candidate_success(self, person, vacante):
        """
        Predice la probabilidad de éxito de un candidato.
        """
        if not Path(self.model_file).exists():
            logger.error(f"Modelo no encontrado: {self.model_file}")
            raise FileNotFoundError("Modelo no entrenado. Entrena el modelo antes de predecir.")

        self.pipeline = load(self.model_file)

        # Crear un objeto simulado de Application para reutilizar los métodos de cálculo
        class MockApplication:
            def __init__(self, person, vacante):
                self.person = person
                self.vacante = vacante

        mock_app = MockApplication(person, vacante)

        features = {
            'experience_years': person.experience_years or 0,
            'hard_skills_match': self._calculate_hard_skills_match(mock_app),
            'soft_skills_match': self._calculate_soft_skills_match(mock_app),
            'salary_alignment': self._calculate_salary_alignment(mock_app),
            'age': self._calculate_age(person)
        }

        feature_array = np.array(list(features.values())).reshape(1, -1)
        prediction_proba = self.pipeline.predict_proba(feature_array)[0][1]
        logger.info(f"Predicción de éxito para {person}: {prediction_proba:.2f}")
        return prediction_proba

    def recommend_skill_improvements(self, person):
        """
        Recomienda mejoras de habilidades basadas en análisis histórico.
        """
        skill_gaps = self._identify_skill_gaps()
        recommendations = []
        person_skills = set([skill.strip().lower() for skill in person.skills.split(',')]) if person.skills else set()

        for skill, importance in skill_gaps.items():
            if skill.lower() not in person_skills:
                recommendations.append({
                    'skill': skill,
                    'importance': importance,
                    'recommendation': f"Considere desarrollar la habilidad: {skill}"
                })
        logger.info(f"Recomendaciones de habilidades para {person}: {recommendations}")
        return recommendations

    def _identify_skill_gaps(self):
        """
        Identifica las brechas de habilidades más comunes.
        """
        # Este método podría mejorarse extrayendo datos de un análisis histórico
        return {
            'Python': 0.9,
            'Gestión de proyectos': 0.8,
            'Análisis de datos': 0.7
        }

    def _calculate_hard_skills_match(self, application):
        """
        Calcula el porcentaje de coincidencia de habilidades técnicas.
        """
        person_skills = set([skill.strip().lower() for skill in application.person.skills.split(',')]) if application.person.skills else set()
        job_skills = set([skill.strip().lower() for skill in application.vacante.skills_required]) if application.vacante.skills_required else set()
        if not job_skills:
            logger.warning(f"Vacante sin habilidades requeridas: {application.vacante}")
            return 0.0
        match_percentage = len(person_skills.intersection(job_skills)) / len(job_skills) * 100
        logger.debug(f"Habilidades técnicas coincididas: {match_percentage:.2f}%")
        return match_percentage

    def _calculate_soft_skills_match(self, application):
        """
        Calcula coincidencia de habilidades blandas.
        """
        person_soft_skills = set([skill.strip().lower() for skill in application.person.metadata.get('soft_skills', [])])
        job_soft_skills = set([skill.strip().lower() for skill in application.vacante.metadata.get('soft_skills', [])])
        if not job_soft_skills:
            logger.warning(f"Vacante sin habilidades blandas requeridas: {application.vacante}")
            return 0.0
        match_percentage = len(person_soft_skills.intersection(job_soft_skills)) / len(job_soft_skills) * 100
        logger.debug(f"Habilidades blandas coincididas: {match_percentage:.2f}%")
        return match_percentage

    def _calculate_salary_alignment(self, application):
        """
        Calcula la alineación salarial.
        """
        current_salary = application.person.salary_data.get('current_salary', 0)
        offered_salary = application.vacante.salario
        if not offered_salary:
            logger.warning(f"Vacante sin salario ofrecido: {application.vacante}")
            return 0.0
        alignment = 100 - abs(current_salary - offered_salary) / offered_salary * 100
        alignment = max(alignment, 0)  # Asegura que no sea negativo
        logger.debug(f"Alineación salarial: {alignment:.2f}%")
        return alignment

    def _calculate_age(self, person):
        """
        Calcula la edad del candidato.
        """
        if not person.fecha_nacimiento:
            logger.warning(f"Persona sin fecha de nacimiento: {person}")
            return 0.0
        age = (timezone.now().date() - person.fecha_nacimiento).days / 365
        logger.debug(f"Edad calculada para {person}: {age:.2f} años")
        return age

    def generate_quarterly_insights(self):
        """
        Genera insights trimestrales sobre el proceso de matchmaking.
        """
        insights = {
            'top_performing_skills': self._analyze_top_skills(),
            'success_rate_by_experience': self._analyze_experience_impact(),
            'salary_correlation': self._analyze_salary_impact()
        }
        logger.info(f"Insights trimestrales generados: {insights}")
        return insights

    def _analyze_top_skills(self):
        """
        Analiza las habilidades más frecuentes en candidatos contratados.
        """
        successful_applications = Application.objects.filter(status='contratado')
        skill_counts = {}
        for app in successful_applications:
            if not app.person.skills:
                continue
            skills = [skill.strip().lower() for skill in app.person.skills.split(',')]
            for skill in skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        top_skills = sorted_skills[:10]
        logger.debug(f"Top habilidades: {top_skills}")
        return top_skills

    def _analyze_experience_impact(self):
        """
        Analiza el impacto de la experiencia laboral en el éxito.
        """
        successful_apps = Application.objects.filter(status='contratado')
        rejected_apps = Application.objects.filter(status='rechazado')

        experience_successful = [app.person.experience_years or 0 for app in successful_apps]
        experience_rejected = [app.person.experience_years or 0 for app in rejected_apps]

        avg_successful = sum(experience_successful) / len(experience_successful) if experience_successful else 0
        avg_rejected = sum(experience_rejected) / len(experience_rejected) if experience_rejected else 0

        difference = avg_successful - avg_rejected

        impact = {
            "avg_experience_successful": round(avg_successful, 2),
            "avg_experience_rejected": round(avg_rejected, 2),
            "difference": round(difference, 2)
        }
        logger.debug(f"Impacto de experiencia: {impact}")
        return impact

    def _analyze_salary_impact(self):
        """
        Analiza la correlación entre expectativas salariales y éxito laboral.
        """
        successful_apps = Application.objects.filter(status='contratado')

        salary_differences = []
        for app in successful_apps:
            expected_salary = app.person.salary_data.get('expected_salary', 0)
            offered_salary = app.vacante.salario
            if not offered_salary:
                continue
            difference = abs(expected_salary - offered_salary) / offered_salary * 100
            salary_differences.append(difference)

        avg_difference = sum(salary_differences) / len(salary_differences) if salary_differences else 0
        aligned_candidates = len([diff for diff in salary_differences if diff < 10])
        total_candidates = len(salary_differences)

        salary_impact = {
            "avg_salary_difference": round(avg_difference, 2),
            "aligned_candidates": aligned_candidates,
            "total_candidates": total_candidates
        }
        logger.debug(f"Impacto salarial: {salary_impact}")
        return salary_impact

    # Skill and Adaptation Metrics
    skill_adaptability_index = models.FloatField(default=0.5)

class GrupohuntREDMLPipeline:
    def __init__(self, business_unit='huntRED®', log_dir='./ml_logs'):
        # Logging setup
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(log_dir, f'{business_unit}_ml.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        logger.info(f"HuntMLPipeline inicializado para {business_unit}")

        # Configuration
        self.business_unit = business_unit
        self.model_config = {
            'huntRED®': {
                'layers': [128, 64, 32],
                'learning_rate': 0.001,
                'dropout_rate': 0.3
            },
            'huntU': {
                'layers': [256, 128, 64],
                'learning_rate': 0.0005,
                'dropout_rate': 0.2
            },
             'Amigro': {
                'layers': [128, 128, 64],
                'activation': 'sigmoid',
                'learning_rate': 0.0008,
                'dropout_rate': 0.25
            }
        }
        
        # Core components
        self.scaler = StandardScaler()
        self.model = None
        self.history = None

    def load_data(self, filepath):
        """
        Robust data loading with multiple format support
        """
        try:
            if filepath.endswith('.csv'):
                data = pd.read_csv(filepath)
            elif filepath.endswith('.xlsx'):
                data = pd.read_excel(filepath)
            elif filepath.endswith('.json'):
                data = pd.read_json(filepath)
            else:
                raise ValueError("Unsupported file format")
            
            logger.info(f"Data loaded successfully from {filepath}")
            return data
        except Exception as e:
            logger.error(f"Error loading data from {filepath}: {e}")
            raise

    def preprocess_data(self, data, target_column='success_label'):
        """
        Advanced preprocessing with feature engineering
        """
        if target_column not in data.columns:
            logger.error(f"Columna objetivo '{target_column}' no encontrada en los datos.")
            raise ValueError(f"Columna objetivo '{target_column}' no encontrada en los datos.")
        
        X = data.drop(columns=[target_column])
        y = data[target_column]
        
        # Handle categorical variables
        X = pd.get_dummies(X)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        logger.info("Data preprocessing completed successfully.")
        return X_train, X_test, y_train, y_test

    def build_model(self):
        """
        Dynamic neural network architecture
        """
        config = self.model_config.get(
            self.business_unit, 
            self.model_config['huntRED®']
        )
        
        model = tf.keras.Sequential()
        
        # Hidden layers
        for units in config['layers']:
            model.add(tf.keras.layers.Dense(
                units, 
                activation='relu',
                kernel_regularizer=tf.keras.regularizers.l2(0.001)
            ))
            model.add(tf.keras.layers.Dropout(config['dropout_rate']))
        
        # Output layer
        model.add(tf.keras.layers.Dense(1, activation='sigmoid'))
        
        # Compile
        optimizer = tf.keras.optimizers.Adam(
            learning_rate=config['learning_rate']
        )
        
        model.compile(
            optimizer=optimizer,
            loss='binary_crossentropy',
            metrics=['accuracy', 'AUC']
        )
        
        self.model = model
        logger.info("Neural network architecture built successfully.")
        return model

    def train(self, X_train, y_train, X_test, y_test):
        """
        Advanced training with callbacks
        """
        if self.model is None:
            logger.error("Modelo no construido. Llama a build_model() antes de entrenar.")
            raise ValueError("Modelo no construido. Llama a build_model() antes de entrenar.")
        
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', patience=15, 
            restore_best_weights=True
        )
        
        model_checkpoint = tf.keras.callbacks.ModelCheckpoint(
            os.path.join(settings.ML_MODELS_DIR, f'{self.business_unit}_best_model.h5'),
            save_best_only=True
        )
        
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=100,
            batch_size=32,
            callbacks=[early_stopping, model_checkpoint]
        )
        
        logger.info("Model training completed successfully.")
        return self.history

    def evaluate_model(self, X_test, y_test):
        """
        Comprehensive model evaluation
        """
        if self.model is None:
            logger.error("Modelo no construido. Llama a build_model() antes de evaluar.")
            raise ValueError("Modelo no construido. Llama a build_model() antes de evaluar.")
        
        y_pred = (self.model.predict(X_test) > 0.5).astype(int)
        
        report = classification_report(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred)
        
        logger.info(f"Classification Report:\n{report}")
        logger.info(f"Confusion Matrix:\n{cm}")
        
        return report, cm

    def save_model(self):
        """
        Save entire pipeline components
        """
        os.makedirs(settings.ML_MODELS_DIR, exist_ok=True)
        
        # Save TensorFlow model
        model_path = os.path.join(settings.ML_MODELS_DIR, f'{self.business_unit}_full_model.h5')
        self.model.save(model_path)
        logger.info(f"TensorFlow model saved at {model_path}")
        
        # Save scaler
        scaler_path = os.path.join(settings.ML_MODELS_DIR, f'{self.business_unit}_scaler.pkl')
        dump(self.scaler, scaler_path)
        logger.info(f"Scaler saved at {scaler_path}")

    def predict(self, new_data):
        """
        Production prediction method
        """
        if self.model is None:
            logger.error("Modelo no construido. Llama a build_model() antes de predecir.")
            raise ValueError("Modelo no construido. Llama a build_model() antes de predecir.")
        
        # Preprocess new data
        new_data_scaled = self.scaler.transform(new_data)
        
        # Predict
        predictions = self.model.predict(new_data_scaled)
        
        logger.info("Predicciones realizadas exitosamente.")
        return predictions

# Uso Ejemplo
def main():
    ml_pipeline = HuntMLPipeline(business_unit='huntRED®')
    
    # Load data
    data = ml_pipeline.load_data('training_data.csv')
    
    # Preprocess
    X_train, X_test, y_train, y_test = ml_pipeline.preprocess_data(data)
    
    # Build model
    ml_pipeline.build_model()
    
    # Train
    ml_pipeline.train(X_train, y_train, X_test, y_test)
    
    # Evaluate
    report, cm = ml_pipeline.evaluate_model(X_test, y_test)
    
    # Save
    ml_pipeline.save_model()

if __name__ == "__main__":
    main()

class AdaptiveMLFramework:
    def __init__(self, business_unit):
        # Configurable model architectures
        self.model_configs = {
            'huntRED®': {
                'layers': [64, 32, 16],
                'activation': 'relu',
                'learning_rate': 0.001,
                'dropout_rate': 0.3
            },
            'huntU': {
                'layers': [128, 64, 32],
                'activation': 'tanh',
                'learning_rate': 0.0005,
                'dropout_rate': 0.2
            },
            'Amigro': {
                'layers': [128, 128, 64],
                'activation': 'sigmoid',
                'learning_rate': 0.0008,
                'dropout_rate': 0.25
            }
        }
        
        self.business_unit = business_unit
        self.config = self.model_configs.get(business_unit, {})
        self.model = None
        self.scaler = StandardScaler()

    def build_model(self, input_shape):
        """Dynamically construct neural network"""
        model = tf.keras.Sequential()

        # Add hidden layers
        for units in self.config.get('layers', [64, 32]):
            model.add(tf.keras.layers.Dense(
                units,
                activation=self.config.get('activation', 'relu')
            ))
            model.add(tf.keras.layers.Dropout(
                self.config.get('dropout_rate', 0.3)
            ))

        # Output layer
        model.add(tf.keras.layers.Dense(1, activation='sigmoid'))

        # Compile model
        optimizer = tf.keras.optimizers.Adam(
            learning_rate=self.config.get('learning_rate', 0.001)
        )

        model.compile(
            optimizer=optimizer,
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        self.model = model
        logger.info("AdaptiveMLFramework: Modelo construido exitosamente.")
        return model

    def train_and_optimize(self, X, y, validation_split=0.2):
        """
        Comprehensive training with:
        - Auto scaling
        - Smart splitting
        - Early stopping
        - Model checkpointing
        """
        # Preprocess data
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, 
            test_size=validation_split, 
            random_state=42
        )
        
        # Callbacks for optimization
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', 
            patience=10,
            restore_best_weights=True
        )
        
        model_checkpoint = tf.keras.callbacks.ModelCheckpoint(
            os.path.join(settings.ML_MODELS_DIR, f'{self.business_unit}_best_model.h5'),
            save_best_only=True
        )
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100,
            batch_size=32,
            callbacks=[early_stopping, model_checkpoint]
        )
        
        logger.info("AdaptiveMLFramework: Entrenamiento completado exitosamente.")
        return history

    def predict_and_explain(self, X_new):
        """
        Advanced prediction with interpretability
        """
        # Preprocess new data
        X_scaled = self.scaler.transform(X_new)
        
        # Predict
        predictions = self.model.predict(X_scaled)
        
        # Placeholder for feature importance or interpretability
        gradients = self._compute_gradients(X_scaled)
        
        logger.info("AdaptiveMLFramework: Predicciones realizadas exitosamente.")
        return {
            'predictions': predictions,
            'feature_importance': gradients
        }

    def _compute_gradients(self, X):
        """Compute feature importances"""
        # Implement gradient computation or use other interpretability methods
        # Por ejemplo, utilizando integraciones como SHAP o LIME
        logger.debug("AdaptiveMLFramework: Computando gradientes para interpretabilidad.")
        pass  # Implementar según necesidades