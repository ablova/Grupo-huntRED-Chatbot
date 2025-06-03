# /home/pablo/app/com/chatbot/workflow/assessments/cultural/cultural_fit_workflow.py
"""
Módulo para la evaluación de compatibilidad cultural en Grupo huntRED®

Este módulo maneja el flujo de trabajo para evaluar la compatibilidad cultural
de los candidatos con la organización, utilizando modelos de ML para análisis
predictivo y recomendaciones personalizadas.
"""

import random
import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from asgiref.sync import sync_to_async
from django.utils import timezone

from app.ats.chatbot.workflow.core.base_workflow import BaseWorkflow
from app.ats.chatbot.workflow.assessments.cultural.cultural_fit_test import (
    get_cultural_fit_questions, analyze_cultural_fit_responses, save_cultural_profile
)
from app.ats.chatbot.values import values_middleware
from app.ml.analyzers import CulturalAnalyzer

logger = logging.getLogger(__name__)

class CulturalDimension(Enum):
    """Dimensiones culturales evaluadas"""
    INNOVATION = "innovation"
    COLLABORATION = "collaboration"
    ADAPTABILITY = "adaptability"
    RESULTS_ORIENTATION = "results_orientation"
    CUSTOMER_FOCUS = "customer_focus"
    INTEGRITY = "integrity"
    DIVERSITY = "diversity"
    LEARNING = "learning"

@dataclass
class CulturalQuestion:
    """Estructura para preguntas culturales"""
    id: str
    dimension: CulturalDimension
    text: str
    weight: float = 1.0
    options: List[Dict[str, Any]] = None

