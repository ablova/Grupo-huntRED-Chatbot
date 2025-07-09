from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg, Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from ..models import (
    PayrollCompany, PayrollEmployee, PayrollPeriod,
    OverheadCategory, EmployeeOverheadCalculation, TeamOverheadAnalysis,
    OverheadMLModel, OverheadBenchmark
)
from ..services.overhead_calculator import OverheadCalculatorService
from ..services.ml_overhead_optimizer import MLOverheadOptimizer


@login_required
def overhead_dashboard(request, company_id=None):
    """Vista principal del dashboard de overhead"""
    
    # Obtener empresa
    if company_id:
        company = get_object_or_404(PayrollCompany, id=company_id)
    else:
        # Usar primera empresa disponible o la del usuario
        company = PayrollCompany.objects.filter(is_active=True).first()
        if not company:
            return render(request, 'payroll/overhead/no_company.html')

    # Parámetros de filtrado
    time_range = request.GET.get('range', '30d')
    department = request.GET.get('department', 'all')
    has_aura = request.GET.get('aura', 'true').lower() == 'true'
    has_ml = request.GET.get('ml', 'true').lower() == 'true'
    
    # Calcular fechas basadas en el rango
    end_date = timezone.now().date()
    if time_range == '7d':
        start_date = end_date - timedelta(days=7)
    elif time_range == '30d':
        start_date = end_date - timedelta(days=30)
    elif time_range == '90d':
        start_date = end_date - timedelta(days=90)
    elif time_range == '1y':
        start_date = end_date - timedelta(days=365)
    else:  # 'all'
        start_date = end_date - timedelta(days=730)  # 2 años max

    # Obtener datos del contexto
    context = {
        'company': company,
        'time_range': time_range,
        'department': department,
        'has_aura': has_aura,
        'has_ml': has_ml,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    # Agregar métricas principales
    context.update(_get_dashboard_metrics(company, start_date, end_date, department))
    
    # Agregar datos históricos
    context.update(_get_historical_data(company, start_date, end_date, department))
    
    # Agregar análisis de equipos
    context.update(_get_team_analysis(company, department))
    
    # Agregar datos AURA si está habilitado
    if has_aura:
        context.update(_get_aura_analysis(company, start_date, end_date, department))
    
    # Agregar datos ML si está habilitado
    if has_ml:
        context.update(_get_ml_analysis(company, start_date, end_date, department))
    
    # Agregar recomendaciones
    context.update(_get_recommendations(company, has_aura, has_ml))

    return render(request, 'payroll/overhead/dashboard.html', context)


@login_required
def dashboard_api_data(request, company_id):
    """API endpoint para datos del dashboard en formato JSON"""
    
    company = get_object_or_404(PayrollCompany, id=company_id)
    time_range = request.GET.get('range', '30d')
    department = request.GET.get('department', 'all')
    
    # Calcular fechas
    end_date = timezone.now().date()
    if time_range == '7d':
        start_date = end_date - timedelta(days=7)
    elif time_range == '30d':
        start_date = end_date - timedelta(days=30)
    elif time_range == '90d':
        start_date = end_date - timedelta(days=90)
    elif time_range == '1y':
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=730)

    data = {
        'metrics': _get_dashboard_metrics(company, start_date, end_date, department),
        'historical': _get_historical_data(company, start_date, end_date, department),
        'teams': _get_team_analysis(company, department),
        'aura': _get_aura_analysis(company, start_date, end_date, department),
        'ml': _get_ml_analysis(company, start_date, end_date, department),
        'recommendations': _get_recommendations(company, True, True),
        'last_updated': timezone.now().isoformat()
    }
    
    return JsonResponse(data)


