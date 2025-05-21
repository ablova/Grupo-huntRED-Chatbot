from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class QuestionCategory(Enum):
    LEADERSHIP = "leadership"
    INNOVATION = "innovation"
    COMMUNICATION = "communication"
    RESILIENCE = "resilience"
    RESULTS = "results"

class BusinessUnit(Enum):
    HUNTRED_EXECUTIVE = "huntred_executive"
    HUNTRED = "huntred"
    HUNTU = "huntu"
    AMIGRO = "amigro"

@dataclass
class Question:
    id: int
    text: str
    category: QuestionCategory
    options: List[str]
    weights: Dict[str, float]
    business_unit: Optional[BusinessUnit] = None
    difficulty_level: int = 1  # 1-5, donde 5 es el más complejo

class ProfessionalDNAQuestions:
    def __init__(self, business_unit: BusinessUnit = BusinessUnit.HUNTRED):
        self.business_unit = business_unit
        self.questions = self._initialize_questions()

    def _initialize_questions(self) -> List[Question]:
        base_questions = [
            # Preguntas base para todas las unidades
            Question(
                id=1,
                text="En una situación de crisis, ¿cómo sueles manejar la presión?",
                category=QuestionCategory.LEADERSHIP,
                options=[
                    "Tomo decisiones rápidas",
                    "Analizo todas las opciones",
                    "Consulto con el equipo",
                    "Sigo protocolos establecidos"
                ],
                weights={"A": 0.3, "B": 0.3, "C": 0.2, "D": 0.2},
                difficulty_level=2
            ),
            Question(
                id=2,
                text="Cuando lideras un equipo, ¿qué aspecto priorizas más?",
                category=QuestionCategory.LEADERSHIP,
                options=[
                    "Resultados",
                    "Bienestar del equipo",
                    "Innovación",
                    "Estabilidad"
                ],
                weights={"A": 0.3, "B": 0.3, "C": 0.2, "D": 0.2}
            ),
            # ... (resto de preguntas de liderazgo)

            # Innovación y Adaptabilidad
            Question(
                id=6,
                text="¿Cómo reaccionas ante cambios inesperados?",
                category=QuestionCategory.INNOVATION,
                options=[
                    "Me adapto rápidamente",
                    "Necesito tiempo para procesar",
                    "Busco estabilidad",
                    "Veo oportunidades"
                ],
                weights={"A": 0.3, "B": 0.2, "C": 0.2, "D": 0.3}
            ),
            # ... (resto de preguntas de innovación)

            # Comunicación y Colaboración
            Question(
                id=11,
                text="¿Cómo prefieres comunicarte con tu equipo?",
                category=QuestionCategory.COMMUNICATION,
                options=[
                    "Reuniones presenciales",
                    "Comunicación asíncrona",
                    "Híbrido",
                    "Según el contexto"
                ],
                weights={"A": 0.2, "B": 0.2, "C": 0.3, "D": 0.3}
            ),
            # ... (resto de preguntas de comunicación)

            # Gestión de Estrés y Resiliencia
            Question(
                id=16,
                text="¿Cómo manejas los plazos ajustados?",
                category=QuestionCategory.RESILIENCE,
                options=[
                    "Priorizo y delego",
                    "Trabajo más horas",
                    "Pido extensión",
                    "Simplifico el alcance"
                ],
                weights={"A": 0.4, "B": 0.2, "C": 0.2, "D": 0.2}
            ),
            # ... (resto de preguntas de resiliencia)

            # Orientación a Resultados
            Question(
                id=21,
                text="¿Cómo defines el éxito en tu trabajo?",
                category=QuestionCategory.RESULTS,
                options=[
                    "Metas alcanzadas",
                    "Impacto generado",
                    "Crecimiento personal",
                    "Reconocimiento"
                ],
                weights={"A": 0.3, "B": 0.3, "C": 0.2, "D": 0.2}
            ),
            # ... (resto de preguntas de resultados)
        ]

        # Preguntas específicas por unidad de negocio
        unit_specific_questions = {
            BusinessUnit.HUNTRED_EXECUTIVE: [
                Question(
                    id=101,
                    text="¿Cómo manejas la transformación digital en una organización tradicional?",
                    category=QuestionCategory.INNOVATION,
                    options=[
                        "Impulso cambios disruptivos",
                        "Busco una evolución gradual",
                        "Mantengo lo que funciona",
                        "Espero a que otros lo hagan"
                    ],
                    weights={"A": 0.4, "B": 0.3, "C": 0.2, "D": 0.1},
                    business_unit=BusinessUnit.HUNTRED_EXECUTIVE,
                    difficulty_level=5
                ),
                # ... más preguntas específicas para Executive
            ],
            BusinessUnit.HUNTRED: [
                Question(
                    id=201,
                    text="¿Cómo manejas la gestión de talento en un entorno competitivo?",
                    category=QuestionCategory.LEADERSHIP,
                    options=[
                        "Desarrollo planes de carrera",
                        "Enfoque en retención",
                        "Contratación estratégica",
                        "Gestión por objetivos"
                    ],
                    weights={"A": 0.3, "B": 0.3, "C": 0.2, "D": 0.2},
                    business_unit=BusinessUnit.HUNTRED,
                    difficulty_level=4
                ),
                # ... más preguntas específicas para huntRED
            ],
            BusinessUnit.HUNTU: [
                Question(
                    id=301,
                    text="¿Cómo manejas el aprendizaje continuo en tu equipo?",
                    category=QuestionCategory.INNOVATION,
                    options=[
                        "Implemento programas de formación",
                        "Fomento la autogestión",
                        "Sigo el plan establecido",
                        "Enfoque en la práctica"
                    ],
                    weights={"A": 0.3, "B": 0.3, "C": 0.2, "D": 0.2},
                    business_unit=BusinessUnit.HUNTU,
                    difficulty_level=3
                ),
                # ... más preguntas específicas para huntU
            ],
            BusinessUnit.AMIGRO: [
                Question(
                    id=401,
                    text="¿Cómo manejas la colaboración en proyectos multidisciplinarios?",
                    category=QuestionCategory.COMMUNICATION,
                    options=[
                        "Fomento la integración",
                        "Divido responsabilidades",
                        "Sigo la jerarquía",
                        "Trabajo independiente"
                    ],
                    weights={"A": 0.3, "B": 0.3, "C": 0.2, "D": 0.2},
                    business_unit=BusinessUnit.AMIGRO,
                    difficulty_level=2
                ),
                # ... más preguntas específicas para amigro
            ]
        }

        # Combinar preguntas base con las específicas de la unidad
        all_questions = base_questions + unit_specific_questions.get(self.business_unit, [])
        
        # Ajustar pesos según la unidad de negocio
        for question in all_questions:
            if question.business_unit == self.business_unit:
                # Aumentar peso para preguntas específicas de la unidad
                question.weights = {k: v * 1.2 for k, v in question.weights.items()}
        
        return all_questions

    def get_questions_by_category(self, category: QuestionCategory) -> List[Question]:
        return [q for q in self.questions if q.category == category]

    def get_questions_by_difficulty(self, min_level: int, max_level: int) -> List[Question]:
        return [q for q in self.questions if min_level <= q.difficulty_level <= max_level]

    def get_question_by_id(self, question_id: int) -> Optional[Question]:
        return next((q for q in self.questions if q.id == question_id), None)

    def get_all_questions(self) -> List[Question]:
        return self.questions

    def get_unit_specific_questions(self) -> List[Question]:
        return [q for q in self.questions if q.business_unit == self.business_unit] 