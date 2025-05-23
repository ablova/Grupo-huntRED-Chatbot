# /home/pablo/app/com/chatbot/integrations/handlers.py
#
# Módulo de manejadores para el chatbot.
# Incluye funcionalidades para manejo de mensajes, gamificación, correo electrónico y más.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from app.com.chatbot.models.chat_state import ChatState
from app.com.chatbot.models.profile import Profile
from app.com.chatbot.integrations.services import MENU_OPTIONS_BY_BU, EVALUATIONS_MENU
from app.com.chatbot.integrations.services import MessageService

from app.com.chatbot.workflow.assessments.professional_dna import (
    ProfessionalDNAAnalysis,
    BusinessUnit,
    QuestionCategory,
    AnalysisType,
    GenerationalAnalysis
)
from app.com.chatbot.workflow.assessments.cultural import (
    CulturalFitWorkflow,
    CulturalAnalysis
)
from app.com.chatbot.workflow.assessments.talent import (
    TalentAnalysisWorkflow,
    TalentAnalysis
)
from app.com.chatbot.workflow.assessments.personality import (
    PersonalityAssessment,
    PersonalityAnalysis
)
from app.com.chatbot.workflow.assessments.generational import (
    GenerationalAnalysis,
    GenerationalPatterns,
    GenerationalInsights
)

from app.com.chatbot.workflow.reports.professional_dna import ProfessionalDNAReport
from app.com.chatbot.workflow.reports.cultural import CulturalReport
from app.com.chatbot.workflow.reports.talent import TalentReport
from app.com.chatbot.workflow.reports.personality import PersonalityReport
from app.com.chatbot.workflow.reports.generational import GenerationalReport

from app.com.chatbot.workflow.analysis.leadership import LeadershipAnalysis
from app.com.chatbot.workflow.analysis.innovation import InnovationAnalysis
from app.com.chatbot.workflow.analysis.communication import CommunicationAnalysis
from app.com.chatbot.workflow.analysis.resilience import ResilienceAnalysis
from app.com.chatbot.workflow.analysis.results import ResultsAnalysis

