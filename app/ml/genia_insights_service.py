"""
Servicio centralizador de insights y métricas de GenIA (Grupo huntRED®)
"""
from app.ml.analyzers import *
from app.ml.metrics import *
from app.ml.feedback import *
from app.ml.data import *
from app.ml.monitoring import *
from app.ml.training import *
from app.ml.validation import *
from app.ml.onboarding_processor import OnboardingProcessor
from app.ml.notification_analyzer import NotificationAnalyzer
from app.ml.ml_config import MLConfig
from app.ml.ml_opt import MLOptimizer
from app.ml.revolutionary_config import *

from typing import Dict, Any, List, Optional

class GeniaInsightsService:
    """
    Servicio para centralizar y exponer insights y métricas de GenIA.
    """
    def __init__(self, business_unit=None):
        self.business_unit = business_unit
        # Instanciar analyzers y módulos relevantes
        self.analyzers = self._load_analyzers()
        self.feedback = FeedbackProcessor()
        self.metrics = MetricsCalculator()
        self.onboarding = OnboardingProcessor()
        self.notification_analyzer = NotificationAnalyzer()
        # ...otros módulos relevantes

    def _load_analyzers(self):
        # Instanciar todos los analyzers relevantes
        from app.ml.analyzers.cultural_analyzer import CulturalAnalyzer
        from app.ml.analyzers.professional_analyzer import ProfessionalAnalyzer
        from app.ml.analyzers.integrated_analyzer import IntegratedAnalyzer
        from app.ml.analyzers.talent_analyzer import TalentAnalyzer
        from app.ml.analyzers.salary_analyzer import SalaryAnalyzer
        from app.ml.analyzers.generational_analyzer import GenerationalAnalyzer
        from app.ml.analyzers.dei_analyzer import DEIAnalyzer
        from app.ml.analyzers.intervention_analyzer import InterventionAnalyzerImpl
        from app.ml.analyzers.scraping_ml_analyzer import ScrapingMLAnalyzer
        return {
            'cultural': CulturalAnalyzer(),
            'professional': ProfessionalAnalyzer(),
            'integrated': IntegratedAnalyzer(),
            'talent': TalentAnalyzer(),
            'salary': SalaryAnalyzer(),
            'generational': GenerationalAnalyzer(),
            'dei': DEIAnalyzer(),
            'intervention': InterventionAnalyzerImpl(),
            'scraping': ScrapingMLAnalyzer(),
        }

    def get_all_insights(self) -> Dict[str, Any]:
        """
        Devuelve todos los insights y métricas relevantes agrupados por categoría/analyzer.
        """
        insights = {}
        for key, analyzer in self.analyzers.items():
            try:
                if hasattr(analyzer, 'get_dashboard_insights'):
                    insights[key] = analyzer.get_dashboard_insights(self.business_unit)
                elif hasattr(analyzer, 'generate_dashboard_insights'):
                    insights[key] = analyzer.generate_dashboard_insights(self.business_unit)
                else:
                    insights[key] = {}
            except Exception as e:
                insights[key] = {'error': str(e)}
        # Feedback, métricas, onboarding, notificaciones, universidades, etc.
        try:
            insights['feedback'] = self.feedback.get_dashboard_metrics(self.business_unit)
        except Exception as e:
            insights['feedback'] = {'error': str(e)}
        try:
            insights['metrics'] = self.metrics.get_dashboard_metrics(self.business_unit)
        except Exception as e:
            insights['metrics'] = {'error': str(e)}
        try:
            insights['onboarding'] = self.onboarding.get_dashboard_insights(self.business_unit)
        except Exception as e:
            insights['onboarding'] = {'error': str(e)}
        try:
            insights['notifications'] = self.notification_analyzer.get_dashboard_metrics(self.business_unit)
        except Exception as e:
            insights['notifications'] = {'error': str(e)}
        # Pincelada de Rotación y Habilidades Emergentes (AURA)
        insights['rotacion'] = {'resumen': 'Análisis avanzado de riesgo de rotación disponible en AURA. Solicita acceso para visualización completa.'}
        insights['habilidades_emergentes'] = {'resumen': 'Detección de skills emergentes y gaps disponible en AURA. Solicita acceso para visualización completa.'}
        # Hooks para clima, capacitación, innovación
        insights['clima_organizacional'] = {'resumen': 'Próximamente: análisis de clima organizacional cuando haya suficiente data.'}
        insights['capacitacion'] = {'resumen': 'Próximamente: análisis de efectividad de capacitación.'}
        insights['innovacion'] = {'resumen': 'Próximamente: análisis de innovación y colaboración.'}
        return insights

    def get_insights_by_category(self, category: str) -> Any:
        """
        Devuelve insights de una categoría/analyzer específica.
        """
        return self.get_all_insights().get(category, {})

    def get_summary(self) -> Dict[str, Any]:
        """
        Devuelve un resumen ejecutivo de los insights más relevantes.
        """
        all_insights = self.get_all_insights()
        summary = {}
        # Ejemplo: extraer los insights clave de cada analyzer
        for key, value in all_insights.items():
            if isinstance(value, dict) and 'summary' in value:
                summary[key] = value['summary']
            elif isinstance(value, list):
                summary[key] = value[:3]  # Top 3 insights
            else:
                summary[key] = value
        return summary 