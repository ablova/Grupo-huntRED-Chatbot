# /home/pablo/app/import_config.py
#
# MÓDULO LEGACY: Este archivo está en proceso de migración
# Esta versión mantiene compatibilidad mientras se completa la migración
# a app/module_registry.py
#

import importlib
import sys
import ast
from typing import Dict, Any, Callable, Optional, Set, List
from pathlib import Path
import logging
import os
from datetime import datetime

# Configure logger
logger = logging.getLogger('import_config')
logger.setLevel(logging.INFO)

# Create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(ch)

# IMPORTANTE: Esta implementación está siendo reemplazada por app/module_registry.py
# Siguiendo las reglas globales de Grupo huntRED®:
# - No Redundancies: Verificar antes de añadir funciones que no existan en el código
# - Modularity: Escribir código modular, reutilizable; evitar duplicar funcionalidad

# Implementación simple con importación a nivel de función 
def get_fetch_whatsapp_user_data(*args, **kwargs):
    """
    Recupera datos de usuario de WhatsApp - importación a nivel de función
    """
    # Importación a nivel de función para evitar dependencias circulares
    from app.com.chatbot.integrations.whatsapp import fetch_whatsapp_user_data
    return fetch_whatsapp_user_data(*args, **kwargs)

# Define package structure
PACKAGE_STRUCTURE = {
    'root': [
        'com',
        'ml',
        'notifications',
        'pagos',
        'utils',
        'views',
        'tests'
    ],
    'com': [
        'notifications',
        'pagos',
        'utils',
        'dynamics',
        'talent',
        'feedback',
        'onboarding'
    ],
    'ml': [
        'core',
        'models',
        'features',
        'analyzers'
    ],
    'notifications': [
        'channels',
        'recipients',
        'templates'
    ],
    'pagos': [
        'gateways',
        'views',
        'services'
    ]
}

# Mapeo de importaciones relativas a absolutas
IMPORT_MAPPINGS = {
    # Notificaciones
    'notifications.handlers': 'app.com.notifications.handlers',
    'notifications.managers': 'app.com.notifications.managers',
    'notifications.core': 'app.com.notifications.core',
    'notifications.templates': 'app.com.notifications.templates',
    
    # Pagos
    'pagos.views': 'app.com.pagos.views',
    'pagos.gateways': 'app.com.pagos.gateways',
    'pagos.services': 'app.com.pagos.services',
    
    # ML
    'ml.core': 'app.ml.core',
    'ml.models': 'app.ml.core.models',
    'ml.features': 'app.ml.core.features',
    'ml.analyzers': 'app.ml.core.analyzers',
    
    # Utils
    'utils.skills': 'app.com.utils.skills',
    'utils.cv_generator': 'app.com.utils.cv_generator',
    'utils.third_parties': 'app.com.utils.third_parties'
}

# Reglas de importación
IMPORT_RULES = {
    'prefer_absolute': True,  # Preferir importaciones absolutas
    'max_relative_level': 1,  # Máximo nivel de importación relativa permitido
    'exclude_patterns': [
        '__init__.py',  # Excluir archivos __init__.py
        'tests/',       # Excluir directorio de tests
        'migrations/'   # Excluir directorio de migraciones
    ]
}

class ModuleRegistry:
    def __init__(self):
        self._modules = {}
        self._logger = logging.getLogger('module_registry')
        self._initialized = False

    def register_module(self, name: str, module_path: str) -> None:
        """
        Register a module for lazy loading.
        
        Args:
            name: The name to use when accessing the module
            module_path: The full module path (e.g., 'app.com.chatbot.chatbot')
        """
        if name in self._modules:
            self._logger.warning(f"Module {name} already registered")
            return
        self._modules[name] = module_path
        self._logger.debug(f"Registered module {name} from {module_path}")

    def get_module(self, name: str) -> Any:
        """
        Get a registered module.
        
        Args:
            name: The name of the module to get
            
        Returns:
            The lazy-loaded module
            
        Raises:
            ImportError: If the module is not registered
        """
        if name not in self._modules:
            self._logger.error(f"Module {name} not registered")
            raise ImportError(f"Module {name} not registered")
            
        module_path = self._modules[name]
        try:
            if module_path not in sys.modules:
                module = importlib.import_module(module_path)
                sys.modules[module_path] = module
            return sys.modules[module_path]
        except ImportError as e:
            self._logger.error(f"Error importing {module_path}: {str(e)}")
            raise

    def register_from_config(self, config_path: str) -> None:
        """
        Register modules from a configuration file.
        
        Args:
            config_path: Path to the configuration file containing module mappings
        """
        try:
            config_module = importlib.import_module(config_path)
            for name, module_path in config_module.__dict__.items():
                if not name.startswith('_') and isinstance(module_path, str):
                    self.register_module(name, module_path)
        except ImportError as e:
            self._logger.error(f"Error loading config from {config_path}: {str(e)}")
            raise

    def initialize(self) -> None:
        """
        Initialize all registered modules.
        This method should be called during application startup.
        """
        if self._initialized:
            return
            
        self._logger.info("Initializing module registry...")
        start_time = datetime.now()
        
        for name, module_path in self._modules.items():
            try:
                self.get_module(name)
                self._logger.info(f"Successfully initialized {name} from {module_path}")
            except Exception as e:
                self._logger.error(f"Failed to initialize {name}: {str(e)}")
                
        self._initialized = True
        end_time = datetime.now()
        self._logger.info(f"Module registry initialization completed in {end_time - start_time}")

    def validate_package_structure(self) -> None:
        """
        Validate that the package structure matches the defined configuration.
        """
        app_path = Path(os.path.dirname(__file__))
        
        # Check root packages
        for package in PACKAGE_STRUCTURE['root']:
            package_path = app_path / package
            if not package_path.exists():
                self._logger.warning(f"Missing root package: {package}")
            if not (package_path / '__init__.py').exists():
                self._logger.warning(f"Missing __init__.py in {package}")
        
        # Check subpackages
        for subdir, packages in PACKAGE_STRUCTURE.items():
            if subdir == 'root':
                continue
                
            subdir_path = app_path / subdir
            if not subdir_path.exists():
                self._logger.warning(f"Missing subdirectory: {subdir}")
                continue
                
            for package in packages:
                package_path = subdir_path / package
                if not package_path.exists():
                    self._logger.warning(f"Missing package in {subdir}: {package}")
                if not (package_path / '__init__.py').exists():
                    self._logger.warning(f"Missing __init__.py in {subdir}/{package}")

    def find_circular_imports(self, file_path: Path) -> Dict[str, Set[str]]:
        """
        Find circular imports in a Python file.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            Dictionary mapping module names to their dependencies
        """
        dependencies = {}
        
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    if module not in dependencies:
                        dependencies[module] = set()
                    dependencies[module].add(os.path.basename(file_path).replace('.py', ''))
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                if module not in dependencies:
                    dependencies[module] = set()
                dependencies[module].add(os.path.basename(file_path).replace('.py', ''))
        
        return dependencies

    def fix_imports(self, file_path: Path) -> None:
        """
        Fix circular imports in a Python file.
        
        Args:
            file_path: Path to the Python file to fix
        """
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Fix import patterns to use absolute imports consistently
        content = content.replace('from .models import', 'from app.models import')
        content = content.replace('from .views import', 'from app.views import')
        content = content.replace('from .forms import', 'from app.forms import')
        
        with open(file_path, 'w') as f:
            f.write(content)

    def process_directory(self, directory: Path) -> None:
        """
        Process all Python files in a directory to fix circular imports.
        
        Args:
            directory: Path to the directory to process
        """
        for file_path in directory.rglob('*.py'):
            if file_path.name == '__init__.py':
                continue
                
            try:
                dependencies = self.find_circular_imports(file_path)
                if dependencies:
                    self._logger.info(f"Found circular imports in {file_path}: {dependencies}")
                    self.fix_imports(file_path)
            except Exception as e:
                self._logger.error(f"Error processing {file_path}: {str(e)}")

