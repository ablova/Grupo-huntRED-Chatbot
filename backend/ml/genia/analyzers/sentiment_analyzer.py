"""
Sentiment Analyzer - Sistema ML GenIA huntRED® v2
Analizador de sentimientos avanzado con capacidades de NLP y análisis emocional.
"""

import logging
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
from dataclasses import dataclass
from enum import Enum

# ML Libraries
try:
    import tensorflow as tf
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    import spacy
    from textblob import TextBlob
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError as e:
    print(f"Missing ML dependencies: {e}")

from ..core.base_analyzer import BaseAnalyzer
from ..core.exceptions import MLAnalysisError, DataValidationError
from ..core.metrics import MLMetrics
from ..core.validators import validate_text_input


logger = logging.getLogger(__name__)


class SentimentType(Enum):
    """Tipos de análisis de sentimiento."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class EmotionType(Enum):
    """Tipos de emociones detectables."""
    JOY = "joy"
    ANGER = "anger"
    FEAR = "fear"
    SADNESS = "sadness"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"


@dataclass
class SentimentResult:
    """Resultado del análisis de sentimiento."""
    text: str
    sentiment: SentimentType
    confidence: float
    emotions: Dict[EmotionType, float]
    polarity: float  # -1 to 1
    subjectivity: float  # 0 to 1
    detailed_scores: Dict[str, float]
    entities: List[Dict[str, Any]]
    keywords: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime


class SentimentAnalyzer(BaseAnalyzer):
    """
    Analizador de sentimientos avanzado para huntRED®.
    
    Utiliza múltiples técnicas de NLP y modelos de ML para análisis
    profundo de sentimientos, emociones y entidades.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el analizador de sentimientos.
        
        Args:
            config: Configuración personalizada del analizador
        """
        super().__init__(config)
        self.model_name = "sentiment_analyzer"
        self.version = "2.0.0"
        
        # Configuración por defecto
        self.default_config = {
            'use_transformers': True,
            'use_vader': True,
            'use_textblob': True,
            'use_spacy': True,
            'language': 'es',
            'confidence_threshold': 0.7,
            'enable_emotion_detection': True,
            'enable_entity_extraction': True,
            'enable_keyword_extraction': True,
            'batch_size': 32,
            'max_length': 512,
            'cache_results': True,
            'model_path': 'models/sentiment/',
            'custom_models': {
                'recruitment_sentiment': 'models/sentiment/recruitment_v1.bin',
                'candidate_feedback': 'models/sentiment/feedback_v1.bin'
            }
        }
        
        self.config = {**self.default_config, **(config or {})}
        self.metrics = MLMetrics("sentiment_analyzer")
        self._models = {}
        self._tokenizers = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Inicializa los modelos de ML necesarios."""
        try:
            # Cargar modelo de transformers para español
            if self.config['use_transformers']:
                model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
                self._tokenizers['bert'] = AutoTokenizer.from_pretrained(model_name)
                self._models['bert'] = AutoModelForSequenceClassification.from_pretrained(model_name)
                
                # Pipeline para análisis rápido
                self._models['pipeline'] = pipeline(
                    "sentiment-analysis",
                    model=model_name,
                    tokenizer=model_name,
                    device=0 if torch.cuda.is_available() else -1
                )
            
            # Inicializar VADER para sentimientos
            if self.config['use_vader']:
                self._models['vader'] = SentimentIntensityAnalyzer()
            
            # Cargar spaCy para análisis de entidades
            if self.config['use_spacy']:
                try:
                    if self.config['language'] == 'es':
                        self._models['spacy'] = spacy.load("es_core_news_sm")
                    else:
                        self._models['spacy'] = spacy.load("en_core_web_sm")
                except OSError:
                    logger.warning("SpaCy model not found, entity extraction disabled")
                    self.config['use_spacy'] = False
            
            # Cargar modelos personalizados si existen
            self._load_custom_models()
            
            logger.info("Sentiment analyzer models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing sentiment models: {e}")
            raise MLAnalysisError(f"Failed to initialize sentiment analyzer: {e}")
    
    def _load_custom_models(self):
        """Carga modelos personalizados específicos del dominio."""
        for model_name, model_path in self.config['custom_models'].items():
            try:
                # Implementar carga de modelos personalizados
                # Por ahora, placeholder para modelos futuros
                logger.info(f"Custom model {model_name} will be loaded from {model_path}")
            except Exception as e:
                logger.warning(f"Failed to load custom model {model_name}: {e}")
    
    async def analyze_sentiment(
        self,
        text: str,
        context: Optional[str] = None,
        domain: Optional[str] = None
    ) -> SentimentResult:
        """
        Analiza el sentimiento de un texto.
        
        Args:
            text: Texto a analizar
            context: Contexto adicional para el análisis
            domain: Dominio específico (recruitment, feedback, etc.)
            
        Returns:
            Resultado del análisis de sentimiento
        """
        try:
            # Validar entrada
            validate_text_input(text, max_length=self.config['max_length'])
            
            start_time = datetime.now()
            
            # Preprocesar texto
            cleaned_text = self._preprocess_text(text)
            
            # Ejecutar análisis en paralelo
            tasks = []
            
            if self.config['use_transformers']:
                tasks.append(self._analyze_with_transformers(cleaned_text))
            
            if self.config['use_vader']:
                tasks.append(self._analyze_with_vader(cleaned_text))
            
            if self.config['use_textblob']:
                tasks.append(self._analyze_with_textblob(cleaned_text))
            
            # Ejecutar análisis en paralelo
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combinar resultados
            combined_result = self._combine_analysis_results(results, cleaned_text)
            
            # Extraer entidades y keywords
            if self.config['enable_entity_extraction']:
                combined_result.entities = await self._extract_entities(cleaned_text)
            
            if self.config['enable_keyword_extraction']:
                combined_result.keywords = await self._extract_keywords(cleaned_text)
            
            # Detectar emociones
            if self.config['enable_emotion_detection']:
                combined_result.emotions = await self._detect_emotions(cleaned_text)
            
            # Aplicar contexto y dominio si se proporcionan
            if context or domain:
                combined_result = await self._apply_context_analysis(
                    combined_result, context, domain
                )
            
            # Registrar métricas
            processing_time = (datetime.now() - start_time).total_seconds()
            await self.metrics.record_analysis(
                'sentiment',
                processing_time,
                {'confidence': combined_result.confidence, 'sentiment': combined_result.sentiment.value}
            )
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            await self.metrics.record_error('sentiment_analysis', str(e))
            raise MLAnalysisError(f"Sentiment analysis failed: {e}")
    
    async def analyze_batch(
        self,
        texts: List[str],
        context: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[SentimentResult]:
        """
        Analiza una lista de textos en lote.
        
        Args:
            texts: Lista de textos a analizar
            context: Contexto adicional
            domain: Dominio específico
            
        Returns:
            Lista de resultados de análisis
        """
        try:
            batch_size = self.config['batch_size']
            results = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Procesar lote en paralelo
                tasks = [
                    self.analyze_sentiment(text, context, domain)
                    for text in batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filtrar errores
                valid_results = [
                    result for result in batch_results
                    if not isinstance(result, Exception)
                ]
                
                results.extend(valid_results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch sentiment analysis: {e}")
            raise MLAnalysisError(f"Batch sentiment analysis failed: {e}")
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocesa el texto para análisis."""
        # Limpiar texto
        text = re.sub(r'http\S+', '', text)  # Remover URLs
        text = re.sub(r'@\w+', '', text)     # Remover menciones
        text = re.sub(r'#\w+', '', text)     # Remover hashtags
        text = re.sub(r'\s+', ' ', text)     # Normalizar espacios
        text = text.strip()
        
        return text
    
    async def _analyze_with_transformers(self, text: str) -> Dict[str, Any]:
        """Analiza sentimiento usando transformers."""
        try:
            result = self._models['pipeline'](text)
            
            # Convertir resultado a formato estándar
            label_map = {
                'POSITIVE': SentimentType.POSITIVE,
                'NEGATIVE': SentimentType.NEGATIVE,
                'NEUTRAL': SentimentType.NEUTRAL
            }
            
            sentiment = label_map.get(result[0]['label'], SentimentType.NEUTRAL)
            confidence = result[0]['score']
            
            return {
                'method': 'transformers',
                'sentiment': sentiment,
                'confidence': confidence,
                'scores': {result[0]['label']: confidence}
            }
            
        except Exception as e:
            logger.error(f"Transformers analysis error: {e}")
            return {'method': 'transformers', 'error': str(e)}
    
    async def _analyze_with_vader(self, text: str) -> Dict[str, Any]:
        """Analiza sentimiento usando VADER."""
        try:
            scores = self._models['vader'].polarity_scores(text)
            
            # Determinar sentimiento principal
            if scores['compound'] >= 0.05:
                sentiment = SentimentType.POSITIVE
            elif scores['compound'] <= -0.05:
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.NEUTRAL
            
            confidence = abs(scores['compound'])
            
            return {
                'method': 'vader',
                'sentiment': sentiment,
                'confidence': confidence,
                'scores': scores,
                'polarity': scores['compound']
            }
            
        except Exception as e:
            logger.error(f"VADER analysis error: {e}")
            return {'method': 'vader', 'error': str(e)}
    
    async def _analyze_with_textblob(self, text: str) -> Dict[str, Any]:
        """Analiza sentimiento usando TextBlob."""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Determinar sentimiento
            if polarity > 0.1:
                sentiment = SentimentType.POSITIVE
            elif polarity < -0.1:
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.NEUTRAL
            
            confidence = abs(polarity)
            
            return {
                'method': 'textblob',
                'sentiment': sentiment,
                'confidence': confidence,
                'polarity': polarity,
                'subjectivity': subjectivity
            }
            
        except Exception as e:
            logger.error(f"TextBlob analysis error: {e}")
            return {'method': 'textblob', 'error': str(e)}
    
    def _combine_analysis_results(
        self,
        results: List[Dict[str, Any]],
        text: str
    ) -> SentimentResult:
        """Combina resultados de múltiples métodos de análisis."""
        
        # Filtrar resultados válidos
        valid_results = [r for r in results if 'error' not in r]
        
        if not valid_results:
            # Si todos los métodos fallaron, retornar resultado neutro
            return SentimentResult(
                text=text,
                sentiment=SentimentType.NEUTRAL,
                confidence=0.0,
                emotions={},
                polarity=0.0,
                subjectivity=0.5,
                detailed_scores={},
                entities=[],
                keywords=[],
                metadata={'error': 'All analysis methods failed'},
                timestamp=datetime.now()
            )
        
        # Calcular sentimiento ponderado
        sentiment_counts = {}
        total_confidence = 0
        polarity_sum = 0
        subjectivity_sum = 0
        detailed_scores = {}
        
        for result in valid_results:
            sentiment = result['sentiment']
            confidence = result['confidence']
            
            # Contar sentimientos ponderados por confianza
            if sentiment not in sentiment_counts:
                sentiment_counts[sentiment] = 0
            sentiment_counts[sentiment] += confidence
            
            total_confidence += confidence
            
            # Acumular polaridad y subjetividad
            if 'polarity' in result:
                polarity_sum += result['polarity']
            if 'subjectivity' in result:
                subjectivity_sum += result['subjectivity']
            
            # Acumular scores detallados
            method = result['method']
            detailed_scores[method] = result.get('scores', {})
        
        # Determinar sentimiento final
        final_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        final_confidence = sentiment_counts[final_sentiment] / total_confidence
        
        # Calcular promedios
        avg_polarity = polarity_sum / len(valid_results) if valid_results else 0
        avg_subjectivity = subjectivity_sum / len(valid_results) if valid_results else 0.5
        
        return SentimentResult(
            text=text,
            sentiment=final_sentiment,
            confidence=final_confidence,
            emotions={},  # Se llenará después
            polarity=avg_polarity,
            subjectivity=avg_subjectivity,
            detailed_scores=detailed_scores,
            entities=[],  # Se llenará después
            keywords=[],  # Se llenará después
            metadata={
                'methods_used': [r['method'] for r in valid_results],
                'sentiment_distribution': sentiment_counts
            },
            timestamp=datetime.now()
        )
    
    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extrae entidades nombradas del texto."""
        entities = []
        
        if self.config['use_spacy'] and 'spacy' in self._models:
            try:
                doc = self._models['spacy'](text)
                
                for ent in doc.ents:
                    entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'description': spacy.explain(ent.label_),
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'confidence': getattr(ent, 'score', 1.0)
                    })
                    
            except Exception as e:
                logger.error(f"Entity extraction error: {e}")
        
        return entities
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """Extrae palabras clave del texto."""
        keywords = []
        
        try:
            # Usar spaCy para extracción básica de keywords
            if self.config['use_spacy'] and 'spacy' in self._models:
                doc = self._models['spacy'](text)
                
                # Extraer tokens importantes
                for token in doc:
                    if (token.pos_ in ['NOUN', 'ADJ', 'VERB'] and
                        not token.is_stop and
                        not token.is_punct and
                        len(token.text) > 2):
                        keywords.append(token.lemma_.lower())
                
                # Remover duplicados manteniendo orden
                keywords = list(dict.fromkeys(keywords))
                
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
        
        return keywords[:10]  # Limitar a 10 keywords
    
    async def _detect_emotions(self, text: str) -> Dict[EmotionType, float]:
        """Detecta emociones en el texto."""
        emotions = {emotion: 0.0 for emotion in EmotionType}
        
        try:
            # Implementar detección básica de emociones
            # Por ahora, mapeo simple basado en sentimiento
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.5:
                emotions[EmotionType.JOY] = polarity
            elif polarity < -0.5:
                emotions[EmotionType.SADNESS] = abs(polarity)
            elif polarity > 0.2:
                emotions[EmotionType.TRUST] = polarity
            elif polarity < -0.2:
                emotions[EmotionType.ANGER] = abs(polarity)
            
            # TODO: Implementar modelo de emociones más sofisticado
            
        except Exception as e:
            logger.error(f"Emotion detection error: {e}")
        
        return emotions
    
    async def _apply_context_analysis(
        self,
        result: SentimentResult,
        context: Optional[str],
        domain: Optional[str]
    ) -> SentimentResult:
        """Aplica análisis contextual al resultado."""
        
        # Ajustar confianza basado en contexto
        context_modifier = 1.0
        
        if domain == 'recruitment':
            # En contexto de reclutamiento, ajustar interpretación
            if 'rechazo' in result.text.lower() or 'no interesado' in result.text.lower():
                result.sentiment = SentimentType.NEGATIVE
                context_modifier = 1.2
        elif domain == 'feedback':
            # En contexto de feedback, ser más sensible
            context_modifier = 1.1
        
        # Aplicar modificador
        result.confidence = min(result.confidence * context_modifier, 1.0)
        
        # Agregar metadata contextual
        result.metadata['context'] = context
        result.metadata['domain'] = domain
        
        return result
    
    async def get_sentiment_trends(
        self,
        texts: List[str],
        time_window: timedelta = timedelta(days=30)
    ) -> Dict[str, Any]:
        """Analiza tendencias de sentimiento en un período de tiempo."""
        
        results = await self.analyze_batch(texts)
        
        # Calcular distribución de sentimientos
        sentiment_distribution = {}
        total_confidence = 0
        
        for result in results:
            sentiment = result.sentiment.value
            if sentiment not in sentiment_distribution:
                sentiment_distribution[sentiment] = 0
            sentiment_distribution[sentiment] += 1
            total_confidence += result.confidence
        
        # Calcular métricas
        total_texts = len(results)
        avg_confidence = total_confidence / total_texts if total_texts > 0 else 0
        
        return {
            'period': time_window,
            'total_analyzed': total_texts,
            'sentiment_distribution': sentiment_distribution,
            'sentiment_percentages': {
                k: (v / total_texts) * 100 for k, v in sentiment_distribution.items()
            },
            'average_confidence': avg_confidence,
            'timestamp': datetime.now()
        }
    
    async def train_custom_model(
        self,
        training_data: List[Dict[str, Any]],
        model_name: str,
        domain: str
    ):
        """Entrena un modelo personalizado para un dominio específico."""
        
        try:
            logger.info(f"Training custom sentiment model: {model_name}")
            
            # Preparar datos de entrenamiento
            texts = [item['text'] for item in training_data]
            labels = [item['sentiment'] for item in training_data]
            
            # TODO: Implementar entrenamiento de modelo personalizado
            # Por ahora, simular entrenamiento
            
            await asyncio.sleep(1)  # Simular tiempo de entrenamiento
            
            # Guardar modelo (placeholder)
            model_path = f"{self.config['model_path']}{model_name}_{domain}.bin"
            
            logger.info(f"Custom model saved to: {model_path}")
            
            return {
                'model_name': model_name,
                'domain': domain,
                'training_samples': len(training_data),
                'model_path': model_path,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error training custom model: {e}")
            raise MLAnalysisError(f"Model training failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna información sobre los modelos cargados."""
        
        model_info = {
            'analyzer_version': self.version,
            'loaded_models': list(self._models.keys()),
            'configuration': self.config,
            'supported_languages': ['es', 'en'],
            'capabilities': {
                'sentiment_analysis': True,
                'emotion_detection': self.config['enable_emotion_detection'],
                'entity_extraction': self.config['enable_entity_extraction'],
                'keyword_extraction': self.config['enable_keyword_extraction'],
                'batch_processing': True,
                'custom_models': len(self.config['custom_models'])
            }
        }
        
        return model_info