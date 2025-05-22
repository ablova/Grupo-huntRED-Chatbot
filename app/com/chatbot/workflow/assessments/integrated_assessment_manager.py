# /home/pablo/app/com/chatbot/workflow/assessments/integrated_assessment_manager.py
"""
Módulo para gestión integrada de assessments en Grupo huntRED®

Este módulo proporciona una interfaz unificada para gestionar todos los tipos
de assessments disponibles (personalidad, cultural, profesional y talento),
permitiendo ejecutarlos individualmente o como conjunto integrado.
"""
import logging
import json
from typing import Dict, List, Any, Optional, Union
from enum import Enum

from asgiref.sync import sync_to_async
from django.utils import timezone

from app.ml.analyzers import (
    PersonalityAnalyzer,
    CulturalAnalyzer, 
    ProfessionalAnalyzer,
    TalentAnalyzer,
    IntegratedAnalyzer
)

from app.com.chatbot.workflow.assessments.personality.personality_workflow import PersonalityAssessment
from app.com.chatbot.workflow.assessments.cultural.cultural_fit_workflow import CulturalFitWorkflow
from app.com.chatbot.workflow.assessments.professional_dna.core import ProfessionalDNAWorkflow
from app.com.chatbot.workflow.assessments.talent.talent_analysis_workflow import TalentAnalysisWorkflow

logger = logging.getLogger(__name__)

class AssessmentType(Enum):
    """Tipos de assessments disponibles"""
    PERSONALITY = "personality"
    CULTURAL = "cultural"
    PROFESSIONAL = "professional"
    TALENT = "talent"
    INTEGRATED = "integrated"

