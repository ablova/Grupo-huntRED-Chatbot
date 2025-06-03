# /home/pablo/app/com/chatbot/workflow/profile_questions.py
import re
from datetime import datetime

# Preguntas comunes a todas las unidades de negocio
COMMON_QUESTIONS = {
    "nombre": {
        "question": "¿Cuál es tu nombre?",
        "next": "apellido_paterno",
        "validation": lambda x: len(x.strip()) > 1 and all(c.isalpha() or c.isspace() for c in x.strip()),
        "field": "nombre"
    },
    "apellido_paterno": {
        "question": "Gracias, {nombre}. ¿Cuál es tu apellido paterno?",
        "next": "apellido_materno",
        "validation": lambda x: len(x.strip()) > 1 and all(c.isalpha() or c.isspace() for c in x.strip()),
        "field": "apellido_paterno"
    },
    "apellido_materno": {
        "question": "¿Cuál es tu apellido materno? (Omitir si no aplica)",
        "next": "email",
        "validation": lambda x: x.strip() == "" or (len(x.strip()) > 1 and all(c.isalpha() or c.isspace() for c in x.strip())),
        "field": "apellido_materno"
    },
    "email": {
        "question": "¿Cuál es tu correo electrónico?",
        "next": "phone",
        "validation": lambda x: bool(re.match(r"[^@]+@[^@]+\.[^@]+", x)),
        "field": "email"
    },
    "phone": {
        "question": "¿Cuál es tu número de teléfono? (Ejemplo: +525534567890)",
        "next": "nacionalidad",
        "validation": lambda x: bool(re.match(r"^\+\d{10,15}$", x)),
        "field": "phone"
    },
    "nacionalidad": {
        "question": "¿Cuál es tu nacionalidad? (Ejemplo: Mexicana, Estadounidense)",
        "next": "fecha_nacimiento",
        "validation": lambda x: len(x.strip()) > 2 and all(c.isalpha() or c.isspace() for c in x.strip()),
        "field": "nacionalidad"
    },
    "fecha_nacimiento": {
        "question": "¿Cuál es tu fecha de nacimiento? (Formato: DD/MM/YYYY)",
        "next": "sexo",
        "validation": lambda x: bool(re.match(r"^\d{2}/\d{2}/\d{4}$", x)) and datetime.strptime(x, "%d/%m/%Y").year <= datetime.now().year - 16,
        "field": "fecha_nacimiento",
        "transform": lambda x: datetime.strptime(x, "%d/%m/%Y").date()
    },
    "sexo": {
        "question": "¿Cuál es tu sexo? Responde: Masculino, Femenino, Otro",
        "next": "job_search_status",
        "validation": lambda x: x.lower() in ["masculino", "femenino", "otro"],
        "field": "sexo",
        "transform": lambda x: {"masculino": "M", "femenino": "F", "otro": "O"}.get(x.lower())
    },
    "job_search_status": {
        "question": "¿Cuál es tu estado de búsqueda de empleo? Responde: Activa, Pasiva, Local, Remota, No en búsqueda",
        "next": "experience_years",
        "validation": lambda x: x.lower() in ["activa", "pasiva", "local", "remota", "no en búsqueda"],
        "field": "job_search_status",
        "transform": lambda x: {"no en búsqueda": "no_busca"}.get(x.lower(), x.lower())
    },
    "experience_years": {
        "question": "¿Cuántos años de experiencia laboral tienes? (Ejemplo: 5)",
        "next": "desired_job_types",
        "validation": lambda x: x.isdigit() and 0 <= int(x) <= 50,
        "field": "experience_years",
        "transform": lambda x: int(x)
    },
    "desired_job_types": {
        "question": "¿Qué tipos de trabajo prefieres? (Ejemplo: Tiempo completo, Medio tiempo, Freelance)",
        "next": "work_experience",
        "validation": lambda x: len(x.strip()) > 3,
        "field": "desired_job_types"
    },
    "work_experience": {
        "question": "¿Cuál ha sido tu experiencia laboral más reciente? Describe tu rol y responsabilidades.",
        "next": "skills",
        "validation": lambda x: len(x.strip()) > 10,
        "field": "metadata",
        "subfield": "experience"
    }
}

