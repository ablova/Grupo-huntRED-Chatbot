# /home/pablo/app/ml/analyzers/team_analyzer.py
"""
Team Analyzer module for Grupo huntRED® assessment system.

This module analyzes optimal team composition based on multiple factors
such as skills, personality, generation, and professional purpose.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import random

import numpy as np
from django.conf import settings

from app.models import Person, Skill, SkillAssessment, BusinessUnit
from app.ats.ml.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class TeamAnalyzerImpl(BaseAnalyzer):
    """
    Analyzer for team composition and synergy optimization.
    
    Evaluates team dynamics based on multiple dimensions including skills,
    personality, generation, and work style to recommend optimal compositions.
    """
    
    # Team synergy factors and weights
    SYNERGY_FACTORS = {
        'skill_coverage': 0.25,
        'personality_balance': 0.20,
        'generational_diversity': 0.15,
        'work_style_compatibility': 0.15,
        'experience_distribution': 0.15,
        'cultural_cohesion': 0.10
    }
    
    # Personality types and complementary relationships
    PERSONALITY_TYPES = {
        'Analítico': {'complementary': ['Expresivo', 'Directivo'], 'conflicting': []},
        'Expresivo': {'complementary': ['Afable', 'Analítico'], 'conflicting': []},
        'Afable': {'complementary': ['Expresivo', 'Directivo'], 'conflicting': []},
        'Directivo': {'complementary': ['Analítico', 'Afable'], 'conflicting': []}
    }
    
    # Generational categories
    GENERATIONS = {
        'Baby Boomers': {'year_start': 1946, 'year_end': 1964},
        'Generación X': {'year_start': 1965, 'year_end': 1980},
        'Millennials': {'year_start': 1981, 'year_end': 1996},
        'Generación Z': {'year_start': 1997, 'year_end': 2012}
    }
    
    def __init__(self):
        """Initialize the team analyzer."""
        super().__init__()

    def get_required_fields(self) -> List[str]:
        """Get required fields for team analysis."""
        return ['team_members']
        
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analyze team synergy and composition optimization.
        
        Args:
            data: Dictionary containing team_members (list of person IDs)
            business_unit: Business unit context for analysis
            
        Returns:
            Dict with team analysis and optimization recommendations
        """
        try:
            # Check cache first
            team_members = data.get('team_members', [])
            if not team_members:
                return self.get_default_result("No team members provided")
                
            cache_key = f"team_analysis_{'-'.join(map(str, sorted(team_members)))}"
            cached_result = self.get_cached_result(data, cache_key)
            if cached_result:
                return cached_result
                
            # Validate input
            is_valid, error_message = self.validate_input(data)
            if not is_valid:
                logger.warning(f"Invalid input for team analysis: {error_message}")
                return self.get_default_result(error_message)
                
            # Get business unit context
            bu_name = self.get_business_unit_name(business_unit)
                
            # Get team member data
            team_data = self._get_team_data(team_members)
            if not team_data or len(team_data) < 2:
                return self.get_default_result("Insufficient team data")
                
            # Analyze current team composition
            composition_analysis = self._analyze_team_composition(team_data)
            
            # Analyze team synergy
            synergy_analysis = self._analyze_team_synergy(team_data)
            
            # Identify synergy gaps
            synergy_gaps = self._identify_synergy_gaps(synergy_analysis)
            
            # Generate optimization recommendations
            optimization_recommendations = self._generate_optimization_recommendations(
                team_data,
                composition_analysis,
                synergy_gaps
            )
            
            # Calculate overall synergy score
            overall_score = self._calculate_overall_synergy_score(synergy_analysis)
            
            # Visualize team dynamics
            team_visualization = self._generate_team_visualization(team_data, synergy_analysis)
            
            # Compile results
            result = {
                'team_members': team_members,
                'team_size': len(team_members),
                'composition_analysis': composition_analysis,
                'synergy_analysis': synergy_analysis,
                'synergy_gaps': synergy_gaps,
                'optimization_recommendations': optimization_recommendations,
                'overall_synergy_score': overall_score,
                'team_visualization': team_visualization,
                'business_unit': bu_name,
                'analyzed_at': datetime.now().isoformat()
            }
            
            # Cache result
            self.set_cached_result(data, result, cache_key)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in team analysis: {str(e)}")
            return self.get_default_result(f"Analysis error: {str(e)}")
    def _get_team_data(self, team_members: List[int]) -> List[Dict]:
        """
        Get data for all team members.
        
        Args:
            team_members: List of person IDs
            
        Returns:
            List of team member data
        """
        team_data = []
        
        for person_id in team_members:
            # In a real implementation, this would retrieve person data from the database
            # For simulation, we'll generate mock data that's deterministic based on ID
            random.seed(person_id)
            
            # Generate birth year for generational analysis
            birth_year = random.randint(1960, 2000)
            generation = self._determine_generation(birth_year)
            
            # Generate personality type
            personality_types = list(self.PERSONALITY_TYPES.keys())
            personality_type = personality_types[person_id % len(personality_types)]
            
            # Generate work style
            work_styles = ["Colaborativo", "Independiente", "Estructurado", "Flexible"]
            work_style = work_styles[person_id % len(work_styles)]
            
            # Generate years of experience
            years_experience = random.randint(1, 25)
            
            # Generate skills
            skills = self._generate_skills(person_id, 5 + (person_id % 3))
            
            # Compile person data
            person_data = {
                'id': person_id,
                'name': f"Person {person_id}",
                'birth_year': birth_year,
                'generation': generation,
                'personality_type': personality_type,
                'work_style': work_style,
                'years_experience': years_experience,
                'skills': skills,
                'cultural_values': self._generate_cultural_values(person_id)
            }
            
            team_data.append(person_data)
        
        return team_data
        
    def _determine_generation(self, birth_year: int) -> str:
        """
        Determine generation based on birth year.
        
        Args:
            birth_year: Year of birth
            
        Returns:
            Generation name
        """
        for gen_name, gen_range in self.GENERATIONS.items():
            if gen_range['year_start'] <= birth_year <= gen_range['year_end']:
                return gen_name
        
        return "Otra generación"
        
    def _generate_skills(self, person_id: int, num_skills: int) -> List[Dict]:
        """
        Generate skills for a person.
        
        Args:
            person_id: Person ID
            num_skills: Number of skills to generate
            
        Returns:
            List of skills
        """
        random.seed(person_id)
        
        all_skills = [
            "Liderazgo", "Comunicación", "Gestión de Proyectos", "Análisis de Datos",
            "Programación", "Diseño UX", "Marketing Digital", "Ventas", "Negociación",
            "Finanzas", "Recursos Humanos", "Estrategia", "Innovación", "Trabajo en Equipo",
            "Resolución de Problemas", "Pensamiento Crítico", "Gestión del Tiempo",
            "Presentaciones", "Redes Sociales", "SEO", "Cloud Computing", "Machine Learning",
            "Business Intelligence", "Gestión de Cambio", "Coaching", "Mentoría"
        ]
        
        # Select random skills
        selected_skills = random.sample(all_skills, min(num_skills, len(all_skills)))
        
        # Create skill objects
        skills = []
        for skill in selected_skills:
            level = random.randint(50, 95)
            skills.append({
                'name': skill,
                'level': level,
                'years': random.randint(1, 5)
            })
        
        return skills
        
    def _generate_cultural_values(self, person_id: int) -> List[str]:
        """
        Generate cultural values for a person.
        
        Args:
            person_id: Person ID
            
        Returns:
            List of cultural values
        """
        random.seed(person_id)
        
        all_values = [
            "Innovación", "Colaboración", "Excelencia", "Integridad", "Respeto",
            "Responsabilidad", "Transparencia", "Diversidad", "Pasión", "Servicio",
            "Aprendizaje", "Balance", "Creatividad", "Empatía", "Resiliencia"
        ]
        
        # Select 3-5 values
        num_values = random.randint(3, 5)
        return random.sample(all_values, num_values)

    def _analyze_team_composition(self, team_data: List[Dict]) -> Dict:
        """
        Analyze current team composition.
        
        Args:
            team_data: Team member data
            
        Returns:
            Dict with composition analysis
        """
        # Analyze personality distribution
        personality_distribution = {}
        for person in team_data:
            p_type = person.get('personality_type', 'Unknown')
            personality_distribution[p_type] = personality_distribution.get(p_type, 0) + 1
            
        # Analyze generational distribution
        generational_distribution = {}
        for person in team_data:
            gen = person.get('generation', 'Unknown')
            generational_distribution[gen] = generational_distribution.get(gen, 0) + 1
            
        # Analyze work style distribution
        work_style_distribution = {}
        for person in team_data:
            style = person.get('work_style', 'Unknown')
            work_style_distribution[style] = work_style_distribution.get(style, 0) + 1
            
        # Analyze experience distribution
        experience_levels = {
            'Junior (0-3 años)': 0,
            'Semi-Senior (4-7 años)': 0,
            'Senior (8-12 años)': 0,
            'Experto (13+ años)': 0
        }
        
        for person in team_data:
            years = person.get('years_experience', 0)
            if years <= 3:
                experience_levels['Junior (0-3 años)'] += 1
            elif years <= 7:
                experience_levels['Semi-Senior (4-7 años)'] += 1
            elif years <= 12:
                experience_levels['Senior (8-12 años)'] += 1
            else:
                experience_levels['Experto (13+ años)'] += 1
                
        # Analyze skill coverage
        all_skills = {}
        for person in team_data:
            for skill in person.get('skills', []):
                skill_name = skill.get('name')
                if skill_name not in all_skills:
                    all_skills[skill_name] = []
                all_skills[skill_name].append({
                    'person_id': person.get('id'),
                    'level': skill.get('level', 0)
                })
                
        # Calculate skill coverage metrics
        skill_coverage = {
            'unique_skills': len(all_skills),
            'redundant_skills': len([s for s in all_skills.values() if len(s) > 1]),
            'coverage_percentage': min(100, len(all_skills) * 100 / 26),  # 26 is max skills in our list
            'skill_details': all_skills
        }
            
        return {
            'personality_distribution': personality_distribution,
            'generational_distribution': generational_distribution,
            'work_style_distribution': work_style_distribution,
            'experience_levels': experience_levels,
            'skill_coverage': skill_coverage,
            'team_size': len(team_data)
        }
        
    def _analyze_team_synergy(self, team_data: List[Dict]) -> Dict:
        """
        Analyze team synergy based on multiple factors.
        
        Args:
            team_data: Team member data
            
        Returns:
            Dict with synergy analysis
        """
        # Analyze skill coverage synergy
        skill_coverage_score = self._analyze_skill_coverage_synergy(team_data)
        
        # Analyze personality balance synergy
        personality_balance_score = self._analyze_personality_balance_synergy(team_data)
        
        # Analyze generational diversity synergy
        generational_diversity_score = self._analyze_generational_diversity_synergy(team_data)
        
        # Analyze work style compatibility synergy
        work_style_compatibility_score = self._analyze_work_style_compatibility_synergy(team_data)
        
        # Analyze experience distribution synergy
        experience_distribution_score = self._analyze_experience_distribution_synergy(team_data)
        
        # Analyze cultural cohesion synergy
        cultural_cohesion_score = self._analyze_cultural_cohesion_synergy(team_data)
        
        # Compile synergy factors
        synergy_factors = {
            'skill_coverage': skill_coverage_score,
            'personality_balance': personality_balance_score,
            'generational_diversity': generational_diversity_score,
            'work_style_compatibility': work_style_compatibility_score,
            'experience_distribution': experience_distribution_score,
            'cultural_cohesion': cultural_cohesion_score
        }
        
        return synergy_factors

    def _analyze_skill_coverage_synergy(self, team_data: List[Dict]) -> Dict:
        """
        Analyze skill coverage synergy.
        
        Args:
            team_data: Team member data
            
        Returns:
            Dict with skill coverage synergy analysis
        """
        # Collect all skills across team
        all_skills = {}
        for person in team_data:
            for skill in person.get('skills', []):
                skill_name = skill.get('name')
                if skill_name not in all_skills:
                    all_skills[skill_name] = []
                all_skills[skill_name].append({
                    'person_id': person.get('id'),
                    'level': skill.get('level', 0)
                })
        
        # Calculate coverage metrics
        total_possible_skills = 26  # From our skill list
        unique_skills_count = len(all_skills)
        coverage_ratio = unique_skills_count / total_possible_skills
        
        # Calculate redundancy (how many skills have multiple people)
        redundant_skills = [s for s in all_skills.values() if len(s) > 1]
        redundancy_ratio = len(redundant_skills) / unique_skills_count if unique_skills_count > 0 else 0
        
        # Calculate average skill level
        all_levels = []
        for skill_holders in all_skills.values():
            for holder in skill_holders:
                all_levels.append(holder.get('level', 0))
        avg_skill_level = sum(all_levels) / len(all_levels) if all_levels else 0
        
        # Calculate final score
        # Good coverage: high unique skills, moderate redundancy, high avg level
        coverage_score = coverage_ratio * 40 + redundancy_ratio * 30 + (avg_skill_level / 100) * 30
        coverage_score = min(100, coverage_score * 1.2)  # Scale to 100
        
        return {
            'score': coverage_score,
            'unique_skills_count': unique_skills_count,
            'coverage_ratio': coverage_ratio,
            'redundancy_ratio': redundancy_ratio,
            'avg_skill_level': avg_skill_level,
            'analysis': self._get_skill_coverage_analysis(coverage_score)
        }
        
    def _analyze_personality_balance_synergy(self, team_data: List[Dict]) -> Dict:
        """
        Analyze personality balance synergy.
        
        Args:
            team_data: Team member data
            
        Returns:
            Dict with personality balance synergy analysis
        """
        # Count personality types
        personality_counts = {}
        for person in team_data:
            p_type = person.get('personality_type', 'Unknown')
            personality_counts[p_type] = personality_counts.get(p_type, 0) + 1
        
        # Calculate distribution evenness
        team_size = len(team_data)
        ideal_count = team_size / len(self.PERSONALITY_TYPES)
        deviation = sum(abs(count - ideal_count) for count in personality_counts.values())
        distribution_score = 100 - (deviation * 100 / team_size)
        
        # Calculate complementary pairs
        complementary_pairs = 0
        for i, person1 in enumerate(team_data):
            for person2 in team_data[i+1:]:
                p1_type = person1.get('personality_type')
                p2_type = person2.get('personality_type')
                
                if p1_type and p2_type:
                    if p2_type in self.PERSONALITY_TYPES.get(p1_type, {}).get('complementary', []):
                        complementary_pairs += 1
        
        max_pairs = (team_size * (team_size - 1)) / 2
        complementary_ratio = complementary_pairs / max_pairs if max_pairs > 0 else 0
        
        # Calculate final score
        balance_score = distribution_score * 0.4 + complementary_ratio * 100 * 0.6
        
        return {
            'score': balance_score,
            'personality_counts': personality_counts,
            'distribution_score': distribution_score,
            'complementary_pairs': complementary_pairs,
            'complementary_ratio': complementary_ratio,
            'analysis': self._get_personality_balance_analysis(balance_score, personality_counts)
        }

    def _analyze_generational_diversity_synergy(self, team_data: List[Dict]) -> Dict:
        """
        Analyze generational diversity synergy.
        
        Args:
            team_data: Team member data
            
        Returns:
            Dict with generational diversity synergy analysis
        """
        # Count generations
        generation_counts = {}
        for person in team_data:
            gen = person.get('generation', 'Unknown')
            generation_counts[gen] = generation_counts.get(gen, 0) + 1
        
        # Calculate diversity score
        team_size = len(team_data)
        diversity_ratio = len(generation_counts) / len(self.GENERATIONS)
        
        # Calculate distribution evenness
        ideal_count = team_size / len(generation_counts) if generation_counts else 0
        deviation = sum(abs(count - ideal_count) for count in generation_counts.values())
        distribution_score = 100 - (deviation * 100 / team_size) if team_size > 0 else 0
        
        # We want some diversity but not too much fragmentation
        # Optimal: 2-3 generations with reasonable distribution
        if len(generation_counts) == 1:
            # Single generation: limited perspective
            gen_score = 50
        elif len(generation_counts) == 2:
            # Two generations: good balance
            gen_score = 85
        elif len(generation_counts) == 3:
            # Three generations: excellent diversity
            gen_score = 95
        else:
            # Four or more: might be too fragmented
            gen_score = 75
        
        # Adjust based on distribution
        final_score = gen_score * 0.7 + distribution_score * 0.3
        
        return {
            'score': final_score,
            'generation_counts': generation_counts,
            'diversity_ratio': diversity_ratio,
            'distribution_score': distribution_score,
            'analysis': self._get_generational_diversity_analysis(final_score, generation_counts)
        }
        
    def _analyze_work_style_compatibility_synergy(self, team_data: List[Dict]) -> Dict:
        """
        Analyze work style compatibility synergy.
        
        Args:
            team_data: Team member data
            
        Returns:
            Dict with work style compatibility synergy analysis
        """
        # Count work styles
        work_style_counts = {}
        for person in team_data:
            style = person.get('work_style', 'Unknown')
            work_style_counts[style] = work_style_counts.get(style, 0) + 1
        
        # Calculate balance score
        # Ideal mix: Collaborative (40%), Structured (25%), Independent (20%), Flexible (15%)
        ideal_mix = {
            'Colaborativo': 0.40,
            'Estructurado': 0.25,
            'Independiente': 0.20,
            'Flexible': 0.15
        }
        
        team_size = len(team_data)
        deviation = 0
        
        for style, ideal_ratio in ideal_mix.items():
            actual_count = work_style_counts.get(style, 0)
            ideal_count = ideal_ratio * team_size
            deviation += abs(actual_count - ideal_count)
        
        balance_score = 100 - (deviation * 100 / team_size) if team_size > 0 else 0
        
        # Calculate compatibility score
        # Some work styles complement each other, some conflict
        complementary_pairs = {
            ('Colaborativo', 'Flexible'): 1.0,
            ('Estructurado', 'Colaborativo'): 0.8,
            ('Independiente', 'Estructurado'): 0.7,
            ('Flexible', 'Independiente'): 0.6
        }
        
        compatibility_score = 0
        pair_count = 0
        
        for i, person1 in enumerate(team_data):
            for person2 in team_data[i+1:]:
                style1 = person1.get('work_style')
                style2 = person2.get('work_style')
                
                if style1 and style2:
                    pair = (style1, style2)
                    reverse_pair = (style2, style1)
                    
                    if pair in complementary_pairs:
                        compatibility_score += complementary_pairs[pair]
                    elif reverse_pair in complementary_pairs:
                        compatibility_score += complementary_pairs[reverse_pair]
                    else:
                        compatibility_score += 0.5  # Neutral compatibility
                    
                    pair_count += 1
        
        avg_compatibility = compatibility_score / pair_count if pair_count > 0 else 0
        
        # Calculate final score
        final_score = balance_score * 0.4 + avg_compatibility * 100 * 0.6
        
        return {
            'score': final_score,
            'work_style_counts': work_style_counts,
            'balance_score': balance_score,
            'avg_compatibility': avg_compatibility,
            'analysis': self._get_work_style_analysis(final_score, work_style_counts)
        }

    def _analyze_experience_distribution_synergy(self, team_data: List[Dict]) -> Dict:
        """
        Analyze experience distribution synergy.
        
        Args:
            team_data: Team member data
            
        Returns:
            Dict with experience distribution synergy analysis
        """
        # Categorize experience levels
        experience_levels = {
            'Junior (0-3 años)': 0,
            'Semi-Senior (4-7 años)': 0,
            'Senior (8-12 años)': 0,
            'Experto (13+ años)': 0
        }
        
        for person in team_data:
            years = person.get('years_experience', 0)
            if years <= 3:
                experience_levels['Junior (0-3 años)'] += 1
            elif years <= 7:
                experience_levels['Semi-Senior (4-7 años)'] += 1
            elif years <= 12:
                experience_levels['Senior (8-12 años)'] += 1
            else:
                experience_levels['Experto (13+ años)'] += 1
        
        # Calculate distribution score
        # Ideal distribution: Senior (30%), Semi-Senior (40%), Junior (20%), Expert (10%)
        ideal_distribution = {
            'Junior (0-3 años)': 0.20,
            'Semi-Senior (4-7 años)': 0.40,
            'Senior (8-12 años)': 0.30,
            'Experto (13+ años)': 0.10
        }
        
        team_size = len(team_data)
        deviation = 0
        
        for level, ideal_ratio in ideal_distribution.items():
            actual_count = experience_levels.get(level, 0)
            ideal_count = ideal_ratio * team_size
            deviation += abs(actual_count - ideal_count)
        
        distribution_score = 100 - (deviation * 100 / team_size) if team_size > 0 else 0
        
        # Calculate experience mix score
        # Check if we have at least one senior/expert and a good mix of others
        has_expert = experience_levels['Experto (13+ años)'] > 0
        has_senior = experience_levels['Senior (8-12 años)'] > 0
        has_junior = experience_levels['Junior (0-3 años)'] > 0
        has_semi = experience_levels['Semi-Senior (4-7 años)'] > 0
        
        mix_score = 0
        if has_expert:
            mix_score += 25
        if has_senior:
            mix_score += 25
        if has_junior:
            mix_score += 25
        if has_semi:
            mix_score += 25
        
        # Calculate final score
        final_score = distribution_score * 0.6 + mix_score * 0.4
        
        return {
            'score': final_score,
            'experience_levels': experience_levels,
            'distribution_score': distribution_score,
            'mix_score': mix_score,
            'analysis': self._get_experience_distribution_analysis(final_score, experience_levels)
        }
        
    def _analyze_cultural_cohesion_synergy(self, team_data: List[Dict]) -> Dict:
        """
        Analyze cultural cohesion synergy.
        
        Args:
            team_data: Team member data
            
        Returns:
            Dict with cultural cohesion synergy analysis
        """
        # Collect all cultural values
        all_values = {}
        for person in team_data:
            for value in person.get('cultural_values', []):
                all_values[value] = all_values.get(value, 0) + 1
        
        # Calculate shared values
        team_size = len(team_data)
        shared_values = [value for value, count in all_values.items() if count > team_size / 2]
        
        # Calculate cohesion score
        if team_size <= 1:
            cohesion_score = 100  # Single person is always cohesive
        else:
            # More shared values = higher cohesion
            shared_ratio = len(shared_values) / len(all_values) if all_values else 0
            
            # We want some shared values but also some diversity
            # Optimal: 30-40% shared values
            if shared_ratio < 0.2:
                cohesion_score = 60  # Too little sharing
            elif shared_ratio < 0.3:
                cohesion_score = 80  # Good balance
            elif shared_ratio < 0.5:
                cohesion_score = 95  # Ideal balance
            else:
                cohesion_score = 70  # Too homogeneous
        
        return {
            'score': cohesion_score,
            'all_values': all_values,
            'shared_values': shared_values,
            'shared_ratio': len(shared_values) / len(all_values) if all_values else 0,
            'analysis': self._get_cultural_cohesion_analysis(cohesion_score, shared_values)
        }

    def _identify_synergy_gaps(self, synergy_analysis: Dict) -> List[Dict]:
        """
        Identify synergy gaps that need improvement.
        
        Args:
            synergy_analysis: Synergy analysis data
            
        Returns:
            List of synergy gaps
        """
        gaps = []
        
        for factor, analysis in synergy_analysis.items():
            score = analysis.get('score', 0)
            
            if score < 60:
                severity = "high"
            elif score < 75:
                severity = "medium"
            else:
                continue  # No significant gap
            
            gaps.append({
                'factor': factor,
                'score': score,
                'severity': severity,
                'analysis': analysis
            })
        
        return sorted(gaps, key=lambda x: (0 if x['severity'] == 'high' else 1, x['score']))
            
    def _generate_optimization_recommendations(self, team_data: List[Dict], 
                                            composition_analysis: Dict,
                                            synergy_gaps: List[Dict]) -> List[Dict]:
        """
        Generate team optimization recommendations.
        
        Args:
            team_data: Team member data
            composition_analysis: Team composition analysis
            synergy_gaps: Identified synergy gaps
            
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        # Generate recommendations based on synergy gaps
        for gap in synergy_gaps:
            factor = gap.get('factor')
            severity = gap.get('severity')
            
            if factor == 'skill_coverage':
                recommendations.append({
                    'category': 'Habilidades',
                    'recommendation': 'Ampliar la cobertura de habilidades del equipo',
                    'actions': [
                        'Incorporar persona con habilidades en áreas faltantes',
                        'Desarrollar capacitación cruzada entre miembros del equipo',
                        'Priorizar desarrollo de habilidades complementarias'
                    ],
                    'priority': 'high' if severity == 'high' else 'medium',
                    'impact': 'high'
                })
            
            elif factor == 'personality_balance':
                # Determine which personality types are missing or underrepresented
                personality_counts = composition_analysis.get('personality_distribution', {})
                missing_types = [p for p in self.PERSONALITY_TYPES if p not in personality_counts]
                
                recommendations.append({
                    'category': 'Personalidad',
                    'recommendation': 'Mejorar el balance de estilos de personalidad',
                    'actions': [
                        f"Incorporar persona con perfil {', '.join(missing_types)}" if missing_types else "Trabajar en técnicas de comunicación entre diferentes perfiles",
                        'Realizar talleres de trabajo en equipo para diferentes perfiles',
                        'Asignar roles según fortalezas de cada tipo de personalidad'
                    ],
                    'priority': 'high' if severity == 'high' else 'medium',
                    'impact': 'medium'
                })
            
            elif factor == 'generational_diversity':
                recommendations.append({
                    'category': 'Diversidad generacional',
                    'recommendation': 'Optimizar la mezcla generacional del equipo',
                    'actions': [
                        'Incorporar miembros de diferentes generaciones',
                        'Implementar programa de mentorías cruzadas entre generaciones',
                        'Adaptar estilos de comunicación para diferentes generaciones'
                    ],
                    'priority': 'medium',
                    'impact': 'medium'
                })
            
            elif factor == 'work_style_compatibility':
                recommendations.append({
                    'category': 'Estilos de trabajo',
                    'recommendation': 'Mejorar la compatibilidad de estilos de trabajo',
                    'actions': [
                        'Establecer protocolos de trabajo claros',
                        'Implementar metodologías adaptables a diferentes estilos',
                        'Capacitar en flexibilidad de estilos según tipo de tarea'
                    ],
                    'priority': 'high' if severity == 'high' else 'medium',
                    'impact': 'high'
                })
            
            elif factor == 'experience_distribution':
                recommendations.append({
                    'category': 'Distribución de experiencia',
                    'recommendation': 'Optimizar la distribución de niveles de experiencia',
                    'actions': [
                        'Incorporar miembros con experiencia complementaria',
                        'Implementar sistema de mentorías interno',
                        'Desarrollar plan de crecimiento para niveles junior'
                    ],
                    'priority': 'medium',
                    'impact': 'high'
                })
            
            elif factor == 'cultural_cohesion':
                recommendations.append({
                    'category': 'Cohesión cultural',
                    'recommendation': 'Fortalecer la cohesión cultural del equipo',
                    'actions': [
                        'Realizar actividades de team building enfocadas en valores',
                        'Definir y comunicar valores compartidos del equipo',
                        'Implementar rituales de equipo que refuercen la cultura'
                    ],
                    'priority': 'medium',
                    'impact': 'medium'
                })
        
        # If no gaps, add general enhancement recommendations
        if not recommendations:
            recommendations.append({
                'category': 'Mejora general',
                'recommendation': 'Potenciar las fortalezas existentes del equipo',
                'actions': [
                    'Implementar reconocimiento específico de fortalezas',
                    'Diseñar proyectos que aprovechen la composición actual',
                    'Realizar talleres para compartir conocimiento internamente'
                ],
                'priority': 'low',
                'impact': 'medium'
            })
        
        return recommendations

    def _calculate_overall_synergy_score(self, synergy_analysis: Dict) -> float:
        """
        Calculate overall synergy score based on weighted factors.
        
        Args:
            synergy_analysis: Synergy analysis data
            
        Returns:
            Overall synergy score
        """
        overall_score = 0
        
        for factor, weight in self.SYNERGY_FACTORS.items():
            factor_score = synergy_analysis.get(factor, {}).get('score', 0)
            overall_score += factor_score * weight
        
        return round(overall_score, 1)
        
    def _generate_team_visualization(self, team_data: List[Dict], synergy_analysis: Dict) -> Dict:
        """
        Generate team dynamics visualization data.
        
        Args:
            team_data: Team member data
            synergy_analysis: Synergy analysis data
            
        Returns:
            Dict with visualization data
        """
        # Generate nodes (team members)
        nodes = []
        for person in team_data:
            nodes.append({
                'id': person.get('id'),
                'name': person.get('name'),
                'personality_type': person.get('personality_type', 'Unknown'),
                'generation': person.get('generation', 'Unknown'),
                'experience_years': person.get('years_experience', 0),
                'top_skills': [s.get('name') for s in person.get('skills', [])[:3]]
            })
        
        # Generate edges (relationships between members)
        edges = []
        for i, person1 in enumerate(team_data):
            for j, person2 in enumerate(team_data[i+1:], i+1):
                # Calculate compatibility between these two members
                p1_type = person1.get('personality_type')
                p2_type = person2.get('personality_type')
                
                # Base compatibility
                compatibility = 0.5
                
                # Adjust based on personality
                if p1_type and p2_type:
                    if p2_type in self.PERSONALITY_TYPES.get(p1_type, {}).get('complementary', []):
                        compatibility += 0.2
                    elif p2_type in self.PERSONALITY_TYPES.get(p1_type, {}).get('conflicting', []):
                        compatibility -= 0.2
                
                # Adjust based on shared skills
                p1_skills = [s.get('name') for s in person1.get('skills', [])]
                p2_skills = [s.get('name') for s in person2.get('skills', [])]
                shared_skills = [s for s in p1_skills if s in p2_skills]
                
                if shared_skills:
                    compatibility += 0.1 * min(3, len(shared_skills)) / 3
                
                # Adjust based on generation
                if person1.get('generation') == person2.get('generation'):
                    compatibility += 0.1
                
                # Ensure compatibility is between 0 and 1
                compatibility = max(0.1, min(1.0, compatibility))
                
                edges.append({
                    'source': person1.get('id'),
                    'target': person2.get('id'),
                    'weight': compatibility,
                    'shared_skills': shared_skills
                })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'factors': {
                factor: analysis.get('score', 0)
                for factor, analysis in synergy_analysis.items()
            }
        }
        
    def _get_skill_coverage_analysis(self, score: float) -> str:
        """Get analysis text for skill coverage score."""
        if score < 50:
            return "Cobertura de habilidades limitada. El equipo carece de diversidad en competencias clave."
        elif score < 75:
            return "Cobertura de habilidades moderada. Hay áreas de mejora en la diversidad de competencias."
        else:
            return "Excelente cobertura de habilidades. El equipo cuenta con diversidad de competencias complementarias."
    
    def _get_personality_balance_analysis(self, score: float, counts: Dict) -> str:
        """Get analysis text for personality balance score."""
        if score < 50:
            return "Desequilibrio en perfiles de personalidad. El equipo puede beneficiarse de mayor diversidad."
        elif score < 75:
            return "Balance moderado de personalidades. Hay oportunidades para mejorar la complementariedad."
        else:
            return "Excelente balance de personalidades. El equipo tiene una mezcla óptima de perfiles complementarios."
    
    def _get_generational_diversity_analysis(self, score: float, counts: Dict) -> str:
        """Get analysis text for generational diversity score."""
        if score < 50:
            return "Baja diversidad generacional. El equipo puede beneficiarse de diferentes perspectivas."
        elif score < 75:
            return "Diversidad generacional moderada. Hay oportunidad para integrar otras generaciones."
        else:
            return "Excelente diversidad generacional. El equipo cuenta con una mezcla óptima de generaciones."
    
    def _get_work_style_analysis(self, score: float, counts: Dict) -> str:
        """Get analysis text for work style compatibility score."""
        if score < 50:
            return "Baja compatibilidad en estilos de trabajo. Puede generar fricciones en la dinámica del equipo."
        elif score < 75:
            return "Compatibilidad moderada en estilos de trabajo. Hay oportunidades para mejorar la integración."
        else:
            return "Excelente compatibilidad en estilos de trabajo. El equipo tiene una dinámica fluida."
    
    def _get_experience_distribution_analysis(self, score: float, levels: Dict) -> str:
        """Get analysis text for experience distribution score."""
        if score < 50:
            return "Distribución desequilibrada de experiencia. Falta variedad en niveles de seniority."
        elif score < 75:
            return "Distribución moderada de experiencia. Hay oportunidad para balancear los niveles de seniority."
        else:
            return "Excelente distribución de experiencia. El equipo tiene una mezcla óptima de niveles de seniority."
    
    def _get_cultural_cohesion_analysis(self, score: float, shared_values: List[str]) -> str:
        """Get analysis text for cultural cohesion score."""
        if score < 50:
            return "Baja cohesión cultural. Pocos valores compartidos pueden afectar la identidad del equipo."
        elif score < 75:
            return "Cohesión cultural moderada. Hay oportunidad para fortalecer valores compartidos."
        else:
            return "Excelente cohesión cultural. El equipo tiene fuertes valores compartidos que mantienen su identidad."
    
    def get_default_result(self, error_message: str = None) -> Dict:
        """
        Get default team analysis result.
        
        Args:
            error_message: Optional error message
            
        Returns:
            Default analysis result
        """
        return {
            'team_members': [],
            'team_size': 0,
            'composition_analysis': {},
            'synergy_analysis': {},
            'synergy_gaps': [],
            'optimization_recommendations': [
                {
                    'category': 'General',
                    'recommendation': 'Proporcionar datos completos para análisis',
                    'actions': ['Incluir al menos 2 miembros en el equipo para análisis'],
                    'priority': 'high',
                    'impact': 'high'
                }
            ],
            'overall_synergy_score': 0,
            'team_visualization': {'nodes': [], 'edges': []},
            'error': error_message,
            'analyzed_at': datetime.now().isoformat()
        }

