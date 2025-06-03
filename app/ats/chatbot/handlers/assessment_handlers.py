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


class AssessmentFactory:
    """Factory for creating assessment handlers"""
    
    @classmethod
    async def create_handler(cls, assessment_type: str, user_id: str, 
                           business_unit: BusinessUnit, context: Dict[str, Any] = None):
        """Create an assessment handler for the specified type"""
        handlers = {
            "cultural_fit": CulturalFitHandler,
            "professional_dna": ProfessionalDNAWorkflow,  # Implement these handlers similarly
            "personality": PersonalityWorkflow,  # Implement these handlers similarly
        }
        
        handler_class = handlers.get(assessment_type)
        if not handler_class:
            raise ValueError(f"No handler found for assessment type: {assessment_type}")
        
        return handler_class(user_id, business_unit, context or {})
