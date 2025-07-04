# app/ats/chatbot/workflow/assessments/professional_dna/analysis.py
"""
Análisis de resultados de la evaluación Professional DNA
"""
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from app.ats.chatbot.integrations.matchmaking.factors import BusinessUnit
from app.ats.chatbot.workflow.assessments.professional_dna.questions import (
    QuestionCategory,
    Question
)

class AnalysisType(Enum):
    LEADERSHIP = "leadership"
    INNOVATION = "innovation"
    COMMUNICATION = "communication"
    RESILIENCE = "resilience"
    RESULTS = "results"
    GENERATIONAL = "generational"
    DIMENSIONAL = "dimensional"

class AnalysisDimension(Enum):
    STRATEGIC_THINKING = "strategic_thinking"
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"
    ADAPTABILITY = "adaptability"
    COLLABORATION = "collaboration"
    INNOVATION = "innovation"
    RESILIENCE = "resilience"
    RESULTS_ORIENTATION = "results_orientation"

@dataclass
class DimensionWeight:
    dimension: AnalysisDimension
    weight: float

@dataclass
class DimensionAnalysis:
    dimension: AnalysisDimension
    score: float
    weighted_score: float
    difficulty_adjusted_score: float
    insights: List[str]
    recommendations: List[str]

@dataclass
class AnalysisResult:
    category: AnalysisType
    score: float
    weighted_score: float
    insights: List[str]
    recommendations: List[str]
    generational_correlation: Optional[Dict[str, float]] = None
    business_unit_correlation: Optional[Dict[str, float]] = None
    difficulty_adjusted_score: Optional[float] = None
    dimensional_analysis: Optional[Dict[str, DimensionAnalysis]] = None

