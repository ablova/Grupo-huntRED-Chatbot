# /home/pablo/app/ml/ml_utils.py

from typing import List, Dict, Optional
from app.utilidades.skill_classifier import SkillClassifier
import logging

logger = logging.getLogger(__name__)

class MLUtils:
    def __init__(self):
        self.skill_classifier = SkillClassifier()

    def calculate_skill_match(self, 
                            candidate_skills: List[str], 
                            required_skills: List[str], 
                            use_classification: bool = True) -> float:
        """
        Calcula el porcentaje de coincidencia entre habilidades usando múltiples sistemas.
        
        Args:
            candidate_skills: Lista de habilidades del candidato
            required_skills: Lista de habilidades requeridas
            use_classification: Si usar el sistema de clasificación de habilidades
            
        Returns:
            float: Porcentaje de coincidencia (0-100)
        """
        if not required_skills:
            return 0.0
            
        if use_classification:
            # Clasificar habilidades usando múltiples sistemas
            skill_classification = self.skill_classifier.classify_skills(
                candidate_skills + required_skills
            )
            
            # Obtener habilidades técnicas y blandas
            technical_skills = skill_classification.get("technical", [])
            soft_skills = skill_classification.get("soft", [])
            
            # Calcular coincidencia ponderada
            technical_overlap = len(set(technical_skills["person"]).intersection(technical_skills["vacancy"]))
            soft_overlap = len(set(soft_skills["person"]).intersection(soft_skills["vacancy"]))
            
            # Calcular ponderación basada en la importancia de cada tipo de habilidad
            total_overlap = (0.7 * technical_overlap + 0.3 * soft_overlap) / (
                len(technical_skills["vacancy"]) + len(soft_skills["vacancy"]) or 1
            )
            
            return min(max(total_overlap * 100, 0), 100)
        
        # Si no se usa clasificación, usar coincidencia directa
        candidate_set = {skill.lower() for skill in candidate_skills}
        required_set = {skill.lower() for skill in required_skills}
        overlap = len(candidate_set.intersection(required_set))
        return min(max(overlap / len(required_set) * 100, 0), 100)

    def calculate_salary_alignment(self, 
                                 candidate_salary: float, 
                                 job_salary: float) -> float:
        """
        Calcula la alineación salarial entre candidato y vacante.
        
        Args:
            candidate_salary: Salario del candidato
            job_salary: Salario de la vacante
            
        Returns:
            float: Porcentaje de alineación (0-100)
        """
        if not job_salary:
            return 0.0
            
        alignment = 100 - abs(candidate_salary - job_salary) / job_salary * 100
        return max(round(alignment, 2), 0)

    def calculate_industry_match(self, 
                               person_industries: List[str], 
                               vacancy_industries: List[str]) -> float:
        """
        Calcula la coincidencia de industria.
        
        Args:
            person_industries: Lista de industrias del candidato
            vacancy_industries: Lista de industrias de la vacante
            
        Returns:
            float: Porcentaje de coincidencia (0-100)
        """
        person_set = {industry.lower() for industry in person_industries}
        vacancy_set = {industry.lower() for industry in vacancy_industries}
        overlap = len(person_set.intersection(vacancy_set))
        return min(max(overlap / len(vacancy_set) * 100, 0), 100)