# /home/pablo/app/com/chatbot/workflow/assessments/professional_dna/core.py
"""
Workflow principal para la evaluación Professional DNA.
"""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

from app.com.chatbot.workflow.core.base_workflow import BaseWorkflow
from app.ml.analyzers import PersonalityAnalyzer, ProfessionalAnalyzer, IntegratedAnalyzer
from app.com.chatbot.workflow.assessments.professional_dna.questions import (
    ProfessionalDNAQuestions,
    QuestionCategory,
    BusinessUnit
)
from app.com.chatbot.workflow.assessments.professional_dna.analysis import (
    ProfessionalDNAAnalysis,
    AnalysisResult
)
from app.com.chatbot.workflow.assessments.professional_dna.presentation import ResultPresentation
from app.com.chatbot.workflow.assessments.cv_generation.cv_generator import CVGenerator

class ProfessionalDNAWorkflow(BaseWorkflow):
    """Workflow para la evaluación Professional DNA."""
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__()
        self.business_unit = business_unit
        self.questions = ProfessionalDNAQuestions(business_unit)
        self.analysis = ProfessionalDNAAnalysis()
        self.personality_analyzer = PersonalityAnalyzer()
        self.cv_generator = CVGenerator()
        
    def execute(self, candidate_data: Dict) -> Dict:
        """Ejecuta el workflow completo de evaluación."""
        # 1. Obtener respuestas del candidato
        responses = self._collect_responses(candidate_data)
        
        # 2. Analizar respuestas
        analysis_result = self._analyze_responses(responses)
        
        # 3. Análisis de personalidad con ML
        personality_insights = self._analyze_personality(candidate_data)
        
        # 4. Generar CV optimizado
        cv_data = self._generate_cv(candidate_data, analysis_result, personality_insights)
        
        # 5. Generar reporte final
        report = self._generate_report(analysis_result, personality_insights, cv_data)
        
        return {
            'analysis': analysis_result,
            'personality': personality_insights,
            'cv': cv_data,
            'report': report
        }
    
    def _collect_responses(self, candidate_data: Dict) -> Dict:
        """Recopila y valida las respuestas del candidato."""
        responses = {}
        for category in QuestionCategory:
            category_questions = self.questions.get_questions(category)
            category_responses = candidate_data.get(category.value, {})
            
            # Validar respuestas
            validated_responses = self._validate_responses(
                category_responses,
                category_questions
            )
            
            responses[category.value] = validated_responses
            
        return responses
    
    def _validate_responses(self, responses: Dict, questions: List) -> Dict:
        """Valida que las respuestas sean coherentes y completas."""
        validated = {}
        for question in questions:
            response = responses.get(question.id)
            if response and self._is_valid_response(response, question):
                validated[question.id] = response
        return validated
    
    def _is_valid_response(self, response: any, question: any) -> bool:
        """Verifica si una respuesta es válida para una pregunta."""
        # Implementar lógica de validación según el tipo de pregunta
        return True
    
    def _analyze_responses(self, responses: Dict) -> AnalysisResult:
        """Analiza las respuestas y genera resultados."""
        try:
            # Primero intentamos usar el analizador centralizado si está disponible
            professional_analyzer = ProfessionalAnalyzer()
            
            # Preparar datos para el analizador centralizado
            analysis_data = {
                'assessment_type': 'professional_dna',
                'responses': responses,
                'business_unit': self.business_unit.value if hasattr(self.business_unit, 'value') else self.business_unit
            }
            
            # Realizar análisis con el analizador centralizado
            central_result = professional_analyzer.analyze(analysis_data, self.business_unit)
            
            # Si el análisis centralizado fue exitoso, lo convertimos al formato AnalysisResult
            if central_result and not central_result.get('status') == 'error':
                logging.info(f"Análisis de ADN profesional realizado con analizador centralizado")
                
                # Mapear resultados del analizador centralizado al formato AnalysisResult
                result = AnalysisResult()
                
                # Mapear dimensiones y puntuaciones
                result.dimension_scores = central_result.get('dimension_scores', {})
                result.dimension_insights = central_result.get('dimension_insights', {})
                result.strengths = central_result.get('strengths', [])
                result.development_areas = central_result.get('development_areas', [])
                result.recommendations = central_result.get('recommendations', [])
                result.career_paths = central_result.get('career_paths', [])
                
                return result
            else:
                # Si hay error, usamos el método tradicional
                logging.warning(f"Fallback a análisis profesional tradicional: {central_result.get('message', 'Error desconocido')}")
                return self.analysis.analyze(responses, self.business_unit)
                
        except Exception as e:
            logging.error(f"Error usando analizador profesional centralizado: {str(e)}. Fallback a análisis tradicional.")
            # En caso de error, usamos el método tradicional como fallback
            return self.analysis.analyze(responses, self.business_unit)
    
    def _analyze_personality(self, candidate_data: Dict) -> Dict:
        """Analiza la personalidad usando ML."""
        return self.personality_analyzer.analyze(
            candidate_data,
            business_unit=self.business_unit
        )
    
    def _generate_cv(self, candidate_data: Dict, analysis_result: AnalysisResult, personality_insights: Dict) -> Dict:
        """Genera un CV optimizado basado en los resultados."""
        return self.cv_generator.generate(
            candidate_data,
            analysis_result,
            personality_insights,
            business_unit=self.business_unit
        )
    
    def _generate_report(self, analysis_result: AnalysisResult, personality_insights: Dict, cv_data: Dict) -> Dict:
        """
        Genera el reporte final de evaluación con formato visual mejorado.
        
        Args:
            analysis_result: Resultados del análisis de ADN profesional
            personality_insights: Insights de personalidad
            cv_data: Datos del CV optimizado
            
        Returns:
            Dict: Reporte formateado
        """
        try:
            # Inicializar presentación
            presentation = ResultPresentation(analysis_result)
            report = presentation.generate_full_report()
            
            # Añadir sección de ADN Profesional
            report['professional_dna'] = {
                'title': '🧬 *Tu ADN Profesional*',
                'sections': []
            }
            
            # Dimensiones principales
            dimensions = {
                'strategic_thinking': '🎯',
                'emotional_intelligence': '❤️',
                'adaptability': '🔄',
                'collaboration': '🤝',
                'innovation': '💡',
                'resilience': '💪',
                'results_orientation': '📈'
            }
            
            for dimension, score in analysis_result.dimension_scores.items():
                emoji = dimensions.get(dimension, '📌')
                progress = "🟢" * int(score/20) + "⚪" * (5 - int(score/20))
                report['professional_dna']['sections'].append({
                    'title': f"{emoji} {dimension.replace('_', ' ').title()}",
                    'score': f"{progress} ({score:.1f}/100)",
                    'description': analysis_result.dimension_insights.get(dimension, '')
                })
            
            # Añadir sección de Personalidad
            report['personality'] = {
                'title': '🧠 *Insights de Personalidad*',
                'sections': []
            }
            
            for trait, value in personality_insights.items():
                report['personality']['sections'].append({
                    'title': trait.replace('_', ' ').title(),
                    'value': value,
                    'description': personality_insights.get(f"{trait}_description", '')
                })
            
            # Añadir sección de CV
            report['cv'] = {
                'title': '📄 *CV Optimizado*',
                'sections': []
            }
            
            for section, content in cv_data.items():
                if section != 'recommendations':
                    report['cv']['sections'].append({
                        'title': section.replace('_', ' ').title(),
                        'content': content
                    })
            
            # Añadir recomendaciones
            report['recommendations'] = {
                'title': '🎯 *Recomendaciones Personalizadas*',
                'items': []
            }
            
            # Combinar recomendaciones de diferentes fuentes
            all_recommendations = []
            all_recommendations.extend(analysis_result.recommendations)
            all_recommendations.extend(cv_data.get('recommendations', []))
            all_recommendations.extend(personality_insights.get('recommendations', []))
            
            for rec in all_recommendations:
                report['recommendations']['items'].append({
                    'text': rec,
                    'priority': 'high' if 'crucial' in rec.lower() else 'medium'
                })
            
            # Añadir sección de próximos pasos
            report['next_steps'] = {
                'title': '🚀 *Próximos Pasos*',
                'items': [
                    'Explorar roles que se alineen con tu ADN profesional',
                    'Desarrollar las áreas identificadas como prioritarias',
                    'Aplicar las recomendaciones personalizadas',
                    'Actualizar tu CV con los insights obtenidos'
                ]
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generando reporte: {str(e)}")
            return {
                'error': 'Lo siento, hubo un error al generar el reporte completo. Por favor, intenta nuevamente.'
            }
    
    def get_questions(self, category: Optional[QuestionCategory] = None) -> Dict:
        """Obtiene las preguntas para una categoría o todas."""
        if category:
            return self.questions.get_questions(category)
        return self.questions.get_all_questions()
    
    def get_progress(self) -> float:
        """Obtiene el progreso actual de la evaluación."""
        return self.analysis.get_progress()
    
    def get_recommendations(self) -> List[str]:
        """Obtiene recomendaciones basadas en el análisis actual."""
        return self.analysis.get_recommendations() 