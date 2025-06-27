"""
Assessment Handlers for the Chatbot

This module contains handlers for different types of assessments in the system.
"""

import logging
from typing import Dict, Any, Optional
from asgiref.sync import sync_to_async

from app.models import BusinessUnit, Person
from app.ats.chatbot.workflow.assessments.cultural.cultural_fit_workflow import CulturalFitWorkflow
from app.ats.chatbot.workflow.assessments.professional_dna.workflow import ProfessionalDNAWorkflow
from app.ats.chatbot.workflow.assessments.personality.workflow import PersonalityWorkflow
from app.ats.chatbot.workflow.assessments.nom35.nom35_questions import NOM35_GUIA_II, NOM35_GUIA_III, NOM35_OPTIONS, NOM35_OPTIONS_WHATSAPP
from app.ats.chatbot.workflow.assessments.nom35.nom35_evaluation import NOM35EvaluationWorkflow

logger = logging.getLogger(__name__)

class AssessmentHandler:
    """Base class for assessment handlers"""
    
    def __init__(self, user_id: str, business_unit: BusinessUnit, context: Dict[str, Any] = None):
        self.user_id = user_id
        self.business_unit = business_unit
        self.context = context or {}
    
    async def start(self):
        """Start the assessment"""
        raise NotImplementedError("Subclasses must implement start method")
    
    async def process_response(self, user_input: str):
        """Process user response to assessment questions"""
        raise NotImplementedError("Subclasses must implement process_response method")
    
    async def get_results(self):
        """Get assessment results"""
        raise NotImplementedError("Subclasses must implement get_results method")


class CulturalFitHandler(AssessmentHandler):
    """Handler for Cultural Fit Assessment"""
    
    def __init__(self, user_id: str, business_unit: BusinessUnit, context: Dict[str, Any] = None):
        super().__init__(user_id, business_unit, context)
        self.workflow = None
    
    async def start(self):
        """Start the cultural fit assessment"""
        try:
            # Get or create person
            person = await self._get_or_create_person()
            
            # Initialize workflow
            self.workflow = CulturalFitWorkflow()
            await self.workflow.initialize({
                "business_unit": self.business_unit.name,
                "person_id": str(person.id),
                "domain": self.context.get("domain", "general"),
                "target_entity_type": self.context.get("target_entity_type"),
                "target_entity_id": self.context.get("target_entity_id")
            })
            
            # Get first question
            return await self.workflow.get_next_question()
            
        except Exception as e:
            logger.error(f"Error starting cultural fit assessment: {str(e)}", exc_info=True)
            raise
    
    async def process_response(self, user_input: str):
        """Process user response to assessment questions"""
        if not self.workflow:
            await self.start()
            
        try:
            # Process the response and get next question or results
            result = await self.workflow.process_response(user_input)
            
            if self.workflow.is_complete():
                # Get and save results
                results = await self.workflow.get_results()
                await self._save_results(results)
                return {"status": "completed", "results": results}
            else:
                # Get next question
                next_question = await self.workflow.get_next_question()
                return {"status": "in_progress", "next_question": next_question}
                
        except Exception as e:
            logger.error(f"Error processing cultural fit response: {str(e)}", exc_info=True)
            raise
    
    async def get_results(self):
        """Get assessment results"""
        if not self.workflow:
            raise ValueError("Assessment not started")
            
        if not self.workflow.is_complete():
            raise ValueError("Assessment not completed")
            
        return await self.workflow.get_results()
    
    async def _get_or_create_person(self):
        """Get or create a person record for the user"""
        # This is a simplified example - adjust based on your actual Person model
        person, created = await Person.objects.aget_or_create(
            external_id=self.user_id,
            defaults={
                "name": self.context.get("name", ""),
                "email": self.context.get("email", ""),
                "phone": self.context.get("phone", ""),
            }
        )
        return person
    
    async def _save_results(self, results: Dict[str, Any]):
        """Save assessment results"""
        # Implement saving results to your database
        # This is a placeholder - implement based on your data model
        pass


