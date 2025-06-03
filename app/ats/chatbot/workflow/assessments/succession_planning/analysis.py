"""
Módulo de análisis para planes de sucesión.

Este módulo proporciona funcionalidades avanzadas de análisis para evaluar
la preparación de candidatos y la fortaleza del banco de talentos.
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

from django.db.models import Count, Avg, Q, F, Value, IntegerField
from django.db.models.functions import Coalesce

from ....models import (
    Employee, 
    Position, 
    Assessment, 
    SuccessionPlan, 
    SuccessionCandidate
)

logger = logging.getLogger(__name__)

class SuccessionAnalysis:
    """Clase para realizar análisis avanzados de sucesión."""
    
    def __init__(self, org_id: Optional[str] = None):
        """
        Inicializa el analizador de sucesión.
        
        Args:
            org_id: ID de la organización (opcional)
        """
        self.org_id = org_id
    
    async def get_readiness_breakdown(
        self, 
        position_id: Optional[str] = None,
        department: Optional[str] = None
    ) -> Dict:
        """
        Obtiene un desglose de la preparación de los candidatos.
        
        Args:
            position_id: ID del puesto (opcional)
            department: Departamento (opcional)
            
        Returns:
            Dict con el desglose de preparación
        """
        try:
            # Construir consulta base
            query = SuccessionCandidate.objects.all()
            
            if position_id:
                query = query.filter(plan__position_id=position_id)
            
            if department:
                query = query.filter(plan__position__department=department)
            
            if self.org_id:
                query = query.filter(plan__position__organization_id=self.org_id)
            
            # Agrupar por nivel de preparación
            readiness_breakdown = await query.values('readiness_level').annotate(
                count=Count('id'),
                avg_potential=Avg('potential_rating'),
                avg_timeline=Avg('timeline_months')
            ).order_by('readiness_level')
            
            # Formatear resultados
            result = {
                'total_candidates': 0,
                'by_readiness_level': {},
                'summary': {
                    'ready_now': 0,
                    'one_to_two_years': 0,
                    'three_to_five_years': 0,
                    'not_feasible': 0
                }
            }
            
            for item in readiness_breakdown:
                level = item['readiness_level'].lower().replace(' ', '_')
                count = item['count']
                
                result['by_readiness_level'][level] = {
                    'count': count,
                    'avg_potential': item['avg_potential'],
                    'avg_timeline_months': item['avg_timeline']
                }
                
                result['total_candidates'] += count
                
                # Actualizar resumen
                if 'ready now' in level:
                    result['summary']['ready_now'] += count
                elif '1-2' in level:
                    result['summary']['one_to_two_years'] += count
                elif '3-5' in level:
                    result['summary']['three_to_five_years'] += count
                elif 'not feasible' in level:
                    result['summary']['not_feasible'] += count
            
            # Calcular porcentajes
            for level in result['by_readiness_level'].values():
                level['percentage'] = (level['count'] / result['total_candidates'] * 100) if result['total_candidates'] > 0 else 0
            
            return result
            
        except Exception as e:
            logger.error(f"Error en get_readiness_breakdown: {str(e)}", exc_info=True)
            return {
                'error': 'No se pudo obtener el desglose de preparación',
                'details': str(e)
            }
    
    async def get_bench_strength(
        self, 
        position_id: Optional[str] = None,
        department: Optional[str] = None,
        min_readiness: str = '3-5 Years'
    ) -> Dict:
        """
        Evalúa la fortaleza del banco de talentos para posiciones clave.
        
        Args:
            position_id: ID del puesto (opcional)
            department: Departamento (opcional)
            min_readiness: Nivel mínimo de preparación a considerar
            
        Returns:
            Dict con el análisis de fortaleza del banco de talentos
        """
        try:
            # Construir consulta base
            query = SuccessionPlan.objects.filter(
                critical_position=True
            )
            
            if position_id:
                query = query.filter(position_id=position_id)
            
            if department:
                query = query.filter(position__department=department)
            
            if self.org_id:
                query = query.filter(position__organization_id=self.org_id)
            
            # Contar puestos críticos
            critical_positions = await query.acount()
            
            if critical_positions == 0:
                return {
                    'total_critical_positions': 0,
                    'positions_with_viable_candidates': 0,
                    'coverage_percentage': 0,
                    'positions_at_risk': 0,
                    'risk_percentage': 0,
                    'details': []
                }
            
            # Obtener datos detallados
            positions_data = []
            positions_with_candidates = 0
            positions_at_risk = 0
            
            async for plan in query.select_related('position').prefetch_related('candidates'):
                # Contar candidatos viables (según min_readiness)
                viable_candidates = [
                    c for c in plan.candidates.all() 
                    if self._compare_readiness_levels(c.readiness_level, min_readiness) >= 0
                ]
                
                has_viable_candidates = len(viable_candidates) > 0
                if has_viable_candidates:
                    positions_with_candidates += 1
                
                # Determinar si el puesto está en riesgo
                is_at_risk = not has_viable_candidates or any(
                    c.readiness_level == 'Ready Now' 
                    for c in viable_candidates
                )
                
                if is_at_risk:
                    positions_at_risk += 1
                
                # Agregar datos del puesto
                positions_data.append({
                    'position_id': str(plan.position.id),
                    'position_title': plan.position.title,
                    'department': plan.position.department,
                    'total_candidates': plan.candidates.count(),
                    'viable_candidates': len(viable_candidates),
                    'has_viable_candidates': has_viable_candidates,
                    'is_at_risk': is_at_risk,
                    'candidates': [{
                        'employee_id': str(c.employee.id),
                        'employee_name': f"{c.employee.first_name} {c.employee.last_name}",
                        'readiness_level': c.readiness_level,
                        'potential_rating': c.potential_rating,
                        'timeline_months': c.timeline_months
                    } for c in viable_candidates]
                })
            
            # Calcular métricas agregadas
            coverage_percentage = (positions_with_candidates / critical_positions) * 100
            risk_percentage = (positions_at_risk / critical_positions) * 100
            
            return {
                'total_critical_positions': critical_positions,
                'positions_with_viable_candidates': positions_with_candidates,
                'coverage_percentage': round(coverage_percentage, 1),
                'positions_at_risk': positions_at_risk,
                'risk_percentage': round(risk_percentage, 1),
                'details': positions_data
            }
            
        except Exception as e:
            logger.error(f"Error en get_bench_strength: {str(e)}", exc_info=True)
            return {
                'error': 'No se pudo evaluar la fortaleza del banco de talentos',
                'details': str(e)
            }
    
    async def get_development_needs_summary(
        self,
        department: Optional[str] = None,
        min_frequency: int = 3
    ) -> Dict:
        """
        Identifica las necesidades de desarrollo más comunes.
        
        Args:
            department: Departamento (opcional)
            min_frequency: Frecuencia mínima para incluir una necesidad
            
        Returns:
            Dict con el resumen de necesidades de desarrollo
        """
        try:
            # Esta es una implementación simplificada
            # En una implementación real, se usaría un campo separado o NLP
            # para extraer las necesidades de desarrollo
            
            # Consulta para obtener todas las necesidades de desarrollo
            candidates = SuccessionCandidate.objects.all()
            
            if department:
                candidates = candidates.filter(plan__position__department=department)
            
            if self.org_id:
                candidates = candidates.filter(plan__position__organization_id=self.org_id)
            
            # Agrupar y contar necesidades (ejemplo simplificado)
            needs = {}
            
            async for candidate in candidates:
                if not candidate.development_needs:
                    continue
                    
                # Suponiendo que development_needs es un texto con necesidades separadas por comas
                for need in candidate.development_needs.split(','):
                    need = need.strip().lower()
                    if need:
                        needs[need] = needs.get(need, 0) + 1
            
            # Filtrar por frecuencia mínima
            filtered_needs = {k: v for k, v in needs.items() if v >= min_frequency}
            
            # Ordenar por frecuencia (descendente)
            sorted_needs = sorted(
                filtered_needs.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            return {
                'total_needs_identified': len(needs),
                'filtered_needs_count': len(filtered_needs),
                'needs': [
                    {'need': need, 'frequency': count} 
                    for need, count in sorted_needs
                ]
            }
            
        except Exception as e:
            logger.error(f"Error en get_development_needs_summary: {str(e)}", exc_info=True)
            return {
                'error': 'No se pudieron identificar las necesidades de desarrollo',
                'details': str(e)
            }
    
    def _compare_readiness_levels(self, level1: str, level2: str) -> int:
        """
        Compara dos niveles de preparación.
        
        Returns:
            -1 si level1 < level2
            0 si level1 == level2
            1 si level1 > level2
        """
        readiness_order = {
            'Ready Now': 3,
            '1-2 Years': 2,
            '3-5 Years': 1,
            'Not Feasible': 0
        }
        
        return (readiness_order.get(level1, 0) - 
                readiness_order.get(level2, 0))

    async def get_succession_risk_dashboard(
        self,
        department: Optional[str] = None
    ) -> Dict:
        """
        Genera un dashboard de riesgo de sucesión.
        
        Args:
            department: Departamento (opcional)
            
        Returns:
            Dict con métricas para el dashboard
        """
        try:
            # Obtener datos de preparación
            readiness = await self.get_readiness_breakdown(department=department)
            
            # Obtener fortaleza del banco de talentos
            bench_strength = await self.get_bench_strength(department=department)
            
            # Obtener necesidades de desarrollo
            dev_needs = await self.get_development_needs_summary(department=department)
            
            # Calcular métricas de riesgo
            risk_metrics = {
                'high_risk_positions': 0,
                'medium_risk_positions': 0,
                'low_risk_positions': 0
            }
            
            if 'details' in bench_strength:
                for position in bench_strength['details']:
                    if position['is_at_risk']:
                        risk_metrics['high_risk_positions'] += 1
                    elif position['has_viable_candidates']:
                        risk_metrics['low_risk_positions'] += 1
                    else:
                        risk_metrics['medium_risk_positions'] += 1
            
            return {
                'readiness_summary': readiness.get('summary', {}),
                'bench_strength': {
                    'total_positions': bench_strength.get('total_critical_positions', 0),
                    'coverage_percentage': bench_strength.get('coverage_percentage', 0),
                    'risk_percentage': bench_strength.get('risk_percentage', 0)
                },
                'risk_metrics': risk_metrics,
                'top_development_needs': dev_needs.get('needs', [])[:5] if 'needs' in dev_needs else []
            }
            
        except Exception as e:
            logger.error(f"Error en get_succession_risk_dashboard: {str(e)}", exc_info=True)
            return {
                'error': 'No se pudo generar el dashboard de riesgo de sucesión',
                'details': str(e)
            }