class MenuHandler:
    def __init__(self, service: MessageService):
        self.service = service
        self.logger = logging.getLogger(__name__)

    async def _handle_create_profile(self, platform: str, user_id: str) -> bool:
        """Maneja la creación inicial del perfil."""
        try:
            # Verificar si ya existe un perfil
            profile = await Profile.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()

            if profile:
                message = "👤 Ya tienes un perfil creado. ¿Qué deseas hacer?"
                buttons = [
                    {"title": "✏️ Editar Perfil", "payload": "editar_perfil"},
                    {"title": "👀 Ver Perfil", "payload": "ver_perfil"},
                    {"title": "📊 Ver Evaluaciones", "payload": "ver_evaluaciones"},
                    {"title": "🔙 Volver al Menú", "payload": "menu"}
                ]
                return await self.service.send_options(platform, user_id, message, buttons)

            # Iniciar proceso de creación de perfil
            message = "👤 *Creación de Perfil*\n\n"
            message += "Para brindarte la mejor experiencia, necesitamos crear tu perfil profesional.\n\n"
            message += "Este perfil nos ayudará a:\n"
            message += "• Personalizar tus evaluaciones\n"
            message += "• Recomendar oportunidades relevantes\n"
            message += "• Guiar tu desarrollo profesional\n\n"
            message += "¿Deseas comenzar con la creación de tu perfil?"

            buttons = [
                {"title": "✅ Comenzar", "payload": "start_profile_creation"},
                {"title": "❌ Más tarde", "payload": "menu"}
            ]

            # Actualizar estado del chat
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_profile_creation_confirmation"
                await chat_state.asave()

            return await self.service.send_options(platform, user_id, message, buttons)

        except Exception as e:
            self.logger.error(f"Error iniciando creación de perfil: {str(e)}")
            return False

    async def _handle_start_profile_creation(self, platform: str, user_id: str) -> bool:
        """Maneja el inicio del proceso de creación de perfil."""
        try:
            message = "👤 *Creación de Perfil*\n\n"
            message += "Por favor, proporciona la siguiente información:\n\n"
            message += "1️⃣ Nombre completo\n"
            message += "2️⃣ Correo electrónico\n"
            message += "3️⃣ Teléfono\n"
            message += "4️⃣ Ubicación\n"
            message += "5️⃣ Años de experiencia\n"
            message += "6️⃣ Educación\n"
            message += "7️⃣ Habilidades principales\n\n"
            message += "Escribe 'comenzar' para iniciar el proceso."

            # Actualizar estado del chat
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_profile_creation"
                await chat_state.asave()

            return await self.service.send_message(platform, user_id, message)

        except Exception as e:
            self.logger.error(f"Error iniciando proceso de creación de perfil: {str(e)}")
            return False

    async def _handle_edit_profile(self, platform: str, user_id: str) -> bool:
        """Maneja la edición del perfil existente."""
        try:
            profile = await Profile.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()

            if not profile:
                message = "❌ No tienes un perfil creado. ¿Deseas crear uno?"
                buttons = [
                    {"title": "📝 Crear Perfil", "payload": "crear_perfil"},
                    {"title": "❌ Cancelar", "payload": "menu"}
                ]
                return await self.service.send_options(platform, user_id, message, buttons)

            # Mostrar campos editables
            message = "✏️ *Editar Perfil*\n\nSelecciona el campo que deseas editar:\n\n"
            message += "1️⃣ Nombre completo\n"
            message += "2️⃣ Correo electrónico\n"
            message += "3️⃣ Teléfono\n"
            message += "4️⃣ Ubicación\n"
            message += "5️⃣ Años de experiencia\n"
            message += "6️⃣ Educación\n"
            message += "7️⃣ Habilidades principales\n\n"
            message += "Escribe el número del campo que deseas editar."

            # Actualizar estado del chat
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_profile_edit"
                await chat_state.asave()

            return await self.service.send_message(platform, user_id, message)

        except Exception as e:
            self.logger.error(f"Error iniciando edición de perfil: {str(e)}")
            return False

    async def _handle_view_profile(self, platform: str, user_id: str) -> bool:
        """Maneja la visualización del perfil."""
        try:
            profile = await Profile.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()

            if not profile:
                message = "❌ No tienes un perfil creado. ¿Deseas crear uno?"
                buttons = [
                    {"title": "📝 Crear Perfil", "payload": "crear_perfil"},
                    {"title": "❌ Cancelar", "payload": "menu"}
                ]
                return await self.service.send_options(platform, user_id, message, buttons)

            # Construir mensaje con información del perfil
            message = "👤 *Tu Perfil Profesional*\n\n"
            message += f"*Nombre:* {profile.name}\n"
            message += f"*Email:* {profile.email}\n"
            message += f"*Teléfono:* {profile.phone}\n"
            message += f"*Ubicación:* {profile.location}\n"
            message += f"*Experiencia:* {profile.experience} años\n"
            message += f"*Educación:* {profile.education}\n"
            message += f"*Habilidades:* {', '.join(profile.skills)}\n\n"
            
            # Agregar botones de acción
            buttons = [
                {"title": "✏️ Editar Perfil", "payload": "editar_perfil"},
                {"title": "📊 Ver Evaluaciones", "payload": "ver_evaluaciones"},
                {"title": "🔙 Volver al Menú", "payload": "menu"}
            ]

            return await self.service.send_options(platform, user_id, message, buttons)

        except Exception as e:
            self.logger.error(f"Error mostrando perfil: {str(e)}")
            return False

    async def handle_menu(self, platform: str, user_id: str, payload: str) -> bool:
        """Maneja las interacciones con el menú principal y submenús."""
        try:
            # Manejar navegación del menú principal
            if payload == "menu_prev":
                return await self._handle_menu_navigation(platform, user_id, "prev")
            elif payload == "menu_next":
                return await self._handle_menu_navigation(platform, user_id, "next")
            elif payload == "menu_search":
                return await self._handle_menu_search(platform, user_id)
            elif payload == "menu":
                return await self.service.send_menu(platform, user_id)

            # Verificar si es un submenú
            if payload.startswith("search_"):
                parent_payload = payload.replace("search_", "")
                return await self._handle_submenu_search(platform, user_id, parent_payload)

            # Obtener el menú actual del usuario
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()

            if not chat_state:
                self.logger.error(f"No se encontró ChatState para {user_id}")
                return False

            # Verificar si el payload corresponde a una opción principal
            bu_name = self.service.business_unit.name.lower()
            menu_options = MENU_OPTIONS_BY_BU.get(bu_name, [])
            
            for option in menu_options:
                if option["payload"] == payload:
                    # Si la opción tiene submenú, mostrarlo
                    if "submenu" in option:
                        return await self.service.send_submenu(platform, user_id, payload)
                    # Si no tiene submenú, procesar la acción directamente
                    return await self._handle_menu_action(platform, user_id, payload)

            # Si no se encontró en el menú principal, buscar en submenús
            for option in menu_options:
                if "submenu" in option:
                    for suboption in option["submenu"]:
                        if suboption["payload"] == payload:
                            return await self._handle_menu_action(platform, user_id, payload)

            self.logger.warning(f"Payload no reconocido: {payload}")
            return False

        except Exception as e:
            self.logger.error(f"Error manejando menú: {str(e)}")
            return False

    async def _handle_menu_navigation(self, platform: str, user_id: str, direction: str) -> bool:
        """Maneja la navegación entre páginas del menú."""
        try:
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()

            if not chat_state:
                return False

            # Obtener el menú actual
            current_page = chat_state.menu_page or 0
            bu_name = self.service.business_unit.name.lower()
            menu_options = MENU_OPTIONS_BY_BU.get(bu_name, [])
            
            # Calcular nueva página
            if direction == "prev":
                new_page = max(0, current_page - 1)
            else:  # next
                new_page = min(len(menu_options) - 1, current_page + 1)

            # Actualizar estado
            chat_state.menu_page = new_page
            await chat_state.asave()

            # Enviar menú actualizado
            return await self.service.send_menu(platform, user_id)

        except Exception as e:
            self.logger.error(f"Error en navegación de menú: {str(e)}")
            return False

    async def _handle_menu_search(self, platform: str, user_id: str) -> bool:
        """Maneja la búsqueda en el menú principal."""
        try:
            # Enviar mensaje solicitando término de búsqueda
            message = "🔍 *Búsqueda en Menú*\n\nPor favor, escribe el término que deseas buscar:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar término de búsqueda
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_menu_search"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error en búsqueda de menú: {str(e)}")
            return False

    async def _handle_submenu_search(self, platform: str, user_id: str, parent_payload: str) -> bool:
        """Maneja la búsqueda en un submenú específico."""
        try:
            # Enviar mensaje solicitando término de búsqueda
            message = f"🔍 *Búsqueda en Submenú*\n\nPor favor, escribe el término que deseas buscar:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar término de búsqueda
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = f"waiting_submenu_search_{parent_payload}"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error en búsqueda de submenú: {str(e)}")
            return False

    async def _handle_menu_action(self, platform: str, user_id: str, payload: str) -> bool:
        """Maneja la acción seleccionada en el menú o submenú."""
        try:
            # Mapeo de acciones específicas
            action_handlers = {
                "ver_perfil": self._handle_view_profile,
                "editar_perfil": self._handle_edit_profile,
                "ver_evaluaciones": self._handle_view_evaluations,
                "prueba_personalidad": self._handle_personality_test,
                "analisis_talento": self._handle_talent_analysis,
                "analisis_cultural": self._handle_cultural_analysis,
                "analisis_generacional": self._handle_generational_analysis,
                "analisis_motivacional": self._handle_motivational_analysis,
                "analisis_estilos": self._handle_work_style_analysis,
                "analisis_desarrollo": self._handle_professional_development,
                "analisis_adaptabilidad": self._handle_adaptability_analysis,
                "subir_cv": self._handle_upload_cv,
                "ver_cv": self._handle_view_cv,
                "editar_cv": self._handle_edit_cv,
                "buscar_vacantes": self._handle_search_jobs,
                "vacantes_recomendadas": self._handle_recommended_jobs,
                "mis_postulaciones": self._handle_my_applications,
                "nueva_entrevista": self._handle_schedule_interview,
                "ver_entrevistas": self._handle_view_interviews,
                "modificar_entrevista": self._handle_modify_interview,
                "neto_a_bruto": self._handle_net_to_gross,
                "bruto_a_neto": self._handle_gross_to_net,
                "chat_asesor": self._handle_chat_advisor,
                "agendar_cita": self._handle_schedule_appointment,
                "ver_mentores": self._handle_view_mentors,
                "agendar_sesion": self._handle_schedule_mentoring,
                "faq": self._handle_faq,
                "guias": self._handle_guides,
                "tutoriales": self._handle_tutorials
            }

            # Obtener el manejador específico
            handler = action_handlers.get(payload)
            if handler:
                return await handler(platform, user_id)
            
            self.logger.warning(f"No se encontró manejador para la acción: {payload}")
            return False

        except Exception as e:
            self.logger.error(f"Error manejando acción de menú: {str(e)}")
            return False

    # Implementación de manejadores específicos
    async def _handle_view_evaluations(self, platform: str, user_id: str) -> bool:
        """Maneja la visualización de evaluaciones disponibles."""
        try:
            message = "📊 *Evaluaciones Disponibles*\n\n"
            message += "Selecciona el tipo de evaluación que deseas realizar:\n\n"
            message += "1️⃣ Evaluación de Personalidad\n"
            message += "2️⃣ Evaluación de Talento\n"
            message += "3️⃣ Evaluación Cultural\n\n"
            message += "Cada evaluación te ayudará a conocerte mejor y potenciar tu desarrollo profesional."

            buttons = [
                {"title": "👤 Personalidad", "payload": "personality_test"},
                {"title": "💫 Talento", "payload": "talent_analysis"},
                {"title": "🌍 Cultural", "payload": "cultural_analysis"},
                {"title": "🔙 Volver", "payload": "menu"}
            ]

            return await self.service.send_options(platform, user_id, message, buttons)

        except Exception as e:
            self.logger.error(f"Error mostrando evaluaciones: {str(e)}")
            return False

    async def _handle_personality_test(self, platform: str, user_id: str) -> bool:
        """Maneja la evaluación de personalidad."""
        try:
            from app.com.chatbot.workflow.evaluaciones.personality_evaluation import PersonalityEvaluation
            
            # Obtener perfil del usuario
            profile = await Profile.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()

            if not profile:
                message = "❌ Necesitas tener un perfil creado para realizar la evaluación."
                buttons = [
                    {"title": "📝 Crear Perfil", "payload": "crear_perfil"},
                    {"title": "🔙 Volver", "payload": "ver_evaluaciones"}
                ]
                return await self.service.send_options(platform, user_id, message, buttons)

            # Iniciar evaluación
            evaluator = PersonalityEvaluation()
            message = "👤 *Evaluación de Personalidad*\n\n"
            message += "Esta evaluación analizará:\n"
            message += "• Liderazgo y toma de decisiones\n"
            message += "• Adaptabilidad y flexibilidad\n"
            message += "• Gestión y organización\n\n"
            message += "¿Deseas comenzar la evaluación?"

            buttons = [
                {"title": "✅ Comenzar", "payload": "start_personality_test"},
                {"title": "❌ Cancelar", "payload": "ver_evaluaciones"}
            ]

            return await self.service.send_options(platform, user_id, message, buttons)

        except Exception as e:
            self.logger.error(f"Error iniciando evaluación de personalidad: {str(e)}")
            return False

    async def _handle_talent_analysis(self, platform: str, user_id: str) -> bool:
        """Maneja la evaluación de talento."""
        try:
            from app.com.chatbot.workflow.evaluaciones.talent_evaluation import TalentEvaluation
            
            # Obtener perfil del usuario
            profile = await Profile.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()

            if not profile:
                message = "❌ Necesitas tener un perfil creado para realizar la evaluación."
                buttons = [
                    {"title": "📝 Crear Perfil", "payload": "crear_perfil"},
                    {"title": "🔙 Volver", "payload": "ver_evaluaciones"}
                ]
                return await self.service.send_options(platform, user_id, message, buttons)

            # Iniciar evaluación
            evaluator = TalentEvaluation()
            message = "💫 *Evaluación de Talento*\n\n"
            message += "Esta evaluación analizará:\n"
            message += "• Estrategia y visión\n"
            message += "• Innovación y creatividad\n"
            message += "• Habilidades técnicas\n\n"
            message += "¿Deseas comenzar la evaluación?"

            buttons = [
                {"title": "✅ Comenzar", "payload": "start_talent_analysis"},
                {"title": "❌ Cancelar", "payload": "ver_evaluaciones"}
            ]

            return await self.service.send_options(platform, user_id, message, buttons)

        except Exception as e:
            self.logger.error(f"Error iniciando evaluación de talento: {str(e)}")
            return False

    async def _handle_cultural_analysis(self, platform: str, user_id: str) -> bool:
        """Maneja la evaluación cultural."""
        try:
            from app.com.chatbot.workflow.evaluaciones.cultural_evaluation import CulturalEvaluation
            
            # Obtener perfil del usuario
            profile = await Profile.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()

            if not profile:
                message = "❌ Necesitas tener un perfil creado para realizar la evaluación."
                buttons = [
                    {"title": "📝 Crear Perfil", "payload": "crear_perfil"},
                    {"title": "🔙 Volver", "payload": "ver_evaluaciones"}
                ]
                return await self.service.send_options(platform, user_id, message, buttons)

            # Iniciar evaluación
            evaluator = CulturalEvaluation()
            message = "🌍 *Evaluación Cultural*\n\n"
            message += "Esta evaluación analizará:\n"
            message += "• Valores y principios\n"
            message += "• Adaptabilidad cultural\n"
            message += "• Comunicación intercultural\n\n"
            message += "¿Deseas comenzar la evaluación?"

            buttons = [
                {"title": "✅ Comenzar", "payload": "start_cultural_analysis"},
                {"title": "❌ Cancelar", "payload": "ver_evaluaciones"}
            ]

            return await self.service.send_options(platform, user_id, message, buttons)

        except Exception as e:
            self.logger.error(f"Error iniciando evaluación cultural: {str(e)}")
            return False

    async def _handle_generational_analysis(self, platform: str, user_id: str) -> bool:
        """Maneja el análisis generacional."""
        try:
            # Enviar mensaje indicando que se está realizando el análisis generacional
            message = "👨‍👩‍👧‍👦 *Análisis Generacional*\n\nPor favor, responde las siguientes preguntas:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar respuestas del análisis
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_generational_analysis"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error manejando análisis generacional: {str(e)}")
            return False

    async def _handle_motivational_analysis(self, platform: str, user_id: str) -> bool:
        """Maneja el análisis motivacional."""
        try:
            # Enviar mensaje indicando que se está realizando el análisis motivacional
            message = "🌟 *Análisis Motivacional*\n\nPor favor, responde las siguientes preguntas:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar respuestas del análisis
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_motivational_analysis"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error manejando análisis motivacional: {str(e)}")
            return False

    async def _handle_work_style_analysis(self, platform: str, user_id: str) -> bool:
        """Maneja el análisis de estilo de trabajo."""
        try:
            # Enviar mensaje indicando que se está realizando el análisis de estilo de trabajo
            message = "💼 *Análisis de Estilo de Trabajo*\n\nPor favor, responde las siguientes preguntas:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar respuestas del análisis
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_work_style_analysis"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error manejando análisis de estilo de trabajo: {str(e)}")
            return False

    async def _handle_professional_development(self, platform: str, user_id: str) -> bool:
        """Maneja el análisis de desarrollo profesional."""
        try:
            # Enviar mensaje indicando que se está realizando el análisis de desarrollo profesional
            message = "🌱 *Análisis de Desarrollo Profesional*\n\nPor favor, responde las siguientes preguntas:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar respuestas del análisis
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_professional_development"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error manejando análisis de desarrollo profesional: {str(e)}")
            return False

    async def _handle_adaptability_analysis(self, platform: str, user_id: str) -> bool:
        """Maneja el análisis de adaptabilidad."""
        try:
            # Enviar mensaje indicando que se está realizando el análisis de adaptabilidad
            message = "🌱 *Análisis de Adaptabilidad*\n\nPor favor, responde las siguientes preguntas:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar respuestas del análisis
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_adaptability_analysis"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error manejando análisis de adaptabilidad: {str(e)}")
            return False

    async def _handle_upload_cv(self, platform: str, user_id: str) -> bool:
        """Maneja la carga de CV."""
        try:
            # Enviar mensaje solicitando CV
            message = "📄 *Carga de CV*\n\nPor favor, sube tu CV en formato PDF o Word:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar CV
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_upload_cv"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error manejando carga de CV: {str(e)}")
            return False

    async def _handle_view_cv(self, platform: str, user_id: str) -> bool:
        """Maneja la visualización del CV."""
        try:
            # Obtener CV del usuario
            cv = await self.service.get_cv(user_id)

            if not cv:
                message = "❌ No tienes un CV registrado."
                return await self.service.send_message(platform, user_id, message)

            # Enviar CV
            return await self.service.send_file(platform, user_id, cv)

        except Exception as e:
            self.logger.error(f"Error mostrando CV: {str(e)}")
            return False

    async def _handle_edit_cv(self, platform: str, user_id: str) -> bool:
        """Maneja la edición del CV."""
        try:
            # Obtener CV del usuario
            cv = await self.service.get_cv(user_id)

            if not cv:
                message = "❌ No tienes un CV registrado. ¿Deseas crear uno?"
                buttons = [
                    {"title": "📝 Crear CV", "payload": "crear_cv"},
                    {"title": "❌ Cancelar", "payload": "menu"}
                ]
                return await self.service.send_options(platform, user_id, message, buttons)

            # Mostrar campos editables
            message = "✏️ *Editar CV*\n\nSelecciona el campo que deseas editar:\n\n"
            message += "1️⃣ Nombre del CV\n"
            message += "2️⃣ Descripción del CV\n"
            message += "3️⃣ Experiencia laboral\n"
            message += "4️⃣ Educación\n"
            message += "5️⃣ Habilidades\n\n"
            message += "Escribe el número del campo que deseas editar."

            # Actualizar estado del chat
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_edit_cv"
                await chat_state.asave()

            return await self.service.send_message(platform, user_id, message)

        except Exception as e:
            self.logger.error(f"Error iniciando edición de CV: {str(e)}")
            return False

    async def _handle_search_jobs(self, platform: str, user_id: str) -> bool:
        """Maneja la búsqueda de vacantes."""
        try:
            # Enviar mensaje solicitando término de búsqueda
            message = "🔍 *Búsqueda de Vacantes*\n\nPor favor, escribe el término que deseas buscar:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar término de búsqueda
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_job_search"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error en búsqueda de vacantes: {str(e)}")
            return False

    async def _handle_recommended_jobs(self, platform: str, user_id: str) -> bool:
        """Maneja la visualización de vacantes recomendadas."""
        try:
            # Obtener vacantes recomendadas
            jobs = await self.service.get_recommended_jobs(user_id)

            if not jobs:
                message = "❌ No hay vacantes recomendadas disponibles."
                return await self.service.send_message(platform, user_id, message)

            # Construir mensaje con información de las vacantes
            message = "📋 *Vacantes Recomendadas*\n\n"
            for job in jobs:
                message += f"*Título:* {job.title}\n"
                message += f"*Empresa:* {job.company}\n"
                message += f"*Ubicación:* {job.location}\n"
                message += f"*Fecha de publicación:* {job.date}\n\n"

            # Enviar mensaje
            return await self.service.send_message(platform, user_id, message)

        except Exception as e:
            self.logger.error(f"Error mostrando vacantes recomendadas: {str(e)}")
            return False

    async def _handle_my_applications(self, platform: str, user_id: str) -> bool:
        """Maneja la visualización de postulaciones."""
        try:
            # Obtener postulaciones del usuario
            applications = await self.service.get_applications(user_id)

            if not applications:
                message = "❌ No tienes postulaciones registradas."
                return await self.service.send_message(platform, user_id, message)

            # Construir mensaje con información de las postulaciones
            message = "📋 *Mis Postulaciones*\n\n"
            for application in applications:
                message += f"*Título:* {application.job.title}\n"
                message += f"*Empresa:* {application.job.company}\n"
                message += f"*Ubicación:* {application.job.location}\n"
                message += f"*Fecha de postulación:* {application.date}\n\n"

            # Enviar mensaje
            return await self.service.send_message(platform, user_id, message)

        except Exception as e:
            self.logger.error(f"Error mostrando postulaciones: {str(e)}")
            return False

    async def _handle_schedule_interview(self, platform: str, user_id: str) -> bool:
        """Maneja la programación de una entrevista."""
        try:
            # Enviar mensaje solicitando información de la entrevista
            message = "📅 *Programación de Entrevista*\n\nPor favor, proporciona la siguiente información:"
            message += "\n1️⃣ Fecha de la entrevista"
            message += "\n2️⃣ Hora de la entrevista"
            message += "\n3️⃣ Lugar de la entrevista"
            message += "\n4️⃣ Nombre del entrevistador"
            message += "\n5️⃣ Detalles adicionales"
            message += "\n\nEscribe 'comenzar' para iniciar el proceso."

            # Actualizar estado del chat
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_schedule_interview"
                await chat_state.asave()

            return await self.service.send_message(platform, user_id, message)

        except Exception as e:
            self.logger.error(f"Error manejando programación de entrevista: {str(e)}")
            return False

    async def _handle_view_interviews(self, platform: str, user_id: str) -> bool:
        """Maneja la visualización de entrevistas."""
        try:
            # Obtener entrevistas del usuario
            interviews = await self.service.get_interviews(user_id)

            if not interviews:
                message = "❌ No tienes entrevistas registradas."
                return await self.service.send_message(platform, user_id, message)

            # Construir mensaje con información de las entrevistas
            message = "📅 *Entrevistas*\n\n"
            for interview in interviews:
                message += f"*Título:* {interview.title}\n"
                message += f"*Fecha:* {interview.date}\n"
                message += f"*Lugar:* {interview.location}\n"
                message += f"*Entrevistador:* {interview.interviewer}\n\n"

            # Enviar mensaje
            return await self.service.send_message(platform, user_id, message)

        except Exception as e:
            self.logger.error(f"Error mostrando entrevistas: {str(e)}")
            return False

    async def _handle_modify_interview(self, platform: str, user_id: str) -> bool:
        """Maneja la modificación de una entrevista."""
        try:
            # Enviar mensaje solicitando información de la entrevista
            message = "📅 *Modificación de Entrevista*\n\nPor favor, proporciona la siguiente información:"
            message += "\n1️⃣ Nueva fecha de la entrevista"
            message += "\n2️⃣ Nueva hora de la entrevista"
            message += "\n3️⃣ Nuevo lugar de la entrevista"
            message += "\n4️⃣ Nuevo entrevistador"
            message += "\n5️⃣ Detalles adicionales"
            message += "\n\nEscribe 'comenzar' para iniciar el proceso."

            # Actualizar estado del chat
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_modify_interview"
                await chat_state.asave()

            return await self.service.send_message(platform, user_id, message)

        except Exception as e:
            self.logger.error(f"Error manejando modificación de entrevista: {str(e)}")
            return False

    async def _handle_net_to_gross(self, platform: str, user_id: str) -> bool:
        """Maneja la conversión de neto a bruto."""
        try:
            # Enviar mensaje solicitando información para la conversión
            message = "💰 *Conversión de Neto a Bruto*\n\nPor favor, proporciona la siguiente información:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar respuesta
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_net_to_gross"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error manejando conversión de neto a bruto: {str(e)}")
            return False

    async def _handle_gross_to_net(self, platform: str, user_id: str) -> bool:
        """Maneja la conversión de bruto a neto."""
        try:
            # Enviar mensaje solicitando información para la conversión
            message = "💰 *Conversión de Bruto a Neto*\n\nPor favor, proporciona la siguiente información:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar respuesta
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_gross_to_net"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error manejando conversión de bruto a neto: {str(e)}")
            return False

    async def _handle_chat_advisor(self, platform: str, user_id: str) -> bool:
        """Maneja la solicitud de chat con un asesor."""
        try:
            # Enviar mensaje solicitando información para el chat
            message = "💬 *Chat con Asesor*\n\nPor favor, escribe tu consulta:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar respuesta
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_chat_advisor"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error manejando chat con asesor: {str(e)}")
            return False

    async def _handle_schedule_appointment(self, platform: str, user_id: str) -> bool:
        """Maneja la programación de una cita."""
        try:
            # Enviar mensaje solicitando información de la cita
            message = "📅 *Programación de Cita*\n\nPor favor, proporciona la siguiente información:"
            message += "\n1️⃣ Fecha de la cita"
            message += "\n2️⃣ Hora de la cita"
            message += "\n3️⃣ Lugar de la cita"
            message += "\n4️⃣ Nombre del asesor"
            message += "\n5️⃣ Detalles adicionales"
            message += "\n\nEscribe 'comenzar' para iniciar el proceso."

            # Actualizar estado del chat
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_schedule_appointment"
                await chat_state.asave()

            return await self.service.send_message(platform, user_id, message)

        except Exception as e:
            self.logger.error(f"Error manejando programación de cita: {str(e)}")
            return False

    async def _handle_view_mentors(self, platform: str, user_id: str) -> bool:
        """Maneja la visualización de mentores."""
        try:
            # Obtener mentores del usuario
            mentors = await self.service.get_mentors(user_id)

            if not mentors:
                message = "❌ No tienes mentores registrados."
                return await self.service.send_message(platform, user_id, message)

            # Construir mensaje con información de los mentores
            message = "👨‍👩‍👧‍👦 *Mentores*\n\n"
            for mentor in mentors:
                message += f"*Nombre:* {mentor.name}\n"
                message += f"*Especialidad:* {mentor.specialty}\n"
                message += f"*Contacto:* {mentor.contact}\n\n"

            # Enviar mensaje
            return await self.service.send_message(platform, user_id, message)

        except Exception as e:
            self.logger.error(f"Error mostrando mentores: {str(e)}")
            return False

    async def _handle_schedule_mentoring(self, platform: str, user_id: str) -> bool:
        """Maneja la programación de una sesión de mentoría."""
        try:
            # Enviar mensaje solicitando información de la sesión de mentoría
            message = "📅 *Programación de Sesión de Mentoría*\n\nPor favor, proporciona la siguiente información:"
            message += "\n1️⃣ Fecha de la sesión"
            message += "\n2️⃣ Hora de la sesión"
            message += "\n3️⃣ Lugar de la sesión"
            message += "\n4️⃣ Nombre del mentor"
            message += "\n5️⃣ Detalles adicionales"
            message += "\n\nEscribe 'comenzar' para iniciar el proceso."

            # Actualizar estado del chat
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_schedule_mentoring"
                await chat_state.asave()

            return await self.service.send_message(platform, user_id, message)

        except Exception as e:
            self.logger.error(f"Error manejando programación de sesión de mentoría: {str(e)}")
            return False

    async def _handle_faq(self, platform: str, user_id: str) -> bool:
        """Maneja la solicitud de respuesta a preguntas frecuentes."""
        try:
            # Enviar mensaje solicitando pregunta
            message = "❓ *Pregunta Frecuente*\n\nPor favor, escribe tu pregunta:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar respuesta
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_faq"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error manejando solicitud de FAQ: {str(e)}")
            return False

    async def _handle_guides(self, platform: str, user_id: str) -> bool:
        """Maneja la solicitud de guías."""
        try:
            # Enviar mensaje solicitando guías
            message = "📚 *Guías*\n\nPor favor, selecciona el tema de interés:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar respuesta
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_guides"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error manejando solicitud de guías: {str(e)}")
            return False

    async def _handle_tutorials(self, platform: str, user_id: str) -> bool:
        """Maneja la solicitud de tutoriales."""
        try:
            # Enviar mensaje solicitando tutoriales
            message = "📚 *Tutoriales*\n\nPor favor, selecciona el tema de interés:"
            await self.service.send_message(platform, user_id, message)
            
            # Actualizar estado para esperar respuesta
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.service.business_unit
            ).afirst()
            
            if chat_state:
                chat_state.state = "waiting_tutorials"
                await chat_state.asave()
            
            return True

        except Exception as e:
            self.logger.error(f"Error manejando solicitud de tutoriales: {str(e)}")
            return False