def _get_dashboard_metrics(company, start_date, end_date, department):
    """Obtener métricas principales del dashboard"""
    
    # Filtros base
    filters = Q(employee__company=company)
    if department != 'all':
        filters &= Q(employee__department=department)
    
    # Cálculos actuales (último mes)
    current_calculations = EmployeeOverheadCalculation.objects.filter(
        filters,
        calculated_at__gte=timezone.now() - timedelta(days=30)
    )
    
    # Cálculos anteriores (penúltimo mes para comparación)
    previous_calculations = EmployeeOverheadCalculation.objects.filter(
        filters,
        calculated_at__gte=timezone.now() - timedelta(days=60),
        calculated_at__lt=timezone.now() - timedelta(days=30)
    )
    
    # Métricas actuales
    current_metrics = current_calculations.aggregate(
        avg_overhead_percentage=Avg('overhead_percentage'),
        avg_total_overhead=Avg('total_overhead'),
        avg_traditional_overhead=Avg('traditional_overhead'),
        avg_aura_overhead=Avg('aura_enhanced_overhead'),
        avg_efficiency=Avg('ml_confidence_score'),
        avg_ethics_score=Avg('aura_ethics_score'),
        total_employees=Count('employee', distinct=True)
    )
    
    # Métricas anteriores para comparación
    previous_metrics = previous_calculations.aggregate(
        avg_overhead_percentage=Avg('overhead_percentage'),
        avg_total_overhead=Avg('total_overhead'),
        avg_efficiency=Avg('ml_confidence_score'),
        avg_ethics_score=Avg('aura_ethics_score')
    )
    
    # Calcular cambios porcentuales
    def calculate_change(current, previous):
        if previous and previous > 0:
            return ((current or 0) - previous) / previous * 100
        return 0
    
    return {
        'current_overhead_percentage': current_metrics['avg_overhead_percentage'] or 0,
        'overhead_change': calculate_change(
            current_metrics['avg_overhead_percentage'],
            previous_metrics['avg_overhead_percentage']
        ),
        'current_total_overhead': current_metrics['avg_total_overhead'] or 0,
        'traditional_overhead': current_metrics['avg_traditional_overhead'] or 0,
        'aura_overhead': current_metrics['avg_aura_overhead'] or 0,
        'current_efficiency': current_metrics['avg_efficiency'] or 0,
        'efficiency_change': calculate_change(
            current_metrics['avg_efficiency'],
            previous_metrics['avg_efficiency']
        ),
        'current_ethics_score': current_metrics['avg_ethics_score'] or 0,
        'ethics_change': calculate_change(
            current_metrics['avg_ethics_score'],
            previous_metrics['avg_ethics_score']
        ),
        'total_employees': current_metrics['total_employees'] or 0,
    }


def _get_historical_data(company, start_date, end_date, department):
    """Obtener datos históricos para gráficos"""
    
    filters = Q(employee__company=company, calculated_at__gte=start_date, calculated_at__lte=end_date)
    if department != 'all':
        filters &= Q(employee__department=department)
    
    # Agrupar por semanas
    calculations = EmployeeOverheadCalculation.objects.filter(filters).order_by('calculated_at')
    
    historical_data = []
    current_date = start_date
    week_num = 1
    
    while current_date <= end_date:
        week_end = min(current_date + timedelta(days=6), end_date)
        
        week_calculations = calculations.filter(
            calculated_at__gte=current_date,
            calculated_at__lte=week_end
        )
        
        if week_calculations.exists():
            week_data = week_calculations.aggregate(
                avg_total_overhead=Avg('overhead_percentage'),
                avg_traditional_overhead=Avg('traditional_overhead'),
                avg_aura_overhead=Avg('aura_enhanced_overhead'),
                avg_efficiency=Avg('ml_confidence_score'),
                avg_ethics_score=Avg('aura_ethics_score'),
                avg_sustainability_score=Avg('aura_sustainability_score'),
                employee_count=Count('employee', distinct=True)
            )
            
            historical_data.append({
                'period': f'S{week_num}',
                'date': current_date.isoformat(),
                'total_overhead': float(week_data['avg_total_overhead'] or 0),
                'traditional_overhead': float(week_data['avg_traditional_overhead'] or 0) / 1000,  # Convert to percentage
                'aura_overhead': float(week_data['avg_aura_overhead'] or 0) / 1000,
                'employees': week_data['employee_count'] or 0,
                'efficiency': float(week_data['avg_efficiency'] or 0),
                'ethics_score': float(week_data['avg_ethics_score'] or 0),
                'sustainability_score': float(week_data['avg_sustainability_score'] or 0),
            })
        
        current_date += timedelta(days=7)
        week_num += 1
    
    # Obtener distribución por categorías
    categories = OverheadCategory.objects.filter(company=company)
    category_data = []
    
    for category in categories:
        if category.aura_category in ['INFRASTRUCTURE', 'ADMINISTRATIVE', 'BENEFITS', 'TRAINING', 'TECHNOLOGY']:
            # Categorías tradicionales
            avg_cost = calculations.aggregate(
                avg_cost=Avg('infrastructure_cost') if category.aura_category == 'INFRASTRUCTURE'
                else Avg('administrative_cost') if category.aura_category == 'ADMINISTRATIVE'
                else Avg('benefits_cost') if category.aura_category == 'BENEFITS'
                else Avg('training_cost') if category.aura_category == 'TRAINING'
                else Avg('technology_cost')
            )['avg_cost'] or 0
        else:
            # Categorías AURA
            avg_cost = calculations.aggregate(
                avg_cost=Avg('social_impact_cost') if category.aura_category == 'SOCIAL_IMPACT'
                else Avg('sustainability_cost') if category.aura_category == 'SUSTAINABILITY'
                else Avg('wellbeing_cost') if category.aura_category == 'WELLBEING'
                else Avg('innovation_cost')
            )['avg_cost'] or 0
        
        # Obtener benchmark correspondiente
        benchmark = OverheadBenchmark.objects.filter(
            industry='Tecnología',  # Por defecto
            region='México'
        ).first()
        
        benchmark_value = 0
        if benchmark:
            if category.aura_category == 'INFRASTRUCTURE':
                benchmark_value = float(benchmark.infrastructure_benchmark)
            elif category.aura_category == 'ADMINISTRATIVE':
                benchmark_value = float(benchmark.administrative_benchmark)
            elif category.aura_category == 'BENEFITS':
                benchmark_value = float(benchmark.benefits_benchmark)
            elif category.aura_category == 'TRAINING':
                benchmark_value = float(benchmark.training_benchmark)
            elif category.aura_category == 'TECHNOLOGY':
                benchmark_value = float(benchmark.technology_benchmark)
            elif category.aura_category == 'SOCIAL_IMPACT':
                benchmark_value = float(benchmark.social_impact_benchmark)
            elif category.aura_category == 'SUSTAINABILITY':
                benchmark_value = float(benchmark.sustainability_benchmark)
            elif category.aura_category == 'WELLBEING':
                benchmark_value = float(benchmark.wellbeing_benchmark)
            elif category.aura_category == 'INNOVATION':
                benchmark_value = float(benchmark.innovation_benchmark)
        
        category_data.append({
            'name': category.name,
            'value': float(avg_cost),
            'percentage': float(category.default_rate),
            'benchmark': benchmark_value,
            'color': _get_category_color(category.aura_category),
            'trend': 0  # Calcular trend si es necesario
        })
    
    return {
        'historical_data': historical_data,
        'category_data': category_data
    }


