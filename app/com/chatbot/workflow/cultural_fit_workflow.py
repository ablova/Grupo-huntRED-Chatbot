# /home/pablo/app/com/chatbot/workflow/cultural_fit_workflow.py
"""
Workflow para test de compatibilidad cultural.
Permite recopilar datos culturales de manera conversacional, 
adaptada a diferentes unidades de negocio.
"""

import random
import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union

from asgiref.sync import sync_to_async
from django.utils import timezone

from app.com.chatbot.workflow.base_workflow import BaseWorkflow
from app.com.chatbot.workflow.cultural_fit_test import (
    get_cultural_fit_questions, analyze_cultural_fit_responses, save_cultural_profile
)
from app.com.chatbot.core.values import get_value_driven_response
from app.com.chatbot.utils.message_utils import format_message

logger = logging.getLogger(__name__)

class CulturalFitWorkflow(BaseWorkflow):
    """
    Workflow para evaluación de compatibilidad cultural.
    
    Este workflow guía a los usuarios a través de un test cultural interactivo,
    analizando sus respuestas para generar un perfil cultural completo.
    El enfoque se basa en los valores de Grupo huntRED®: Apoyo, Solidaridad y Sinergia.
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
        self.dimensions = ["values", "motivators", "interests", "work_style", "social_impact", "generational_values"]
        self.questions_by_dimension = {}
        self.person_id = None
        self.questions_count = 0
        self.all_questions = []
        self.target_entity_type = "COMPANY"
        self.target_entity_id = None
        
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
            "nos permitirá conocerte de manera más integral.\n\n"
            "¿Estás listo para comenzar? Solo te tomará unos minutos."
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
    
    async def _process_responses(self) -> Dict[str, Any]:
        """
        Procesa las respuestas del usuario y genera el análisis cultural.
        
        Returns:
            Dict: Resultado del análisis cultural
        """
        try:
            # Calculamos los puntajes promedio por dimensión
            scores = {}
            for dimension, responses in self.responses.items():
                if responses:  # Evitar división por cero
                    scores[dimension] = sum(responses) / len(responses)
                else:
                    scores[dimension] = 0.0
            
            # Analizamos las respuestas con nuestro módulo de análisis cultural
            analysis_result = await analyze_cultural_fit_responses(
                {"scores": scores},  # Enviamos scores directamente como dict
                self.business_unit
            )
            
            # Si tenemos ID de persona, guardamos el perfil cultural
            if self.person_id:
                await save_cultural_profile(
                    self.person_id,
                    analysis_result
                )
            
            # Guardamos el resultado en el contexto
            self.context['cultural_analysis_result'] = analysis_result
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error procesando respuestas culturales: {e}", exc_info=True)
            # En caso de error, devolvemos un resultado básico
            return {
                "scores": scores if 'scores' in locals() else {},
                "strengths": ["Adaptabilidad", "Colaboración"],
                "areas_for_improvement": ["Comunicación", "Balance trabajo-vida"],
                "recommendations": ["Buscar entornos que valoren la colaboración"]
            }
    
    async def _generate_results_summary(self, analysis_result: Dict[str, Any]) -> str:
        """
        Genera un resumen de los resultados del análisis cultural.
        
        Args:
            analysis_result: Resultado del análisis cultural
            
        Returns:
            str: Mensaje con el resumen de resultados
        """
        try:
            # Extraemos datos del análisis
            scores = analysis_result.get('scores', {})
            strengths = analysis_result.get('strengths', [])
            areas_for_improvement = analysis_result.get('areas_for_improvement', [])
            recommendations = analysis_result.get('recommendations', [])
            compatibility = analysis_result.get('compatibility', {})
            
            # Calculamos puntuación global
            global_score = compatibility.get('general', 0)
            
            # Determinamos nivel de compatibilidad
            if global_score >= 85:
                compatibility_level = "Excelente"
            elif global_score >= 70:
                compatibility_level = "Muy bueno"
            elif global_score >= 50:
                compatibility_level = "Bueno"
            elif global_score >= 30:
                compatibility_level = "Regular"
            else:
                compatibility_level = "Bajo"
            
            # Construimos el mensaje de resultados, reflejando los valores de Grupo huntRED®
            message = "✅ **Análisis de Compatibilidad Cultural Completo**\n\n"
            message += f"**Puntuación Global**: {global_score:.1f}/100\n"
            message += f"**Nivel de Compatibilidad**: {compatibility_level}\n\n"
            
            # Fortalezas (Apoyo)
            message += "**Fortalezas Culturales**:\n"
            for strength in strengths[:3]:  # Limitamos a 3 para no saturar
                message += f"• {strength}\n"
            
            # Dimensiones principales (Sinergia)
            message += "\n**Dimensiones Culturales Destacadas**:\n"
            # Ordenamos dimensiones por puntaje
            sorted_dimensions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            for dimension, score in sorted_dimensions[:3]:
                dimension_name = dimension.replace('_', ' ').title()
                message += f"• {dimension_name}: {score:.1f}/5\n"
            
            # Recomendaciones (Solidaridad)
            message += "\n**Recomendaciones Personalizadas**:\n"
            for recommendation in recommendations[:2]:
                message += f"• {recommendation}\n"
            
            # Compatibilidad por BU si está disponible
            if self.business_unit and self.business_unit in compatibility:
                bu_score = compatibility[self.business_unit]
                message += f"\n**Compatibilidad con {self.business_unit.title()}**: {bu_score:.1f}%\n"
            
            # Enlace al reporte completo (simulado)
            report_id = "sample"  # En un escenario real, tendríamos un ID
            message += f"\n📊 Puedes ver el reporte completo en: /reports/cultural-fit/{report_id}\n\n"
            
            # Mensaje de cierre con valores de Grupo huntRED®
            message += (
                "Con este análisis cultural, podemos brindarte un **Apoyo** más personalizado "
                "en tu desarrollo profesional, crear **Sinergia** entre tus fortalezas y las "
                "oportunidades del mercado, y ofrecer **Solidaridad** mediante recomendaciones "
                "adaptadas a tus valores y motivaciones.\n\n"
                "¿Te gustaría recibir una propuesta comercial para un análisis más completo "
                "que incluya compatibilidad con equipos específicos o empresas?"
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Error generando resumen de resultados: {e}", exc_info=True)
            return (
                "Hemos completado tu análisis de compatibilidad cultural. "
                "Lamentablemente ocurrió un problema al generar el resumen detallado. "
                "Sin embargo, tus datos han sido guardados y podrás acceder a ellos más adelante. "
                "¿Hay algo más en lo que pueda ayudarte?"
            )
    
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
