# /home/pablo/app/ats/utils/cv_generator/cv_generator.py
"""
Sistema de generación de CVs para Grupo huntRED®

Este módulo proporciona funcionalidad para generar CVs en diferentes formatos,
con capacidades básicas y avanzadas.

Incluye dos clases principales:
- CVGenerator: Funcionalidad básica de generación de CV
- EnhancedCVGenerator: Versión avanzada con análisis de carrera y valores integrados
"""
import os
import logging
import asyncio
from typing import Dict, List, Union, Any, Optional, Tuple
from datetime import datetime

from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
import tempfile

from app.ats.utils.cv_generator.cv_template import CVTemplate
from app.ats.utils.cv_generator.cv_utils import CVUtils
from app.ats.utils.cv_generator.cv_data import CVData
from app.ats.utils.cv_generator.career_analyzer import career_analyzer, CVCareerAnalyzer
from app.ats.chatbot.values.core import ValuesPrinciples
from app.ml.core.models.base import MatchmakingLearningSystem
# Importamos las funciones adaptadoras de career_analyzer
from app.ats.utils.cv_generator.career_analyzer import calculate_match_percentage, calculate_alignment_percentage
from app.ats.utils.cv_generator.values_adapter import CVValuesAdapter as ValuesAdapter
from app.ats.kanban.ml_integration import get_candidate_growth_data

logger = logging.getLogger(__name__)

# Deshabilitar WeasyPrint durante las migraciones
WEASYPRINT_AVAILABLE = False

