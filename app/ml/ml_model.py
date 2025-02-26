# /home/pablo/app/ml/ml_model.py


import os
import shap
import gc
import json
import logging
from pathlib import Path

from functools import lru_cache
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Prefetch

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score

from joblib import dump, load, Parallel, delayed
from keras_tuner import RandomSearch

import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint, TensorBoard
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam

from app.models import Person, Application, WeightingModel   # Asegúrate de que Application está correctamente definido en models.py
from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage

# Configuración de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(os.path.join(settings.BASE_DIR, 'logs', 'ml_model.log'))
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Carga condicional de TensorFlow (solo si es necesario)
try:
    import tensorflow as tf
    tf.config.set_visible_devices([], 'GPU')  # Evita que TensorFlow busque GPUs si no hay
    logger.info("✅ TensorFlow cargado correctamente.")
except ImportError:
    logger.warning("⚠ TensorFlow no está instalado. Se usará solo scikit-learn.")


class MatchmakingLearningSystem:
    """
    Sistema de aprendizaje automático para matchmaking de candidatos y vacantes.
    Usa principalmente RandomForest de scikit-learn.
    """

    def __init__(self, business_unit=None):
        self.business_unit = business_unit
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        # Se combina todo en un Pipeline (escalado + modelo)
        self.pipeline = Pipeline([
            ('scaler', self.scaler),
            ('classifier', self.model)
        ])
        # Ruta donde se guardará/cargará el modelo
        self.model_file = os.path.join(
            settings.ML_MODELS_DIR,
            f"matchmaking_model_{business_unit or 'global'}.pkl"
        )
        self._loaded_model = None

    def _get_applications(self):
        """
        Recupera aplicaciones históricas con estado 'contratado' o 'rechazado'.
        Filtra por unidad de negocio si corresponde.
        """
        if self.business_unit:
            apps = Application.objects.filter(
                vacancy__business_unit=self.business_unit,
                status__in=['contratado', 'rechazado']
            )
        else:
            apps = Application.objects.filter(status__in=['contratado', 'rechazado'])
        logger.info(f"Aplicaciones recuperadas: {apps.count()}")
        return apps

    def prepare_training_data(self):
        """
        Prepara datos de entrenamiento a partir de las aplicaciones recuperadas,
        extrayendo características relevantes con manejo de errores.
        """
        applications = self._get_applications()
        data = []
        for app in applications:
            if not app.vacancy:
                logger.warning(f"Aplicación sin vacante: {app.id}")
                continue
            try:
                features = {
                    'experience_years': app.person.experience_years or 0,
                    'hard_skills_match': self._calculate_hard_skills_match(app),
                    'soft_skills_match': self._calculate_soft_skills_match(app),
                    'salary_alignment': self._calculate_salary_alignment(app),
                    'age': self._calculate_age(app.person),
                    'is_successful': 1 if app.status == 'contratado' else 0
                }
                data.append(features)
            except Exception as e:
                logger.error(f"Error procesando aplicación {app.id}: {e}")
                continue

        df = pd.DataFrame(data)
        if df.empty:
            raise ValueError("No hay datos válidos para entrenar el modelo.")
        logger.info(f"Datos preparados para entrenamiento: {len(df)} registros.")
        return df

    def train_model(self, df, test_size=0.2):
        """
        Entrena el RandomForest sobre los datos proporcionados.
        Se realiza un split en train y test para evaluar métricas.
        """
        X = df.drop(columns=["is_successful"])
        y = df["is_successful"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        self.pipeline.fit(X_train, y_train)
        dump(self.pipeline, self.model_file)
        logger.info(f"✅ Modelo RandomForest entrenado y guardado en {self.model_file}")

        # Métricas de evaluación
        y_pred = self.pipeline.predict(X_test)
        report = classification_report(y_test, y_pred)
        logger.info(f"Reporte de clasificación:\n{report}")
        logger.info(f"Precisión: {precision_score(y_test, y_pred, zero_division=0):.2f}")
        logger.info(f"Recall: {recall_score(y_test, y_pred, zero_division=0):.2f}")
        logger.info(f"F1-Score: {f1_score(y_test, y_pred, zero_division=0):.2f}")

        gc.collect()

    def predict_candidate_success(self, person, vacancy):
        """
        Predice la probabilidad de éxito de un candidato en una vacante
        usando el modelo entrenado (RandomForest).
        """
        if not Path(self.model_file).exists():
            logger.error(f"Modelo no encontrado: {self.model_file}")
            raise FileNotFoundError("El modelo no está entrenado.")

        if not self._loaded_model:
            self._loaded_model = load(self.model_file)

        features = {
            'experience_years': person.experience_years or 0,
            'hard_skills_match': self._calculate_hard_skills_match_mock(person, vacancy),
            'soft_skills_match': self._calculate_soft_skills_match_mock(person, vacancy),
            'salary_alignment': self._calculate_salary_alignment_mock(person, vacancy),
            'age': self._calculate_age(person)
        }
        array = np.array(list(features.values())).reshape(1, -1)
        proba = self._loaded_model.predict_proba(array)[0][1]
        logger.info(f"Predicción de éxito para {person}: {proba:.2f}")
        return proba

    def predict_all_active_matches(self, person):
        """
        Predice en lote la probabilidad de éxito para todas las vacantes activas
        de la BU del candidato con manejo de errores.
        """
        self.load_model()
        bu = person.current_stage.business_unit if person.current_stage else None
        if not bu:
            return []

        active_vacancies = Vacante.objects.filter(activa=True, business_unit=bu)
        if not active_vacancies.exists():
            return []

        features_list = []
        for vacante in active_vacancies:
            try:
                features = {
                    'experience_years': person.experience_years or 0,
                    'hard_skills_match': calculate_match_percentage(person.skills, vacante.skills_required),
                    'soft_skills_match': calculate_match_percentage(
                        person.metadata.get('soft_skills', []),
                        vacante.metadata.get('soft_skills', [])
                    ),
                    'salary_alignment': calculate_alignment_percentage(
                        person.salary_data.get('current_salary', 0),
                        vacante.salario or 0
                    ),
                    'age': (timezone.now().date() - person.fecha_nacimiento).days / 365
                        if person.fecha_nacimiento else 0
                }
                features_list.append(features)
            except Exception as e:
                logger.error(f"Error procesando vacante {vacante.id}: {e}")
                continue

        if not features_list:
            return []

        X = pd.DataFrame(features_list)
        X_scaled = self.scaler.transform(X)
        predictions = (self.model.predict(X_scaled).flatten() * 100).tolist()
        results = [
            {"vacante": v.titulo, "empresa": v.empresa, "score": round(p, 2)}
            for v, p in zip(active_vacancies, predictions)
        ]
        return sorted(results, key=lambda x: x["score"], reverse=True)

    def recommend_skill_improvements(self, person):
        """
        Genera recomendaciones de habilidades basadas en brechas detectadas.
        (Versión simple o heurística).
        """
        skill_gaps = self._identify_skill_gaps()
        person_skills = set(skill.strip().lower() for skill in (person.skills or "").split(','))

        recommendations = []
        for skill, importance in skill_gaps.items():
            if skill.lower() not in person_skills:
                recommendations.append({
                    'skill': skill,
                    'importance': importance,
                    'recommendation': f"Deberías desarrollar más la habilidad '{skill}'"
                })
        logger.info(f"Recomendaciones para {person}: {recommendations}")
        return recommendations

    def generate_quarterly_insights(self):
        """
        Genera estadísticas e insights trimestrales del proceso de selección.
        """
        insights = {
            'top_performing_skills': self._analyze_top_skills(),
            'success_rate_by_experience': self._analyze_experience_impact(),
            'salary_correlation': self._analyze_salary_impact()
        }
        logger.info(f"Insights trimestrales: {insights}")
        return insights

    def explain_prediction(self, person, vacancy):
        """
        Usa SHAP para explicar la predicción de un candidato en una vacante.
        """
        if not Path(self.model_file).exists():
            logger.error("Modelo no encontrado para explicar la predicción.")
            raise FileNotFoundError("Modelo no entrenado.")

        if not self._loaded_model:
            self._loaded_model = load(self.model_file)

        explainer = shap.TreeExplainer(self._loaded_model['classifier'])
        features = [
            person.experience_years or 0,
            self._calculate_hard_skills_match_mock(person, vacancy),
            self._calculate_soft_skills_match_mock(person, vacancy),
            self._calculate_salary_alignment_mock(person, vacancy),
            self._calculate_age(person)
        ]
        shap_values = explainer.shap_values([features])
        logger.info(f"SHAP Values: {shap_values}")
        return shap_values

    # ----------------------------------------
    # Métodos internos para cálculo de features
    # ----------------------------------------

    def _calculate_hard_skills_match(self, application):
        """Porcentaje de coincidencia de habilidades técnicas para una aplicación real."""
        person_skills = (application.person.skills or "").split(',')
        job_skills = application.vacancy.skills_required or []
        return calculate_match_percentage(person_skills, job_skills)

    def _calculate_soft_skills_match(self, application):
        """Porcentaje de coincidencia de habilidades blandas para una aplicación real."""
        person_soft_skills = set(application.person.metadata.get('soft_skills', []))
        job_soft_skills = set(application.vacancy.metadata.get('soft_skills', []))
        if not job_soft_skills:
            return 0.0
        return (len(person_soft_skills.intersection(job_soft_skills)) / len(job_soft_skills)) * 100

    def _calculate_salary_alignment(self, application):
        """Alineación salarial entre candidato y vacante."""
        current_salary = application.person.salary_data.get('current_salary', 0)
        offered_salary = application.vacancy.salario or 0
        return calculate_alignment_percentage(current_salary, offered_salary)

    def _calculate_age(self, person):
        """Calcula la edad (en años) de la persona a partir de la fecha de nacimiento."""
        if not person.fecha_nacimiento:
            return 0
        return (timezone.now().date() - person.fecha_nacimiento).days / 365

    def _calculate_hard_skills_match_mock(self, person, vacancy):
        """Versión mock para calcular 'hard_skills_match' sin un objeto Application."""
        person_skills = (person.skills or "").split(',')
        job_skills = vacancy.skills_required or []
        return calculate_match_percentage(person_skills, job_skills)

    def _calculate_soft_skills_match_mock(self, person, vacancy):
        """Versión mock para 'soft_skills_match' sin Application."""
        p_soft = set(person.metadata.get("soft_skills", []))
        v_soft = set(vacancy.metadata.get("soft_skills", []))
        if not v_soft:
            return 0.0
        return (len(p_soft.intersection(v_soft)) / len(v_soft)) * 100

    def _calculate_salary_alignment_mock(self, person, vacancy):
        """Versión mock para 'salary_alignment' sin Application."""
        cur_sal = person.salary_data.get('current_salary', 0)
        off_sal = vacancy.salario or 0
        return calculate_alignment_percentage(cur_sal, off_sal)

    # ----------------------------------------
    # Métodos para generar insights
    # ----------------------------------------

    def _identify_skill_gaps(self):
        """
        Identifica brechas de habilidades más comunes en los datos.
        Ejemplo simplificado.
        """
        return {
            'Python': 0.9,
            'Gestión de proyectos': 0.8,
            'Análisis de datos': 0.7
        }

    def _analyze_top_skills(self):
        """
        Analiza las habilidades más frecuentes en candidatos contratados.
        """
        successful_apps = Application.objects.filter(status='contratado')
        skill_counts = {}
        for app in successful_apps:
            if not app.person.skills:
                continue
            skills = [s.strip().lower() for s in app.person.skills.split(',')]
            for skill in skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_skills[:10]

    def _analyze_experience_impact(self):
        """
        Analiza el impacto de la experiencia laboral en la probabilidad de ser contratado.
        """
        s_apps = Application.objects.filter(status='contratado')
        r_apps = Application.objects.filter(status='rechazado')

        exp_success = [app.person.experience_years or 0 for app in s_apps]
        exp_reject = [app.person.experience_years or 0 for app in r_apps]

        avg_succ = sum(exp_success) / len(exp_success) if exp_success else 0
        avg_reje = sum(exp_reject) / len(exp_reject) if exp_reject else 0

        return {
            "avg_experience_contratados": round(avg_succ, 2),
            "avg_experience_rechazados": round(avg_reje, 2),
            "difference": round(avg_succ - avg_reje, 2)
        }

    def _analyze_salary_impact(self):
        """
        Analiza la correlación entre expectativas salariales y éxito (contratación).
        """
        from app.models import Vacante
        s_apps = Application.objects.filter(status='contratado')
        salary_diffs = []
        for app in s_apps:
            expected_salary = app.person.salary_data.get('expected_salary', 0)
            offered_salary = app.vacancy.salario if app.vacancy else 0
            if offered_salary:
                diff = abs(expected_salary - offered_salary) / offered_salary * 100
                salary_diffs.append(diff)

        avg_diff = sum(salary_diffs) / len(salary_diffs) if salary_diffs else 0
        aligned_count = sum(1 for d in salary_diffs if d < 10)

        return {
            "avg_salary_difference": round(avg_diff, 2),
            "aligned_candidates": aligned_count,
            "total_candidates": len(salary_diffs)
        }

class GrupohuntREDMLPipeline:
    """
    Pipeline de Machine Learning con TensorFlow/Keras para la Business Unit 'huntRED®',
    aunque se puede generalizar a otras.
    """

    # Configuraciones por unidad de negocio
    model_config = {
        'huntRED®': {
            'layers': [256, 128, 64],
            'learning_rate': 0.001,
            'dropout_rate': 0.3
        },
        'huntU': {
            'layers': [128, 64],
            'learning_rate': 0.0005,
            'dropout_rate': 0.2
        },
        'Amigro': {
            'layers': [128, 64, 32],
            'learning_rate': 0.0008,
            'dropout_rate': 0.25
        }
    }
    _loaded_models = {}

    def __init__(self, business_unit='huntRED®', log_dir='./ml_logs'):
        os.makedirs(log_dir, exist_ok=True)
        self.business_unit = business_unit
        self.model_path = os.path.join(settings.ML_MODELS_DIR, f'{business_unit}_model.h5')
        self.scaler_path = os.path.join(settings.ML_MODELS_DIR, f'{business_unit}_scaler.pkl')
        self.model = None
        self.scaler = StandardScaler()

    def build_model(self, input_dim):
        """
        Construye una red neuronal (Sequential) personalizada según la unidad de negocio.
        """
        config = self.model_config.get(self.business_unit, self.model_config['huntRED®'])
        model = Sequential()
        for units in config['layers']:
            model.add(Dense(units, activation='relu'))
            model.add(Dropout(config['dropout_rate']))
        model.add(Dense(1, activation='sigmoid'))

        model.compile(
            optimizer=Adam(learning_rate=config['learning_rate']),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        self.model = model
        logger.info(f"Modelo Keras construido para {self.business_unit} con capas {config['layers']}.")

    def prepare_training_data(self):
        """
        Recupera datos históricos de Applications (status: contratado, rechazado),
        extrae features y retorna un DataFrame.
        """
        apps = Application.objects.filter(
            vacancy__business_unit=self.business_unit,
            status__in=['contratado', 'rechazado']
        ).select_related('person', 'vacancy')

        data = []
        for app in apps:
            if not app.vacancy:
                continue
            data.append({
                'experience_years': app.person.experience_years or 0,
                'hard_skills_match': calculate_match_percentage(app.person.skills, app.vacancy.skills_required),
                'soft_skills_match': calculate_match_percentage(
                    app.person.metadata.get('soft_skills', []),
                    app.vacancy.metadata.get('soft_skills', [])
                ),
                'salary_alignment': calculate_alignment_percentage(
                    app.person.salary_data.get('current_salary', 0),
                    app.vacancy.salario or 0
                ),
                'age': (timezone.now().date() - app.person.fecha_nacimiento).days / 365
                       if app.person.fecha_nacimiento else 0,
                'success_label': 1 if app.status == 'contratado' else 0
            })

        df = pd.DataFrame(data)
        logger.info(f"Datos preparados para {self.business_unit}: {len(df)} registros.")
        return df

    def preprocess_data(self, df):
        """
        Aplica dummy encoding (si fuera necesario), escalado y luego
        separa en train/test.
        """
        if 'success_label' not in df.columns:
            raise ValueError("Falta la columna 'success_label' en los datos.")

        X = df.drop(columns=['success_label'])
        y = df['success_label']

        # Escalado
        X_scaled = self.scaler.fit_transform(X)
        dump(self.scaler, self.scaler_path)

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        return X_train, X_test, y_train, y_test

    def train_model(self, X_train, y_train, X_test, y_test):
        """
        Entrena la red neuronal construida con callbacks de regularización.
        Guarda el modelo en self.model_path.
        """
        # Si el modelo no está creado todavía
        if self.model is None:
            self.build_model(input_dim=X_train.shape[1])

        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=1e-5, verbose=1),
            ModelCheckpoint(self.model_path, save_best_only=True, monitor='val_loss', verbose=1),
            TensorBoard(log_dir='./logs')
        ]

        self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=100,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )

        self.model.save(self.model_path)
        logger.info(f"✅ Modelo entrenado y guardado en {self.model_path}")
        gc.collect()

    @lru_cache(maxsize=1)
    def load_model(self):
        """
        Carga el modelo y el scaler en memoria de forma eficiente con caching.
        """
        if os.path.exists(self.model_path):
            self.model = load_model(self.model_path)
            logger.info(f"Modelo Keras cargado desde {self.model_path}.")
        else:
            logger.warning("No se encontró un modelo entrenado. Se construirá uno nuevo.")
            self.build_model(input_dim=5)  # Asumiendo 5 características; ajustar según datos reales

        if os.path.exists(self.scaler_path):
            self.scaler = load(self.scaler_path)
        else:
            logger.warning("Scaler no encontrado. Se usará un scaler no entrenado.")

    def predict_candidate_success(self, person, vacancy):
        """
        Predice la probabilidad de éxito con el modelo Keras para un candidato y una vacante.
        """
        self.load_model()

        features = [{
            'experience_years': person.experience_years or 0,
            'hard_skills_match': calculate_match_percentage(person.skills, vacancy.skills_required),
            'soft_skills_match': calculate_match_percentage(
                person.metadata.get("soft_skills", []),
                vacancy.metadata.get("soft_skills", [])
            ),
            'salary_alignment': calculate_alignment_percentage(
                person.salary_data.get("current_salary", 0),
                vacancy.salario or 0
            ),
            'age': (timezone.now().date() - person.fecha_nacimiento).days / 365
                   if person.fecha_nacimiento else 0
        }]

        X = pd.DataFrame(features)
        X_scaled = self.scaler.transform(X)
        proba = self.model.predict(X_scaled)[0][0]
        logger.info(f"Probabilidad de éxito para {person} en '{vacancy.titulo}': {proba:.2f}")
        return proba

    def predict_all_active_matches(self, person):
        """
        Predice en lote la probabilidad de éxito para todas las vacantes activas
        de la BU del candidato.
        """
        self.load_model()
        bu = person.current_stage.business_unit if person.current_stage else None
        if not bu:
            return []

        active_vacancies = Vacante.objects.filter(activa=True, business_unit=bu)
        if not active_vacancies.exists():
            return []

        # Construir features en lote
        features_list = []
        for vacante in active_vacancies:
            features_list.append({
                'experience_years': person.experience_years or 0,
                'hard_skills_match': calculate_match_percentage(person.skills, vacante.skills_required),
                'soft_skills_match': calculate_match_percentage(
                    person.metadata.get("soft_skills", []),
                    vacante.metadata.get("soft_skills", [])
                ),
                'salary_alignment': calculate_alignment_percentage(
                    person.salary_data.get("current_salary", 0),
                    vacante.salario or 0
                ),
                'age': (timezone.now().date() - person.fecha_nacimiento).days / 365
                       if person.fecha_nacimiento else 0
            })

        X = pd.DataFrame(features_list)
        X_scaled = self.scaler.transform(X)

        predictions = (self.model.predict(X_scaled).flatten() * 100).tolist()
        results = [
            {"vacante": v.titulo, "empresa": v.empresa, "score": round(p, 2)}
            for v, p in zip(active_vacancies, predictions)
        ]
        return sorted(results, key=lambda x: x["score"], reverse=True)
    

