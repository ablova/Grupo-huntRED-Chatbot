"""
🎭 Analizador de Sentimientos y Engagement en Tiempo Real

Este módulo proporciona análisis avanzado de sentimientos y engagement
para optimizar las comunicaciones y mejorar la experiencia del usuario.

Características:
- Análisis de sentimientos en múltiples idiomas
- Detección de engagement y satisfacción
- Recomendaciones de comunicación personalizada
- Integración con el sistema de notificaciones
- Análisis de tendencias temporales
"""

import logging
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Analizador de sentimientos avanzado con capacidades de engagement.
    """
    
    def __init__(self):
        self.sentiment_lexicons = self._load_sentiment_lexicons()
        self.engagement_patterns = self._load_engagement_patterns()
        self.language_detector = self._init_language_detector()
        self.cache_ttl = 3600  # 1 hora
        
    def _load_sentiment_lexicons(self) -> Dict[str, Dict[str, float]]:
        """Carga los lexicones de sentimientos para diferentes idiomas."""
        return {
            'es': {
                'positive': {
                    'excelente': 0.9, 'fantástico': 0.9, 'maravilloso': 0.8,
                    'genial': 0.8, 'perfecto': 0.9, 'increíble': 0.8,
                    'bueno': 0.6, 'bien': 0.5, 'agradable': 0.6,
                    'satisfecho': 0.7, 'contento': 0.7, 'feliz': 0.8,
                    'gracias': 0.6, 'aprecio': 0.7, 'me gusta': 0.6
                },
                'negative': {
                    'terrible': -0.9, 'horrible': -0.9, 'pésimo': -0.8,
                    'malo': -0.6, 'mal': -0.5, 'desagradable': -0.6,
                    'insatisfecho': -0.7, 'molesto': -0.6, 'enojado': -0.7,
                    'frustrado': -0.6, 'decepcionado': -0.7, 'no me gusta': -0.6,
                    'problema': -0.4, 'error': -0.5, 'falla': -0.5
                },
                'intensifiers': {
                    'muy': 1.5, 'extremadamente': 2.0, 'increíblemente': 1.8,
                    'totalmente': 1.3, 'completamente': 1.3, 'absolutamente': 1.5,
                    'realmente': 1.2, 'verdaderamente': 1.2, 'genuinamente': 1.1
                },
                'negators': {
                    'no': -1.0, 'nunca': -1.0, 'jamás': -1.0,
                    'tampoco': -0.8, 'ni': -0.8, 'sin': -0.6
                }
            },
            'en': {
                'positive': {
                    'excellent': 0.9, 'fantastic': 0.9, 'wonderful': 0.8,
                    'great': 0.8, 'perfect': 0.9, 'amazing': 0.8,
                    'good': 0.6, 'nice': 0.5, 'pleasant': 0.6,
                    'satisfied': 0.7, 'happy': 0.8, 'pleased': 0.7,
                    'thank you': 0.6, 'appreciate': 0.7, 'like': 0.6
                },
                'negative': {
                    'terrible': -0.9, 'horrible': -0.9, 'awful': -0.8,
                    'bad': -0.6, 'poor': -0.5, 'unpleasant': -0.6,
                    'dissatisfied': -0.7, 'annoyed': -0.6, 'angry': -0.7,
                    'frustrated': -0.6, 'disappointed': -0.7, 'dislike': -0.6,
                    'problem': -0.4, 'error': -0.5, 'issue': -0.5
                },
                'intensifiers': {
                    'very': 1.5, 'extremely': 2.0, 'incredibly': 1.8,
                    'totally': 1.3, 'completely': 1.3, 'absolutely': 1.5,
                    'really': 1.2, 'truly': 1.2, 'genuinely': 1.1
                },
                'negators': {
                    'not': -1.0, 'never': -1.0, 'no': -1.0,
                    'neither': -0.8, 'nor': -0.8, 'without': -0.6
                }
            }
        }
    
    def _load_engagement_patterns(self) -> Dict[str, List[str]]:
        """Carga patrones de engagement y satisfacción."""
        return {
            'high_engagement': [
                r'\b(?:gracias|thank you)\b',
                r'\b(?:excelente|excellent)\b',
                r'\b(?:me gusta|like)\b',
                r'\b(?:perfecto|perfect)\b',
                r'\b(?:increíble|amazing)\b',
                r'\b(?:fantástico|fantastic)\b',
                r'\b(?:satisfecho|satisfied)\b',
                r'\b(?:contento|happy)\b'
            ],
            'low_engagement': [
                r'\b(?:no me gusta|dislike)\b',
                r'\b(?:insatisfecho|dissatisfied)\b',
                r'\b(?:molesto|annoyed)\b',
                r'\b(?:frustrado|frustrated)\b',
                r'\b(?:decepcionado|disappointed)\b',
                r'\b(?:terrible|awful)\b',
                r'\b(?:horrible|horrible)\b',
                r'\b(?:pésimo|poor)\b'
            ],
            'questions': [
                r'\?$',
                r'\b(?:qué|cómo|cuándo|dónde|quién|por qué)\b',
                r'\b(?:what|how|when|where|who|why)\b'
            ],
            'urgency': [
                r'\b(?:urgente|urgent)\b',
                r'\b(?:inmediato|immediate)\b',
                r'\b(?:rápido|quick|fast)\b',
                r'\b(?:ahora|now)\b',
                r'\b(?:pronto|soon)\b'
            ]
        }
    
    def _init_language_detector(self):
        """Inicializa el detector de idioma."""
        # Detector simple basado en palabras comunes
        language_indicators = {
            'es': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'como', 'más', 'pero', 'sus', 'me', 'hasta', 'hay', 'donde', 'han', 'quien', 'están', 'estado', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'qué', 'unos', 'yo', 'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada', 'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo', 'nosotros'],
            'en': ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us']
        }
        return language_indicators
    
    def detect_language(self, text: str) -> str:
        """Detecta el idioma del texto."""
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        scores = {}
        for lang, indicators in self.language_detector.items():
            score = sum(1 for word in words if word in indicators)
            scores[lang] = score / len(words) if words else 0
        
        return max(scores, key=scores.get) if scores else 'es'
    
    def analyze_sentiment(self, text: str, language: str = None) -> Dict[str, Any]:
        """
        Analiza el sentimiento del texto.
        
        Args:
            text: Texto a analizar
            language: Idioma del texto (opcional, se detecta automáticamente)
        
        Returns:
            Diccionario con el análisis de sentimiento
        """
        if not text or not text.strip():
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'language': 'unknown',
                'details': {}
            }
        
        # Detectar idioma si no se especifica
        if not language:
            language = self.detect_language(text)
        
        # Verificar caché
        cache_key = f"sentiment_{hash(text)}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Obtener lexicón para el idioma
        lexicon = self.sentiment_lexicons.get(language, self.sentiment_lexicons['es'])
        
        # Preprocesar texto
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        # Calcular puntuación de sentimiento
        sentiment_score = 0.0
        word_scores = []
        negator_count = 0
        intensifier_count = 0
        
        for i, word in enumerate(words):
            word_score = 0.0
            
            # Verificar palabras positivas
            if word in lexicon['positive']:
                word_score = lexicon['positive'][word]
            # Verificar palabras negativas
            elif word in lexicon['negative']:
                word_score = lexicon['negative'][word]
            # Verificar intensificadores
            elif word in lexicon['intensifiers']:
                intensifier_count += 1
                continue
            # Verificar negadores
            elif word in lexicon['negators']:
                negator_count += 1
                continue
            
            # Aplicar negadores
            if negator_count > 0:
                word_score *= -1
                negator_count -= 1
            
            # Aplicar intensificadores
            if intensifier_count > 0 and word_score != 0:
                word_score *= lexicon['intensifiers'].get(words[i-1], 1.0)
                intensifier_count -= 1
            
            sentiment_score += word_score
            if word_score != 0:
                word_scores.append((word, word_score))
        
        # Normalizar puntuación
        if words:
            sentiment_score = sentiment_score / len(words)
        
        # Determinar etiqueta de sentimiento
        if sentiment_score > 0.1:
            sentiment_label = 'positive'
        elif sentiment_score < -0.1:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        # Calcular confianza
        confidence = min(abs(sentiment_score) * 2, 1.0)
        
        result = {
            'sentiment_score': round(sentiment_score, 3),
            'sentiment_label': sentiment_label,
            'confidence': round(confidence, 3),
            'language': language,
            'details': {
                'word_count': len(words),
                'significant_words': word_scores,
                'negator_count': negator_count,
                'intensifier_count': intensifier_count
            }
        }
        
        # Guardar en caché
        cache.set(cache_key, result, self.cache_ttl)
        
        return result
    
    def analyze_engagement(self, text: str) -> Dict[str, Any]:
        """
        Analiza el nivel de engagement del texto.
        
        Args:
            text: Texto a analizar
        
        Returns:
            Diccionario con el análisis de engagement
        """
        if not text or not text.strip():
            return {
                'engagement_score': 0.0,
                'engagement_level': 'low',
                'patterns_detected': [],
                'urgency_level': 'normal'
            }
        
        text_lower = text.lower()
        patterns_detected = []
        engagement_score = 0.0
        
        # Detectar patrones de engagement
        for pattern_type, patterns in self.engagement_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    patterns_detected.append(pattern_type)
                    if pattern_type == 'high_engagement':
                        engagement_score += 0.3
                    elif pattern_type == 'low_engagement':
                        engagement_score -= 0.3
                    elif pattern_type == 'questions':
                        engagement_score += 0.2
                    elif pattern_type == 'urgency':
                        engagement_score += 0.4
        
        # Normalizar puntuación
        engagement_score = max(-1.0, min(1.0, engagement_score))
        
        # Determinar nivel de engagement
        if engagement_score > 0.3:
            engagement_level = 'high'
        elif engagement_score < -0.3:
            engagement_level = 'low'
        else:
            engagement_level = 'medium'
        
        # Determinar nivel de urgencia
        urgency_patterns = [p for p in patterns_detected if p == 'urgency']
        urgency_level = 'high' if urgency_patterns else 'normal'
        
        return {
            'engagement_score': round(engagement_score, 3),
            'engagement_level': engagement_level,
            'patterns_detected': list(set(patterns_detected)),
            'urgency_level': urgency_level
        }
    
    def analyze_communication_effectiveness(self, text: str, context: str = None) -> Dict[str, Any]:
        """
        Analiza la efectividad de la comunicación.
        
        Args:
            text: Texto a analizar
            context: Contexto de la comunicación (opcional)
        
        Returns:
            Diccionario con recomendaciones de comunicación
        """
        sentiment_analysis = self.analyze_sentiment(text)
        engagement_analysis = self.analyze_engagement(text)
        
        # Generar recomendaciones
        recommendations = []
        
        if sentiment_analysis['sentiment_label'] == 'negative':
            recommendations.append({
                'type': 'sentiment_improvement',
                'priority': 'high',
                'suggestion': 'Considera usar un tono más positivo y empático',
                'examples': ['Gracias por tu paciencia', 'Entiendo tu situación', 'Estamos aquí para ayudarte']
            })
        
        if engagement_analysis['engagement_level'] == 'low':
            recommendations.append({
                'type': 'engagement_boost',
                'priority': 'medium',
                'suggestion': 'Incluye elementos que generen más engagement',
                'examples': ['¿Te gustaría saber más sobre...?', '¿Qué opinas de...?', '¿Cómo podemos ayudarte mejor?']
            })
        
        if engagement_analysis['urgency_level'] == 'high':
            recommendations.append({
                'type': 'urgency_response',
                'priority': 'high',
                'suggestion': 'Responde con urgencia y proporciona soluciones inmediatas',
                'examples': ['Entiendo la urgencia', 'Te ayudo inmediatamente', 'Vamos a resolverlo ahora']
            })
        
        # Análisis de longitud
        word_count = len(text.split())
        if word_count < 10:
            recommendations.append({
                'type': 'content_length',
                'priority': 'low',
                'suggestion': 'Considera agregar más detalles para mayor claridad'
            })
        elif word_count > 100:
            recommendations.append({
                'type': 'content_length',
                'priority': 'medium',
                'suggestion': 'Considera dividir el mensaje en partes más pequeñas'
            })
        
        return {
            'sentiment': sentiment_analysis,
            'engagement': engagement_analysis,
            'recommendations': recommendations,
            'overall_score': round((sentiment_analysis['sentiment_score'] + engagement_analysis['engagement_score']) / 2, 3)
        }
    
    def get_communication_tips(self, sentiment_label: str, engagement_level: str) -> List[str]:
        """
        Obtiene consejos de comunicación basados en el análisis.
        
        Args:
            sentiment_label: Etiqueta de sentimiento
            engagement_level: Nivel de engagement
        
        Returns:
            Lista de consejos de comunicación
        """
        tips = []
        
        if sentiment_label == 'negative':
            tips.extend([
                "Usa un tono empático y comprensivo",
                "Reconoce la frustración del usuario",
                "Ofrece soluciones concretas",
                "Mantén un lenguaje positivo",
                "Demuestra que entiendes la situación"
            ])
        
        if engagement_level == 'low':
            tips.extend([
                "Haz preguntas abiertas",
                "Incluye elementos interactivos",
                "Personaliza la respuesta",
                "Usa ejemplos relevantes",
                "Invita a la participación"
            ])
        
        if sentiment_label == 'positive' and engagement_level == 'high':
            tips.extend([
                "Mantén el momentum positivo",
                "Reconoce el entusiasmo",
                "Ofrece oportunidades adicionales",
                "Celebra los logros",
                "Fomenta la continuidad"
            ])
        
        return tips

class EngagementTracker:
    """
    Rastreador de engagement para análisis temporal.
    """
    
    def __init__(self):
        self.engagement_history = defaultdict(list)
        self.sentiment_trends = defaultdict(list)
    
    def track_interaction(self, user_id: str, interaction_data: Dict[str, Any]):
        """
        Registra una interacción para análisis temporal.
        
        Args:
            user_id: ID del usuario
            interaction_data: Datos de la interacción
        """
        timestamp = timezone.now()
        
        # Registrar engagement
        self.engagement_history[user_id].append({
            'timestamp': timestamp,
            'engagement_score': interaction_data.get('engagement_score', 0),
            'interaction_type': interaction_data.get('type', 'unknown')
        })
        
        # Registrar sentimiento
        self.sentiment_trends[user_id].append({
            'timestamp': timestamp,
            'sentiment_score': interaction_data.get('sentiment_score', 0),
            'sentiment_label': interaction_data.get('sentiment_label', 'neutral')
        })
        
        # Limpiar datos antiguos (más de 30 días)
        cutoff_date = timestamp - timedelta(days=30)
        self.engagement_history[user_id] = [
            entry for entry in self.engagement_history[user_id]
            if entry['timestamp'] > cutoff_date
        ]
        self.sentiment_trends[user_id] = [
            entry for entry in self.sentiment_trends[user_id]
            if entry['timestamp'] > cutoff_date
        ]
    
    def get_user_engagement_trend(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Obtiene la tendencia de engagement de un usuario.
        
        Args:
            user_id: ID del usuario
            days: Número de días a analizar
        
        Returns:
            Diccionario con la tendencia de engagement
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        recent_engagement = [
            entry for entry in self.engagement_history[user_id]
            if entry['timestamp'] > cutoff_date
        ]
        
        if not recent_engagement:
            return {
                'trend': 'stable',
                'average_score': 0.0,
                'interaction_count': 0,
                'trend_direction': 'neutral'
            }
        
        scores = [entry['engagement_score'] for entry in recent_engagement]
        average_score = np.mean(scores)
        
        # Calcular tendencia
        if len(scores) >= 2:
            trend_slope = np.polyfit(range(len(scores)), scores, 1)[0]
            if trend_slope > 0.01:
                trend_direction = 'increasing'
            elif trend_slope < -0.01:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'stable'
        
        return {
            'trend': 'increasing' if average_score > 0.3 else 'decreasing' if average_score < -0.3 else 'stable',
            'average_score': round(average_score, 3),
            'interaction_count': len(recent_engagement),
            'trend_direction': trend_direction,
            'recent_interactions': recent_engagement[-5:]  # Últimas 5 interacciones
        }
    
    def get_sentiment_insights(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Obtiene insights de sentimiento de un usuario.
        
        Args:
            user_id: ID del usuario
            days: Número de días a analizar
        
        Returns:
            Diccionario con insights de sentimiento
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        recent_sentiments = [
            entry for entry in self.sentiment_trends[user_id]
            if entry['timestamp'] > cutoff_date
        ]
        
        if not recent_sentiments:
            return {
                'overall_sentiment': 'neutral',
                'sentiment_distribution': {},
                'sentiment_stability': 'stable',
                'recommendations': []
            }
        
        # Distribución de sentimientos
        sentiment_counts = defaultdict(int)
        for entry in recent_sentiments:
            sentiment_counts[entry['sentiment_label']] += 1
        
        # Sentimiento predominante
        overall_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        
        # Estabilidad del sentimiento
        sentiment_changes = 0
        for i in range(1, len(recent_sentiments)):
            if recent_sentiments[i]['sentiment_label'] != recent_sentiments[i-1]['sentiment_label']:
                sentiment_changes += 1
        
        stability_ratio = sentiment_changes / len(recent_sentiments) if recent_sentiments else 0
        sentiment_stability = 'stable' if stability_ratio < 0.3 else 'volatile'
        
        # Recomendaciones
        recommendations = []
        if overall_sentiment == 'negative':
            recommendations.append("El usuario muestra sentimientos negativos. Considera un enfoque más empático.")
        if sentiment_stability == 'volatile':
            recommendations.append("El sentimiento del usuario es volátil. Mantén consistencia en la comunicación.")
        
        return {
            'overall_sentiment': overall_sentiment,
            'sentiment_distribution': dict(sentiment_counts),
            'sentiment_stability': sentiment_stability,
            'recommendations': recommendations,
            'recent_sentiments': recent_sentiments[-5:]  # Últimos 5 sentimientos
        }

# Instancia global del analizador
sentiment_analyzer = SentimentAnalyzer()
engagement_tracker = EngagementTracker()

def analyze_user_communication(text: str, user_id: str = None, context: str = None) -> Dict[str, Any]:
    """
    Función de conveniencia para analizar comunicación de usuario.
    
    Args:
        text: Texto a analizar
        user_id: ID del usuario (opcional)
        context: Contexto de la comunicación (opcional)
    
    Returns:
        Diccionario con análisis completo
    """
    # Análisis de efectividad
    effectiveness = sentiment_analyzer.analyze_communication_effectiveness(text, context)
    
    # Si hay user_id, registrar para tracking
    if user_id:
        engagement_tracker.track_interaction(user_id, {
            'sentiment_score': effectiveness['sentiment']['sentiment_score'],
            'sentiment_label': effectiveness['sentiment']['sentiment_label'],
            'engagement_score': effectiveness['engagement']['engagement_score'],
            'type': context or 'general'
        })
    
    # Agregar tips de comunicación
    effectiveness['communication_tips'] = sentiment_analyzer.get_communication_tips(
        effectiveness['sentiment']['sentiment_label'],
        effectiveness['engagement']['engagement_level']
    )
    
    return effectiveness 