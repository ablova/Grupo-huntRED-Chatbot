from typing import Dict, Any, List
from datetime import datetime
from app.ats.market.models.trend import MarketTrend
from app.ats.market.models.benchmark import MarketBenchmark
from app.models import BusinessUnit
from app.ats.integrations.notifications.process.market_notifications import MarketNotificationService

class MarketReportGenerator:
    """Generador de reportes de mercado"""
    
    def __init__(self):
        self.notification_service = MarketNotificationService()
    
    async def generate_market_report(
        self,
        business_unit: BusinessUnit,
        skills: List[str] = None,
        period: str = "monthly"
    ) -> Dict[str, Any]:
        """Genera reporte de mercado"""
        try:
            # Obtener tendencias
            trends = await self._get_trends(skills)
            
            # Obtener benchmarks
            benchmarks = await self._get_benchmarks(skills)
            
            # Generar insights
            insights = await self._generate_insights(trends, benchmarks)
            
            # Notificar reporte
            await self._notify_report(business_unit, insights)
            
            return {
                'period': period,
                'generated_at': datetime.now(),
                'insights': insights,
                'trends': trends,
                'benchmarks': benchmarks
            }
        except Exception as e:
            self.logger.error(f"Error generando reporte: {str(e)}")
            return None
    
    async def _get_trends(self, skills: List[str] = None) -> List[MarketTrend]:
        """Obtiene tendencias de mercado"""
        query = MarketTrend.objects.all()
        if skills:
            query = query.filter(skill__in=skills)
        return await query.order_by('-created_at')
    
    async def _get_benchmarks(self, skills: List[str] = None) -> List[MarketBenchmark]:
        """Obtiene benchmarks de mercado"""
        query = MarketBenchmark.objects.all()
        if skills:
            query = query.filter(skill__in=skills)
        return await query.order_by('-updated_at')
    
    async def _generate_insights(
        self,
        trends: List[MarketTrend],
        benchmarks: List[MarketBenchmark]
    ) -> Dict[str, Any]:
        """Genera insights del mercado"""
        return {
            'top_skills': self._get_top_skills(trends),
            'salary_trends': self._get_salary_trends(benchmarks),
            'demand_analysis': self._get_demand_analysis(trends),
            'competition_analysis': self._get_competition_analysis(trends)
        }
    
    def _get_top_skills(self, trends: List[MarketTrend]) -> List[Dict[str, Any]]:
        """Obtiene top habilidades por demanda"""
        return [
            {
                'skill': trend.skill,
                'demand_level': trend.demand_level,
                'growth_rate': trend.growth_rate
            }
            for trend in sorted(trends, key=lambda x: x.demand_level, reverse=True)[:10]
        ]
    
    def _get_salary_trends(self, benchmarks: List[MarketBenchmark]) -> List[Dict[str, Any]]:
        """Obtiene tendencias salariales"""
        return [
            {
                'skill': benchmark.skill,
                'salary_range': benchmark.salary_range,
                'trend': benchmark.market_metrics.get('salary_trend')
            }
            for benchmark in benchmarks
        ]
    
    def _get_demand_analysis(self, trends: List[MarketTrend]) -> Dict[str, Any]:
        """Analiza demanda del mercado"""
        return {
            'high_demand': len([t for t in trends if t.demand_level == 'high']),
            'medium_demand': len([t for t in trends if t.demand_level == 'medium']),
            'low_demand': len([t for t in trends if t.demand_level == 'low']),
            'growing_skills': [
                t.skill for t in trends
                if t.growth_rate > 10
            ]
        }
    
    def _get_competition_analysis(self, trends: List[MarketTrend]) -> Dict[str, Any]:
        """Analiza competencia del mercado"""
        return {
            'high_competition': len([t for t in trends if t.competition_level == 'high']),
            'medium_competition': len([t for t in trends if t.competition_level == 'medium']),
            'low_competition': len([t for t in trends if t.competition_level == 'low']),
            'opportunity_areas': [
                t.skill for t in trends
                if t.competition_level == 'low' and t.demand_level == 'high'
            ]
        }
    
    async def _notify_report(
        self,
        business_unit: BusinessUnit,
        insights: Dict[str, Any]
    ) -> None:
        """Notifica reporte generado"""
        await self.notification_service.send_notification(
            title="Reporte de Mercado Generado",
            message=self._format_report_message(insights),
            notification_type="MARKET_REPORT",
            severity="INFO",
            business_unit=business_unit,
            metadata={'insights': insights}
        )
    
    def _format_report_message(self, insights: Dict[str, Any]) -> str:
        """Formatea mensaje de reporte"""
        return (
            "Nuevo reporte de mercado generado:\n\n"
            f"Top Habilidades:\n{self._format_top_skills(insights['top_skills'])}\n\n"
            f"Análisis de Demanda:\n{self._format_demand(insights['demand_analysis'])}\n\n"
            f"Análisis de Competencia:\n{self._format_competition(insights['competition_analysis'])}"
        )
    
    def _format_top_skills(self, skills: List[Dict[str, Any]]) -> str:
        """Formatea top habilidades"""
        return "\n".join([
            f"• {s['skill']}: Demanda {s['demand_level']} (Crecimiento: {s['growth_rate']}%)"
            for s in skills
        ])
    
    def _format_demand(self, demand: Dict[str, Any]) -> str:
        """Formatea análisis de demanda"""
        return (
            f"• Alta demanda: {demand['high_demand']} habilidades\n"
            f"• Media demanda: {demand['medium_demand']} habilidades\n"
            f"• Baja demanda: {demand['low_demand']} habilidades\n"
            f"• Habilidades en crecimiento: {', '.join(demand['growing_skills'])}"
        )
    
    def _format_competition(self, competition: Dict[str, Any]) -> str:
        """Formatea análisis de competencia"""
        return (
            f"• Alta competencia: {competition['high_competition']} habilidades\n"
            f"• Media competencia: {competition['medium_competition']} habilidades\n"
            f"• Baja competencia: {competition['low_competition']} habilidades\n"
            f"• Áreas de oportunidad: {', '.join(competition['opportunity_areas'])}"
        ) 