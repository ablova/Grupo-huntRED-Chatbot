"""
SocialLink - Análisis Completo de Redes Sociales huntRED® v2
============================================================

Funcionalidades:
- Graph analysis de redes profesionales
- Sentiment analysis de posts y contenido
- Professional network mapping y influencia
- Credibility scoring y verificación
- Social media scraping ético
- Behavioral pattern analysis
- Reputation monitoring
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import re
import networkx as nx
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger(__name__)

class SocialPlatform(Enum):
    """Plataformas de redes sociales soportadas."""
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    GITHUB = "github"
    STACKOVERFLOW = "stackoverflow"
    MEDIUM = "medium"
    YOUTUBE = "youtube"

class ContentType(Enum):
    """Tipos de contenido en redes sociales."""
    POST = "post"
    COMMENT = "comment"
    ARTICLE = "article"
    VIDEO = "video"
    IMAGE = "image"
    STORY = "story"
    LIVE = "live"
    POLL = "poll"

class SentimentType(Enum):
    """Tipos de sentimiento."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

class InfluenceLevel(Enum):
    """Niveles de influencia."""
    MICRO = "micro"           # < 1K followers
    EMERGING = "emerging"     # 1K - 10K
    RISING = "rising"         # 10K - 100K
    INFLUENCER = "influencer" # 100K - 1M
    MEGA = "mega"            # > 1M

@dataclass
class SocialProfile:
    """Perfil de red social de un usuario."""
    platform: SocialPlatform
    username: str
    display_name: str
    user_id: str
    
    # Métricas básicas
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    engagement_rate: float = 0.0
    
    # Información del perfil
    bio: str = ""
    location: str = ""
    website: str = ""
    verified: bool = False
    
    # Análisis profesional
    job_title: str = ""
    company: str = ""
    industry: str = ""
    skills: List[str] = field(default_factory=list)
    
    # Fechas
    account_created: Optional[datetime] = None
    last_active: Optional[datetime] = None
    profile_updated: datetime = field(default_factory=datetime.now)

@dataclass
class SocialContent:
    """Contenido de redes sociales."""
    id: str
    platform: SocialPlatform
    author_id: str
    content_type: ContentType
    
    # Contenido
    text: str = ""
    media_urls: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    
    # Métricas de engagement
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    views_count: int = 0
    
    # Análisis
    sentiment_score: float = 0.0
    sentiment_type: SentimentType = SentimentType.NEUTRAL
    topics: List[str] = field(default_factory=list)
    language: str = "es"
    
    # Metadatos
    posted_at: datetime = field(default_factory=datetime.now)
    scraped_at: datetime = field(default_factory=datetime.now)

@dataclass
class NetworkConnection:
    """Conexión en la red social."""
    source_id: str
    target_id: str
    platform: SocialPlatform
    connection_type: str  # "follow", "friend", "connection", "collaboration"
    
    # Fortaleza de la conexión
    interaction_frequency: float = 0.0
    mutual_connections: int = 0
    relationship_strength: float = 0.0
    
    # Metadatos
    connected_since: Optional[datetime] = None
    last_interaction: Optional[datetime] = None

@dataclass
class InfluenceMetrics:
    """Métricas de influencia de un usuario."""
    user_id: str
    platform: SocialPlatform
    
    # Métricas básicas
    reach: int = 0
    engagement_rate: float = 0.0
    influence_score: float = 0.0
    influence_level: InfluenceLevel = InfluenceLevel.MICRO
    
    # Análisis de red
    network_centrality: float = 0.0
    clustering_coefficient: float = 0.0
    betweenness_centrality: float = 0.0
    pagerank_score: float = 0.0
    
    # Credibilidad
    credibility_score: float = 0.0
    expertise_areas: List[str] = field(default_factory=list)
    authority_indicators: List[str] = field(default_factory=list)
    
    # Temporales
    growth_rate: float = 0.0
    consistency_score: float = 0.0
    last_calculated: datetime = field(default_factory=datetime.now)

@dataclass
class SocialAnalysis:
    """Análisis completo de presencia social."""
    user_id: str
    analysis_id: str
    
    # Perfiles analizados
    profiles: List[SocialProfile] = field(default_factory=list)
    content_analyzed: List[SocialContent] = field(default_factory=list)
    
    # Métricas consolidadas
    overall_influence_score: float = 0.0
    professional_credibility: float = 0.0
    content_quality_score: float = 0.0
    network_strength: float = 0.0
    
    # Análisis de sentimiento
    sentiment_distribution: Dict[SentimentType, float] = field(default_factory=dict)
    topic_expertise: Dict[str, float] = field(default_factory=dict)
    
    # Red profesional
    network_size: int = 0
    network_quality: float = 0.0
    industry_connections: Dict[str, int] = field(default_factory=dict)
    
    # Insights y recomendaciones
    strengths: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Alertas
    red_flags: List[str] = field(default_factory=list)
    risk_indicators: List[str] = field(default_factory=list)
    
    # Metadatos
    analysis_date: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.0