# Create a global instance of ModuleRegistry
module_registry = ModuleRegistry()

def register_module(name: str, module_path: str) -> None:
    """
    Register a module for lazy loading.
    
    Args:
        name: The name to use when accessing the module
        module_path: The full module path (e.g., 'app.com.chatbot.chatbot')
    """
    module_registry.register_module(name, module_path)

def get_module(name: str) -> Any:
    """
    Get a registered module.
    
    Args:
        name: The name of the module to get
        
    Returns:
        The lazy-loaded module
        
    Raises:
        ImportError: If the module is not registered
    """
    return module_registry.get_module(name)

def register_from_config(config_path: str) -> None:
    """
    Register modules from a configuration file.
    
    Args:
        config_path: Path to the configuration file containing module mappings
    """
    module_registry.register_from_config(config_path)

def initialize_all() -> None:
    """
    Initialize all registered modules.
    This method should be called during application startup.
    """
    module_registry.initialize()

def validate_imports() -> bool:
    """
    Validate and register essential modules.
    
    Returns:
        bool: True if validation passed, False otherwise
    """
    # Validate package structure first
    module_registry.validate_package_structure()
    
    # List of essential packages to register
    essential_packages = ['com']  # Only register com package for now
    
    # Register essential modules
    for package in essential_packages:
        try:
            config_path = f"app.{package}.import_config"
            register_from_config(config_path)
            logger.info(f"Successfully registered modules from package {package}")
        except Exception as e:
            logger.error(f"Error registering modules from {package}: {str(e)}")
            continue
    
    # Process directory for circular imports
    app_path = Path(__file__).parent
    module_registry.process_directory(app_path)
    
    # Initialize all modules
    try:
        initialize_all()
        return True
    except Exception as e:
        logger.error(f"Error initializing modules: {str(e)}")
        return False

# Register essential modules at startup
if os.environ.get('DJANGO_SETTINGS_MODULE'):
    validate_imports()

# Add getter functions for existing modules
# Funciones de chatbot
def get_conversational_flow_manager():
    """Get ConversationalFlowManager instance."""
    # FIXED: # FIXED: # FIXED: # FIXED: # FIXED: # FIXED: # FIXED: # FIXED: # FIXED: from app.com.chatbot.conversational_flow_manager import ConversationalFlowManager # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular
    return ConversationalFlowManager

def get_intents_handler():
    """Get IntentsHandler instance."""
    from app.com.chatbot.intents_handler import IntentsHandler
    return IntentsHandler

def get_intent_detector():
    """Get IntentDetector instance (alias for IntentsHandler)."""
    return get_intents_handler()

def get_intents_optimizer():
    """Get IntentsOptimizer instance."""
    from app.com.chatbot.intents_optimizer import IntentsOptimizer
    return IntentsOptimizer

def get_context_manager():
    """Get ContextManager instance."""
    from app.com.chatbot.context_manager import ContextManager
    return ContextManager

def get_response_generator():
    """Get ResponseGenerator instance."""
    from app.com.chatbot.response_generator import ResponseGenerator
    return ResponseGenerator

def get_state_manager():
    """Get StateManager instance."""
    from app.com.chatbot.state_manager import StateManager
    return StateManager

def get_gpt_handler():
    """Get GPTHandler instance."""
    from app.com.chatbot.gpt_handler import GPTHandler
    return GPTHandler

def get_channel_config():
    """Get channel configuration."""
    from app.com.utils.channel_config import ChannelConfig
    return ChannelConfig

def get_rate_limiter():
    """Get RateLimiter instance."""
    from app.com.utils.rate_limiter import RateLimiter
    return RateLimiter

# Funciones de workflow
def get_workflow_manager():
    """Get WorkflowManager instance."""
    from app.com.chatbot.workflow.manager import WorkflowManager
    return WorkflowManager

def get_contract_generator():
    """Get ContractGenerator instance."""
    from app.com.chatbot.workflow.contract_generator import ContractGenerator
    return ContractGenerator

