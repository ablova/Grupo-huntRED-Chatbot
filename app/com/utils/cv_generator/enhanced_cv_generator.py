# /home/pablo/app/com/utils/cv_generator/enhanced_cv_generator.py
"""
Generador mejorado de CVs con análisis de carrera y valores integrados.

Este módulo extiende las capacidades del generador de CVs tradicional integrando:
1. Análisis de carrera avanzado (potencial, habilidades críticas, plan de desarrollo)
2. Mensajes personalizados basados en valores (apoyo, solidaridad, sinergia)
3. Visualizaciones mejoradas de trayectoria profesional
4. Diferentes vistas según audiencia (cliente, candidato, consultor)

Mantiene compatibilidad con la estructura existente y mejora la experiencia.
"""

import os
import logging
import asyncio
from typing import Dict, List, Union, Any, Optional
from datetime import datetime

from django.conf import settings
from django.template.loader import render_to_string

from app.com.utils.cv_generator.cv_generator import CVGenerator
from app.com.utils.cv_generator.cv_data import CVData
from app.com.utils.cv_generator.career_analyzer import career_analyzer, CVCareerAnalyzer
from app.com.chatbot.core.values import ValuesPrinciples
from app.ml.ml_model import MatchmakingLearningSystem
from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage
from app.com.utils.cv_generator.values_adapter import ValuesAdapter

logger = logging.getLogger(__name__)

