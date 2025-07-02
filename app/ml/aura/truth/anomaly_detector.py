from typing import Dict, Any, List

class AnomalyDetector:
    """
    Analizador avanzado de anomalías para datos de personas.
    Detecta patrones atípicos, inconsistencias graves y posibles fraudes en la información.
    Puede ser usado como componente en TruthAnalyzer o TruthSense.
    """
    def __init__(self):
        pass

    def detect(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        anomaly_score = 0.0  # Score base: 0 = sin anomalías, 1 = anomalía grave
        anomalies = []
        evidence_sources = []

        # Ejemplo: Experiencia laboral con fechas futuras
        if "experience" in person_data:
            for exp in person_data["experience"]:
                if "end_date" in exp:
                    try:
                        from datetime import datetime
                        end = datetime.strptime(exp["end_date"], "%Y-%m-%d")
                        if end > datetime.now():
                            anomalies.append("Experiencia con fecha de finalización en el futuro")
                            anomaly_score = max(anomaly_score, 0.7)
                            evidence_sources.append("future_experience_date")
                    except:
                        pass

        # Ejemplo: Edad fuera de rango razonable
        if "edad" in person_data:
            edad = person_data["edad"]
            if not (14 <= edad <= 90):
                anomalies.append(f"Edad atípica detectada: {edad}")
                anomaly_score = max(anomaly_score, 0.8)
                evidence_sources.append("age_out_of_range")

        # Ejemplo: Duplicidad de identificadores
        if "identifiers" in person_data:
            ids = person_data["identifiers"]
            if isinstance(ids, list) and len(set(ids)) != len(ids):
                anomalies.append("Identificadores duplicados detectados")
                anomaly_score = max(anomaly_score, 0.6)
                evidence_sources.append("duplicate_identifiers")

        return {
            "anomaly_score": anomaly_score,
            "anomalies": anomalies,
            "evidence_sources": evidence_sources or ["anomaly_detection"]
        } 