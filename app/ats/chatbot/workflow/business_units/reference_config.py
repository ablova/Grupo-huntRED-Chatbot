# /home/pablo/app/ats/chatbot/workflow/business_units/reference_config.py
"""
Configuración de preguntas y parámetros de referencias por unidad de negocio.
"""

REFERENCE_CONFIGS = {
    'huntred': {
        'questions': [
            {
                'id': 'performance',
                'text': '¿Cómo calificarías el desempeño general?',
                'type': 'rating',
                'scale': 5,
                'weight': 1.0,
                'options': [
                    {'value': 1, 'label': '⭐ Muy por debajo de lo esperado'},
                    {'value': 2, 'label': '⭐⭐ Por debajo de lo esperado'},
                    {'value': 3, 'label': '⭐⭐⭐ Cumple con lo esperado'},
                    {'value': 4, 'label': '⭐⭐⭐⭐ Por encima de lo esperado'},
                    {'value': 5, 'label': '⭐⭐⭐⭐⭐ Muy por encima de lo esperado'}
                ]
            },
            {
                'id': 'grit',
                'text': '¿Cómo evaluarías su GRIT (talento + actitud + determinación)?',
                'type': 'multiple_choice',
                'weight': 0.9,
                'options': [
                    '💪 Perseverancia excepcional',
                    '🛡️ Resiliencia ante desafíos',
                    '❤️ Pasión por el trabajo',
                    '🎯 Determinación para lograr objetivos',
                    '📈 Capacidad de superación',
                    '🤝 Compromiso a largo plazo',
                    '🌊 Manejo de la adversidad',
                    '⏳ Constancia en el esfuerzo'
                ],
                'max_selections': 4
            },
            {
                'id': 'strengths',
                'text': '¿Cuáles son sus principales fortalezas?',
                'type': 'multiple_choice',
                'weight': 0.8,
                'options': [
                    '👑 Liderazgo',
                    '🗣️ Comunicación',
                    '👥 Trabajo en equipo',
                    '🔧 Resolución de problemas',
                    '🎯 Pensamiento estratégico',
                    '💡 Innovación',
                    '📊 Gestión de proyectos',
                    '🤝 Relaciones interpersonales',
                    '🔄 Adaptabilidad',
                    '🎯 Orientación a resultados'
                ],
                'max_selections': 3
            },
            {
                'id': 'leadership',
                'text': '¿Cómo describirías su estilo de liderazgo?',
                'type': 'multiple_choice',
                'weight': 0.7,
                'options': [
                    '👑 Directivo',
                    '🤝 Participativo',
                    '🎯 Delegativo',
                    '✨ Transformacional',
                    '🔄 Situacional',
                    '💝 Servicial'
                ],
                'max_selections': 2
            },
            {
                'id': 'technical',
                'text': '¿Cómo evaluarías sus habilidades técnicas?',
                'type': 'rating',
                'scale': 5,
                'weight': 0.9,
                'options': [
                    {'value': 1, 'label': '🌱 Principiante'},
                    {'value': 2, 'label': '🌿 Básico'},
                    {'value': 3, 'label': '🌳 Intermedio'},
                    {'value': 4, 'label': '🌲 Avanzado'},
                    {'value': 5, 'label': '🎯 Experto'}
                ]
            },
            {
                'id': 'ethics',
                'text': '¿Cómo evaluarías su ética profesional y valores?',
                'type': 'multiple_choice',
                'weight': 0.9,
                'options': [
                    '🤝 Integridad y honestidad',
                    '🔒 Confidencialidad',
                    '🌍 Responsabilidad social',
                    '🌈 Respeto a la diversidad',
                    '✨ Compromiso con la excelencia',
                    '⚖️ Ética en la toma de decisiones'
                ],
                'max_selections': 3
            },
            {
                'id': 'open_feedback',
                'text': '✍️ Comparte cualquier aspecto adicional que consideres relevante sobre esta persona:',
                'type': 'text',
                'weight': 0.8,
                'max_length': 1000
            },
            {
                'id': 'recommendation',
                'text': '¿Recomendarías trabajar con esta persona?',
                'type': 'boolean',
                'weight': 1.0,
                'follow_up': {
                    'if_true': '👍 ¿Por qué la recomendarías?',
                    'if_false': '👎 ¿Qué aspectos debería mejorar?'
                }
            }
        ],
        'min_references': 4,
        'max_references': 6,
        'response_days': 14,
        'reminder_days': [3, 7, 10]
    },
    
    'amigro': {
        'questions': [
            {
                'id': 'attitude',
                'text': '¿Cómo calificarías su actitud y disposición al trabajo?',
                'type': 'rating',
                'scale': 5,
                'weight': 1.0,
                'options': [
                    {'value': 1, 'label': '⭐ Muy por debajo de lo esperado'},
                    {'value': 2, 'label': '⭐⭐ Por debajo de lo esperado'},
                    {'value': 3, 'label': '⭐⭐⭐ Cumple con lo esperado'},
                    {'value': 4, 'label': '⭐⭐⭐⭐ Por encima de lo esperado'},
                    {'value': 5, 'label': '⭐⭐⭐⭐⭐ Muy por encima de lo esperado'}
                ]
            },
            {
                'id': 'grit',
                'text': '¿Cómo evaluarías su GRIT (talento + actitud + determinación)?',
                'type': 'multiple_choice',
                'weight': 0.9,
                'options': [
                    '💪 Perseverancia excepcional',
                    '🛡️ Resiliencia ante desafíos',
                    '❤️ Pasión por el trabajo',
                    '🎯 Determinación para lograr objetivos',
                    '📈 Capacidad de superación',
                    '🤝 Compromiso a largo plazo',
                    '🌊 Manejo de la adversidad',
                    '⏳ Constancia en el esfuerzo'
                ],
                'max_selections': 4
            },
            {
                'id': 'soft_skills',
                'text': '¿Cuáles son sus principales cualidades personales?',
                'type': 'multiple_choice',
                'weight': 0.9,
                'options': [
                    '✨ Entusiasmo y energía',
                    '✅ Responsabilidad y compromiso',
                    '⏳ Constancia y perseverancia',
                    '🔄 Adaptabilidad al cambio',
                    '👥 Trabajo en equipo',
                    '💡 Iniciativa propia',
                    '🛡️ Resiliencia',
                    '❤️ Empatía',
                    '🗣️ Comunicación efectiva',
                    '🎯 Orientación al servicio'
                ],
                'max_selections': 4
            },
            {
                'id': 'reliability',
                'text': '¿Cómo evaluarías su confiabilidad y cumplimiento?',
                'type': 'multiple_choice',
                'weight': 0.8,
                'options': [
                    '✅ Siempre cumple con sus compromisos',
                    '😊 Mantiene una actitud positiva',
                    '⏰ Es puntual y organizado',
                    '🎯 Maneja bien la presión',
                    '💡 Es proactivo en la resolución de problemas',
                    '🤝 Mantiene buenas relaciones con el equipo'
                ],
                'max_selections': 3
            },
            {
                'id': 'growth',
                'text': '📈 ¿Observaste crecimiento y desarrollo durante su tiempo en la empresa?',
                'type': 'text',
                'weight': 0.7,
                'max_length': 500
            },
            {
                'id': 'open_feedback',
                'text': '✍️ Comparte cualquier aspecto adicional que consideres relevante sobre esta persona:',
                'type': 'text',
                'weight': 0.8,
                'max_length': 1000
            },
            {
                'id': 'recommendation',
                'text': '¿Recomendarías trabajar con esta persona?',
                'type': 'boolean',
                'weight': 1.0,
                'follow_up': {
                    'if_true': '👍 ¿Por qué la recomendarías?',
                    'if_false': '👎 ¿Qué aspectos debería mejorar?'
                }
            }
        ],
        'min_references': 3,
        'max_references': 5,
        'response_days': 10,
        'reminder_days': [2, 5, 8]
    },
    
    'huntu': {
        'questions': [
            {
                'id': 'performance',
                'text': '¿Cómo calificarías su desempeño técnico?',
                'type': 'rating',
                'scale': 5,
                'weight': 1.0,
                'options': [
                    {'value': 1, 'label': '👶 Necesita supervisión constante'},
                    {'value': 2, 'label': '👨‍💻 Requiere supervisión ocasional'},
                    {'value': 3, 'label': '💻 Trabaja de forma independiente'},
                    {'value': 4, 'label': '👨‍🏫 Es un referente técnico'},
                    {'value': 5, 'label': '👨‍🔬 Es un experto reconocido'}
                ]
            },
            {
                'id': 'grit',
                'text': '¿Cómo evaluarías su GRIT (talento + actitud + determinación)?',
                'type': 'multiple_choice',
                'weight': 0.9,
                'options': [
                    '💪 Perseverancia excepcional',
                    '🛡️ Resiliencia ante desafíos',
                    '❤️ Pasión por el trabajo',
                    '🎯 Determinación para lograr objetivos',
                    '📈 Capacidad de superación',
                    '🤝 Compromiso a largo plazo',
                    '🌊 Manejo de la adversidad',
                    '⏳ Constancia en el esfuerzo'
                ],
                'max_selections': 4
            },
            {
                'id': 'skills',
                'text': '¿Cuáles son sus principales habilidades técnicas?',
                'type': 'multiple_choice',
                'weight': 0.9,
                'options': [
                    '🎨 Desarrollo Frontend',
                    '⚙️ Desarrollo Backend',
                    '🗄️ Bases de datos',
                    '🔄 DevOps',
                    '☁️ Cloud Computing',
                    '🔒 Seguridad',
                    '🧪 Testing',
                    '🏗️ Arquitectura de software',
                    '📊 Gestión de proyectos',
                    '🔄 Metodologías ágiles'
                ],
                'max_selections': 4
            },
            {
                'id': 'teamwork',
                'text': '¿Cómo trabaja en equipo?',
                'type': 'multiple_choice',
                'weight': 0.7,
                'options': [
                    '🗣️ Comunicación efectiva',
                    '🤝 Colaboración',
                    '👨‍🏫 Mentoría',
                    '⚖️ Resolución de conflictos',
                    '📚 Comparte conocimiento',
                    '👑 Liderazgo técnico'
                ],
                'max_selections': 3
            },
            {
                'id': 'innovation',
                'text': '¿Cómo evaluarías su capacidad de innovación y aprendizaje?',
                'type': 'multiple_choice',
                'weight': 0.8,
                'options': [
                    '🔍 Busca constantemente nuevas tecnologías',
                    '💡 Propone mejoras y soluciones innovadoras',
                    '📚 Aprende rápidamente nuevas tecnologías',
                    '🤝 Comparte conocimiento con el equipo',
                    '📈 Se mantiene actualizado en su campo',
                    '✨ Aplica mejores prácticas'
                ],
                'max_selections': 3
            },
            {
                'id': 'open_feedback',
                'text': '✍️ Comparte cualquier aspecto adicional que consideres relevante sobre esta persona:',
                'type': 'text',
                'weight': 0.8,
                'max_length': 1000
            },
            {
                'id': 'recommendation',
                'text': '¿Recomendarías trabajar con esta persona?',
                'type': 'boolean',
                'weight': 1.0,
                'follow_up': {
                    'if_true': '👍 ¿Por qué la recomendarías?',
                    'if_false': '👎 ¿Qué aspectos debería mejorar?'
                }
            }
        ],
        'min_references': 4,
        'max_references': 6,
        'response_days': 12,
        'reminder_days': [3, 6, 9]
    },
    
    'sexsi': {
        'questions': [
            {
                'id': 'performance',
                'text': '¿Cómo calificarías su desempeño en atención al cliente?',
                'type': 'rating',
                'scale': 5,
                'weight': 1.0,
                'options': [
                    {'value': 1, 'label': '⭐ No cumple expectativas'},
                    {'value': 2, 'label': '⭐⭐ Cumple expectativas básicas'},
                    {'value': 3, 'label': '⭐⭐⭐ Cumple expectativas'},
                    {'value': 4, 'label': '⭐⭐⭐⭐ Supera expectativas'},
                    {'value': 5, 'label': '⭐⭐⭐⭐⭐ Supera expectativas significativamente'}
                ]
            },
            {
                'id': 'grit',
                'text': '¿Cómo evaluarías su GRIT (talento + actitud + determinación)?',
                'type': 'multiple_choice',
                'weight': 0.9,
                'options': [
                    '💪 Perseverancia excepcional',
                    '🛡️ Resiliencia ante desafíos',
                    '❤️ Pasión por el trabajo',
                    '🎯 Determinación para lograr objetivos',
                    '📈 Capacidad de superación',
                    '🤝 Compromiso a largo plazo',
                    '🌊 Manejo de la adversidad',
                    '⏳ Constancia en el esfuerzo'
                ],
                'max_selections': 4
            },
            {
                'id': 'customer_service',
                'text': '¿Cuáles son sus principales habilidades en atención al cliente?',
                'type': 'multiple_choice',
                'weight': 0.9,
                'options': [
                    '❤️ Empatía y comprensión',
                    '🗣️ Comunicación clara y efectiva',
                    '⚡ Manejo de situaciones difíciles',
                    '🔧 Resolución de problemas',
                    '⏳ Paciencia y tolerancia',
                    '🔄 Adaptabilidad a diferentes clientes',
                    '😌 Manejo de estrés',
                    '🎯 Trabajo bajo presión'
                ],
                'max_selections': 4
            },
            {
                'id': 'situations',
                'text': '¿Cómo maneja situaciones difíciles o clientes insatisfechos?',
                'type': 'multiple_choice',
                'weight': 0.8,
                'options': [
                    '😌 Mantiene la calma',
                    '👂 Escucha activamente',
                    '💡 Busca soluciones efectivas',
                    '❤️ Maneja las emociones del cliente',
                    '📋 Sigue protocolos establecidos',
                    '📚 Aprende de cada situación'
                ],
                'max_selections': 3
            },
            {
                'id': 'teamwork',
                'text': '¿Cómo trabaja en equipo?',
                'type': 'multiple_choice',
                'weight': 0.7,
                'options': [
                    '🤝 Colaboración efectiva',
                    '🗣️ Comunicación clara',
                    '💪 Apoyo a compañeros',
                    '✨ Comparte mejores prácticas',
                    '⚖️ Manejo de conflictos',
                    '😊 Contribuye al ambiente laboral'
                ],
                'max_selections': 3
            },
            {
                'id': 'open_feedback',
                'text': '✍️ Comparte cualquier aspecto adicional que consideres relevante sobre esta persona:',
                'type': 'text',
                'weight': 0.8,
                'max_length': 1000
            },
            {
                'id': 'recommendation',
                'text': '¿Recomendarías trabajar con esta persona?',
                'type': 'boolean',
                'weight': 1.0,
                'follow_up': {
                    'if_true': '👍 ¿Por qué la recomendarías?',
                    'if_false': '👎 ¿Qué aspectos debería mejorar?'
                }
            }
        ],
        'min_references': 3,
        'max_references': 5,
        'response_days': 10,
        'reminder_days': [2, 5, 8]
    }
}

