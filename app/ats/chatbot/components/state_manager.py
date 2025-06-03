# /home/pablo/app/com/chatbot/components/state_manager.py
#
# Módulo de gestor de estados para el chatbot.
# Incluye funcionalidades para manejo de transiciones, validación y seguimiento de historial.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from django.utils import timezone
from app.models import Person, BusinessUnit, ChatState, StateTransition, RecoveryAttempt
import logging
import asyncio
import time
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class RecoveryState(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    RECOVERED = 'recovered'
    ABANDONED = 'abandoned'

@dataclass
class PerformanceMetrics:
    """Métricas de rendimiento en tiempo real"""
    response_time: float = 0.0
    error_rate: float = 0.0
    active_sessions: int = 0
    avg_steps_to_completion: float = 0.0
    recovery_attempts: int = 0
    recovery_success_rate: float = 0.0
    last_updated: datetime = datetime.now()

class RecoveryConfig:
    """Configuración para la recuperación de abandonos"""
    INACTIVITY_THRESHOLD = 180  # 3 minutos en segundos
    MAX_RECOVERY_ATTEMPTS = 2
    RECOVERY_MESSAGES = {
        'initial': "¡Hola! Vemos que te quedaste a la mitad. ¿Te gustaría continuar con tu registro?",
        'reminder': "Tu progreso está guardado. ¿Quieres retomar ahora?",
        'benefits': [
            "💼 Encuentra las mejores oportunidades laborales",
            "⚡ Proceso de registro rápido y sencillo",
            "📱 Acceso desde cualquier dispositivo"
        ]
    }

class StateManager:
    """Gestor de estados para el chatbot.
    
    Características mejoradas:
    - Manejo de transiciones de estado
    - Validación de estados
    - Seguimiento de historial
    - Manejo de timeouts
    - Recuperación de abandonos
    - Monitoreo de rendimiento
    """

    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el gestor de estados con capacidades mejoradas.
        
        Args:
            business_unit (BusinessUnit): Unidad de negocio asociada
        """
        self.business_unit = business_unit
        self._transitions = None
        self._recovery_attempts: Dict[str, int] = {}
        self._last_interaction: Dict[str, datetime] = {}
        self._session_metrics: Dict[str, List[float]] = {}
        self._global_metrics = PerformanceMetrics()
        self._recovery_config = RecoveryConfig()
        self._recovery_tasks: Dict[str, asyncio.Task] = {}
        
        # Inicializar ProgressKeeper
        self.progress_keeper = self.ProgressKeeper(self)
        
        # Iniciar tareas en segundo plano
        self._background_tasks = set()
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Inicia tareas en segundo plano para monitoreo y recuperación"""
        task = asyncio.create_task(self._monitor_inactivity())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        
        task = asyncio.create_task(self._update_metrics())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
    
    async def _monitor_inactivity(self):
        """Monitorea la inactividad de los usuarios"""
        while True:
            try:
                current_time = datetime.now()
                inactive_users = [
                    user_id for user_id, last_active in self._last_interaction.items()
                    if (current_time - last_active).total_seconds() > self._recovery_config.INACTIVITY_THRESHOLD
                ]
                
                for user_id in inactive_users:
                    await self._handle_inactive_user(user_id)
                    
            except Exception as e:
                logger.error(f"Error en monitoreo de inactividad: {e}", exc_info=True)
            
            await asyncio.sleep(60)  # Revisar cada minuto
    
    async def _update_metrics(self):
        """Actualiza las métricas de rendimiento"""
        while True:
            try:
                self._global_metrics.active_sessions = len(self._last_interaction)
                self._global_metrics.last_updated = datetime.now()
                
                # Calcular métricas agregadas
                if self._session_metrics:
                    self._global_metrics.avg_steps_to_completion = sum(
                        len(steps) for steps in self._session_metrics.values()
                    ) / len(self._session_metrics)
                
            except Exception as e:
                logger.error(f"Error al actualizar métricas: {e}", exc_info=True)
            
            await asyncio.sleep(300)  # Actualizar cada 5 minutos
    
    async def _handle_inactive_user(self, user_id: str):
        """Maneja la recuperación de usuarios inactivos"""
        if user_id in self._recovery_tasks:
            return  # Ya hay una tarea de recuperación en curso
            
        async def recovery_task():
            try:
                # Verificar si el usuario sigue inactivo
                if not await self._is_user_inactive(user_id):
                    return
                
                # Obtener intento de recuperación
                attempt = await self._get_recovery_attempt(user_id)
                
                if attempt.attempts >= self._recovery_config.MAX_RECOVERY_ATTEMPTS:
                    await self._mark_abandoned(user_id)
                    return
                
                # Enviar mensaje de recuperación
                message = self._get_recovery_message(attempt.attempts + 1)
                await self._send_recovery_message(user_id, message)
                
                # Registrar el intento
                attempt.attempts += 1
                attempt.last_attempt = timezone.now()
                await attempt.save()
                
            except Exception as e:
                logger.error(f"Error en tarea de recuperación: {e}", exc_info=True)
            finally:
                self._recovery_tasks.pop(user_id, None)
        
        # Iniciar tarea de recuperación
        task = asyncio.create_task(recovery_task())
        self._recovery_tasks[user_id] = task
    
    async def handle_user_message(self, user_id: str, message: str):
        """Procesa un mensaje del usuario y actualiza el estado correspondiente."""
        try:
            # Registrar interacción
            current_time = datetime.now()
            self._last_interaction[user_id] = current_time
            
            # Registrar actividad para ProgressKeeper
            current_state = await self.get_current_state(user_id)
            if current_state:
                await self.progress_keeper.record_checkpoint(user_id, current_state)
            
            # Si el usuario pide ayuda, responder inmediatamente
            if message and message.lower() in ['ayuda', 'help', 'necesito ayuda']:
                await self._provide_help(user_id, current_state)
                return
            
            # Resto de la lógica de procesamiento de mensajes...
            # (código existente)
            logger.debug(f"Mensaje de {user_id} en estado {current_state}: {message}")
            
        except Exception as e:
            logger.error(f"Error al procesar mensaje de {user_id}: {str(e)}")
            self._update_metrics('error', 1)
    
    async def _provide_help(self, user_id: str, current_state: str):
        """Proporciona ayuda contextual basada en el estado actual."""
        try:
            help_messages = {
                'personal_info': "Puedo ayudarte a completar tu información personal. Solo necesito...",
                'experience': "Para agregar experiencia laboral, necesito: empresa, puesto y fechas.",
                'education': "¿Qué estudios has realizado? Necesito institución, título y año de graduación.",
                'default': "Estoy aquí para ayudarte. ¿En qué parte del proceso necesitas asistencia?"
            }
            
            message = help_messages.get(current_state, help_messages['default'])
            await self.send_message(user_id, f"🤖 {message}")
            
            # Registrar la interacción de ayuda
            await self.record_interaction(user_id, 'help_requested', {'state': current_state})
            
        except Exception as e:
            logger.error(f"Error al proporcionar ayuda a {user_id}: {str(e)}")
    
    async def _is_user_inactive(self, user_id: str) -> bool:
        """Verifica si un usuario está inactivo"""
        last_active = self._last_interaction.get(user_id)
        if not last_active:
            return False
            
        inactive_time = (datetime.now() - last_active).total_seconds()
        return inactive_time > self._recovery_config.INACTIVITY_THRESHOLD
    
    async def _get_recovery_attempt(self, user_id: str) -> RecoveryAttempt:
        """Obtiene o crea un intento de recuperación"""
        attempt, _ = await RecoveryAttempt.objects.aget_or_create(
            user_id=user_id,
            defaults={'attempts': 0, 'status': RecoveryState.ACTIVE}
        )
        return attempt
    
    async def _mark_abandoned(self, user_id: str):
        """Marca un usuario como abandonado"""
        await RecoveryAttempt.objects.filter(user_id=user_id).aupdate(
            status=RecoveryState.ABANDONED,
            ended_at=timezone.now()
        )
        self._last_interaction.pop(user_id, None)
    
    def update_interaction(self, user_id: str):
        """Actualiza el tiempo de última interacción de un usuario"""
        self._last_interaction[user_id] = datetime.now()
        
        # Registrar métrica de tiempo de respuesta
        if user_id not in self._session_metrics:
            self._session_metrics[user_id] = []
        
        self._session_metrics[user_id].append(time.time())
        
        # Limpiar métricas antiguas
        if len(self._session_metrics[user_id]) > 100:  # Mantener solo las 100 últimas interacciones
            self._session_metrics[user_id] = self._session_metrics[user_id][-100:]

    async def determine_next_state(self, user_id: str, intent: str) -> Optional[str]:
        """
        Determina el siguiente estado basado en el intent.
        
        Args:
            user_id (str): ID del usuario para seguimiento
            intent (str): Intent detectado
            
        Returns:
            Optional[str]: Estado siguiente o None si no se puede determinar
        """
        start_time = time.time()
        self.update_interaction(user_id)
        
        try:
            if not self._transitions:
                await self._load_transitions()

            # Buscar transiciones válidas para el intent
            for transition in self._transitions:
                if transition.matches(intent):
                    # Registrar transición exitosa
                    self._log_transition(user_id, transition.source_state, transition.target_state, True)
                    return transition.target_state

            # Registrar transición fallida
            default_state = self._get_default_transition(intent)
            self._log_transition(user_id, None, default_state, False)
            
            return default_state

        except Exception as e:
            error_msg = f"Error determining next state: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._global_metrics.error_rate += 1
            return None
        finally:
            # Registrar tiempo de procesamiento
            processing_time = (time.time() - start_time) * 1000  # en ms
            logger.debug(f"Tiempo de procesamiento de estado: {processing_time:.2f}ms")
            
            # Actualizar métricas de rendimiento
            self._global_metrics.response_time = (
                self._global_metrics.response_time + processing_time
            ) / 2  # Promedio móvil
    
    def _log_transition(self, user_id: str, from_state: Optional[str], to_state: str, success: bool):
        """Registra una transición de estado"""
        logger.info(
            f"Transición de estado: {from_state} -> {to_state} "
            f"(usuario: {user_id}, éxito: {success})"
        )
        
        # Actualizar métricas
        if user_id in self._session_metrics:
            self._session_metrics[user_id].append(time.time())
        
        if not success:
            self._global_metrics.error_rate = min(
                self._global_metrics.error_rate + 0.1,  # Aumentar tasa de error
                1.0  # Límite máximo
            )

    async def update_state(self, chat_state: ChatState, new_state: str, user_id: Optional[str] = None) -> bool:
        """
        Actualiza el estado del chat con manejo mejorado de errores y métricas.
        
        Args:
            chat_state (ChatState): Estado actual del chat
            new_state (str): Nuevo estado
            user_id (Optional[str]): ID del usuario para seguimiento
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        start_time = time.time()
        
        if user_id:
            self.update_interaction(user_id)
            
            # Verificar si es un estado de recuperación
            if user_id in self._recovery_attempts:
                await self._handle_recovery_success(user_id)
        
        try:
            # Validar transición
            if not await self._validate_transition(chat_state.state, new_state):
                logger.warning(f"Transición inválida: {chat_state.state} -> {new_state}")
                return False

            # Registrar transición
            old_state = chat_state.state
            chat_state.state = new_state
            chat_state.last_transition = timezone.now()
            
            # Actualizar en base de datos
            await chat_state.asave()
            
            # Actualizar historial
            await self._update_history(chat_state, new_state)
            
            # Registrar métricas
            if user_id:
                self._log_state_change(user_id, old_state, new_state, True)
            
            return True

        except Exception as e:
            error_msg = f"Error actualizando estado: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            if user_id:
                self._log_state_change(user_id, chat_state.state, new_state, False)
                self._global_metrics.error_rate = min(
                    self._global_metrics.error_rate + 0.1,
                    1.0
                )
                
            return False
        finally:
            # Registrar tiempo de procesamiento
            processing_time = (time.time() - start_time) * 1000  # en ms
            logger.debug(f"Tiempo de actualización de estado: {processing_time:.2f}ms")
    
    async def _handle_recovery_success(self, user_id: str):
        """Maneja una recuperación exitosa"""
        if user_id in self._recovery_attempts:
            await RecoveryAttempt.objects.filter(user_id=user_id).aupdate(
                status=RecoveryState.RECOVERED,
                ended_at=timezone.now()
            )
            self._recovery_attempts.pop(user_id, None)
            logger.info(f"Usuario {user_id} recuperado exitosamente")
    
    def _log_state_change(self, user_id: str, old_state: str, new_state: str, success: bool):
        """Registra un cambio de estado"""
        logger.info(
            f"Cambio de estado: {old_state} -> {new_state} "
            f"(usuario: {user_id}, éxito: {success})"
        )
        
        # Actualizar métricas
        if success and user_id in self._session_metrics:
            self._session_metrics[user_id].append(time.time())
        
        if not success:
            self._global_metrics.error_rate = min(
                self._global_metrics.error_rate + 0.05,
                1.0
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene las métricas de rendimiento actuales"""
        return {
            'response_time_ms': round(self._global_metrics.response_time, 2),
            'error_rate': round(self._global_metrics.error_rate, 4),
            'active_sessions': self._global_metrics.active_sessions,
            'avg_steps_to_completion': round(self._global_metrics.avg_steps_to_completion, 2),
            'last_updated': self._global_metrics.last_updated.isoformat(),
            'recovery_attempts': self._global_metrics.recovery_attempts,
            'recovery_success_rate': round(self._global_metrics.recovery_success_rate, 2)
        }

    async def _load_transitions(self):
        """
        Carga las transiciones de estado desde la base de datos con caché.
        Incluye manejo de errores y métricas de rendimiento.
        """
        start_time = time.time()
        try:
            self._transitions = await StateTransition.objects.filter(
                business_unit=self.business_unit,
                is_active=True
            ).prefetch_related('conditions').aall()
            
            logger.info(f"Cargadas {len(self._transitions)} transiciones para {self.business_unit.name}")
            
        except Exception as e:
            logger.error(f"Error cargando transiciones: {str(e)}", exc_info=True)
            self._transitions = []
            self._global_metrics.error_rate = min(
                self._global_metrics.error_rate + 0.1,
                1.0
            )
        finally:
            load_time = (time.time() - start_time) * 1000  # en ms
            logger.debug(f"Tiempo de carga de transiciones: {load_time:.2f}ms")

    async def _validate_transition(self, current_state: str, new_state: str) -> bool:
        """
        Valida si la transición de estado es válida.
        
        Args:
            current_state (str): Estado actual
            new_state (str): Nuevo estado propuesto
            
        Returns:
            bool: True si la transición es válida, False en caso contrario
        """
        # Estado inicial siempre es válido
        if current_state is None:
            return True
            
        # Mismo estado es válido (puede usarse para reintentos)
        if current_state == new_state:
            return True
            
        # Obtener transiciones válidas desde el estado actual
        valid_transitions = [
            t.target_state for t in self._transitions 
            if t.source_state == current_state
        ]
        
        # Verificar si la transición es válida
        is_valid = new_state in valid_transitions
        
        if not is_valid:
            logger.warning(
                f"Transición inválida detectada: {current_state} -> {new_state}. "
                f"Transiciones válidas: {', '.join(valid_transitions) if valid_transitions else 'Ninguna'}"
            )
            
        return is_valid

    async def _update_history(self, chat_state: ChatState, new_state: str):
        """Actualiza el historial de estados."""
        chat_state.history.append({
            'state': new_state,
            'timestamp': timezone.now()
        })
        await chat_state.asave()
