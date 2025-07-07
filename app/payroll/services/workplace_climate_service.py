"""
Servicio de Clima Laboral y Detección Inteligente huntRED®
Análisis de sentimientos, detección de bajas y recomendaciones proactivas
"""
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

from django.utils import timezone
from django.db.models import Q, Avg, Count
from textblob import TextBlob
import numpy as np

from ..models import PayrollEmployee, AttendanceRecord, EmployeeRequest
from .ml_attendance_service import MLAttendanceService

logger = logging.getLogger(__name__)


class WorkplaceClimateService:
    """
    Servicio de análisis de clima laboral y detección inteligente
    """
    
    def __init__(self, company):
        self.company = company
        self.ml_service = MLAttendanceService(company)
    
    def analyze_workplace_climate(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Analiza el clima laboral de la empresa
        
        Args:
            period_days: Días a analizar
            
        Returns:
            Análisis completo del clima laboral
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=period_days)
            
            # Obtener datos del período
            employees = self.company.employees.filter(is_active=True)
            attendance_records = AttendanceRecord.objects.filter(
                employee__company=self.company,
                date__range=[start_date, end_date]
            )
            requests = EmployeeRequest.objects.filter(
                employee__company=self.company,
                created_at__date__range=[start_date, end_date]
            )
            
            # Análisis de asistencia
            attendance_analysis = self._analyze_attendance_patterns(attendance_records)
            
            # Análisis de solicitudes
            requests_analysis = self._analyze_requests_patterns(requests)
            
            # Análisis de sentimientos
            sentiment_analysis = self._analyze_sentiments(requests)
            
            # Detección de riesgos
            risk_analysis = self._detect_risks(employees, attendance_records, requests)
            
            # Recomendaciones
            recommendations = self._generate_recommendations(
                attendance_analysis, requests_analysis, sentiment_analysis, risk_analysis
            )
            
            # Calcular score general
            overall_score = self._calculate_climate_score(
                attendance_analysis, requests_analysis, sentiment_analysis, risk_analysis
            )
            
            return {
                'success': True,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days_analyzed': period_days
                },
                'overall_score': overall_score,
                'attendance_analysis': attendance_analysis,
                'requests_analysis': requests_analysis,
                'sentiment_analysis': sentiment_analysis,
                'risk_analysis': risk_analysis,
                'recommendations': recommendations,
                'analysis_date': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analizando clima laboral: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def detect_termination_risks(self) -> Dict[str, Any]:
        """
        Detecta empleados con riesgo de terminación
        
        Returns:
            Lista de empleados en riesgo con scores
        """
        try:
            employees = self.company.employees.filter(is_active=True)
            risks = []
            
            for employee in employees:
                risk_score = self._calculate_termination_risk(employee)
                
                if risk_score > 0.3:  # Umbral de riesgo
                    risks.append({
                        'employee_id': str(employee.id),
                        'employee_name': employee.get_full_name(),
                        'employee_number': employee.employee_number,
                        'department': employee.department,
                        'risk_score': risk_score,
                        'risk_level': self._get_risk_level(risk_score),
                        'risk_factors': self._identify_risk_factors(employee),
                        'recommendations': self._get_risk_recommendations(employee, risk_score)
                    })
            
            # Ordenar por score de riesgo
            risks.sort(key=lambda x: x['risk_score'], reverse=True)
            
            return {
                'success': True,
                'total_employees': employees.count(),
                'employees_at_risk': len(risks),
                'risk_threshold': 0.3,
                'risks': risks,
                'analysis_date': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detectando riesgos de terminación: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_employee_sentiment(self, employee: PayrollEmployee, period_days: int = 90) -> Dict[str, Any]:
        """
        Analiza sentimientos de un empleado específico
        
        Args:
            employee: Empleado a analizar
            period_days: Días a analizar
            
        Returns:
            Análisis de sentimientos del empleado
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=period_days)
            
            # Obtener solicitudes del empleado
            requests = EmployeeRequest.objects.filter(
                employee=employee,
                created_at__date__range=[start_date, end_date]
            )
            
            # Analizar sentimientos en las solicitudes
            sentiments = []
            for request in requests:
                sentiment = self._analyze_text_sentiment(request.reason)
                sentiments.append({
                    'date': request.created_at.date().isoformat(),
                    'request_type': request.request_type,
                    'sentiment_score': sentiment['score'],
                    'sentiment_label': sentiment['label'],
                    'text': request.reason[:100] + "..." if len(request.reason) > 100 else request.reason
                })
            
            # Calcular tendencias
            if sentiments:
                avg_sentiment = np.mean([s['sentiment_score'] for s in sentiments])
                sentiment_trend = self._calculate_sentiment_trend(sentiments)
            else:
                avg_sentiment = 0
                sentiment_trend = 'neutral'
            
            return {
                'success': True,
                'employee_name': employee.get_full_name(),
                'period_days': period_days,
                'total_requests': len(requests),
                'average_sentiment': avg_sentiment,
                'sentiment_trend': sentiment_trend,
                'sentiment_history': sentiments,
                'analysis_date': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analizando sentimientos de {employee.get_full_name()}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_proactive_recommendations(self) -> Dict[str, Any]:
        """
        Genera recomendaciones proactivas para RH
        
        Returns:
            Lista de recomendaciones priorizadas
        """
        try:
            recommendations = []
            
            # Analizar clima laboral
            climate = self.analyze_workplace_climate()
            if climate['success']:
                if climate['overall_score'] < 0.6:
                    recommendations.append({
                        'type': 'climate_improvement',
                        'priority': 'high',
                        'title': 'Mejorar Clima Laboral',
                        'description': f'El clima laboral está en {climate["overall_score"]:.1%}. Considerar encuestas de satisfacción.',
                        'actions': [
                            'Realizar encuesta de clima laboral',
                            'Revisar políticas de reconocimiento',
                            'Implementar programas de bienestar'
                        ]
                    })
            
            # Detectar riesgos de terminación
            risks = self.detect_termination_risks()
            if risks['success'] and risks['employees_at_risk'] > 0:
                recommendations.append({
                    'type': 'retention',
                    'priority': 'high',
                    'title': 'Prevenir Rotación',
                    'description': f'{risks["employees_at_risk"]} empleados con riesgo de terminación.',
                    'actions': [
                        'Revisar empleados en riesgo',
                        'Implementar programas de retención',
                        'Mejorar comunicación con empleados'
                    ]
                })
            
            # Analizar patrones de asistencia
            attendance_patterns = self._analyze_attendance_trends()
            if attendance_patterns['absenteeism_trend'] == 'increasing':
                recommendations.append({
                    'type': 'attendance',
                    'priority': 'medium',
                    'title': 'Controlar Ausentismo',
                    'description': 'Tendencia creciente en ausentismo.',
                    'actions': [
                        'Revisar causas de ausentismo',
                        'Implementar políticas de flexibilidad',
                        'Mejorar condiciones de trabajo'
                    ]
                })
            
            # Recomendaciones de capacitación
            training_needs = self._identify_training_needs()
            if training_needs:
                recommendations.append({
                    'type': 'training',
                    'priority': 'medium',
                    'title': 'Oportunidades de Capacitación',
                    'description': f'Identificadas {len(training_needs)} áreas de mejora.',
                    'actions': [
                        'Desarrollar plan de capacitación',
                        'Ofertar cursos relevantes',
                        'Establecer métricas de mejora'
                    ]
                })
            
            return {
                'success': True,
                'total_recommendations': len(recommendations),
                'high_priority': len([r for r in recommendations if r['priority'] == 'high']),
                'medium_priority': len([r for r in recommendations if r['priority'] == 'medium']),
                'recommendations': recommendations,
                'generated_date': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_attendance_patterns(self, records) -> Dict[str, Any]:
        """Analiza patrones de asistencia"""
        if not records.exists():
            return {
                'total_records': 0,
                'attendance_rate': 0,
                'absenteeism_rate': 0,
                'late_arrivals': 0,
                'early_departures': 0,
                'anomalies': 0
            }
        
        total_records = records.count()
        present_records = records.filter(status='present').count()
        absent_records = records.filter(status='absent').count()
        late_records = records.filter(status='late').count()
        anomaly_records = records.filter(ml_anomaly_detected=True).count()
        
        attendance_rate = present_records / total_records if total_records > 0 else 0
        absenteeism_rate = absent_records / total_records if total_records > 0 else 0
        
        return {
            'total_records': total_records,
            'attendance_rate': attendance_rate,
            'absenteeism_rate': absenteeism_rate,
            'late_arrivals': late_records,
            'early_departures': 0,  # Implementar lógica específica
            'anomalies': anomaly_records,
            'trend': self._calculate_attendance_trend(records)
        }
    
    def _analyze_requests_patterns(self, requests) -> Dict[str, Any]:
        """Analiza patrones de solicitudes"""
        if not requests.exists():
            return {
                'total_requests': 0,
                'request_types': {},
                'approval_rate': 0,
                'avg_processing_time': 0
            }
        
        total_requests = requests.count()
        approved_requests = requests.filter(status='approved').count()
        pending_requests = requests.filter(status='pending').count()
        
        # Análisis por tipo
        request_types = {}
        for request_type in ['vacation', 'permission', 'other']:
            type_count = requests.filter(request_type=request_type).count()
            request_types[request_type] = {
                'count': type_count,
                'percentage': type_count / total_requests if total_requests > 0 else 0
            }
        
        # Tiempo promedio de procesamiento
        processed_requests = requests.filter(
            Q(status='approved') | Q(status='rejected')
        ).exclude(approval_date__isnull=True)
        
        avg_processing_time = 0
        if processed_requests.exists():
            total_days = 0
            for request in processed_requests:
                if request.approval_date:
                    days = (request.approval_date - request.created_at).days
                    total_days += days
            avg_processing_time = total_days / processed_requests.count()
        
        return {
            'total_requests': total_requests,
            'approved_requests': approved_requests,
            'pending_requests': pending_requests,
            'approval_rate': approved_requests / total_requests if total_requests > 0 else 0,
            'request_types': request_types,
            'avg_processing_time': avg_processing_time
        }
    
    def _analyze_sentiments(self, requests) -> Dict[str, Any]:
        """Analiza sentimientos en solicitudes"""
        if not requests.exists():
            return {
                'total_analyzed': 0,
                'average_sentiment': 0,
                'sentiment_distribution': {},
                'trend': 'neutral'
            }
        
        sentiments = []
        for request in requests:
            if request.reason:
                sentiment = self._analyze_text_sentiment(request.reason)
                sentiments.append(sentiment['score'])
        
        if sentiments:
            avg_sentiment = np.mean(sentiments)
            
            # Distribución de sentimientos
            positive = len([s for s in sentiments if s > 0.1])
            neutral = len([s for s in sentiments if -0.1 <= s <= 0.1])
            negative = len([s for s in sentiments if s < -0.1])
            
            sentiment_distribution = {
                'positive': {'count': positive, 'percentage': positive / len(sentiments)},
                'neutral': {'count': neutral, 'percentage': neutral / len(sentiments)},
                'negative': {'count': negative, 'percentage': negative / len(sentiments)}
            }
            
            # Tendencia
            trend = self._calculate_sentiment_trend_from_scores(sentiments)
        else:
            avg_sentiment = 0
            sentiment_distribution = {}
            trend = 'neutral'
        
        return {
            'total_analyzed': len(sentiments),
            'average_sentiment': avg_sentiment,
            'sentiment_distribution': sentiment_distribution,
            'trend': trend
        }
    
    def _detect_risks(self, employees, attendance_records, requests) -> Dict[str, Any]:
        """Detecta riesgos generales"""
        risks = []
        
        # Riesgo de rotación alta
        if employees.count() > 10:
            high_risk_employees = 0
            for employee in employees:
                risk_score = self._calculate_termination_risk(employee)
                if risk_score > 0.5:
                    high_risk_employees += 1
            
            if high_risk_employees > employees.count() * 0.1:  # Más del 10%
                risks.append({
                    'type': 'high_turnover_risk',
                    'severity': 'high',
                    'description': f'{high_risk_employees} empleados con alto riesgo de rotación',
                    'impact': 'Pérdida de talento y conocimiento'
                })
        
        # Riesgo de clima laboral negativo
        if requests.exists():
            negative_requests = requests.filter(
                Q(request_type='complaint') | Q(reason__icontains='problema')
            ).count()
            
            if negative_requests > requests.count() * 0.2:  # Más del 20%
                risks.append({
                    'type': 'negative_workplace_climate',
                    'severity': 'medium',
                    'description': 'Alto número de quejas y problemas',
                    'impact': 'Disminución de productividad y satisfacción'
                })
        
        return {
            'total_risks': len(risks),
            'high_severity': len([r for r in risks if r['severity'] == 'high']),
            'medium_severity': len([r for r in risks if r['severity'] == 'medium']),
            'risks': risks
        }
    
    def _calculate_termination_risk(self, employee: PayrollEmployee) -> float:
        """Calcula score de riesgo de terminación para un empleado"""
        risk_factors = []
        
        # Factor 1: Ausentismo reciente
        recent_attendance = AttendanceRecord.objects.filter(
            employee=employee,
            date__gte=date.today() - timedelta(days=30)
        )
        
        if recent_attendance.exists():
            attendance_rate = recent_attendance.filter(status='present').count() / recent_attendance.count()
            if attendance_rate < 0.9:  # Menos del 90%
                risk_factors.append(0.3)
        
        # Factor 2: Solicitudes recientes
        recent_requests = EmployeeRequest.objects.filter(
            employee=employee,
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        if recent_requests.count() > 3:  # Muchas solicitudes
            risk_factors.append(0.2)
        
        # Factor 3: Anomalías ML
        ml_anomalies = AttendanceRecord.objects.filter(
            employee=employee,
            ml_anomaly_detected=True,
            date__gte=date.today() - timedelta(days=60)
        ).count()
        
        if ml_anomalies > 5:  # Muchas anomalías
            risk_factors.append(0.25)
        
        # Factor 4: Antigüedad baja
        seniority_years = (date.today() - employee.hire_date).days / 365
        if seniority_years < 1:  # Menos de 1 año
            risk_factors.append(0.15)
        
        # Factor 5: Sentimientos negativos
        sentiment_analysis = self.analyze_employee_sentiment(employee, 30)
        if sentiment_analysis['success'] and sentiment_analysis['average_sentiment'] < -0.2:
            risk_factors.append(0.2)
        
        # Calcular score total
        if risk_factors:
            return min(sum(risk_factors), 1.0)
        else:
            return 0.0
    
    def _identify_risk_factors(self, employee: PayrollEmployee) -> List[str]:
        """Identifica factores de riesgo específicos"""
        factors = []
        
        # Ausentismo
        recent_attendance = AttendanceRecord.objects.filter(
            employee=employee,
            date__gte=date.today() - timedelta(days=30)
        )
        
        if recent_attendance.exists():
            attendance_rate = recent_attendance.filter(status='present').count() / recent_attendance.count()
            if attendance_rate < 0.9:
                factors.append(f'Ausentismo reciente ({attendance_rate:.1%} asistencia)')
        
        # Anomalías
        anomalies = AttendanceRecord.objects.filter(
            employee=employee,
            ml_anomaly_detected=True,
            date__gte=date.today() - timedelta(days=60)
        ).count()
        
        if anomalies > 3:
            factors.append(f'Patrones anómalos ({anomalies} anomalías)')
        
        # Sentimientos negativos
        sentiment = self.analyze_employee_sentiment(employee, 30)
        if sentiment['success'] and sentiment['average_sentiment'] < -0.1:
            factors.append('Sentimientos negativos detectados')
        
        return factors
    
    def _get_risk_recommendations(self, employee: PayrollEmployee, risk_score: float) -> List[str]:
        """Obtiene recomendaciones para reducir riesgo"""
        recommendations = []
        
        if risk_score > 0.5:
            recommendations.append('Reunión urgente con supervisor')
            recommendations.append('Evaluación de satisfacción laboral')
        
        if risk_score > 0.3:
            recommendations.append('Programa de retención')
            recommendations.append('Mentoría o coaching')
        
        recommendations.append('Mejorar comunicación')
        recommendations.append('Revisar carga de trabajo')
        
        return recommendations
    
    def _analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """Analiza sentimiento de un texto"""
        try:
            blob = TextBlob(text)
            sentiment_score = blob.sentiment.polarity
            
            if sentiment_score > 0.1:
                label = 'positive'
            elif sentiment_score < -0.1:
                label = 'negative'
            else:
                label = 'neutral'
            
            return {
                'score': sentiment_score,
                'label': label,
                'confidence': abs(sentiment_score)
            }
        except Exception as e:
            logger.error(f"Error analizando sentimiento: {str(e)}")
            return {
                'score': 0,
                'label': 'neutral',
                'confidence': 0
            }
    
    def _calculate_sentiment_trend(self, sentiments: List[Dict[str, Any]]) -> str:
        """Calcula tendencia de sentimientos"""
        if len(sentiments) < 2:
            return 'neutral'
        
        scores = [s['sentiment_score'] for s in sentiments]
        recent_scores = scores[-5:] if len(scores) >= 5 else scores
        
        if len(recent_scores) >= 2:
            trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
            
            if trend > 0.01:
                return 'improving'
            elif trend < -0.01:
                return 'declining'
            else:
                return 'stable'
        
        return 'neutral'
    
    def _calculate_sentiment_trend_from_scores(self, scores: List[float]) -> str:
        """Calcula tendencia desde scores de sentimiento"""
        if len(scores) < 2:
            return 'neutral'
        
        recent_scores = scores[-5:] if len(scores) >= 5 else scores
        
        if len(recent_scores) >= 2:
            trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
            
            if trend > 0.01:
                return 'improving'
            elif trend < -0.01:
                return 'declining'
            else:
                return 'stable'
        
        return 'neutral'
    
    def _calculate_attendance_trend(self, records) -> str:
        """Calcula tendencia de asistencia"""
        if not records.exists():
            return 'stable'
        
        # Agrupar por semana
        weekly_data = {}
        for record in records:
            week_start = record.date - timedelta(days=record.date.weekday())
            if week_start not in weekly_data:
                weekly_data[week_start] = {'total': 0, 'present': 0}
            
            weekly_data[week_start]['total'] += 1
            if record.status == 'present':
                weekly_data[week_start]['present'] += 1
        
        if len(weekly_data) < 2:
            return 'stable'
        
        # Calcular tendencia
        weeks = sorted(weekly_data.keys())
        rates = []
        
        for week in weeks:
            data = weekly_data[week]
            if data['total'] > 0:
                rate = data['present'] / data['total']
                rates.append(rate)
        
        if len(rates) >= 2:
            trend = np.polyfit(range(len(rates)), rates, 1)[0]
            
            if trend > 0.01:
                return 'improving'
            elif trend < -0.01:
                return 'declining'
            else:
                return 'stable'
        
        return 'stable'
    
    def _analyze_attendance_trends(self) -> Dict[str, Any]:
        """Analiza tendencias de asistencia"""
        # Implementar análisis de tendencias
        return {
            'absenteeism_trend': 'stable',
            'late_arrivals_trend': 'stable',
            'overall_trend': 'stable'
        }
    
    def _identify_training_needs(self) -> List[str]:
        """Identifica necesidades de capacitación"""
        # Implementar identificación de necesidades
        return [
            'Gestión del tiempo',
            'Comunicación efectiva',
            'Resolución de conflictos'
        ]
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Obtiene nivel de riesgo"""
        if risk_score > 0.7:
            return 'critical'
        elif risk_score > 0.5:
            return 'high'
        elif risk_score > 0.3:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_climate_score(self, attendance_analysis: Dict[str, Any], 
                               requests_analysis: Dict[str, Any],
                               sentiment_analysis: Dict[str, Any],
                               risk_analysis: Dict[str, Any]) -> float:
        """Calcula score general del clima laboral"""
        scores = []
        
        # Score de asistencia (40% peso)
        attendance_score = attendance_analysis.get('attendance_rate', 0)
        scores.append(attendance_score * 0.4)
        
        # Score de solicitudes (20% peso)
        approval_rate = requests_analysis.get('approval_rate', 0)
        scores.append(approval_rate * 0.2)
        
        # Score de sentimientos (30% peso)
        avg_sentiment = sentiment_analysis.get('average_sentiment', 0)
        sentiment_score = (avg_sentiment + 1) / 2  # Convertir de [-1,1] a [0,1]
        scores.append(sentiment_score * 0.3)
        
        # Score de riesgos (10% peso)
        risk_score = 1 - (risk_analysis.get('total_risks', 0) * 0.1)
        risk_score = max(0, min(1, risk_score))
        scores.append(risk_score * 0.1)
        
        return sum(scores)
    
    def _generate_recommendations(self, attendance_analysis: Dict[str, Any],
                                requests_analysis: Dict[str, Any],
                                sentiment_analysis: Dict[str, Any],
                                risk_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera recomendaciones basadas en análisis"""
        recommendations = []
        
        # Recomendaciones de asistencia
        if attendance_analysis.get('attendance_rate', 0) < 0.9:
            recommendations.append({
                'category': 'attendance',
                'priority': 'high',
                'title': 'Mejorar Asistencia',
                'description': 'La tasa de asistencia está por debajo del 90%',
                'actions': [
                    'Revisar políticas de flexibilidad',
                    'Implementar programas de bienestar',
                    'Mejorar condiciones de trabajo'
                ]
            })
        
        # Recomendaciones de sentimientos
        if sentiment_analysis.get('average_sentiment', 0) < 0:
            recommendations.append({
                'category': 'sentiment',
                'priority': 'medium',
                'title': 'Mejorar Clima Laboral',
                'description': 'Sentimientos negativos detectados',
                'actions': [
                    'Realizar encuestas de satisfacción',
                    'Mejorar comunicación interna',
                    'Implementar programas de reconocimiento'
                ]
            })
        
        # Recomendaciones de riesgos
        if risk_analysis.get('total_risks', 0) > 0:
            recommendations.append({
                'category': 'risk',
                'priority': 'high',
                'title': 'Gestionar Riesgos',
                'description': f'{risk_analysis["total_risks"]} riesgos identificados',
                'actions': [
                    'Revisar empleados en riesgo',
                    'Implementar programas de retención',
                    'Mejorar políticas de recursos humanos'
                ]
            })
        
        return recommendations 