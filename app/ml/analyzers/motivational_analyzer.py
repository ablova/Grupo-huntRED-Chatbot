# /home/pablo/app/ml/analyzers/motivational_analyzer.py
"""
Motivational Analyzer module for Grupo huntRED® assessment system.

This module analyzes motivational factors, engagement drivers and recognition 
preferences to enhance team performance and individual alignment.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

import numpy as np
from django.conf import settings
from django.core.cache import cache

from app.models import Person, BusinessUnit, EnhancedMLProfile
from app.ats.ml.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class MotivationalAnalyzer(BaseAnalyzer):
    """
    Analyzer for motivational factors and engagement drivers.
    
    Identifies and analyzes motivation patterns to optimize engagement,
    recognition strategies and team alignment.
    """
    
    # Motivation factors definitions
    MOTIVATION_FACTORS = {
        'achievement': {
            'name': 'Logro',
            'description': 'Motivación por alcanzar metas y objetivos'
        },
        'recognition': {
            'name': 'Reconocimiento',
            'description': 'Importancia del reconocimiento y feedback'
        },
        'autonomy': {
            'name': 'Autonomía',
            'description': 'Preferencia por independencia y libertad'
        },
        'purpose': {
            'name': 'Propósito',
            'description': 'Búsqueda de significado en el trabajo'
        },
        'growth': {
            'name': 'Crecimiento',
            'description': 'Deseo de desarrollo y aprendizaje'
        },
        'security': {
            'name': 'Seguridad',
            'description': 'Importancia de la estabilidad'
        },
        'social': {
            'name': 'Social',
            'description': 'Valor de las relaciones laborales'
        }
    }
    
    # Recognition type preferences
    RECOGNITION_TYPES = {
        'public': 'Reconocimiento público ante el equipo o la organización',
        'private': 'Reconocimiento privado entre el supervisor y el individuo',
        'tangible': 'Recompensas materiales como bonos o regalos',
        'verbal': 'Expresiones verbales de aprecio y reconocimiento',
        'written': 'Notas o correos de reconocimiento',
        'development': 'Oportunidades de desarrollo profesional'
    }
    
    def __init__(self):
        """Initialize the motivational analyzer with required configuration."""
        super().__init__()
        self.cache_timeout = 86400  # 24 hours (in seconds)
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for motivational analysis."""
        return ['person_id']
        
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analyze motivational factors and preferences for a person.
        
        Args:
            data: Dictionary containing person_id
            business_unit: Business unit context for analysis
            
        Returns:
            Dict with motivational insights and recommendations
        """
        try:
            # Check cache first
            person_id = data.get('person_id')
            cached_result = self.get_cached_result(data, "motivational_insights")
            if cached_result:
                return cached_result
                
            # Validate input
            is_valid, error_message = self.validate_input(data)
            if not is_valid:
                logger.warning(f"Invalid input for motivational analysis: {error_message}")
                return self.get_default_result(error_message)
                
            # Get person data
            person = self._get_person(person_id)
            if not person:
                return self.get_default_result("Person not found")
                
            # Process person data for motivational insights
            insights = self.process_person_data(person)
            
            # Cache and return results
            self.set_cached_result(data, insights, "motivational_insights")
            return insights
            
        except Exception as e:
            logger.error(f"Error in motivational analysis: {str(e)}", exc_info=True)
            return self.get_default_result(f"Analysis error: {str(e)}")
    
    def process_person_data(self, person: Person) -> Dict:
        """
        Process a person's data to generate motivational insights.
        
        Args:
            person: Person object to analyze
            
        Returns:
            Dict with comprehensive motivational insights
        """
        try:
            # Analyze different motivational dimensions
            motivation_profile = self._analyze_motivation_profile(person)
            engagement_factors = self._analyze_engagement_factors(person)
            recognition_preferences = self._analyze_recognition_preferences(person)
            growth_orientation = self._analyze_growth_orientation(person)
            
            # Combine all insights
            insights = {
                'status': 'success',
                'person_id': person.id,
                'motivation_profile': motivation_profile,
                'engagement_factors': engagement_factors,
                'recognition_preferences': recognition_preferences,
                'growth_orientation': growth_orientation,
                'recommendations': self._generate_recommendations(
                    motivation_profile, 
                    engagement_factors,
                    recognition_preferences
                )
            }
            
            # Update ML profile if available
            ml_profile = EnhancedMLProfile.objects.filter(user=person).first()
            if ml_profile:
                try:
                    ml_profile.update_motivational_insights(insights)
                except Exception as e:
                    logger.warning(f"Could not update ML profile: {str(e)}")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error processing person data: {str(e)}", exc_info=True)
            return self.get_default_result(f"Processing error: {str(e)}")
    
    def _get_person(self, person_id: int) -> Optional[Person]:
        """Get person object from database."""
        try:
            return Person.objects.get(id=person_id)
        except Person.DoesNotExist:
            logger.warning(f"Person with ID {person_id} not found")
            return None
    
    def _analyze_motivation_profile(self, person: Person) -> Dict:
        """
        Analyze the motivation profile of a person.
        
        In a production environment, this would use assessment data,
        chat history, résumé analysis, etc. This implementation uses
        a simulated approach for demonstration.
        """
        # Simulated motivation profile based on deterministic calculation from person ID
        # In a real implementation, this would use actual data
        import hashlib
        
        # Use hash of person ID to ensure consistent results
        seed = int(hashlib.md5(str(person.id).encode()).hexdigest(), 16) % 10000
        np.random.seed(seed)
        
        # Generate normalized scores for each motivation factor
        profile = {}
        for factor in self.MOTIVATION_FACTORS.keys():
            # Generate a score between 0.3 and 0.9
            profile[factor] = round(0.3 + np.random.random() * 0.6, 2)
        
        # Categorize into intrinsic vs. extrinsic motivation
        intrinsic_factors = {'autonomy', 'purpose', 'growth'}
        extrinsic_factors = {'recognition', 'security', 'achievement'}
        social_factors = {'social'}
        
        intrinsic = {k: v for k, v in profile.items() if k in intrinsic_factors}
        extrinsic = {k: v for k, v in profile.items() if k in extrinsic_factors}
        social = {k: v for k, v in profile.items() if k in social_factors}
        
        # Calculate average scores
        avg_intrinsic = sum(intrinsic.values()) / len(intrinsic) if intrinsic else 0
        avg_extrinsic = sum(extrinsic.values()) / len(extrinsic) if extrinsic else 0
        avg_social = sum(social.values()) / len(social) if social else 0
        
        # Determine primary and secondary drivers
        all_factors = sorted(profile.items(), key=lambda x: x[1], reverse=True)
        primary_driver = all_factors[0][0] if all_factors else None
        secondary_driver = all_factors[1][0] if len(all_factors) > 1 else None
        
        return {
            'factors': profile,
            'intrinsic': intrinsic,
            'extrinsic': extrinsic,
            'social': social,
            'avg_intrinsic': avg_intrinsic,
            'avg_extrinsic': avg_extrinsic,
            'avg_social': avg_social,
            'primary_driver': primary_driver,
            'secondary_driver': secondary_driver,
            'motivation_type': 'intrinsic' if avg_intrinsic > avg_extrinsic else 'extrinsic'
        }
    
    def _analyze_engagement_factors(self, person: Person) -> Dict:
        """
        Analyze engagement factors for a person.
        
        This identifies what drives engagement and satisfaction.
        """
        # Simulated engagement analysis
        # In a real implementation, this would use actual assessment data
        import hashlib
        
        seed = int(hashlib.md5(str(person.id + 1).encode()).hexdigest(), 16) % 10000
        np.random.seed(seed)
        
        engagement_factors = {
            'work_content': round(0.4 + np.random.random() * 0.5, 2),
            'team_dynamics': round(0.4 + np.random.random() * 0.5, 2),
            'leadership': round(0.4 + np.random.random() * 0.5, 2),
            'work_environment': round(0.4 + np.random.random() * 0.5, 2),
            'compensation': round(0.4 + np.random.random() * 0.5, 2),
            'career_opportunities': round(0.4 + np.random.random() * 0.5, 2)
        }
        
        # Determine top engagement drivers
        sorted_factors = sorted(engagement_factors.items(), key=lambda x: x[1], reverse=True)
        top_drivers = [factor for factor, _ in sorted_factors[:3]]
        
        return {
            'factors': engagement_factors,
            'top_drivers': top_drivers,
            'engagement_score': sum(engagement_factors.values()) / len(engagement_factors),
            'risk_factors': [factor for factor, score in engagement_factors.items() if score < 0.5]
        }
    
    def _analyze_recognition_preferences(self, person: Person) -> Dict:
        """
        Analyze recognition preferences for a person.
        
        This identifies how the person prefers to be recognized.
        """
        # Simulated recognition preferences
        # In a real implementation, this would use actual assessment data
        import hashlib
        
        seed = int(hashlib.md5(str(person.id + 2).encode()).hexdigest(), 16) % 10000
        np.random.seed(seed)
        
        preferences = {}
        for rec_type in self.RECOGNITION_TYPES.keys():
            preferences[rec_type] = round(0.2 + np.random.random() * 0.7, 2)
        
        # Determine preferred recognition types
        sorted_prefs = sorted(preferences.items(), key=lambda x: x[1], reverse=True)
        primary_preference = sorted_prefs[0][0] if sorted_prefs else None
        secondary_preference = sorted_prefs[1][0] if len(sorted_prefs) > 1 else None
        
        return {
            'preferences': preferences,
            'primary_preference': primary_preference,
            'secondary_preference': secondary_preference,
            'descriptions': {
                'primary': self.RECOGNITION_TYPES.get(primary_preference, ''),
                'secondary': self.RECOGNITION_TYPES.get(secondary_preference, '')
            }
        }
    
    def _analyze_growth_orientation(self, person: Person) -> Dict:
        """
        Analyze growth orientation and learning preferences.
        
        This identifies how the person approaches learning and development.
        """
        # Simulated growth orientation
        # In a real implementation, this would use actual assessment data
        import hashlib
        
        seed = int(hashlib.md5(str(person.id + 3).encode()).hexdigest(), 16) % 10000
        np.random.seed(seed)
        
        learning_styles = {
            'experiential': round(0.3 + np.random.random() * 0.6, 2),
            'conceptual': round(0.3 + np.random.random() * 0.6, 2),
            'social': round(0.3 + np.random.random() * 0.6, 2),
            'practical': round(0.3 + np.random.random() * 0.6, 2)
        }
        
        development_preferences = {
            'formal_education': round(0.3 + np.random.random() * 0.6, 2),
            'on_the_job': round(0.3 + np.random.random() * 0.6, 2),
            'mentoring': round(0.3 + np.random.random() * 0.6, 2),
            'self_directed': round(0.3 + np.random.random() * 0.6, 2),
            'stretch_assignments': round(0.3 + np.random.random() * 0.6, 2)
        }
        
        # Calculate growth mindset score (0.0-1.0)
        growth_mindset = round(0.4 + np.random.random() * 0.5, 2)
        
        return {
            'learning_styles': learning_styles,
            'primary_learning_style': max(learning_styles.items(), key=lambda x: x[1])[0],
            'development_preferences': development_preferences,
            'primary_development_preference': max(development_preferences.items(), key=lambda x: x[1])[0],
            'growth_mindset': growth_mindset,
            'growth_level': 'high' if growth_mindset > 0.7 else 'medium' if growth_mindset > 0.5 else 'low'
        }
    
    def _generate_recommendations(self, motivation_profile: Dict, 
                                 engagement_factors: Dict, 
                                 recognition_preferences: Dict) -> List[Dict]:
        """
        Generate actionable recommendations based on motivational analysis.
        
        Args:
            motivation_profile: Motivation profile results
            engagement_factors: Engagement factors results
            recognition_preferences: Recognition preferences results
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Recommendations based on motivation profile
        primary_driver = motivation_profile.get('primary_driver')
        if primary_driver == 'purpose':
            recommendations.append({
                'type': 'motivation',
                'title': 'Enfatizar Propósito y Misión',
                'description': 'Conectar el trabajo con el propósito organizacional y su impacto',
                'importance': 'high'
            })
        elif primary_driver == 'growth':
            recommendations.append({
                'type': 'motivation',
                'title': 'Oportunidades de Desarrollo',
                'description': 'Proporcionar oportunidades claras de aprendizaje y crecimiento profesional',
                'importance': 'high'
            })
        elif primary_driver == 'autonomy':
            recommendations.append({
                'type': 'motivation',
                'title': 'Aumentar Autonomía',
                'description': 'Ofrecer mayor libertad en la forma de realizar el trabajo y toma de decisiones',
                'importance': 'high'
            })
        
        # Recommendations based on intrinsic vs extrinsic motivation
        if motivation_profile.get('avg_intrinsic', 0) > 0.7:
            recommendations.append({
                'type': 'engagement',
                'title': 'Motivación Intrínseca',
                'description': 'Enfatizar el sentido de propósito y desarrollo personal en vez de incentivos externos',
                'importance': 'medium'
            })
        elif motivation_profile.get('avg_extrinsic', 0) > 0.7:
            recommendations.append({
                'type': 'engagement',
                'title': 'Motivación Extrínseca',
                'description': 'Establecer un sistema claro de reconocimiento y recompensas tangibles',
                'importance': 'medium'
            })
        
        # Recommendations based on recognition preferences
        primary_recognition = recognition_preferences.get('primary_preference')
        if primary_recognition == 'public':
            recommendations.append({
                'type': 'recognition',
                'title': 'Reconocimiento Público',
                'description': 'Reconocer logros en reuniones de equipo o comunicaciones grupales',
                'importance': 'medium'
            })
        elif primary_recognition == 'private':
            recommendations.append({
                'type': 'recognition',
                'title': 'Reconocimiento Privado',
                'description': 'Proporcionar retroalimentación positiva en reuniones uno a uno',
                'importance': 'medium'
            })
        elif primary_recognition == 'development':
            recommendations.append({
                'type': 'recognition',
                'title': 'Oportunidades como Reconocimiento',
                'description': 'Recompensar con nuevas responsabilidades o proyectos de desarrollo',
                'importance': 'medium'
            })
        
        # Recommendations based on engagement factors
        risk_factors = engagement_factors.get('risk_factors', [])
        if 'leadership' in risk_factors:
            recommendations.append({
                'type': 'leadership',
                'title': 'Mejorar Relación con Liderazgo',
                'description': 'Establecer sesiones regulares de feedback con supervisor directo',
                'importance': 'high'
            })
        if 'team_dynamics' in risk_factors:
            recommendations.append({
                'type': 'team',
                'title': 'Fortalecer Dinámica de Equipo',
                'description': 'Promover actividades de team building y clarificar roles',
                'importance': 'high'
            })
        
        return recommendations
