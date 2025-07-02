from typing import Dict, Any, List

class InfluenceCalculator:
    """
    Calculadora avanzada de influencia social para perfiles y redes.
    Evalúa el nivel de influencia de una persona en función de su red, interacciones y señales sociales.
    Puede ser usada como componente en análisis de veracidad, reputación o impacto social.
    """
    def __init__(self):
        pass

    def calculate(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        influence_score = 0.0  # Score base
        influence_factors = []
        evidence_sources = []

        # Ejemplo: Número de conexiones o seguidores
        if "connections" in person_data:
            num_connections = len(person_data["connections"])
            if num_connections > 500:
                influence_score += 0.4
                influence_factors.append("Amplia red de contactos")
                evidence_sources.append("connections_count")
            elif num_connections > 100:
                influence_score += 0.2
                influence_factors.append("Red de contactos moderada")
                evidence_sources.append("connections_count")

        # Ejemplo: Participación en grupos o comunidades
        if "groups" in person_data:
            num_groups = len(person_data["groups"])
            if num_groups > 5:
                influence_score += 0.2
                influence_factors.append("Participación activa en comunidades")
                evidence_sources.append("groups_participation")

        # Ejemplo: Endosos o recomendaciones
        if "endorsements" in person_data:
            num_endorsements = len(person_data["endorsements"])
            if num_endorsements > 10:
                influence_score += 0.2
                influence_factors.append("Recibió múltiples endosos")
                evidence_sources.append("endorsements_count")

        # Ejemplo: Actividad reciente
        if "last_active" in person_data:
            from datetime import datetime, timedelta
            try:
                last_active = datetime.strptime(person_data["last_active"], "%Y-%m-%d")
                if (datetime.now() - last_active) < timedelta(days=30):
                    influence_score += 0.1
                    influence_factors.append("Actividad reciente detectada")
                    evidence_sources.append("recent_activity")
            except:
                pass

        influence_score = min(1.0, influence_score)
        return {
            "influence_score": influence_score,
            "influence_factors": influence_factors,
            "evidence_sources": evidence_sources or ["influence_analysis"]
        } 