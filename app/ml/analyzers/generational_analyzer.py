# /home/pablo/app/ml/analyzers/generational_analyzer.py
"""
Generational Analyzer module for Grupo huntRED® assessment system.

This module analyzes generational characteristics, preferences and work styles
to improve mentoring, team formation and cultural integration.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

import numpy as np
from django.conf import settings
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from app.models import Person, BusinessUnit, EnhancedMLProfile
from app.ats.ml.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class GenerationalAnalyzer(BaseAnalyzer):
    """
    Analyzer for generational trends, preferences and work styles.
    
    Identifies generational characteristics to optimize mentoring matches,
    team formation, and communication strategies.
    """
    
    # Generational cohorts and their birth year ranges
    GENERATIONAL_COHORTS = {
        'BB': {'range': (1946, 1964), 'name': 'Baby Boomers'},
        'X': {'range': (1965, 1980), 'name': 'Generación X'},
        'Y': {'range': (1981, 1996), 'name': 'Millennials'},
        'Z': {'range': (1997, 2012), 'name': 'Generación Z'},
        'Alpha': {'range': (2013, 2025), 'name': 'Generación Alpha'}
    }
    
    # Work preferences by generation (generalized patterns)
    WORK_PREFERENCES = {
        'Baby Boomers': {
            'communication': 'face-to-face, phone calls',
            'feedback': 'formal, scheduled reviews',
            'work_style': 'hierarchical, process-oriented',
            'motivation': 'recognition, position, status',
            'learning': 'structured, instructor-led'
        },
        'Generation X': {
            'communication': 'email, direct conversation',
            'feedback': 'direct, informal, immediate',
            'work_style': 'independent, results-oriented',
            'motivation': 'work-life balance, autonomy',
            'learning': 'self-directed, practical'
        },
        'Millennials': {
            'communication': 'instant messaging, text',
            'feedback': 'frequent, constructive, immediate',
            'work_style': 'collaborative, purpose-driven',
            'motivation': 'purpose, development, impact',
            'learning': 'on-demand, technology-enabled'
        },
        'Generation Z': {
            'communication': 'visual platforms, messaging apps',
            'feedback': 'continuous, digital, personalized',
            'work_style': 'multi-tasking, digital-first',
            'motivation': 'security, flexibility, social impact',
            'learning': 'micro-learning, video, interactive'
        },
        'Generation Alpha': {
            'communication': 'immersive, AI-assisted',
            'feedback': 'real-time, gamified, adaptive',
            'work_style': 'tech-integrated, flexible',
            'motivation': 'innovation, creativity, impact',
            'learning': 'personalized, AI-driven, experiential'
        }
    }
    
    def __init__(self):
        """Initialize the generational analyzer with required models."""
        super().__init__()
        self.cache_duration = timedelta(days=30)  # Generational insights change slowly
        self.cache_timeout = 86400 * 30  # 30 days (in seconds)
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=4, random_state=42)
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for generational analysis."""
        return ['person_id']
        
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analyze generational characteristics and preferences for a person.
        
        Args:
            data: Dictionary containing person_id
            business_unit: Business unit context for analysis
            
        Returns:
            Dict with generational insights and compatibility analysis
        """
        try:
            # Check cache first
            person_id = data.get('person_id')
            cached_result = self.get_cached_result(data, "generational_insights")
            if cached_result:
                return cached_result
                
            # Validate input
            is_valid, error_message = self.validate_input(data)
            if not is_valid:
                logger.warning(f"Invalid input for generational analysis: {error_message}")
                return self.get_default_result(error_message)
                
            # Get person data
            person = self._get_person(person_id)
            if not person:
                return self.get_default_result("Person not found")
                
            # Process person data for generational insights
            result = self.process_person_data(person)
            
            # Cache and return results
            self.set_cached_result(data, result, "generational_insights")
            return result
            
        except Exception as e:
            logger.error(f"Error in generational analysis: {str(e)}", exc_info=True)
            return self.get_default_result(f"Analysis error: {str(e)}")
    
    def _get_person(self, person_id: int) -> Optional[Person]:
        """Get person object from database."""
        try:
            return Person.objects.get(id=person_id)
        except Person.DoesNotExist:
            logger.warning(f"Person with ID {person_id} not found")
            return None
    
    def _get_birth_year(self, person: Person) -> Optional[int]:
        """Extract birth year from person data."""
        if hasattr(person, 'birth_date') and person.birth_date:
            return person.birth_date.year
        
        # Fallback to age if available
        if hasattr(person, 'age') and person.age:
            current_year = datetime.now().year
            return current_year - person.age
            
        # Default to millennial generation if no data available
        logger.warning(f"Birth year not available for person {person.id}, using default")
        return 1990
    
    def _determine_generation(self, birth_year: int) -> str:
        """Determine generation based on birth year."""
        if not birth_year:
            return "Unknown"
            
        for generation, data in self.GENERATIONAL_COHORTS.items():
            start_year, end_year = data['range']
            if start_year <= birth_year <= end_year:
                return generation
                
        return "Unknown"
    
    def _get_generational_preferences(self, generation: str) -> Dict:
        """Get work preferences for the specified generation."""
        return self.WORK_PREFERENCES.get(generation, {})
    
    def _generate_insights(self, generation: str, preferences: Dict, 
                          person: Person, business_unit: Optional[BusinessUnit]) -> Dict:
        """Generate actionable insights based on generational analysis."""
        insights = {
            'communication_strategies': [],
            'mentoring_recommendations': [],
            'team_integration': [],
            'learning_approaches': [],
            'motivation_factors': []
        }
        
        # Communication strategies
        if 'communication' in preferences:
            insights['communication_strategies'] = [
                f"Prefer {preferences.get('communication')} for primary communication",
                f"Adapt messaging style to {generation} preferences",
                "Maintain communication consistency across channels"
            ]
        
        # Mentoring recommendations
        insights['mentoring_recommendations'] = [
            f"Align mentoring style with {generation} learning preferences",
            "Consider generational differences in mentor matching",
            "Address potential generational knowledge gaps"
        ]
        
        # Team integration
        insights['team_integration'] = [
            f"Leverage {generation} strengths in team formation",
            "Create balanced teams across generations",
            "Address potential generational conflict points proactively"
        ]
        
        # Learning approaches
        if 'learning' in preferences:
            insights['learning_approaches'] = [
                f"Optimize for {preferences.get('learning')} learning style",
                "Provide multiple learning pathways",
                "Consider generational differences in technology adoption"
            ]
        
        # Motivation factors
        if 'motivation' in preferences:
            insights['motivation_factors'] = [
                f"Emphasize {preferences.get('motivation')} in engagement",
                "Align incentives with generational preferences",
                "Create personalized motivation strategies"
            ]
            
        return insights
    
    def analyze_team_composition(self, team_members: List[Person]) -> Dict:
        """Analiza la composición generacional de un equipo"""
        if not team_members:
            return self.get_default_result("No team members provided")
            
        generational_distribution = {}
        motivational_patterns = {
            'intrinsic': {'autonomy': 0, 'mastery': 0, 'purpose': 0},
            'extrinsic': {'recognition': 0, 'compensation': 0, 'status': 0}
        }
        
        for member in team_members:
            # Distribución generacional
            generation = self._determine_generation(self._get_birth_year(member))
            if generation:
                generational_distribution[generation] = generational_distribution.get(generation, 0) + 1
            
            # Patrones motivacionales
            motivational = self._get_motivational_profile(member)
            if motivational:
                for category in ['intrinsic', 'extrinsic']:
                    for factor in motivational_patterns[category]:
                        if category in motivational and factor in motivational[category]:
                            motivational_patterns[category][factor] += motivational[category][factor]
        
        # Normalizar patrones motivacionales
        team_size = len(team_members)
        for category in motivational_patterns:
            for factor in motivational_patterns[category]:
                motivational_patterns[category][factor] /= team_size
        
        return {
            'status': 'success',
            'generational_distribution': generational_distribution,
            'motivational_patterns': motivational_patterns,
            'team_size': team_size,
            'recommendations': self.generate_team_recommendations({
                'generational_distribution': generational_distribution,
                'motivational_patterns': motivational_patterns,
                'team_size': team_size
            })
        }
    
    def process_person_data(self, person: Person) -> Dict:
        """Procesa los datos de una persona para análisis generacional"""
        try:
            # Determine generation based on birth date
            birth_year = self._get_birth_year(person)
            generation = self._determine_generation(birth_year)
            
            # Get preferences for the identified generation
            preferences = self._get_generational_preferences(generation)
            
            # Generate insights
            insights = self._generate_insights(generation, preferences, person)
            
            # Obtener perfil motivacional
            motivational_profile = self._get_motivational_profile(person)
            
            # Obtener preferencias de trabajo
            work_preferences = self._get_work_style_preferences(person)
            
            # Combine all data
            result = {
                'status': 'success',
                'person_id': person.id,
                'generation': generation,
                'generation_name': self.GENERATIONAL_COHORTS.get(generation, {}).get('name', 'Unknown'),
                'birth_year': birth_year,
                'preferences': preferences,
                'work_preferences': work_preferences,
                'values': {
                    'career_growth': self._calculate_career_growth_importance(person),
                    'social_impact': self._calculate_social_impact_importance(person),
                    'financial_security': self._calculate_financial_security_importance(person)
                },
                'motivational': motivational_profile,
                'insights': insights,
                'recommendations': self._generate_recommendations(generation, preferences, work_preferences)
            }
            
            # Actualizar perfil ML si existe
            ml_profile = EnhancedMLProfile.objects.filter(user=person).first()
            if ml_profile:
                try:
                    ml_profile.update_generational_insights(result)
                except Exception as e:
                    logger.warning(f"Could not update ML profile: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing person data: {str(e)}", exc_info=True)
            return self.get_default_result(f"Processing error: {str(e)}")
