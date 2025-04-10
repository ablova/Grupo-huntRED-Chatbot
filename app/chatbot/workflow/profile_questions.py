# /home/pablo/app/chatbot/workflow/profile_questions.py
import re

# Preguntas comunes a todas las unidades de negocio
COMMON_QUESTIONS = {
    "nombre": {
        "question": "¿Cuál es tu nombre?",
        "next": "apellido_paterno",
        "validation": lambda x: len(x) > 1
    },
    "apellido_paterno": {
        "question": "Gracias, {nombre}. ¿Cuál es tu apellido paterno?",
        "next": "email",
        "validation": lambda x: len(x) > 1
    },
    "email": {
        "question": "¿Cuál es tu correo electrónico?",
        "next": "phone",
        "validation": lambda x: bool(re.match(r"[^@]+@[^@]+\.[^@]+", x))
    },
    "phone": {
        "question": "Por último, ¿cuál es tu número de teléfono? (ej. +525534567890)",
        "next": "work_experience",
        "validation": lambda x: bool(re.match(r"^\+\d{10,15}$", x))
    },
    "work_experience": {
        "question": "¿Cuál ha sido tu experiencia laboral más reciente? Cuéntame sobre tu rol y responsabilidades.",
        "next": "skills",
        "validation": lambda x: len(x) > 10
    }
}

# Preguntas específicas por unidad de negocio
QUESTIONS_BY_BU = {
    "amigro": {
        "skills": {
            "question": "¿Qué habilidades básicas tienes? Por ejemplo, carpintería, cocina, atención al cliente.",
            "next": None,
            "validation": lambda x: len(x.split()) > 1
        }
    },
    "huntu": {
        "skills": {
            "question": "¿Qué habilidades técnicas y blandas posees? Ejemplo: Python, liderazgo, trabajo en equipo.",
            "next": None,
            "validation": lambda x: len(x.split()) > 1
        }
    },
    "huntred": {
        "skills": {
            "question": "¿Qué habilidades de gerencia media tienes? Ejemplo: gestión de equipos, presupuestos, estrategia.",
            "next": None,
            "validation": lambda x: len(x.split()) > 1
        }
    },
    "huntred_executive": {
        "skills": {
            "question": "¿Qué habilidades de management y estrategia posees? Ejemplo: liderazgo ejecutivo, visión estratégica, innovación.",
            "next": None,
            "validation": lambda x: len(x.split()) > 1
        }
    }
}

def get_questions(business_unit: str) -> dict:
    """Combina preguntas comunes con las específicas de la unidad de negocio."""
    specific_questions = QUESTIONS_BY_BU.get(business_unit.lower(), {})
    return {**COMMON_QUESTIONS, **specific_questions}