#!/usr/bin/env python3
# /home/pablo/app/com/chatbot/integrations/enhanced_document_processor.py
# 
# Procesador mejorado de documentos que integra NLP, LinkedIn y el sistema de parsing existente.

import os
import io
import re
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from asgiref.sync import sync_to_async

from app.ats.chatbot.utils import ChatbotUtils
get_nlp_processor = ChatbotUtils.get_nlp_processor
from app.ats.chatbot.components.metrics import chatbot_metrics
from app.ats.chatbot.components.events import workflow_event_manager
from app.ats.utils.parser import CVParser
from app.ats.utils.linkedin import LinkedInScraper
from app.models import (
    BusinessUnit, Person,
    Conversation, ChatMessage, Notification,
    Metric, WorkflowStatus, ChannelSettings
)
from app.ml.core.models.base import MatchmakingLearningSystem
from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage

# Configuramos el logger
logger = logging.getLogger('chatbot')

class EnhancedDocumentProcessor:
    """
    Procesador mejorado de documentos que integra:
    - Procesamiento de documentos (PDF, DOCX, etc.)
    - Análisis NLP avanzado
    - Integración con LinkedIn
    - Sistema de métricas y eventos
    """
    
    def __init__(self, user_id: str = None, business_unit_id: str = None):
        self.user_id = user_id
        self.business_unit_id = business_unit_id
        self.storage_path = getattr(settings, 'DOCUMENTS_STORAGE_PATH', 'media/documents/')
        self.max_file_size = getattr(settings, 'MAX_DOCUMENT_SIZE_MB', 10) * 1024 * 1024
        
        # Inicializamos los procesadores
        self.parser = CVParser(business_unit_id)
        self.nlp_processor = get_nlp_processor()
        self.linkedin_processor = LinkedInScraper()
        
        # Aseguramos que existe la carpeta de almacenamiento
        os.makedirs(self.storage_path, exist_ok=True)
        
    async def process_document(self, file_data: bytes, filename: str, mime_type: str) -> Dict[str, Any]:
        """
        Procesa un documento con todas las integraciones disponibles.
        """
        start_time = time.time()
        try:
            # Validación básica
            if not file_data:
                return {"success": False, "error": "No se recibieron datos del archivo"}
                
            if len(file_data) > self.max_file_size:
                return {"success": False, "error": f"El archivo excede el tamaño máximo permitido ({self.max_file_size/(1024*1024)}MB)"}
            
            # Guardamos el documento
            file_path = await self._save_document(file_data, filename)
            if not file_path:
                return {"success": False, "error": "Error al guardar el documento"}
            
            # Extraemos el texto
            text_content = await self._extract_text(file_path, mime_type)
            if not text_content:
                return {"success": False, "error": "No se pudo extraer texto del documento"}
            
            # Procesamos con NLP
            nlp_analysis = await self._process_with_nlp(text_content)
            
            # Procesamos con el parser existente
            parsed_data = await self.parser.parse(text_content)
            
            # Enriquecimiento con LinkedIn si hay URL
            if "linkedin_url" in parsed_data:
                linkedin_data = await self._enrich_with_linkedin(parsed_data["linkedin_url"])
                if linkedin_data:
                    parsed_data.update(linkedin_data)
            
            # Procesamos habilidades
            skills = await self._process_skills(nlp_analysis, parsed_data)
            parsed_data["skills"] = skills
            
            # Enriquecimiento con ML
            ml_insights = await self._enrich_with_ml(parsed_data)
            parsed_data["ml_insights"] = ml_insights
            
            # Registramos métricas
            processing_time = time.time() - start_time
            await self._track_metrics("document_processing", True, processing_time)
            
            # Publicamos evento
            await self._publish_event("document_processed", {
                "file_path": file_path,
                "doc_type": mime_type,
                "processing_time": processing_time,
                "ml_insights": ml_insights
            })
            
            return {
                "success": True,
                "file_path": file_path,
                "parsed_data": parsed_data,
                "nlp_analysis": nlp_analysis,
                "ml_insights": ml_insights,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error procesando documento: {str(e)}", exc_info=True)
            await self._track_metrics("document_processing", False, time.time() - start_time)
            return {"success": False, "error": f"Error al procesar el documento: {str(e)}"}
    
    async def _save_document(self, file_data: bytes, filename: str) -> str:
        """Guarda un documento en el almacenamiento configurado."""
        try:
            timestamp = int(time.time())
            safe_filename = re.sub(r'[^\w\.-]', '_', filename)
            unique_filename = f"doc_{timestamp}_{safe_filename}"
            
            user_path = f"user_{self.user_id}/" if self.user_id else ""
            relative_path = f"{self.storage_path}{user_path}{unique_filename}"
            
            saved_path = await sync_to_async(default_storage.save)(relative_path, ContentFile(file_data))
            logger.info(f"Documento guardado en: {saved_path}")
            
            return saved_path
        except Exception as e:
            logger.error(f"Error guardando documento: {str(e)}", exc_info=True)
            return ""
    
    async def _extract_text(self, file_path: str, mime_type: str) -> Optional[str]:
        """Extrae texto del documento según su tipo."""
        try:
            if mime_type == 'application/pdf':
                return await self.parser.extract_text_from_file(Path(file_path))
            elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return await self.parser.extract_text_from_file(Path(file_path))
            return None
        except Exception as e:
            logger.error(f"Error extrayendo texto: {str(e)}", exc_info=True)
            return None
    
    async def _process_with_nlp(self, text: str) -> Dict[str, Any]:
        """Procesa el texto con el sistema NLP."""
        try:
            if not self.nlp_processor:
                return {}
            
            analysis = await self.nlp_processor.analyze_text(text)
            await self._track_metrics("nlp_processing", True, 0)
            return analysis
        except Exception as e:
            logger.error(f"Error en procesamiento NLP: {str(e)}", exc_info=True)
            await self._track_metrics("nlp_processing", False, 0)
            return {}
    
    async def _enrich_with_linkedin(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
        """Enriquece los datos con información de LinkedIn."""
        try:
            if not linkedin_url:
                return None
                
            data = await self.linkedin_processor.scrape_profile(linkedin_url)
            await self._track_metrics("linkedin_enrichment", True, 0)
            return data
        except Exception as e:
            logger.error(f"Error en enriquecimiento LinkedIn: {str(e)}", exc_info=True)
            await self._track_metrics("linkedin_enrichment", False, 0)
            return None
    
    async def _process_skills(self, nlp_analysis: Dict, parsed_data: Dict) -> List[str]:
        """Procesa y combina habilidades de diferentes fuentes."""
        try:
            skills = set()
            
            # Habilidades del NLP
            if nlp_analysis and "skills" in nlp_analysis:
                skills.update(nlp_analysis["skills"])
            
            # Habilidades del parser
            if "skills" in parsed_data:
                skills.update(parsed_data["skills"])
            
            # Habilidades de LinkedIn
            if "skills" in parsed_data.get("linkedin_data", {}):
                skills.update(parsed_data["linkedin_data"]["skills"])
            
            return list(skills)
        except Exception as e:
            logger.error(f"Error procesando habilidades: {str(e)}", exc_info=True)
            return []
    
    async def _enrich_with_ml(self, parsed_data: Dict) -> Dict[str, Any]:
        """Enriquece los datos con insights del sistema ML."""
        try:
            ml_system = MatchmakingLearningSystem(business_unit=self.business_unit_id)
            
            # Extraemos características relevantes
            features = {
                "skills": parsed_data.get("skills", []),
                "experience": parsed_data.get("experience", []),
                "education": parsed_data.get("education", []),
                "personality_traits": parsed_data.get("personality_traits", {}),
                "salary_expectations": parsed_data.get("salary_expectations", {})
            }
            
            # Generamos insights
            insights = {
                "skill_recommendations": await self._get_skill_recommendations(features),
                "career_path": await self._analyze_career_path(features),
                "market_alignment": await self._analyze_market_alignment(features),
                "success_predictions": await self._predict_success_probability(features)
            }
            
            # Actualizamos métricas
            await self._track_metrics("ml_enrichment", True, 0)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error en enriquecimiento ML: {str(e)}", exc_info=True)
            await self._track_metrics("ml_enrichment", False, 0)
            return {}
    
    async def _get_skill_recommendations(self, features: Dict) -> List[Dict]:
        """Obtiene recomendaciones de habilidades basadas en el perfil."""
        try:
            ml_system = MatchmakingLearningSystem(business_unit=self.business_unit_id)
            return await ml_system.recommend_skill_improvements(features)
        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones de habilidades: {str(e)}", exc_info=True)
            return []
    
    async def _analyze_career_path(self, features: Dict) -> Dict:
        """Analiza posibles trayectorias profesionales."""
        try:
            ml_system = MatchmakingLearningSystem(business_unit=self.business_unit_id)
            return await ml_system.predict_transition(features)
        except Exception as e:
            logger.error(f"Error analizando trayectoria profesional: {str(e)}", exc_info=True)
            return {}
    
    async def _analyze_market_alignment(self, features: Dict) -> Dict:
        """Analiza la alineación con el mercado laboral."""
        try:
            ml_system = MatchmakingLearningSystem(business_unit=self.business_unit_id)
            return await ml_system.calculate_market_alignment(features)
        except Exception as e:
            logger.error(f"Error analizando alineación con el mercado: {str(e)}", exc_info=True)
            return {}
    
    async def _predict_success_probability(self, features: Dict) -> Dict:
        """Predice la probabilidad de éxito en diferentes roles."""
        try:
            ml_system = MatchmakingLearningSystem(business_unit=self.business_unit_id)
            return await ml_system.predict_all_active_matches(features)
        except Exception as e:
            logger.error(f"Error prediciendo probabilidad de éxito: {str(e)}", exc_info=True)
            return {}
    
    async def _track_metrics(self, step: str, success: bool, processing_time: float):
        """Registra métricas del procesamiento."""
        try:
            await chatbot_metrics.track_workflow_step(
                workflow_type="document_processing",
                step_name=step,
                success=success,
                processing_time=processing_time
            )
        except Exception as e:
            logger.error(f"Error registrando métricas: {str(e)}", exc_info=True)
    
    async def _publish_event(self, event_type: str, data: Dict):
        """Publica eventos del procesamiento."""
        try:
            await workflow_event_manager.publish(
                event_type=event_type,
                data={
                    "timestamp": time.time(),
                    "user_id": self.user_id,
                    "business_unit_id": self.business_unit_id,
                    **data
                }
            )
        except Exception as e:
            logger.error(f"Error publicando evento: {str(e)}", exc_info=True) 