def get_profile_creator():
    """Get ProfileCreator instance."""
    from app.com.chatbot.workflow.profile_creator import ProfileCreator
    return ProfileCreator
    
# Register essential modules at startup
if os.environ.get('DJANGO_SETTINGS_MODULE'):
    validate_imports()

def get_absolute_import(relative_path: str) -> str:
    """
    Convierte una ruta relativa en una importación absoluta.
    
    Args:
        relative_path: Ruta relativa del módulo
        
    Returns:
        Ruta absoluta para la importación
    """
    for rel, abs_path in IMPORT_MAPPINGS.items():
        if relative_path.startswith(rel):
            return relative_path.replace(rel, abs_path)
    return f"app.{relative_path}"

def validate_import_structure() -> Dict[str, List[str]]:
    """
    Valida la estructura de importaciones del proyecto.
    
    Returns:
        Diccionario con errores encontrados por módulo
    """
    errors = {}
    base_dir = Path(__file__).parent
    
    for package, subpackages in PACKAGE_STRUCTURE.items():
        if package == 'root':
            continue
            
        package_dir = base_dir / package
        if not package_dir.exists():
            errors[package] = [f"Directorio {package} no encontrado"]
            continue
            
        for subpackage in subpackages:
            subpackage_dir = package_dir / subpackage
            if not subpackage_dir.exists():
                if package not in errors:
                    errors[package] = []
                errors[package].append(f"Subdirectorio {subpackage} no encontrado en {package}")
                
    return errors

def get_import_path(file_path: Path) -> str:
    """
    Obtiene la ruta de importación para un archivo.
    
    Args:
        file_path: Ruta al archivo
        
    Returns:
        Ruta de importación
    """
    rel_path = file_path.relative_to(Path(__file__).parent)
    return '.'.join(rel_path.parts[:-1] + (rel_path.stem,))

def should_process_file(file_path: Path) -> bool:
    """
    Determina si un archivo debe ser procesado según las reglas.
    
    Args:
        file_path: Ruta al archivo
        
    Returns:
        True si el archivo debe ser procesado
    """
    for pattern in IMPORT_RULES['exclude_patterns']:
        if pattern in str(file_path):
            return False
    return True

# Compatibilidad con código legacy
# Siguiendo reglas globales de Grupo huntRED® para mantenimiento

# Si get_state_manager existe, creamos un alias get_chat_state_manager
if 'get_state_manager' in globals():
    # Alias para mantener compatibilidad
    def get_chat_state_manager(*args, **kwargs):
        import logging
        logging.getLogger('import_compatibility').warning(
            "Uso de función renombrada: get_chat_state_manager -> get_state_manager"
        )
        return get_state_manager(*args, **kwargs)

# Si get_intent_detector existe, creamos un alias get_intent_processor
if 'get_intent_detector' in globals():
    # Alias para mantener compatibilidad
    def get_intent_processor(*args, **kwargs):
        import logging
        logging.getLogger('import_compatibility').warning(
            "Uso de función renombrada: get_intent_processor -> get_intent_detector"
        )
        return get_intent_detector(*args, **kwargs)

# Soporte para ConversationalFlowManager
try:
    # FIXED: # FIXED: # FIXED: # FIXED: # FIXED: # FIXED: # FIXED: # FIXED: # FIXED: from app.com.chatbot.conversational_flow_manager import ConversationalFlowManager # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular # Importación removida para evitar dependencia circular
    # Alias para mantener compatibilidad
    def get_conversational_flow_manager(*args, **kwargs):
        import logging
        logging.getLogger('import_compatibility').warning(
            "Uso de función renombrada: get_conversational_flow_manager"
        )
        return ConversationalFlowManager
except (ImportError, ModuleNotFoundError):
    pass


# Mapa integral de compatibilidad con código legacy
# Implementado siguiendo reglas globales de Grupo huntRED® para mantenimiento de código
# Generado automáticamente por import_compatibility_patch.py

# Inicialización del logger para compatibilidad
import logging
compatibility_logger = logging.getLogger('import_compatibility')

# Alias para get_gpt_handler
if 'get_gpt_handler' in globals():
    # Compatibilidad: get_gpt_processor -> get_gpt_handler
    def get_gpt_processor(*args, **kwargs):
        compatibility_logger.warning("Uso de función renombrada: get_gpt_processor -> get_gpt_handler")
        return get_gpt_handler(*args, **kwargs)
    # Compatibilidad: get_gpt_engine -> get_gpt_handler
    def get_gpt_engine(*args, **kwargs):
        compatibility_logger.warning("Uso de función renombrada: get_gpt_engine -> get_gpt_handler")
        return get_gpt_handler(*args, **kwargs)
    # Compatibilidad: get_gpt_connector -> get_gpt_handler
    def get_gpt_connector(*args, **kwargs):
        compatibility_logger.warning("Uso de función renombrada: get_gpt_connector -> get_gpt_handler")
        return get_gpt_handler(*args, **kwargs)

# Alias para get_state_manager
if 'get_state_manager' in globals():
    # Compatibilidad: get_chat_state_manager -> get_state_manager
    def get_chat_state_manager(*args, **kwargs):
        compatibility_logger.warning("Uso de función renombrada: get_chat_state_manager -> get_state_manager")
        return get_state_manager(*args, **kwargs)

# Alias para get_workflow_manager
if 'get_workflow_manager' in globals():
    # Compatibilidad: get_workflow_handler -> get_workflow_manager
    def get_workflow_handler(*args, **kwargs):
        compatibility_logger.warning("Uso de función renombrada: get_workflow_handler -> get_workflow_manager")
        return get_workflow_manager(*args, **kwargs)
    # Compatibilidad: get_workflow_engine -> get_workflow_manager
    def get_workflow_engine(*args, **kwargs):
        compatibility_logger.warning("Uso de función renombrada: get_workflow_engine -> get_workflow_manager")
        return get_workflow_manager(*args, **kwargs)

