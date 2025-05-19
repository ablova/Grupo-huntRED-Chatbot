"""
API para el dashboard de clientes.

Este módulo proporciona los endpoints de API que alimentan el dashboard 
interactivo para clientes, permitiéndoles visualizar métricas de satisfacción
y recibir recomendaciones personalizadas.
"""

import logging
import json
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count, Q, F, Sum, Case, When, Value, IntegerField
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from asgiref.sync import sync_to_async

from app.models import Person, Vacante, BusinessUnit, OnboardingProcess, OnboardingTask
from app.models_client_feedback import ClientFeedback, ClientFeedbackSchedule
from app.ml.onboarding_processor import OnboardingMLProcessor

logger = logging.getLogger(__name__)

class DashboardDataAPI(View):
    """
    API para proporcionar datos al dashboard de clientes.
    Incluye métricas, tendencias y recomendaciones.
    """
    
    @method_decorator(login_required)
    async def get(self, request):
        """
        Obtiene los datos para el dashboard según el tipo solicitado.
        """
        try:
            data_type = request.GET.get('data_type', 'summary')
            business_unit_id = request.GET.get('business_unit_id')
            empresa_id = request.GET.get('empresa_id')
            
            # Filtros temporales
            days = request.GET.get('days')
            if days:
                try:
                    days = int(days)
                    start_date = timezone.now() - timedelta(days=days)
                except ValueError:
                    return JsonResponse({'error': 'Valor de días inválido'}, status=400)
            else:
                # Por defecto, datos de los últimos 90 días
                days = 90
                start_date = timezone.now() - timedelta(days=days)
            
            # Retornar datos específicos según el tipo solicitado
            if data_type == 'summary':
                result = await self.get_summary_data(business_unit_id, empresa_id, start_date)
            elif data_type == 'satisfaction_trend':
                result = await self.get_satisfaction_trend(business_unit_id, empresa_id, start_date)
            elif data_type == 'onboarding_metrics':
                result = await self.get_onboarding_metrics(business_unit_id, empresa_id, start_date)
            elif data_type == 'candidate_satisfaction':
                result = await self.get_candidate_satisfaction(business_unit_id, empresa_id, start_date)
            elif data_type == 'client_satisfaction':
                result = await self.get_client_satisfaction(business_unit_id, empresa_id, start_date)
            elif data_type == 'recommendations':
                result = await self.get_recommendations(business_unit_id, empresa_id)
            else:
                return JsonResponse({'error': 'Tipo de datos no válido'}, status=400)
            
            return JsonResponse(result)
        
        except Exception as e:
            logger.error(f"Error en DashboardDataAPI.get: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    async def get_summary_data(self, business_unit_id=None, empresa_id=None, start_date=None):
        """
        Obtiene un resumen general con las métricas principales para el dashboard.
        """
        @sync_to_async
        def get_data():
            filters = {}
            
            if business_unit_id:
                filters['business_unit_id'] = business_unit_id
            
            # Métricas de candidatos contratados
            onboarding_filters = {}
            if empresa_id:
                onboarding_filters['vacancy__empresa_id'] = empresa_id
            
            if business_unit_id:
                onboarding_filters['vacancy__business_unit_id'] = business_unit_id
            
            if start_date:
                onboarding_filters['hire_date__gte'] = start_date
            
            # Obtener procesos de onboarding
            onboarding_processes = OnboardingProcess.objects.filter(**onboarding_filters)
            
            # Satisfacción de candidatos
            total_candidates = onboarding_processes.count()
            
            # Calcular satisfacción promedio manualmente
            satisfaction_scores = []
            for process in onboarding_processes:
                score = process.get_satisfaction_score()
                if score is not None:
                    satisfaction_scores.append(score)
            
            avg_candidate_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
            
            # Satisfacción de clientes
            client_feedback_filters = filters.copy()
            if empresa_id:
                client_feedback_filters['empresa_id'] = empresa_id
            
            if start_date:
                client_feedback_filters['completed_date__gte'] = start_date
            
            client_feedback = ClientFeedback.objects.filter(
                **client_feedback_filters,
                status='COMPLETED',
                satisfaction_score__isnull=False
            )
            
            avg_client_satisfaction = client_feedback.aggregate(
                avg=Avg('satisfaction_score')
            )['avg'] or 0
            
            # Tendencia de satisfacción (últimos 30 días vs período anterior)
            last_30_days = timezone.now() - timedelta(days=30)
            
            recent_candidate_scores = []
            previous_candidate_scores = []
            
            for process in onboarding_processes:
                if process.last_survey_date and process.last_survey_date >= last_30_days:
                    score = process.get_satisfaction_score()
                    if score is not None:
                        recent_candidate_scores.append(score)
                elif process.last_survey_date:
                    score = process.get_satisfaction_score()
                    if score is not None:
                        previous_candidate_scores.append(score)
            
            recent_candidate_avg = sum(recent_candidate_scores) / len(recent_candidate_scores) if recent_candidate_scores else 0
            previous_candidate_avg = sum(previous_candidate_scores) / len(previous_candidate_scores) if previous_candidate_scores else 0
            
            candidate_trend = 0
            if previous_candidate_avg > 0:
                candidate_trend = ((recent_candidate_avg - previous_candidate_avg) / previous_candidate_avg) * 100
            
            # Para clientes
            recent_client_feedback = client_feedback.filter(completed_date__gte=last_30_days)
            previous_client_feedback = client_feedback.filter(completed_date__lt=last_30_days)
            
            recent_client_avg = recent_client_feedback.aggregate(avg=Avg('satisfaction_score'))['avg'] or 0
            previous_client_avg = previous_client_feedback.aggregate(avg=Avg('satisfaction_score'))['avg'] or 0
            
            client_trend = 0
            if previous_client_avg > 0:
                client_trend = ((recent_client_avg - previous_client_avg) / previous_client_avg) * 100
            
            # Tasa de tareas completadas a tiempo
            onboarding_tasks = OnboardingTask.objects.filter(
                onboarding__in=onboarding_processes
            )
            
            total_tasks = onboarding_tasks.count()
            completed_tasks = onboarding_tasks.filter(status='COMPLETED').count()
            overdue_tasks = onboarding_tasks.filter(status='OVERDUE').count()
            
            task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            overdue_rate = (overdue_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                'period_days': int((timezone.now() - start_date).days),
                'total_candidates': total_candidates,
                'candidate_satisfaction': round(avg_candidate_satisfaction, 2),
                'candidate_satisfaction_trend': round(candidate_trend, 2),
                'client_satisfaction': round(avg_client_satisfaction, 2),
                'client_satisfaction_trend': round(client_trend, 2),
                'task_completion_rate': round(task_completion_rate, 2),
                'overdue_rate': round(overdue_rate, 2),
                'timestamp': timezone.now().isoformat()
            }
        
        return await get_data()
    
    async def get_satisfaction_trend(self, business_unit_id=None, empresa_id=None, start_date=None):
        """
        Obtiene datos de tendencia de satisfacción para gráficos temporales.
        """
        @sync_to_async
        def get_data():
            # Filtros base
            filters = {}
            
            if business_unit_id:
                filters['business_unit_id'] = business_unit_id
            
            # Filtros para procesos de onboarding
            onboarding_filters = {}
            if empresa_id:
                onboarding_filters['vacancy__empresa_id'] = empresa_id
            
            if business_unit_id:
                onboarding_filters['vacancy__business_unit_id'] = business_unit_id
            
            if start_date:
                onboarding_filters['hire_date__gte'] = start_date
            
            # Obtener procesos de onboarding
            onboarding_processes = OnboardingProcess.objects.filter(**onboarding_filters)
            
            # Para feedback de clientes
            client_feedback_filters = filters.copy()
            if empresa_id:
                client_feedback_filters['empresa_id'] = empresa_id
            
            if start_date:
                client_feedback_filters['completed_date__gte'] = start_date
            
            client_feedback = ClientFeedback.objects.filter(
                **client_feedback_filters,
                status='COMPLETED'
            )
            
            # Generar datos para gráfico de tendencia mensual (últimos 12 meses)
            end_date = timezone.now()
            months = []
            candidate_data = []
            client_data = []
            
            for i in range(12):
                month_end = end_date - timedelta(days=i*30)
                month_start = month_end - timedelta(days=30)
                month_label = month_end.strftime('%b %Y')
                
                # Datos de candidatos para este mes
                month_processes = onboarding_processes.filter(
                    last_survey_date__gte=month_start,
                    last_survey_date__lt=month_end
                )
                
                month_scores = []
                for process in month_processes:
                    score = process.get_satisfaction_score()
                    if score is not None:
                        month_scores.append(score)
                
                month_avg = sum(month_scores) / len(month_scores) if month_scores else None
                
                # Datos de clientes para este mes
                month_feedback = client_feedback.filter(
                    completed_date__gte=month_start,
                    completed_date__lt=month_end
                )
                
                month_client_avg = month_feedback.aggregate(avg=Avg('satisfaction_score'))['avg']
                
                months.insert(0, month_label)
                candidate_data.insert(0, month_avg)
                client_data.insert(0, month_client_avg)
            
            # Generar datos para satisfacción por período (días desde contratación)
            from app.models import SATISFACTION_PERIODS
            period_labels = [f"{p} días" for p in SATISFACTION_PERIODS]
            period_data = []
            
            for period in SATISFACTION_PERIODS:
                period_scores = []
                for process in onboarding_processes:
                    if not process.survey_responses:
                        continue
                        
                    period_key = str(period)
                    if period_key in process.survey_responses:
                        responses = process.survey_responses[period_key]
                        if 'general_satisfaction' in responses:
                            period_scores.append(float(responses['general_satisfaction']))
                
                period_avg = sum(period_scores) / len(period_scores) if period_scores else None
                period_data.append(period_avg)
            
            return {
                'monthly_trend': {
                    'labels': months,
                    'candidate_data': candidate_data,
                    'client_data': client_data
                },
                'period_trend': {
                    'labels': period_labels,
                    'data': period_data
                },
                'timestamp': timezone.now().isoformat()
            }
        
        return await get_data()
    
    async def get_onboarding_metrics(self, business_unit_id=None, empresa_id=None, start_date=None):
        """
        Obtiene métricas detalladas del proceso de onboarding.
        """
        @sync_to_async
        def get_data():
            # Filtros para procesos de onboarding
            onboarding_filters = {}
            if empresa_id:
                onboarding_filters['vacancy__empresa_id'] = empresa_id
            
            if business_unit_id:
                onboarding_filters['vacancy__business_unit_id'] = business_unit_id
            
            if start_date:
                onboarding_filters['hire_date__gte'] = start_date
            
            # Obtener procesos de onboarding
            onboarding_processes = OnboardingProcess.objects.filter(**onboarding_filters)
            
            # Métricas de tareas
            onboarding_tasks = OnboardingTask.objects.filter(
                onboarding__in=onboarding_processes
            )
            
            total_tasks = onboarding_tasks.count()
            task_status = onboarding_tasks.values('status').annotate(count=Count('id'))
            
            task_status_data = {}
            for status in task_status:
                task_status_data[status['status']] = status['count']
            
            # Tiempo promedio para completar tareas
            avg_completion_days = None
            completed_tasks = onboarding_tasks.filter(
                status='COMPLETED',
                completion_date__isnull=False,
                due_date__isnull=False
            )
            
            if completed_tasks.exists():
                total_days = 0
                count = 0
                
                for task in completed_tasks:
                    days_taken = (task.completion_date.date() - task.due_date.date()).days
                    total_days += days_taken
                    count += 1
                
                avg_completion_days = total_days / count if count > 0 else None
            
            # Distribución de prioridad de tareas
            task_priority = onboarding_tasks.values('priority').annotate(count=Count('id'))
            
            priority_data = {}
            for priority in task_priority:
                priority_data[priority['priority']] = priority['count']
            
            # Tareas más comunes
            common_tasks = onboarding_tasks.values('title').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            return {
                'total_processes': onboarding_processes.count(),
                'total_tasks': total_tasks,
                'task_status': task_status_data,
                'avg_completion_days': avg_completion_days,
                'task_priority': priority_data,
                'common_tasks': list(common_tasks),
                'timestamp': timezone.now().isoformat()
            }
        
        return await get_data()
    
    async def get_candidate_satisfaction(self, business_unit_id=None, empresa_id=None, start_date=None):
        """
        Obtiene datos detallados de satisfacción de candidatos.
        """
        @sync_to_async
        def get_data():
            # Filtros para procesos de onboarding
            onboarding_filters = {}
            if empresa_id:
                onboarding_filters['vacancy__empresa_id'] = empresa_id
            
            if business_unit_id:
                onboarding_filters['vacancy__business_unit_id'] = business_unit_id
            
            if start_date:
                onboarding_filters['hire_date__gte'] = start_date
            
            # Obtener procesos de onboarding
            onboarding_processes = OnboardingProcess.objects.filter(**onboarding_filters)
            
            # Analizar respuestas específicas a preguntas comunes
            question_data = {
                'position_match': {'yes': 0, 'partly': 0, 'no': 0},
                'team_integration': {'yes': 0, 'partly': 0, 'no': 0},
                'resources': {'yes': 0, 'partly': 0, 'no': 0}
            }
            
            total_responses = 0
            
            for process in onboarding_processes:
                if not process.survey_responses:
                    continue
                
                for period, responses in process.survey_responses.items():
                    total_responses += 1
                    
                    # Analizar respuestas a preguntas específicas
                    for question in question_data.keys():
                        if question in responses:
                            value = responses[question]
                            if value in question_data[question]:
                                question_data[question][value] += 1
            
            # Convertir conteos a porcentajes
            for question, values in question_data.items():
                for key in values:
                    if total_responses > 0:
                        question_data[question][key] = round((values[key] / total_responses) * 100, 2)
            
            # Obtener comentarios recientes
            recent_comments = []
            
            for process in onboarding_processes:
                if not process.survey_responses:
                    continue
                
                for period, responses in process.survey_responses.items():
                    if 'comments' in responses and responses['comments'].strip():
                        recent_comments.append({
                            'period': period,
                            'comment': responses['comments'],
                            'satisfaction': responses.get('general_satisfaction', 'N/A')
                        })
                        
                        if len(recent_comments) >= 10:
                            break
                
                if len(recent_comments) >= 10:
                    break
            
            # Distribuir por nivel de satisfacción
            satisfaction_distribution = {
                'high': 0,  # 8-10
                'medium': 0,  # 5-7
                'low': 0  # 1-4
            }
            
            satisfaction_scores = []
            for process in onboarding_processes:
                score = process.get_satisfaction_score()
                if score is not None:
                    satisfaction_scores.append(score)
                    
                    if score >= 8:
                        satisfaction_distribution['high'] += 1
                    elif score >= 5:
                        satisfaction_distribution['medium'] += 1
                    else:
                        satisfaction_distribution['low'] += 1
            
            # Convertir a porcentajes
            total_scores = len(satisfaction_scores)
            for key in satisfaction_distribution:
                if total_scores > 0:
                    satisfaction_distribution[key] = round((satisfaction_distribution[key] / total_scores) * 100, 2)
            
            return {
                'total_candidates': onboarding_processes.count(),
                'total_responses': total_responses,
                'question_data': question_data,
                'satisfaction_distribution': satisfaction_distribution,
                'recent_comments': recent_comments,
                'timestamp': timezone.now().isoformat()
            }
        
        return await get_data()
    
    async def get_client_satisfaction(self, business_unit_id=None, empresa_id=None, start_date=None):
        """
        Obtiene datos detallados de satisfacción de clientes.
        """
        @sync_to_async
        def get_data():
            # Filtros para feedback de clientes
            filters = {}
            
            if business_unit_id:
                filters['business_unit_id'] = business_unit_id
            
            if empresa_id:
                filters['empresa_id'] = empresa_id
            
            if start_date:
                filters['completed_date__gte'] = start_date
            
            # Obtener feedback completado
            client_feedback = ClientFeedback.objects.filter(
                **filters,
                status='COMPLETED'
            )
            
            # Analizar respuestas específicas a preguntas comunes
            question_data = {
                'clear_communication': {'yes': 0, 'partly': 0, 'no': 0},
                'candidate_adaptation': {'yes': 0, 'partly': 0, 'no': 0},
                'would_recommend': {'yes': 0, 'maybe': 0, 'no': 0}
            }
            
            total_responses = client_feedback.count()
            
            for feedback in client_feedback:
                if not feedback.responses:
                    continue
                
                # Analizar respuestas a preguntas específicas
                for question in question_data.keys():
                    if question in feedback.responses:
                        value = feedback.responses[question]
                        if value in question_data[question]:
                            question_data[question][value] += 1
            
            # Convertir conteos a porcentajes
            for question, values in question_data.items():
                for key in values:
                    if total_responses > 0:
                        question_data[question][key] = round((values[key] / total_responses) * 100, 2)
            
            # Métricas de calidad de candidatos
            candidate_quality_scores = []
            recruitment_speed_scores = []
            
            for feedback in client_feedback:
                if not feedback.responses:
                    continue
                
                if 'candidate_quality' in feedback.responses:
                    try:
                        score = float(feedback.responses['candidate_quality'])
                        candidate_quality_scores.append(score)
                    except (ValueError, TypeError):
                        pass
                
                if 'recruitment_speed' in feedback.responses:
                    try:
                        score = float(feedback.responses['recruitment_speed'])
                        recruitment_speed_scores.append(score)
                    except (ValueError, TypeError):
                        pass
            
            avg_candidate_quality = sum(candidate_quality_scores) / len(candidate_quality_scores) if candidate_quality_scores else 0
            avg_recruitment_speed = sum(recruitment_speed_scores) / len(recruitment_speed_scores) if recruitment_speed_scores else 0
            
            # Obtener sugerencias de mejora recientes
            recent_suggestions = []
            
            for feedback in client_feedback.order_by('-completed_date')[:10]:
                if not feedback.responses:
                    continue
                
                if 'improvement_suggestions' in feedback.responses and feedback.responses['improvement_suggestions'].strip():
                    recent_suggestions.append({
                        'empresa': feedback.empresa.name,
                        'date': feedback.completed_date.isoformat() if feedback.completed_date else None,
                        'suggestion': feedback.responses['improvement_suggestions'],
                        'satisfaction': feedback.satisfaction_score
                    })
            
            # Distribuir por nivel de satisfacción
            satisfaction_distribution = {
                'high': 0,  # 8-10
                'medium': 0,  # 5-7
                'low': 0  # 1-4
            }
            
            for feedback in client_feedback:
                if feedback.satisfaction_score is None:
                    continue
                
                if feedback.satisfaction_score >= 8:
                    satisfaction_distribution['high'] += 1
                elif feedback.satisfaction_score >= 5:
                    satisfaction_distribution['medium'] += 1
                else:
                    satisfaction_distribution['low'] += 1
            
            # Convertir a porcentajes
            for key in satisfaction_distribution:
                if total_responses > 0:
                    satisfaction_distribution[key] = round((satisfaction_distribution[key] / total_responses) * 100, 2)
            
            return {
                'total_feedback': total_responses,
                'question_data': question_data,
                'avg_candidate_quality': round(avg_candidate_quality, 2),
                'avg_recruitment_speed': round(avg_recruitment_speed, 2),
                'satisfaction_distribution': satisfaction_distribution,
                'recent_suggestions': recent_suggestions,
                'timestamp': timezone.now().isoformat()
            }
        
        return await get_data()
    
    async def get_recommendations(self, business_unit_id=None, empresa_id=None):
        """
        Obtiene recomendaciones personalizadas basadas en ML.
        """
        try:
            # Utilizar el procesador ML para generar recomendaciones
            ml_processor = OnboardingMLProcessor()
            
            if empresa_id:
                recommendations = await ml_processor.generate_client_recommendations(empresa_id)
            else:
                recommendations = await ml_processor.generate_bu_recommendations(business_unit_id)
            
            return {
                'recommendations': recommendations,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return {
                'recommendations': [],
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
