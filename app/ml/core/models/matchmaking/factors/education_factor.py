"""
Factor de educación para el sistema de matchmaking.
"""
from typing import Dict, List, Optional, Any
import numpy as np
from ..base import BaseFactor
from ...education.university import UniversityModel
from ...education.program_ranking import ProgramRankingModel

class EducationFactor(BaseFactor):
    """Factor que evalúa la educación de los candidatos."""
    
    def __init__(self,
                 university_model: UniversityModel,
                 program_model: ProgramRankingModel,
                 product_type: str = 'huntred',
                 weights: Optional[Dict[str, float]] = None):
        """
        Inicializa el factor de educación.
        
        Args:
            university_model: Modelo de universidades
            program_model: Modelo de programas
            product_type: Tipo de producto (huntred, executive, huntu)
            weights: Pesos personalizados para el factor
        """
        super().__init__('education')
        self.university_model = university_model
        self.program_model = program_model
        self.product_type = product_type
        
        # Pesos por defecto según producto
        self.default_weights = {
            'huntred': {
                'university_score': 0.4,
                'program_score': 0.3,
                'experience_match': 0.2,
                'skills_match': 0.1
            },
            'executive': {
                'university_score': 0.5,
                'program_score': 0.3,
                'experience_match': 0.15,
                'skills_match': 0.05
            },
            'huntu': {
                'university_score': 0.3,
                'program_score': 0.3,
                'experience_match': 0.2,
                'skills_match': 0.2
            }
        }
        
        # Usar pesos personalizados o los por defecto
        self.weights = weights or self.default_weights.get(product_type, self.default_weights['huntred'])
        
        # Scores mínimos por producto
        self.min_scores = {
            'huntred': 0.6,
            'executive': 0.8,
            'huntu': 0.5
        }
        
    def calculate_score(self,
                       candidate_data: Dict[str, Any],
                       job_data: Dict[str, Any]) -> float:
        """
        Calcula el score de educación.
        
        Args:
            candidate_data: Datos del candidato
            job_data: Datos del trabajo
            
        Returns:
            Score de educación (0-1)
        """
        # Obtener datos de educación
        education = candidate_data.get('education', {})
        
        # Calcular scores individuales
        university_score = self._calculate_university_score(
            university=education.get('university'),
            preferred_universities=job_data.get('requirements', {}).get('preferred_universities', [])
        )
        
        program_score = self._calculate_program_score(
            program=education.get('program'),
            preferred_programs=job_data.get('requirements', {}).get('preferred_programs', [])
        )
        
        experience_score = self._calculate_experience_score(
            experience=education.get('experience', 0),
            required_experience=job_data.get('requirements', {}).get('required_experience', 0)
        )
        
        skills_score = self._calculate_skills_score(
            candidate_skills=education.get('skills', []),
            required_skills=job_data.get('requirements', {}).get('required_skills', [])
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
                                  university: Optional[str],
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
                               program: Optional[str],
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
        
    def get_analysis(self,
                    candidate_data: Dict[str, Any],
                    job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene un análisis detallado del factor.
        
        Args:
            candidate_data: Datos del candidato
            job_data: Datos del trabajo
            
        Returns:
            Análisis detallado
        """
        education = candidate_data.get('education', {})
        university = education.get('university')
        program = education.get('program')
        
        # Obtener métricas detalladas
        university_metrics = self.university_model.get_university_metrics(
            university=university,
            program=program
        )
        
        # Calcular scores individuales
        university_score = self._calculate_university_score(
            university=university,
            preferred_universities=job_data.get('requirements', {}).get('preferred_universities', [])
        )
        
        program_score = self._calculate_program_score(
            program=program,
            preferred_programs=job_data.get('requirements', {}).get('preferred_programs', [])
        )
        
        experience_score = self._calculate_experience_score(
            experience=education.get('experience', 0),
            required_experience=job_data.get('requirements', {}).get('required_experience', 0)
        )
        
        skills_score = self._calculate_skills_score(
            candidate_skills=education.get('skills', []),
            required_skills=job_data.get('requirements', {}).get('required_skills', [])
        )
        
        # Calcular score final
        final_score = self.calculate_score(candidate_data, job_data)
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations({
            'university_score': university_score,
            'program_score': program_score,
            'experience_score': experience_score,
            'skills_score': skills_score,
            'university_metrics': university_metrics
        })
        
        return {
            'score': final_score,
            'passes_threshold': final_score >= self.min_scores.get(self.product_type, 0.6),
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
            },
            'recommendations': recommendations,
            'weights': self.weights
        }
        
    def _generate_recommendations(self, 
                                analysis: Dict[str, Any]) -> List[str]:
        """
        Genera recomendaciones basadas en el análisis.
        
        Args:
            analysis: Análisis detallado
            
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        # Umbrales según producto
        thresholds = {
            'huntred': {
                'university': 0.7,
                'program': 0.7,
                'experience': 0.8,
                'skills': 0.8
            },
            'executive': {
                'university': 0.8,
                'program': 0.8,
                'experience': 0.9,
                'skills': 0.9
            },
            'huntu': {
                'university': 0.6,
                'program': 0.6,
                'experience': 0.7,
                'skills': 0.7
            }
        }
        
        threshold = thresholds.get(self.product_type, thresholds['huntred'])
        
        # Verificar score de universidad
        if analysis['university_score'] < threshold['university']:
            if self.product_type == 'executive':
                recommendations.append(
                    "Considerar candidatos de universidades top-tier"
                )
            elif self.product_type == 'huntu':
                recommendations.append(
                    "Considerar candidatos de universidades acreditadas"
                )
            else:
                recommendations.append(
                    "Considerar candidatos de universidades mejor rankeadas"
                )
                
        # Verificar score de programa
        if analysis['program_score'] < threshold['program']:
            if self.product_type == 'executive':
                recommendations.append(
                    "Considerar candidatos con programas de élite"
                )
            elif self.product_type == 'huntu':
                recommendations.append(
                    "Considerar candidatos con programas relevantes"
                )
            else:
                recommendations.append(
                    "Considerar candidatos con programas más alineados"
                )
                
        # Verificar experiencia
        if analysis['experience_score'] < threshold['experience']:
            if self.product_type == 'executive':
                recommendations.append(
                    "Considerar candidatos con experiencia ejecutiva"
                )
            elif self.product_type == 'huntu':
                recommendations.append(
                    "Considerar candidatos con experiencia básica"
                )
            else:
                recommendations.append(
                    "Considerar candidatos con más experiencia"
                )
                
        # Verificar habilidades
        if analysis['skills_score'] < threshold['skills']:
            missing_skills = analysis['components']['skills']['missing']
            if missing_skills:
                if self.product_type == 'executive':
                    recommendations.append(
                        f"Considerar candidatos con habilidades ejecutivas en: {', '.join(missing_skills)}"
                    )
                else:
                    recommendations.append(
                        f"Considerar candidatos con habilidades en: {', '.join(missing_skills)}"
                    )
                    
        return recommendations 