"""
AURA - Advanced Unified Reasoning Assistant
Sistema completo de IA ética y responsable para toma de decisiones.

Características principales:
- Motor ético con múltiples marcos de razonamiento
- TruthSense™ para análisis de veracidad
- SocialVerify™ para verificación social
- Detección y mitigación de sesgos
- Optimización de equidad
- Análisis de impacto social
- Orquestación inteligente de módulos
- Control de recursos y escalabilidad
"""

from app.ml.aura.core.ethics_engine import EthicsEngine, EthicsConfig, ServiceTier
from app.ml.aura.core.moral_reasoning import MoralReasoning
from app.ml.aura.core.bias_detection import BiasDetectionEngine
from app.ml.aura.core.fairness_optimizer import FairnessOptimizer
from app.ml.aura.truth.truth_analyzer import TruthAnalyzer
from app.ml.aura.social.social_verifier import SocialVerifier
from app.ml.aura.impact.impact_analyzer import ImpactAnalyzer
from app.ml.aura.orchestrator import AURAOrchestrator, AuraOrchestratorConfig, AuraOrchestratorState, AuraOrchestratorEvent, AuraOrchestratorAction
from app.ml.aura.aura import AuraEngine
from app.ml.aura.compatibility_engine import CompatibilityEngine
from app.ml.aura.recommendation_engine import RecommendationEngine, RecommendationType, RecommendationPriority
from app.ml.aura.energy_analyzer import EnergyAnalyzer, EnergyProfile, EnergyType, EnergyLevel
from app.ml.aura.vibrational_matcher import VibrationalMatcher
from app.ml.aura.holistic_assessor import HolisticAssessor
from app.ml.aura.aura_metrics import AuraMetrics, MetricType, MetricCategory
from app.ml.aura.graph_builder import AuraGraphBuilder
from app.ml.aura.integration_layer import AuraIntegrationLayer
from app.ml.aura.personalization.user_segmenter import UserSegmenter
from app.ml.aura.personalization.context_analyzer import ContextAnalyzer
from app.ml.aura.personalization.adaptive_engine import AdaptiveEngine
from app.ml.aura.personalization.personalization_engine import PersonalizationEngine
from app.ml.aura.upskilling.skill_gap_analyzer import SkillGapAnalyzer
from app.ml.aura.upskilling.career_simulator import CareerSimulator
from app.ml.aura.upskilling.market_alerts import MarketAlerts
from app.ml.aura.networking.network_matchmaker import NetworkMatchmaker
from app.ml.aura.networking.auto_introducer import AutoIntroducer
from app.ml.aura.networking.event_recommender import EventRecommender
from app.ml.aura.analytics.executive_dashboard import ExecutiveAnalytics
from app.ml.aura.analytics.performance_metrics import PerformanceMetrics
from app.ml.aura.analytics.trend_analyzer import TrendAnalyzer
from app.ml.aura.gamification.achievement_system import AchievementSystem

__version__ = "1.0.0"
__author__ = "Grupo huntRED"
__description__ = "Sistema de IA ética y responsable para toma de decisiones AURA"

__all__ = [
    'EthicsEngine',
    'EthicsConfig', 
    'ServiceTier',
    'MoralReasoning',
    'BiasDetectionEngine',
    'FairnessOptimizer',
    'TruthAnalyzer',
    'SocialVerifier',
    'ImpactAnalyzer',
    'AURAOrchestrator',
    'AuraOrchestratorConfig',
    'AuraOrchestratorState',
    'AuraOrchestratorEvent',
    'AuraOrchestratorAction',
    'AuraEngine',
    'CompatibilityEngine',
    'RecommendationEngine',
    'RecommendationType',
    'RecommendationPriority',
    'EnergyAnalyzer',
    'EnergyProfile',
    'EnergyType',
    'EnergyLevel',
    'VibrationalMatcher',
    'HolisticAssessor',
    'AuraMetrics',
    'MetricType',
    'MetricCategory',
    'AuraGraphBuilder',
    'AuraIntegrationLayer',
    'UserSegmenter',
    'ContextAnalyzer',
    'AdaptiveEngine',
    'PersonalizationEngine',
    'SkillGapAnalyzer',
    'CareerSimulator',
    'MarketAlerts',
    'NetworkMatchmaker',
    'AutoIntroducer',
    'EventRecommender',
    'ExecutiveAnalytics',
    'PerformanceMetrics',
    'TrendAnalyzer',
    'AchievementSystem'
]
