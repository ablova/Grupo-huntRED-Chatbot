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
                    {'value': 1, 'label': 'Muy por debajo de lo esperado'},
                    {'value': 2, 'label': 'Por debajo de lo esperado'},
                    {'value': 3, 'label': 'Cumple con lo esperado'},
                    {'value': 4, 'label': 'Por encima de lo esperado'},
                    {'value': 5, 'label': 'Muy por encima de lo esperado'}
                ]
            },
            {
                'id': 'strengths',
                'text': '¿Cuáles son sus principales fortalezas?',
                'type': 'multiple_choice',
                'weight': 0.8,
                'options': [
                    'Liderazgo',
                    'Comunicación',
                    'Trabajo en equipo',
                    'Resolución de problemas',
                    'Pensamiento estratégico',
                    'Innovación',
                    'Gestión de proyectos',
                    'Relaciones interpersonales',
                    'Adaptabilidad',
                    'Orientación a resultados'
                ],
                'max_selections': 3
            },
            {
                'id': 'leadership',
                'text': '¿Cómo describirías su estilo de liderazgo?',
                'type': 'multiple_choice',
                'weight': 0.7,
                'options': [
                    'Directivo',
                    'Participativo',
                    'Delegativo',
                    'Transformacional',
                    'Situacional',
                    'Servicial'
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
                    {'value': 1, 'label': 'Principiante'},
                    {'value': 2, 'label': 'Básico'},
                    {'value': 3, 'label': 'Intermedio'},
                    {'value': 4, 'label': 'Avanzado'},
                    {'value': 5, 'label': 'Experto'}
                ]
            },
            {
                'id': 'recommendation',
                'text': '¿Recomendarías trabajar con esta persona?',
                'type': 'boolean',
                'weight': 1.0,
                'follow_up': {
                    'if_true': '¿Por qué la recomendarías?',
                    'if_false': '¿Qué aspectos debería mejorar?'
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
                'id': 'performance',
                'text': '¿Cómo calificarías su desempeño en ventas?',
                'type': 'rating',
                'scale': 5,
                'weight': 1.0,
                'options': [
                    {'value': 1, 'label': 'No cumple objetivos'},
                    {'value': 2, 'label': 'Cumple objetivos mínimos'},
                    {'value': 3, 'label': 'Cumple objetivos'},
                    {'value': 4, 'label': 'Supera objetivos'},
                    {'value': 5, 'label': 'Supera objetivos significativamente'}
                ]
            },
            {
                'id': 'customer_service',
                'text': '¿Cómo maneja las relaciones con clientes?',
                'type': 'multiple_choice',
                'weight': 0.9,
                'options': [
                    'Excelente comunicación',
                    'Empatía con clientes',
                    'Resolución de problemas',
                    'Manejo de objeciones',
                    'Fidelización',
                    'Negociación',
                    'Servicio post-venta'
                ],
                'max_selections': 3
            },
            {
                'id': 'achievements',
                'text': '¿Cuáles fueron sus principales logros?',
                'type': 'text',
                'weight': 0.8,
                'max_length': 500
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
                    {'value': 1, 'label': 'Necesita supervisión constante'},
                    {'value': 2, 'label': 'Requiere supervisión ocasional'},
                    {'value': 3, 'label': 'Trabaja de forma independiente'},
                    {'value': 4, 'label': 'Es un referente técnico'},
                    {'value': 5, 'label': 'Es un experto reconocido'}
                ]
            },
            {
                'id': 'skills',
                'text': '¿Cuáles son sus principales habilidades técnicas?',
                'type': 'multiple_choice',
                'weight': 0.9,
                'options': [
                    'Desarrollo Frontend',
                    'Desarrollo Backend',
                    'Bases de datos',
                    'DevOps',
                    'Cloud Computing',
                    'Seguridad',
                    'Testing',
                    'Arquitectura de software',
                    'Gestión de proyectos',
                    'Metodologías ágiles'
                ],
                'max_selections': 4
            },
            {
                'id': 'teamwork',
                'text': '¿Cómo trabaja en equipo?',
                'type': 'multiple_choice',
                'weight': 0.7,
                'options': [
                    'Comunicación efectiva',
                    'Colaboración',
                    'Mentoría',
                    'Resolución de conflictos',
                    'Comparte conocimiento',
                    'Liderazgo técnico'
                ],
                'max_selections': 3
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
                    {'value': 1, 'label': 'No cumple expectativas'},
                    {'value': 2, 'label': 'Cumple expectativas básicas'},
                    {'value': 3, 'label': 'Cumple expectativas'},
                    {'value': 4, 'label': 'Supera expectativas'},
                    {'value': 5, 'label': 'Supera expectativas significativamente'}
                ]
            },
            {
                'id': 'communication',
                'text': '¿Cómo evalúas sus habilidades de comunicación?',
                'type': 'multiple_choice',
                'weight': 0.9,
                'options': [
                    'Claridad en mensajes',
                    'Escucha activa',
                    'Empatía',
                    'Asertividad',
                    'Manejo de situaciones difíciles',
                    'Comunicación no verbal'
                ],
                'max_selections': 3
            },
            {
                'id': 'empathy',
                'text': '¿Cómo maneja situaciones difíciles?',
                'type': 'multiple_choice',
                'weight': 0.8,
                'options': [
                    'Mantiene la calma',
                    'Busca soluciones',
                    'Empatiza con el cliente',
                    'Sigue protocolos',
                    'Escala cuando es necesario',
                    'Aprende de la experiencia'
                ],
                'max_selections': 3
            }
        ],
        'min_references': 3,
        'max_references': 5,
        'response_days': 10,
        'reminder_days': [2, 5, 8]
    }
}

def get_reference_config(business_unit: str) -> dict:
    """
    Obtiene la configuración de referencias para una unidad de negocio.
    
    Args:
        business_unit: str - Código de la unidad de negocio
        
    Returns:
        dict - Configuración de referencias
    """
    return REFERENCE_CONFIGS.get(business_unit.lower(), REFERENCE_CONFIGS['huntred']) 