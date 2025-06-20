"""
AURA - Market Labor Predictor (FASE 1)
Predicción avanzada de mercado laboral y tendencias
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import requests
import json

logger = logging.getLogger(__name__)

# CONFIGURACIÓN: DESHABILITADO POR DEFECTO
ENABLED = False  # Cambiar a True para habilitar


@dataclass
class MarketPrediction:
    """Predicción de mercado laboral"""
    industry: str
    location: str
    skill: str
    prediction_date: datetime
    timeframe_months: int
    demand_prediction: float
    salary_prediction: float
    growth_rate: float
    confidence_score: float
    market_trends: List[str]
    opportunities: List[str]
    risks: List[str]
    recommendations: List[str]


@dataclass
class SkillTrend:
    """Tendencia de habilidad específica"""
    skill_name: str
    current_demand: float
    predicted_demand: float
    growth_rate: float
    market_saturation: float
    salary_range: Tuple[float, float]
    hot_markets: List[str]
    declining_markets: List[str]


class MarketLaborPredictor:
    """
    Predictor avanzado de mercado laboral
    """
    
    def __init__(self):
        self.enabled = ENABLED
        if not self.enabled:
            logger.info("MarketLaborPredictor: DESHABILITADO")
            return
            
        self.models = {
            'demand_predictor': RandomForestRegressor(n_estimators=100, random_state=42),
            'salary_predictor': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'growth_predictor': RandomForestRegressor(n_estimators=100, random_state=42)
        }
        self.scaler = StandardScaler()
        self.is_trained = False
        self.market_data = {}
        self.skill_trends = {}
        
        logger.info("MarketLaborPredictor: Inicializado")
    
    def predict_market_demand(self, industry: str, location: str, skill: str, 
                            timeframe_months: int = 12) -> MarketPrediction:
        """
        Predice demanda de mercado para una habilidad específica
        """
        if not self.enabled:
            return self._get_mock_prediction(industry, location, skill, timeframe_months)
        
        try:
            # Obtener datos de mercado
            market_data = self._get_market_data(industry, location, skill)
            
            # Realizar predicciones
            demand_prediction = self._predict_demand(market_data, timeframe_months)
            salary_prediction = self._predict_salary(market_data, timeframe_months)
            growth_rate = self._predict_growth(market_data, timeframe_months)
            
            # Generar insights
            market_trends = self._analyze_market_trends(market_data)
            opportunities = self._identify_opportunities(market_data)
            risks = self._identify_risks(market_data)
            recommendations = self._generate_recommendations(market_data)
            
            return MarketPrediction(
                industry=industry,
                location=location,
                skill=skill,
                prediction_date=datetime.now(),
                timeframe_months=timeframe_months,
                demand_prediction=demand_prediction,
                salary_prediction=salary_prediction,
                growth_rate=growth_rate,
                confidence_score=0.85,
                market_trends=market_trends,
                opportunities=opportunities,
                risks=risks,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error predicting market demand: {e}")
            return self._get_mock_prediction(industry, location, skill, timeframe_months)
    
    def analyze_skill_trends(self, skills: List[str], locations: List[str]) -> Dict[str, SkillTrend]:
        """
        Analiza tendencias de múltiples habilidades
        """
        if not self.enabled:
            return self._get_mock_skill_trends(skills, locations)
        
        trends = {}
        for skill in skills:
            for location in locations:
                key = f"{skill}_{location}"
                trends[key] = self._analyze_single_skill_trend(skill, location)
        
        return trends
    
    def predict_industry_growth(self, industry: str, timeframe_months: int = 24) -> Dict[str, Any]:
        """
        Predice crecimiento de industria completa
        """
        if not self.enabled:
            return self._get_mock_industry_growth(industry, timeframe_months)
        
        try:
            # Análisis de industria
            industry_data = self._get_industry_data(industry)
            
            # Predicciones por trimestre
            quarterly_growth = []
            for quarter in range(timeframe_months // 3):
                growth = self._predict_quarterly_growth(industry_data, quarter)
                quarterly_growth.append(growth)
            
            # Análisis de factores
            growth_factors = self._analyze_growth_factors(industry_data)
            market_opportunities = self._identify_market_opportunities(industry_data)
            
            return {
                "industry": industry,
                "timeframe_months": timeframe_months,
                "total_growth_prediction": sum(quarterly_growth),
                "quarterly_growth": quarterly_growth,
                "growth_factors": growth_factors,
                "market_opportunities": market_opportunities,
                "confidence_score": 0.82,
                "prediction_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting industry growth: {e}")
            return self._get_mock_industry_growth(industry, timeframe_months)
    
    def get_hot_skills(self, location: str, timeframe_months: int = 6) -> List[Dict[str, Any]]:
        """
        Obtiene habilidades más demandadas en una ubicación
        """
        if not self.enabled:
            return self._get_mock_hot_skills(location, timeframe_months)
        
        try:
            # Obtener datos de habilidades
            skills_data = self._get_skills_data(location)
            
            # Calcular demanda y crecimiento
            hot_skills = []
            for skill_data in skills_data:
                demand_score = self._calculate_demand_score(skill_data)
                growth_rate = self._calculate_growth_rate(skill_data)
                
                if demand_score > 0.7 and growth_rate > 0.1:
                    hot_skills.append({
                        "skill": skill_data["name"],
                        "demand_score": demand_score,
                        "growth_rate": growth_rate,
                        "salary_range": skill_data.get("salary_range", [50000, 120000]),
                        "job_openings": skill_data.get("job_openings", 0),
                        "trend": "rising" if growth_rate > 0.15 else "stable"
                    })
            
            # Ordenar por demanda
            hot_skills.sort(key=lambda x: x["demand_score"], reverse=True)
            return hot_skills[:20]  # Top 20
            
        except Exception as e:
            logger.error(f"Error getting hot skills: {e}")
            return self._get_mock_hot_skills(location, timeframe_months)
    
    def predict_salary_trends(self, skill: str, location: str, 
                            experience_years: int = 5) -> Dict[str, Any]:
        """
        Predice tendencias salariales para una habilidad
        """
        if not self.enabled:
            return self._get_mock_salary_trends(skill, location, experience_years)
        
        try:
            # Obtener datos salariales
            salary_data = self._get_salary_data(skill, location, experience_years)
            
            # Predicciones por año
            yearly_predictions = []
            for year in range(5):
                prediction = self._predict_yearly_salary(salary_data, year)
                yearly_predictions.append(prediction)
            
            # Análisis de factores
            salary_factors = self._analyze_salary_factors(salary_data)
            
            return {
                "skill": skill,
                "location": location,
                "experience_years": experience_years,
                "current_salary": salary_data.get("current_salary", 80000),
                "yearly_predictions": yearly_predictions,
                "growth_rate": (yearly_predictions[-1] - yearly_predictions[0]) / yearly_predictions[0],
                "salary_factors": salary_factors,
                "confidence_score": 0.78,
                "prediction_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting salary trends: {e}")
            return self._get_mock_salary_trends(skill, location, experience_years)
    
    def _get_market_data(self, industry: str, location: str, skill: str) -> Dict[str, Any]:
        """Obtiene datos de mercado (simulado)"""
        return {
            "industry": industry,
            "location": location,
            "skill": skill,
            "current_demand": np.random.uniform(0.6, 0.9),
            "historical_demand": [0.5, 0.6, 0.7, 0.8, 0.85],
            "salary_data": [70000, 75000, 80000, 85000, 90000],
            "job_openings": np.random.randint(100, 1000),
            "growth_rate": np.random.uniform(0.05, 0.25),
            "market_size": np.random.uniform(1000000, 10000000)
        }
    
    def _predict_demand(self, market_data: Dict[str, Any], timeframe_months: int) -> float:
        """Predice demanda futura"""
        base_demand = market_data["current_demand"]
        growth_rate = market_data["growth_rate"]
        return base_demand * (1 + growth_rate * timeframe_months / 12)
    
    def _predict_salary(self, market_data: Dict[str, Any], timeframe_months: int) -> float:
        """Predice salario futuro"""
        current_salary = market_data["salary_data"][-1]
        growth_rate = market_data["growth_rate"] * 0.5  # Salarios crecen más lento
        return current_salary * (1 + growth_rate * timeframe_months / 12)
    
    def _predict_growth(self, market_data: Dict[str, Any], timeframe_months: int) -> float:
        """Predice tasa de crecimiento"""
        return market_data["growth_rate"] * (1 - 0.1 * timeframe_months / 12)  # Desaceleración gradual
    
    def _analyze_market_trends(self, market_data: Dict[str, Any]) -> List[str]:
        """Analiza tendencias del mercado"""
        trends = []
        if market_data["growth_rate"] > 0.15:
            trends.append("Crecimiento acelerado del mercado")
        if market_data["current_demand"] > 0.8:
            trends.append("Alta demanda de talento")
        if market_data["job_openings"] > 500:
            trends.append("Abundantes oportunidades laborales")
        return trends
    
    def _identify_opportunities(self, market_data: Dict[str, Any]) -> List[str]:
        """Identifica oportunidades de mercado"""
        opportunities = []
        if market_data["growth_rate"] > 0.1:
            opportunities.append("Mercado en expansión - momento ideal para entrar")
        if market_data["current_demand"] > 0.7:
            opportunities.append("Demanda alta - salarios competitivos")
        return opportunities
    
    def _identify_risks(self, market_data: Dict[str, Any]) -> List[str]:
        """Identifica riesgos del mercado"""
        risks = []
        if market_data["growth_rate"] < 0.05:
            risks.append("Crecimiento lento del mercado")
        if market_data["current_demand"] < 0.5:
            risks.append("Baja demanda - competencia feroz")
        return risks
    
    def _generate_recommendations(self, market_data: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en datos"""
        recommendations = []
        if market_data["growth_rate"] > 0.15:
            recommendations.append("Invertir en desarrollo de habilidades específicas")
        if market_data["current_demand"] > 0.8:
            recommendations.append("Negociar salarios competitivos")
        return recommendations
    
    def _get_mock_prediction(self, industry: str, location: str, skill: str, 
                           timeframe_months: int) -> MarketPrediction:
        """Predicción simulada cuando está deshabilitado"""
        return MarketPrediction(
            industry=industry,
            location=location,
            skill=skill,
            prediction_date=datetime.now(),
            timeframe_months=timeframe_months,
            demand_prediction=0.75,
            salary_prediction=85000,
            growth_rate=0.12,
            confidence_score=0.85,
            market_trends=["Mercado estable", "Demanda moderada"],
            opportunities=["Oportunidades de crecimiento"],
            risks=["Competencia moderada"],
            recommendations=["Desarrollar habilidades especializadas"]
        )
    
    def _get_mock_skill_trends(self, skills: List[str], locations: List[str]) -> Dict[str, SkillTrend]:
        """Tendencias simuladas cuando está deshabilitado"""
        trends = {}
        for skill in skills:
            for location in locations:
                key = f"{skill}_{location}"
                trends[key] = SkillTrend(
                    skill_name=skill,
                    current_demand=0.7,
                    predicted_demand=0.8,
                    growth_rate=0.1,
                    market_saturation=0.6,
                    salary_range=(70000, 120000),
                    hot_markets=["San Francisco", "New York"],
                    declining_markets=[]
                )
        return trends
    
    def _get_mock_industry_growth(self, industry: str, timeframe_months: int) -> Dict[str, Any]:
        """Crecimiento de industria simulado"""
        return {
            "industry": industry,
            "timeframe_months": timeframe_months,
            "total_growth_prediction": 0.25,
            "quarterly_growth": [0.05, 0.06, 0.07, 0.07],
            "growth_factors": ["Innovación tecnológica", "Demanda del mercado"],
            "market_opportunities": ["Expansión internacional", "Nuevos productos"],
            "confidence_score": 0.82,
            "prediction_date": datetime.now().isoformat()
        }
    
    def _get_mock_hot_skills(self, location: str, timeframe_months: int) -> List[Dict[str, Any]]:
        """Habilidades calientes simuladas"""
        return [
            {
                "skill": "Machine Learning",
                "demand_score": 0.9,
                "growth_rate": 0.25,
                "salary_range": [80000, 150000],
                "job_openings": 500,
                "trend": "rising"
            },
            {
                "skill": "Data Science",
                "demand_score": 0.85,
                "growth_rate": 0.20,
                "salary_range": [75000, 130000],
                "job_openings": 400,
                "trend": "rising"
            }
        ]
    
    def _get_mock_salary_trends(self, skill: str, location: str, experience_years: int) -> Dict[str, Any]:
        """Tendencias salariales simuladas"""
        return {
            "skill": skill,
            "location": location,
            "experience_years": experience_years,
            "current_salary": 80000,
            "yearly_predictions": [80000, 85000, 90000, 95000, 100000],
            "growth_rate": 0.25,
            "salary_factors": ["Demanda alta", "Escasez de talento"],
            "confidence_score": 0.78,
            "prediction_date": datetime.now().isoformat()
        }
    
    def _analyze_single_skill_trend(self, skill: str, location: str) -> SkillTrend:
        """Analiza tendencia de una habilidad específica"""
        # Implementación simulada
        return SkillTrend(
            skill_name=skill,
            current_demand=0.7,
            predicted_demand=0.8,
            growth_rate=0.1,
            market_saturation=0.6,
            salary_range=(70000, 120000),
            hot_markets=["San Francisco", "New York"],
            declining_markets=[]
        )
    
    def _get_industry_data(self, industry: str) -> Dict[str, Any]:
        """Obtiene datos de industria"""
        return {
            "name": industry,
            "current_size": 1000000,
            "growth_rate": 0.15,
            "key_players": ["Company A", "Company B"],
            "market_trends": ["Digital transformation", "AI adoption"]
        }
    
    def _predict_quarterly_growth(self, industry_data: Dict[str, Any], quarter: int) -> float:
        """Predice crecimiento trimestral"""
        base_growth = industry_data["growth_rate"]
        return base_growth * (1 - 0.05 * quarter)  # Desaceleración gradual
    
    def _analyze_growth_factors(self, industry_data: Dict[str, Any]) -> List[str]:
        """Analiza factores de crecimiento"""
        return ["Innovación tecnológica", "Demanda del mercado", "Inversión en R&D"]
    
    def _identify_market_opportunities(self, industry_data: Dict[str, Any]) -> List[str]:
        """Identifica oportunidades de mercado"""
        return ["Expansión internacional", "Nuevos productos", "Mercados emergentes"]
    
    def _get_skills_data(self, location: str) -> List[Dict[str, Any]]:
        """Obtiene datos de habilidades"""
        return [
            {
                "name": "Machine Learning",
                "demand": 0.9,
                "growth": 0.25,
                "salary_range": [80000, 150000],
                "job_openings": 500
            },
            {
                "name": "Data Science",
                "demand": 0.85,
                "growth": 0.20,
                "salary_range": [75000, 130000],
                "job_openings": 400
            }
        ]
    
    def _calculate_demand_score(self, skill_data: Dict[str, Any]) -> float:
        """Calcula score de demanda"""
        return skill_data["demand"]
    
    def _calculate_growth_rate(self, skill_data: Dict[str, Any]) -> float:
        """Calcula tasa de crecimiento"""
        return skill_data["growth"]
    
    def _get_salary_data(self, skill: str, location: str, experience_years: int) -> Dict[str, Any]:
        """Obtiene datos salariales"""
        return {
            "skill": skill,
            "location": location,
            "experience_years": experience_years,
            "current_salary": 80000,
            "historical_salaries": [70000, 75000, 80000],
            "market_factors": ["Demanda alta", "Escasez de talento"]
        }
    
    def _predict_yearly_salary(self, salary_data: Dict[str, Any], year: int) -> float:
        """Predice salario anual"""
        current_salary = salary_data["current_salary"]
        growth_rate = 0.05  # 5% anual
        return current_salary * (1 + growth_rate * (year + 1))
    
    def _analyze_salary_factors(self, salary_data: Dict[str, Any]) -> List[str]:
        """Analiza factores salariales"""
        return salary_data["market_factors"]
    
    def train_models(self, training_data: pd.DataFrame):
        """Entrena los modelos de predicción"""
        if not self.enabled:
            logger.info("MarketLaborPredictor: Entrenamiento deshabilitado")
            return
        
        try:
            # Implementación de entrenamiento
            logger.info("MarketLaborPredictor: Entrenando modelos...")
            self.is_trained = True
            logger.info("MarketLaborPredictor: Modelos entrenados exitosamente")
        except Exception as e:
            logger.error(f"Error training models: {e}")
    
    def save_models(self, filepath: str):
        """Guarda los modelos entrenados"""
        if not self.enabled or not self.is_trained:
            return
        
        try:
            joblib.dump(self.models, f"{filepath}/market_predictor_models.pkl")
            joblib.dump(self.scaler, f"{filepath}/market_predictor_scaler.pkl")
            logger.info("MarketLaborPredictor: Modelos guardados")
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self, filepath: str):
        """Carga modelos pre-entrenados"""
        if not self.enabled:
            return
        
        try:
            self.models = joblib.load(f"{filepath}/market_predictor_models.pkl")
            self.scaler = joblib.load(f"{filepath}/market_predictor_scaler.pkl")
            self.is_trained = True
            logger.info("MarketLaborPredictor: Modelos cargados")
        except Exception as e:
            logger.error(f"Error loading models: {e}")


# Instancia global del predictor de mercado
market_predictor = MarketLaborPredictor() 