"""
HuntRED® v2 - ML Turnover Prediction System
Advanced machine learning system for predicting employee turnover
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import pickle
import os
import json

# ML Libraries with fallback
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.impute import SimpleImputer
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

from sqlalchemy.orm import Session
from ..database.models import Employee, AttendanceRecord, PayrollRecord
from ..database.database import get_db

logger = logging.getLogger(__name__)

class TurnoverPredictor:
    """Advanced ML system for predicting employee turnover"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        self.model_metrics = {}
        
        # Risk factors and weights
        self.risk_factors = {
            'attendance': {
                'low_attendance_rate': 0.3,
                'frequent_late_arrivals': 0.2,
                'irregular_patterns': 0.15
            },
            'performance': {
                'declining_performance': 0.25,
                'missed_deadlines': 0.2,
                'low_engagement': 0.15
            },
            'compensation': {
                'below_market_salary': 0.2,
                'no_recent_raise': 0.15,
                'high_deductions': 0.1
            },
            'demographic': {
                'tenure_risk_zone': 0.15,
                'age_risk_factor': 0.1,
                'department_turnover': 0.2
            },
            'satisfaction': {
                'low_survey_scores': 0.3,
                'negative_feedback': 0.25,
                'complaint_history': 0.2
            }
        }
        
        # Load pre-trained models
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models from disk"""
        model_path = "models/turnover/"
        if os.path.exists(model_path):
            try:
                for model_file in os.listdir(model_path):
                    if model_file.endswith('.pkl'):
                        model_name = model_file.replace('.pkl', '')
                        with open(os.path.join(model_path, model_file), 'rb') as f:
                            self.models[model_name] = pickle.load(f)
                
                logger.info(f"Loaded {len(self.models)} turnover prediction models")
            except Exception as e:
                logger.warning(f"Failed to load models: {e}")
    
    def extract_employee_features(self, employee_id: str, db: Session) -> Dict[str, Any]:
        """Extract comprehensive features for an employee"""
        try:
            # Get employee data
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return {}
            
            # Calculate tenure
            tenure_days = (datetime.now().date() - employee.hire_date).days
            tenure_years = tenure_days / 365.25
            
            # Get attendance data (last 6 months)
            six_months_ago = datetime.now() - timedelta(days=180)
            attendance_records = db.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.date >= six_months_ago
            ).all()
            
            # Get payroll data (last 12 months)
            twelve_months_ago = datetime.now() - timedelta(days=365)
            payroll_records = db.query(PayrollRecord).filter(
                PayrollRecord.employee_id == employee_id,
                PayrollRecord.created_at >= twelve_months_ago
            ).all()
            
            # Calculate attendance features
            attendance_features = self._calculate_attendance_features(attendance_records)
            
            # Calculate compensation features
            compensation_features = self._calculate_compensation_features(payroll_records, employee)
            
            # Calculate demographic features
            demographic_features = self._calculate_demographic_features(employee, tenure_years, db)
            
            # Combine all features
            features = {
                # Basic demographics
                'age': self._calculate_age(employee.hire_date),
                'tenure_years': tenure_years,
                'department': employee.department,
                'position': employee.position,
                'role': employee.role.value,
                'monthly_salary': float(employee.monthly_salary),
                
                # Attendance features
                **attendance_features,
                
                # Compensation features
                **compensation_features,
                
                # Demographic features
                **demographic_features,
                
                # Manager relationship
                'has_manager': employee.manager_id is not None,
                'is_manager': db.query(Employee).filter(Employee.manager_id == employee_id).count() > 0,
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features for employee {employee_id}: {e}")
            return {}
    
    def _calculate_attendance_features(self, attendance_records: List) -> Dict[str, float]:
        """Calculate attendance-related features"""
        if not attendance_records:
            return {
                'attendance_rate': 0.5,
                'avg_hours_per_day': 0.0,
                'late_arrival_rate': 0.0,
                'attendance_consistency': 0.0
            }
        
        # Attendance rate
        total_days = len(attendance_records)
        present_days = len([r for r in attendance_records if r.check_in_time])
        attendance_rate = present_days / total_days if total_days > 0 else 0
        
        # Average hours per day
        hours_worked = [float(r.hours_worked) for r in attendance_records if r.hours_worked]
        avg_hours = np.mean(hours_worked) if hours_worked else 0
        
        # Late arrival rate (after 9:00 AM)
        late_arrivals = 0
        for record in attendance_records:
            if record.check_in_time and record.check_in_time.time() > datetime.strptime("09:00", "%H:%M").time():
                late_arrivals += 1
        
        late_rate = late_arrivals / present_days if present_days > 0 else 0
        
        # Attendance consistency (standard deviation of daily hours)
        consistency = 1 - (np.std(hours_worked) / 8) if hours_worked else 0
        consistency = max(0, min(1, consistency))  # Clamp between 0 and 1
        
        return {
            'attendance_rate': attendance_rate,
            'avg_hours_per_day': avg_hours,
            'late_arrival_rate': late_rate,
            'attendance_consistency': consistency
        }
    
    def _calculate_compensation_features(self, payroll_records: List, employee) -> Dict[str, float]:
        """Calculate compensation-related features"""
        if not payroll_records:
            return {
                'salary_growth_rate': 0.0,
                'bonus_frequency': 0.0,
                'deduction_rate': 0.0,
                'overtime_frequency': 0.0
            }
        
        # Salary growth rate
        if len(payroll_records) >= 2:
            first_salary = float(payroll_records[0].base_salary)
            last_salary = float(payroll_records[-1].base_salary)
            growth_rate = (last_salary - first_salary) / first_salary if first_salary > 0 else 0
        else:
            growth_rate = 0.0
        
        # Bonus frequency
        bonus_count = len([r for r in payroll_records if float(r.bonuses) > 0])
        bonus_frequency = bonus_count / len(payroll_records)
        
        # Average deduction rate
        deduction_rates = []
        for record in payroll_records:
            gross = float(record.gross_income)
            deductions = float(record.total_deductions)
            if gross > 0:
                deduction_rates.append(deductions / gross)
        
        avg_deduction_rate = np.mean(deduction_rates) if deduction_rates else 0
        
        # Overtime frequency
        overtime_count = len([r for r in payroll_records if float(r.overtime_hours) > 0])
        overtime_frequency = overtime_count / len(payroll_records)
        
        return {
            'salary_growth_rate': growth_rate,
            'bonus_frequency': bonus_frequency,
            'deduction_rate': avg_deduction_rate,
            'overtime_frequency': overtime_frequency
        }
    
    def _calculate_demographic_features(self, employee, tenure_years: float, db: Session) -> Dict[str, float]:
        """Calculate demographic and organizational features"""
        # Department turnover rate (last year)
        dept_employees = db.query(Employee).filter(
            Employee.department == employee.department,
            Employee.company_id == employee.company_id
        ).all()
        
        # Calculate department turnover (simplified)
        dept_turnover_rate = 0.15  # Default industry average
        
        # Tenure risk zones
        tenure_risk = 0.0
        if tenure_years < 0.5:  # First 6 months
            tenure_risk = 0.8
        elif tenure_years < 2:  # 6 months to 2 years
            tenure_risk = 0.6
        elif tenure_years < 5:  # 2-5 years
            tenure_risk = 0.3
        elif tenure_years > 10:  # Over 10 years
            tenure_risk = 0.4
        else:
            tenure_risk = 0.2
        
        # Age risk factor
        age = self._calculate_age(employee.hire_date)
        age_risk = 0.0
        if age < 25 or age > 55:
            age_risk = 0.6
        elif age < 30 or age > 50:
            age_risk = 0.4
        else:
            age_risk = 0.2
        
        return {
            'dept_turnover_rate': dept_turnover_rate,
            'tenure_risk_score': tenure_risk,
            'age_risk_score': age_risk,
            'dept_size': len(dept_employees)
        }
    
    def _calculate_age(self, hire_date) -> int:
        """Estimate age based on hire date (simplified)"""
        # Assume average hiring age of 28
        years_since_hire = (datetime.now().date() - hire_date).days / 365.25
        estimated_age = 28 + years_since_hire
        return int(estimated_age)
    
    def calculate_turnover_risk_score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate turnover risk score using rule-based approach"""
        risk_score = 0.0
        risk_factors = []
        
        # Attendance risk
        attendance_rate = features.get('attendance_rate', 1.0)
        late_rate = features.get('late_arrival_rate', 0.0)
        
        if attendance_rate < 0.85:
            risk_score += 0.3
            risk_factors.append('Low attendance rate')
        
        if late_rate > 0.2:
            risk_score += 0.2
            risk_factors.append('Frequent late arrivals')
        
        # Compensation risk
        salary_growth = features.get('salary_growth_rate', 0.0)
        bonus_freq = features.get('bonus_frequency', 0.0)
        
        if salary_growth < 0.05:  # Less than 5% growth
            risk_score += 0.25
            risk_factors.append('No salary growth')
        
        if bonus_freq < 0.1:  # Less than 10% bonus frequency
            risk_score += 0.15
            risk_factors.append('Infrequent bonuses')
        
        # Tenure risk
        tenure_risk = features.get('tenure_risk_score', 0.0)
        risk_score += tenure_risk * 0.3
        
        if tenure_risk > 0.6:
            risk_factors.append('High tenure risk period')
        
        # Department risk
        dept_turnover = features.get('dept_turnover_rate', 0.15)
        if dept_turnover > 0.2:
            risk_score += 0.2
            risk_factors.append('High department turnover')
        
        # Normalize risk score
        risk_score = min(1.0, risk_score)
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = 'high'
        elif risk_score >= 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendations': self._generate_recommendations(risk_factors, features)
        }
    
    def _generate_recommendations(self, risk_factors: List[str], features: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on risk factors"""
        recommendations = []
        
        if 'Low attendance rate' in risk_factors:
            recommendations.append({
                'category': 'Attendance',
                'action': 'Schedule one-on-one meeting',
                'description': 'Discuss attendance issues and potential barriers',
                'priority': 'high'
            })
        
        if 'No salary growth' in risk_factors:
            recommendations.append({
                'category': 'Compensation',
                'action': 'Salary review',
                'description': 'Conduct market analysis and consider salary adjustment',
                'priority': 'medium'
            })
        
        if 'Frequent late arrivals' in risk_factors:
            recommendations.append({
                'category': 'Performance',
                'action': 'Flexible schedule discussion',
                'description': 'Explore flexible work arrangements',
                'priority': 'low'
            })
        
        if 'High tenure risk period' in risk_factors:
            tenure_years = features.get('tenure_years', 0)
            if tenure_years < 1:
                recommendations.append({
                    'category': 'Onboarding',
                    'action': 'Enhanced mentoring',
                    'description': 'Assign dedicated mentor and increase check-ins',
                    'priority': 'high'
                })
            else:
                recommendations.append({
                    'category': 'Career Development',
                    'action': 'Career path planning',
                    'description': 'Discuss growth opportunities and career progression',
                    'priority': 'medium'
                })
        
        return recommendations
    
    def predict_turnover_ml(self, features: Dict[str, Any], model_name: str = 'default') -> Dict[str, Any]:
        """ML-based turnover prediction"""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available, using rule-based prediction")
            return self.calculate_turnover_risk_score(features)
        
        if model_name not in self.models:
            logger.warning(f"Model {model_name} not found, using rule-based prediction")
            return self.calculate_turnover_risk_score(features)
        
        try:
            # Prepare features for ML model
            feature_vector = self._prepare_feature_vector(features)
            
            # Get model
            model = self.models[model_name]
            scaler = self.scalers.get(model_name)
            
            # Scale features if scaler available
            if scaler:
                feature_vector = scaler.transform([feature_vector])
            else:
                feature_vector = [feature_vector]
            
            # Predict
            prediction = model.predict(feature_vector)[0]
            probability = model.predict_proba(feature_vector)[0]
            
            # Get probability of turnover (class 1)
            turnover_probability = probability[1] if len(probability) > 1 else probability[0]
            
            # Determine risk level
            if turnover_probability >= 0.7:
                risk_level = 'high'
            elif turnover_probability >= 0.4:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            return {
                'prediction': bool(prediction),
                'probability': float(turnover_probability),
                'risk_level': risk_level,
                'model_used': model_name,
                'confidence': float(max(probability))
            }
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return self.calculate_turnover_risk_score(features)
    
    def _prepare_feature_vector(self, features: Dict[str, Any]) -> List[float]:
        """Prepare feature vector for ML model"""
        # Define feature order (should match training data)
        feature_order = [
            'age', 'tenure_years', 'monthly_salary',
            'attendance_rate', 'avg_hours_per_day', 'late_arrival_rate',
            'salary_growth_rate', 'bonus_frequency', 'deduction_rate',
            'tenure_risk_score', 'age_risk_score', 'dept_turnover_rate'
        ]
        
        vector = []
        for feature_name in feature_order:
            value = features.get(feature_name, 0.0)
            if isinstance(value, (int, float)):
                vector.append(float(value))
            else:
                vector.append(0.0)
        
        return vector
    
    def analyze_company_turnover_risk(self, company_id: str, db: Session) -> Dict[str, Any]:
        """Analyze turnover risk for entire company"""
        try:
            # Get all active employees
            employees = db.query(Employee).filter(
                Employee.company_id == company_id,
                Employee.is_active == True
            ).all()
            
            if not employees:
                return {'error': 'No active employees found'}
            
            results = {
                'company_id': company_id,
                'total_employees': len(employees),
                'risk_distribution': defaultdict(int),
                'department_analysis': defaultdict(list),
                'high_risk_employees': [],
                'recommendations': [],
                'overall_risk_score': 0.0
            }
            
            total_risk = 0.0
            
            for employee in employees:
                # Extract features
                features = self.extract_employee_features(employee.id, db)
                
                if not features:
                    continue
                
                # Calculate risk
                risk_analysis = self.calculate_turnover_risk_score(features)
                
                risk_level = risk_analysis['risk_level']
                risk_score = risk_analysis['risk_score']
                
                # Update results
                results['risk_distribution'][risk_level] += 1
                results['department_analysis'][employee.department].append({
                    'employee_id': employee.id,
                    'name': f"{employee.first_name} {employee.last_name}",
                    'risk_level': risk_level,
                    'risk_score': risk_score
                })
                
                total_risk += risk_score
                
                # Track high-risk employees
                if risk_level == 'high':
                    results['high_risk_employees'].append({
                        'employee_id': employee.id,
                        'name': f"{employee.first_name} {employee.last_name}",
                        'department': employee.department,
                        'position': employee.position,
                        'risk_score': risk_score,
                        'risk_factors': risk_analysis['risk_factors'],
                        'recommendations': risk_analysis['recommendations']
                    })
            
            # Calculate overall metrics
            results['overall_risk_score'] = total_risk / len(employees)
            
            # Department summaries
            dept_summaries = {}
            for dept, employee_risks in results['department_analysis'].items():
                dept_risk_scores = [emp['risk_score'] for emp in employee_risks]
                dept_risk_levels = [emp['risk_level'] for emp in employee_risks]
                
                dept_summaries[dept] = {
                    'total_employees': len(employee_risks),
                    'average_risk_score': np.mean(dept_risk_scores),
                    'high_risk_count': dept_risk_levels.count('high'),
                    'medium_risk_count': dept_risk_levels.count('medium'),
                    'low_risk_count': dept_risk_levels.count('low')
                }
            
            results['department_summaries'] = dept_summaries
            
            # Generate company-level recommendations
            results['recommendations'] = self._generate_company_recommendations(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing company turnover risk: {e}")
            return {'error': str(e)}
    
    def _generate_company_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate company-level recommendations"""
        recommendations = []
        
        high_risk_count = analysis_results['risk_distribution']['high']
        total_employees = analysis_results['total_employees']
        
        if high_risk_count > total_employees * 0.2:  # More than 20% high risk
            recommendations.append({
                'category': 'Critical',
                'action': 'Immediate retention program',
                'description': 'High turnover risk detected - implement company-wide retention initiatives',
                'priority': 'urgent'
            })
        
        overall_risk = analysis_results['overall_risk_score']
        if overall_risk > 0.6:
            recommendations.append({
                'category': 'Culture',
                'action': 'Employee satisfaction survey',
                'description': 'Conduct comprehensive survey to identify systemic issues',
                'priority': 'high'
            })
        
        # Department-specific recommendations
        dept_summaries = analysis_results.get('department_summaries', {})
        for dept, summary in dept_summaries.items():
            if summary['high_risk_count'] > summary['total_employees'] * 0.3:
                recommendations.append({
                    'category': 'Department',
                    'action': f'Focus on {dept} department',
                    'description': f'{dept} has high turnover risk - review management and workload',
                    'priority': 'high'
                })
        
        return recommendations
    
    def train_turnover_model(self, training_data: List[Dict[str, Any]], model_name: str = 'custom') -> Dict[str, Any]:
        """Train a custom turnover prediction model"""
        if not ML_AVAILABLE:
            return {'error': 'ML libraries not available'}
        
        try:
            # Prepare training data
            features = []
            labels = []
            
            for item in training_data:
                feature_dict = item.get('features', {})
                turnover = item.get('turnover', False)
                
                if feature_dict:
                    feature_vector = self._prepare_feature_vector(feature_dict)
                    features.append(feature_vector)
                    labels.append(1 if turnover else 0)
            
            if len(features) < 20:
                return {'error': 'Insufficient training data (minimum 20 samples required)'}
            
            # Convert to numpy arrays
            X = np.array(features)
            y = np.array(labels)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            y_prob = model.predict_proba(X_test_scaled)[:, 1]
            
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'f1_score': f1_score(y_test, y_pred),
                'auc_roc': roc_auc_score(y_test, y_prob)
            }
            
            # Save model
            self.models[model_name] = model
            self.scalers[model_name] = scaler
            self.model_metrics[model_name] = metrics
            
            # Save to disk
            os.makedirs('models/turnover', exist_ok=True)
            joblib.dump(model, f'models/turnover/{model_name}_model.pkl')
            joblib.dump(scaler, f'models/turnover/{model_name}_scaler.pkl')
            
            return {
                'success': True,
                'model_name': model_name,
                'metrics': metrics,
                'training_samples': len(features),
                'feature_importance': dict(zip(
                    ['age', 'tenure_years', 'monthly_salary', 'attendance_rate', 
                     'avg_hours_per_day', 'late_arrival_rate', 'salary_growth_rate',
                     'bonus_frequency', 'deduction_rate', 'tenure_risk_score',
                     'age_risk_score', 'dept_turnover_rate'],
                    model.feature_importances_
                ))
            }
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {'error': str(e)}

# Global turnover predictor instance
turnover_predictor = TurnoverPredictor()

# Utility functions
def predict_employee_turnover(employee_id: str, db: Session) -> Dict[str, Any]:
    """Predict turnover risk for a single employee"""
    features = turnover_predictor.extract_employee_features(employee_id, db)
    if not features:
        return {'error': 'Could not extract employee features'}
    
    return turnover_predictor.calculate_turnover_risk_score(features)

def analyze_company_turnover(company_id: str, db: Session) -> Dict[str, Any]:
    """Analyze turnover risk for entire company"""
    return turnover_predictor.analyze_company_turnover_risk(company_id, db)