class AssessmentHandler(ABC):
    @abstractmethod
    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa los datos del assessment"""
        pass

    @abstractmethod
    def get_questions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene las preguntas del assessment"""
        pass

    @abstractmethod
    def analyze_answers(self, answers: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza las respuestas del assessment"""
        pass

class ProfessionalDNAHandler(AssessmentHandler):
    def __init__(self):
        self.analysis = ProfessionalDNAAnalysis()

    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa los datos del ADN Profesional"""
        answers = data.get('answers', {})
        generation = context.get('generation', 'millennial')
        business_unit = context.get('business_unit', BusinessUnit.HUNTRED)
        
        results = self.analysis.analyze_answers(
            answers=answers,
            generation=generation,
            business_unit=business_unit
        )
        
        return {
            'results': results,
            'summary': self.analysis.get_analysis_summary(results)
        }

    def get_questions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene las preguntas del ADN Profesional"""
        if category:
            return self.analysis.get_questions_by_category(QuestionCategory(category))
        return self.analysis.get_all_questions()

    def analyze_answers(self, answers: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza las respuestas del ADN Profesional"""
        generation = context.get('generation', 'millennial')
        business_unit = context.get('business_unit', BusinessUnit.HUNTRED)
        
        return self.analysis.analyze_answers(
            answers=answers,
            generation=generation,
            business_unit=business_unit
        )

class CulturalFitHandler(AssessmentHandler):
    def __init__(self):
        self.workflow = CulturalFitWorkflow()

    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa los datos del Fit Cultural"""
        answers = data.get('answers', {})
        results = self.workflow.analyze_answers(answers)
        
        return {
            'results': results,
            'summary': self.workflow.get_summary(results)
        }

    def get_questions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene las preguntas del Fit Cultural"""
        return self.workflow.get_questions(category)

    def analyze_answers(self, answers: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza las respuestas del Fit Cultural"""
        return self.workflow.analyze_answers(answers)

class TalentAnalysisHandler(AssessmentHandler):
    def __init__(self):
        self.workflow = TalentAnalysisWorkflow()

    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa los datos del Análisis de Talento"""
        answers = data.get('answers', {})
        results = self.workflow.analyze_answers(answers)
        
        return {
            'results': results,
            'summary': self.workflow.get_summary(results)
        }

    def get_questions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene las preguntas del Análisis de Talento"""
        return self.workflow.get_questions(category)

    def analyze_answers(self, answers: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza las respuestas del Análisis de Talento"""
        return self.workflow.analyze_answers(answers)

class PersonalityAssessmentHandler(AssessmentHandler):
    def __init__(self):
        self.assessment = PersonalityAssessment()

    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa los datos de la Evaluación de Personalidad"""
        answers = data.get('answers', {})
        results = self.assessment.analyze_answers(answers)
        
        return {
            'results': results,
            'summary': self.assessment.get_summary(results)
        }

    def get_questions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene las preguntas de la Evaluación de Personalidad"""
        return self.assessment.get_questions(category)

    def analyze_answers(self, answers: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza las respuestas de la Evaluación de Personalidad"""
        return self.assessment.analyze_answers(answers) 