# /home/pablo/app/com/chatbot/workflow/assessments/personality/personality_workflow.py
import random
import logging
from django.core.cache import cache
from typing import Dict, Any, Optional, List

# Importar el analizador centralizado
from app.ml.analyzers import PersonalityAnalyzer

logger = logging.getLogger(__name__)

class PersonalityAssessment:
    """Clase para manejar la evaluación de personalidad."""
    
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

    def get_questions(self, test_type, domain='general', business_unit=None):
        questions = self.TEST_QUESTIONS.get(test_type, {}).get(domain, [])
        if business_unit and business_unit in self.TEST_QUESTIONS.get(test_type, {}):
            return self.TEST_QUESTIONS[test_type][business_unit]
        return questions

    def get_random_tipi_questions(self, domain='general', business_unit=None):
        questions = self.TEST_QUESTIONS.get('TIPI', {}).get(domain, [])
        if business_unit and business_unit in self.TEST_QUESTIONS.get('TIPI', {}):
            questions = self.TEST_QUESTIONS['TIPI'][business_unit]
        return random.sample(questions, min(10, len(questions)))

    def analyze_responses(self, responses: dict, business_unit: str = None) -> dict:
        """Analiza las respuestas del test de personalidad.
        
        Args:
            responses: Diccionario con las respuestas del usuario
            business_unit: Unidad de negocio para contextualizar el análisis
            
        Returns:
            Dict con resultados del análisis de personalidad
        """
        # Primero intentamos usar el analizador centralizado si está disponible
        try:
            # Preparar datos para el analizador centralizado
            analysis_data = {
                'assessment_type': 'personality',
                'responses': responses,
                'test_type': responses.get('test_type', 'huntBigFive')
            }
            
            # Instanciar y usar el analizador centralizado
            analyzer = PersonalityAnalyzer()
            result = analyzer.analyze(analysis_data, business_unit)
            
            # Si el análisis centralizado fue exitoso, lo devolvemos
            if result and not result.get('status') == 'error':
                logger.info(f"Análisis de personalidad realizado con analizador centralizado")
                return result
                
            # Si hay un error, caemos al método tradicional
            logger.warning(f"Fallback a análisis tradicional: {result.get('message', 'Error desconocido')}")
            
        except Exception as e:
            logger.error(f"Error usando analizador centralizado: {str(e)}. Fallback a análisis tradicional.")
        
        # Método tradicional como fallback
        test_type = responses.get('test_type', 'huntBigFive')
        
        if test_type == 'huntBigFive':
            return self._analyze_big_five(responses, business_unit)
        elif test_type == 'DISC':
            return self._analyze_disc(responses, business_unit)
        elif test_type == '16PF':
            return self._analyze_16pf(responses, business_unit)
        elif test_type == 'MBTI':
            return self._analyze_mbti(responses)
        elif test_type == 'TIPI':
            return self._analyze_tipi(responses)
        else:
            # Fallback al modelo Big Five por defecto
            return self._analyze_big_five(responses, business_unit)

    def _analyze_big_five(self, responses: dict, business_unit: str = None) -> dict:
        scores = {
            'apertura': 0,
            'conciencia': 0,
            'extraversion': 0,
            'amabilidad': 0,
            'neuroticismo': 0
        }
        for domain, response in responses.items():
            scores[domain] = sum(response) / len(response)
        if business_unit:
            self._add_business_unit_interpretation(scores, business_unit)
        return scores

    def _analyze_disc(self, responses: dict, business_unit: str = None) -> dict:
        scores = {
            'dominante': 0,
            'influencia': 0,
            'estabilidad': 0,
            'conformidad': 0
        }
        for option, count in responses.items():
            if option == 'a':
                scores['dominante'] += count
            elif option == 'b':
                scores['influencia'] += count
            elif option == 'c':
                scores['estabilidad'] += count
            elif option == 'd':
                scores['conformidad'] += count
        return scores

    def _analyze_16pf(self, responses: dict, business_unit: str = None) -> dict:
        scores = {
            'calidez': 0,
            'estabilidad': 0
        }
        for factor, response in responses.items():
            scores[factor] = sum(response) / len(response)
        return scores

    def _analyze_mbti(self, responses: dict) -> dict:
        scores = {
            'E': 0,
            'I': 0,
            'S': 0,
            'N': 0,
            'T': 0,
            'F': 0,
            'J': 0,
            'P': 0
        }
        for option, count in responses.items():
            if option.endswith('E'):
                scores['E'] += count
            elif option.endswith('I'):
                scores['I'] += count
            elif option.endswith('S'):
                scores['S'] += count
            elif option.endswith('N'):
                scores['N'] += count
            elif option.endswith('T'):
                scores['T'] += count
            elif option.endswith('F'):
                scores['F'] += count
            elif option.endswith('J'):
                scores['J'] += count
            elif option.endswith('P'):
                scores['P'] += count
        return scores

    def _analyze_tipi(self, responses: dict) -> dict:
        scores = {
            'extraversion': 0,
            'amabilidad': 0,
            'conciencia': 0,
            'estabilidad_emocional': 0,
            'apertura': 0
        }
        for domain, response in responses.items():
            scores[domain] = sum(response) / len(response)
        return scores

    def _get_business_unit_recommendations(self, business_unit: str, scores: dict) -> list:
        recommendations = []
        if business_unit == 'consumer':
            recommendations.extend([
                'Foco en habilidades de comunicación',
                'Desarrollo de técnicas de cierre',
                'Manejo de objeciones'
            ])
        elif business_unit == 'pharma':
            recommendations.extend([
                'Desarrollo técnico',
                'Habilidades de presentación',
                'Conocimiento del mercado'
            ])
        elif business_unit == 'service':
            recommendations.extend([
                'Manejo de conflictos',
                'Resolución de problemas',
                'Atención al detalle'
            ])
        return recommendations

    def _add_business_unit_interpretation(self, scores: dict, business_unit: str) -> None:
        if business_unit == 'consumer':
            scores['extraversion'] *= 1.2
            scores['amabilidad'] *= 1.1
        elif business_unit == 'pharma':
            scores['conciencia'] *= 1.2
            scores['apertura'] *= 1.1
        elif business_unit == 'service':
            scores['amabilidad'] *= 1.2
            scores['estabilidad'] *= 1.1

    async def _generate_results_summary(self, analysis_result: Dict[str, Any]) -> str:
        """
        Genera un resumen visual y atractivo de los resultados del análisis de personalidad.
        
        Args:
            analysis_result: Resultados del análisis de personalidad
            
        Returns:
            str: Resumen formateado de los resultados
        """
        try:
            # Obtener scores y dimensiones
            scores = analysis_result.get('scores', {})
            dimensions = analysis_result.get('dimensions', {})
            insights = analysis_result.get('insights', [])
            recommendations = analysis_result.get('recommendations', [])
            
            # Construir mensaje con formato visual
            message = "🧠 *Resultados de tu Evaluación de Personalidad*\n\n"
            
            # Sección de Perfil Principal
            message += "🌟 *Tu Perfil Principal*\n"
            if 'mbti' in scores:
                mbti_type = scores['mbti']
                message += f"• Tipo MBTI: {mbti_type}\n"
                message += f"• Descripción: {dimensions.get(mbti_type, 'Perfil único y valioso')}\n"
            message += "\n"
            
            # Sección de Dimensiones de Personalidad
            message += "📊 *Dimensiones de Personalidad*\n"
            dimension_emojis = {
                'extraversion': '🗣️',
                'introversion': '🤫',
                'sensing': '🔍',
                'intuition': '💡',
                'thinking': '🧮',
                'feeling': '❤️',
                'judging': '📋',
                'perceiving': '🔄',
                'openness': '🌍',
                'conscientiousness': '✅',
                'agreeableness': '🤝',
                'neuroticism': '😌',
                'stability': '⚖️'
            }
            
            for dimension, score in scores.items():
                if dimension != 'mbti':  # Excluir MBTI que ya se mostró
                    emoji = dimension_emojis.get(dimension, '📌')
                    progress = "🟢" * int(score/20) + "⚪" * (5 - int(score/20))
                    message += f"{emoji} {dimension.replace('_', ' ').title()}: {progress} ({score:.1f}/100)\n"
            message += "\n"
            
            # Sección de Insights
            if insights:
                message += "💡 *Insights Clave*\n"
                for insight in insights:
                    message += f"• {insight}\n"
                message += "\n"
            
            # Sección de Recomendaciones
            if recommendations:
                message += "🎯 *Recomendaciones Personalizadas*\n"
                for rec in recommendations:
                    message += f"• {rec}\n"
                message += "\n"
            
            # Sección de Fortalezas y Áreas de Desarrollo
            message += "✨ *Fortalezas y Áreas de Desarrollo*\n"
            strengths = analysis_result.get('strengths', [])
            development_areas = analysis_result.get('development_areas', [])
            
            if strengths:
                message += "💪 *Tus Fortalezas*\n"
                for strength in strengths:
                    message += f"• {strength}\n"
                message += "\n"
            
            if development_areas:
                message += "📈 *Áreas de Desarrollo*\n"
                for area in development_areas:
                    message += f"• {area}\n"
                message += "\n"
            
            # Mensaje final motivacional
            message += "🚀 *Próximos Pasos*\n"
            message += "Tu perfil de personalidad te ayudará a:\n"
            message += "• Entender mejor tus preferencias naturales\n"
            message += "• Desarrollar tus fortalezas\n"
            message += "• Trabajar en áreas de mejora\n"
            message += "• Encontrar roles que se alineen con tu personalidad\n\n"
            
            message += "¿Te gustaría explorar más a fondo algún aspecto específico de tu perfil de personalidad?"
            
            return message
            
        except Exception as e:
            logger.error(f"Error generando resumen de resultados: {str(e)}")
            return "Lo siento, hubo un error al generar el resumen de resultados. Por favor, intenta nuevamente."