class ProfessionalDNAAnalysis:
    def __init__(self, business_unit: BusinessUnit = BusinessUnit.HUNTRED):
        self.business_unit = business_unit
        self.analysis_results = {}
        self.generational_patterns = {
            'boomer': {
                'leadership': {'A': 0.4, 'B': 0.3, 'C': 0.2, 'D': 0.1},
                'innovation': {'A': 0.2, 'B': 0.3, 'C': 0.3, 'D': 0.2},
                'communication': {'A': 0.3, 'B': 0.2, 'C': 0.3, 'D': 0.2},
                'resilience': {'A': 0.3, 'B': 0.3, 'C': 0.2, 'D': 0.2},
                'results': {'A': 0.3, 'B': 0.2, 'C': 0.2, 'D': 0.3}
            },
            'gen_x': {
                'leadership': {'A': 0.3, 'B': 0.3, 'C': 0.2, 'D': 0.2},
                'innovation': {'A': 0.3, 'B': 0.3, 'C': 0.2, 'D': 0.2},
                'communication': {'A': 0.2, 'B': 0.3, 'C': 0.3, 'D': 0.2},
                'resilience': {'A': 0.3, 'B': 0.2, 'C': 0.3, 'D': 0.2},
                'results': {'A': 0.3, 'B': 0.3, 'C': 0.2, 'D': 0.2}
            },
            'millennial': {
                'leadership': {'A': 0.2, 'B': 0.3, 'C': 0.3, 'D': 0.2},
                'innovation': {'A': 0.3, 'B': 0.2, 'C': 0.2, 'D': 0.3},
                'communication': {'A': 0.2, 'B': 0.3, 'C': 0.3, 'D': 0.2},
                'resilience': {'A': 0.2, 'B': 0.2, 'C': 0.3, 'D': 0.3},
                'results': {'A': 0.2, 'B': 0.3, 'C': 0.3, 'D': 0.2}
            },
            'gen_z': {
                'leadership': {'A': 0.2, 'B': 0.2, 'C': 0.3, 'D': 0.3},
                'innovation': {'A': 0.3, 'B': 0.2, 'C': 0.2, 'D': 0.3},
                'communication': {'A': 0.1, 'B': 0.4, 'C': 0.3, 'D': 0.2},
                'resilience': {'A': 0.2, 'B': 0.2, 'C': 0.3, 'D': 0.3},
                'results': {'A': 0.2, 'B': 0.3, 'C': 0.3, 'D': 0.2}
            }
        }
        
        self.business_unit_patterns = {
            BusinessUnit.HUNTRED_EXECUTIVE: {
                'leadership': 0.4,
                'innovation': 0.3,
                'communication': 0.1,
                'resilience': 0.1,
                'results': 0.1
            },
            BusinessUnit.HUNTRED: {
                'leadership': 0.3,
                'innovation': 0.2,
                'communication': 0.2,
                'resilience': 0.2,
                'results': 0.1
            },
            BusinessUnit.HUNTU: {
                'leadership': 0.2,
                'innovation': 0.3,
                'communication': 0.2,
                'resilience': 0.2,
                'results': 0.1
            },
            BusinessUnit.AMIGRO: {
                'leadership': 0.2,
                'innovation': 0.2,
                'communication': 0.3,
                'resilience': 0.2,
                'results': 0.1
            }
        }

        # Patrones por dimensión
        self.dimensional_patterns = {
            AnalysisDimension.STRATEGIC_THINKING: {
                'high': "Demuestra capacidad para pensar estratégicamente y ver el panorama general",
                'medium': "Muestra algunas habilidades estratégicas pero puede mejorar",
                'low': "Necesita desarrollar habilidades de pensamiento estratégico"
            },
            # ... (patrones para otras dimensiones)
        }

    def analyze_answers(
        self, 
        answers: Dict[str, Dict[str, str]], 
        generation: str,
        questions: List[Question]
    ) -> Dict[str, AnalysisResult]:
        """Analiza las respuestas y genera insights"""
        results = {}
        
        for category in QuestionCategory:
            category_answers = answers.get(category.value, {})
            if category_answers:
                # Análisis por categoría
                base_score = self._calculate_category_score(category_answers)
                weighted_score = self._calculate_weighted_score(
                    category, 
                    category_answers,
                    questions
                )
                difficulty_adjusted_score = self._calculate_difficulty_adjusted_score(
                    category,
                    category_answers,
                    questions
                )
                
                # Análisis dimensional
                dimensional_analysis = self._analyze_dimensions(
                    category,
                    category_answers,
                    questions
                )
                
                # Generar insights y recomendaciones
                insights = self._generate_insights(category, category_answers)
                recommendations = self._generate_recommendations(
                    category, 
                    weighted_score,
                    difficulty_adjusted_score,
                    dimensional_analysis
                )
                
                # Analizar correlaciones
                generational_correlation = self._analyze_generational_correlation(
                    category, 
                    category_answers, 
                    generation
                )
                business_unit_correlation = self._analyze_business_unit_correlation(
                    category,
                    category_answers
                )
                
                results[category.value] = AnalysisResult(
                    category=AnalysisType(category.value),
                    score=base_score,
                    weighted_score=weighted_score,
                    difficulty_adjusted_score=difficulty_adjusted_score,
                    insights=insights,
                    recommendations=recommendations,
                    generational_correlation=generational_correlation,
                    business_unit_correlation=business_unit_correlation,
                    dimensional_analysis=dimensional_analysis
                )
        
        return results

    def _calculate_category_score(self, answers: Dict[str, str]) -> float:
        """Calcula el puntaje base para una categoría"""
        total_weight = 0
        for question_id, answer in answers.items():
            # Implementar lógica de cálculo de peso base
            pass
        return total_weight / len(answers) if answers else 0.0

    def _calculate_weighted_score(
        self,
        category: QuestionCategory,
        answers: Dict[str, str],
        questions: List[Question]
    ) -> float:
        """Calcula el puntaje ponderado considerando la unidad de negocio"""
        total_weight = 0
        total_questions = 0
        
        for question in questions:
            if question.category == category:
                answer = answers.get(str(question.id))
                if answer:
                    # Aplicar peso de la unidad de negocio
                    business_unit_weight = self.business_unit_patterns[self.business_unit][category.value]
                    question_weight = question.weights.get(answer, 0)
                    total_weight += question_weight * business_unit_weight
                    total_questions += 1
        
        return total_weight / total_questions if total_questions > 0 else 0.0

    def _calculate_difficulty_adjusted_score(
        self,
        category: QuestionCategory,
        answers: Dict[str, str],
        questions: List[Question]
    ) -> float:
        """Calcula el puntaje ajustado por dificultad"""
        total_weight = 0
        total_difficulty = 0
        
        for question in questions:
            if question.category == category:
                answer = answers.get(str(question.id))
                if answer:
                    # Ajustar por dificultad
                    difficulty_factor = question.difficulty_level / 5.0
                    question_weight = question.weights.get(answer, 0)
                    total_weight += question_weight * difficulty_factor
                    total_difficulty += difficulty_factor
        
        return total_weight / total_difficulty if total_difficulty > 0 else 0.0

    def _analyze_dimensions(
        self,
        category: QuestionCategory,
        answers: Dict[str, str],
        questions: List[Question]
    ) -> Dict[str, DimensionAnalysis]:
        """Analiza las respuestas desde múltiples dimensiones"""
        dimensional_scores = {}
        
        for question in questions:
            if question.category == category:
                answer = answers.get(str(question.id))
                if answer and answer in question.dimensions:
                    for dimension_weight in question.dimensions[answer]:
                        dimension = dimension_weight.dimension
                        if dimension not in dimensional_scores:
                            dimensional_scores[dimension] = {
                                'total_weight': 0,
                                'total_questions': 0,
                                'difficulty_total': 0
                            }
                        
                        # Calcular puntajes
                        dimensional_scores[dimension]['total_weight'] += (
                            dimension_weight.weight * question.weights[answer]
                        )
                        dimensional_scores[dimension]['total_questions'] += 1
                        dimensional_scores[dimension]['difficulty_total'] += question.difficulty_level
        
        # Generar análisis por dimensión
        dimensional_analysis = {}
        for dimension, scores in dimensional_scores.items():
            if scores['total_questions'] > 0:
                base_score = scores['total_weight'] / scores['total_questions']
                difficulty_adjusted_score = (
                    scores['total_weight'] / scores['difficulty_total']
                    if scores['difficulty_total'] > 0 else 0
                )
                
                # Generar insights y recomendaciones específicas por dimensión
                insights = self._generate_dimension_insights(
                    dimension,
                    base_score,
                    difficulty_adjusted_score
                )
                recommendations = self._generate_dimension_recommendations(
                    dimension,
                    base_score,
                    difficulty_adjusted_score
                )
                
                dimensional_analysis[dimension.value] = DimensionAnalysis(
                    dimension=dimension,
                    score=base_score,
                    weighted_score=base_score,  # Puede ser ajustado según necesidades
                    difficulty_adjusted_score=difficulty_adjusted_score,
                    insights=insights,
                    recommendations=recommendations
                )
        
        return dimensional_analysis

    def _generate_dimension_insights(
        self,
        dimension: AnalysisDimension,
        score: float,
        difficulty_adjusted_score: float
    ) -> List[str]:
        """Genera insights específicos para una dimensión"""
        insights = []
        pattern = self.dimensional_patterns.get(dimension, {})
        
        if score >= 0.8:
            insights.append(pattern.get('high', f"Excelente desempeño en {dimension.value}"))
        elif score >= 0.5:
            insights.append(pattern.get('medium', f"Buen desempeño en {dimension.value}"))
        else:
            insights.append(pattern.get('low', f"Área de mejora en {dimension.value}"))
        
        return insights

    def _generate_dimension_recommendations(
        self,
        dimension: AnalysisDimension,
        score: float,
        difficulty_adjusted_score: float
    ) -> List[str]:
        """Genera recomendaciones específicas para una dimensión"""
        recommendations = []
        # Implementar lógica de recomendaciones por dimensión
        return recommendations

    def _generate_insights(self, category: QuestionCategory, answers: Dict[str, str]) -> List[str]:
        """Genera insights basados en las respuestas"""
        insights = []
        
        # Insights específicos por categoría
        category_insights = {
            QuestionCategory.LEADERSHIP: {
                'A': [
                    "Muestra una tendencia hacia la toma de decisiones rápida y asertiva",
                    "Prioriza la acción sobre el análisis",
                    "Tiene un estilo de liderazgo directivo"
                ],
                'B': [
                    "Demuestra un enfoque analítico en la toma de decisiones",
                    "Valora la consideración de múltiples perspectivas",
                    "Muestra un estilo de liderazgo participativo"
                ],
                'C': [
                    "Prefiere un enfoque colaborativo en la toma de decisiones",
                    "Valora la participación del equipo",
                    "Muestra un estilo de liderazgo democrático"
                ],
                'D': [
                    "Tiene un enfoque estructurado y basado en procesos",
                    "Valora la estabilidad y consistencia",
                    "Muestra un estilo de liderazgo burocrático"
                ]
            },
            QuestionCategory.INNOVATION: {
                'A': [
                    "Muestra una alta adaptabilidad al cambio",
                    "Busca activamente nuevas oportunidades",
                    "Tiene un enfoque disruptivo"
                ],
                'B': [
                    "Tiene un enfoque gradual hacia la innovación",
                    "Valora la mejora continua",
                    "Busca el equilibrio entre cambio y estabilidad"
                ],
                'C': [
                    "Prefiere mantener lo que funciona",
                    "Valora la estabilidad",
                    "Tiene un enfoque conservador"
                ],
                'D': [
                    "Es cauteloso con los cambios",
                    "Prefiere seguir el camino establecido",
                    "Valora la seguridad sobre la innovación"
                ]
            },
            QuestionCategory.COMMUNICATION: {
                'A': [
                    "Prefiere la comunicación directa y presencial",
                    "Valora la interacción cara a cara",
                    "Tiene un estilo de comunicación asertivo"
                ],
                'B': [
                    "Se adapta a diferentes estilos de comunicación",
                    "Valora la flexibilidad en la comunicación",
                    "Tiene un enfoque híbrido"
                ],
                'C': [
                    "Prefiere la comunicación asíncrona",
                    "Valora la documentación escrita",
                    "Tiene un estilo de comunicación estructurado"
                ],
                'D': [
                    "Adapta su estilo según el contexto",
                    "Valora la efectividad sobre el formato",
                    "Tiene un enfoque pragmático"
                ]
            },
            QuestionCategory.RESILIENCE: {
                'A': [
                    "Muestra alta capacidad de adaptación",
                    "Gestiona eficientemente la presión",
                    "Tiene un enfoque proactivo ante los desafíos"
                ],
                'B': [
                    "Demuestra capacidad de recuperación",
                    "Maneja el estrés de manera efectiva",
                    "Tiene un enfoque equilibrado"
                ],
                'C': [
                    "Prefiere entornos estables",
                    "Valora la previsibilidad",
                    "Tiene un enfoque cauteloso"
                ],
                'D': [
                    "Busca evitar situaciones estresantes",
                    "Prefiere la estabilidad",
                    "Tiene un enfoque conservador"
                ]
            },
            QuestionCategory.RESULTS: {
                'A': [
                    "Se enfoca en el logro de objetivos",
                    "Valora los resultados tangibles",
                    "Tiene un enfoque orientado a metas"
                ],
                'B': [
                    "Busca el impacto y la transformación",
                    "Valora el cambio significativo",
                    "Tiene un enfoque transformacional"
                ],
                'C': [
                    "Prioriza el desarrollo personal",
                    "Valora el aprendizaje continuo",
                    "Tiene un enfoque de crecimiento"
                ],
                'D': [
                    "Busca el reconocimiento externo",
                    "Valora la visibilidad",
                    "Tiene un enfoque de reputación"
                ]
            }
        }
        
        # Generar insights basados en las respuestas
        for question_id, answer in answers.items():
            if answer in category_insights.get(category, {}):
                insights.extend(category_insights[category][answer])
        
        return insights

    def _generate_recommendations(
        self,
        category: QuestionCategory,
        weighted_score: float,
        difficulty_adjusted_score: float,
        dimensional_analysis: Dict[str, DimensionAnalysis]
    ) -> List[str]:
        """Genera recomendaciones basadas en los puntajes"""
        recommendations = []
        
        # Recomendaciones específicas por categoría y puntaje
        category_recommendations = {
            QuestionCategory.LEADERSHIP: {
                'high': [
                    "Desarrollar habilidades de mentoría y coaching",
                    "Explorar roles de liderazgo estratégico",
                    "Fomentar la innovación en el equipo"
                ],
                'medium': [
                    "Practicar la toma de decisiones bajo presión",
                    "Mejorar la comunicación con el equipo",
                    "Desarrollar habilidades de resolución de conflictos"
                ],
                'low': [
                    "Participar en proyectos de liderazgo",
                    "Buscar oportunidades de liderar iniciativas pequeñas",
                    "Recibir feedback sobre estilos de liderazgo"
                ]
            },
            QuestionCategory.INNOVATION: {
                'high': [
                    "Explorar nuevas tecnologías y metodologías",
                    "Fomentar la cultura de innovación",
                    "Mentorizar a otros en procesos de innovación"
                ],
                'medium': [
                    "Participar en proyectos de innovación",
                    "Aprender nuevas herramientas y técnicas",
                    "Colaborar con equipos innovadores"
                ],
                'low': [
                    "Familiarizarse con tendencias emergentes",
                    "Practicar el pensamiento creativo",
                    "Buscar oportunidades de mejora continua"
                ]
            },
            QuestionCategory.COMMUNICATION: {
                'high': [
                    "Desarrollar habilidades de presentación ejecutiva",
                    "Mentorizar en comunicación efectiva",
                    "Liderar iniciativas de comunicación organizacional"
                ],
                'medium': [
                    "Mejorar la comunicación escrita",
                    "Practicar la escucha activa",
                    "Desarrollar habilidades de presentación"
                ],
                'low': [
                    "Participar en talleres de comunicación",
                    "Practicar la comunicación en diferentes contextos",
                    "Buscar feedback sobre habilidades comunicativas"
                ]
            },
            QuestionCategory.RESILIENCE: {
                'high': [
                    "Mentorizar en gestión del estrés",
                    "Desarrollar programas de bienestar",
                    "Liderar iniciativas de cambio organizacional"
                ],
                'medium': [
                    "Practicar técnicas de mindfulness",
                    "Mejorar la gestión del tiempo",
                    "Desarrollar estrategias de afrontamiento"
                ],
                'low': [
                    "Aprender técnicas de manejo del estrés",
                    "Establecer rutinas de bienestar",
                    "Buscar apoyo en situaciones desafiantes"
                ]
            },
            QuestionCategory.RESULTS: {
                'high': [
                    "Mentorizar en gestión de proyectos",
                    "Liderar iniciativas estratégicas",
                    "Desarrollar métricas de éxito"
                ],
                'medium': [
                    "Mejorar la planificación y seguimiento",
                    "Desarrollar habilidades de gestión de proyectos",
                    "Establecer objetivos SMART"
                ],
                'low': [
                    "Aprender técnicas de gestión de proyectos",
                    "Practicar el establecimiento de objetivos",
                    "Buscar feedback sobre resultados"
                ]
            }
        }
        
        # Determinar el nivel basado en los puntajes
        level = 'high' if weighted_score >= 0.8 else 'medium' if weighted_score >= 0.5 else 'low'
        
        # Obtener recomendaciones específicas
        if category in category_recommendations and level in category_recommendations[category]:
            recommendations.extend(category_recommendations[category][level])
        
        # Ajustar recomendaciones basadas en la dificultad
        if difficulty_adjusted_score < weighted_score:
            recommendations.append(
                "Considerar oportunidades de desarrollo en áreas más desafiantes"
            )
        
        # Agregar recomendaciones basadas en el análisis dimensional
        for dimension, analysis in dimensional_analysis.items():
            if analysis.score >= 0.8:
                recommendations.append(f"Mejorar en la dimensión: {dimension}")
            elif analysis.score >= 0.5:
                recommendations.append(f"Mantener el desempeño en la dimensión: {dimension}")
            else:
                recommendations.append(f"Mejorar en la dimensión: {dimension}")
        
        return recommendations

    def _analyze_generational_correlation(
        self, 
        category: QuestionCategory, 
        answers: Dict[str, str],
        generation: str
    ) -> Dict[str, float]:
        """Analiza la correlación con patrones generacionales"""
        correlations = {}
        generation_pattern = self.generational_patterns.get(generation, {})
        category_pattern = generation_pattern.get(category.value, {})
        
        # Calcular correlación para cada respuesta
        for question_id, answer in answers.items():
            if answer in category_pattern:
                correlations[question_id] = category_pattern[answer]
        
        return correlations

    def _analyze_business_unit_correlation(
        self,
        category: QuestionCategory,
        answers: Dict[str, str]
    ) -> Dict[str, float]:
        """Analiza la correlación con patrones de la unidad de negocio"""
        correlations = {}
        unit_pattern = self.business_unit_patterns.get(self.business_unit, {})
        category_weight = unit_pattern.get(category.value, 0)
        
        # Calcular correlación para cada respuesta
        for question_id, answer in answers.items():
            correlations[question_id] = category_weight
        
        return correlations

    def get_analysis_summary(self, results: Dict[str, AnalysisResult]) -> Dict:
        """Genera un resumen del análisis"""
        summary = {
            'overall_score': 0.0,
            'weighted_score': 0.0,
            'difficulty_adjusted_score': 0.0,
            'category_scores': {},
            'key_insights': [],
            'top_recommendations': [],
            'generational_insights': {},
            'business_unit_insights': {},
            'dimensional_insights': {}
        }
        
        # Calcular puntajes generales
        total_weight = 0
        for category, result in results.items():
            weight = self.business_unit_patterns[self.business_unit][category]
            summary['overall_score'] += result.score * weight
            summary['weighted_score'] += result.weighted_score * weight
            summary['difficulty_adjusted_score'] += result.difficulty_adjusted_score * weight
            total_weight += weight
            
            summary['category_scores'][category] = {
                'base_score': result.score,
                'weighted_score': result.weighted_score,
                'difficulty_adjusted_score': result.difficulty_adjusted_score
            }
        
        # Normalizar puntajes
        if total_weight > 0:
            summary['overall_score'] /= total_weight
            summary['weighted_score'] /= total_weight
            summary['difficulty_adjusted_score'] /= total_weight
        
        # Agregar insights y recomendaciones
        for result in results.values():
            summary['key_insights'].extend(result.insights)
            summary['top_recommendations'].extend(result.recommendations)
        
        # Agregar insights y recomendaciones dimensionales
        for dimension, analysis in result.dimensional_analysis.items():
            summary['dimensional_insights'][dimension] = {
                'insights': analysis.insights,
                'recommendations': analysis.recommendations
            }
        
        return summary 