class CulturalFitWorkflow(BaseWorkflow):
    """
    Workflow para evaluación de compatibilidad cultural.
    
    Este workflow maneja el proceso de evaluación cultural, incluyendo:
    - Presentación de preguntas contextualizadas
    - Análisis de respuestas usando modelos de ML
    - Generación de insights y recomendaciones
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workflow_id = "cultural_fit"
        self.workflow_name = "Evaluación de Compatibilidad Cultural"
        self.current_question_index = 0
        self.responses = {}
        self.current_dimension = None
        self.business_unit = None
        self.domain = "general"
        self.dimensions = [
            "values", "motivators", "interests", 
            "work_style", "social_impact", "generational_values"
        ]
        self.questions_by_dimension = {}
        self.person_id = None
        self.questions_count = 0
        self.all_questions = []
        self.target_entity_type = "COMPANY"
        self.target_entity_id = None
        self.analyzer = CulturalAnalyzer()
        self.questions = self._initialize_questions()
        
    async def initialize(self, context: Dict[str, Any] = None) -> str:
        """Inicializa el workflow y da la bienvenida."""
        
        if context:
            self.context.update(context)
            
        self.business_unit = self.context.get("business_unit")
        self.person_id = self.context.get("person_id")
        self.domain = self.context.get("domain", "general")
        
        # Determinar el tipo de entidad objetivo
        self.target_entity_type = self.context.get("target_entity_type", "COMPANY")
        self.target_entity_id = self.context.get("target_entity_id")
        
        # Mensaje de bienvenida que demuestra los valores
        welcome_message = await get_value_driven_response(
            "cultural_fit_welcome",
            {
                "business_unit": self.business_unit,
                "person_id": self.person_id
            },
            "Bienvenido a la Evaluación de Compatibilidad Cultural de Grupo huntRED®. "
            "Este test nos ayudará a entenderte mejor como persona, conocer tus valores, "
            "motivaciones y preferencias culturales. Con esta información, podremos "
            "apoyarte en tu trayectoria profesional y encontrar un entorno donde puedas "
            "sentirte realizado y aportar todo tu potencial.\n\n"
            "🌟 Basado en nuestros valores de Apoyo, Solidaridad y Sinergia, este análisis "
            "nos permitirá conocerte de manera más integral llegando a un mejor entendimiento "
            "de tu perfil y tus necesidades.\n\n"
            "¿Estás listo para comenzar? Solo te tomará unos minutos y los aportes al sistema "
            "serán de gran ayuda para tu desarrollo profesional y podremos ofrecerte mejores "
            "oportunidades de crecimiento y desarrollo, alineadas a tus valores e intereses."
        )
        
        self.state = "AWAITING_START_CONFIRMATION"
        return welcome_message
    
    async def _load_questions(self) -> None:
        """Carga las preguntas del cuestionario cultural según BU y dominio."""
        # Cargamos preguntas para cada dimensión
        for dimension in self.dimensions:
            # Definimos el contexto de búsqueda
            find_context = {"dimension": dimension, "domain": self.domain}
            if self.business_unit:
                find_context["business_unit"] = self.business_unit
                
            # Obtenemos las preguntas filtradas por dimensión
            questions = await sync_to_async(get_cultural_fit_questions)(
                test_type='CulturalFit',
                domain=self.domain,
                business_unit=self.business_unit
            )
            
            # Inicializamos respuestas para esta dimensión
            self.responses[dimension] = []
            
            # Guardamos las preguntas por dimensión
            if dimension in questions:
                self.questions_by_dimension[dimension] = questions[dimension]
                self.all_questions.extend(
                    [(dimension, q) for q in questions[dimension]]
                )
        
        # Mezclamos las preguntas para una experiencia más natural
        random.shuffle(self.all_questions)
        self.questions_count = len(self.all_questions)
    
    async def handle_message(self, message_text: str) -> str:
        """
        Procesa los mensajes del usuario durante el workflow.
        
        Args:
            message_text: Texto del mensaje del usuario
            
        Returns:
            str: Respuesta del chatbot
        """
        # Limpiamos y normalizamos el mensaje
        message_text = message_text.strip().lower()
        
        # Estado: Esperando confirmación para iniciar
        if self.state == "AWAITING_START_CONFIRMATION":
            if re.search(r'si|s[ií]|comenzar|empezar|listo|adelante|ok|okay|dale', message_text):
                await self._load_questions()
                self.state = "ASKING_QUESTIONS"
                return await self._ask_next_question()
            elif re.search(r'no|luego|después|ahora no|m[aá]s tarde', message_text):
                self.state = "COMPLETED"
                return await get_value_driven_response(
                    "cultural_fit_declined",
                    self.context,
                    "Entiendo, no hay problema. Puedes realizar la evaluación cultural "
                    "en otro momento cuando lo consideres conveniente. Recuerda que esta "
                    "información nos ayudará a brindarte un mejor servicio y encontrar "
                    "oportunidades que se alineen con tus valores y preferencias.\n\n"
                    "¿En qué más puedo ayudarte ahora?"
                )
            else:
                # Si no entendemos la respuesta, pedimos confirmación de nuevo
                return "No entendí tu respuesta. ¿Te gustaría comenzar la evaluación cultural ahora? Por favor responde con 'sí' o 'no'."
        
        # Estado: Haciendo preguntas del test
        elif self.state == "ASKING_QUESTIONS":
            # Procesamos la respuesta a la pregunta actual
            current_dimension, current_question = self.all_questions[self.current_question_index - 1]
            
            # Detectamos la respuesta del usuario (valor numérico o texto)
            response_value = self._extract_response_value(message_text, current_question)
            
            if response_value is None:
                # Si no podemos extraer un valor válido, pedimos clarificación
                options_text = " | ".join(current_question.get('options', []))
                return f"No pude entender tu respuesta. Por favor, elige una opción entre: {options_text}"
            
            # Guardamos la respuesta
            self.responses[current_dimension].append(response_value)
            
            # Verificamos si hay más preguntas
            if self.current_question_index < self.questions_count:
                return await self._ask_next_question()
            else:
                # Si terminamos todas las preguntas, pasamos al análisis
                self.state = "ANALYZING"
                # Mostramos mensaje de procesamiento
                processing_message = await get_value_driven_response(
                    "cultural_fit_processing",
                    self.context,
                    "¡Gracias por completar la evaluación cultural! Estamos procesando tus respuestas para generar tu perfil de compatibilidad cultural.\n\nEsto solo tardará unos segundos..."
                )
                
                # Analizamos respuestas y generamos el reporte
                analysis_result = await self._process_responses()
                
                # Transición al estado final
                self.state = "COMPLETED"
                
                # Generamos respuesta con resultados resumidos
                return await self._generate_results_summary(analysis_result)
        
        # Estado: Completado (solo debería ocurrir si el usuario sigue enviando mensajes después)
        elif self.state == "COMPLETED":
            return "Tu evaluación cultural ya ha sido completada. ¿Te gustaría ver tus resultados de nuevo o prefieres explorar otras opciones?"
        
        # Estado desconocido (no debería ocurrir)
        else:
            logger.error(f"Estado desconocido en CulturalFitWorkflow: {self.state}")
            return "Lo siento, ha ocurrido un error en el proceso. Por favor, intenta nuevamente."
    
    async def _ask_next_question(self) -> str:
        """Presenta la siguiente pregunta del cuestionario cultural."""
        
        if self.current_question_index >= self.questions_count:
            # No hay más preguntas
            return "Hemos terminado con todas las preguntas."
        
        # Obtenemos la siguiente pregunta
        dimension, question = self.all_questions[self.current_question_index]
        self.current_dimension = dimension
        
        # Incrementamos el índice para la próxima pregunta
        self.current_question_index += 1
        
        # Formateamos la pregunta con opciones
        question_text = question.get('text', '')
        options = question.get('options', [])
        
        # Mostrar progreso actual
        progress = f"Pregunta {self.current_question_index} de {self.questions_count}"
        
        # Construimos el mensaje de la pregunta
        message = f"**{progress}**\n\n{question_text}\n\n"
        
        # Agregamos las opciones numeradas
        for i, option in enumerate(options, 1):
            message += f"{option}\n"
        
        message += "\nPor favor, selecciona la opción que mejor refleje tu opinión."
        
        return message
    
    def _extract_response_value(self, message_text: str, question: Dict) -> Optional[int]:
        """
        Extrae el valor numérico de la respuesta del usuario.
        
        Args:
            message_text: Texto del mensaje del usuario
            question: Diccionario con la pregunta y opciones
            
        Returns:
            int: Valor numérico de la respuesta (1-5) o None si no se puede extraer
        """
        # Patrones para detectar respuestas numéricas directas
        if re.search(r'^[1-5]$', message_text):
            return int(message_text)
        
        # Patrones para detectar respuestas como "opción 3" o "3 - xxx"
        match = re.search(r'(?:opci[oó]n\s*)?([1-5])(?:\s*[-:]\s*|\s+)', message_text)
        if match:
            return int(match.group(1))
        
        # Verificar por texto exacto de las opciones
        options = question.get('options', [])
        for i, option in enumerate(options, 1):
            if option.lower() in message_text:
                return i
        
        # Patrones para detectar intensidad
        intensity_patterns = {
            1: r'nada|nunca|muy poco|muy mal|p[ée]simo',
            2: r'poco|mal|ocasionalmente|apenas',
            3: r'neutral|a veces|regular|ni bien ni mal|parcialmente',
            4: r'bastante|bien|frecuentemente|mucho',
            5: r'siempre|excelente|totalmente|completamente|muchísimo'
        }
        
        for value, pattern in intensity_patterns.items():
            if re.search(pattern, message_text):
                return value
        
        # No pudimos extraer un valor válido
        return None
    
    async def _process_responses(self) -> Dict:
        """
        Procesa las respuestas del usuario y genera el análisis cultural.
        
        Returns:
            Dict: Resultado del análisis cultural
        """
        try:
            # Convertir las respuestas al formato esperado por el analizador
            formatted_responses = {}
            for dimension, questions in self.questions_by_dimension.items():
                for question in questions:
                    question_id = question.get('id')
                    if question_id in self.responses:
                        formatted_responses[question_id] = self.responses[question_id]
            
            # Primero intentamos usar el analizador centralizado si está disponible
            try:
                # Preparar datos para el analizador centralizado
                analysis_data = {
                    'assessment_type': 'cultural_fit',
                    'cultural_responses': formatted_responses,
                    'business_unit': self.business_unit,
                    'domain': self.domain,
                    'target_entity_type': self.target_entity_type,
                    'target_entity_id': self.target_entity_id
                }
                
                # Instanciar y usar el analizador centralizado
                analyzer = CulturalAnalyzer()
                result = await sync_to_async(analyzer.analyze)(analysis_data, self.business_unit)
                
                # Si el análisis centralizado fue exitoso, lo usamos
                if result and not result.get('status') == 'error':
                    logger.info(f"Análisis cultural realizado con analizador centralizado")
                    analysis_result = result
                else:
                    # Si hay un error, caemos al método tradicional
                    logger.warning(f"Fallback a análisis cultural tradicional: {result.get('message', 'Error desconocido')}")
                    # Ejecutar el análisis cultural tradicional
                    analysis_result = await sync_to_async(analyze_cultural_fit_responses)(
                        formatted_responses,
                        self.business_unit,
                        self.domain,
                        self.target_entity_type,
                        self.target_entity_id
                    )
            except Exception as e:
                logger.error(f"Error usando analizador cultural centralizado: {str(e)}. Fallback a análisis tradicional.")
                # Ejecutar el análisis cultural tradicional como fallback
                analysis_result = await sync_to_async(analyze_cultural_fit_responses)(
                    formatted_responses,
                    self.business_unit,
                    self.domain,
                    self.target_entity_type,
                    self.target_entity_id
                )
            
            # Guardar el perfil cultural si tenemos un person_id
            if self.person_id:
                await sync_to_async(save_cultural_profile)(
                    self.person_id,
                    analysis_result,
                    self.business_unit
                )
            
            logger.info(f"Análisis cultural completado para BU: {self.business_unit}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error procesando respuestas culturales: {str(e)}")
            return {
                'error': True,
                'message': 'Lo sentimos, ha ocurrido un error al procesar tus respuestas. Por favor, intenta nuevamente.'
            }
    
    async def _generate_results_summary(self, analysis_result: Dict) -> str:
        """
        Genera un resumen visual y atractivo de los resultados del análisis cultural.
        
        Args:
            analysis_result: Resultados del análisis cultural
            
        Returns:
            str: Resumen formateado de los resultados
        """
        try:
            # Obtener scores y compatibilidad
            scores = analysis_result.get('scores', {})
            compatibility = analysis_result.get('compatibility', {})
            strengths = analysis_result.get('strengths', [])
            improvement_areas = analysis_result.get('improvement_areas', [])
            recommendations = analysis_result.get('recommendations', [])
            
            # Construir mensaje con formato visual
            message = "🎯 *Resultados de tu Evaluación Cultural*\n\n"
            
            # Sección de Compatibilidad General
            message += "🌟 *Compatibilidad General*\n"
            for unit, score in compatibility.items():
                # Convertir score a emoji de progreso
                progress = "🟢" * int(score/20) + "⚪" * (5 - int(score/20))
                message += f"• {unit.title()}: {progress} {score:.1f}%\n"
            message += "\n"
            
            # Sección de Dimensiones
            message += "📊 *Análisis por Dimensiones*\n"
            dimension_emojis = {
                'values': '💎',
                'motivators': '🎯',
                'interests': '🎨',
                'work_style': '⚡',
                'social_impact': '🤝',
                'generational_values': '👥'
            }
            
            for dimension, score in scores.items():
                emoji = dimension_emojis.get(dimension, '📌')
                progress = "🟢" * int(score) + "⚪" * (5 - int(score))
                message += f"{emoji} {dimension.replace('_', ' ').title()}: {progress} ({score:.1f}/5)\n"
            message += "\n"
            
            # Sección de Fortalezas
            if strengths:
                message += "💪 *Tus Fortalezas*\n"
                for strength in strengths:
                    message += f"• {strength}\n"
                message += "\n"
            
            # Sección de Áreas de Mejora
            if improvement_areas:
                message += "📈 *Áreas de Oportunidad*\n"
                for area in improvement_areas:
                    message += f"• {area}\n"
                message += "\n"
            
            # Sección de Recomendaciones
            if recommendations:
                message += "🎓 *Recomendaciones Personalizadas*\n"
                for rec in recommendations:
                    message += f"• {rec}\n"
                message += "\n"
            
            # Mensaje final motivacional
            message += "✨ *Próximos Pasos*\n"
            message += "Estos resultados te ayudarán a:\n"
            message += "• Identificar tu mejor ajuste cultural\n"
            message += "• Desarrollar tus fortalezas\n"
            message += "• Trabajar en áreas de oportunidad\n"
            message += "• Encontrar el entorno laboral ideal\n\n"
            
            message += "¿Te gustaría explorar más a fondo algún aspecto específico de tu perfil cultural?"
            
            return message
            
        except Exception as e:
            logger.error(f"Error generando resumen de resultados: {str(e)}")
            return "Lo siento, hubo un error al generar el resumen de resultados. Por favor, intenta nuevamente."
    
    async def get_next_state(self, message_text: str) -> Optional[str]:
        """Determina el siguiente estado del workflow basado en el mensaje y estado actual."""
        
        if self.state == "AWAITING_START_CONFIRMATION":
            if re.search(r'si|s[ií]|comenzar|empezar|listo|adelante|ok|okay|dale', message_text.lower()):
                return "ASKING_QUESTIONS"
            elif re.search(r'no|luego|después|ahora no|m[aá]s tarde', message_text.lower()):
                return "COMPLETED"
        
        elif self.state == "ASKING_QUESTIONS":
            if self.current_question_index >= self.questions_count:
                return "ANALYZING"
        
        elif self.state == "ANALYZING":
            return "COMPLETED"
        
        # Si no hay cambio de estado, devolvemos None
        return None

    def _initialize_questions(self) -> List[CulturalQuestion]:
        """Inicializa el conjunto de preguntas culturales."""
        return [
            CulturalQuestion(
                id="innov_1",
                dimension=CulturalDimension.INNOVATION,
                text="¿Cómo te sientes al proponer nuevas ideas o formas de hacer las cosas?",
                options=[
                    {"value": 1, "text": "Prefiero seguir procesos establecidos"},
                    {"value": 2, "text": "A veces propongo mejoras"},
                    {"value": 3, "text": "Me gusta innovar cuando es necesario"},
                    {"value": 4, "text": "Busco constantemente nuevas soluciones"},
                    {"value": 5, "text": "La innovación es parte fundamental de mi trabajo"}
                ]
            ),
            CulturalQuestion(
                id="collab_1",
                dimension=CulturalDimension.COLLABORATION,
                text="¿Cómo describes tu estilo de trabajo en equipo?",
                options=[
                    {"value": 1, "text": "Prefiero trabajar de forma independiente"},
                    {"value": 2, "text": "Colaboro cuando es necesario"},
                    {"value": 3, "text": "Disfruto trabajando en equipo"},
                    {"value": 4, "text": "Busco activamente la colaboración"},
                    {"value": 5, "text": "Soy un facilitador de la colaboración"}
                ]
            ),
            CulturalQuestion(
                id="adapt_1",
                dimension=CulturalDimension.ADAPTABILITY,
                text="¿Cómo manejas los cambios en tu entorno de trabajo?",
                options=[
                    {"value": 1, "text": "Me cuesta adaptarme a los cambios"},
                    {"value": 2, "text": "Me adapto cuando es necesario"},
                    {"value": 3, "text": "Acepto los cambios positivamente"},
                    {"value": 4, "text": "Anticipo y me preparo para los cambios"},
                    {"value": 5, "text": "Promuevo y lidero cambios"}
                ]
            ),
            CulturalQuestion(
                id="results_1",
                dimension=CulturalDimension.RESULTS_ORIENTATION,
                text="¿Qué priorizas en tu trabajo diario?",
                options=[
                    {"value": 1, "text": "Cumplir con mis tareas asignadas"},
                    {"value": 2, "text": "Mantener un buen ambiente de trabajo"},
                    {"value": 3, "text": "Alcanzar objetivos individuales"},
                    {"value": 4, "text": "Contribuir al éxito del equipo"},
                    {"value": 5, "text": "Impulsar resultados organizacionales"}
                ]
            ),
            CulturalQuestion(
                id="customer_1",
                dimension=CulturalDimension.CUSTOMER_FOCUS,
                text="¿Cómo manejas las necesidades de los clientes?",
                options=[
                    {"value": 1, "text": "Respondo a solicitudes directas"},
                    {"value": 2, "text": "Busco entender las necesidades básicas"},
                    {"value": 3, "text": "Anticipo necesidades comunes"},
                    {"value": 4, "text": "Desarrollo soluciones personalizadas"},
                    {"value": 5, "text": "Creo experiencias excepcionales"}
                ]
            ),
            CulturalQuestion(
                id="integrity_1",
                dimension=CulturalDimension.INTEGRITY,
                text="¿Cómo manejas situaciones éticas complejas?",
                options=[
                    {"value": 1, "text": "Sigo las reglas establecidas"},
                    {"value": 2, "text": "Consulto con superiores"},
                    {"value": 3, "text": "Analizo el impacto de mis decisiones"},
                    {"value": 4, "text": "Promuevo prácticas éticas"},
                    {"value": 5, "text": "Lidero con ejemplo en integridad"}
                ]
            ),
            CulturalQuestion(
                id="diversity_1",
                dimension=CulturalDimension.DIVERSITY,
                text="¿Cómo valoras la diversidad en el trabajo?",
                options=[
                    {"value": 1, "text": "Respeto las diferencias"},
                    {"value": 2, "text": "Aprecio diferentes perspectivas"},
                    {"value": 3, "text": "Busco incluir diversas opiniones"},
                    {"value": 4, "text": "Promuevo la inclusión activamente"},
                    {"value": 5, "text": "Lidero iniciativas de diversidad"}
                ]
            ),
            CulturalQuestion(
                id="learning_1",
                dimension=CulturalDimension.LEARNING,
                text="¿Cómo manejas tu desarrollo profesional?",
                options=[
                    {"value": 1, "text": "Aprendo de la experiencia diaria"},
                    {"value": 2, "text": "Busco capacitación cuando es necesaria"},
                    {"value": 3, "text": "Me mantengo actualizado en mi área"},
                    {"value": 4, "text": "Busco crecimiento continuo"},
                    {"value": 5, "text": "Comparto conocimiento y mentoría"}
                ]
            )
        ]
