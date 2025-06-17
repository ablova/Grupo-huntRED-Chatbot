"""
Analyzer de educación.
"""
from typing import Dict, List, Optional, Any, Union
import numpy as np
from ...models.education.university import UniversityModel
from ...models.education.program_ranking import ProgramRankingModel

class EducationAnalyzer:
    """Analyzer para evaluación de educación."""
    
    def __init__(self,
                 university_model: UniversityModel,
                 program_model: ProgramRankingModel):
        """
        Inicializa el analyzer de educación.
        
        Args:
            university_model: Modelo de universidades
            program_model: Modelo de programas
        """
        self.university_model: UniversityModel = university_model
        self.program_model: ProgramRankingModel = program_model
        
    def analyze(self,
                candidate_data: Dict[str, Any],
                job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza la educación del candidato.
        
        Args:
            candidate_data: Datos del candidato
            job_data: Datos del trabajo
            
        Returns:
            Análisis detallado
        """
        education: Dict[str, Any] = candidate_data.get('education', {})
        university: Optional[str] = education.get('university')
        program: Optional[str] = education.get('program')
        
        # Obtener métricas de universidad
        university_metrics: Dict[str, Any] = self.university_model.get_university_metrics(
            university=university,
            program=program
        )
        
        # Obtener categoría del programa
        program_category: Optional[str] = self.program_model.get_program_category(program)
        
        # Calcular scores
        university_score: float = self._calculate_university_score(
            university=university,
            preferred_universities=job_data.get('requirements', {}).get('preferred_universities', [])
        )
        
        program_score: float = self._calculate_program_score(
            program=program,
            preferred_programs=job_data.get('requirements', {}).get('preferred_programs', [])
        )
        
        experience_score: float = self._calculate_experience_score(
            experience=education.get('experience', 0),
            required_experience=job_data.get('requirements', {}).get('required_experience', 0)
        )
        
        skills_score: float = self._calculate_skills_score(
            candidate_skills=education.get('skills', []),
            required_skills=job_data.get('requirements', {}).get('required_skills', [])
        )
        
        return {
            'university': {
                'score': university_score,
                'metrics': university_metrics
            },
            'program': {
                'score': program_score,
                'category': program_category
            },
            'experience': {
                'score': experience_score,
                'candidate': education.get('experience', 0),
                'required': job_data.get('requirements', {}).get('required_experience', 0)
            },
            'skills': {
                'score': skills_score,
                'matching': [
                    skill for skill in job_data.get('requirements', {}).get('required_skills', [])
                    if skill in education.get('skills', [])
                ],
                'missing': [
                    skill for skill in job_data.get('requirements', {}).get('required_skills', [])
                    if skill not in education.get('skills', [])
                ]
            }
        }
        
    def _calculate_university_score(self,
                                  university: Optional[str],
                                  preferred_universities: List[str]) -> float:
        """
        Calcula el score de universidad.
        
        Args:
            university: Universidad del candidato
            preferred_universities: Universidades preferidas
            
        Returns:
            Score de universidad (0-1)
        """
        if not university:
            return 0.5
            
        metrics: Dict[str, Any] = self.university_model.get_university_metrics(university)
        preferred_bonus: float = 0.1 if university in preferred_universities else 0.0
        
        return min(1.0, metrics['final_score'] + preferred_bonus)
        
    def _calculate_program_score(self,
                               program: Optional[str],
                               preferred_programs: List[str]) -> float:
        """
        Calcula el score de programa.
        
        Args:
            program: Programa del candidato
            preferred_programs: Programas preferidos
            
        Returns:
            Score de programa (0-1)
        """
        if not program:
            return 0.5
            
        category: Optional[str] = self.program_model.get_program_category(program)
        if not category:
            return 0.5
            
        preferred_bonus: float = 0.1 if program in preferred_programs else 0.0
        category_weight: float = self.program_model.category_weights.get(category, 0.8)
        
        return min(1.0, category_weight + preferred_bonus)
        
    def _calculate_experience_score(self,
                                  experience: float,
                                  required_experience: float) -> float:
        """
        Calcula el score de experiencia.
        
        Args:
            experience: Experiencia del candidato
            required_experience: Experiencia requerida
            
        Returns:
            Score de experiencia (0-1)
        """
        if experience >= required_experience:
            return 1.0
        return experience / required_experience
        
    def _calculate_skills_score(self,
                              candidate_skills: List[str],
                              required_skills: List[str]) -> float:
        """
        Calcula el score de habilidades.
        
        Args:
            candidate_skills: Habilidades del candidato
            required_skills: Habilidades requeridas
            
        Returns:
            Score de habilidades (0-1)
        """
        if not required_skills:
            return 1.0
            
        matching_skills: int = sum(1 for skill in required_skills if skill in candidate_skills)
        return matching_skills / len(required_skills) 