class AdaptiveMLFramework(GrupohuntREDMLPipeline):
    """
    Variante adaptativa que hereda del GrupohuntREDMLPipeline,
    permitiendo ajustes y explicaciones extra (via SHAP).
    """

    def __init__(self, business_unit):
        super().__init__(business_unit)
        self.model_path = os.path.join(settings.ML_MODELS_DIR, f'{business_unit}_adaptive_model.h5')

    def build_model(self, input_dim):
        """
        Construye la red neuronal adaptativa con base en la config del padre.
        """
        super().build_model(input_dim)
        logger.info(f"Modelo adaptativo para {self.business_unit} listo.")

    def train_and_optimize(self, X, y, validation_split=0.2):
        """
        Entrena y optimiza el modelo adaptativo con evaluación post-entrenamiento.
        """
        X_scaled = self.scaler.fit_transform(X)
        dump(self.scaler, self.scaler_path)

        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, test_size=validation_split, random_state=42
        )

        self.build_model(input_dim=X_train.shape[1])

        early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        model_checkpoint = ModelCheckpoint(self.model_path, save_best_only=True, monitor='val_loss')

        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100,
            batch_size=32,
            callbacks=[early_stopping, model_checkpoint],
            verbose=1
        )

        # Evaluación post-entrenamiento
        val_loss, val_acc = self.model.evaluate(X_val, y_val, verbose=0)
        logger.info(f"Entrenamiento completado - Val Loss: {val_loss:.4f}, Val Accuracy: {val_acc:.4f}")
        logger.info(f"Modelo guardado en {self.model_path}")

    def predict_and_explain(self, X_new):
        """
        Realiza predicciones con el modelo adaptativo y genera explicaciones SHAP.
        """
        if self.model is None:
            self.model = load_model(self.model_path)

        # Asegurarnos de cargar el scaler
        self.scaler = load(self.scaler_path)
        X_scaled = self.scaler.transform(X_new)

        predictions = self.model.predict(X_scaled)
        # SHAP para redes neuronales: KernelExplainer como aproximación
        explainer = shap.KernelExplainer(self.model.predict, X_scaled[:50])  # Muestra de referencia
        shap_values = explainer.shap_values(X_scaled)
        return {
            'predictions': predictions,
            'shap_values': shap_values
        }
    

def main():
    pipeline = GrupohuntREDMLPipeline(business_unit='huntRED®')

    # 1) Preparar datos
    data = pipeline.prepare_training_data()
    
    # 2) Preprocesar
    X_train, X_test, y_train, y_test = pipeline.preprocess_data(data)
    
    # 3) Entrenar
    pipeline.train_model(X_train, y_train, X_test, y_test)

    # 4) Predecir matches para una persona de ejemplo
    from app.models import Person
    person = Person.objects.first()  # Ejemplo
    if person:
        matches = pipeline.predict_all_active_matches(person)
        logger.info(f"Coincidencias para {person.nombre}: {matches}")

if __name__ == "__main__":
    main()