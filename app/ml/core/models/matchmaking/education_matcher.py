"""
Modelo para el matchmaking basado en educación.
"""
from typing import Dict, List, Optional, Any
import numpy as np
from ...education.university import UniversityModel
from ...education.program_ranking import ProgramRankingModel

class EducationMatcher:
    """Modelo para matching basado en educación."""
    
    def __init__(self, 
                 university_model: UniversityModel,
                 program_model: ProgramRankingModel):
        """
        Inicializa el matcher de educación.
        
        Args:
            university_model: Modelo de universidades
            program_model: Modelo de programas
        """
        self.university_model = university_model
        self.program_model = program_model
        
        # Pesos para diferentes aspectos
        self.weights = {
            'university_score': 0.4,
            'program_score': 0.3,
            'experience_match': 0.2,
            'skills_match': 0.1
        }
        
    def calculate_education_score(self,
                                candidate_education: Dict[str, Any],
                                job_requirements: Dict[str, Any]) -> float:
        """
        Calcula el score de match basado en educación.
        
        Args:
            candidate_education: Educación del candidato
            job_requirements: Requisitos del trabajo
            
        Returns:
            Score de match (0-1)
        """
        # Obtener datos de educación
        university = candidate_education.get('university')
        program = candidate_education.get('program')
        degree = candidate_education.get('degree')
        experience = candidate_education.get('experience', 0)
        
        # Obtener requisitos
        required_degree = job_requirements.get('required_degree')
        required_experience = job_requirements.get('required_experience', 0)
        preferred_universities = job_requirements.get('preferred_universities', [])
        preferred_programs = job_requirements.get('preferred_programs', [])
        required_skills = job_requirements.get('required_skills', [])
        candidate_skills = candidate_education.get('skills', [])
        
        # Calcular scores individuales
        university_score = self._calculate_university_score(
            university=university,
            preferred_universities=preferred_universities
        )
        
        program_score = self._calculate_program_score(
            program=program,
            preferred_programs=preferred_programs
        )
        
        experience_score = self._calculate_experience_score(
            experience=experience,
            required_experience=required_experience
        )
        
        skills_score = self._calculate_skills_score(
            candidate_skills=candidate_skills,
            required_skills=required_skills
        )
        
        # Calcular score final
        final_score = (
            university_score * self.weights['university_score'] +
            program_score * self.weights['program_score'] +
            experience_score * self.weights['experience_match'] +
            skills_score * self.weights['skills_match']
        )
        
        return min(1.0, max(0.0, final_score))
        
    def _calculate_university_score(self,
                                  university: str,
                                  preferred_universities: List[str]) -> float:
        """Calcula el score de universidad."""
        if not university:
            return 0.5  # Score neutral si no hay universidad
            
        # Obtener métricas de la universidad
        metrics = self.university_model.get_university_metrics(university)
        
        # Bonus si es una universidad preferida
        preferred_bonus = 0.1 if university in preferred_universities else 0.0
        
        return min(1.0, metrics['final_score'] + preferred_bonus)
        
    def _calculate_program_score(self,
                               program: str,
                               preferred_programs: List[str]) -> float:
        """Calcula el score de programa."""
        if not program:
            return 0.5  # Score neutral si no hay programa
            
        # Obtener categoría del programa
        category = self.program_model.get_program_category(program)
        if not category:
            return 0.5  # Score neutral si no hay categoría
            
        # Bonus si es un programa preferido
        preferred_bonus = 0.1 if program in preferred_programs else 0.0
        
        # Obtener peso de la categoría
        category_weight = self.program_model.category_weights.get(category, 0.8)
        
        return min(1.0, category_weight + preferred_bonus)
        
    def _calculate_experience_score(self,
                                  experience: float,
                                  required_experience: float) -> float:
        """Calcula el score de experiencia."""
        if experience >= required_experience:
            return 1.0
        return experience / required_experience
        
    def _calculate_skills_score(self,
                              candidate_skills: List[str],
                              required_skills: List[str]) -> float:
        """Calcula el score de habilidades."""
        if not required_skills:
            return 1.0
            
        # Contar habilidades que coinciden
        matching_skills = sum(1 for skill in required_skills if skill in candidate_skills)
        
        return matching_skills / len(required_skills)
        
    def get_detailed_match(self,
                          candidate_education: Dict[str, Any],
                          job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene un análisis detallado del match.
        
        Args:
            candidate_education: Educación del candidato
            job_requirements: Requisitos del trabajo
            
        Returns:
            Diccionario con análisis detallado
        """
        university = candidate_education.get('university')
        program = candidate_education.get('program')
        
        # Obtener métricas detalladas
        university_metrics = self.university_model.get_university_metrics(
            university=university,
            program=program
        )
        
        # Calcular scores individuales
        university_score = self._calculate_university_score(
            university=university,
            preferred_universities=job_requirements.get('preferred_universities', [])
        )
        
        program_score = self._calculate_program_score(
            program=program,
            preferred_programs=job_requirements.get('preferred_programs', [])
        )
        
        experience_score = self._calculate_experience_score(
            experience=candidate_education.get('experience', 0),
            required_experience=job_requirements.get('required_experience', 0)
        )
        
        skills_score = self._calculate_skills_score(
            candidate_skills=candidate_education.get('skills', []),
            required_skills=job_requirements.get('required_skills', [])
        )
        
        # Calcular score final
        final_score = (
            university_score * self.weights['university_score'] +
            program_score * self.weights['program_score'] +
            experience_score * self.weights['experience_match'] +
            skills_score * self.weights['skills_match']
        )
        
        return {
            'final_score': min(1.0, max(0.0, final_score)),
            'components': {
                'university': {
                    'score': university_score,
                    'metrics': university_metrics
                },
                'program': {
                    'score': program_score,
                    'category': self.program_model.get_program_category(program)
                },
                'experience': {
                    'score': experience_score,
                    'candidate': candidate_education.get('experience', 0),
                    'required': job_requirements.get('required_experience', 0)
                },
                'skills': {
                    'score': skills_score,
                    'matching': [
                        skill for skill in job_requirements.get('required_skills', [])
                        if skill in candidate_education.get('skills', [])
                    ],
                    'missing': [
                        skill for skill in job_requirements.get('required_skills', [])
                        if skill not in candidate_education.get('skills', [])
                    ]
                }
            },
            'weights': self.weights
        } 