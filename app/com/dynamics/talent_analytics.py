from typing import Dict, Any, Optional, List
import logging
from .core import DynamicModule
from app.models import BusinessUnit, Person, Vacante
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import spacy
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class TalentAnalytics(DynamicModule):
    """Sistema avanzado de análisis de talento y matchmaking."""
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self.nlp = spacy.load("en_core_web_lg")
        self.talent_cache = {}
        self.job_cache = {}
        self.similarity_cache = {}
        self.config = None
        
    async def _load_config(self) -> Dict:
        """Carga configuración dinámica desde la base de datos."""
        try:
            config = await TalentConfig.objects.get(
                business_unit=self.business_unit
            )
            
            # Obtener ponderaciones por defecto
            default_weights = await config.default_weights
            
            return {
                'matching': {
                    'threshold': config.match_threshold,
                    'weights': {
                        'skills': default_weights.weight_skills,
                        'experience': default_weights.weight_experience,
                        'culture': default_weights.weight_culture,
                        'location': default_weights.weight_location
                    }
                },
                'analytics': {
                    'time_window': config.time_window_days,
                    'min_interactions': config.min_interactions,
                    'sentiment_threshold': config.sentiment_threshold
                },
                'optimization': {
                    'cache_ttl': config.cache_ttl,
                    'batch_size': config.batch_size
                },
                'personality': {
                    'importance': config.personality_importance
                }
            }
        except (TalentConfig.DoesNotExist, WeightingModel.DoesNotExist):
            # Si no existe la configuración, usar valores por defecto
            return {
                'matching': {
                    'threshold': 0.75,
                    'weights': {
                        'skills': 0.4,
                        'experience': 0.3,
                        'culture': 0.2,
                        'location': 0.1
                    }
                },
                'analytics': {
                    'time_window': 30,
                    'min_interactions': 5,
                    'sentiment_threshold': 0.7
                },
                'optimization': {
                    'cache_ttl': 3600,
                    'batch_size': 100
                },
                'personality': {
                    'importance': 0.3
                }
            }
        
    async def initialize(self) -> None:
        """Inicializa recursos para análisis de talento."""
        await super().initialize()
        await self._load_talent_data()
        await self._load_job_data()
        
    async def _load_talent_data(self) -> None:
        """Carga datos de talento existentes."""
        talents = await Person.objects.filter(
            business_unit=self.business_unit
        ).values()
        
        for talent in talents:
            self.talent_cache[talent['id']] = {
                'profile': talent,
                'embeddings': await self._generate_embeddings(talent['skills']),
                'sentiment': await self._analyze_sentiment(talent['messages'])
            }
            
    async def _load_job_data(self) -> None:
        """Carga datos de vacantes existentes."""
        jobs = await Vacante.objects.filter(
            business_unit=self.business_unit
        ).values()
        
        for job in jobs:
            self.job_cache[job['id']] = {
                'description': job,
                'embeddings': await self._generate_embeddings(job['requirements'])
            }
            
    async def _generate_embeddings(self, text: str) -> np.ndarray:
        """Genera embeddings para texto."""
        doc = self.nlp(text)
        return doc.vector
        
    async def _analyze_sentiment(self, messages: List[str]) -> float:
        """Analiza el sentimiento de los mensajes."""
        if not messages:
            return 0.5
            
        sentiments = []
        for message in messages:
            doc = self.nlp(message)
            sentiment = doc.sentiment
            sentiments.append(sentiment)
            
        return float(np.mean(sentiments))
        
    async def extract_talent_profile(self, messages: List[Dict]) -> Dict:
        """Extrae perfil de talento de mensajes."""
        profile = {
            'skills': [],
            'experience': [],
            'preferences': {},
            'sentiment': 0.0,
            'culture_fit': 0.0
        }
        
        # Procesar mensajes
        for message in messages:
            doc = self.nlp(message['text'])
            
            # Extraer habilidades
            for token in doc:
                if token.pos_ in ['NOUN', 'ADJ'] and token.ent_type_ == '':
                    profile['skills'].append(token.text)
                    
            # Extraer experiencia
            if 'experience' in message['text'].lower():
                profile['experience'].append(message['text'])
                
            # Analizar sentimiento
            profile['sentiment'] = await self._analyze_sentiment([message['text']])
            
        # Analizar preferencias
        if profile['sentiment'] > self.config['analytics']['sentiment_threshold']:
            profile['preferences']['communication'] = 'positive'
            
        return profile
        
    async def calculate_match_score(self, talent_id: int, job_id: int) -> Dict:
        """Calcula el score de matching entre talento y vacante."""
        cache_key = f"match:{talent_id}:{job_id}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
            
        try:
            talent = self.talent_cache.get(talent_id)
            job = self.job_cache.get(job_id)
            
            if not talent or not job:
                return {'score': 0.0, 'details': {} }
                
            # Calcular similitudes
            skill_sim = cosine_similarity(
                [talent['embeddings']],
                [job['embeddings']]
            )[0][0]
            
            # Calcular score ponderado
            weights = self.config['matching']
            score = (
                weights['weight_skills'] * skill_sim +
                weights['weight_experience'] * await self._calculate_experience_match(talent, job) +
                weights['weight_culture'] * await self._calculate_culture_fit(talent) +
                weights['weight_location'] * await self._calculate_location_match(talent, job)
            )
            
            result = {
                'score': float(score),
                'details': {
                    'skills': float(skill_sim),
                    'experience': float(await self._calculate_experience_match(talent, job)),
                    'culture': float(await self._calculate_culture_fit(talent)),
                    'location': float(await self._calculate_location_match(talent, job)),
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            self.similarity_cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error calculating match score: {str(e)}")
            return {'score': 0.0, 'details': {} }
            
    async def _calculate_experience_match(self, talent: Dict, job: Dict) -> float:
        """Calcula match de experiencia."""
        if not talent['experience'] or not job['description']['experience']:
            return 0.5
            
        exp_talent = ' '.join(talent['experience'])
        exp_job = job['description']['experience']
        
        doc_talent = self.nlp(exp_talent)
        doc_job = self.nlp(exp_job)
        
        return float(cosine_similarity(
            [doc_talent.vector],
            [doc_job.vector]
        )[0][0])
        
    async def _calculate_culture_fit(self, talent: Dict) -> float:
        """Calcula fit cultural basado en mensajes."""
        if not talent['messages']:
            return 0.5
            
        # Analizar mensajes recientes
        recent_messages = talent['messages'][-5:]  # Últimos 5 mensajes
        sentiment = await self._analyze_sentiment(recent_messages)
        
        # Analizar temas
        topics = []
        for message in recent_messages:
            doc = self.nlp(message)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PERSON', 'WORK_OF_ART']:
                    topics.append(ent.text)
                    
        # Calcular score de fit cultural
        return float(
            sentiment * 0.6 +  # 60% basado en sentimiento
            (len(topics) > 0) * 0.4  # 40% basado en participación
        )
        
    async def _calculate_location_match(self, talent: Dict, job: Dict) -> float:
        """Calcula match de ubicación."""
        if not talent['profile']['location'] or not job['description']['location']:
            return 0.5
            
        loc_talent = talent['profile']['location']
        loc_job = job['description']['location']
        
        doc_talent = self.nlp(loc_talent)
        doc_job = self.nlp(loc_job)
        
        return float(cosine_similarity(
            [doc_talent.vector],
            [doc_job.vector]
        )[0][0])
        
    async def get_top_matches(self, job_id: int, limit: int = 5) -> List[Dict]:
        """Obtiene los mejores matches para una vacante."""
        matches = []
        
        for talent_id in self.talent_cache:
            score = await self.calculate_match_score(talent_id, job_id)
            if score['score'] >= self.matching_threshold:
                matches.append({
                    'talent_id': talent_id,
                    'score': score
                })
                
        matches.sort(key=lambda x: x['score']['score'], reverse=True)
        return matches[:limit]
        
    async def process_event(self, event_type: str, data: Dict) -> Dict:
        """Procesa eventos de análisis de talento."""
        if event_type == 'message':
            # Extraer perfil de talento
            profile = await self.extract_talent_profile(data['messages'])
            return {'profile': profile}
            
        if event_type == 'match':
            # Calcular matching
            score = await self.calculate_match_score(
                data['talent_id'],
                data['job_id']
            )
            return {'match_score': score}
            
        if event_type == 'top_matches':
            # Obtener mejores matches
            matches = await self.get_top_matches(data['job_id'])
            return {'matches': matches}
            
        return {}
