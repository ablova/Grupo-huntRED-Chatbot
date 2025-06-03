# /home/pablo/app/ml/analyzers/talent_analyzer.py
"""
Talent Analyzer module for Grupo huntRED® assessment system.

This module provides analysis of technical skills, abilities, and potential
for various roles across different business units.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple

from app.models import BusinessUnit
from app.ml.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class TalentAnalyzer(BaseAnalyzer):
    """
    Analyzer for technical skills, competencies and talent potential.
    
    Evaluates a candidate's skills, experience, and growth potential
    to provide insights on role fit and development opportunities.
    """
    
    # Skill categories by business unit
    SKILL_CATEGORIES = {
        'huntRED': [
            'liderazgo_ejecutivo', 
            'gestion_estrategica', 
            'desarrollo_negocio',
            'gestion_equipos', 
            'comunicacion_corporativa'
        ],
        'huntU': [
            'desarrollo_software', 
            'analisis_datos', 
            'experiencia_usuario',
            'metodologias_agiles', 
            'gestion_proyectos_tecnicos'
        ],
        'Amigro': [
            'servicio_comunitario', 
            'desarrollo_social', 
            'coordinacion_campo',
            'comunicacion_intercultural', 
            'gestion_recursos'
        ],
        'SEXSI': [
            'gestion_relaciones', 
            'confidencialidad', 
            'analisis_contratos',
            'negociacion', 
            'gestion_conflictos'
        ]
    }
    
    # Experience levels and descriptions
    EXPERIENCE_LEVELS = {
        'principiante': 'Conocimientos básicos, necesita supervisión constante',
        'intermedio': 'Conocimientos sólidos, requiere supervisión ocasional',
        'avanzado': 'Dominio completo, puede trabajar independientemente',
        'experto': 'Dominio excepcional, puede enseñar y liderar a otros'
    }
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for talent analysis."""
        return ['assessment_type', 'skills', 'experience']
        
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analyze talent based on skills and experience data.
        
        Args:
            data: Dictionary containing skills and experience information
            business_unit: Business unit for contextual analysis
            
        Returns:
            Dict with talent analysis results
        """
        try:
            # Check cache first
            cached_result = self.get_cached_result(data, "talent_analysis")
            if cached_result:
                return cached_result
                
            # Validate input
            is_valid, error_message = self.validate_input(data)
            if not is_valid:
                logger.warning(f"Invalid input for talent analysis: {error_message}")
                return self.get_default_result(error_message)
                
            # Get business unit context
            bu_name = self.get_business_unit_name(business_unit)
            if bu_name not in self.SKILL_CATEGORIES:
                bu_name = 'huntRED'  # Default to huntRED if unknown BU
                
            # Process assessment data
            result = self._analyze_talent(data, bu_name)
            
            # Cache result
            self.set_cached_result(data, result, "talent_analysis")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in talent analysis: {str(e)}")
            return self.get_default_result(f"Analysis error: {str(e)}")
            
    def _analyze_talent(self, data: Dict, business_unit: str) -> Dict:
        """
        Perform core talent analysis.
        
        Args:
            data: Skills and experience data
            business_unit: Business unit name
            
        Returns:
            Dict with analysis results
        """
        # Extract skills and experience data
        skills_data = data.get('skills', {})
        experience_data = data.get('experience', {})
        
        # Get relevant skill categories for this BU
        bu_categories = self.SKILL_CATEGORIES.get(business_unit, [])
        
        # Calculate skill scores by category
        category_scores = {}
        for category in bu_categories:
            category_score = self._calculate_category_score(category, skills_data)
            category_scores[category] = category_score
            
        # Calculate overall skill level
        overall_skill_score = sum(category_scores.values()) / len(category_scores) if category_scores else 0
        
        # Analyze experience
        experience_analysis = self._analyze_experience(experience_data, business_unit)
        
        # Assess growth potential
        growth_potential = self._assess_growth_potential(skills_data, experience_data, business_unit)
        
        # Generate skill gap analysis
        skill_gaps = self._identify_skill_gaps(skills_data, business_unit)
        
        # Generate development recommendations
        development_recommendations = self._generate_development_recommendations(
            category_scores, skill_gaps, business_unit
        )
        
        # Generate role recommendations
        role_recommendations = self._generate_role_recommendations(
            category_scores, experience_analysis, business_unit
        )
        
        # Compile results
        result = {
            'assessment_type': 'talent',
            'business_unit': business_unit,
            'category_scores': category_scores,
            'overall_skill_level': overall_skill_score,
            'experience_analysis': experience_analysis,
            'growth_potential': growth_potential,
            'skill_gaps': skill_gaps,
            'development_recommendations': development_recommendations,
            'role_recommendations': role_recommendations
        }
        
        return result
        
    def _calculate_category_score(self, category: str, skills_data: Dict) -> float:
        """
        Calculate score for a skill category.
        
        Args:
            category: Skill category to calculate
            skills_data: Skills assessment data
            
        Returns:
            Score between 0 and 1
        """
        # Find skills related to this category
        category_skills = {
            skill: level for skill, level in skills_data.items() 
            if category.replace('_', ' ') in skill.lower()
        }
        
        if not category_skills:
            return 0.5  # Default score
            
        # Map skill levels to numeric scores
        level_mapping = {
            'principiante': 0.25,
            'intermedio': 0.5,
            'avanzado': 0.75,
            'experto': 1.0
        }
        
        # Calculate average score
        scores = []
        for skill, level in category_skills.items():
            if isinstance(level, (int, float)):
                # Normalize to 0-1 scale
                scores.append(min(1.0, max(0.0, float(level) / 100)))
            elif isinstance(level, str):
                # Map text level to score
                normalized_level = level.lower()
                if normalized_level in level_mapping:
                    scores.append(level_mapping[normalized_level])
                else:
                    # Try to find closest match
                    for key in level_mapping:
                        if key in normalized_level:
                            scores.append(level_mapping[key])
                            break
                    else:
                        scores.append(0.5)  # Default if no match
            
        return sum(scores) / len(scores) if scores else 0.5
        
    def _analyze_experience(self, experience_data: Dict, business_unit: str) -> Dict:
        """
        Analyze professional experience data.
        
        Args:
            experience_data: Experience information
            business_unit: Business unit name
            
        Returns:
            Dict with experience analysis
        """
        # Extract years of experience
        total_years = experience_data.get('total_years', 0)
        relevant_years = experience_data.get('relevant_years', 0)
        
        # Extract role information
        roles = experience_data.get('roles', [])
        
        # Determine experience level
        if total_years >= 10:
            experience_level = "Senior"
        elif total_years >= 5:
            experience_level = "Mid-level"
        else:
            experience_level = "Junior"
            
        # Calculate relevance percentage
        relevance_percentage = (relevant_years / total_years * 100) if total_years > 0 else 0
        
        # Analyze career progression
        progression = "Constante"
        if len(roles) >= 3:
            # Check for progression in responsibilities
            progression = "Ascendente" if roles[0].get('level', 0) < roles[-1].get('level', 0) else "Constante"
            
        return {
            'total_years': total_years,
            'relevant_years': relevant_years,
            'relevance_percentage': relevance_percentage,
            'experience_level': experience_level,
            'career_progression': progression
        }
        
    def _assess_growth_potential(self, skills_data: Dict, experience_data: Dict, business_unit: str) -> Dict:
        """
        Assess candidate's growth potential.
        
        Args:
            skills_data: Skills information
            experience_data: Experience information
            business_unit: Business unit
            
        Returns:
            Dict with growth potential assessment
        """
        # Default values
        learning_speed = 0.7
        adaptability = 0.7
        
        # Extract learning indicators if available
        if 'learning_speed' in skills_data:
            learning_speed = float(skills_data['learning_speed']) / 100
            
        if 'adaptability' in skills_data:
            adaptability = float(skills_data['adaptability']) / 100
            
        # Calculate growth potential score
        potential_score = (learning_speed * 0.6) + (adaptability * 0.4)
        
        # Determine potential level
        if potential_score > 0.8:
            potential_level = "Alto"
            potential_description = "Excelente potencial para crecimiento acelerado y adaptación a nuevos desafíos"
        elif potential_score > 0.6:
            potential_level = "Bueno"
            potential_description = "Buen potencial para crecer y desarrollar nuevas habilidades"
        elif potential_score > 0.4:
            potential_level = "Moderado"
            potential_description = "Potencial moderado para desarrollo con el apoyo adecuado"
        else:
            potential_level = "Limitado"
            potential_description = "Puede requerir más tiempo y estructura para desarrollar nuevas habilidades"
            
        # Estimate time to proficiency for next level
        current_level = experience_data.get('experience_level', 'Junior')
        
        if current_level == "Junior":
            time_to_next_level = "18-24 meses" if potential_score > 0.7 else "24-36 meses"
        elif current_level == "Mid-level":
            time_to_next_level = "24-30 meses" if potential_score > 0.7 else "30-48 meses"
        else:
            time_to_next_level = "Nivel máximo alcanzado"
            
        return {
            'potential_score': potential_score,
            'potential_level': potential_level,
            'description': potential_description,
            'time_to_next_level': time_to_next_level
        }
        
    def _identify_skill_gaps(self, skills_data: Dict, business_unit: str) -> List[Dict]:
        """
        Identify skill gaps based on business unit requirements.
        
        Args:
            skills_data: Skills information
            business_unit: Business unit
            
        Returns:
            List of skill gap dictionaries
        """
        # Define critical skills by business unit
        critical_skills = {
            'huntRED': [
                ('liderazgo_ejecutivo', 0.7),
                ('gestion_estrategica', 0.8),
                ('negociacion_alto_nivel', 0.7),
                ('toma_decisiones', 0.8),
                ('vision_negocio', 0.8)
            ],
            'huntU': [
                ('desarrollo_software', 0.7),
                ('analisis_datos', 0.6),
                ('metodologias_agiles', 0.7),
                ('soluciones_tecnicas', 0.7),
                ('aprendizaje_continuo', 0.8)
            ],
            'Amigro': [
                ('coordinacion_equipos', 0.7),
                ('comunicacion_intercultural', 0.8),
                ('resolucion_problemas', 0.7),
                ('gestion_recursos', 0.6),
                ('adaptabilidad_campo', 0.8)
            ],
            'SEXSI': [
                ('gestion_relaciones', 0.8),
                ('confidencialidad', 0.9),
                ('negociacion', 0.8),
                ('analisis_contratos', 0.7),
                ('manejo_situaciones_complejas', 0.8)
            ]
        }
        
        # Get critical skills for this BU
        bu_critical_skills = critical_skills.get(business_unit, critical_skills['huntRED'])
        
        # Identify gaps
        skill_gaps = []
        
        for skill, required_level in bu_critical_skills:
            # Find closest match in skills_data
            skill_found = False
            current_level = 0
            
            for candidate_skill, level in skills_data.items():
                if skill.replace('_', ' ') in candidate_skill.lower():
                    skill_found = True
                    
                    # Normalize level to 0-1 scale
                    if isinstance(level, (int, float)):
                        current_level = min(1.0, max(0.0, float(level) / 100))
                    elif isinstance(level, str):
                        level_mapping = {
                            'principiante': 0.25,
                            'intermedio': 0.5,
                            'avanzado': 0.75,
                            'experto': 1.0
                        }
                        normalized_level = level.lower()
                        if normalized_level in level_mapping:
                            current_level = level_mapping[normalized_level]
                        else:
                            current_level = 0.5  # Default
                            
                    break
                    
            # If skill not found or below required level, add as gap
            if not skill_found or current_level < required_level:
                gap_size = required_level - (current_level if skill_found else 0)
                
                # Determine gap level
                if gap_size > 0.5:
                    gap_level = "Significativo"
                elif gap_size > 0.3:
                    gap_level = "Moderado"
                else:
                    gap_level = "Leve"
                    
                skill_gaps.append({
                    'skill': skill.replace('_', ' ').title(),
                    'required_level': required_level,
                    'current_level': current_level if skill_found else 0,
                    'gap_level': gap_level
                })
                
        return skill_gaps
        
    def _generate_development_recommendations(self, category_scores: Dict, skill_gaps: List[Dict], business_unit: str) -> List[str]:
        """
        Generate development recommendations based on skill gaps.
        
        Args:
            category_scores: Scores by skill category
            skill_gaps: Identified skill gaps
            business_unit: Business unit
            
        Returns:
            List of development recommendations
        """
        recommendations = []
        
        # Generate recommendations for significant gaps
        significant_gaps = [gap for gap in skill_gaps if gap['gap_level'] == "Significativo"]
        
        for gap in significant_gaps[:2]:  # Focus on top 2 significant gaps
            skill_name = gap['skill']
            
            # Add specific recommendation based on skill
            if 'liderazgo' in skill_name.lower():
                recommendations.append(f"Desarrollar habilidades de {skill_name} a través de un programa formal de liderazgo y mentoring con ejecutivos senior")
            elif 'gestion' in skill_name.lower():
                recommendations.append(f"Fortalecer capacidades de {skill_name} mediante la gestión de proyectos de complejidad creciente con supervisión adecuada")
            elif 'desarrollo' in skill_name.lower() or 'tecnic' in skill_name.lower():
                recommendations.append(f"Mejorar competencias en {skill_name} a través de cursos especializados y proyectos prácticos en entornos reales")
            elif 'comunicacion' in skill_name.lower() or 'relacion' in skill_name.lower():
                recommendations.append(f"Perfeccionar habilidades de {skill_name} mediante talleres específicos y práctica regular en situaciones profesionales")
            else:
                recommendations.append(f"Desarrollar competencias en {skill_name} a través de formación específica y experiencia práctica guiada")
                
        # Add BU-specific recommendation
        bu_recommendations = {
            'huntRED': "Para roles ejecutivos en huntRED, considera participar en un programa de desarrollo ejecutivo con énfasis en liderazgo estratégico y visión de negocio",
            'huntU': "Para roles técnicos en huntU, mantente actualizado con las últimas tecnologías a través de cursos especializados y proyectos de innovación",
            'Amigro': "Para roles en Amigro, fortalece tu capacidad de trabajo en entornos diversos mediante experiencias de campo y proyectos comunitarios",
            'SEXSI': "Para roles en SEXSI, desarrolla tus habilidades de manejo de relaciones complejas y situaciones confidenciales a través de formación especializada"
        }
        
        if business_unit in bu_recommendations:
            recommendations.append(bu_recommendations[business_unit])
            
        # Add general recommendation if needed
        if len(recommendations) < 3:
            recommendations.append("Crear un plan de desarrollo personal con objetivos específicos de crecimiento en habilidades clave para tu trayectoria profesional")
            
        return recommendations
        
    def _generate_role_recommendations(self, category_scores: Dict, experience_analysis: Dict, business_unit: str) -> List[Dict]:
        """
        Generate role recommendations based on skill profile.
        
        Args:
            category_scores: Scores by skill category
            experience_analysis: Analysis of experience
            business_unit: Business unit
            
        Returns:
            List of role recommendation dictionaries
        """
        # Define roles by business unit and experience level
        roles_by_bu = {
            'huntRED': {
                'Senior': [
                    ('Director Ejecutivo', ['liderazgo_ejecutivo', 'gestion_estrategica']),
                    ('Director Comercial', ['desarrollo_negocio', 'gestion_equipos']),
                    ('Gerente Senior', ['gestion_estrategica', 'comunicacion_corporativa'])
                ],
                'Mid-level': [
                    ('Gerente de Área', ['gestion_equipos', 'comunicacion_corporativa']),
                    ('Consultor Senior', ['desarrollo_negocio', 'gestion_estrategica']),
                    ('Líder de Proyecto', ['gestion_equipos', 'desarrollo_negocio'])
                ],
                'Junior': [
                    ('Analista de Negocio', ['desarrollo_negocio', 'comunicacion_corporativa']),
                    ('Consultor Junior', ['comunicacion_corporativa', 'gestion_estrategica']),
                    ('Coordinador', ['gestion_equipos', 'comunicacion_corporativa'])
                ]
            },
            'huntU': {
                'Senior': [
                    ('Tech Lead', ['desarrollo_software', 'gestion_proyectos_tecnicos']),
                    ('Product Manager', ['analisis_datos', 'metodologias_agiles']),
                    ('Arquitecto de Software', ['desarrollo_software', 'experiencia_usuario'])
                ],
                'Mid-level': [
                    ('Desarrollador Senior', ['desarrollo_software', 'metodologias_agiles']),
                    ('Analista de Datos', ['analisis_datos', 'gestion_proyectos_tecnicos']),
                    ('UX/UI Designer', ['experiencia_usuario', 'metodologias_agiles'])
                ],
                'Junior': [
                    ('Desarrollador Junior', ['desarrollo_software', 'metodologias_agiles']),
                    ('Tester', ['metodologias_agiles', 'gestion_proyectos_tecnicos']),
                    ('Asistente de Diseño UX', ['experiencia_usuario', 'desarrollo_software'])
                ]
            },
            'Amigro': {
                'Senior': [
                    ('Coordinador de Proyecto', ['coordinacion_campo', 'gestion_recursos']),
                    ('Especialista en Desarrollo', ['desarrollo_social', 'comunicacion_intercultural']),
                    ('Líder Comunitario', ['servicio_comunitario', 'desarrollo_social'])
                ],
                'Mid-level': [
                    ('Supervisor de Campo', ['coordinacion_campo', 'servicio_comunitario']),
                    ('Facilitador', ['comunicacion_intercultural', 'desarrollo_social']),
                    ('Analista de Proyectos', ['gestion_recursos', 'desarrollo_social'])
                ],
                'Junior': [
                    ('Asistente de Campo', ['servicio_comunitario', 'coordinacion_campo']),
                    ('Promotor Comunitario', ['servicio_comunitario', 'comunicacion_intercultural']),
                    ('Asistente Administrativo', ['gestion_recursos', 'coordinacion_campo'])
                ]
            },
            'SEXSI': {
                'Senior': [
                    ('Consultor Senior', ['gestion_relaciones', 'analisis_contratos']),
                    ('Gerente de Relaciones', ['gestion_relaciones', 'negociacion']),
                    ('Especialista Legal', ['analisis_contratos', 'confidencialidad'])
                ],
                'Mid-level': [
                    ('Consultor', ['gestion_relaciones', 'confidencialidad']),
                    ('Asesor de Contratos', ['analisis_contratos', 'negociacion']),
                    ('Coordinador de Servicios', ['gestion_relaciones', 'gestion_conflictos'])
                ],
                'Junior': [
                    ('Asistente de Consultoría', ['confidencialidad', 'gestion_relaciones']),
                    ('Analista Junior', ['analisis_contratos', 'confidencialidad']),
                    ('Asistente de Coordinación', ['gestion_conflictos', 'gestion_relaciones'])
                ]
            }
        }
        
        # Get experience level and roles for this BU
        experience_level = experience_analysis.get('experience_level', 'Junior')
        bu_roles = roles_by_bu.get(business_unit, {}).get(experience_level, [])
        
        if not bu_roles:
            # Fallback to default roles
            bu_roles = roles_by_bu['huntRED'].get(experience_level, [])
            
        # Calculate match for each role
        role_matches = []
        
        for role_name, key_categories in bu_roles:
            # Calculate average score for key categories
            category_values = [category_scores.get(cat, 0.5) for cat in key_categories]
            avg_score = sum(category_values) / len(category_values) if category_values else 0.5
            
            # Calculate match percentage
            match_percentage = avg_score * 100
            
            # Determine match level
            if match_percentage >= 80:
                match_level = "Excelente"
                match_description = f"Tu perfil de habilidades es ideal para el rol de {role_name}"
            elif match_percentage >= 70:
                match_level = "Muy bueno"
                match_description = f"Tu perfil de habilidades se alinea muy bien con el rol de {role_name}"
            elif match_percentage >= 60:
                match_level = "Bueno"
                match_description = f"Tu perfil tiene buena alineación con el rol de {role_name}"
            else:
                match_level = "Moderado"
                match_description = f"Tu perfil tiene algunos puntos de alineación con el rol de {role_name}"
                
            # Add to matches if above minimum threshold
            if match_percentage >= 60:
                role_matches.append({
                    'role': role_name,
                    'match_percentage': match_percentage,
                    'match_level': match_level,
                    'description': match_description,
                    'key_categories': [cat.replace('_', ' ').title() for cat in key_categories]
                })
                
        # Sort by match percentage (descending)
        role_matches.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        # Return top 3 matches
        return role_matches[:3]
