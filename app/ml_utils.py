# /home/amigro/app/ml_utils.py

from typing import List, Dict

def calculate_match_percentage(candidate_skills: List[str], required_skills: List[str]) -> float:
    """
    Calcula el porcentaje de coincidencia entre habilidades del candidato y habilidades requeridas.
    """
    if not required_skills:
        return 0.0
    candidate_set = set(skill.lower() for skill in candidate_skills)
    required_set = set(skill.lower() for skill in required_skills)
    match_percentage = len(candidate_set.intersection(required_set)) / len(required_set) * 100
    return round(match_percentage, 2)

def calculate_alignment_percentage(candidate_salary: float, job_salary: float) -> float:
    """
    Calcula la alineación salarial entre candidato y vacante.
    """
    if not job_salary:
        return 0.0
    alignment = 100 - abs(candidate_salary - job_salary) / job_salary * 100
    return max(round(alignment, 2), 0)