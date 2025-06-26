from typing import Dict, Any, List
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType, NotificationSeverity
from app.ats.market.models.trend import MarketTrend
from app.ats.market.models.benchmark import MarketBenchmark
from app.models import BusinessUnit
from app.ml.analyzers.market.trend_analyzer import TrendAnalyzer
from app.ml.analyzers.market.demand_analyzer import DemandAnalyzer

class MarketAlertService(BaseNotificationService):
    """Servicio de alertas de mercado"""
    
    def __init__(self):
        super().__init__()
        self.trend_analyzer = TrendAnalyzer()
        self.demand_analyzer = DemandAnalyzer()
    
    async def check_market_alerts(
        self,
        business_unit: BusinessUnit,
        skills: List[str] = None
    ) -> None:
        """Verifica y envía alertas de mercado"""
        try:
            # Analizar tendencias
            trends = await self.trend_analyzer.analyze_market_trends(skills)
            
            # Analizar demanda
            demand = await self.demand_analyzer.analyze_demand(skills)
            
            # Generar alertas
            await self._generate_trend_alerts(business_unit, trends)
            await self._generate_demand_alerts(business_unit, demand)
            
        except Exception as e:
            self.logger.error(f"Error verificando alertas: {str(e)}")
    
    async def _generate_trend_alerts(
        self,
        business_unit: BusinessUnit,
        trends: List[Dict[str, Any]]
    ) -> None:
        """Genera alertas basadas en tendencias"""
        for trend in trends:
            if self._is_significant_trend(trend):
                await self.send_notification(
                    title=f"Alerta de Tendencia: {trend['skill']}",
                    message=self._format_trend_alert(trend),
                    notification_type=NotificationType.MARKET_ALERT,
                    severity=self._get_trend_severity(trend),
                    business_unit=business_unit,
                    metadata={'trend': trend}
                )
    
    async def _generate_demand_alerts(
        self,
        business_unit: BusinessUnit,
        demand: List[Dict[str, Any]]
    ) -> None:
        """Genera alertas basadas en demanda"""
        for skill_demand in demand:
            if self._is_significant_demand(skill_demand):
                await self.send_notification(
                    title=f"Alerta de Demanda: {skill_demand['skill']}",
                    message=self._format_demand_alert(skill_demand),
                    notification_type=NotificationType.DEMAND_ALERT,
                    severity=self._get_demand_severity(skill_demand),
                    business_unit=business_unit,
                    metadata={'demand': skill_demand}
                )
    
    def _is_significant_trend(self, trend: Dict[str, Any]) -> bool:
        """Determina si una tendencia es significativa"""
        return (
            trend['growth_rate'] > 20 or  # Crecimiento rápido
            trend['demand_level'] == 'high' or  # Alta demanda
            trend['competition_level'] == 'low'  # Baja competencia
        )
    
    def _is_significant_demand(self, demand: Dict[str, Any]) -> bool:
        """Determina si una demanda es significativa"""
        return (
            demand['demand_level'] == 'high' or  # Alta demanda
            demand['growth_rate'] > 15 or  # Crecimiento significativo
            demand['active_postings'] > 100  # Muchos postulantes
        )
    
    def _get_trend_severity(self, trend: Dict[str, Any]) -> str:
        """Determina la severidad de una tendencia"""
        if trend['growth_rate'] > 30:
            return NotificationSeverity.HIGH
        elif trend['growth_rate'] > 20:
            return NotificationSeverity.MEDIUM
        return NotificationSeverity.LOW
    
    def _get_demand_severity(self, demand: Dict[str, Any]) -> str:
        """Determina la severidad de una demanda"""
        if demand['demand_level'] == 'high' and demand['growth_rate'] > 20:
            return NotificationSeverity.HIGH
        elif demand['demand_level'] == 'high':
            return NotificationSeverity.MEDIUM
        return NotificationSeverity.LOW
    
    def _format_trend_alert(self, trend: Dict[str, Any]) -> str:
        """Formatea mensaje de alerta de tendencia"""
        return (
            f"Tendencia significativa detectada para {trend['skill']}:\n"
            f"• Tasa de crecimiento: {trend['growth_rate']}%\n"
            f"• Nivel de demanda: {trend['demand_level']}\n"
            f"• Nivel de competencia: {trend['competition_level']}\n"
            f"• Tendencias: {', '.join(trend['trends'])}"
        )
    
    def _format_demand_alert(self, demand: Dict[str, Any]) -> str:
        """Formatea mensaje de alerta de demanda"""
        return (
            f"Demanda significativa detectada para {demand['skill']}:\n"
            f"• Nivel de demanda: {demand['demand_level']}\n"
            f"• Tasa de crecimiento: {demand['growth_rate']}%\n"
            f"• Postulaciones activas: {demand['active_postings']}\n"
            f"• Tendencias: {', '.join(demand['trends'])}"
        ) 