# Preguntas específicas por unidad de negocio
QUESTIONS_BY_BU = {
    "amigro": {
        "skills": {
            "question": "¿Qué habilidades básicas tienes? Ejemplo: Carpintería, Cocina, Atención al cliente",
            "next": "migratory_status",
            "validation": lambda x: len(x.strip().split(",")) > 1,
            "field": "skills"
        },
        "migratory_status": {
            "question": "¿Cuál es tu estatus migratorio en México? Responde: Residente permanente, Residente temporal, Refugiado, Sin estatus",
            "next": "education",
            "validation": lambda x: x.lower() in ["residente permanente", "residente temporal", "refugiado", "sin estatus"],
            "field": "metadata",
            "subfield": "migratory_status"
        },
        "education": {
            "question": "¿Cuál es tu nivel educativo? Ejemplo: Secundaria, Bachillerato, Licenciatura",
            "next": None,
            "validation": lambda x: len(x.strip()) > 3,
            "field": "metadata",
            "subfield": "education"
        }
    },
    "huntu": {
        "skills": {
            "question": "¿Qué habilidades técnicas y blandas posees? Ejemplo: Python, Liderazgo, Trabajo en equipo",
            "next": "education",
            "validation": lambda x: len(x.strip().split(",")) > 1,
            "field": "skills"
        },
        "education": {
            "question": "¿Cuál es tu nivel educativo? Ejemplo: Licenciatura en curso, Licenciatura concluida",
            "next": "certifications",
            "validation": lambda x: len(x.strip()) > 3,
            "field": "metadata",
            "subfield": "education"
        },
        "certifications": {
            "question": "¿Tienes certificaciones relevantes? Ejemplo: TOEFL, AWS Certified (Omitir si no aplica)",
            "next": None,
            "validation": lambda x: x.strip() == "" or len(x.strip()) > 3,
            "field": "metadata",
            "subfield": "certifications"
        }
    },
    "huntred": {
        "skills": {
            "question": "¿Qué habilidades de gerencia media tienes? Ejemplo: Gestión de equipos, Presupuestos, Estrategia",
            "next": "education",
            "validation": lambda x: len(x.strip().split(",")) > 1,
            "field": "skills"
        },
        "education": {
            "question": "¿Cuál es tu nivel educativo? Ejemplo: Licenciatura, Maestría",
            "next": "certifications",
            "validation": lambda x: len(x.strip()) > 3,
            "field": "metadata",
            "subfield": "education"
        },
        "certifications": {
            "question": "¿Tienes certificaciones relevantes? Ejemplo: PMP, Lean Six Sigma (Omitir si no aplica)",
            "next": None,
            "validation": lambda x: x.strip() == "" or len(x.strip()) > 3,
            "field": "metadata",
            "subfield": "certifications"
        }
    },
    "huntred_executive": {
        "skills": {
            "question": "¿Qué habilidades de management y estrategia posees? Ejemplo: Liderazgo ejecutivo, Visión estratégica, Innovación",
            "next": "education",
            "validation": lambda x: len(x.strip().split(",")) > 1,
            "field": "skills"
        },
        "education": {
            "question": "¿Cuál es tu nivel educativo? Ejemplo: Maestría, Doctorado",
            "next": "certifications",
            "validation": lambda x: len(x.strip()) > 3,
            "field": "metadata",
            "subfield": "education"
        },
        "certifications": {
            "question": "¿Tienes certificaciones relevantes? Ejemplo: CFA, Executive MBA (Omitir si no aplica)",
            "next": None,
            "validation": lambda x: x.strip() == "" or len(x.strip()) > 3,
            "field": "metadata",
            "subfield": "certifications"
        }
    }
}

def get_questions(business_unit: str) -> dict:
    """Combina preguntas comunes con las específicas de la unidad de negocio."""
    specific_questions = QUESTIONS_BY_BU.get(business_unit.lower(), {})
    return {**COMMON_QUESTIONS, **specific_questions}