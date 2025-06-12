from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.ats.pricing.models.addons import BusinessUnitAddon
from app.ats.models.business_unit import BusinessUnit
from app.ats.integrations.notifications.process.market_notifications import MarketNotificationService
from app.ats.analytics.services.satisfaction_analyzer import SatisfactionAnalyzer
from app.ats.market.services.report_generator import MarketReportGenerator
from app.ats.learning.services.recommendation_service import LearningRecommendationService

class AddonReportGenerator:
    """Generador de reportes de addons"""
    
    def __init__(self):
        self.notification_service = MarketNotificationService()
        self.satisfaction_analyzer = SatisfactionAnalyzer()
        self.market_generator = MarketReportGenerator()
        self.learning_service = LearningRecommendationService()
    
    async def generate_addon_report(
        self,
        business_unit: BusinessUnit,
        addon: BusinessUnitAddon,
        period: str = "monthly"
    ) -> Dict[str, Any]:
        """Genera reporte completo de addon"""
        try:
            # Análisis de satisfacción
            satisfaction = await self.satisfaction_analyzer.analyze_satisfaction(
                business_unit=business_unit,
                addon=addon
            )
            
            # Datos específicos según tipo de addon
            addon_data = await self._get_addon_specific_data(
                business_unit=business_unit,
                addon=addon,
                period=period
            )
            
            # Generar reporte
            report = {
                'addon_id': addon.id,
                'business_unit_id': business_unit.id,
                'period': period,
                'generated_at': datetime.now(),
                'satisfaction_analysis': satisfaction,
                'addon_data': addon_data,
                'recommendations': self._generate_recommendations(
                    satisfaction=satisfaction,
                    addon_data=addon_data
                )
            }
            
            # Notificar reporte
            await self._notify_report(business_unit, report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generando reporte: {str(e)}")
            return None
    
    async def _get_addon_specific_data(
        self,
        business_unit: BusinessUnit,
        addon: BusinessUnitAddon,
        period: str
    ) -> Dict[str, Any]:
        """Obtiene datos específicos según tipo de addon"""
        if addon.addon.type == 'market_report':
            return await self.market_generator.generate_market_report(
                business_unit=business_unit,
                period=period
            )
        elif addon.addon.type == 'learning_analytics':
            return await self.learning_service.generate_recommendations(
                business_unit=business_unit
            )
        return {}
    
    def _generate_recommendations(
        self,
        satisfaction: Dict[str, Any],
        addon_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []
        
        # Recomendaciones de satisfacción
        if satisfaction and 'recommendations' in satisfaction:
            recommendations.extend(satisfaction['recommendations'])
        
        # Recomendaciones específicas del addon
        if addon_data:
            recommendations.extend(self._get_addon_specific_recommendations(addon_data))
        
        return recommendations
    
    def _get_addon_specific_recommendations(
        self,
        addon_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Obtiene recomendaciones específicas según tipo de addon"""
        recommendations = []
        
        if 'market_data' in addon_data:
            recommendations.extend(self._get_market_recommendations(addon_data['market_data']))
        
        if 'learning_data' in addon_data:
            recommendations.extend(self._get_learning_recommendations(addon_data['learning_data']))
        
        return recommendations
    
    def _get_market_recommendations(
        self,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Obtiene recomendaciones basadas en datos de mercado"""
        recommendations = []
        
        # Analizar tendencias
        if 'trends' in market_data:
            for trend in market_data['trends']:
                if trend['growth_rate'] > 20:
                    recommendations.append({
                        'type': 'market_trend',
                        'action': f"Considerar inversión en {trend['skill']}",
                        'priority': 'high',
                        'rationale': f"Alta tasa de crecimiento ({trend['growth_rate']}%)"
                    })
        
        return recommendations
    
    def _get_learning_recommendations(
        self,
        learning_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Obtiene recomendaciones basadas en datos de aprendizaje"""
        recommendations = []
        
        # Analizar gaps
        if 'skill_gaps' in learning_data:
            for gap in learning_data['skill_gaps']['gaps']:
                if gap['required_level'] - gap['current_level'] > 2:
                    recommendations.append({
                        'type': 'learning_gap',
                        'action': f"Priorizar desarrollo de {gap['skill']}",
                        'priority': 'high',
                        'rationale': f"Gran gap de habilidad ({gap['required_level'] - gap['current_level']} niveles)"
                    })
        
        return recommendations
    
    async def _notify_report(
        self,
        business_unit: BusinessUnit,
        report: Dict[str, Any]
    ) -> None:
        """Notifica reporte generado"""
        await self.notification_service.send_notification(
            title=f"Reporte de Addon: {report['addon_id']}",
            message=self._format_report_message(report),
            notification_type="ADDON_REPORT",
            severity="INFO",
            business_unit=business_unit,
            metadata={'report': report}
        )
    
    def _format_report_message(self, report: Dict[str, Any]) -> str:
        """Formatea mensaje de reporte"""
        return (
            f"Reporte generado para el período {report['period']}:\n\n"
            f"Análisis de Satisfacción:\n{self._format_satisfaction(report['satisfaction_analysis'])}\n\n"
            f"Datos del Addon:\n{self._format_addon_data(report['addon_data'])}\n\n"
            f"Recomendaciones:\n{self._format_recommendations(report['recommendations'])}"
        )
    
    def _format_satisfaction(self, satisfaction: Dict[str, Any]) -> str:
        """Formatea sección de satisfacción"""
        if not satisfaction:
            return "No hay datos de satisfacción disponibles"
        
        return "\n".join([
            f"• Métricas de uso: {satisfaction['metrics']['usage']}",
            f"• Métricas de valor: {satisfaction['metrics']['value']}",
            f"• Métricas de retención: {satisfaction['metrics']['retention']}"
        ])
    
    def _format_addon_data(self, addon_data: Dict[str, Any]) -> str:
        """Formatea sección de datos del addon"""
        if not addon_data:
            return "No hay datos específicos disponibles"
        
        return "\n".join([
            f"• {key}: {value}"
            for key, value in addon_data.items()
        ])
    
    def _format_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        """Formatea sección de recomendaciones"""
        if not recommendations:
            return "No hay recomendaciones disponibles"
        
        return "\n".join([
            f"• {rec['action']} (Prioridad: {rec['priority']})\n"
            f"  Razonamiento: {rec['rationale']}"
            for rec in recommendations
        ]) 