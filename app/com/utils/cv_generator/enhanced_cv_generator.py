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

from .cv_generator import CVGenerator
from .cv_data import CVData
from .career_analyzer import career_analyzer
from app.com.chatbot.core.values import ValuesPrinciples

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
        self.career_analyzer = career_analyzer
    
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
            
            # Generar análisis de carrera en paralelo para optimizar tiempo
            career_analysis_tasks = [
                self.career_analyzer.analyze_career_potential(candidate_id),
                self.career_analyzer.identify_critical_skills(candidate_id, business_unit),
            ]
            
            # Si el tipo de audiencia es 'candidate' o 'consultant', añadir plan de desarrollo
            if audience_type in ['candidate', 'consultant']:
                career_analysis_tasks.append(
                    self.career_analyzer.generate_development_plan(candidate_id, business_unit)
                )
            
            # Ejecutar tareas en paralelo
            results = await asyncio.gather(*career_analysis_tasks)
            
            # Estructurar resultados
            career_potential = results[0]
            critical_skills = results[1]
            development_plan = results[2] if len(results) > 2 else None
            
            # Generar mensaje personalizado según valores
            personalized_message = self.career_analyzer.personalize_cv_message(
                candidate_data.__dict__, audience_type
            )
            
            # Enriquecer datos del candidato con análisis y mensaje
            enriched_data = self._enrich_candidate_data(
                candidate_data, 
                career_potential, 
                critical_skills, 
                development_plan,
                personalized_message
            )
            
            # Generar CV utilizando la funcionalidad base
            cv_path = await self._generate_cv_with_enriched_data(
                enriched_data, output_path, language, blind, audience_type
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
                from .cv_template import CVTemplate
                self.template = CVTemplate(template_name)
            
            # Usar la implementación original con datos enriquecidos
            return self.save_cv(enriched_data, output_path, language, blind)
        except Exception as e:
            logger.error(f"Error generando CV con datos enriquecidos: {str(e)}")
            return None
        finally:
            # Restaurar template original
            if template_name != original_template:
                from .cv_template import CVTemplate
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
    
    def _enrich_candidate_data(self, cv_data, career_potential, critical_skills, 
                              development_plan, personalized_message):
        """Enriquece los datos del CV con análisis de carrera y mensaje personalizado."""
        # Crear copia para no modificar el original
        enriched = cv_data.__dict__.copy() if hasattr(cv_data, '__dict__') else cv_data.copy()
        
        # Añadir análisis de carrera
        enriched['career_potential'] = career_potential
        enriched['critical_skills'] = critical_skills
        
        # Añadir plan de desarrollo si está disponible
        if development_plan:
            enriched['development_plan'] = development_plan
        
        # Añadir mensaje personalizado
        enriched['personalized_message'] = personalized_message
        
        # Añadir metadatos del análisis
        enriched['analysis_timestamp'] = datetime.now().isoformat()
        enriched['analysis_version'] = '2.0'
        
        return enriched


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
