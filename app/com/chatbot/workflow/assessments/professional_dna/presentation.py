from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from .questions import QuestionCategory, BusinessUnit
from .analysis import AnalysisResult

class PresentationFormat(Enum):
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"

@dataclass
class PresentationConfig:
    format: PresentationFormat = PresentationFormat.MARKDOWN
    include_charts: bool = True
    include_recommendations: bool = True
    include_insights: bool = True
    include_generational: bool = True
    include_business_unit: bool = True
    language: str = "es"

class ResultPresentation:
    def __init__(self, config: Optional[PresentationConfig] = None):
        self.config = config or PresentationConfig()
        self.chart_templates = {
            'radar': """
            ```mermaid
            radarChart
                title {title}
                {categories}
                {scores}
            ```
            """,
            'bar': """
            ```mermaid
            barChart
                title {title}
                x-axis {categories}
                y-axis 0 1
                {scores}
            ```
            """,
            'pie': """
            ```mermaid
            pieChart
                title {title}
                {scores}
            ```
            """
        }

    def format_results(
        self,
        results: Dict[str, AnalysisResult],
        business_unit: BusinessUnit,
        generation: str
    ) -> str:
        """Formatea los resultados según la configuración"""
        if self.config.format == PresentationFormat.MARKDOWN:
            return self._format_markdown(results, business_unit, generation)
        elif self.config.format == PresentationFormat.HTML:
            return self._format_html(results, business_unit, generation)
        elif self.config.format == PresentationFormat.JSON:
            return self._format_json(results, business_unit, generation)
        else:
            return self._format_text(results, business_unit, generation)

    def _format_markdown(
        self,
        results: Dict[str, AnalysisResult],
        business_unit: BusinessUnit,
        generation: str
    ) -> str:
        """Formatea los resultados en Markdown"""
        sections = []
        
        # Título y resumen
        sections.append(f"# Análisis de ADN Profesional - {business_unit.value.title()}\n")
        sections.append(f"## Resumen Ejecutivo\n")
        
        # Puntajes generales
        overall_scores = self._calculate_overall_scores(results)
        sections.append(self._format_overall_scores(overall_scores))
        
        # Gráficos
        if self.config.include_charts:
            sections.append("## Visualización de Resultados\n")
            sections.append(self._generate_charts(results))
        
        # Insights por categoría
        if self.config.include_insights:
            sections.append("## Insights por Categoría\n")
            sections.append(self._format_category_insights(results))
        
        # Correlación generacional
        if self.config.include_generational:
            sections.append("## Análisis Generacional\n")
            sections.append(self._format_generational_analysis(results, generation))
        
        # Correlación con unidad de negocio
        if self.config.include_business_unit:
            sections.append("## Análisis por Unidad de Negocio\n")
            sections.append(self._format_business_unit_analysis(results, business_unit))
        
        # Recomendaciones
        if self.config.include_recommendations:
            sections.append("## Recomendaciones\n")
            sections.append(self._format_recommendations(results))
        
        return "\n".join(sections)

    def _format_overall_scores(self, scores: Dict) -> str:
        """Formatea los puntajes generales"""
        return f"""
### Puntajes Generales
- **Puntaje Base**: {scores['base_score']:.2f}
- **Puntaje Ponderado**: {scores['weighted_score']:.2f}
- **Puntaje Ajustado por Dificultad**: {scores['difficulty_adjusted_score']:.2f}
"""

    def _generate_charts(self, results: Dict[str, AnalysisResult]) -> str:
        """Genera gráficos para visualizar los resultados"""
        # Radar chart para categorías
        categories = [cat.value for cat in QuestionCategory]
        scores = [results[cat].weighted_score for cat in categories]
        
        radar_chart = self.chart_templates['radar'].format(
            title="Puntajes por Categoría",
            categories=", ".join(categories),
            scores=", ".join(map(str, scores))
        )
        
        # Bar chart para comparación de puntajes
        bar_chart = self.chart_templates['bar'].format(
            title="Comparación de Puntajes",
            categories=", ".join(categories),
            scores=", ".join(map(str, scores))
        )
        
        return f"{radar_chart}\n\n{bar_chart}"

    def _format_category_insights(self, results: Dict[str, AnalysisResult]) -> str:
        """Formatea los insights por categoría"""
        insights = []
        for category, result in results.items():
            insights.append(f"### {category.title()}\n")
            for insight in result.insights:
                insights.append(f"- {insight}")
            insights.append("")
        return "\n".join(insights)

    def _format_generational_analysis(
        self,
        results: Dict[str, AnalysisResult],
        generation: str
    ) -> str:
        """Formatea el análisis generacional"""
        analysis = [f"### Correlación con Generación {generation.title()}\n"]
        for category, result in results.items():
            if result.generational_correlation:
                correlation = sum(result.generational_correlation.values()) / len(result.generational_correlation)
                analysis.append(f"- **{category.title()}**: {correlation:.2f}")
        return "\n".join(analysis)

    def _format_business_unit_analysis(
        self,
        results: Dict[str, AnalysisResult],
        business_unit: BusinessUnit
    ) -> str:
        """Formatea el análisis por unidad de negocio"""
        analysis = [f"### Análisis para {business_unit.value.title()}\n"]
        for category, result in results.items():
            if result.business_unit_correlation:
                correlation = sum(result.business_unit_correlation.values()) / len(result.business_unit_correlation)
                analysis.append(f"- **{category.title()}**: {correlation:.2f}")
        return "\n".join(analysis)

    def _format_recommendations(self, results: Dict[str, AnalysisResult]) -> str:
        """Formatea las recomendaciones"""
        recommendations = []
        for category, result in results.items():
            recommendations.append(f"### Recomendaciones para {category.title()}\n")
            for rec in result.recommendations:
                recommendations.append(f"- {rec}")
            recommendations.append("")
        return "\n".join(recommendations)

    def _calculate_overall_scores(self, results: Dict[str, AnalysisResult]) -> Dict:
        """Calcula los puntajes generales"""
        return {
            'base_score': sum(r.score for r in results.values()) / len(results),
            'weighted_score': sum(r.weighted_score for r in results.values()) / len(results),
            'difficulty_adjusted_score': sum(r.difficulty_adjusted_score for r in results.values()) / len(results)
        }

    def _format_html(self, results: Dict[str, AnalysisResult], business_unit: BusinessUnit, generation: str) -> str:
        """Formatea los resultados en HTML"""
        # Implementar formato HTML
        pass

    def _format_json(self, results: Dict[str, AnalysisResult], business_unit: BusinessUnit, generation: str) -> str:
        """Formatea los resultados en JSON"""
        # Implementar formato JSON
        pass

    def _format_text(self, results: Dict[str, AnalysisResult], business_unit: BusinessUnit, generation: str) -> str:
        """Formatea los resultados en texto plano"""
        # Implementar formato texto
        pass 