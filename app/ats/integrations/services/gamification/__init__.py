# app/ats/integrations/services/gamification/__init__.py
"""
GAMIFICATION SERVICES - Grupo huntRED®
Servicios avanzados de gamificación con analytics predictivo
"""

from app.ats.integrations.services.gamification.predictive_analytics import PredictiveGamificationAnalytics, predictive_analytics

__all__ = [
    'PredictiveGamificationAnalytics',
    'predictive_analytics'
] 