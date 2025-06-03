"""
Presentación de resultados de la evaluación Professional DNA
"""
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
from enum import Enum
from app.ats.chatbot.workflow.assessments.professional_dna.questions import (
    QuestionCategory,
    BusinessUnit
)
from app.ats.chatbot.workflow.assessments.professional_dna.analysis import (
    AnalysisResult
)

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

@dataclass
class ReportSection:
    """Sección de un reporte con título, contenido y tipo de visualización."""
    title: str
    content: str
    visualization_type: str  # 'bar', 'radar', 'text', etc.
    data: Optional[Dict] = None

class ResultPresentation:
    """Clase para generar presentaciones visuales y narrativas de resultados."""
    
    def __init__(self, analysis_result: AnalysisResult):
        self.result = analysis_result
        self.sections: List[ReportSection] = []
        
    def generate_full_report(self) -> Dict:
        """Genera un reporte completo con todas las secciones."""
        self._add_overview_section()
        self._add_dimension_analysis()
        self._add_strengths_weaknesses()
        self._add_recommendations()
        self._add_business_unit_insights()
        return self._format_report()
    
    def _add_overview_section(self):
        """Añade una sección de resumen general."""
        overview = ReportSection(
            title="Resumen General",
            content=self._generate_overview_text(),
            visualization_type="radar",
            data=self._prepare_overview_data()
        )
        self.sections.append(overview)
    
    def _add_dimension_analysis(self):
        """Añade análisis detallado por dimensión."""
        for dimension in self.result.dimensions:
            section = ReportSection(
                title=f"Análisis de {dimension.name}",
                content=self._generate_dimension_text(dimension),
                visualization_type="bar",
                data=self._prepare_dimension_data(dimension)
            )
            self.sections.append(section)
    
    def _add_strengths_weaknesses(self):
        """Añade sección de fortalezas y áreas de mejora."""
        section = ReportSection(
            title="Fortalezas y Áreas de Mejora",
            content=self._generate_swot_text(),
            visualization_type="text",
            data=self._prepare_swot_data()
        )
        self.sections.append(section)
    
    def _add_recommendations(self):
        """Añade recomendaciones personalizadas."""
        section = ReportSection(
            title="Recomendaciones",
            content=self._generate_recommendations_text(),
            visualization_type="text",
            data=self._prepare_recommendations_data()
        )
        self.sections.append(section)
    
    def _add_business_unit_insights(self):
        """Añade insights específicos por unidad de negocio."""
        if self.result.business_unit:
            section = ReportSection(
                title=f"Insights para {self.result.business_unit}",
                content=self._generate_business_unit_text(),
                visualization_type="bar",
                data=self._prepare_business_unit_data()
            )
            self.sections.append(section)
    
    def _generate_overview_text(self) -> str:
        """Genera texto descriptivo del resumen general."""
        return f"""
        El candidato muestra un perfil profesional con las siguientes características principales:
        - Puntuación general: {self.result.overall_score}/100
        - Dimensiones más destacadas: {', '.join(self.result.top_dimensions)}
        - Áreas de oportunidad: {', '.join(self.result.improvement_areas)}
        """
    
    def _prepare_overview_data(self) -> Dict:
        """Prepara datos para visualización del resumen."""
        return {
            'dimensions': [d.name for d in self.result.dimensions],
            'scores': [d.score for d in self.result.dimensions]
        }
    
    def _generate_dimension_text(self, dimension) -> str:
        """Genera texto descriptivo para una dimensión específica."""
        return f"""
        {dimension.name}:
        - Puntuación: {dimension.score}/100
        - Interpretación: {dimension.interpretation}
        - Comportamientos clave: {', '.join(dimension.key_behaviors)}
        """
    
    def _prepare_dimension_data(self, dimension) -> Dict:
        """Prepara datos para visualización de una dimensión."""
        return {
            'subdimensions': dimension.subdimensions,
            'scores': dimension.subscores
        }
    
    def _generate_swot_text(self) -> str:
        """Genera texto de análisis FODA."""
        return f"""
        Fortalezas:
        {self._format_list(self.result.strengths)}
        
        Áreas de Mejora:
        {self._format_list(self.result.improvement_areas)}
        """
    
    def _prepare_swot_data(self) -> Dict:
        """Prepara datos para visualización FODA."""
        return {
            'strengths': self.result.strengths,
            'weaknesses': self.result.improvement_areas
        }
    
    def _generate_recommendations_text(self) -> str:
        """Genera texto de recomendaciones."""
        return f"""
        Recomendaciones de Desarrollo:
        {self._format_list(self.result.recommendations)}
        
        Plan de Acción Sugerido:
        {self._format_list(self.result.action_plan)}
        """
    
    def _prepare_recommendations_data(self) -> Dict:
        """Prepara datos para visualización de recomendaciones."""
        return {
            'recommendations': self.result.recommendations,
            'action_plan': self.result.action_plan
        }
    
    def _generate_business_unit_text(self) -> str:
        """Genera texto específico para unidad de negocio."""
        return f"""
        Análisis para {self.result.business_unit}:
        - Compatibilidad: {self.result.business_unit_compatibility}%
        - Roles recomendados: {', '.join(self.result.recommended_roles)}
        - Áreas de desarrollo específicas: {', '.join(self.result.business_unit_development_areas)}
        """
    
    def _prepare_business_unit_data(self) -> Dict:
        """Prepara datos para visualización de unidad de negocio."""
        return {
            'compatibility': self.result.business_unit_compatibility,
            'recommended_roles': self.result.recommended_roles,
            'development_areas': self.result.business_unit_development_areas
        }
    
    def _format_list(self, items: List[str]) -> str:
        """Formatea una lista de items para presentación."""
        return "\n".join(f"- {item}" for item in items)
    
    def _format_report(self) -> Dict:
        """Formatea el reporte final con todas las secciones."""
        return {
            'sections': [
                {
                    'title': section.title,
                    'content': section.content,
                    'visualization': self._generate_visualization(section)
                }
                for section in self.sections
            ]
        }
    
    def _generate_visualization(self, section: ReportSection) -> Dict:
        """Genera visualización según el tipo de sección."""
        if section.visualization_type == 'radar':
            return self._create_radar_chart(section.data)
        elif section.visualization_type == 'bar':
            return self._create_bar_chart(section.data)
        return None
    
    def _create_radar_chart(self, data: Dict) -> Dict:
        """Crea gráfico radar para dimensiones."""
        # Implementación de gráfico radar usando matplotlib
        pass
    
    def _create_bar_chart(self, data: Dict) -> Dict:
        """Crea gráfico de barras para comparativas."""
        # Implementación de gráfico de barras usando matplotlib
        pass

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