class NOM35AssessmentHandler:
    """Handler para la evaluación NOM 35 con experiencia optimizada."""
    def __init__(self, user_id: str, business_unit: BusinessUnit, context: Dict[str, Any] = None):
        self.user_id = user_id
        self.business_unit = business_unit
        self.context = context or {}
        self.profile = self.context.get("profile", "employee")  # 'employee' o 'leader'
        self.channel = self.context.get("channel", "web")  # 'web' o 'whatsapp'
        self.guide = NOM35_GUIA_III if self.profile == "leader" else NOM35_GUIA_II
        self.options = NOM35_OPTIONS_WHATSAPP if self.channel == "whatsapp" else NOM35_OPTIONS
        self.total_questions = sum(len(section["questions"]) for section in self.guide)
        self.answers = []
        self.current_section = 0
        self.current_question = 0
        self.completed = False

    async def start(self):
        msg = (
            "Esta evaluación es obligatoria por la NOM-035 para cuidar tu salud mental y la de tu empresa. "
            "Debes completarla para obtener tu certificado. ¡Responde con sinceridad!"
        )
        return await self._next_question(intro=msg)

    async def process_response(self, user_input: str):
        # Convertir respuesta de texto a valor numérico
        value = self._parse_response(user_input)
        if value is None:
            return {"error": "Respuesta no válida. Por favor selecciona una opción válida."}
        
        # Guardar respuesta
        self.answers.append(value)
        # Avanzar pregunta
        self.current_question += 1
        # Si termina sección, avanzar sección
        if self.current_question >= len(self.guide[self.current_section]["questions"]):
            self.current_section += 1
            self.current_question = 0
        # Si termina todo
        if self.current_section >= len(self.guide):
            self.completed = True
            return await self._finish()
        # Siguiente pregunta
        return await self._next_question()

    def _parse_response(self, user_input: str) -> Optional[int]:
        """Convierte la respuesta del usuario a valor numérico"""
        user_input = user_input.lower().strip()
        
        # Buscar coincidencia en las opciones
        for option in self.options:
            if user_input in option["label"].lower() or str(option["value"]) == user_input:
                return option["value"]
        
        return None

    async def _next_question(self, intro: Optional[str] = None):
        section = self.guide[self.current_section]
        question = section["questions"][self.current_question]
        progress = int(100 * (len(self.answers) / self.total_questions))
        msg = f"{intro + '\n' if intro else ''}({progress}% completado)\nSección: {section['section']}\n{question['text']}"
        quick_replies = [opt["label"] for opt in self.options]
        return {"question": msg, "quick_replies": quick_replies}

    async def _finish(self):
        msg = (
            "¡Has completado la evaluación NOM 35! 🎉\n"
            "Tus respuestas han sido registradas y recibirás tu certificado y reporte de cumplimiento."
        )
        # Aquí puedes guardar las respuestas y disparar el flujo de scoring y reporte
        await self._save_results()
        return {"status": "completed", "message": msg}

    async def _save_results(self):
        """Guarda los resultados de la evaluación"""
        try:
            from app.ats.chatbot.workflow.assessments.nom35.models import AssessmentNOM35
            
            # Calcular score y nivel de riesgo
            total_score = sum(self.answers)
            risk_level = self._calculate_risk_level(total_score)
            
            # Guardar en base de datos
            assessment = AssessmentNOM35(
                person_id=self.user_id,
                business_unit=self.business_unit,
                responses={"answers": self.answers},
                score=total_score,
                risk_level=risk_level
            )
            await sync_to_async(assessment.save)()
            
        except Exception as e:
            logger.error(f"Error saving NOM35 results: {str(e)}")

    def _calculate_risk_level(self, total_score: int) -> str:
        """Calcula el nivel de riesgo basado en el score total"""
        if total_score <= 50:
            return "bajo"
        elif total_score <= 100:
            return "medio"
        else:
            return "alto"

    async def get_results(self):
        if not self.completed:
            raise ValueError("Assessment not completed")
        return {
            "answers": self.answers, 
            "score": sum(self.answers), 
            "risk_level": self._calculate_risk_level(sum(self.answers))
        }


class AssessmentFactory:
    """Factory for creating assessment handlers"""
    
    handlers = {
        "cultural_fit": CulturalFitHandler,
        "professional_dna": ProfessionalDNAWorkflow,  # Implement these handlers similarly
        "personality": PersonalityWorkflow,  # Implement these handlers similarly
        "nom35": NOM35AssessmentHandler,
    }
    
    @classmethod
    async def create_handler(cls, assessment_type: str, user_id: str, 
                           business_unit: BusinessUnit, context: Dict[str, Any] = None):
        """Create an assessment handler for the specified type"""
        handler_class = cls.handlers.get(assessment_type)
        if not handler_class:
            raise ValueError(f"No handler found for assessment type: {assessment_type}")
        
        return handler_class(user_id, business_unit, context or {})
