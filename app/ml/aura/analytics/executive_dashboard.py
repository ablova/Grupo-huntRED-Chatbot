"""
AURA - Analytics Ejecutivo Avanzado
Executive Dashboard & Business Intelligence
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from collections import defaultdict
import json
from app.ml.aura.graph_builder import GNNManager

logger = logging.getLogger(__name__)


@dataclass
class KPIMetric:
    """Métrica KPI ejecutiva"""
    name: str
    value: float
    target: float
    unit: str
    trend: str  # 'up', 'down', 'stable'
    change_percentage: float
    status: str  # 'excellent', 'good', 'warning', 'critical'
    category: str
    description: str
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class BusinessInsight:
    """Insight de negocio"""
    id: str
    title: str
    description: str
    category: str
    impact: str  # 'high', 'medium', 'low'
    confidence: float
    data_points: List[Dict[str, Any]]
    recommendations: List[str]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MarketAnalysis:
    """Análisis de mercado"""
    industry: str
    location: str
    growth_rate: float
    market_size: float
    key_trends: List[str]
    opportunities: List[str]
    threats: List[str]
    competitive_landscape: Dict[str, Any]
    forecast: Dict[str, float]


class ExecutiveAnalytics:
    """
    Sistema de analytics ejecutivo para toma de decisiones estratégicas
    """
    
    def __init__(self):
        self.kpi_metrics = {}
        self.business_insights = []
        self.market_analyses = {}
        self.performance_data = defaultdict(list)
        self.alert_thresholds = self._initialize_thresholds()
        self.gnn = GNNManager()
        self.last_dashboards = {}
    
    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Inicializa umbrales de alerta para KPIs"""
        return {
            "network_growth": {
                "critical": 0.05,
                "warning": 0.10,
                "good": 0.20,
                "excellent": 0.30
            },
            "influence_score": {
                "critical": 0.3,
                "warning": 0.5,
                "good": 0.7,
                "excellent": 0.9
            },
            "engagement_rate": {
                "critical": 0.02,
                "warning": 0.05,
                "good": 0.10,
                "excellent": 0.20
            },
            "retention_rate": {
                "critical": 0.70,
                "warning": 0.80,
                "good": 0.90,
                "excellent": 0.95
            },
            "revenue_per_user": {
                "critical": 50,
                "warning": 100,
                "good": 200,
                "excellent": 500
            }
        }
    
    def calculate_executive_kpis(self, network_data: Dict[str, Any]) -> Dict[str, KPIMetric]:
        """
        Calcula KPIs ejecutivos clave
        """
        kpis = {}
        
        # KPI: Crecimiento de Red
        network_growth = self._calculate_network_growth(network_data)
        kpis["network_growth"] = KPIMetric(
            name="Crecimiento de Red",
            value=network_growth["current"],
            target=network_growth["target"],
            unit="usuarios/mes",
            trend=network_growth["trend"],
            change_percentage=network_growth["change_percentage"],
            status=self._get_kpi_status("network_growth", network_growth["current"]),
            category="growth",
            description="Tasa de crecimiento mensual de la red profesional"
        )
        
        # KPI: Score de Influencia Promedio
        influence_score = self._calculate_influence_score(network_data)
        kpis["influence_score"] = KPIMetric(
            name="Score de Influencia",
            value=influence_score["current"],
            target=influence_score["target"],
            unit="score",
            trend=influence_score["trend"],
            change_percentage=influence_score["change_percentage"],
            status=self._get_kpi_status("influence_score", influence_score["current"]),
            category="quality",
            description="Score promedio de influencia de los usuarios"
        )
        
        # KPI: Tasa de Engagement
        engagement_rate = self._calculate_engagement_rate(network_data)
        kpis["engagement_rate"] = KPIMetric(
            name="Tasa de Engagement",
            value=engagement_rate["current"],
            target=engagement_rate["target"],
            unit="%",
            trend=engagement_rate["trend"],
            change_percentage=engagement_rate["change_percentage"],
            status=self._get_kpi_status("engagement_rate", engagement_rate["current"]),
            category="engagement",
            description="Porcentaje de usuarios activos mensualmente"
        )
        
        # KPI: Tasa de Retención
        retention_rate = self._calculate_retention_rate(network_data)
        kpis["retention_rate"] = KPIMetric(
            name="Tasa de Retención",
            value=retention_rate["current"],
            target=retention_rate["target"],
            unit="%",
            trend=retention_rate["trend"],
            change_percentage=retention_rate["change_percentage"],
            status=self._get_kpi_status("retention_rate", retention_rate["current"]),
            category="retention",
            description="Porcentaje de usuarios que permanecen activos"
        )
        
        # KPI: Ingresos por Usuario
        revenue_per_user = self._calculate_revenue_per_user(network_data)
        kpis["revenue_per_user"] = KPIMetric(
            name="Ingresos por Usuario",
            value=revenue_per_user["current"],
            target=revenue_per_user["target"],
            unit="$",
            trend=revenue_per_user["trend"],
            change_percentage=revenue_per_user["change_percentage"],
            status=self._get_kpi_status("revenue_per_user", revenue_per_user["current"]),
            category="revenue",
            description="Ingresos promedio generados por usuario"
        )
        
        # KPI: Calidad de Red
        network_quality = self._calculate_network_quality(network_data)
        kpis["network_quality"] = KPIMetric(
            name="Calidad de Red",
            value=network_quality["current"],
            target=network_quality["target"],
            unit="score",
            trend=network_quality["trend"],
            change_percentage=network_quality["change_percentage"],
            status=self._get_kpi_status("influence_score", network_quality["current"]),
            category="quality",
            description="Score de calidad general de la red"
        )
        
        # KPI: Eficiencia de Matching
        matching_efficiency = self._calculate_matching_efficiency(network_data)
        kpis["matching_efficiency"] = KPIMetric(
            name="Eficiencia de Matching",
            value=matching_efficiency["current"],
            target=matching_efficiency["target"],
            unit="%",
            trend=matching_efficiency["trend"],
            change_percentage=matching_efficiency["change_percentage"],
            status=self._get_kpi_status("engagement_rate", matching_efficiency["current"]),
            category="efficiency",
            description="Porcentaje de matches exitosos"
        )
        
        self.kpi_metrics = kpis
        return kpis
    
    def _calculate_network_growth(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula métricas de crecimiento de red"""
        current_users = network_data.get("total_users", 1000)
        previous_users = network_data.get("previous_users", 950)
        target_growth = 0.15  # 15% mensual
        
        growth_rate = (current_users - previous_users) / previous_users if previous_users > 0 else 0
        target_users = previous_users * (1 + target_growth)
        
        return {
            "current": current_users - previous_users,
            "target": target_users - previous_users,
            "trend": "up" if growth_rate > 0 else "down" if growth_rate < 0 else "stable",
            "change_percentage": growth_rate * 100
        }
    
    def _calculate_influence_score(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula score de influencia promedio"""
        current_score = network_data.get("avg_influence_score", 0.65)
        previous_score = network_data.get("previous_influence_score", 0.62)
        target_score = 0.75
        
        change_percentage = ((current_score - previous_score) / previous_score * 100) if previous_score > 0 else 0
        
        return {
            "current": current_score,
            "target": target_score,
            "trend": "up" if current_score > previous_score else "down" if current_score < previous_score else "stable",
            "change_percentage": change_percentage
        }
    
    def _calculate_engagement_rate(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula tasa de engagement"""
        active_users = network_data.get("active_users", 750)
        total_users = network_data.get("total_users", 1000)
        previous_rate = network_data.get("previous_engagement_rate", 0.08)
        target_rate = 0.12
        
        current_rate = active_users / total_users if total_users > 0 else 0
        change_percentage = ((current_rate - previous_rate) / previous_rate * 100) if previous_rate > 0 else 0
        
        return {
            "current": current_rate * 100,
            "target": target_rate * 100,
            "trend": "up" if current_rate > previous_rate else "down" if current_rate < previous_rate else "stable",
            "change_percentage": change_percentage
        }
    
    def _calculate_retention_rate(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula tasa de retención"""
        retained_users = network_data.get("retained_users", 850)
        total_users = network_data.get("total_users", 1000)
        previous_rate = network_data.get("previous_retention_rate", 0.85)
        target_rate = 0.92
        
        current_rate = retained_users / total_users if total_users > 0 else 0
        change_percentage = ((current_rate - previous_rate) / previous_rate * 100) if previous_rate > 0 else 0
        
        return {
            "current": current_rate * 100,
            "target": target_rate * 100,
            "trend": "up" if current_rate > previous_rate else "down" if current_rate < previous_rate else "stable",
            "change_percentage": change_percentage
        }
    
    def _calculate_revenue_per_user(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula ingresos por usuario"""
        total_revenue = network_data.get("total_revenue", 150000)
        total_users = network_data.get("total_users", 1000)
        previous_rpu = network_data.get("previous_rpu", 140)
        target_rpu = 200
        
        current_rpu = total_revenue / total_users if total_users > 0 else 0
        change_percentage = ((current_rpu - previous_rpu) / previous_rpu * 100) if previous_rpu > 0 else 0
        
        return {
            "current": current_rpu,
            "target": target_rpu,
            "trend": "up" if current_rpu > previous_rpu else "down" if current_rpu < previous_rpu else "stable",
            "change_percentage": change_percentage
        }
    
    def _calculate_network_quality(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula calidad general de la red"""
        avg_connections = network_data.get("avg_connections", 45)
        avg_influence = network_data.get("avg_influence_score", 0.65)
        avg_activity = network_data.get("avg_activity_score", 0.7)
        
        # Score compuesto de calidad
        current_quality = (avg_connections / 100 + avg_influence + avg_activity) / 3
        previous_quality = network_data.get("previous_quality", 0.6)
        target_quality = 0.8
        
        change_percentage = ((current_quality - previous_quality) / previous_quality * 100) if previous_quality > 0 else 0
        
        return {
            "current": current_quality,
            "target": target_quality,
            "trend": "up" if current_quality > previous_quality else "down" if current_quality < previous_quality else "stable",
            "change_percentage": change_percentage
        }
    
    def _calculate_matching_efficiency(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula eficiencia de matching"""
        successful_matches = network_data.get("successful_matches", 180)
        total_attempts = network_data.get("total_match_attempts", 250)
        previous_efficiency = network_data.get("previous_matching_efficiency", 0.65)
        target_efficiency = 0.80
        
        current_efficiency = successful_matches / total_attempts if total_attempts > 0 else 0
        change_percentage = ((current_efficiency - previous_efficiency) / previous_efficiency * 100) if previous_efficiency > 0 else 0
        
        return {
            "current": current_efficiency * 100,
            "target": target_efficiency * 100,
            "trend": "up" if current_efficiency > previous_efficiency else "down" if current_efficiency < previous_efficiency else "stable",
            "change_percentage": change_percentage
        }
    
    def _get_kpi_status(self, kpi_name: str, value: float) -> str:
        """Determina el estado de un KPI basado en umbrales"""
        thresholds = self.alert_thresholds.get(kpi_name, {})
        
        if value >= thresholds.get("excellent", float('inf')):
            return "excellent"
        elif value >= thresholds.get("good", float('inf')):
            return "good"
        elif value >= thresholds.get("warning", float('inf')):
            return "warning"
        else:
            return "critical"
    
    def generate_business_insights(self, network_data: Dict[str, Any]) -> List[BusinessInsight]:
        """
        Genera insights de negocio basados en datos de red
        """
        insights = []
        
        # Insight: Crecimiento de Red
        if network_data.get("growth_rate", 0) > 0.2:
            insights.append(BusinessInsight(
                id="high_growth_opportunity",
                title="Oportunidad de Crecimiento Acelerado",
                description="La red está creciendo a una tasa superior al 20% mensual, indicando fuerte demanda del mercado",
                category="growth",
                impact="high",
                confidence=0.85,
                data_points=[
                    {"metric": "growth_rate", "value": network_data.get("growth_rate", 0)},
                    {"metric": "new_users", "value": network_data.get("new_users", 0)}
                ],
                recommendations=[
                    "Aumentar inversión en marketing digital",
                    "Expandir a nuevos mercados geográficos",
                    "Optimizar proceso de onboarding"
                ]
            ))
        
        # Insight: Engagement Bajo
        if network_data.get("engagement_rate", 0) < 0.05:
            insights.append(BusinessInsight(
                id="low_engagement_risk",
                title="Riesgo de Bajo Engagement",
                description="La tasa de engagement está por debajo del 5%, indicando posible pérdida de usuarios",
                category="engagement",
                impact="high",
                confidence=0.90,
                data_points=[
                    {"metric": "engagement_rate", "value": network_data.get("engagement_rate", 0)},
                    {"metric": "churn_rate", "value": network_data.get("churn_rate", 0)}
                ],
                recommendations=[
                    "Implementar programa de re-engagement",
                    "Mejorar experiencia de usuario",
                    "Añadir funcionalidades gamificadas"
                ]
            ))
        
        # Insight: Alta Calidad de Red
        if network_data.get("avg_influence_score", 0) > 0.8:
            insights.append(BusinessInsight(
                id="high_network_quality",
                title="Excelente Calidad de Red",
                description="La red tiene un score de influencia promedio superior al 80%",
                category="quality",
                impact="medium",
                confidence=0.75,
                data_points=[
                    {"metric": "avg_influence_score", "value": network_data.get("avg_influence_score", 0)},
                    {"metric": "avg_connections", "value": network_data.get("avg_connections", 0)}
                ],
                recommendations=[
                    "Leverage high-quality network for premium features",
                    "Implementar programa de referidos premium",
                    "Desarrollar funcionalidades para influenciadores"
                ]
            ))
        
        # Insight: Oportunidad de Monetización
        if network_data.get("revenue_per_user", 0) < 100:
            insights.append(BusinessInsight(
                id="monetization_opportunity",
                title="Oportunidad de Monetización",
                description="Los ingresos por usuario están por debajo del objetivo, indicando oportunidad de mejora",
                category="revenue",
                impact="high",
                confidence=0.80,
                data_points=[
                    {"metric": "revenue_per_user", "value": network_data.get("revenue_per_user", 0)},
                    {"metric": "conversion_rate", "value": network_data.get("conversion_rate", 0)}
                ],
                recommendations=[
                    "Optimizar estrategia de precios",
                    "Desarrollar nuevos productos premium",
                    "Mejorar funnel de conversión"
                ]
            ))
        
        # Insight: Eficiencia de Matching
        if network_data.get("matching_efficiency", 0) > 0.75:
            insights.append(BusinessInsight(
                id="high_matching_efficiency",
                title="Alta Eficiencia de Matching",
                description="El sistema de matching está funcionando excepcionalmente bien",
                category="efficiency",
                impact="medium",
                confidence=0.85,
                data_points=[
                    {"metric": "matching_efficiency", "value": network_data.get("matching_efficiency", 0)},
                    {"metric": "user_satisfaction", "value": network_data.get("user_satisfaction", 0)}
                ],
                recommendations=[
                    "Promocionar éxito del matching en marketing",
                    "Optimizar algoritmo para mayor precisión",
                    "Expandir funcionalidades de matching"
                ]
            ))
        
        self.business_insights = insights
        return insights
    
    def generate_market_analysis(self, industry: str, location: str) -> MarketAnalysis:
        """
        Genera análisis de mercado para una industria y ubicación específicas
        """
        # Simulación de datos de mercado
        market_data = {
            "tech": {
                "growth_rate": 0.15,
                "market_size": 5000000000,  # 5B USD
                "key_trends": [
                    "Adopción acelerada de IA/ML",
                    "Crecimiento del trabajo remoto",
                    "Demanda de habilidades cloud"
                ],
                "opportunities": [
                    "Expansión a mercados emergentes",
                    "Desarrollo de productos SaaS",
                    "Servicios de consultoría especializada"
                ],
                "threats": [
                    "Competencia de grandes tech companies",
                    "Cambios regulatorios",
                    "Escasez de talento calificado"
                ]
            }
        }
        
        industry_data = market_data.get(industry, market_data["tech"])
        
        return MarketAnalysis(
            industry=industry,
            location=location,
            growth_rate=industry_data["growth_rate"],
            market_size=industry_data["market_size"],
            key_trends=industry_data["key_trends"],
            opportunities=industry_data["opportunities"],
            threats=industry_data["threats"],
            competitive_landscape={
                "major_players": ["LinkedIn", "Indeed", "Glassdoor"],
                "market_share": {"LinkedIn": 0.45, "Indeed": 0.25, "Others": 0.30},
                "competitive_advantages": ["AI-powered matching", "Professional focus", "Quality network"]
            },
            forecast={
                "next_quarter": industry_data["growth_rate"] * 1.1,
                "next_year": industry_data["growth_rate"] * 1.2,
                "next_3_years": industry_data["growth_rate"] * 1.5
            }
        )
    
    def generate_executive_report(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera reporte ejecutivo completo
        """
        # Calcular KPIs
        kpis = self.calculate_executive_kpis(network_data)
        
        # Generar insights
        insights = self.generate_business_insights(network_data)
        
        # Análisis de mercado
        market_analysis = self.generate_market_analysis("tech", "global")
        
        # Resumen ejecutivo
        summary = {
            "overall_performance": self._calculate_overall_performance(kpis),
            "key_achievements": self._identify_key_achievements(kpis),
            "critical_issues": self._identify_critical_issues(kpis, insights),
            "strategic_recommendations": self._generate_strategic_recommendations(insights)
        }
        
        return {
            "report_date": datetime.now().isoformat(),
            "summary": summary,
            "kpis": {k: self._kpi_to_dict(v) for k, v in kpis.items()},
            "insights": [self._insight_to_dict(i) for i in insights],
            "market_analysis": self._market_analysis_to_dict(market_analysis),
            "performance_trends": self._generate_performance_trends(network_data),
            "forecast": self._generate_forecast(network_data)
        }
    
    def _calculate_overall_performance(self, kpis: Dict[str, KPIMetric]) -> str:
        """Calcula rendimiento general basado en KPIs"""
        excellent_count = sum(1 for kpi in kpis.values() if kpi.status == "excellent")
        good_count = sum(1 for kpi in kpis.values() if kpi.status == "good")
        total_kpis = len(kpis)
        
        if excellent_count / total_kpis >= 0.5:
            return "excellent"
        elif (excellent_count + good_count) / total_kpis >= 0.7:
            return "good"
        else:
            return "needs_improvement"
    
    def _identify_key_achievements(self, kpis: Dict[str, KPIMetric]) -> List[str]:
        """Identifica logros clave"""
        achievements = []
        for kpi in kpis.values():
            if kpi.status in ["excellent", "good"] and kpi.change_percentage > 0:
                achievements.append(f"{kpi.name}: {kpi.change_percentage:.1f}% de mejora")
        return achievements[:3]  # Top 3
    
    def _identify_critical_issues(self, kpis: Dict[str, KPIMetric], insights: List[BusinessInsight]) -> List[str]:
        """Identifica problemas críticos"""
        issues = []
        for kpi in kpis.values():
            if kpi.status == "critical":
                issues.append(f"{kpi.name}: {kpi.value} (objetivo: {kpi.target})")
        
        for insight in insights:
            if insight.impact == "high" and "risk" in insight.title.lower():
                issues.append(insight.title)
        
        return issues[:3]  # Top 3
    
    def _generate_strategic_recommendations(self, insights: List[BusinessInsight]) -> List[str]:
        """Genera recomendaciones estratégicas"""
        recommendations = []
        for insight in insights:
            if insight.impact == "high":
                recommendations.extend(insight.recommendations[:2])
        
        return list(set(recommendations))[:5]  # Top 5 únicos
    
    def _kpi_to_dict(self, kpi: KPIMetric) -> Dict[str, Any]:
        """Convierte KPI a diccionario"""
        return {
            "name": kpi.name,
            "value": kpi.value,
            "target": kpi.target,
            "unit": kpi.unit,
            "trend": kpi.trend,
            "change_percentage": kpi.change_percentage,
            "status": kpi.status,
            "category": kpi.category,
            "description": kpi.description
        }
    
    def _insight_to_dict(self, insight: BusinessInsight) -> Dict[str, Any]:
        """Convierte insight a diccionario"""
        return {
            "id": insight.id,
            "title": insight.title,
            "description": insight.description,
            "category": insight.category,
            "impact": insight.impact,
            "confidence": insight.confidence,
            "data_points": insight.data_points,
            "recommendations": insight.recommendations
        }
    
    def _market_analysis_to_dict(self, analysis: MarketAnalysis) -> Dict[str, Any]:
        """Convierte análisis de mercado a diccionario"""
        return {
            "industry": analysis.industry,
            "location": analysis.location,
            "growth_rate": analysis.growth_rate,
            "market_size": analysis.market_size,
            "key_trends": analysis.key_trends,
            "opportunities": analysis.opportunities,
            "threats": analysis.threats,
            "competitive_landscape": analysis.competitive_landscape,
            "forecast": analysis.forecast
        }
    
    def _generate_performance_trends(self, network_data: Dict[str, Any]) -> Dict[str, List[float]]:
        """Genera tendencias de rendimiento"""
        # Simulación de datos históricos
        months = 12
        trends = {
            "network_growth": [100 + i * 15 + np.random.normal(0, 5) for i in range(months)],
            "influence_score": [0.6 + i * 0.02 + np.random.normal(0, 0.01) for i in range(months)],
            "engagement_rate": [0.08 + i * 0.005 + np.random.normal(0, 0.002) for i in range(months)],
            "revenue_per_user": [120 + i * 8 + np.random.normal(0, 3) for i in range(months)]
        }
        
        return trends
    
    def _generate_forecast(self, network_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Genera pronósticos futuros"""
        current_users = network_data.get("total_users", 1000)
        current_revenue = network_data.get("total_revenue", 150000)
        
        return {
            "user_growth": {
                "3_months": current_users * 1.15,
                "6_months": current_users * 1.35,
                "12_months": current_users * 1.75
            },
            "revenue_growth": {
                "3_months": current_revenue * 1.20,
                "6_months": current_revenue * 1.45,
                "12_months": current_revenue * 2.00
            },
            "market_share": {
                "3_months": 0.025,
                "6_months": 0.035,
                "12_months": 0.050
            }
        }

    def generate_dashboard(self, user_id: str, business_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Genera un dashboard ejecutivo personalizado para el usuario.
        Args:
            user_id: ID del usuario
            business_unit: contexto de unidad de negocio (opcional)
        Returns:
            dict con KPIs, comparativas y alertas
        """
        kpis = self.gnn.get_executive_kpis(user_id, business_unit)
        sector_comparison = self.gnn.compare_to_sector(user_id, business_unit)
        alerts = self.gnn.get_smart_alerts(user_id, business_unit)
        dashboard = {
            'kpis': kpis,
            'sector_comparison': sector_comparison,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }
        self.last_dashboards[user_id] = dashboard
        logger.info(f"ExecutiveAnalytics: dashboard generado para {user_id}.")
        return dashboard


# Instancia global del sistema de analytics ejecutivo
executive_analytics = ExecutiveAnalytics() 