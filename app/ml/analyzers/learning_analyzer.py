# /home/pablo/app/ml/analyzers/learning_analyzer.py
"""
Learning Analyzer module for Grupo huntRED® assessment system.

This module provides personalized learning recommendations based on
skill gaps, career objectives, and learning preferences.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import random

import numpy as np
from django.conf import settings

from app.models import Person, Skill, SkillAssessment
from app.ats.ml.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class LearningAnalyzerImpl(BaseAnalyzer):
    """
    Analyzer for personalized learning recommendations.
    
    Identifies skill gaps and recommends optimal learning resources
    aligned with learning preferences and career goals.
    """
    
    # Resource types for learning recommendations
    RESOURCE_TYPES = [
        "Artículo", "Video", "Curso", "Libro", "Podcast", 
        "Webinar", "Ejercicio práctico", "Mentor", "Comunidad"
    ]
    
    # Learning modes and associated resource types
    LEARNING_MODES = {
        "Teórico": ["Artículo", "Libro", "Podcast"],
        "Práctico": ["Ejercicio práctico", "Proyecto", "Simulación"],
        "Social": ["Mentor", "Comunidad", "Workshop"],
        "Visual": ["Video", "Infografía", "Diagrama"],
        "Auditivo": ["Podcast", "Audiobook", "Webinar"]
    }
    
    # Resource library - this would normally be in a database
    # We define it here as a fallback when LearningResource model is not available
    RESOURCE_LIBRARY = {
        "Liderazgo": [
            {
                "title": "Liderazgo Situacional",
                "type": "Curso",
                "url": "https://www.coursera.org/learn/situational-leadership",
                "duration_hours": 8,
                "level": "Intermedio",
                "popularity_score": 85,
                "effectiveness_score": 88,
                "skills": ["Liderazgo"]
            },
            {
                "title": "Comunicación Efectiva para Líderes",
                "type": "Libro",
                "url": "https://www.amazon.com/comunicacion-efectiva-lideres",
                "duration_hours": 6,
                "level": "Principiante",
                "popularity_score": 75,
                "effectiveness_score": 80,
                "skills": ["Liderazgo", "Comunicación"]
            }
        ],
        "Gestión de Proyectos": [
            {
                "title": "Metodologías Ágiles",
                "type": "Curso",
                "url": "https://www.udemy.com/course/agile-methodologies",
                "duration_hours": 12,
                "level": "Intermedio",
                "popularity_score": 90,
                "effectiveness_score": 85,
                "skills": ["Gestión de Proyectos", "Metodologías Ágiles"]
            },
            {
                "title": "Gestión de Proyectos Complejos",
                "type": "Webinar",
                "url": "https://webinars.projectmanagement.com/complex-projects",
                "duration_hours": 2,
                "level": "Avanzado",
                "popularity_score": 70,
                "effectiveness_score": 75,
                "skills": ["Gestión de Proyectos", "Resolución de Problemas"]
            }
        ],
        "Programación": [
            {
                "title": "Python para Análisis de Datos",
                "type": "Curso",
                "url": "https://www.datacamp.com/courses/python-data-analysis",
                "duration_hours": 20,
                "level": "Intermedio",
                "popularity_score": 95,
                "effectiveness_score": 90,
                "skills": ["Programación", "Python", "Análisis de Datos"]
            },
            {
                "title": "Arquitectura de Software Moderna",
                "type": "Libro",
                "url": "https://www.oreilly.com/modern-software-architecture",
                "duration_hours": 8,
                "level": "Avanzado",
                "popularity_score": 85,
                "effectiveness_score": 80,
                "skills": ["Programación", "Arquitectura de Software"]
            }
        ]
    }
    
    def __init__(self):
        """Initialize the learning analyzer."""
        super().__init__()
        self.resource_cache = {}
        
    def get_required_fields(self) -> List[str]:
        """Get required fields for learning analysis."""
        return ['person_id', 'context']
        
    def analyze(self, data: Dict, business_unit: Optional[Any] = None) -> Dict:
        """
        Generate a personalized learning sequence based on skill gaps and preferences.
        
        Args:
            data: Dictionary containing person_id and optionally skill_gap and context
            business_unit: Business unit context for analysis
            
        Returns:
            Dict with learning sequence recommendations
        """
        try:
            # Check cache first
            person_id = data.get('person_id')
            context = data.get('context', 'job_search')
            cached_result = self.get_cached_result(data, "learning_sequence")
            if cached_result:
                return cached_result
                
            # Validate input
            is_valid, error_message = self.validate_input(data)
            if not is_valid:
                logger.warning(f"Invalid input for learning analysis: {error_message}")
                return self.get_default_result(error_message)
                
            # Get person data
            person_data = self._get_person_data(person_id)
            if not person_data:
                return self.get_default_result("Person not found")
                
            # Identify skill gap if not provided
            skill_gap = data.get('skill_gap')
            if not skill_gap:
                skill_gap = self._identify_skill_gap(person_id, context)
                
            # Get learning preferences
            learning_preferences = self._get_learning_preferences(person_id)
            
            # Filter relevant resources
            relevant_resources = self._filter_relevant_resources(
                skill_gap,
                learning_preferences
            )
            
            # Order by effectiveness and preference
            ordered_resources = self._order_by_effectiveness(
                relevant_resources,
                learning_preferences,
                person_data
            )
            
            # Create sequence with optimal timing
            learning_sequence = []
            for skill_name, gap_info in skill_gap.items():
                # Resources for this skill
                skill_resources = [r for r in ordered_resources if skill_name in r['skills']]
                
                # Limit resources per skill
                max_resources = min(3, len(skill_resources))
                top_resources = skill_resources[:max_resources]
                
                for i, resource in enumerate(top_resources):
                    timing_days = i * 7  # One week between resources
                    
                    # Predict impact of this resource
                    impact = self._predict_impact(resource, gap_info)
                    
                    # Get prerequisites if any
                    prerequisites = self._get_prerequisites(resource, skill_gap)
                    
                    sequence_item = {
                        'resource': resource,
                        'skill': skill_name,
                        'current_level': gap_info['current_level'],
                        'target_level': gap_info['target_level'],
                        'gap': gap_info['gap'],
                        'timing_days': timing_days,
                        'impact': impact,
                        'prerequisites': prerequisites
                    }
                    
                    learning_sequence.append(sequence_item)
            
            # Calculate total duration
            total_duration_days = sum([item['timing_days'] for item in learning_sequence])
            if learning_sequence:
                # Add average duration of resources
                avg_resource_days = sum([item['resource'].get('duration_hours', 0) for item in learning_sequence]) / len(learning_sequence) / 2  # Assuming 2 hours/day
                total_duration_days += avg_resource_days
            
            # Compile result
            result = {
                'person_id': person_id,
                'context': context,
                'skill_gap': skill_gap,
                'learning_preferences': learning_preferences,
                'learning_sequence': learning_sequence,
                'estimated_duration_days': round(total_duration_days),
                'total_resources': len(learning_sequence),
                'business_unit': self.get_business_unit_name(business_unit),
                'analyzed_at': datetime.now().isoformat()
            }
            
            # Cache result
            self.set_cached_result(data, result, "learning_sequence")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in learning analysis: {str(e)}")
            return self.get_default_result(f"Analysis error: {str(e)}")
    
    def _get_person_data(self, person_id: int) -> Dict:
        """
        Get basic person data.
        
        Args:
            person_id: ID of the person
            
        Returns:
            Dict with person data
        """
        try:
            # In a real implementation, this would retrieve person data from the database
            # This is a simplified version
            return {
                'id': person_id,
                'name': f"Person {person_id}",
                'years_experience': 3,
                'current_position': "Analyst",
                'education_level': "Bachelor's",
                'industries': ["Technology", "Finance"]
            }
        except Exception as e:
            logger.error(f"Error getting person data: {str(e)}")
            return {}
    
    def _identify_skill_gap(self, person_id: int, context: str) -> Dict:
        """
        Identify skill gaps for development.
        
        Args:
            person_id: ID of the person
            context: Context for skill gap analysis
            
        Returns:
            Dict with skill gaps and levels
        """
        try:
            # Get current skills
            current_skills = self._get_person_skills(person_id)
            
            # Get target skills based on context
            target_skills = {}
            
            if context == 'job_search':
                # For job search, focus on trending skills
                trending_skills = self._get_trending_skills()
                target_skills = {s['name']: s['level'] for s in trending_skills}
            elif context == 'new_position':
                # For new position, get role-specific skills
                # In a real implementation, this would determine the person's target role
                role = "Project Manager"  # Example
                role_skills = self._get_default_role_skills(role)
                target_skills = {s['name']: s['level'] for s in role_skills}
            else:  # 'development' or other
                # For general development, focus on key skills with higher targets
                target_skills = {s['name']: min(s['level'] + 20, 100) for s in current_skills if s['level'] < 80}
            
            # Calculate gaps
            skill_gap = {}
            current_skill_map = {s['name']: s['level'] for s in current_skills}
            
            for skill_name, target_level in target_skills.items():
                current_level = current_skill_map.get(skill_name, 0)
                if current_level < target_level:
                    skill_gap[skill_name] = {
                        'current_level': current_level,
                        'target_level': target_level,
                        'gap': target_level - current_level
                    }
            
            # Sort by gap size and limit to top 5
            sorted_gap = {k: v for k, v in sorted(
                skill_gap.items(), 
                key=lambda item: item[1]['gap'], 
                reverse=True
            )[:5]}
            
            return sorted_gap
        except Exception as e:
            logger.error(f"Error identifying skill gap: {str(e)}")
            return {}
    
    def _get_person_skills(self, person_id: int) -> List[Dict]:
        """
        Get current skills of the person.
        
        Args:
            person_id: ID of the person
            
        Returns:
            List of skills with levels
        """
        try:
            # In a real implementation, this would retrieve skills from the database
            # This is a simulated version
            skills = [
                {'name': 'Liderazgo', 'level': 60},
                {'name': 'Comunicación', 'level': 75},
                {'name': 'Gestión de Proyectos', 'level': 65},
                {'name': 'Análisis de Datos', 'level': 45},
                {'name': 'Programación', 'level': 40},
                {'name': 'Finanzas', 'level': 30},
                {'name': 'Marketing Digital', 'level': 50}
            ]
            
            # Add some randomness to simulate different profiles
            import random
            random.seed(person_id)
            
            # Adjust levels randomly within ±15%
            for skill in skills:
                adjustment = random.randint(-15, 15)
                skill['level'] = max(0, min(100, skill['level'] + adjustment))
            
            return skills
        except Exception as e:
            logger.error(f"Error getting person skills: {str(e)}")
            return []
    
    def _get_default_role_skills(self, role: str) -> List[Dict]:
        """
        Get relevant skills for a specific role.
        
        Args:
            role: Role title
            
        Returns:
            List of skills with required levels
        """
        # Role-specific skill requirements
        role_skills = {
            "Project Manager": [
                {'name': 'Gestión de Proyectos', 'level': 85},
                {'name': 'Liderazgo', 'level': 80},
                {'name': 'Comunicación', 'level': 85},
                {'name': 'Resolución de Problemas', 'level': 75},
                {'name': 'Planificación Estratégica', 'level': 70}
            ],
            "Data Analyst": [
                {'name': 'Análisis de Datos', 'level': 85},
                {'name': 'Programación', 'level': 75},
                {'name': 'Estadística', 'level': 80},
                {'name': 'Visualización de Datos', 'level': 75},
                {'name': 'SQL', 'level': 80}
            ],
            "Marketing Manager": [
                {'name': 'Marketing Digital', 'level': 85},
                {'name': 'Análisis de Mercado', 'level': 80},
                {'name': 'Comunicación', 'level': 85},
                {'name': 'Gestión de Campañas', 'level': 80},
                {'name': 'SEO/SEM', 'level': 75}
            ]
        }
        
        return role_skills.get(role, [
            {'name': 'Comunicación', 'level': 80},
            {'name': 'Resolución de Problemas', 'level': 75},
            {'name': 'Trabajo en Equipo', 'level': 80}
        ])
    
    def _get_trending_skills(self) -> List[Dict]:
        """
        Get trending skills in the job market.
        
        Returns:
            List of trending skills with required levels
        """
        # In a real implementation, this would retrieve trending skills from analytics
        return [
            {'name': 'Inteligencia Artificial', 'level': 70},
            {'name': 'Machine Learning', 'level': 75},
            {'name': 'Data Science', 'level': 80},
            {'name': 'Cloud Computing', 'level': 70},
            {'name': 'Ciberseguridad', 'level': 75}
        ]
    
    def _get_learning_preferences(self, person_id: int) -> Dict:
        """
        Get learning preferences of the user.
        
        Args:
            person_id: ID of the person
            
        Returns:
            Dict with learning preferences
        """
        try:
            # In a real implementation, this would retrieve preferences from user profile
            # This is a simplified version
            
            # Use person_id to create deterministic preferences for testing
            random.seed(person_id)
            
            # Select preferred modes
            all_modes = list(self.LEARNING_MODES.keys())
            num_preferred_modes = min(3, len(all_modes))
            preferred_modes = random.sample(all_modes, num_preferred_modes)
            
            # Determine preferred resource types based on modes
            preferred_types = []
            for mode in preferred_modes:
                preferred_types.extend(self.LEARNING_MODES[mode][:2])  # Take top 2 types
            
            # Remove duplicates
            preferred_types = list(set(preferred_types))
            
            # Time preferences
            available_hours_per_week = random.randint(3, 15)
            max_duration_per_session = random.randint(1, 3)
            
            # Learning level preference biases toward current experience
            person_data = self._get_person_data(person_id)
            years_exp = person_data.get('years_experience', 3)
            
            if years_exp < 2:
                preferred_level = "Principiante"
            elif 2 <= years_exp <= 5:
                preferred_level = "Intermedio"
            else:
                preferred_level = "Avanzado"
            
            # Other preferences
            preferences = {
                'preferred_modes': preferred_modes,
                'preferred_resource_types': preferred_types,
                'available_hours_per_week': available_hours_per_week,
                'max_duration_per_session': max_duration_per_session,
                'preferred_level': preferred_level,
                'language_preference': 'Español',
                'certifications_important': random.choice([True, False]),
                'learn_with_others': random.choice([True, False]),
                'weekend_learning': random.choice([True, False])
            }
            
            return preferences
        except Exception as e:
            logger.error(f"Error getting learning preferences: {str(e)}")
            return {
                'preferred_modes': ['Práctico', 'Visual'],
                'preferred_resource_types': ['Video', 'Curso', 'Ejercicio práctico'],
                'available_hours_per_week': 5,
                'max_duration_per_session': 1
            }
    
    def _filter_relevant_resources(self, skill_gap: Dict, preferences: Dict) -> List[Dict]:
        """
        Filter relevant resources for target skills.
        
        Args:
            skill_gap: Dictionary of skills to develop and target levels
            preferences: Learning preferences
            
        Returns:
            List of relevant resources
        """
        try:
            # In a real implementation, this would query the LearningResource model
            # Since we don't have it, we'll use our mock library
            
            all_resources = []
            
            # Get resources for each skill in the gap
            for skill_name in skill_gap.keys():
                # Check if we have resources for this skill
                if skill_name in self.RESOURCE_LIBRARY:
                    all_resources.extend(self.RESOURCE_LIBRARY[skill_name])
                else:
                    # Generate mock resources for skills not in our library
                    mock_resources = self._generate_mock_resources(skill_name)
                    all_resources.extend(mock_resources)
            
            # Filter based on preferences
            filtered_resources = []
            
            for resource in all_resources:
                # Keep if matches preferred types or no preferences specified
                if not preferences.get('preferred_resource_types') or \
                   resource['type'] in preferences.get('preferred_resource_types', []):
                    filtered_resources.append(resource)
                    continue
                
                # Also keep high-effectiveness resources regardless of type
                if resource.get('effectiveness_score', 0) >= 85:
                    filtered_resources.append(resource)
                    continue
            
            return filtered_resources
        except Exception as e:
            logger.error(f"Error filtering resources: {str(e)}")
            return []
    
    def _generate_mock_resources(self, skill_name: str) -> List[Dict]:
        """
        Generate mock resources for a skill.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            List of mock resources
        """
        # Cache results for performance
        if skill_name in self.resource_cache:
            return self.resource_cache[skill_name]
        
        resources = []
        
        # Generate resources of different types and levels
        for level in ["Principiante", "Intermedio", "Avanzado"]:
            # Create a course
            course = {
                "title": f"{skill_name} {level}",
                "type": "Curso",
                "url": f"https://www.example.com/courses/{skill_name.lower().replace(' ', '-')}-{level.lower()}",
                "duration_hours": 8 if level == "Principiante" else (12 if level == "Intermedio" else 16),
                "level": level,
                "popularity_score": random.randint(70, 95),
                "effectiveness_score": random.randint(75, 90),
                "skills": [skill_name]
            }
            resources.append(course)
            
            # Create a video
            video = {
                "title": f"Tutorial de {skill_name}",
                "type": "Video",
                "url": f"https://www.example.com/videos/{skill_name.lower().replace(' ', '-')}-tutorial",
                "duration_hours": 1 if level == "Principiante" else (2 if level == "Intermedio" else 3),
                "level": level,
                "popularity_score": random.randint(75, 90),
                "effectiveness_score": random.randint(70, 85),
                "skills": [skill_name]
            }
            resources.append(video)
            
            # Create an article
            article = {
                "title": f"Guía de {skill_name}",
                "type": "Artículo",
                "url": f"https://www.example.com/articles/{skill_name.lower().replace(' ', '-')}-guide",
                "duration_hours": 0.5,
                "level": level,
                "popularity_score": random.randint(65, 85),
                "effectiveness_score": random.randint(60, 80),
                "skills": [skill_name]
            }
            resources.append(article)
        
        # Cache for future use
        self.resource_cache[skill_name] = resources
        
        return resources
    
    def _order_by_effectiveness(self, resources: List[Dict], preferences: Dict, person_data: Dict) -> List[Dict]:
        """
        Order resources by effectiveness and fit to preferences.
        
        Args:
            resources: List of resources
            preferences: Learning preferences
            person_data: Person data
            
        Returns:
            Ordered list of resources
        """
        # Calculate fit score for each resource
        for resource in resources:
            # Base: effectiveness_score
            score = resource.get('effectiveness_score', 70)
            
            # Adjust by preferred resource type
            if resource['type'] in preferences.get('preferred_resource_types', []):
                score += 10
            
            # Adjust by experience level
            years_exp = person_data.get('years_experience', 3)
            if (years_exp < 2 and resource['level'] == 'Principiante') or \
               (2 <= years_exp <= 5 and resource['level'] == 'Intermedio') or \
               (years_exp > 5 and resource['level'] == 'Avanzado'):
                score += 5
            
            # Adjust by popularity (minor effect)
            score += min(5, resource.get('popularity_score', 0) / 20)
            
            # Save score in resource
            resource['fit_score'] = min(100, score)
        
        # Sort by fit score
        return sorted(resources, key=lambda x: x.get('fit_score', 0), reverse=True)
    
    def _predict_impact(self, resource: Dict, gap_info: Dict) -> Dict:
        """
        Predict the impact of a resource on closing the skill gap.
        
        Args:
            resource: Resource info
            gap_info: Gap information
            
        Returns:
            Impact prediction
        """
        # Calculate base impact by effectiveness and type
        effectiveness = resource.get('effectiveness_score', 70) / 100
        
        # Factors by type (some types have more impact on learning)
        type_factors = {
            'Curso': 1.0,
            'Ejercicio práctico': 0.9,
            'Mentor': 0.9,
            'Proyecto': 0.8,
            'Video': 0.7,
            'Libro': 0.7,
            'Webinar': 0.6,
            'Artículo': 0.5,
            'Podcast': 0.5,
            'Infografía': 0.3
        }
        
        type_factor = type_factors.get(resource['type'], 0.6)
        
        # Estimate improvement points (out of 100)
        max_improvement = 15  # Maximum for a single resource
        improvement_points = effectiveness * type_factor * max_improvement
        
        # Estimate new level after resource
        current_level = gap_info['current_level']
        new_level = min(100, current_level + improvement_points)
        
        # Calculate gap closure percentage
        gap = gap_info['gap']
        gap_closed_percent = (improvement_points / gap) * 100 if gap > 0 else 100
        
        return {
            'improvement_points': round(improvement_points, 1),
            'expected_new_level': round(new_level, 1),
            'gap_closed_percent': min(100, round(gap_closed_percent, 1))
        }
    
    def _get_prerequisites(self, resource: Dict, skill_gap: Dict) -> List[str]:
        """
        Determine prerequisites for a resource if they exist.
        
        Args:
            resource: Resource info
            skill_gap: Skill gap information
            
        Returns:
            List of prerequisite skills
        """
        # Simplified - in a real system this would analyze dependencies between skills
        level = resource.get('level', 'Intermedio')
        
        # Advanced resources may need a certain level in other skills
        if level == 'Avanzado' and len(skill_gap) > 1:
            # Randomly select other skills as prerequisite
            skills = list(skill_gap.keys())
            main_skill = resource['skills'][0]
            other_skills = [s for s in skills if s != main_skill]
            
            if other_skills:
                # 50% chance of having prerequisite
                if random.random() > 0.5:
                    return random.sample(other_skills, min(1, len(other_skills)))
        
        return []
    
    def get_default_result(self, error_message: str = None) -> Dict:
        """
        Get default learning sequence result.
        
        Args:
            error_message: Optional error message
            
        Returns:
            Default result
        """
        return {
            'person_id': None,
            'skill_gap': {},
            'learning_sequence': [],
            'estimated_duration_days': 0,
            'total_resources': 0,
            'error': error_message,
            'analyzed_at': datetime.now().isoformat()
        }