def _get_team_analysis(company, department):
    """Obtener análisis de equipos"""
    
    filters = Q(company=company, is_active=True)
    if department != 'all':
        filters &= Q(department=department)
    
    teams = TeamOverheadAnalysis.objects.filter(filters).order_by('department', 'team_name')
    
    team_data = []
    for team in teams:
        team_data.append({
            'team_name': team.team_name,
            'department': team.department,
            'efficiency': float(team.efficiency_score or 0),
            'overhead': float(team.overhead_per_employee or 0) / 1000,  # Convert to percentage
            'ethics_score': float(team.team_ethics_score or 0),
            'size': team.team_size,
            'trend': 5.0  # Mock trend data
        })
    
    return {'team_data': team_data}


def _get_aura_analysis(company, start_date, end_date, department):
    """Obtener análisis AURA"""
    
    filters = Q(employee__company=company, calculated_at__gte=start_date, calculated_at__lte=end_date)
    if department != 'all':
        filters &= Q(employee__department=department)
    
    aura_data = EmployeeOverheadCalculation.objects.filter(filters).aggregate(
        avg_ethics_score=Avg('aura_ethics_score'),
        avg_fairness_score=Avg('aura_fairness_score'),
        avg_sustainability_score=Avg('aura_sustainability_score')
    )
    
    # Datos del radar chart AURA
    radar_data = [
        {'subject': 'Ética', 'A': float(aura_data['avg_ethics_score'] or 0), 'fullMark': 100},
        {'subject': 'Equidad', 'A': float(aura_data['avg_fairness_score'] or 85), 'fullMark': 100},
        {'subject': 'Sustentabilidad', 'A': float(aura_data['avg_sustainability_score'] or 0), 'fullMark': 100},
        {'subject': 'Transparencia', 'A': 92, 'fullMark': 100},
        {'subject': 'Responsabilidad', 'A': 89, 'fullMark': 100},
        {'subject': 'Innovación', 'A': 85, 'fullMark': 100}
    ]
    
    # Métricas de sustentabilidad
    sustainability_metrics = {
        'co2_reduction': -15,
        'energy_efficiency': 22,
        'waste_reduction': -30,
        'employee_wellbeing': 18
    }
    
    # Recomendaciones AURA
    aura_recommendations = [
        {
            'type': 'success',
            'text': 'Implementar programa de home office híbrido',
            'icon': 'check-circle'
        },
        {
            'type': 'success', 
            'text': 'Optimizar infraestructura tecnológica',
            'icon': 'check-circle'
        },
        {
            'type': 'warning',
            'text': 'Revisar políticas de bienestar mental',
            'icon': 'alert-triangle'
        }
    ]
    
    return {
        'aura_radar_data': radar_data,
        'sustainability_score': float(aura_data['avg_sustainability_score'] or 0),
        'sustainability_metrics': sustainability_metrics,
        'aura_recommendations': aura_recommendations
    }


