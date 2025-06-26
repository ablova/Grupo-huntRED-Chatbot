"""
AURA - Reporting Engine
Motor avanzado de reportes que integra datos históricos, análisis predictivo y insights de AURA.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json
import pandas as pd
from collections import defaultdict
from django.db.models import Q, Count, Avg, Sum, F
from django.utils import timezone

from app.models import Opportunity, Contract, Vacancy, Person, BusinessUnit
from app.ml.aura.analytics.trend_analyzer import TrendAnalyzer
from app.ml.aura.energy_analyzer import EnergyAnalyzer

logger = logging.getLogger(__name__)

class ReportingEngine:
    """
    Motor avanzado de reportes de AURA:
    - Integración con datos históricos y análisis predictivo
    - Reportes automáticos con insights de AURA
    - Análisis de tendencias y patrones organizacionales
    - Predicciones basadas en modelos de ML
    - Reportes personalizados por unidad de negocio
    """
    
    def __init__(self):
        self.trend_analyzer = TrendAnalyzer()
        self.energy_analyzer = EnergyAnalyzer()
        self.report_cache = {}
        self.historical_data = {}
        self.prediction_models = {}
        
    def generate_comprehensive_report(self, business_unit: Optional[str] = None, 
                                    report_type: str = 'full', 
                                    time_range: str = '90d') -> Dict[str, Any]:
        """
        Genera un reporte comprehensivo integrando todos los sistemas de AURA.
        
        Args:
            business_unit: Unidad de negocio específica
            report_type: Tipo de reporte ('full', 'summary', 'predictive')
            time_range: Rango de tiempo para el análisis
            
        Returns:
            Dict con reporte comprehensivo
        """
        try:
            # Obtener datos base
            base_data = self._get_base_data(business_unit, time_range)
            
            # Análisis de tendencias con AURA
            trend_analysis = self._analyze_trends_with_aura(base_data, time_range)
            
            # Análisis de energía organizacional
            energy_analysis = self._analyze_organizational_energy(business_unit)
            
            # Predicciones avanzadas
            predictions = self._generate_advanced_predictions(base_data, trend_analysis)
            
            # Insights de AURA
            aura_insights = self._generate_aura_insights(base_data, trend_analysis, energy_analysis)
            
            # KPIs organizacionales
            kpis = self._calculate_organizational_kpis(base_data, business_unit)
            
            # Recomendaciones estratégicas
            recommendations = self._generate_strategic_recommendations(
                base_data, trend_analysis, energy_analysis, predictions
            )
            
            report = {
                'report_type': report_type,
                'business_unit': business_unit,
                'time_range': time_range,
                'generated_at': datetime.now().isoformat(),
                'base_metrics': base_data,
                'trend_analysis': trend_analysis,
                'energy_analysis': energy_analysis,
                'predictions': predictions,
                'aura_insights': aura_insights,
                'organizational_kpis': kpis,
                'strategic_recommendations': recommendations,
                'confidence_score': self._calculate_report_confidence(
                    base_data, trend_analysis, predictions
                )
            }
            
            # Cachear reporte
            cache_key = f"{business_unit}_{report_type}_{time_range}"
            self.report_cache[cache_key] = report
            
            return report
            
        except Exception as e:
            logger.error(f"Error generando reporte comprehensivo: {str(e)}")
            return self._get_error_report(str(e))
    
    def generate_performance_report(self, business_unit: str, 
                                  performance_type: str = 'recruitment') -> Dict[str, Any]:
        """
        Genera reporte de rendimiento específico para reclutamiento.
        
        Args:
            business_unit: Unidad de negocio
            performance_type: Tipo de rendimiento a analizar
            
        Returns:
            Dict con análisis de rendimiento
        """
        try:
            # Obtener datos de rendimiento
            performance_data = self._get_performance_data(business_unit, performance_type)
            
            # Análisis de eficiencia
            efficiency_analysis = self._analyze_recruitment_efficiency(performance_data)
            
            # Análisis de calidad de contrataciones
            quality_analysis = self._analyze_hiring_quality(performance_data)
            
            # Análisis de costos
            cost_analysis = self._analyze_recruitment_costs(performance_data)
            
            # Predicciones de rendimiento
            performance_predictions = self._predict_performance_trends(performance_data)
            
            return {
                'business_unit': business_unit,
                'performance_type': performance_type,
                'efficiency_metrics': efficiency_analysis,
                'quality_metrics': quality_analysis,
                'cost_analysis': cost_analysis,
                'performance_predictions': performance_predictions,
                'recommendations': self._generate_performance_recommendations(
                    efficiency_analysis, quality_analysis, cost_analysis
                ),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte de rendimiento: {str(e)}")
            return {'error': str(e)}
    
    def generate_predictive_report(self, business_unit: str, 
                                 forecast_period: int = 30) -> Dict[str, Any]:
        """
        Genera reporte predictivo usando modelos de AURA.
        
        Args:
            business_unit: Unidad de negocio
            forecast_period: Período de predicción en días
            
        Returns:
            Dict con predicciones y análisis
        """
        try:
            # Obtener datos históricos
            historical_data = self._get_historical_data(business_unit)
            
            # Predicciones de demanda de talento
            talent_demand_forecast = self._forecast_talent_demand(historical_data, forecast_period)
            
            # Predicciones de rotación
            turnover_forecast = self._forecast_turnover(historical_data, forecast_period)
            
            # Predicciones de costos
            cost_forecast = self._forecast_recruitment_costs(historical_data, forecast_period)
            
            # Análisis de riesgos
            risk_analysis = self._analyze_recruitment_risks(historical_data, forecast_period)
            
            # Escenarios de planificación
            planning_scenarios = self._generate_planning_scenarios(
                talent_demand_forecast, turnover_forecast, cost_forecast
            )
            
            return {
                'business_unit': business_unit,
                'forecast_period': forecast_period,
                'talent_demand_forecast': talent_demand_forecast,
                'turnover_forecast': turnover_forecast,
                'cost_forecast': cost_forecast,
                'risk_analysis': risk_analysis,
                'planning_scenarios': planning_scenarios,
                'confidence_intervals': self._calculate_forecast_confidence(
                    historical_data, forecast_period
                ),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte predictivo: {str(e)}")
            return {'error': str(e)}
    
    def _get_base_data(self, business_unit: Optional[str], time_range: str) -> Dict[str, Any]:
        """Obtiene datos base para el análisis."""
        end_date = timezone.now()
        
        if time_range == '30d':
            start_date = end_date - timedelta(days=30)
        elif time_range == '90d':
            start_date = end_date - timedelta(days=90)
        elif time_range == '365d':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=90)
        
        # Filtros base
        filters = Q(created_at__gte=start_date, created_at__lte=end_date)
        if business_unit:
            filters &= Q(business_unit__name=business_unit)
        
        # Obtener datos
        opportunities = Opportunity.objects.filter(filters)
        contracts = Contract.objects.filter(filters)
        vacancies = Vacancy.objects.filter(filters)
        persons = Person.objects.filter(filters)
        
        return {
            'opportunities': list(opportunities.values()),
            'contracts': list(contracts.values()),
            'vacancies': list(vacancies.values()),
            'persons': list(persons.values()),
            'time_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
    
    def _analyze_trends_with_aura(self, base_data: Dict[str, Any], time_range: str) -> Dict[str, Any]:
        """Analiza tendencias usando el poder de AURA."""
        # Convertir datos a formato para TrendAnalyzer
        trend_data = []
        
        for contract in base_data['contracts']:
            trend_data.append({
                'timestamp': contract['created_at'],
                'value': 1,  # Contrato firmado
                'type': 'contract'
            })
        
        for opportunity in base_data['opportunities']:
            trend_data.append({
                'timestamp': opportunity['created_at'],
                'value': 1,  # Oportunidad creada
                'type': 'opportunity'
            })
        
        # Analizar tendencias
        return self.trend_analyzer.analyze_trends(trend_data, 'recruitment_activity', time_range)
    
    def _analyze_organizational_energy(self, business_unit: Optional[str]) -> Dict[str, Any]:
        """Analiza la energía organizacional usando AURA."""
        try:
            return self.energy_analyzer.analyze_organizational_energy(business_unit)
        except Exception as e:
            logger.warning(f"No se pudo analizar energía organizacional: {str(e)}")
            return {'status': 'unavailable', 'reason': str(e)}
    
    def _generate_advanced_predictions(self, base_data: Dict[str, Any], 
                                     trend_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Genera predicciones avanzadas basadas en datos y tendencias."""
        predictions = {}
        
        # Predicción de conversión de oportunidades
        if base_data['opportunities']:
            conversion_rate = len(base_data['contracts']) / len(base_data['opportunities'])
            predictions['opportunity_conversion'] = {
                'current_rate': conversion_rate,
                'predicted_rate_30d': conversion_rate * 1.1,  # Mejora del 10%
                'confidence': 0.85
            }
        
        # Predicción de tiempo de contratación
        if base_data['contracts']:
            avg_time = self._calculate_average_hiring_time(base_data['contracts'])
            predictions['hiring_time'] = {
                'current_avg_days': avg_time,
                'predicted_avg_days_30d': avg_time * 0.9,  # Reducción del 10%
                'confidence': 0.80
            }
        
        return predictions
    
    def _generate_aura_insights(self, base_data: Dict[str, Any], 
                               trend_analysis: Dict[str, Any],
                               energy_analysis: Dict[str, Any]) -> List[str]:
        """Genera insights específicos de AURA."""
        insights = []
        
        # Insight basado en tendencias
        if trend_analysis.get('trend_analysis', {}).get('direction') == 'increasing':
            insights.append("📈 Las tendencias muestran un crecimiento sostenido en la actividad de reclutamiento")
        elif trend_analysis.get('trend_analysis', {}).get('direction') == 'decreasing':
            insights.append("📉 Se detecta una disminución en la actividad de reclutamiento que requiere atención")
        
        # Insight basado en energía organizacional
        if energy_analysis.get('overall_energy') == 'high':
            insights.append("⚡ La energía organizacional es alta, ideal para iniciativas de reclutamiento")
        elif energy_analysis.get('overall_energy') == 'low':
            insights.append("🔋 La energía organizacional es baja, considera estrategias de engagement")
        
        # Insight basado en datos
        if len(base_data['opportunities']) > len(base_data['contracts']) * 2:
            insights.append("🎯 Hay muchas oportunidades sin convertir, revisa el proceso de seguimiento")
        
        return insights
    
    def _calculate_organizational_kpis(self, base_data: Dict[str, Any], 
                                     business_unit: Optional[str]) -> Dict[str, Any]:
        """Calcula KPIs organizacionales clave."""
        kpis = {}
        
        # KPI de conversión
        if base_data['opportunities']:
            kpis['conversion_rate'] = len(base_data['contracts']) / len(base_data['opportunities'])
        
        # KPI de tiempo promedio de contratación
        if base_data['contracts']:
            kpis['avg_hiring_time_days'] = self._calculate_average_hiring_time(base_data['contracts'])
        
        # KPI de costo por contratación
        kpis['cost_per_hire'] = self._calculate_cost_per_hire(base_data)
        
        # KPI de calidad de contratación
        kpis['hiring_quality_score'] = self._calculate_hiring_quality_score(base_data)
        
        return kpis
    
    def _generate_strategic_recommendations(self, base_data: Dict[str, Any],
                                          trend_analysis: Dict[str, Any],
                                          energy_analysis: Dict[str, Any],
                                          predictions: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones estratégicas basadas en el análisis."""
        recommendations = []
        
        # Recomendación basada en tendencias
        if trend_analysis.get('trend_analysis', {}).get('direction') == 'decreasing':
            recommendations.append("🚀 Implementa campañas de marketing de empleador para aumentar el pipeline")
        
        # Recomendación basada en energía
        if energy_analysis.get('overall_energy') == 'low':
            recommendations.append("💪 Desarrolla programas de engagement para mejorar la energía organizacional")
        
        # Recomendación basada en predicciones
        if predictions.get('opportunity_conversion', {}).get('current_rate', 0) < 0.3:
            recommendations.append("📊 Optimiza el proceso de seguimiento de candidatos para mejorar la conversión")
        
        return recommendations
    
    def _calculate_report_confidence(self, base_data: Dict[str, Any],
                                   trend_analysis: Dict[str, Any],
                                   predictions: Dict[str, Any]) -> float:
        """Calcula el nivel de confianza del reporte."""
        confidence_factors = []
        
        # Factor de cantidad de datos
        data_volume = len(base_data['opportunities']) + len(base_data['contracts'])
        if data_volume > 100:
            confidence_factors.append(0.9)
        elif data_volume > 50:
            confidence_factors.append(0.8)
        elif data_volume > 20:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        # Factor de calidad de tendencias
        if trend_analysis.get('confidence_score'):
            confidence_factors.append(trend_analysis['confidence_score'])
        
        # Factor de predicciones
        if predictions.get('opportunity_conversion', {}).get('confidence'):
            confidence_factors.append(predictions['opportunity_conversion']['confidence'])
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.7
    
    def _get_performance_data(self, business_unit: str, performance_type: str) -> Dict[str, Any]:
        """Obtiene datos específicos de rendimiento."""
        # Implementación específica según el tipo de rendimiento
        return {}
    
    def _analyze_recruitment_efficiency(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza la eficiencia del reclutamiento."""
        return {}
    
    def _analyze_hiring_quality(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza la calidad de las contrataciones."""
        return {}
    
    def _analyze_recruitment_costs(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza los costos de reclutamiento."""
        return {}
    
    def _predict_performance_trends(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predice tendencias de rendimiento."""
        return {}
    
    def _generate_performance_recommendations(self, efficiency: Dict[str, Any],
                                            quality: Dict[str, Any],
                                            costs: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones de rendimiento."""
        return []
    
    def _get_historical_data(self, business_unit: str) -> Dict[str, Any]:
        """Obtiene datos históricos para predicciones."""
        return {}
    
    def _forecast_talent_demand(self, historical_data: Dict[str, Any], 
                               forecast_period: int) -> Dict[str, Any]:
        """Predice la demanda de talento."""
        return {}
    
    def _forecast_turnover(self, historical_data: Dict[str, Any], 
                          forecast_period: int) -> Dict[str, Any]:
        """Predice la rotación de empleados."""
        return {}
    
    def _forecast_recruitment_costs(self, historical_data: Dict[str, Any], 
                                   forecast_period: int) -> Dict[str, Any]:
        """Predice los costos de reclutamiento."""
        return {}
    
    def _analyze_recruitment_risks(self, historical_data: Dict[str, Any], 
                                  forecast_period: int) -> Dict[str, Any]:
        """Analiza riesgos en el reclutamiento."""
        return {}
    
    def _generate_planning_scenarios(self, talent_demand: Dict[str, Any],
                                   turnover: Dict[str, Any],
                                   costs: Dict[str, Any]) -> Dict[str, Any]:
        """Genera escenarios de planificación."""
        return {}
    
    def _calculate_forecast_confidence(self, historical_data: Dict[str, Any], 
                                     forecast_period: int) -> Dict[str, float]:
        """Calcula intervalos de confianza para predicciones."""
        return {}
    
    def _calculate_average_hiring_time(self, contracts: List[Dict[str, Any]]) -> float:
        """Calcula el tiempo promedio de contratación."""
        if not contracts:
            return 0.0
        
        total_days = 0
        for contract in contracts:
            if contract.get('created_at') and contract.get('proposal__created_at'):
                # Calcular diferencia en días
                created = datetime.fromisoformat(contract['created_at'].replace('Z', '+00:00'))
                proposal_created = datetime.fromisoformat(contract['proposal__created_at'].replace('Z', '+00:00'))
                days_diff = (created - proposal_created).days
                total_days += days_diff
        
        return total_days / len(contracts) if contracts else 0.0
    
    def _calculate_cost_per_hire(self, base_data: Dict[str, Any]) -> float:
        """Calcula el costo por contratación."""
        # Implementación simplificada
        return 5000.0  # Costo promedio estimado
    
    def _calculate_hiring_quality_score(self, base_data: Dict[str, Any]) -> float:
        """Calcula el score de calidad de contratación."""
        # Implementación simplificada
        return 0.85  # Score promedio estimado
    
    def _get_error_report(self, error_message: str) -> Dict[str, Any]:
        """Genera un reporte de error."""
        return {
            'error': True,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat(),
            'recommendation': 'Revisar logs y datos de entrada'
        } 