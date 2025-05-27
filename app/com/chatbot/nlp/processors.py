"""
Procesadores de análisis para Grupo huntRED®.
Contiene los procesadores para diferentes tipos de análisis.
"""

# Importaciones estándar de Python
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

# Importaciones de Django
from django.conf import settings
from django.core.cache import cache

# Importaciones de utilidades
from app.com.utils.logger_utils import get_module_logger

# Configuración del logger
logger = get_module_logger('nlp.processors')

class PersonalityTestProcessor:
    """Procesa la prueba de personalidad."""
    
    def __init__(self):
        self.questions = [
            {
                "id": 1,
                "text": "¿Cómo te describirías en situaciones sociales?",
                "options": [
                    {"text": "Extrovertido y sociable", "score": {"extroversion": 2}},
                    {"text": "Equilibrado", "score": {"extroversion": 1}},
                    {"text": "Introvertido y reservado", "score": {"extroversion": 0}}
                ]
            },
            {
                "id": 2,
                "text": "¿Cómo manejas los cambios?",
                "options": [
                    {"text": "Me adapto fácilmente", "score": {"adaptability": 2}},
                    {"text": "Me cuesta un poco", "score": {"adaptability": 1}},
                    {"text": "Prefiero la estabilidad", "score": {"adaptability": 0}}
                ]
            },
            # ... más preguntas ...
        ]
        self.results = {
            "extroversion": {
                "high": "Eres una persona sociable y energética",
                "medium": "Tienes un balance entre sociabilidad e introspección",
                "low": "Eres una persona reflexiva y reservada"
            },
            "adaptability": {
                "high": "Eres muy flexible y adaptable",
                "medium": "Tienes una adaptabilidad moderada",
                "low": "Prefieres entornos estables y predecibles"
            }
            # ... más resultados ...
        }

    async def process_answer(self, question_id: int, answer: str) -> dict:
        """Procesa una respuesta individual."""
        question = next((q for q in self.questions if q["id"] == question_id), None)
        if not question:
            return None

        option = next((opt for opt in question["options"] if opt["text"] == answer), None)
        return option["score"] if option else None

    async def calculate_result(self, answers: dict) -> dict:
        """Calcula el resultado final basado en todas las respuestas."""
        scores = {}
        for answer in answers.values():
            for trait, score in answer.items():
                scores[trait] = scores.get(trait, 0) + score

        result = {}
        for trait, score in scores.items():
            if score >= 4:
                level = "high"
            elif score >= 2:
                level = "medium"
            else:
                level = "low"
            result[trait] = self.results[trait][level]

        return result

class TalentAnalysisProcessor:
    """Procesa el análisis de talento 360°."""
    
    def __init__(self):
        self.questions = [
            {
                "id": 1,
                "text": "¿Cómo evalúas tu capacidad de liderazgo?",
                "options": [
                    {"text": "Excelente", "score": {"leadership": 2}},
                    {"text": "Buena", "score": {"leadership": 1}},
                    {"text": "En desarrollo", "score": {"leadership": 0}}
                ]
            },
            {
                "id": 2,
                "text": "¿Cómo manejas los conflictos?",
                "options": [
                    {"text": "Busco soluciones colaborativas", "score": {"conflict_resolution": 2}},
                    {"text": "Intento mediar", "score": {"conflict_resolution": 1}},
                    {"text": "Evito los conflictos", "score": {"conflict_resolution": 0}}
                ]
            },
            # ... más preguntas ...
        ]
        self.results = {
            "leadership": {
                "high": "Tienes un fuerte potencial de liderazgo",
                "medium": "Tienes habilidades de liderazgo básicas",
                "low": "Tu liderazgo está en desarrollo"
            },
            "conflict_resolution": {
                "high": "Eres experto en resolver conflictos",
                "medium": "Tienes buenas habilidades de resolución",
                "low": "Necesitas mejorar en resolución de conflictos"
            }
            # ... más resultados ...
        }

    async def process_answer(self, question_id: int, answer: str) -> dict:
        """Procesa una respuesta individual."""
        question = next((q for q in self.questions if q["id"] == question_id), None)
        if not question:
            return None

        option = next((opt for opt in question["options"] if opt["text"] == answer), None)
        return option["score"] if option else None

    async def calculate_result(self, answers: dict) -> dict:
        """Calcula el resultado final basado en todas las respuestas."""
        scores = {}
        for answer in answers.values():
            for trait, score in answer.items():
                scores[trait] = scores.get(trait, 0) + score

        result = {}
        for trait, score in scores.items():
            if score >= 4:
                level = "high"
            elif score >= 2:
                level = "medium"
            else:
                level = "low"
            result[trait] = self.results[trait][level]

        return result

