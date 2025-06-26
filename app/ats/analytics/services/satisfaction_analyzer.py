from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.ats.pricing.models.addons import BusinessUnitAddon
from app.models import BusinessUnit
from app.ats.integrations.notifications.process.market_notifications import MarketNotificationService

class SatisfactionAnalyzer:
    """Servicio de análisis de satisfacción"""
    
    def __init__(self):
        self.notification_service = MarketNotificationService()
    
    async def analyze_satisfaction(
        self,
        business_unit: BusinessUnit,
        addon: BusinessUnitAddon
    ) -> Dict[str, Any]:
        """Analiza satisfacción con un addon"""
        try:
            # Métricas de uso
            usage_metrics = await self._analyze_usage(business_unit, addon)
            
            # Métricas de valor
            value_metrics = await self._analyze_value(business_unit, addon)
            
            # Métricas de retención
            retention_metrics = await self._analyze_retention(business_unit, addon)
            
            # Generar insights
            insights = self._generate_insights(
                usage_metrics=usage_metrics,
                value_metrics=value_metrics,
                retention_metrics=retention_metrics
            )
            
            # Notificar si hay problemas
            await self._notify_issues(business_unit, insights)
            
            return {
                'addon_id': addon.id,
                'business_unit_id': business_unit.id,
                'analysis_date': datetime.now(),
                'metrics': {
                    'usage': usage_metrics,
                    'value': value_metrics,
                    'retention': retention_metrics
                },
                'insights': insights,
                'recommendations': self._generate_recommendations(insights)
            }
            
        except Exception as e:
            self.logger.error(f"Error analizando satisfacción: {str(e)}")
            return None
    
    async def _analyze_usage(
        self,
        business_unit: BusinessUnit,
        addon: BusinessUnitAddon
    ) -> Dict[str, Any]:
        """Analiza métricas de uso"""
        return {
            'active_users': await self._get_active_users(business_unit, addon),
            'usage_frequency': await self._get_usage_frequency(business_unit, addon),
            'feature_usage': await self._get_feature_usage(business_unit, addon)
        }
    
    async def _analyze_value(
        self,
        business_unit: BusinessUnit,
        addon: BusinessUnitAddon
    ) -> Dict[str, Any]:
        """Analiza métricas de valor"""
        return {
            'roi': await self._calculate_roi(business_unit, addon),
            'savings': await self._calculate_savings(business_unit, addon),
            'efficiency_gains': await self._calculate_efficiency(business_unit, addon)
        }
    
    async def _analyze_retention(
        self,
        business_unit: BusinessUnit,
        addon: BusinessUnitAddon
    ) -> Dict[str, Any]:
        """Analiza métricas de retención"""
        return {
            'renewal_probability': await self._calculate_renewal_probability(business_unit, addon),
            'churn_risk': await self._calculate_churn_risk(business_unit, addon),
            'lifetime_value': await self._calculate_lifetime_value(business_unit, addon)
        }
    
    def _generate_insights(
        self,
        usage_metrics: Dict[str, Any],
        value_metrics: Dict[str, Any],
        retention_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Genera insights del análisis"""
        insights = []
        
        # Análisis de uso
        if usage_metrics['active_users'] < 0.5:  # Menos del 50% de usuarios activos
            insights.append({
                'type': 'usage',
                'severity': 'high',
                'message': 'Bajo nivel de adopción del addon',
                'recommendation': 'Implementar programa de onboarding'
            })
        
        # Análisis de valor
        if value_metrics['roi'] < 1.0:  # ROI negativo
            insights.append({
                'type': 'value',
                'severity': 'high',
                'message': 'ROI negativo detectado',
                'recommendation': 'Revisar estrategia de implementación'
            })
        
        # Análisis de retención
        if retention_metrics['churn_risk'] > 0.7:  # Alto riesgo de churn
            insights.append({
                'type': 'retention',
                'severity': 'high',
                'message': 'Alto riesgo de no renovación',
                'recommendation': 'Implementar plan de retención'
            })
        
        return insights
    
    def _generate_recommendations(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Genera recomendaciones basadas en insights"""
        recommendations = []
        
        for insight in insights:
            if insight['severity'] == 'high':
                recommendations.append({
                    'action': self._get_action_for_insight(insight),
                    'priority': 'high',
                    'expected_impact': self._get_expected_impact(insight),
                    'timeline': self._get_timeline(insight)
                })
        
        return recommendations
    
    async def _notify_issues(
        self,
        business_unit: BusinessUnit,
        insights: List[Dict[str, Any]]
    ) -> None:
        """Notifica problemas detectados"""
        high_severity_insights = [
            insight for insight in insights
            if insight['severity'] == 'high'
        ]
        
        if high_severity_insights:
            await self.notification_service.send_notification(
                title="Alertas de Satisfacción",
                message=self._format_insights_message(high_severity_insights),
                notification_type="SATISFACTION_ALERT",
                severity="HIGH",
                business_unit=business_unit,
                metadata={'insights': high_severity_insights}
            )
    
    def _format_insights_message(self, insights: List[Dict[str, Any]]) -> str:
        """Formatea mensaje de insights"""
        return "\n\n".join([
            f"• {insight['message']}\n"
            f"  Recomendación: {insight['recommendation']}"
            for insight in insights
        ])
    
    def _get_action_for_insight(self, insight: Dict[str, Any]) -> str:
        """Obtiene acción recomendada para un insight"""
        actions = {
            'usage': 'Implementar programa de adopción',
            'value': 'Optimizar implementación',
            'retention': 'Desarrollar plan de retención'
        }
        return actions.get(insight['type'], 'Revisar situación')
    
    def _get_expected_impact(self, insight: Dict[str, Any]) -> str:
        """Obtiene impacto esperado de la acción"""
        impacts = {
            'usage': 'Aumento del 30% en adopción',
            'value': 'Mejora del 25% en ROI',
            'retention': 'Reducción del 40% en riesgo de churn'
        }
        return impacts.get(insight['type'], 'Mejora general')
    
    def _get_timeline(self, insight: Dict[str, Any]) -> str:
        """Obtiene timeline recomendado"""
        timelines = {
            'usage': '2 semanas',
            'value': '1 mes',
            'retention': '3 semanas'
        }
        return timelines.get(insight['type'], '1 mes') 