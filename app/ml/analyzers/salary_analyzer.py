# /home/pablo/app/ml/analyzers/salary_analyzer.py
"""
Salary Analyzer module for Grupo huntRED® assessment system.

This module analyzes salary competitiveness, satisfaction, and projections
to optimize compensation strategies and retention.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio

import numpy as np
from django.conf import settings
from django.core.cache import cache
from asgiref.sync import sync_to_async

from app.models import Person, BusinessUnit, Vacante, Skill
from app.ats.ml.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class SalaryAnalyzer(BaseAnalyzer):
    """
    Analyzer for salary competitiveness, satisfaction and projections.
    
    Provides insights on salary positioning, satisfaction levels,
    and career growth recommendations based on compensation data.
    """
    
    # Salary percentile thresholds for market comparison
    SALARY_PERCENTILES = {
        'low': 25,        # Bottom 25%
        'below_avg': 40,  # Below average
        'average': 50,    # Average (median)
        'above_avg': 75,  # Above average
        'high': 90        # Top 10%
    }
    
    # Satisfaction indicators and their scoring thresholds
    SATISFACTION_THRESHOLDS = {
        'very_low': 0.25,
        'low': 0.40,
        'moderate': 0.60,
        'high': 0.75,
        'very_high': 0.90
    }
    
    # Industry adjustment factors (examples)
    INDUSTRY_FACTORS = {
        'technology': 1.15,
        'finance': 1.10,
        'healthcare': 1.05,
        'retail': 0.90,
        'education': 0.85,
        'manufacturing': 0.95,
        'consulting': 1.08,
        'non_profit': 0.80
    }
    
    # Location adjustment factors (examples)
    LOCATION_FACTORS = {
        'capital_city': 1.20,
        'major_city': 1.10,
        'mid_size_city': 1.00,
        'small_city': 0.90,
        'rural': 0.80
    }
    
    def __init__(self):
        """Initialize the salary analyzer with required models."""
        super().__init__()
        self.cache_timeout = 86400 * 7  # 7 days (in seconds)
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for salary analysis."""
        return ['person_id']
        
    async def analyze_async(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Async version of analyze method for better performance.
        
        Args:
            data: Dictionary containing person_id and optional parameters
            business_unit: Optional business unit context
            
        Returns:
            Dict with salary analysis results
        """
        try:
            person_id = data.get('person_id')
            
            # Get person data asynchronously
            person = await self._get_person_async(person_id)
            if not person:
                return self.get_default_result("Person not found")
                
            # Get market data asynchronously
            market_data = await self._get_market_data_async(person)
            
            # Get satisfaction indicators
            satisfaction = await self._analyze_satisfaction_async(person)
            
            # Calculate competitiveness
            competitiveness = self._calculate_competitiveness(
                person.current_salary if hasattr(person, 'current_salary') else 0,
                market_data
            )
            
            # Generate projections
            projections = await self._generate_projections_async(person, market_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                competitiveness,
                satisfaction,
                projections,
                person
            )
            
            # Return comprehensive analysis
            return {
                'status': 'success',
                'person_id': person_id,
                'market_data': market_data,
                'competitiveness': competitiveness,
                'satisfaction': satisfaction,
                'projections': projections,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error in async salary analysis: {str(e)}", exc_info=True)
            return self.get_default_result(f"Analysis error: {str(e)}")
        
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analyze salary data for a person.
        
        Args:
            data: Dictionary containing person_id and optional parameters
            business_unit: Optional business unit context
            
        Returns:
            Dict with salary analysis results
        """
        try:
            # Check cache first
            person_id = data.get('person_id')
            cached_result = self.get_cached_result(data, "salary_insights")
            if cached_result:
                return cached_result
                
            # Validate input
            is_valid, error_message = self.validate_input(data)
            if not is_valid:
                logger.warning(f"Invalid input for salary analysis: {error_message}")
                return self.get_default_result(error_message)
                
            # Get person data
            person = self._get_person(person_id)
            if not person:
                return self.get_default_result("Person not found")
            
            # Perform salary analysis
            result = asyncio.run(self.analyze_async(data, business_unit))
            
            # Cache and return results
            self.set_cached_result(data, result, "salary_insights")
            return result
            
        except Exception as e:
            logger.error(f"Error in salary analysis: {str(e)}", exc_info=True)
            return self.get_default_result(f"Analysis error: {str(e)}")
    
    def _get_person(self, person_id: int) -> Optional[Person]:
        """Get person object from database."""
        try:
            return Person.objects.get(id=person_id)
        except Person.DoesNotExist:
            logger.warning(f"Person with ID {person_id} not found")
            return None
    
    @sync_to_async
    def _get_person_async(self, person_id: int) -> Optional[Person]:
        """Get person object from database asynchronously."""
        return self._get_person(person_id)
    
    def _get_market_data(self, person: Person) -> Dict:
        """
        Get market salary data for comparable positions.
        
        In a production environment, this would query actual market data sources
        or internal salary benchmarks. This implementation uses a simulated approach.
        """
        # This is a simplified implementation
        # In production, this would query actual market data
        
        # Example market data structure
        market_data = {
            'role_type': 'developer' if hasattr(person, 'role') else 'unknown',
            'industry': 'technology' if hasattr(person, 'industry') else 'unknown',
            'location': 'major_city' if hasattr(person, 'location') else 'unknown',
            'years_experience': getattr(person, 'years_experience', 5),
            'skill_level': 'senior' if getattr(person, 'years_experience', 0) > 5 else 'mid',
            'percentiles': {
                '10': 30000,
                '25': 45000,
                '50': 60000,
                '75': 80000,
                '90': 100000
            },
            'average': 65000,
            'currency': 'USD',
            'benefits_value': 12000,  # Estimated annual value of benefits
            'total_compensation_avg': 77000
        }
        
        # Apply industry adjustment
        industry = getattr(person, 'industry', 'unknown')
        industry_factor = self.INDUSTRY_FACTORS.get(industry, 1.0)
        
        # Apply location adjustment
        location = getattr(person, 'location', 'unknown') 
        location_factor = self.LOCATION_FACTORS.get(location, 1.0)
        
        # Apply adjustments to all values
        combined_factor = industry_factor * location_factor
        for percentile in market_data['percentiles']:
            market_data['percentiles'][percentile] = int(market_data['percentiles'][percentile] * combined_factor)
        
        market_data['average'] = int(market_data['average'] * combined_factor)
        market_data['benefits_value'] = int(market_data['benefits_value'] * combined_factor)
        market_data['total_compensation_avg'] = int(market_data['total_compensation_avg'] * combined_factor)
        
        return market_data
    
    @sync_to_async
    def _get_market_data_async(self, person: Person) -> Dict:
        """Get market salary data asynchronously."""
        return self._get_market_data(person)
    
    def _analyze_satisfaction(self, person: Person) -> Dict:
        """
        Analyze salary satisfaction indicators.
        
        In a production environment, this would use survey data, feedback,
        performance reviews, etc. This implementation uses a simulated approach.
        """
        # This is a simplified implementation
        # In production, this would use actual satisfaction metrics
        
        # Generate deterministic but realistic satisfaction metrics
        import hashlib
        import random
        
        # Use person ID for consistent results
        seed = int(hashlib.md5(str(person.id).encode()).hexdigest(), 16) % 10000
        random.seed(seed)
        
        # Calculate base satisfaction scores
        base_compensation_satisfaction = round(random.uniform(0.3, 0.9), 2)
        base_benefits_satisfaction = round(random.uniform(0.4, 0.9), 2)
        base_fairness_perception = round(random.uniform(0.3, 0.8), 2)
        base_growth_satisfaction = round(random.uniform(0.4, 0.85), 2)
        
        # Adjust for salary-to-market comparison if we have current_salary data
        if hasattr(person, 'current_salary') and person.current_salary:
            current_salary = person.current_salary
            market_data = self._get_market_data(person)
            median_salary = market_data['percentiles']['50']
            
            # Adjust satisfaction based on market comparison
            salary_ratio = current_salary / median_salary
            
            compensation_adjustment = min(0.3, max(-0.3, (salary_ratio - 1) * 0.5))
            fairness_adjustment = min(0.25, max(-0.25, (salary_ratio - 1) * 0.4))
            growth_adjustment = 0.1 if salary_ratio > 1.1 else -0.1 if salary_ratio < 0.9 else 0
            
            # Apply adjustments
            base_compensation_satisfaction = min(0.95, max(0.1, base_compensation_satisfaction + compensation_adjustment))
            base_fairness_perception = min(0.95, max(0.1, base_fairness_perception + fairness_adjustment))
            base_growth_satisfaction = min(0.95, max(0.1, base_growth_satisfaction + growth_adjustment))
        
        # Determine categories based on thresholds
        compensation_category = self._get_satisfaction_category(base_compensation_satisfaction)
        benefits_category = self._get_satisfaction_category(base_benefits_satisfaction)
        fairness_category = self._get_satisfaction_category(base_fairness_perception)
        growth_category = self._get_satisfaction_category(base_growth_satisfaction)
        
        # Calculate overall satisfaction (weighted average)
        weights = {
            'compensation': 0.4,
            'benefits': 0.2,
            'fairness': 0.25,
            'growth': 0.15
        }
        
        overall_satisfaction = (
            base_compensation_satisfaction * weights['compensation'] +
            base_benefits_satisfaction * weights['benefits'] +
            base_fairness_perception * weights['fairness'] +
            base_growth_satisfaction * weights['growth']
        )
        
        overall_category = self._get_satisfaction_category(overall_satisfaction)
        
        return {
            'compensation': {
                'score': base_compensation_satisfaction,
                'category': compensation_category
            },
            'benefits': {
                'score': base_benefits_satisfaction,
                'category': benefits_category
            },
            'fairness': {
                'score': base_fairness_perception,
                'category': fairness_category
            },
            'growth': {
                'score': base_growth_satisfaction,
                'category': growth_category
            },
            'overall': {
                'score': round(overall_satisfaction, 2),
                'category': overall_category
            },
            'risk_factors': self._identify_risk_factors(
                base_compensation_satisfaction,
                base_benefits_satisfaction,
                base_fairness_perception,
                base_growth_satisfaction
            )
        }
    
    @sync_to_async
    def _analyze_satisfaction_async(self, person: Person) -> Dict:
        """Analyze satisfaction asynchronously."""
        return self._analyze_satisfaction(person)
    
    def _get_satisfaction_category(self, score: float) -> str:
        """Convert numerical satisfaction score to category."""
        if score < self.SATISFACTION_THRESHOLDS['very_low']:
            return 'very_low'
        elif score < self.SATISFACTION_THRESHOLDS['low']:
            return 'low'
        elif score < self.SATISFACTION_THRESHOLDS['moderate']:
            return 'moderate'
        elif score < self.SATISFACTION_THRESHOLDS['high']:
            return 'high'
        else:
            return 'very_high'
    
    def _identify_risk_factors(self, compensation: float, benefits: float, 
                              fairness: float, growth: float) -> List[str]:
        """Identify potential retention risk factors based on satisfaction scores."""
        risk_factors = []
        
        if compensation < self.SATISFACTION_THRESHOLDS['low']:
            risk_factors.append('severe_compensation_dissatisfaction')
        elif compensation < self.SATISFACTION_THRESHOLDS['moderate']:
            risk_factors.append('compensation_dissatisfaction')
            
        if benefits < self.SATISFACTION_THRESHOLDS['low']:
            risk_factors.append('benefits_dissatisfaction')
            
        if fairness < self.SATISFACTION_THRESHOLDS['low']:
            risk_factors.append('perceived_unfairness')
            
        if growth < self.SATISFACTION_THRESHOLDS['moderate']:
            risk_factors.append('growth_concerns')
            
        # Combined risk factors
        if compensation < self.SATISFACTION_THRESHOLDS['moderate'] and growth < self.SATISFACTION_THRESHOLDS['moderate']:
            risk_factors.append('high_attrition_risk')
            
        if fairness < self.SATISFACTION_THRESHOLDS['low'] and compensation < self.SATISFACTION_THRESHOLDS['moderate']:
            risk_factors.append('equity_concerns')
            
        return risk_factors
    
    def _calculate_competitiveness(self, current_salary: float, market_data: Dict) -> Dict:
        """
        Calculate salary competitiveness relative to market data.
        
        Args:
            current_salary: Current salary of the person
            market_data: Market salary data for comparison
            
        Returns:
            Dict with competitiveness analysis
        """
        if not current_salary:
            return {
                'percentile': 'unknown',
                'ratio_to_median': 0,
                'ratio_to_average': 0,
                'position': 'unknown',
                'gap_to_median': 0
            }
        
        # Get market percentiles
        percentiles = market_data['percentiles']
        median_salary = float(percentiles['50'])
        average_salary = float(market_data['average'])
        
        # Calculate percentile position
        # This is a simplified approach; in practice you'd use statistical methods
        estimated_percentile = 0
        for p, value in sorted([(int(k), float(v)) for k, v in percentiles.items()]):
            if current_salary <= value:
                lower_p = p
                if p == 10:  # Lowest percentile in our data
                    estimated_percentile = p * (current_salary / value)
                    break
                else:
                    # Interpolate between percentiles
                    prev_p = next(pct for pct, _ in sorted([(int(k), float(v)) for k, v in percentiles.items()]) if pct < p)
                    prev_value = float(percentiles[str(prev_p)])
                    range_size = value - prev_value
                    position_in_range = current_salary - prev_value
                    estimated_percentile = prev_p + (p - prev_p) * (position_in_range / range_size)
                    break
        else:
            # Salary is above all percentiles
            estimated_percentile = 95  # Approximation
        
        # Calculate ratios
        ratio_to_median = current_salary / median_salary if median_salary else 0
        ratio_to_average = current_salary / average_salary if average_salary else 0
        
        # Determine market position
        if ratio_to_median < 0.85:
            position = 'below_market'
        elif ratio_to_median < 0.95:
            position = 'slightly_below_market'
        elif ratio_to_median <= 1.05:
            position = 'at_market'
        elif ratio_to_median <= 1.15:
            position = 'slightly_above_market'
        else:
            position = 'above_market'
        
        # Calculate gap to median
        gap_to_median = median_salary - current_salary
        
        return {
            'percentile': round(estimated_percentile, 1),
            'ratio_to_median': round(ratio_to_median, 2),
            'ratio_to_average': round(ratio_to_average, 2),
            'position': position,
            'gap_to_median': round(gap_to_median, 2)
        }
    
    async def _generate_projections_async(self, person: Person, market_data: Dict) -> Dict:
        """
        Generate salary growth projections asynchronously.
        
        Args:
            person: Person object
            market_data: Market salary data
            
        Returns:
            Dict with salary projections
        """
        # This is a simplified implementation
        # In production, this would use more sophisticated projection models
        
        # Get base data
        current_salary = getattr(person, 'current_salary', market_data['percentiles']['25'])
        years_experience = getattr(person, 'years_experience', 3)
        skill_level = getattr(person, 'skill_level', 'mid')
        
        # Growth factors based on experience and skill level
        growth_factors = {
            'junior': 0.10,  # 10% annual growth
            'mid': 0.07,     # 7% annual growth
            'senior': 0.05,  # 5% annual growth
            'lead': 0.04,    # 4% annual growth
            'executive': 0.03 # 3% annual growth
        }
        
        # Determine base growth factor
        base_growth = growth_factors.get(skill_level, 0.07)
        
        # Adjust for experience (decreases as experience increases)
        experience_adjustment = max(0, 0.02 - (years_experience * 0.001))
        
        # Adjust for market position
        competitiveness = self._calculate_competitiveness(current_salary, market_data)
        if competitiveness['position'] == 'below_market':
            market_adjustment = 0.02  # Faster growth to catch up
        elif competitiveness['position'] == 'slightly_below_market':
            market_adjustment = 0.01
        elif competitiveness['position'] == 'slightly_above_market':
            market_adjustment = -0.01
        elif competitiveness['position'] == 'above_market':
            market_adjustment = -0.02  # Slower growth when already above market
        else:
            market_adjustment = 0
        
        # Calculate adjusted growth rate
        adjusted_growth_rate = base_growth + experience_adjustment + market_adjustment
        adjusted_growth_rate = max(0.02, min(0.15, adjusted_growth_rate))  # Cap between 2% and 15%
        
        # Generate 5-year projections
        projections = {'yearly': [], 'cumulative': []}
        projected_salary = current_salary
        
        for year in range(1, 6):  # 5-year projection
            yearly_increase = projected_salary * adjusted_growth_rate
            projected_salary += yearly_increase
            
            projections['yearly'].append({
                'year': year,
                'salary': round(projected_salary, 2),
                'increase': round(yearly_increase, 2),
                'growth_percentage': round(adjusted_growth_rate * 100, 1)
            })
        
        # Calculate cumulative growth and percentages
        initial_salary = current_salary
        for i, yearly in enumerate(projections['yearly']):
            year = i + 1
            salary = yearly['salary']
            cumulative_increase = salary - initial_salary
            cumulative_percentage = (salary / initial_salary - 1) * 100
            
            projections['cumulative'].append({
                'year': year,
                'salary': round(salary, 2),
                'total_increase': round(cumulative_increase, 2),
                'total_percentage': round(cumulative_percentage, 1)
            })
        
        # Add summary information
        projections['summary'] = {
            'current_salary': current_salary,
            'five_year_projection': round(projections['yearly'][4]['salary'], 2),
            'total_growth_amount': round(projections['cumulative'][4]['total_increase'], 2),
            'total_growth_percentage': round(projections['cumulative'][4]['total_percentage'], 1),
            'average_annual_growth': round(adjusted_growth_rate * 100, 1)
        }
        
        return projections
    
    def _generate_recommendations(self, competitiveness: Dict, satisfaction: Dict, 
                                 projections: Dict, person: Person) -> List[Dict]:
        """
        Generate actionable recommendations based on salary analysis.
        
        Args:
            competitiveness: Competitiveness analysis
            satisfaction: Satisfaction analysis
            projections: Salary projections
            person: Person object
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Market position recommendations
        market_position = competitiveness.get('position', 'unknown')
        if market_position == 'below_market':
            recommendations.append({
                'type': 'compensation',
                'title': 'Revisión Salarial',
                'description': 'El salario está significativamente por debajo del mercado. Considerar una revisión salarial para alinearse con la mediana del mercado.',
                'priority': 'high'
            })
        elif market_position == 'slightly_below_market':
            recommendations.append({
                'type': 'compensation',
                'title': 'Ajuste Gradual',
                'description': 'El salario está ligeramente por debajo del mercado. Considerar un ajuste gradual en los próximos ciclos de evaluación.',
                'priority': 'medium'
            })
        elif market_position == 'above_market':
            recommendations.append({
                'type': 'retention',
                'title': 'Enfoque en Retención',
                'description': 'El salario está por encima del mercado. Enfatizar otros aspectos de la propuesta de valor para mantener la retención.',
                'priority': 'medium'
            })
        
        # Satisfaction-based recommendations
        overall_satisfaction = satisfaction['overall']['category']
        if overall_satisfaction in ['very_low', 'low']:
            recommendations.append({
                'type': 'engagement',
                'title': 'Plan de Mejora de Satisfacción',
                'description': 'La satisfacción general es baja. Implementar un plan de mejora para abordar los factores de insatisfacción.',
                'priority': 'high'
            })
        
        compensation_satisfaction = satisfaction['compensation']['category']
        if compensation_satisfaction in ['very_low', 'low'] and market_position in ['below_market', 'slightly_below_market']:
            recommendations.append({
                'type': 'compensation',
                'title': 'Alineación Salarial Prioritaria',
                'description': 'Baja satisfacción con compensación y salario por debajo de mercado. Priorizar ajuste salarial para prevenir attrición.',
                'priority': 'high'
            })
        
        fairness_satisfaction = satisfaction['fairness']['category']
        if fairness_satisfaction in ['very_low', 'low']:
            recommendations.append({
                'type': 'equity',
                'title': 'Revisión de Equidad Interna',
                'description': 'Percepción de inequidad salarial. Realizar una revisión de equidad interna y comunicar transparentemente los resultados.',
                'priority': 'high'
            })
        
        benefits_satisfaction = satisfaction['benefits']['category']
        if benefits_satisfaction in ['very_low', 'low']:
            recommendations.append({
                'type': 'benefits',
                'title': 'Mejora de Beneficios',
                'description': 'Baja satisfacción con los beneficios. Considerar mejorar o comunicar mejor el paquete de beneficios existente.',
                'priority': 'medium'
            })
        
        growth_satisfaction = satisfaction['growth']['category']
        if growth_satisfaction in ['very_low', 'low']:
            recommendations.append({
                'type': 'development',
                'title': 'Plan de Desarrollo',
                'description': 'Baja satisfacción con crecimiento profesional. Implementar un plan de desarrollo claro con trayectoria salarial.',
                'priority': 'medium'
            })
        
        # Risk-based recommendations
        risk_factors = satisfaction.get('risk_factors', [])
        if 'high_attrition_risk' in risk_factors:
            recommendations.append({
                'type': 'retention',
                'title': 'Plan de Retención Urgente',
                'description': 'Alto riesgo de attrición identificado. Implementar plan de retención con mejoras en compensación y crecimiento.',
                'priority': 'critical'
            })
        
        # Projection-based recommendations
        if projections and 'summary' in projections:
            five_year_growth = projections['summary'].get('total_growth_percentage', 0)
            if five_year_growth < 20:
                recommendations.append({
                    'type': 'growth',
                    'title': 'Acelerar Crecimiento Salarial',
                    'description': f'Proyección de crecimiento a 5 años ({five_year_growth}%) es baja. Considerar un plan para acelerar el crecimiento salarial.',
                    'priority': 'medium'
                })
        
        return recommendations
    
    def validate_input(self, data: Dict) -> tuple:
        """Validate input data for salary analysis."""
        if not data.get('person_id'):
            return False, "Missing required field: person_id"
        return True, ""
    
    def get_default_result(self, error_message: str = "") -> Dict:
        """Return default result when analysis cannot be completed."""
        return {
            'status': 'error',
            'error': error_message or "Could not complete salary analysis",
            'market_data': {},
            'competitiveness': {},
            'satisfaction': {},
            'projections': {},
            'recommendations': []
        }