class SocialLinkEngine:
    """Motor principal de análisis de redes sociales."""
    
    def __init__(self):
        self.profiles: Dict[str, List[SocialProfile]] = defaultdict(list)
        self.content: Dict[str, List[SocialContent]] = defaultdict(list)
        self.networks: Dict[SocialPlatform, nx.DiGraph] = {}
        self.analyses: Dict[str, SocialAnalysis] = {}
        
        # Configuración de scoring
        self.sentiment_weights = {
            SentimentType.VERY_POSITIVE: 1.0,
            SentimentType.POSITIVE: 0.5,
            SentimentType.NEUTRAL: 0.0,
            SentimentType.NEGATIVE: -0.5,
            SentimentType.VERY_NEGATIVE: -1.0
        }
        
        # Palabras clave para análisis profesional
        self.professional_keywords = {
            "leadership": ["liderazgo", "gestión", "equipo", "management", "director"],
            "innovation": ["innovación", "creatividad", "disruptivo", "startup", "tecnología"],
            "expertise": ["experto", "especialista", "certificación", "experiencia"],
            "collaboration": ["colaboración", "trabajo en equipo", "networking", "mentoring"],
            "communication": ["presentación", "conferencia", "speaker", "webinar", "podcast"]
        }
        
        # Setup inicial
        self._initialize_networks()
        self._setup_sample_data()
    
    def _initialize_networks(self):
        """Inicializa los grafos de red para cada plataforma."""
        for platform in SocialPlatform:
            self.networks[platform] = nx.DiGraph()
    
    def _setup_sample_data(self):
        """Configura datos de ejemplo para testing."""
        
        # Perfil ejemplo LinkedIn
        sample_profile = SocialProfile(
            platform=SocialPlatform.LINKEDIN,
            username="ana.garcia.dev",
            display_name="Ana García",
            user_id="ana_garcia_001",
            followers_count=2500,
            following_count=800,
            posts_count=150,
            engagement_rate=0.08,
            bio="Senior Software Engineer | Python Expert | AI Enthusiast",
            location="Ciudad de México, México",
            job_title="Senior Software Engineer",
            company="TechCorp",
            industry="Technology",
            skills=["Python", "Machine Learning", "Django", "React"],
            verified=False
        )
        
        self.profiles["ana_garcia_001"].append(sample_profile)
    
    async def analyze_social_presence(self, user_identifier: str, 
                                    platforms: List[SocialPlatform] = None,
                                    deep_analysis: bool = True) -> str:
        """Realiza análisis completo de presencia social."""
        
        analysis_id = str(uuid.uuid4())
        
        if platforms is None:
            platforms = [SocialPlatform.LINKEDIN, SocialPlatform.TWITTER, SocialPlatform.GITHUB]
        
        # Buscar perfiles en plataformas especificadas
        profiles = []
        for platform in platforms:
            profile = await self._find_profile(user_identifier, platform)
            if profile:
                profiles.append(profile)
        
        if not profiles:
            logger.warning(f"No profiles found for user: {user_identifier}")
            return analysis_id
        
        # Analizar contenido de cada perfil
        all_content = []
        for profile in profiles:
            content = await self._analyze_profile_content(profile, deep_analysis)
            all_content.extend(content)
        
        # Realizar análisis de red
        network_analysis = await self._analyze_network_connections(profiles)
        
        # Calcular métricas de influencia
        influence_metrics = await self._calculate_influence_metrics(profiles, all_content)
        
        # Análisis de sentimiento y contenido
        sentiment_analysis = await self._analyze_content_sentiment(all_content)
        content_quality = await self._assess_content_quality(all_content)
        
        # Análisis de credibilidad profesional
        credibility_score = await self._assess_professional_credibility(profiles, all_content)
        
        # Detectar red flags y riesgos
        red_flags = await self._detect_red_flags(profiles, all_content)
        
        # Generar insights y recomendaciones
        insights = await self._generate_social_insights(profiles, all_content, influence_metrics)
        
        # Crear análisis completo
        analysis = SocialAnalysis(
            user_id=user_identifier,
            analysis_id=analysis_id,
            profiles=profiles,
            content_analyzed=all_content,
            overall_influence_score=influence_metrics.get("overall_score", 0.0),
            professional_credibility=credibility_score,
            content_quality_score=content_quality,
            network_strength=network_analysis.get("strength", 0.0),
            sentiment_distribution=sentiment_analysis,
            network_size=network_analysis.get("size", 0),
            network_quality=network_analysis.get("quality", 0.0),
            strengths=insights.get("strengths", []),
            improvement_areas=insights.get("improvements", []),
            recommendations=insights.get("recommendations", []),
            red_flags=red_flags,
            confidence_score=await self._calculate_analysis_confidence(profiles, all_content)
        )
        
        self.analyses[analysis_id] = analysis
        
        logger.info(f"Social analysis completed: {analysis_id} for {user_identifier}")
        return analysis_id
    
    async def _find_profile(self, user_identifier: str, platform: SocialPlatform) -> Optional[SocialProfile]:
        """Busca perfil de usuario en una plataforma específica."""
        
        # En un sistema real, aquí se integraría con APIs de cada plataforma
        # Por ahora, simular búsqueda
        
        existing_profiles = self.profiles.get(user_identifier, [])
        for profile in existing_profiles:
            if profile.platform == platform:
                return profile
        
        # Simular búsqueda por diferentes criterios
        if platform == SocialPlatform.LINKEDIN:
            # Búsqueda por email, nombre, etc.
            return await self._simulate_linkedin_search(user_identifier)
        
        elif platform == SocialPlatform.GITHUB:
            return await self._simulate_github_search(user_identifier)
        
        elif platform == SocialPlatform.TWITTER:
            return await self._simulate_twitter_search(user_identifier)
        
        return None
    
    async def _simulate_linkedin_search(self, identifier: str) -> Optional[SocialProfile]:
        """Simula búsqueda en LinkedIn."""
        
        # En producción: usar LinkedIn API o scraping ético
        if "ana" in identifier.lower():
            return SocialProfile(
                platform=SocialPlatform.LINKEDIN,
                username="ana.garcia.dev",
                display_name="Ana García",
                user_id=f"linkedin_{identifier}",
                followers_count=2500,
                following_count=800,
                job_title="Senior Software Engineer",
                company="TechCorp",
                industry="Technology",
                bio="Passionate about AI and clean code"
            )
        
        return None
    
    async def _simulate_github_search(self, identifier: str) -> Optional[SocialProfile]:
        """Simula búsqueda en GitHub."""
        
        if "ana" in identifier.lower():
            return SocialProfile(
                platform=SocialPlatform.GITHUB,
                username="ana-garcia-dev",
                display_name="Ana García",
                user_id=f"github_{identifier}",
                followers_count=150,
                following_count=80,
                posts_count=45,  # Repositorios
                bio="Python developer | ML enthusiast",
                skills=["Python", "JavaScript", "Machine Learning"]
            )
        
        return None
    
    async def _simulate_twitter_search(self, identifier: str) -> Optional[SocialProfile]:
        """Simula búsqueda en Twitter."""
        
        if "ana" in identifier.lower():
            return SocialProfile(
                platform=SocialPlatform.TWITTER,
                username="ana_garcia_dev",
                display_name="Ana García 🐍",
                user_id=f"twitter_{identifier}",
                followers_count=850,
                following_count=320,
                posts_count=1200,
                bio="Senior Developer | Python | AI | Coffee ☕",
                location="CDMX"
            )
        
        return None
    
    async def _analyze_profile_content(self, profile: SocialProfile, 
                                     deep_analysis: bool = True) -> List[SocialContent]:
        """Analiza el contenido de un perfil."""
        
        content_list = []
        
        # En un sistema real, aquí se haría scraping del contenido real
        # Por ahora, generar contenido de ejemplo basado en el perfil
        
        if profile.platform == SocialPlatform.LINKEDIN:
            # Simular posts profesionales
            content_list.extend(await self._generate_linkedin_content(profile))
        
        elif profile.platform == SocialPlatform.GITHUB:
            # Analizar repositorios y commits
            content_list.extend(await self._generate_github_content(profile))
        
        elif profile.platform == SocialPlatform.TWITTER:
            # Analizar tweets
            content_list.extend(await self._generate_twitter_content(profile))
        
        # Realizar análisis de sentimiento en cada contenido
        for content in content_list:
            content.sentiment_score = await self._calculate_sentiment(content.text)
            content.sentiment_type = await self._classify_sentiment(content.sentiment_score)
            content.topics = await self._extract_topics(content.text)
        
        return content_list
    
    async def _generate_linkedin_content(self, profile: SocialProfile) -> List[SocialContent]:
        """Genera contenido de ejemplo para LinkedIn."""
        
        sample_posts = [
            {
                "text": "Excited to share insights from our latest AI project! Machine learning is transforming how we approach software development. #AI #MachineLearning #TechInnovation",
                "likes": 45,
                "comments": 8,
                "shares": 12
            },
            {
                "text": "Just completed a challenging migration to Django 4.0. The performance improvements are incredible! Here's what we learned... #Django #Python #WebDev",
                "likes": 32,
                "comments": 15,
                "shares": 6
            },
            {
                "text": "Mentoring junior developers has been one of the most rewarding aspects of my career. Sharing knowledge creates stronger teams. #Mentoring #Leadership #TeamBuilding",
                "likes": 67,
                "comments": 23,
                "shares": 18
            }
        ]
        
        content_list = []
        for i, post_data in enumerate(sample_posts):
            content = SocialContent(
                id=f"{profile.user_id}_post_{i}",
                platform=profile.platform,
                author_id=profile.user_id,
                content_type=ContentType.POST,
                text=post_data["text"],
                likes_count=post_data["likes"],
                comments_count=post_data["comments"],
                shares_count=post_data["shares"],
                hashtags=re.findall(r'#\w+', post_data["text"]),
                posted_at=datetime.now() - timedelta(days=i*7)
            )
            content_list.append(content)
        
        return content_list
    
    async def _generate_github_content(self, profile: SocialProfile) -> List[SocialContent]:
        """Genera contenido de ejemplo para GitHub."""
        
        sample_repos = [
            {
                "text": "ml-pipeline: Production-ready machine learning pipeline with Django REST API",
                "stars": 23,
                "forks": 8
            },
            {
                "text": "data-visualization-toolkit: Interactive data visualization components for React",
                "stars": 15,
                "forks": 4
            }
        ]
        
        content_list = []
        for i, repo_data in enumerate(sample_repos):
            content = SocialContent(
                id=f"{profile.user_id}_repo_{i}",
                platform=profile.platform,
                author_id=profile.user_id,
                content_type=ContentType.POST,  # Tratamos repos como posts
                text=repo_data["text"],
                likes_count=repo_data["stars"],
                shares_count=repo_data["forks"],
                posted_at=datetime.now() - timedelta(days=i*30)
            )
            content_list.append(content)
        
        return content_list
    
    async def _generate_twitter_content(self, profile: SocialProfile) -> List[SocialContent]:
        """Genera contenido de ejemplo para Twitter."""
        
        sample_tweets = [
            {
                "text": "Working on a new ML model for predictive analytics. The preliminary results are promising! 🤖 #MachineLearning #DataScience",
                "likes": 12,
                "retweets": 3,
                "replies": 2
            },
            {
                "text": "Python's new match statement is a game changer for code readability. Finally! 🐍 #Python #Programming",
                "likes": 8,
                "retweets": 1,
                "replies": 4
            }
        ]
        
        content_list = []
        for i, tweet_data in enumerate(sample_tweets):
            content = SocialContent(
                id=f"{profile.user_id}_tweet_{i}",
                platform=profile.platform,
                author_id=profile.user_id,
                content_type=ContentType.POST,
                text=tweet_data["text"],
                likes_count=tweet_data["likes"],
                shares_count=tweet_data["retweets"],
                comments_count=tweet_data["replies"],
                hashtags=re.findall(r'#\w+', tweet_data["text"]),
                posted_at=datetime.now() - timedelta(hours=i*12)
            )
            content_list.append(content)
        
        return content_list
    
    async def _calculate_sentiment(self, text: str) -> float:
        """Calcula score de sentimiento (-1 a 1)."""
        
        # Palabras positivas y negativas en español e inglés
        positive_words = [
            "excelente", "increíble", "amazing", "great", "excited", "love",
            "fantastic", "awesome", "brilliant", "outstanding", "successful",
            "innovador", "genial", "fantástico", "éxito", "logro"
        ]
        
        negative_words = [
            "terrible", "awful", "bad", "horrible", "hate", "failed",
            "disaster", "worst", "disappointed", "frustrated", "angry",
            "malo", "terrible", "horrible", "fracaso", "problema"
        ]
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if any(pos in word for pos in positive_words))
        negative_count = sum(1 for word in words if any(neg in word for neg in negative_words))
        
        total_words = len(words)
        if total_words == 0:
            return 0.0
        
        sentiment_score = (positive_count - negative_count) / total_words
        return max(-1.0, min(1.0, sentiment_score))
    
    async def _classify_sentiment(self, score: float) -> SentimentType:
        """Clasifica el sentimiento basado en el score."""
        
        if score >= 0.5:
            return SentimentType.VERY_POSITIVE
        elif score >= 0.1:
            return SentimentType.POSITIVE
        elif score <= -0.5:
            return SentimentType.VERY_NEGATIVE
        elif score <= -0.1:
            return SentimentType.NEGATIVE
        else:
            return SentimentType.NEUTRAL
    
    async def _extract_topics(self, text: str) -> List[str]:
        """Extrae tópicos principales del texto."""
        
        topics = []
        text_lower = text.lower()
        
        # Buscar tópicos profesionales
        for topic, keywords in self.professional_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        # Buscar tecnologías
        tech_keywords = ["python", "javascript", "react", "django", "ai", "ml", "data", "cloud"]
        for tech in tech_keywords:
            if tech in text_lower:
                topics.append(f"tech_{tech}")
        
        return topics
    
    async def _analyze_network_connections(self, profiles: List[SocialProfile]) -> Dict[str, Any]:
        """Analiza las conexiones de red del usuario."""
        
        total_connections = sum(profile.following_count for profile in profiles)
        total_followers = sum(profile.followers_count for profile in profiles)
        
        # Calcular fortaleza de red basada en engagement
        network_strength = 0.0
        if total_followers > 0:
            avg_engagement = sum(profile.engagement_rate for profile in profiles) / len(profiles)
            network_strength = min(1.0, avg_engagement * 10)  # Normalizar a 0-1
        
        # Calcular calidad de red
        network_quality = 0.0
        if total_connections > 0:
            # Ratio followers/following como indicador de calidad
            ratio = total_followers / total_connections if total_connections > 0 else 0
            network_quality = min(1.0, ratio / 3)  # Normalizar
        
        return {
            "size": total_connections,
            "followers": total_followers,
            "strength": network_strength,
            "quality": network_quality,
            "platforms": len(profiles)
        }
    
    async def _calculate_influence_metrics(self, profiles: List[SocialProfile], 
                                         content: List[SocialContent]) -> Dict[str, float]:
        """Calcula métricas de influencia."""
        
        # Métricas básicas
        total_reach = sum(profile.followers_count for profile in profiles)
        total_engagement = sum(c.likes_count + c.comments_count + c.shares_count for c in content)
        
        # Calcular engagement rate promedio
        avg_engagement_rate = 0.0
        if profiles:
            avg_engagement_rate = sum(profile.engagement_rate for profile in profiles) / len(profiles)
        
        # Score de influencia basado en múltiples factores
        influence_score = 0.0
        
        if total_reach > 0:
            # Factor reach (30%)
            reach_factor = min(1.0, total_reach / 10000) * 0.3
            
            # Factor engagement (40%)
            engagement_factor = avg_engagement_rate * 0.4
            
            # Factor contenido (30%)
            content_factor = 0.0
            if content:
                avg_engagement_per_post = total_engagement / len(content)
                content_factor = min(1.0, avg_engagement_per_post / 100) * 0.3
            
            influence_score = reach_factor + engagement_factor + content_factor
        
        return {
            "overall_score": influence_score * 100,
            "reach": total_reach,
            "engagement_rate": avg_engagement_rate,
            "content_performance": total_engagement
        }
    
    async def _analyze_content_sentiment(self, content: List[SocialContent]) -> Dict[SentimentType, float]:
        """Analiza la distribución de sentimientos en el contenido."""
        
        if not content:
            return {sentiment: 0.0 for sentiment in SentimentType}
        
        sentiment_counts = Counter(c.sentiment_type for c in content)
        total_content = len(content)
        
        return {
            sentiment: (count / total_content) * 100
            for sentiment, count in sentiment_counts.items()
        }
    
    async def _assess_content_quality(self, content: List[SocialContent]) -> float:
        """Evalúa la calidad del contenido."""
        
        if not content:
            return 0.0
        
        quality_factors = []
        
        for c in content:
            # Factor 1: Engagement ratio
            total_interactions = c.likes_count + c.comments_count + c.shares_count
            engagement_quality = min(1.0, total_interactions / 50)  # Normalizar
            
            # Factor 2: Contenido profesional
            professional_score = 0.0
            if any(topic.startswith("leadership") or topic.startswith("expertise") 
                   for topic in c.topics):
                professional_score = 0.3
            
            # Factor 3: Uso de hashtags apropiados
            hashtag_score = min(0.2, len(c.hashtags) * 0.05)
            
            # Factor 4: Sentimiento positivo
            sentiment_score = max(0.0, c.sentiment_score) * 0.2
            
            content_quality = engagement_quality + professional_score + hashtag_score + sentiment_score
            quality_factors.append(min(1.0, content_quality))
        
        return (sum(quality_factors) / len(quality_factors)) * 100
    
    async def _assess_professional_credibility(self, profiles: List[SocialProfile], 
                                             content: List[SocialContent]) -> float:
        """Evalúa la credibilidad profesional."""
        
        credibility_score = 0.0
        factors_count = 0
        
        # Factor 1: Perfiles completos
        complete_profiles = sum(1 for p in profiles if p.job_title and p.company and p.bio)
        if profiles:
            profile_completeness = (complete_profiles / len(profiles)) * 20
            credibility_score += profile_completeness
            factors_count += 1
        
        # Factor 2: Verificación
        verified_profiles = sum(1 for p in profiles if p.verified)
        if profiles:
            verification_score = (verified_profiles / len(profiles)) * 15
            credibility_score += verification_score
            factors_count += 1
        
        # Factor 3: Contenido profesional
        professional_content = sum(1 for c in content if any(
            topic in ["leadership", "expertise", "innovation"] for topic in c.topics
        ))
        if content:
            professional_ratio = (professional_content / len(content)) * 25
            credibility_score += professional_ratio
            factors_count += 1
        
        # Factor 4: Consistencia en industria/skills
        industry_consistency = await self._calculate_industry_consistency(profiles)
        credibility_score += industry_consistency * 20
        factors_count += 1
        
        # Factor 5: Actividad reciente
        recent_activity = await self._assess_recent_activity(profiles, content)
        credibility_score += recent_activity * 20
        factors_count += 1
        
        return credibility_score / factors_count if factors_count > 0 else 0.0
    
    async def _calculate_industry_consistency(self, profiles: List[SocialProfile]) -> float:
        """Calcula consistencia en industria y skills."""
        
        if not profiles:
            return 0.0
        
        # Verificar consistencia en industria
        industries = [p.industry for p in profiles if p.industry]
        industry_consistency = 1.0 if len(set(industries)) <= 1 else 0.5
        
        # Verificar overlap en skills
        all_skills = []
        for profile in profiles:
            all_skills.extend(profile.skills)
        
        if len(all_skills) > 0:
            unique_skills = set(all_skills)
            skill_repetition = len(all_skills) / len(unique_skills)
            skill_consistency = min(1.0, skill_repetition / 2)
        else:
            skill_consistency = 0.0
        
        return (industry_consistency + skill_consistency) / 2
    
    async def _assess_recent_activity(self, profiles: List[SocialProfile], 
                                    content: List[SocialContent]) -> float:
        """Evalúa la actividad reciente."""
        
        now = datetime.now()
        recent_threshold = timedelta(days=30)
        
        # Verificar perfiles actualizados recientemente
        recent_profiles = sum(1 for p in profiles 
                            if p.profile_updated and (now - p.profile_updated) <= recent_threshold)
        
        # Verificar contenido reciente
        recent_content = sum(1 for c in content 
                           if (now - c.posted_at) <= recent_threshold)
        
        profile_activity = (recent_profiles / len(profiles)) if profiles else 0
        content_activity = (recent_content / len(content)) if content else 0
        
        return (profile_activity + content_activity) / 2
    
    async def _detect_red_flags(self, profiles: List[SocialProfile], 
                              content: List[SocialContent]) -> List[str]:
        """Detecta banderas rojas en el análisis social."""
        
        red_flags = []
        
        # Flag 1: Muy pocos seguidores vs seguidos (posible bot)
        for profile in profiles:
            if profile.followers_count > 0 and profile.following_count > 0:
                ratio = profile.following_count / profile.followers_count
                if ratio > 10:  # Sigue 10x más de lo que lo siguen
                    red_flags.append(f"Ratio seguimiento sospechoso en {profile.platform.value}")
        
        # Flag 2: Contenido muy negativo
        negative_content = sum(1 for c in content 
                             if c.sentiment_type in [SentimentType.NEGATIVE, SentimentType.VERY_NEGATIVE])
        if content and (negative_content / len(content)) > 0.3:
            red_flags.append("Alto porcentaje de contenido negativo")
        
        # Flag 3: Perfil incompleto en plataformas profesionales
        linkedin_profiles = [p for p in profiles if p.platform == SocialPlatform.LINKEDIN]
        for profile in linkedin_profiles:
            if not profile.job_title or not profile.company:
                red_flags.append("Perfil LinkedIn incompleto")
        
        # Flag 4: Inconsistencias en información
        job_titles = [p.job_title for p in profiles if p.job_title]
        companies = [p.company for p in profiles if p.company]
        
        if len(set(job_titles)) > 2:
            red_flags.append("Inconsistencias en títulos de trabajo")
        
        if len(set(companies)) > 2:
            red_flags.append("Inconsistencias en empresas")
        
        # Flag 5: Actividad sospechosa
        if content:
            avg_engagement = statistics.mean(
                c.likes_count + c.comments_count + c.shares_count for c in content
            )
            max_engagement = max(
                c.likes_count + c.comments_count + c.shares_count for c in content
            )
            
            if max_engagement > avg_engagement * 20:  # Un post con engagement 20x superior
                red_flags.append("Patrón de engagement irregular")
        
        return red_flags
    
    async def _generate_social_insights(self, profiles: List[SocialProfile], 
                                       content: List[SocialContent],
                                       influence_metrics: Dict[str, float]) -> Dict[str, List[str]]:
        """Genera insights y recomendaciones."""
        
        insights = {
            "strengths": [],
            "improvements": [],
            "recommendations": []
        }
        
        # Analizar fortalezas
        if influence_metrics.get("overall_score", 0) > 70:
            insights["strengths"].append("Alta influencia en redes sociales")
        
        if any(p.verified for p in profiles):
            insights["strengths"].append("Perfil verificado en al menos una plataforma")
        
        professional_content_ratio = sum(1 for c in content if "leadership" in c.topics or "expertise" in c.topics)
        if content and (professional_content_ratio / len(content)) > 0.4:
            insights["strengths"].append("Contenido altamente profesional")
        
        multi_platform = len(profiles) >= 3
        if multi_platform:
            insights["strengths"].append("Presencia sólida en múltiples plataformas")
        
        # Identificar áreas de mejora
        linkedin_present = any(p.platform == SocialPlatform.LINKEDIN for p in profiles)
        if not linkedin_present:
            insights["improvements"].append("Ausencia en LinkedIn (plataforma profesional clave)")
        
        low_engagement = influence_metrics.get("engagement_rate", 0) < 0.02
        if low_engagement:
            insights["improvements"].append("Tasa de engagement baja")
        
        inconsistent_activity = await self._assess_recent_activity(profiles, content) < 0.3
        if inconsistent_activity:
            insights["improvements"].append("Actividad irregular en redes sociales")
        
        # Generar recomendaciones
        if not linkedin_present:
            insights["recommendations"].append("Crear perfil completo en LinkedIn")
        
        if low_engagement:
            insights["recommendations"].append("Incrementar interacción con contenido de la industria")
            insights["recommendations"].append("Publicar contenido más específico y valioso")
        
        if len(profiles) < 2:
            insights["recommendations"].append("Expandir presencia a otras plataformas relevantes")
        
        insights["recommendations"].append("Mantener consistencia en información de perfil")
        insights["recommendations"].append("Incrementar frecuencia de publicación de contenido profesional")
        
        return insights
    
    async def _calculate_analysis_confidence(self, profiles: List[SocialProfile], 
                                           content: List[SocialContent]) -> float:
        """Calcula el nivel de confianza del análisis."""
        
        confidence_factors = []
        
        # Factor 1: Número de plataformas analizadas
        platform_factor = min(1.0, len(profiles) / 4) * 25  # Máximo 4 plataformas
        confidence_factors.append(platform_factor)
        
        # Factor 2: Cantidad de contenido analizado
        content_factor = min(1.0, len(content) / 20) * 25  # Máximo 20 posts
        confidence_factors.append(content_factor)
        
        # Factor 3: Completitud de perfiles
        complete_profiles = sum(1 for p in profiles if p.bio and p.job_title)
        completeness_factor = (complete_profiles / len(profiles)) * 25 if profiles else 0
        confidence_factors.append(completeness_factor)
        
        # Factor 4: Recencia de datos
        recent_data = await self._assess_recent_activity(profiles, content)
        recency_factor = recent_data * 25
        confidence_factors.append(recency_factor)
        
        return sum(confidence_factors)
    
    def get_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        """Obtiene los resultados completos del análisis."""
        
        analysis = self.analyses.get(analysis_id)
        if not analysis:
            return {"error": "Analysis not found"}
        
        # Clasificar nivel de influencia
        influence_level = "Bajo"
        if analysis.overall_influence_score >= 80:
            influence_level = "Muy Alto"
        elif analysis.overall_influence_score >= 60:
            influence_level = "Alto"
        elif analysis.overall_influence_score >= 40:
            influence_level = "Medio"
        elif analysis.overall_influence_score >= 20:
            influence_level = "Bajo-Medio"
        
        # Clasificar credibilidad
        credibility_level = "Baja"
        if analysis.professional_credibility >= 80:
            credibility_level = "Muy Alta"
        elif analysis.professional_credibility >= 60:
            credibility_level = "Alta"
        elif analysis.professional_credibility >= 40:
            credibility_level = "Media"
        
        return {
            "analysis_id": analysis_id,
            "user_id": analysis.user_id,
            "summary": {
                "platforms_analyzed": len(analysis.profiles),
                "content_pieces": len(analysis.content_analyzed),
                "overall_influence_score": analysis.overall_influence_score,
                "influence_level": influence_level,
                "professional_credibility": analysis.professional_credibility,
                "credibility_level": credibility_level,
                "content_quality_score": analysis.content_quality_score,
                "network_strength": analysis.network_strength
            },
            "platforms": [
                {
                    "platform": p.platform.value,
                    "username": p.username,
                    "followers": p.followers_count,
                    "engagement_rate": p.engagement_rate,
                    "verified": p.verified
                } for p in analysis.profiles
            ],
            "sentiment_analysis": dict(analysis.sentiment_distribution),
            "network_metrics": {
                "size": analysis.network_size,
                "quality": analysis.network_quality,
                "industry_connections": dict(analysis.industry_connections)
            },
            "insights": {
                "strengths": analysis.strengths,
                "improvement_areas": analysis.improvement_areas,
                "recommendations": analysis.recommendations
            },
            "risk_assessment": {
                "red_flags": analysis.red_flags,
                "risk_indicators": analysis.risk_indicators
            },
            "confidence_score": analysis.confidence_score,
            "analysis_date": analysis.analysis_date.isoformat()
        }
    
    def get_influence_comparison(self, analysis_ids: List[str]) -> Dict[str, Any]:
        """Compara análisis de influencia entre múltiples usuarios."""
        
        comparisons = []
        
        for analysis_id in analysis_ids:
            analysis = self.analyses.get(analysis_id)
            if analysis:
                comparisons.append({
                    "user_id": analysis.user_id,
                    "influence_score": analysis.overall_influence_score,
                    "credibility_score": analysis.professional_credibility,
                    "network_size": analysis.network_size,
                    "platforms_count": len(analysis.profiles)
                })
        
        if not comparisons:
            return {"error": "No valid analyses found"}
        
        # Calcular estadísticas comparativas
        influence_scores = [c["influence_score"] for c in comparisons]
        credibility_scores = [c["credibility_score"] for c in comparisons]
        
        return {
            "comparison_data": comparisons,
            "statistics": {
                "avg_influence": statistics.mean(influence_scores),
                "max_influence": max(influence_scores),
                "min_influence": min(influence_scores),
                "avg_credibility": statistics.mean(credibility_scores),
                "max_credibility": max(credibility_scores),
                "min_credibility": min(credibility_scores)
            },
            "rankings": {
                "by_influence": sorted(comparisons, key=lambda x: x["influence_score"], reverse=True),
                "by_credibility": sorted(comparisons, key=lambda x: x["credibility_score"], reverse=True),
                "by_network_size": sorted(comparisons, key=lambda x: x["network_size"], reverse=True)
            }
        }

# Funciones de utilidad
async def quick_social_scan(user_identifier: str, platforms: List[str] = None) -> str:
    """Función de conveniencia para análisis social rápido."""
    
    engine = SocialLinkEngine()
    
    platform_enums = []
    if platforms:
        for platform_str in platforms:
            try:
                platform_enums.append(SocialPlatform(platform_str.lower()))
            except ValueError:
                continue
    
    return await engine.analyze_social_presence(user_identifier, platform_enums)

# Exportaciones
__all__ = [
    'SocialPlatform', 'ContentType', 'SentimentType', 'InfluenceLevel',
    'SocialProfile', 'SocialContent', 'NetworkConnection', 'InfluenceMetrics',
    'SocialAnalysis', 'SocialLinkEngine', 'quick_social_scan'
]