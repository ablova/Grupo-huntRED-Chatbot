# app/ml/core/cv_analyzer.py
"""
Analizador centralizado de CVs para Grupo huntRED®

Este módulo proporciona una interfaz unificada para el análisis completo de CVs,
integrando todos los componentes del sistema de análisis de talento:
- Estructuración y limpieza de datos
- Análisis de carrera y potencial
- Procesamiento de referencias
- Análisis de valores y ML
- Preparación para matching y dashboards
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import asdict

from django.conf import settings
from asgiref.sync import sync_to_async

# Importaciones de componentes existentes
from app.ats.utils.cv_generator.cv_data import CVData
from app.ats.utils.cv_generator.cv_utils import CVUtils
from app.ats.utils.cv_generator.career_analyzer import CVCareerAnalyzer
from app.ats.utils.cv_generator.values_adapter import CVValuesAdapter
from app.ats.chatbot.values.core import ValuesPrinciples
from app.ml.core.models.base import MatchmakingLearningSystem
from app.ats.kanban.ml_integration import get_candidate_growth_data

logger = logging.getLogger(__name__)

class CVAnalyzer:
    """
    Analizador centralizado de CVs que integra todos los componentes del sistema.
    
    Proporciona una interfaz unificada para:
    - Extracción y estructuración de datos de CV
    - Análisis de carrera y potencial
    - Procesamiento de referencias
    - Análisis de valores y alineación cultural
    - Preparación para sistemas de matching y dashboards
    """
    
    def __init__(self, analysis_level: str = 'comprehensive'):
        """
        Inicializa el analizador de CVs.
        
        Args:
            analysis_level: Nivel de análisis ('basic', 'enhanced', 'comprehensive')
        """
        self.analysis_level = analysis_level
        self.utils = CVUtils()
        self.career_analyzer = CVCareerAnalyzer()
        self.values_adapter = CVValuesAdapter()
        self.values_principles = ValuesPrinciples()
        self.ml_system = MatchmakingLearningSystem()
        
        logger.info(f"CVAnalyzer inicializado con nivel: {analysis_level}")
    
    async def analyze(
        self, 
        cv_input: Union[Dict, str, bytes, CVData],
        person_id: Optional[int] = None,
        business_unit: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analiza un CV y devuelve información estructurada y enriquecida.
        
        Args:
            cv_input: Datos del CV (dict, texto, bytes, o CVData)
            person_id: ID de la persona (opcional, para análisis avanzado)
            business_unit: Unidad de negocio (opcional, para análisis contextual)
            
        Returns:
            Dict con análisis completo del CV
        """
        try:
            # 1. Preparar y estructurar datos básicos
            cv_data = await self._prepare_cv_data(cv_input)
            
            # 2. Análisis básico de estructura
            basic_analysis = await self._analyze_basic_structure(cv_data)
            
            # 3. Análisis de carrera (si hay person_id)
            career_analysis = {}
            if person_id and self.analysis_level in ['enhanced', 'comprehensive']:
                career_analysis = await self._analyze_career_potential(person_id, business_unit)
            
            # 4. Procesamiento de referencias
            reference_analysis = await self._analyze_references(cv_data)
            
            # 5. Análisis de valores y alineación cultural
            values_analysis = await self._analyze_values_alignment(cv_data, business_unit)
            
            # 6. Análisis ML y predicciones
            ml_analysis = {}
            if person_id and self.analysis_level == 'comprehensive':
                ml_analysis = await self._analyze_ml_insights(person_id, business_unit)
            
            # 7. Integrar todos los análisis
            integrated_analysis = self._integrate_analyses(
                basic_analysis,
                career_analysis,
                reference_analysis,
                values_analysis,
                ml_analysis
            )
            
            # 8. Generar recomendaciones y insights
            recommendations = await self._generate_recommendations(integrated_analysis, business_unit)
            
            # 9. Preparar resultado final
            result = {
                'cv_data': cv_data,
                'analysis': integrated_analysis,
                'recommendations': recommendations,
                'metadata': {
                    'analysis_level': self.analysis_level,
                    'analysis_date': datetime.now().isoformat(),
                    'person_id': person_id,
                    'business_unit': business_unit
                }
            }
            
            logger.info(f"Análisis de CV completado para person_id: {person_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis de CV: {str(e)}")
            return self._get_error_result(str(e))
    
    async def _prepare_cv_data(self, cv_input: Union[Dict, str, bytes, CVData]) -> CVData:
        """Prepara y estructura los datos del CV."""
        try:
            if isinstance(cv_input, CVData):
                return cv_input
            elif isinstance(cv_input, dict):
                return CVData(**cv_input)
            elif isinstance(cv_input, str):
                # Parsear texto del CV
                parsed_data = await self._parse_cv_text(cv_input)
                return CVData(**parsed_data)
            elif isinstance(cv_input, bytes):
                # Parsear PDF o documento binario
                parsed_data = await self._parse_cv_document(cv_input)
                return CVData(**parsed_data)
            else:
                raise ValueError(f"Tipo de entrada no soportado: {type(cv_input)}")
        except Exception as e:
            logger.error(f"Error preparando datos del CV: {str(e)}")
            return CVData()
    
    async def _analyze_basic_structure(self, cv_data: CVData) -> Dict[str, Any]:
        """Analiza la estructura básica del CV."""
        try:
            # Limpiar y normalizar datos
            cleaned_data = self.utils.clean_candidate_data(asdict(cv_data))
            
            # Extraer información estructurada
            analysis = {
                'personal_info': {
                    'name': cleaned_data.get('name', ''),
                    'email': cleaned_data.get('email', ''),
                    'phone': cleaned_data.get('phone', ''),
                    'location': cleaned_data.get('location', ''),
                    'linkedin': cleaned_data.get('linkedin', '')
                },
                'education': self._analyze_education(cleaned_data.get('education', [])),
                'experience': self._analyze_experience(cleaned_data.get('experience', [])),
                'skills': self._analyze_skills(cleaned_data.get('skills', [])),
                'languages': self._analyze_languages(cleaned_data.get('languages', [])),
                'certifications': cleaned_data.get('certifications', []),
                'projects': cleaned_data.get('projects', []),
                'achievements': cleaned_data.get('achievements', [])
            }
            
            # Calcular métricas básicas
            analysis['metrics'] = {
                'total_experience_years': self._calculate_total_experience(analysis['experience']),
                'skill_count': len(analysis['skills']),
                'language_count': len(analysis['languages']),
                'education_level': self._determine_education_level(analysis['education']),
                'career_progression': self._analyze_career_progression(analysis['experience'])
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error en análisis básico: {str(e)}")
            return {}
    
    async def _analyze_career_potential(self, person_id: int, business_unit: str) -> Dict[str, Any]:
        """Analiza el potencial de carrera usando CVCareerAnalyzer."""
        try:
            # Obtener análisis de potencial
            potential_analysis = await self.career_analyzer.analyze_career_potential(person_id)
            
            # Identificar habilidades críticas
            critical_skills = await self.career_analyzer.identify_critical_skills(person_id, business_unit)
            
            # Generar plan de desarrollo
            development_plan = await self.career_analyzer.generate_development_plan(person_id, business_unit)
            
            return {
                'potential_score': potential_analysis.get('potential_score', 0.0),
                'potential_level': potential_analysis.get('potential_level', 'unknown'),
                'critical_skills': critical_skills,
                'development_plan': development_plan,
                'growth_areas': potential_analysis.get('growth_areas', []),
                'top_roles': potential_analysis.get('top_roles', [])
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de carrera: {str(e)}")
            return {}
    
    async def _analyze_references(self, cv_data: CVData) -> Dict[str, Any]:
        """Analiza las referencias del candidato."""
        try:
            references = getattr(cv_data, 'references', [])
            if not references:
                return {'reference_count': 0, 'reference_quality': 'no_references'}
            
            # Procesar referencias
            processed_references = []
            for ref in references:
                processed_ref = await self.reference_processor.process_reference(ref)
                processed_references.append(processed_ref)
            
            # Calcular métricas de calidad
            quality_metrics = self._calculate_reference_quality(processed_references)
            
            return {
                'reference_count': len(processed_references),
                'reference_quality': quality_metrics['overall_quality'],
                'references': processed_references,
                'quality_metrics': quality_metrics
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de referencias: {str(e)}")
            return {'reference_count': 0, 'reference_quality': 'error'}
    
    async def _analyze_values_alignment(self, cv_data: CVData, business_unit: str) -> Dict[str, Any]:
        """Analiza la alineación de valores y cultura."""
        try:
            # Extraer valores del CV
            cv_values = self.values_adapter.extract_values_from_cv(cv_data)
            
            # Obtener valores de la unidad de negocio
            bu_values = await self._get_business_unit_values(business_unit)
            
            # Calcular alineación
            alignment_score = self.values_adapter.calculate_values_alignment(cv_values, bu_values)
            
            # Generar insights de valores
            values_insights = self.values_adapter.generate_values_insights(cv_values, bu_values)
            
            return {
                'cv_values': cv_values,
                'business_unit_values': bu_values,
                'alignment_score': alignment_score,
                'values_insights': values_insights,
                'cultural_fit': self._determine_cultural_fit(alignment_score)
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de valores: {str(e)}")
            return {'alignment_score': 0.0, 'cultural_fit': 'unknown'}
    
    async def _analyze_ml_insights(self, person_id: int, business_unit: str) -> Dict[str, Any]:
        """Analiza insights de ML y predicciones."""
        try:
            # Obtener datos de crecimiento del candidato
            growth_data = await sync_to_async(get_candidate_growth_data)(person_id)
            
            # Obtener predicciones del sistema ML
            ml_predictions = await self._get_ml_predictions(person_id, business_unit)
            
            # Calcular métricas de ML
            ml_metrics = self._calculate_ml_metrics(growth_data, ml_predictions)
            
            return {
                'growth_data': growth_data,
                'ml_predictions': ml_predictions,
                'ml_metrics': ml_metrics,
                'success_probability': ml_predictions.get('success_probability', 0.0),
                'recommended_roles': ml_predictions.get('recommended_roles', [])
            }
            
        except Exception as e:
            logger.error(f"Error en análisis ML: {str(e)}")
            return {}
    
    def _integrate_analyses(
        self,
        basic_analysis: Dict,
        career_analysis: Dict,
        reference_analysis: Dict,
        values_analysis: Dict,
        ml_analysis: Dict
    ) -> Dict[str, Any]:
        """Integra todos los análisis en un resultado coherente."""
        integrated = {
            'profile_summary': {
                'experience_years': basic_analysis.get('metrics', {}).get('total_experience_years', 0),
                'education_level': basic_analysis.get('metrics', {}).get('education_level', 'unknown'),
                'skill_count': basic_analysis.get('metrics', {}).get('skill_count', 0),
                'potential_score': career_analysis.get('potential_score', 0.0),
                'cultural_fit': values_analysis.get('cultural_fit', 'unknown'),
                'reference_quality': reference_analysis.get('reference_quality', 'unknown')
            },
            'strengths': self._identify_strengths(basic_analysis, career_analysis, values_analysis),
            'areas_for_improvement': self._identify_improvement_areas(basic_analysis, career_analysis),
            'career_recommendations': career_analysis.get('top_roles', []),
            'skill_gaps': career_analysis.get('critical_skills', []),
            'values_alignment': values_analysis.get('alignment_score', 0.0),
            'ml_insights': ml_analysis.get('ml_metrics', {}),
            'overall_score': self._calculate_overall_score(
                basic_analysis, career_analysis, reference_analysis, values_analysis, ml_analysis
            )
        }
        
        return integrated
    
    async def _generate_recommendations(self, analysis: Dict, business_unit: str) -> List[Dict]:
        """Genera recomendaciones basadas en el análisis."""
        recommendations = []
        
        try:
            # Recomendaciones de desarrollo
            if analysis.get('areas_for_improvement'):
                for area in analysis['areas_for_improvement']:
                    recommendations.append({
                        'type': 'development',
                        'category': area['category'],
                        'title': f"Desarrollar {area['skill']}",
                        'description': area['description'],
                        'priority': area.get('priority', 'medium')
                    })
            
            # Recomendaciones de carrera
            if analysis.get('career_recommendations'):
                for role in analysis['career_recommendations'][:3]:  # Top 3
                    recommendations.append({
                        'type': 'career',
                        'category': 'role_transition',
                        'title': f"Considerar rol: {role['title']}",
                        'description': f"Probabilidad de éxito: {role.get('probability', 0):.1%}",
                        'priority': 'high' if role.get('probability', 0) > 0.8 else 'medium'
                    })
            
            # Recomendaciones de valores
            if analysis.get('values_alignment', 0) < 0.7:
                recommendations.append({
                    'type': 'cultural',
                    'category': 'values_alignment',
                    'title': "Evaluar alineación cultural",
                    'description': "El candidato puede requerir adaptación cultural",
                    'priority': 'medium'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return []
    
    # Métodos auxiliares para análisis específicos
    
    def _analyze_education(self, education: List[Dict]) -> List[Dict]:
        """Analiza la educación del candidato."""
        analyzed_education = []
        for edu in education:
            analyzed_edu = {
                'degree': edu.get('degree', ''),
                'institution': edu.get('institution', ''),
                'field': edu.get('field_of_study', ''),
                'start_date': edu.get('start_date', ''),
                'end_date': edu.get('end_date', ''),
                'gpa': edu.get('gpa', ''),
                'level': self._determine_education_level_single(edu)
            }
            analyzed_education.append(analyzed_edu)
        return analyzed_education
    
    def _analyze_experience(self, experience: List[Dict]) -> List[Dict]:
        """Analiza la experiencia laboral."""
        analyzed_experience = []
        for exp in experience:
            analyzed_exp = {
                'title': exp.get('title', ''),
                'company': exp.get('company', ''),
                'start_date': exp.get('start_date', ''),
                'end_date': exp.get('end_date', ''),
                'duration': self._calculate_duration(exp.get('start_date'), exp.get('end_date')),
                'description': exp.get('description', ''),
                'achievements': exp.get('achievements', []),
                'skills_used': exp.get('skills_used', [])
            }
            analyzed_experience.append(analyzed_exp)
        return analyzed_experience
    
    def _analyze_skills(self, skills: List[Dict]) -> List[Dict]:
        """Analiza las habilidades del candidato."""
        analyzed_skills = []
        for skill in skills:
            analyzed_skill = {
                'name': skill.get('name', ''),
                'level': skill.get('level', ''),
                'years_experience': skill.get('years_experience', 0),
                'category': self._categorize_skill(skill.get('name', '')),
                'relevance': skill.get('relevance', 'medium')
            }
            analyzed_skills.append(analyzed_skill)
        return analyzed_skills
    
    def _analyze_languages(self, languages: List[Dict]) -> List[Dict]:
        """Analiza los idiomas del candidato."""
        analyzed_languages = []
        for lang in languages:
            analyzed_lang = {
                'language': lang.get('language', ''),
                'level': lang.get('level', ''),
                'certification': lang.get('certification', ''),
                'proficiency_score': self._calculate_language_proficiency(lang.get('level', ''))
            }
            analyzed_languages.append(analyzed_lang)
        return analyzed_languages
    
    # Métodos de cálculo y utilidades
    
    def _calculate_total_experience(self, experience: List[Dict]) -> float:
        """Calcula el total de años de experiencia."""
        total_years = 0.0
        for exp in experience:
            duration = exp.get('duration', 0)
            if isinstance(duration, (int, float)):
                total_years += duration
        return total_years
    
    def _determine_education_level(self, education: List[Dict]) -> str:
        """Determina el nivel educativo más alto."""
        levels = ['high_school', 'bachelor', 'master', 'phd']
        highest_level = 'high_school'
        
        for edu in education:
            level = edu.get('level', 'high_school')
            if level in levels and levels.index(level) > levels.index(highest_level):
                highest_level = level
        
        return highest_level
    
    def _determine_education_level_single(self, education: Dict) -> str:
        """Determina el nivel educativo de un grado específico."""
        degree = education.get('degree', '').lower()
        if 'phd' in degree or 'doctorado' in degree:
            return 'phd'
        elif 'master' in degree or 'maestría' in degree:
            return 'master'
        elif 'bachelor' in degree or 'licenciatura' in degree:
            return 'bachelor'
        else:
            return 'high_school'
    
    def _analyze_career_progression(self, experience: List[Dict]) -> Dict:
        """Analiza la progresión de carrera."""
        if not experience:
            return {'progression': 'no_experience', 'growth_rate': 0.0}
        
        # Ordenar por fecha
        sorted_exp = sorted(experience, key=lambda x: x.get('start_date', ''))
        
        # Analizar cambios de título y responsabilidades
        title_changes = len(set(exp.get('title', '') for exp in sorted_exp))
        company_changes = len(set(exp.get('company', '') for exp in sorted_exp))
        
        return {
            'progression': 'stable' if company_changes <= 2 else 'dynamic',
            'growth_rate': title_changes / max(len(sorted_exp), 1),
            'company_changes': company_changes,
            'title_changes': title_changes
        }
    
    def _calculate_duration(self, start_date: str, end_date: str) -> float:
        """Calcula la duración en años entre dos fechas."""
        try:
            if not start_date:
                return 0.0
            
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
            
            duration = (end - start).days / 365.25
            return max(0.0, duration)
        except:
            return 0.0
    
    def _categorize_skill(self, skill_name: str) -> str:
        """Categoriza una habilidad."""
        skill_lower = skill_name.lower()
        
        if any(tech in skill_lower for tech in ['python', 'java', 'javascript', 'sql', 'html', 'css']):
            return 'technical'
        elif any(soft in skill_lower for soft in ['leadership', 'communication', 'teamwork', 'problem_solving']):
            return 'soft_skills'
        elif any(domain in skill_lower for domain in ['marketing', 'sales', 'finance', 'hr']):
            return 'domain_knowledge'
        else:
            return 'other'
    
    def _calculate_language_proficiency(self, level: str) -> float:
        """Calcula un score de proficiencia de idioma."""
        level_mapping = {
            'native': 1.0,
            'fluent': 0.9,
            'advanced': 0.8,
            'intermediate': 0.6,
            'basic': 0.4,
            'beginner': 0.2
        }
        return level_mapping.get(level.lower(), 0.5)
    
    def _calculate_reference_quality(self, references: List[Dict]) -> Dict:
        """Calcula métricas de calidad de referencias."""
        if not references:
            return {'overall_quality': 'no_references', 'score': 0.0}
        
        total_score = 0.0
        for ref in references:
            score = ref.get('quality_score', 0.0)
            total_score += score
        
        avg_score = total_score / len(references)
        
        if avg_score >= 0.8:
            quality = 'excellent'
        elif avg_score >= 0.6:
            quality = 'good'
        elif avg_score >= 0.4:
            quality = 'fair'
        else:
            quality = 'poor'
        
        return {
            'overall_quality': quality,
            'score': avg_score,
            'reference_count': len(references)
        }
    
    def _determine_cultural_fit(self, alignment_score: float) -> str:
        """Determina el fit cultural basado en el score de alineación."""
        if alignment_score >= 0.8:
            return 'excellent'
        elif alignment_score >= 0.6:
            return 'good'
        elif alignment_score >= 0.4:
            return 'fair'
        else:
            return 'poor'
    
    def _calculate_ml_metrics(self, growth_data: Dict, ml_predictions: Dict) -> Dict:
        """Calcula métricas de ML."""
        return {
            'growth_trend': growth_data.get('growth_trend', 'stable'),
            'success_probability': ml_predictions.get('success_probability', 0.0),
            'recommendation_confidence': ml_predictions.get('confidence', 0.0)
        }
    
    def _identify_strengths(self, basic_analysis: Dict, career_analysis: Dict, values_analysis: Dict) -> List[str]:
        """Identifica las fortalezas del candidato."""
        strengths = []
        
        # Fortalezas basadas en experiencia
        if basic_analysis.get('metrics', {}).get('total_experience_years', 0) > 5:
            strengths.append("Experiencia sólida en el campo")
        
        # Fortalezas basadas en habilidades
        skill_count = basic_analysis.get('metrics', {}).get('skill_count', 0)
        if skill_count > 10:
            strengths.append("Amplio conjunto de habilidades")
        
        # Fortalezas basadas en potencial
        if career_analysis.get('potential_score', 0) > 0.8:
            strengths.append("Alto potencial de crecimiento")
        
        # Fortalezas basadas en valores
        if values_analysis.get('alignment_score', 0) > 0.8:
            strengths.append("Excelente alineación cultural")
        
        return strengths
    
    def _identify_improvement_areas(self, basic_analysis: Dict, career_analysis: Dict) -> List[Dict]:
        """Identifica áreas de mejora."""
        areas = []
        
        # Áreas basadas en habilidades críticas
        critical_skills = career_analysis.get('critical_skills', [])
        for skill in critical_skills:
            areas.append({
                'category': 'skill_gap',
                'skill': skill.get('name', ''),
                'description': f"Desarrollar {skill.get('name', '')} para el siguiente nivel",
                'priority': 'high' if skill.get('gap', 0) > 30 else 'medium'
            })
        
        # Áreas basadas en experiencia
        experience_years = basic_analysis.get('metrics', {}).get('total_experience_years', 0)
        if experience_years < 2:
            areas.append({
                'category': 'experience',
                'skill': 'Experiencia laboral',
                'description': "Ganar más experiencia práctica en el campo",
                'priority': 'high'
            })
        
        return areas
    
    def _calculate_overall_score(
        self,
        basic_analysis: Dict,
        career_analysis: Dict,
        reference_analysis: Dict,
        values_analysis: Dict,
        ml_analysis: Dict
    ) -> float:
        """Calcula un score general del candidato."""
        weights = {
            'experience': 0.25,
            'skills': 0.20,
            'potential': 0.20,
            'references': 0.15,
            'values': 0.10,
            'ml': 0.10
        }
        
        scores = {
            'experience': min(basic_analysis.get('metrics', {}).get('total_experience_years', 0) / 10, 1.0),
            'skills': min(basic_analysis.get('metrics', {}).get('skill_count', 0) / 20, 1.0),
            'potential': career_analysis.get('potential_score', 0.0),
            'references': reference_analysis.get('quality_metrics', {}).get('score', 0.0),
            'values': values_analysis.get('alignment_score', 0.0),
            'ml': ml_analysis.get('ml_metrics', {}).get('success_probability', 0.0)
        }
        
        overall_score = sum(scores[key] * weights[key] for key in weights)
        return min(1.0, max(0.0, overall_score))
    
    # Métodos de parsing (stubs para implementación futura)
    
    async def _parse_cv_text(self, text: str) -> Dict:
        """Parsea texto de CV (stub para implementación futura)."""
        # TODO: Implementar parsing de texto de CV
        return {
            'name': '',
            'email': '',
            'phone': '',
            'location': '',
            'education': [],
            'experience': [],
            'skills': [],
            'languages': []
        }
    
    async def _parse_cv_document(self, document: bytes) -> Dict:
        """Parsea documento de CV (stub para implementación futura)."""
        # TODO: Implementar parsing de PDF/documentos
        return {
            'name': '',
            'email': '',
            'phone': '',
            'location': '',
            'education': [],
            'experience': [],
            'skills': [],
            'languages': []
        }
    
    async def _get_business_unit_values(self, business_unit: str) -> Dict:
        """Obtiene valores de la unidad de negocio."""
        # TODO: Implementar obtención de valores de BU
        return {}
    
    async def _get_ml_predictions(self, person_id: int, business_unit: str) -> Dict:
        """Obtiene predicciones de ML."""
        # TODO: Implementar predicciones de ML
        return {
            'success_probability': 0.7,
            'confidence': 0.8,
            'recommended_roles': []
        }
    
    def _get_error_result(self, error_message: str) -> Dict:
        """Devuelve un resultado de error."""
        return {
            'error': True,
            'error_message': error_message,
            'cv_data': {},
            'analysis': {},
            'recommendations': [],
            'metadata': {
                'analysis_level': self.analysis_level,
                'analysis_date': datetime.now().isoformat(),
                'error': True
            } 
        }