def _get_ml_analysis(company, start_date, end_date, department):
    """Obtener análisis de Machine Learning"""
    
    # Obtener modelos ML de la empresa
    ml_models = OverheadMLModel.objects.filter(company=company, is_active=True)
    
    model_performance = []
    for model in ml_models:
        model_performance.append({
            'model_name': model.model_name.replace('Overhead Predictor', '').replace('Optimizer', '').strip(),
            'accuracy': float(model.accuracy),
            'model_type': model.get_model_type_display(),
            'color_class': _get_model_color_class(model.model_type)
        })
    
    # Predicciones recientes
    recent_predictions = {
        'potential_savings': 12450,
        'average_confidence': 89.3,
        'optimizations_applied': 23,
        'total_optimizations': 31
    }
    
    # Optimizaciones automatizadas
    automated_optimizations = [
        {
            'category': 'Infraestructura',
            'description': 'Consolidación de servidores detectada. Ahorro estimado: $2,100/mes',
            'status': 'applied',
            'color': 'green'
        },
        {
            'category': 'Procesos Admin',
            'description': 'Automatización de reportes. Reducción 35% tiempo manual',
            'status': 'in_progress',
            'color': 'blue'
        },
        {
            'category': 'Capacitación',
            'description': 'Optimización calendario training. Eficiencia +28%',
            'status': 'pending',
            'color': 'orange'
        }
    ]
    
    # ROI de optimizaciones
    optimization_roi = {
        'current_roi': 347,
        'target_roi': 300,
        'progress_percentage': 87
    }
    
    return {
        'model_performance': model_performance,
        'recent_predictions': recent_predictions,
        'automated_optimizations': automated_optimizations,
        'optimization_roi': optimization_roi
    }


def _get_recommendations(company, has_aura, has_ml):
    """Obtener recomendaciones del sistema"""
    
    recommendations = []
    
    # Recomendación de alta prioridad
    recommendations.append({
        'priority': 'high',
        'title': 'Revisar Equipo Operaciones',
        'description': 'Overhead 48.3% por encima del benchmark. Posible optimización de $3,200/mes.',
        'color': 'red'
    })
    
    # Recomendación de media prioridad
    if has_ml:
        recommendations.append({
            'priority': 'medium',
            'title': 'Actualizar Modelo ML',
            'description': 'Nuevos datos disponibles. Reentrenamiento podría mejorar accuracy +2.3%.',
            'color': 'yellow'
        })
    
    # Oportunidad AURA
    if has_aura:
        recommendations.append({
            'priority': 'opportunity',
            'title': 'Expandir AURA Enhanced',
            'description': 'Equipos con AURA muestran 15% mayor eficiencia. Considerar expansión.',
            'color': 'green'
        })
    
    return {'recommendations': recommendations}


def _get_category_color(aura_category):
    """Obtener color para categoría basado en tipo AURA"""
    color_map = {
        'INFRASTRUCTURE': '#3B82F6',
        'ADMINISTRATIVE': '#10B981',
        'BENEFITS': '#8B5CF6',
        'TRAINING': '#F59E0B',
        'TECHNOLOGY': '#6366F1',
        'SOCIAL_IMPACT': '#EF4444',
        'SUSTAINABILITY': '#22C55E',
        'WELLBEING': '#EC4899',
        'INNOVATION': '#F97316'
    }
    return color_map.get(aura_category, '#6B7280')


def _get_model_color_class(model_type):
    """Obtener clase de color para modelo ML"""
    color_map = {
        'RANDOM_FOREST': 'indigo',
        'AURA_ENHANCED': 'purple',
        'HYBRID_ML_AURA': 'green',
        'NEURAL_NETWORK': 'blue',
        'GRADIENT_BOOSTING': 'yellow'
    }
    return color_map.get(model_type, 'gray')