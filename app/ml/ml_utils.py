# /home/pablollh/app/ml/ml_utils.py

from typing import List, Dict
from app.chatbot.chatbot import nlp_processor as NLPProcessor
import logging
logger = logging.getLogger(__name__)


def calculate_match_percentage(candidate_skills: List[str], required_skills: List[str], classifier=None) -> float:
    if not required_skills:
        return 0.0
    if classifier is None:
        classifier = NLPProcessor(mode="candidate", analysis_depth="deep")
    candidate_skills_text = " ".join(candidate_skills)
    required_skills_text = " ".join(required_skills)
    classified_candidate = classifier.analyze(candidate_skills_text)["skills"]
    classified_required = classifier.analyze(required_skills_text)["skills"]
    candidate_set = set(classified_candidate["technical"] + classified_candidate["soft"] + classified_candidate["tools"])
    required_set = set(classified_required["technical"] + classified_required["soft"] + classified_required["tools"])
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

def calculate_match_percentage(candidate_skills: List[str], required_skills: List[str], classifier=None) -> float:
    """
    Calcula el porcentaje de coincidencia entre habilidades, opcionalmente usando el clasificador de Tabiya.
    """
    if not required_skills:
        return 0.0
    if classifier:
        candidate_skills_text = " ".join(candidate_skills)
        required_skills_text = " ".join(required_skills)
        classified_candidate = classifier.classify(candidate_skills_text)
        classified_required = classifier.classify(required_skills_text)
        candidate_set = {item['skill'].lower() for item in classified_candidate if 'skill' in item}
        required_set = {item['skill'].lower() for item in classified_required if 'skill' in item}
    else:
        candidate_set = {skill.lower() for skill in candidate_skills}
        required_set = {skill.lower() for skill in required_skills}
    match_percentage = len(candidate_set.intersection(required_set)) / len(required_set) * 100
    return round(match_percentage, 2)