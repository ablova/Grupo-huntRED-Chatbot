# /home/pablo/app/ml/ml_model.py
import os
import gc
import json
import logging
from pathlib import Path
from functools import lru_cache
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
import pandas as pd
import numpy as np
from joblib import dump, load
from celery import shared_task
from typing import Dict, List, Any, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from app.ml.core.utils.matchmaking import calculate_match_percentage, calculate_alignment_percentage
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Diccionario de jerarquía de unidades de negocio
BUSINESS_UNIT_HIERARCHY = {
    "amigro": 1,
    "huntu": 2,
    "huntred": 3,
    "huntred_executive": 4,
}

class BaseMLModel(ABC):
    """Clase base abstracta para todos los modelos de ML."""
    
    def __init__(self, business_unit: Optional[str] = None):
        self.business_unit = business_unit
        self.model = None
        self.scaler = None
        self._initialize_models()
    
    @abstractmethod
    def _initialize_models(self) -> None:
        """Inicializa los modelos específicos."""
        pass
    
    @abstractmethod
    def prepare_training_data(self):
        """Prepara los datos para entrenamiento."""
        pass
    
    @abstractmethod
    def train_model(self, df, test_size=0.2):
        """Entrena el modelo con los datos proporcionados."""
        pass

class MatchmakingModel(BaseMLModel):
    """Modelo específico para matchmaking de candidatos."""
    
    def __init__(self, business_unit: Optional[str] = None):
        super().__init__(business_unit)
        self.model_file = os.path.join(
            settings.ML_MODELS_DIR,
            f"matchmaking_model_{business_unit or 'global'}.pkl"
        )
    
    def _initialize_models(self) -> None:
        self.model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
        self.pipeline = Pipeline([
            ('scaler', self.scaler),
            ('classifier', self.model)
        ])
    
    def prepare_training_data(self):
        """Implementación específica para matchmaking."""
        # ... existing code ...
    
    def train_model(self, df, test_size=0.2):
        """Implementación específica para matchmaking."""
        # ... existing code ...

class TransitionModel(BaseMLModel):
    """Modelo específico para predicción de transiciones."""
    
    def __init__(self, business_unit: Optional[str] = None):
        super().__init__(business_unit)
        self.model_file = os.path.join(
            settings.ML_MODELS_DIR,
            f"transition_model_{business_unit or 'global'}.pkl"
        )
    
    def _initialize_models(self) -> None:
        self.model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
        self.pipeline = Pipeline([
            ('scaler', self.scaler),
            ('classifier', self.model)
        ])
    
    def prepare_training_data(self):
        """Implementación específica para transiciones."""
        # ... existing code ...
    
    def train_model(self, df, test_size=0.2):
        """Implementación específica para transiciones."""
        # ... existing code ...

class MarketAnalysisModel(BaseMLModel):
    """Modelo específico para análisis de mercado."""
    
    def __init__(self, business_unit: Optional[str] = None):
        super().__init__(business_unit)
        self.model_file = os.path.join(
            settings.ML_MODELS_DIR,
            f"market_analysis_model_{business_unit or 'global'}.pkl"
        )
    
    def _initialize_models(self) -> None:
        self.model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
        self.pipeline = Pipeline([
            ('scaler', self.scaler),
            ('classifier', self.model)
        ])
    
    def prepare_training_data(self):
        """Implementación específica para análisis de mercado."""
        # ... existing code ...
    
    def train_model(self, df, test_size=0.2):
        """Implementación específica para análisis de mercado."""
        # ... existing code ...