class EnhancedCVGenerator(CVGenerator):
    """
    Generador mejorado de CVs que integra análisis de carrera y valores.
    """
    
    def __init__(self, template: str = 'modern', include_growth_plan: bool = True, 
                 integration_level: str = 'enhanced'):
        """
        Inicializa el generador de CVs mejorado.
        
        Args:
            template: Plantilla a utilizar para el CV
            include_growth_plan: Si se debe incluir plan de desarrollo profesional
            integration_level: Nivel de integración de valores ('basic', 'enhanced', 'full')
        """
        super().__init__(template, include_growth_plan)
        self.integration_level = integration_level
        self.values_principles = ValuesPrinciples()
        self.career_analyzer = CVCareerAnalyzer()
        self.ml_system = MatchmakingLearningSystem()
        self.values_adapter = ValuesAdapter()
    
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
            
            # Obtener análisis de carrera y ML en paralelo
            career_analysis, ml_insights = await asyncio.gather(
                self.career_analyzer.analyze_career_potential(candidate_id),
                self._get_ml_insights(person)
            )
            
            # Enriquecer datos del candidato
            enriched_data = await self._enrich_candidate_data(person, career_analysis, ml_insights)
            
            # Generar CV con datos enriquecidos
            cv_data = await self._generate_cv_data(enriched_data, self.template.name)
            
            # Generar CV utilizando la funcionalidad base
            cv_path = await self._generate_cv_with_enriched_data(
                cv_data, output_path, language, blind, audience_type
            )
            
            return cv_path
        except Exception as e:
            logger.error(f"Error generando CV mejorado: {str(e)}")
            # Fallback a generación básica
            return await self._generate_basic_cv(candidate_data, output_path, language, blind)
    
    async def _generate_basic_cv(self, candidate_data, output_path, language, blind):
        """Genera un CV básico sin análisis avanzado."""
        try:
            # Usar la implementación original
            return self.save_cv(candidate_data, output_path, language, blind)
        except Exception as e:
            logger.error(f"Error generando CV básico: {str(e)}")
            return None
    
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
        
        # Guardar temporalmente el template actual
        original_template = self.template.name
        
        try:
            # Cambiar template si es necesario
            if template_name != original_template:
                from app.com.utils.cv_generator.career_analyzercv_template import CVTemplate
                self.template = CVTemplate(template_name)
            
            # Usar la implementación original con datos enriquecidos
            return self.save_cv(enriched_data, output_path, language, blind)
        except Exception as e:
            logger.error(f"Error generando CV con datos enriquecidos: {str(e)}")
            return None
        finally:
            # Restaurar template original
            if template_name != original_template:
                from app.com.utils.cv_generator.career_analyzercv_template import CVTemplate
                self.template = CVTemplate(original_template)
    
    def _extract_candidate_id(self, cv_data):
        """Extrae el ID del candidato de los datos del CV."""
        # Intentar diferentes métodos para obtener el ID
        if hasattr(cv_data, 'id'):
            return cv_data.id
        
        if hasattr(cv_data, 'reference_code'):
            try:
                # Intentar extraer ID numérico de reference_code
                import re
                match = re.search(r'\d+', cv_data.reference_code)
                if match:
                    return int(match.group())
            except:
                pass
        
        if hasattr(cv_data, 'get_person_object'):
            try:
                person = cv_data.get_person_object()
                if person and hasattr(person, 'id'):
                    return person.id
            except:
                pass
        
        return None
    
    async def _get_person(self, person_id: int) -> Dict:
        """Obtiene los datos de la persona."""
        try:
            # Implementar lógica para obtener datos de la persona
            return {}
        except Exception as e:
            logger.error(f"Error obteniendo datos de la persona: {str(e)}")
            return None
    
    async def _get_ml_insights(self, person) -> Dict[str, Any]:
        """Obtiene insights del sistema ML."""
        try:
            # Obtener alineación con el mercado
            market_alignment = await self.ml_system.calculate_market_alignment({
                "skills": person.skills.split(',') if person.skills else [],
                "experience": [{"years": person.experience_years or 0}],
                "salary_expectations": person.salary_data or {},
                "personality_traits": person.personality_traits or {}
            })
            
            # Obtener probabilidad de transición
            transition_probability = await self.ml_system.predict_transition(person)
            
            # Obtener probabilidades de éxito en diferentes roles
            success_probabilities = await self.ml_system.predict_all_active_matches(person)
            
            return {
                "market_alignment": market_alignment,
                "transition_probability": transition_probability,
                "success_probabilities": success_probabilities
            }
        except Exception as e:
            logger.error(f"Error obteniendo insights de ML: {str(e)}")
            return {}
    
    async def _enrich_candidate_data(self, person: Dict, career_analysis: Dict, 
                                   ml_insights: Dict) -> Dict[str, Any]:
        """Enriquece los datos del candidato con análisis y valores."""
        try:
            # Datos básicos
            enriched_data = {
                "personal_info": {
                    "name": person.name,
                    "email": person.email,
                    "phone": person.phone,
                    "location": person.location,
                    "linkedin": person.linkedin_url
                },
                "career_analysis": {
                    "score": career_analysis.get("score", 0),
                    "level": career_analysis.get("level", "en desarrollo"),
                    "growth_rate": career_analysis.get("growth_rate", 0),
                    "market_alignment": ml_insights.get("market_alignment", {}),
                    "transition_readiness": ml_insights.get("transition_probability", 0),
                    "top_roles": self._get_top_roles(ml_insights.get("success_probabilities", [])),
                    "recommendations": career_analysis.get("recommendations", [])
                },
                "skills": self._process_skills(person.skills, ml_insights),
                "experience": self._process_experience(person.experience),
                "education": self._process_education(person.education),
                "languages": self._process_languages(person.languages),
                "values": await self.values_adapter.get_person_values(person.id)
            }
            
            return enriched_data
        except Exception as e:
            logger.error(f"Error enriqueciendo datos del candidato: {str(e)}")
            raise
    
    def _process_skills(self, skills: str, ml_insights: Dict) -> List[Dict]:
        """Procesa las habilidades con información de ML."""
        try:
            if not skills:
                return []
            
            skill_list = skills.split(',')
            market_alignment = ml_insights.get("market_alignment", {})
            skill_scores = market_alignment.get("skill_scores", {})
            
            return [
                {
                    "name": skill.strip(),
                    "market_demand": skill_scores.get(skill.strip(), 0),
                    "years_experience": self._get_skill_experience(skill.strip())
                }
                for skill in skill_list
            ]
        except Exception as e:
            logger.error(f"Error procesando habilidades: {str(e)}")
            return []
    
    def _get_skill_experience(self, skill: str) -> int:
        """Obtiene años de experiencia en una habilidad."""
        # Implementar lógica para obtener años de experiencia
        return 0
    
    def _get_top_roles(self, success_probabilities: List[Dict]) -> List[Dict]:
        """Obtiene los roles con mayor probabilidad de éxito."""
        try:
            # Ordenar por probabilidad de éxito
            sorted_roles = sorted(
                success_probabilities,
                key=lambda x: x.get("score", 0),
                reverse=True
            )
            
            # Retornar top 3 roles
            return [
                {
                    "role": role.get("vacante", "Desconocido"),
                    "company": role.get("empresa", "Desconocida"),
                    "probability": role.get("score", 0)
                }
                for role in sorted_roles[:3]
            ]
        except Exception as e:
            logger.error(f"Error obteniendo roles top: {str(e)}")
            return []
    
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
