# /home/pablo/app/com/chatbot/workflow/assessments/talent/talent_analysis_workflow.py
"""
Workflow para Análisis de Talento 360°.

Este workflow maneja la recopilación de información para realizar
un análisis integral de talento, incluyendo sinergia de equipos,
trayectoria profesional, cultural fit y retención.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from django.conf import settings

from app.ats.chatbot.workflow.core.base_workflow import BaseWorkflow
from app.models import Person, BusinessUnit, Company, Team
from app.ats.talent.team_synergy import TeamSynergyAnalyzer
from app.ats.talent.trajectory_analyzer import TrajectoryAnalyzer
from app.ats.talent.cultural_fit import CulturalFitAnalyzer
from app.ats.talent.learning_engine import LearningEngine
from app.ats.talent.mentor_matcher import MentorMatcher
from app.ats.talent.retention_predictor import RetentionPredictor
from app.ats.talent.intervention_system import InterventionSystem

# Importar los analizadores centralizados
from app.ml.analyzers import TalentAnalyzer, IntegratedAnalyzer

logger = logging.getLogger(__name__)

class TalentAnalysisWorkflow(BaseWorkflow):
    """Clase para el análisis de talento 360° que proporciona insights sobre trayectoria, sinergia, cultural fit y retención."""
    
    workflow_type = "talent_analysis"  # Identificador único del workflow
    """
    Workflow para gestionar el proceso de análisis de talento 360°.
    
    Este workflow guía al usuario a través de la recopilación de datos
    necesarios para realizar un análisis integral de talento, que incluye:
    - Análisis de sinergia de equipos
    - Análisis de trayectoria profesional
    - Análisis de compatibilidad cultural
    - Recomendaciones de aprendizaje
    - Emparejamiento con mentores
    - Predicción de retención e intervención
    """
    
    def __init__(self, user_id=None, chat_id=None, business_unit=None, **kwargs):
        """Inicializa el workflow con parámetros específicos."""
        super().__init__(user_id, chat_id, **kwargs)
        self.business_unit = business_unit
        self.workflow_id = "talent_analysis"
        self.workflow_name = "Análisis de Talento 360°"
        self.analysis_type = None
        self.target_person_id = None
        self.target_team_ids = []
        self.target_company_id = None
        self.discovery_complete = False
        self.data_collection_complete = False
        self.current_phase = "discovery"  # discovery, individual_data, team_dynamics, culture, confirmation
        self.phases_data = {
            "discovery": {},
            "individual_data": {},
            "team_dynamics": {},
            "culture": {},
            "confirmation": {}
        }
        
        # Inicializar analizadores
        self.team_synergy_analyzer = TeamSynergyAnalyzer()
        self.trajectory_analyzer = TrajectoryAnalyzer()
        self.cultural_fit_analyzer = CulturalFitAnalyzer()
        self.learning_engine = LearningEngine()
        self.mentor_matcher = MentorMatcher()
        self.retention_predictor = RetentionPredictor()
        self.intervention_system = InterventionSystem()
        
    async def process_message(self, message_text: str, message_type: str = 'text') -> str:
        """
        Procesa los mensajes del usuario durante el workflow.
        
        Args:
            message_text: Texto del mensaje del usuario
            message_type: Tipo de mensaje ('text', 'image', 'document', etc.)
            
        Returns:
            str: Respuesta del chatbot
        """
        try:
            # Si estamos en la fase de descubrimiento
            if self.current_phase == "discovery":
                return await self._process_discovery_phase(message_text, message_type)
                
            # Si estamos en la fase de datos individuales
            elif self.current_phase == "individual_data":
                return await self._process_individual_data_phase(message_text, message_type)
                
            # Si estamos en la fase de dinámica de equipo
            elif self.current_phase == "team_dynamics":
                return await self._process_team_dynamics_phase(message_text, message_type)
                
            # Si estamos en la fase de cultura organizacional
            elif self.current_phase == "culture":
                return await self._process_culture_phase(message_text, message_type)
                
            # Si estamos en la fase de confirmación
            elif self.current_phase == "confirmation":
                return await self._process_confirmation_phase(message_text, message_type)
                
            # Caso no esperado
            else:
                logger.warning(f"Fase no reconocida en workflow de análisis de talento: {self.current_phase}")
                return "Disculpa, hubo un problema con el procesamiento de tu solicitud. ¿Podemos comenzar de nuevo?"
                
        except Exception as e:
            logger.error(f"Error en TalentAnalysisWorkflow.process_message: {str(e)}")
            return "Disculpa, ocurrió un error al procesar tu mensaje. Por favor, inténtalo de nuevo."
    
    async def _process_discovery_phase(self, message_text: str, message_type: str) -> str:
        """Procesa mensajes durante la fase de descubrimiento."""
        # Si es el primer mensaje en esta fase, iniciar con preguntas de descubrimiento
        if not self.phases_data["discovery"]:
            self.phases_data["discovery"]["started_at"] = datetime.now().isoformat()
            return (
                "👋 Bienvenido al Análisis de Talento 360° de Grupo huntRED®. "
                "Este proceso nos permitirá obtener insights valiosos sobre el talento individual y/o de equipo. "
                "\n\n¿Qué tipo de análisis te gustaría realizar?\n"
                "1️⃣ Análisis de Sinergia de Equipo\n"
                "2️⃣ Análisis de Trayectoria Profesional\n"
                "3️⃣ Análisis de Compatibilidad Cultural\n"
                "4️⃣ Predicción de Retención\n"
                "5️⃣ Análisis Integral 360°"
            )
            
        # Determinar el tipo de análisis basado en la respuesta
        if "1" in message_text or "sinergia" in message_text.lower() or "equipo" in message_text.lower():
            self.analysis_type = "team_synergy"
            self.phases_data["discovery"]["analysis_type"] = "team_synergy"
            return (
                "Has seleccionado el Análisis de Sinergia de Equipo. Este análisis evalúa la composición "
                "del equipo en términos de habilidades, personalidades, generaciones y propósito, "
                "identificando fortalezas y áreas de mejora.\n\n"
                "Por favor, indícame el nombre de la empresa y equipo que deseas analizar."
            )
            
        elif "2" in message_text or "trayectoria" in message_text.lower() or "carrera" in message_text.lower():
            self.analysis_type = "career_trajectory"
            self.phases_data["discovery"]["analysis_type"] = "career_trajectory"
            return (
                "Has seleccionado el Análisis de Trayectoria Profesional. Este análisis predice "
                "la ruta óptima de desarrollo profesional, identificando habilidades críticas a desarrollar "
                "y oportunidades de crecimiento.\n\n"
                "Por favor, indícame el nombre de la persona que deseas analizar o su ID."
            )
            
        elif "3" in message_text or "cultural" in message_text.lower() or "compatibilidad" in message_text.lower():
            self.analysis_type = "cultural_fit"
            self.phases_data["discovery"]["analysis_type"] = "cultural_fit"
            return (
                "Has seleccionado el Análisis de Compatibilidad Cultural. Este análisis evalúa "
                "la alineación de valores y prácticas culturales entre la persona y la organización.\n\n"
                "Por favor, indícame el nombre de la persona y la empresa que deseas analizar."
            )
            
        elif "4" in message_text or "retención" in message_text.lower() or "rotación" in message_text.lower():
            self.analysis_type = "retention"
            self.phases_data["discovery"]["analysis_type"] = "retention"
            return (
                "Has seleccionado la Predicción de Retención. Este análisis identifica el riesgo "
                "de desvinculación y genera planes de intervención personalizados.\n\n"
                "Por favor, indícame el nombre de la persona que deseas analizar o su ID."
            )
            
        elif "5" in message_text or "360" in message_text or "integral" in message_text.lower():
            self.analysis_type = "360"
            self.phases_data["discovery"]["analysis_type"] = "360"
            return (
                "Has seleccionado el Análisis Integral 360°. Este análisis combina todos los módulos "
                "para una evaluación holística del talento individual y de equipo.\n\n"
                "¿Deseas analizar a una persona específica o a un equipo completo?"
            )
            
        # Si estamos en proceso de identificar la empresa/equipo/persona
        if self.analysis_type and not self.target_person_id and not self.target_team_ids:
            # Procesar respuesta según tipo de análisis
            if self.analysis_type in ["team_synergy", "360"] and "equipo" in message_text.lower():
                # Intentar identificar el equipo
                team_name = message_text.replace("equipo", "", 1).strip()
                # En una implementación real, aquí buscaríamos el equipo en la base de datos
                # Por ahora, simularemos una respuesta exitosa
                self.target_team_ids = [1]  # ID simulado
                self.phases_data["discovery"]["team_name"] = team_name
                self.phases_data["discovery"]["team_id"] = 1
                
                # Avanzar a la siguiente fase
                self.current_phase = "team_dynamics"
                return (
                    f"Gracias. Vamos a analizar el equipo '{team_name}'.\n\n"
                    "Para realizar un análisis completo, necesitaré información sobre la dinámica del equipo. "
                    "¿Podrías describir brevemente cómo es la interacción entre los miembros?"
                )
                
            elif self.analysis_type in ["career_trajectory", "cultural_fit", "retention", "360"] and not "equipo" in message_text.lower():
                # Intentar identificar a la persona
                person_name = message_text.strip()
                # En una implementación real, aquí buscaríamos a la persona en la base de datos
                # Por ahora, simularemos una respuesta exitosa
                self.target_person_id = 1  # ID simulado
                self.phases_data["discovery"]["person_name"] = person_name
                self.phases_data["discovery"]["person_id"] = 1
                
                # Avanzar a la siguiente fase
                self.current_phase = "individual_data"
                return (
                    f"Gracias. Vamos a analizar a '{person_name}'.\n\n"
                    "Para realizar un análisis completo, necesitaré información adicional. "
                    "¿Cuál es su puesto actual y experiencia aproximada en años?"
                )
        
        # Respuesta por defecto si no se reconoce la entrada
        return (
            "No he podido entender completamente tu respuesta. Por favor, selecciona una de las opciones "
            "proporcionadas o proporciona la información solicitada."
        )
    
    async def _process_individual_data_phase(self, message_text: str, message_type: str) -> str:
        """Procesa mensajes durante la fase de recopilación de datos individuales."""
        # Si es el primer mensaje en esta fase, iniciar con preguntas sobre experiencia
        if not self.phases_data["individual_data"]:
            self.phases_data["individual_data"]["started_at"] = datetime.now().isoformat()
            # Capturar información del mensaje actual (puesto y experiencia)
            if "puesto" in message_text.lower() or "cargo" in message_text.lower() or "posición" in message_text.lower():
                position_info = message_text.strip()
                self.phases_data["individual_data"]["position_info"] = position_info
                
                return (
                    "Gracias por esa información. Ahora necesito conocer sus principales habilidades y competencias. "
                    "¿Podrías enumerar las 3-5 habilidades más destacadas?"
                )
            else:
                return (
                    "Entiendo. Para continuar con el análisis, necesito conocer su puesto actual y experiencia aproximada. "
                    "¿Podrías proporcionarme esa información?"
                )
                
        # Si ya tenemos información de posición pero no habilidades
        elif "position_info" in self.phases_data["individual_data"] and not "skills" in self.phases_data["individual_data"]:
            skills_info = message_text.strip()
            self.phases_data["individual_data"]["skills"] = skills_info
            
            return (
                "Excelentes habilidades. Ahora, hablemos de sus aspiraciones profesionales. "
                "¿Cuáles son sus metas de carrera a corto y mediano plazo?"
            )
            
        # Si ya tenemos habilidades pero no aspiraciones
        elif "skills" in self.phases_data["individual_data"] and not "aspirations" in self.phases_data["individual_data"]:
            aspirations_info = message_text.strip()
            self.phases_data["individual_data"]["aspirations"] = aspirations_info
            
            # Si es análisis cultural, preguntar por valores
            if self.analysis_type in ["cultural_fit", "360"]:
                return (
                    "Gracias por compartir esas aspiraciones. Para evaluar compatibilidad cultural, "
                    "necesito conocer sus valores profesionales principales. "
                    "¿Qué valores son más importantes para esta persona en su entorno laboral?"
                )
            # Si es análisis de retención, preguntar por factores de satisfacción
            elif self.analysis_type in ["retention", "360"]:
                return (
                    "Gracias por compartir esas aspiraciones. Para evaluar el riesgo de retención, "
                    "necesito entender los factores de satisfacción laboral. "
                    "¿Qué aspectos del trabajo actual generan mayor y menor satisfacción?"
                )
            # Para otros análisis, avanzar a la siguiente fase
            else:
                self.current_phase = "confirmation"
                return await self._generate_confirmation_message()
                
        # Si ya tenemos aspiraciones pero no valores/satisfacción (para análisis que los requieren)
        elif "aspirations" in self.phases_data["individual_data"] and (
                (self.analysis_type in ["cultural_fit", "360"] and not "values" in self.phases_data["individual_data"]) or
                (self.analysis_type in ["retention", "360"] and not "satisfaction_factors" in self.phases_data["individual_data"])
            ):
            
            # Capturar valores o factores de satisfacción según corresponda
            if self.analysis_type in ["cultural_fit", "360"]:
                values_info = message_text.strip()
                self.phases_data["individual_data"]["values"] = values_info
                
                # Si también necesitamos factores de satisfacción (para análisis 360)
                if self.analysis_type == "360" and not "satisfaction_factors" in self.phases_data["individual_data"]:
                    return (
                        "Gracias por compartir esos valores. Para completar el análisis, "
                        "necesito entender los factores de satisfacción laboral. "
                        "¿Qué aspectos del trabajo actual generan mayor y menor satisfacción?"
                    )
                else:
                    self.current_phase = "culture"
                    return (
                        "Perfecto. Ahora necesito información sobre la cultura de la organización "
                        "para evaluar la compatibilidad. ¿Cómo describirías los valores y prácticas "
                        "culturales predominantes en la empresa?"
                    )
                    
            elif self.analysis_type in ["retention", "360"]:
                satisfaction_info = message_text.strip()
                self.phases_data["individual_data"]["satisfaction_factors"] = satisfaction_info
                
                # Si también necesitamos valores (para análisis 360)
                if self.analysis_type == "360" and not "values" in self.phases_data["individual_data"]:
                    return (
                        "Gracias por compartir esos factores de satisfacción. Para completar el análisis, "
                        "necesito conocer sus valores profesionales principales. "
                        "¿Qué valores son más importantes para esta persona en su entorno laboral?"
                    )
                else:
                    self.current_phase = "confirmation"
                    return await self._generate_confirmation_message()
        
        # Si ya tenemos toda la información individual necesaria para el análisis 360
        elif self.analysis_type == "360" and "values" in self.phases_data["individual_data"] and "satisfaction_factors" in self.phases_data["individual_data"]:
            self.current_phase = "culture"
            return (
                "Perfecto. Ahora necesito información sobre la cultura de la organización "
                "para evaluar la compatibilidad. ¿Cómo describirías los valores y prácticas "
                "culturales predominantes en la empresa?"
            )
            
        # Respuesta por defecto
        return (
            "Gracias por esa información. Por favor, continúa proporcionando los detalles solicitados "
            "para que pueda completar el análisis."
        )
    
    async def _process_team_dynamics_phase(self, message_text: str, message_type: str) -> str:
        """Procesa mensajes durante la fase de recopilación de datos de dinámica de equipo."""
        # Si es el primer mensaje en esta fase
        if not self.phases_data["team_dynamics"]:
            self.phases_data["team_dynamics"]["started_at"] = datetime.now().isoformat()
            self.phases_data["team_dynamics"]["interaction_description"] = message_text.strip()
            
            return (
                "Gracias por esa descripción. Ahora, ¿podrías indicarme la composición del equipo "
                "en términos de roles y experiencia? Por ejemplo: 2 desarrolladores senior, "
                "1 diseñador UX, 1 product manager, etc."
            )
            
        # Si ya tenemos descripción de interacción pero no composición
        elif "interaction_description" in self.phases_data["team_dynamics"] and not "composition" in self.phases_data["team_dynamics"]:
            composition_info = message_text.strip()
            self.phases_data["team_dynamics"]["composition"] = composition_info
            
            return (
                "Excelente. ¿Podrías describir las principales fortalezas y áreas de mejora que "
                "has observado en el equipo? Esto me ayudará a entender mejor su dinámica actual."
            )
            
        # Si ya tenemos composición pero no fortalezas/debilidades
        elif "composition" in self.phases_data["team_dynamics"] and not "strengths_weaknesses" in self.phases_data["team_dynamics"]:
            strengths_weaknesses_info = message_text.strip()
            self.phases_data["team_dynamics"]["strengths_weaknesses"] = strengths_weaknesses_info
            
            # Si es un análisis que requiere información cultural, continuar a esa fase
            if self.analysis_type in ["cultural_fit", "360"]:
                self.current_phase = "culture"
                return (
                    "Gracias por esa información tan valiosa. Ahora me gustaría conocer más sobre "
                    "la cultura organizacional. ¿Cómo describirías los valores y prácticas culturales "
                    "predominantes en la empresa?"
                )
            # De lo contrario, avanzar a confirmación
            else:
                self.current_phase = "confirmation"
                return await self._generate_confirmation_message()
                
        # Respuesta por defecto
        return (
            "Gracias por esa información. Por favor, continúa proporcionando los detalles solicitados "
            "para que pueda completar el análisis."
        )
    
    async def _process_culture_phase(self, message_text: str, message_type: str) -> str:
        """Procesa mensajes durante la fase de recopilación de datos culturales."""
        # Si es el primer mensaje en esta fase
        if not self.phases_data["culture"]:
            self.phases_data["culture"]["started_at"] = datetime.now().isoformat()
            self.phases_data["culture"]["org_culture_description"] = message_text.strip()
            
            return (
                "Gracias por esa descripción de la cultura. ¿Podrías indicarme cuáles son los valores "
                "corporativos oficiales o declarados por la organización?"
            )
            
        # Si ya tenemos descripción de cultura pero no valores declarados
        elif "org_culture_description" in self.phases_data["culture"] and not "declared_values" in self.phases_data["culture"]:
            values_info = message_text.strip()
            self.phases_data["culture"]["declared_values"] = values_info
            
            return (
                "Perfecto. Por último, ¿cómo describirías el estilo de liderazgo predominante "
                "en la organización? (Por ejemplo: participativo, directivo, coaching, etc.)"
            )
            
        # Si ya tenemos valores declarados pero no estilo de liderazgo
        elif "declared_values" in self.phases_data["culture"] and not "leadership_style" in self.phases_data["culture"]:
            leadership_info = message_text.strip()
            self.phases_data["culture"]["leadership_style"] = leadership_info
            
            # Avanzar a fase de confirmación
            self.current_phase = "confirmation"
            return await self._generate_confirmation_message()
            
        # Respuesta por defecto
        return (
            "Gracias por esa información. Por favor, continúa proporcionando los detalles solicitados "
            "para que pueda completar el análisis."
        )
    
    async def _process_confirmation_phase(self, message_text: str, message_type: str) -> str:
        """Procesa mensajes durante la fase de confirmación y genera el análisis."""
        # Si es una confirmación positiva
        if any(word in message_text.lower() for word in ["sí", "si", "adelante", "correcto", "procede", "generar"]):
            # Indicar que estamos procesando
            processing_message = (
                "¡Excelente! Estoy procesando toda la información recopilada para generar "
                "un análisis completo. Esto puede tomar unos momentos...\n\n"
                "⏳ Generando análisis de talento..."
            )
            
            # En una implementación real, aquí generaríamos el análisis usando los módulos correspondientes
            # Por ahora, simularemos una respuesta exitosa
            
            # Generar el análisis según el tipo
            if self.analysis_type == "team_synergy":
                analysis_result = await self._generate_team_synergy_analysis()
            elif self.analysis_type == "career_trajectory":
                analysis_result = await self._generate_career_trajectory_analysis()
            elif self.analysis_type == "cultural_fit":
                analysis_result = await self._generate_cultural_fit_analysis()
            elif self.analysis_type == "retention":
                analysis_result = await self._generate_retention_analysis()
            elif self.analysis_type == "360":
                analysis_result = await self._generate_360_analysis()
            else:
                analysis_result = "No se pudo determinar el tipo de análisis a generar."
                
            # Resetear el workflow para un nuevo análisis
            self._reset_workflow()
                
            return f"{processing_message}\n\n{analysis_result}"
            
        # Si es una negación o corrección
        elif any(word in message_text.lower() for word in ["no", "incorrecto", "corregir", "cambiar", "modificar"]):
            # Preguntar qué información desea corregir
            return (
                "Entiendo que hay información que deseas corregir. Por favor, indícame qué aspecto "
                "específico necesitas modificar y proporciónme la información correcta."
            )
            
        # Si proporciona información para corregir
        else:
            # En una implementación real, aquí procesaríamos la corrección específica
            # Por ahora, simularemos una actualización genérica
            correction_info = message_text.strip()
            
            return (
                f"He actualizado la información con tu corrección: '{correction_info}'. "
                "¿Hay alguna otra corrección que desees hacer? Si no es así, por favor confirma "
                "para proceder con la generación del análisis."
            )
            
    async def _generate_confirmation_message(self) -> str:
        """Genera un mensaje de confirmación con los datos recopilados."""
        # Construir resumen según el tipo de análisis
        summary = "He recopilado la siguiente información para el análisis:\n\n"
        
        # Datos de descubrimiento
        if self.analysis_type == "team_synergy":
            summary += f"📊 **Tipo de Análisis**: Sinergia de Equipo\n"
            summary += f"🏢 **Empresa/Equipo**: {self.phases_data['discovery'].get('team_name', 'No especificado')}\n\n"
        elif self.analysis_type == "career_trajectory":
            summary += f"📊 **Tipo de Análisis**: Trayectoria Profesional\n"
            summary += f"👤 **Persona**: {self.phases_data['discovery'].get('person_name', 'No especificado')}\n\n"
        elif self.analysis_type == "cultural_fit":
            summary += f"📊 **Tipo de Análisis**: Compatibilidad Cultural\n"
            summary += f"👤 **Persona**: {self.phases_data['discovery'].get('person_name', 'No especificado')}\n\n"
        elif self.analysis_type == "retention":
            summary += f"📊 **Tipo de Análisis**: Predicción de Retención\n"
            summary += f"👤 **Persona**: {self.phases_data['discovery'].get('person_name', 'No especificado')}\n\n"
        elif self.analysis_type == "360":
            summary += f"📊 **Tipo de Análisis**: Análisis Integral 360°\n"
            if self.target_person_id:
                summary += f"👤 **Persona**: {self.phases_data['discovery'].get('person_name', 'No especificado')}\n\n"
            else:
                summary += f"🏢 **Empresa/Equipo**: {self.phases_data['discovery'].get('team_name', 'No especificado')}\n\n"
                
        # Datos individuales si aplica
        if "individual_data" in self.phases_data and self.phases_data["individual_data"]:
            summary += "📋 **Datos Individuales**:\n"
            if "position_info" in self.phases_data["individual_data"]:
                summary += f"• Posición: {self.phases_data['individual_data']['position_info']}\n"
            if "skills" in self.phases_data["individual_data"]:
                summary += f"• Habilidades: {self.phases_data['individual_data']['skills']}\n"
            if "aspirations" in self.phases_data["individual_data"]:
                summary += f"• Aspiraciones: {self.phases_data['individual_data']['aspirations']}\n"
            if "values" in self.phases_data["individual_data"]:
                summary += f"• Valores: {self.phases_data['individual_data']['values']}\n"
            if "satisfaction_factors" in self.phases_data["individual_data"]:
                summary += f"• Factores de Satisfacción: {self.phases_data['individual_data']['satisfaction_factors']}\n"
            summary += "\n"
            
        # Datos de equipo si aplica
        if "team_dynamics" in self.phases_data and self.phases_data["team_dynamics"]:
            summary += "👥 **Dinámica de Equipo**:\n"
            if "interaction_description" in self.phases_data["team_dynamics"]:
                summary += f"• Interacción: {self.phases_data['team_dynamics']['interaction_description']}\n"
            if "composition" in self.phases_data["team_dynamics"]:
                summary += f"• Composición: {self.phases_data['team_dynamics']['composition']}\n"
            if "strengths_weaknesses" in self.phases_data["team_dynamics"]:
                summary += f"• Fortalezas/Debilidades: {self.phases_data['team_dynamics']['strengths_weaknesses']}\n"
            summary += "\n"
            
        # Datos culturales si aplica
        if "culture" in self.phases_data and self.phases_data["culture"]:
            summary += "🏛️ **Cultura Organizacional**:\n"
            if "org_culture_description" in self.phases_data["culture"]:
                summary += f"• Descripción: {self.phases_data['culture']['org_culture_description']}\n"
            if "declared_values" in self.phases_data["culture"]:
                summary += f"• Valores Declarados: {self.phases_data['culture']['declared_values']}\n"
            if "leadership_style" in self.phases_data["culture"]:
                summary += f"• Estilo de Liderazgo: {self.phases_data['culture']['leadership_style']}\n"
            summary += "\n"
            
        # Solicitar confirmación
        summary += "¿Es correcta esta información? Si es así, procederé a generar el análisis. Si no, por favor indícame qué aspectos necesito corregir."
        
        return summary
    
    async def _generate_team_synergy_analysis(self) -> str:
        """Genera un análisis de sinergia de equipo."""
        try:
            # En una implementación real, aquí usaríamos los datos recopilados
            # para generar un análisis completo con TeamSynergyAnalyzer
            team_members = self.target_team_ids
            business_unit = self.business_unit
            
            # Generar el análisis
            analysis_result = await self.team_synergy_analyzer.analyze_team_synergy(
                team_members=team_members,
                business_unit=business_unit
            )
            
            # Crear enlace al reporte
            report_url = f"/reports/team-synergy/{analysis_result.get('id', 'sample')}"
            
            # Crear respuesta con insights principales
            response = (
                "✅ **Análisis de Sinergia de Equipo Completado**\n\n"
                f"**Puntuación de Sinergia**: {analysis_result.get('synergy_score', 75)}/100\n"
                f"**Tamaño del Equipo**: {analysis_result.get('team_size', len(team_members))} miembros\n\n"
                
                "**Distribución de Personalidades**:\n"
            )
            
            # Añadir distribución de personalidades
            personality_analysis = analysis_result.get('personality_analysis', {})
            for personality, percentage in personality_analysis.get('distribution', {}).items():
                response += f"• {personality}: {percentage}%\n"
            
            response += "\n**Análisis de Habilidades**:\n"
            skills_analysis = analysis_result.get('skills_analysis', {})
            response += f"• Cobertura: {skills_analysis.get('coverage_score', 70)}/100\n"
            response += f"• Balance: {skills_analysis.get('balance_score', 65)}/100\n"
            
            # Añadir principales recomendaciones
            response += "\n**Principales Recomendaciones**:\n"
            for i, rec in enumerate(analysis_result.get('recommendations', [])[:3]):
                response += f"• {rec.get('title', f'Recomendación {i+1}')}\n"
                
            # Añadir enlace al reporte completo
            response += ("\n📊 Puedes ver el reporte completo con visualizaciones detalladas "
                        f"en el siguiente enlace: {report_url}\n\n")
            
            # Añadir oferta de propuesta comercial para más análisis
            response += (
                "💼 **¿Te gustaría recibir una propuesta comercial para realizar "
                "más análisis de sinergia de equipo en tu organización?** "
                "Podemos crear un programa personalizado para optimizar el rendimiento "
                "de tus equipos a través de análisis periódicos y recomendaciones específicas."
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generando análisis de sinergia de equipo: {str(e)}")
            return (
                "Lo siento, hubo un problema al generar el análisis de sinergia de equipo. "
                "Por favor, intenta nuevamente más tarde o contacta a nuestro equipo de soporte."
            )
    
    async def _generate_career_trajectory_analysis(self) -> str:
        """Genera un análisis de trayectoria profesional."""
        try:
            person_id = self.target_person_id
            time_horizon = 60  # 5 años
            
            # Recopilamos los datos relevantes del candidato
            person_data = self.phases_data.get('individual_data', {})
            skills_data = person_data.get('skills', {})
            experience_data = person_data.get('experience', [])
            education_data = person_data.get('education', [])
            achievements_data = person_data.get('achievements', [])
            
            # Primero intentamos usar el analizador centralizado si está disponible
            central_analysis_result = None
            try:
                # Preparar datos para el analizador centralizado
                analysis_data = {
                    'assessment_type': 'talent',
                    'candidate_id': str(person_id),
                    'skills': skills_data,
                    'experience': {
                        'roles': experience_data,
                        'total_years': sum(role.get('duration', 0) for role in experience_data),
                        'relevant_years': sum(role.get('duration', 0) for role in experience_data if role.get('relevant', True))
                    },
                    'education': education_data,
                    'achievements': achievements_data
                }
                
                # Instanciar y usar el analizador centralizado
                analyzer = TalentAnalyzer()
                central_analysis_result = analyzer.analyze(analysis_data, self.business_unit)
                
                if central_analysis_result and not central_analysis_result.get('status') == 'error':
                    logger.info(f"Análisis de talento realizado con analizador centralizado")
                else:
                    logger.warning(f"Fallback a análisis tradicional: {central_analysis_result.get('message', 'Error desconocido')}")
                    central_analysis_result = None
            except Exception as e:
                logger.error(f"Error usando analizador centralizado: {str(e)}. Fallback a análisis tradicional.")
                central_analysis_result = None
            
            # Si el analizador centralizado no está disponible o falla, usamos el tradicional
            if not central_analysis_result:
                # Generar el análisis con el TrajectoryAnalyzer tradicional
                analysis_result = await self.trajectory_analyzer.predict_optimal_path(
                    person_id=person_id,
                    time_horizon=time_horizon
                )
            else:
                # Mapear los resultados del analizador centralizado al formato esperado
                analysis_result = {
                    'id': central_analysis_result.get('candidate_id', 'sample'),
                    'current_position': next((role.get('role') for role in experience_data if role.get('is_current', False)), 'No especificada'),
                    'potential_score': int(central_analysis_result.get('growth_potential', {}).get('potential_score', 0.7) * 100),
                    'optimal_path': {
                        'positions': [
                            {'position': rec.get('role'), 'is_current': i == 0, 'start_month': i * 12}
                            for i, rec in enumerate([{'role': 'Posición Actual'}] + central_analysis_result.get('role_recommendations', []))
                        ]
                    },
                    'critical_skills': [
                        {'name': gap.get('skill'), 'current_level': int(gap.get('current_level', 0) * 100), 'required_level': int(gap.get('required_level', 0) * 100)}
                        for gap in central_analysis_result.get('skill_gaps', [])
                    ],
                    'financial_projection': {'growth_rate': 30}  # Valor por defecto
                }
            
            # Crear enlace al reporte
            report_url = f"/reports/career-trajectory/{analysis_result.get('id', 'sample')}"
            
            # Crear respuesta con insights principales
            response = (
                "✅ **Análisis de Trayectoria Profesional Completado**\n\n"
                f"**Posición Actual**: {analysis_result.get('current_position', 'No especificada')}\n"
                f"**Potencial de Desarrollo**: {analysis_result.get('potential_score', 80)}/100\n\n"
                
                "**Trayectoria Óptima**:\n"
            )
            
            # Añadir ruta óptima
            optimal_path = analysis_result.get('optimal_path', {})
            for i, position in enumerate(optimal_path.get('positions', [])):
                prefix = "[Actual] " if position.get('is_current', False) else f"[+{position.get('start_month', i*12)}m] "
                response += f"• {prefix}{position.get('position', f'Posición {i+1}')}\n"
            
            # Añadir habilidades críticas
            response += "\n**Habilidades Críticas a Desarrollar**:\n"
            for i, skill in enumerate(analysis_result.get('critical_skills', [])[:3]):
                response += f"• {skill.get('name', f'Habilidad {i+1}')} ({skill.get('current_level', 50)} → {skill.get('required_level', 70)})\n"
                
            # Añadir proyección financiera
            financial = analysis_result.get('financial_projection', {})
            response += "\n**Proyección Financiera**:\n"
            response += f"• Crecimiento Proyectado: +{financial.get('growth_rate', 30)}%\n"
                
            # Añadir enlace al reporte completo
            response += ("\n📊 Puedes ver el reporte completo con visualizaciones detalladas "
                        f"en el siguiente enlace: {report_url}\n\n")
            
            # Añadir oferta de propuesta comercial para más análisis
            response += (
                "💼 **¿Te gustaría recibir una propuesta comercial para realizar "
                "más análisis de trayectoria profesional en tu organización?** "
                "Podemos crear un programa personalizado para optimizar el desarrollo "
                "de talento a través de análisis periódicos y planes de carrera específicos."
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generando análisis de trayectoria profesional: {str(e)}")
            return (
                "Lo siento, hubo un problema al generar el análisis de trayectoria profesional. "
                "Por favor, intenta nuevamente o contacta a nuestro equipo de soporte."
            )

    async def _generate_cultural_fit_analysis(self) -> str:
        """Genera un análisis de compatibilidad cultural enriquecido con el test cultural personalizado."""
        try:
            # ... (rest of the code remains the same)
            # Importamos el módulo de test cultural
            from app.ats.chatbot.workflow.cultural_fit_test import analyze_cultural_fit_responses, save_cultural_profile
            
            person_id = self.target_person_id
            company_id = self.target_company_id or 1  # ID por defecto si no se especificó
            business_unit = self.business_unit
            
            # Verificamos si la persona ya tiene un perfil cultural guardado
            has_profile = False
            profile_data = {}
            
            try:
                # Intentamos obtener el perfil cultural existente
                from app.models import Person, PersonCulturalProfile
                from asgiref.sync import sync_to_async
                
                # Verificar si existe perfil previo
                person = await sync_to_async(Person.objects.get)(id=person_id)
                has_profile = await sync_to_async(lambda: hasattr(person, 'cultural_profile'))()
                
                if has_profile:
                    # Obtener datos del perfil
                    cultural_profile = await sync_to_async(lambda: person.cultural_profile)()
                    profile_data = await sync_to_async(lambda: getattr(cultural_profile, 'full_profile_data', {}))() or {}
            except Exception as e:
                logger.error(f"Error verificando perfil cultural: {e}", exc_info=True)
        
            # Si no tiene perfil o estamos haciendo un nuevo análisis, usamos el test cultural
            if not has_profile or self.context.get('refresh_analysis', False):
                # En un escenario real, estas respuestas vendrían de interacciones previas con el usuario
                # Aquí simulamos respuestas para las dimensiones culturales
                # Valores del 1 al 5 para cada dimensión
                responses = {
                    'values': [4, 5, 4],  # Valores altos en transparencia, innovación, colaboración
                    'motivators': [3, 4, 5],  # Motivación media-alta en autonomía, reconocimiento e impacto
                    'interests': [4, 5],  # Alto interés en resolver problemas y aprender
                    'work_style': [3, 4],  # Preferencia media-alta por estructura e independencia
                    'social_impact': [4, 5, 5],  # Alta orientación al impacto social
                    'generational_values': [4, 5, 4]  # Alta preferencia por comunicación digital, flexibilidad y propósito
                }
                
                # Analizar respuestas
                profile_data = await analyze_cultural_fit_responses(responses, business_unit)
                
                # Guardar perfil cultural
                await save_cultural_profile(person_id, profile_data)
            
            # Generar análisis basado en el perfil cultural
            # Primero generar el análisis estándar con nuestro analizador existente
            base_analysis_result = await self.cultural_fit_analyzer.analyze_cultural_fit(
                person_id=person_id,
                company_id=company_id,
                business_unit=business_unit
            )
            
            # Combinar con los datos del perfil cultural enriquecido
            analysis_result = {**base_analysis_result}
            
            # Actualizar o añadir datos del perfil cultural
            if profile_data:
                # Actualizamos la puntuación de alineación
                if 'compatibility' in profile_data and business_unit in profile_data['compatibility']:
                    analysis_result['alignment_score'] = profile_data['compatibility'][business_unit]
                elif 'compatibility' in profile_data and 'general' in profile_data['compatibility']:
                    analysis_result['alignment_score'] = profile_data['compatibility']['general']
                
                # Nivel de compatibilidad
                score = analysis_result.get('alignment_score', 0)
                if score >= 85:
                    analysis_result['alignment_level'] = 'Excelente'
                elif score >= 70:
                    analysis_result['alignment_level'] = 'Muy bueno'
                elif score >= 50:
                    analysis_result['alignment_level'] = 'Bueno'
                elif score >= 30:
                    analysis_result['alignment_level'] = 'Regular'
                else:
                    analysis_result['alignment_level'] = 'Bajo'
                
                # Añadir fortalezas como valores compartidos
                if 'strengths' in profile_data:
                    values_analysis = analysis_result.get('values_analysis', {})
                    values_analysis['common_values'] = profile_data['strengths']
                    analysis_result['values_analysis'] = values_analysis
                
                # Añadir dimensiones culturales
                if 'scores' in profile_data:
                    cultural_dimensions = {}
                    for dimension, score in profile_data['scores'].items():
                        # Convertir a escala 0-100
                        cultural_dimensions[dimension.replace('_', ' ').title()] = score * 20
                    analysis_result['cultural_dimensions'] = cultural_dimensions
                
                # Añadir recomendaciones
                if 'recommendations' in profile_data:
                    analysis_result['recommendations'] = [
                        {'action': rec} for rec in profile_data['recommendations']
                    ]
        
            # Crear enlace al reporte
            report_url = f"/reports/cultural-fit/{analysis_result.get('id', 'sample')}"
            
            # Crear respuesta con insights principales, enfocada en valores de Grupo huntRED®: Apoyo, Solidaridad, Sinergia
            response = (
                "✅ **Análisis de Compatibilidad Cultural Integral**\n\n"
                f"**Puntuación de Compatibilidad**: {analysis_result.get('alignment_score', 78)}/100\n"
                f"**Nivel de Compatibilidad**: {analysis_result.get('alignment_level', 'Bueno')}\n\n"
                
                "**Fortalezas y Valores Compartidos**:\n"
            )
            
            # Añadir valores compartidos
            values_analysis = analysis_result.get('values_analysis', {})
            for value in values_analysis.get('common_values', ['Innovación', 'Colaboración']):
                response += f"• {value}\n"
            
            # Añadir dimensiones culturales con enfoque holístico
            response += "\n**Dimensiones de Compatibilidad Cultural**:\n"
            dimensions = analysis_result.get('cultural_dimensions', {})
            dimension_items = list(dimensions.items())[:5]  # Mostrar hasta 5 dimensiones
            for dimension, score in dimension_items:
                response += f"• {dimension}: {score:.1f}/100\n"
                
            # Añadir recomendaciones para mejorar la compatibilidad
            response += "\n**Recomendaciones Personalizadas**:\n"
            for i, rec in enumerate(analysis_result.get('recommendations', [])[:3]):
                response += f"• {rec.get('action', f'Recomendación {i+1}')}\n"
                
            # Añadir enlace al reporte completo
            response += ("\n📊 Puedes ver el reporte completo con visualizaciones detalladas "
                        f"en el siguiente enlace: {report_url}\n\n")
            
            # Añadir oferta de propuesta comercial para más análisis, destacando los valores de huntRED®
            response += (
                "💼 **¿Te gustaría recibir una propuesta comercial para realizar "
                "un análisis de compatibilidad cultural 360° en tu organización?** \n\n"
                "Con nuestro enfoque integral basado en Apoyo, Solidaridad y Sinergia, "
                "creamos programas personalizados para optimizar el fit cultural, "
                "potenciar equipos de alto rendimiento y mejorar la retención de talento clave."
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generando análisis de compatibilidad cultural: {str(e)}")
            return (
                "Lo siento, hubo un problema al generar el análisis de compatibilidad cultural. "
                "Por favor, intenta nuevamente más tarde o contacta a nuestro equipo de soporte."
            )
    
    async def _generate_retention_analysis(self) -> str:
        """Genera un análisis de riesgo de retención."""
        try:
            # En una implementación real, aquí usaríamos los datos recopilados
            # para generar un análisis completo con RetentionPredictor
            person_id = self.target_person_id
            business_unit = self.business_unit
            
            # Generar el análisis
            analysis_result = await self.retention_predictor.analyze_retention_risk(
                person_id=person_id,
                business_unit=business_unit
            )
            
            # Generar plan de intervención
            intervention_plan = await self.intervention_system.generate_intervention_plan(
                person_id=person_id,
                causal_factors=analysis_result.get('causal_factors', [])
            )
            
            # Crear enlace al reporte
            report_url = f"/reports/retention/{analysis_result.get('id', 'sample')}"
            
            # Crear respuesta con insights principales
            response = (
                "✅ **Análisis de Riesgo de Retención Completado**\n\n"
                f"**Puntuación de Riesgo**: {analysis_result.get('risk_score', 65)}/100\n"
                f"**Nivel de Riesgo**: {analysis_result.get('risk_level', 'medium').title()}\n\n"
                
                "**Factores Causales Principales**:\n"
            )
            
            # Añadir factores causales
            causal_factors = analysis_result.get('causal_factors', [])
            for factor in causal_factors[:3]:
                factor_name = factor.get('factor', 'unknown').replace('_', ' ').title()
                trend = factor.get('trend', 'stable')
                trend_icon = "📉" if trend == 'declining' else "📈" if trend == 'improving' else "➖"
                response += f"• {factor_name}: {factor.get('score', 50)}/100 {trend_icon}\n"
            
            # Añadir recomendaciones del plan de intervención
            response += "\n**Plan de Intervención Recomendado**:\n"
            interventions = intervention_plan.get('interventions', [])
            for intervention in interventions[:2]:
                response += f"• Para {intervention.get('factor_label', 'mejorar retención')}:\n"
                for action in intervention.get('actions', [])[:2]:
                    response += f"  - {action.get('action', 'Acción recomendada')}\n"
                    
            # Añadir métricas de éxito
            response += "\n**Métricas de Éxito**:\n"
            for metric in intervention_plan.get('success_metrics', [])[:3]:
                response += f"• {metric}\n"
                
            # Añadir enlace al reporte completo
            response += ("\n📊 Puedes ver el reporte completo con visualizaciones detalladas "
                        f"en el siguiente enlace: {report_url}\n\n")
            
            # Añadir oferta de propuesta comercial para más análisis
            response += (
                "💼 **¿Te gustaría recibir una propuesta comercial para implementar "
                "un programa de retención de talento en tu organización?** "
                "Podemos crear un sistema personalizado para identificar riesgos "
                "de rotación y generar planes de intervención efectivos."
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generando análisis de riesgo de retención: {str(e)}")
            return (
                "Lo siento, hubo un problema al generar el análisis de riesgo de retención. "
                "Por favor, intenta nuevamente más tarde o contacta a nuestro equipo de soporte."
            )
    
    async def _generate_360_analysis(self) -> str:
        """Genera un análisis integral 360° con formato visual mejorado."""
        try:
            # Determinar si es análisis individual o de equipo
            if self.target_person_id:
                # Análisis individual 360°
                person_id = self.target_person_id
                business_unit = self.business_unit
                
                # Generar los diferentes análisis
                trajectory_result = await self.trajectory_analyzer.predict_optimal_path(
                    person_id=person_id,
                    time_horizon=60
                )
                
                retention_result = await self.retention_predictor.analyze_retention_risk(
                    person_id=person_id,
                    business_unit=business_unit
                )
                
                learning_result = await self.learning_engine.generate_learning_sequence(
                    person_id=person_id,
                    context='career_development'
                )
                
                mentor_result = await self.mentor_matcher.find_optimal_mentors(
                    person_id=person_id,
                    limit=3
                )
                
                # Crear respuesta con formato visual mejorado
                response = "🎯 *Análisis Integral de Talento 360°*\n\n"
                
                # Información básica
                response += "👤 *Información del Candidato*\n"
                response += f"• Nombre: {self.phases_data['discovery'].get('person_name', 'No especificado')}\n"
                response += f"• Posición Actual: {trajectory_result.get('current_position', 'No especificada')}\n"
                response += f"• Unidad de Negocio: {business_unit}\n\n"
                
                # Resumen Ejecutivo
                response += "📊 *Resumen Ejecutivo*\n"
                potential_score = trajectory_result.get('potential_score', 80)
                risk_score = retention_result.get('risk_score', 65)
                risk_level = retention_result.get('risk_level', 'medium').title()
                
                # Barras de progreso visuales
                potential_progress = "🟢" * int(potential_score/20) + "⚪" * (5 - int(potential_score/20))
                risk_progress = "🔴" * int(risk_score/20) + "⚪" * (5 - int(risk_score/20))
                
                response += f"• Potencial de Desarrollo: {potential_progress} {potential_score}/100\n"
                response += f"• Riesgo de Rotación: {risk_progress} {risk_score}/100 ({risk_level})\n"
                response += f"• Compatibilidad Cultural: {'🟢' * 3 + '⚪' * 2} 75/100\n\n"
                
                # Trayectoria Profesional
                response += "🎯 *Trayectoria Profesional*\n"
                optimal_path = trajectory_result.get('optimal_path', {})
                response += f"• Próxima posición recomendada: {optimal_path.get('next_position', 'No especificada')}\n"
                response += f"• Timeframe estimado: {optimal_path.get('timeframe', 18)} meses\n"
                response += f"• Habilidades clave a desarrollar: {', '.join(optimal_path.get('key_skills', ['No especificadas']))}\n\n"
                
                # Factores de Retención
                response += "🔍 *Factores de Riesgo de Rotación*\n"
                causal_factors = retention_result.get('causal_factors', [])
                for factor in causal_factors[:3]:
                    factor_name = factor.get('factor', 'unknown').replace('_', ' ').title()
                    factor_score = factor.get('score', 50)
                    factor_progress = "🔴" * int(factor_score/20) + "⚪" * (5 - int(factor_score/20))
                    response += f"• {factor_name}: {factor_progress} {factor_score}/100\n"
                response += "\n"
                
                # Plan de Aprendizaje
                response += "📚 *Plan de Aprendizaje Personalizado*\n"
                learning_modules = learning_result.get('learning_modules', [])
                for module in learning_modules[:3]:
                    response += f"• {module.get('title', 'Módulo')}: {module.get('description', 'No especificado')}\n"
                response += "\n"
                
                # Mentores Recomendados
                response += "👥 *Mentores Recomendados*\n"
                mentors = mentor_result.get('mentors', [])
                for mentor in mentors:
                    response += f"• {mentor.get('name', 'Mentor')}: {mentor.get('expertise', 'No especificado')}\n"
                response += "\n"
                
                # Recomendaciones Finales
                response += "💡 *Recomendaciones Clave*\n"
                recommendations = [
                    "Mantener un plan de desarrollo personalizado",
                    "Establecer objetivos claros de carrera",
                    "Participar en programas de mentoría",
                    "Desarrollar habilidades identificadas como críticas"
                ]
                for rec in recommendations:
                    response += f"• {rec}\n"
                response += "\n"
                
                # Próximos Pasos
                response += "🚀 *Próximos Pasos*\n"
                response += "1. Revisar y validar el plan de desarrollo\n"
                response += "2. Establecer reuniones con mentores recomendados\n"
                response += "3. Iniciar los módulos de aprendizaje prioritarios\n"
                response += "4. Programar seguimiento en 3 meses\n\n"
                
                response += "¿Te gustaría profundizar en algún aspecto específico del análisis?"
                
                return response
                
            else:
                # Análisis de equipo
                team_ids = self.target_team_ids
                team_result = await self.team_synergy_analyzer.analyze_team_synergy(team_ids)
                
                response = "👥 *Análisis Integral de Equipo 360°*\n\n"
                
                # Información del Equipo
                response += "📋 *Información del Equipo*\n"
                response += f"• Nombre: {self.phases_data['discovery'].get('team_name', 'No especificado')}\n"
                response += f"• Tamaño: {team_result.get('team_size', len(team_ids))} miembros\n"
                response += f"• Unidad de Negocio: {self.business_unit}\n\n"
                
                # Resumen Ejecutivo
                response += "📊 *Resumen Ejecutivo*\n"
                synergy_score = team_result.get('synergy_score', 75)
                skills_coverage = team_result.get('skills_analysis', {}).get('coverage_score', 70)
                diversity_score = team_result.get('generation_analysis', {}).get('diversity_score', 65)
                
                # Barras de progreso visuales
                synergy_progress = "🟢" * int(synergy_score/20) + "⚪" * (5 - int(synergy_score/20))
                skills_progress = "🟢" * int(skills_coverage/20) + "⚪" * (5 - int(skills_coverage/20))
                diversity_progress = "🟢" * int(diversity_score/20) + "⚪" * (5 - int(diversity_score/20))
                
                response += f"• Sinergia de Equipo: {synergy_progress} {synergy_score}/100\n"
                response += f"• Cobertura de Habilidades: {skills_progress} {skills_coverage}/100\n"
                response += f"• Diversidad Generacional: {diversity_progress} {diversity_score}/100\n\n"
                
                # Composición del Equipo
                response += "👥 *Composición del Equipo*\n"
                personality_analysis = team_result.get('personality_analysis', {})
                response += f"• Personalidad Dominante: {personality_analysis.get('dominant_personality', 'Analítico')}\n"
                response += f"• Diversidad de Personalidades: {personality_analysis.get('diversity_score', 68)}/100\n"
                response += f"• Balance de Roles: {personality_analysis.get('role_balance', 'Bueno')}\n\n"
                
                # Análisis de Habilidades
                response += "🎯 *Análisis de Habilidades*\n"
                skills_analysis = team_result.get('skills_analysis', {})
                response += f"• Cobertura: {skills_analysis.get('coverage_score', 70)}/100\n"
                response += f"• Balance: {skills_analysis.get('balance_score', 65)}/100\n"
                response += f"• Habilidades Críticas: {', '.join(skills_analysis.get('critical_skills', ['No especificadas']))}\n\n"
                
                # Brechas y Oportunidades
                response += "📈 *Brechas y Oportunidades*\n"
                for gap in skills_analysis.get('skill_gaps', [])[:3]:
                    response += f"• {gap}\n"
                response += "\n"
                
                # Recomendaciones
                response += "💡 *Recomendaciones para el Equipo*\n"
                recommendations = [
                    "Implementar programa de desarrollo de habilidades críticas",
                    "Fomentar la diversidad de pensamiento",
                    "Establecer objetivos de equipo claros",
                    "Mejorar la comunicación intergeneracional"
                ]
                for rec in recommendations:
                    response += f"• {rec}\n"
                response += "\n"
                
                # Próximos Pasos
                response += "🚀 *Próximos Pasos*\n"
                response += "1. Revisar y validar el análisis con el equipo\n"
                response += "2. Establecer plan de acción para cerrar brechas\n"
                response += "3. Implementar programa de desarrollo\n"
                response += "4. Programar seguimiento en 3 meses\n\n"
                
                response += "¿Te gustaría profundizar en algún aspecto específico del análisis del equipo?"
                
                return response
                
        except Exception as e:
            logger.error(f"Error generando análisis 360°: {str(e)}")
            return "Lo siento, hubo un error al generar el análisis 360°. Por favor, intenta nuevamente."
    
    def _reset_workflow(self):
        """Restablece el estado del workflow para un nuevo análisis."""
        self.analysis_type = None
        self.target_person_id = None
        self.target_team_ids = []
        self.target_company_id = None
        self.discovery_complete = False
        self.data_collection_complete = False
        self.current_phase = "discovery"
        self.phases_data = {
            "discovery": {},
            "individual_data": {},
            "team_dynamics": {},
            "culture": {},
            "confirmation": {}
        }
