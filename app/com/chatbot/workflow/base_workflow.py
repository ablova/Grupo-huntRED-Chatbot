# /home/pablo/app/com/chatbot/workflow/base_workflow.py
"""
Clase base para todos los workflows del chatbot.

Este módulo define la estructura común y funcionalidades
compartidas por todos los workflows del sistema.
Sigue los valores fundamentales de Grupo huntRED®: Apoyo, Solidaridad y Sinergia.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from abc import ABC, abstractmethod

from asgiref.sync import sync_to_async
from django.utils import timezone

logger = logging.getLogger(__name__)

class BaseWorkflow(ABC):
    """
    Clase base abstracta para todos los workflows del chatbot.
    
    Define la interfaz común y funcionalidad básica para los workflows.
    Cada workflow especializado debe heredar de esta clase e implementar
    su lógica específica para procesar mensajes y gestionar el estado.
    """
    
    workflow_type = "base"  # Debe ser sobreescrito por cada workflow
    
    def __init__(self, user_id=None, chat_id=None, **kwargs):
        """
        Inicializa el workflow con información de contexto básica.
        
        Args:
            user_id: ID del usuario que interactúa con el workflow
            chat_id: ID de la conversación actual
            **kwargs: Argumentos adicionales específicos de cada workflow
        """
        self.user_id = user_id
        self.chat_id = chat_id
        self.state = "INITIAL"  # Estado inicial del workflow
        self.context = {
            "user_id": user_id,
            "chat_id": chat_id,
            "created_at": timezone.now().isoformat(),
            "last_updated": timezone.now().isoformat()
        }
        self.context.update(kwargs)
        self.workflow_id = self.__class__.__name__
    
    @abstractmethod
    async def initialize(self, context: Dict[str, Any] = None) -> str:
        """
        Inicializa el workflow con el contexto proporcionado.
        
        Args:
            context: Contexto adicional para inicializar el workflow
            
        Returns:
            str: Mensaje inicial para el usuario
        """
        if context:
            self.context.update(context)
        
        # Este método debe ser implementado por cada workflow específico
        return "Iniciando workflow..."
    
    @abstractmethod
    async def handle_message(self, message_text: str) -> str:
        """
        Procesa un mensaje del usuario y devuelve una respuesta.
        
        Args:
            message_text: Texto del mensaje del usuario
            
        Returns:
            str: Respuesta generada por el workflow
        """
        # Este método debe ser implementado por cada workflow específico
        pass
    
    async def get_next_state(self, message_text: str) -> Optional[str]:
        """
        Determina el siguiente estado del workflow basado en el mensaje actual.
        
        Args:
            message_text: Texto del mensaje del usuario
            
        Returns:
            Optional[str]: Siguiente estado o None si no hay cambio de estado
        """
        # Este método puede ser implementado por cada workflow específico
        # para manejar transiciones de estado basadas en mensajes
        return None
    
    async def transition_to(self, new_state: str) -> None:
        """
        Realiza la transición a un nuevo estado del workflow.
        
        Args:
            new_state: Nuevo estado al que transicionar
        """
        logger.info(f"Workflow {self.workflow_id} transitioning from {self.state} to {new_state}")
        self.state = new_state
        self.context["last_updated"] = timezone.now().isoformat()
        self.context["current_state"] = new_state
    
    async def save_state(self) -> Dict[str, Any]:
        """
        Guarda el estado actual del workflow para persistencia.
        
        Returns:
            Dict[str, Any]: Estado serializado del workflow
        """
        state_data = {
            "workflow_type": self.workflow_type,
            "workflow_id": self.workflow_id,
            "state": self.state,
            "context": self.context,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "last_updated": timezone.now().isoformat()
        }
        
        # En una implementación real, aquí se guardaría el estado en una base de datos
        # o en Redis para persistencia
        
        return state_data
    
    @classmethod
    async def load_from_state(cls, state_data: Dict[str, Any]) -> 'BaseWorkflow':
        """
        Carga un workflow desde un estado serializado.
        
        Args:
            state_data: Estado serializado del workflow
            
        Returns:
            BaseWorkflow: Instancia del workflow con el estado restaurado
        """
        # Este método debe ser implementado más específicamente por cada workflow
        workflow = cls(
            user_id=state_data.get("user_id"),
            chat_id=state_data.get("chat_id")
        )
        
        workflow.state = state_data.get("state", "INITIAL")
        workflow.context = state_data.get("context", {})
        
        return workflow
    
    async def is_completed(self) -> bool:
        """
        Verifica si el workflow ha completado su ejecución.
        
        Returns:
            bool: True si el workflow está completado
        """
        return self.state == "COMPLETED"
    
    async def abort(self) -> None:
        """Aborta el workflow actual."""
        await self.transition_to("ABORTED")
    
    async def get_state_summary(self) -> str:
        """
        Genera un resumen del estado actual del workflow.
        
        Returns:
            str: Resumen del estado actual
        """
        return f"Workflow: {self.workflow_id}, Estado: {self.state}, Usuario: {self.user_id}"
    
    def get_elapsed_time(self) -> float:
        """
        Calcula el tiempo transcurrido desde la creación del workflow.
        
        Returns:
            float: Tiempo transcurrido en segundos
        """
        created_at = datetime.fromisoformat(self.context.get("created_at"))
        now = timezone.now()
        return (now - created_at).total_seconds()
    
    async def format_response(self, message: str) -> str:
        """
        Formatea la respuesta del workflow según el contexto actual.
        
        Args:
            message: Mensaje a formatear
            
        Returns:
            str: Mensaje formateado
        """
        # Formato por defecto, puede ser sobreescrito por workflows específicos
        return message
    
    def __str__(self) -> str:
        """
        Representación en cadena del workflow.
        
        Returns:
            str: Representación textual del workflow
        """
        return f"{self.workflow_id}(state={self.state}, user_id={self.user_id})"
