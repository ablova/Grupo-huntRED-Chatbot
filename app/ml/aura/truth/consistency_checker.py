from typing import Dict, Any, List

class ConsistencyChecker:
    """
    Analizador avanzado de consistencia interna para datos de personas.
    Puede ser usado como componente en TruthAnalyzer para evaluar solapamientos,
    duplicados, y coherencia de ubicaciones, entre otros checks.
    """
    def __init__(self):
        pass

    def check(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        consistency_score = 0.8  # Base score
        red_flags = []

        # Verificar consistencia en fechas de experiencia
        if "experience" in person_data:
            experience_data = person_data["experience"]
            if isinstance(experience_data, list):
                dates = []
                for exp in experience_data:
                    if "start_date" in exp and "end_date" in exp:
                        dates.append((exp["start_date"], exp["end_date"]))
                for i, (start1, end1) in enumerate(dates):
                    for j, (start2, end2) in enumerate(dates[i+1:], i+1):
                        if start1 < end2 and start2 < end1:
                            red_flags.append("Solapamiento en fechas de experiencia")
                            consistency_score -= 0.1

        # Verificar duplicados en educación
        if "education" in person_data:
            education_data = person_data["education"]
            if isinstance(education_data, list):
                degrees = [edu.get("degree", "") for edu in education_data]
                if len(set(degrees)) != len(degrees):
                    red_flags.append("Grados duplicados en educación")
                    consistency_score -= 0.05

        # Verificar coherencia de ubicaciones
        if "location" in person_data and "experience" in person_data:
            current_location = person_data.get("location", "")
            experience_locations = [exp.get("location", "") for exp in person_data["experience"] if "location" in exp]
            if current_location and experience_locations:
                if current_location not in experience_locations:
                    if len(experience_locations) > 3:
                        red_flags.append("Ubicación actual no aparece en experiencia previa")
                        consistency_score -= 0.05

        return {
            "score": max(0.0, consistency_score),
            "red_flags": red_flags,
            "evidence_sources": ["internal_consistency_check"]
        } 