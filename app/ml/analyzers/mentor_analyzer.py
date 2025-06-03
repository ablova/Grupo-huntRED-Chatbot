# /home/pablo/app/ml/analyzers/mentor_analyzer.py
"""
Mentor Analyzer module for Grupo huntRED® assessment system.

This module analyzes and matches candidates with optimal mentors
based on multiple factors including experience, skills, and compatibility.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import random

import numpy as np
from django.conf import settings

from app.models import Person, Skill, SkillAssessment, BusinessUnit, Mentor, MentorSkill, MentorSession
from app.ats.ml.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class MentorAnalyzerImpl(BaseAnalyzer):
    """
    Analyzer for mentor matching and compatibility assessment.
    
    Integrates multiple factors to determine optimal compatibility
    between mentors and mentees.
    """
    
    # Compatibility factors and weights
    COMPATIBILITY_FACTORS = {
        'career_alignment': 0.30,
        'skill_match': 0.25,
        'personality_compatibility': 0.20,
        'industry_experience': 0.15,
        'mentoring_style': 0.10
    }
    
    # Mentoring types
    MENTORING_TYPES = [
        "Carrera", "Habilidades técnicas", "Liderazgo", 
        "Emprendimiento", "Equilibrio vida-trabajo", "Networking"
    ]
    
    def __init__(self):
        """Initialize the mentor analyzer with required models."""
        super().__init__()
        self.mock_mentors_cache = {}
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for mentor analysis."""
        return ['person_id']
        
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Find optimal mentors for a candidate based on multiple compatibility factors.
        
        Args:
            data: Dictionary containing person_id and optionally goal
            business_unit: Business unit context for analysis
            
        Returns:
            Dict with recommended mentors and compatibility analysis
        """
        try:
            # Check cache first
            person_id = data.get('person_id')
            cached_result = self.get_cached_result(data, "mentor_matches")
            if cached_result:
                return cached_result
                
            # Validate input
            is_valid, error_message = self.validate_input(data)
            if not is_valid:
                logger.warning(f"Invalid input for mentor matching: {error_message}")
                return self.get_default_result(error_message)
                
            # Get person data
            person_data = self._get_person_data(person_id)
            if not person_data:
                return self.get_default_result("Person not found")
                
            # Get matching goal
            goal = data.get('goal')
            if not goal:
                goal = self._determine_mentoring_goal(person_id, person_data)
                
            # Get business unit name
            bu_name = self.get_business_unit_name(business_unit)
            
            # Get available mentors
            mentoring_type = data.get('mentoring_type')
            limit = data.get('limit', 5)
            available_mentors = self._get_available_mentors(bu_name)
            
            # Filter by mentoring type if specified
            if mentoring_type:
                available_mentors = [
                    m for m in available_mentors 
                    if mentoring_type in m.get('mentoring_types', [])
                ]
            
            # Analyze compatibility for each mentor
            matches = []
            for mentor in available_mentors:
                compatibility = self._analyze_compatibility(
                    person_data, 
                    mentor,
                    goal
                )
                
                # Generate compatibility reasons
                reasons = self._generate_compatibility_reasons(
                    person_data,
                    mentor,
                    goal,
                    compatibility['factors']
                )
                
                matches.append({
                    'mentor': mentor,
                    'match_score': compatibility['overall_score'],
                    'factors': compatibility['factors'],
                    'reasons': reasons
                })
                
            # Sort by match score
            sorted_matches = sorted(
                matches,
                key=lambda x: x['match_score'],
                reverse=True
            )
            
            # Limit number of results
            limited_matches = sorted_matches[:limit]
            
            # Prepare final result
            result = {
                'person_id': person_id,
                'goal': goal,
                'business_unit': bu_name,
                'mentoring_type': mentoring_type,
                'matches': limited_matches,
                'total_matches': len(limited_matches),
                'analyzed_at': datetime.now().isoformat()
            }
            
            # Cache result
            self.set_cached_result(data, result, "mentor_matches")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in mentor matching: {str(e)}")
            return self.get_default_result(f"Analysis error: {str(e)}")
    
    def _get_person_data(self, person_id: int) -> Dict:
        """
        Get relevant candidate data for matching.
        
        Args:
            person_id: ID of the person
            
        Returns:
            Dict with person data
        """
        try:
            # In a real implementation, this would retrieve person data from the database
            # This is a simplified version
            personality_types = ["Analítico", "Expresivo", "Afable", "Directivo"]
            industries = ["Tecnología", "Finanzas", "Salud", "Educación", "Manufactura"]
            
            # Use person_id to create deterministic data for testing
            random.seed(person_id)
            
            return {
                'id': person_id,
                'name': f"Person {person_id}",
                'years_experience': random.randint(1, 20),
                'current_position': "Senior Manager" if random.random() > 0.7 else "Analyst",
                'industry': random.choice(industries),
                'skills': self._generate_mock_skills(5, person_id),
                'personality': {
                    'type': random.choice(personality_types),
                    'work_style': random.choice(["Colaborativo", "Independiente", "Estructurado", "Flexible"]),
                    'communication': random.choice(["Directo", "Indirecto", "Formal", "Informal"])
                },
                'values': {
                    'primary': random.choice(["Logro", "Autonomía", "Seguridad", "Creatividad"]),
                    'secondary': random.choice(["Reconocimiento", "Equilibrio", "Servicio", "Desafío"])
                },
                'learning_style': random.choice(["Visual", "Auditivo", "Kinestésico"]),
                'goals': {
                    'short_term': "Mejorar habilidades de liderazgo",
                    'long_term': "Avanzar a posición directiva"
                }
            }
        except Exception as e:
            logger.error(f"Error getting person data: {str(e)}")
            return {}
    
    def _determine_mentoring_goal(self, person_id: int, person_data: Dict) -> str:
        """
        Determine the most appropriate mentoring goal.
        
        Args:
            person_id: ID of the person
            person_data: Person data
            
        Returns:
            Mentoring goal
        """
        # Default goals based on experience level
        years_exp = person_data.get('years_experience', 0)
        
        if years_exp < 3:
            return "Desarrollo de habilidades técnicas"
        elif 3 <= years_exp < 7:
            return "Desarrollo de liderazgo"
        elif 7 <= years_exp < 12:
            return "Crecimiento ejecutivo"
        else:
            return "Mentoría estratégica"
    
    def _get_available_mentors(self, business_unit: Optional[str] = None) -> List[Dict]:
        """
        Get available mentors, optionally filtered by business unit.
        
        Args:
            business_unit: Business unit name
            
        Returns:
            List of available mentors
        """
        # Cache key for this business unit
        cache_key = f"mentors_{business_unit}" if business_unit else "mentors_all"
        
        # Check cache
        if cache_key in self.mock_mentors_cache:
            return self.mock_mentors_cache[cache_key]
        
        # Query real mentors from database
        mentor_query = Mentor.objects.filter(is_active=True)
        
        # Filter by business unit if specified
        if business_unit:
            try:
                bu = BusinessUnit.objects.get(name=business_unit)
                # Filter mentors by business unit via company
                mentor_query = mentor_query.filter(company__business_unit=bu)
            except BusinessUnit.DoesNotExist:
                logger.warning(f"Business unit not found: {business_unit}")
        
        # Convert mentors to dictionaries
        mentors = []
        for mentor in mentor_query:
            mentor_dict = mentor.to_dict()
            
            # Get mentor skills
            skills = MentorSkill.objects.filter(mentor=mentor)
            mentor_dict['skills'] = [skill.to_dict() for skill in skills]
            
            # Get person industry and position for compatibility matching
            try:
                if mentor.person:
                    person = mentor.person
                    mentor_dict['industry'] = getattr(person, 'industry', '')
                    mentor_dict['position'] = getattr(person, 'position', '')
            except Exception as e:
                logger.error(f"Error getting mentor person data: {e}")
            
            mentors.append(mentor_dict)
        
        # If no real mentors found, fallback to mock data for development
        if not mentors and settings.DEBUG:
            logger.warning("No real mentors found, using mock data")
            mentors = self._generate_mock_mentors(business_unit)
        
        # Cache for future use
        self.mock_mentors_cache[cache_key] = mentors
        
        return mentors
    
    def _generate_mock_mentors(self, business_unit: Optional[str] = None) -> List[Dict]:
        """
        Generate mock mentors for demonstration.
        
        Args:
            business_unit: Business unit name
            
        Returns:
            List of mock mentors
        """
        # Constants for mentor generation
        personality_types = ["Analítico", "Expresivo", "Afable", "Directivo"]
        industries = ["Tecnología", "Finanzas", "Salud", "Educación", "Manufactura"]
        positions = ["Director", "VP", "CTO", "CFO", "COO", "Senior Manager"]
        expertise_areas = [
            "Liderazgo", "Gestión de Proyectos", "Desarrollo de Producto",
            "Estrategia", "Innovación", "Marketing", "Ventas", "Finanzas",
            "Recursos Humanos", "Tecnología", "Operaciones"
        ]
        companies = [
            "Tech Innovations", "Global Finance", "Healthcare Solutions",
            "EduTech", "Manufacturing Plus", "Creative Agency",
            "Consulting Group", "Retail Solutions"
        ]
        
        # Ensure deterministic generation
        random.seed(42)
        
        mentors = []
        for i in range(20):  # Generate 20 mock mentors
            mentor_id = i + 1
            
            # Filter by business unit if specified
            if business_unit:
                mentor_bu = business_unit
            else:
                mentor_bu = random.choice(["huntRED", "huntU", "Amigro"])
                
            if business_unit and mentor_bu != business_unit and random.random() < 0.7:
                continue  # Skip this mentor if BU doesn't match (70% probability)
            
            # Generate mentor skills
            mentor_skills = self._generate_mock_skills(7, mentor_id + 100)
            
            # Select random expertise areas
            num_expertise = random.randint(2, 4)
            mentor_expertise = random.sample(expertise_areas, num_expertise)
            
            # Select random mentoring types
            num_types = random.randint(1, 3)
            mentor_types = random.sample(self.MENTORING_TYPES, num_types)
            
            # Create mentor
            mentor = {
                'id': mentor_id,
                'name': f"Mentor {mentor_id}",
                'position': random.choice(positions),
                'company': random.choice(companies),
                'industry': random.choice(industries),
                'years_experience': random.randint(10, 30),
                'business_unit': mentor_bu,
                'rating': round(random.uniform(3.5, 5.0), 1),
                'availability': f"{random.randint(2, 10)} horas/mes",
                'expertise_areas': mentor_expertise,
                'mentoring_types': mentor_types,
                'skills': mentor_skills,
                'personality_type': random.choice(personality_types),
                'teaching_style': random.choice(["Práctico", "Teórico", "Reflexivo", "Desafiante"]),
                'communication_style': random.choice(["Directo", "Indirecto", "Formal", "Informal"]),
                'previous_mentees': random.randint(0, 15),
                'work_style': random.choice(["Colaborativo", "Independiente", "Estructurado", "Flexible"]),
                'bio': f"Profesional con {random.randint(10, 30)} años de experiencia en {random.choice(industries)}.",
                'achievements': [
                    f"Liderazgo en {random.choice(expertise_areas)}",
                    f"Desarrollo de {random.choice(['estrategias', 'productos', 'equipos', 'procesos'])}"
                ]
            }
            
            mentors.append(mentor)
        
        return mentors
    
    def _generate_mock_skills(self, num_skills: int, seed: int) -> List[Dict]:
        """
        Generate mock skills for demonstration.
        
        Args:
            num_skills: Number of skills to generate
            seed: Random seed for deterministic generation
            
        Returns:
            List of mock skills
        """
        random.seed(seed)
        
        all_skills = [
            "Liderazgo", "Comunicación", "Gestión de Proyectos", "Análisis de Datos",
            "Programación", "Diseño UX", "Marketing Digital", "Ventas", "Negociación",
            "Finanzas", "Recursos Humanos", "Estrategia", "Innovación", "Trabajo en Equipo",
            "Resolución de Problemas", "Pensamiento Crítico", "Gestión del Tiempo",
            "Presentaciones", "Redes Sociales", "SEO", "Cloud Computing", "Machine Learning",
            "Business Intelligence", "Gestión de Cambio", "Coaching", "Mentoría"
        ]
        
        # Select random skills
        selected_skills = random.sample(all_skills, min(num_skills, len(all_skills)))
        
        # Create skill objects
        skills = []
        for skill in selected_skills:
            level = random.randint(70, 100)  # Mentors have high skill levels
            skills.append({
                'name': skill,
                'level': level,
                'years': random.randint(1, 10)
            })
        
        return skills
    
    def _analyze_compatibility(self, person_data: Dict, mentor: Dict, goal: str) -> Dict:
        """
        Analyze multifactorial compatibility between candidate and mentor.
        
        Args:
            person_data: Person data
            mentor: Mentor data
            goal: Mentoring goal
            
        Returns:
            Dict with compatibility analysis
        """
        # Calculate individual factors
        factors = {}
        
        # Career alignment
        factors['career_alignment'] = self._calculate_career_alignment(
            person_data.get('current_position', ''),
            mentor.get('position', ''),
            person_data.get('goals', {}),
            mentor.get('expertise_areas', [])
        )
        
        # Skill match
        factors['skill_match'] = self._calculate_skill_match(
            person_data.get('skills', []),
            mentor.get('skills', [])
        )
        
        # Personality compatibility
        factors['personality_compatibility'] = self._calculate_personality_compatibility(
            person_data.get('personality', {}).get('type', ''),
            mentor.get('personality_type', ''),
            person_data.get('values', {}),
            mentor.get('teaching_style', '')
        )
        
        # Experience match
        factors['experience_match'] = self._calculate_experience_match(
            person_data.get('years_experience', 0),
            mentor.get('years_experience', 0),
            person_data.get('industry', ''),
            mentor.get('industry', '')
        )
        
        # Mentoring style match
        factors['mentoring_style'] = self._calculate_mentoring_style_match(
            goal,
            mentor.get('mentoring_types', []),
            person_data.get('learning_style', ''),
            mentor.get('teaching_style', '')
        )
        
        # Get dynamic weights based on context
        weights = self._get_dynamic_weights(person_data, mentor, goal)
        
        # Calculate overall score
        overall_score = sum(factors[factor] * weights.get(factor, 0) for factor in factors)
        
        return {
            'overall_score': round(overall_score, 1),
            'factors': {k: round(v, 1) for k, v in factors.items()},
            'weights': {k: round(v, 2) for k, v in weights.items()}
        }
    
    def _calculate_career_alignment(self, person_position: str, mentor_position: str, 
                                 person_goals: Dict, mentor_expertise: List[str]) -> float:
        """
        Calculate alignment between candidate trajectory and mentor experience.
        
        Args:
            person_position: Current position of the person
            mentor_position: Position of the mentor
            person_goals: Career goals of the person
            mentor_expertise: Expertise areas of the mentor
            
        Returns:
            Career alignment score (0-100)
        """
        score = 50  # Base score
        
        # Position progression
        position_levels = {
            "Intern": 1,
            "Assistant": 2,
            "Analyst": 3,
            "Senior Analyst": 4,
            "Manager": 5,
            "Senior Manager": 6,
            "Director": 7,
            "VP": 8,
            "CXO": 9
        }
        
        # Get position levels
        person_level = 3  # Default: Analyst
        mentor_level = 7  # Default: Director
        
        for position, level in position_levels.items():
            if position.lower() in person_position.lower():
                person_level = level
            if position.lower() in mentor_position.lower():
                mentor_level = level
        
        # Check if mentor is 2-4 levels above mentee (ideal)
        level_diff = mentor_level - person_level
        if 2 <= level_diff <= 4:
            score += 25
        elif level_diff > 0:
            score += 15
        
        # Check if mentor's expertise aligns with mentee's goals
        if person_goals:
            short_term = person_goals.get('short_term', '').lower()
            long_term = person_goals.get('long_term', '').lower()
            
            for expertise in mentor_expertise:
                if expertise.lower() in short_term or expertise.lower() in long_term:
                    score += 25
                    break
        
        return min(100, score)
    
    def _calculate_skill_match(self, person_skills: List[Dict], mentor_skills: List[Dict]) -> float:
        """
        Calculate skill match between candidate and mentor.
        
        Args:
            person_skills: Skills of the person
            mentor_skills: Skills of the mentor
            
        Returns:
            Skill match score (0-100)
        """
        if not person_skills or not mentor_skills:
            return 50  # Base score if no skills
        
        # Create maps of skills by name
        person_skill_map = {s['name'].lower(): s for s in person_skills}
        mentor_skill_map = {s['name'].lower(): s for s in mentor_skills}
        
        # Count matching skills
        matching_skills = 0
        total_skills = len(person_skills)
        
        for skill_name, skill_data in person_skill_map.items():
            if skill_name in mentor_skill_map:
                # Mentor has this skill
                mentor_skill = mentor_skill_map[skill_name]
                
                # Check if mentor's level is higher
                if mentor_skill.get('level', 0) > skill_data.get('level', 0):
                    matching_skills += 1
        
        # Calculate match percentage
        if total_skills == 0:
            return 50
        
        match_percentage = (matching_skills / total_skills) * 100
        
        # Adjust score: 50% base + match percentage
        score = 50 + (match_percentage / 2)
        
        return min(100, score)
    
    def _calculate_personality_compatibility(self, person_type: str, mentor_type: str,
                                          person_values: Dict, mentor_teaching_style: str) -> float:
        """
        Calculate personality and values compatibility.
        
        Args:
            person_type: Personality type of the person
            mentor_type: Personality type of the mentor
            person_values: Values of the person
            mentor_teaching_style: Teaching style of the mentor
            
        Returns:
            Personality compatibility score (0-100)
        """
        score = 70  # Base score - personality compatibility is generally good
        
        # Complementary personality types
        complementary_types = {
            "Analítico": ["Expresivo", "Directivo"],
            "Expresivo": ["Analítico", "Afable"],
            "Afable": ["Expresivo", "Directivo"],
            "Directivo": ["Analítico", "Afable"]
        }
        
        # Check if personality types are complementary
        if mentor_type in complementary_types.get(person_type, []):
            score += 15
        elif mentor_type == person_type:
            score += 5  # Small bonus for same type
        
        # Check if teaching style matches values
        if person_values:
            primary_value = person_values.get('primary', '').lower()
            
            # Match teaching style to values
            if primary_value == "logro" and mentor_teaching_style == "Desafiante":
                score += 15
            elif primary_value == "autonomía" and mentor_teaching_style == "Práctico":
                score += 15
            elif primary_value == "seguridad" and mentor_teaching_style == "Teórico":
                score += 15
            elif primary_value == "creatividad" and mentor_teaching_style == "Reflexivo":
                score += 15
        
        return min(100, score)
    
    def _calculate_experience_match(self, person_years: int, mentor_years: int,
                                 person_industry: str, mentor_industry: str) -> float:
        """
        Calculate match between candidate and mentor experience.
        
        Args:
            person_years: Years of experience of the person
            mentor_years: Years of experience of the mentor
            person_industry: Industry of the person
            mentor_industry: Industry of the mentor
            
        Returns:
            Experience match score (0-100)
        """
        score = 50  # Base score
        
        # Check years difference (ideal: mentor has 5-15 years more experience)
        years_diff = mentor_years - person_years
        if 5 <= years_diff <= 15:
            score += 25
        elif years_diff > 0:
            score += 15
        
        # Check industry match
        if person_industry.lower() == mentor_industry.lower():
            score += 25
        
        return min(100, score)
    
    def _calculate_mentoring_style_match(self, goal: str, mentoring_types: List[str],
                                      person_learning_style: str, mentor_teaching_style: str) -> float:
        """
        Calculate match between goal and mentoring types.
        
        Args:
            goal: Mentoring goal
            mentoring_types: Mentoring types of the mentor
            person_learning_style: Learning style of the person
            mentor_teaching_style: Teaching style of the mentor
            
        Returns:
            Mentoring style match score (0-100)
        """
        score = 60  # Base score
        
        # Check if mentoring types align with goal
        goal_lower = goal.lower()
        
        for mentoring_type in mentoring_types:
            if mentoring_type.lower() in goal_lower:
                score += 20
                break
            elif "desarrollo" in goal_lower and "habilidades" in mentoring_type.lower():
                score += 15
                break
            elif "liderazgo" in goal_lower and "liderazgo" in mentoring_type.lower():
                score += 20
                break
        
        # Check if teaching style matches learning style
        learning_teaching_match = {
            "Visual": ["Práctico", "Reflexivo"],
            "Auditivo": ["Teórico", "Reflexivo"],
            "Kinestésico": ["Práctico", "Desafiante"]
        }
        
        if mentor_teaching_style in learning_teaching_match.get(person_learning_style, []):
            score += 20
        
        return min(100, score)
    
    def _get_dynamic_weights(self, person_data: Dict, mentor: Dict, goal: str) -> Dict:
        """
        Get dynamic weights based on context and goals.
        
        Args:
            person_data: Person data
            mentor: Mentor data
            goal: Mentoring goal
            
        Returns:
            Dict with dynamic weights
        """
        # Start with base weights
        base_weights = self.COMPATIBILITY_FACTORS.copy()
        
        # Adjust weights based on goal
        if 'carrera' in goal.lower():
            base_weights['career_alignment'] += 0.05
            base_weights['skill_match'] -= 0.05
        elif 'habilidades' in goal.lower():
            base_weights['skill_match'] += 0.05
            base_weights['career_alignment'] -= 0.05
        elif 'liderazgo' in goal.lower():
            base_weights['personality_compatibility'] += 0.05
            base_weights['mentoring_style'] -= 0.05
            
        # Adjust weights based on mentor experience
        if mentor.get('years_experience', 0) > 15:
            base_weights['experience_match'] += 0.05
            base_weights['skill_match'] -= 0.05
            
        # Normalize weights
        total = sum(base_weights.values())
        return {k: v/total for k, v in base_weights.items()}
    
    def _generate_compatibility_reasons(self, person_data: Dict, mentor: Dict, 
                                      goal: str, factors: Dict) -> List[str]:
        """
        Generate compatibility reasons to explain the match.
        
        Args:
            person_data: Person data
            mentor: Mentor data
            goal: Mentoring goal
            factors: Compatibility factors
            
        Returns:
            List of compatibility reasons
        """
        reasons = []
        
        # Sort factors from highest to lowest
        sorted_factors = sorted(
            factors.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Generate reasons for top factors
        for factor_name, score in sorted_factors[:3]:
            if score < 60:
                continue  # Don't mention low factors
                
            if factor_name == 'career_alignment' and score > 70:
                if 'position' in mentor:
                    reasons.append(f"Trayectoria alineada con la posición de {mentor['position']}")
                if 'expertise_areas' in mentor:
                    reasons.append(f"Experiencia en {', '.join(mentor['expertise_areas'][:2])}")
                    
            elif factor_name == 'skill_match' and score > 70:
                if 'skills' in mentor:
                    skill_names = [s['name'] for s in mentor['skills'][:2]]
                    reasons.append(f"Dominio en habilidades clave: {', '.join(skill_names)}")
                    
            elif factor_name == 'personality_compatibility' and score > 70:
                if 'personality_type' in mentor:
                    person_type = person_data.get('personality', {}).get('type', 'Equilibrado')
                    reasons.append(f"Compatibilidad entre {person_type} y {mentor['personality_type']}")
                    
            elif factor_name == 'experience_match' and score > 70:
                if 'years_experience' in mentor and 'industry' in mentor:
                    reasons.append(f"{mentor['years_experience']} años en {mentor['industry']}")
                    
            elif factor_name == 'mentoring_style' and score > 70:
                if 'mentoring_types' in mentor:
                    reasons.append(f"Especializado en {', '.join(mentor['mentoring_types'][:2])}")
        
        # Add additional specific reasons
        if mentor.get('rating', 0) >= 4.5:
            reasons.append(f"Alta calificación de {mentor['rating']}/5.0")
            
        if goal in str(mentor.get('expertise_areas', [])):
            reasons.append(f"Especialista en {goal}")
            
        if person_data.get('industry') == mentor.get('industry'):
            reasons.append("Misma industria")
            
        # Limit to 3 reasons
        return reasons[:3]
    
    def get_default_result(self, error_message: str = None) -> Dict:
        """
        Get default mentor matching result.
        
        Args:
            error_message: Optional error message
            
        Returns:
            Default matching result
        """
        return {
            'person_id': None,
            'goal': "Desarrollo profesional general",
            'matches': [],
            'total_matches': 0,
            'error': error_message,
            'analyzed_at': datetime.now().isoformat()
        }