class CulturalAnalysisProcessor:
    """Procesa el análisis de compatibilidad cultural."""
    
    def __init__(self):
        self.questions = [
            {
                "id": 1,
                "text": "¿Qué valoras más en una empresa?",
                "options": [
                    {"text": "Innovación y creatividad", "score": {"innovation": 2}},
                    {"text": "Estabilidad y tradición", "score": {"stability": 2}},
                    {"text": "Equilibrio entre ambos", "score": {"balance": 1}}
                ]
            },
            {
                "id": 2,
                "text": "¿Cómo prefieres trabajar?",
                "options": [
                    {"text": "En equipo colaborativo", "score": {"teamwork": 2}},
                    {"text": "De forma independiente", "score": {"independence": 2}},
                    {"text": "Combinando ambos", "score": {"flexible": 1}}
                ]
            },
            # ... más preguntas ...
        ]
        self.results = {
            "innovation": {
                "high": "Te adaptas bien a culturas innovadoras",
                "medium": "Valoras la innovación moderadamente",
                "low": "Prefieres entornos más tradicionales"
            },
            "teamwork": {
                "high": "Eres un excelente colaborador",
                "medium": "Tienes buen balance individual/grupo",
                "low": "Prefieres trabajar de forma independiente"
            }
            # ... más resultados ...
        }

    async def process_answer(self, question_id: int, answer: str) -> dict:
        """Procesa una respuesta individual."""
        question = next((q for q in self.questions if q["id"] == question_id), None)
        if not question:
            return None

        option = next((opt for opt in question["options"] if opt["text"] == answer), None)
        return option["score"] if option else None

    async def calculate_result(self, answers: dict) -> dict:
        """Calcula el resultado final basado en todas las respuestas."""
        scores = {}
        for answer in answers.values():
            for trait, score in answer.items():
                scores[trait] = scores.get(trait, 0) + score

        result = {}
        for trait, score in scores.items():
            if score >= 4:
                level = "high"
            elif score >= 2:
                level = "medium"
            else:
                level = "low"
            result[trait] = self.results[trait][level]

        return result

class MobilityAnalysisProcessor:
    """Procesa el análisis de movilidad."""
    
    def __init__(self):
        self.questions = [
            {
                "id": 1,
                "text": "¿Has trabajado en diferentes ciudades?",
                "options": [
                    {"text": "Sí, varias veces", "score": {"experience": 2}},
                    {"text": "Una o dos veces", "score": {"experience": 1}},
                    {"text": "Nunca", "score": {"experience": 0}}
                ]
            },
            {
                "id": 2,
                "text": "¿Cómo te sientes con la idea de mudarte?",
                "options": [
                    {"text": "Muy cómodo", "score": {"willingness": 2}},
                    {"text": "Depende de las condiciones", "score": {"willingness": 1}},
                    {"text": "Prefiero no mudarme", "score": {"willingness": 0}}
                ]
            },
            # ... más preguntas ...
        ]
        self.results = {
            "experience": {
                "high": "Tienes amplia experiencia en movilidad",
                "medium": "Tienes algo de experiencia en movilidad",
                "low": "No tienes experiencia en movilidad"
            },
            "willingness": {
                "high": "Estás muy abierto a la movilidad",
                "medium": "Estás moderadamente abierto",
                "low": "Prefieres mantenerte en tu ubicación actual"
            }
            # ... más resultados ...
        }

    async def process_answer(self, question_id: int, answer: str) -> dict:
        """Procesa una respuesta individual."""
        question = next((q for q in self.questions if q["id"] == question_id), None)
        if not question:
            return None

        option = next((opt for opt in question["options"] if opt["text"] == answer), None)
        return option["score"] if option else None

    async def calculate_result(self, answers: dict) -> dict:
        """Calcula el resultado final basado en todas las respuestas."""
        scores = {}
        for answer in answers.values():
            for trait, score in answer.items():
                scores[trait] = scores.get(trait, 0) + score

        result = {}
        for trait, score in scores.items():
            if score >= 4:
                level = "high"
            elif score >= 2:
                level = "medium"
            else:
                level = "low"
            result[trait] = self.results[trait][level]

        return result

