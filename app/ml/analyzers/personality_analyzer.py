# /home/pablo/app/ml/analyzers/personality_analyzer.py
"""
Analizador de personalidad que integra datos de diversos assessments.
Este módulo sirve como puente entre los assessments del chatbot y el sistema ML.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from django.core.cache import cache

# Importaciones del sistema ML existente
from app.ml.ml_model import MatchmakingLearningSystem
from app.models import BusinessUnit  # Usando la importación centralizada

logger = logging.getLogger(__name__)

class PersonalityAnalyzer:
    """
    Analizador de personalidad que integra datos de diversos assessments.
    """
    
    # Definición de rasgos de personalidad para diferentes modelos
    PERSONALITY_TRAITS = {
        'big_five': ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'],
        'professional_dna': ['strategic_thinking', 'emotional_intelligence', 'adaptability', 
                           'collaboration', 'innovation', 'resilience', 'results_orientation'],
        'leadership': ['vision', 'influence', 'motivation', 'decision_making', 'accountability'],
        'cultural_fit': ['adaptability', 'values_alignment', 'team_orientation', 'growth_mindset', 'work_ethic']
    }
    
    def __init__(self):
        self.ml_system = MatchmakingLearningSystem()
        self.cache_timeout = 3600  # 1 hora
        
    def analyze(self, candidate_data: Dict, business_unit: Any = None) -> Dict:
        """
        Analiza los datos de personalidad del candidato.
        
        Args:
            candidate_data: Datos del candidato incluyendo respuestas de assessment
            business_unit: Unidad de negocio para contextualizar el análisis
            
        Returns:
            Dict con resultados del análisis de personalidad
        """
        try:
            # Usar caché para resultados frecuentes
            cache_key = f"personality_analysis_{hash(str(candidate_data))}"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Using cached personality analysis for {cache_key}")
                return cached_result
                
            # Procesar según el tipo de assessment y BU
            result = self._process_assessment_data(candidate_data, business_unit)
            
            # Enriquecer con recomendaciones basadas en ML
            result = self._enrich_with_ml_insights(result, candidate_data, business_unit)
            
            # Guardar en caché para futuras consultas
            cache.set(cache_key, result, self.cache_timeout)
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing personality: {str(e)}")
            # Devolver un resultado por defecto para evitar fallos críticos
            return self._get_default_analysis()
        
    def _process_assessment_data(self, data: Dict, business_unit: Any) -> Dict:
        """Procesa los datos de assessment según su tipo y BU."""
        # Identificar tipo de assessment
        assessment_type = data.get('assessment_type', 'personality')
        
        if assessment_type == 'personality':
            return self._analyze_personality(data, business_unit)
        elif assessment_type == 'professional_dna':
            return self._analyze_professional_dna(data, business_unit)
        elif assessment_type == 'cultural_fit':
            return self._analyze_cultural_fit(data, business_unit)
        elif assessment_type == 'talent':
            return self._analyze_talent(data, business_unit)
        else:
            # Análisis genérico
            return self._analyze_generic(data, business_unit)
    
    def _analyze_personality(self, data: Dict, business_unit: Any) -> Dict:
        """Analiza datos específicos de personalidad (BigFive)."""
        # Extraer respuestas relevantes
        responses = data.get('responses', {})
        
        # Calcular puntuaciones de rasgos
        traits = {}
        for trait in self.PERSONALITY_TRAITS['big_five']:
            trait_score = self._calculate_trait_score(trait, responses)
            traits[trait] = trait_score
            
        # Generar insights basados en puntuaciones
        strengths, improvements = self._identify_strengths_improvements(traits)
        recommended_roles = self._recommend_roles(traits, business_unit)
        
        return {
            'traits': traits,
            'insights': {
                'strengths': strengths,
                'areas_improvement': improvements,
                'recommended_roles': recommended_roles
            }
        }
    
    def _analyze_professional_dna(self, data: Dict, business_unit: Any) -> Dict:
        """Analiza datos específicos de ADN profesional."""
        # Extraer respuestas relevantes
        responses = data.get('responses', {})
        
        # Calcular puntuaciones de dimensiones
        dimensions = {}
        for dimension in self.PERSONALITY_TRAITS['professional_dna']:
            dimension_score = self._calculate_dimension_score(dimension, responses)
            dimensions[dimension] = dimension_score
            
        # Generar insights basados en puntuaciones
        insights = self._generate_professional_dna_insights(dimensions)
        recommendations = self._generate_professional_dna_recommendations(dimensions, business_unit)
        
        return {
            'dimensions': dimensions,
            'insights': insights,
            'recommendations': recommendations
        }
    
    def _analyze_cultural_fit(self, data: Dict, business_unit: Any) -> Dict:
        """Analiza datos de fit cultural."""
        # Implementación básica que se puede expandir
        cultural_aspects = {}
        for aspect in self.PERSONALITY_TRAITS['cultural_fit']:
            cultural_aspects[aspect] = data.get(aspect, 0.5)
            
        return {
            'cultural_fit': cultural_aspects,
            'compatibility_score': sum(cultural_aspects.values()) / len(cultural_aspects),
            'recommendations': [
                'Evaluar alineación con valores de la empresa',
                'Considerar dinámicas de equipo en la entrevista'
            ]
        }
    
    def _analyze_talent(self, data: Dict, business_unit: Any) -> Dict:
        """Analiza datos de evaluación de talento."""
        # Implementación básica
        skill_levels = data.get('skill_levels', {})
        experience = data.get('experience', {})
        
        return {
            'skill_assessment': skill_levels,
            'experience_assessment': experience,
            'talent_score': 0.7,  # Placeholder, se implementaría algoritmo real
            'development_areas': ['Liderazgo técnico', 'Gestión de proyectos']
        }
    
    def _analyze_generic(self, data: Dict, business_unit: Any) -> Dict:
        """Analiza datos genéricos cuando no hay tipo específico."""
        # Fallback genérico
        return {
            'general_score': 0.7,
            'recommendations': [
                'Revisar historial profesional para evaluar trayectoria',
                'Considerar entrevista adicional para validar habilidades'
            ]
        }
        
    def _calculate_trait_score(self, trait: str, responses: Dict) -> float:
        """Calcula la puntuación para un rasgo basado en las respuestas."""
        # Implementación básica que se puede expandir
        trait_questions = [q for q in responses.keys() if trait in q.lower()]
        if not trait_questions:
            return 0.5  # Valor por defecto
            
        scores = [float(responses[q]) for q in trait_questions if responses[q]]
        return sum(scores) / len(scores) if scores else 0.5
        
    def _calculate_dimension_score(self, dimension: str, responses: Dict) -> float:
        """Calcula la puntuación para una dimensión de DNA profesional."""
        # Similar a trait_score pero adaptado a dimensiones profesionales
        dimension_questions = [q for q in responses.keys() if dimension.replace('_', ' ') in q.lower()]
        if not dimension_questions:
            return 50.0  # Valor por defecto (escala 0-100)
            
        scores = []
        for q in dimension_questions:
            if responses[q]:
                # Convertir respuestas a escala 0-100
                try:
                    val = float(responses[q])
                    # Asumiendo respuestas en escala 1-5
                    scores.append((val - 1) * 25)  # Convierte 1-5 a 0-100
                except (ValueError, TypeError):
                    continue
                    
        return sum(scores) / len(scores) if scores else 50.0
        
    def _identify_strengths_improvements(self, traits: Dict) -> Tuple[List[str], List[str]]:
        """Identifica fortalezas y áreas de mejora basadas en rasgos."""
        strengths = []
        improvements = []
        
        # Mapeo de rasgos a fortalezas (alto) y mejoras (bajo)
        trait_mapping = {
            'openness': ('Creatividad e innovación', 'Apertura a nuevas ideas'),
            'conscientiousness': ('Organización y responsabilidad', 'Planificación y disciplina'),
            'extraversion': ('Habilidades sociales y comunicativas', 'Asertividad en grupos'),
            'agreeableness': ('Trabajo en equipo y empatía', 'Colaboración y consenso'),
            'neuroticism': ('Estabilidad emocional', 'Manejo del estrés')
        }
        
        # Umbrales para considerar alto o bajo
        high_threshold = 0.7
        low_threshold = 0.3
        
        for trait, score in traits.items():
            if trait == 'neuroticism':
                # Para neuroticismo, bajo es bueno (estabilidad emocional)
                if score < low_threshold:
                    strengths.append(trait_mapping[trait][0])
                elif score > high_threshold:
                    improvements.append(trait_mapping[trait][1])
            else:
                # Para otros rasgos, alto es generalmente bueno
                if score > high_threshold:
                    strengths.append(trait_mapping[trait][0])
                elif score < low_threshold:
                    improvements.append(trait_mapping[trait][1])
                    
        return strengths, improvements
        
    def _recommend_roles(self, traits: Dict, business_unit: Any) -> List[str]:
        """Recomienda roles basados en perfil de personalidad y BU."""
        # Implementación básica que se puede expandir
        
        # Si no hay BU, dar recomendaciones genéricas
        if not business_unit:
            return ['Analista', 'Especialista', 'Coordinador']
            
        # Mapeo simplificado de rasgos dominantes a roles por BU
        bu_role_mapping = {
            'huntRED': {
                'openness': ['Consultor de Innovación', 'Estratega de Transformación'],
                'conscientiousness': ['Gerente de Proyectos', 'Director de Operaciones'],
                'extraversion': ['Director Comercial', 'Gerente de Relaciones Públicas'],
                'agreeableness': ['Gerente de Recursos Humanos', 'Director de Cultura Organizacional'],
                'low_neuroticism': ['Director General', 'Gerente de Crisis']
            },
            'huntU': {
                'openness': ['Desarrollador Creativo', 'Investigador'],
                'conscientiousness': ['Analista de Datos', 'Ingeniero de Calidad'],
                'extraversion': ['Ejecutivo de Ventas', 'Coordinador de Eventos'],
                'agreeableness': ['Especialista en Atención al Cliente', 'Coordinador de Equipo'],
                'low_neuroticism': ['Analista de Riesgos', 'Coordinador de Proyectos']
            },
            'Amigro': {
                'openness': ['Desarrollador de Soluciones', 'Especialista en Mejora Continua'],
                'conscientiousness': ['Supervisor de Operaciones', 'Administrador de Inventario'],
                'extraversion': ['Representante de Ventas', 'Ejecutivo de Servicio'],
                'agreeableness': ['Representante de Servicio al Cliente', 'Coordinador de Comunidad'],
                'low_neuroticism': ['Supervisor de Logística', 'Coordinador de Campo']
            }
        }
        
        # Determinar rasgo dominante (excluye neuroticismo)
        dominant_traits = []
        for trait, score in traits.items():
            if trait != 'neuroticism' and score > 0.65:
                dominant_traits.append(trait)
                
        if traits.get('neuroticism', 1.0) < 0.35:
            dominant_traits.append('low_neuroticism')
            
        # Si no hay rasgos dominantes, dar recomendación genérica para esa BU
        if not dominant_traits:
            return ['Posición analítica', 'Rol de especialista']
            
        # Obtener roles para los rasgos dominantes
        recommended_roles = []
        bu_name = getattr(business_unit, 'name', str(business_unit))
        bu_name = bu_name if bu_name in bu_role_mapping else 'huntRED'
        
        for trait in dominant_traits:
            if trait in bu_role_mapping[bu_name]:
                recommended_roles.extend(bu_role_mapping[bu_name][trait])
                
        return recommended_roles[:3]  # Limitar a 3 recomendaciones
        
    def _generate_professional_dna_insights(self, dimensions: Dict) -> Dict:
        """Genera insights basados en dimensiones de DNA profesional."""
        insights = {}
        
        # Definir interpretaciones para cada dimensión
        dimension_insights = {
            'strategic_thinking': 'Capacidad para pensar a largo plazo y alinear acciones con objetivos',
            'emotional_intelligence': 'Habilidad para reconocer y gestionar emociones propias y ajenas',
            'adaptability': 'Flexibilidad para ajustarse a cambios y nuevos entornos',
            'collaboration': 'Efectividad trabajando con otros para lograr objetivos comunes',
            'innovation': 'Capacidad para generar y aplicar ideas nuevas',
            'resilience': 'Fortaleza para recuperarse de dificultades y persistir',
            'results_orientation': 'Enfoque en lograr objetivos medibles y tangibles'
        }
        
        # Generar insight para cada dimensión
        for dimension, score in dimensions.items():
            base_insight = dimension_insights.get(dimension, '')
            if score > 75:
                level = "alto"
                impact = "una fortaleza significativa"
            elif score > 50:
                level = "moderado"
                impact = "un área con buen desarrollo"
            else:
                level = "en desarrollo"
                impact = "un área de oportunidad"
                
            insights[dimension] = f"{base_insight}. Tu nivel es {level}, lo que representa {impact}."
            
        return insights
        
    def _generate_professional_dna_recommendations(self, dimensions: Dict, business_unit: Any) -> List[str]:
        """Genera recomendaciones basadas en DNA profesional."""
        recommendations = []
        
        # Identificar dimensiones más bajas (áreas de oportunidad)
        low_dimensions = [d for d, score in dimensions.items() if score < 50]
        
        # Recomendaciones generales basadas en dimensiones bajas
        dimension_recommendations = {
            'strategic_thinking': 'Desarrollar habilidades de pensamiento a largo plazo y planificación',
            'emotional_intelligence': 'Practicar la autoconciencia y la empatía en interacciones profesionales',
            'adaptability': 'Exponerse a situaciones nuevas y diversas para aumentar flexibilidad',
            'collaboration': 'Participar en proyectos de equipo que requieran coordinación efectiva',
            'innovation': 'Dedicar tiempo a la generación de ideas y soluciones creativas',
            'resilience': 'Desarrollar técnicas de manejo del estrés y recuperación',
            'results_orientation': 'Establecer objetivos claros y medibles para tareas y proyectos'
        }
        
        # Añadir recomendaciones para dimensiones bajas
        for dimension in low_dimensions:
            if dimension in dimension_recommendations:
                recommendations.append(dimension_recommendations[dimension])
                
        # Añadir recomendaciones basadas en dimensiones altas (fortalezas)
        high_dimensions = [d for d, score in dimensions.items() if score > 75]
        if high_dimensions:
            high_dim = high_dimensions[0]  # Tomar la primera dimensión alta
            recommendations.append(f"Aprovechar tu alta {high_dim.replace('_', ' ')} en roles que requieran esta habilidad")
            
        # Añadir recomendación general si no hay muchas específicas
        if len(recommendations) < 2:
            recommendations.append("Buscar oportunidades de desarrollo integral en todas las dimensiones del ADN profesional")
            
        return recommendations
        
    def _enrich_with_ml_insights(self, result: Dict, candidate_data: Dict, business_unit: Any) -> Dict:
        """Enriquece los resultados con insights del sistema ML."""
        try:
            # Solo si tenemos suficiente información del candidato
            if 'personality_traits' in candidate_data or 'responses' in candidate_data:
                # Usar el sistema ML existente para obtener insights adicionales
                # Esto podría incluir predicciones basadas en modelos entrenados
                
                # Ejemplo de enriquecimiento:
                result['ml_insights'] = {
                    'market_alignment': 0.75,
                    'success_probability': 0.68,
                    'development_path': [
                        'Especializarse en habilidades técnicas core',
                        'Desarrollar competencias de liderazgo',
                        'Fortalecer habilidades de comunicación escrita'
                    ]
                }
                
                # Si el sistema ML tiene funcionalidad de matchmaking, usarla
                if hasattr(self.ml_system, 'calculate_personality_similarity'):
                    # Simulamos un objeto persona y vacante para la interfaz existente
                    # En una implementación real, construiríamos estos objetos adecuadamente
                    class MockObject:
                        def __init__(self, **kwargs):
                            for key, value in kwargs.items():
                                setattr(self, key, value)
                    
                    person = MockObject(personality_traits=result.get('traits', {}))
                    vacancy = MockObject(culture_fit={})
                    
                    # Calcular similitud usando el sistema existente
                    similarity = 0.5  # Valor por defecto
                    try:
                        similarity = self.ml_system.calculate_personality_similarity(person, vacancy)
                    except Exception as e:
                        logger.warning(f"Error calculating personality similarity: {str(e)}")
                        
                    result['personality_match'] = similarity
                
            return result
        except Exception as e:
            logger.error(f"Error enriching with ML insights: {str(e)}")
            return result  # Devolver el resultado sin enriquecer
    
    def _get_default_analysis(self) -> Dict:
        """Proporciona un análisis por defecto en caso de error."""
        return {
            'traits': {
                'openness': 0.5,
                'conscientiousness': 0.5,
                'extraversion': 0.5,
                'agreeableness': 0.5,
                'neuroticism': 0.5
            },
            'insights': {
                'note': 'Este es un análisis por defecto debido a un error en el procesamiento.',
                'recommendations': [
                    'Realizar una evaluación completa para obtener resultados precisos',
                    'Proporcionar datos adicionales para mejorar el análisis'
                ]
            }
        }
