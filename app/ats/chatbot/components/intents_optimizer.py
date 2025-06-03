import asyncio
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache
import re
from app.ats.chatbot.components.channel_config import ChannelConfig
from app.ats.chatbot.components.metrics import chatbot_metrics

logger = logging.getLogger(__name__)

class IntentOptimizer:
    @staticmethod
    @lru_cache(maxsize=128)
    def compile_patterns(patterns: List[str]) -> List[re.Pattern]:
        """Compila y cachea las expresiones regulares de los patterns."""
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

    @staticmethod
    def optimize_patterns(patterns: List[str]) -> List[str]:
        """Optimiza los patterns eliminando redundancias y combinando similares."""
        optimized = []
        seen = set()
        
        for pattern in patterns:
            # Eliminar redundancias
            if pattern.lower() in seen:
                continue
                
            # Simplificar patrones comunes
            if "\b" in pattern:
                pattern = pattern.replace("\b", "")
                
            # Combinar patrones similares
            if "|" in pattern:
                parts = pattern.split("|")
                parts = [p.strip() for p in parts if p.strip()]
                if len(parts) > 1:
                    pattern = "|".join(sorted(parts))
            
            optimized.append(pattern)
            seen.add(pattern.lower())
        
        return optimized

    @staticmethod
    async def process_intent(
        intent: str,
        platform: str,
        user_id: str,
        chat_state: Any,
        business_unit: Any,
        text: str
    ) -> Dict[str, Any]:
        """Procesa un intent de manera optimizada."""
        try:
            # Validar canal
            if not ChannelConfig.get_config()[platform]['enabled']:
                logger.warning(f"Canal {platform} deshabilitado")
                return {'success': False, 'error': 'Canal deshabilitado'}
                
            # Validar estado del chat
            if not chat_state.is_active:
                logger.warning(f"Chat inactivo para {user_id}")
                return {'success': False, 'error': 'Chat inactivo'}
                
            # Registrar métrica
            chatbot_metrics.track_message(platform, 'intent', success=True)
            
            # Procesar intent
            result = await asyncio.create_task(
                IntentOptimizer._process_intent_task(
                    intent, platform, user_id, chat_state, business_unit, text
                )
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error procesando intent: {str(e)}")
            chatbot_metrics.track_message(platform, 'intent', success=False)
            return {'success': False, 'error': str(e)}

    @staticmethod
    async def _process_intent_task(
        intent: str,
        platform: str,
        user_id: str,
        chat_state: Any,
        business_unit: Any,
        text: str
    ) -> Dict[str, Any]:
        """Tarea asíncrona para procesar el intent."""
        # Implementar lógica específica para cada intent
        if intent == 'show_jobs':
            return await IntentOptimizer._handle_show_jobs(
                platform, user_id, chat_state, business_unit, text
            )
            
        elif intent == 'upload_cv':
            return await IntentOptimizer._handle_upload_cv(
                platform, user_id, chat_state, business_unit, text
            )
            
        # Agregar más handlers según sea necesario
        return {'success': True, 'result': 'Intent procesado'}

    @staticmethod
    async def _handle_show_jobs(
        platform: str,
        user_id: str,
        chat_state: Any,
        business_unit: Any,
        text: str
    ) -> Dict[str, Any]:
        """Handler optimizado para mostrar vacantes."""
        try:
            # Implementar lógica específica para mostrar vacantes
            # Usar batch processing y paginación
            return {'success': True, 'result': 'Vacantes mostradas'}
            
        except Exception as e:
            logger.error(f"Error mostrando vacantes: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    async def _handle_upload_cv(
        platform: str,
        user_id: str,
        chat_state: Any,
        business_unit: Any,
        text: str
    ) -> Dict[str, Any]:
        """Handler optimizado para subir CV."""
        try:
            # Implementar lógica específica para subir CV
            return {'success': True, 'result': 'CV subido'}
            
        except Exception as e:
            logger.error(f"Error subiendo CV: {str(e)}")
            return {'success': False, 'error': str(e)}

# Singleton instance
intent_optimizer = IntentOptimizer()