class MatchmakingLearningSystem:
    """
    Sistema de aprendizaje automático para matchmaking y análisis de perfiles.
    
    Este sistema maneja:
    - Predicción de éxito de candidatos
    - Análisis de compatibilidad cultural
    - Recomendaciones personalizadas
    - Análisis de mercado
    - Transiciones entre unidades de negocio
    """
    
    def __init__(self, business_unit=None):
        """
        Inicializa el sistema de aprendizaje automático.
        
        Args:
            business_unit: Unidad de negocio específica (opcional)
        """
        self.business_unit = business_unit
        self.model = None
        self.scaler = None
        self.model_file = os.path.join(
            settings.ML_MODELS_DIR,
            f"matchmaking_model_{business_unit or 'global'}.pkl"
        )
        self.transition_model_file = os.path.join(
            settings.ML_MODELS_DIR,
            f"transition_model_{business_unit or 'global'}.pkl"
        )
        self._loaded_model = None
        self._loaded_transition_model = None
        
        # Inicializar modelos específicos
        self.personality_model = RandomForestClassifier(n_estimators=100)
        self.professional_model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
        self._initialize_models()

    def load_tensorflow(self):
        try:
            import tensorflow as tf
            tf.config.set_visible_devices([], 'GPU')
            tf.config.threading.set_intra_op_parallelism_threads(1)
            tf.config.threading.set_inter_op_parallelism_threads(1)
            logger.info("✅ TensorFlow cargado bajo demanda.")
            return tf
        except ImportError:
            logger.warning("⚠ TensorFlow no está instalado. Usando solo scikit-learn.")
            return None

    def load_model(self):
        if not self._loaded_model and os.path.exists(self.model_file):
            self._loaded_model = load(self.model_file)
            logger.info(f"Modelo cargado desde {self.model_file}")
        elif not os.path.exists(self.model_file):
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.scaler = StandardScaler()
            self.pipeline = Pipeline([
                ('scaler', self.scaler),
                ('classifier', self.model)
            ])
            logger.info("Modelo RandomForest inicializado (no entrenado).")
    
    def load_transition_model(self):
        if not self._loaded_transition_model and os.path.exists(self.transition_model_file):
            self._loaded_transition_model = load(self.transition_model_file)
            logger.info(f"Modelo de transición cargado desde {self.transition_model_file}")
        elif not os.path.exists(self.transition_model_file):
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline
            self.transition_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.transition_scaler = StandardScaler()
            self.transition_pipeline = Pipeline([
                ('scaler', self.transition_scaler),
                ('classifier', self.transition_model)
            ])
            logger.info("Modelo de transición RandomForest inicializado (no entrenado).")

    def _get_applications(self):
        from app.models import Application
        if self.business_unit:
            apps = Application.objects.filter(
                vacancy__business_unit=self.business_unit,
                status__in=['contratado', 'rechazado']
            )
        else:
            apps = Application.objects.filter(status__in=['contratado', 'rechazado'])
        logger.info(f"Aplicaciones recuperadas: {apps.count()}")
        return apps

    @shared_task(name='ml.prepare_batch_data', retry_backoff=True, retry_jitter=True, max_retries=3)
    def process_batch(self, batch_ids):
        """Process a batch of applications to extract features."""
        from app.models import Application
        from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage
        batch_apps = Application.objects.filter(id__in=batch_ids)
        batch_data = []
        for app in batch_apps:
            try:
                hard_skills_score = calculate_match_percentage(app.person.skills, app.vacancy.required_skills)
                soft_skills_score = calculate_match_percentage(app.person.personality, app.vacancy.culture_fit)
                salary_alignment = self._calculate_salary_alignment(app)
                age = self._calculate_age(app.person)
                success = 1 if app.status == 'contratado' else 0
                batch_data.append({
                    'person_id': app.person.id,
                    'vacancy_id': app.vacancy.id,
                    'hard_skills_score': hard_skills_score,
                    'soft_skills_score': soft_skills_score,
                    'salary_alignment': salary_alignment,
                    'age': age,
                    'success': success
                })
                logger.info(f"Processed application {app.id} in batch")
            except Exception as e:
                logger.error(f"Error processing application {app.id}: {str(e)}")
        return batch_data

    def prepare_training_data(self):
        """Prepare training data with batch processing to optimize memory usage."""
        from app.models import Application
        if self.business_unit:
            apps = Application.objects.filter(
                vacancy__business_unit=self.business_unit,
                status__in=['contratado', 'rechazado']
            )
        else:
            apps = Application.objects.filter(status__in=['contratado', 'rechazado'])
        logger.info(f"Total applications to process: {apps.count()}")
        
        # Process in batches to avoid memory issues
        batch_size = 1000
        app_ids = list(apps.values_list('id', flat=True))
        data = []
        for i in range(0, len(app_ids), batch_size):
            batch_ids = app_ids[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1} with {len(batch_ids)} applications")
            batch_result = self.process_batch.delay(batch_ids)
            batch_data = batch_result.get()  # Wait for the batch to complete
            data.extend(batch_data)
            logger.info(f"Batch {i // batch_size + 1} completed, {len(batch_data)} records processed")
        
        return data

    def train_model(self, df, test_size=0.2):
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.ensemble import RandomForestClassifier
        from joblib import dump

        if os.path.exists(self.model_file):
            logger.info("Modelo ya entrenado, omitiendo entrenamiento.")
            return

        # Definir el pipeline si no está ya definido
        if not hasattr(self, 'pipeline'):
            self.pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', RandomForestClassifier(random_state=42))
            ])

        X = df.drop(columns=["success"])
        y = df["success"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

        self.pipeline.fit(X_train, y_train)
        dump(self.pipeline, self.model_file)
        logger.info(f"✅ Modelo RandomForest entrenado y guardado en {self.model_file}")

        y_pred = self.pipeline.predict(X_test)
        report = classification_report(y_test, y_pred)
        logger.info(f"Reporte de clasificación:\n{report}")

    def predict_candidate_success(self, person, vacancy):
        from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage
        self.load_model()
        if not self.pipeline:
            raise FileNotFoundError("El modelo no está entrenado.")

        features = {
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
                if person.fecha_nacimiento else 0,
            'openness': person.openness,
            'conscientiousness': person.conscientiousness,
            'extraversion': person.extraversion,
            'agreeableness': person.agreeableness,
            'neuroticism': person.neuroticism
        }

        X = pd.DataFrame([features])
        proba = self.pipeline.predict_proba(X)[0][1]  # Probabilidad de éxito (clase 'hired')
        logger.info(f"Probabilidad de éxito para {person} en '{vacancy.titulo}': {proba:.2f}")
        return proba

    @shared_task(name='ml.predict_batch_matches', retry_backoff=True, retry_jitter=True, max_retries=3)
    def predict_batch(self, person_id, batch_vacancy_ids):
        """Predict matches for a batch of vacancies."""
        from app.models import Person, Vacante
        from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage
        person = Person.objects.get(id=person_id)
        batch_vacancies = Vacante.objects.filter(id__in=batch_vacancy_ids, status='activa')
        batch_predictions = []
        for vacancy in batch_vacancies:
            try:
                score = self.predict_candidate_success(person, vacancy)
                batch_predictions.append({
                    'vacancy_id': vacancy.id,
                    'score': score
                })
                logger.info(f"Predicted match for person {person_id} and vacancy {vacancy.id}: {score}")
            except Exception as e:
                logger.error(f"Error predicting match for person {person_id} and vacancy {vacancy.id}: {str(e)}")
        return batch_predictions

    def predict_all_active_matches(self, person, batch_size=50):
        """Predict matches for a person across all active vacancies with batch processing."""
        self.load_model()
        if not self.pipeline:
            raise FileNotFoundError("El modelo no está entrenado.")
        
        if self.business_unit:
            vacancies = Vacante.objects.filter(business_unit=self.business_unit, status='activa')
        else:
            vacancies = Vacante.objects.filter(status='activa')
        logger.info(f"Predicting matches for person {person.id} across {vacancies.count()} active vacancies")
        
        vacancy_ids = list(vacancies.values_list('id', flat=True))
        predictions = []
        for i in range(0, len(vacancy_ids), batch_size):
            batch_vacancy_ids = vacancy_ids[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1} with {len(batch_vacancy_ids)} vacancies")
            batch_result = self.predict_batch.delay(person.id, batch_vacancy_ids)
            batch_predictions = batch_result.get()  # Wait for the batch to complete
            predictions.extend(batch_predictions)
            logger.info(f"Batch {i // batch_size + 1} completed, {len(batch_predictions)} predictions made")
        
        sorted_predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)
        return sorted_predictions[:10]  # Return top 10 matches

    # Métodos internos (sin cambios, están bien)
    def _calculate_hard_skills_match(self, application):
        from app.ml.ml_utils import calculate_match_percentage
        person_skills = (application.person.skills or "").split(',')
        job_skills = application.vacancy.skills_required or []
        return calculate_match_percentage(person_skills, job_skills)

    def _calculate_soft_skills_match(self, application):
        person_soft_skills = set(application.person.metadata.get('soft_skills', []))
        job_soft_skills = set(application.vacancy.metadata.get('soft_skills', []))
        if not job_soft_skills:
            return 0.0
        return (len(person_soft_skills.intersection(job_soft_skills)) / len(job_soft_skills)) * 100

    def _calculate_salary_alignment(self, application):
        from app.ml.ml_utils import calculate_alignment_percentage
        current_salary = application.person.salary_data.get('current_salary', 0)
        offered_salary = application.vacancy.salario or 0
        return calculate_alignment_percentage(current_salary, offered_salary)

    def _calculate_age(self, person):
        if not person.fecha_nacimiento:
            return 0
        return (timezone.now().date() - person.fecha_nacimiento).days / 365

    def _calculate_hard_skills_match_mock(self, person, vacancy):
        from app.ml.ml_utils import calculate_match_percentage
        person_skills = (person.skills or "").split(',')
        job_skills = vacancy.skills_required or []
        return calculate_match_percentage(person_skills, job_skills)

    def _calculate_soft_skills_match_mock(self, person, vacancy):
        p_soft = set(person.metadata.get("soft_skills", []))
        v_soft = set(vacancy.metadata.get("soft_skills", []))
        if not v_soft:
            return 0.0
        return (len(p_soft.intersection(v_soft)) / len(v_soft)) * 100

    def _calculate_salary_alignment_mock(self, person, vacancy):
        from app.ml.ml_utils import calculate_alignment_percentage
        cur_sal = person.salary_data.get('current_salary', 0)
        off_sal = vacancy.salario or 0
        return calculate_alignment_percentage(cur_sal, off_sal)
    
    def calculate_personality_similarity(self, person, vacancy):
        # Obtener rasgos del candidato (suponiendo que están en person.personality_traits como dict)
        candidate_traits = person.personality_traits or {}
        # Generar rasgos deseados si no están definidos
        desired_traits = vacancy.rasgos_deseados or generate_desired_traits(vacancy.skills_required or [])
        
        if not desired_traits:
            return 0.0
        
        similarity = 0.0
        trait_count = 0
        for trait, desired_value in desired_traits.items():
            candidate_value = candidate_traits.get(trait, 0)
            # Normalizar la diferencia (asumiendo escala de 0 a 5)
            similarity += 1 - abs(candidate_value - desired_value) / 5
            trait_count += 1
        
        return similarity / trait_count if trait_count > 0 else 0.0

    def recommend_skill_improvements(self, person):
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
        insights = {
            'top_performing_skills': self._analyze_top_skills(),
            'success_rate_by_experience': self._analyze_experience_impact(),
            'salary_correlation': self._analyze_salary_impact()
        }
        logger.info(f"Insights trimestrales: {insights}")
        return insights

    def explain_prediction(self, person, vacancy):
        if not Path(self.model_file).exists():
            logger.error("Modelo no encontrado para explicar la predicción.")
            raise FileNotFoundError("Modelo no entrenado.")

        self.load_model()
        if not self._loaded_model:
            raise FileNotFoundError("El modelo no está cargado.")

        import shap
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

    def _identify_skill_gaps(self):
        return {
            'Python': 0.9,
            'Gestión de proyectos': 0.8,
            'Análisis de datos': 0.7
        }

    def _analyze_top_skills(self):
        from app.models import Application
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
        from app.models import Application
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
        from app.models import Application, Vacante
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
    
    def load_transition_model(self):
        """Carga o inicializa el modelo de predicción de transiciones."""
        if not self._loaded_transition_model and os.path.exists(self.transition_model_file):
            self._loaded_transition_model = load(self.transition_model_file)
            logger.info(f"Modelo de transición cargado desde {self.transition_model_file}")
        elif not os.path.exists(self.transition_model_file):
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline
            self.transition_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.transition_scaler = StandardScaler()
            self.transition_pipeline = Pipeline([
                ('scaler', self.transition_scaler),
                ('classifier', self.transition_model)
            ])
            logger.info("Modelo de transición RandomForest inicializado (no entrenado).")

    def prepare_transition_training_data(self):
        """Prepara datos para entrenar el modelo de transiciones entre BusinessUnits."""
        from app.models import Person, BusinessUnit, DivisionTransition
        # Datos de candidatos que han transicionado
        transitions = DivisionTransition.objects.select_related('person', 'from_business_unit', 'to_business_unit')
        data = []
        for transition in transitions:
            person = transition.person
            education_level = {
                'licenciatura': 1,
                'maestría': 2,
                'doctorado': 3
            }.get(person.metadata.get('education', [''])[0].lower(), 0)
            data.append({
                'experience_years': person.experience_years or 0,
                'skills_count': len(person.skills.split(',')) if person.skills else 0,
                'certifications_count': len(person.metadata.get('certifications', [])),
                'education_level': education_level,
                'openness': person.openness,
                'conscientiousness': person.conscientiousness,
                'extraversion': person.extraversion,
                'agreeableness': person.agreeableness,
                'neuroticism': person.neuroticism,
                'transition_label': 1 if transition.success else 0
            })
        # Datos de candidatos sin transiciones
        non_transitions = Person.objects.filter(divisiontransition__isnull=True)
        for person in non_transitions:
            education_level = {
                'licenciatura': 1,
                'maestría': 2,
                'doctorado': 3
            }.get(person.metadata.get('education', [''])[0].lower(), 0)
            data.append({
                'experience_years': person.experience_years or 0,
                'skills_count': len(person.skills.split(',')) if person.skills else 0,
                'certifications_count': len(person.metadata.get('certifications', [])),
                'education_level': education_level,
                'openness': person.openness,
                'conscientiousness': person.conscientiousness,
                'extraversion': person.extraversion,
                'agreeableness': person.agreeableness,
                'neuroticism': person.neuroticism,
                'transition_label': 0
            })
        df = pd.DataFrame(data)
        logger.info(f"Datos de transición preparados: {len(df)} registros.")
        return df

    def train_transition_model(self, df, test_size=0.2):
        """Entrena el modelo de transiciones con los datos preparados."""
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report
        X = df.drop(columns=["transition_label"])
        y = df["transition_label"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
        self.transition_pipeline.fit(X_train, y_train)
        dump(self.transition_pipeline, self.transition_model_file)
        logger.info(f"✅ Modelo de transición entrenado y guardado en {self.transition_model_file}")
        y_pred = self.transition_pipeline.predict(X_test)
        report = classification_report(y_test, y_pred)
        logger.info(f"Reporte de clasificación para transición:\n{report}")

    def predict_transition(self, person):
        """Predice la probabilidad de que un candidato esté listo para transicionar."""
        self.load_transition_model()
        if not self.transition_pipeline:
            raise FileNotFoundError("El modelo de transición no está entrenado.")
        education_level = {
            'licenciatura': 1,
            'maestría': 2,
            'doctorado': 3
        }.get(person.metadata.get('education', [''])[0].lower(), 0)
        features = {
            'experience_years': person.experience_years or 0,
            'skills_count': len(person.skills.split(',')) if person.skills else 0,
            'certifications_count': len(person.metadata.get('certifications', [])),
            'education_level': education_level,
            'openness': person.openness,
            'conscientiousness': person.conscientiousness,
            'extraversion': person.extraversion,
            'agreeableness': person.agreeableness,
            'neuroticism': person.neuroticism
        }
        X = pd.DataFrame([features])
        proba = self.transition_pipeline.predict_proba(X)[0][1]  # Probabilidad de transición
        logger.info(f"Probabilidad de transición para {person}: {proba:.2f}")
        return proba

    def get_possible_transitions(self, current_bu_name):
        """Obtiene las transiciones posibles desde la unidad de negocio actual."""
        current_level = BUSINESS_UNIT_HIERARCHY.get(current_bu_name.lower(), 0)
        possible_transitions = []
        for bu, level in BUSINESS_UNIT_HIERARCHY.items():
            if level > current_level:
                possible_transitions.append(bu)
        return possible_transitions
    
    async def calculate_market_alignment(self, features: Dict) -> Dict:
        """Calcula la alineación del candidato con el mercado laboral."""
        try:
            # Obtenemos datos del mercado
            market_data = await self._get_market_data()
            
            # Calculamos alineación por categoría
            alignment = {
                "skills": self._calculate_skills_alignment(features["skills"], market_data["skills"]),
                "experience": self._calculate_experience_alignment(features["experience"], market_data["experience"]),
                "salary": self._calculate_salary_alignment(features["salary_expectations"], market_data["salary"]),
                "personality": self._calculate_personality_alignment(features["personality_traits"], market_data["personality"])
            }
            
            # Calculamos score general
            alignment["overall_score"] = sum(alignment.values()) / len(alignment)
            
            return alignment
        except Exception as e:
            logger.error(f"Error calculando alineación con el mercado: {str(e)}", exc_info=True)
            return {}
    
    async def _get_market_data(self) -> Dict:
        """Obtiene datos actualizados del mercado laboral."""
        try:
            # Intentamos obtener de caché primero
            market_data = cache.get("market_data")
            if market_data:
                return market_data
            
            # Si no está en caché, lo generamos
            market_data = {
                "skills": await self._analyze_market_skills(),
                "experience": await self._analyze_market_experience(),
                "salary": await self._analyze_market_salaries(),
                "personality": await self._analyze_market_personality()
            }
            
            # Guardamos en caché por 24 horas
            cache.set("market_data", market_data, 86400)
            
            return market_data
        except Exception as e:
            logger.error(f"Error obteniendo datos del mercado: {str(e)}", exc_info=True)
            return {}
    
    async def _analyze_market_skills(self) -> Dict:
        """Analiza las habilidades más demandadas en el mercado."""
        try:
            from app.models import Vacancy, Skill
            
            # Obtenemos todas las vacantes activas
            vacancies = Vacancy.objects.filter(status="active")
            
            # Analizamos habilidades requeridas
            skills_analysis = {}
            for vacancy in vacancies:
                for skill in vacancy.required_skills.all():
                    skills_analysis[skill.name] = skills_analysis.get(skill.name, 0) + 1
            
            # Normalizamos y ordenamos
            total_vacancies = vacancies.count()
            return {
                skill: count/total_vacancies 
                for skill, count in sorted(
                    skills_analysis.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
            }
        except Exception as e:
            logger.error(f"Error analizando habilidades del mercado: {str(e)}", exc_info=True)
            return {}
    
    async def _analyze_market_experience(self) -> Dict:
        """Analiza los requisitos de experiencia en el mercado."""
        try:
            from app.models import Vacancy
            
            # Obtenemos todas las vacantes activas
            vacancies = Vacancy.objects.filter(status="active")
            
            # Analizamos rangos de experiencia
            experience_ranges = {
                "0-2": 0,
                "2-5": 0,
                "5-10": 0,
                "10+": 0
            }
            
            for vacancy in vacancies:
                exp_years = vacancy.experience_years or 0
                if exp_years <= 2:
                    experience_ranges["0-2"] += 1
                elif exp_years <= 5:
                    experience_ranges["2-5"] += 1
                elif exp_years <= 10:
                    experience_ranges["5-10"] += 1
                else:
                    experience_ranges["10+"] += 1
            
            # Normalizamos
            total_vacancies = vacancies.count()
            return {
                range_name: count/total_vacancies 
                for range_name, count in experience_ranges.items()
            }
        except Exception as e:
            logger.error(f"Error analizando experiencia del mercado: {str(e)}", exc_info=True)
            return {}
    
    async def _analyze_market_salaries(self) -> Dict:
        """Analiza los rangos salariales en el mercado."""
        try:
            from app.models import Vacancy
            
            # Obtenemos todas las vacantes activas
            vacancies = Vacancy.objects.filter(status="active")
            
            # Analizamos rangos salariales
            salary_ranges = {
                "0-30000": 0,
                "30000-60000": 0,
                "60000-90000": 0,
                "90000+": 0
            }
            
            for vacancy in vacancies:
                salary = vacancy.salario or 0
                if salary <= 30000:
                    salary_ranges["0-30000"] += 1
                elif salary <= 60000:
                    salary_ranges["30000-60000"] += 1
                elif salary <= 90000:
                    salary_ranges["60000-90000"] += 1
                else:
                    salary_ranges["90000+"] += 1
            
            # Normalizamos
            total_vacancies = vacancies.count()
            return {
                range_name: count/total_vacancies 
                for range_name, count in salary_ranges.items()
            }
        except Exception as e:
            logger.error(f"Error analizando salarios del mercado: {str(e)}", exc_info=True)
            return {}
    
    async def _analyze_market_personality(self) -> Dict:
        """Analiza los rasgos de personalidad más valorados en el mercado."""
        try:
            from app.models import Vacancy
            
            # Obtenemos todas las vacantes activas
            vacancies = Vacancy.objects.filter(status="active")
            
            # Analizamos rasgos de personalidad
            personality_traits = {}
            for vacancy in vacancies:
                for trait in vacancy.metadata.get("personality_traits", []):
                    personality_traits[trait] = personality_traits.get(trait, 0) + 1
            
            # Normalizamos y ordenamos
            total_vacancies = vacancies.count()
            return {
                trait: count/total_vacancies 
                for trait, count in sorted(
                    personality_traits.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
            }
        except Exception as e:
            logger.error(f"Error analizando personalidad del mercado: {str(e)}", exc_info=True)
            return {}
    
    def _calculate_skills_alignment(self, candidate_skills: List[str], market_skills: Dict) -> float:
        """Calcula la alineación de habilidades del candidato con el mercado."""
        try:
            if not candidate_skills or not market_skills:
                return 0.0
            
            # Calculamos score para cada habilidad
            total_score = 0.0
            for skill in candidate_skills:
                total_score += market_skills.get(skill, 0)
            
            # Normalizamos
            return total_score / len(candidate_skills)
        except Exception as e:
            logger.error(f"Error calculando alineación de habilidades: {str(e)}", exc_info=True)
            return 0.0
    
    def _calculate_experience_alignment(self, candidate_experience: List[Dict], market_experience: Dict) -> float:
        """Calcula la alineación de experiencia del candidato con el mercado."""
        try:
            if not candidate_experience or not market_experience:
                return 0.0
            
            # Calculamos años totales de experiencia
            total_years = sum(exp.get("years", 0) for exp in candidate_experience)
            
            # Determinamos el rango
            if total_years <= 2:
                range_key = "0-2"
            elif total_years <= 5:
                range_key = "2-5"
            elif total_years <= 10:
                range_key = "5-10"
            else:
                range_key = "10+"
            
            return market_experience.get(range_key, 0)
        except Exception as e:
            logger.error(f"Error calculando alineación de experiencia: {str(e)}", exc_info=True)
            return 0.0
    
    def _calculate_salary_alignment(self, candidate_salary: Dict, market_salary: Dict) -> float:
        """Calcula la alineación salarial del candidato con el mercado."""
        try:
            if not candidate_salary or not market_salary:
                return 0.0
            
            expected_salary = candidate_salary.get("expected", 0)
            
            # Determinamos el rango
            if expected_salary <= 30000:
                range_key = "0-30000"
            elif expected_salary <= 60000:
                range_key = "30000-60000"
            elif expected_salary <= 90000:
                range_key = "60000-90000"
            else:
                range_key = "90000+"
            
            return market_salary.get(range_key, 0)
        except Exception as e:
            logger.error(f"Error calculando alineación salarial: {str(e)}", exc_info=True)
            return 0.0
    
    def _calculate_personality_alignment(self, candidate_traits: Dict, market_traits: Dict) -> float:
        """Calcula la alineación de personalidad del candidato con el mercado."""
        try:
            if not candidate_traits or not market_traits:
                return 0.0
            
            # Calculamos score para cada rasgo
            total_score = 0.0
            for trait, value in candidate_traits.items():
                total_score += market_traits.get(trait, 0) * value
            
            # Normalizamos
            return total_score / len(candidate_traits)
        except Exception as e:
            logger.error(f"Error calculando alineación de personalidad: {str(e)}", exc_info=True)
            return 0.0
    
    def _initialize_models(self) -> None:
        """
        Inicializa los modelos con datos de entrenamiento.
        
        Este método carga los datos de entrenamiento y entrena los modelos
        específicos para personalidad y profesional.
        """
        try:
            # Aquí se cargarían los datos de entrenamiento y se entrenarían los modelos
            # Por ahora, los modelos se inicializan vacíos
            pass
        except Exception as e:
            logger.error(f"Error inicializando modelos: {str(e)}")

    def predict_compatibility(self, traits: Dict[str, float]) -> Dict[str, float]:
        """
        Predice la compatibilidad con diferentes perfiles.
        
        Args:
            traits: Diccionario con rasgos de personalidad
            
        Returns:
            Dict con puntuaciones de compatibilidad
        """
        try:
            # Convertir rasgos a vector
            trait_vector = self._dict_to_vector(traits)
            
            # Normalizar vector
            normalized_vector = self.scaler.transform([trait_vector])[0]
            
            # Predecir compatibilidad
            compatibility_scores = self.personality_model.predict_proba([normalized_vector])[0]
            
            # Mapear scores a perfiles
            profiles = ['Analítico', 'Creativo', 'Social', 'Estructurado']
            return dict(zip(profiles, compatibility_scores))
            
        except Exception as e:
            logger.error(f"Error prediciendo compatibilidad: {str(e)}")
            return {}

    def _dict_to_vector(self, data: Dict[str, float]) -> np.ndarray:
        """
        Convierte un diccionario de características a vector numpy.
        
        Args:
            data: Diccionario con características
            
        Returns:
            Vector numpy con las características
        """
        return np.array(list(data.values()))

def main():
    pipeline = MatchmakingModel(business_unit='huntRED®')
    data = pipeline.prepare_training_data()
    X_train, X_test, y_train, y_test = pipeline.preprocess_data(data)
    pipeline.train_model(X_train, y_train, X_test, y_test)
    from app.models import Person
    person = Person.objects.first()
    if person:
        matches = pipeline.predict_all_active_matches(person)
        logger.info(f"Coincidencias para {person.nombre}: {matches}")

if __name__ == "__main__":
    main()