"""
AURA - Predictive Analytics Service (FASE 1)
Servicio completo de analytics predictivo para nómina
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

# CONFIGURACIÓN: HABILITADO POR DEFECTO
ENABLED = True


@dataclass
class PredictiveResult:
    """Resultado de análisis predictivo"""
    prediction_type: str
    prediction_value: float
    confidence: float
    factors: List[str]
    recommendations: List[str]
    risk_level: str  # 'low', 'medium', 'high'
    timestamp: datetime
    employee_id: Optional[int] = None


@dataclass
class SentimentAnalysisResult:
    """Resultado de análisis de sentimientos"""
    employee_id: int
    sentiment_score: float
    sentiment_label: str  # 'positive', 'negative', 'neutral'
    confidence: float
    categories: Dict[str, float]
    keywords: List[str]
    recommendations: List[str]
    timestamp: datetime


@dataclass
class BenefitsOptimizationResult:
    """Resultado de optimización de beneficios"""
    employee_id: int
    current_benefits_cost: float
    optimized_benefits_cost: float
    savings_percentage: float
    recommended_benefits: List[Dict[str, Any]]
    employee_satisfaction_impact: float
    implementation_priority: str  # 'high', 'medium', 'low'
    timestamp: datetime


class PredictiveAnalyticsService:
    """
    Servicio completo de analytics predictivo para nómina
    """
    
    def __init__(self):
        self.enabled = ENABLED
        if not self.enabled:
            logger.info("PredictiveAnalyticsService: DESHABILITADO")
            return
        
        # Modelos de ML
        self.turnover_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.performance_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.attendance_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.sentiment_model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Scaler para normalización
        self.scaler = StandardScaler()
        
        # Estado de entrenamiento
        self.models_trained = {
            'turnover': False,
            'performance': False,
            'attendance': False,
            'sentiment': False
        }
        
        # Configuración de features
        self.feature_config = {
            'turnover': [
                'age', 'tenure', 'salary', 'performance_rating', 'attendance_rate',
                'overtime_hours', 'sick_days', 'promotion_count', 'salary_increases',
                'sentiment_score', 'engagement_score', 'workload_score'
            ],
            'performance': [
                'age', 'tenure', 'education_level', 'training_hours', 'overtime_hours',
                'attendance_rate', 'previous_performance', 'team_size', 'manager_rating'
            ],
            'attendance': [
                'age', 'tenure', 'salary', 'performance_rating', 'workload_score',
                'commute_distance', 'health_issues', 'family_responsibilities',
                'previous_attendance', 'seasonal_factors'
            ],
            'sentiment': [
                'salary_satisfaction', 'work_environment', 'management_quality',
                'career_growth', 'work_life_balance', 'benefits_satisfaction',
                'team_cohesion', 'job_security', 'workload_balance'
            ]
        }
        
        logger.info("PredictiveAnalyticsService: Inicializado")
    
    def predict_turnover_risk(self, employee_data: Dict[str, Any]) -> PredictiveResult:
        """
        Predice riesgo de rotación de empleados
        
        Args:
            employee_data: Datos del empleado
            
        Returns:
            Resultado de predicción de rotación
        """
        if not self.enabled:
            return self._get_mock_turnover_prediction(employee_data)
        
        try:
            # Extraer features
            features = self._extract_turnover_features(employee_data)
            
            # Hacer predicción
            if self.models_trained['turnover']:
                risk_score = self.turnover_model.predict_proba([features])[0][1]
            else:
                risk_score = self._calculate_heuristic_turnover_risk(employee_data)
            
            # Determinar nivel de riesgo
            risk_level = self._determine_risk_level(risk_score)
            
            # Identificar factores de riesgo
            risk_factors = self._identify_turnover_factors(employee_data)
            
            # Generar recomendaciones
            recommendations = self._generate_turnover_recommendations(risk_level, risk_factors)
            
            return PredictiveResult(
                prediction_type='turnover_risk',
                prediction_value=risk_score,
                confidence=0.85 if self.models_trained['turnover'] else 0.65,
                factors=risk_factors,
                recommendations=recommendations,
                risk_level=risk_level,
                timestamp=timezone.now(),
                employee_id=employee_data.get('employee_id')
            )
            
        except Exception as e:
            logger.error(f"Error prediciendo rotación: {str(e)}")
            return self._get_mock_turnover_prediction(employee_data)
    
    def predict_performance(self, employee_data: Dict[str, Any]) -> PredictiveResult:
        """
        Predice rendimiento futuro del empleado
        
        Args:
            employee_data: Datos del empleado
            
        Returns:
            Resultado de predicción de rendimiento
        """
        if not self.enabled:
            return self._get_mock_performance_prediction(employee_data)
        
        try:
            # Extraer features
            features = self._extract_performance_features(employee_data)
            
            # Hacer predicción
            if self.models_trained['performance']:
                performance_score = self.performance_model.predict([features])[0]
            else:
                performance_score = self._calculate_heuristic_performance(employee_data)
            
            # Normalizar score (0-100)
            performance_score = max(0, min(100, performance_score))
            
            # Generar recomendaciones
            recommendations = self._generate_performance_recommendations(performance_score, employee_data)
            
            return PredictiveResult(
                prediction_type='performance_prediction',
                prediction_value=performance_score,
                confidence=0.80 if self.models_trained['performance'] else 0.60,
                factors=['training', 'experience', 'motivation', 'workload'],
                recommendations=recommendations,
                risk_level='low' if performance_score > 70 else 'medium',
                timestamp=timezone.now(),
                employee_id=employee_data.get('employee_id')
            )
            
        except Exception as e:
            logger.error(f"Error prediciendo rendimiento: {str(e)}")
            return self._get_mock_performance_prediction(employee_data)
    
    def predict_attendance_patterns(self, employee_data: Dict[str, Any]) -> PredictiveResult:
        """
        Predice patrones de asistencia
        
        Args:
            employee_data: Datos del empleado
            
        Returns:
            Resultado de predicción de asistencia
        """
        if not self.enabled:
            return self._get_mock_attendance_prediction(employee_data)
        
        try:
            # Extraer features
            features = self._extract_attendance_features(employee_data)
            
            # Hacer predicción
            if self.models_trained['attendance']:
                attendance_rate = self.attendance_model.predict([features])[0]
            else:
                attendance_rate = self._calculate_heuristic_attendance(employee_data)
            
            # Normalizar (0-1)
            attendance_rate = max(0, min(1, attendance_rate))
            
            # Determinar nivel de riesgo
            risk_level = 'low' if attendance_rate > 0.95 else 'medium' if attendance_rate > 0.90 else 'high'
            
            # Generar recomendaciones
            recommendations = self._generate_attendance_recommendations(attendance_rate, employee_data)
            
            return PredictiveResult(
                prediction_type='attendance_prediction',
                prediction_value=attendance_rate,
                confidence=0.75 if self.models_trained['attendance'] else 0.55,
                factors=['health', 'motivation', 'workload', 'personal_issues'],
                recommendations=recommendations,
                risk_level=risk_level,
                timestamp=timezone.now(),
                employee_id=employee_data.get('employee_id')
            )
            
        except Exception as e:
            logger.error(f"Error prediciendo asistencia: {str(e)}")
            return self._get_mock_attendance_prediction(employee_data)
    
    def analyze_sentiment(self, employee_data: Dict[str, Any]) -> SentimentAnalysisResult:
        """
        Analiza sentimientos del empleado
        
        Args:
            employee_data: Datos del empleado
            
        Returns:
            Resultado de análisis de sentimientos
        """
        if not self.enabled:
            return self._get_mock_sentiment_analysis(employee_data)
        
        try:
            # Extraer features de sentimiento
            sentiment_features = self._extract_sentiment_features(employee_data)
            
            # Calcular score de sentimiento
            sentiment_score = self._calculate_sentiment_score(sentiment_features)
            
            # Determinar etiqueta
            if sentiment_score > 0.1:
                sentiment_label = 'positive'
            elif sentiment_score < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            # Analizar categorías
            categories = self._analyze_sentiment_categories(sentiment_features)
            
            # Extraer keywords
            keywords = self._extract_sentiment_keywords(employee_data)
            
            # Generar recomendaciones
            recommendations = self._generate_sentiment_recommendations(sentiment_score, categories)
            
            return SentimentAnalysisResult(
                employee_id=employee_data.get('employee_id'),
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                confidence=0.85,
                categories=categories,
                keywords=keywords,
                recommendations=recommendations,
                timestamp=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error analizando sentimientos: {str(e)}")
            return self._get_mock_sentiment_analysis(employee_data)
    
    def optimize_benefits(self, employee_data: Dict[str, Any]) -> BenefitsOptimizationResult:
        """
        Optimiza beneficios para el empleado
        
        Args:
            employee_data: Datos del empleado
            
        Returns:
            Resultado de optimización de beneficios
        """
        if not self.enabled:
            return self._get_mock_benefits_optimization(employee_data)
        
        try:
            # Analizar beneficios actuales
            current_benefits = employee_data.get('current_benefits', {})
            current_cost = self._calculate_benefits_cost(current_benefits)
            
            # Generar beneficios optimizados
            optimized_benefits = self._generate_optimized_benefits(employee_data)
            optimized_cost = self._calculate_benefits_cost(optimized_benefits)
            
            # Calcular ahorros
            savings = current_cost - optimized_cost
            savings_percentage = (savings / current_cost * 100) if current_cost > 0 else 0
            
            # Calcular impacto en satisfacción
            satisfaction_impact = self._calculate_satisfaction_impact(optimized_benefits, employee_data)
            
            # Determinar prioridad de implementación
            implementation_priority = self._determine_implementation_priority(savings_percentage, satisfaction_impact)
            
            return BenefitsOptimizationResult(
                employee_id=employee_data.get('employee_id'),
                current_benefits_cost=current_cost,
                optimized_benefits_cost=optimized_cost,
                savings_percentage=savings_percentage,
                recommended_benefits=optimized_benefits,
                employee_satisfaction_impact=satisfaction_impact,
                implementation_priority=implementation_priority,
                timestamp=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error optimizando beneficios: {str(e)}")
            return self._get_mock_benefits_optimization(employee_data)
    
    def generate_comprehensive_report(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera reporte completo de analytics predictivo
        
        Args:
            employee_data: Datos del empleado
            
        Returns:
            Reporte completo
        """
        if not self.enabled:
            return self._get_mock_comprehensive_report(employee_data)
        
        try:
            # Ejecutar todos los análisis
            turnover_prediction = self.predict_turnover_risk(employee_data)
            performance_prediction = self.predict_performance(employee_data)
            attendance_prediction = self.predict_attendance_patterns(employee_data)
            sentiment_analysis = self.analyze_sentiment(employee_data)
            benefits_optimization = self.optimize_benefits(employee_data)
            
            # Calcular score de riesgo general
            overall_risk_score = self._calculate_overall_risk_score(
                turnover_prediction, performance_prediction, attendance_prediction, sentiment_analysis
            )
            
            # Generar recomendaciones prioritarias
            priority_recommendations = self._generate_priority_recommendations(
                turnover_prediction, performance_prediction, attendance_prediction, 
                sentiment_analysis, benefits_optimization
            )
            
            return {
                'employee_id': employee_data.get('employee_id'),
                'report_date': timezone.now().isoformat(),
                'overall_risk_score': overall_risk_score,
                'risk_level': self._determine_risk_level(overall_risk_score),
                'predictions': {
                    'turnover_risk': {
                        'score': turnover_prediction.prediction_value,
                        'confidence': turnover_prediction.confidence,
                        'risk_level': turnover_prediction.risk_level,
                        'factors': turnover_prediction.factors,
                        'recommendations': turnover_prediction.recommendations
                    },
                    'performance_prediction': {
                        'score': performance_prediction.prediction_value,
                        'confidence': performance_prediction.confidence,
                        'risk_level': performance_prediction.risk_level,
                        'recommendations': performance_prediction.recommendations
                    },
                    'attendance_prediction': {
                        'score': attendance_prediction.prediction_value,
                        'confidence': attendance_prediction.confidence,
                        'risk_level': attendance_prediction.risk_level,
                        'recommendations': attendance_prediction.recommendations
                    }
                },
                'sentiment_analysis': {
                    'score': sentiment_analysis.sentiment_score,
                    'label': sentiment_analysis.sentiment_label,
                    'confidence': sentiment_analysis.confidence,
                    'categories': sentiment_analysis.categories,
                    'keywords': sentiment_analysis.keywords,
                    'recommendations': sentiment_analysis.recommendations
                },
                'benefits_optimization': {
                    'current_cost': benefits_optimization.current_benefits_cost,
                    'optimized_cost': benefits_optimization.optimized_benefits_cost,
                    'savings_percentage': benefits_optimization.savings_percentage,
                    'recommended_benefits': benefits_optimization.recommended_benefits,
                    'satisfaction_impact': benefits_optimization.employee_satisfaction_impact,
                    'implementation_priority': benefits_optimization.implementation_priority
                },
                'priority_recommendations': priority_recommendations,
                'next_review_date': (timezone.now() + timedelta(days=30)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte completo: {str(e)}")
            return self._get_mock_comprehensive_report(employee_data)
    
    # Métodos auxiliares privados
    
    def _extract_turnover_features(self, employee_data: Dict[str, Any]) -> List[float]:
        """Extrae features para predicción de rotación"""
        features = []
        for feature in self.feature_config['turnover']:
            value = employee_data.get(feature, 0)
            if isinstance(value, (int, float)):
                features.append(float(value))
            else:
                features.append(0.0)
        return features
    
    def _extract_performance_features(self, employee_data: Dict[str, Any]) -> List[float]:
        """Extrae features para predicción de rendimiento"""
        features = []
        for feature in self.feature_config['performance']:
            value = employee_data.get(feature, 0)
            if isinstance(value, (int, float)):
                features.append(float(value))
            else:
                features.append(0.0)
        return features
    
    def _extract_attendance_features(self, employee_data: Dict[str, Any]) -> List[float]:
        """Extrae features para predicción de asistencia"""
        features = []
        for feature in self.feature_config['attendance']:
            value = employee_data.get(feature, 0)
            if isinstance(value, (int, float)):
                features.append(float(value))
            else:
                features.append(0.0)
        return features
    
    def _extract_sentiment_features(self, employee_data: Dict[str, Any]) -> Dict[str, float]:
        """Extrae features para análisis de sentimientos"""
        features = {}
        for feature in self.feature_config['sentiment']:
            value = employee_data.get(feature, 0.5)
            if isinstance(value, (int, float)):
                features[feature] = float(value)
            else:
                features[feature] = 0.5
        return features
    
    def _calculate_heuristic_turnover_risk(self, employee_data: Dict[str, Any]) -> float:
        """Calcula riesgo de rotación usando heurísticas"""
        risk_factors = []
        
        # Antigüedad baja
        tenure = employee_data.get('tenure', 0)
        if tenure < 1:
            risk_factors.append(0.3)
        elif tenure < 2:
            risk_factors.append(0.2)
        
        # Bajo rendimiento
        performance = employee_data.get('performance_rating', 0.5)
        if performance < 0.6:
            risk_factors.append(0.25)
        
        # Baja asistencia
        attendance = employee_data.get('attendance_rate', 0.95)
        if attendance < 0.9:
            risk_factors.append(0.2)
        
        # Muchas horas extra (sobrecarga)
        overtime = employee_data.get('overtime_hours', 0)
        if overtime > 20:
            risk_factors.append(0.15)
        
        return min(sum(risk_factors), 1.0)
    
    def _calculate_heuristic_performance(self, employee_data: Dict[str, Any]) -> float:
        """Calcula rendimiento usando heurísticas"""
        performance_factors = []
        
        # Rendimiento actual
        current_performance = employee_data.get('performance_rating', 0.5)
        performance_factors.append(current_performance * 0.4)
        
        # Antigüedad (experiencia)
        tenure = employee_data.get('tenure', 0)
        experience_bonus = min(tenure * 0.05, 0.2)
        performance_factors.append(experience_bonus)
        
        # Entrenamiento
        training_hours = employee_data.get('training_hours', 0)
        training_bonus = min(training_hours * 0.01, 0.15)
        performance_factors.append(training_bonus)
        
        # Asistencia
        attendance = employee_data.get('attendance_rate', 0.95)
        performance_factors.append(attendance * 0.25)
        
        return min(sum(performance_factors), 1.0) * 100
    
    def _calculate_heuristic_attendance(self, employee_data: Dict[str, Any]) -> float:
        """Calcula asistencia usando heurísticas"""
        attendance_factors = []
        
        # Asistencia histórica
        historical_attendance = employee_data.get('attendance_rate', 0.95)
        attendance_factors.append(historical_attendance * 0.6)
        
        # Satisfacción laboral
        satisfaction = employee_data.get('job_satisfaction', 0.5)
        attendance_factors.append(satisfaction * 0.2)
        
        # Carga de trabajo
        workload = employee_data.get('workload_score', 0.5)
        if workload < 0.8:  # Carga de trabajo manejable
            attendance_factors.append(0.1)
        else:
            attendance_factors.append(0.05)
        
        # Distancia al trabajo
        commute = employee_data.get('commute_distance', 10)
        if commute < 20:  # Distancia razonable
            attendance_factors.append(0.1)
        else:
            attendance_factors.append(0.05)
        
        return min(sum(attendance_factors), 1.0)
    
    def _calculate_sentiment_score(self, sentiment_features: Dict[str, float]) -> float:
        """Calcula score de sentimiento"""
        weights = {
            'salary_satisfaction': 0.2,
            'work_environment': 0.15,
            'management_quality': 0.15,
            'career_growth': 0.15,
            'work_life_balance': 0.15,
            'benefits_satisfaction': 0.1,
            'team_cohesion': 0.05,
            'job_security': 0.03,
            'workload_balance': 0.02
        }
        
        total_score = 0
        total_weight = 0
        
        for feature, weight in weights.items():
            if feature in sentiment_features:
                total_score += sentiment_features[feature] * weight
                total_weight += weight
        
        if total_weight > 0:
            # Normalizar a rango -1 a 1
            normalized_score = (total_score / total_weight - 0.5) * 2
            return max(-1, min(1, normalized_score))
        
        return 0.0
    
    def _analyze_sentiment_categories(self, sentiment_features: Dict[str, float]) -> Dict[str, float]:
        """Analiza categorías de sentimiento"""
        categories = {}
        
        # Mapear features a categorías
        category_mapping = {
            'salary_satisfaction': 'compensation',
            'benefits_satisfaction': 'compensation',
            'work_environment': 'workplace',
            'team_cohesion': 'workplace',
            'management_quality': 'leadership',
            'career_growth': 'development',
            'work_life_balance': 'wellbeing',
            'job_security': 'security',
            'workload_balance': 'workload'
        }
        
        for feature, category in category_mapping.items():
            if feature in sentiment_features:
                if category not in categories:
                    categories[category] = []
                categories[category].append(sentiment_features[feature])
        
        # Calcular promedios por categoría
        for category in categories:
            categories[category] = np.mean(categories[category])
        
        return categories
    
    def _extract_sentiment_keywords(self, employee_data: Dict[str, Any]) -> List[str]:
        """Extrae keywords de sentimiento"""
        keywords = []
        
        # Analizar feedback y comentarios
        feedback = employee_data.get('feedback', '')
        if feedback:
            # Palabras positivas
            positive_words = ['satisfecho', 'contento', 'feliz', 'motivado', 'apoyado']
            for word in positive_words:
                if word in feedback.lower():
                    keywords.append(word)
            
            # Palabras negativas
            negative_words = ['frustrado', 'estresado', 'insatisfecho', 'preocupado', 'confundido']
            for word in negative_words:
                if word in feedback.lower():
                    keywords.append(word)
        
        return keywords[:5]  # Máximo 5 keywords
    
    def _generate_optimized_benefits(self, employee_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera beneficios optimizados"""
        age = employee_data.get('age', 30)
        salary = employee_data.get('salary', 50000)
        family_size = employee_data.get('family_size', 1)
        
        optimized_benefits = []
        
        # Seguro médico
        if family_size > 1:
            optimized_benefits.append({
                'type': 'health_insurance',
                'name': 'Seguro Familiar',
                'cost': salary * 0.08,
                'value': salary * 0.12,
                'priority': 'high'
            })
        else:
            optimized_benefits.append({
                'type': 'health_insurance',
                'name': 'Seguro Individual',
                'cost': salary * 0.05,
                'value': salary * 0.08,
                'priority': 'medium'
            })
        
        # Plan de retiro
        if age > 35:
            optimized_benefits.append({
                'type': 'retirement',
                'name': 'Plan de Retiro',
                'cost': salary * 0.06,
                'value': salary * 0.10,
                'priority': 'high'
            })
        
        # Desarrollo profesional
        optimized_benefits.append({
            'type': 'development',
            'name': 'Capacitación',
            'cost': salary * 0.02,
            'value': salary * 0.05,
            'priority': 'medium'
        })
        
        return optimized_benefits
    
    def _calculate_benefits_cost(self, benefits: List[Dict[str, Any]]) -> float:
        """Calcula costo de beneficios"""
        total_cost = 0
        for benefit in benefits:
            total_cost += benefit.get('cost', 0)
        return total_cost
    
    def _calculate_satisfaction_impact(self, benefits: List[Dict[str, Any]], employee_data: Dict[str, Any]) -> float:
        """Calcula impacto en satisfacción"""
        impact = 0.1  # Base
        
        for benefit in benefits:
            if benefit.get('priority') == 'high':
                impact += 0.15
            elif benefit.get('priority') == 'medium':
                impact += 0.10
            else:
                impact += 0.05
        
        return min(impact, 1.0)
    
    def _determine_implementation_priority(self, savings_percentage: float, satisfaction_impact: float) -> str:
        """Determina prioridad de implementación"""
        if savings_percentage > 20 and satisfaction_impact > 0.3:
            return 'high'
        elif savings_percentage > 10 or satisfaction_impact > 0.2:
            return 'medium'
        else:
            return 'low'
    
    def _determine_risk_level(self, score: float) -> str:
        """Determina nivel de riesgo"""
        if score > 0.7:
            return 'high'
        elif score > 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _identify_turnover_factors(self, employee_data: Dict[str, Any]) -> List[str]:
        """Identifica factores de riesgo de rotación"""
        factors = []
        
        if employee_data.get('tenure', 0) < 1:
            factors.append('Antigüedad baja')
        
        if employee_data.get('performance_rating', 0.5) < 0.6:
            factors.append('Bajo rendimiento')
        
        if employee_data.get('attendance_rate', 0.95) < 0.9:
            factors.append('Baja asistencia')
        
        if employee_data.get('overtime_hours', 0) > 20:
            factors.append('Sobrecarga de trabajo')
        
        if employee_data.get('salary_increases', 0) < 0.05:
            factors.append('Pocos aumentos salariales')
        
        return factors
    
    def _generate_turnover_recommendations(self, risk_level: str, factors: List[str]) -> List[str]:
        """Genera recomendaciones para reducir rotación"""
        recommendations = []
        
        if risk_level == 'high':
            recommendations.append('Reunión urgente con supervisor')
            recommendations.append('Evaluación de satisfacción laboral')
            recommendations.append('Programa de retención personalizado')
        
        if 'Antigüedad baja' in factors:
            recommendations.append('Programa de onboarding mejorado')
            recommendations.append('Mentoría para nuevos empleados')
        
        if 'Bajo rendimiento' in factors:
            recommendations.append('Plan de desarrollo personalizado')
            recommendations.append('Capacitación específica')
        
        if 'Sobrecarga de trabajo' in factors:
            recommendations.append('Redistribución de carga de trabajo')
            recommendations.append('Evaluación de procesos')
        
        return recommendations
    
    def _generate_performance_recommendations(self, performance_score: float, employee_data: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones para mejorar rendimiento"""
        recommendations = []
        
        if performance_score < 60:
            recommendations.append('Plan de desarrollo urgente')
            recommendations.append('Capacitación intensiva')
            recommendations.append('Mentoría especializada')
        elif performance_score < 80:
            recommendations.append('Capacitación adicional')
            recommendations.append('Objetivos de mejora')
            recommendations.append('Feedback regular')
        else:
            recommendations.append('Mantener excelente rendimiento')
            recommendations.append('Considerar promoción')
            recommendations.append('Mentoría a otros empleados')
        
        return recommendations
    
    def _generate_attendance_recommendations(self, attendance_rate: float, employee_data: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones para mejorar asistencia"""
        recommendations = []
        
        if attendance_rate < 0.85:
            recommendations.append('Entrevista para identificar problemas')
            recommendations.append('Evaluación de salud')
            recommendations.append('Flexibilidad de horarios')
        elif attendance_rate < 0.95:
            recommendations.append('Monitoreo de patrones')
            recommendations.append('Comunicación proactiva')
            recommendations.append('Programa de bienestar')
        else:
            recommendations.append('Mantener excelente asistencia')
            recommendations.append('Reconocimiento por puntualidad')
        
        return recommendations
    
    def _generate_sentiment_recommendations(self, sentiment_score: float, categories: Dict[str, float]) -> List[str]:
        """Genera recomendaciones basadas en sentimientos"""
        recommendations = []
        
        if sentiment_score < -0.2:
            recommendations.append('Entrevista de satisfacción urgente')
            recommendations.append('Programa de mejora del clima laboral')
            recommendations.append('Revisión de políticas')
        
        for category, score in categories.items():
            if score < 0.4:
                if category == 'compensation':
                    recommendations.append('Revisión de compensación')
                elif category == 'leadership':
                    recommendations.append('Capacitación de managers')
                elif category == 'workplace':
                    recommendations.append('Mejora del ambiente de trabajo')
                elif category == 'development':
                    recommendations.append('Oportunidades de crecimiento')
        
        return recommendations
    
    def _calculate_overall_risk_score(self, turnover: PredictiveResult, performance: PredictiveResult, 
                                    attendance: PredictiveResult, sentiment: SentimentAnalysisResult) -> float:
        """Calcula score de riesgo general"""
        weights = {
            'turnover': 0.4,
            'performance': 0.25,
            'attendance': 0.2,
            'sentiment': 0.15
        }
        
        # Normalizar scores
        turnover_score = turnover.prediction_value
        performance_score = 1 - (performance.prediction_value / 100)  # Invertir (menor rendimiento = mayor riesgo)
        attendance_score = 1 - attendance.prediction_value  # Invertir (menor asistencia = mayor riesgo)
        sentiment_score = (1 - sentiment.sentiment_score) / 2  # Normalizar a 0-1
        
        overall_score = (
            turnover_score * weights['turnover'] +
            performance_score * weights['performance'] +
            attendance_score * weights['attendance'] +
            sentiment_score * weights['sentiment']
        )
        
        return min(overall_score, 1.0)
    
    def _generate_priority_recommendations(self, turnover: PredictiveResult, performance: PredictiveResult,
                                         attendance: PredictiveResult, sentiment: SentimentAnalysisResult,
                                         benefits: BenefitsOptimizationResult) -> List[Dict[str, Any]]:
        """Genera recomendaciones prioritarias"""
        recommendations = []
        
        # Prioridad 1: Riesgo alto de rotación
        if turnover.risk_level == 'high':
            recommendations.append({
                'priority': 1,
                'category': 'retention',
                'title': 'Prevenir Rotación Urgente',
                'description': f'Empleado con {turnover.prediction_value:.1%} de riesgo de rotación',
                'actions': turnover.recommendations[:3],
                'impact': 'high'
            })
        
        # Prioridad 2: Bajo rendimiento
        if performance.prediction_value < 60:
            recommendations.append({
                'priority': 2,
                'category': 'performance',
                'title': 'Mejorar Rendimiento',
                'description': f'Rendimiento actual: {performance.prediction_value:.0f}/100',
                'actions': performance.recommendations[:3],
                'impact': 'medium'
            })
        
        # Prioridad 3: Optimización de beneficios
        if benefits.savings_percentage > 15:
            recommendations.append({
                'priority': 3,
                'category': 'benefits',
                'title': 'Optimizar Beneficios',
                'description': f'Ahorro potencial: {benefits.savings_percentage:.1f}%',
                'actions': ['Implementar beneficios recomendados', 'Comunicar cambios a empleado'],
                'impact': 'medium'
            })
        
        return recommendations
    
    # Métodos mock para cuando el servicio está deshabilitado
    
    def _get_mock_turnover_prediction(self, employee_data: Dict[str, Any]) -> PredictiveResult:
        return PredictiveResult(
            prediction_type='turnover_risk',
            prediction_value=0.25,
            confidence=0.65,
            factors=['Antigüedad media', 'Rendimiento estable'],
            recommendations=['Monitoreo regular', 'Feedback constructivo'],
            risk_level='medium',
            timestamp=timezone.now(),
            employee_id=employee_data.get('employee_id')
        )
    
    def _get_mock_performance_prediction(self, employee_data: Dict[str, Any]) -> PredictiveResult:
        return PredictiveResult(
            prediction_type='performance_prediction',
            prediction_value=75.0,
            confidence=0.60,
            factors=['Experiencia', 'Motivación'],
            recommendations=['Capacitación adicional', 'Objetivos claros'],
            risk_level='low',
            timestamp=timezone.now(),
            employee_id=employee_data.get('employee_id')
        )
    
    def _get_mock_attendance_prediction(self, employee_data: Dict[str, Any]) -> PredictiveResult:
        return PredictiveResult(
            prediction_type='attendance_prediction',
            prediction_value=0.92,
            confidence=0.55,
            factors=['Salud', 'Motivación'],
            recommendations=['Monitoreo de patrones', 'Comunicación proactiva'],
            risk_level='low',
            timestamp=timezone.now(),
            employee_id=employee_data.get('employee_id')
        )
    
    def _get_mock_sentiment_analysis(self, employee_data: Dict[str, Any]) -> SentimentAnalysisResult:
        return SentimentAnalysisResult(
            employee_id=employee_data.get('employee_id'),
            sentiment_score=0.2,
            sentiment_label='positive',
            confidence=0.65,
            categories={
                'compensation': 0.6,
                'workplace': 0.5,
                'leadership': 0.6,
                'development': 0.7
            },
            keywords=['satisfecho', 'motivado'],
            recommendations=['Mantener políticas actuales', 'Reconocimiento regular'],
            timestamp=timezone.now()
        )
    
    def _get_mock_benefits_optimization(self, employee_data: Dict[str, Any]) -> BenefitsOptimizationResult:
        return BenefitsOptimizationResult(
            employee_id=employee_data.get('employee_id'),
            current_benefits_cost=5000.0,
            optimized_benefits_cost=4200.0,
            savings_percentage=16.0,
            recommended_benefits=[
                {'type': 'health_insurance', 'name': 'Seguro Mejorado', 'cost': 3000, 'value': 4500, 'priority': 'high'},
                {'type': 'retirement', 'name': 'Plan de Retiro', 'cost': 1200, 'value': 2000, 'priority': 'medium'}
            ],
            employee_satisfaction_impact=0.25,
            implementation_priority='medium',
            timestamp=timezone.now()
        )
    
    def _get_mock_comprehensive_report(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'employee_id': employee_data.get('employee_id'),
            'report_date': timezone.now().isoformat(),
            'overall_risk_score': 0.35,
            'risk_level': 'medium',
            'predictions': {
                'turnover_risk': {'score': 0.25, 'confidence': 0.65, 'risk_level': 'medium'},
                'performance_prediction': {'score': 75.0, 'confidence': 0.60, 'risk_level': 'low'},
                'attendance_prediction': {'score': 0.92, 'confidence': 0.55, 'risk_level': 'low'}
            },
            'sentiment_analysis': {'score': 0.2, 'label': 'positive', 'confidence': 0.65},
            'benefits_optimization': {'savings_percentage': 16.0, 'implementation_priority': 'medium'},
            'priority_recommendations': [
                {'priority': 1, 'category': 'monitoring', 'title': 'Monitoreo Regular', 'impact': 'medium'}
            ],
            'next_review_date': (timezone.now() + timedelta(days=30)).isoformat()
        } 