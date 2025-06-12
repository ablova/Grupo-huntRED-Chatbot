"""
Módulo para el panel de control de consultores.
Permite a los consultores monitorear y gestionar interacciones con candidatos.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from django.db.models import Count, Q, F
from django.utils import timezone
from asgiref.sync import sync_to_async
from app.models import Person, ChatState, RecoveryAttempt, BusinessUnit, ConsultorInteraction
from app.ats.integrations.channels.whatsapp import WhatsAppService
import logging

logger = logging.getLogger(__name__)

class ConsultantDashboard:
    """Panel de control para consultores de huntRED.
    
    Permite a los consultores:
    - Ver candidatos por estado
    - Monitorear intentos de recuperación
    - Contactar candidatos directamente
    - Reiniciar conversaciones
    """
    
    def __init__(self, consultor_id: str):
        """
        Inicializa el dashboard para un consultor específico.
        
        Args:
            consultor_id: ID del usuario consultor
        """
        self.consultor_id = consultor_id
        self.whatsapp_service = WhatsAppService()
    
    @sync_to_async
    def get_candidates_by_status(self, status: str = None, business_unit: str = None) -> List[Dict]:
        """
        Obtiene candidatos filtrados por estado y unidad de negocio.
        
        Args:
            status: Estado del candidato (opcional)
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Lista de diccionarios con información de los candidatos
        """
        try:
            query = ChatState.objects.all()
            
            if status:
                query = query.filter(state=status)
                
            if business_unit:
                query = query.filter(user__business_unit__name=business_unit)
            
            # Obtener los últimos 50 candidatos ordenados por última interacción
            candidates = query.select_related('user').order_by('-last_interaction')[:50]
            
            return [{
                'id': str(candidate.user.id),
                'name': candidate.user.get_full_name() or 'Sin nombre',
                'phone': candidate.user.phone,
                'email': candidate.user.email,
                'state': candidate.state,
                'last_interaction': candidate.last_interaction,
                'business_unit': candidate.user.business_unit.name if candidate.user.business_unit else 'Sin unidad'
            } for candidate in candidates]
            
        except Exception as e:
            logger.error(f"Error obteniendo candidatos: {str(e)}")
            return []
    
    @sync_to_async
    def get_recovery_attempts(self, days: int = 7) -> List[Dict]:
        """
        Obtiene los intentos de recuperación recientes.
        
        Args:
            days: Número de días hacia atrás para buscar
            
        Returns:
            Lista de intentos de recuperación
        """
        try:
            since = timezone.now() - timedelta(days=days)
            attempts = RecoveryAttempt.objects.filter(
                last_attempt__gte=since
            ).select_related('user').order_by('-last_attempt')
            
            return [{
                'user_id': str(attempt.user.id),
                'user_name': attempt.user.get_full_name() or 'Sin nombre',
                'attempts': attempt.attempts,
                'status': attempt.status,
                'last_attempt': attempt.last_attempt,
                'first_attempt': attempt.first_attempt
            } for attempt in attempts]
            
        except Exception as e:
            logger.error(f"Error obteniendo intentos de recuperación: {str(e)}")
            return []
    
    async def contact_candidate(self, candidate_id: str, message: str) -> bool:
        """
        Envía un mensaje directo a un candidato.
        
        Args:
            candidate_id: ID del candidato
            message: Mensaje a enviar
            
        Returns:
            bool: True si el mensaje se envió correctamente
        """
        try:
            # Obtener información del candidato
            candidate = await sync_to_async(Person.objects.get)(id=candidate_id)
            
            if not candidate.phone:
                logger.error(f"El candidato {candidate_id} no tiene número de teléfono")
                return False
            
            # Enviar mensaje a través del servicio de WhatsApp
            success = await self.whatsapp_service.send_message(
                to=candidate.phone,
                message=f"🤖 Mensaje de tu consultor huntRED:\n\n{message}"
            )
            
            if success:
                # Registrar la interacción
                await sync_to_async(self._log_consultant_interaction)(
                    consultor_id=self.consultor_id,
                    candidate_id=candidate_id,
                    action='direct_message',
                    details={'message': message[:500]}  # Limitar tamaño del mensaje
                )
            
            return success
            
        except Person.DoesNotExist:
            logger.error(f"Candidato {candidate_id} no encontrado")
            return False
        except Exception as e:
            logger.error(f"Error contactando al candidato {candidate_id}: {str(e)}")
            return False
    
    @sync_to_async
    def reset_conversation(self, candidate_id: str) -> bool:
        """
        Reinicia la conversación con un candidato.
        
        Args:
            candidate_id: ID del candidato
            
        Returns:
            bool: True si se reinició correctamente
        """
        try:
            # Obtener el estado del chat del candidato
            chat_state = ChatState.objects.get(user_id=candidate_id)
            
            # Reiniciar el estado a uno inicial
            chat_state.state = 'welcome'
            chat_state.context = {}
            chat_state.save()
            
            # Registrar la interacción
            self._log_consultant_interaction(
                consultor_id=self.consultor_id,
                candidate_id=candidate_id,
                action='reset_conversation',
                details={'previous_state': chat_state.state}
            )
            
            return True
            
        except ChatState.DoesNotExist:
            logger.error(f"No se encontró estado de chat para el candidato {candidate_id}")
            return False
        except Exception as e:
            logger.error(f"Error reiniciando conversación para {candidate_id}: {str(e)}")
            return False
    
    def _log_consultant_interaction(self, consultor_id: str, candidate_id: str, action: str, details: dict):
        """
        Registra una interacción del consultor con un candidato.
        
        Args:
            consultor_id: ID del consultor
            candidate_id: ID del candidato
            action: Acción realizada (direct_message, reset_conversation, etc.)
            details: Detalles adicionales de la interacción
        """
        try:
            ConsultorInteraction.objects.create(
                consultor_id=consultor_id,
                candidate_id=candidate_id,
                action=action,
                details=details
            )
        except Exception as e:
            logger.error(f"Error registrando interacción del consultor: {str(e)}")
    
    @sync_to_async
    def get_candidate_status(self, candidate_id: str) -> Optional[Dict]:
        """
        Obtiene el estado actual de un candidato.
        
        Args:
            candidate_id: ID del candidato
            
        Returns:
            Dict con el estado del candidato o None si no se encuentra
        """
        try:
            chat_state = ChatState.objects.get(user_id=candidate_id)
            recovery_attempt = RecoveryAttempt.objects.filter(user_id=candidate_id).first()
            
            return {
                'state': chat_state.state,
                'last_interaction': chat_state.last_interaction,
                'recovery_attempts': recovery_attempt.attempts if recovery_attempt else 0,
                'recovery_status': recovery_attempt.status if recovery_attempt else 'none',
                'context': chat_state.context or {}
            }
        except ChatState.DoesNotExist:
            return None
