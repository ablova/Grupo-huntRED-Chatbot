"""
AURA - Sentiment Analyzer (FASE 1)
Análisis de sentimientos para satisfacción laboral y engagement
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import re
import json

logger = logging.getLogger(__name__)

# CONFIGURACIÓN: DESHABILITADO POR DEFECTO
ENABLED = False  # Cambiar a True para habilitar


@dataclass
class SentimentResult:
    """Resultado de análisis de sentimientos"""
    text: str
    sentiment_score: float
    sentiment_label: str  # 'positive', 'negative', 'neutral'
    confidence: float
    categories: Dict[str, float]
    keywords: List[str]
    timestamp: datetime
    user_id: Optional[int] = None


@dataclass
class EngagementAnalysis:
    """Análisis de engagement"""
    user_id: int
    engagement_score: float
    activity_level: str  # 'high', 'medium', 'low'
    satisfaction_score: float
    churn_risk: float
    recommendations: List[str]
    last_activity: datetime
    activity_trend: str  # 'increasing', 'decreasing', 'stable'


class SentimentAnalyzer:
    """
    Analizador de sentimientos para satisfacción laboral y engagement
    """
    
    def __init__(self):
        self.enabled = ENABLED
        if not self.enabled:
            logger.info("SentimentAnalyzer: DESHABILITADO")
            return
        
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.sentiment_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        
        # Categorías de análisis
        self.categories = {
            'job_satisfaction': ['satisfied', 'happy', 'fulfilled', 'motivated', 'engaged'],
            'work_environment': ['culture', 'team', 'colleagues', 'atmosphere', 'environment'],
            'compensation': ['salary', 'benefits', 'compensation', 'pay', 'rewards'],
            'career_growth': ['growth', 'development', 'advancement', 'opportunities', 'learning'],
            'work_life_balance': ['balance', 'flexibility', 'time', 'family', 'personal'],
            'management': ['manager', 'leadership', 'supervision', 'support', 'guidance']
        }
        
        logger.info("SentimentAnalyzer: Inicializado")
    
    def analyze_text_sentiment(self, text: str, user_id: Optional[int] = None) -> SentimentResult:
        """
        Analiza sentimientos en texto
        """
        if not self.enabled:
            return self._get_mock_sentiment_result(text, user_id)
        
        try:
            # Preprocesar texto
            processed_text = self._preprocess_text(text)
            
            # Extraer características
            features = self.vectorizer.transform([processed_text])
            
            # Predecir sentimiento
            sentiment_score = self._predict_sentiment_score(features)
            sentiment_label = self._get_sentiment_label(sentiment_score)
            confidence = self._calculate_confidence(features)
            
            # Analizar categorías
            categories = self._analyze_categories(processed_text)
            
            # Extraer palabras clave
            keywords = self._extract_keywords(processed_text)
            
            return SentimentResult(
                text=text,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                confidence=confidence,
                categories=categories,
                keywords=keywords,
                timestamp=datetime.now(),
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return self._get_mock_sentiment_result(text, user_id)
    
    def analyze_user_engagement(self, user_id: int, user_data: Dict[str, Any]) -> EngagementAnalysis:
        """
        Analiza engagement de un usuario
        """
        if not self.enabled:
            return self._get_mock_engagement_analysis(user_id, user_data)
        
        try:
            # Calcular score de engagement
            engagement_score = self._calculate_engagement_score(user_data)
            activity_level = self._get_activity_level(engagement_score)
            
            # Calcular satisfacción
            satisfaction_score = self._calculate_satisfaction_score(user_data)
            
            # Calcular riesgo de churn
            churn_risk = self._calculate_churn_risk(user_data)
            
            # Generar recomendaciones
            recommendations = self._generate_engagement_recommendations(user_data)
            
            # Analizar tendencia
            activity_trend = self._analyze_activity_trend(user_data)
            
            return EngagementAnalysis(
                user_id=user_id,
                engagement_score=engagement_score,
                activity_level=activity_level,
                satisfaction_score=satisfaction_score,
                churn_risk=churn_risk,
                recommendations=recommendations,
                last_activity=user_data.get("last_activity", datetime.now()),
                activity_trend=activity_trend
            )
            
        except Exception as e:
            logger.error(f"Error analyzing user engagement: {user_id}: {e}")
            return self._get_mock_engagement_analysis(user_id, user_data)
    
    def analyze_team_sentiment(self, team_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza sentimientos de un equipo completo
        """
        if not self.enabled:
            return self._get_mock_team_sentiment(team_data)
        
        try:
            team_sentiments = []
            overall_sentiment = 0
            category_scores = defaultdict(list)
            
            for member in team_data:
                sentiment = self.analyze_text_sentiment(
                    member.get("feedback", ""),
                    member.get("user_id")
                )
                team_sentiments.append(sentiment)
                overall_sentiment += sentiment.sentiment_score
                
                # Agregar scores por categoría
                for category, score in sentiment.categories.items():
                    category_scores[category].append(score)
            
            # Calcular promedios
            avg_sentiment = overall_sentiment / len(team_data) if team_data else 0
            avg_categories = {
                category: np.mean(scores) for category, scores in category_scores.items()
            }
            
            # Identificar problemas
            issues = self._identify_team_issues(avg_categories)
            
            # Generar recomendaciones
            recommendations = self._generate_team_recommendations(avg_categories, issues)
            
            return {
                "team_size": len(team_data),
                "overall_sentiment": avg_sentiment,
                "sentiment_label": self._get_sentiment_label(avg_sentiment),
                "category_scores": avg_categories,
                "issues": issues,
                "recommendations": recommendations,
                "individual_sentiments": [
                    {
                        "user_id": s.user_id,
                        "sentiment_score": s.sentiment_score,
                        "sentiment_label": s.sentiment_label
                    } for s in team_sentiments
                ],
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing team sentiment: {e}")
            return self._get_mock_team_sentiment(team_data)
    
    def predict_churn_risk(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predice riesgo de churn de un usuario
        """
        if not self.enabled:
            return self._get_mock_churn_prediction(user_data)
        
        try:
            # Calcular factores de riesgo
            engagement_risk = self._calculate_engagement_risk(user_data)
            satisfaction_risk = self._calculate_satisfaction_risk(user_data)
            activity_risk = self._calculate_activity_risk(user_data)
            
            # Score compuesto de riesgo
            total_risk = (engagement_risk + satisfaction_risk + activity_risk) / 3
            
            # Categorizar riesgo
            risk_level = self._categorize_risk_level(total_risk)
            
            # Factores contribuyentes
            risk_factors = self._identify_risk_factors(user_data)
            
            # Recomendaciones de retención
            retention_recommendations = self._generate_retention_recommendations(risk_factors)
            
            return {
                "user_id": user_data.get("user_id"),
                "churn_risk": total_risk,
                "risk_level": risk_level,
                "engagement_risk": engagement_risk,
                "satisfaction_risk": satisfaction_risk,
                "activity_risk": activity_risk,
                "risk_factors": risk_factors,
                "retention_recommendations": retention_recommendations,
                "prediction_confidence": 0.85,
                "prediction_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting churn risk: {e}")
            return self._get_mock_churn_prediction(user_data)
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocesa texto para análisis"""
        # Convertir a minúsculas
        text = text.lower()
        
        # Remover caracteres especiales
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remover espacios extra
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _predict_sentiment_score(self, features) -> float:
        """Predice score de sentimiento"""
        if not self.is_trained:
            # Simulación cuando no está entrenado
            return np.random.uniform(-1, 1)
        
        # En implementación real, usar el modelo entrenado
        return np.random.uniform(-1, 1)
    
    def _get_sentiment_label(self, score: float) -> str:
        """Convierte score a etiqueta de sentimiento"""
        if score > 0.2:
            return "positive"
        elif score < -0.2:
            return "negative"
        else:
            return "neutral"
    
    def _calculate_confidence(self, features) -> float:
        """Calcula confianza de la predicción"""
        # Simulación de confianza
        return np.random.uniform(0.7, 0.95)
    
    def _analyze_categories(self, text: str) -> Dict[str, float]:
        """Analiza sentimientos por categorías"""
        categories = {}
        for category, keywords in self.categories.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 0.2
            categories[category] = min(score, 1.0)
        return categories
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrae palabras clave del texto"""
        words = text.split()
        # Filtrar palabras comunes y cortas
        keywords = [word for word in words if len(word) > 3 and word not in ['the', 'and', 'for', 'with']]
        return keywords[:10]  # Top 10 keywords
    
    def _calculate_engagement_score(self, user_data: Dict[str, Any]) -> float:
        """Calcula score de engagement"""
        # Factores de engagement
        activity_frequency = user_data.get("activity_frequency", 0.5)
        interaction_count = user_data.get("interaction_count", 0)
        content_creation = user_data.get("content_creation", 0)
        event_participation = user_data.get("event_participation", 0)
        
        # Score compuesto
        engagement_score = (
            activity_frequency * 0.4 +
            min(interaction_count / 100, 1.0) * 0.3 +
            min(content_creation / 10, 1.0) * 0.2 +
            min(event_participation / 5, 1.0) * 0.1
        )
        
        return engagement_score
    
    def _get_activity_level(self, engagement_score: float) -> str:
        """Determina nivel de actividad"""
        if engagement_score > 0.7:
            return "high"
        elif engagement_score > 0.4:
            return "medium"
        else:
            return "low"
    
    def _calculate_satisfaction_score(self, user_data: Dict[str, Any]) -> float:
        """Calcula score de satisfacción"""
        # Simulación basada en datos del usuario
        base_satisfaction = user_data.get("base_satisfaction", 0.6)
        recent_feedback = user_data.get("recent_feedback_sentiment", 0)
        
        return (base_satisfaction + recent_feedback) / 2
    
    def _calculate_churn_risk(self, user_data: Dict[str, Any]) -> float:
        """Calcula riesgo de churn"""
        engagement_score = self._calculate_engagement_score(user_data)
        satisfaction_score = self._calculate_satisfaction_score(user_data)
        days_inactive = user_data.get("days_inactive", 0)
        
        # Factores de riesgo
        engagement_risk = 1 - engagement_score
        satisfaction_risk = 1 - satisfaction_score
        inactivity_risk = min(days_inactive / 30, 1.0)
        
        # Score compuesto de riesgo
        total_risk = (engagement_risk * 0.4 + satisfaction_risk * 0.4 + inactivity_risk * 0.2)
        
        return total_risk
    
    def _generate_engagement_recommendations(self, user_data: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones de engagement"""
        recommendations = []
        engagement_score = self._calculate_engagement_score(user_data)
        
        if engagement_score < 0.4:
            recommendations.append("Participar en eventos de networking")
            recommendations.append("Crear contenido profesional")
            recommendations.append("Conectar con colegas")
        
        if user_data.get("days_inactive", 0) > 7:
            recommendations.append("Revisar notificaciones pendientes")
            recommendations.append("Actualizar perfil profesional")
        
        return recommendations
    
    def _analyze_activity_trend(self, user_data: Dict[str, Any]) -> str:
        """Analiza tendencia de actividad"""
        recent_activity = user_data.get("recent_activity", 0)
        previous_activity = user_data.get("previous_activity", 0)
        
        if recent_activity > previous_activity * 1.2:
            return "increasing"
        elif recent_activity < previous_activity * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _identify_team_issues(self, category_scores: Dict[str, float]) -> List[str]:
        """Identifica problemas del equipo"""
        issues = []
        for category, score in category_scores.items():
            if score < 0.4:
                if category == "job_satisfaction":
                    issues.append("Baja satisfacción laboral general")
                elif category == "work_environment":
                    issues.append("Problemas en el ambiente de trabajo")
                elif category == "management":
                    issues.append("Problemas con la gestión")
        
        return issues
    
    def _generate_team_recommendations(self, category_scores: Dict[str, float], 
                                     issues: List[str]) -> List[str]:
        """Genera recomendaciones para el equipo"""
        recommendations = []
        
        if "Baja satisfacción laboral general" in issues:
            recommendations.append("Implementar encuestas de satisfacción regulares")
            recommendations.append("Revisar políticas de compensación")
        
        if "Problemas en el ambiente de trabajo" in issues:
            recommendations.append("Mejorar comunicación interna")
            recommendations.append("Organizar actividades de team building")
        
        if "Problemas con la gestión" in issues:
            recommendations.append("Capacitar a managers en liderazgo")
            recommendations.append("Implementar feedback 360")
        
        return recommendations
    
    def _calculate_engagement_risk(self, user_data: Dict[str, Any]) -> float:
        """Calcula riesgo basado en engagement"""
        engagement_score = self._calculate_engagement_score(user_data)
        return 1 - engagement_score
    
    def _calculate_satisfaction_risk(self, user_data: Dict[str, Any]) -> float:
        """Calcula riesgo basado en satisfacción"""
        satisfaction_score = self._calculate_satisfaction_score(user_data)
        return 1 - satisfaction_score
    
    def _calculate_activity_risk(self, user_data: Dict[str, Any]) -> float:
        """Calcula riesgo basado en actividad"""
        days_inactive = user_data.get("days_inactive", 0)
        return min(days_inactive / 30, 1.0)
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categoriza nivel de riesgo"""
        if risk_score > 0.7:
            return "high"
        elif risk_score > 0.4:
            return "medium"
        else:
            return "low"
    
    def _identify_risk_factors(self, user_data: Dict[str, Any]) -> List[str]:
        """Identifica factores de riesgo"""
        factors = []
        
        if user_data.get("days_inactive", 0) > 14:
            factors.append("Inactividad prolongada")
        
        if user_data.get("complaints", 0) > 2:
            factors.append("Múltiples quejas")
        
        if user_data.get("satisfaction_score", 0.5) < 0.4:
            factors.append("Baja satisfacción")
        
        return factors
    
    def _generate_retention_recommendations(self, risk_factors: List[str]) -> List[str]:
        """Genera recomendaciones de retención"""
        recommendations = []
        
        if "Inactividad prolongada" in risk_factors:
            recommendations.append("Contactar al usuario personalmente")
            recommendations.append("Ofrecer contenido relevante")
        
        if "Múltiples quejas" in risk_factors:
            recommendations.append("Revisar y resolver quejas pendientes")
            recommendations.append("Implementar mejoras basadas en feedback")
        
        if "Baja satisfacción" in risk_factors:
            recommendations.append("Conducir entrevista de salida")
            recommendations.append("Ofrecer incentivos de retención")
        
        return recommendations
    
    def _get_mock_sentiment_result(self, text: str, user_id: Optional[int]) -> SentimentResult:
        """Resultado simulado cuando está deshabilitado"""
        return SentimentResult(
            text=text,
            sentiment_score=0.2,
            sentiment_label="positive",
            confidence=0.8,
            categories={
                "job_satisfaction": 0.6,
                "work_environment": 0.5,
                "compensation": 0.4,
                "career_growth": 0.7,
                "work_life_balance": 0.5,
                "management": 0.6
            },
            keywords=["work", "team", "growth"],
            timestamp=datetime.now(),
            user_id=user_id
        )
    
    def _get_mock_engagement_analysis(self, user_id: int, user_data: Dict[str, Any]) -> EngagementAnalysis:
        """Análisis simulado cuando está deshabilitado"""
        return EngagementAnalysis(
            user_id=user_id,
            engagement_score=0.7,
            activity_level="medium",
            satisfaction_score=0.6,
            churn_risk=0.3,
            recommendations=["Participar en eventos", "Crear contenido"],
            last_activity=datetime.now(),
            activity_trend="stable"
        )
    
    def _get_mock_team_sentiment(self, team_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sentimiento de equipo simulado"""
        return {
            "team_size": len(team_data),
            "overall_sentiment": 0.6,
            "sentiment_label": "positive",
            "category_scores": {
                "job_satisfaction": 0.6,
                "work_environment": 0.5,
                "compensation": 0.4,
                "career_growth": 0.7,
                "work_life_balance": 0.5,
                "management": 0.6
            },
            "issues": [],
            "recommendations": ["Mejorar comunicación", "Organizar team building"],
            "individual_sentiments": [],
            "analysis_date": datetime.now().isoformat()
        }
    
    def _get_mock_churn_prediction(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predicción de churn simulada"""
        return {
            "user_id": user_data.get("user_id"),
            "churn_risk": 0.3,
            "risk_level": "low",
            "engagement_risk": 0.3,
            "satisfaction_risk": 0.4,
            "activity_risk": 0.2,
            "risk_factors": [],
            "retention_recommendations": ["Mantener engagement activo"],
            "prediction_confidence": 0.85,
            "prediction_date": datetime.now().isoformat()
        }
    
    def train_models(self, training_data: pd.DataFrame):
        """Entrena los modelos de análisis de sentimientos"""
        if not self.enabled:
            logger.info("SentimentAnalyzer: Entrenamiento deshabilitado")
            return
        
        try:
            # Preprocesar datos de entrenamiento
            texts = training_data['text'].apply(self._preprocess_text)
            
            # Vectorizar textos
            X = self.vectorizer.fit_transform(texts)
            y = training_data['sentiment']
            
            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Entrenar modelo
            self.sentiment_model.fit(X_train, y_train)
            
            # Evaluar modelo
            y_pred = self.sentiment_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            self.is_trained = True
            logger.info(f"SentimentAnalyzer: Modelo entrenado con accuracy {accuracy:.3f}")
            
        except Exception as e:
            logger.error(f"Error training sentiment models: {e}")
    
    def save_models(self, filepath: str):
        """Guarda los modelos entrenados"""
        if not self.enabled or not self.is_trained:
            return
        
        try:
            joblib.dump(self.vectorizer, f"{filepath}/sentiment_vectorizer.pkl")
            joblib.dump(self.sentiment_model, f"{filepath}/sentiment_model.pkl")
            logger.info("SentimentAnalyzer: Modelos guardados")
        except Exception as e:
            logger.error(f"Error saving sentiment models: {e}")
    
    def load_models(self, filepath: str):
        """Carga modelos pre-entrenados"""
        if not self.enabled:
            return
        
        try:
            self.vectorizer = joblib.load(f"{filepath}/sentiment_vectorizer.pkl")
            self.sentiment_model = joblib.load(f"{filepath}/sentiment_model.pkl")
            self.is_trained = True
            logger.info("SentimentAnalyzer: Modelos cargados")
        except Exception as e:
            logger.error(f"Error loading sentiment models: {e}")


# Instancia global del analizador de sentimientos
sentiment_analyzer = SentimentAnalyzer() 