"""
Gestión de reportes y dashboards para assessments de Grupo huntRED®

Este módulo proporciona funcionalidades para generar reportes y
visualizaciones de los resultados de los assessments.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path

from app.ml.analyzers.assessment_registry import (
    AssessmentType,
    assessment_registry
)

logger = logging.getLogger(__name__)

class AssessmentReporter:
    """Gestiona la generación de reportes y visualizaciones de assessments."""
    
    def __init__(self, output_dir: str = "reports"):
        """
        Inicializa el reporter.
        
        Args:
            output_dir: Directorio donde se guardarán los reportes
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_assessment_report(
        self,
        assessment_type: AssessmentType,
        results: Dict[str, Any],
        candidate_id: str,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Genera un reporte detallado para un assessment específico.
        
        Args:
            assessment_type: Tipo de assessment
            results: Resultados del assessment
            candidate_id: ID del candidato
            timestamp: Fecha y hora del assessment
            
        Returns:
            Dict con el reporte generado
        """
        try:
            # Obtener metadata del assessment
            metadata = assessment_registry.get_assessment_metadata(assessment_type)
            
            # Crear estructura base del reporte
            report = {
                "assessment_type": assessment_type.value,
                "assessment_name": metadata.name,
                "candidate_id": candidate_id,
                "timestamp": timestamp or datetime.now().isoformat(),
                "version": metadata.version,
                "results": results
            }
            
            # Añadir visualizaciones específicas según el tipo
            if assessment_type == AssessmentType.PERSONALITY:
                report["visualizations"] = self._generate_personality_visualizations(results)
            elif assessment_type == AssessmentType.CULTURAL:
                report["visualizations"] = self._generate_cultural_visualizations(results)
            elif assessment_type == AssessmentType.PROFESSIONAL:
                report["visualizations"] = self._generate_professional_visualizations(results)
            elif assessment_type == AssessmentType.TALENT:
                report["visualizations"] = self._generate_talent_visualizations(results)
            
            # Guardar reporte
            self._save_report(report, assessment_type, candidate_id)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generando reporte para {assessment_type}: {str(e)}")
            raise
            
    def generate_integrated_report(
        self,
        assessment_results: Dict[AssessmentType, Dict[str, Any]],
        candidate_id: str
    ) -> Dict[str, Any]:
        """
        Genera un reporte integrado con todos los assessments.
        
        Args:
            assessment_results: Resultados de todos los assessments
            candidate_id: ID del candidato
            
        Returns:
            Dict con el reporte integrado
        """
        try:
            # Crear estructura base del reporte integrado
            report = {
                "candidate_id": candidate_id,
                "timestamp": datetime.now().isoformat(),
                "assessments": {}
            }
            
            # Procesar cada assessment
            for assessment_type, results in assessment_results.items():
                assessment_report = self.generate_assessment_report(
                    assessment_type,
                    results,
                    candidate_id
                )
                report["assessments"][assessment_type.value] = assessment_report
            
            # Generar análisis integrado
            report["integrated_analysis"] = self._generate_integrated_analysis(assessment_results)
            
            # Guardar reporte integrado
            self._save_integrated_report(report, candidate_id)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generando reporte integrado: {str(e)}")
            raise
            
    def _generate_personality_visualizations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera visualizaciones para el assessment de personalidad."""
        return {
            "traits_radar": {
                "type": "radar",
                "data": {
                    "labels": list(results["traits"].keys()),
                    "values": list(results["traits"].values())
                }
            },
            "insights_chart": {
                "type": "bar",
                "data": {
                    "labels": ["Fortalezas", "Áreas de Desarrollo"],
                    "values": [
                        len(results["insights"]["strengths"]),
                        len(results["insights"]["development_areas"])
                    ]
                }
            }
        }
        
    def _generate_cultural_visualizations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera visualizaciones para el assessment cultural."""
        return {
            "dimensions_radar": {
                "type": "radar",
                "data": {
                    "labels": list(results["dimensions"].keys()),
                    "values": list(results["dimensions"].values())
                }
            },
            "compatibility_gauge": {
                "type": "gauge",
                "data": {
                    "value": results["compatibility"] * 100,
                    "min": 0,
                    "max": 100
                }
            }
        }
        
    def _generate_professional_visualizations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera visualizaciones para el assessment profesional."""
        return {
            "competencies_heatmap": {
                "type": "heatmap",
                "data": {
                    "labels": list(results["competencies"].keys()),
                    "values": list(results["competencies"].values())
                }
            },
            "strengths_chart": {
                "type": "bar",
                "data": {
                    "labels": results["strengths"],
                    "values": [1] * len(results["strengths"])
                }
            }
        }
        
    def _generate_talent_visualizations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera visualizaciones para el assessment de talento."""
        return {
            "potential_gauge": {
                "type": "gauge",
                "data": {
                    "value": results["potential"] * 100,
                    "min": 0,
                    "max": 100
                }
            },
            "development_plan_timeline": {
                "type": "timeline",
                "data": results["development_plan"]
            }
        }
        
    def _generate_integrated_analysis(self, results: Dict[AssessmentType, Dict[str, Any]]) -> Dict[str, Any]:
        """Genera análisis integrado de todos los assessments."""
        return {
            "overall_score": self._calculate_overall_score(results),
            "key_insights": self._extract_key_insights(results),
            "recommendations": self._generate_integrated_recommendations(results)
        }
        
    def _calculate_overall_score(self, results: Dict[AssessmentType, Dict[str, Any]]) -> float:
        """Calcula puntuación global basada en todos los assessments."""
        scores = []
        
        if AssessmentType.PERSONALITY in results:
            personality_score = sum(results[AssessmentType.PERSONALITY]["traits"].values()) / len(results[AssessmentType.PERSONALITY]["traits"])
            scores.append(personality_score)
            
        if AssessmentType.CULTURAL in results:
            scores.append(results[AssessmentType.CULTURAL]["compatibility"])
            
        if AssessmentType.PROFESSIONAL in results:
            professional_score = sum(results[AssessmentType.PROFESSIONAL]["competencies"].values()) / len(results[AssessmentType.PROFESSIONAL]["competencies"])
            scores.append(professional_score)
            
        if AssessmentType.TALENT in results:
            scores.append(results[AssessmentType.TALENT]["potential"])
            
        return sum(scores) / len(scores) if scores else 0.0
        
    def _extract_key_insights(self, results: Dict[AssessmentType, Dict[str, Any]]) -> List[str]:
        """Extrae insights clave de todos los assessments."""
        insights = []
        
        for assessment_type, assessment_results in results.items():
            if "insights" in assessment_results:
                insights.extend(assessment_results["insights"].get("key_points", []))
                
        return insights
        
    def _generate_integrated_recommendations(self, results: Dict[AssessmentType, Dict[str, Any]]) -> List[str]:
        """Genera recomendaciones integradas basadas en todos los assessments."""
        recommendations = []
        
        for assessment_type, assessment_results in results.items():
            if "recommendations" in assessment_results:
                recommendations.extend(assessment_results["recommendations"])
                
        return recommendations
        
    def _save_report(self, report: Dict[str, Any], assessment_type: AssessmentType, candidate_id: str):
        """Guarda un reporte individual en disco."""
        filename = f"{candidate_id}_{assessment_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)
            
    def _save_integrated_report(self, report: Dict[str, Any], candidate_id: str):
        """Guarda un reporte integrado en disco."""
        filename = f"{candidate_id}_integrated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2) 