class SkillsAnalysisProcessor:
    """Procesa el análisis de habilidades."""
    
    def __init__(self):
        self.questions = [
            {
                "id": 1,
                "text": "¿Cómo evalúas tus habilidades técnicas?",
                "options": [
                    {"text": "Avanzadas", "score": {"technical": 2}},
                    {"text": "Intermedias", "score": {"technical": 1}},
                    {"text": "Básicas", "score": {"technical": 0}}
                ]
            },
            {
                "id": 2,
                "text": "¿Cómo evalúas tus habilidades blandas?",
                "options": [
                    {"text": "Excelentes", "score": {"soft": 2}},
                    {"text": "Buenas", "score": {"soft": 1}},
                    {"text": "En desarrollo", "score": {"soft": 0}}
                ]
            },
            # ... más preguntas ...
        ]
        self.results = {
            "technical": {
                "high": "Tienes habilidades técnicas avanzadas",
                "medium": "Tienes habilidades técnicas intermedias",
                "low": "Tus habilidades técnicas son básicas"
            },
            "soft": {
                "high": "Tienes excelentes habilidades blandas",
                "medium": "Tienes buenas habilidades blandas",
                "low": "Tus habilidades blandas están en desarrollo"
            }
            # ... más resultados ...
        }

    async def process_answer(self, question_id: int, answer: str) -> dict:
        """Procesa una respuesta individual."""
        question = next((q for q in self.questions if q["id"] == question_id), None)
        if not question:
            return None

        option = next((opt for opt in question["options"] if opt["text"] == answer), None)
        return option["score"] if option else None

    async def calculate_result(self, answers: dict) -> dict:
        """Calcula el resultado final basado en todas las respuestas."""
        scores = {}
        for answer in answers.values():
            for trait, score in answer.items():
                scores[trait] = scores.get(trait, 0) + score

        result = {}
        for trait, score in scores.items():
            if score >= 4:
                level = "high"
            elif score >= 2:
                level = "medium"
            else:
                level = "low"
            result[trait] = self.results[trait][level]

        return result

class GenerationalAnalysisProcessor:
    """Procesa el análisis generacional."""
    
    def __init__(self):
        self.questions = [
            {
                "id": 1,
                "text": "¿Qué valoras más en el trabajo?",
                "options": [
                    {"text": "Equilibrio vida-trabajo", "score": {"work_life_balance": 2}},
                    {"text": "Estabilidad y seguridad", "score": {"stability": 2}},
                    {"text": "Crecimiento y desarrollo", "score": {"growth": 2}}
                ]
            },
            {
                "id": 2,
                "text": "¿Cómo prefieres comunicarte?",
                "options": [
                    {"text": "Digital y asíncrono", "score": {"digital": 2}},
                    {"text": "Presencial", "score": {"face_to_face": 2}},
                    {"text": "Combinación de ambos", "score": {"hybrid": 1}}
                ]
            },
            # ... más preguntas ...
        ]
        self.results = {
            "work_life_balance": {
                "high": "Valoras mucho el equilibrio",
                "medium": "Buscas un balance moderado",
                "low": "Priorizas otros aspectos"
            },
            "digital": {
                "high": "Prefieres la comunicación digital",
                "medium": "Te adaptas a diferentes medios",
                "low": "Prefieres la comunicación presencial"
            }
            # ... más resultados ...
        }

    async def process_answer(self, question_id: int, answer: str) -> dict:
        """Procesa una respuesta individual."""
        question = next((q for q in self.questions if q["id"] == question_id), None)
        if not question:
            return None

        option = next((opt for opt in question["options"] if opt["text"] == answer), None)
        return option["score"] if option else None

    async def calculate_result(self, answers: dict) -> dict:
        """Calcula el resultado final basado en todas las respuestas."""
        scores = {}
        for answer in answers.values():
            for trait, score in answer.items():
                scores[trait] = scores.get(trait, 0) + score

        result = {}
        for trait, score in scores.items():
            if score >= 4:
                level = "high"
            elif score >= 2:
                level = "medium"
            else:
                level = "low"
            result[trait] = self.results[trait][level]

        return result

