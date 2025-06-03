# /home/pablo/app/ml/analyzers/integrated_analyzer.py
"""
Integrated Analyzer module for Grupo huntRED® assessment system.

This module provides a unified interface for analyzing all assessment types,
integrating personality, cultural, professional, and talent assessments
into a comprehensive profile analysis.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
import json
from django.core.cache import cache

from app.models import BusinessUnit
from app.ats.ml.analyzers.base_analyzer import BaseAnalyzer
from app.ats.ml.analyzers.personality_analyzer import PersonalityAnalyzer
from app.ats.ml.analyzers.cultural_analyzer import CulturalAnalyzer
from app.ats.ml.analyzers.professional_analyzer import ProfessionalAnalyzer
from app.ats.ml.analyzers.talent_analyzer import TalentAnalyzer
from app.ml.base import BaseAnalyzer as NewBaseAnalyzer
from app.ml.models import MatchmakingLearningSystem

logger = logging.getLogger(__name__)

class IntegratedAnalyzer(NewBaseAnalyzer):
    """
    Unified analyzer that integrates all assessment types.
    
    Provides a holistic view of a candidate by combining insights from:
    - Personality assessments
    - Cultural fit assessments
    - Professional DNA assessments
    - Talent and skills assessments
    
    This analyzer serves as the primary entry point for workflows needing
    comprehensive candidate analysis.
    """
    
    def __init__(self):
        """Initialize all component analyzers."""
        super().__init__()
        self.personality_analyzer = PersonalityAnalyzer()
        self.cultural_analyzer = CulturalAnalyzer()
        self.professional_analyzer = ProfessionalAnalyzer()
        self.talent_analyzer = TalentAnalyzer()
        self.model = MatchmakingLearningSystem()
        self.cache_timeout = 7200  # 2 hours (longer than individual analyzers)
        
    def get_required_fields(self) -> List[str]:
        """
        Get minimal required fields for integrated analysis.
        Individual analyzers will have more specific requirements.
        """
        return ['candidate_id']
        
    def analyze(self, data: Dict[str, Any], business_unit: str = None) -> Dict[str, Any]:
        """
        Realiza un análisis integrado de todos los assessments disponibles.
        
        Args:
            data: Diccionario con los resultados de los diferentes assessments
            business_unit: Unidad de negocio para contextualizar el análisis
            
        Returns:
            Dict con el análisis integrado
        """
        # Usar caché si está disponible
        cache_key = self._generate_cache_key(data, business_unit)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
            
        try:
            # Extraer datos de cada assessment
            personality_results = data.get('personality_results', {})
            cultural_results = data.get('cultural_results', {})
            professional_results = data.get('professional_results', {})
            talent_results = data.get('talent_results', {})
            
            # Validar que hay suficientes datos para un análisis integrado
            if not any([personality_results, cultural_results, professional_results, talent_results]):
                return {
                    'status': 'error',
                    'message': 'No hay suficientes datos para realizar un análisis integrado'
                }
            
            # Realizar análisis integrado
            integrated_results = {
                'status': 'success',
                'overall_score': 0.0,
                'strengths': [],
                'development_areas': [],
                'key_insights': [],
                'recommendations': [],
                'fit_analysis': {}
            }
            
            # Calcular puntaje general basado en los assessments disponibles
            scores = []
            weights = {
                'personality': 0.25,
                'cultural': 0.25,
                'professional': 0.25,
                'talent': 0.25
            }
            
            # Ajustar pesos según la unidad de negocio si está disponible
            if business_unit:
                bu_weights = self._get_business_unit_weights(business_unit)
                if bu_weights:
                    weights = bu_weights
            
            if personality_results:
                personality_score = self._extract_overall_score(personality_results)
                if personality_score is not None:
                    scores.append(personality_score * weights['personality'])
                    
            if cultural_results:
                cultural_score = self._extract_overall_score(cultural_results)
                if cultural_score is not None:
                    scores.append(cultural_score * weights['cultural'])
            
            if professional_results:
                professional_score = self._extract_overall_score(professional_results)
                if professional_score is not None:
                    scores.append(professional_score * weights['professional'])
            
            if talent_results:
                talent_score = self._extract_overall_score(talent_results)
                if talent_score is not None:
                    scores.append(talent_score * weights['talent'])
            
            # Calcular puntaje promedio ponderado
            if scores:
                integrated_results['overall_score'] = sum(scores) / sum(weights.values())
            
            # Combinar fortalezas y áreas de desarrollo
            all_strengths = []
            all_development_areas = []
            
            if personality_results:
                all_strengths.extend(personality_results.get('strengths', []))
                all_development_areas.extend(personality_results.get('development_areas', []))
            
            if cultural_results:
                all_strengths.extend(cultural_results.get('strengths', []))
                all_development_areas.extend(cultural_results.get('areas_for_improvement', []))
            
            if professional_results:
                all_strengths.extend(professional_results.get('strengths', []))
                all_development_areas.extend(professional_results.get('development_areas', []))
            
            if talent_results:
                all_strengths.extend(talent_results.get('strengths', []))
                all_development_areas.extend(talent_results.get('gaps', []))
            
            # Eliminar duplicados y seleccionar las más relevantes
            integrated_results['strengths'] = self._deduplicate_and_rank(all_strengths)
            integrated_results['development_areas'] = self._deduplicate_and_rank(all_development_areas)
            
            # Generar insights clave basados en la combinación de assessments
            integrated_results['key_insights'] = self._generate_key_insights(
                personality_results, 
                cultural_results,
                professional_results,
                talent_results,
                business_unit
            )
            
            # Generar recomendaciones integrales
            integrated_results['recommendations'] = self._generate_integrated_recommendations(
                personality_results, 
                professional_results,
                business_unit
            )
            
            # Análisis de compatibilidad
            integrated_results['fit_analysis'] = self._analyze_fit(
                personality_results, 
                cultural_results,
                professional_results,
                talent_results,
                business_unit
            )
            
            # Añadir análisis de compatibilidad organizacional
            integrated_results['organizational_compatibility'] = self._analyze_organizational_compatibility(
                personality_results, 
                cultural_results,
                professional_results,
                talent_results,
                business_unit
            )
            
            # Añadir métricas de éxito potencial
            integrated_results['success_metrics'] = self._calculate_success_metrics(
                personality_results, 
                cultural_results,
                professional_results,
                talent_results,
                business_unit
            )
            
            # Añadir análisis de liderazgo
            integrated_results['leadership_analysis'] = self._analyze_leadership_potential(
                personality_results, 
                cultural_results,
                professional_results,
                talent_results
            )
            
            # Añadir análisis de desarrollo
            integrated_results['development_plan'] = self._create_development_plan(
                integrated_results['development_areas'],
                integrated_results['strengths'],
                personality_results,
                professional_results
            )
            
            # Guardar en caché
            self._save_to_cache(cache_key, integrated_results)
            
            return integrated_results
            
        except Exception as e:
            logger.error(f"Error en análisis integrado: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error realizando análisis integrado: {str(e)}"
            }
        
    def _integrate_results(self, personality_results: Dict[str, Any], 
                         professional_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integra los resultados de personalidad y perfil profesional.
        """
        try:
            # Extraer rasgos y habilidades
            personality_traits = personality_results.get('traits', {})
            professional_skills = professional_results.get('skills', {})
            
            # Calcular compatibilidad entre rasgos y habilidades
            trait_skill_compatibility = self.model.calculate_trait_skill_compatibility(personality_traits, professional_skills)
            
            # Identificar fortalezas y áreas de mejora integradas
            strengths = self.model.identify_integrated_strengths(personality_traits, professional_skills)
            
            areas_for_improvement = self.model.identify_integrated_improvements(personality_traits, professional_skills)
            
            return {
                'trait_skill_compatibility': trait_skill_compatibility,
                'strengths': strengths,
                'areas_for_improvement': areas_for_improvement,
                'professional_level': professional_results.get('professional_level', 'Entry-Level'),
                'personality_type': self._determine_personality_type(personality_traits)
            }
            
        except Exception as e:
            logger.error(f"Error integrando resultados: {str(e)}")
            return {}
            
    def _calculate_trait_skill_compatibility(self, traits: Dict[str, float], 
                                          skills: Dict[str, float]) -> Dict[str, float]:
        """
        Calcula la compatibilidad entre rasgos de personalidad y habilidades.
        """
        try:
            return self.model.calculate_trait_skill_compatibility(traits, skills)
        except Exception as e:
            logger.error(f"Error calculando compatibilidad: {str(e)}")
            return {}
            
    def _identify_integrated_strengths(self, traits: Dict[str, float], 
                                     skills: Dict[str, float]) -> List[str]:
        """
        Identifica fortalezas integradas basadas en rasgos y habilidades.
        """
        try:
            return self.model.identify_integrated_strengths(traits, skills)
        except Exception as e:
            logger.error(f"Error identificando fortalezas: {str(e)}")
            return []
            
    def _identify_integrated_improvements(self, traits: Dict[str, float], 
                                       skills: Dict[str, float]) -> List[str]:
        """
        Identifica áreas de mejora integradas basadas en rasgos y habilidades.
        """
        try:
            return self.model.identify_integrated_improvements(traits, skills)
        except Exception as e:
            logger.error(f"Error identificando mejoras: {str(e)}")
            return []
            
    def _determine_personality_type(self, traits: Dict[str, float]) -> str:
        """
        Determina el tipo de personalidad basado en los rasgos.
        """
        try:
            return self.model.determine_personality_type(traits)
        except Exception as e:
            logger.error(f"Error determinando tipo de personalidad: {str(e)}")
            return 'Unknown'
            
    def _generate_integrated_recommendations(self, personality_results: Dict[str, Any],
                                          professional_results: Dict[str, Any],
                                          business_unit: Optional[BusinessUnit] = None) -> List[str]:
        """
        Genera recomendaciones integradas basadas en ambos análisis.
        """
        try:
            return self.model.generate_integrated_recommendations(
                personality_results,
                professional_results,
                business_unit
            )
        except Exception as e:
            logger.error(f"Error generando recomendaciones integradas: {str(e)}")
            return []
        
    def _calculate_overall_match(self, analyses: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Calculate overall match score across all assessment dimensions.
        
        Args:
            analyses: Dictionary containing results from individual analyzers
            business_unit: Business unit context
            
        Returns:
            Dict with overall match information
        """
        # Define dimension weights by business unit
        dimension_weights = {
            'huntRED': {
                'personality': 0.2,
                'professional_dna': 0.3,
                'cultural_fit': 0.2,
                'talent': 0.3
            },
            'huntU': {
                'personality': 0.2,
                'professional_dna': 0.2,
                'cultural_fit': 0.2,
                'talent': 0.4
            },
            'Amigro': {
                'personality': 0.3,
                'professional_dna': 0.2,
                'cultural_fit': 0.3,
                'talent': 0.2
            },
            'SEXSI': {
                'personality': 0.3,
                'professional_dna': 0.2,
                'cultural_fit': 0.3,
                'talent': 0.2
            }
        }
        
        # Get BU name and weights
        bu_name = self.get_business_unit_name(business_unit)
        weights = dimension_weights.get(bu_name, dimension_weights['huntRED'])
        
        # Extract scores from each analysis
        scores = {}
        
        if 'personality' in analyses:
            personality = analyses['personality']
            if 'traits' in personality:
                # Calculate average of trait scores
                trait_scores = personality['traits'].values()
                scores['personality'] = sum(trait_scores) / len(trait_scores) if trait_scores else 0.6
                
        if 'professional_dna' in analyses:
            prof_dna = analyses['professional_dna']
            if 'overall_score' in prof_dna:
                scores['professional_dna'] = prof_dna['overall_score'] / 100  # Convert to 0-1 scale
                
        if 'cultural_fit' in analyses:
            cultural = analyses['cultural_fit']
            if 'overall_fit' in cultural:
                scores['cultural_fit'] = cultural['overall_fit']
                
        if 'talent' in analyses:
            talent = analyses['talent']
            if 'overall_skill_level' in talent:
                scores['talent'] = talent['overall_skill_level']
                
        # Calculate weighted score
        weighted_sum = 0
        total_weight = 0
        
        for dimension, weight in weights.items():
            if dimension in scores:
                weighted_sum += scores[dimension] * weight
                total_weight += weight
                
        # Calculate overall match
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.5
        
        # Determine match level
        if overall_score >= 0.85:
            match_level = "Excepcional"
            match_description = "Candidato ideal con excelente alineación en todas las dimensiones clave"
        elif overall_score >= 0.75:
            match_level = "Excelente"
            match_description = "Candidato muy fuerte con alta alineación en la mayoría de dimensiones"
        elif overall_score >= 0.65:
            match_level = "Muy bueno"
            match_description = "Candidato sólido con buena alineación en dimensiones importantes"
        elif overall_score >= 0.55:
            match_level = "Bueno"
            match_description = "Candidato con potencial, alineación adecuada en algunas dimensiones clave"
        else:
            match_level = "Moderado"
            match_description = "Candidato con alineación limitada, requiere evaluación adicional"
            
        return {
            'score': overall_score,
            'percentage': int(overall_score * 100),
            'level': match_level,
            'description': match_description,
            'dimension_scores': scores
        }
