# app/ml/aura/__init__.py
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
from app.ml.analyzers.market.salary_analyzer import SalaryAnalyzer
from app.ml.analyzers.organizational_analytics.organizational_analytics import OrganizationalAnalytics
from app.ml.aura.analytics.custom_dashboard import CustomDashboard
from app.ml.aura.analytics.executive_dashboard import ExecutiveAnalytics
from app.ml.aura.analytics.performance_metrics import PerformanceMetrics
from app.ml.aura.analytics.sector_comparator import SectorComparator
from app.ml.aura.analytics.trend_analyzer import TrendAnalyzer
from app.ml.aura.aura import AuraEngine
from app.ml.aura.aura_metrics import AuraMetrics, MetricType, MetricCategory
from app.ml.aura.cache.intelligent_cache import IntelligentCache
from app.ml.aura.compatibility_engine import CompatibilityEngine
from app.ml.aura.core.bias_detection import BiasDetectionEngine
from app.ml.aura.core.ethics_engine import EthicsEngine, EthicsConfig, ServiceTier
from app.ml.aura.core.fairness_optimizer import FairnessOptimizer
from app.ml.aura.core.moral_reasoning import MoralReasoning
from app.ml.aura.ecosystem.public_api import PublicAPI
from app.ml.aura.ecosystem.module_marketplace import ModuleMarketplace
from app.ml.aura.energy_analyzer import EnergyAnalyzer, EnergyProfile, EnergyType, EnergyLevel
from app.ml.aura.gamification.achievement_system import AchievementSystem, BadgeRarity, AchievementType
from app.ml.aura.gamification.impact_ranking import ImpactRanking
from app.ml.aura.gamification.social_achievements import SocialAchievements
from app.ml.aura.generative.auto_summarizer import AutoSummarizer
from app.ml.aura.generative.cv_generator import CVGenerator
from app.ml.aura.generative.interview_simulator import InterviewSimulator
from app.ml.aura.graph_builder import AuraGraphBuilder
from app.ml.aura.holistic_assessor import HolisticAssessor
from app.ml.aura.impact.impact_analyzer import ImpactAnalyzer
from app.ml.aura.impact.sustainability_calculator import SustainabilityCalculator
from app.ml.aura.integration_layer import AuraIntegrationLayer
# Crear alias para IntegrationLayer
IntegrationLayer = AuraIntegrationLayer
from app.ml.aura.monitoring.aura_monitor import AuraMonitor
from app.ml.aura.networking.auto_introducer import AutoIntroducer
from app.ml.aura.networking.event_recommender import EventRecommender
from app.ml.aura.networking.network_matchmaker import NetworkMatchmaker
# Crear alias para Matchmaker
Matchmaker = NetworkMatchmaker
from app.ml.aura.orchestrator import AuraOrchestrator, AuraOrchestratorConfig, AuraOrchestratorState, AuraOrchestratorEvent, AuraOrchestratorAction
from app.ml.aura.organizational.bu_insights import BUInsights
from app.ml.aura.organizational.network_analyzer import NetworkAnalyzer
from app.ml.aura.organizational.reporting_engine import ReportingEngine
from app.ml.aura.payroll_overhead_integration import AuraPayrollOverheadIntegration
from app.ml.aura.personalization.adaptive_engine import AdaptiveEngine
from app.ml.aura.personalization.context_analyzer import ContextAnalyzer
from app.ml.aura.personalization.personalization_engine import PersonalizationEngine
from app.ml.aura.personalization.user_segmenter import UserSegmenter
from app.ml.aura.predictive.career_predictor import CareerPrediction, CareerMovementPredictor, MarketTrend
from app.ml.aura.predictive.market_predictor import MarketPrediction
from app.ml.aura.predictive.predictive_analytics_service import PredictiveAnalyticsService
from app.ml.aura.predictive.sentiment_analyzer import SentimentAnalyzer
from app.ml.aura.quantum_predictor import QuantumCandidatePredictor as QuantumAnalyzer
from app.ml.aura.recommendation_engine import RecommendationEngine, RecommendationType, RecommendationPriority
from app.ml.aura.security.explainable_ai import ExplainableAI
from app.ml.aura.security.privacy_panel import PrivacyPanel
from app.ml.aura.social.influence_calculator import InfluenceCalculator
from app.ml.aura.social.social_verifier import SocialVerifier
from app.ml.aura.truth.anomaly_detector import AnomalyDetector
from app.ml.aura.truth.consistency_checker import ConsistencyChecker
from app.ml.aura.truth.truth_analyzer import TruthAnalyzer
from app.ml.aura.upskilling.career_simulator import CareerSimulator
from app.ml.aura.upskilling.market_alerts import MarketAlerts
from app.ml.aura.upskilling.skill_gap_analyzer import SkillGapAnalyzer
# La siguiente importación parece estar mal ubicada
# from app.ml.aura.upskilling.aura_metrics import AuraMetric, MetricAggregation
from app.ml.aura.aura_metrics import AuraMetric, MetricAggregation
from app.ml.aura.vibrational_matcher import VibrationalMatcher

__version__ = "1.0.0"
__author__ = "Grupo huntRED"
__description__ = "Sistema de IA ética y responsable para toma de decisiones AURA"

__all__ = [
    'AchievementSystem',
    'AdaptiveEngine',
    'AnomalyDetector',
    'AuraEngine',
    'AuraGraphBuilder',
    'AuraIntegrationLayer',
    'IntegrationLayer',  # Alias para AuraIntegrationLayer
    'AuraMetric',
    'AuraMetrics',
    'AuraMonitor',
    'AuraPayrollOverheadIntegration',
    'AuraOrchestrator',
    'AuraOrchestratorAction',
    'AuraOrchestratorConfig',
    'AuraOrchestratorEvent',
    'AuraOrchestratorState',
    'AutoIntroducer',
    'AutoSummarizer',
    'BadgeRarity',
    'BiasDetectionEngine',
    'BUInsights',
    'CareerMovementPredictor',
    'MarketTrend',
    'CareerSimulator',
    'CompatibilityEngine',
    'ConsistencyChecker',
    'ContextAnalyzer',
    'CustomDashboard',
    'CVGenerator',
    'EnergyAnalyzer',
    'EnergyLevel',
    'EnergyProfile',
    'EnergyType',
    'EthicsConfig',
    'EthicsEngine',
    'EventRecommender',
    'ExecutiveAnalytics',
    'ExplainableAI',
    'FairnessOptimizer',
    'HolisticAssessor',
    'ImpactAnalyzer',
    'ImpactRanking',
    'InfluenceCalculator',
    'IntelligentCache',
    'InterviewSimulator',
    'MarketAlerts',
    'MarketPrediction',
    'ModuleMarketplace',
    'MetricAggregation',
    'MetricCategory',
    'MetricType',
    'MoralReasoning',
    'NetworkAnalyzer',
    'NetworkMatchmaker',
    'OrganizationalAnalytics',
    'PerformanceMetrics',
    'PersonalizationEngine',
    'PredictiveAnalyticsService',
    'PrivacyPanel',
    'PublicAPI',
    'QuantumAnalyzer',
    'RecommendationEngine',
    'RecommendationPriority',
    'RecommendationType',
    'ReportingEngine',
    'SalaryAnalyzer',
    'SectorComparator',
    'SentimentAnalyzer',
    'ServiceTier',
    'SkillGapAnalyzer',
    'SocialAchievements',
    'SocialVerifier',
    'SustainabilityCalculator',
    'TrendAnalyzer',
    'TruthAnalyzer',
    'UserSegmenter',
    'VibrationalMatcher',
    'CareerPrediction',
]