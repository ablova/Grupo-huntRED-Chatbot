"""
AURA - Sistema de IA Predictiva Avanzada
Career Movement Predictor & Intelligent Recommendations
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import networkx as nx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CareerPrediction:
    """Resultado de predicción de carrera"""
    person_id: int
    prediction_date: datetime
    timeframe_months: int
    career_moves: List[Dict[str, Any]]
    confidence_score: float
    opportunity_windows: List[Dict[str, Any]]
    risk_factors: List[str]
    recommended_actions: List[str]
    market_trends: Dict[str, Any]
    skill_gaps: List[str]
    networking_opportunities: List[Dict[str, Any]]


@dataclass
class MarketTrend:
    """Tendencia del mercado laboral"""
    industry: str
    location: str
    trend_direction: str  # 'up', 'down', 'stable'
    growth_rate: float
    hot_skills: List[str]
    declining_skills: List[str]
    salary_trends: Dict[str, float]
    demand_prediction: Dict[str, float]


class CareerMovementPredictor:
    """
    Sistema de IA para predecir movimientos profesionales
    """
    
    def __init__(self):
        self.models = {
            'career_move': RandomForestRegressor(n_estimators=100, random_state=42),
            'salary_prediction': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'attrition_risk': MLPRegressor(hidden_layer_sizes=(100, 50), random_state=42)
        }
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.is_trained = False
        
    def extract_career_features(self, person_data: Dict, network_data: Dict) -> np.ndarray:
        """
        Extrae características para predicción de carrera
        """
        features = []
        
        # Características personales
        features.extend([
            person_data.get('years_experience', 0),
            person_data.get('education_level', 0),
            person_data.get('current_salary', 0),
            person_data.get('job_satisfaction', 0.5),
            person_data.get('company_size', 0),
            person_data.get('industry_tenure', 0)
        ])
        
        # Características de red
        network_metrics = network_data.get('metrics', {})
        features.extend([
            network_metrics.get('network_strength', 0),
            network_metrics.get('reputation_score', 0),
            network_metrics.get('influence_score', 0),
            network_metrics.get('connection_count', 0),
            network_metrics.get('community_count', 0),
            network_metrics.get('key_connections_ratio', 0)
        ])
        
        # Características de actividad
        activity_data = person_data.get('activity', {})
        features.extend([
            activity_data.get('posts_per_month', 0),
            activity_data.get('interactions_per_month', 0),
            activity_data.get('events_attended', 0),
            activity_data.get('skills_updated', 0),
            activity_data.get('certifications_earned', 0)
        ])
        
        # Características de mercado
        market_data = person_data.get('market_context', {})
        features.extend([
            market_data.get('industry_growth', 0),
            market_data.get('skill_demand', 0),
            market_data.get('salary_growth', 0),
            market_data.get('job_openings', 0)
        ])
        
        return np.array(features).reshape(1, -1)
    
    def predict_career_moves(self, person_id: int, timeframe_months: int = 12) -> CareerPrediction:
        """
        Predice próximos movimientos de carrera
        """
        try:
            # Obtener datos de la persona y su red
            person_data = self._get_person_data(person_id)
            network_data = self._get_network_data(person_id)
            
            # Extraer características
            features = self.extract_career_features(person_data, network_data)
            
            # Realizar predicciones
            career_move_probability = self.models['career_move'].predict(features)[0]
            salary_prediction = self.models['salary_prediction'].predict(features)[0]
            attrition_risk = self.models['attrition_risk'].predict(features)[0]
            
            # Generar predicciones específicas
            career_moves = self._generate_career_moves(person_data, career_move_probability, timeframe_months)
            opportunity_windows = self._identify_opportunity_windows(person_data, network_data)
            risk_factors = self._identify_risk_factors(person_data, attrition_risk)
            recommended_actions = self._generate_recommendations(person_data, network_data)
            market_trends = self._analyze_market_trends(person_data)
            skill_gaps = self._identify_skill_gaps(person_data)
            networking_opportunities = self._find_networking_opportunities(person_data, network_data)
            
            return CareerPrediction(
                person_id=person_id,
                prediction_date=datetime.now(),
                timeframe_months=timeframe_months,
                career_moves=career_moves,
                confidence_score=career_move_probability,
                opportunity_windows=opportunity_windows,
                risk_factors=risk_factors,
                recommended_actions=recommended_actions,
                market_trends=market_trends,
                skill_gaps=skill_gaps,
                networking_opportunities=networking_opportunities
            )
            
        except Exception as e:
            logger.error(f"Error predicting career moves for person {person_id}: {e}")
            raise
    
    def _generate_career_moves(self, person_data: Dict, probability: float, timeframe: int) -> List[Dict]:
        """Genera predicciones específicas de movimientos de carrera"""
        moves = []
        
        if probability > 0.7:
            moves.append({
                'type': 'job_change',
                'probability': probability,
                'timeline': f"{timeframe//3}-{timeframe} months",
                'reason': 'High market demand and network opportunities',
                'impact': 'high'
            })
        
        if probability > 0.5:
            moves.append({
                'type': 'promotion',
                'probability': probability * 0.8,
                'timeline': f"{timeframe//2}-{timeframe} months",
                'reason': 'Strong performance and network influence',
                'impact': 'medium'
            })
        
        if probability > 0.3:
            moves.append({
                'type': 'skill_development',
                'probability': probability * 0.9,
                'timeline': f"1-{timeframe//2} months",
                'reason': 'Market trends and skill gaps identified',
                'impact': 'low'
            })
        
        return moves
    
    def _identify_opportunity_windows(self, person_data: Dict, network_data: Dict) -> List[Dict]:
        """Identifica ventanas de oportunidad"""
        opportunities = []
        
        # Oportunidades basadas en red
        if network_data.get('metrics', {}).get('influence_score', 0) > 0.7:
            opportunities.append({
                'type': 'thought_leadership',
                'timeline': '1-3 months',
                'description': 'High influence score indicates opportunity for thought leadership',
                'confidence': 0.85
            })
        
        # Oportunidades basadas en mercado
        if person_data.get('market_context', {}).get('skill_demand', 0) > 0.8:
            opportunities.append({
                'type': 'skill_monetization',
                'timeline': '2-6 months',
                'description': 'High demand for current skills in market',
                'confidence': 0.9
            })
        
        return opportunities
    
    def _identify_risk_factors(self, person_data: Dict, attrition_risk: float) -> List[str]:
        """Identifica factores de riesgo"""
        risks = []
        
        if attrition_risk > 0.7:
            risks.append("High attrition risk - consider retention strategies")
        
        if person_data.get('job_satisfaction', 0.5) < 0.4:
            risks.append("Low job satisfaction - monitor engagement")
        
        if person_data.get('network_strength', 0) < 0.3:
            risks.append("Weak professional network - focus on networking")
        
        return risks
    
    def _generate_recommendations(self, person_data: Dict, network_data: Dict) -> List[str]:
        """Genera recomendaciones personalizadas"""
        recommendations = []
        
        # Recomendaciones basadas en red
        if network_data.get('metrics', {}).get('network_strength', 0) < 0.5:
            recommendations.append("Strengthen professional network through targeted outreach")
        
        if network_data.get('metrics', {}).get('influence_score', 0) > 0.6:
            recommendations.append("Leverage high influence for thought leadership opportunities")
        
        # Recomendaciones basadas en habilidades
        skill_gaps = self._identify_skill_gaps(person_data)
        if skill_gaps:
            recommendations.append(f"Develop skills: {', '.join(skill_gaps[:3])}")
        
        # Recomendaciones de mercado
        if person_data.get('market_context', {}).get('salary_growth', 0) > 0.1:
            recommendations.append("Market shows salary growth - consider salary negotiations")
        
        return recommendations
    
    def _analyze_market_trends(self, person_data: Dict) -> Dict[str, Any]:
        """Analiza tendencias del mercado"""
        market_context = person_data.get('market_context', {})
        
        return {
            'industry_growth': market_context.get('industry_growth', 0),
            'skill_demand': market_context.get('skill_demand', 0),
            'salary_trends': {
                'current': market_context.get('current_salary', 0),
                'predicted': market_context.get('current_salary', 0) * (1 + market_context.get('salary_growth', 0))
            },
            'hot_skills': market_context.get('hot_skills', []),
            'declining_skills': market_context.get('declining_skills', [])
        }
    
    def _identify_skill_gaps(self, person_data: Dict) -> List[str]:
        """Identifica brechas de habilidades"""
        current_skills = set(person_data.get('skills', []))
        market_skills = set(person_data.get('market_context', {}).get('hot_skills', []))
        
        return list(market_skills - current_skills)
    
    def _find_networking_opportunities(self, person_data: Dict, network_data: Dict) -> List[Dict]:
        """Encuentra oportunidades de networking"""
        opportunities = []
        
        # Eventos de networking
        opportunities.append({
            'type': 'industry_event',
            'title': 'Tech Leadership Summit',
            'date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'relevance': 0.9,
            'description': 'High-relevance event for current network'
        })
        
        # Conexiones clave
        key_connections = network_data.get('key_connections', [])
        for connection in key_connections[:3]:
            opportunities.append({
                'type': 'key_connection',
                'person': connection.get('name', 'Unknown'),
                'relevance': connection.get('strength', 0),
                'description': f"Strengthen connection with {connection.get('name', 'Unknown')}"
            })
        
        return opportunities
    
    def _get_person_data(self, person_id: int) -> Dict:
        """Obtiene datos de la persona (simulado)"""
        # En implementación real, esto vendría de la base de datos
        return {
            'years_experience': 5,
            'education_level': 4,  # Master's degree
            'current_salary': 80000,
            'job_satisfaction': 0.7,
            'company_size': 1000,
            'industry_tenure': 3,
            'skills': ['Python', 'Machine Learning', 'Data Analysis'],
            'activity': {
                'posts_per_month': 5,
                'interactions_per_month': 20,
                'events_attended': 3,
                'skills_updated': 2,
                'certifications_earned': 1
            },
            'market_context': {
                'industry_growth': 0.15,
                'skill_demand': 0.8,
                'salary_growth': 0.08,
                'job_openings': 150,
                'hot_skills': ['AI', 'Machine Learning', 'Data Science', 'Cloud Computing'],
                'declining_skills': ['COBOL', 'Fortran']
            }
        }
    
    def _get_network_data(self, person_id: int) -> Dict:
        """Obtiene datos de red (simulado)"""
        return {
            'metrics': {
                'network_strength': 0.75,
                'reputation_score': 0.8,
                'influence_score': 0.65,
                'connection_count': 250,
                'community_count': 3,
                'key_connections_ratio': 0.15
            },
            'key_connections': [
                {'name': 'John Smith', 'strength': 0.9, 'role': 'CTO'},
                {'name': 'Jane Doe', 'strength': 0.8, 'role': 'VP Engineering'},
                {'name': 'Bob Johnson', 'strength': 0.7, 'role': 'Senior Manager'}
            ]
        }
    
    def train_models(self, training_data: pd.DataFrame):
        """Entrena los modelos de predicción"""
        try:
            # Preparar datos
            X = training_data.drop(['career_move', 'salary', 'attrition'], axis=1)
            y_career = training_data['career_move']
            y_salary = training_data['salary']
            y_attrition = training_data['attrition']
            
            # Escalar características
            X_scaled = self.scaler.fit_transform(X)
            
            # Dividir datos
            X_train, X_test, y_career_train, y_career_test = train_test_split(
                X_scaled, y_career, test_size=0.2, random_state=42
            )
            
            # Entrenar modelos
            self.models['career_move'].fit(X_train, y_career_train)
            self.models['salary_prediction'].fit(X_train, y_salary)
            self.models['attrition_risk'].fit(X_train, y_attrition)
            
            # Evaluar modelos
            career_pred = self.models['career_move'].predict(X_test)
            career_score = r2_score(y_career_test, career_pred)
            
            logger.info(f"Career prediction model R² score: {career_score:.3f}")
            
            self.is_trained = True
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            raise
    
    def save_models(self, filepath: str):
        """Guarda los modelos entrenados"""
        if self.is_trained:
            joblib.dump(self.models, f"{filepath}/career_predictor_models.pkl")
            joblib.dump(self.scaler, f"{filepath}/career_predictor_scaler.pkl")
            logger.info("Models saved successfully")
    
    def load_models(self, filepath: str):
        """Carga modelos pre-entrenados"""
        try:
            self.models = joblib.load(f"{filepath}/career_predictor_models.pkl")
            self.scaler = joblib.load(f"{filepath}/career_predictor_scaler.pkl")
            self.is_trained = True
            logger.info("Models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise


class MarketTrendAnalyzer:
    """
    Analizador de tendencias del mercado laboral
    """
    
    def __init__(self):
        self.trend_models = {
            'industry_growth': RandomForestRegressor(n_estimators=100, random_state=42),
            'skill_demand': RandomForestRegressor(n_estimators=100, random_state=42),
            'salary_trends': RandomForestRegressor(n_estimators=100, random_state=42)
        }
    
    def predict_industry_trends(self, industry: str, location: str, timeframe_months: int = 12) -> MarketTrend:
        """Predice tendencias de industria"""
        # Simulación de predicción de tendencias
        growth_rate = np.random.uniform(-0.1, 0.3)
        hot_skills = ['AI/ML', 'Cloud Computing', 'Data Science', 'Cybersecurity']
        declining_skills = ['Manual Testing', 'Waterfall', 'Legacy Systems']
        
        return MarketTrend(
            industry=industry,
            location=location,
            trend_direction='up' if growth_rate > 0 else 'down',
            growth_rate=growth_rate,
            hot_skills=hot_skills,
            declining_skills=declining_skills,
            salary_trends={'entry': 0.05, 'mid': 0.08, 'senior': 0.12},
            demand_prediction={'q1': 0.15, 'q2': 0.18, 'q3': 0.20, 'q4': 0.22}
        )
    
    def forecast_skill_demand(self, skills: List[str], location: str) -> Dict[str, float]:
        """Pronostica demanda de habilidades"""
        demand_forecast = {}
        for skill in skills:
            # Simulación de demanda
            base_demand = np.random.uniform(0.3, 0.9)
            location_factor = 1.2 if location in ['San Francisco', 'New York', 'London'] else 1.0
            demand_forecast[skill] = base_demand * location_factor
        
        return demand_forecast
    
    def predict_network_growth(self, person_id: int, months: int) -> Dict[str, Any]:
        """Predice crecimiento de red"""
        # Simulación de crecimiento de red
        current_connections = 250
        growth_rate = np.random.uniform(0.05, 0.15)
        
        predicted_connections = []
        for month in range(1, months + 1):
            new_connections = int(current_connections * growth_rate * month)
            predicted_connections.append(current_connections + new_connections)
        
        return {
            'current_connections': current_connections,
            'predicted_connections': predicted_connections,
            'growth_rate': growth_rate,
            'confidence_interval': [0.03, 0.20]
        }


# Instancia global del predictor
career_predictor = CareerMovementPredictor()
market_analyzer = MarketTrendAnalyzer() 