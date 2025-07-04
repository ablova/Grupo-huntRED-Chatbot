"""
Sistema de Assessments Dinámicos huntRED® v2
===========================================

Funcionalidades:
- Assessments adaptativos con branching lógico
- Menús interactivos dinámicos
- Personalización en tiempo real
- Múltiples tipos de preguntas avanzadas
- Sistema de scoring inteligente
- Análisis de patrones de respuesta
- Recomendaciones adaptativas
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import random
import math

logger = logging.getLogger(__name__)

class QuestionType(Enum):
    """Tipos de preguntas disponibles."""
    MULTIPLE_CHOICE = "multiple_choice"
    MULTIPLE_SELECT = "multiple_select"
    TRUE_FALSE = "true_false"
    TEXT_INPUT = "text_input"
    NUMERIC_INPUT = "numeric_input"
    SLIDER_SCALE = "slider_scale"
    RANKING = "ranking"
    MATCHING = "matching"
    DRAG_DROP = "drag_drop"
    CODE_COMPLETION = "code_completion"
    SCENARIO_BASED = "scenario_based"
    VIDEO_RESPONSE = "video_response"
    INTERACTIVE_SIMULATION = "interactive_simulation"

class DifficultyLevel(Enum):
    """Niveles de dificultad."""
    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5
    EXPERT = 6

class BranchingCondition(Enum):
    """Condiciones para branching lógico."""
    SCORE_THRESHOLD = "score_threshold"
    SPECIFIC_ANSWER = "specific_answer"
    TIME_TAKEN = "time_taken"
    SKILL_LEVEL = "skill_level"
    PREVIOUS_PERFORMANCE = "previous_performance"
    RANDOM = "random"
    COMPETENCY_GAP = "competency_gap"

class AssessmentType(Enum):
    """Tipos de assessment."""
    SKILLS_TECHNICAL = "skills_technical"
    PERSONALITY = "personality"
    COGNITIVE = "cognitive"
    SITUATIONAL = "situational"
    COMPETENCY = "competency"
    CULTURE_FIT = "culture_fit"
    LANGUAGE = "language"
    CUSTOM = "custom"

@dataclass
class InteractiveElement:
    """Elemento interactivo en una pregunta."""
    id: str
    element_type: str  # dropdown, checkbox, button, slider, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    styling: Dict[str, Any] = field(default_factory=dict)
    
    # Eventos y callbacks
    events: Dict[str, str] = field(default_factory=dict)  # event_name -> function_name
    dependencies: List[str] = field(default_factory=list)  # IDs de otros elementos

@dataclass
class QuestionOption:
    """Opción de respuesta para una pregunta."""
    id: str
    text: str
    value: Any
    is_correct: bool = False
    score_weight: float = 1.0
    
    # Interactividad
    requires_input: bool = False
    input_type: Optional[str] = None
    interactive_elements: List[InteractiveElement] = field(default_factory=list)
    
    # Branching
    next_question_id: Optional[str] = None
    condition_met_action: Optional[str] = None

@dataclass
class BranchingRule:
    """Regla de branching para navegación condicional."""
    id: str
    condition_type: BranchingCondition
    condition_value: Any
    target_question_id: str
    
    # Condiciones avanzadas
    multiple_conditions: List[Dict[str, Any]] = field(default_factory=list)
    condition_operator: str = "AND"  # AND, OR
    
    # Acciones adicionales
    set_variables: Dict[str, Any] = field(default_factory=dict)
    trigger_events: List[str] = field(default_factory=list)

@dataclass
class DynamicQuestion:
    """Pregunta dinámica con capacidades avanzadas."""
    id: str
    question_text: str
    question_type: QuestionType
    difficulty_level: DifficultyLevel
    
    # Opciones y respuestas
    options: List[QuestionOption] = field(default_factory=list)
    correct_answers: List[Any] = field(default_factory=list)
    
    # Interactividad
    interactive_elements: List[InteractiveElement] = field(default_factory=list)
    custom_rendering: Optional[str] = None  # HTML/React component
    
    # Branching y navegación
    branching_rules: List[BranchingRule] = field(default_factory=list)
    next_question_id: Optional[str] = None
    
    # Configuración
    time_limit: Optional[int] = None  # segundos
    attempts_allowed: int = 1
    show_feedback: bool = True
    feedback_text: str = ""
    
    # Scoring
    max_score: float = 100.0
    min_score: float = 0.0
    scoring_algorithm: str = "standard"  # standard, weighted, adaptive
    
    # Metadatos
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    competencies: List[str] = field(default_factory=list)
    
    # Adaptabilidad
    adaptive_difficulty: bool = False
    prerequisite_skills: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class AssessmentResponse:
    """Respuesta a una pregunta del assessment."""
    question_id: str
    user_answer: Any
    selected_options: List[str] = field(default_factory=list)
    
    # Timing
    time_started: datetime = field(default_factory=datetime.now)
    time_completed: Optional[datetime] = None
    time_taken: float = 0.0  # segundos
    
    # Scoring
    score: float = 0.0
    max_possible_score: float = 100.0
    is_correct: bool = False
    
    # Metadatos
    attempt_number: int = 1
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Análisis
    confidence_level: Optional[float] = None
    response_pattern: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AssessmentSession:
    """Sesión de assessment en progreso."""
    id: str
    user_id: str
    assessment_id: str
    assessment_type: AssessmentType
    
    # Estado
    current_question_id: Optional[str] = None
    questions_completed: List[str] = field(default_factory=list)
    responses: List[AssessmentResponse] = field(default_factory=list)
    
    # Navegación dinámica
    question_path: List[str] = field(default_factory=list)
    available_next_questions: List[str] = field(default_factory=list)
    
    # Variables de sesión
    session_variables: Dict[str, Any] = field(default_factory=dict)
    user_profile: Dict[str, Any] = field(default_factory=dict)
    
    # Scoring
    current_score: float = 0.0
    max_possible_score: float = 0.0
    completion_percentage: float = 0.0
    
    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    estimated_completion_time: Optional[int] = None
    
    # Estado
    is_completed: bool = False
    is_paused: bool = False
    
    # Adaptabilidad
    difficulty_adjustments: List[Dict[str, Any]] = field(default_factory=list)
    performance_trends: Dict[str, List[float]] = field(default_factory=dict)

class DynamicAssessmentEngine:
    """Motor principal de assessments dinámicos."""
    
    def __init__(self):
        self.assessments: Dict[str, Dict] = {}
        self.questions: Dict[str, DynamicQuestion] = {}
        self.active_sessions: Dict[str, AssessmentSession] = {}
        self.templates: Dict[str, Dict] = {}
        
        # Configuración de algoritmos
        self.scoring_algorithms = {
            "standard": self._standard_scoring,
            "weighted": self._weighted_scoring,
            "adaptive": self._adaptive_scoring,
            "irt": self._irt_scoring  # Item Response Theory
        }
        
        # Setup inicial
        self._setup_default_templates()
        self._setup_sample_questions()
    
    def _setup_default_templates(self):
        """Configura templates por defecto."""
        
        self.templates = {
            "technical_skills": {
                "name": "Technical Skills Assessment",
                "description": "Adaptive technical assessment with code challenges",
                "duration_minutes": 60,
                "question_types": [
                    QuestionType.MULTIPLE_CHOICE,
                    QuestionType.CODE_COMPLETION,
                    QuestionType.SCENARIO_BASED
                ],
                "difficulty_progression": True,
                "adaptive_branching": True
            },
            
            "personality_profile": {
                "name": "Personality & Culture Fit",
                "description": "Dynamic personality assessment with situational questions",
                "duration_minutes": 30,
                "question_types": [
                    QuestionType.SLIDER_SCALE,
                    QuestionType.RANKING,
                    QuestionType.SCENARIO_BASED
                ],
                "adaptive_difficulty": False,
                "branching_logic": True
            },
            
            "cognitive_ability": {
                "name": "Cognitive Ability Test",
                "description": "Adaptive cognitive assessment with real-time difficulty adjustment",
                "duration_minutes": 45,
                "question_types": [
                    QuestionType.MULTIPLE_CHOICE,
                    QuestionType.NUMERIC_INPUT,
                    QuestionType.INTERACTIVE_SIMULATION
                ],
                "adaptive_difficulty": True,
                "time_pressure": True
            }
        }
    
    def _setup_sample_questions(self):
        """Configura preguntas de ejemplo."""
        
        # Pregunta técnica con branching
        tech_question = DynamicQuestion(
            id="tech_001",
            question_text="¿Cuál es la complejidad temporal de este algoritmo?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            difficulty_level=DifficultyLevel.MEDIUM,
            options=[
                QuestionOption(id="opt1", text="O(n)", value="O(n)", is_correct=False),
                QuestionOption(id="opt2", text="O(n²)", value="O(n²)", is_correct=True),
                QuestionOption(id="opt3", text="O(log n)", value="O(log n)", is_correct=False),
                QuestionOption(id="opt4", text="O(1)", value="O(1)", is_correct=False)
            ],
            branching_rules=[
                BranchingRule(
                    id="br1",
                    condition_type=BranchingCondition.SPECIFIC_ANSWER,
                    condition_value="O(n²)",
                    target_question_id="tech_002_advanced"
                ),
                BranchingRule(
                    id="br2",
                    condition_type=BranchingCondition.SPECIFIC_ANSWER,
                    condition_value=["O(n)", "O(log n)", "O(1)"],
                    target_question_id="tech_002_basic"
                )
            ],
            category="programming",
            competencies=["algorithm_analysis", "big_o_notation"]
        )
        
        # Pregunta interactiva con elementos dinámicos
        interactive_question = DynamicQuestion(
            id="interactive_001",
            question_text="Ordena estos elementos de mayor a menor prioridad en un proyecto:",
            question_type=QuestionType.RANKING,
            difficulty_level=DifficultyLevel.MEDIUM,
            interactive_elements=[
                InteractiveElement(
                    id="ranking_widget",
                    element_type="sortable_list",
                    properties={
                        "items": ["Calidad", "Tiempo", "Presupuesto", "Recursos"],
                        "allow_ties": False,
                        "animation": True
                    },
                    events={"onChange": "updateRanking"}
                )
            ],
            scoring_algorithm="weighted",
            category="project_management"
        )
        
        # Pregunta adaptativa con simulación
        simulation_question = DynamicQuestion(
            id="sim_001",
            question_text="Maneja esta situación de crisis en el equipo:",
            question_type=QuestionType.INTERACTIVE_SIMULATION,
            difficulty_level=DifficultyLevel.HARD,
            interactive_elements=[
                InteractiveElement(
                    id="crisis_simulation",
                    element_type="scenario_simulator",
                    properties={
                        "scenario_type": "team_conflict",
                        "time_limit": 300,
                        "decision_points": 5
                    }
                )
            ],
            adaptive_difficulty=True,
            category="leadership"
        )
        
        self.questions.update({
            "tech_001": tech_question,
            "interactive_001": interactive_question,
            "sim_001": simulation_question
        })
    
    async def create_assessment(self, template_id: str, customizations: Dict[str, Any] = None) -> str:
        """Crea un nuevo assessment basado en un template."""
        
        assessment_id = str(uuid.uuid4())
        template = self.templates.get(template_id, {})
        
        assessment = {
            "id": assessment_id,
            "template_id": template_id,
            "name": template.get("name", "Custom Assessment"),
            "description": template.get("description", ""),
            "questions": [],
            "settings": {
                "duration_minutes": template.get("duration_minutes", 30),
                "adaptive_difficulty": template.get("adaptive_difficulty", False),
                "branching_logic": template.get("branching_logic", False),
                "randomize_questions": False,
                "show_progress": True,
                "allow_review": False
            },
            "created_at": datetime.now()
        }
        
        # Aplicar customizaciones
        if customizations:
            assessment["settings"].update(customizations.get("settings", {}))
            if "questions" in customizations:
                assessment["questions"] = customizations["questions"]
        
        # Generar preguntas si no se especificaron
        if not assessment["questions"]:
            assessment["questions"] = await self._generate_questions_for_template(template_id)
        
        self.assessments[assessment_id] = assessment
        return assessment_id
    
    async def _generate_questions_for_template(self, template_id: str) -> List[str]:
        """Genera preguntas automáticamente para un template."""
        
        template = self.templates.get(template_id, {})
        question_types = template.get("question_types", [QuestionType.MULTIPLE_CHOICE])
        
        generated_questions = []
        
        # Por ahora, usar preguntas de ejemplo
        for question_id, question in self.questions.items():
            if question.question_type in question_types:
                generated_questions.append(question_id)
        
        return generated_questions
    
    async def start_assessment_session(self, user_id: str, assessment_id: str,
                                     user_profile: Dict[str, Any] = None) -> str:
        """Inicia una nueva sesión de assessment."""
        
        session_id = str(uuid.uuid4())
        assessment = self.assessments.get(assessment_id)
        
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        # Crear sesión
        session = AssessmentSession(
            id=session_id,
            user_id=user_id,
            assessment_id=assessment_id,
            assessment_type=AssessmentType.CUSTOM,
            user_profile=user_profile or {}
        )
        
        # Determinar primera pregunta
        questions = assessment["questions"]
        if questions:
            first_question = await self._select_starting_question(questions, user_profile or {})
            session.current_question_id = first_question
            session.available_next_questions = [first_question]
        
        # Configurar variables de sesión
        session.session_variables = {
            "adaptive_mode": assessment["settings"].get("adaptive_difficulty", False),
            "current_difficulty": DifficultyLevel.MEDIUM.value,
            "performance_score": 0.0,
            "question_sequence": []
        }
        
        self.active_sessions[session_id] = session
        
        logger.info(f"Started assessment session {session_id} for user {user_id}")
        return session_id
    
    async def _select_starting_question(self, questions: List[str], 
                                      user_profile: Dict[str, Any]) -> str:
        """Selecciona la pregunta inicial basada en el perfil del usuario."""
        
        if not questions:
            raise ValueError("No questions available")
        
        # Análisis del perfil para selección inteligente  
        experience_level = user_profile.get("experience_level", "medium") if user_profile else "medium"
        skills = user_profile.get("skills", []) if user_profile else []
        
        # Filtrar preguntas por nivel apropiado
        suitable_questions = []
        
        for question_id in questions:
            question = self.questions.get(question_id)
            if not question:
                continue
            
            # Verificar prerrequisitos
            if question.prerequisite_skills:
                if not any(skill in skills for skill in question.prerequisite_skills):
                    continue
            
            # Ajustar por experiencia
            if experience_level == "junior" and question.difficulty_level.value > 3:
                continue
            elif experience_level == "senior" and question.difficulty_level.value < 3:
                continue
            
            suitable_questions.append(question_id)
        
        return suitable_questions[0] if suitable_questions else questions[0]
    
    async def get_current_question(self, session_id: str) -> Dict[str, Any]:
        """Obtiene la pregunta actual de una sesión."""
        
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not session.current_question_id:
            return {"completed": True, "message": "Assessment completed"}
        
        question = self.questions.get(session.current_question_id)
        if not question:
            raise ValueError(f"Question {session.current_question_id} not found")
        
        # Preparar datos de la pregunta
        question_data = {
            "id": question.id,
            "text": question.question_text,
            "type": question.question_type.value,
            "difficulty": question.difficulty_level.value,
            "options": [],
            "interactive_elements": [],
            "time_limit": question.time_limit,
            "attempts_remaining": question.attempts_allowed,
            "progress": session.completion_percentage
        }
        
        # Procesar opciones
        for option in question.options:
            option_data = {
                "id": option.id,
                "text": option.text,
                "requires_input": option.requires_input,
                "input_type": option.input_type
            }
            
            # Agregar elementos interactivos de la opción
            for element in option.interactive_elements:
                option_data["interactive_elements"] = self._process_interactive_element(element, session)
            
            question_data["options"].append(option_data)
        
        # Procesar elementos interactivos de la pregunta
        for element in question.interactive_elements:
            processed_element = self._process_interactive_element(element, session)
            question_data["interactive_elements"].append(processed_element)
        
        # Aplicar personalización dinámica
        question_data = await self._apply_dynamic_personalization(question_data, session)
        
        return question_data
    
    def _process_interactive_element(self, element: InteractiveElement, 
                                   session: AssessmentSession) -> Dict[str, Any]:
        """Procesa un elemento interactivo para renderizado."""
        
        processed = {
            "id": element.id,
            "type": element.element_type,
            "properties": element.properties.copy(),
            "validation": element.validation,
            "styling": element.styling,
            "events": element.events
        }
        
        # Aplicar personalizaciones basadas en la sesión
        user_profile = session.user_profile
        
        if element.element_type == "sortable_list":
            # Personalizar lista según perfil
            if user_profile.get("industry") == "tech":
                processed["properties"]["items"] = [
                    "Innovación", "Calidad", "Velocidad", "Escalabilidad"
                ]
        
        elif element.element_type == "slider_scale":
            # Ajustar rango según contexto
            if "confidence" in element.properties.get("label", "").lower():
                processed["properties"]["max"] = 10
                processed["properties"]["step"] = 0.5
        
        return processed
    
    async def _apply_dynamic_personalization(self, question_data: Dict[str, Any],
                                           session: AssessmentSession) -> Dict[str, Any]:
        """Aplica personalización dinámica a la pregunta."""
        
        user_profile = session.user_profile
        
        # Personalizar texto según perfil
        if user_profile.get("language", "es") != "es":
            # En un sistema real, aquí se aplicaría traducción
            pass
        
        # Ajustar dificultad si está en modo adaptativo
        if session.session_variables.get("adaptive_mode", False):
            performance = session.session_variables.get("performance_score", 0.5)
            
            if performance > 0.8 and question_data["difficulty"] < 5:
                question_data["difficulty"] += 1
                question_data["adapted"] = True
                question_data["adaptation_reason"] = "High performance detected"
            
            elif performance < 0.3 and question_data["difficulty"] > 1:
                question_data["difficulty"] -= 1
                question_data["adapted"] = True
                question_data["adaptation_reason"] = "Supporting struggling user"
        
        return question_data
    
    async def submit_answer(self, session_id: str, question_id: str, 
                          answer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa la respuesta a una pregunta."""
        
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        question = self.questions.get(question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")
        
        # Crear respuesta
        response = AssessmentResponse(
            question_id=question_id,
            user_answer=answer_data.get("answer"),
            selected_options=answer_data.get("selected_options", []),
            time_completed=datetime.now()
        )
        
        # Calcular tiempo tomado
        if session.last_activity and response.time_completed:
            response.time_taken = (response.time_completed - session.last_activity).total_seconds()
        
        # Calcular score
        score_result = await self._calculate_question_score(question, response, session)
        response.score = score_result["score"]
        response.max_possible_score = score_result["max_score"]
        response.is_correct = score_result["is_correct"]
        response.confidence_level = score_result.get("confidence")
        
        # Agregar respuesta a la sesión
        session.responses.append(response)
        session.questions_completed.append(question_id)
        session.current_score += response.score
        session.max_possible_score += response.max_possible_score
        
        # Actualizar variables de sesión
        await self._update_session_variables(session, response)
        
        # Determinar siguiente pregunta
        next_question = await self._determine_next_question(session, question, response)
        session.current_question_id = next_question
        
        # Calcular progreso
        await self._update_progress(session)
        
        # Verificar si terminó
        if not next_question:
            session.is_completed = True
            await self._finalize_assessment(session)
        
        session.last_activity = datetime.now()
        
        return {
            "score": response.score,
            "max_score": response.max_possible_score,
            "is_correct": response.is_correct,
            "feedback": score_result.get("feedback", ""),
            "next_question_id": next_question,
            "progress": session.completion_percentage,
            "session_completed": session.is_completed
        }
    
    async def _calculate_question_score(self, question: DynamicQuestion, 
                                      response: AssessmentResponse,
                                      session: AssessmentSession) -> Dict[str, Any]:
        """Calcula el score de una respuesta."""
        
        algorithm = self.scoring_algorithms.get(
            question.scoring_algorithm, 
            self._standard_scoring
        )
        
        return await algorithm(question, response, session)
    
    async def _standard_scoring(self, question: DynamicQuestion, 
                              response: AssessmentResponse,
                              session: AssessmentSession) -> Dict[str, Any]:
        """Algoritmo de scoring estándar."""
        
        max_score = question.max_score
        score = 0.0
        feedback = ""
        
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            # Verificar respuesta correcta
            user_answer = response.user_answer
            correct_options = [opt for opt in question.options if opt.is_correct]
            
            if correct_options and user_answer == correct_options[0].value:
                score = max_score
                feedback = "¡Correcto!"
            else:
                score = 0.0
                feedback = "Incorrecto. " + question.feedback_text
        
        elif question.question_type == QuestionType.MULTIPLE_SELECT:
            # Scoring proporcional para selección múltiple
            selected = set(response.selected_options)
            correct = set(opt.id for opt in question.options if opt.is_correct)
            
            if correct:
                intersection = len(selected & correct)
                union = len(selected | correct)
                score = (intersection / len(correct)) * max_score
                feedback = f"Seleccionaste {intersection} de {len(correct)} respuestas correctas"
        
        elif question.question_type == QuestionType.RANKING:
            # Scoring para ranking (correlación de Spearman simplificada)
            user_ranking = response.user_answer
            correct_ranking = question.correct_answers
            
            if user_ranking and correct_ranking:
                # Calcular similitud de rankings
                similarity = self._calculate_ranking_similarity(user_ranking, correct_ranking)
                score = similarity * max_score
                feedback = f"Tu ranking tiene {similarity*100:.1f}% de similitud con el ideal"
        
        # Aplicar bonus por velocidad
        if response.time_taken and question.time_limit:
            time_ratio = response.time_taken / question.time_limit
            if time_ratio < 0.5:  # Completó en menos de la mitad del tiempo
                score *= 1.1  # 10% bonus
                feedback += " ¡Bonus por velocidad!"
        
        return {
            "score": min(score, max_score),
            "max_score": max_score,
            "is_correct": score > (max_score * 0.7),
            "feedback": feedback,
            "confidence": self._calculate_confidence(response, question)
        }
    
    async def _weighted_scoring(self, question: DynamicQuestion, 
                              response: AssessmentResponse,
                              session: AssessmentSession) -> Dict[str, Any]:
        """Algoritmo de scoring con pesos."""
        
        # Implementar scoring ponderado basado en importancia de competencias
        base_result = await self._standard_scoring(question, response, session)
        
        # Aplicar pesos según competencias
        competency_weights = session.user_profile.get("competency_weights", {})
        total_weight = 1.0
        
        for competency in question.competencies:
            weight = competency_weights.get(competency, 1.0)
            total_weight *= weight
        
        base_result["score"] *= total_weight
        return base_result
    
    async def _adaptive_scoring(self, question: DynamicQuestion, 
                              response: AssessmentResponse,
                              session: AssessmentSession) -> Dict[str, Any]:
        """Algoritmo de scoring adaptativo."""
        
        base_result = await self._standard_scoring(question, response, session)
        
        # Ajustar score basado en historial de performance
        performance_trend = session.performance_trends.get("overall", [0.5])
        recent_performance = sum(performance_trend[-3:]) / min(3, len(performance_trend))
        
        # Si el usuario está luchando, ser más generoso con el scoring
        if recent_performance < 0.4:
            base_result["score"] *= 1.2
        elif recent_performance > 0.8:
            # Si está muy bien, ser más estricto
            base_result["score"] *= 0.9
        
        return base_result
    
    async def _irt_scoring(self, question: DynamicQuestion, 
                         response: AssessmentResponse,
                         session: AssessmentSession) -> Dict[str, Any]:
        """Algoritmo basado en Item Response Theory."""
        
        # Implementación simplificada de IRT
        base_result = await self._standard_scoring(question, response, session)
        
        # Parámetros IRT (en un sistema real, estos vendrían de calibración)
        difficulty = question.difficulty_level.value / 6.0  # Normalizar a 0-1
        discrimination = 1.5  # Parámetro de discriminación
        
        # Estimar habilidad del usuario
        user_ability = session.session_variables.get("estimated_ability", 0.5)
        
        # Calcular probabilidad de respuesta correcta
        probability = 1 / (1 + math.exp(-discrimination * (user_ability - difficulty)))
        
        # Ajustar score basado en probabilidad esperada
        if base_result["is_correct"]:
            # Si acertó una pregunta difícil para su nivel, premio extra
            if probability < 0.5:
                base_result["score"] *= 1.3
        else:
            # Si falló una pregunta fácil, penalización menor
            if probability > 0.7:
                base_result["score"] = base_result["max_score"] * 0.1
        
        return base_result
    
    def _calculate_confidence(self, response: AssessmentResponse, 
                            question: DynamicQuestion) -> float:
        """Calcula nivel de confianza en la respuesta."""
        
        confidence = 0.5  # Base
        
        # Factor tiempo
        if response.time_taken and question.time_limit:
            time_ratio = response.time_taken / question.time_limit
            if 0.3 <= time_ratio <= 0.7:  # Tiempo óptimo
                confidence += 0.2
            elif time_ratio < 0.1:  # Muy rápido
                confidence -= 0.3
            elif time_ratio > 0.9:  # Muy lento
                confidence -= 0.1
        
        # Factor de consistencia (si hay patrones previos)
        # En un sistema real, se analizarían patrones de respuesta
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_ranking_similarity(self, user_ranking: List, correct_ranking: List) -> float:
        """Calcula similitud entre dos rankings."""
        
        if len(user_ranking) != len(correct_ranking):
            return 0.0
        
        # Calcular inversiones (pares ordenados incorrectamente)
        inversions = 0
        total_pairs = 0
        
        for i in range(len(user_ranking)):
            for j in range(i + 1, len(user_ranking)):
                total_pairs += 1
                
                # Posiciones en ranking correcto
                pos_i_correct = correct_ranking.index(user_ranking[i])
                pos_j_correct = correct_ranking.index(user_ranking[j])
                
                # Si el orden está invertido, contar inversión
                if pos_i_correct > pos_j_correct:
                    inversions += 1
        
        # Calcular similitud (1 - proporción de inversiones)
        return 1.0 - (inversions / total_pairs) if total_pairs > 0 else 1.0
    
    async def _update_session_variables(self, session: AssessmentSession, 
                                      response: AssessmentResponse):
        """Actualiza variables de sesión basadas en la respuesta."""
        
        # Actualizar performance score
        current_performance = response.score / response.max_possible_score
        session.session_variables["performance_score"] = current_performance
        
        # Actualizar trends
        if "overall" not in session.performance_trends:
            session.performance_trends["overall"] = []
        
        session.performance_trends["overall"].append(current_performance)
        
        # Actualizar habilidad estimada (para IRT)
        if "estimated_ability" not in session.session_variables:
            session.session_variables["estimated_ability"] = 0.5
        
        # Ajuste simple de habilidad
        ability = session.session_variables["estimated_ability"]
        if response.is_correct:
            ability += 0.1
        else:
            ability -= 0.1
        
        session.session_variables["estimated_ability"] = max(0.0, min(1.0, ability))
        
        # Registrar secuencia de preguntas
        session.session_variables["question_sequence"].append({
            "question_id": response.question_id,
            "score": response.score,
            "time_taken": response.time_taken,
            "difficulty": self.questions[response.question_id].difficulty_level.value
        })
    
    async def _determine_next_question(self, session: AssessmentSession,
                                     current_question: DynamicQuestion,
                                     response: AssessmentResponse) -> Optional[str]:
        """Determina la siguiente pregunta usando branching lógico."""
        
        # Verificar reglas de branching de la pregunta actual
        for rule in current_question.branching_rules:
            if await self._evaluate_branching_condition(rule, session, response):
                # Aplicar acciones de la regla
                if rule.set_variables:
                    session.session_variables.update(rule.set_variables)
                
                return rule.target_question_id
        
        # Si no hay branching específico, usar siguiente pregunta por defecto
        if current_question.next_question_id:
            return current_question.next_question_id
        
        # Selección adaptativa basada en performance
        return await self._select_adaptive_next_question(session)
    
    async def _evaluate_branching_condition(self, rule: BranchingRule,
                                          session: AssessmentSession,
                                          response: AssessmentResponse) -> bool:
        """Evalúa si se cumple una condición de branching."""
        
        if rule.condition_type == BranchingCondition.SCORE_THRESHOLD:
            return response.score >= rule.condition_value
        
        elif rule.condition_type == BranchingCondition.SPECIFIC_ANSWER:
            if isinstance(rule.condition_value, list):
                return response.user_answer in rule.condition_value
            else:
                return response.user_answer == rule.condition_value
        
        elif rule.condition_type == BranchingCondition.TIME_TAKEN:
            return response.time_taken <= rule.condition_value
        
        elif rule.condition_type == BranchingCondition.SKILL_LEVEL:
            estimated_ability = session.session_variables.get("estimated_ability", 0.5)
            return estimated_ability >= rule.condition_value
        
        elif rule.condition_type == BranchingCondition.PREVIOUS_PERFORMANCE:
            performance_trend = session.performance_trends.get("overall", [])
            if len(performance_trend) >= 3:
                recent_avg = sum(performance_trend[-3:]) / 3
                return recent_avg >= rule.condition_value
        
        elif rule.condition_type == BranchingCondition.RANDOM:
            return random.random() < rule.condition_value
        
        return False
    
    async def _select_adaptive_next_question(self, session: AssessmentSession) -> Optional[str]:
        """Selecciona la siguiente pregunta de manera adaptativa."""
        
        assessment = self.assessments[session.assessment_id]
        remaining_questions = [
            q for q in assessment["questions"] 
            if q not in session.questions_completed
        ]
        
        if not remaining_questions:
            return None  # Assessment completado
        
        # Si no está en modo adaptativo, tomar la siguiente
        if not session.session_variables.get("adaptive_mode", False):
            return remaining_questions[0]
        
        # Selección adaptativa basada en performance y dificultad
        estimated_ability = session.session_variables.get("estimated_ability", 0.5)
        
        best_question = None
        best_score = -1
        
        for question_id in remaining_questions:
            question = self.questions.get(question_id)
            if not question:
                continue
            
            # Calcular qué tan bien la dificultad coincide con la habilidad
            difficulty_normalized = question.difficulty_level.value / 6.0
            match_score = 1.0 - abs(estimated_ability - difficulty_normalized)
            
            if match_score > best_score:
                best_score = match_score
                best_question = question_id
        
        return best_question
    
    async def _update_progress(self, session: AssessmentSession):
        """Actualiza el progreso de la sesión."""
        
        assessment = self.assessments[session.assessment_id]
        total_questions = len(assessment["questions"])
        completed_questions = len(session.questions_completed)
        
        session.completion_percentage = (completed_questions / total_questions) * 100
        
        # Estimar tiempo restante
        if session.responses:
            avg_time_per_question = sum(r.time_taken for r in session.responses) / len(session.responses)
            remaining_questions = total_questions - completed_questions
            session.estimated_completion_time = int(avg_time_per_question * remaining_questions)
    
    async def _finalize_assessment(self, session: AssessmentSession):
        """Finaliza un assessment y calcula resultados finales."""
        
        # Calcular score final
        if session.max_possible_score > 0:
            final_score_percentage = (session.current_score / session.max_possible_score) * 100
        else:
            final_score_percentage = 0
        
        # Generar reporte de competencias
        competency_scores = self._calculate_competency_scores(session)
        
        # Generar recomendaciones
        recommendations = await self._generate_recommendations(session, competency_scores)
        
        # Almacenar resultados
        session.session_variables.update({
            "final_score_percentage": final_score_percentage,
            "competency_scores": competency_scores,
            "recommendations": recommendations,
            "completion_time": (datetime.now() - session.started_at).total_seconds()
        })
        
        logger.info(f"Assessment completed: {session.id} - Score: {final_score_percentage:.1f}%")
    
    def _calculate_competency_scores(self, session: AssessmentSession) -> Dict[str, float]:
        """Calcula scores por competencia."""
        
        competency_scores = {}
        competency_totals = {}
        
        for response in session.responses:
            question = self.questions.get(response.question_id)
            if not question:
                continue
            
            for competency in question.competencies:
                if competency not in competency_scores:
                    competency_scores[competency] = 0
                    competency_totals[competency] = 0
                
                competency_scores[competency] += response.score
                competency_totals[competency] += response.max_possible_score
        
        # Normalizar scores
        for competency in competency_scores:
            if competency_totals[competency] > 0:
                competency_scores[competency] = (
                    competency_scores[competency] / competency_totals[competency]
                ) * 100
        
        return competency_scores
    
    async def _generate_recommendations(self, session: AssessmentSession,
                                      competency_scores: Dict[str, float]) -> List[str]:
        """Genera recomendaciones basadas en resultados."""
        
        recommendations = []
        
        # Recomendaciones basadas en competencias débiles
        weak_competencies = [
            comp for comp, score in competency_scores.items() 
            if score < 60
        ]
        
        for competency in weak_competencies:
            recommendations.append(
                f"Considera reforzar tus habilidades en {competency} "
                f"mediante cursos especializados."
            )
        
        # Recomendaciones basadas en fortalezas
        strong_competencies = [
            comp for comp, score in competency_scores.items() 
            if score > 85
        ]
        
        for competency in strong_competencies:
            recommendations.append(
                f"Excelente dominio en {competency}. "
                f"Podrías considerar roles de liderazgo en esta área."
            )
        
        # Recomendaciones basadas en patrones de respuesta
        performance_trend = session.performance_trends.get("overall", [])
        if len(performance_trend) > 3:
            if all(p < 0.5 for p in performance_trend[-3:]):
                recommendations.append(
                    "Se detectó una tendencia descendente en el rendimiento. "
                    "Considera tomar descansos durante evaluaciones largas."
                )
        
        return recommendations
    
    def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """Obtiene los resultados completos de una sesión."""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        if not session.is_completed:
            return {"error": "Assessment not completed yet"}
        
        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "assessment_id": session.assessment_id,
            "final_score": session.session_variables.get("final_score_percentage", 0),
            "competency_scores": session.session_variables.get("competency_scores", {}),
            "recommendations": session.session_variables.get("recommendations", []),
            "completion_time_minutes": session.session_variables.get("completion_time", 0) / 60,
            "questions_completed": len(session.questions_completed),
            "total_questions": len(session.responses),
            "performance_trend": session.performance_trends.get("overall", []),
            "difficulty_adjustments": session.difficulty_adjustments,
            "started_at": session.started_at.isoformat(),
            "completed_at": datetime.now().isoformat()
        }

# Funciones de utilidad
async def create_quick_assessment(assessment_type: str, user_id: str) -> str:
    """Función de conveniencia para crear assessments rápidos."""
    
    engine = DynamicAssessmentEngine()
    
    # Crear assessment basado en tipo
    template_map = {
        "technical": "technical_skills",
        "personality": "personality_profile",
        "cognitive": "cognitive_ability"
    }
    
    template_id = template_map.get(assessment_type, "technical_skills")
    assessment_id = await engine.create_assessment(template_id)
    
    # Iniciar sesión
    session_id = await engine.start_assessment_session(user_id, assessment_id)
    
    return session_id

# Exportaciones
__all__ = [
    'QuestionType', 'DifficultyLevel', 'BranchingCondition', 'AssessmentType',
    'InteractiveElement', 'QuestionOption', 'BranchingRule', 'DynamicQuestion',
    'AssessmentResponse', 'AssessmentSession', 'DynamicAssessmentEngine',
    'create_quick_assessment'
]