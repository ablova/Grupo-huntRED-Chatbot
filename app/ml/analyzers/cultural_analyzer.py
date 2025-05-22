
# /home/pablo/app/ml/analyzers/cultural_analyzer.py
"""
Cultural Analyzer module for Grupo huntRED® assessment system.

This module provides analysis of cultural fit between candidates and organizations,
focusing on values alignment, work environment preferences, and organizational culture compatibility.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import json
from django.core.cache import cache

from app.models import BusinessUnit
from app.ml.analyzers.base_analyzer import BaseAnalyzer

# Removida la importación problemática
# En lugar de importar, implementamos la funcionalidad directamente en esta clase

logger = logging.getLogger(__name__)

class CulturalAnalyzer(BaseAnalyzer):
    """
    Analyzer for cultural fit and values alignment.
    
    Evaluates how well a candidate's values, working style, and preferences
    align with an organization's culture across different business units.
    """
    
    # Cultural dimensions across different business units
    CULTURAL_DIMENSIONS = {
        'all': ['adaptability', 'values_alignment', 'team_orientation', 'growth_mindset', 'work_ethic'],
        'huntRED': ['strategic_vision', 'executive_presence', 'stakeholder_management', 'change_leadership', 'business_acumen'],
        'huntU': ['innovation', 'learning_agility', 'digital_fluency', 'collaboration', 'entrepreneurial_mindset'],
        'Amigro': ['service_orientation', 'community_focus', 'practical_problem_solving', 'reliability', 'empathy'],
        'SEXSI': ['discretion', 'emotional_intelligence', 'ethical_standards', 'interpersonal_skills', 'professionalism']
    }
    
    # Value systems by business unit
    VALUE_SYSTEMS = {
        'huntRED': {
            'core_values': ['excellence', 'integrity', 'innovation', 'leadership', 'results'],
            'work_environment': 'structured yet dynamic, with high accountability and strategic focus'
        },
        'huntU': {
            'core_values': ['growth', 'creativity', 'collaboration', 'adaptability', 'curiosity'],
            'work_environment': 'innovative and flexible, encouraging continuous learning and experimentation'
        },
        'Amigro': {
            'core_values': ['community', 'accessibility', 'reliability', 'empathy', 'practicality'],
            'work_environment': 'supportive and practical, focused on tangible impact and community connection'
        },
        'SEXSI': {
            'core_values': ['trust', 'confidentiality', 'respect', 'professionalism', 'ethics'],
            'work_environment': 'discreet and professional, with high standards for conduct and confidentiality'
        }
    }
    
    def __init__(self):
        """Initialize the cultural analyzer with required components."""
        super().__init__()
        # No necesitamos el analizador core ya que implementamos la funcionalidad directamente en esta clase
        # Cache timeout en segundos (2 horas por defecto)
        self.cache_timeout = 7200
        
    def get_required_fields(self) -> List[str]:
        """Get required fields for cultural analysis."""
        return ['assessment_type', 'cultural_responses']
        
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analyze cultural fit based on assessment data.
        
        Args:
            data: Dictionary containing cultural assessment responses
            business_unit: Business unit for contextual analysis
            
        Returns:
            Dict with cultural fit analysis results
        """
        try:
            # Check cache first
            cached_result = self.get_cached_result(data, "cultural_analysis")
            if cached_result:
                return cached_result
                
            # Validate input
            is_valid, error_message = self.validate_input(data)
            if not is_valid:
                logger.warning(f"Invalid input for cultural analysis: {error_message}")
                return self.get_default_result(error_message)
                
            # Get business unit context
            bu_name = self.get_business_unit_name(business_unit)
            
            # Process assessment data
            result = self._analyze_cultural_fit(data, bu_name)
            
            # Cache result
            self.set_cached_result(data, result, "cultural_analysis")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in cultural analysis: {str(e)}")
            return self.get_default_result(f"Analysis error: {str(e)}")
            
    def _analyze_cultural_fit(self, data: Dict, business_unit: str) -> Dict:
        """
        Perform core cultural fit analysis.
        
        Args:
            data: Assessment data
            business_unit: Business unit name
            
        Returns:
            Dict with analysis results
        """
        # Extract cultural responses
        responses = data.get('cultural_responses', {})
        
        # Get relevant dimensions for this BU
        dimensions = self.CULTURAL_DIMENSIONS.get(business_unit, self.CULTURAL_DIMENSIONS['all'])
        
        # Calculate dimension scores
        dimension_scores = {}
        for dimension in dimensions:
            dimension_score = self._calculate_dimension_score(dimension, responses)
            dimension_scores[dimension] = dimension_score
            
        # Get organization values for this BU
        org_values = self.VALUE_SYSTEMS.get(business_unit, self.VALUE_SYSTEMS['huntRED'])
        
        # Calculate overall fit score
        overall_score = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0.5
        
        # Generate insights
        insights = self._generate_cultural_insights(dimension_scores, org_values, business_unit)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(dimension_scores, org_values, business_unit)
        
        # En lugar de usar el core_analyzer, implementamos el análisis directamente aquí
        additional_analysis = {}
        try:
            # Concatenate all responses into a single text for sentiment analysis
            cultural_text = ' '.join([f"{k}: {v}" for k, v in responses.items()])
            
            # Get organization description
            org_description = org_values.get('work_environment', '')
            
            # Implementación simplificada del análisis cultural
            # Calcular similitud simple basada en palabras clave
            keywords_org = set(org_description.lower().split())
            keywords_candidate = set(cultural_text.lower().split())
            
            # Calcular intersección y similitud de Jaccard simple
            common_words = keywords_org.intersection(keywords_candidate)
            similarity = len(common_words) / (len(keywords_org) + len(keywords_candidate) - len(common_words)) if keywords_org and keywords_candidate else 0
            
            # Análisis básico de compatibilidad
            additional_analysis = {
                'cultural_compatibility': similarity * 100,  # Convertir a porcentaje
                'common_themes': list(common_words)[:5],  # Limitar a 5 temas comunes
                'compatibility_level': 'Alto' if similarity > 0.7 else 'Medio' if similarity > 0.4 else 'Bajo'
            }
        except Exception as e:
            logger.warning(f"Additional cultural analysis failed: {str(e)}")
            additional_analysis = {}
            
        # Combine results
        result = {
            'assessment_type': 'cultural_fit',
            'business_unit': business_unit,
            'dimension_scores': dimension_scores,
            'overall_fit': overall_score,
            'organization_values': org_values['core_values'],
            'work_environment': org_values['work_environment'],
            'insights': insights,
            'recommendations': recommendations
        }
        
        # Add additional analysis if available
        if additional_analysis:
            result['additional_analysis'] = additional_analysis
            
        return result
        
    def _calculate_dimension_score(self, dimension: str, responses: Dict) -> float:
        """
        Calculate score for a specific cultural dimension.
        
        Args:
            dimension: Cultural dimension to calculate
            responses: Assessment responses
            
        Returns:
            Score between 0 and 1
        """
        # Find questions related to this dimension
        dimension_questions = [q for q in responses.keys() if dimension.replace('_', ' ') in q.lower()]
        
        if not dimension_questions:
            return 0.5  # Default score
            
        # Calculate average score from responses
        try:
            scores = []
            for q in dimension_questions:
                response = responses.get(q)
                if response:
                    # Convert various response formats to normalized score
                    if isinstance(response, (int, float)):
                        # Assuming scale of 1-5
                        scores.append((float(response) - 1) / 4)
                    elif isinstance(response, str) and response.isdigit():
                        # Numeric string
                        scores.append((float(response) - 1) / 4)
                    elif isinstance(response, str):
                        # Text response - check for positive keywords
                        positive_keywords = ['yes', 'agree', 'strongly', 'always', 'very']
                        negative_keywords = ['no', 'disagree', 'never', 'rarely', 'not']
                        
                        response_lower = response.lower()
                        if any(keyword in response_lower for keyword in positive_keywords):
                            scores.append(0.8)
                        elif any(keyword in response_lower for keyword in negative_keywords):
                            scores.append(0.2)
                        else:
                            scores.append(0.5)
                            
            return sum(scores) / len(scores) if scores else 0.5
            
        except Exception as e:
            logger.warning(f"Error calculating dimension score for {dimension}: {str(e)}")
            return 0.5
            
    def _generate_cultural_insights(self, dimension_scores: Dict, org_values: Dict, business_unit: str) -> Dict:
        """
        Generate insights based on cultural dimension scores.
        
        Args:
            dimension_scores: Scores for each cultural dimension
            org_values: Organization values and environment
            business_unit: Business unit name
            
        Returns:
            Dict with insights
        """
        insights = {}
        
        # Find top strengths (highest scores)
        strengths = sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        strengths_list = [f"{s[0].replace('_', ' ').title()}: {int(s[1]*100)}%" for s in strengths]
        
        # Find development areas (lowest scores)
        development = sorted(dimension_scores.items(), key=lambda x: x[1])[:2]
        development_list = [f"{d[0].replace('_', ' ').title()}: {int(d[1]*100)}%" for d in development]
        
        # Generate alignment insight
        core_values = org_values['core_values']
        alignment_score = self._calculate_values_alignment(dimension_scores, core_values)
        
        # Set alignment level based on score
        if alignment_score > 0.8:
            alignment_level = "Excelente"
            alignment_detail = f"Tu perfil muestra una alineación excelente con los valores centrales de {business_unit}"
        elif alignment_score > 0.6:
            alignment_level = "Buena"
            alignment_detail = f"Tu perfil se alinea bien con varios valores importantes de {business_unit}"
        elif alignment_score > 0.4:
            alignment_level = "Moderada"
            alignment_detail = f"Tu perfil tiene algunos puntos de alineación con {business_unit}, pero también diferencias"
        else:
            alignment_level = "Baja"
            alignment_detail = f"Tu perfil cultural muestra diferencias significativas con la cultura de {business_unit}"
            
        # Generate workstyle insight
        work_environment = org_values['work_environment']
        workstyle_match = self._analyze_workstyle_match(dimension_scores, work_environment)
        
        # Compile insights
        insights = {
            'strengths': strengths_list,
            'development_areas': development_list,
            'values_alignment': {
                'level': alignment_level,
                'score': int(alignment_score * 100),
                'detail': alignment_detail
            },
            'workstyle_match': workstyle_match
        }
        
        return insights
        
    def _calculate_values_alignment(self, dimension_scores: Dict, core_values: List) -> float:
        """
        Calculate alignment between dimension scores and core organizational values.
        
        Args:
            dimension_scores: Candidate's dimension scores
            core_values: Organization's core values
            
        Returns:
            Alignment score between 0 and 1
        """
        # Map organizational values to dimensions
        value_dimension_map = {
            'excellence': ['work_ethic', 'growth_mindset'],
            'integrity': ['values_alignment', 'ethical_standards'],
            'innovation': ['adaptability', 'innovation', 'digital_fluency'],
            'leadership': ['strategic_vision', 'change_leadership', 'executive_presence'],
            'results': ['business_acumen', 'results_orientation'],
            'growth': ['growth_mindset', 'learning_agility'],
            'creativity': ['innovation', 'entrepreneurial_mindset'],
            'collaboration': ['team_orientation', 'collaboration', 'interpersonal_skills'],
            'adaptability': ['adaptability', 'change_leadership'],
            'curiosity': ['learning_agility', 'growth_mindset'],
            'community': ['community_focus', 'team_orientation'],
            'accessibility': ['service_orientation', 'empathy'],
            'reliability': ['reliability', 'work_ethic'],
            'empathy': ['empathy', 'emotional_intelligence'],
            'practicality': ['practical_problem_solving', 'reliability'],
            'trust': ['ethical_standards', 'reliability'],
            'confidentiality': ['discretion', 'ethical_standards'],
            'respect': ['interpersonal_skills', 'emotional_intelligence'],
            'professionalism': ['professionalism', 'executive_presence'],
            'ethics': ['ethical_standards', 'values_alignment']
        }
        
        # Calculate alignment for each core value
        value_scores = []
        for value in core_values:
            # Get related dimensions
            related_dimensions = value_dimension_map.get(value, [])
            if not related_dimensions:
                continue
                
            # Calculate average score for related dimensions
            dimension_values = [dimension_scores.get(d, 0.5) for d in related_dimensions if d in dimension_scores]
            value_score = sum(dimension_values) / len(dimension_values) if dimension_values else 0.5
            value_scores.append(value_score)
            
        # Return average alignment score
        return sum(value_scores) / len(value_scores) if value_scores else 0.5
        
    def _analyze_workstyle_match(self, dimension_scores: Dict, work_environment: str) -> Dict:
        """
        Analyze match between candidate's workstyle and organization's environment.
        
        Args:
            dimension_scores: Candidate's dimension scores
            work_environment: Description of work environment
            
        Returns:
            Dict with workstyle match analysis
        """
        # Extract workstyle signals from dimension scores
        structure_preference = 0.5  # Default neutral
        if 'adaptability' in dimension_scores:
            # Higher adaptability suggests preference for flexible environments
            structure_preference = 1 - dimension_scores['adaptability']
            
        if 'work_ethic' in dimension_scores:
            # Adjust based on work ethic
            structure_preference = (structure_preference + dimension_scores['work_ethic']) / 2
            
        # Analyze collaboration preference
        collaboration_preference = 0.5  # Default neutral
        if 'team_orientation' in dimension_scores:
            collaboration_preference = dimension_scores['team_orientation']
            
        # Analyze innovation preference
        innovation_preference = 0.5  # Default neutral
        if 'innovation' in dimension_scores:
            innovation_preference = dimension_scores['innovation']
        elif 'growth_mindset' in dimension_scores:
            innovation_preference = dimension_scores['growth_mindset']
            
        # Analyze environment keywords
        env_lower = work_environment.lower()
        
        structure_keywords = {
            'high': ['structured', 'formal', 'process', 'systematic', 'standardized'],
            'medium': ['balanced', 'organized', 'methodical'],
            'low': ['flexible', 'dynamic', 'adaptable', 'fluid', 'agile']
        }
        
        collab_keywords = {
            'high': ['collaborative', 'team', 'cooperation', 'community'],
            'medium': ['partnership', 'coordination'],
            'low': ['independent', 'autonomous', 'self-directed']
        }
        
        innov_keywords = {
            'high': ['innovative', 'creative', 'experimental', 'cutting-edge'],
            'medium': ['balanced', 'thoughtful', 'improvement'],
            'low': ['traditional', 'established', 'proven']
        }
        
        # Determine environment characteristics
        env_structure = 'medium'
        for level, words in structure_keywords.items():
            if any(word in env_lower for word in words):
                env_structure = level
                break
                
        env_collab = 'medium'
        for level, words in collab_keywords.items():
            if any(word in env_lower for word in words):
                env_collab = level
                break
                
        env_innov = 'medium'
        for level, words in innov_keywords.items():
            if any(word in env_lower for word in words):
                env_innov = level
                break
                
        # Convert preferences to levels for comparison
        structure_level = 'high' if structure_preference > 0.7 else 'low' if structure_preference < 0.3 else 'medium'
        collab_level = 'high' if collaboration_preference > 0.7 else 'low' if collaboration_preference < 0.3 else 'medium'
        innov_level = 'high' if innovation_preference > 0.7 else 'low' if innovation_preference < 0.3 else 'medium'
        
        # Calculate matches
        structure_match = (structure_level == env_structure)
        collab_match = (collab_level == env_collab)
        innov_match = (innov_level == env_innov)
        
        # Generate match level and description
        match_count = sum([structure_match, collab_match, innov_match])
        if match_count == 3:
            match_level = "Excelente"
            match_description = "Tu estilo de trabajo se alinea perfectamente con el entorno organizacional"
        elif match_count == 2:
            match_level = "Bueno"
            match_description = "Tu estilo de trabajo se alinea bien con aspectos importantes del entorno"
        elif match_count == 1:
            match_level = "Parcial"
            match_description = "Tu estilo de trabajo coincide con algunos elementos del entorno, pero hay diferencias"
        else:
            match_level = "Bajo"
            match_description = "Tu estilo de trabajo muestra diferencias con el entorno organizacional"
            
        return {
            'level': match_level,
            'description': match_description,
            'details': {
                'structure': {'preference': structure_level, 'environment': env_structure, 'match': structure_match},
                'collaboration': {'preference': collab_level, 'environment': env_collab, 'match': collab_match},
                'innovation': {'preference': innov_level, 'environment': env_innov, 'match': innov_match}
            }
        }
        
    def _generate_recommendations(self, dimension_scores: Dict, org_values: Dict, business_unit: str) -> List[str]:
        """
        Generate recommendations based on cultural analysis.
        
        Args:
            dimension_scores: Scores for each cultural dimension
            org_values: Organization values and environment
            business_unit: Business unit name
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Find dimensions with lowest scores
        low_dimensions = [(d, s) for d, s in dimension_scores.items() if s < 0.4]
        
        # Recommendations for low dimensions
        dimension_recommendations = {
            'adaptability': "Buscar oportunidades para trabajar en entornos cambiantes que te desafíen a adaptarte",
            'values_alignment': "Investigar más a fondo los valores de la organización y reflexionar sobre tu conexión con ellos",
            'team_orientation': "Participar en proyectos colaborativos que requieran coordinación y trabajo en equipo",
            'growth_mindset': "Adoptar una mentalidad de aprendizaje continuo y buscar feedback constructivo",
            'work_ethic': "Enfocarte en la consistencia y compromiso con objetivos y plazos",
            'strategic_vision': "Desarrollar tu capacidad de pensamiento a largo plazo y visión estratégica",
            'executive_presence': "Trabajar en tu comunicación ejecutiva y presencia en entornos formales",
            'stakeholder_management': "Practicar la gestión de relaciones con diferentes grupos de interés",
            'change_leadership': "Buscar roles donde puedas liderar iniciativas de cambio",
            'business_acumen': "Fortalecer tu comprensión de los aspectos financieros y estratégicos del negocio",
            'innovation': "Participar en sesiones de ideación y proponer soluciones creativas a problemas",
            'learning_agility': "Exponerte a nuevas tecnologías y metodologías para desarrollar tu agilidad de aprendizaje",
            'digital_fluency': "Mejorar tus habilidades digitales y familiarizarte con nuevas tecnologías",
            'collaboration': "Buscar proyectos interdisciplinarios que requieran colaboración",
            'entrepreneurial_mindset': "Desarrollar iniciativas propias que muestren tu capacidad emprendedora",
            'service_orientation': "Enfocarte en entender y satisfacer las necesidades de los demás",
            'community_focus': "Participar en iniciativas comunitarias que generen impacto social",
            'practical_problem_solving': "Trabajar en tu capacidad para resolver problemas prácticos de manera eficiente",
            'reliability': "Construir una reputación de confiabilidad cumpliendo consistentemente con tus compromisos",
            'empathy': "Practicar la escucha activa y la comprensión de perspectivas diferentes",
            'discretion': "Desarrollar tu capacidad para manejar información sensible con confidencialidad",
            'emotional_intelligence': "Trabajar en el reconocimiento y gestión de emociones propias y ajenas",
            'ethical_standards': "Reflexionar sobre tus principios éticos y su aplicación en entornos profesionales",
            'interpersonal_skills': "Mejorar tus habilidades de comunicación y relación interpersonal",
            'professionalism': "Enfocarte en mantener estándares profesionales consistentes en todas las interacciones"
        }
        
        for dimension, score in low_dimensions:
            if dimension in dimension_recommendations:
                recommendations.append(dimension_recommendations[dimension])
                
        # Add BU-specific recommendations
        bu_recommendations = {
            'huntRED': "Para tener éxito en huntRED, enfócate en desarrollar tu visión estratégica y capacidad de liderazgo ejecutivo",
            'huntU': "Para destacar en huntU, cultiva tu capacidad de innovación y aprendizaje continuo en entornos tecnológicos",
            'Amigro': "Para prosperar en Amigro, desarrolla tu orientación al servicio y capacidad para resolver problemas prácticos",
            'SEXSI': "Para exceler en SEXSI, fortalece tu profesionalismo y capacidad para manejar relaciones con discreción y ética"
        }
        
        if business_unit in bu_recommendations:
            recommendations.append(bu_recommendations[business_unit])
            
        # Add general recommendation if needed
        if len(recommendations) < 2:
            recommendations.append("Busca oportunidades para experimentar la cultura organizacional a través de proyectos colaborativos o programas de mentoring")
            
        # Limit to 3-5 recommendations
        return recommendations[:5]
