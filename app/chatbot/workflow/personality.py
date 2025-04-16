# /home/pablollh/app/chatbot/workflow/personality.py
import random
from django.core.cache import cache
# Estructura de preguntas por prueba y dominio
TEST_QUESTIONS = {
    'huntBigFive': {
        'general': {
            'apertura': [
                {'text': '¿Te consideras una persona creativa e imaginativa?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']},
                {'text': '¿Disfrutas probando cosas nuevas y diferentes?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']},
            ],
            'conciencia': [
                {'text': '¿Eres organizado y planeas tus actividades con anticipación?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']},
                {'text': '¿Cumples siempre con tus responsabilidades y plazos?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']},
            ],
            'extraversion': [
                {'text': '¿Te gusta socializar y estar rodeado de mucha gente?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']},
                {'text': '¿Eres enérgico y hablas con facilidad en grupos?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']},
            ],
            'amabilidad': [
                {'text': '¿Te preocupas por los sentimientos de los demás?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']},
                {'text': '¿Eres amable y considerado con las personas?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']},
            ],
            'neuroticismo': [
                {'text': '¿Te estresas o preocupas con facilidad?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']},
                {'text': '¿Tus emociones cambian frecuentemente?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']},
            ],
        },
        'consumer': {
            'apertura': [{'text': '¿Disfrutas creando estrategias para atraer clientes?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'conciencia': [{'text': '¿Planificas tus metas de ventas con detalle?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'extraversion': [{'text': '¿Disfrutas interactuar con clientes en un entorno minorista?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'amabilidad': [{'text': '¿Te gusta ayudar a los clientes a encontrar lo que necesitan?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'neuroticismo': [{'text': '¿Te afecta mucho no cumplir una venta?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
        },
        'pharma': {
            'apertura': [{'text': '¿Te interesa aprender sobre nuevos medicamentos?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'conciencia': [{'text': '¿Te preparas minuciosamente para reuniones con médicos?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'extraversion': [{'text': '¿Disfrutas negociar con profesionales de la salud?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'amabilidad': [{'text': '¿Buscas entender las necesidades de los médicos?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'neuroticismo': [{'text': '¿Te preocupa mucho no alcanzar tus metas técnicas?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
        },
        'service': {
            'apertura': [{'text': '¿Te gusta idear nuevas formas de atender clientes?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'conciencia': [{'text': '¿Cumples siempre con los tiempos de respuesta al cliente?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'extraversion': [{'text': '¿Disfrutas resolver dudas en persona o por teléfono?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'amabilidad': [{'text': '¿Manejas bien las quejas de los clientes?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'neuroticismo': [{'text': '¿Te estresas ante clientes difíciles?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
        },
    },
    'DISC': {
        'general': [
            {'text': 'Selecciona lo que más te describe: a) Decisivo, b) Amigable, c) Paciente, d) Detallista', 'options': ['a', 'b', 'c', 'd']},
            {'text': '¿Qué prefieres? a) Liderar, b) Socializar, c) Colaborar, d) Analizar', 'options': ['a', 'b', 'c', 'd']},
        ],
        'consumer': [
            {'text': 'En ventas, ¿qué destacas? a) Cerrar rápido, b) Conectar con el cliente, c) Mantener calma, d) Revisar detalles', 'options': ['a', 'b', 'c', 'd']},
        ],
        'pharma': [
            {'text': 'Con médicos, ¿qué priorizas? a) Ser directo, b) Persuadir, c) Escuchar, d) Datos precisos', 'options': ['a', 'b', 'c', 'd']},
        ],
        'service': [
            {'text': 'Con clientes, ¿qué haces? a) Resolver rápido, b) Ser cálido, c) Paciencia, d) Detalles correctos', 'options': ['a', 'b', 'c', 'd']},
        ],
    },
    '16PF': {
        'general': {
            'calidez': [{'text': '¿Disfrutas hacer sentir bienvenidas a las personas?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'estabilidad': [{'text': '¿Mantienes la calma bajo presión?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            # Simplificado: solo 2 factores por ahora, se pueden añadir más
        },
        'consumer': {
            'calidez': [{'text': '¿Te gusta hacer que los clientes se sientan cómodos?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'estabilidad': [{'text': '¿Controlas tus emociones si un cliente no compra?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
        },
        'pharma': {
            'calidez': [{'text': '¿Buscas que los médicos confíen en ti?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'estabilidad': [{'text': '¿Te mantienes sereno si un médico cuestiona tus datos?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
        },
        'service': {
            'calidez': [{'text': '¿Tratas a los clientes con empatía?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
            'estabilidad': [{'text': '¿Sigues tranquilo con clientes exigentes?', 'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']}],
        },
    },
    'NEO': {
        'general': {},  # Reutiliza huntBigFive['general'] por solapamiento
        'consumer': {},  # Reutiliza huntBigFive['consumer']
        'pharma': {},    # Reutiliza huntBigFive['pharma']
        'service': {},   # Reutiliza huntBigFive['service']
    },
    'MBTI': {
        'general': [
            {'text': '¿Prefieres pasar tiempo con muchas personas o estar solo/a?', 'options': ['1 - Muchas personas (E)', '2 - Neutral', '3 - Solo/a (I)']},
            {'text': '¿Te enfocas más en los detalles concretos o en las posibilidades futuras?', 'options': ['1 - Detalles (S)', '2 - Neutral', '3 - Posibilidades (N)']},
            {'text': '¿Tomas decisiones basándote en lógica o en emociones?', 'options': ['1 - Lógica (T)', '2 - Neutral', '3 - Emociones (F)']},
            {'text': '¿Prefieres tener un plan estructurado o mantener tus opciones abiertas?', 'options': ['1 - Plan (J)', '2 - Neutral', '3 - Opciones abiertas (P)']},
        ],
    },
    'TIPI': {
        'general': {
            'extraversion': [
                {'text': 'Me veo como: Extrovertido, entusiasta.', 'reverse': False},
                {'text': 'Me veo como: Reservado, tranquilo.', 'reverse': True},
            ],
            'agreeableness': [
                {'text': 'Me veo como: Simpático, cálido.', 'reverse': False},
                {'text': 'Me veo como: Crítico, pendenciero.', 'reverse': True},
            ],
            'conscientiousness': [
                {'text': 'Me veo como: Confiable, autodisciplinado.', 'reverse': False},
                {'text': 'Me veo como: Desorganizado, descuidado.', 'reverse': True},
            ],
            'neuroticism': [
                {'text': 'Me veo como: Ansioso, fácilmente molesto.', 'reverse': False},
                {'text': 'Me veo como: Calmo, emocionalmente estable.', 'reverse': True},
            ],
            'openness': [
                {'text': 'Me veo como: Abierto a nuevas experiencias, complejo.', 'reverse': False},
                {'text': 'Me veo como: Convencional, poco creativo.', 'reverse': True},
            ],
        },
    },
}

def get_questions_personality(test_type, domain='general'):
    """Devuelve las preguntas según el tipo de prueba y dominio."""
    cache_key = f"questions_{test_type}_{domain}"
    questions = cache.get(cache_key)
    if not questions:
        # Suponiendo que TEST_QUESTIONS es un diccionario con las preguntas
        questions = TEST_QUESTIONS.get(test_type, {}).get(domain, {})
        cache.set(cache_key, questions, timeout=3600)  # 1 hora de caché
    return questions

def get_random_tipi_questions(domain='general'):
    """Selecciona preguntas aleatorias para TIPI."""
    selected_questions = {}
    for trait in TEST_QUESTIONS['TIPI']['general']:
        direct = [q for q in TEST_QUESTIONS['TIPI']['general'][trait] if not q['reverse']]
        reverse = [q for q in TEST_QUESTIONS['TIPI']['general'][trait] if q['reverse']]
        selected_questions[trait] = [random.choice(direct), random.choice(reverse)]
    return selected_questions