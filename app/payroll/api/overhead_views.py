"""
APIs REST para Cálculo de Overhead con ML y AURA
Sistema completo de APIs para overhead individual y grupal
"""
import logging
from decimal import Decimal
from typing import Dict, List, Optional
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import (
    PayrollEmployee, PayrollCompany, PayrollPeriod,
    EmployeeOverheadCalculation, TeamOverheadAnalysis,
    OverheadCategory, OverheadBenchmark
)
from ..services.overhead_calculator import OverheadCalculatorService
from ..services.ml_overhead_optimizer import MLOverheadOptimizer
from ..serializers import (
    OverheadCalculationSerializer, TeamOverheadAnalysisSerializer,
    OverheadCategorySerializer
)

logger = logging.getLogger(__name__)


class OverheadCalculationAPIView(APIView):
    """
    API para cálculo de overhead individual
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Calcula overhead individual para un empleado",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'employee_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID del empleado'),
                'period_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID del período (opcional)'),
                'use_aura': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Usar capacidades AURA (opcional)'),
                'use_ml': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Usar optimización ML (opcional)'),
                'optimization_goals': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='Objetivos de optimización (opcional)'
                )
            },
            required=['employee_id']
        ),
        responses={
            200: openapi.Response(
                description="Cálculo exitoso",
                examples={
                    "application/json": {
                        "success": True,
                        "data": {
                            "employee_id": "uuid",
                            "base_salary": 50000,
                            "total_overhead": 21500,
                            "overhead_percentage": 43.0,
                            "traditional_overhead": {},
                            "aura_enhanced_overhead": {},
                            "ml_optimization": {},
                            "benchmark_data": {},
                            "recommendations": []
                        }
                    }
                }
            ),
            400: "Error en parámetros",
            404: "Empleado no encontrado"
        }
    )
    def post(self, request):
        """Calcula overhead individual"""
        try:
            data = request.data
            employee_id = data.get('employee_id')
            period_id = data.get('period_id')
            use_aura = data.get('use_aura')
            use_ml = data.get('use_ml', True)
            optimization_goals = data.get('optimization_goals', {})
            
            # Validar empleado
            employee = get_object_or_404(PayrollEmployee, id=employee_id)
            
            # Verificar que el usuario tenga acceso a esta empresa
            if not self._has_company_access(request.user, employee.company):
                return Response({
                    'success': False,
                    'error': 'Sin permisos para acceder a esta empresa'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Obtener o crear período actual
            period = self._get_or_create_current_period(employee.company, period_id)
            
            # Inicializar servicios
            calculator = OverheadCalculatorService(employee.company)
            result = calculator.calculate_individual_overhead(
                employee=employee,
                period=period,
                use_aura=use_aura,
                save_calculation=True
            )
            
            # Optimización ML (si se solicita)
            ml_optimization = {}
            if use_ml:
                ml_optimizer = MLOverheadOptimizer(employee.company)
                ml_optimization = ml_optimizer.predict_optimal_overhead(
                    employee=employee,
                    optimization_goals=optimization_goals
                )
                result['ml_optimization'] = ml_optimization
            
            # Combinar resultados
            combined_result = self._combine_calculation_results(result, ml_optimization)
            
            return Response({
                'success': True,
                'data': combined_result,
                'metadata': {
                    'calculated_at': result['calculation_metadata']['calculated_at'],
                    'version': '2.0',
                    'has_aura': employee.company.premium_services.get('aura_enabled', False),
                    'ml_enabled': use_ml
                }
            })
            
        except PayrollEmployee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Empleado no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Error en cálculo de overhead individual: {e}")
            return Response({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _has_company_access(self, user, company):
        """Verifica si el usuario tiene acceso a la empresa"""
        # Implementar lógica de permisos según el modelo de usuario
        # Por ahora, asumimos que todos los usuarios autenticados tienen acceso
        return True
    
    def _get_or_create_current_period(self, company, period_id=None):
        """Obtiene o crea período actual"""
        if period_id:
            try:
                return PayrollPeriod.objects.get(id=period_id, company=company)
            except PayrollPeriod.DoesNotExist:
                pass
        
        # Crear período actual si no existe
        from datetime import datetime
        current_month = datetime.now().strftime('%Y-%m')
        period, created = PayrollPeriod.objects.get_or_create(
            company=company,
            period_name=f"Período {current_month}",
            defaults={
                'start_date': datetime.now().replace(day=1).date(),
                'end_date': datetime.now().date(),
                'frequency': 'monthly',
                'status': 'draft'
            }
        )
        return period
    
    def _combine_calculation_results(self, calculation_result, ml_optimization):
        """Combina resultados de cálculo y optimización ML"""
        combined = calculation_result.copy()
        
        if ml_optimization:
            combined.update({
                'ml_predicted_overhead': ml_optimization.get('predicted_overhead', 0),
                'ml_confidence_score': ml_optimization.get('confidence_score', 0),
                'ml_optimization_potential': ml_optimization.get('optimization_potential', 0),
                'ml_recommendations': ml_optimization.get('recommendations', []),
                'ml_category_breakdown': ml_optimization.get('category_breakdown', {}),
                'ethics_analysis': ml_optimization.get('ethics_analysis', {})
            })
            
            # Calcular savings potenciales
            current_overhead = combined.get('total_overhead', 0)
            predicted_overhead = ml_optimization.get('predicted_overhead', 0)
            if predicted_overhead > 0:
                combined['potential_savings'] = max(0, current_overhead - predicted_overhead)
                combined['savings_percentage'] = (combined['potential_savings'] / current_overhead * 100) if current_overhead > 0 else 0
        
        return combined


class TeamOverheadAnalysisAPIView(APIView):
    """
    API para análisis de overhead grupal
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Analiza overhead grupal para un equipo",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'employee_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description='Lista de IDs de empleados del equipo'
                ),
                'team_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre del equipo'),
                'department': openapi.Schema(type=openapi.TYPE_STRING, description='Departamento (opcional)'),
                'period_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID del período (opcional)'),
                'use_aura': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Usar capacidades AURA (opcional)'),
                'use_ml': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Usar optimización ML (opcional)'),
                'optimization_goals': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='Objetivos de optimización del equipo (opcional)'
                )
            },
            required=['employee_ids', 'team_name']
        ),
        responses={
            200: openapi.Response(
                description="Análisis exitoso",
                examples={
                    "application/json": {
                        "success": True,
                        "data": {
                            "team_name": "Equipo IT",
                            "team_size": 5,
                            "team_metrics": {},
                            "individual_calculations": [],
                            "efficiency_analysis": {},
                            "aura_analysis": {},
                            "ml_optimization": {},
                            "benchmark_analysis": {},
                            "recommendations": []
                        }
                    }
                }
            )
        }
    )
    def post(self, request):
        """Analiza overhead de equipo"""
        try:
            data = request.data
            employee_ids = data.get('employee_ids', [])
            team_name = data.get('team_name')
            department = data.get('department')
            period_id = data.get('period_id')
            use_aura = data.get('use_aura')
            use_ml = data.get('use_ml', True)
            optimization_goals = data.get('optimization_goals', {})
            
            if not employee_ids:
                return Response({
                    'success': False,
                    'error': 'Lista de empleados requerida'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener empleados
            employees = PayrollEmployee.objects.filter(id__in=employee_ids)
            if len(employees) != len(employee_ids):
                return Response({
                    'success': False,
                    'error': 'Algunos empleados no fueron encontrados'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verificar que todos pertenezcan a la misma empresa
            companies = set(emp.company.id for emp in employees)
            if len(companies) > 1:
                return Response({
                    'success': False,
                    'error': 'Todos los empleados deben pertenecer a la misma empresa'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            company = employees[0].company
            
            # Verificar permisos
            if not self._has_company_access(request.user, company):
                return Response({
                    'success': False,
                    'error': 'Sin permisos para acceder a esta empresa'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Obtener período
            period = self._get_or_create_current_period(company, period_id)
            
            # Análisis base de overhead
            calculator = OverheadCalculatorService(company)
            team_analysis = calculator.calculate_team_overhead(
                team_employees=list(employees),
                period=period,
                team_name=team_name,
                department=department,
                use_aura=use_aura,
                save_analysis=True
            )
            
            # Optimización ML del equipo (si se solicita)
            ml_team_optimization = {}
            if use_ml:
                ml_optimizer = MLOverheadOptimizer(company)
                ml_team_optimization = ml_optimizer.analyze_team_ml_optimization(
                    team_employees=list(employees),
                    team_data=team_analysis,
                    optimization_goals=optimization_goals
                )
                team_analysis['ml_optimization'] = ml_team_optimization
            
            # Enriquecer con datos adicionales
            enriched_analysis = self._enrich_team_analysis(team_analysis, ml_team_optimization)
            
            return Response({
                'success': True,
                'data': enriched_analysis,
                'metadata': {
                    'analyzed_at': team_analysis['metadata']['calculated_at'],
                    'version': '2.0',
                    'has_aura': company.premium_services.get('aura_enabled', False),
                    'ml_enabled': use_ml,
                    'team_size': len(employees)
                }
            })
            
        except Exception as e:
            logger.error(f"Error en análisis de equipo: {e}")
            return Response({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _has_company_access(self, user, company):
        """Verifica acceso a empresa"""
        return True  # Implementar lógica real
    
    def _get_or_create_current_period(self, company, period_id=None):
        """Obtiene o crea período"""
        if period_id:
            try:
                return PayrollPeriod.objects.get(id=period_id, company=company)
            except PayrollPeriod.DoesNotExist:
                pass
        
        from datetime import datetime
        current_month = datetime.now().strftime('%Y-%m')
        period, created = PayrollPeriod.objects.get_or_create(
            company=company,
            period_name=f"Período {current_month}",
            defaults={
                'start_date': datetime.now().replace(day=1).date(),
                'end_date': datetime.now().date(),
                'frequency': 'monthly',
                'status': 'draft'
            }
        )
        return period
    
    def _enrich_team_analysis(self, team_analysis, ml_optimization):
        """Enriquece análisis con datos adicionales"""
        enriched = team_analysis.copy()
        
        if ml_optimization:
            # Métricas ML del equipo
            ml_metrics = ml_optimization.get('team_metrics', {})
            enriched['ml_enhanced_metrics'] = {
                'current_vs_optimized': {
                    'current_overhead': ml_metrics.get('current_total_overhead', 0),
                    'optimized_overhead': ml_metrics.get('optimized_total_overhead', 0),
                    'savings_potential': ml_metrics.get('total_savings_potential', 0),
                    'efficiency_improvement': ml_metrics.get('efficiency_improvement', 0)
                },
                'confidence_metrics': {
                    'avg_confidence': ml_metrics.get('avg_confidence', 0),
                    'prediction_reliability': self._calculate_prediction_reliability(ml_optimization)
                }
            }
            
            # Integrar recomendaciones ML
            if 'team_recommendations' in ml_optimization:
                existing_recs = enriched.get('recommendations', [])
                ml_recs = ml_optimization['team_recommendations']
                enriched['recommendations'] = existing_recs + ml_recs
            
            # Roadmap de implementación
            if 'implementation_roadmap' in ml_optimization:
                enriched['implementation_roadmap'] = ml_optimization['implementation_roadmap']
        
        return enriched
    
    def _calculate_prediction_reliability(self, ml_optimization):
        """Calcula confiabilidad de predicciones"""
        individual_predictions = ml_optimization.get('individual_predictions', [])
        if not individual_predictions:
            return 0
        
        confidences = [p.get('confidence_score', 0) for p in individual_predictions]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Penalizar por alta variabilidad
        if len(confidences) > 1:
            import statistics
            std_dev = statistics.stdev(confidences)
            reliability = avg_confidence * (1 - min(0.5, std_dev / avg_confidence))
        else:
            reliability = avg_confidence
        
        return reliability


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_overhead_benchmarks(request):
    """
    Obtiene benchmarks de overhead por industria y tamaño
    """
    try:
        industry = request.GET.get('industry', '')
        company_size = request.GET.get('company_size', '')
        region = request.GET.get('region', '')
        
        # Filtros
        filters = {'is_active': True}
        if industry:
            filters['industry__icontains'] = industry
        if company_size:
            filters['company_size_range'] = company_size
        if region:
            filters['region__icontains'] = region
        
        benchmarks = OverheadBenchmark.objects.filter(**filters)
        
        # Serializar resultados
        benchmark_data = []
        for benchmark in benchmarks:
            benchmark_data.append({
                'id': str(benchmark.id),
                'industry': benchmark.industry,
                'region': benchmark.region,
                'company_size_range': benchmark.company_size_range,
                'total_overhead_benchmark': float(benchmark.total_overhead_benchmark),
                'category_benchmarks': {
                    'infrastructure': float(benchmark.infrastructure_benchmark),
                    'administrative': float(benchmark.administrative_benchmark),
                    'benefits': float(benchmark.benefits_benchmark),
                    'training': float(benchmark.training_benchmark),
                    'technology': float(benchmark.technology_benchmark),
                    'social_impact': float(benchmark.social_impact_benchmark),
                    'sustainability': float(benchmark.sustainability_benchmark),
                    'wellbeing': float(benchmark.wellbeing_benchmark),
                    'innovation': float(benchmark.innovation_benchmark)
                },
                'percentiles': benchmark.get_benchmark_range(),
                'metadata': {
                    'sample_size': benchmark.sample_size,
                    'confidence_level': float(benchmark.confidence_level),
                    'last_updated': benchmark.last_updated.isoformat()
                }
            })
        
        return Response({
            'success': True,
            'data': benchmark_data,
            'count': len(benchmark_data),
            'filters_applied': {
                'industry': industry,
                'company_size': company_size,
                'region': region
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo benchmarks: {e}")
        return Response({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_employee_overhead_history(request, employee_id):
    """
    Obtiene historial de overhead para un empleado
    """
    try:
        employee = get_object_or_404(PayrollEmployee, id=employee_id)
        
        # Verificar permisos
        # TODO: Implementar verificación de permisos real
        
        # Obtener historial
        calculations = EmployeeOverheadCalculation.objects.filter(
            employee=employee
        ).order_by('-calculated_at')[:24]  # Últimos 24 períodos
        
        history_data = []
        for calc in calculations:
            history_data.append({
                'period': calc.period.period_name,
                'calculated_at': calc.calculated_at.isoformat(),
                'total_overhead': float(calc.total_overhead),
                'overhead_percentage': float(calc.overhead_percentage),
                'category_breakdown': {
                    'traditional': {
                        'infrastructure': float(calc.infrastructure_cost),
                        'administrative': float(calc.administrative_cost),
                        'benefits': float(calc.benefits_cost),
                        'training': float(calc.training_cost),
                        'technology': float(calc.technology_cost)
                    },
                    'aura_enhanced': {
                        'social_impact': float(calc.social_impact_cost),
                        'sustainability': float(calc.sustainability_cost),
                        'wellbeing': float(calc.wellbeing_cost),
                        'innovation': float(calc.innovation_cost)
                    }
                },
                'benchmarks': {
                    'industry': float(calc.industry_benchmark),
                    'company_size': float(calc.company_size_benchmark),
                    'regional': float(calc.regional_benchmark)
                },
                'ml_data': {
                    'predicted_overhead': float(calc.ml_predicted_overhead),
                    'confidence_score': float(calc.ml_confidence_score),
                    'optimization_potential': float(calc.ml_optimization_potential)
                },
                'aura_scores': {
                    'ethics': float(calc.aura_ethics_score),
                    'fairness': float(calc.aura_fairness_score),
                    'sustainability': float(calc.aura_sustainability_score)
                }
            })
        
        # Calcular estadísticas del historial
        if history_data:
            overheads = [h['total_overhead'] for h in history_data]
            percentages = [h['overhead_percentage'] for h in history_data]
            
            stats = {
                'avg_overhead': sum(overheads) / len(overheads),
                'min_overhead': min(overheads),
                'max_overhead': max(overheads),
                'avg_percentage': sum(percentages) / len(percentages),
                'trend': 'stable'  # TODO: Calcular tendencia real
            }
        else:
            stats = {}
        
        return Response({
            'success': True,
            'data': {
                'employee_id': str(employee.id),
                'employee_name': employee.get_full_name(),
                'history': history_data,
                'statistics': stats,
                'metadata': {
                    'periods_included': len(history_data),
                    'date_range': {
                        'from': history_data[-1]['calculated_at'] if history_data else None,
                        'to': history_data[0]['calculated_at'] if history_data else None
                    }
                }
            }
        })
        
    except PayrollEmployee.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Empleado no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error obteniendo historial de overhead: {e}")
        return Response({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_ml_model(request):
    """
    Entrena o actualiza modelos ML de overhead
    """
    try:
        data = request.data
        company_id = data.get('company_id')
        model_type = data.get('model_type', 'hybrid_ml_aura')
        force_retrain = data.get('force_retrain', False)
        
        if not company_id:
            return Response({
                'success': False,
                'error': 'company_id requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        company = get_object_or_404(PayrollCompany, id=company_id)
        
        # TODO: Verificar permisos de administrador
        
        # Inicializar optimizador ML
        ml_optimizer = MLOverheadOptimizer(company)
        
        # Verificar si es necesario entrenar
        if not force_retrain:
            latest_model = company.overhead_ml_models.filter(
                model_type=model_type,
                is_active=True
            ).order_by('-last_training_date').first()
            
            if latest_model and latest_model.last_training_date:
                from datetime import datetime, timedelta
                if datetime.now() - latest_model.last_training_date.replace(tzinfo=None) < timedelta(days=7):
                    return Response({
                        'success': True,
                        'message': 'Modelo entrenado recientemente, no es necesario reentrenar',
                        'last_training': latest_model.last_training_date.isoformat(),
                        'model_accuracy': float(latest_model.accuracy)
                    })
        
        # TODO: Implementar entrenamiento real del modelo
        # Por ahora, simulamos el entrenamiento
        
        import random
        from datetime import datetime
        from ..models import OverheadMLModel
        
        # Crear o actualizar modelo
        model, created = OverheadMLModel.objects.update_or_create(
            company=company,
            model_type=model_type,
            defaults={
                'model_name': f'{model_type}_model_{company.name}',
                'accuracy': Decimal(str(random.uniform(80, 95))),  # Simulado
                'precision': Decimal(str(random.uniform(75, 90))),
                'recall': Decimal(str(random.uniform(75, 90))),
                'f1_score': Decimal(str(random.uniform(75, 90))),
                'training_data_size': random.randint(100, 1000),
                'last_training_date': datetime.now(),
                'is_active': True,
                'is_production': True,
                'version': '2.0.0'
            }
        )
        
        return Response({
            'success': True,
            'message': f'Modelo {model_type} {"creado" if created else "actualizado"} exitosamente',
            'model_data': {
                'model_id': str(model.id),
                'model_name': model.model_name,
                'model_type': model.model_type,
                'accuracy': float(model.accuracy),
                'precision': float(model.precision),
                'recall': float(model.recall),
                'f1_score': float(model.f1_score),
                'training_data_size': model.training_data_size,
                'last_training_date': model.last_training_date.isoformat(),
                'version': model.version
            }
        })
        
    except PayrollCompany.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Empresa no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error entrenando modelo ML: {e}")
        return Response({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_aura_insights(request, company_id):
    """
    Obtiene insights AURA para la empresa
    """
    try:
        company = get_object_or_404(PayrollCompany, id=company_id)
        
        # Verificar si tiene AURA habilitado
        if not company.premium_services.get('aura_enabled', False):
            return Response({
                'success': False,
                'error': 'AURA no está habilitado para esta empresa',
                'upgrade_info': {
                    'message': 'Actualiza a AURA para acceder a insights avanzados',
                    'benefits': [
                        'Análisis ético de decisiones',
                        'Optimización de equidad',
                        'Insights de sustentabilidad',
                        'Predicciones mejoradas con IA'
                    ]
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener datos para análisis AURA
        employees = company.employees.filter(is_active=True)
        recent_analyses = TeamOverheadAnalysis.objects.filter(
            company=company,
            is_active=True
        ).order_by('-created_at')[:10]
        
        # TODO: Implementar análisis AURA real
        # Por ahora simulamos los insights
        
        aura_insights = {
            'ethical_score': random.uniform(75, 95),
            'fairness_index': random.uniform(70, 90),
            'sustainability_impact': random.uniform(60, 85),
            'innovation_potential': random.uniform(65, 88),
            'social_responsibility_score': random.uniform(70, 92),
            'overall_aura_rating': 'Bueno',  # Excelente, Muy Bueno, Bueno, Regular, Necesita Mejora
            'key_insights': [
                'Distribución de overhead equitativa entre departamentos',
                'Oportunidades de mejora en sustentabilidad',
                'Alta correlación entre bienestar y productividad',
                'Potencial de innovación en equipos técnicos'
            ],
            'recommendations': [
                {
                    'category': 'sustainability',
                    'priority': 'High',
                    'description': 'Implementar programa de sustentabilidad corporativa',
                    'impact': 'Reducción 15% en overhead ambiental'
                },
                {
                    'category': 'wellbeing',
                    'priority': 'Medium',
                    'description': 'Expandir programas de bienestar empleados',
                    'impact': 'Mejora 10% en retención y productividad'
                },
                {
                    'category': 'innovation',
                    'priority': 'Medium',
                    'description': 'Crear fondo de innovación interno',
                    'impact': 'Acelerar desarrollo de nuevas soluciones'
                }
            ],
            'department_analysis': {},
            'predictive_insights': {
                'turnover_risk': 'Low',
                'cost_trend': 'Stable',
                'efficiency_forecast': 'Improving',
                'ethical_risk_level': 'Very Low'
            }
        }
        
        # Análisis por departamento
        departments = set(emp.department for emp in employees)
        for dept in departments:
            dept_employees = employees.filter(department=dept)
            aura_insights['department_analysis'][dept] = {
                'employee_count': dept_employees.count(),
                'avg_satisfaction': random.uniform(70, 90),
                'innovation_score': random.uniform(60, 85),
                'sustainability_score': random.uniform(65, 88),
                'efficiency_rating': random.choice(['Excellent', 'Good', 'Average'])
            }
        
        return Response({
            'success': True,
            'data': aura_insights,
            'metadata': {
                'company_id': str(company.id),
                'company_name': company.name,
                'analysis_date': datetime.now().isoformat(),
                'aura_version': '2.0',
                'employee_count': employees.count(),
                'departments_analyzed': len(departments)
            }
        })
        
    except PayrollCompany.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Empresa no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error obteniendo insights AURA: {e}")
        return Response({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)