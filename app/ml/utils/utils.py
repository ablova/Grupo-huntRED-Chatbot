# /home/pablo/app/ml/utils/utils.py

from typing import List, Dict, Optional
from app.com.utils.skill_classifier import SkillClassifier
import logging

logger = logging.getLogger(__name__)

class MLUtils:
    def __init__(self, business_unit_id=None):
        """
        Inicializa la utilidad de Machine Learning.
        
        Args:
            business_unit_id: ID de la unidad de negocio para el análisis.
                            Si es None, se intenta obtener la BU predeterminada.
        """
        from app.models import BusinessUnit
        
        # Obtener la unidad de negocio adecuada
        try:
            if business_unit_id:
                business_unit = BusinessUnit.objects.get(id=business_unit_id)
            else:
                # Intentar obtener la BU predeterminada (huntRED como fallback)
                business_unit = BusinessUnit.objects.filter(name__icontains='huntRED').first()
                if not business_unit:
                    # Si no se encuentra, usar la primera BU disponible
                    business_unit = BusinessUnit.objects.first()
                    
            if not business_unit:
                logger.error("No se pudo encontrar una unidad de negocio válida para MLUtils")
                # No inicializamos el skill_classifier si no hay BU
                self.skill_classifier = None
            else:
                self.skill_classifier = SkillClassifier(business_unit)
                
        except Exception as e:
            logger.error(f"Error al inicializar MLUtils: {str(e)}")
            self.skill_classifier = None

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
        
        # Si no hay clasificador o no se solicita clasificación, usar método directo
        if not self.skill_classifier or not use_classification:
            # Comparación directa entre conjuntos (caso base)
            if not candidate_skills:
                return 0.0
                
            # Normalizar términos para una mejor coincidencia
            normalized_candidate = [s.lower().strip() for s in candidate_skills]
            normalized_required = [s.lower().strip() for s in required_skills]
            
            # Calcular solapamiento
            matches = set(normalized_candidate).intersection(set(normalized_required))
            match_percentage = (len(matches) / len(normalized_required)) * 100
            
            return min(max(match_percentage, 0), 100)
            
        try:
            # Clasificar habilidades usando múltiples sistemas
            skill_classification = self.skill_classifier.classify_skills(
                candidate_skills + required_skills
            )
            
            # Obtener habilidades técnicas y blandas
            technical_skills = skill_classification.get("technical", [])
            soft_skills = skill_classification.get("soft", [])
            
            # Calcular coincidencia ponderada
            technical_overlap = len(set(technical_skills.get("person", [])).intersection(technical_skills.get("vacancy", [])))
            soft_overlap = len(set(soft_skills.get("person", [])).intersection(soft_skills.get("vacancy", [])))
            
            # Calcular ponderación basada en la importancia de cada tipo de habilidad
            total_vacancy = (len(technical_skills.get("vacancy", [])) + len(soft_skills.get("vacancy", []))) or 1
            total_overlap = (0.7 * technical_overlap + 0.3 * soft_overlap) / total_vacancy
            
            return min(max(total_overlap * 100, 0), 100)
        except Exception as e:
            logger.error(f"Error en clasificación de habilidades: {str(e)}")
            # Fallback al método directo
            return self.calculate_skill_match(candidate_skills, required_skills, use_classification=False)
        
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