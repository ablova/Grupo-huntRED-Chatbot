import logging
import spacy
import transformers
import torch
from typing import Dict, Any, Optional, List, Union
from app.models import BusinessUnit
from .core import DynamicModule
from cachetools import TTLCache
from concurrent.futures import ThreadPoolExecutor
import asyncio
import numpy as np

logger = logging.getLogger(__name__)

# Configuración de cache
CACHE_SIZE = 1000
CACHE_TTL = 3600  # segundos

# Configuración de modelos
MODEL_CONFIG = {
    'sentiment': 'distilbert-base-uncased-finetuned-sst-2-english',
    'ner': 'dbmdz/bert-large-cased-finetuned-conll03-english',
    'contextual': 'sentence-transformers/all-MiniLM-L6-v2'
}

class EnhancedNLPProcessor(DynamicModule):
    """Procesador NLP mejorado con cache y procesamiento contextual."""
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self.cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)
        self.models = {}
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
    async def initialize(self) -> None:
        """Inicializa los recursos NLP."""
        await super().initialize()
        await self._load_models()
        
    async def _load_models(self) -> None:
        """Carga los modelos NLP."""
        # Cargar modelos en ThreadPool para evitar bloqueo
        for model_type, model_name in MODEL_CONFIG.items():
            await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                lambda: self._load_model(model_type, model_name)
            )
            
    def _load_model(self, model_type: str, model_name: str) -> None:
        """Carga un modelo específico."""
        try:
            if model_type == 'sentiment':
                model = transformers.pipeline('sentiment-analysis', model=model_name)
            elif model_type == 'ner':
                model = transformers.pipeline('ner', model=model_name)
            elif model_type == 'contextual':
                model = transformers.SentenceTransformer(model_name)
            else:
                raise ValueError(f"Modelo no soportado: {model_type}")
                
            self.models[model_type] = model
            logger.info(f"Modelo {model_type} cargado exitosamente")
            
        except Exception as e:
            logger.error(f"Error cargando modelo {model_type}: {str(e)}")
            
    async def analyze_sentiment(self, text: str) -> Dict:
        """Analiza el sentimiento del texto."""
        cache_key = f"sentiment:{text}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        try:
            result = await self._run_model('sentiment', text)
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {str(e)}")
            raise
            
    async def extract_entities(self, text: str) -> List[Dict]:
        """Extrae entidades nombradas del texto."""
        cache_key = f"ner:{text}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        try:
            result = await self._run_model('ner', text)
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error en extracción de entidades: {str(e)}")
            raise
            
    async def generate_contextual_response(self, 
                                         text: str, 
                                         context: Optional[List[str]] = None,
                                         previous_messages: Optional[List[Dict]] = None) -> Dict:
        """Genera una respuesta contextualizada."""
        try:
            # Analizar sentimiento
            sentiment = await self.analyze_sentiment(text)
            
            # Extraer entidades
            entities = await self.extract_entities(text)
            
            # Generar embeddings
            embeddings = await self._generate_embeddings(text, context)
            
            # Analizar contexto
            context_analysis = await self._analyze_context(
                text,
                previous_messages
            )
            
            # Generar respuesta
            response = self._generate_response(
                text,
                sentiment,
                entities,
                embeddings,
                context_analysis
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error en procesamiento contextual: {str(e)}")
            raise
            
    async def _run_model(self, model_type: str, text: str) -> Any:
        """Ejecuta un modelo específico."""
        if model_type not in self.models:
            raise ValueError(f"Modelo no encontrado: {model_type}")
            
        model = self.models[model_type]
        return await asyncio.get_event_loop().run_in_executor(
            self.thread_pool,
            lambda: model(text)
        )
        
    async def _generate_embeddings(self, text: str, context: Optional[List[str]]) -> np.ndarray:
        """Genera embeddings contextuales."""
        try:
            if not context:
                context = [text]
                
            # Concatenar contexto
            full_text = ' '.join(context + [text])
            
            # Generar embeddings
            embeddings = await self._run_model('contextual', full_text)
            return embeddings.get('sentence_embedding')
            
        except Exception as e:
            logger.error(f"Error generando embeddings: {str(e)}")
            raise
            
    async def _analyze_context(self, 
                             text: str, 
                             previous_messages: Optional[List[Dict]]) -> Dict:
        """Analiza el contexto de la conversación."""
        context = {
            'message_count': 0,
            'topics': [],
            'sentiment_trend': 'neutral',
            'relevance': 1.0
        }
        
        if not previous_messages:
            return context
            
        try:
            # Analizar mensajes previos
            for msg in previous_messages:
                msg_sentiment = await self.analyze_sentiment(msg['text'])
                context['message_count'] += 1
                
                # Detectar temas
                entities = await self.extract_entities(msg['text'])
                for entity in entities:
                    if entity['entity'] not in context['topics']:
                        context['topics'].append(entity['entity'])
            
            # Calcular tendencia de sentimiento
            if context['message_count'] > 1:
                context['sentiment_trend'] = self._calculate_sentiment_trend(
                    previous_messages
                )
            
            # Calcular relevancia
            context['relevance'] = self._calculate_relevance(
                text,
                previous_messages
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error analizando contexto: {str(e)}")
            raise
            
    def _calculate_sentiment_trend(self, messages: List[Dict]) -> str:
        """Calcula la tendencia del sentimiento en la conversación."""
        sentiments = []
        for msg in messages:
            sentiment = self.analyze_sentiment(msg['text'])
            sentiments.append(sentiment['label'])
            
        # Simple trend analysis
        if len(sentiments) < 2:
            return 'neutral'
            
        last_sentiment = sentiments[-1]
        previous_sentiment = sentiments[-2]
        
        if last_sentiment == previous_sentiment:
            return 'stable'
        elif last_sentiment == 'POSITIVE':
            return 'improving'
        else:
            return 'declining'
            
    def _calculate_relevance(self, text: str, messages: List[Dict]) -> float:
        """Calcula la relevancia del texto en el contexto."""
        if not messages:
            return 1.0
            
        try:
            # Generar embeddings
            current_embedding = await self._generate_embeddings(text, [])
            previous_embeddings = []
            
            for msg in messages:
                embedding = await self._generate_embeddings(
                    msg['text'],
                    []
                )
                previous_embeddings.append(embedding)
            
            # Calcular similitud media
            similarities = []
            for prev_emb in previous_embeddings:
                similarity = np.dot(current_embedding, prev_emb) / \
                             (np.linalg.norm(current_embedding) * 
                              np.linalg.norm(prev_emb))
                similarities.append(similarity)
            
            return float(np.mean(similarities))
            
        except Exception as e:
            logger.error(f"Error calculando relevancia: {str(e)}")
            return 0.5
            
    def _generate_response(self, 
                         text: str,
                         sentiment: Dict,
                         entities: List[Dict],
                         embeddings: np.ndarray,
                         context: Dict) -> Dict:
        """Genera una respuesta completa con análisis contextual."""
        return {
            'text': text,
            'sentiment': sentiment,
            'entities': entities,
            'context': context,
            'embeddings': embeddings.tolist(),
            'timestamp': time.time(),
            'business_unit': self.business_unit.name
        }
        
    async def process_event(self, event_type: str, data: Dict) -> Dict:
        """Procesa eventos NLP."""
        if event_type == 'analyze_text':
            return await self.generate_contextual_response(
                data['text'],
                data.get('context'),
                data.get('previous_messages')
            )
            
        if event_type == 'sentiment':
            return await self.analyze_sentiment(data['text'])
            
        if event_type == 'entities':
            return await self.extract_entities(data['text'])
            
        return {}
