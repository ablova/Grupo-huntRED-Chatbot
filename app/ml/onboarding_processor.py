"""
Procesador de datos de onboarding para modelos de Machine Learning.
Extrae, transforma y prepara datos de satisfacción y retención para
alimentar los modelos predictivos del sistema.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
import json
from datetime import datetime, timedelta
import os
import logging
from django.conf import settings
from django.db.models import Q, F, Count, Avg
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Imports de modelos
from app.models import (
    OnboardingProcess, Person, Vacante, Company, 
    BusinessUnit, OnboardingTask
)

logger = logging.getLogger(__name__)

class OnboardingMLProcessor:
    """Procesa datos de onboarding para alimentar modelos de ML"""
    
    def __init__(self):
        # Asegurar que existan los directorios necesarios
        self.base_dir = os.path.join(settings.BASE_DIR, 'app', 'ml')
        self.data_dir = os.path.join(self.base_dir, 'data', 'onboarding')
        self.models_dir = os.path.join(self.base_dir, 'models', 'onboarding')
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Cargar modelos existentes o crear nuevos
        self.retention_model = self._load_model('retention_model.joblib')
        self.satisfaction_predictor = self._load_model('satisfaction_predictor.joblib')
    
    def _load_model(self, model_name: str):
        """Carga un modelo desde disco o crea uno nuevo si no existe"""
        model_path = os.path.join(self.models_dir, model_name)
        try:
            if os.path.exists(model_path):
                return joblib.load(model_path)
        except Exception as e:
            logger.error(f"Error cargando modelo {model_name}: {e}")
        
        # Si falla o no existe, retornar None
        return None
    
    def _save_model(self, model, model_name: str):
        """Guarda un modelo en disco"""
        model_path = os.path.join(self.models_dir, model_name)
        try:
            joblib.dump(model, model_path)
            logger.info(f"Modelo {model_name} guardado exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error guardando modelo {model_name}: {e}")
            return False
    
    async def process_satisfaction_data(self) -> Dict:
        """
        Procesa todos los datos de satisfacción disponibles y los prepara para ML.
        Extrae datos, los transforma, y guarda en CSV para entrenar modelos.
        """
        try:
            # Obtener procesos de onboarding con encuestas
            processes = OnboardingProcess.objects.filter(
                survey_responses__isnull=False
            ).select_related(
                'person', 'vacancy', 'vacancy__company', 
                'vacancy__businessunit'
            )
            
            if not processes:
                return {'success': False, 'message': 'No hay datos para procesar'}
                
            # Preparar datos
            all_data = []
            
            for process in processes:
                if not process.survey_responses:
                    continue
                    
                responses = process.get_responses()
                for period, survey in responses.items():
                    # Datos básicos
                    row = {
                        'onboarding_id': process.id,
                        'person_id': process.person.id,
                        'vacancy_id': process.vacancy.id,
                        'company_id': process.vacancy.company.id,
                        'businessunit_id': process.vacancy.businessunit_id if hasattr(process.vacancy, 'businessunit') else None,
                        'businessunit_name': process.vacancy.businessunit.name if hasattr(process.vacancy, 'businessunit') else None,
                        'hire_date': process.hire_date.isoformat(),
                        'survey_period': int(period),
                        'completed_surveys': process.completed_surveys
                    }
                    
                    # Añadir respuestas de encuesta
                    for question_id, response in survey.items():
                        if isinstance(response, dict) and 'value' in response:
                            row[f'q_{question_id}'] = response['value']
                            # Añadir timestamp si está disponible
                            if 'timestamp' in response:
                                row[f'q_{question_id}_timestamp'] = response['timestamp']
                    
                    # Añadir datos de persona
                    person = process.person
                    row['person_experience'] = getattr(person, 'experience_years', None)
                    row['person_age'] = getattr(person, 'age', None)
                    row['person_gender'] = getattr(person, 'gender', None)
                    
                    # Añadir datos de vacante
                    vacancy = process.vacancy
                    row['vacancy_title'] = vacancy.title
                    row['vacancy_salary'] = getattr(vacancy, 'salary', None)
                    row['vacancy_remote'] = getattr(vacancy, 'is_remote', False)
                    
                    # Añadir datos de empresa
                    company = vacancy.company
                    row['company_name'] = company.name
                    row['company_size'] = getattr(company, 'employee_count', None)
                    row['company_industry'] = getattr(company, 'industry', None)
                    
                    # Calcular satisfacción numérica
                    row['satisfaction_score'] = process.get_satisfaction_score(int(period))
                    
                    all_data.append(row)
                    
            # Crear DataFrame
            if not all_data:
                return {'success': False, 'message': 'No hay datos transformados para procesar'}
                
            df = pd.DataFrame(all_data)
            
            # Guardar como CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"onboarding_satisfaction_{timestamp}.csv"
            file_path = os.path.join(self.data_dir, filename)
            df.to_csv(file_path, index=False)
            
            # Análisis básico
            satisfaction_analysis = self._analyze_satisfaction(df)
            
            # Intentar entrenar modelos si hay suficientes datos
            if len(df) >= 30:  # Umbral mínimo para entrenar
                training_results = await self.train_models(df)
            else:
                training_results = {'trained': False, 'reason': 'Datos insuficientes'}
            
            return {
                'success': True,
                'file_path': file_path,
                'row_count': len(df),
                'analysis': satisfaction_analysis,
                'training': training_results,
                'message': f'Datos procesados y guardados en {filename}'
            }
            
        except Exception as e:
            logger.error(f"Error procesando datos de satisfacción: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Error procesando datos de satisfacción'
            }
    
    def _analyze_satisfaction(self, df: pd.DataFrame) -> Dict:
        """Realiza análisis estadístico de datos de satisfacción"""
        analysis = {}
        
        # Solo proceder si tenemos columna de satisfacción
        if 'satisfaction_score' not in df.columns:
            return {'error': 'No hay datos de satisfacción'}
        
        # Eliminar filas con valores nulos en satisfacción
        df_clean = df.dropna(subset=['satisfaction_score'])
        if len(df_clean) == 0:
            return {'error': 'No hay datos válidos de satisfacción'}
        
        # Estadísticas básicas
        analysis['global_stats'] = {
            'mean': df_clean['satisfaction_score'].mean(),
            'median': df_clean['satisfaction_score'].median(),
            'std': df_clean['satisfaction_score'].std(),
            'min': df_clean['satisfaction_score'].min(),
            'max': df_clean['satisfaction_score'].max(),
            'count': len(df_clean)
        }
        
        # Análisis por período
        if 'survey_period' in df_clean.columns:
            period_stats = df_clean.groupby('survey_period')['satisfaction_score'].agg(['mean', 'count']).reset_index()
            analysis['by_period'] = period_stats.to_dict(orient='records')
        
        # Análisis por BU
        if 'businessunit_name' in df_clean.columns:
            bu_stats = df_clean.groupby('businessunit_name')['satisfaction_score'].agg(['mean', 'count']).reset_index()
            analysis['by_bu'] = bu_stats.to_dict(orient='records')
        
        # Análisis por industria
        if 'company_industry' in df_clean.columns:
            industry_stats = df_clean.groupby('company_industry')['satisfaction_score'].agg(['mean', 'count']).reset_index()
            analysis['by_industry'] = industry_stats.to_dict(orient='records')
        
        return analysis
    
    async def train_models(self, data: Union[pd.DataFrame, str]) -> Dict:
        """
        Entrena modelos de ML con datos de satisfacción.
        Puede recibir un DataFrame o ruta a archivo CSV.
        """
        try:
            # Cargar datos si se proporciona ruta
            if isinstance(data, str):
                if os.path.exists(data):
                    df = pd.read_csv(data)
                else:
                    return {'success': False, 'error': 'Archivo no encontrado'}
            else:
                df = data.copy()
            
            results = {}
            
            # Entrenar modelo de predicción de satisfacción
            satisfaction_result = await self._train_satisfaction_predictor(df)
            results['satisfaction_predictor'] = satisfaction_result
            
            # Entrenar modelo de predicción de retención
            retention_result = await self._train_retention_predictor(df)
            results['retention_predictor'] = retention_result
            
            return {
                'success': True,
                'models_trained': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error entrenando modelos: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _train_satisfaction_predictor(self, df: pd.DataFrame) -> Dict:
        """Entrena modelo para predecir satisfacción futura basada en datos tempranos"""
        try:
            # Verificar si hay suficientes datos
            if len(df) < 30:
                return {'trained': False, 'reason': 'Datos insuficientes'}
                
            # Preparar datos para entrenamiento
            # Necesitamos predecir satisfacción en períodos tardíos usando datos de períodos tempranos
            
            # 1. Filtrar sólo filas con satisfacción y período
            df_clean = df.dropna(subset=['satisfaction_score', 'survey_period'])
            
            # 2. Identificar personas con múltiples encuestas
            person_surveys = df_clean.groupby('person_id')['survey_period'].nunique()
            multi_survey_persons = person_surveys[person_surveys > 1].index
            
            # 3. Filtrar solo personas con múltiples encuestas
            df_multi = df_clean[df_clean['person_id'].isin(multi_survey_persons)]
            
            if len(df_multi) < 30:
                return {'trained': False, 'reason': 'Insuficientes datos de series temporales'}
            
            # 4. Preparar features y target
            # Para cada persona, usamos datos de primera encuesta para predecir última
            X_data = []
            y_data = []
            
            for person_id in multi_survey_persons:
                person_df = df_multi[df_multi['person_id'] == person_id].sort_values('survey_period')
                
                if len(person_df) < 2:
                    continue
                    
                # Usar primera encuesta como features
                first_survey = person_df.iloc[0]
                # Usar última encuesta como target
                last_survey = person_df.iloc[-1]
                
                # Extraer features numéricas y categóricas relevantes
                feature_row = {}
                
                # Features básicas
                for feature in ['person_experience', 'person_age', 'survey_period', 'vacancy_salary']:
                    if feature in first_survey:
                        feature_row[feature] = first_survey[feature]
                
                # Features calculadas
                if 'satisfaction_score' in first_survey:
                    feature_row['initial_satisfaction'] = first_survey['satisfaction_score']
                
                # Variable objetivo: satisfacción final
                target = last_survey['satisfaction_score'] if 'satisfaction_score' in last_survey else None
                
                if target is not None and not pd.isna(target) and len(feature_row) > 0:
                    X_data.append(feature_row)
                    y_data.append(target)
            
            if len(X_data) < 20:
                return {'trained': False, 'reason': 'Insuficientes datos de entrenamiento válidos'}
            
            # Convertir a DataFrame para facilitar manejo
            X = pd.DataFrame(X_data)
            y = np.array(y_data)
            
            # Dividir en train/test
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Crear pipeline con preprocesamiento
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('model', GradientBoostingRegressor(random_state=42))
            ])
            
            # Entrenar modelo
            pipeline.fit(X_train, y_train)
            
            # Evaluar modelo
            train_score = pipeline.score(X_train, y_train)
            test_score = pipeline.score(X_test, y_test)
            
            # Guardar modelo
            self.satisfaction_predictor = pipeline
            saved = self._save_model(pipeline, 'satisfaction_predictor.joblib')
            
            return {
                'trained': True,
                'train_score': train_score,
                'test_score': test_score,
                'samples': len(X),
                'features': list(X.columns),
                'model_saved': saved
            }
            
        except Exception as e:
            logger.error(f"Error entrenando predictor de satisfacción: {e}")
            return {
                'trained': False,
                'error': str(e)
            }
    
    async def _train_retention_predictor(self, df: pd.DataFrame) -> Dict:
        """Entrena modelo para predecir probabilidad de retención basado en satisfacción"""
        try:
            # Verificar si tenemos datos de terminación para algún proceso
            terminated_processes = OnboardingProcess.objects.filter(
                status='terminated'
            ).values_list('id', flat=True)
            
            # Si no hay procesos terminados, no podemos entrenar
            if not terminated_processes.exists():
                return {'trained': False, 'reason': 'No hay datos de procesos terminados'}
            
            # Preparar datos combinando procesos activos (retenidos) y terminados (rotación)
            retention_data = []
            
            # 1. Obtener todos los procesos con suficiente antigüedad
            min_age_days = 30  # Mínimo 30 días para considerar retención
            cutoff_date = datetime.now() - timedelta(days=min_age_days)
            
            all_processes = OnboardingProcess.objects.filter(
                hire_date__lt=cutoff_date
            ).select_related(
                'person', 'vacancy', 'vacancy__company', 
                'vacancy__businessunit'
            )
            
            for process in all_processes:
                # Target: 1 si sigue activo (retenido), 0 si terminó (rotación)
                is_retained = process.status != 'terminated'
                
                # Calcular datos clave
                days_employed = (datetime.now() - process.hire_date.replace(tzinfo=None)).days
                if not is_retained and process.end_date:
                    days_employed = (process.end_date.replace(tzinfo=None) - process.hire_date.replace(tzinfo=None)).days
                
                # Obtener satisfacción si existe
                satisfaction = process.get_satisfaction_score()
                
                # Obtener otros datos relevantes
                row = {
                    'onboarding_id': process.id,
                    'person_id': process.person.id,
                    'vacancy_id': process.vacancy.id,
                    'is_retained': int(is_retained),  # Target variable
                    'days_employed': days_employed,
                    'satisfaction_score': satisfaction,
                    'completed_surveys': process.completed_surveys
                }
                
                # Añadir datos de persona
                person = process.person
                row['person_experience'] = getattr(person, 'experience_years', None)
                row['person_age'] = getattr(person, 'age', None)
                
                # Añadir datos de vacante
                vacancy = process.vacancy
                row['vacancy_salary'] = getattr(vacancy, 'salary', None)
                row['vacancy_remote'] = int(getattr(vacancy, 'is_remote', False))
                
                # Añadir datos de empresa
                company = vacancy.company
                row['company_size'] = getattr(company, 'employee_count', None)
                
                retention_data.append(row)
            
            # Convertir a DataFrame
            retention_df = pd.DataFrame(retention_data)
            
            # Eliminar filas con valores nulos en columnas críticas
            retention_df = retention_df.dropna(subset=['days_employed'])
            
            if len(retention_df) < 20:
                return {'trained': False, 'reason': 'Datos insuficientes para modelo de retención'}
            
            # Preparar features y target
            features = ['satisfaction_score', 'days_employed', 'person_experience', 
                        'person_age', 'vacancy_salary', 'vacancy_remote', 
                        'company_size', 'completed_surveys']
            
            # Usar solo features disponibles
            features = [f for f in features if f in retention_df.columns]
            
            X = retention_df[features].copy()
            y = retention_df['is_retained'].values
            
            # Manejar valores nulos
            X = X.fillna(X.mean())
            
            # Dividir en train/test
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
            
            # Crear y entrenar modelo
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('model', RandomForestClassifier(random_state=42))
            ])
            
            pipeline.fit(X_train, y_train)
            
            # Evaluar modelo
            train_score = pipeline.score(X_train, y_train)
            test_score = pipeline.score(X_test, y_test)
            
            # Guardar modelo
            self.retention_model = pipeline
            saved = self._save_model(pipeline, 'retention_model.joblib')
            
            return {
                'trained': True,
                'train_score': train_score,
                'test_score': test_score,
                'samples': len(X),
                'features': list(X.columns),
                'model_saved': saved
            }
            
        except Exception as e:
            logger.error(f"Error entrenando predictor de retención: {e}")
            return {
                'trained': False,
                'error': str(e)
            }
    
    async def predict_satisfaction(self, person_id: int, vacancy_id: int) -> Dict:
        """
        Predice satisfacción futura para un candidato específico
        basado en datos actuales y históricos.
        """
        try:
            # Verificar si tenemos el modelo entrenado
            if self.satisfaction_predictor is None:
                return {
                    'predicted': False,
                    'error': 'Modelo de predicción no disponible'
                }
                
            # Obtener proceso de onboarding
            try:
                process = OnboardingProcess.objects.get(
                    person_id=person_id, 
                    vacancy_id=vacancy_id
                )
            except OnboardingProcess.DoesNotExist:
                return {
                    'predicted': False,
                    'error': 'Proceso de onboarding no encontrado'
                }
            
            # Obtener datos necesarios para predicción
            person = process.person
            vacancy = process.vacancy
            
            # Obtener satisfacción actual si existe
            current_satisfaction = process.get_satisfaction_score()
            
            # Preparar features para predicción
            features = {
                'person_experience': getattr(person, 'experience_years', 0),
                'person_age': getattr(person, 'age', 30),  # Valor por defecto
                'survey_period': process.completed_surveys,
                'vacancy_salary': getattr(vacancy, 'salary', 15000),  # Valor por defecto
                'initial_satisfaction': current_satisfaction
            }
            
            # Manejar valores nulos
            for key, value in features.items():
                if value is None:
                    if key == 'initial_satisfaction':
                        features[key] = 7.5  # Valor neutral
                    else:
                        features[key] = 0
            
            # Crear DataFrame con un solo registro
            X_pred = pd.DataFrame([features])
            
            # Realizar predicción
            prediction = self.satisfaction_predictor.predict(X_pred)[0]
            
            # Asegurar que predicción está en rango válido (0-10)
            prediction = max(0, min(10, prediction))
            
            return {
                'predicted': True,
                'current_satisfaction': current_satisfaction,
                'predicted_satisfaction': round(prediction, 2),
                'change': round(prediction - current_satisfaction, 2) if current_satisfaction else None,
                'features_used': features
            }
            
        except Exception as e:
            logger.error(f"Error prediciendo satisfacción: {e}")
            return {
                'predicted': False,
                'error': str(e)
            }
    
    async def predict_retention(self, person_id: int, vacancy_id: int) -> Dict:
        """
        Predice probabilidad de retención (no rotación) para un candidato
        en diferentes horizontes temporales.
        """
        try:
            # Verificar si tenemos el modelo entrenado
            if self.retention_model is None:
                return {
                    'predicted': False,
                    'error': 'Modelo de retención no disponible'
                }
                
            # Obtener proceso de onboarding
            try:
                process = OnboardingProcess.objects.get(
                    person_id=person_id, 
                    vacancy_id=vacancy_id
                )
            except OnboardingProcess.DoesNotExist:
                return {
                    'predicted': False,
                    'error': 'Proceso de onboarding no encontrado'
                }
            
            # Obtener datos necesarios para predicción
            person = process.person
            vacancy = process.vacancy
            
            # Calcular días desde contratación
            days_employed = (datetime.now() - process.hire_date.replace(tzinfo=None)).days
            
            # Obtener satisfacción actual si existe
            current_satisfaction = process.get_satisfaction_score() or 7.5  # Valor por defecto
            
            # Preparar features base para predicción
            base_features = {
                'satisfaction_score': current_satisfaction,
                'person_experience': getattr(person, 'experience_years', 0),
                'person_age': getattr(person, 'age', 30),
                'vacancy_salary': getattr(vacancy, 'salary', 15000),
                'vacancy_remote': int(getattr(vacancy, 'is_remote', False)),
                'company_size': getattr(vacancy.company, 'employee_count', 100),
                'completed_surveys': process.completed_surveys
            }
            
            # Manejar valores nulos
            for key, value in base_features.items():
                if value is None:
                    base_features[key] = 0
            
            # Predicciones para diferentes horizontes temporales
            horizons = [
                ('6_months', 180),
                ('1_year', 365),
                ('2_years', 730)
            ]
            
            results = {}
            
            for label, days in horizons:
                # Copiar features base y ajustar días
                features = base_features.copy()
                features['days_employed'] = days
                
                # Crear DataFrame con un solo registro
                X_pred = pd.DataFrame([features])
                
                # Asegurar que solo usamos features que el modelo conoce
                model_features = self.retention_model.named_steps['model'].feature_names_in_
                X_pred = X_pred[model_features].copy()
                
                # Realizar predicción
                prob_retained = self.retention_model.predict_proba(X_pred)[0][1]
                
                # Mapear a categoría y añadir factores de riesgo
                results[label] = {
                    'probability': round(prob_retained * 100, 2),
                    'risk_level': self._map_retention_risk(prob_retained),
                    'risk_factors': self._identify_retention_risk_factors(features, prob_retained)
                }
            
            return {
                'predicted': True,
                'current_days': days_employed,
                'predictions': results
            }
            
        except Exception as e:
            logger.error(f"Error prediciendo retención: {e}")
            return {
                'predicted': False,
                'error': str(e)
            }
    
    def _map_retention_risk(self, probability: float) -> str:
        """Mapea probabilidad a nivel de riesgo"""
        if probability >= 0.85:
            return 'very_low'
        elif probability >= 0.70:
            return 'low'
        elif probability >= 0.50:
            return 'medium'
        elif probability >= 0.30:
            return 'high'
        else:
            return 'very_high'
    
    def _identify_retention_risk_factors(self, features: Dict, probability: float) -> List[Dict]:
        """Identifica factores de riesgo que contribuyen a la probabilidad de rotación"""
        risk_factors = []
        
        # Si probabilidad es alta, no hay factores de riesgo significativos
        if probability >= 0.80:
            return risk_factors
            
        # Analizar factores de riesgo conocidos
        if features.get('satisfaction_score', 10) <.0:
            risk_factors.append({
                'factor': 'satisfaction',
                'name': 'Baja satisfacción',
                'description': 'La satisfacción del candidato está por debajo del promedio.',
                'impact': 'high'
            })
            
        if features.get('vacancy_remote', 0) == 0 and features.get('vacancy_salary', 0) < 15000:
            risk_factors.append({
                'factor': 'compensation',
                'name': 'Compensación',
                'description': 'El salario es relativamente bajo para un puesto presencial.',
                'impact': 'medium'
            })
            
        if features.get('completed_surveys', 0) < 2:
            risk_factors.append({
                'factor': 'engagement',
                'name': 'Bajo engagement',
                'description': 'El candidato ha completado pocas encuestas de seguimiento.',
                'impact': 'medium'
            })
            
        # Factores adicionales según correlaciones conocidas
        if features.get('person_age', 30) < 25 and features.get('company_size', 0) > 500:
            risk_factors.append({
                'factor': 'fit',
                'name': 'Ajuste cultural',
                'description': 'Profesionales jóvenes suelen tener mayor rotación en empresas grandes.',
                'impact': 'low'
            })
        
        return risk_factors

class OnboardingProcessor(OnboardingMLProcessor):
    """
    Wrapper para compatibilidad retroactiva y uso en el sistema.
    Hereda de OnboardingMLProcessor.
    """
    pass
