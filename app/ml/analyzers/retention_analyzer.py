# /home/pablo/app/ml/analyzers/retention_analyzer.py
"""
Retention Analyzer module for Grupo huntRED® assessment system.

This module analyzes behavior patterns to identify early signals of
potential disengagement of valuable talent.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random

import numpy as np
from django.conf import settings

from app.models import Person, BusinessUnit
from app.ats.ml.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class RetentionAnalyzerImpl(BaseAnalyzer):
    """
    Analyzer for retention risk and disengagement signals.
    
    Identifies early warning signals of potential disengagement and
    provides personalized retention strategies.
    """
    
    # Risk levels and thresholds
    RISK_LEVELS = {
        'Low': {'threshold': 30, 'color': 'green'},
        'Medium': {'threshold': 60, 'color': 'yellow'},
        'High': {'threshold': 80, 'color': 'orange'},
        'Critical': {'threshold': 100, 'color': 'red'}
    }
    
    # Risk factors and weights
    RISK_FACTORS = {
        'job_satisfaction': 0.25,
        'performance_trend': 0.20,
        'workload': 0.15,
        'team_integration': 0.15,
        'career_growth': 0.15,
        'compensation': 0.10
    }
    
    def __init__(self):
        """Initialize the retention analyzer."""
        super().__init__()
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for retention analysis."""
        return ['person_id']
        
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analyze retention risk and disengagement signals.
        
        Args:
            data: Dictionary containing person_id
            business_unit: Business unit context for analysis
            
        Returns:
            Dict with retention risk analysis and recommendations
        """
        try:
            # Check cache first
            person_id = data.get('person_id')
            cached_result = self.get_cached_result(data, "retention_analysis")
            if cached_result:
                return cached_result
                
            # Validate input
            is_valid, error_message = self.validate_input(data)
            if not is_valid:
                logger.warning(f"Invalid input for retention analysis: {error_message}")
                return self.get_default_result(error_message)
                
            # Get business unit context
            bu_name = self.get_business_unit_name(business_unit)
                
            # Get person data
            person_data = self._get_person_data(person_id)
            if not person_data:
                return self.get_default_result("Person not found")
                
            # Analyze risk factors
            risk_factors = self._analyze_risk_factors(person_id, person_data)
            
            # Calculate overall risk score
            risk_score = self._calculate_risk_score(risk_factors)
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Identify warning signals
            warning_signals = self._identify_warning_signals(risk_factors)
            
            # Generate retention strategies
            retention_strategies = self._generate_retention_strategies(
                risk_factors, 
                risk_level,
                person_data
            )
            
            # Compile results
            result = {
                'person_id': person_id,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'warning_signals': warning_signals,
                'retention_strategies': retention_strategies,
                'business_unit': bu_name,
                'analyzed_at': datetime.now().isoformat()
            }
            
            # Cache result
            self.set_cached_result(data, result, "retention_analysis")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in retention analysis: {str(e)}")
            return self.get_default_result(f"Analysis error: {str(e)}")
    
    def _get_person_data(self, person_id: int) -> Dict:
        """
        Get person data for retention analysis.
        
        Args:
            person_id: ID of the person
            
        Returns:
            Dict with person data
        """
        try:
            # In a real implementation, this would retrieve person data from the database
            # This is a simplified version for demonstration
            random.seed(person_id)  # Ensure deterministic output for testing
            
            # Generate tenure between 6 months and 7 years
            tenure_months = random.randint(6, 84)
            
            positions = ["Analyst", "Senior Analyst", "Manager", "Senior Manager", "Director"]
            position_index = min(int(tenure_months / 18), len(positions) - 1)
            
            return {
                'id': person_id,
                'name': f"Person {person_id}",
                'position': positions[position_index],
                'tenure_months': tenure_months,
                'team_size': random.randint(3, 15),
                'manager_id': random.randint(1000, 1100),
                'performance_rating': round(random.uniform(2.5, 5.0), 1),
                'last_promotion_months': random.randint(0, 36),
                'salary_percentile': random.randint(30, 90)
            }
        except Exception as e:
            logger.error(f"Error getting person data: {str(e)}")
            return {}
    
    def _analyze_risk_factors(self, person_id: int, person_data: Dict) -> Dict:
        """
        Analyze retention risk factors.
        
        Args:
            person_id: ID of the person
            person_data: Person data
            
        Returns:
            Dict with risk factors analysis
        """
        # For demonstration, we'll generate simulated risk factors
        # In a real implementation, this would analyze various data sources
        
        # Ensure deterministic output for testing
        random.seed(person_id + 1)  
        
        # Job satisfaction (higher is better)
        job_satisfaction = random.randint(40, 95)
        
        # Performance trend (higher is better)
        performance_rating = person_data.get('performance_rating', 3.0)
        performance_trend = min(100, int(performance_rating * 20))
        
        # Workload (higher score = worse workload)
        workload = random.randint(30, 90)
        
        # Team integration (higher is better)
        team_integration = random.randint(50, 95)
        
        # Career growth (higher is better)
        months_since_promotion = person_data.get('last_promotion_months', 24)
        career_growth = max(20, 100 - (months_since_promotion * 2))
        
        # Compensation satisfaction (higher is better)
        salary_percentile = person_data.get('salary_percentile', 50)
        compensation = salary_percentile
        
        # Convert factors so higher values = higher risk
        return {
            'job_satisfaction': 100 - job_satisfaction,
            'performance_trend': 100 - performance_trend,
            'workload': workload,
            'team_integration': 100 - team_integration,
            'career_growth': 100 - career_growth,
            'compensation': 100 - compensation
        }
    
    def _calculate_risk_score(self, risk_factors: Dict) -> float:
        """
        Calculate overall retention risk score.
        
        Args:
            risk_factors: Risk factors with scores
            
        Returns:
            Overall risk score (0-100)
        """
        # Calculate weighted average of risk factors
        weighted_sum = sum(
            risk_factors.get(factor, 50) * weight
            for factor, weight in self.RISK_FACTORS.items()
        )
        
        return round(weighted_sum, 1)
    
    def _determine_risk_level(self, risk_score: float) -> Dict:
        """
        Determine risk level based on risk score.
        
        Args:
            risk_score: Overall risk score
            
        Returns:
            Dict with risk level information
        """
        level = "Low"
        
        for risk_level, info in sorted(
            self.RISK_LEVELS.items(), 
            key=lambda x: x[1]['threshold']
        ):
            if risk_score <= info['threshold']:
                level = risk_level
                break
        
        return {
            'level': level,
            'color': self.RISK_LEVELS[level]['color']
        }
    
    def _identify_warning_signals(self, risk_factors: Dict) -> List[Dict]:
        """
        Identify warning signals from risk factors.
        
        Args:
            risk_factors: Risk factors with scores
            
        Returns:
            List of warning signals
        """
        signals = []
        
        # Check each factor for high risk
        for factor, score in risk_factors.items():
            if score >= 70:
                severity = "High" if score >= 85 else "Medium"
                
                # Generate appropriate description based on factor
                if factor == 'job_satisfaction':
                    description = "Baja satisfacción laboral"
                    impact = "Alta probabilidad de búsqueda activa de empleo"
                elif factor == 'performance_trend':
                    description = "Tendencia negativa en desempeño"
                    impact = "Indica posible desconexión o desmotivación"
                elif factor == 'workload':
                    description = "Sobrecarga de trabajo"
                    impact = "Riesgo de burnout y búsqueda de opciones más equilibradas"
                elif factor == 'team_integration':
                    description = "Baja integración con el equipo"
                    impact = "Falta de conexión social, menor retención"
                elif factor == 'career_growth':
                    description = "Estancamiento en desarrollo profesional"
                    impact = "Búsqueda de oportunidades de crecimiento en otro lugar"
                elif factor == 'compensation':
                    description = "Insatisfacción con compensación"
                    impact = "Vulnerabilidad ante ofertas externas competitivas"
                else:
                    description = f"Problema en {factor}"
                    impact = "Impacto negativo en retención"
                
                signals.append({
                    'factor': factor,
                    'score': score,
                    'severity': severity,
                    'description': description,
                    'impact': impact
                })
        
        return signals
    
    def _generate_retention_strategies(self, risk_factors: Dict, risk_level: Dict, 
                                     person_data: Dict) -> List[Dict]:
        """
        Generate personalized retention strategies.
        
        Args:
            risk_factors: Risk factors with scores
            risk_level: Risk level information
            person_data: Person data
            
        Returns:
            List of retention strategies
        """
        strategies = []
        
        # Add strategies based on risk factors
        high_risk_factors = [
            factor for factor, score in risk_factors.items() 
            if score >= 60
        ]
        
        # Job satisfaction strategies
        if 'job_satisfaction' in high_risk_factors:
            strategies.append({
                'area': 'Satisfacción laboral',
                'actions': [
                    'Realizar entrevista de satisfacción',
                    'Revisar asignación de proyectos',
                    'Considerar rotación de responsabilidades'
                ],
                'priority': 'high' if risk_factors.get('job_satisfaction', 0) >= 80 else 'medium',
                'timeframe': 'Inmediato'
            })
        
        # Performance trend strategies
        if 'performance_trend' in high_risk_factors:
            strategies.append({
                'area': 'Desempeño',
                'actions': [
                    'Sesión de retroalimentación constructiva',
                    'Identificar obstáculos para el rendimiento',
                    'Establecer metas claras de corto plazo'
                ],
                'priority': 'high' if risk_factors.get('performance_trend', 0) >= 80 else 'medium',
                'timeframe': '2 semanas'
            })
        
        # Workload strategies
        if 'workload' in high_risk_factors:
            strategies.append({
                'area': 'Carga de trabajo',
                'actions': [
                    'Revisar y redistribuir cargas de trabajo',
                    'Considerar recursos adicionales temporales',
                    'Priorizar y eliminar tareas no esenciales'
                ],
                'priority': 'high' if risk_factors.get('workload', 0) >= 80 else 'medium',
                'timeframe': '1 mes'
            })
        
        # Team integration strategies
        if 'team_integration' in high_risk_factors:
            strategies.append({
                'area': 'Integración de equipo',
                'actions': [
                    'Asignar a proyectos colaborativos',
                    'Incorporar en actividades de team building',
                    'Crear rol de mentor/mentee dentro del equipo'
                ],
                'priority': 'medium',
                'timeframe': '2 meses'
            })
        
        # Career growth strategies
        if 'career_growth' in high_risk_factors:
            last_promotion = person_data.get('last_promotion_months', 24)
            
            strategies.append({
                'area': 'Desarrollo profesional',
                'actions': [
                    'Crear plan de desarrollo individual',
                    'Identificar oportunidades de crecimiento',
                    'Considerar para promoción' if last_promotion > 18 else 'Asignar proyectos de alto impacto'
                ],
                'priority': 'high' if risk_factors.get('career_growth', 0) >= 80 else 'medium',
                'timeframe': '3 meses'
            })
        
        # Compensation strategies
        if 'compensation' in high_risk_factors:
            salary_percentile = person_data.get('salary_percentile', 50)
            
            strategies.append({
                'area': 'Compensación',
                'actions': [
                    'Revisar equidad salarial interna',
                    'Explorar beneficios no monetarios',
                    'Considerar ajuste salarial' if salary_percentile < 50 else 'Evaluar para bono por desempeño'
                ],
                'priority': 'medium',
                'timeframe': 'Próximo ciclo de revisión'
            })
        
        # Add general strategies for overall risk
        if risk_level['level'] in ['High', 'Critical']:
            strategies.append({
                'area': 'Engagement general',
                'actions': [
                    'Reunión 1:1 con gerente directo',
                    'Seguimiento semanal de satisfacción',
                    'Evaluar para programa de reconocimiento'
                ],
                'priority': 'high',
                'timeframe': 'Inmediato'
            })
        
        return strategies
    
    def get_default_result(self, error_message: str = None) -> Dict:
        """
        Get default retention analysis result.
        
        Args:
            error_message: Optional error message
            
        Returns:
            Default analysis result
        """
        return {
            'person_id': None,
            'risk_score': 0,
            'risk_level': {
                'level': 'Unknown',
                'color': 'gray'
            },
            'risk_factors': {},
            'warning_signals': [],
            'retention_strategies': [
                {
                    'area': 'General',
                    'actions': ['Completar perfil para análisis detallado'],
                    'priority': 'medium',
                    'timeframe': 'N/A'
                }
            ],
            'error': error_message,
            'analyzed_at': datetime.now().isoformat()
        }
