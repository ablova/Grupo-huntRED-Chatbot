# app/ml/aura/__init__.py
"""
Sistema Aura - Motor de Inteligencia Artificial Avanzada para Grupo huntRED®

Este módulo implementa el sistema Aura, un motor de IA que analiza la "aura" 
o compatibilidad holística entre candidatos y empresas, proporcionando 
recomendaciones inteligentes basadas en múltiples dimensiones de análisis.

Módulos implementados:
- Core: Motor principal de AURA
- Personalización: Adaptación dinámica a usuarios y contextos
- Upskilling: Análisis de gaps de skills y desarrollo profesional
- Networking: Matchmaking y conexiones inteligentes
- Analytics: Dashboards ejecutivos y métricas avanzadas
- Gamification: Sistema de logros y engagement
- Generative AI: Generación de contenido y simulaciones
- Organizational Analytics: Análisis organizacional y reporting
- Security: Privacidad y explicabilidad
- Ecosystem: API público y marketplace de módulos
- Monitoring: Monitoreo y alertas del sistema
- Cache: Sistema de caché inteligente
- Integration: Orquestador de integraciones
- Conversational: Chatbot avanzado
- Predictive: Análisis predictivo y forecasting
"""

# Core modules
from .core import AuraEngine
from .compatibility_engine import CompatibilityEngine
from .recommendation_engine import RecommendationEngine
from .energy_analyzer import EnergyAnalyzer
from .vibrational_matcher import VibrationalMatcher
from .holistic_assessor import HolisticAssessor
from .aura_metrics import AuraMetrics
from .graph_builder import AuraGraphBuilder
from .integration_layer import IntegrationLayer

# Personalization modules
from .personalization.personalization_engine import PersonalizationEngine
from .personalization.user_segmenter import UserSegmenter
from .personalization.context_analyzer import ContextAnalyzer
from .personalization.adaptive_engine import AdaptiveEngine

# Upskilling modules
from .upskilling.skill_gap_analyzer import SkillGapAnalyzer
from .upskilling.career_simulator import CareerSimulator
from .upskilling.market_alerts import MarketAlerts

# Networking modules
from .networking.network_matchmaker import NetworkMatchmaker
from .networking.auto_introducer import AutoIntroducer
from .networking.event_recommender import EventRecommender

# Analytics modules
from .analytics.executive_dashboard import ExecutiveDashboard
from .analytics.performance_metrics import PerformanceMetrics
from .analytics.trend_analyzer import TrendAnalyzer

# Gamification modules
from .gamification.achievement_system import AchievementSystem
from .gamification.impact_ranking import ImpactRanking
from .gamification.social_achievements import SocialAchievements

# Generative AI modules
from .generative.cv_generator import CVGenerator
from .generative.interview_simulator import InterviewSimulator
from .generative.auto_summarizer import AutoSummarizer

# Organizational Analytics modules
from .organizational.organizational_analytics import OrganizationalAnalytics

# Security modules
from .security.privacy_panel import PrivacyPanel
from .security.explainable_ai import ExplainableAI

# Ecosystem modules
from .ecosystem.public_api import PublicAPI
from .ecosystem.module_marketplace import ModuleMarketplace, module_marketplace

# Monitoring modules
from .monitoring.aura_monitor import AuraMonitor

# Cache modules
from .cache.intelligent_cache import IntelligentCache

# Integration modules
from .integration.aura_orchestrator import AuraOrchestrator

# Conversational modules
from .conversational.advanced_chatbot import AdvancedChatbot

# Predictive modules
from .predictive.sentiment_analyzer import SentimentAnalyzer
from .predictive.market_predictor import MarketPredictor
from .predictive.career_predictor import CareerPredictor

# API modules
from .api.endpoints import AuraAPIEndpoints

# Models modules
from .models.gnn_models import GNNModels

# Connectors modules
from .connectors.linkedin_connector import LinkedInConnector
from .connectors.icloud_connector import iCloudConnector

__all__ = [
    # Core
    'AuraEngine',
    'CompatibilityEngine', 
    'RecommendationEngine',
    'EnergyAnalyzer',
    'VibrationalMatcher',
    'HolisticAssessor',
    'AuraMetrics',
    'AuraGraphBuilder',
    'IntegrationLayer',
    
    # Personalization
    'PersonalizationEngine',
    'UserSegmenter',
    'ContextAnalyzer',
    'AdaptiveEngine',
    
    # Upskilling
    'SkillGapAnalyzer',
    'CareerSimulator',
    'MarketAlerts',
    
    # Networking
    'NetworkMatchmaker',
    'AutoIntroducer',
    'EventRecommender',
    
    # Analytics
    'ExecutiveDashboard',
    'PerformanceMetrics',
    'TrendAnalyzer',
    
    # Gamification
    'AchievementSystem',
    'ImpactRanking',
    'SocialAchievements',
    
    # Generative AI
    'CVGenerator',
    'InterviewSimulator',
    'AutoSummarizer',
    
    # Organizational Analytics
    'OrganizationalAnalytics',
    
    # Security
    'PrivacyPanel',
    'ExplainableAI',
    
    # Ecosystem
    'PublicAPI',
    'ModuleMarketplace',
    'module_marketplace',
    
    # Monitoring
    'AuraMonitor',
    
    # Cache
    'IntelligentCache',
    
    # Integration
    'AuraOrchestrator',
    
    # Conversational
    'AdvancedChatbot',
    
    # Predictive
    'SentimentAnalyzer',
    'MarketPredictor',
    'CareerPredictor',
    
    # API
    'AuraAPIEndpoints',
    
    # Models
    'GNNModels',
    
    # Connectors
    'LinkedInConnector',
    'iCloudConnector'
]

__version__ = '1.0.0'
__author__ = 'Grupo huntRED® AI Team' 