class IntegratedAssessmentManager:
    """
    Gestor integral de assessments que proporciona una interfaz unificada para
    todos los tipos de evaluaciones disponibles en el sistema.
    
    Permite ejecutar assessments individuales o integrados, y generar reportes
    holísticos que combinen múltiples fuentes de datos.
    """
    
    def __init__(self, business_unit: str = None):
        """
        Inicializa el gestor de assessments.
        
        Args:
            business_unit: Unidad de negocio para contextualizar los assessments
        """
        self.business_unit = business_unit
        self.assessment_results = {}
        self.completed_assessments = set()
        
        # Inicializar analizadores centralizados
        self.personality_analyzer = PersonalityAnalyzer()
        self.cultural_analyzer = CulturalAnalyzer()
        self.professional_analyzer = ProfessionalAnalyzer()
        self.talent_analyzer = TalentAnalyzer()
        self.integrated_analyzer = IntegratedAnalyzer()
        
        # Cache para instancias de workflows
        self._workflow_instances = {}
        
    async def initialize_assessment(self, 
                                   assessment_type: Union[str, AssessmentType], 
                                   context: Dict[str, Any] = None) -> str:
        """
        Inicializa un flujo de assessment específico.
        
        Args:
            assessment_type: Tipo de assessment a inicializar
            context: Contexto inicial para el assessment
            
        Returns:
            Mensaje de bienvenida del assessment
        """
        if isinstance(assessment_type, str):
            try:
                assessment_type = AssessmentType(assessment_type)
            except ValueError:
                logger.error(f"Tipo de assessment inválido: {assessment_type}")
                return "Tipo de assessment inválido"
        
        # Preparar contexto base si no existe
        if context is None:
            context = {}
        
        # Asegurarse que el business_unit esté en el contexto
        if self.business_unit and 'business_unit' not in context:
            context['business_unit'] = self.business_unit
        
        # Inicializar el workflow específico
        workflow_instance = await self._get_workflow_instance(assessment_type, context)
        if not workflow_instance:
            return "No se pudo inicializar el assessment solicitado"
        
        # Inicializar el assessment
        welcome_message = await workflow_instance.initialize(context)
        return welcome_message
    
    async def process_assessment_message(self, 
                                        assessment_type: Union[str, AssessmentType], 
                                        message: str,
                                        message_type: str = 'text') -> str:
        """
        Procesa un mensaje dentro de un flujo de assessment específico.
        
        Args:
            assessment_type: Tipo de assessment
            message: Mensaje del usuario
            message_type: Tipo de mensaje (texto, imagen, etc.)
            
        Returns:
            Respuesta del sistema al mensaje
        """
        if isinstance(assessment_type, str):
            try:
                assessment_type = AssessmentType(assessment_type)
            except ValueError:
                logger.error(f"Tipo de assessment inválido: {assessment_type}")
                return "Tipo de assessment inválido"
        
        # Obtener el workflow correspondiente
        workflow_instance = await self._get_workflow_instance(assessment_type)
        if not workflow_instance:
            return "No se encontró un assessment activo del tipo solicitado"
        
        # Procesar el mensaje
        response = await workflow_instance.process_message(message, message_type)
        
        # Si el assessment ha finalizado, guardar resultados
        if workflow_instance.is_completed:
            self.completed_assessments.add(assessment_type.value)
            self.assessment_results[assessment_type.value] = workflow_instance.get_results()
            
            # Si hay suficientes assessments completados, generar análisis integrado
            if len(self.completed_assessments) >= 2:
                await self._update_integrated_analysis()
        
        return response
    
    async def get_assessment_results(self, 
                                    assessment_type: Union[str, AssessmentType] = None,
                                    format_type: str = 'json') -> Union[Dict, str]:
        """
        Obtiene los resultados de un assessment específico o todos si no se especifica.
        
        Args:
            assessment_type: Tipo de assessment o None para todos
            format_type: Formato de salida ('json', 'html', 'text')
            
        Returns:
            Resultados del assessment en el formato solicitado
        """
        # Si no se especifica tipo, devolver todos los resultados disponibles
        if assessment_type is None:
            results = self.assessment_results
        else:
            if isinstance(assessment_type, AssessmentType):
                assessment_type = assessment_type.value
                
            if assessment_type not in self.assessment_results:
                return {"error": "No se encontraron resultados para el tipo de assessment solicitado"}
            
            results = {assessment_type: self.assessment_results[assessment_type]}
        
        # Formatear resultados según el tipo solicitado
        if format_type == 'json':
            return results
        elif format_type == 'html':
            return self._format_results_as_html(results)
        elif format_type == 'text':
            return self._format_results_as_text(results)
        else:
            return {"error": f"Formato de salida no soportado: {format_type}"}
    
    async def generate_integrated_report(self, 
                                        person_id: str = None, 
                                        include_assessments: List[str] = None,
                                        report_format: str = 'html') -> Union[Dict, str]:
        """
        Genera un reporte integrado que combina los resultados de múltiples assessments.
        
        Args:
            person_id: ID de la persona para la que se genera el reporte
            include_assessments: Lista de assessments a incluir o None para todos
            report_format: Formato del reporte ('html', 'pdf', 'json')
            
        Returns:
            Reporte integrado en el formato solicitado
        """
        if not self.assessment_results:
            return {"error": "No hay resultados de assessments disponibles"}
        
        # Filtrar assessments a incluir
        results_to_include = {}
        if include_assessments:
            for assessment in include_assessments:
                if assessment in self.assessment_results:
                    results_to_include[assessment] = self.assessment_results[assessment]
        else:
            results_to_include = self.assessment_results
        
        # Si tenemos resultados integrados, usarlos como base
        if 'integrated' in self.assessment_results:
            integrated_results = self.assessment_results['integrated']
        else:
            # Realizar análisis integrado
            integrated_results = await self._perform_integrated_analysis(results_to_include)
        
        # Generar reporte según el formato solicitado
        if report_format == 'html':
            return await self._generate_html_report(integrated_results, person_id)
        elif report_format == 'pdf':
            return await self._generate_pdf_report(integrated_results, person_id)
        elif report_format == 'json':
            return integrated_results
        else:
            return {"error": f"Formato de reporte no soportado: {report_format}"}
    
    # Métodos privados
    
    async def _get_workflow_instance(self, 
                                    assessment_type: AssessmentType, 
                                    context: Dict[str, Any] = None) -> Any:
        """
        Obtiene o crea una instancia del workflow para el tipo de assessment solicitado.
        
        Args:
            assessment_type: Tipo de assessment
            context: Contexto para inicializar el workflow si es nuevo
            
        Returns:
            Instancia del workflow o None si no se puede crear
        """
        # Si ya tenemos una instancia, la devolvemos
        if assessment_type.value in self._workflow_instances:
            return self._workflow_instances[assessment_type.value]
        
        # Si no hay contexto, no podemos crear un nuevo workflow
        if context is None:
            logger.error(f"No se puede crear workflow sin contexto para: {assessment_type.value}")
            return None
        
        # Crear la instancia correspondiente
        try:
            if assessment_type == AssessmentType.PERSONALITY:
                workflow = PersonalityAssessment(context=context)
            elif assessment_type == AssessmentType.CULTURAL:
                workflow = CulturalFitWorkflow(context=context)
            elif assessment_type == AssessmentType.PROFESSIONAL:
                workflow = ProfessionalDNAWorkflow(context=context)
            elif assessment_type == AssessmentType.TALENT:
                workflow = TalentAnalysisWorkflow(context=context)
            elif assessment_type == AssessmentType.INTEGRATED:
                # Para integrated no tenemos un workflow específico
                return None
            else:
                logger.error(f"Tipo de assessment no implementado: {assessment_type.value}")
                return None
                
            # Guardar instancia para futuros usos
            self._workflow_instances[assessment_type.value] = workflow
            return workflow
            
        except Exception as e:
            logger.error(f"Error creando workflow para {assessment_type.value}: {str(e)}")
            return None
    
    async def _update_integrated_analysis(self) -> Dict:
        """
        Actualiza el análisis integrado con los resultados disponibles.
        
        Returns:
            Resultados del análisis integrado
        """
        # Verificar que tenemos suficientes assessments
        if len(self.completed_assessments) < 2:
            return {"error": "Se necesitan al menos dos assessments para realizar análisis integrado"}
        
        # Realizar análisis integrado
        integrated_results = await self._perform_integrated_analysis(self.assessment_results)
        
        # Guardar resultados
        self.assessment_results['integrated'] = integrated_results
        
        return integrated_results
    
    async def _perform_integrated_analysis(self, assessment_results: Dict) -> Dict:
        """
        Realiza un análisis integrado utilizando el IntegratedAnalyzer.
        
        Args:
            assessment_results: Resultados de assessments a integrar
            
        Returns:
            Resultados del análisis integrado
        """
        try:
            # Preparar datos para el analizador
            analysis_data = {
                'personality_results': assessment_results.get('personality', {}),
                'cultural_results': assessment_results.get('cultural', {}),
                'professional_results': assessment_results.get('professional', {}),
                'talent_results': assessment_results.get('talent', {})
            }
            
            # Realizar análisis integrado
            analyzer = self.integrated_analyzer
            result = await sync_to_async(analyzer.analyze)(analysis_data, self.business_unit)
            
            if result and not result.get('status') == 'error':
                logger.info("Análisis integrado completado exitosamente")
                return result
            else:
                logger.error(f"Error en análisis integrado: {result.get('message', 'Error desconocido')}")
                return {
                    "error": True,
                    "message": result.get('message', 'Error en análisis integrado'),
                    "partial_results": assessment_results
                }
                
        except Exception as e:
            logger.error(f"Error en _perform_integrated_analysis: {str(e)}")
            return {
                "error": True,
                "message": f"Error realizando análisis integrado: {str(e)}",
                "partial_results": assessment_results
            }
    
    def _format_results_as_html(self, results: Dict) -> str:
        """
        Formatea los resultados como HTML para presentación web.
        
        Args:
            results: Resultados a formatear
            
        Returns:
            Resultados formateados como HTML
        """
        # Template HTML básico - en producción se usaría un sistema de templates
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reporte de Assessments - Grupo huntRED®</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }
                .assessment-section { margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                h1, h2, h3 { color: #444; }
                .highlight { background-color: #f9f9f9; padding: 10px; border-left: 4px solid #7066e0; }
                .score-container { display: flex; align-items: center; margin: 10px 0; }
                .score-bar { height: 20px; background: #e0e0e0; border-radius: 10px; flex-grow: 1; overflow: hidden; }
                .score-fill { height: 100%; background: linear-gradient(90deg, #7066e0, #a496ff); }
                .recommendation { background-color: #f0f0f0; padding: 10px; margin: 5px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <header>
                <h1>Reporte de Assessments - Grupo huntRED®</h1>
                <p>Fecha: """ + timezone.now().strftime("%d/%m/%Y %H:%M") + """</p>
            </header>
            <main>
        """
        
        # Añadir cada assessment
        for assessment_type, assessment_data in results.items():
            html += f"""
            <section class="assessment-section">
                <h2>{self._get_assessment_title(assessment_type)}</h2>
            """
            
            # Formatear según el tipo de assessment
            if assessment_type == 'personality':
                html += self._format_personality_html(assessment_data)
            elif assessment_type == 'cultural':
                html += self._format_cultural_html(assessment_data)
            elif assessment_type == 'professional':
                html += self._format_professional_html(assessment_data)
            elif assessment_type == 'talent':
                html += self._format_talent_html(assessment_data)
            elif assessment_type == 'integrated':
                html += self._format_integrated_html(assessment_data)
            else:
                # Formato genérico para otros tipos
                html += f"<pre>{json.dumps(assessment_data, indent=2)}</pre>"
                
            html += """
            </section>
            """
        
        # Cerrar el HTML
        html += """
            </main>
            <footer>
                <p>© """ + str(timezone.now().year) + """ Grupo huntRED® - Todos los derechos reservados</p>
            </footer>
        </body>
        </html>
        """
        
        return html
    
    def _format_results_as_text(self, results: Dict) -> str:
        """
        Formatea los resultados como texto plano.
        
        Args:
            results: Resultados a formatear
            
        Returns:
            Resultados formateados como texto
        """
        text = "REPORTE DE ASSESSMENTS - GRUPO HUNTRED®\n"
        text += f"Fecha: {timezone.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        
        for assessment_type, assessment_data in results.items():
            text += f"{self._get_assessment_title(assessment_type).upper()}\n"
            text += "=" * len(self._get_assessment_title(assessment_type)) + "\n\n"
            
            # Formatear según el tipo de assessment
            if assessment_type == 'personality':
                text += self._format_personality_text(assessment_data)
            elif assessment_type == 'cultural':
                text += self._format_cultural_text(assessment_data)
            elif assessment_type == 'professional':
                text += self._format_professional_text(assessment_data)
            elif assessment_type == 'talent':
                text += self._format_talent_text(assessment_data)
            elif assessment_type == 'integrated':
                text += self._format_integrated_text(assessment_data)
            else:
                # Formato genérico para otros tipos
                text += json.dumps(assessment_data, indent=2) + "\n"
                
            text += "\n\n"
        
        text += "© " + str(timezone.now().year) + " Grupo huntRED® - Todos los derechos reservados"
        
        return text
    
    def _get_assessment_title(self, assessment_type: str) -> str:
        """
        Obtiene el título legible para un tipo de assessment.
        
        Args:
            assessment_type: Tipo de assessment
            
        Returns:
            Título legible
        """
        titles = {
            'personality': 'Análisis de Personalidad',
            'cultural': 'Análisis de Compatibilidad Cultural',
            'professional': 'Análisis de ADN Profesional',
            'talent': 'Análisis de Talento',
            'integrated': 'Análisis Integrado'
        }
        
        return titles.get(assessment_type, f'Assessment: {assessment_type}')
    
    # Métodos de formateo específicos para cada tipo de assessment
    # (Estos métodos se implementarían con el formato específico para cada tipo)
    
    def _format_personality_html(self, data: Dict) -> str:
        """Formatea resultados de personalidad como HTML"""
        # Implementación básica, se expandiría según necesidades
        html = ""
        if 'traits' in data:
            html += "<h3>Rasgos de Personalidad</h3><ul>"
            for trait, value in data.get('traits', {}).items():
                score = int(value * 100) if isinstance(value, float) else value
                html += f"""
                <li>
                    <strong>{trait.replace('_', ' ').title()}</strong>
                    <div class="score-container">
                        <div class="score-bar">
                            <div class="score-fill" style="width: {score}%;"></div>
                        </div>
                        <span style="margin-left: 10px;">{score}%</span>
                    </div>
                </li>
                """
            html += "</ul>"
            
        if 'insights' in data:
            html += "<h3>Insights</h3><ul>"
            for insight in data.get('insights', []):
                html += f"<li>{insight}</li>"
            html += "</ul>"
            
        if 'recommendations' in data:
            html += "<h3>Recomendaciones</h3>"
            for rec in data.get('recommendations', []):
                html += f'<div class="recommendation">{rec}</div>'
                
        return html
    
    def _format_cultural_html(self, data: Dict) -> str:
        """Formatea resultados culturales como HTML"""
        # Implementación similar a personalidad
        return self._format_generic_html(data)
    
    def _format_professional_html(self, data: Dict) -> str:
        """Formatea resultados profesionales como HTML"""
        return self._format_generic_html(data)
    
    def _format_talent_html(self, data: Dict) -> str:
        """Formatea resultados de talento como HTML"""
        return self._format_generic_html(data)
    
    def _format_integrated_html(self, data: Dict) -> str:
        """Formatea resultados integrados como HTML"""
        return self._format_generic_html(data)
    
    def _format_generic_html(self, data: Dict) -> str:
        """Formato genérico para datos que no tienen formato específico"""
        html = ""
        
        # Procesar fortalezas si existen
        if 'strengths' in data:
            html += "<h3>Fortalezas</h3><ul>"
            for strength in data.get('strengths', []):
                html += f"<li>{strength}</li>"
            html += "</ul>"
        
        # Procesar áreas de mejora
        improvement_keys = ['areas_for_improvement', 'development_areas', 'gaps']
        for key in improvement_keys:
            if key in data:
                html += "<h3>Áreas de Desarrollo</h3><ul>"
                for area in data.get(key, []):
                    if isinstance(area, dict) and 'name' in area:
                        html += f"<li>{area['name']}</li>"
                    else:
                        html += f"<li>{area}</li>"
                html += "</ul>"
                break
        
        # Procesar recomendaciones
        if 'recommendations' in data:
            html += "<h3>Recomendaciones</h3>"
            for rec in data.get('recommendations', []):
                if isinstance(rec, dict) and 'text' in rec:
                    html += f'<div class="recommendation">{rec["text"]}</div>'
                else:
                    html += f'<div class="recommendation">{rec}</div>'
        
        # Puntajes
        score_keys = ['scores', 'values', 'dimensions', 'category_scores']
        for key in score_keys:
            if key in data and isinstance(data[key], dict):
                html += f"<h3>{key.replace('_', ' ').title()}</h3>"
                html += "<ul>"
                for name, value in data[key].items():
                    score = int(value * 100) if isinstance(value, float) else value
                    html += f"""
                    <li>
                        <strong>{name.replace('_', ' ').title()}</strong>
                        <div class="score-container">
                            <div class="score-bar">
                                <div class="score-fill" style="width: {score}%;"></div>
                            </div>
                            <span style="margin-left: 10px;">{score}%</span>
                        </div>
                    </li>
                    """
                html += "</ul>"
        
        return html
    
    # Implementaciones de texto plano (simplificadas)
    
    def _format_personality_text(self, data: Dict) -> str:
        """Formatea resultados de personalidad como texto"""
        text = ""
        if 'traits' in data:
            text += "RASGOS DE PERSONALIDAD\n"
            for trait, value in data.get('traits', {}).items():
                score = int(value * 100) if isinstance(value, float) else value
                text += f"- {trait.replace('_', ' ').title()}: {score}%\n"
            text += "\n"
            
        if 'insights' in data:
            text += "INSIGHTS\n"
            for insight in data.get('insights', []):
                text += f"- {insight}\n"
            text += "\n"
            
        if 'recommendations' in data:
            text += "RECOMENDACIONES\n"
            for rec in data.get('recommendations', []):
                text += f"- {rec}\n"
                
        return text
    
    def _format_cultural_text(self, data: Dict) -> str:
        """Formatea resultados culturales como texto"""
        return self._format_generic_text(data)
    
    def _format_professional_text(self, data: Dict) -> str:
        """Formatea resultados profesionales como texto"""
        return self._format_generic_text(data)
    
    def _format_talent_text(self, data: Dict) -> str:
        """Formatea resultados de talento como texto"""
        return self._format_generic_text(data)
    
    def _format_integrated_text(self, data: Dict) -> str:
        """Formatea resultados integrados como texto"""
        return self._format_generic_text(data)
    
    def _format_generic_text(self, data: Dict) -> str:
        """Formato genérico para datos que no tienen formato específico"""
        text = ""
        
        # Procesar fortalezas
        if 'strengths' in data:
            text += "FORTALEZAS\n"
            for strength in data.get('strengths', []):
                text += f"- {strength}\n"
            text += "\n"
        
        # Procesar áreas de mejora
        improvement_keys = ['areas_for_improvement', 'development_areas', 'gaps']
        for key in improvement_keys:
            if key in data:
                text += "ÁREAS DE DESARROLLO\n"
                for area in data.get(key, []):
                    if isinstance(area, dict) and 'name' in area:
                        text += f"- {area['name']}\n"
                    else:
                        text += f"- {area}\n"
                text += "\n"
                break
        
        # Procesar recomendaciones
        if 'recommendations' in data:
            text += "RECOMENDACIONES\n"
            for rec in data.get('recommendations', []):
                if isinstance(rec, dict) and 'text' in rec:
                    text += f"- {rec['text']}\n"
                else:
                    text += f"- {rec}\n"
            text += "\n"
        
        # Puntajes
        score_keys = ['scores', 'values', 'dimensions', 'category_scores']
        for key in score_keys:
            if key in data and isinstance(data[key], dict):
                text += f"{key.replace('_', ' ').upper()}\n"
                for name, value in data[key].items():
                    score = int(value * 100) if isinstance(value, float) else value
                    text += f"- {name.replace('_', ' ').title()}: {score}%\n"
                text += "\n"
        
        return text
    
    async def _generate_html_report(self, data: Dict, person_id: str = None) -> str:
        """
        Genera un reporte HTML completo con los resultados integrados.
        
        Args:
            data: Datos del análisis integrado
            person_id: ID de la persona para la que se genera el reporte
            
        Returns:
            Reporte HTML
        """
        # En una implementación real, aquí se usaría un sistema de templates
        # y se integraría con datos de la persona si person_id es proporcionado
        
        return self._format_results_as_html({'integrated': data})
    
    async def _generate_pdf_report(self, data: Dict, person_id: str = None) -> Dict:
        """
        Genera un reporte PDF con los resultados integrados.
        
        Args:
            data: Datos del análisis integrado
            person_id: ID de la persona para la que se genera el reporte
            
        Returns:
            Información del PDF generado
        """
        # En una implementación real, aquí se generaría un PDF utilizando
        # una biblioteca como weasyprint o reportlab
        
        # Por ahora, simulamos la generación
        return {
            "status": "success",
            "message": "PDF generado exitosamente",
            "filename": f"integrated_report_{person_id or 'anonymous'}_{timezone.now().strftime('%Y%m%d%H%M%S')}.pdf",
            "size": "2.1 MB",
            "download_url": f"/reports/download/pdf/{person_id or 'anonymous'}/{timezone.now().strftime('%Y%m%d%H%M%S')}"
        }
