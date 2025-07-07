"""
Servicio de ML para Asistencia huntRED® Payroll
Predicción y análisis de asistencia con Machine Learning
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

from django.utils import timezone
from django.core.exceptions import ValidationError

from ..models import PayrollCompany, PayrollEmployee, AttendanceRecord, MLAttendanceModel
from .. import ATTENDANCE_STATUSES

logger = logging.getLogger(__name__)


class MLAttendanceService:
    """
    Servicio de Machine Learning para predicción de asistencia
    """
    
    def __init__(self, company: PayrollCompany):
        self.company = company
        self.ml_config = {
            'mode': company.ml_attendance_mode,
            'accuracy_threshold': float(company.ml_accuracy_threshold),
            'learning_enabled': company.ml_learning_enabled,
            'training_days': company.ml_training_data_days
        }
        
        # Obtener modelo activo
        self.model = self._get_active_model()
    
    def _get_active_model(self) -> Optional[MLAttendanceModel]:
        """Obtiene modelo ML activo para la empresa"""
        return MLAttendanceModel.objects.filter(
            company=self.company,
            is_active=True
        ).first()
    
    def predict_attendance(self, employee: PayrollEmployee, target_date: date) -> Dict[str, Any]:
        """
        Predice asistencia de un empleado para una fecha específica
        
        Args:
            employee: Empleado
            target_date: Fecha objetivo
            
        Returns:
            Predicción con confianza y detalles
        """
        try:
            # Obtener datos históricos
            historical_data = self._get_historical_data(employee, target_date)
            
            if len(historical_data) < 30:  # Mínimo 30 días de datos
                return {
                    'prediction': 'insufficient_data',
                    'confidence': 0.0,
                    'reason': 'Datos insuficientes para predicción'
                }
            
            # Preparar features
            features = self._prepare_features(historical_data, target_date)
            
            # Realizar predicción según modo
            if self.ml_config['mode'] == 'precise':
                prediction = self._precise_prediction(features)
            elif self.ml_config['mode'] == 'ml_learning':
                prediction = self._ml_learning_prediction(features)
            elif self.ml_config['mode'] == 'random_ml':
                prediction = self._random_ml_prediction(features)
            else:  # hybrid
                prediction = self._hybrid_prediction(features)
            
            # Calcular confianza
            confidence = self._calculate_confidence(features, prediction)
            
            # Actualizar patrón de asistencia del empleado
            self._update_employee_pattern(employee, features, prediction, confidence)
            
            return {
                'prediction': prediction['status'],
                'confidence': confidence,
                'expected_checkin': prediction.get('expected_checkin'),
                'expected_checkout': prediction.get('expected_checkout'),
                'anomaly_risk': prediction.get('anomaly_risk', 0.0),
                'features_used': list(features.keys())
            }
            
        except Exception as e:
            logger.error(f"Error prediciendo asistencia: {str(e)}")
            return {
                'prediction': 'error',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def analyze_attendance_record(self, record: AttendanceRecord) -> Dict[str, Any]:
        """
        Analiza un registro de asistencia con ML
        
        Args:
            record: Registro de asistencia
            
        Returns:
            Análisis ML del registro
        """
        try:
            # Obtener datos históricos
            historical_data = self._get_historical_data(record.employee, record.date)
            
            # Preparar features
            features = self._prepare_features(historical_data, record.date)
            
            # Analizar anomalías
            anomaly_analysis = self._detect_anomalies(record, features)
            
            # Calcular confianza
            confidence = self._calculate_record_confidence(record, features)
            
            return {
                'prediction': {
                    'status': record.status,
                    'expected_checkin': features.get('avg_checkin_time'),
                    'expected_checkout': features.get('avg_checkout_time')
                },
                'confidence': confidence,
                'anomaly_detected': anomaly_analysis['detected'],
                'anomaly_type': anomaly_analysis['type'],
                'anomaly_score': anomaly_analysis['score']
            }
            
        except Exception as e:
            logger.error(f"Error analizando registro: {str(e)}")
            return {
                'prediction': {},
                'confidence': 0.0,
                'anomaly_detected': False,
                'error': str(e)
            }
    
    def analyze_period(self, period) -> Dict[str, Any]:
        """
        Analiza un período completo con ML
        
        Args:
            period: Período de nómina
            
        Returns:
            Análisis ML del período
        """
        try:
            # Obtener todos los registros del período
            records = AttendanceRecord.objects.filter(
                employee__company=self.company,
                date__range=[period.start_date, period.end_date]
            )
            
            if not records.exists():
                return {
                    'accuracy': 0.0,
                    'total_records': 0,
                    'anomalies_detected': 0,
                    'ml_insights': {}
                }
            
            # Calcular métricas
            total_records = records.count()
            anomalies_detected = records.filter(ml_anomaly_detected=True).count()
            
            # Calcular precisión promedio
            avg_confidence = records.aggregate(
                avg_confidence=models.Avg('ml_confidence')
            )['avg_confidence'] or 0.0
            
            # Análisis por empleado
            employee_analysis = {}
            for employee in self.company.employees.filter(is_active=True):
                employee_records = records.filter(employee=employee)
                if employee_records.exists():
                    employee_analysis[employee.id] = {
                        'total_days': employee_records.count(),
                        'present_days': employee_records.filter(status='present').count(),
                        'avg_confidence': float(employee_records.aggregate(
                            avg_confidence=models.Avg('ml_confidence')
                        )['avg_confidence'] or 0.0),
                        'anomalies': employee_records.filter(ml_anomaly_detected=True).count()
                    }
            
            return {
                'accuracy': float(avg_confidence),
                'total_records': total_records,
                'anomalies_detected': anomalies_detected,
                'anomaly_rate': (anomalies_detected / total_records * 100) if total_records > 0 else 0,
                'employee_analysis': employee_analysis,
                'ml_insights': self._generate_ml_insights(records)
            }
            
        except Exception as e:
            logger.error(f"Error analizando período: {str(e)}")
            return {
                'accuracy': 0.0,
                'error': str(e)
            }
    
    def train_model(self) -> Dict[str, Any]:
        """
        Entrena el modelo ML con datos históricos
        
        Returns:
            Resultado del entrenamiento
        """
        try:
            # Obtener datos de entrenamiento
            training_data = self._get_training_data()
            
            if len(training_data) < 100:  # Mínimo 100 registros
                return {
                    'success': False,
                    'error': 'Datos insuficientes para entrenamiento'
                }
            
            # Preparar dataset
            X, y = self._prepare_training_dataset(training_data)
            
            # Entrenar modelo según tipo
            if self.model and self.model.model_type == 'random_forest':
                model_result = self._train_random_forest(X, y)
            elif self.model and self.model.model_type == 'neural_network':
                model_result = self._train_neural_network(X, y)
            elif self.model and self.model.model_type == 'lstm':
                model_result = self._train_lstm(X, y)
            else:
                model_result = self._train_hybrid_model(X, y)
            
            # Actualizar modelo
            if self.model:
                self.model.accuracy = model_result['accuracy']
                self.model.precision = model_result['precision']
                self.model.recall = model_result['recall']
                self.model.training_data_size = len(training_data)
                self.model.last_training_date = timezone.now()
                self.model.model_parameters = model_result['parameters']
                self.model.save()
            
            return {
                'success': True,
                'accuracy': model_result['accuracy'],
                'precision': model_result['precision'],
                'recall': model_result['recall'],
                'training_samples': len(training_data)
            }
            
        except Exception as e:
            logger.error(f"Error entrenando modelo: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_historical_data(self, employee: PayrollEmployee, target_date: date) -> List[Dict]:
        """Obtiene datos históricos de asistencia"""
        start_date = target_date - timedelta(days=self.ml_config['training_days'])
        
        records = AttendanceRecord.objects.filter(
            employee=employee,
            date__range=[start_date, target_date - timedelta(days=1)]
        ).order_by('date')
        
        data = []
        for record in records:
            data.append({
                'date': record.date,
                'status': record.status,
                'check_in_time': record.check_in_time,
                'check_out_time': record.check_out_time,
                'hours_worked': float(record.hours_worked),
                'overtime_hours': float(record.overtime_hours),
                'day_of_week': record.date.weekday(),
                'is_holiday': self._is_holiday(record.date),
                'month': record.date.month,
                'day': record.date.day
            })
        
        return data
    
    def _prepare_features(self, historical_data: List[Dict], target_date: date) -> Dict[str, Any]:
        """Prepara features para predicción"""
        if not historical_data:
            return {}
        
        df = pd.DataFrame(historical_data)
        
        features = {
            # Estadísticas básicas
            'avg_attendance_rate': (df['status'] == 'present').mean() * 100,
            'avg_hours_worked': df['hours_worked'].mean(),
            'avg_overtime_hours': df['overtime_hours'].mean(),
            
            # Patrones temporales
            'day_of_week': target_date.weekday(),
            'month': target_date.month,
            'is_holiday': self._is_holiday(target_date),
            
            # Patrones de entrada/salida
            'avg_checkin_time': self._calculate_avg_time(df, 'check_in_time'),
            'avg_checkout_time': self._calculate_avg_time(df, 'check_out_time'),
            
            # Tendencias
            'recent_attendance_trend': self._calculate_trend(df, 'status', 7),
            'recent_hours_trend': self._calculate_trend(df, 'hours_worked', 7),
            
            # Anomalías recientes
            'recent_anomalies': self._count_recent_anomalies(df, 7),
            
            # Patrones específicos del día
            'same_day_week_attendance': self._get_same_day_attendance(df, target_date.weekday()),
            'same_month_attendance': self._get_same_month_attendance(df, target_date.month)
        }
        
        return features
    
    def _precise_prediction(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predicción precisa basada en reglas"""
        attendance_rate = features.get('avg_attendance_rate', 0)
        day_of_week = features.get('day_of_week', 0)
        is_holiday = features.get('is_holiday', False)
        
        # Reglas de predicción
        if is_holiday:
            status = 'absent'
        elif day_of_week >= 5:  # Fin de semana
            status = 'absent'
        elif attendance_rate > 95:
            status = 'present'
        elif attendance_rate > 80:
            status = 'present' if np.random.random() > 0.1 else 'absent'
        else:
            status = 'present' if np.random.random() > 0.3 else 'absent'
        
        return {
            'status': status,
            'expected_checkin': features.get('avg_checkin_time'),
            'expected_checkout': features.get('avg_checkout_time'),
            'anomaly_risk': 0.1
        }
    
    def _ml_learning_prediction(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predicción usando ML con aprendizaje"""
        # Simular predicción ML (aquí se integraría el modelo real)
        attendance_rate = features.get('avg_attendance_rate', 0)
        recent_trend = features.get('recent_attendance_trend', 0)
        
        # Factor de confianza del modelo
        model_confidence = min(attendance_rate / 100, 0.95)
        
        # Predicción con incertidumbre
        if model_confidence > 0.8:
            status = 'present'
        elif model_confidence > 0.6:
            status = 'present' if np.random.random() > 0.2 else 'absent'
        else:
            status = 'present' if np.random.random() > 0.4 else 'absent'
        
        return {
            'status': status,
            'expected_checkin': features.get('avg_checkin_time'),
            'expected_checkout': features.get('avg_checkout_time'),
            'anomaly_risk': 1 - model_confidence
        }
    
    def _random_ml_prediction(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predicción aleatoria con influencia ML"""
        # Base aleatoria con influencia de patrones
        base_probability = 0.5
        attendance_rate = features.get('avg_attendance_rate', 0) / 100
        
        # Ajustar probabilidad basado en patrones
        adjusted_probability = base_probability + (attendance_rate - 0.5) * 0.3
        
        status = 'present' if np.random.random() < adjusted_probability else 'absent'
        
        return {
            'status': status,
            'expected_checkin': features.get('avg_checkin_time'),
            'expected_checkout': features.get('avg_checkout_time'),
            'anomaly_risk': 0.5
        }
    
    def _hybrid_prediction(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predicción híbrida (precisa + ML)"""
        # Predicción precisa
        precise_pred = self._precise_prediction(features)
        
        # Predicción ML
        ml_pred = self._ml_learning_prediction(features)
        
        # Combinar predicciones
        if precise_pred['status'] == ml_pred['status']:
            final_status = precise_pred['status']
            confidence_boost = 0.2
        else:
            # Usar la predicción con mayor confianza
            if features.get('avg_attendance_rate', 0) > 85:
                final_status = precise_pred['status']
            else:
                final_status = ml_pred['status']
            confidence_boost = 0.0
        
        return {
            'status': final_status,
            'expected_checkin': features.get('avg_checkin_time'),
            'expected_checkout': features.get('avg_checkout_time'),
            'anomaly_risk': min(precise_pred['anomaly_risk'], ml_pred['anomaly_risk']) + confidence_boost
        }
    
    def _detect_anomalies(self, record: AttendanceRecord, features: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta anomalías en el registro"""
        anomalies = []
        anomaly_score = 0.0
        
        # Anomalía de horario
        expected_checkin = features.get('avg_checkin_time')
        if expected_checkin and record.check_in_time:
            checkin_hour = record.check_in_time.hour + record.check_in_time.minute / 60
            if abs(checkin_hour - expected_checkin) > 2:  # Más de 2 horas de diferencia
                anomalies.append('late_checkin')
                anomaly_score += 0.3
        
        # Anomalía de horas trabajadas
        expected_hours = features.get('avg_hours_worked', 8)
        if abs(float(record.hours_worked) - expected_hours) > 3:  # Más de 3 horas de diferencia
            anomalies.append('unusual_hours')
            anomaly_score += 0.4
        
        # Anomalía de patrón
        attendance_rate = features.get('avg_attendance_rate', 0)
        if attendance_rate > 95 and record.status == 'absent':
            anomalies.append('unexpected_absence')
            anomaly_score += 0.5
        
        return {
            'detected': len(anomalies) > 0,
            'type': ', '.join(anomalies) if anomalies else '',
            'score': min(anomaly_score, 1.0)
        }
    
    def _calculate_confidence(self, features: Dict[str, Any], prediction: Dict[str, Any]) -> float:
        """Calcula nivel de confianza de la predicción"""
        base_confidence = 0.5
        
        # Factor de datos históricos
        attendance_rate = features.get('avg_attendance_rate', 0)
        data_confidence = min(attendance_rate / 100, 0.3)
        
        # Factor de consistencia
        recent_trend = features.get('recent_attendance_trend', 0)
        trend_confidence = min(abs(recent_trend) / 100, 0.2)
        
        # Factor de anomalías
        anomaly_risk = prediction.get('anomaly_risk', 0)
        anomaly_confidence = (1 - anomaly_risk) * 0.3
        
        total_confidence = base_confidence + data_confidence + trend_confidence + anomaly_confidence
        
        return min(total_confidence, 1.0)
    
    def _update_employee_pattern(self, employee: PayrollEmployee, features: Dict[str, Any], 
                               prediction: Dict[str, Any], confidence: float):
        """Actualiza patrón de asistencia del empleado"""
        pattern = employee.attendance_pattern or {}
        
        pattern.update({
            'last_prediction': {
                'date': timezone.now().isoformat(),
                'prediction': prediction['status'],
                'confidence': confidence,
                'features': features
            },
            'avg_attendance_rate': features.get('avg_attendance_rate', 0),
            'avg_hours_worked': features.get('avg_hours_worked', 0),
            'ml_confidence_score': confidence
        })
        
        employee.attendance_pattern = pattern
        employee.ml_confidence_score = Decimal(str(confidence * 100))
        employee.save()
    
    def _is_holiday(self, date_obj: date) -> bool:
        """Verifica si es día festivo (simplificado)"""
        # Aquí se integraría con API de días festivos
        holidays_2024 = [
            date(2024, 1, 1),   # Año Nuevo
            date(2024, 2, 5),   # Día de la Constitución
            date(2024, 3, 18),  # Natalicio de Benito Juárez
            date(2024, 5, 1),   # Día del Trabajo
            date(2024, 9, 16),  # Día de la Independencia
            date(2024, 11, 20), # Día de la Revolución
            date(2024, 12, 25), # Navidad
        ]
        
        return date_obj in holidays_2024
    
    def _calculate_avg_time(self, df: pd.DataFrame, column: str) -> Optional[float]:
        """Calcula hora promedio"""
        times = df[column].dropna()
        if len(times) == 0:
            return None
        
        # Convertir a horas decimales
        hours = []
        for time in times:
            if time:
                hours.append(time.hour + time.minute / 60)
        
        return np.mean(hours) if hours else None
    
    def _calculate_trend(self, df: pd.DataFrame, column: str, days: int) -> float:
        """Calcula tendencia de los últimos días"""
        if len(df) < days:
            return 0.0
        
        recent_data = df.tail(days)
        if column == 'status':
            # Para status, calcular cambio en tasa de asistencia
            recent_rate = (recent_data[column] == 'present').mean()
            overall_rate = (df[column] == 'present').mean()
            return (recent_rate - overall_rate) * 100
        else:
            # Para valores numéricos, calcular pendiente
            recent_values = recent_data[column].values
            if len(recent_values) > 1:
                return np.polyfit(range(len(recent_values)), recent_values, 1)[0]
            return 0.0
    
    def _count_recent_anomalies(self, df: pd.DataFrame, days: int) -> int:
        """Cuenta anomalías recientes"""
        if len(df) < days:
            return 0
        
        recent_data = df.tail(days)
        anomalies = 0
        
        for _, row in recent_data.iterrows():
            # Detectar anomalías simples
            if row['hours_worked'] > 12 or row['hours_worked'] < 4:
                anomalies += 1
            if row['overtime_hours'] > 6:
                anomalies += 1
        
        return anomalies
    
    def _get_same_day_attendance(self, df: pd.DataFrame, day_of_week: int) -> float:
        """Obtiene tasa de asistencia para el mismo día de la semana"""
        same_day_data = df[df['day_of_week'] == day_of_week]
        if len(same_day_data) == 0:
            return 0.0
        
        return (same_day_data['status'] == 'present').mean() * 100
    
    def _get_same_month_attendance(self, df: pd.DataFrame, month: int) -> float:
        """Obtiene tasa de asistencia para el mismo mes"""
        same_month_data = df[df['month'] == month]
        if len(same_month_data) == 0:
            return 0.0
        
        return (same_month_data['status'] == 'present').mean() * 100
    
    def _generate_ml_insights(self, records) -> Dict[str, Any]:
        """Genera insights de ML para reportes"""
        if not records.exists():
            return {}
        
        df = pd.DataFrame(list(records.values()))
        
        insights = {
            'total_records': len(df),
            'attendance_rate': (df['status'] == 'present').mean() * 100,
            'avg_hours_worked': float(df['hours_worked'].mean()),
            'avg_overtime_hours': float(df['overtime_hours'].mean()),
            'anomaly_rate': float(df['ml_anomaly_detected'].mean() * 100),
            'avg_confidence': float(df['ml_confidence'].mean()),
            'top_anomaly_types': df['ml_anomaly_type'].value_counts().head(3).to_dict()
        }
        
        return insights 