def get_reference_config(business_unit: str, skills: list = None, required_skills: list = None) -> dict:
    """
    Obtiene la configuración de referencias para una unidad de negocio.
    Si se pasan required_skills, solo pregunta por esos skills y pide nivel de expertise visual (3 niveles).
    """
    config = REFERENCE_CONFIGS.get(business_unit.lower(), REFERENCE_CONFIGS['huntred']).copy()
    dynamic_questions = []
    # Usar solo los skills obligatorios y limitar a 3-5 más relevantes
    if required_skills:
        top_skills = required_skills[:5]
        for skill in top_skills:
            dynamic_questions.append({
                'id': f'skill_{skill.lower().replace(" ", "_")}',
                'text': f'¿Qué nivel de expertise tiene el candidato en "{skill}"?',
                'type': 'quick_reply',
                'options': [
                    {'title': 'X', 'value': 0, 'description': 'No lo domina'},
                    {'title': '👍', 'value': 1, 'description': 'Nivel básico'},
                    {'title': '👍👍', 'value': 2, 'description': 'Nivel avanzado'}
                ],
                'weight': 1.0
            })
    elif skills:
        # Si no hay required_skills, usar skills generales
        top_skills = skills[:5]
        for skill in top_skills:
            dynamic_questions.append({
                'id': f'skill_{skill.lower().replace(" ", "_")}',
                'text': f'¿Qué nivel de expertise tiene el candidato en "{skill}"?',
                'type': 'quick_reply',
                'options': [
                    {'title': 'X', 'value': 0, 'description': 'No lo domina'},
                    {'title': '👍', 'value': 1, 'description': 'Nivel básico'},
                    {'title': '👍👍', 'value': 2, 'description': 'Nivel avanzado'}
                ],
                'weight': 1.0
            })
    if dynamic_questions:
        config['questions'] = config['questions'] + dynamic_questions
    # Comentario: aquí se pueden agregar más lógicas dinámicas por seniority, tipo de vacante, etc.
    return config 