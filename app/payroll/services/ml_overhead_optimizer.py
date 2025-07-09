"""
Servicio de Optimización ML con AURA para Overhead
Sistema avanzado de ML para predicción y optimización de overhead
"""
import logging
import numpy as np
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q

# AURA imports
from app.ml.aura import (
    AuraEngine, RecommendationEngine, EthicsEngine, BiasDetectionEngine,
    FairnessOptimizer, HolisticAssessor, CompatibilityEngine,
    PersonalizationEngine, ExecutiveAnalytics
)

from ..models import (
    PayrollEmployee, PayrollCompany, EmployeeOverheadCalculation,
    TeamOverheadAnalysis, OverheadMLModel, OverheadBenchmark
)

logger = logging.getLogger(__name__)


class MLOverheadOptimizer:
    """
    Optimizador de overhead usando ML y capacidades AURA
    """
    
    def __init__(self, company: PayrollCompany):
        self.company = company
        self.aura_engine = AuraEngine()
        self.recommendation_engine = RecommendationEngine()
        self.ethics_engine = EthicsEngine()
        self.bias_detector = BiasDetectionEngine()
        self.fairness_optimizer = FairnessOptimizer()
        self.holistic_assessor = HolisticAssessor()
        self.compatibility_engine = CompatibilityEngine()
        self.personalization_engine = PersonalizationEngine()
        self.executive_analytics = ExecutiveAnalytics()
        
        # Configuración ML
        self.ml_models = self._load_ml_models()
        self.has_aura = self._check_aura_subscription()
        
    def _load_ml_models(self) -> Dict:
        """Carga modelos ML activos para la empresa"""
        models = {}
        
        active_models = self.company.overhead_ml_models.filter(
            is_active=True,
            is_production=True
        ).order_by('-accuracy')
        
        for model in active_models:
            models[model.model_type] = {
                'instance': model,
                'accuracy': float(model.accuracy),
                'parameters': model.model_parameters,
                'feature_importance': model.feature_importance,
                'aura_weights': model.aura_weights
            }
        
        return models
    
    def _check_aura_subscription(self) -> bool:
        """Verifica si la empresa tiene suscripción AURA activa"""
        return self.company.premium_services.get('aura_enabled', False)
    
    def predict_optimal_overhead(
        self, 
        employee: PayrollEmployee, 
        historical_data: Optional[List[Dict]] = None,
        optimization_goals: Optional[Dict] = None
    ) -> Dict:
        """
        Predice overhead óptimo para un empleado usando ML y AURA
        """
        try:
            # Preparar características del empleado
            features = self._extract_employee_features(employee)
            
            # Carga datos históricos si no se proporcionan
            if historical_data is None:
                historical_data = self._get_employee_historical_data(employee)
            
            # Predicción base ML
            ml_prediction = self._predict_with_ml(features, historical_data)
            
            # Mejora con AURA (si disponible)
            if self.has_aura:
                aura_enhancement = self._enhance_with_aura(employee, ml_prediction, optimization_goals)
                final_prediction = self._combine_ml_aura(ml_prediction, aura_enhancement)
            else:
                final_prediction = ml_prediction
                aura_enhancement = {}
            
            # Análisis ético y de sesgos
            ethics_analysis = self._analyze_ethics_and_bias(employee, final_prediction)
            
            # Generar recomendaciones
            recommendations = self._generate_optimization_recommendations(
                employee, final_prediction, aura_enhancement, ethics_analysis
            )
            
            return {
                'employee_id': str(employee.id),
                'predicted_overhead': final_prediction.get('total_overhead', 0),
                'category_breakdown': final_prediction.get('categories', {}),
                'confidence_score': final_prediction.get('confidence', 0),
                'ml_prediction': ml_prediction,
                'aura_enhancement': aura_enhancement,
                'ethics_analysis': ethics_analysis,
                'optimization_potential': final_prediction.get('savings_potential', 0),
                'recommendations': recommendations,
                'model_metadata': {
                    'models_used': list(self.ml_models.keys()),
                    'has_aura': self.has_aura,
                    'predicted_at': timezone.now().isoformat(),
                    'optimization_goals': optimization_goals or {}
                }
            }
            
        except Exception as e:
            logger.error(f"Error prediciendo overhead óptimo para {employee.get_full_name()}: {e}")
            raise
    
    def _extract_employee_features(self, employee: PayrollEmployee) -> Dict:
        """Extrae características del empleado para ML"""
        features = {
            # Básicas
            'salary': float(employee.monthly_salary),
            'department_encoded': self._encode_department(employee.department),
            'job_title_encoded': self._encode_job_title(employee.job_title),
            'employee_type_encoded': self._encode_employee_type(employee.employee_type),
            
            # Experiencia y performance
            'experience_years': getattr(employee, 'experience_years', 0) or 0,
            'hire_date_days': (timezone.now().date() - employee.hire_date).days,
            'performance_score': employee.career_profile.get('avg_score', 75) if employee.career_profile else 75,
            'attendance_rate': employee.attendance_pattern.get('rate', 95) if employee.attendance_pattern else 95,
            
            # Características de la empresa
            'company_size': self.company.get_employee_count(),
            'company_industry': self._encode_industry(self.company.business_unit.name),
            'company_age_days': (timezone.now().date() - self.company.created_at.date()).days,
            
            # Métricas históricas
            'avg_historical_overhead': self._get_avg_historical_overhead(employee),
            'overhead_trend': self._get_overhead_trend(employee),
            'cost_center_avg': self._get_department_avg_overhead(employee.department)
        }
        
        return features
    
    def _encode_department(self, department: str) -> int:
        """Codifica departamento para ML"""
        encoding = {
            'it': 1, 'tecnologia': 1, 'sistemas': 1,
            'rrhh': 2, 'recursos humanos': 2, 'people': 2,
            'finanzas': 3, 'contabilidad': 3, 'finance': 3,
            'ventas': 4, 'comercial': 4, 'sales': 4,
            'marketing': 5, 'mercadotecnia': 5,
            'operaciones': 6, 'produccion': 6, 'operations': 6,
            'administracion': 7, 'admin': 7,
            'legal': 8, 'juridico': 8,
            'r&d': 9, 'investigacion': 9, 'desarrollo': 9
        }
        return encoding.get(department.lower(), 0)
    
    def _encode_job_title(self, job_title: str) -> int:
        """Codifica puesto para ML"""
        title_lower = job_title.lower()
        
        if any(word in title_lower for word in ['director', 'ceo', 'cto', 'cfo']):
            return 5  # Executive
        elif any(word in title_lower for word in ['gerente', 'manager', 'lead']):
            return 4  # Manager
        elif any(word in title_lower for word in ['coordinador', 'supervisor']):
            return 3  # Coordinator
        elif any(word in title_lower for word in ['senior', 'especialista']):
            return 2  # Senior
        else:
            return 1  # Junior/Entry level
    
    def _encode_employee_type(self, emp_type: str) -> int:
        """Codifica tipo de empleado"""
        encoding = {
            'permanent': 1,
            'temporary': 2,
            'contractor': 3,
            'intern': 4,
            'freelance': 5
        }
        return encoding.get(emp_type, 1)
    
    def _encode_industry(self, industry: str) -> int:
        """Codifica industria"""
        encoding = {
            'technology': 1, 'tech': 1,
            'finance': 2, 'fintech': 2,
            'healthcare': 3, 'health': 3,
            'retail': 4, 'e-commerce': 4,
            'manufacturing': 5, 'industrial': 5,
            'services': 6, 'consulting': 6,
            'education': 7, 'academic': 7,
            'government': 8, 'public': 8
        }
        return encoding.get(industry.lower(), 0)
    
    def _get_avg_historical_overhead(self, employee: PayrollEmployee) -> float:
        """Obtiene promedio histórico de overhead del empleado"""
        historical = EmployeeOverheadCalculation.objects.filter(
            employee=employee
        ).aggregate(avg_overhead=Avg('overhead_percentage'))
        
        return float(historical['avg_overhead'] or 0)
    
    def _get_overhead_trend(self, employee: PayrollEmployee) -> float:
        """Calcula tendencia de overhead (positiva = creciente)"""
        recent_calcs = EmployeeOverheadCalculation.objects.filter(
            employee=employee
        ).order_by('-calculated_at')[:6]  # Últimos 6 períodos
        
        if len(recent_calcs) < 2:
            return 0
        
        percentages = [float(calc.overhead_percentage) for calc in recent_calcs]
        # Simple linear trend
        x = list(range(len(percentages)))
        if len(x) > 1:
            slope = np.polyfit(x, percentages, 1)[0]
            return float(slope)
        
        return 0
    
    def _get_department_avg_overhead(self, department: str) -> float:
        """Obtiene promedio de overhead del departamento"""
        dept_avg = EmployeeOverheadCalculation.objects.filter(
            employee__department__iexact=department,
            employee__company=self.company
        ).aggregate(avg_overhead=Avg('overhead_percentage'))
        
        return float(dept_avg['avg_overhead'] or 0)
    
    def _get_employee_historical_data(self, employee: PayrollEmployee) -> List[Dict]:
        """Obtiene datos históricos del empleado"""
        historical = EmployeeOverheadCalculation.objects.filter(
            employee=employee
        ).order_by('-calculated_at')[:12]  # Último año
        
        return [
            {
                'period': calc.period.period_name,
                'total_overhead': float(calc.total_overhead),
                'overhead_percentage': float(calc.overhead_percentage),
                'categories': {
                    'infrastructure': float(calc.infrastructure_cost),
                    'administrative': float(calc.administrative_cost),
                    'benefits': float(calc.benefits_cost),
                    'training': float(calc.training_cost),
                    'technology': float(calc.technology_cost),
                    'social_impact': float(calc.social_impact_cost),
                    'sustainability': float(calc.sustainability_cost),
                    'wellbeing': float(calc.wellbeing_cost),
                    'innovation': float(calc.innovation_cost)
                }
            }
            for calc in historical
        ]
    
    def _predict_with_ml(self, features: Dict, historical_data: List[Dict]) -> Dict:
        """Realiza predicción usando modelos ML"""
        predictions = {}
        
        # Si no hay modelos entrenados, usar baseline
        if not self.ml_models:
            return self._baseline_prediction(features, historical_data)
        
        # Usar mejor modelo disponible
        best_model = max(self.ml_models.values(), key=lambda x: x['accuracy'])
        
        # Simulación de predicción ML (en implementación real usaría el modelo entrenado)
        base_overhead = features['salary'] * 0.43  # 43% base
        
        # Ajustes basados en características
        if features['department_encoded'] == 1:  # IT
            base_overhead *= 0.95  # Menor overhead administrativo
        elif features['department_encoded'] == 6:  # Operations
            base_overhead *= 1.1  # Mayor overhead
        
        # Ajuste por performance
        performance_factor = features['performance_score'] / 100
        efficiency_adjustment = 1 - (performance_factor - 0.75) * 0.2
        base_overhead *= efficiency_adjustment
        
        # Ajuste por tendencia
        trend_adjustment = 1 + (features['overhead_trend'] * 0.1)
        base_overhead *= trend_adjustment
        
        # Distribución por categorías (simulada)
        categories = {
            'infrastructure': base_overhead * 0.30,
            'administrative': base_overhead * 0.18,
            'benefits': base_overhead * 0.25,
            'training': base_overhead * 0.07,
            'technology': base_overhead * 0.20
        }
        
        return {
            'total_overhead': base_overhead,
            'categories': categories,
            'confidence': best_model['accuracy'] / 100,
            'model_used': best_model['instance'].model_name,
            'savings_potential': max(0, features['avg_historical_overhead'] - base_overhead)
        }
    
    def _baseline_prediction(self, features: Dict, historical_data: List[Dict]) -> Dict:
        """Predicción baseline cuando no hay modelos entrenados"""
        if historical_data:
            avg_overhead = sum(h['total_overhead'] for h in historical_data) / len(historical_data)
            confidence = 0.6  # Confianza baja para baseline
        else:
            # Usar benchmark industry
            avg_overhead = features['salary'] * 0.45  # 45% industry average
            confidence = 0.4
        
        # Distribución estándar
        categories = {
            'infrastructure': avg_overhead * 0.33,
            'administrative': avg_overhead * 0.17,
            'benefits': avg_overhead * 0.27,
            'training': avg_overhead * 0.06,
            'technology': avg_overhead * 0.17
        }
        
        return {
            'total_overhead': avg_overhead,
            'categories': categories,
            'confidence': confidence,
            'model_used': 'baseline',
            'savings_potential': avg_overhead * 0.1  # 10% potential savings
        }
    
    def _enhance_with_aura(
        self, 
        employee: PayrollEmployee, 
        ml_prediction: Dict,
        optimization_goals: Optional[Dict] = None
    ) -> Dict:
        """Mejora predicción ML con capacidades AURA"""
        try:
            # Análisis holístico del empleado
            holistic_profile = self.holistic_assessor.assess_employee(employee)
            
            # Personalización basada en perfil AURA
            personalization = self.personalization_engine.generate_recommendations(
                employee, context='overhead_optimization'
            )
            
            # Compatibilidad con valores organizacionales
            compatibility = self.compatibility_engine.assess_organizational_fit(
                employee, self.company
            )
            
            # Cálculo de overhead AURA enhanced
            aura_categories = self._calculate_aura_overhead_categories(
                employee, ml_prediction, holistic_profile, optimization_goals
            )
            
            # Recomendaciones ejecutivas
            executive_insights = self.executive_analytics.generate_employee_insights(
                employee, context='cost_optimization'
            )
            
            return {
                'aura_categories': aura_categories,
                'holistic_profile': holistic_profile,
                'personalization': personalization,
                'compatibility_score': compatibility,
                'executive_insights': executive_insights,
                'total_aura_overhead': sum(aura_categories.values()),
                'aura_optimization_potential': self._calculate_aura_optimization(
                    ml_prediction, aura_categories, holistic_profile
                )
            }
            
        except Exception as e:
            logger.error(f"Error en mejora AURA: {e}")
            return {}
    
    def _calculate_aura_overhead_categories(
        self, 
        employee: PayrollEmployee, 
        ml_prediction: Dict,
        holistic_profile: Dict,
        optimization_goals: Optional[Dict] = None
    ) -> Dict:
        """Calcula categorías de overhead mejoradas con AURA"""
        base_salary = float(employee.monthly_salary)
        
        # Factores AURA basados en perfil holístico
        wellbeing_factor = holistic_profile.get('wellbeing_score', 75) / 100
        sustainability_factor = holistic_profile.get('sustainability_score', 75) / 100
        innovation_factor = holistic_profile.get('innovation_potential', 75) / 100
        social_impact_factor = holistic_profile.get('social_impact_score', 75) / 100
        
        # Ajustar según objetivos de optimización
        if optimization_goals:
            if optimization_goals.get('focus') == 'sustainability':
                sustainability_factor *= 1.3
            elif optimization_goals.get('focus') == 'innovation':
                innovation_factor *= 1.3
            elif optimization_goals.get('focus') == 'wellbeing':
                wellbeing_factor *= 1.3
        
        aura_categories = {
            'social_impact': base_salary * 0.02 * social_impact_factor,
            'sustainability': base_salary * 0.015 * sustainability_factor,
            'wellbeing': base_salary * 0.025 * wellbeing_factor,
            'innovation': base_salary * 0.02 * innovation_factor
        }
        
        return aura_categories
    
    def _calculate_aura_optimization(
        self, 
        ml_prediction: Dict, 
        aura_categories: Dict,
        holistic_profile: Dict
    ) -> Dict:
        """Calcula potencial de optimización con AURA"""
        # Eficiencia AURA vs predicción ML base
        total_ml = ml_prediction['total_overhead']
        total_aura = sum(aura_categories.values())
        
        # Factores de optimización
        holistic_score = holistic_profile.get('overall_score', 75)
        optimization_multiplier = holistic_score / 100
        
        # Potencial de ahorro
        base_savings = ml_prediction.get('savings_potential', 0)
        aura_enhanced_savings = base_savings * optimization_multiplier * 1.2  # 20% boost with AURA
        
        return {
            'base_ml_overhead': total_ml,
            'aura_enhanced_overhead': total_aura,
            'efficiency_gain': max(0, total_ml - total_aura),
            'optimization_multiplier': optimization_multiplier,
            'enhanced_savings_potential': aura_enhanced_savings,
            'holistic_optimization_score': holistic_score
        }
    
    def _combine_ml_aura(self, ml_prediction: Dict, aura_enhancement: Dict) -> Dict:
        """Combina predicción ML con mejora AURA"""
        combined = ml_prediction.copy()
        
        if aura_enhancement:
            # Combinar categorías
            combined_categories = combined['categories'].copy()
            combined_categories.update(aura_enhancement.get('aura_categories', {}))
            
            # Recalcular total
            total_combined = sum(combined_categories.values())
            
            # Ajustar confianza
            aura_confidence_boost = 0.15  # AURA aumenta confianza 15%
            new_confidence = min(0.95, combined['confidence'] + aura_confidence_boost)
            
            combined.update({
                'categories': combined_categories,
                'total_overhead': total_combined,
                'confidence': new_confidence,
                'aura_enhanced': True,
                'savings_potential': aura_enhancement.get('aura_optimization_potential', {}).get(
                    'enhanced_savings_potential', combined['savings_potential']
                )
            })
        
        return combined
    
    def _analyze_ethics_and_bias(self, employee: PayrollEmployee, prediction: Dict) -> Dict:
        """Analiza aspectos éticos y sesgos en la predicción"""
        try:
            # Detectar sesgos potenciales
            bias_analysis = self.bias_detector.analyze_prediction_bias(
                employee_data={
                    'department': employee.department,
                    'job_title': employee.job_title,
                    'salary': float(employee.monthly_salary),
                    'gender': getattr(employee, 'gender', 'unknown'),
                    'age': self._calculate_age(employee),
                },
                prediction=prediction
            )
            
            # Análisis ético
            ethics_score = self.ethics_engine.evaluate_decision(
                decision_context='overhead_optimization',
                affected_party=employee,
                decision_data=prediction
            )
            
            # Fairness optimization
            fairness_recommendations = self.fairness_optimizer.generate_fairness_improvements(
                current_allocation=prediction,
                employee_profile=employee
            )
            
            return {
                'bias_analysis': bias_analysis,
                'ethics_score': ethics_score,
                'fairness_recommendations': fairness_recommendations,
                'overall_ethical_rating': self._calculate_ethical_rating(
                    bias_analysis, ethics_score, fairness_recommendations
                )
            }
            
        except Exception as e:
            logger.error(f"Error en análisis ético: {e}")
            return {
                'bias_analysis': {},
                'ethics_score': 75,  # Default neutral score
                'fairness_recommendations': [],
                'overall_ethical_rating': 'Neutral'
            }
    
    def _calculate_age(self, employee: PayrollEmployee) -> int:
        """Calcula edad del empleado"""
        if hasattr(employee, 'fecha_nacimiento') and employee.fecha_nacimiento:
            today = timezone.now().date()
            return today.year - employee.fecha_nacimiento.year
        return 30  # Default age if not available
    
    def _calculate_ethical_rating(self, bias_analysis: Dict, ethics_score: float, fairness_recs: List) -> str:
        """Calcula rating ético general"""
        bias_score = bias_analysis.get('overall_bias_score', 50)
        fairness_issues = len(fairness_recs)
        
        combined_score = (ethics_score + (100 - bias_score)) / 2
        combined_score -= (fairness_issues * 5)  # Penalizar por issues de fairness
        
        if combined_score >= 85:
            return 'Excelente'
        elif combined_score >= 75:
            return 'Bueno'
        elif combined_score >= 65:
            return 'Aceptable'
        elif combined_score >= 50:
            return 'Necesita Mejoras'
        else:
            return 'Problemático'
    
    def _generate_optimization_recommendations(
        self, 
        employee: PayrollEmployee, 
        prediction: Dict,
        aura_enhancement: Dict,
        ethics_analysis: Dict
    ) -> List[Dict]:
        """Genera recomendaciones de optimización"""
        recommendations = []
        
        # Recomendaciones basadas en predicción ML
        savings_potential = prediction.get('savings_potential', 0)
        if savings_potential > employee.monthly_salary * 0.05:  # >5% salary
            recommendations.append({
                'type': 'cost_reduction',
                'priority': 'High',
                'category': 'general',
                'description': f'Potencial de ahorro de ${savings_potential:,.2f} mensual',
                'action': 'Revisar procesos y asignación de recursos',
                'impact': 'financial'
            })
        
        # Recomendaciones por categoría
        categories = prediction.get('categories', {})
        for category, amount in categories.items():
            percentage = (amount / employee.monthly_salary) * 100
            if percentage > 20:  # >20% del salario en una categoría
                recommendations.append({
                    'type': 'category_optimization',
                    'priority': 'Medium',
                    'category': category,
                    'description': f'Alto overhead en {category}: {percentage:.1f}% del salario',
                    'action': f'Optimizar procesos de {category}',
                    'impact': 'operational'
                })
        
        # Recomendaciones AURA (si disponible)
        if aura_enhancement and self.has_aura:
            aura_insights = aura_enhancement.get('executive_insights', {})
            if aura_insights.get('recommendations'):
                for rec in aura_insights['recommendations']:
                    recommendations.append({
                        'type': 'aura_enhancement',
                        'priority': 'Medium',
                        'category': 'strategic',
                        'description': rec.get('description', ''),
                        'action': rec.get('action', ''),
                        'impact': 'strategic'
                    })
        
        # Recomendaciones éticas
        fairness_recs = ethics_analysis.get('fairness_recommendations', [])
        for rec in fairness_recs:
            recommendations.append({
                'type': 'ethical_improvement',
                'priority': 'High',
                'category': 'ethics',
                'description': rec.get('description', ''),
                'action': rec.get('action', ''),
                'impact': 'ethical'
            })
        
        return sorted(recommendations, key=lambda x: {
            'High': 3, 'Medium': 2, 'Low': 1
        }.get(x['priority'], 0), reverse=True)
    
    def analyze_team_ml_optimization(
        self, 
        team_employees: List[PayrollEmployee],
        team_data: Dict,
        optimization_goals: Optional[Dict] = None
    ) -> Dict:
        """Analiza optimización ML para todo el equipo"""
        try:
            team_predictions = []
            total_current_overhead = 0
            total_optimized_overhead = 0
            
            # Predicciones individuales
            for employee in team_employees:
                prediction = self.predict_optimal_overhead(employee, optimization_goals=optimization_goals)
                team_predictions.append(prediction)
                
                # Calcular overhead actual vs optimizado
                current = self._get_current_employee_overhead(employee)
                total_current_overhead += current
                total_optimized_overhead += prediction['predicted_overhead']
            
            # Análisis del equipo
            team_savings = total_current_overhead - total_optimized_overhead
            team_efficiency = (total_optimized_overhead / total_current_overhead) * 100 if total_current_overhead > 0 else 100
            
            # Análisis AURA del equipo (si disponible)
            team_aura_analysis = {}
            if self.has_aura:
                team_aura_analysis = self._analyze_team_aura_optimization(team_employees, team_predictions)
            
            # Recomendaciones del equipo
            team_recommendations = self._generate_team_ml_recommendations(
                team_employees, team_predictions, team_aura_analysis
            )
            
            # Análisis de riesgo y factibilidad
            risk_analysis = self._analyze_optimization_risks(team_predictions)
            
            return {
                'team_name': team_data.get('team_name', 'Unknown Team'),
                'team_size': len(team_employees),
                'individual_predictions': team_predictions,
                'team_metrics': {
                    'current_total_overhead': total_current_overhead,
                    'optimized_total_overhead': total_optimized_overhead,
                    'total_savings_potential': team_savings,
                    'efficiency_improvement': 100 - team_efficiency,
                    'avg_confidence': sum(p['confidence_score'] for p in team_predictions) / len(team_predictions)
                },
                'aura_team_analysis': team_aura_analysis,
                'team_recommendations': team_recommendations,
                'risk_analysis': risk_analysis,
                'implementation_roadmap': self._create_implementation_roadmap(team_recommendations),
                'metadata': {
                    'analyzed_at': timezone.now().isoformat(),
                    'has_aura': self.has_aura,
                    'optimization_goals': optimization_goals or {},
                    'analysis_version': '2.0'
                }
            }
            
        except Exception as e:
            logger.error(f"Error en análisis ML del equipo: {e}")
            raise
    
    def _get_current_employee_overhead(self, employee: PayrollEmployee) -> float:
        """Obtiene overhead actual del empleado"""
        latest_calc = EmployeeOverheadCalculation.objects.filter(
            employee=employee
        ).order_by('-calculated_at').first()
        
        if latest_calc:
            return float(latest_calc.total_overhead)
        
        # Estimación si no hay datos
        return float(employee.monthly_salary) * 0.45  # 45% default
    
    def _analyze_team_aura_optimization(
        self, 
        team_employees: List[PayrollEmployee],
        predictions: List[Dict]
    ) -> Dict:
        """Análisis AURA de optimización del equipo"""
        if not self.has_aura:
            return {}
        
        try:
            # Análisis de compatibilidad del equipo
            team_compatibility = self.compatibility_engine.analyze_team_compatibility(team_employees)
            
            # Potencial de sinergia
            synergy_potential = self._calculate_team_synergy_potential(team_employees, predictions)
            
            # Recomendaciones de estructura óptima
            optimal_structure = self._recommend_optimal_team_structure(team_employees, predictions)
            
            return {
                'team_compatibility': team_compatibility,
                'synergy_potential': synergy_potential,
                'optimal_structure': optimal_structure,
                'collective_impact_score': self._calculate_collective_impact(predictions)
            }
            
        except Exception as e:
            logger.error(f"Error en análisis AURA del equipo: {e}")
            return {}
    
    def _calculate_team_synergy_potential(
        self, 
        team_employees: List[PayrollEmployee],
        predictions: List[Dict]
    ) -> Dict:
        """Calcula potencial de sinergia del equipo"""
        # Diversidad de habilidades
        departments = set(emp.department for emp in team_employees)
        job_levels = set(self._encode_job_title(emp.job_title) for emp in team_employees)
        
        diversity_score = min(100, (len(departments) + len(job_levels)) * 10)
        
        # Eficiencia colaborativa
        avg_confidence = sum(p['confidence_score'] for p in predictions) / len(predictions)
        
        # Potencial de ahorro conjunto
        total_savings = sum(p.get('optimization_potential', 0) for p in predictions)
        
        return {
            'diversity_score': diversity_score,
            'collaborative_efficiency': avg_confidence * diversity_score / 100,
            'collective_savings_potential': total_savings,
            'synergy_multiplier': 1 + (diversity_score / 1000)  # 1.0 - 1.1x multiplier
        }
    
    def _recommend_optimal_team_structure(
        self, 
        team_employees: List[PayrollEmployee],
        predictions: List[Dict]
    ) -> Dict:
        """Recomienda estructura óptima del equipo"""
        # Análisis de costos por rol
        role_efficiency = {}
        for emp, pred in zip(team_employees, predictions):
            role = emp.job_title
            if role not in role_efficiency:
                role_efficiency[role] = []
            
            efficiency = pred['confidence_score'] * (1 - pred.get('optimization_potential', 0) / float(emp.monthly_salary))
            role_efficiency[role].append(efficiency)
        
        # Promedio por rol
        avg_role_efficiency = {
            role: sum(efficiencies) / len(efficiencies)
            for role, efficiencies in role_efficiency.items()
        }
        
        # Recomendaciones
        recommendations = []
        for role, efficiency in avg_role_efficiency.items():
            if efficiency < 0.7:  # Baja eficiencia
                recommendations.append({
                    'role': role,
                    'action': 'review_or_restructure',
                    'reason': f'Baja eficiencia detectada: {efficiency:.2%}',
                    'priority': 'High'
                })
            elif efficiency > 0.9:  # Alta eficiencia
                recommendations.append({
                    'role': role,
                    'action': 'expand_or_promote',
                    'reason': f'Alta eficiencia: {efficiency:.2%}',
                    'priority': 'Medium'
                })
        
        return {
            'role_efficiency_analysis': avg_role_efficiency,
            'structure_recommendations': recommendations,
            'optimal_team_size': self._calculate_optimal_team_size(predictions),
            'skill_gaps': self._identify_skill_gaps(team_employees)
        }
    
    def _calculate_optimal_team_size(self, predictions: List[Dict]) -> Dict:
        """Calcula tamaño óptimo del equipo"""
        current_size = len(predictions)
        avg_efficiency = sum(p['confidence_score'] for p in predictions) / len(predictions)
        
        if avg_efficiency > 0.85:
            optimal_size = int(current_size * 1.1)  # Puede crecer
            recommendation = 'expand'
        elif avg_efficiency < 0.65:
            optimal_size = max(1, int(current_size * 0.9))  # Debe reducir
            recommendation = 'downsize'
        else:
            optimal_size = current_size
            recommendation = 'maintain'
        
        return {
            'current_size': current_size,
            'optimal_size': optimal_size,
            'recommendation': recommendation,
            'efficiency_threshold': avg_efficiency
        }
    
    def _identify_skill_gaps(self, team_employees: List[PayrollEmployee]) -> List[str]:
        """Identifica gaps de habilidades en el equipo"""
        departments = set(emp.department.lower() for emp in team_employees)
        
        # Skills críticos por industria
        critical_skills = {
            'technology', 'digital_marketing', 'data_analysis', 
            'project_management', 'customer_service', 'finance'
        }
        
        current_skills = set()
        for emp in team_employees:
            dept = emp.department.lower()
            if 'it' in dept or 'tech' in dept:
                current_skills.add('technology')
            elif 'marketing' in dept:
                current_skills.add('digital_marketing')
            elif 'finance' in dept or 'contab' in dept:
                current_skills.add('finance')
            # Add more mappings as needed
        
        gaps = list(critical_skills - current_skills)
        return gaps
    
    def _calculate_collective_impact(self, predictions: List[Dict]) -> float:
        """Calcula score de impacto colectivo"""
        total_savings = sum(p.get('optimization_potential', 0) for p in predictions)
        avg_confidence = sum(p['confidence_score'] for p in predictions) / len(predictions)
        
        # Score basado en savings potenciales y confianza
        impact_score = (total_savings / 1000) * avg_confidence  # Normalize savings
        return min(100, impact_score)
    
    def _generate_team_ml_recommendations(
        self, 
        team_employees: List[PayrollEmployee],
        predictions: List[Dict],
        aura_analysis: Dict
    ) -> List[Dict]:
        """Genera recomendaciones ML para el equipo"""
        recommendations = []
        
        # Analizar savings potenciales
        total_savings = sum(p.get('optimization_potential', 0) for p in predictions)
        if total_savings > 5000:  # Significant savings potential
            recommendations.append({
                'type': 'team_cost_optimization',
                'priority': 'High',
                'description': f'Potencial de ahorro de ${total_savings:,.2f} mensual para el equipo',
                'action': 'Implementar optimizaciones ML identificadas',
                'timeline': '3-6 months',
                'impact': 'financial'
            })
        
        # Recomendaciones de estructura
        if aura_analysis.get('optimal_structure', {}).get('structure_recommendations'):
            for struct_rec in aura_analysis['optimal_structure']['structure_recommendations']:
                if struct_rec['priority'] == 'High':
                    recommendations.append({
                        'type': 'team_restructure',
                        'priority': 'Medium',
                        'description': f"Optimizar rol: {struct_rec['role']}",
                        'action': struct_rec['action'],
                        'timeline': '1-3 months',
                        'impact': 'operational'
                    })
        
        # Recomendaciones de sinergia
        synergy = aura_analysis.get('synergy_potential', {})
        if synergy.get('synergy_multiplier', 1) > 1.05:  # >5% synergy potential
            recommendations.append({
                'type': 'synergy_enhancement',
                'priority': 'Medium',
                'description': 'Alto potencial de sinergia detectado',
                'action': 'Implementar estrategias de colaboración mejorada',
                'timeline': '2-4 months',
                'impact': 'strategic'
            })
        
        return recommendations
    
    def _analyze_optimization_risks(self, predictions: List[Dict]) -> Dict:
        """Analiza riesgos de la optimización"""
        # Calcular riesgos
        low_confidence_count = sum(1 for p in predictions if p['confidence_score'] < 0.7)
        high_savings_count = sum(1 for p in predictions if p.get('optimization_potential', 0) > p.get('predicted_overhead', 0) * 0.2)
        
        risk_level = 'Low'
        if low_confidence_count > len(predictions) * 0.3:  # >30% low confidence
            risk_level = 'High'
        elif high_savings_count > len(predictions) * 0.5:  # >50% high savings
            risk_level = 'Medium'
        
        return {
            'overall_risk_level': risk_level,
            'low_confidence_predictions': low_confidence_count,
            'high_impact_changes': high_savings_count,
            'risk_factors': self._identify_risk_factors(predictions),
            'mitigation_strategies': self._generate_mitigation_strategies(risk_level)
        }
    
    def _identify_risk_factors(self, predictions: List[Dict]) -> List[str]:
        """Identifica factores de riesgo"""
        factors = []
        
        confidences = [p['confidence_score'] for p in predictions]
        if min(confidences) < 0.6:
            factors.append('Predicciones con baja confianza')
        
        if len(set(p.get('model_used', '') for p in predictions)) > 2:
            factors.append('Múltiples modelos con resultados inconsistentes')
        
        savings = [p.get('optimization_potential', 0) for p in predictions]
        if max(savings) > sum(savings) / len(savings) * 3:  # Outlier detection
            factors.append('Savings potenciales muy variables')
        
        return factors
    
    def _generate_mitigation_strategies(self, risk_level: str) -> List[str]:
        """Genera estrategias de mitigación"""
        strategies = []
        
        if risk_level == 'High':
            strategies.extend([
                'Implementar cambios gradualmente',
                'Monitorear KPIs semanalmente',
                'Tener plan de rollback preparado',
                'Validar predicciones con datos adicionales'
            ])
        elif risk_level == 'Medium':
            strategies.extend([
                'Implementar en fases piloto',
                'Monitorear mensualmente',
                'Ajustar según resultados iniciales'
            ])
        else:  # Low risk
            strategies.extend([
                'Proceder con implementación estándar',
                'Monitorear trimestralmente'
            ])
        
        return strategies
    
    def _create_implementation_roadmap(self, recommendations: List[Dict]) -> Dict:
        """Crea roadmap de implementación"""
        # Agrupar por timeline
        phases = {
            'immediate': [],  # 0-1 month
            'short_term': [],  # 1-3 months
            'medium_term': [],  # 3-6 months
            'long_term': []  # 6+ months
        }
        
        for rec in recommendations:
            timeline = rec.get('timeline', '1-3 months')
            if 'immediate' in timeline or 'week' in timeline:
                phases['immediate'].append(rec)
            elif '1-3' in timeline:
                phases['short_term'].append(rec)
            elif '3-6' in timeline:
                phases['medium_term'].append(rec)
            else:
                phases['long_term'].append(rec)
        
        return {
            'phases': phases,
            'total_duration': '6-12 months',
            'key_milestones': [
                'Completar optimizaciones inmediatas (1 mes)',
                'Evaluar resultados fase piloto (3 meses)',
                'Implementación completa (6 meses)',
                'Evaluación final y ajustes (12 meses)'
            ],
            'success_metrics': [
                'Reducción de overhead total',
                'Mejora en scores de eficiencia',
                'Satisfacción del equipo',
                'ROI de optimización'
            ]
        }