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
from app.ml.analyzers.base_analyzer import BaseAnalyzer
from app.ml.analyzers.personality_analyzer import PersonalityAnalyzer
from app.ml.analyzers.cultural_analyzer import CulturalAnalyzer
from app.ml.analyzers.professional_analyzer import ProfessionalAnalyzer
from app.ml.analyzers.talent_analyzer import TalentAnalyzer

logger = logging.getLogger(__name__)

class IntegratedAnalyzer(BaseAnalyzer):
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
            integrated_results['recommendations'] = self._generate_recommendations(
                personality_results, 
                cultural_results,
                professional_results,
                talent_results,
                integrated_results['development_areas'],
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
        # Deduplicate strengths
        insights['key_strengths'] = list(set(strengths))[:5]  # Top 5 unique strengths
        
        # Collect development areas from all analyses
        development_areas = []
        
        if 'personality' in analyses:
            personality_insights = analyses['personality'].get('insights', {})
            development_areas.extend(personality_insights.get('areas_improvement', []))
            
        if 'professional_dna' in analyses:
            prof_areas = analyses['professional_dna'].get('development_areas', [])
            development_areas.extend([a.replace('_', ' ').title() for a in prof_areas])
            
        if 'talent' in analyses and 'skill_gaps' in analyses['talent']:
            talent_gaps = analyses['talent'].get('skill_gaps', [])
            development_areas.extend([gap['skill'] for gap in talent_gaps if gap['gap_level'] == 'Significativo'])
            
        # Deduplicate development areas
        insights['development_priorities'] = list(set(development_areas))[:3]  # Top 3 unique priorities
        
        # Generate compatibility factors
        compatibility = {}
        
        if 'cultural_fit' in analyses:
            cultural = analyses['cultural_fit']
            if 'insights' in cultural and 'values_alignment' in cultural['insights']:
                compatibility['values_alignment'] = cultural['insights']['values_alignment']
                
            if 'insights' in cultural and 'workstyle_match' in cultural['insights']:
                compatibility['workstyle'] = cultural['insights']['workstyle_match']
                
        if 'professional_dna' in analyses:
            prof_dna = analyses['professional_dna']
            if 'career_recommendations' in prof_dna:
                top_role = prof_dna['career_recommendations'][0] if prof_dna['career_recommendations'] else {}
                if top_role:
                    compatibility['role_fit'] = {
                        'role': top_role.get('role', ''),
                        'match_level': top_role.get('match_level', ''),
                        'match_percentage': top_role.get('match_percentage', 0)
                    }
                    
        insights['compatibility_factors'] = compatibility
        
        # Generate profile summary
        profile_summary = self._generate_profile_summary(analyses)
        insights['profile_summary'] = profile_summary
        
        return insights
        
    def _generate_profile_summary(self, analyses: Dict) -> str:
        """
        Generate a concise profile summary from all analyses.
        
        Args:
            analyses: Dictionary containing results from individual analyzers
            
        Returns:
            String with integrated profile summary
        """
        summary_parts = []
        
        # Add personality insights
        if 'personality' in analyses:
            personality = analyses['personality']
            traits = personality.get('traits', {})
            
            # Find dominant traits (top 2)
            dominant_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)[:2]
            dom_trait_names = [t[0].replace('_', ' ').title() for t in dominant_traits]
            
            if dom_trait_names:
                summary_parts.append(f"Perfil caracterizado por alta {' y '.join(dom_trait_names)}")
                
        # Add professional DNA insights
        if 'professional_dna' in analyses:
            prof_dna = analyses['professional_dna']
            strengths = prof_dna.get('strengths', [])
            
            if strengths:
                strength_names = [s.replace('_', ' ').title() for s in strengths[:2]]
                summary_parts.append(f"Destacado en {' y '.join(strength_names)}")
                
        # Add cultural fit insights
        if 'cultural_fit' in analyses:
            cultural = analyses['cultural_fit']
            if 'insights' in cultural and 'values_alignment' in cultural['insights']:
                alignment = cultural['insights']['values_alignment']
                summary_parts.append(f"Alineación cultural {alignment.get('level', 'Moderada').lower()}")
                
        # Add talent insights
        if 'talent' in analyses:
            talent = analyses['talent']
            if 'growth_potential' in talent:
                potential = talent['growth_potential']
                summary_parts.append(f"Potencial de desarrollo {potential.get('potential_level', 'Moderado').lower()}")
                
        # Combine parts into coherent summary
        if summary_parts:
            summary = "Profesional con " + ", ".join(summary_parts) + "."
        else:
            summary = "Perfil profesional balanceado con potencial de desarrollo en múltiples áreas."
            
        return summary
        
    def _generate_integrated_recommendations(self, analyses: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Generate integrated recommendations from all analyses.
        
        Args:
            analyses: Dictionary containing results from individual analyzers
            business_unit: Business unit context
            
        Returns:
            Dict with integrated recommendations
        """
        recommendations = {
            'career_path': [],
            'development_plan': [],
            'interview_focus': []
        }
        
        bu_name = self.get_business_unit_name(business_unit)
        
        # Collect career recommendations
        career_recs = []
        
        if 'professional_dna' in analyses and 'career_recommendations' in analyses['professional_dna']:
            prof_careers = analyses['professional_dna']['career_recommendations']
            career_recs.extend([
                {
                    'role': rec['role'],
                    'match': rec['match_percentage'],
                    'source': 'professional_dna'
                }
                for rec in prof_careers if 'role' in rec
            ])
            
        if 'talent' in analyses and 'role_recommendations' in analyses['talent']:
            talent_roles = analyses['talent']['role_recommendations']
            career_recs.extend([
                {
                    'role': rec['role'],
                    'match': rec['match_percentage'],
                    'source': 'talent'
                }
                for rec in talent_roles if 'role' in rec
            ])
            
        # Deduplicate and sort career recommendations
        unique_roles = {}
        for rec in career_recs:
            role = rec['role']
            if role not in unique_roles or rec['match'] > unique_roles[role]['match']:
                unique_roles[role] = rec
                
        # Format top 3 career recommendations
        recommendations['career_path'] = [
            f"{rec['role']} ({int(rec['match'])}% match)"
            for rec in sorted(unique_roles.values(), key=lambda x: x['match'], reverse=True)[:3]
        ]
        
        # Collect development recommendations
        dev_recs = []
        
        if 'professional_dna' in analyses and 'development_recommendations' in analyses['professional_dna']:
            dev_recs.extend(analyses['professional_dna']['development_recommendations'])
            
        if 'talent' in analyses and 'development_recommendations' in analyses['talent']:
            dev_recs.extend(analyses['talent']['development_recommendations'])
            
        if 'cultural_fit' in analyses and 'recommendations' in analyses['cultural_fit']:
            dev_recs.extend(analyses['cultural_fit']['recommendations'])
            
        # Deduplicate development recommendations
        recommendations['development_plan'] = list(set(dev_recs))[:5]  # Top 5 unique recommendations
        
        # Generate interview focus areas
        interview_focus = []
        
        # Add focus based on development areas
        if 'development_priorities' in self._generate_integrated_insights(analyses):
            dev_priorities = self._generate_integrated_insights(analyses)['development_priorities']
            for priority in dev_priorities[:2]:  # Top 2 priorities
                interview_focus.append(f"Explorar experiencia en {priority}")
                
        # Add focus based on cultural fit
        if 'cultural_fit' in analyses and 'overall_fit' in analyses['cultural_fit']:
            cultural_fit = analyses['cultural_fit']['overall_fit']
            if cultural_fit < 0.7:  # If cultural fit is below 70%
                interview_focus.append("Profundizar en alineación cultural y valores")
                
        # Add focus based on skill gaps
        if 'talent' in analyses and 'skill_gaps' in analyses['talent']:
            skill_gaps = analyses['talent']['skill_gaps']
            for gap in skill_gaps[:1]:  # Top gap
                interview_focus.append(f"Validar nivel actual en {gap['skill']}")
                
        # Add BU-specific interview focus
        bu_focus = {
            'huntRED': "Evaluar capacidad de pensamiento estratégico y toma de decisiones ejecutivas",
            'huntU': "Explorar conocimientos técnicos actualizados y capacidad de aprendizaje continuo",
            'Amigro': "Verificar experiencia en entornos diversos y resolución práctica de problemas",
            'SEXSI': "Validar manejo de confidencialidad y situaciones profesionales complejas"
        }
        
        if bu_name in bu_focus:
            interview_focus.append(bu_focus[bu_name])
            
        # Ensure we have at least 3 interview focus areas
        if len(interview_focus) < 3:
            general_focus = [
                "Explorar motivaciones y expectativas profesionales",
                "Evaluar capacidad de adaptación a la cultura organizacional",
                "Validar experiencia práctica con ejemplos concretos"
            ]
            
            for focus in general_focus:
                if len(interview_focus) < 3 and focus not in interview_focus:
                    interview_focus.append(focus)
                    
        recommendations['interview_focus'] = interview_focus
        
        return recommendations
        
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
