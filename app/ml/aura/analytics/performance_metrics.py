"""
AURA - Performance Metrics
Sistema avanzado de métricas de rendimiento para análisis de usuarios, equipos y organizaciones.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import numpy as np

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """
    Sistema de métricas de rendimiento para AURA:
    - Métricas individuales de usuarios
    - Métricas de equipos y organizaciones
    - Análisis de tendencias y benchmarking
    - Integración con GNN para métricas de red
    - Reportes automáticos y alertas
    """
    
    def __init__(self):
        self.metrics_cache = {}
        self.benchmark_data = {}
        self.alert_thresholds = {}
        self.report_templates = {}
        
        # Configurar métricas por defecto
        self._setup_default_metrics()
        
    def _setup_default_metrics(self):
        """Configura métricas por defecto."""
        self.default_metrics = {
            'user_engagement': {
                'daily_active_users': {'type': 'count', 'unit': 'users'},
                'session_duration': {'type': 'duration', 'unit': 'minutes'},
                'feature_adoption': {'type': 'percentage', 'unit': '%'},
                'task_completion_rate': {'type': 'percentage', 'unit': '%'},
                'error_rate': {'type': 'percentage', 'unit': '%'}
            },
            'network_metrics': {
                'connections_made': {'type': 'count', 'unit': 'connections'},
                'network_growth': {'type': 'percentage', 'unit': '%'},
                'influence_score': {'type': 'score', 'unit': '0-100'},
                'engagement_quality': {'type': 'score', 'unit': '0-100'}
            },
            'business_metrics': {
                'recruitment_success': {'type': 'percentage', 'unit': '%'},
                'time_to_hire': {'type': 'duration', 'unit': 'days'},
                'candidate_quality': {'type': 'score', 'unit': '0-100'},
                'cost_per_hire': {'type': 'currency', 'unit': 'MXN'}
            }
        }
        
        # Configurar umbrales de alerta
        self.alert_thresholds = {
            'user_engagement': {
                'session_duration': {'min': 5, 'max': 120},
                'task_completion_rate': {'min': 0.7, 'max': 1.0},
                'error_rate': {'min': 0.0, 'max': 0.1}
            },
            'network_metrics': {
                'network_growth': {'min': 0.05, 'max': 0.5},
                'influence_score': {'min': 20, 'max': 100}
            },
            'business_metrics': {
                'recruitment_success': {'min': 0.6, 'max': 1.0},
                'time_to_hire': {'min': 7, 'max': 60}
            }
        }
    
    def calculate_user_metrics(self, user_id: str, time_range: str = '30d', 
                             business_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Calcula métricas de rendimiento para un usuario específico.
        
        Args:
            user_id: ID del usuario
            time_range: Rango de tiempo ('7d', '30d', '90d', '1y')
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Dict con métricas calculadas
        """
        # Obtener datos del usuario
        user_data = self._get_user_data(user_id, time_range)
        
        # Calcular métricas de engagement
        engagement_metrics = self._calculate_engagement_metrics(user_data)
        
        # Calcular métricas de red
        network_metrics = self._calculate_network_metrics(user_id, time_range)
        
        # Calcular métricas de negocio
        business_metrics = self._calculate_business_metrics(user_id, time_range, business_unit)
        
        # Calcular scores compuestos
        composite_scores = self._calculate_composite_scores(
            engagement_metrics, network_metrics, business_metrics
        )
        
        # Generar insights y recomendaciones
        insights = self._generate_insights(engagement_metrics, network_metrics, business_metrics)
        
        return {
            'user_id': user_id,
            'time_range': time_range,
            'business_unit': business_unit,
            'engagement_metrics': engagement_metrics,
            'network_metrics': network_metrics,
            'business_metrics': business_metrics,
            'composite_scores': composite_scores,
            'insights': insights,
            'benchmark_comparison': self._compare_with_benchmark(composite_scores, business_unit),
            'alerts': self._check_alerts(engagement_metrics, network_metrics, business_metrics),
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_team_metrics(self, team_id: str, time_range: str = '30d',
                             business_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Calcula métricas de rendimiento para un equipo.
        
        Args:
            team_id: ID del equipo
            time_range: Rango de tiempo
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Dict con métricas del equipo
        """
        # Obtener miembros del equipo
        team_members = self._get_team_members(team_id)
        
        # Calcular métricas individuales para cada miembro
        member_metrics = {}
        for member_id in team_members:
            member_metrics[member_id] = self.calculate_user_metrics(member_id, time_range, business_unit)
        
        # Agregar métricas del equipo
        team_metrics = self._aggregate_team_metrics(member_metrics)
        
        # Calcular métricas de colaboración
        collaboration_metrics = self._calculate_collaboration_metrics(team_id, time_range)
        
        return {
            'team_id': team_id,
            'time_range': time_range,
            'business_unit': business_unit,
            'member_count': len(team_members),
            'member_metrics': member_metrics,
            'team_metrics': team_metrics,
            'collaboration_metrics': collaboration_metrics,
            'performance_distribution': self._calculate_performance_distribution(member_metrics),
            'top_performers': self._identify_top_performers(member_metrics),
            'improvement_opportunities': self._identify_improvement_opportunities(member_metrics),
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_organization_metrics(self, organization_id: str, time_range: str = '30d') -> Dict[str, Any]:
        """
        Calcula métricas de rendimiento para toda la organización.
        
        Args:
            organization_id: ID de la organización
            time_range: Rango de tiempo
            
        Returns:
            Dict con métricas organizacionales
        """
        # Obtener equipos de la organización
        teams = self._get_organization_teams(organization_id)
        
        # Calcular métricas por equipo
        team_metrics = {}
        for team_id in teams:
            team_metrics[team_id] = self.calculate_team_metrics(team_id, time_range)
        
        # Agregar métricas organizacionales
        org_metrics = self._aggregate_organization_metrics(team_metrics)
        
        # Calcular métricas de cultura y engagement
        culture_metrics = self._calculate_culture_metrics(organization_id, time_range)
        
        return {
            'organization_id': organization_id,
            'time_range': time_range,
            'total_employees': self._get_total_employees(organization_id),
            'team_count': len(teams),
            'team_metrics': team_metrics,
            'organization_metrics': org_metrics,
            'culture_metrics': culture_metrics,
            'performance_trends': self._calculate_performance_trends(organization_id, time_range),
            'benchmark_analysis': self._compare_organization_benchmark(org_metrics),
            'strategic_insights': self._generate_strategic_insights(org_metrics, culture_metrics),
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_engagement_metrics(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula métricas de engagement del usuario."""
        sessions = user_data.get('sessions', [])
        interactions = user_data.get('interactions', [])
        
        # Métricas básicas
        daily_active_users = len(set([s['date'] for s in sessions]))
        session_duration = np.mean([s['duration'] for s in sessions]) if sessions else 0
        feature_adoption = len(set([i['feature'] for i in interactions])) / len(self.default_metrics['user_engagement'])
        task_completion_rate = sum(1 for i in interactions if i.get('completed')) / len(interactions) if interactions else 0
        error_rate = sum(1 for i in interactions if i.get('error')) / len(interactions) if interactions else 0
        
        return {
            'daily_active_users': daily_active_users,
            'session_duration': session_duration,
            'feature_adoption': feature_adoption,
            'task_completion_rate': task_completion_rate,
            'error_rate': error_rate,
            'total_sessions': len(sessions),
            'total_interactions': len(interactions)
        }
    
    def _calculate_network_metrics(self, user_id: str, time_range: str) -> Dict[str, Any]:
        """Calcula métricas de red del usuario."""
        # Implementar cálculo de métricas de red usando GNN
        # Por ahora retorna métricas simuladas
        return {
            'connections_made': 15,
            'network_growth': 0.25,
            'influence_score': 75,
            'engagement_quality': 82,
            'network_size': 150,
            'mutual_connections': 45
        }
    
    def _calculate_business_metrics(self, user_id: str, time_range: str, 
                                  business_unit: Optional[str]) -> Dict[str, Any]:
        """Calcula métricas de negocio del usuario."""
        # Implementar cálculo de métricas de negocio
        # Por ahora retorna métricas simuladas
        return {
            'recruitment_success': 0.85,
            'time_to_hire': 25,
            'candidate_quality': 78,
            'cost_per_hire': 15000,
            'placements_made': 8,
            'client_satisfaction': 4.2
        }
    
    def _calculate_composite_scores(self, engagement: Dict[str, Any], 
                                  network: Dict[str, Any], 
                                  business: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula scores compuestos de rendimiento."""
        # Score de engagement (40% peso)
        engagement_score = (
            engagement.get('task_completion_rate', 0) * 0.4 +
            engagement.get('feature_adoption', 0) * 0.3 +
            (1 - engagement.get('error_rate', 0)) * 0.3
        ) * 100
        
        # Score de red (30% peso)
        network_score = (
            network.get('influence_score', 0) * 0.5 +
            network.get('engagement_quality', 0) * 0.5
        )
        
        # Score de negocio (30% peso)
        business_score = (
            business.get('recruitment_success', 0) * 0.4 +
            (business.get('candidate_quality', 0) / 100) * 0.3 +
            (business.get('client_satisfaction', 0) / 5) * 0.3
        ) * 100
        
        # Score total
        total_score = engagement_score * 0.4 + network_score * 0.3 + business_score * 0.3
        
        return {
            'engagement_score': engagement_score,
            'network_score': network_score,
            'business_score': business_score,
            'total_score': total_score,
            'performance_level': self._get_performance_level(total_score)
        }
    
    def _get_performance_level(self, score: float) -> str:
        """Determina el nivel de rendimiento basado en el score."""
        if score >= 90:
            return 'excellent'
        elif score >= 80:
            return 'good'
        elif score >= 70:
            return 'average'
        elif score >= 60:
            return 'below_average'
        else:
            return 'poor'
    
    def _generate_insights(self, engagement: Dict[str, Any], 
                          network: Dict[str, Any], 
                          business: Dict[str, Any]) -> List[str]:
        """Genera insights basados en las métricas."""
        insights = []
        
        # Insights de engagement
        if engagement.get('task_completion_rate', 0) < 0.8:
            insights.append("Oportunidad de mejora en tasa de completación de tareas")
        if engagement.get('error_rate', 0) > 0.1:
            insights.append("Tasa de errores elevada - considerar capacitación adicional")
        
        # Insights de red
        if network.get('network_growth', 0) < 0.1:
            insights.append("Crecimiento de red lento - activar networking automático")
        if network.get('influence_score', 0) < 50:
            insights.append("Bajo score de influencia - enfocar en contenido de valor")
        
        # Insights de negocio
        if business.get('recruitment_success', 0) < 0.7:
            insights.append("Tasa de éxito de reclutamiento por debajo del objetivo")
        if business.get('time_to_hire', 0) > 45:
            insights.append("Tiempo de contratación elevado - optimizar proceso")
        
        return insights
    
    def _compare_with_benchmark(self, composite_scores: Dict[str, Any], 
                               business_unit: Optional[str]) -> Dict[str, Any]:
        """Compara métricas con benchmarks."""
        benchmark = self.benchmark_data.get(business_unit, self.benchmark_data.get('default', {}))
        
        return {
            'total_score_vs_benchmark': composite_scores['total_score'] - benchmark.get('total_score', 75),
            'percentile': self._calculate_percentile(composite_scores['total_score'], benchmark),
            'benchmark_data': benchmark
        }
    
    def _check_alerts(self, engagement: Dict[str, Any], 
                     network: Dict[str, Any], 
                     business: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verifica si hay alertas basadas en umbrales."""
        alerts = []
        
        # Verificar umbrales de engagement
        for metric, thresholds in self.alert_thresholds.get('user_engagement', {}).items():
            value = engagement.get(metric, 0)
            if value < thresholds.get('min', 0) or value > thresholds.get('max', float('inf')):
                alerts.append({
                    'type': 'engagement',
                    'metric': metric,
                    'value': value,
                    'threshold': thresholds,
                    'severity': 'high' if abs(value - thresholds.get('min', 0)) > thresholds.get('min', 0) * 0.5 else 'medium'
                })
        
        # Verificar umbrales de red
        for metric, thresholds in self.alert_thresholds.get('network_metrics', {}).items():
            value = network.get(metric, 0)
            if value < thresholds.get('min', 0) or value > thresholds.get('max', float('inf')):
                alerts.append({
                    'type': 'network',
                    'metric': metric,
                    'value': value,
                    'threshold': thresholds,
                    'severity': 'medium'
                })
        
        # Verificar umbrales de negocio
        for metric, thresholds in self.alert_thresholds.get('business_metrics', {}).items():
            value = business.get(metric, 0)
            if value < thresholds.get('min', 0) or value > thresholds.get('max', float('inf')):
                alerts.append({
                    'type': 'business',
                    'metric': metric,
                    'value': value,
                    'threshold': thresholds,
                    'severity': 'high'
                })
        
        return alerts
    
    def _get_user_data(self, user_id: str, time_range: str) -> Dict[str, Any]:
        """Obtiene datos del usuario para el período especificado."""
        # Implementar obtención de datos del usuario
        # Por ahora retorna datos simulados
        return {
            'sessions': [
                {'date': '2024-01-01', 'duration': 45},
                {'date': '2024-01-02', 'duration': 30},
                {'date': '2024-01-03', 'duration': 60}
            ],
            'interactions': [
                {'feature': 'dashboard', 'completed': True, 'error': False},
                {'feature': 'search', 'completed': True, 'error': False},
                {'feature': 'profile', 'completed': False, 'error': True}
            ]
        }
    
    def _get_team_members(self, team_id: str) -> List[str]:
        """Obtiene miembros de un equipo."""
        # Implementar obtención de miembros del equipo
        return ['user_1', 'user_2', 'user_3']
    
    def _get_organization_teams(self, organization_id: str) -> List[str]:
        """Obtiene equipos de una organización."""
        # Implementar obtención de equipos
        return ['team_1', 'team_2', 'team_3']
    
    def _aggregate_team_metrics(self, member_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega métricas de miembros del equipo."""
        # Implementar agregación de métricas
        return {
            'average_engagement_score': 75,
            'average_network_score': 70,
            'average_business_score': 80,
            'team_performance_level': 'good'
        }
    
    def _calculate_collaboration_metrics(self, team_id: str, time_range: str) -> Dict[str, Any]:
        """Calcula métricas de colaboración del equipo."""
        # Implementar cálculo de métricas de colaboración
        return {
            'cross_team_projects': 3,
            'knowledge_sharing_score': 85,
            'team_cohesion': 78
        }
    
    def _calculate_performance_distribution(self, member_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula distribución de rendimiento en el equipo."""
        scores = [metrics['composite_scores']['total_score'] for metrics in member_metrics.values()]
        return {
            'excellent': len([s for s in scores if s >= 90]),
            'good': len([s for s in scores if 80 <= s < 90]),
            'average': len([s for s in scores if 70 <= s < 80]),
            'below_average': len([s for s in scores if 60 <= s < 70]),
            'poor': len([s for s in scores if s < 60])
        }
    
    def _identify_top_performers(self, member_metrics: Dict[str, Any]) -> List[str]:
        """Identifica los mejores performers del equipo."""
        sorted_members = sorted(
            member_metrics.items(),
            key=lambda x: x[1]['composite_scores']['total_score'],
            reverse=True
        )
        return [member_id for member_id, _ in sorted_members[:3]]
    
    def _identify_improvement_opportunities(self, member_metrics: Dict[str, Any]) -> List[str]:
        """Identifica oportunidades de mejora en el equipo."""
        improvement_opportunities = []
        for member_id, metrics in member_metrics.items():
            if metrics['composite_scores']['total_score'] < 70:
                improvement_opportunities.append(member_id)
        return improvement_opportunities
    
    def _aggregate_organization_metrics(self, team_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega métricas organizacionales."""
        # Implementar agregación de métricas organizacionales
        return {
            'overall_performance_score': 78,
            'employee_engagement': 82,
            'organizational_health': 75
        }
    
    def _calculate_culture_metrics(self, organization_id: str, time_range: str) -> Dict[str, Any]:
        """Calcula métricas de cultura organizacional."""
        # Implementar cálculo de métricas de cultura
        return {
            'diversity_score': 85,
            'inclusion_index': 78,
            'innovation_culture': 72
        }
    
    def _calculate_performance_trends(self, organization_id: str, time_range: str) -> Dict[str, Any]:
        """Calcula tendencias de rendimiento."""
        # Implementar cálculo de tendencias
        return {
            'trend_direction': 'improving',
            'trend_strength': 'moderate',
            'key_drivers': ['engagement', 'collaboration']
        }
    
    def _compare_organization_benchmark(self, org_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compara métricas organizacionales con benchmarks."""
        # Implementar comparación con benchmarks
        return {
            'industry_percentile': 75,
            'peer_comparison': 'above_average'
        }
    
    def _generate_strategic_insights(self, org_metrics: Dict[str, Any], 
                                   culture_metrics: Dict[str, Any]) -> List[str]:
        """Genera insights estratégicos."""
        insights = []
        
        if org_metrics.get('employee_engagement', 0) < 80:
            insights.append("Oportunidad de mejora en engagement organizacional")
        
        if culture_metrics.get('innovation_culture', 0) < 75:
            insights.append("Fortalecer cultura de innovación")
        
        return insights
    
    def _calculate_percentile(self, score: float, benchmark: Dict[str, Any]) -> float:
        """Calcula el percentil del score."""
        # Implementar cálculo de percentil
        return 75.0
    
    def _get_total_employees(self, organization_id: str) -> int:
        """Obtiene el total de empleados de la organización."""
        # Implementar obtención de total de empleados
        return 150
    
    def update_benchmark_data(self, business_unit: str, benchmark_data: Dict[str, Any]):
        """Actualiza datos de benchmark para una unidad de negocio."""
        self.benchmark_data[business_unit] = benchmark_data
        logger.info(f"Updated benchmark data for '{business_unit}'")
    
    def set_alert_threshold(self, metric_category: str, metric_name: str, 
                           min_value: float, max_value: float):
        """Establece umbrales de alerta para una métrica."""
        if metric_category not in self.alert_thresholds:
            self.alert_thresholds[metric_category] = {}
        
        self.alert_thresholds[metric_category][metric_name] = {
            'min': min_value,
            'max': max_value
        }
        logger.info(f"Set alert threshold for {metric_category}.{metric_name}")
    
    def get_metrics_history(self, user_id: str, metric_name: str, 
                          time_range: str = '90d') -> List[Dict[str, Any]]:
        """Obtiene historial de una métrica específica."""
        # Implementar obtención de historial
        return [
            {'date': '2024-01-01', 'value': 75},
            {'date': '2024-01-02', 'value': 78},
            {'date': '2024-01-03', 'value': 82}
        ]

# Instancia global
performance_metrics = PerformanceMetrics() 