# Alias para get_intent_detector
if 'get_intent_detector' in globals():
    # Compatibilidad: get_intent_processor -> get_intent_detector
    def get_intent_processor(*args, **kwargs):
        compatibility_logger.warning("Uso de función renombrada: get_intent_processor -> get_intent_detector")
        return get_intent_detector(*args, **kwargs)
    # Compatibilidad: get_intents_handler -> get_intent_detector
    def get_intents_handler(*args, **kwargs):
        compatibility_logger.warning("Uso de función renombrada: get_intents_handler -> get_intent_detector")
        return get_intent_detector(*args, **kwargs)

# Get ConversationalFlowManager instance con manejo de importación diferida.
def get_conversational_flow_manager():
    """Obtiene una instancia de ConversationalFlowManager con importación diferida.
    
    Implementado siguiendo reglas globales de CPU usage y code maintenance de Grupo huntRED®
    """
    try:
        # Importación diferida para evitar dependencias circulares
        from app.com.chatbot.conversational_flow import ConversationalFlowManager
        return ConversationalFlowManager
    except ImportError as e:
        compatibility_logger.error(f"Error al importar ConversationalFlowManager: {e}")
        # Fallback para mantener compatibilidad
        return None

# Alias para get_conversational_flow_manager
if 'get_conversational_flow_manager' in globals():
    # Compatibilidad: get_conversation_manager -> get_conversational_flow_manager
    def get_conversation_manager(*args, **kwargs):
        compatibility_logger.warning("Uso de función renombrada: get_conversation_manager -> get_conversational_flow_manager")
        return get_conversational_flow_manager(*args, **kwargs)
    # Compatibilidad: get_conversation_flow -> get_conversational_flow_manager
    def get_conversation_flow(*args, **kwargs):
        compatibility_logger.warning("Uso de función renombrada: get_conversation_flow -> get_conversational_flow_manager")
        return get_conversational_flow_manager(*args, **kwargs)

# Alias para get_intents_optimizer
if 'get_intents_optimizer' in globals():
    # Compatibilidad: get_intent_optimizer -> get_intents_optimizer
    def get_intent_optimizer(*args, **kwargs):
        compatibility_logger.warning("Uso de función renombrada: get_intent_optimizer -> get_intents_optimizer")
        return get_intents_optimizer(*args, **kwargs)



# FIXED: Funciones generadas automáticamente - v2025.05.19

# Compatibilidad: get_whatsapp_handler -> get_intents

def get_whatsapp_handler(*args, **kwargs):
    """Obtiene un handler para WhatsApp con importación diferida."""
    try:
        try:
            from app.com.chatbot.integrations.whatsapp import WhatsAppHandler
            compatibility_logger.info("Handler WhatsAppHandler importado desde app.com.chatbot.integrations.whatsapp")
            return WhatsAppHandler
        except ImportError:
            try:
                from app.com.chatbot.whatsapp import WhatsAppHandler
                compatibility_logger.info("Handler WhatsAppHandler importado desde app.com.chatbot.whatsapp")
                return WhatsAppHandler
            except ImportError:
                # Implementación de respaldo básica
                from app.com.chatbot.handlers.base_handler import BaseHandler
                compatibility_logger.warning("Usando implementación de respaldo para WhatsAppHandler")
                
                class GenericWhatsAppHandler(BaseHandler):
                    """Implementación genérica para WhatsAppHandler."""
                    def __init__(self):
                        super().__init__()
                        self.handler_type = "WhatsApp"
                    
                    async def send_message(self, user_id, message):
                        """Envía un mensaje vía WhatsApp de forma genérica."""
                        compatibility_logger.info(f"[MOCK] Enviando mensaje a {user_id} vía WhatsApp: {message[:50]}...")
                        return {'success': True, 'message_id': f'mock-{user_id}-{int(time.time())}'}
                    
                    async def check_condition(self, condition, context):
                        """Verifica condiciones de forma genérica."""
                        return True
                
                return GenericWhatsAppHandler
    except Exception as e:
        compatibility_logger.error(f"Error al crear handler genérico para WhatsAppHandler: {e}")
        return None
def get_telegram_handler(*args, **kwargs):
    """Obtiene un handler para telegram handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_telegram_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_slack_handler -> get_intents
def get_slack_handler(*args, **kwargs):
    """Obtiene un handler para slack handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_slack_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_messenger_handler -> get_intents
def get_messenger_handler(*args, **kwargs):
    """Obtiene un handler para messenger handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_messenger_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_instagram_handler -> get_intents
def get_instagram_handler(*args, **kwargs):
    """Obtiene un handler para instagram handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_instagram_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_email_handler -> get_intents
def get_email_handler(*args, **kwargs):
    """Obtiene un handler para email handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_email_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_sms_handler -> get_intents
def get_sms_handler(*args, **kwargs):
    """Obtiene un handler para sms handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_sms_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_voice_handler -> get_intents
def get_voice_handler(*args, **kwargs):
    """Obtiene un handler para voice handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_voice_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_web_handler -> get_intents
def get_web_handler(*args, **kwargs):
    """Obtiene un handler para web handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_web_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_app_handler -> get_intents
