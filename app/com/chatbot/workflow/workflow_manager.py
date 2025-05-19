# /home/pablo/app/com/chatbot/workflow/workflow_manager.py
"""
Gestor de workflows para el chatbot.

Este módulo facilita la creación, gestión y ejecución de workflows
conversacionales, permitiendo una interacción fluida con el usuario
y manteniendo el contexto de la conversación.
"""

import logging
from typing import Dict, List, Any, Optional, Type, Union
import importlib
import inspect

from app.com.chatbot.workflow.base_workflow import BaseWorkflow
from app.com.chatbot.core.values_integration import get_value_driven_response

# Si existen en el sistema, añadimos estas importaciones
# Importación con manejo de errores para cada módulo individual
try:
    from app.com.chatbot.workflow.talent_analysis_workflow import TalentAnalysisWorkflow
    has_talent_workflow = True
except ImportError:
    has_talent_workflow = False
    logging.warning("No se pudo importar TalentAnalysisWorkflow.")

try:
    from app.com.chatbot.workflow.cultural_fit_workflow import CulturalFitWorkflow
    has_cultural_workflow = True
except ImportError:
    has_cultural_workflow = False
    logging.warning("No se pudo importar CulturalFitWorkflow.")

logger = logging.getLogger(__name__)

class WorkflowManager:
    """
    Gestor central para todos los workflows del chatbot.
    
    Facilita:
    - Registro de workflows disponibles
    - Creación de instancias de workflow
    - Persistencia y restauración de estados
    - Enrutamiento de mensajes al workflow correcto
    """
    
    _instance = None
    
    def __new__(cls):
        """Implementación de Singleton para el gestor de workflows."""
        if cls._instance is None:
            cls._instance = super(WorkflowManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa el gestor de workflows y registra los workflows disponibles."""
        if self._initialized:
            return
            
        self.workflows = {}
        self.active_workflows = {}
        
        # Registramos los workflows disponibles
        self._register_workflows()
        
        self._initialized = True
    
    def _register_workflows(self):
        """Registra todos los workflows disponibles en el sistema."""
        # Buscamos clases que hereden de BaseWorkflow en este módulo
        workflow_module = importlib.import_module('app.com.chatbot.workflow')
        
        # Registramos workflows específicos solo si están disponibles
        if has_talent_workflow:
            self.register_workflow("talent_analysis", TalentAnalysisWorkflow)
            
        if has_cultural_workflow:
            self.register_workflow("cultural_fit", CulturalFitWorkflow)
        
        # Registramos dinámicamente todos los workflows que se encuentren
        self._discover_and_register_workflows()
        
        logger.info(f"Workflows registrados: {', '.join(self.workflows.keys())}")
    
    def _discover_and_register_workflows(self):
        """Descubre y registra automáticamente workflows disponibles."""
        try:
            # Importamos todos los módulos en el paquete workflow
            import app.com.chatbot.workflow
            
            # Obtenemos todos los módulos en el paquete
            workflow_package = importlib.import_module('app.com.chatbot.workflow')
            
            # Para cada módulo, buscamos clases que hereden de BaseWorkflow
            for module_name in dir(workflow_package):
                if module_name.startswith('__'):
                    continue
                
                try:
                    module = importlib.import_module(f'app.com.chatbot.workflow.{module_name}')
                    
                    # Buscamos clases que hereden de BaseWorkflow
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        if (inspect.isclass(attr) and 
                            issubclass(attr, BaseWorkflow) and 
                            attr is not BaseWorkflow):
                            
                            # Registramos el workflow
                            workflow_type = getattr(attr, 'workflow_type', attr_name.lower())
                            self.register_workflow(workflow_type, attr)
                            logger.info(f"Workflow autodescubierto: {workflow_type}")
                            
                except (ImportError, AttributeError) as e:
                    logger.debug(f"Error cargando módulo {module_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error en descubrimiento de workflows: {e}", exc_info=True)
    
    def register_workflow(self, workflow_type: str, workflow_class: Type[BaseWorkflow]):
        """
        Registra un nuevo tipo de workflow.
        
        Args:
            workflow_type: Identificador único del tipo de workflow
            workflow_class: Clase del workflow a registrar
        """
        if not issubclass(workflow_class, BaseWorkflow):
            raise TypeError(f"La clase {workflow_class.__name__} no hereda de BaseWorkflow")
            
        self.workflows[workflow_type] = workflow_class
        logger.info(f"Workflow '{workflow_type}' registrado exitosamente")
    
    async def create_workflow(self, workflow_type: str, **kwargs) -> Optional[BaseWorkflow]:
        """
        Crea una nueva instancia de un workflow.
        
        Args:
            workflow_type: Tipo de workflow a crear
            **kwargs: Argumentos para inicializar el workflow
            
        Returns:
            BaseWorkflow: Instancia del workflow creado, o None si el tipo no existe
        """
        workflow_class = self.workflows.get(workflow_type)
        
        if not workflow_class:
            logger.error(f"Tipo de workflow '{workflow_type}' no registrado")
            return None
            
        try:
            workflow = workflow_class(**kwargs)
            
            # Generamos un ID único para esta instancia
            if 'session_id' in kwargs:
                workflow_id = f"{workflow_type}_{kwargs['session_id']}"
            else:
                from uuid import uuid4
                workflow_id = f"{workflow_type}_{uuid4().hex[:8]}"
                
            # Almacenamos la instancia activa
            self.active_workflows[workflow_id] = workflow
            
            # Inicializamos el workflow
            await workflow.initialize(kwargs.get('context', {}))
            
            return workflow
        except Exception as e:
            logger.error(f"Error creando workflow '{workflow_type}': {e}", exc_info=True)
            return None
    
    async def get_workflow(self, workflow_id: str) -> Optional[BaseWorkflow]:
        """
        Obtiene una instancia activa de workflow por su ID.
        
        Args:
            workflow_id: ID único del workflow
            
        Returns:
            BaseWorkflow: Instancia del workflow, o None si no existe
        """
        return self.active_workflows.get(workflow_id)
    
    async def handle_message(self, workflow_id: str, message: str) -> Optional[str]:
        """
        Procesa un mensaje para un workflow específico.
        
        Args:
            workflow_id: ID del workflow que debe procesar el mensaje
            message: Mensaje a procesar
            
        Returns:
            str: Respuesta generada por el workflow, o None si hay error
        """
        workflow = await self.get_workflow(workflow_id)
        
        if not workflow:
            logger.error(f"Workflow '{workflow_id}' no encontrado")
            return await get_value_driven_response(
                "workflow_not_found",
                {"workflow_id": workflow_id},
                "Lo siento, no pude encontrar la conversación activa. ¿Puedo ayudarte con algo más?"
            )
            
        try:
            # Procesamos el mensaje
            response = await workflow.handle_message(message)
            
            # Verificamos si hay cambio de estado
            next_state = await workflow.get_next_state(message)
            if next_state:
                await workflow.transition_to(next_state)
                
            # Si el workflow ha finalizado, lo eliminamos de los activos
            if await workflow.is_completed():
                self.active_workflows.pop(workflow_id, None)
                
            return response
        except Exception as e:
            logger.error(f"Error procesando mensaje en workflow '{workflow_id}': {e}", exc_info=True)
            
            # Respuesta amigable en caso de error
            return await get_value_driven_response(
                "workflow_error",
                {"workflow_id": workflow_id, "error": str(e)},
                "Disculpa, ocurrió un problema procesando tu mensaje. ¿Podrías intentarlo de nuevo?"
            )
    
    async def abort_workflow(self, workflow_id: str) -> bool:
        """
        Aborta un workflow activo.
        
        Args:
            workflow_id: ID del workflow a abortar
            
        Returns:
            bool: True si se abortó exitosamente, False en caso contrario
        """
        workflow = await self.get_workflow(workflow_id)
        
        if not workflow:
            logger.warning(f"Intento de abortar workflow inexistente: {workflow_id}")
            return False
            
        try:
            await workflow.abort()
            self.active_workflows.pop(workflow_id, None)
            return True
        except Exception as e:
            logger.error(f"Error abortando workflow '{workflow_id}': {e}", exc_info=True)
            return False
    
    async def get_active_workflows_for_user(self, user_id: str) -> List[str]:
        """
        Obtiene los IDs de workflows activos para un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            List[str]: Lista de IDs de workflows activos
        """
        active_ids = []
        
        for workflow_id, workflow in self.active_workflows.items():
            if workflow.user_id == user_id:
                active_ids.append(workflow_id)
                
        return active_ids
    
    async def save_all_workflows(self) -> Dict[str, Any]:
        """
        Guarda el estado de todos los workflows activos.
        
        Returns:
            Dict[str, Any]: Mapa de ID de workflow a estado serializado
        """
        saved_states = {}
        
        for workflow_id, workflow in self.active_workflows.items():
            try:
                state = await workflow.save_state()
                saved_states[workflow_id] = state
            except Exception as e:
                logger.error(f"Error guardando estado de workflow '{workflow_id}': {e}", exc_info=True)
                
        return saved_states
    
    async def restore_workflows(self, states: Dict[str, Any]) -> int:
        """
        Restaura workflows desde estados serializados.
        
        Args:
            states: Mapa de ID de workflow a estado serializado
            
        Returns:
            int: Número de workflows restaurados exitosamente
        """
        restored_count = 0
        
        for workflow_id, state_data in states.items():
            try:
                workflow_type = state_data.get("workflow_type")
                
                if workflow_type not in self.workflows:
                    logger.warning(f"No se puede restaurar workflow de tipo desconocido: {workflow_type}")
                    continue
                    
                workflow_class = self.workflows[workflow_type]
                workflow = await workflow_class.load_from_state(state_data)
                
                self.active_workflows[workflow_id] = workflow
                restored_count += 1
                
            except Exception as e:
                logger.error(f"Error restaurando workflow '{workflow_id}': {e}", exc_info=True)
                
        return restored_count

# Instancia singleton para acceso global
workflow_manager = WorkflowManager()

# Funciones de conveniencia para acceso directo
async def get_workflow_manager() -> WorkflowManager:
    """
    Obtiene la instancia del gestor de workflows.
    
    Returns:
        WorkflowManager: Instancia singleton del gestor
    """
    return workflow_manager

async def create_workflow(workflow_type: str, **kwargs) -> Optional[BaseWorkflow]:
    """
    Crea una nueva instancia de workflow.
    
    Args:
        workflow_type: Tipo de workflow a crear
        **kwargs: Argumentos para inicializar el workflow
        
    Returns:
        Optional[BaseWorkflow]: Instancia del workflow o None si hay error
    """
    return await workflow_manager.create_workflow(workflow_type, **kwargs)

async def handle_workflow_message(workflow_id: str, message: str) -> Optional[str]:
    """
    Procesa un mensaje para un workflow específico.
    
    Args:
        workflow_id: ID del workflow
        message: Mensaje a procesar
        
    Returns:
        Optional[str]: Respuesta del workflow o None si hay error
    """
    return await workflow_manager.handle_message(workflow_id, message)
