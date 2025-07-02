"""
Utilidades para el módulo de Plan de Sucesión.

Este módulo proporciona funciones de utilidad para el manejo de planes de sucesión,
validación de datos, formateo y otras operaciones auxiliares.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

from django.utils import timezone
from django.db.models import Q, F, Count, Avg, Max, Min, Sum, Value, IntegerField
from django.db.models.functions import Coalesce, Concat

from app.ats.chatbot.models import Employee, Position, SuccessionPlan, SuccessionCandidate

logger = logging.getLogger(__name__)

def validate_email(email: str) -> bool:
    """
    Valida que un correo electrónico tenga un formato válido.
    
    Args:
        email: Correo electrónico a validar
        
    Returns:
        bool: True si el correo es válido, False en caso contrario
    """
    if not email:
        return False
    
    # Expresión regular para validar correos electrónicos
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def calculate_readiness_score(
    readiness_level: str, 
    confidence: float, 
    gap_count: int,
    max_gaps: int = 5
) -> float:
    """
    Calcula una puntuación de preparación basada en el nivel, confianza y brechas.
    
    Args:
        readiness_level: Nivel de preparación ('Ready Now', '1-2 Years', etc.)
        confidence: Nivel de confianza de la predicción (0-1)
        gap_count: Número de brechas críticas
        max_gaps: Número máximo de brechas para normalizar
        
    Returns:
        float: Puntuación de preparación (0-100)
    """
    # Peso base según el nivel de preparación
    level_weights = {
        'Ready Now': 1.0,
        '1-2 Years': 0.75,
        '3-5 Years': 0.5,
        'Not Feasible': 0.25
    }
    
    # Obtener peso base
    base_score = level_weights.get(readiness_level, 0) * 100
    
    # Ajustar por confianza
    adjusted_score = base_score * confidence
    
    # Penalizar por brechas (máximo 20% de penalización)
    gap_penalty = min(gap_count / max_gaps, 1.0) * 20
    final_score = max(0, adjusted_score - gap_penalty)
    
    return round(final_score, 2)

def format_development_timeline(months: int) -> str:
    """
    Formatea un período en meses a un formato legible.
    
    Args:
        months: Número de meses
        
    Returns:
        str: Período formateado (ej. "6 meses", "1 año y 3 meses")
    """
    if months < 1:
        return "Menos de 1 mes"
    
    years = months // 12
    remaining_months = months % 12
    
    parts = []
    if years > 0:
        parts.append(f"{years} año{'s' if years > 1 else ''}")
    
    if remaining_months > 0:
        parts.append(f"{remaining_months} mes{'es' if remaining_months > 1 else ''}")
    
    return " y ".join(parts)

def get_risk_level(score: float) -> Tuple[str, str]:
    """
    Determina el nivel de riesgo basado en una puntuación.
    
    Args:
        score: Puntuación de riesgo (0-100)
        
    Returns:
        Tuple[str, str]: (nivel_riesgo, clase_css)
    """
    if score >= 80:
        return ("Crítico", "danger")
    elif score >= 60:
        return ("Alto", "warning")
    elif score >= 40:
        return ("Moderado", "info")
    elif score >= 20:
        return ("Bajo", "primary")
    else:
        return ("Mínimo", "success")

def get_succession_metrics(org_id: str = None) -> Dict[str, Any]:
    """
    Obtiene métricas clave de sucesión para la organización.
    
    Args:
        org_id: ID de la organización (opcional)
        
    Returns:
        Dict con las métricas de sucesión
    """
    try:
        # Construir consulta base
        plans = SuccessionPlan.objects.all()
        candidates = SuccessionCandidate.objects.all()
        
        if org_id:
            plans = plans.filter(position__organization_id=org_id)
            candidates = candidates.filter(plan__position__organization_id=org_id)
        
        # Obtener conteo de planes por nivel de riesgo
        risk_levels = list(plants.values('risk_level').annotate(
            count=Count('id'),
            avg_risk=Avg('risk_score')
        ))
        
        # Obtener distribución de preparación de candidatos
        readiness_dist = list(candidates.values('readiness_level').annotate(
            count=Count('id'),
            avg_potential=Avg('potential_rating')
        ))
        
        # Calcular métricas agregadas
        total_positions = plans.count()
        total_candidates = candidates.count()
        avg_candidates_per_position = total_positions > 0 and total_candidates / total_positions or 0
        
        # Calcular cobertura de sucesión (porcentaje de puestos con al menos un candidato viable)
        covered_positions = plans.annotate(
            viable_candidates=Count('candidates', filter=Q(candidates__readiness_level__in=['Ready Now', '1-2 Years']))
        ).filter(viable_candidates__gt=0).count()
        
        coverage_pct = (covered_positions / total_positions * 100) if total_positions > 0 else 0
        
        return {
            'total_positions': total_positions,
            'total_candidates': total_candidates,
            'avg_candidates_per_position': round(avg_candidates_per_position, 1),
            'coverage_percentage': round(coverage_pct, 1),
            'risk_levels': risk_levels,
            'readiness_distribution': readiness_dist,
            'last_updated': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error al obtener métricas de sucesión: {str(e)}", exc_info=True)
        return {
            'error': 'No se pudieron obtener las métricas de sucesión',
            'details': str(e)
        }

def generate_development_plan(
    candidate_id: str, 
    position_id: str,
    gap_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Genera un plan de desarrollo personalizado para un candidato.
    
    Args:
        candidate_id: ID del candidato
        position_id: ID del puesto objetivo
        gap_analysis: Análisis de brechas
        
    Returns:
        Dict con el plan de desarrollo
    """
    try:
        # Obtener información del candidato y el puesto
        candidate = Employee.objects.get(id=candidate_id)
        position = Position.objects.get(id=position_id)
        
        # Generar recomendaciones basadas en las brechas
        recommendations = []
        
        for gap in gap_analysis.get('critical_gaps', []):
            # En una implementación real, esto podría usar un motor de recomendaciones
            # o reglas de negocio más sofisticadas
            
            if 'liderazgo' in gap.lower():
                recommendations.append({
                    'area': gap,
                    'actions': [
                        'Tomar un curso de liderazgo avanzado',
                        'Participar en un programa de mentoría',
                        'Asumir un proyecto que requiera liderazgo de equipo'
                    ],
                    'timeline_months': 6,
                    'priority': 'Alta'
                })
            elif 'técnic' in gap.lower() or 'tecnico' in gap.lower():
                recommendations.append({
                    'area': gap,
                    'actions': [
                        'Completar certificaciones técnicas relevantes',
                        'Participar en proyectos que requieran estas habilidades',
                        'Recibir capacitación específica en el área'
                    ],
                    'timeline_months': 3,
                    'priority': 'Media'
                })
            else:
                recommendations.append({
                    'area': gap,
                    'actions': [
                        f'Desarrollar habilidades en {gap} a través de capacitación',
                        'Buscar oportunidades para practicar estas habilidades',
                        'Solicitar retroalimentación regular'
                    ],
                    'timeline_months': 4,
                    'priority': 'Media'
                })
        
        # Calcular línea de tiempo total (máximo de los plazos individuales + 2 meses)
        total_months = max([r['timeline_months'] for r in recommendations] + [0]) + 2
        
        return {
            'candidate_id': candidate_id,
            'candidate_name': f"{candidate.first_name} {candidate.last_name}",
            'position_id': position_id,
            'position_title': position.title,
            'development_areas': recommendations,
            'total_timeline_months': total_months,
            'estimated_completion_date': (timezone.now() + timedelta(days=total_months*30)).strftime('%Y-%m-%d'),
            'created_at': timezone.now().isoformat()
        }
        
    except (Employee.DoesNotExist, Position.DoesNotExist) as e:
        logger.error(f"Error al generar plan de desarrollo: {str(e)}")
        return {
            'error': 'No se pudo generar el plan de desarrollo',
            'details': str(e)
        }
    except Exception as e:
        logger.error(f"Error inesperado al generar plan de desarrollo: {str(e)}", exc_info=True)
        return {
            'error': 'Error inesperado al generar el plan de desarrollo',
            'details': str(e)
        }

def format_currency(amount: float, currency: str = 'MXN') -> str:
    """
    Formatea una cantidad monetaria según la moneda especificada.
    
    Args:
        amount: Cantidad a formatear
        currency: Código de moneda (MXN, USD, EUR, etc.)
        
    Returns:
        str: Cantidad formateada con símbolo de moneda
    """
    currency_symbols = {
        'MXN': '\u0024',  # $
        'USD': '\u0024',  # $
        'EUR': '\u20AC',  # €
        'GBP': '\u00A3',  # £
        'JPY': '\u00A5'   # ¥
    }
    
    symbol = currency_symbols.get(currency, currency)
    
    # Formatear con separadores de miles y 2 decimales
    formatted_amount = "{:,.2f}".format(amount)
    
    # Algunas monedas ponen el símbolo después del número
    if currency in ['EUR', 'GBP']:
        return f"{formatted_amount} {symbol}"
    else:
        return f"{symbol}{formatted_amount}"