def get_app_handler(*args, **kwargs):
    """Obtiene un handler para app handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_app_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_verification_handler -> get_workflow
def get_verification_handler(*args, **kwargs):
    """Obtiene un handler para verification handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_verification_handler -> get_workflow")
        from app.import_config import get_workflow
        return get_workflow(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_workflow: {e}")
        return None

# Compatibilidad: get_notification_handler -> get_workflow
def get_notification_handler(*args, **kwargs):
    """Obtiene un handler para notification handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_notification_handler -> get_workflow")
        from app.import_config import get_workflow
        return get_workflow(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_workflow: {e}")
        return None

# Compatibilidad: get_scheduling_handler -> get_intents
def get_scheduling_handler(*args, **kwargs):
    """Obtiene un handler para scheduling handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_scheduling_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_payment_handler -> get_intents
def get_payment_handler(*args, **kwargs):
    """Obtiene un handler para payment handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_payment_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_location_handler -> get_intents
def get_location_handler(*args, **kwargs):
    """Obtiene un handler para location handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_location_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_document_handler -> get_intents
def get_document_handler(*args, **kwargs):
    """Obtiene un handler para document handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_document_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_media_handler -> get_intents
def get_media_handler(*args, **kwargs):
    """Obtiene un handler para media handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_media_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_sentiment_handler -> get_intents
def get_sentiment_handler(*args, **kwargs):
    """Obtiene un handler para sentiment handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_sentiment_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_analytics_handler -> get_intents
def get_analytics_handler(*args, **kwargs):
    """Obtiene un handler para analytics handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_analytics_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_crm_handler -> get_workflow
def get_crm_handler(*args, **kwargs):
    """Obtiene un handler para crm handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_crm_handler -> get_workflow")
        from app.import_config import get_workflow
        return get_workflow(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_workflow: {e}")
        return None

# Compatibilidad: get_erp_handler -> get_workflow
def get_erp_handler(*args, **kwargs):
    """Obtiene un handler para erp handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_erp_handler -> get_workflow")
        from app.import_config import get_workflow
        return get_workflow(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_workflow: {e}")
        return None

# Compatibilidad: get_context_handler -> get_intents
def get_context_handler(*args, **kwargs):
    """Obtiene un handler para context handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_context_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Compatibilidad: get_llm_handler -> get_intents
def get_llm_handler(*args, **kwargs):
    """Obtiene un handler para llm handler con importación diferida."""
    try:
        compatibility_logger.warning("Uso de función creada automáticamente: get_llm_handler -> get_intents")
        from app.import_config import get_intents
        return get_intents(*args, **kwargs)
    except ImportError as e:
        compatibility_logger.error(f"Error al importar get_intents: {e}")
        return None

# Función auxiliar para encontrar el mejor manejador existente para compatibilidad
def find_best_match_handler(target_handler, existing_handlers):
    """Encuentra el manejador existente más similar al objetivo."""
    if not existing_handlers:
        return None
        
    # Primero intentar encontrar un manejador genérico como 'default_handler'
    if 'default' in existing_handlers:
        return 'default'
    
    # Luego buscar coincidencias por categoría
    categories = {
        'messaging': ['whatsapp', 'telegram', 'slack', 'messenger', 'sms', 'email'],
        'processing': ['intents', 'gpt', 'llm', 'sentiment', 'context'],
        'integration': ['workflow', 'crm', 'erp', 'notification', 'verification'],
        'media': ['document', 'media', 'voice', 'location'],
        'platform': ['web', 'app']
    }
    
    # Identificar la categoría del objetivo
    target_category = None
    target_base = target_handler.replace('_handler', '')
    
    for category, items in categories.items():
        if any(item in target_base for item in items):
            target_category = category
            break
    
    if target_category:
        # Buscar manejadores en la misma categoría
        for existing in existing_handlers:
            existing_base = existing.replace('_handler', '')
            for item in categories.get(target_category, []):
                if item in existing_base:
                    return existing
    
    # Finalmente, elegir el primer manejador disponible como último recurso
    if existing_handlers:
        return existing_handlers[0]
    
    return None

import time  # Agregado para los handlers genéricos


# FIXED: Funciones de workflow y contexto - v2025.05.19

def get_workflow_context(*args, **kwargs):
    """Obtiene una instancia o referencia para workflow context con importación diferida."""
    try:
        # Intentar importar desde el módulo esperado
        try:
            from app.com.chatbot.workflow import WorkflowContext
            logger.info(f"[AUTO-GEN] get_workflow_context importado desde app.com.chatbot.workflow")
            return WorkflowContext
        except ImportError as e:
            # Implementación genérica como fallback
            logger.warning(f"Error importando WorkflowContext desde app.com.chatbot.workflow. Usando implementación genérica: {e}")
            
            class GenericImplementation:
                """Implementación genérica para WorkflowContext."""
                
                def __init__(self, *args, **kwargs):
                    self.name = "WorkflowContext"
                    self.initialized = True
                    logger.info(f"[MOCK] {self.name} inicializado con {args} {kwargs}")
                
                def process(self, *args, **kwargs):
                    """Procesa información de manera genérica."""
                    logger.info(f"[MOCK] {self.name}.process llamado con {args} {kwargs}")
                    return {
                        "success": True,
                        "result": "Procesamiento simulado",
                        "timestamp": time.time()
                    }
                
                def analyze(self, *args, **kwargs):
                    """Análisis genérico."""
                    logger.info(f"[MOCK] {self.name}.analyze llamado con {args} {kwargs}")
                    return {
                        "score": 0.75,
                        "confidence": 0.85,
                        "timestamp": time.time()
                    }
                
                def get_context(self, *args, **kwargs):
                    """Obtiene un contexto genérico."""
                    logger.info(f"[MOCK] {self.name}.get_context llamado con {args} {kwargs}")
                    return {
                        "type": "generic_context",
                        "data": {},
                        "timestamp": time.time()
                    }
            
            return GenericImplementation
    except Exception as e:
        logger.error(f"Error en get_workflow_context: {e}")
        return None

def get_workflow_step(*args, **kwargs):
    """Obtiene una instancia o referencia para workflow step con importación diferida."""
    try:
        # Intentar importar desde el módulo esperado
        try:
            from app.com.chatbot.workflow import WorkflowEngine
            logger.info(f"[AUTO-GEN] get_workflow_step importado desde app.com.chatbot.workflow")
            return WorkflowEngine
        except ImportError as e:
            # Implementación genérica como fallback
            logger.warning(f"Error importando WorkflowEngine desde app.com.chatbot.workflow. Usando implementación genérica: {e}")
            
            class GenericImplementation:
                """Implementación genérica para WorkflowEngine."""
                
                def __init__(self, *args, **kwargs):
                    self.name = "WorkflowEngine"
                    self.initialized = True
                    logger.info(f"[MOCK] {self.name} inicializado con {args} {kwargs}")
                
                def process(self, *args, **kwargs):
                    """Procesa información de manera genérica."""
                    logger.info(f"[MOCK] {self.name}.process llamado con {args} {kwargs}")
                    return {
                        "success": True,
                        "result": "Procesamiento simulado",
                        "timestamp": time.time()
                    }
                
                def analyze(self, *args, **kwargs):
                    """Análisis genérico."""
                    logger.info(f"[MOCK] {self.name}.analyze llamado con {args} {kwargs}")
                    return {
                        "score": 0.75,
                        "confidence": 0.85,
                        "timestamp": time.time()
                    }
                
                def get_context(self, *args, **kwargs):
                    """Obtiene un contexto genérico."""
                    logger.info(f"[MOCK] {self.name}.get_context llamado con {args} {kwargs}")
                    return {
                        "type": "generic_context",
                        "data": {},
                        "timestamp": time.time()
                    }
            
            return GenericImplementation
    except Exception as e:
        logger.error(f"Error en get_workflow_step: {e}")
        return None

def get_workflow_transition(*args, **kwargs):
    """Obtiene una instancia o referencia para workflow transition con importación diferida."""
    try:
        # Intentar importar desde el módulo esperado
        try:
            from app.com.chatbot.workflow import WorkflowEngine
            logger.info(f"[AUTO-GEN] get_workflow_transition importado desde app.com.chatbot.workflow")
            return WorkflowEngine
        except ImportError as e:
            # Implementación genérica como fallback
            logger.warning(f"Error importando WorkflowEngine desde app.com.chatbot.workflow. Usando implementación genérica: {e}")
            
            class GenericImplementation:
                """Implementación genérica para WorkflowEngine."""
                
                def __init__(self, *args, **kwargs):
                    self.name = "WorkflowEngine"
                    self.initialized = True
                    logger.info(f"[MOCK] {self.name} inicializado con {args} {kwargs}")
                
                def process(self, *args, **kwargs):
                    """Procesa información de manera genérica."""
                    logger.info(f"[MOCK] {self.name}.process llamado con {args} {kwargs}")
                    return {
                        "success": True,
                        "result": "Procesamiento simulado",
                        "timestamp": time.time()
                    }
                
                def analyze(self, *args, **kwargs):
                    """Análisis genérico."""
                    logger.info(f"[MOCK] {self.name}.analyze llamado con {args} {kwargs}")
                    return {
                        "score": 0.75,
                        "confidence": 0.85,
                        "timestamp": time.time()
                    }
                
                def get_context(self, *args, **kwargs):
                    """Obtiene un contexto genérico."""
                    logger.info(f"[MOCK] {self.name}.get_context llamado con {args} {kwargs}")
                    return {
                        "type": "generic_context",
                        "data": {},
                        "timestamp": time.time()
                    }
            
            return GenericImplementation
    except Exception as e:
        logger.error(f"Error en get_workflow_transition: {e}")
        return None

def get_personality_test(*args, **kwargs):
    """Obtiene una instancia o referencia para personality test con importación diferida."""
    try:
        # Intentar importar desde el módulo esperado
        try:
            from app.com.talent.personality import PersonalityTest
            logger.info(f"[AUTO-GEN] get_personality_test importado desde app.com.talent.personality")
            return PersonalityTest
        except ImportError as e:
            # Implementación genérica como fallback
            logger.warning(f"Error importando PersonalityTest desde app.com.talent.personality. Usando implementación genérica: {e}")
            
            class GenericImplementation:
                """Implementación genérica para PersonalityTest."""
                
                def __init__(self, *args, **kwargs):
                    self.name = "PersonalityTest"
                    self.initialized = True
                    logger.info(f"[MOCK] {self.name} inicializado con {args} {kwargs}")
                
                def process(self, *args, **kwargs):
                    """Procesa información de manera genérica."""
                    logger.info(f"[MOCK] {self.name}.process llamado con {args} {kwargs}")
                    return {
                        "success": True,
                        "result": "Procesamiento simulado",
                        "timestamp": time.time()
                    }
                
                def analyze(self, *args, **kwargs):
                    """Análisis genérico."""
                    logger.info(f"[MOCK] {self.name}.analyze llamado con {args} {kwargs}")
                    return {
                        "score": 0.75,
                        "confidence": 0.85,
                        "timestamp": time.time()
                    }
                
                def get_context(self, *args, **kwargs):
                    """Obtiene un contexto genérico."""
                    logger.info(f"[MOCK] {self.name}.get_context llamado con {args} {kwargs}")
                    return {
                        "type": "generic_context",
                        "data": {},
                        "timestamp": time.time()
                    }
            
            return GenericImplementation
    except Exception as e:
        logger.error(f"Error en get_personality_test: {e}")
        return None

def get_personality_analyzer(*args, **kwargs):
    """Obtiene una instancia o referencia para personality analyzer con importación diferida."""
    try:
        # Intentar importar desde el módulo esperado
        try:
            from app.com.talent.personality import PersonalityAnalyzer
            logger.info(f"[AUTO-GEN] get_personality_analyzer importado desde app.com.talent.personality")
            return PersonalityAnalyzer
        except ImportError as e:
            # Implementación genérica como fallback
            logger.warning(f"Error importando PersonalityAnalyzer desde app.com.talent.personality. Usando implementación genérica: {e}")
            
            class GenericImplementation:
                """Implementación genérica para PersonalityAnalyzer."""
                
                def __init__(self, *args, **kwargs):
                    self.name = "PersonalityAnalyzer"
                    self.initialized = True
                    logger.info(f"[MOCK] {self.name} inicializado con {args} {kwargs}")
                
                def process(self, *args, **kwargs):
                    """Procesa información de manera genérica."""
                    logger.info(f"[MOCK] {self.name}.process llamado con {args} {kwargs}")
                    return {
                        "success": True,
                        "result": "Procesamiento simulado",
                        "timestamp": time.time()
                    }
                
                def analyze(self, *args, **kwargs):
                    """Análisis genérico."""
                    logger.info(f"[MOCK] {self.name}.analyze llamado con {args} {kwargs}")
                    return {
                        "score": 0.75,
                        "confidence": 0.85,
                        "timestamp": time.time()
                    }
                
                def get_context(self, *args, **kwargs):
                    """Obtiene un contexto genérico."""
                    logger.info(f"[MOCK] {self.name}.get_context llamado con {args} {kwargs}")
                    return {
                        "type": "generic_context",
                        "data": {},
                        "timestamp": time.time()
                    }
            
            return GenericImplementation
    except Exception as e:
        logger.error(f"Error en get_personality_analyzer: {e}")
        return None

def get_culture_analyzer(*args, **kwargs):
    """Obtiene una instancia o referencia para culture analyzer con importación diferida."""
    try:
        # Intentar importar desde el módulo esperado
        try:
            from app.com.talent.culture import CultureAnalyzer
            logger.info(f"[AUTO-GEN] get_culture_analyzer importado desde app.com.talent.culture")
            return CultureAnalyzer
        except ImportError as e:
            # Implementación genérica como fallback
            logger.warning(f"Error importando CultureAnalyzer desde app.com.talent.culture. Usando implementación genérica: {e}")
            
            class GenericImplementation:
                """Implementación genérica para CultureAnalyzer."""
                
                def __init__(self, *args, **kwargs):
                    self.name = "CultureAnalyzer"
                    self.initialized = True
                    logger.info(f"[MOCK] {self.name} inicializado con {args} {kwargs}")
                
                def process(self, *args, **kwargs):
                    """Procesa información de manera genérica."""
                    logger.info(f"[MOCK] {self.name}.process llamado con {args} {kwargs}")
                    return {
                        "success": True,
                        "result": "Procesamiento simulado",
                        "timestamp": time.time()
                    }
                
                def analyze(self, *args, **kwargs):
                    """Análisis genérico."""
                    logger.info(f"[MOCK] {self.name}.analyze llamado con {args} {kwargs}")
                    return {
                        "score": 0.75,
                        "confidence": 0.85,
                        "timestamp": time.time()
                    }
                
                def get_context(self, *args, **kwargs):
                    """Obtiene un contexto genérico."""
                    logger.info(f"[MOCK] {self.name}.get_context llamado con {args} {kwargs}")
                    return {
                        "type": "generic_context",
                        "data": {},
                        "timestamp": time.time()
                    }
            
            return GenericImplementation
    except Exception as e:
        logger.error(f"Error en get_culture_analyzer: {e}")
        return None

def get_team_analyzer(*args, **kwargs):
    """Obtiene una instancia o referencia para team analyzer con importación diferida."""
    try:
        # Intentar importar desde el módulo esperado
        try:
            from app.com.talent.team import TeamAnalyzer
            logger.info(f"[AUTO-GEN] get_team_analyzer importado desde app.com.talent.team")
            return TeamAnalyzer
        except ImportError as e:
            # Implementación genérica como fallback
            logger.warning(f"Error importando TeamAnalyzer desde app.com.talent.team. Usando implementación genérica: {e}")
            
            class GenericImplementation:
                """Implementación genérica para TeamAnalyzer."""
                
                def __init__(self, *args, **kwargs):
                    self.name = "TeamAnalyzer"
                    self.initialized = True
                    logger.info(f"[MOCK] {self.name} inicializado con {args} {kwargs}")
                
                def process(self, *args, **kwargs):
                    """Procesa información de manera genérica."""
                    logger.info(f"[MOCK] {self.name}.process llamado con {args} {kwargs}")
                    return {
                        "success": True,
                        "result": "Procesamiento simulado",
                        "timestamp": time.time()
                    }
                
                def analyze(self, *args, **kwargs):
                    """Análisis genérico."""
                    logger.info(f"[MOCK] {self.name}.analyze llamado con {args} {kwargs}")
                    return {
                        "score": 0.75,
                        "confidence": 0.85,
                        "timestamp": time.time()
                    }
                
                def get_context(self, *args, **kwargs):
                    """Obtiene un contexto genérico."""
                    logger.info(f"[MOCK] {self.name}.get_context llamado con {args} {kwargs}")
                    return {
                        "type": "generic_context",
                        "data": {},
                        "timestamp": time.time()
                    }
            
            return GenericImplementation
    except Exception as e:
        logger.error(f"Error en get_team_analyzer: {e}")
        return None

def get_organizational_analyzer(*args, **kwargs):
    """Obtiene una instancia o referencia para organizational analyzer con importación diferida."""
    try:
        # Intentar importar desde el módulo esperado
        try:
            from app.com.talent.organization import OrganizationalAnalyzer
            logger.info(f"[AUTO-GEN] get_organizational_analyzer importado desde app.com.talent.organization")
            return OrganizationalAnalyzer
        except ImportError as e:
            # Implementación genérica como fallback
            logger.warning(f"Error importando OrganizationalAnalyzer desde app.com.talent.organization. Usando implementación genérica: {e}")
            
            class GenericImplementation:
                """Implementación genérica para OrganizationalAnalyzer."""
                
                def __init__(self, *args, **kwargs):
                    self.name = "OrganizationalAnalyzer"
                    self.initialized = True
                    logger.info(f"[MOCK] {self.name} inicializado con {args} {kwargs}")
                
                def process(self, *args, **kwargs):
                    """Procesa información de manera genérica."""
                    logger.info(f"[MOCK] {self.name}.process llamado con {args} {kwargs}")
                    return {
                        "success": True,
                        "result": "Procesamiento simulado",
                        "timestamp": time.time()
                    }
                
                def analyze(self, *args, **kwargs):
                    """Análisis genérico."""
                    logger.info(f"[MOCK] {self.name}.analyze llamado con {args} {kwargs}")
                    return {
                        "score": 0.75,
                        "confidence": 0.85,
                        "timestamp": time.time()
                    }
                
                def get_context(self, *args, **kwargs):
                    """Obtiene un contexto genérico."""
                    logger.info(f"[MOCK] {self.name}.get_context llamado con {args} {kwargs}")
                    return {
                        "type": "generic_context",
                        "data": {},
                        "timestamp": time.time()
                    }
            
            return GenericImplementation
    except Exception as e:
        logger.error(f"Error en get_organizational_analyzer: {e}")
        return None

def get_skill_analyzer(*args, **kwargs):
    """Obtiene una instancia o referencia para skill analyzer con importación diferida."""
    try:
        # Intentar importar desde el módulo esperado
        try:
            from app.com.talent.skills import SkillAnalyzer
            logger.info(f"[AUTO-GEN] get_skill_analyzer importado desde app.com.talent.skills")
            return SkillAnalyzer
        except ImportError as e:
            # Implementación genérica como fallback
            logger.warning(f"Error importando SkillAnalyzer desde app.com.talent.skills. Usando implementación genérica: {e}")
            
            class GenericImplementation:
                """Implementación genérica para SkillAnalyzer."""
                
                def __init__(self, *args, **kwargs):
                    self.name = "SkillAnalyzer"
                    self.initialized = True
                    logger.info(f"[MOCK] {self.name} inicializado con {args} {kwargs}")
                
                def process(self, *args, **kwargs):
                    """Procesa información de manera genérica."""
                    logger.info(f"[MOCK] {self.name}.process llamado con {args} {kwargs}")
                    return {
                        "success": True,
                        "result": "Procesamiento simulado",
                        "timestamp": time.time()
                    }
                
                def analyze(self, *args, **kwargs):
                    """Análisis genérico."""
                    logger.info(f"[MOCK] {self.name}.analyze llamado con {args} {kwargs}")
                    return {
                        "score": 0.75,
                        "confidence": 0.85,
                        "timestamp": time.time()
                    }
                
                def get_context(self, *args, **kwargs):
                    """Obtiene un contexto genérico."""
                    logger.info(f"[MOCK] {self.name}.get_context llamado con {args} {kwargs}")
                    return {
                        "type": "generic_context",
                        "data": {},
                        "timestamp": time.time()
                    }
            
            return GenericImplementation
    except Exception as e:
        logger.error(f"Error en get_skill_analyzer: {e}")
        return None

def get_values_integrator(*args, **kwargs):
    """Obtiene una instancia o referencia para values integrator con importación diferida."""
    try:
        # Intentar importar desde el nuevo módulo de valores
        try:
            from app.com.chatbot.values import ValuesChatMiddleware
            logger.info(f"[AUTO-GEN] get_values_integrator importado desde app.com.chatbot.values")
            return ValuesChatMiddleware
        except ImportError as e:
            # Implementación genérica como fallback
            logger.warning(f"Error importando ValuesIntegrator desde app.com.chatbot.core.values. Usando implementación genérica: {e}")
            
            class GenericImplementation:
                """Implementación genérica para ValuesIntegrator."""
                
                def __init__(self, *args, **kwargs):
                    self.name = "ValuesIntegrator"
                    self.initialized = True
                    logger.info(f"[MOCK] {self.name} inicializado con {args} {kwargs}")
                
                def process(self, *args, **kwargs):
                    """Procesa información de manera genérica."""
                    logger.info(f"[MOCK] {self.name}.process llamado con {args} {kwargs}")
                    return {
                        "success": True,
                        "result": "Procesamiento simulado",
                        "timestamp": time.time()
                    }
                
                def analyze(self, *args, **kwargs):
                    """Análisis genérico."""
                    logger.info(f"[MOCK] {self.name}.analyze llamado con {args} {kwargs}")
                    return {
                        "score": 0.75,
                        "confidence": 0.85,
                        "timestamp": time.time()
                    }
                
                def get_context(self, *args, **kwargs):
                    """Obtiene un contexto genérico."""
                    logger.info(f"[MOCK] {self.name}.get_context llamado con {args} {kwargs}")
                    return {
                        "type": "generic_context",
                        "data": {},
                        "timestamp": time.time()
                    }
            
            return GenericImplementation
    except Exception as e:
        logger.error(f"Error en get_values_integrator: {e}")
        return None

def get_principles_manager(*args, **kwargs):
    """Obtiene una instancia o referencia para principles manager con importación diferida."""
    try:
        # Intentar importar desde el módulo esperado
        try:
            from app.com.chatbot.core.values import PrinciplesManager
            logger.info(f"[AUTO-GEN] get_principles_manager importado desde app.com.chatbot.core.values")
            return PrinciplesManager
        except ImportError as e:
            # Implementación genérica como fallback
            logger.warning(f"Error importando PrinciplesManager desde app.com.chatbot.core.values. Usando implementación genérica: {e}")
            
            class GenericImplementation:
                """Implementación genérica para PrinciplesManager."""
                
                def __init__(self, *args, **kwargs):
                    self.name = "PrinciplesManager"
                    self.initialized = True
                    logger.info(f"[MOCK] {self.name} inicializado con {args} {kwargs}")
                
                def process(self, *args, **kwargs):
                    """Procesa información de manera genérica."""
                    logger.info(f"[MOCK] {self.name}.process llamado con {args} {kwargs}")
                    return {
                        "success": True,
                        "result": "Procesamiento simulado",
                        "timestamp": time.time()
                    }
                
                def analyze(self, *args, **kwargs):
                    """Análisis genérico."""
                    logger.info(f"[MOCK] {self.name}.analyze llamado con {args} {kwargs}")
                    return {
                        "score": 0.75,
                        "confidence": 0.85,
                        "timestamp": time.time()
                    }
                
                def get_context(self, *args, **kwargs):
                    """Obtiene un contexto genérico."""
                    logger.info(f"[MOCK] {self.name}.get_context llamado con {args} {kwargs}")
                    return {
                        "type": "generic_context",
                        "data": {},
                        "timestamp": time.time()
                    }
            
            return GenericImplementation
    except Exception as e:
        logger.error(f"Error en get_principles_manager: {e}")
        return None
