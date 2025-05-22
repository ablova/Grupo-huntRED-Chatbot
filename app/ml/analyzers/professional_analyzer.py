# /home/pablo/app/ml/analyzers/professional_analyzer.py
"""
Professional DNA Analyzer module for Grupo huntRED® assessment system.

This module provides analysis of professional DNA assessments, focusing on key
professional dimensions like strategic thinking, emotional intelligence, 
adaptability, and results orientation.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

from app.models import BusinessUnit
from app.ml.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class ProfessionalAnalyzer(BaseAnalyzer):
    """
    Analyzer for Professional DNA assessments.
    
    Evaluates professional dimensions and generates insights on strengths, 
    development areas, and career recommendations across different business units.
    """
    
    # Professional DNA dimensions (common across assessments)
    PROFESSIONAL_DIMENSIONS = [
        'strategic_thinking', 
        'emotional_intelligence', 
        'adaptability', 
        'collaboration', 
        'innovation', 
        'resilience', 
        'results_orientation'
    ]
    
    # BU-specific dimension importance
    DIMENSION_IMPORTANCE = {
        'huntRED': {
            'strategic_thinking': 0.9,
            'emotional_intelligence': 0.8,
            'adaptability': 0.7,
            'collaboration': 0.6,
            'innovation': 0.8,
            'resilience': 0.7,
            'results_orientation': 0.9
        },
        'huntU': {
            'strategic_thinking': 0.7,
            'emotional_intelligence': 0.7,
            'adaptability': 0.8,
            'collaboration': 0.8,
            'innovation': 0.9,
            'resilience': 0.7,
            'results_orientation': 0.7
        },
        'Amigro': {
            'strategic_thinking': 0.6,
            'emotional_intelligence': 0.8,
            'adaptability': 0.8,
            'collaboration': 0.9,
            'innovation': 0.7,
            'resilience': 0.8,
            'results_orientation': 0.7
        },
        'SEXSI': {
            'strategic_thinking': 0.7,
            'emotional_intelligence': 0.9,
            'adaptability': 0.7,
            'collaboration': 0.8,
            'innovation': 0.6,
            'resilience': 0.8,
            'results_orientation': 0.8
        }
    }
    
    # Professional DNA insights
    DIMENSION_INSIGHTS = {
        'strategic_thinking': {
            'high': 'Tienes una excelente capacidad para pensar a largo plazo, visualizar objetivos estratégicos y alinear acciones con la visión general. Esta habilidad es particularmente valiosa en roles directivos y estratégicos.',
            'medium': 'Muestras una capacidad adecuada para el pensamiento estratégico, aunque puedes fortalecer tu habilidad para conectar acciones diarias con objetivos a largo plazo.',
            'low': 'El pensamiento estratégico es un área de desarrollo para ti. Considera ejercitar tu capacidad de visualizar escenarios futuros y conectar decisiones actuales con objetivos a largo plazo.'
        },
        'emotional_intelligence': {
            'high': 'Tu inteligencia emocional es sobresaliente, con una gran capacidad para reconocer y gestionar emociones propias y ajenas. Esta habilidad te permite navegar eficazmente situaciones interpersonales complejas.',
            'medium': 'Muestras un nivel adecuado de inteligencia emocional, con oportunidades para profundizar en la comprensión de dinámicas emocionales complejas.',
            'low': 'La inteligencia emocional representa un área de desarrollo importante. Trabajar en la autoconciencia emocional y la empatía beneficiaría significativamente tu perfil profesional.'
        },
        'adaptability': {
            'high': 'Tu capacidad de adaptación es excepcional, permitiéndote prosperar en entornos cambiantes y ambiguos. Esta flexibilidad es un activo valioso en el mercado laboral actual.',
            'medium': 'Muestras una adaptabilidad moderada, funcionando bien en cambios anticipados pero con oportunidad de mejorar tu respuesta a situaciones imprevistas.',
            'low': 'La adaptabilidad es un área que requiere desarrollo. Considera buscar experiencias que te expongan a entornos cambiantes para fortalecer esta habilidad.'
        },
        'collaboration': {
            'high': 'Eres excepcionalmente colaborativo, con habilidad para trabajar eficazmente en diversos equipos y fomentar sinergias. Esta capacidad es fundamental para roles que requieren coordinación entre departamentos.',
            'medium': 'Tu nivel de colaboración es adecuado, con capacidad para trabajar en equipo efectivamente en la mayoría de situaciones.',
            'low': 'La colaboración representa un área de desarrollo. Fortalecer tus habilidades para trabajar en equipo y contribuir a esfuerzos colectivos enriquecería tu perfil profesional.'
        },
        'innovation': {
            'high': 'Tu capacidad innovadora es sobresaliente, permitiéndote generar ideas originales y soluciones creativas. Esta habilidad es particularmente valiosa en entornos que valoran la innovación disruptiva.',
            'medium': 'Muestras un nivel adecuado de innovación, con capacidad para contribuir ideas y adaptarte a nuevos enfoques.',
            'low': 'La innovación representa un área de desarrollo. Cultivar tu pensamiento creativo y apertura a nuevos enfoques fortalecería significativamente tu perfil.'
        },
        'resilience': {
            'high': 'Tu resiliencia es excepcional, permitiéndote mantener efectividad y equilibrio incluso en circunstancias desafiantes. Esta fortaleza es invaluable en roles de alta presión.',
            'medium': 'Muestras un nivel adecuado de resiliencia, con capacidad para recuperarte de la mayoría de obstáculos laborales.',
            'low': 'La resiliencia es un área que requiere desarrollo. Fortalecer tu capacidad para mantener efectividad ante la adversidad sería beneficioso para tu trayectoria profesional.'
        },
        'results_orientation': {
            'high': 'Tu orientación a resultados es sobresaliente, con fuerte enfoque en lograr objetivos medibles y tangibles. Esta cualidad es altamente valorada en roles con responsabilidad por resultados de negocio.',
            'medium': 'Muestras un nivel adecuado de orientación a resultados, con capacidad para completar objetivos establecidos.',
            'low': 'La orientación a resultados representa un área de desarrollo. Fortalecer tu enfoque en objetivos concretos y medibles mejoraría significativamente tu perfil profesional.'
        }
    }
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for professional DNA analysis."""
        return ['assessment_type', 'responses']
        
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        """
        Analyze professional DNA based on assessment data.
        
        Args:
            data: Dictionary containing professional assessment responses
            business_unit: Business unit for contextual analysis
            
        Returns:
            Dict with professional DNA analysis results
        """
        try:
            # Check cache first
            cached_result = self.get_cached_result(data, "professional_dna_analysis")
            if cached_result:
                return cached_result
                
            # Validate input
            is_valid, error_message = self.validate_input(data)
            if not is_valid:
                logger.warning(f"Invalid input for professional analysis: {error_message}")
                return self.get_default_result(error_message)
                
            # Get business unit context
            bu_name = self.get_business_unit_name(business_unit)
            if bu_name not in self.DIMENSION_IMPORTANCE:
                bu_name = 'huntRED'  # Default to huntRED if unknown BU
                
            # Process assessment data
            result = self._analyze_professional_dna(data, bu_name)
            
            # Cache result
            self.set_cached_result(data, result, "professional_dna_analysis")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in professional DNA analysis: {str(e)}")
            return self.get_default_result(f"Analysis error: {str(e)}")
            
    def _analyze_professional_dna(self, data: Dict, business_unit: str) -> Dict:
        """
        Perform core professional DNA analysis.
        
        Args:
            data: Assessment data
            business_unit: Business unit name
            
        Returns:
            Dict with analysis results
        """
        # Extract responses
        responses = data.get('responses', {})
        
        # Calculate dimension scores
        dimension_scores = {}
        for dimension in self.PROFESSIONAL_DIMENSIONS:
            dimension_score = self._calculate_dimension_score(dimension, responses)
            dimension_scores[dimension] = dimension_score
            
        # Get importance weights for this BU
        importance_weights = self.DIMENSION_IMPORTANCE.get(business_unit, self.DIMENSION_IMPORTANCE['huntRED'])
        
        # Calculate weighted overall score
        weighted_scores = [
            dimension_scores[dim] * importance_weights[dim]
            for dim in self.PROFESSIONAL_DIMENSIONS
            if dim in dimension_scores and dim in importance_weights
        ]
        
        total_weights = sum([
            importance_weights[dim]
            for dim in self.PROFESSIONAL_DIMENSIONS
            if dim in dimension_scores and dim in importance_weights
        ])
        
        overall_score = sum(weighted_scores) / total_weights if total_weights > 0 else 0
        
        # Generate dimension insights
        dimension_insights = {}
        for dimension, score in dimension_scores.items():
            level = 'high' if score > 75 else 'low' if score < 45 else 'medium'
            dimension_insights[dimension] = self.DIMENSION_INSIGHTS[dimension][level]
            
        # Identify strengths and areas for development
        strengths = [dim for dim, score in dimension_scores.items() if score > 75]
        development_areas = [dim for dim, score in dimension_scores.items() if score < 45]
        
        # Generate career recommendations
        career_recommendations = self._generate_career_recommendations(
            dimension_scores, business_unit
        )
        
        # Generate development recommendations
        development_recommendations = self._generate_development_recommendations(
            dimension_scores, business_unit
        )
        
        # Compile results
        result = {
            'assessment_type': 'professional_dna',
            'business_unit': business_unit,
            'dimension_scores': dimension_scores,
            'dimension_insights': dimension_insights,
            'overall_score': overall_score,
            'strengths': strengths,
            'development_areas': development_areas,
            'career_recommendations': career_recommendations,
            'development_recommendations': development_recommendations
        }
        
        return result
        
    def _calculate_dimension_score(self, dimension: str, responses: Dict) -> float:
        """
        Calculate score for a specific professional dimension.
        
        Args:
            dimension: Professional dimension to calculate
            responses: Assessment responses
            
        Returns:
            Score between 0 and 100
        """
        # Find questions related to this dimension
        dimension_questions = [
            q for q in responses.keys() 
            if dimension.replace('_', ' ') in q.lower()
        ]
        
        if not dimension_questions:
            return 50.0  # Default score
            
        # Calculate average score from responses
        try:
            scores = []
            for q in dimension_questions:
                response = responses.get(q)
                if response:
                    # Convert various response formats to normalized score (0-100)
                    if isinstance(response, (int, float)):
                        # Assuming scale of 1-5
                        scores.append((float(response) - 1) * 25)  # Convert to 0-100
                    elif isinstance(response, str) and response.isdigit():
                        # Numeric string
                        scores.append((float(response) - 1) * 25)  # Convert to 0-100
                    elif isinstance(response, str) and '-' in response:
                        # Format like "4 - Agree"
                        try:
                            value = float(response.split('-')[0].strip())
                            scores.append((value - 1) * 25)  # Convert to 0-100
                        except (ValueError, IndexError):
                            scores.append(50.0)  # Default if parsing fails
                    elif isinstance(response, str):
                        # Text response - map to numeric value
                        response_lower = response.lower()
                        if any(word in response_lower for word in ['strongly agree', 'excellent', 'always', '5']):
                            scores.append(100.0)
                        elif any(word in response_lower for word in ['agree', 'good', 'often', '4']):
                            scores.append(75.0)
                        elif any(word in response_lower for word in ['neutral', 'sometimes', 'average', '3']):
                            scores.append(50.0)
                        elif any(word in response_lower for word in ['disagree', 'rarely', 'poor', '2']):
                            scores.append(25.0)
                        elif any(word in response_lower for word in ['strongly disagree', 'never', 'very poor', '1']):
                            scores.append(0.0)
                        else:
                            scores.append(50.0)  # Default for unrecognized text
                            
            return sum(scores) / len(scores) if scores else 50.0
            
        except Exception as e:
            logger.warning(f"Error calculating dimension score for {dimension}: {str(e)}")
            return 50.0
            
    def _generate_career_recommendations(self, dimension_scores: Dict, business_unit: str) -> List[Dict]:
        """
        Generate career path recommendations based on professional DNA.
        
        Args:
            dimension_scores: Scores for each professional dimension
            business_unit: Business unit name
            
        Returns:
            List of career recommendation dictionaries
        """
        # Define role-dimension mapping by business unit
        role_dimension_mapping = {
            'huntRED': {
                'CEO/Director General': {
                    'key_dimensions': ['strategic_thinking', 'results_orientation', 'resilience'],
                    'threshold': 80
                },
                'Director Comercial': {
                    'key_dimensions': ['results_orientation', 'emotional_intelligence', 'strategic_thinking'],
                    'threshold': 75
                },
                'Director de Operaciones': {
                    'key_dimensions': ['results_orientation', 'strategic_thinking', 'collaboration'],
                    'threshold': 75
                },
                'Director de Recursos Humanos': {
                    'key_dimensions': ['emotional_intelligence', 'collaboration', 'resilience'],
                    'threshold': 75
                },
                'Director de Tecnología': {
                    'key_dimensions': ['innovation', 'strategic_thinking', 'adaptability'],
                    'threshold': 75
                },
                'Gerente de Proyecto': {
                    'key_dimensions': ['results_orientation', 'collaboration', 'adaptability'],
                    'threshold': 70
                }
            },
            'huntU': {
                'Tech Lead': {
                    'key_dimensions': ['innovation', 'collaboration', 'results_orientation'],
                    'threshold': 75
                },
                'Product Manager': {
                    'key_dimensions': ['strategic_thinking', 'innovation', 'collaboration'],
                    'threshold': 75
                },
                'UX/UI Designer': {
                    'key_dimensions': ['innovation', 'emotional_intelligence', 'adaptability'],
                    'threshold': 75
                },
                'Data Scientist': {
                    'key_dimensions': ['innovation', 'strategic_thinking', 'results_orientation'],
                    'threshold': 75
                },
                'Backend Developer': {
                    'key_dimensions': ['innovation', 'results_orientation', 'resilience'],
                    'threshold': 70
                },
                'Frontend Developer': {
                    'key_dimensions': ['innovation', 'collaboration', 'adaptability'],
                    'threshold': 70
                }
            },
            'Amigro': {
                'Coordinador de Comunidad': {
                    'key_dimensions': ['emotional_intelligence', 'collaboration', 'adaptability'],
                    'threshold': 75
                },
                'Líder de Proyecto Social': {
                    'key_dimensions': ['collaboration', 'resilience', 'results_orientation'],
                    'threshold': 75
                },
                'Especialista en Desarrollo': {
                    'key_dimensions': ['emotional_intelligence', 'adaptability', 'resilience'],
                    'threshold': 70
                },
                'Coordinador de Operaciones': {
                    'key_dimensions': ['results_orientation', 'collaboration', 'resilience'],
                    'threshold': 70
                },
                'Especialista en Inclusión': {
                    'key_dimensions': ['emotional_intelligence', 'adaptability', 'collaboration'],
                    'threshold': 70
                }
            },
            'SEXSI': {
                'Consultor Senior': {
                    'key_dimensions': ['emotional_intelligence', 'adaptability', 'strategic_thinking'],
                    'threshold': 80
                },
                'Gerente de Relaciones': {
                    'key_dimensions': ['emotional_intelligence', 'collaboration', 'resilience'],
                    'threshold': 75
                },
                'Especialista en Contratos': {
                    'key_dimensions': ['results_orientation', 'strategic_thinking', 'resilience'],
                    'threshold': 75
                },
                'Coordinador de Servicios': {
                    'key_dimensions': ['emotional_intelligence', 'collaboration', 'adaptability'],
                    'threshold': 70
                }
            }
        }
        
        # Get roles for this business unit
        bu_roles = role_dimension_mapping.get(business_unit, role_dimension_mapping['huntRED'])
        
        # Calculate match score for each role
        role_matches = []
        for role, requirements in bu_roles.items():
            key_dimensions = requirements['key_dimensions']
            threshold = requirements['threshold']
            
            # Calculate average score for key dimensions
            dimension_values = [dimension_scores.get(dim, 0) for dim in key_dimensions]
            avg_score = sum(dimension_values) / len(dimension_values) if dimension_values else 0
            
            # Calculate match percentage
            match_percentage = min(100, (avg_score / threshold) * 100)
            
            # Determine match level
            if match_percentage >= 90:
                match_level = "Excelente"
                match_description = f"Tu perfil profesional es ideal para el rol de {role}"
            elif match_percentage >= 75:
                match_level = "Muy bueno"
                match_description = f"Tu perfil profesional se alinea muy bien con el rol de {role}"
            elif match_percentage >= 60:
                match_level = "Bueno"
                match_description = f"Tu perfil tiene buena alineación con aspectos clave del rol de {role}"
            else:
                match_level = "Moderado"
                match_description = f"Tu perfil tiene algunos puntos de alineación con el rol de {role}"
                
            # Add to matches if above minimum threshold
            if match_percentage >= 60:
                role_matches.append({
                    'role': role,
                    'match_percentage': match_percentage,
                    'match_level': match_level,
                    'description': match_description,
                    'key_dimensions': key_dimensions
                })
                
        # Sort by match percentage (descending)
        role_matches.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        # Return top 3 matches
        return role_matches[:3]
        
    def _generate_development_recommendations(self, dimension_scores: Dict, business_unit: str) -> List[str]:
        """
        Generate development recommendations based on dimension scores.
        
        Args:
            dimension_scores: Scores for each professional dimension
            business_unit: Business unit name
            
        Returns:
            List of development recommendations
        """
        recommendations = []
        
        # Development recommendations by dimension
        dimension_recommendations = {
            'strategic_thinking': [
                "Participar en ejercicios de planificación estratégica para desarrollar visión a largo plazo",
                "Practicar la conexión de acciones tácticas con objetivos estratégicos",
                "Leer sobre tendencias de la industria y análisis de mercado para ampliar perspectiva"
            ],
            'emotional_intelligence': [
                "Desarrollar técnicas de autoconciencia emocional a través de prácticas reflexivas",
                "Practicar la empatía activa en interacciones profesionales",
                "Buscar feedback sobre cómo tus acciones impactan a otros"
            ],
            'adaptability': [
                "Exponerse deliberadamente a situaciones nuevas y fuera de tu zona de confort",
                "Practicar respuestas flexibles ante cambios inesperados",
                "Desarrollar habilidades en múltiples áreas para aumentar versatilidad"
            ],
            'collaboration': [
                "Participar en proyectos interdisciplinarios que requieran coordinación",
                "Practicar técnicas de facilitación de grupos y construcción de consenso",
                "Desarrollar habilidades de comunicación efectiva para entornos colaborativos"
            ],
            'innovation': [
                "Reservar tiempo para sesiones de ideación y pensamiento creativo",
                "Experimentar con técnicas de design thinking y solución creativa de problemas",
                "Exponerse a ideas diversas fuera de tu campo de especialización"
            ],
            'resilience': [
                "Desarrollar técnicas de gestión del estrés y recuperación",
                "Practicar la reinterpretación positiva de obstáculos como oportunidades",
                "Fortalecer tu red de apoyo profesional"
            ],
            'results_orientation': [
                "Establecer objetivos claros y medibles para proyectos y tareas",
                "Implementar sistemas de seguimiento de progreso hacia metas",
                "Practicar la priorización estratégica de tareas con mayor impacto"
            ]
        }
        
        # Find dimensions with lowest scores (below 60)
        low_dimensions = [dim for dim, score in dimension_scores.items() if score < 60]
        
        # Add recommendations for low dimensions
        for dimension in low_dimensions:
            if dimension in dimension_recommendations:
                # Add one recommendation for each low dimension
                recommendations.append(dimension_recommendations[dimension][0])
                
        # If not enough low dimensions, add recommendations for medium dimensions (60-75)
        if len(recommendations) < 3:
            medium_dimensions = [dim for dim, score in dimension_scores.items() 
                                if 60 <= score <= 75 and dim not in low_dimensions]
            
            for dimension in medium_dimensions:
                if dimension in dimension_recommendations and len(recommendations) < 3:
                    recommendations.append(dimension_recommendations[dimension][1])
                    
        # Add business unit specific recommendation
        bu_recommendations = {
            'huntRED': "Para roles ejecutivos en huntRED, considera un programa de desarrollo en liderazgo estratégico y gestión de stakeholders de alto nivel",
            'huntU': "Para roles técnicos en huntU, enfócate en actualizar constantemente tus conocimientos sobre tecnologías emergentes y metodologías ágiles",
            'Amigro': "Para roles en Amigro, desarrolla tu capacidad de trabajar con comunidades diversas y generar impacto social medible",
            'SEXSI': "Para roles en SEXSI, fortalece tu manejo profesional de relaciones interpersonales complejas y situaciones confidenciales"
        }
        
        if business_unit in bu_recommendations:
            recommendations.append(bu_recommendations[business_unit])
            
        # Ensure we have at least 3 recommendations
        if len(recommendations) < 3:
            general_recommendations = [
                "Buscar un mentor que pueda guiar tu desarrollo profesional en áreas clave",
                "Crear un plan de desarrollo personal con objetivos específicos a 3-6 meses",
                "Participar en comunidades profesionales para ampliar tu red y conocimientos"
            ]
            
            for rec in general_recommendations:
                if len(recommendations) < 3:
                    recommendations.append(rec)
                    
        return recommendations