class MotivationalAnalysisProcessor:
    """Procesa el análisis motivacional."""
    
    def __init__(self):
        self.questions = [
            {
                "id": 1,
                "text": "¿Qué te motiva más en el trabajo?",
                "options": [
                    {"text": "Reconocimiento y logros", "score": {"achievement": 2}},
                    {"text": "Aprendizaje y crecimiento", "score": {"growth": 2}},
                    {"text": "Estabilidad y seguridad", "score": {"security": 2}}
                ]
            },
            {
                "id": 2,
                "text": "¿Cómo te sientes con los desafíos?",
                "options": [
                    {"text": "Me motivan y energizan", "score": {"challenge": 2}},
                    {"text": "Los acepto con cautela", "score": {"cautious": 1}},
                    {"text": "Prefiero evitar riesgos", "score": {"risk_averse": 0}}
                ]
            },
            # ... más preguntas ...
        ]
        self.results = {
            "achievement": {
                "high": "Te motiva mucho el reconocimiento",
                "medium": "Valoras el reconocimiento moderadamente",
                "low": "Otros factores te motivan más"
            },
            "challenge": {
                "high": "Te motivan los desafíos",
                "medium": "Aceptas desafíos con precaución",
                "low": "Prefieres evitar desafíos"
            }
            # ... más resultados ...
        }

    async def process_answer(self, question_id: int, answer: str) -> dict:
        """Procesa una respuesta individual."""
        question = next((q for q in self.questions if q["id"] == question_id), None)
        if not question:
            return None

        option = next((opt for opt in question["options"] if opt["text"] == answer), None)
        return option["score"] if option else None

    async def calculate_result(self, answers: dict) -> dict:
        """Calcula el resultado final basado en todas las respuestas."""
        scores = {}
        for answer in answers.values():
            for trait, score in answer.items():
                scores[trait] = scores.get(trait, 0) + score

        result = {}
        for trait, score in scores.items():
            if score >= 4:
                level = "high"
            elif score >= 2:
                level = "medium"
            else:
                level = "low"
            result[trait] = self.results[trait][level]

        return result

class WorkStyleAnalysisProcessor:
    """Procesa el análisis de estilos de trabajo."""
    
    def __init__(self):
        self.questions = [
            {
                "id": 1,
                "text": "¿Cómo prefieres organizar tu trabajo?",
                "options": [
                    {"text": "Estructurado y planificado", "score": {"structured": 2}},
                    {"text": "Flexible y adaptable", "score": {"flexible": 2}},
                    {"text": "Combinación de ambos", "score": {"balanced": 1}}
                ]
            },
            {
                "id": 2,
                "text": "¿Cómo manejas las decisiones?",
                "options": [
                    {"text": "Analítico y detallado", "score": {"analytical": 2}},
                    {"text": "Intuitivo y rápido", "score": {"intuitive": 2}},
                    {"text": "Depende de la situación", "score": {"adaptive": 1}}
                ]
            },
            # ... más preguntas ...
        ]
        self.results = {
            "structured": {
                "high": "Prefieres un estilo estructurado",
                "medium": "Buscas un balance en la estructura",
                "low": "Prefieres un estilo más flexible"
            },
            "analytical": {
                "high": "Tienes un enfoque analítico",
                "medium": "Combinas análisis e intuición",
                "low": "Prefieres un enfoque más intuitivo"
            }
            # ... más resultados ...
        }

    async def process_answer(self, question_id: int, answer: str) -> dict:
        """Procesa una respuesta individual."""
        question = next((q for q in self.questions if q["id"] == question_id), None)
        if not question:
            return None

        option = next((opt for opt in question["options"] if opt["text"] == answer), None)
        return option["score"] if option else None

    async def calculate_result(self, answers: dict) -> dict:
        """Calcula el resultado final basado en todas las respuestas."""
        scores = {}
        for answer in answers.values():
            for trait, score in answer.items():
                scores[trait] = scores.get(trait, 0) + score

        result = {}
        for trait, score in scores.items():
            if score >= 4:
                level = "high"
            elif score >= 2:
                level = "medium"
            else:
                level = "low"
            result[trait] = self.results[trait][level]

        return result 