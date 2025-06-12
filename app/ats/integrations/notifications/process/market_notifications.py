from typing import Dict, Any, List
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType, NotificationSeverity
from app.ats.market.models.trend import MarketTrend
from app.ats.market.models.benchmark import MarketBenchmark
from app.ats.models.business_unit import BusinessUnit
from app.ats.models.user import User

class MarketNotificationService(BaseNotificationService):
    """Servicio de notificaciones para análisis de mercado"""
    
    async def notify_market_trends(
        self,
        business_unit: BusinessUnit,
        trends: List[MarketTrend]
    ) -> None:
        """Notifica tendencias de mercado"""
        try:
            # Notificar a stakeholders
            for trend in trends:
                await self.send_notification(
                    title=f"Tendencia de Mercado: {trend.skill}",
                    message=self._format_trend_message(trend),
                    notification_type=NotificationType.MARKET_TREND,
                    severity=NotificationSeverity.INFO,
                    business_unit=business_unit,
                    metadata={
                        'trend_id': trend.id,
                        'skill': trend.skill,
                        'demand_level': trend.demand_level,
                        'growth_rate': trend.growth_rate
                    }
                )
        except Exception as e:
            self.logger.error(f"Error notificando tendencias: {str(e)}")
    
    async def notify_benchmark_update(
        self,
        business_unit: BusinessUnit,
        benchmark: MarketBenchmark
    ) -> None:
        """Notifica actualización de benchmarks"""
        try:
            await self.send_notification(
                title=f"Actualización de Benchmark: {benchmark.skill}",
                message=self._format_benchmark_message(benchmark),
                notification_type=NotificationType.MARKET_BENCHMARK,
                severity=NotificationSeverity.INFO,
                business_unit=business_unit,
                metadata={
                    'benchmark_id': benchmark.id,
                    'skill': benchmark.skill,
                    'salary_range': benchmark.salary_range,
                    'market_metrics': benchmark.market_metrics
                }
            )
        except Exception as e:
            self.logger.error(f"Error notificando benchmark: {str(e)}")
    
    async def notify_skill_demand(
        self,
        business_unit: BusinessUnit,
        skill: str,
        demand_data: Dict[str, Any]
    ) -> None:
        """Notifica demanda de habilidades"""
        try:
            await self.send_notification(
                title=f"Demanda de Habilidad: {skill}",
                message=self._format_demand_message(skill, demand_data),
                notification_type=NotificationType.SKILL_DEMAND,
                severity=NotificationSeverity.INFO,
                business_unit=business_unit,
                metadata={
                    'skill': skill,
                    'demand_data': demand_data
                }
            )
        except Exception as e:
            self.logger.error(f"Error notificando demanda: {str(e)}")
    
    def _format_trend_message(self, trend: MarketTrend) -> str:
        """Formatea mensaje de tendencia"""
        return (
            f"Tendencia detectada para {trend.skill}:\n"
            f"• Nivel de demanda: {trend.demand_level}\n"
            f"• Tasa de crecimiento: {trend.growth_rate}%\n"
            f"• Competencia: {trend.competition_level}\n"
            f"• Tendencias: {', '.join(trend.trends)}"
        )
    
    def _format_benchmark_message(self, benchmark: MarketBenchmark) -> str:
        """Formatea mensaje de benchmark"""
        return (
            f"Benchmark actualizado para {benchmark.skill}:\n"
            f"• Rango salarial: {benchmark.salary_range}\n"
            f"• Métricas de mercado: {benchmark.market_metrics}\n"
            f"• Última actualización: {benchmark.updated_at}"
        )
    
    def _format_demand_message(self, skill: str, demand_data: Dict[str, Any]) -> str:
        """Formatea mensaje de demanda"""
        return (
            f"Análisis de demanda para {skill}:\n"
            f"• Nivel de demanda: {demand_data.get('demand_level')}\n"
            f"• Tasa de crecimiento: {demand_data.get('growth_rate')}%\n"
            f"• Postulaciones activas: {demand_data.get('active_postings')}"
        ) 