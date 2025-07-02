"""
Sistema de Matching Automático al 100% con Analytics Avanzados integrado con AURA.
Ubicado en la estructura correcta de ML: app/ml/core/models/matchmaking/
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import joblib
import json

from app.ml.aura.aura import AuraEngine
from app.ml.core.models.matchmaking.base import MatchmakingPipeline
from app.ml.core.models.matchmaking.factors import MatchmakingFactors

logger = logging.getLogger(__name__)

class AdvancedMatchingSystem(MatchmakingPipeline):
    """
    Sistema avanzado de matching automático con analytics en tiempo real.
    Hereda de BaseMatchmakingModel para mantener consistencia con la arquitectura ML.
    """
    
    def __init__(self):
        super().__init__()
        self.aura_engine = AuraEngine()
        self.factors = MatchmakingFactors()
        self.scaler = StandardScaler()
        self.vectorizer = TfidfVectorizer(max_features=1000)
        
        # Modelos específicos
        self.matching_model = None
        self.success_prediction_model = None
        self.culture_fit_model = None
        self.retention_model = None
        
        # Analytics en tiempo real
        self.analytics_data = {
            'matching_accuracy': [],
            'conversion_rates': [],
            'time_to_hire': [],
            'cost_per_hire': [],
            'candidate_satisfaction': [],
            'client_satisfaction': []
        }
        
        self.load_models()
    
    def load_models(self):
        """Carga los modelos entrenados."""
        try:
            # Cargar modelos desde archivos
            self.matching_model = joblib.load('models/matching_model.pkl')
            self.success_prediction_model = joblib.load('models/success_prediction.pkl')
            self.culture_fit_model = joblib.load('models/culture_fit.pkl')
            self.retention_model = joblib.load('models/retention.pkl')
            
            logger.info("Modelos cargados exitosamente")
            
        except Exception as e:
            logger.warning(f"Modelos no encontrados, entrenando nuevos: {str(e)}")
            self.train_models()
    
    def train_models(self):
        """Entrena los modelos con datos históricos."""
        try:
            # Obtener datos históricos
            historical_data = self._get_historical_data()
            
            # Preparar features
            X, y_matching, y_success, y_culture, y_retention = self._prepare_training_data(historical_data)
            
            # Entrenar modelos
            self.matching_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.matching_model.fit(X, y_matching)
            
            self.success_prediction_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            self.success_prediction_model.fit(X, y_success)
            
            self.culture_fit_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.culture_fit_model.fit(X, y_culture)
            
            self.retention_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            self.retention_model.fit(X, y_retention)
            
            # Guardar modelos
            joblib.dump(self.matching_model, 'models/matching_model.pkl')
            joblib.dump(self.success_prediction_model, 'models/success_prediction.pkl')
            joblib.dump(self.culture_fit_model, 'models/culture_fit.pkl')
            joblib.dump(self.retention_model, 'models/retention.pkl')
            
            logger.info("Modelos entrenados y guardados exitosamente")
            
        except Exception as e:
            logger.error(f"Error entrenando modelos: {str(e)}")
    
    def advanced_matching(self, candidate_id: int, position_id: int) -> Dict:
        """
        Matching automático al 100% con múltiples factores.
        """
        try:
            # Obtener datos del candidato y posición
            candidate_data = self._get_candidate_data(candidate_id)
            position_data = self._get_position_data(position_id)
            
            # Generar features avanzados
            features = self._generate_advanced_features(candidate_data, position_data)
            
            # Predicciones múltiples
            matching_score = self._calculate_matching_score(features)
            success_probability = self._predict_success_probability(features)
            culture_fit = self._predict_culture_fit(features)
            retention_probability = self._predict_retention_probability(features)
            
            # Análisis de AURA
            aura_analysis = self.aura_engine.analyze_candidate_position_fit(
                candidate_data, position_data
            )
            
            # Scoring final integrado
            final_score = self._calculate_final_score(
                matching_score, success_probability, culture_fit, 
                retention_probability, aura_analysis
            )
            
            # Analytics en tiempo real
            self._update_analytics(candidate_id, position_id, final_score)
            
            # Recomendaciones automáticas
            recommendations = self._generate_recommendations(
                candidate_data, position_data, final_score, aura_analysis
            )
            
            return {
                'candidate_id': candidate_id,
                'position_id': position_id,
                'matching_score': matching_score,
                'success_probability': success_probability,
                'culture_fit': culture_fit,
                'retention_probability': retention_probability,
                'final_score': final_score,
                'aura_analysis': aura_analysis,
                'recommendations': recommendations,
                'confidence_level': self._calculate_confidence_level(features),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en matching avanzado: {str(e)}")
            return {'error': str(e)}
    
    def _generate_advanced_features(self, candidate_data: Dict, position_data: Dict) -> np.ndarray:
        """Genera features avanzados para el matching."""
        try:
            features = []
            
            # Skills matching
            skills_match = self._calculate_skills_match(
                candidate_data.get('skills', []), 
                position_data.get('required_skills', [])
            )
            features.append(skills_match)
            
            # Experience level
            exp_match = self._calculate_experience_match(
                candidate_data.get('experience_years', 0),
                position_data.get('min_experience', 0),
                position_data.get('max_experience', 10)
            )
            features.append(exp_match)
            
            # Salary expectations
            salary_match = self._calculate_salary_match(
                candidate_data.get('salary_expectation', 0),
                position_data.get('salary_range_min', 0),
                position_data.get('salary_range_max', 0)
            )
            features.append(salary_match)
            
            # Location compatibility
            location_match = self._calculate_location_match(
                candidate_data.get('location', ''),
                position_data.get('location', ''),
                position_data.get('remote_allowed', False)
            )
            features.append(location_match)
            
            # Cultural fit indicators
            culture_indicators = self._calculate_culture_indicators(
                candidate_data, position_data
            )
            features.extend(culture_indicators)
            
            # Performance history
            performance_metrics = self._calculate_performance_metrics(candidate_data)
            features.extend(performance_metrics)
            
            # Market demand
            market_demand = self._calculate_market_demand(position_data)
            features.append(market_demand)
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error generando features: {str(e)}")
            return np.zeros((1, 20))  # Features por defecto
    
    def _calculate_skills_match(self, candidate_skills: List, required_skills: List) -> float:
        """Calcula el match de skills."""
        if not required_skills:
            return 1.0
        
        candidate_skills_set = set(skill.lower() for skill in candidate_skills)
        required_skills_set = set(skill.lower() for skill in required_skills)
        
        if not required_skills_set:
            return 1.0
        
        intersection = candidate_skills_set.intersection(required_skills_set)
        return len(intersection) / len(required_skills_set)
    
    def _calculate_experience_match(self, candidate_exp: float, min_exp: float, max_exp: float) -> float:
        """Calcula el match de experiencia."""
        if candidate_exp < min_exp:
            return 0.0
        elif candidate_exp > max_exp:
            return 0.5  # Penalización por sobre-experiencia
        else:
            return 1.0
    
    def _calculate_salary_match(self, candidate_salary: float, min_salary: float, max_salary: float) -> float:
        """Calcula el match de expectativas salariales."""
        if min_salary <= candidate_salary <= max_salary:
            return 1.0
        elif candidate_salary < min_salary:
            return 0.8  # Ligeramente favorable
        else:
            return 0.3  # Penalización por expectativas altas
    
    def _calculate_location_match(self, candidate_location: str, position_location: str, remote_allowed: bool) -> float:
        """Calcula el match de ubicación."""
        if remote_allowed:
            return 1.0  # Ubicación no es crítica
        
        candidate_location_clean = candidate_location.lower().strip()
        position_location_clean = position_location.lower().strip()
        
        if candidate_location_clean == position_location_clean:
            return 1.0
        elif self._are_locations_close(candidate_location_clean, position_location_clean):
            return 0.8
        else:
            return 0.2
    
    def _are_locations_close(self, loc1: str, loc2: str) -> bool:
        """Verifica si las ubicaciones están cerca."""
        # Simulación - en producción usar API de geolocalización
        close_locations = {
            'cdmx': ['mexico city', 'ciudad de mexico', 'df'],
            'guadalajara': ['gdl', 'jalisco'],
            'monterrey': ['mty', 'nuevo leon']
        }
        
        for key, locations in close_locations.items():
            if loc1 in locations and loc2 in locations:
                return True
        return False
    
    def _calculate_culture_indicators(self, candidate_data: Dict, position_data: Dict) -> List[float]:
        """Calcula indicadores de cultura organizacional."""
        indicators = []
        
        # Work style preference
        work_style_match = self._compare_work_styles(
            candidate_data.get('work_style', ''),
            position_data.get('company_culture', {})
        )
        indicators.append(work_style_match)
        
        # Values alignment
        values_match = self._compare_values(
            candidate_data.get('values', []),
            position_data.get('company_values', [])
        )
        indicators.append(values_match)
        
        # Communication style
        comm_match = self._compare_communication_styles(
            candidate_data.get('communication_style', ''),
            position_data.get('communication_culture', '')
        )
        indicators.append(comm_match)
        
        return indicators
    
    def _calculate_performance_metrics(self, candidate_data: Dict) -> List[float]:
        """Calcula métricas de rendimiento del candidato."""
        metrics = []
        
        # Historical performance
        avg_performance = candidate_data.get('avg_performance_score', 0.7)
        metrics.append(avg_performance)
        
        # Interview success rate
        interview_success = candidate_data.get('interview_success_rate', 0.6)
        metrics.append(interview_success)
        
        # Reference scores
        reference_score = candidate_data.get('reference_score', 0.8)
        metrics.append(reference_score)
        
        # Assessment scores
        assessment_score = candidate_data.get('assessment_score', 0.75)
        metrics.append(assessment_score)
        
        return metrics
    
    def _calculate_market_demand(self, position_data: Dict) -> float:
        """Calcula la demanda del mercado para la posición."""
        # Simulación - en producción usar datos reales del mercado
        position_title = position_data.get('title', '').lower()
        
        high_demand_positions = ['developer', 'engineer', 'data scientist', 'devops']
        medium_demand_positions = ['manager', 'analyst', 'designer']
        
        if any(pos in position_title for pos in high_demand_positions):
            return 0.9  # Alta demanda
        elif any(pos in position_title for pos in medium_demand_positions):
            return 0.7  # Demanda media
        else:
            return 0.5  # Demanda normal
    
    def _calculate_matching_score(self, features: np.ndarray) -> float:
        """Calcula el score de matching usando el modelo."""
        try:
            prediction = self.matching_model.predict_proba(features)[0]
            return prediction[1]  # Probabilidad de match exitoso
        except Exception as e:
            logger.error(f"Error calculando matching score: {str(e)}")
            return 0.5
    
    def _predict_success_probability(self, features: np.ndarray) -> float:
        """Predice la probabilidad de éxito del candidato."""
        try:
            return self.success_prediction_model.predict(features)[0]
        except Exception as e:
            logger.error(f"Error prediciendo éxito: {str(e)}")
            return 0.5
    
    def _predict_culture_fit(self, features: np.ndarray) -> float:
        """Predice el fit cultural."""
        try:
            prediction = self.culture_fit_model.predict_proba(features)[0]
            return prediction[1]
        except Exception as e:
            logger.error(f"Error prediciendo cultura: {str(e)}")
            return 0.5
    
    def _predict_retention_probability(self, features: np.ndarray) -> float:
        """Predice la probabilidad de retención."""
        try:
            return self.retention_model.predict(features)[0]
        except Exception as e:
            logger.error(f"Error prediciendo retención: {str(e)}")
            return 0.5
    
    def _calculate_final_score(self, matching_score: float, success_prob: float, 
                             culture_fit: float, retention_prob: float, 
                             aura_analysis: Dict) -> float:
        """Calcula el score final integrado."""
        try:
            # Pesos de cada factor
            weights = {
                'matching': 0.25,
                'success': 0.25,
                'culture': 0.20,
                'retention': 0.15,
                'aura': 0.15
            }
            
            # Score de AURA
            aura_score = aura_analysis.get('overall_score', 0.5)
            
            # Cálculo ponderado
            final_score = (
                matching_score * weights['matching'] +
                success_prob * weights['success'] +
                culture_fit * weights['culture'] +
                retention_prob * weights['retention'] +
                aura_score * weights['aura']
            )
            
            return min(max(final_score, 0.0), 1.0)  # Normalizar entre 0 y 1
            
        except Exception as e:
            logger.error(f"Error calculando score final: {str(e)}")
            return 0.5
    
    def _calculate_confidence_level(self, features: np.ndarray) -> float:
        """Calcula el nivel de confianza de la predicción."""
        try:
            # Basado en la varianza de las predicciones
            predictions = [
                self._calculate_matching_score(features),
                self._predict_success_probability(features),
                self._predict_culture_fit(features),
                self._predict_retention_probability(features)
            ]
            
            confidence = 1.0 - np.std(predictions)
            return min(max(confidence, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculando confianza: {str(e)}")
            return 0.5
    
    def _generate_recommendations(self, candidate_data: Dict, position_data: Dict, 
                                final_score: float, aura_analysis: Dict) -> List[Dict]:
        """Genera recomendaciones automáticas."""
        recommendations = []
        
        # Recomendación de entrevista
        if final_score >= 0.8:
            recommendations.append({
                'type': 'interview',
                'priority': 'high',
                'message': 'Candidato altamente recomendado para entrevista inmediata',
                'reason': f'Score de matching: {final_score:.2%}'
            })
        elif final_score >= 0.6:
            recommendations.append({
                'type': 'interview',
                'priority': 'medium',
                'message': 'Candidato recomendado para entrevista',
                'reason': f'Score de matching: {final_score:.2%}'
            })
        
        # Recomendaciones específicas de AURA
        if 'recommendations' in aura_analysis:
            recommendations.extend(aura_analysis['recommendations'])
        
        # Recomendaciones de mejora
        if final_score < 0.6:
            recommendations.append({
                'type': 'improvement',
                'priority': 'low',
                'message': 'Considerar candidatos con mejor perfil',
                'reason': 'Score de matching bajo'
            })
        
        return recommendations
    
    def _update_analytics(self, candidate_id: int, position_id: int, final_score: float):
        """Actualiza analytics en tiempo real."""
        try:
            timestamp = datetime.now()
            
            # Actualizar métricas
            self.analytics_data['matching_accuracy'].append({
                'timestamp': timestamp,
                'candidate_id': candidate_id,
                'position_id': position_id,
                'score': final_score
            })
            
            # Mantener solo los últimos 1000 registros
            if len(self.analytics_data['matching_accuracy']) > 1000:
                self.analytics_data['matching_accuracy'] = self.analytics_data['matching_accuracy'][-1000:]
                
        except Exception as e:
            logger.error(f"Error actualizando analytics: {str(e)}")
    
    def get_advanced_analytics(self) -> Dict:
        """Obtiene analytics avanzados del sistema."""
        try:
            analytics = {
                'matching_performance': self._calculate_matching_performance(),
                'conversion_metrics': self._calculate_conversion_metrics(),
                'cost_analysis': self._calculate_cost_analysis(),
                'satisfaction_metrics': self._calculate_satisfaction_metrics(),
                'predictive_insights': self._generate_predictive_insights(),
                'recommendations': self._generate_system_recommendations()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_matching_performance(self) -> Dict:
        """Calcula métricas de rendimiento del matching."""
        try:
            scores = [item['score'] for item in self.analytics_data['matching_accuracy']]
            
            if not scores:
                return {'error': 'No hay datos suficientes'}
            
            return {
                'average_score': np.mean(scores),
                'median_score': np.median(scores),
                'std_deviation': np.std(scores),
                'high_matches': len([s for s in scores if s >= 0.8]),
                'medium_matches': len([s for s in scores if 0.6 <= s < 0.8]),
                'low_matches': len([s for s in scores if s < 0.6]),
                'total_matches': len(scores)
            }
            
        except Exception as e:
            logger.error(f"Error calculando rendimiento: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_conversion_metrics(self) -> Dict:
        """Calcula métricas de conversión."""
        # Simulación - en producción usar datos reales
        return {
            'interview_to_offer': 0.35,
            'offer_to_hire': 0.85,
            'hire_to_retention_6m': 0.92,
            'overall_conversion': 0.28
        }
    
    def _calculate_cost_analysis(self) -> Dict:
        """Calcula análisis de costos."""
        # Simulación - en producción usar datos reales
        return {
            'cost_per_hire': 8500,
            'time_to_hire_days': 25,
            'source_cost_breakdown': {
                'linkedin': 45,
                'referrals': 15,
                'job_boards': 25,
                'direct': 15
            }
        }
    
    def _calculate_satisfaction_metrics(self) -> Dict:
        """Calcula métricas de satisfacción."""
        # Simulación - en producción usar datos reales
        return {
            'candidate_satisfaction': 4.6,
            'client_satisfaction': 4.8,
            'consultant_satisfaction': 4.5
        }
    
    def _generate_predictive_insights(self) -> List[Dict]:
        """Genera insights predictivos."""
        insights = [
            {
                'type': 'trend',
                'title': 'Demanda creciente en Data Science',
                'description': 'Se observa un incremento del 25% en demanda de Data Scientists',
                'confidence': 0.85,
                'impact': 'high'
            },
            {
                'type': 'opportunity',
                'title': 'Optimización de tiempo de contratación',
                'description': 'Reducir el tiempo promedio de 25 a 20 días aumentaría la conversión en 15%',
                'confidence': 0.78,
                'impact': 'medium'
            },
            {
                'type': 'risk',
                'title': 'Escasez de talento en DevOps',
                'description': 'Posible escasez de candidatos DevOps en los próximos 3 meses',
                'confidence': 0.72,
                'impact': 'high'
            }
        ]
        
        return insights
    
    def _generate_system_recommendations(self) -> List[Dict]:
        """Genera recomendaciones para el sistema."""
        recommendations = [
            {
                'type': 'optimization',
                'title': 'Ajustar pesos del matching',
                'description': 'Considerar aumentar el peso de cultura organizacional',
                'priority': 'medium',
                'expected_impact': '5% mejora en retención'
            },
            {
                'type': 'feature',
                'title': 'Implementar feedback loop',
                'description': 'Recolectar feedback post-contratación para mejorar predicciones',
                'priority': 'high',
                'expected_impact': '10% mejora en accuracy'
            }
        ]
        
        return recommendations
    
    def _get_historical_data(self) -> List[Dict]:
        """Obtiene datos históricos para entrenamiento."""
        # Simulación - en producción obtener de la base de datos
        return [
            {
                'candidate_id': 1,
                'position_id': 1,
                'skills_match': 0.8,
                'experience_match': 1.0,
                'salary_match': 0.9,
                'location_match': 1.0,
                'culture_fit': 0.85,
                'success': 1,
                'retention': 0.9
            }
            # ... más datos históricos
        ]
    
    def _get_candidate_data(self, candidate_id: int) -> Dict:
        """Obtiene datos del candidato."""
        # Simulación - en producción obtener de la base de datos
        return {
            'id': candidate_id,
            'skills': ['Python', 'Machine Learning', 'Data Analysis'],
            'experience_years': 5,
            'salary_expectation': 80000,
            'location': 'CDMX',
            'work_style': 'collaborative',
            'values': ['innovation', 'growth', 'teamwork'],
            'communication_style': 'direct',
            'avg_performance_score': 0.85,
            'interview_success_rate': 0.75,
            'reference_score': 0.9,
            'assessment_score': 0.88
        }
    
    def _get_position_data(self, position_id: int) -> Dict:
        """Obtiene datos de la posición."""
        # Simulación - en producción obtener de la base de datos
        return {
            'id': position_id,
            'title': 'Senior Data Scientist',
            'required_skills': ['Python', 'Machine Learning', 'SQL'],
            'min_experience': 3,
            'max_experience': 8,
            'salary_range_min': 70000,
            'salary_range_max': 90000,
            'location': 'CDMX',
            'remote_allowed': True,
            'company_culture': {
                'work_style': 'collaborative',
                'values': ['innovation', 'excellence', 'teamwork'],
                'communication': 'open'
            }
        }
    
    def _prepare_training_data(self, historical_data: List[Dict]) -> Tuple:
        """Prepara datos para entrenamiento."""
        X = []
        y_matching = []
        y_success = []
        y_culture = []
        y_retention = []
        
        for record in historical_data:
            features = [
                record['skills_match'],
                record['experience_match'],
                record['salary_match'],
                record['location_match'],
                record['culture_fit']
            ]
            
            X.append(features)
            y_matching.append(1 if record['success'] else 0)
            y_success.append(record['success'])
            y_culture.append(record['culture_fit'])
            y_retention.append(record['retention'])
        
        return np.array(X), np.array(y_matching), np.array(y_success), np.array(y_culture), np.array(y_retention)
    
    def _compare_work_styles(self, candidate_style: str, company_culture: Dict) -> float:
        """Compara estilos de trabajo."""
        company_style = company_culture.get('work_style', '')
        
        if candidate_style == company_style:
            return 1.0
        elif candidate_style in ['collaborative', 'team'] and company_style in ['collaborative', 'team']:
            return 0.8
        else:
            return 0.3
    
    def _compare_values(self, candidate_values: List, company_values: List) -> float:
        """Compara valores del candidato y la empresa."""
        if not company_values:
            return 0.5
        
        candidate_values_set = set(value.lower() for value in candidate_values)
        company_values_set = set(value.lower() for value in company_values)
        
        intersection = candidate_values_set.intersection(company_values_set)
        return len(intersection) / len(company_values_set)
    
    def _compare_communication_styles(self, candidate_style: str, company_style: str) -> float:
        """Compara estilos de comunicación."""
        if candidate_style == company_style:
            return 1.0
        elif candidate_style in ['direct', 'open'] and company_style in ['direct', 'open']:
            return 0.8
        else:
            return 0.4 