class CVGenerator:
    """
    Generates PDF CVs from candidate data.
    """
    
    def __init__(self, template: str = 'modern', include_growth_plan: bool = False):
        """
        Initialize the CVGenerator.
        
        Args:
            template: The template to use for the CV
            include_growth_plan: Whether to include a professional development plan
        """
        self.template = CVTemplate(template)
        self.utils = CVUtils()
        self.include_growth_plan = include_growth_plan
    
    def _prepare_blind_data(self, cv_data: CVData) -> Dict:
        """
        Prepare data for blind CV generation.
        
        Args:
            cv_data: CVData object containing candidate information
            
        Returns:
            Dictionary with blind CV data
        """
        # Convert to dictionary
        data = cv_data.__dict__.copy()
        
        # Generate blind identifier
        data['blind_identifier'] = cv_data.get_blind_identifier()
        
        # Remove sensitive information
        data.pop('contact_info', None)
        data.pop('name', None)
        
        # Remove company names from experience
        if 'experience' in data:
            for exp in data['experience']:
                exp.pop('company', None)
                
        # Remove business unit information
        data.pop('business_unit', None)
        data.pop('business_unit_logo', None)
        
        return data
    
    def generate_cv(self, candidate_data: Union[Dict, CVData], language: str = 'es', blind: bool = False) -> bytes:
        """
        Generate a PDF CV from candidate data.
        
        Args:
            candidate_data: Dictionary or CVData object containing candidate information
            language: Language for the CV (es or en)
            blind: If True, generate a blind CV without personal information
            
        Returns:
            Bytes of the generated PDF
        """
        # Convert to CVData if it's a dictionary
        if isinstance(candidate_data, dict):
            candidate_data = CVData(**candidate_data)
        
        # Set language and dates
        candidate_data.language = language
        candidate_data.cv_creation_date = datetime.now()
        if not hasattr(candidate_data, 'ml_analysis_date') or not candidate_data.ml_analysis_date:
            candidate_data.ml_analysis_date = datetime.now()
        
        # Prepare data for template - use translated data if available
        if hasattr(candidate_data, 'get_translated_data'):
            template_data = candidate_data.get_translated_data()
        else:
            template_data = candidate_data.__dict__.copy()
            
        # If blind CV requested, prepare blind data
        if blind:
            template_data = self._prepare_blind_data(candidate_data)
        
        # Validate and clean data
        cleaned_data = self.utils.clean_candidate_data(template_data)
        
        # Add visual elements if available and not a blind CV
        if not blind:
            if hasattr(cleaned_data, 'get'):
                if cleaned_data.get('personality_test') and hasattr(cleaned_data['personality_test'], 'get_personality_chart'):
                    cleaned_data['personality_chart'] = cleaned_data['personality_test'].get_personality_chart()
                
                if cleaned_data.get('values_alignment') and hasattr(cleaned_data['values_alignment'], 'get_values_chart'):
                    cleaned_data['values_chart'] = cleaned_data['values_alignment'].get_values_chart()
        
        # Render template to HTML
        html_string = self.template.render(cleaned_data)
        
        # Generate PDF from HTML
        try:
            from weasyprint import HTML
            return HTML(string=html_string).write_pdf()
        except ImportError:
            logger.warning("WeasyPrint no está disponible. Se devuelve el HTML como bytes.")
            return html_string.encode('utf-8')
        
    def generate_multiple_cvs(self, candidates_data: List[Union[Dict, CVData]], language: str = 'es', blind: bool = False) -> List[bytes]:
        """
        Generate multiple PDF CVs from a list of candidates.
        
        Args:
            candidates_data: List of dictionaries or CVData objects containing candidate information
            language: Language for the CVs (es or en)
            blind: If True, generates blind CVs without contact information
            
        Returns:
            List of bytes for each generated PDF
        """
        return [self.generate_cv(candidate_data, language, blind) 
                for candidate_data in candidates_data]
    
    def save_cv(self, candidate_data: Union[Dict, CVData], output_path: str, language: str = 'es', blind: bool = False, include_growth_plan: bool = None) -> str:
        """
        Generate and save a CV to a file. Optionally includes a development plan.
        
        Args:
            candidate_data: Dictionary or CVData object containing candidate information
            output_path: Path where to save the PDF
            language: Language for the CV (es or en)
            blind: If True, generates a blind CV without contact information
            include_growth_plan: Override for class setting on including growth plan
            
        Returns:
            Path to the saved PDF file
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate CV
        pdf_bytes = self.generate_cv(candidate_data, language, blind)
        
        # Save to file
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
            
        # Determine if growth plan should be included
        should_include_plan = include_growth_plan if include_growth_plan is not None else self.include_growth_plan
        
        # If development plan is enabled and ML features are active, add it
        if should_include_plan and getattr(settings, 'ENABLE_ML_FEATURES', False):
            try:
                # Get candidate Person object from candidate_data
                person = None
                if isinstance(candidate_data, CVData) and hasattr(candidate_data, 'get_person_object'):
                    person = candidate_data.get_person_object()
                elif isinstance(candidate_data, dict) and 'id' in candidate_data:
                    from app.models import Person
                    try:
                        person = Person.objects.get(id=candidate_data['id'])
                    except Person.DoesNotExist:
                        pass
                
                if person:
                    # Generate development plan
                    plan_path = self._generate_development_plan(person, output_path)
                    if plan_path:
                        # Merge the PDFs (CV and development plan)
                        merged_path = self._merge_pdfs(output_path, plan_path, output_path)
                        return merged_path
            except Exception as e:
                logger.error(f"Error adding development plan to CV: {str(e)}")
        
        return output_path
    
    def _generate_development_plan(self, person, output_base_path: str) -> Optional[str]:
        """
        Generate a professional development plan PDF.
        
        Args:
            person: Person object for whom to generate the plan
            output_base_path: Base path for output file
            
        Returns:
            Path to the generated plan PDF, or None if generation failed
        """
        try:
            # Determine output path for the plan
            plan_filename = f"development_plan_{person.id}.pdf"
            plan_path = os.path.join(os.path.dirname(output_base_path), plan_filename)
            
            # Get development plan data for candidate audience
            growth_data = get_candidate_growth_data(person, audience_type='candidate')
            
            # Render template to HTML
            html_string = render_to_string('ml/candidate/growth_plan.html', {
                'candidate': growth_data,
                'for_pdf': True,
                'for_candidate': True,
                'timestamp': self.utils.get_current_date()
            })
            
            # Generate PDF
            HTML(string=html_string).write_pdf(plan_path)
            
            return plan_path
        except Exception as e:
            logger.error(f"Error generating development plan PDF: {str(e)}")
            return None
    
    def _merge_pdfs(self, cv_path: str, plan_path: str, output_base_path: str) -> str:
        """
        Merge CV and development plan PDFs.
        
        Args:
            cv_path: Path to CV PDF
            plan_path: Path to development plan PDF
            output_base_path: Base path for output file
            
        Returns:
            Path to merged PDF
        """
        try:
            from PyPDF2 import PdfMerger
            
            # Create merger object
            merger = PdfMerger()
            
            # Add the PDFs to the merger
            merger.append(cv_path)
            merger.append(plan_path)
            
            # Generate output path for merged file
            merged_filename = os.path.basename(output_base_path).replace('.pdf', '_with_plan.pdf')
            merged_path = os.path.join(os.path.dirname(output_base_path), merged_filename)
            
            # Write to output file
            with open(merged_path, 'wb') as output_file:
                merger.write(output_file)
            
            return merged_path
        except Exception as e:
            logger.error(f"Error merging PDFs: {str(e)}")
            # Return original CV path if merging fails
            return cv_path


class EnhancedCVGenerator(CVGenerator):
    """
    Genera CVs mejorados con análisis de carrera y valores integrados.
    """
    
    def __init__(self, template: str = 'modern', include_growth_plan: bool = False):
        """
        Inicializa el EnhancedCVGenerator.
        
        Args:
            template: Plantilla a utilizar
            include_growth_plan: Si se debe incluir plan de desarrollo profesional
        """
        super().__init__(template, include_growth_plan)
        self.career_analyzer = CVCareerAnalyzer()
        self.values_adapter = ValuesAdapter()
        self.reference_processor = None  # Se inicializará con la business_unit
    
    async def _enrich_candidate_data(self, person: Dict, career_analysis: Dict, 
                               ml_insights: Dict) -> Dict:
        """
        Enriquece los datos del candidato con análisis y valores.
        """
        enriched_data = {}
        
        # Datos básicos
        enriched_data['name'] = f"{person.first_name} {person.last_name}"
        enriched_data['contact_info'] = {
            'email': person.email,
            'phone': person.phone,
            'address': person.address if hasattr(person, 'address') else None
        }
        
        # Añadir resumen
        enriched_data['summary'] = person.professional_summary if hasattr(person, 'professional_summary') else ""
        
        # Procesar experiencia, educación, habilidades
        enriched_data['experience'] = self._process_experience(career_analysis.get('experience', []))
        enriched_data['education'] = self._process_education(career_analysis.get('education', []))
        enriched_data['skills'] = self._process_skills(person.skills if hasattr(person, 'skills') else "", ml_insights)
        
        # Añadir idiomas
        enriched_data['languages'] = self._process_languages(career_analysis.get('languages', []))
        
        # Procesar referencias según el tipo de audiencia
        if self.reference_processor:
            enriched_data['references'] = await self.reference_processor.process_references_for_cv(
                person,
                self.audience_type
            )
        
        # Añadir insights de ML
        if ml_insights:
            enriched_data['personality_insights'] = ml_insights.get('personality', {})
            enriched_data['talent_insights'] = ml_insights.get('talent', {})
            enriched_data['cultural_insights'] = ml_insights.get('cultural', {})
            
            # Roles recomendados basados en análisis de ML
            if 'talent' in ml_insights and 'success_probabilities' in ml_insights['talent']:
                enriched_data['recommended_roles'] = self._get_top_roles(
                    ml_insights['talent']['success_probabilities']
                )
        
        # Añadir fecha de análisis
        enriched_data['ml_analysis_date'] = datetime.now()
        
        return enriched_data
    
    async def generate_enhanced_cv(self, candidate_data: Union[Dict, CVData], 
                                  business_unit: str,
                                  output_path: str, 
                                  audience_type: str = 'client',
                                  language: str = 'es',
                                  blind: bool = False) -> str:
        """
        Genera un CV mejorado con análisis de carrera y valores integrados.
        
        Args:
            candidate_data: Datos del candidato (diccionario o CVData)
            business_unit: Unidad de negocio
            output_path: Ruta donde guardar el PDF
            audience_type: Tipo de audiencia ('client', 'candidate', 'consultant')
            language: Idioma del CV ('es' o 'en')
            blind: Si es True, genera un CV ciego sin información personal
            
        Returns:
            Ruta al archivo PDF generado
        """
        try:
            # Convertir a CVData si es un diccionario
            if isinstance(candidate_data, dict):
                candidate_data = CVData(**candidate_data)
            
            # Obtener ID del candidato
            candidate_id = self._extract_candidate_id(candidate_data)
            if not candidate_id:
                logger.warning("No se pudo extraer ID del candidato. Generando CV sin análisis avanzado.")
                return await self._generate_basic_cv(candidate_data, output_path, language, blind)
            
            # Obtener datos básicos del candidato
            person = await self._get_person(candidate_id)
            if not person:
                raise ValueError(f"No se encontró la persona con ID {candidate_id}")
            
            # Inicializar procesador de referencias
            from app.ats.utils.cv_generator.reference_processor import ReferenceProcessor
            self.reference_processor = ReferenceProcessor(business_unit)
            self.audience_type = audience_type
            
            # Obtener análisis de carrera y ML en paralelo
            career_analysis, ml_insights = await asyncio.gather(
                self.career_analyzer.analyze_career(person),
                self._get_ml_insights(person)
            )
            
            # Enriquecer datos con análisis
            enriched_data = await self._enrich_candidate_data(person, career_analysis, ml_insights)
            
            # Añadir información original del CV
            for key, value in candidate_data.__dict__.items():
                if key not in enriched_data and key != 'business_unit':
                    enriched_data[key] = value
            
            # Asignar unidad de negocio
            enriched_data['business_unit'] = business_unit
            
            # Generar CV con datos enriquecidos
            return await self._generate_cv_with_enriched_data(
                enriched_data, 
                output_path, 
                language, 
                blind, 
                audience_type
            )
            
        except Exception as e:
            logger.error(f"Error generando CV mejorado: {str(e)}")
            # Fallback a CV básico en caso de error
            return await self._generate_basic_cv(candidate_data, output_path, language, blind)
    
    async def _generate_basic_cv(self, candidate_data, output_path, language, blind):
        """Genera un CV básico sin análisis avanzado."""
        return self.save_cv(candidate_data, output_path, language, blind)
    
    async def _generate_cv_with_enriched_data(self, enriched_data, output_path, 
                                         language, blind, audience_type):
        """Genera CV utilizando datos enriquecidos."""
        # Seleccionar template según audiencia
        template_map = {
            'client': self.template.name,
            'candidate': 'candidate',
            'consultant': 'detailed',
            'blind': 'blind'
        }
        template_name = template_map.get(audience_type, self.template.name)
        
        # Guardar template original
        original_template = self.template.name
        
        try:
            # Cambiar template si es necesario
            if template_name != original_template:
                from app.ats.utils.cv_generator.cv_template import CVTemplate
                self.template = CVTemplate(template_name)
            
            # Usar la implementación original con datos enriquecidos
            return self.save_cv(enriched_data, output_path, language, blind)
        except Exception as e:
            logger.error(f"Error generando CV con datos enriquecidos: {str(e)}")
            return None
        finally:
            # Restaurar template original
            if template_name != original_template:
                from app.ats.utils.cv_generator.cv_template import CVTemplate
                self.template = CVTemplate(original_template)
    
    def _extract_candidate_id(self, cv_data):
        """
        Extrae el ID del candidato de los datos del CV.
        """
        try:
            # Intentar obtener ID de diferentes formas
            if hasattr(cv_data, 'id') and cv_data.id:
                return cv_data.id
                
            if hasattr(cv_data, 'person_id') and cv_data.person_id:
                return cv_data.person_id
                
            if hasattr(cv_data, 'candidate_id') and cv_data.candidate_id:
                return cv_data.candidate_id
                
            # Buscar en atributos anidados
            if hasattr(cv_data, 'personal_info'):
                personal_info = cv_data.personal_info
                if isinstance(personal_info, dict) and 'id' in personal_info:
                    return personal_info['id']
                    
            return None
        except Exception as e:
            logger.error(f"Error extrayendo ID del candidato: {str(e)}")
            return None
    
    async def _get_person(self, person_id: int):
        """
        Obtiene los datos de la persona.
        """
        from app.models import Person
        try:
            from asgiref.sync import sync_to_async
            return await sync_to_async(Person.objects.get)(id=person_id)
        except Exception as e:
            logger.error(f"Error obteniendo persona: {str(e)}")
            return None
    
    async def _get_ml_insights(self, person):
        """
        Obtiene insights del sistema ML.
        """
        try:
            # Obtener insights del sistema ML
            from app.ml.personality_analyzer import get_personality_insights
            from app.ml.talent_analyzer import get_talent_insights
            from app.ml.cultural_analyzer import get_cultural_insights
            
            # Ejecutar análisis en paralelo
            personality_insights, talent_insights, cultural_insights = await asyncio.gather(
                sync_to_async(get_personality_insights)(person),
                sync_to_async(get_talent_insights)(person),
                sync_to_async(get_cultural_insights)(person)
            )
            
            return {
                'personality': personality_insights,
                'talent': talent_insights,
                'cultural': cultural_insights
            }
        except Exception as e:
            logger.error(f"Error obteniendo insights ML: {str(e)}")
            return {}
    
    def _process_skills(self, skills: str, ml_insights: Dict) -> List[Dict]:
        """
        Procesa las habilidades con información de ML.
        """
        try:
            # Dividir habilidades por coma si es un string
            if isinstance(skills, str):
                skill_list = [s.strip() for s in skills.split(',') if s.strip()]
            elif isinstance(skills, list):
                skill_list = skills
            else:
                skill_list = []
                
            # Obtener niveles de habilidad de insights ML si están disponibles
            skill_levels = {}
            if 'talent' in ml_insights and 'skill_levels' in ml_insights['talent']:
                skill_levels = ml_insights['talent']['skill_levels']
                
            # Crear lista de habilidades con niveles
            processed_skills = []
            for skill in skill_list:
                skill_info = {
                    'name': skill,
                    'level': skill_levels.get(skill.lower(), 0.7),  # Nivel por defecto si no está disponible
                    'years': self._get_skill_experience(skill)
                }
                processed_skills.append(skill_info)
                
            return processed_skills
        except Exception as e:
            logger.error(f"Error procesando habilidades: {str(e)}")
            return []
    
    def _get_skill_experience(self, skill: str):
        """
        Obtiene años de experiencia en una habilidad.
        """
        return 0  # En una implementación real, esto se calcularía de la experiencia laboral
    
    def _get_top_roles(self, success_probabilities: List[Dict]):
        """
        Obtiene los roles con mayor probabilidad de éxito.
        """
        try:
            if not success_probabilities:
                return []
                
            # Ordenar por probabilidad de éxito
            sorted_roles = sorted(success_probabilities, 
                                 key=lambda x: x.get('probability', 0), 
                                 reverse=True)
                                 
            # Seleccionar los 3 roles principales
            top_roles = sorted_roles[:3]
            
            # Formatear para presentación
            formatted_roles = []
            for role in top_roles:
                probability = role.get('probability', 0)
                formatted_roles.append({
                    'role': role.get('role', ''),
                    'probability': probability,
                    'probability_percentage': int(probability * 100),
                    'description': role.get('description', ''),
                    'match_level': self._get_match_level(probability)
                })
                
            return formatted_roles
        except Exception as e:
            logger.error(f"Error obteniendo roles top: {str(e)}")
            return []
    
    def _get_match_level(self, probability: float) -> str:
        """
        Determina el nivel de match basado en la probabilidad.
        """
        if probability >= 0.85:
            return "Excelente"
        elif probability >= 0.70:
            return "Muy bueno"
        elif probability >= 0.60:
            return "Bueno" 
        else:
            return "Moderado"
    
    def _process_experience(self, experience: List[Dict]) -> List[Dict]:
        """Procesa la experiencia laboral."""
        try:
            if not experience:
                return []
            
            return [
                {
                    "position": exp.get("position", ""),
                    "company": exp.get("company", ""),
                    "start_date": exp.get("start_date", ""),
                    "end_date": exp.get("end_date", ""),
                    "description": exp.get("description", ""),
                    "achievements": exp.get("achievements", [])
                }
                for exp in experience
            ]
        except Exception as e:
            logger.error(f"Error procesando experiencia: {str(e)}")
            return []
    
    def _process_education(self, education: List[Dict]) -> List[Dict]:
        """Procesa la educación."""
        try:
            if not education:
                return []
            
            return [
                {
                    "degree": edu.get("degree", ""),
                    "institution": edu.get("institution", ""),
                    "field_of_study": edu.get("field_of_study", ""),
                    "start_date": edu.get("start_date", ""),
                    "end_date": edu.get("end_date", ""),
                    "grade": edu.get("grade", ""),
                    "description": edu.get("description", "")
                }
                for edu in education
            ]
        except Exception as e:
            logger.error(f"Error procesando educación: {str(e)}")
            return []
    
    def _process_languages(self, languages: List[Dict]) -> List[Dict]:
        """Procesa los idiomas."""
        try:
            if not languages:
                return []
            
            return [
                {
                    "language": lang.get("language", ""),
                    "level": lang.get("level", ""),
                    "level_percentage": lang.get("level_percentage", 50),
                    "certificate": lang.get("certificate", "")
                }
                for lang in languages
            ]
        except Exception as e:
            logger.error(f"Error procesando idiomas: {str(e)}")
            return []
    
    async def _generate_cv_data(self, enriched_data: Dict, template: str) -> Dict[str, Any]:
        """Genera los datos finales del CV."""
        try:
            return {
                "template": template,
                "data": enriched_data,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "version": "3.0",
                    "analysis_version": "2.0"
                }
            }
        except Exception as e:
            logger.error(f"Error generando datos del CV: {str(e)}")
            raise


# Función de conveniencia para generar CV mejorado
async def generate_enhanced_cv(
    candidate_data: Union[Dict, CVData],
    business_unit: str,
    output_path: str,
    audience_type: str = 'client',
    language: str = 'es',
    blind: bool = False,
    template: str = 'modern'
) -> str:
    """
    Genera un CV mejorado con análisis de carrera y valores integrados.
    
    Args:
        candidate_data: Datos del candidato (diccionario o CVData)
        business_unit: Unidad de negocio
        output_path: Ruta donde guardar el PDF
        audience_type: Tipo de audiencia ('client', 'candidate', 'consultant')
        language: Idioma del CV ('es' o 'en')
        blind: Si es True, genera un CV ciego sin información personal
        template: Plantilla a utilizar
        
    Returns:
        Ruta al archivo PDF generado
    """
    generator = EnhancedCVGenerator(template=template, include_growth_plan=True)
    return await generator.generate_enhanced_cv(
        candidate_data, 
        business_unit,
        output_path, 
        audience_type,
        language, 
        blind
    )


# Función de conveniencia para generar CV básico
def generate_cv(
    candidate_data: Union[Dict, CVData],
    output_path: str,
    language: str = 'es',
    blind: bool = False,
    template: str = 'modern',
    include_growth_plan: bool = False
) -> str:
    """
    Genera un CV básico.
    
    Args:
        candidate_data: Datos del candidato (diccionario o CVData)
        output_path: Ruta donde guardar el PDF
        language: Idioma del CV ('es' o 'en')
        blind: Si es True, genera un CV ciego sin información personal
        template: Plantilla a utilizar
        include_growth_plan: Si se debe incluir plan de desarrollo profesional
        
    Returns:
        Ruta al archivo PDF generado
    """
    generator = CVGenerator(template=template, include_growth_plan=include_growth_plan)
    return generator.save_cv(
        candidate_data, 
        output_path, 
        language, 
        blind
    )
