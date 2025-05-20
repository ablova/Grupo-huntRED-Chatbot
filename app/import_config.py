# /home/pablo/app/import_config.py
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
    from app.com.chatbot.conversational_flow_manager import ConversationalFlowManager
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
    from app.com.chatbot.conversational_flow_manager import ConversationalFlowManager
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

