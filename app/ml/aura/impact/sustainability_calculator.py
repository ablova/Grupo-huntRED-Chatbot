from typing import Dict, Any, List

class SustainabilityCalculator:
    """
    Calculadora avanzada de sostenibilidad para perfiles, empresas o proyectos.
    Evalúa el nivel de sostenibilidad en función de prácticas, certificaciones, impacto ambiental y social.
    Puede ser usada como componente en análisis de impacto, reputación o responsabilidad social.
    """
    def __init__(self):
        pass

    def calculate(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        sustainability_score = 0.0  # Score base
        sustainability_factors = []
        evidence_sources = []

        # Ejemplo: Certificaciones de sostenibilidad
        if "certifications" in entity_data:
            certs = entity_data["certifications"]
            if isinstance(certs, list):
                for cert in certs:
                    if cert.lower() in ["iso 14001", "b corp", "leed", "fair trade"]:
                        sustainability_score += 0.2
                        sustainability_factors.append(f"Certificación: {cert}")
                        evidence_sources.append("sustainability_certification")

        # Ejemplo: Prácticas de reciclaje
        if entity_data.get("recycling_program", False):
            sustainability_score += 0.1
            sustainability_factors.append("Programa de reciclaje activo")
            evidence_sources.append("recycling_program")

        # Ejemplo: Reportes de impacto social
        if entity_data.get("social_impact_report", False):
            sustainability_score += 0.1
            sustainability_factors.append("Reporte de impacto social disponible")
            evidence_sources.append("social_impact_report")

        # Ejemplo: Uso de energías renovables
        if entity_data.get("renewable_energy", False):
            sustainability_score += 0.2
            sustainability_factors.append("Uso de energías renovables")
            evidence_sources.append("renewable_energy")

        # Ejemplo: Políticas de diversidad e inclusión
        if entity_data.get("dei_policy", False):
            sustainability_score += 0.1
            sustainability_factors.append("Política DEI activa")
            evidence_sources.append("dei_policy")

        sustainability_score = min(1.0, sustainability_score)
        return {
            "sustainability_score": sustainability_score,
            "sustainability_factors": sustainability_factors,
            "evidence_sources": evidence_sources or ["sustainability_analysis"]
        } 