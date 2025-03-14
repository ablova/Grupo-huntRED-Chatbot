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

logger = logging.getLogger(__name__)

class MatchmakingLearningSystem:
    def __init__(self, business_unit=None):
        self.business_unit = business_unit
        self.model = None
        self.scaler = None
        self.model_file = os.path.join(
            settings.ML_MODELS_DIR,
            f"matchmaking_model_{business_unit or 'global'}.pkl"
        )
        self._loaded_model = None

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

    def prepare_training_data(self):
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
        from app.ml.ml_opt import configure_tensorflow_based_on_load
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report, precision_score, recall_score, f1_score
        configure_tensorflow_based_on_load()
        if os.path.exists(self.model_file):
            logger.info("Modelo ya entrenado, omitiendo entrenamiento.")
            return
        self.load_model()
        X = df.drop(columns=["is_successful"])
        y = df["is_successful"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        self.pipeline.fit(X_train, y_train)
        dump(self.pipeline, self.model_file)
        logger.info(f"✅ Modelo RandomForest entrenado y guardado en {self.model_file}")

        y_pred = self.pipeline.predict(X_test)
        report = classification_report(y_test, y_pred)
        logger.info(f"Reporte de clasificación:\n{report}")
        logger.info(f"Precisión: {precision_score(y_test, y_pred, zero_division=0):.2f}")
        logger.info(f"Recall: {recall_score(y_test, y_pred, zero_division=0):.2f}")
        logger.info(f"F1-Score: {f1_score(y_test, y_pred, zero_division=0):.2f}")

        gc.collect()

    def predict_candidate_success(self, person, vacancy):
        self.load_model()
        if not self._loaded_model:
            raise FileNotFoundError("El modelo no está entrenado.")

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

    def predict_all_active_matches(self, person, batch_size=50):
        from app.models import Vacante
        from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage
        self.load_model()
        if not self._loaded_model:
            raise FileNotFoundError("El modelo no está entrenado.")

        bu = person.current_stage.business_unit if person.current_stage else None
        if not bu:
            logger.info(f"No se encontró BU para la persona {person.id}")
            return []

        active_vacancies = Vacante.objects.select_related('business_unit').filter(
            activa=True, business_unit=bu
        )
        if not active_vacancies.exists():
            logger.info(f"No hay vacantes activas para BU {bu.id}")
            return []

        results = []
        total_vacancies = active_vacancies.count()
        logger.info(f"Procesando {total_vacancies} vacantes para persona {person.id}")

        for i in range(0, total_vacancies, batch_size):
            batch = active_vacancies[i:i + batch_size]
            batch_results = []

            for vacante in batch:
                cache_key = f"match_{person.id}_{vacante.id}"
                cached_result = cache.get(cache_key)
                
                if cached_result is not None:
                    batch_results.append(cached_result)
                    continue

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
                    
                    X = pd.DataFrame([features])
                    X_scaled = self.scaler.transform(X)
                    prediction = (self._loaded_model.predict(X_scaled).flatten() * 100)[0]
                    result = {
                        "vacante": vacante.titulo,
                        "empresa": vacante.empresa,
                        "score": round(prediction, 2)
                    }
                    
                    cache.set(cache_key, result, timeout=3600)
                    batch_results.append(result)
                except Exception as e:
                    logger.warning(f"Error procesando vacante {vacante.id}: {str(e)}")
                    continue

            results.extend(batch_results)

        return sorted(results, key=lambda x: x["score"], reverse=True)

    async def predict_top_candidates(self, vacancy=None, limit=5):
        """
        Predice los mejores candidatos para una vacante específica o globalmente.
        :param vacancy: Objeto Vacante (opcional). Si es None, evalúa todas las vacantes activas.
        :param limit: Número máximo de candidatos a devolver.
        :return: Lista de tuplas (Person, score) ordenada por score descendente.
        """
        from app.models import Person, Vacante
        from asgiref.sync import sync_to_async
        self.load_model()
        if not self._loaded_model:
            logger.warning("Modelo no entrenado. No se pueden predecir candidatos.")
            return []

        # Obtener todos los candidatos (Person) activos
        candidates = await sync_to_async(
            lambda: list(Person.objects.filter(is_active=True))
        )()

        if not candidates:
            logger.info("No hay candidatos activos disponibles.")
            return []

        # Si se proporciona una vacante específica
        if vacancy:
            results = []
            for person in candidates:
                try:
                    score = self.predict_candidate_success(person, vacancy)
                    results.append((person, score))
                except Exception as e:
                    logger.error(f"Error prediciendo para {person.id}: {e}")
                    continue
            return sorted(results, key=lambda x: x[1], reverse=True)[:limit]

        # Si no hay vacante específica, evaluar contra todas las vacantes activas
        active_vacancies = await sync_to_async(
            lambda: list(Vacante.objects.filter(
                activa=True,
                business_unit=self.business_unit if self.business_unit else None
            ))
        )()

        if not active_vacancies:
            logger.info(f"No hay vacantes activas para BU {self.business_unit or 'global'}.")
            return []

        # Calcular el mejor score promedio por candidato
        results = {}
        for person in candidates:
            total_score = 0
            count = 0
            for vacancy in active_vacancies:
                try:
                    score = self.predict_candidate_success(person, vacancy)
                    total_score += score
                    count += 1
                except Exception as e:
                    logger.error(f"Error prediciendo para {person.id} en vacante {vacancy.id}: {e}")
                    continue
            if count > 0:
                avg_score = total_score / count
                results[person] = avg_score

        # Ordenar y devolver los mejores candidatos
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        logger.info(f"Top {limit} candidatos predichos: {[f'{p.nombre}: {s:.2f}' for p, s in sorted_results[:limit]]}")
        return sorted_results[:limit]

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

class GrupohuntREDMLPipeline:
    model_config = {
        'huntRED®': {'layers': [256, 128, 64], 'learning_rate': 0.001, 'dropout_rate': 0.3},
        'huntU': {'layers': [128, 64], 'learning_rate': 0.0005, 'dropout_rate': 0.2},
        'Amigro': {'layers': [128, 64, 32], 'learning_rate': 0.0008, 'dropout_rate': 0.25}
    }

    def __init__(self, business_unit='huntRED®', log_dir='./ml_logs'):
        os.makedirs(log_dir, exist_ok=True)
        self.business_unit = business_unit
        self.model_path = os.path.join(settings.ML_MODELS_DIR, f'{business_unit}_model.h5')
        self.scaler_path = os.path.join(settings.ML_MODELS_DIR, f'{business_unit}_scaler.pkl')
        self.model = None
        self.scaler = None

    def load_tensorflow(self):
        try:
            import tensorflow as tf
            tf.config.threading.set_intra_op_parallelism_threads(1)
            tf.config.threading.set_inter_op_parallelism_threads(1)
            logger.info("✅ TensorFlow cargado bajo demanda para Keras.")
            return tf
        except ImportError:
            logger.error("⚠ TensorFlow no está disponible para Keras.")
            return None

    def build_model(self, input_dim):
        tf = self.load_tensorflow()
        if not tf:
            raise ImportError("TensorFlow es requerido para construir el modelo Keras.")
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Dense, Dropout
        from tensorflow.keras.optimizers import Adam
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
        from app.models import Application
        from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage
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
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        if 'success_label' not in df.columns:
            raise ValueError("Falta la columna 'success_label' en los datos.")
        X = df.drop(columns=['success_label'])
        y = df['success_label']
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        dump(self.scaler, self.scaler_path)
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        return X_train, X_test, y_train, y_test

    def train_model(self, X_train, y_train, X_test, y_test):
        if self.model is None:
            self.build_model(input_dim=X_train.shape[1])
        from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint, TensorBoard
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
        from tensorflow.keras.models import load_model
        if os.path.exists(self.model_path):
            self.model = load_model(self.model_path)
            logger.info(f"Modelo Keras cargado desde {self.model_path}.")
        else:
            logger.warning("No se encontró un modelo entrenado. Se construirá uno nuevo.")
            self.build_model(input_dim=5)
        if os.path.exists(self.scaler_path):
            self.scaler = load(self.scaler_path)
        else:
            from sklearn.preprocessing import StandardScaler
            self.scaler = StandardScaler()
            logger.warning("Scaler no encontrado. Se usará un scaler no entrenado.")

    def predict_candidate_success(self, person, vacancy):
        from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage
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
        from app.models import Vacante
        from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage
        self.load_model()
        bu = person.current_stage.business_unit if person.current_stage else None
        if not bu:
            return []
        active_vacancies = Vacante.objects.filter(activa=True, business_unit=bu)
        if not active_vacancies.exists():
            return []
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

    def predict_pending(self):
        from app.models import Application
        pending_apps = Application.objects.filter(
            vacancy__business_unit__name=self.business_unit,
            status='pendiente'
        ).select_related('person', 'vacancy')
        
        if not pending_apps.exists():
            logger.info(f"No hay aplicaciones pendientes para {self.business_unit}.")
            return []

        predictions = []
        for app in pending_apps:
            probability = self.predict_candidate_success(app.person, app.vacancy)
            predictions.append({
                'application_id': app.id,
                'candidate': app.person.nombre,
                'vacancy': app.vacancy.titulo,
                'probability': probability
            })
            logger.info(f"Predicción realizada para aplicación {app.id}: {probability:.2%}")

        return predictions
    
class AdaptiveMLFramework(GrupohuntREDMLPipeline):
    def __init__(self, business_unit):
        super().__init__(business_unit)
        self.model_path = os.path.join(settings.ML_MODELS_DIR, f'{business_unit}_adaptive_model.h5')

    def train_and_optimize(self, X, y, validation_split=0.2):
        from sklearn.model_selection import train_test_split
        from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
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
        val_loss, val_acc = self.model.evaluate(X_val, y_val, verbose=0)
        logger.info(f"Entrenamiento completado - Val Loss: {val_loss:.4f}, Val Accuracy: {val_acc:.4f}")
        logger.info(f"Modelo guardado en {self.model_path}")

    def predict_and_explain(self, X_new):
        from tensorflow.keras.models import load_model
        import shap
        if self.model is None:
            self.model = load_model(self.model_path)
        self.scaler = load(self.scaler_path)
        X_scaled = self.scaler.transform(X_new)
        predictions = self.model.predict(X_scaled)
        explainer = shap.KernelExplainer(self.model.predict, X_scaled[:50])
        shap_values = explainer.shap_values(X_scaled)
        return {'predictions': predictions, 'shap_values': shap_values}

def main():
    pipeline = GrupohuntREDMLPipeline(business_unit='huntRED®')
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