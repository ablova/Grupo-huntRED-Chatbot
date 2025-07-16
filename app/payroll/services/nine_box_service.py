"""
Servicio de Matriz 9 Boxes para huntRED® Payroll
Integrado con evaluaciones de desempeño y sistema de talento
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q, Count, Avg, F, Value
from django.db.models.functions import Coalesce

from app.payroll.models import (
    PayrollEmployee, NineBoxMatrix, PerformanceEvaluation,
    AttendanceRecord, PayrollFeedback, EmployeeRequest
)
from app.ats.models import Assessment, Interview  # Integración con ATS

logger = logging.getLogger(__name__)


class NineBoxService:
    """
    Servicio para gestión de la matriz 9 boxes
    """
    
    def __init__(self, company):
        self.company = company
    
    def create_nine_box_evaluation(self, employee: PayrollEmployee, evaluator, evaluation_data: Dict[str, Any]) -> NineBoxMatrix:
        """
        Crea una evaluación de matriz 9 boxes
        
        Args:
            employee: Empleado a evaluar
            evaluator: Usuario que evalúa
            evaluation_data: Datos de la evaluación
            
        Returns:
            NineBoxMatrix: Evaluación creada
        """
        try:
            # Calcular scores automáticamente si no se proporcionan
            if 'performance_score' not in evaluation_data:
                evaluation_data['performance_score'] = self._calculate_performance_score(employee)
            
            if 'potential_score' not in evaluation_data:
                evaluation_data['potential_score'] = self._calculate_potential_score(employee)
            
            # Determinar niveles
            performance_level = self._get_performance_level(evaluation_data['performance_score'])
            potential_level = self._get_potential_level(evaluation_data['potential_score'])
            
            # Calcular categoría del box
            box_category = self._calculate_box_category(
                evaluation_data['performance_score'],
                evaluation_data['potential_score']
            )
            
            # Crear evaluación
            nine_box = NineBoxMatrix.objects.create(
                employee=employee,
                evaluator=evaluator,
                performance_level=performance_level,
                potential_level=potential_level,
                box_category=box_category,
                performance_score=evaluation_data['performance_score'],
                potential_score=evaluation_data['potential_score'],
                performance_factors=evaluation_data.get('performance_factors', {}),
                potential_factors=evaluation_data.get('potential_factors', {}),
                development_plan=evaluation_data.get('development_plan', ''),
                career_path=evaluation_data.get('career_path', ''),
                retention_risk=self._calculate_retention_risk(employee, evaluation_data),
                recommended_actions=evaluation_data.get('recommended_actions', []),
                timeline=evaluation_data.get('timeline', ''),
                next_review_date=evaluation_data.get('next_review_date'),
                progress_notes=evaluation_data.get('progress_notes', '')
            )
            
            logger.info(f"Evaluación 9 boxes creada para {employee.get_full_name()}: Box {box_category}")
            return nine_box
            
        except Exception as e:
            logger.error(f"Error creando evaluación 9 boxes: {str(e)}")
            raise
    
    def update_nine_box_evaluation(self, nine_box: NineBoxMatrix, update_data: Dict[str, Any]) -> NineBoxMatrix:
        """
        Actualiza una evaluación 9 boxes existente
        
        Args:
            nine_box: Evaluación a actualizar
            update_data: Datos de actualización
            
        Returns:
            NineBoxMatrix: Evaluación actualizada
        """
        try:
            # Actualizar campos
            for field, value in update_data.items():
                if hasattr(nine_box, field):
                    setattr(nine_box, field, value)
            
            # Recalcular si se actualizaron scores
            if 'performance_score' in update_data or 'potential_score' in update_data:
                nine_box.box_category = self._calculate_box_category(
                    nine_box.performance_score,
                    nine_box.potential_score
                )
                nine_box.performance_level = self._get_performance_level(nine_box.performance_score)
                nine_box.potential_level = self._get_potential_level(nine_box.potential_score)
            
            nine_box.save()
            
            logger.info(f"Evaluación 9 boxes actualizada para {nine_box.employee.get_full_name()}")
            return nine_box
            
        except Exception as e:
            logger.error(f"Error actualizando evaluación 9 boxes: {str(e)}")
            raise
    
    def get_company_nine_box_matrix(self, include_inactive: bool = False) -> Dict[str, Any]:
        """
        Obtiene la matriz 9 boxes completa de la empresa
        
        Args:
            include_inactive: Incluir empleados inactivos
            
        Returns:
            Dict con la matriz completa
        """
        try:
            # Obtener evaluaciones activas
            evaluations = NineBoxMatrix.objects.filter(
                employee__company=self.company,
                is_active=True
            ).select_related('employee', 'evaluator')
            
            if not include_inactive:
                evaluations = evaluations.filter(employee__is_active=True)
            
            # Organizar por box
            matrix = {
                '1': [], '2': [], '3': [],
                '4': [], '5': [], '6': [],
                '7': [], '8': [], '9': []
            }
            
            for evaluation in evaluations:
                matrix[evaluation.box_category].append({
                    'employee_id': evaluation.employee.id,
                    'employee_name': evaluation.employee.get_full_name(),
                    'department': evaluation.employee.department,
                    'job_title': evaluation.employee.job_title,
                    'performance_score': float(evaluation.performance_score),
                    'potential_score': float(evaluation.potential_score),
                    'retention_risk': evaluation.retention_risk,
                    'evaluation_date': evaluation.created_at.strftime('%Y-%m-%d'),
                    'next_review': evaluation.next_review_date.strftime('%Y-%m-%d') if evaluation.next_review_date else None
                })
            
            # Estadísticas
            stats = self._calculate_matrix_statistics(matrix)
            
            return {
                'matrix': matrix,
                'statistics': stats,
                'total_employees': sum(len(employees) for employees in matrix.values()),
                'last_updated': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo matriz 9 boxes: {str(e)}")
            return {'error': str(e)}
    
    def get_employee_nine_box_history(self, employee: PayrollEmployee) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de evaluaciones 9 boxes de un empleado
        
        Args:
            employee: Empleado
            
        Returns:
            Lista con historial de evaluaciones
        """
        try:
            evaluations = NineBoxMatrix.objects.filter(
                employee=employee
            ).order_by('-created_at')
            
            history = []
            for evaluation in evaluations:
                history.append({
                    'evaluation_id': evaluation.id,
                    'box_category': evaluation.box_category,
                    'box_description': evaluation.get_box_description(),
                    'performance_score': float(evaluation.performance_score),
                    'potential_score': float(evaluation.potential_score),
                    'performance_level': evaluation.get_performance_level_display(),
                    'potential_level': evaluation.get_potential_level_display(),
                    'retention_risk': evaluation.retention_risk,
                    'evaluator': evaluation.evaluator.get_full_name(),
                    'evaluation_date': evaluation.created_at.strftime('%Y-%m-%d'),
                    'development_plan': evaluation.development_plan,
                    'recommended_actions': evaluation.recommended_actions,
                    'progress_notes': evaluation.progress_notes
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error obteniendo historial 9 boxes: {str(e)}")
            return []
    
    def generate_nine_box_report(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Genera reporte completo de matriz 9 boxes
        
        Args:
            filters: Filtros opcionales
            
        Returns:
            Dict con reporte completo
        """
        try:
            # Obtener matriz
            matrix_data = self.get_company_nine_box_matrix()
            
            if 'error' in matrix_data:
                return matrix_data
            
            # Análisis por departamento
            department_analysis = self._analyze_by_department(matrix_data['matrix'])
            
            # Análisis de retención
            retention_analysis = self._analyze_retention_risks(matrix_data['matrix'])
            
            # Tendencias temporales
            trends = self._analyze_temporal_trends()
            
            # Recomendaciones estratégicas
            recommendations = self._generate_strategic_recommendations(matrix_data['matrix'])
            
            return {
                'matrix_data': matrix_data,
                'department_analysis': department_analysis,
                'retention_analysis': retention_analysis,
                'temporal_trends': trends,
                'strategic_recommendations': recommendations,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte 9 boxes: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_performance_score(self, employee: PayrollEmployee) -> Decimal:
        """
        Calcula score de desempeño basado en múltiples factores
        """
        try:
            # Obtener evaluación de desempeño más reciente
            latest_evaluation = PerformanceEvaluation.objects.filter(
                employee=employee,
                status='completed'
            ).order_by('-evaluation_period_end').first()
            
            if latest_evaluation:
                # Usar calificación general de la evaluación
                return Decimal(str(latest_evaluation.overall_rating * 20))  # Convertir 1-5 a 0-100
            
            # Calcular basado en asistencia si no hay evaluación
            attendance_score = self._calculate_attendance_score(employee)
            
            # Calcular basado en feedback
            feedback_score = self._calculate_feedback_score(employee)
            
            # Promedio ponderado
            return (attendance_score * 0.6 + feedback_score * 0.4)
            
        except Exception as e:
            logger.error(f"Error calculando performance score: {str(e)}")
            return Decimal('70.0')  # Score por defecto
    
    def _calculate_potential_score(self, employee: PayrollEmployee) -> Decimal:
        """
        Calcula score de potencial basado en múltiples factores
        """
        try:
            # Factores de potencial
            factors = {}
            
            # 1. Antigüedad y crecimiento
            hire_date = employee.hire_date
            years_of_service = (date.today() - hire_date).days / 365.25
            factors['tenure_growth'] = min(100, years_of_service * 10)  # Máximo 10 años
            
            # 2. Evaluaciones de ATS (si existe)
            if employee.ats_candidate_id:
                ats_score = self._get_ats_assessment_score(employee)
                factors['ats_assessment'] = ats_score
            
            # 3. Feedback positivo
            positive_feedback = PayrollFeedback.objects.filter(
                employee=employee,
                is_resolved=True
            ).count()
            factors['feedback_quality'] = min(100, positive_feedback * 10)
            
            # 4. Iniciativa (solicitudes de desarrollo)
            development_requests = EmployeeRequest.objects.filter(
                employee=employee,
                request_type__in=['training', 'advancement']
            ).count()
            factors['initiative'] = min(100, development_requests * 15)
            
            # 5. Adaptabilidad (cambios de turno exitosos)
            successful_changes = ShiftChangeRequest.objects.filter(
                employee=employee,
                status='approved'
            ).count()
            factors['adaptability'] = min(100, successful_changes * 20)
            
            # Promedio ponderado
            weights = {
                'tenure_growth': 0.2,
                'ats_assessment': 0.3,
                'feedback_quality': 0.2,
                'initiative': 0.15,
                'adaptability': 0.15
            }
            
            total_score = 0
            total_weight = 0
            
            for factor, score in factors.items():
                if factor in weights:
                    total_score += score * weights[factor]
                    total_weight += weights[factor]
            
            return Decimal(str(total_score / total_weight if total_weight > 0 else 70.0))
            
        except Exception as e:
            logger.error(f"Error calculando potential score: {str(e)}")
            return Decimal('70.0')
    
    def _calculate_attendance_score(self, employee: PayrollEmployee) -> Decimal:
        """Calcula score basado en asistencia"""
        try:
            # Últimos 90 días
            end_date = date.today()
            start_date = end_date - timedelta(days=90)
            
            attendance_records = AttendanceRecord.objects.filter(
                employee=employee,
                date__range=[start_date, end_date]
            )
            
            if not attendance_records:
                return Decimal('70.0')
            
            total_days = attendance_records.count()
            present_days = attendance_records.filter(status='present').count()
            attendance_rate = (present_days / total_days) * 100
            
            return Decimal(str(attendance_rate))
            
        except Exception as e:
            logger.error(f"Error calculando attendance score: {str(e)}")
            return Decimal('70.0')
    
    def _calculate_feedback_score(self, employee: PayrollEmployee) -> Decimal:
        """Calcula score basado en feedback"""
        try:
            feedbacks = PayrollFeedback.objects.filter(
                employee=employee,
                is_resolved=True
            )
            
            if not feedbacks:
                return Decimal('70.0')
            
            # Score basado en resolución rápida y satisfacción
            resolved_count = feedbacks.count()
            quick_resolution_count = feedbacks.filter(
                response_date__lte=F('created_at') + timedelta(days=3)
            ).count()
            
            quick_resolution_rate = (quick_resolution_count / resolved_count) * 100
            return Decimal(str(quick_resolution_rate))
            
        except Exception as e:
            logger.error(f"Error calculando feedback score: {str(e)}")
            return Decimal('70.0')
    
    def _get_ats_assessment_score(self, employee: PayrollEmployee) -> Decimal:
        """Obtiene score de evaluaciones ATS"""
        try:
            if not employee.ats_candidate_id:
                return Decimal('70.0')
            
            # Buscar evaluaciones en ATS
            assessments = Assessment.objects.filter(
                candidate_id=employee.ats_candidate_id
            ).order_by('-created_at')
            
            if not assessments:
                return Decimal('70.0')
            
            # Promedio de scores
            total_score = sum(float(assessment.score) for assessment in assessments if assessment.score)
            avg_score = total_score / len(assessments)
            
            return Decimal(str(avg_score * 20))  # Convertir a escala 0-100
            
        except Exception as e:
            logger.error(f"Error obteniendo ATS assessment score: {str(e)}")
            return Decimal('70.0')
    
    def _get_performance_level(self, score: Decimal) -> str:
        """Determina nivel de desempeño basado en score"""
        if score >= 80:
            return 'high'
        elif score >= 60:
            return 'medium'
        else:
            return 'low'
    
    def _get_potential_level(self, score: Decimal) -> str:
        """Determina nivel de potencial basado en score"""
        if score >= 80:
            return 'high'
        elif score >= 60:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_box_category(self, performance_score: Decimal, potential_score: Decimal) -> str:
        """Calcula categoría del box basado en scores"""
        if performance_score >= 80 and potential_score >= 80:
            return '1'
        elif performance_score >= 80 and 60 <= potential_score < 80:
            return '2'
        elif performance_score >= 80 and potential_score < 60:
            return '3'
        elif 60 <= performance_score < 80 and potential_score >= 80:
            return '4'
        elif 60 <= performance_score < 80 and 60 <= potential_score < 80:
            return '5'
        elif 60 <= performance_score < 80 and potential_score < 60:
            return '6'
        elif performance_score < 60 and potential_score >= 80:
            return '7'
        elif performance_score < 60 and 60 <= potential_score < 80:
            return '8'
        else:
            return '9'
    
    def _calculate_retention_risk(self, employee: PayrollEmployee, evaluation_data: Dict[str, Any]) -> str:
        """Calcula riesgo de retención"""
        try:
            risk_factors = 0
            
            # Score bajo de potencial
            if evaluation_data.get('potential_score', 100) < 60:
                risk_factors += 2
            
            # Antigüedad baja
            years_of_service = (date.today() - employee.hire_date).days / 365.25
            if years_of_service < 1:
                risk_factors += 1
            
            # Feedback negativo reciente
            recent_negative_feedback = PayrollFeedback.objects.filter(
                employee=employee,
                created_at__gte=timezone.now() - timedelta(days=30),
                priority__in=['high', 'urgent']
            ).count()
            risk_factors += recent_negative_feedback
            
            # Solicitudes de cambio de turno frecuentes
            frequent_shift_requests = ShiftChangeRequest.objects.filter(
                employee=employee,
                created_at__gte=timezone.now() - timedelta(days=90)
            ).count()
            if frequent_shift_requests > 3:
                risk_factors += 1
            
            # Determinar nivel de riesgo
            if risk_factors >= 4:
                return 'critical'
            elif risk_factors >= 2:
                return 'high'
            elif risk_factors >= 1:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"Error calculando retention risk: {str(e)}")
            return 'medium'
    
    def _calculate_matrix_statistics(self, matrix: Dict[str, List]) -> Dict[str, Any]:
        """Calcula estadísticas de la matriz"""
        try:
            stats = {
                'total_employees': sum(len(employees) for employees in matrix.values()),
                'box_distribution': {box: len(employees) for box, employees in matrix.items()},
                'high_potential_count': len(matrix['1']) + len(matrix['2']) + len(matrix['4']),
                'critical_retention_count': sum(
                    1 for employees in matrix.values() 
                    for emp in employees 
                    if emp.get('retention_risk') == 'critical'
                ),
                'avg_performance_score': 0,
                'avg_potential_score': 0
            }
            
            # Calcular promedios
            total_performance = 0
            total_potential = 0
            total_count = 0
            
            for employees in matrix.values():
                for emp in employees:
                    total_performance += emp.get('performance_score', 0)
                    total_potential += emp.get('potential_score', 0)
                    total_count += 1
            
            if total_count > 0:
                stats['avg_performance_score'] = total_performance / total_count
                stats['avg_potential_score'] = total_potential / total_count
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculando estadísticas: {str(e)}")
            return {}
    
    def _analyze_by_department(self, matrix: Dict[str, List]) -> Dict[str, Any]:
        """Analiza distribución por departamento"""
        try:
            department_analysis = {}
            
            for box, employees in matrix.items():
                for emp in employees:
                    dept = emp.get('department', 'Sin departamento')
                    if dept not in department_analysis:
                        department_analysis[dept] = {
                            'total': 0,
                            'boxes': {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0, '9': 0},
                            'high_potential': 0,
                            'avg_performance': 0,
                            'avg_potential': 0
                        }
                    
                    department_analysis[dept]['total'] += 1
                    department_analysis[dept]['boxes'][box] += 1
                    
                    if box in ['1', '2', '4']:
                        department_analysis[dept]['high_potential'] += 1
            
            # Calcular promedios por departamento
            for dept, data in department_analysis.items():
                total_performance = 0
                total_potential = 0
                count = 0
                
                for box, employees in matrix.items():
                    for emp in employees:
                        if emp.get('department') == dept:
                            total_performance += emp.get('performance_score', 0)
                            total_potential += emp.get('potential_score', 0)
                            count += 1
                
                if count > 0:
                    data['avg_performance'] = total_performance / count
                    data['avg_potential'] = total_potential / count
            
            return department_analysis
            
        except Exception as e:
            logger.error(f"Error analizando por departamento: {str(e)}")
            return {}
    
    def _analyze_retention_risks(self, matrix: Dict[str, List]) -> Dict[str, Any]:
        """Analiza riesgos de retención"""
        try:
            retention_analysis = {
                'critical_risk': [],
                'high_risk': [],
                'medium_risk': [],
                'low_risk': [],
                'total_by_risk': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            }
            
            for employees in matrix.values():
                for emp in employees:
                    risk = emp.get('retention_risk', 'medium')
                    retention_analysis[f'{risk}_risk'].append({
                        'employee_name': emp.get('employee_name'),
                        'department': emp.get('department'),
                        'box_category': emp.get('box_category'),
                        'performance_score': emp.get('performance_score'),
                        'potential_score': emp.get('potential_score')
                    })
                    retention_analysis['total_by_risk'][risk] += 1
            
            return retention_analysis
            
        except Exception as e:
            logger.error(f"Error analizando riesgos de retención: {str(e)}")
            return {}
    
    def _analyze_temporal_trends(self) -> Dict[str, Any]:
        """Analiza tendencias temporales"""
        try:
            # Últimos 12 meses
            end_date = date.today()
            start_date = end_date - timedelta(days=365)
            
            evaluations = NineBoxMatrix.objects.filter(
                employee__company=self.company,
                created_at__date__range=[start_date, end_date]
            ).order_by('created_at')
            
            trends = {
                'monthly_distribution': {},
                'box_movements': {},
                'performance_trends': [],
                'potential_trends': []
            }
            
            # Análisis mensual
            for evaluation in evaluations:
                month_key = evaluation.created_at.strftime('%Y-%m')
                if month_key not in trends['monthly_distribution']:
                    trends['monthly_distribution'][month_key] = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0, '9': 0}
                
                trends['monthly_distribution'][month_key][evaluation.box_category] += 1
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analizando tendencias temporales: {str(e)}")
            return {}
    
    def _generate_strategic_recommendations(self, matrix: Dict[str, List]) -> List[Dict[str, Any]]:
        """Genera recomendaciones estratégicas"""
        try:
            recommendations = []
            
            # Análisis de talento crítico
            critical_talent = matrix['1'] + matrix['2']
            if len(critical_talent) < 3:
                recommendations.append({
                    'type': 'critical_talent',
                    'priority': 'high',
                    'title': 'Desarrollo de Talento Crítico',
                    'description': f'Solo {len(critical_talent)} empleados en boxes 1 y 2. Necesario desarrollar más líderes.',
                    'actions': [
                        'Identificar empleados con potencial en boxes 4 y 7',
                        'Implementar programas de desarrollo de liderazgo',
                        'Crear planes de sucesión'
                    ]
                })
            
            # Análisis de retención crítica
            critical_retention = sum(
                1 for employees in matrix.values() 
                for emp in employees 
                if emp.get('retention_risk') == 'critical'
            )
            
            if critical_retention > 0:
                recommendations.append({
                    'type': 'retention',
                    'priority': 'critical',
                    'title': 'Riesgo de Retención Crítico',
                    'description': f'{critical_retention} empleados con riesgo crítico de retención.',
                    'actions': [
                        'Revisar políticas de compensación',
                        'Implementar programas de engagement',
                        'Entrevistas de salida preventivas'
                    ]
                })
            
            # Análisis de boxes 8 y 9
            low_performers = len(matrix['8']) + len(matrix['9'])
            if low_performers > len(matrix['1']) + len(matrix['2']):
                recommendations.append({
                    'type': 'performance',
                    'priority': 'medium',
                    'title': 'Optimización de Desempeño',
                    'description': f'Muchos empleados en boxes 8 y 9 ({low_performers}).',
                    'actions': [
                        'Implementar programas de mejora de desempeño',
                        'Revisar procesos de selección',
                        'Capacitación específica'
                    ]
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return [] 