# /home/pablo/app/ats/integrations/services/assessment.py
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from django.core.cache import cache
from .base import Button, MAX_RETRIES, CACHE_TIMEOUT

logger = logging.getLogger('integrations')

class Assessment:
    """
    Clase base para evaluaciones
    """
    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        questions: List[Dict[str, Any]],
        time_limit: Optional[int] = None
    ):
        self.id = id
        self.title = title
        self.description = description
        self.questions = questions
        self.time_limit = time_limit

    def get_question(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene una pregunta por índice
        """
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None

    def get_total_questions(self) -> int:
        """
        Obtiene el total de preguntas
        """
        return len(self.questions)

class AssessmentService:
    """
    Servicio para manejar evaluaciones
    """
    def __init__(self):
        self._assessments: Dict[str, Assessment] = {}

    def register_assessment(self, assessment: Assessment):
        """
        Registra una evaluación
        """
        self._assessments[assessment.id] = assessment

    def get_assessment(self, assessment_id: str) -> Optional[Assessment]:
        """
        Obtiene una evaluación por ID
        """
        return self._assessments.get(assessment_id)

    async def start_assessment(
        self,
        user_id: str,
        assessment_id: str,
        business_unit: str
    ) -> bool:
        """
        Inicia una evaluación para un usuario
        """
        assessment = self.get_assessment(assessment_id)
        if not assessment:
            logger.error(f"Assessment {assessment_id} not found")
            return False

        cache_key = f"assessment:{user_id}:{assessment_id}"
        assessment_data = {
            "start_time": datetime.now().isoformat(),
            "current_question": 0,
            "answers": [],
            "completed": False
        }

        if assessment.time_limit:
            assessment_data["end_time"] = (
                datetime.now() + assessment.time_limit
            ).isoformat()

        cache.set(cache_key, assessment_data, CACHE_TIMEOUT)
        return True

    async def submit_answer(
        self,
        user_id: str,
        assessment_id: str,
        answer: Any
    ) -> bool:
        """
        Envía una respuesta para una evaluación
        """
        cache_key = f"assessment:{user_id}:{assessment_id}"
        assessment_data = cache.get(cache_key)

        if not assessment_data:
            logger.error(f"No active assessment found for user {user_id}")
            return False

        assessment = self.get_assessment(assessment_id)
        if not assessment:
            logger.error(f"Assessment {assessment_id} not found")
            return False

        current_question = assessment_data["current_question"]
        question = assessment.get_question(current_question)

        if not question:
            logger.error(f"Question {current_question} not found")
            return False

        assessment_data["answers"].append({
            "question_id": question["id"],
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        })

        assessment_data["current_question"] += 1

        if assessment_data["current_question"] >= assessment.get_total_questions():
            assessment_data["completed"] = True

        cache.set(cache_key, assessment_data, CACHE_TIMEOUT)
        return True

    async def get_current_question(
        self,
        user_id: str,
        assessment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene la pregunta actual de una evaluación
        """
        cache_key = f"assessment:{user_id}:{assessment_id}"
        assessment_data = cache.get(cache_key)

        if not assessment_data:
            return None

        assessment = self.get_assessment(assessment_id)
        if not assessment:
            return None

        current_question = assessment_data["current_question"]
        return assessment.get_question(current_question)

    async def get_assessment_progress(
        self,
        user_id: str,
        assessment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene el progreso de una evaluación
        """
        cache_key = f"assessment:{user_id}:{assessment_id}"
        return cache.get(cache_key)

    async def complete_assessment(
        self,
        user_id: str,
        assessment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Completa una evaluación y retorna los resultados
        """
        cache_key = f"assessment:{user_id}:{assessment_id}"
        assessment_data = cache.get(cache_key)

        if not assessment_data:
            return None

        assessment = self.get_assessment(assessment_id)
        if not assessment:
            return None

        results = {
            "assessment_id": assessment_id,
            "user_id": user_id,
            "start_time": assessment_data["start_time"],
            "end_time": datetime.now().isoformat(),
            "answers": assessment_data["answers"],
            "total_questions": assessment.get_total_questions(),
            "completed_questions": len(assessment_data["answers"])
        }

        cache.delete(cache_key)
        return results

# Instancia global del servicio de evaluaciones
assessment_service = AssessmentService()

# Registro de evaluaciones predefinidas
assessment_service.register_assessment(
    Assessment(
        id="tech_assessment",
        title="Evaluación Técnica",
        description="Evaluación de conocimientos técnicos",
        questions=[
            {
                "id": "tech_1",
                "text": "¿Qué es un algoritmo?",
                "type": "text"
            },
            {
                "id": "tech_2",
                "text": "¿Cuál es la diferencia entre HTTP y HTTPS?",
                "type": "text"
            },
            {
                "id": "tech_3",
                "text": "¿Qué es la programación orientada a objetos?",
                "type": "text"
            }
        ],
        time_limit=3600  # 1 hora
    )
)

assessment_service.register_assessment(
    Assessment(
        id="health_assessment",
        title="Evaluación de Salud",
        description="Evaluación de conocimientos en salud",
        questions=[
            {
                "id": "health_1",
                "text": "¿Cuáles son los signos vitales?",
                "type": "text"
            },
            {
                "id": "health_2",
                "text": "¿Qué es la presión arterial?",
                "type": "text"
            },
            {
                "id": "health_3",
                "text": "¿Cuáles son los primeros auxilios básicos?",
                "type": "text"
            }
        ],
        time_limit=1800  # 30 minutos
    )
) 